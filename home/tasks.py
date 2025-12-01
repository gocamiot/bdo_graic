from celery import shared_task
from django.shortcuts import get_object_or_404
from django.apps import apps
from django.db import models, connections
from django.utils import timezone
from django.contrib.auth import get_user_model
from urllib.parse import urlparse
import os
from math import ceil
from django.contrib.contenttypes.models import ContentType

from home.models import IPE, PyFunction, JoinModel
from loader.models import InstantUpload, hash_json, json_to_vector, is_pgvector_enabled, TypeChoices

from rapidfuzz.fuzz import ratio, token_set_ratio, WRatio
from fuzzywuzzy import fuzz
import jellyfish

User = get_user_model()

BATCH_SIZE = 500


def get_original_field_name(join_field_name):
    field_name = join_field_name
    if field_name.startswith('d_'):
        field_name = field_name[2:]

    if field_name.lower() in ['id_original', 'count_original']:
        return field_name

    if field_name.endswith('_original'):
        field_name = field_name[:-9]
        field_name = f"_{field_name}"

    return field_name

@shared_task(bind=True)
def async_load_data_to_join_model(self, model_name, pk, params):
    method = params.get('method')
    percent = params.get('percent')

    c_full_word_match = params.get('c_full_word_match') == 'on'
    py_function = params.get('py_function')
    c_percent = params.get('c_percent')
    fields_to_pass = params.get('fields_to_pass', [])

    split_char = params.get('split_char')
    word_position = params.get('word_position')
    split_space = params.get('split_space') == 'on'
    s_full_word_match = params.get('s_full_word_match') == 'on'

    pre_char = params.get('pre_char')
    post_char = params.get('post_char')
    pp_full_word_match = params.get('pp_full_word_match') == 'on'

    jaro_winkler = params.get('jaro_winkler')
    levenshtein = params.get('levenshtein')
    v_token_set_ratio = params.get('token_set_ratio')
    phonetic = params.get('phonetic')
    fuzzy_wuzzy = params.get('fuzzy_wuzzy')

    left_split_char = params.get('left_split_char')
    email_pre_char = params.get('email_pre_char')
    email_post_char = params.get('email_post_char')

    join_model = JoinModel.objects.get(pk=pk)
    model = apps.get_model('tables', model_name)
    vector_model_name = getattr(model, 'vector_model', 'BAAI/bge-large-en-v1.5')

    loader_instance = InstantUpload.objects.create(
        type=TypeChoices.FILE,
        content_type=ContentType.objects.get_for_model(model)
    )

    base_model_class = join_model.base_model.model_class()
    has_delta_model = bool(join_model.delta_model)
    delta_model_class = join_model.delta_model.model_class() if has_delta_model else None

    max_base_loader_instance = base_model_class.objects.aggregate(models.Max('loader_instance'))['loader_instance__max']
    base_records = list(base_model_class.objects.filter(loader_instance=max_base_loader_instance))

    delta_records = []
    if has_delta_model:
        max_delta_loader_instance = delta_model_class.objects.aggregate(models.Max('loader_instance'))['loader_instance__max']
        delta_records = list(delta_model_class.objects.filter(loader_instance=max_delta_loader_instance))

    base_field = join_model.base_f_key_fields
    delta_f_fields = join_model.delta_f_key_fields.split(',') if join_model.delta_f_key_fields and has_delta_model else []

    base_fields = join_model.base_fields.split(',') if join_model.base_fields else []
    delta_fields = join_model.delta_fields.split(',') if join_model.delta_fields and has_delta_model else []

    def safe_field_name(name):
        if name.startswith('_') or name.lower() == 'count':
            sanitized = name.lstrip('_')
            return f"{sanitized}_original"
        return name

    base_field = safe_field_name(base_field)
    delta_f_fields = [safe_field_name(f) for f in delta_f_fields]
    base_fields = [safe_field_name(f) for f in base_fields]
    delta_fields = [safe_field_name(f) for f in delta_fields]
    fields_to_pass = [safe_field_name(f) for f in fields_to_pass]

    delta_values_set = set()
    delta_mapping = {}
    if has_delta_model:
        for delta in delta_records:
            delta_values = [str(getattr(delta, field, None)) for field in delta_f_fields if getattr(delta, field, None) is not None]
            normalized_delta_value = "".join(delta_values).replace(" ", "").lower()
            delta_values_set.add(normalized_delta_value)
            delta_mapping[normalized_delta_value] = delta

    total = len(base_records)
    total_batches = ceil(total / BATCH_SIZE) if total else 0

    total_created_instances = 0

    for batch_index in range(total_batches):
        start = batch_index * BATCH_SIZE
        end = start + BATCH_SIZE
        base_batch = base_records[start:end]

        adjoin_instances = []

        for base_record in base_batch:
            base_value = str(getattr(base_record, base_field, None)) if base_record else None
            normalized_base_value = base_value.replace(" ", "").lower() if base_value else None
            raw_base_value = base_value if base_value else None

            matched_delta_record = []

            if has_delta_model and normalized_base_value:

                # ---------- contains method ----------
                if method == 'contains':
                    for delta_value in delta_values_set:
                        delta_combined = "".join(
                            [str(getattr(delta_mapping[delta_value], f, "")).strip() for f in delta_f_fields]
                        ).replace(" ", "").lower()

                        normalized_base = normalized_base_value.strip()

                        if c_full_word_match:
                            if normalized_base == delta_combined:
                                matched_delta_record.append(delta_mapping[delta_value])
                        else:
                            if normalized_base in delta_combined:
                                matched_delta_record.append(delta_mapping[delta_value])

                # ---------- winkler_levenshtein method ----------
                elif method == 'winkler_levenshtein':
                    required_methods = []
                    if jaro_winkler: required_methods.append('jaro_winkler')
                    if levenshtein: required_methods.append('levenshtein')
                    if v_token_set_ratio: required_methods.append('token_set_ratio')
                    if phonetic: required_methods.append('phonetic')
                    if fuzzy_wuzzy: required_methods.append('fuzzy_wuzzy')
                    if not required_methods: required_methods = ['jaro_winkler','levenshtein','token_set_ratio']

                    for delta_value in delta_values_set:
                        meets_threshold = True
                        scores = {}
                        if 'jaro_winkler' in required_methods:
                            try:
                                scores['jaro_winkler'] = WRatio(normalized_base_value, delta_value)
                            except Exception:
                                scores['jaro_winkler'] = 0
                            if scores['jaro_winkler'] < int(percent): meets_threshold=False
                        if 'levenshtein' in required_methods:
                            try:
                                scores['levenshtein'] = ratio(normalized_base_value, delta_value)
                            except Exception:
                                scores['levenshtein'] = 0
                            if scores['levenshtein'] < int(percent): meets_threshold=False
                        if 'token_set_ratio' in required_methods:
                            try:
                                scores['token_set_ratio'] = token_set_ratio(normalized_base_value, delta_value)
                            except Exception:
                                scores['token_set_ratio'] = 0
                            if scores['token_set_ratio'] < int(percent): meets_threshold=False
                        if 'phonetic' in required_methods:
                            try:
                                soundex_base = jellyfish.soundex(normalized_base_value)
                                soundex_delta = jellyfish.soundex(delta_value)
                                scores['phonetic'] = 100 if soundex_base==soundex_delta else 0
                            except Exception:
                                scores['phonetic'] = 0
                            if scores['phonetic'] < int(percent): meets_threshold=False
                        if 'fuzzy_wuzzy' in required_methods:
                            try:
                                scores['fuzzy_wuzzy'] = fuzz.ratio(normalized_base_value, delta_value)
                            except Exception:
                                scores['fuzzy_wuzzy'] = 0
                            if scores['fuzzy_wuzzy'] < int(percent): meets_threshold=False
                        if meets_threshold:
                            matched_delta_record.append(delta_mapping[delta_value])

                # ---------- split method ----------
                elif method == 'split':
                    extracted_words = []
                    temp_value = raw_base_value
                    if split_char:
                        try:
                            position = int(word_position) - 1
                            parts = temp_value.split(split_char)
                            temp_value = parts[position] if 0 <= position < len(parts) else ""
                        except (ValueError, IndexError):
                            temp_value = ""
                    if split_space:
                        words = temp_value.split()
                        try:
                            position = int(word_position) - 1
                            extracted_words = words[position:] if position < len(words) else []
                        except (ValueError, IndexError):
                            extracted_words = []

                    if extracted_words:
                        normalized_extracted_words = [word.lower() for word in extracted_words]
                        for delta_value in delta_values_set:
                            delta_combined = "".join([str(getattr(delta_mapping[delta_value], f, "")) for f in delta_f_fields]).replace(" ", "").lower()
                            if s_full_word_match:
                                if "".join(normalized_extracted_words) == delta_combined:
                                    matched_delta_record.append(delta_mapping[delta_value])
                            else:
                                if all(word in delta_combined for word in normalized_extracted_words):
                                    matched_delta_record.append(delta_mapping[delta_value])

                # ---------- pre_post method ----------
                elif method == 'pre_post':
                    modified_base_value = normalized_base_value
                    if pre_char and pre_char.isdigit():
                        remove_count = int(pre_char)
                        modified_base_value = modified_base_value[remove_count:] if remove_count < len(modified_base_value) else ""
                    if post_char and post_char.isdigit():
                        remove_count = int(post_char)
                        modified_base_value = modified_base_value[:-remove_count] if remove_count < len(modified_base_value) else ""

                    for delta_value in delta_values_set:
                        delta_combined = "".join([str(getattr(delta_mapping[delta_value], f, "")) for f in delta_f_fields]).replace(" ", "").lower()
                        if pp_full_word_match:
                            if modified_base_value == delta_combined:
                                matched_delta_record.append(delta_mapping[delta_value])
                        else:
                            if modified_base_value in delta_combined:
                                matched_delta_record.append(delta_mapping[delta_value])

                # ---------- custom method ----------
                elif method == 'custom' and py_function:
                    local_vars = {}
                    py_func = get_object_or_404(PyFunction, id=py_function)
                    try:
                        exec(py_func.func, {}, local_vars)
                        func = next((v for v in local_vars.values() if callable(v)), None)
                        if func:
                            for delta_record in delta_records:
                                base_values = [str(getattr(base_record, f, "")) for f in fields_to_pass if not f.startswith('d_')]
                                delta_values = [str(getattr(delta_record, f[2:], "")) for f in fields_to_pass if f.startswith('d_')]
                                try:
                                    result = func(*base_values, *delta_values)
                                    if result:
                                        matched_delta_record.append(delta_record)
                                except:
                                    continue
                    except Exception as e:
                        print(f"Error executing custom function: {e}")

                # ---------- email_join method ----------
                elif method == 'email_join':
                    temp_value = normalized_base_value.split('@')[0] if normalized_base_value else ""
                    if left_split_char:
                        temp_value = temp_value.split(left_split_char)[0]
                    if email_pre_char and email_pre_char.isdigit():
                        remove_count = int(email_pre_char)
                        temp_value = temp_value[remove_count:] if remove_count < len(temp_value) else ""
                    if email_post_char and email_post_char.isdigit():
                        remove_count = int(email_post_char)
                        temp_value = temp_value[:-remove_count] if remove_count < len(temp_value) else ""
                    for delta_value in delta_values_set:
                        delta_combined = "".join([str(getattr(delta_mapping[delta_value], f, "")) for f in delta_f_fields]).replace(" ", "").lower()
                        if temp_value in delta_combined:
                            matched_delta_record.append(delta_mapping[delta_value])

            adjoin_data = {'loader_instance': loader_instance.pk, 'json_data': None, 'hash_data': None}
            if matched_delta_record:
                for rec in matched_delta_record:
                    adjoin_copy = adjoin_data.copy()
                    adjoin_copy.update({'both':1, 'base':0, 'delta':0})

                    for f in base_fields:
                        adjoin_copy[f] = getattr(base_record, f, None)

                    for f in delta_fields:
                        join_field_name = f"d_{f}"
                        orig_field_name = get_original_field_name(f)
                        adjoin_copy[join_field_name] = getattr(rec, orig_field_name, None)

                    db_alias = model._default_manager.db
                    database_path = connections[db_alias].settings_dict['NAME']
                    database_name = os.path.basename(database_path) if database_path else database_path
                    json_data = {
                        'database': database_name,
                        'table': model._meta.db_table,
                        'loader_instance': loader_instance.pk,
                        'snapshot_at': timezone.now().isoformat(),
                        'both': adjoin_copy['both'],
                        'base': adjoin_copy['base'],
                        'delta': adjoin_copy['delta']
                    }

                    for f in base_fields:
                        json_data[f] = getattr(base_record, f, None)

                    for f in delta_fields:
                        join_field_name = f"d_{f}"
                        orig_field_name = get_original_field_name(f)
                        json_data[join_field_name] = getattr(rec, orig_field_name, None)

                    adjoin_copy['json_data'] = json_data
                    if is_pgvector_enabled():
                        adjoin_copy['hash_data'] = json_to_vector(json_data)
                    else:
                        adjoin_copy['hash_data'] = hash_json(json_data)

                    adjoin_instances.append(model(**adjoin_copy))
            else:
                adjoin_data.update({'both':0, 'base':1, 'delta':0})
                for f in base_fields:
                    adjoin_data[f] = getattr(base_record, f, None)

                db_alias = model._default_manager.db
                database_path = connections[db_alias].settings_dict['NAME']
                database_name = os.path.basename(database_path) if database_path else database_path
                json_data = {
                    'database': database_name,
                    'table': model._meta.db_table,
                    'loader_instance': loader_instance.pk,
                    'snapshot_at': timezone.now().isoformat(),
                    'both': adjoin_data['both'],
                    'base': adjoin_data['base'],
                    'delta': adjoin_data['delta']
                }

                for f in base_fields:
                    json_data[f] = getattr(base_record, f, None)

                for f in delta_fields:
                    join_field_name = f"d_{f}"
                    json_data[join_field_name] = None

                adjoin_data['json_data'] = json_data
                if is_pgvector_enabled():
                    adjoin_data['hash_data'] = json_to_vector(json_data, model_name=vector_model_name)
                else:
                    adjoin_data['hash_data'] = hash_json(json_data)

                adjoin_instances.append(model(**adjoin_data))

        if adjoin_instances:
            model.objects.bulk_create(adjoin_instances)
            total_created_instances += len(adjoin_instances)

        self.update_state(
            state='PROGRESS',
            meta={
                'current_batch': batch_index + 1,
                'total_batches': total_batches,
                'created_so_far': total_created_instances
            }
        )

    if has_delta_model:
        db_alias = model._default_manager.db
        database_path = connections[db_alias].settings_dict['NAME']
        database_name = os.path.basename(database_path) if database_path else database_path

        delta_only_instances = []
        for delta_record in delta_records:
            adjoin_data = {'loader_instance': loader_instance.pk, 'both':0, 'base':0, 'delta':1, 'json_data':None, 'hash_data':None}

            for f in delta_fields:
                join_field_name = f"d_{f}"
                orig_field_name = get_original_field_name(f)
                adjoin_data[join_field_name] = getattr(delta_record, orig_field_name, None)

            json_data = {
                'database': database_name,
                'table': model._meta.db_table,
                'loader_instance': loader_instance.pk,
                'snapshot_at': timezone.now().isoformat(),
                'both': 0,
                'base': 0,
                'delta': 1
            }

            for f in delta_fields:
                join_field_name = f"d_{f}"
                json_data[join_field_name] = adjoin_data.get(join_field_name)

            adjoin_data['json_data'] = json_data
            if is_pgvector_enabled():
                adjoin_data['hash_data'] = json_to_vector(json_data, model_name=vector_model_name)
            else:
                adjoin_data['hash_data'] = hash_json(json_data)

            delta_only_instances.append(model(**adjoin_data))

        if delta_only_instances:
            model.objects.bulk_create(delta_only_instances)
            total_created_instances += len(delta_only_instances)

    try:
        user = User.objects.get(pk=params.get('user_id'))
    except Exception:
        user = None

    timestamp_local = timezone.localtime(timezone.now())
    timestamp_str = timestamp_local.strftime('%Y-%m-%d %H:%M:%S')

    base_model_class = join_model.base_model.model_class()
    delta_model_class = join_model.delta_model.model_class() if has_delta_model else None

    description_parts = [f'Data extraction: {base_model_class.__name__}' + (f' and {delta_model_class.__name__}' if has_delta_model else ''),
                         f'{base_model_class.__name__} rows: {len(base_records)}']
    if has_delta_model:
        description_parts.append(f'{delta_model_class.__name__} rows: {len(delta_records)}')
    description_parts += [f'New Join table name: {model.__name__}',
                          f'Extracted by: {user.get_full_name() or user.username if user else "system"}',
                          f'Extracted on: {timestamp_str}',
                          f'Rows extracted: {total_created_instances}',
                          f'Snapshot: {loader_instance.pk}',
                          f'Columns: {", ".join([field.name for field in model._meta.get_fields()])}']

    IPE.objects.create(userID=user,
                       path=urlparse(params.get('referer', '/')).path,
                       description='\n'.join(description_parts))

    return {
        'status': 'completed',
        'total_base_rows': len(base_records),
        'total_delta_rows': len(delta_records) if has_delta_model else 0,
        'total_created': total_created_instances
    }
