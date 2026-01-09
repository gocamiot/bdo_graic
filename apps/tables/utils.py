import hashlib
import json
import datetime
import re
import numpy as np
from loader.models import Log, InstantUpload, VectorModel
from django.db import connection
from django.conf import settings
from django.db.models import Subquery, Case, Count, F, OuterRef, Value, When, Q, Window
from django.apps import apps
from apps.common.models import SavedFilter, FieldType
from django.db.models.fields import CharField, DateField, DateTimeField, IntegerField, BigIntegerField
from apps.tables.models import (
    UserFilter, ModelChoices, 
    PageItems, HideShowFilter,
    ServerFilter, 
    mssql_database_connection, database_connection, 
    DBType, DependentDropdown
)
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db.models.functions import RowNumber
from sentence_transformers import SentenceTransformer
from apps.file_manager.models import DefaultValues, FilterMethod

map_field_names = getattr(settings, 'MAP_FIELD_NAMES')
reverse_map_field_names = {v: k for k, v in map_field_names.items()}

def global_filter(request, queryset, fields):
    value = request.GET.get('search')
    
    if value:
        dynamic_q = Q()
        for field in fields:
            dynamic_q |= Q(**{f'{field}__icontains': value})
        return queryset.filter(dynamic_q)

    return queryset

def device_filter(request, queryset, fields):
    value = request.GET.get('search')
    
    if value:
        dynamic_q = Q()
        for field in fields:
            dynamic_q |= Q(**{f'{field}__icontains': value})
        return queryset.filter(dynamic_q)

    return queryset

from apps.graic.utils import search_model_fts, search_model_vector, extract_keywords

def software_filter(request, queryset, fields, search_value="", search_mode=""):
    value = search_value or request.GET.get('search')
    mode = search_mode or request.GET.get('mode')

    default_value = DefaultValues.objects.first()
    if not default_value:
        DefaultValues.objects.create()

    if value and mode == "graic":
        model_name = getattr(queryset.model, 'vector_model', 'BAAI/bge-large-en-v1.5')
        model = SentenceTransformer(model_name)

        # if default_value and default_value.extract_keywords:
        #     value = extract_keywords(value)

        if default_value and default_value.filter_method == FilterMethod.vector:
            vector = to_sql_vector(value, model)
        
        table_name = queryset.model._meta.db_table
        content_type = ContentType.objects.get_for_model(queryset.model)
        snapshots = InstantUpload.objects.filter(content_type=content_type).order_by('-created_at')
        snapshot = request.GET.get('snapshot')
        snapshot_value = None
        if snapshot and snapshot != 'all':
            try:
                summary = InstantUpload.objects.get(id=snapshot, content_type=content_type)
                snapshot_value = summary.pk
            except InstantUpload.DoesNotExist:
                snapshot_value = None

        elif snapshots.exists():
            latest_snapshot = snapshots.first()
            snapshot_value = latest_snapshot.pk

        excluded_fields = {"loader_instance", "json_data", "hash_data", "fts"}
        field_list = ', '.join([f't."{field}"' for field in fields if field not in excluded_fields])

        if default_value.filter_method == FilterMethod.graic:
            result = search_model_fts(model=queryset.model, search_text=value, snapshot_value=snapshot_value)
        else:
            query = f"""
                WITH q AS (
                    SELECT '{vector}'::vector AS v
                )
                SELECT 
                    t."ID",
                    {field_list},
                    ROUND((t.hash_data <=> q.v)::numeric, 3) AS l2_distance
                FROM public."{table_name}" t, q
                WHERE t.loader_instance IS NOT NULL
            """
            if snapshot_value:
                query += f" WHERE t.loader_instance={snapshot_value}"

            query += " ORDER BY t.hash_data <=> q.v;"

            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()


        distance_map = {row[0]: round(1 - float(row[-1]), 3) for row in result}
        if not distance_map:
            return queryset.none()

        original_order = list(distance_map.keys())
        preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(original_order)])
        qs = queryset.filter(pk__in=original_order).order_by(preserved_order)

        if default_value and default_value.dynamic_similarity and default_value.dynamic_rows:
            if not distance_map:
                return queryset.none()

            rows_n = int(default_value.dynamic_rows)

            similarities = [round(sim * 100, 1) for sim in distance_map.values()]
            grouped = sorted(set(int(s) for s in similarities), reverse=True)

            if len(grouped) >= rows_n:
                nth_group = grouped[rows_n - 1]
            else:
                nth_group = grouped[-1]

            valid_pks = [
                pk for pk, sim in distance_map.items()
                if int(sim * 100) >= nth_group
            ]

        else:
            rows_n = 10

            similarities = [round(sim * 100, 1) for sim in distance_map.values()]
            grouped = sorted(set(int(s) for s in similarities), reverse=True)

            if len(grouped) >= rows_n:
                nth_group = grouped[rows_n - 1]
            else:
                nth_group = grouped[-1]

            valid_pks = [
                pk for pk, sim in distance_map.items()
                if int(sim * 100) >= nth_group
            ]


        if not valid_pks:
            return queryset.none()
        
        filtered_order = [pk for pk in original_order if pk in valid_pks]
        preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(filtered_order)])
        qs = queryset.filter(pk__in=filtered_order).order_by(preserved_order)

        for obj in qs:
            obj.dynamic_fields = {field.name: getattr(obj, field.name) for field in obj._meta.fields}
            obj.dynamic_fields['similarity'] = 1 - float(distance_map[obj.pk])

        return qs

    elif value:
        dropdown_fields = ('companies', 'itgc_categories', 'itgc_questions')
        dynamic_q = Q()
        for field in fields:
            if field in dropdown_fields:
                dropdown_value = DependentDropdown.objects.filter(title__icontains=value).values_list('id', flat=True).first()
                if dropdown_value:
                    dynamic_q |= Q(**{f'{field}__icontains': dropdown_value})
            else:
                dynamic_q |= Q(**{f'{field}__icontains': value})
        return queryset.filter(dynamic_q)

    return queryset


def finance_filter(request, queryset, fields):
    value = request.GET.get('search')
    
    if value:
        dynamic_q = Q()
        for field in fields:
            dynamic_q |= Q(**{f'{field}__icontains': value})
        return queryset.filter(dynamic_q)

    return queryset


def server_filter(parent):
    filter_string = {}
    filter_instance = ServerFilter.objects.filter(parent=parent)
    for filter_data in filter_instance:
        filter_string[f'{filter_data.key}__icontains'] = filter_data.value
    
    return filter_string


def user_filter(parent):
    filter_string = {}
    filter_instance = UserFilter.objects.filter(parent=parent)
    for filter_data in filter_instance:
        filter_string[f'{filter_data.key}__icontains'] = filter_data.value
    
    return filter_string


def software_assets_filter(fields=[], value=""):
    dynamic_q = Q()
    if value is not None:
        for field in fields:
            dynamic_q |= Q(**{f'{field}__icontains': value})
    
    return dynamic_q



def calculate_hash(self):
    fields = [field for field in self._meta.get_fields() if not field.is_relation]
    model_args = {}

    skip_fields = getattr(self, 'skip_fields', [])
    behave_like_string = getattr(self, 'behave_like_string', [])

    for field in fields:
        if field.name == 'ID' or field.name == 'id' or field.name in skip_fields:
            continue
        
        value = getattr(self, field.name)
        if value is not None:
            if field.name in behave_like_string:
                model_args[field.name] = str(value)
            else:
                model_args[field.name] = value

    hash_object = hashlib.sha256(json.dumps(model_args, sort_keys=True).encode())
    hashed = hash_object.hexdigest()

    return hashed

def get_log_entry(self):
    try:
        hashed = calculate_hash(self)
        return Log.objects.get(hash_value=hashed)
    except Log.DoesNotExist:
        return None  


def same_key_filter(filter_instance, return_count_filters=False):
    conditions = {}
    unique_filters = []
    count_filters = []
    query_conditions = Q()
    dropdown_fields = ('companies', 'itgc_categories', 'itgc_questions', )

    for filter_data in filter_instance:
        key = filter_data.field_name
        value = filter_data.value_start

        if key in reverse_map_field_names:
            key = reverse_map_field_names[key]

        if key not in conditions:
            conditions[key] = []

        if value:
            if filter_data.is_not:
                if key in dropdown_fields:
                    dropdown_value = DependentDropdown.objects.filter(title__icontains=value).values_list('id', flat=True).first()
                    if dropdown_value:
                        conditions[key].append(~Q(**{f"{key}__icontains": dropdown_value}))
                    else:
                        conditions[key].append(~Q(**{f"{key}__icontains": '-1'}))
                else:
                    conditions[key].append(~Q(**{f"{key}__icontains": value}))
            else:
                if key in dropdown_fields:
                    dropdown_value = DependentDropdown.objects.filter(title__icontains=value).values_list('id', flat=True).first()
                    if dropdown_value:
                        conditions[key].append(Q(**{f"{key}__icontains": dropdown_value}))
                    else:
                        conditions[key].append(Q(**{f"{key}__icontains": '-1'}))
                else:
                    conditions[key].append(Q(**{f"{key}__icontains": value}))
    
        
        # Handle combined filters
        if filter_data.is_null:
            query_conditions |= (Q(**{f"{key}__isnull": True}) | Q(**{f"{key}": ''}))
        if filter_data.is_not_null:
            query_conditions |= (~Q(**{f"{key}__isnull": True}) & ~Q(**{f"{key}": ''}))
        if filter_data.is_unique:
            unique_filters.append(key)
        if filter_data.is_count:
            unique_filters.append(key)
            count_filters.append(key)
            count_key = f"{key}-COUNT"
            count_filters.append(count_key)

    field_q_objects_list = []
    for key, q_objects in conditions.items():
        field_q_objects_list.append(Q(*q_objects, _connector=Q.OR))

    combined_q_objects = Q(*field_q_objects_list, _connector=Q.AND)

    if return_count_filters:
        return combined_q_objects, unique_filters, query_conditions, count_filters
    else:
        return combined_q_objects, unique_filters, query_conditions


def query_shoot_func(model, table):
    result = []
    if table.database:
        if table.database.db_type == DBType.mssql:
            result, row_count = mssql_database_connection(table.database, table.query)
            if result:
                result = result

        else:
            result, row_count = database_connection(table.database, table.query)
            if result:
                result = result
    else:
        with connection.cursor() as cursor:
            cursor.execute(table.query)
            result = cursor.fetchall()
    
    instances_to_create = []
    db_field_names = [field.name for field in model._meta.get_fields() if not field.is_relation]

    for row in result:
        field_values = dict(zip(db_field_names, row))

        if field_values.get('ID'):
            field_values.pop('ID')

        if field_values.get('id'):
            field_values.pop('id')

        if field_values.get('loader_instance'):
            field_values.pop('loader_instance')

        instances_to_create.append(model(**field_values))
    
    return instances_to_create

def get_model_fields(model_name, pre_column):
    model = apps.get_model('tables', model_name)
    fields = model._meta.get_fields()

    # Get field types from the model
    date_fields = getattr(model, 'date_fields_to_convert', [])
    integer_fields = getattr(model, 'integer_fields', [])
    float_fields = getattr(model, 'float_fields', [])

    field_data = []

    for field in fields:

        if field.is_relation:
            continue
        field_name = field.name

        if field_name in map_field_names:
            field_name = map_field_names[field_name]
        
        # Determine field type based on the arrays
        if field_name in date_fields:
            field_type = 'Date'
        elif field_name in integer_fields:
            field_type = 'Integer'
        elif field_name in float_fields:
            field_type = 'Float'
        else:
            field_type = 'Text'

        if field_name not in pre_column:
            field_data.append({
                'name': field_name,
                'type': field_type
            })
    
    return field_data


def unique_filter_func(field_names, table_name, loader_instance=None, primary_key="ID"):
    if 'mssql' not in settings.DATABASES['default']['ENGINE']:      
        temp_table_name = 'TEMPORARY temp_table'
    else:
        temp_table_name = '#temp_table'
    queries = []

    loader_instance_condition = f"WHERE loader_instance = " + str(loader_instance) if loader_instance is not None else ""

    for index, field_name in enumerate(field_names):
        if index == 0:
            query = f"""
                SELECT {primary_key} INTO {temp_table_name}
                FROM (
                    SELECT 
                        {primary_key},
                        ROW_NUMBER() OVER (PARTITION BY {field_name} ORDER BY {primary_key}) AS row_num
                    FROM {table_name}
                    {loader_instance_condition}
                ) AS subquery
                WHERE subquery.row_num = 1
            """
        else:
            query = f"""
                DELETE FROM {temp_table_name} WHERE {primary_key} NOT IN (
                    SELECT {primary_key}
                    FROM (
                        SELECT 
                            {primary_key},
                            ROW_NUMBER() OVER (PARTITION BY {field_name} ORDER BY {primary_key}) AS row_num
                        FROM {table_name}
                        {loader_instance_condition}
                    ) AS subquery
                    WHERE subquery.row_num = 1
                )
            """
        
        queries.append(query)

    raw_sql = "\n".join(queries)
    return raw_sql


# Reusable view

def get_user_id(request):
    if request.user.is_authenticated:
        return request.user.pk
    else:
        return -1

def user_filter_common_func(request, model_name, model_choice):
    model = apps.get_model('tables', model_name)

    field_type_map = {
        'date': getattr(model, 'date_fields_to_convert', []),
        'int': getattr(model, 'integer_fields', []),
        'float': getattr(model, 'float_fields', [])
    }

    def get_field_type(value):
        for f_type, fields in field_type_map.items():
            if value in fields:
                return getattr(FieldType, f_type.upper())
        return FieldType.TEXT

    def get_boolean_field(name, index):
        return request.POST.get(f'{name}_{index}') == 'true'

    existing_count_filter = SavedFilter.objects.filter(userID=request.user.id, parent=ModelChoices[model_choice], is_count=True).first()
    for key, value in request.POST.items():
        if key.startswith('field_name_') and value:
            index = key.split('_')[-1]
            field_name = value
            field_type = get_field_type(value)

            if field_type == FieldType.TEXT:
                value_start = request.POST.get(f'value_start_{index}') or ''
                value_end = request.POST.get(f'value_end_{index}') or ''
            else:
                value_start = request.POST.get(f'value_start_{index}') or None
                value_end = request.POST.get(f'value_end_{index}') or None

            is_not = get_boolean_field('is_not', index)
            is_null = get_boolean_field('is_null', index)
            is_not_null = get_boolean_field('is_not_null', index)
            is_unique = get_boolean_field('is_unique', index)
            is_count = get_boolean_field('is_count', index)

            filter_id = request.POST.get(f'filter_id_{index}')
            if filter_id in [None, '', 'null']:
                filter_id = None

            if is_count:
                if existing_count_filter and (not filter_id or str(existing_count_filter.id) != filter_id):
                    is_count = False

            filter_data = {
                'userID': request.user.id,
                'parent': ModelChoices[model_choice],
                'field_name': field_name,
                'field_type': field_type,
                'value_start': value_start,
                'value_end': value_end,
                'is_not': is_not,
                'is_null': is_null,
                'is_not_null': is_not_null,
                'is_unique': is_unique,
                'is_count': is_count
            }

            if filter_id:
                SavedFilter.objects.filter(pk=filter_id).update(**filter_data)
            else:
                SavedFilter.objects.create(**filter_data)


def create_page_items(request, model_choice):
    items = request.POST.get('items')
    page_items, created = PageItems.objects.update_or_create(
        userID=get_user_id(request),
        parent=ModelChoices[model_choice],
        defaults={'items_per_page':items}
    )


def create_hide_show_filter(request, model_choice):
    data_list = json.loads(request.body)

    for data in data_list:
        HideShowFilter.objects.update_or_create(
            userID=get_user_id(request),
            parent=ModelChoices[model_choice],
            key=data.get('key'),
            defaults={'value': data.get('value')}
        )

    response_data = {'message': 'Filters updated successfully'}
    return response_data


def common_snapshot_filter(request, table_name):
    latest_snapshot = ''
    summary = None
    snapshot_filter = {}
    snapshots = {}
    try:
        content_type = ContentType.objects.get(model=table_name)
        snapshots = InstantUpload.objects.filter(content_type=content_type).order_by('-created_at')
        snapshot = request.GET.get('snapshot')
        latest_snapshot = snapshots.latest('created_at')
        
        if latest_snapshot and not snapshot == 'all':
            snapshot_filter['loader_instance'] = latest_snapshot.pk
        
        if snapshot and not snapshot == 'all':
            summary = InstantUpload.objects.get(id=snapshot)
            snapshot_filter['loader_instance'] = summary.pk

    except:
        pass

    return latest_snapshot, summary, snapshot_filter, snapshots


def common_date_filter(date_filters, return_count_filters=False):
    date_string = {}
    unique_filters = []
    count_filters = []
    query_conditions = Q()

    for date_filter in date_filters:
        from_date = ''
        to_date = ''
    
        if date_filter.value_start:
            from_date = datetime.datetime.strptime(date_filter.value_start, "%Y-%m-%d").timestamp()
        if date_filter.value_end:
            end_date = datetime.datetime.strptime(date_filter.value_end, "%Y-%m-%d") + timezone.timedelta(days=1)
            to_date = end_date.timestamp()

        if date_filter.is_not:
            if from_date and to_date:
                query_conditions &= ~Q(**{f"{date_filter.field_name}__range": [from_date, to_date]})
            elif from_date:
                query_conditions &= ~Q(**{f"{date_filter.field_name}__gte": from_date})
            elif to_date:
                query_conditions &= ~Q(**{f"{date_filter.field_name}__lte": to_date})
        else:
            if from_date and to_date:
                date_string[f'{date_filter.field_name}__range'] = [from_date, to_date]
            elif from_date:
                date_string[f'{date_filter.field_name}__gte'] = from_date
            elif to_date:
                date_string[f'{date_filter.field_name}__lte'] = to_date

        # Handle combined filters
        if date_filter.is_null:
            query_conditions |= (Q(**{f"{date_filter.field_name}__isnull": True}) | Q(**{f"{date_filter.field_name}": None}))
        if date_filter.is_not_null:
            query_conditions |= (~Q(**{f"{date_filter.field_name}__isnull": True}) & ~Q(**{f"{date_filter.field_name}": None}))
        if date_filter.is_unique:
            unique_filters.append(date_filter.field_name)
        if date_filter.is_count:
            unique_filters.append(date_filter.field_name)
            count_filters.append(date_filter.field_name)
            count_key = f"{date_filter.field_name}-COUNT"
            count_filters.append(count_key)

    if return_count_filters:
        return date_string, unique_filters, query_conditions, count_filters
    else:
        return date_string, unique_filters, query_conditions


def common_integer_filter(int_filters, return_count_filters=False):
    int_string = {}
    unique_filters = []
    count_filters = []
    query_conditions = Q()

    for int_value in int_filters:
        if int_value.is_not:
            if int_value.value_start is not None and int_value.value_end is not None:
                query_conditions &= ~Q(**{f'{int_value.field_name}__range': [int_value.value_start, int_value.value_end]})
            elif int_value.value_start is not None:
                query_conditions &= ~Q(**{f'{int_value.field_name}__gte': int_value.value_start})
            elif int_value.value_end is not None:
                query_conditions &= ~Q(**{f'{int_value.field_name}__lte': int_value.value_end})
        else:
            if int_value.value_start is not None and int_value.value_end is not None:
                int_string[f'{int_value.field_name}__range'] = [int_value.value_start, int_value.value_end]
            elif int_value.value_start is not None:
                int_string[f'{int_value.field_name}__gte'] = int_value.value_start
            elif int_value.value_end is not None:
                int_string[f'{int_value.field_name}__lte'] = int_value.value_end

        if int_value.is_null:
            query_conditions |= (Q(**{f"{int_value.field_name}__isnull": True}) | Q(**{f"{int_value.field_name}": None}))
        if int_value.is_not_null:
            query_conditions |= (~Q(**{f"{int_value.field_name}__isnull": True}) & ~Q(**{f"{int_value.field_name}": None}))
        if int_value.is_unique:
            unique_filters.append(int_value.field_name)
        if int_value.is_count:
            unique_filters.append(int_value.field_name)
            count_filters.append(int_value.field_name)
            count_key = f"{int_value.field_name}-COUNT"
            count_filters.append(count_key)

    if return_count_filters:
        return int_string, unique_filters, query_conditions, count_filters
    else:
        return int_string, unique_filters, query_conditions


def common_float_filter(float_filters, return_count_filters=False):
    float_string = {}
    unique_filters = []
    count_filters = []
    query_conditions = Q()

    for float_value in float_filters:
        if float_value.is_not:
            if float_value.value_start is not None and float_value.value_end is not None:
                query_conditions &= ~Q(**{f'{float_value.field_name}__range': [float_value.value_start, float_value.value_end]})
            elif float_value.value_start is not None:
                query_conditions &= ~Q(**{f'{float_value.field_name}__gte': float_value.value_start})
            elif float_value.value_end is not None:
                query_conditions &= ~Q(**{f'{float_value.field_name}__lte': float_value.value_end})
        else:
            if float_value.value_start is not None and float_value.value_end is not None:
                float_string[f'{float_value.field_name}__range'] = [float_value.value_start, float_value.value_end]
            elif float_value.value_start is not None:
                float_string[f'{float_value.field_name}__gte'] = float_value.value_start
            elif float_value.value_end is not None:
                float_string[f'{float_value.field_name}__lte'] = float_value.value_end

        # Handle combined filters
        if float_value.is_null:
            query_conditions |= (Q(**{f"{float_value.field_name}__isnull": True}) | Q(**{f"{float_value.field_name}": None}))
        if float_value.is_not_null:
            query_conditions |= (~Q(**{f"{float_value.field_name}__isnull": True}) & ~Q(**{f"{float_value.field_name}": None}))
        if float_value.is_unique:
            unique_filters.append(float_value.field_name)
        if float_value.is_count:
            unique_filters.append(float_value.field_name)
            count_filters.append(float_value.field_name)
            count_key = f"{float_value.field_name}-COUNT"
            count_filters.append(count_key)

    if return_count_filters:
        return float_string, unique_filters, query_conditions, count_filters
    else:
        return float_string, unique_filters, query_conditions


def common_unique_filter(request, unique_filter, queryset, snapshot_filter, table_name):
    if 'mssql' not in settings.DATABASES['default']['ENGINE']:
        for field_name in unique_filter:
            
            try:
                queryset = queryset.annotate(
                    row_num=Window(
                        expression=RowNumber(),
                        partition_by=[F(field_name)],
                        order_by=F('ID').asc()
                    )
                ).filter(row_num=1)
            except:
                queryset = queryset.annotate(
                    row_num=Window(
                        expression=RowNumber(),
                        partition_by=[F(field_name)],
                        order_by=F('id').asc()
                    )
                ).filter(row_num=1)
    else:
        loader_instance = request.GET.get('snapshot') if request.GET.get('snapshot') and request.GET.get('snapshot') != 'all' else snapshot_filter['loader_instance'] if snapshot_filter else None
        raw_sql = unique_filter_func(unique_filter, table_name, loader_instance)
        with connection.cursor() as cursor:
            cursor.execute(raw_sql)

        with connection.cursor() as cursor:
            cursor.execute(f"SELECT ID FROM #temp_table")
            unique_ids = [row[0] for row in cursor.fetchall()]

        queryset = queryset.filter(pk__in=unique_ids)
    
    return queryset


def common_count_filter(count_filters, base_queryset, queryset, db_field_names, exp_fields=[], export=False, total=False):
    fields = [field.replace('-COUNT', '') for field in count_filters]
    count_field = fields[-1]

    model = queryset.model

    for field in fields:
        field_type = model._meta.get_field(field)
        safe_field = f"{field}_safe"

        if isinstance(field_type, (DateField, DateTimeField)):
            default = Value(datetime.date(1900, 1, 1), output_field=field_type)
        elif isinstance(field_type, (IntegerField, BigIntegerField)):
            default = Value(-1, output_field=field_type)
        else:
            default = Value('__NULL__', output_field=CharField())

        annotation = {
            safe_field: Case(
                When(**{f"{field}__isnull": True}, then=default),
                default=F(field),
                output_field=field_type
            )
        }
        queryset = queryset.annotate(**annotation)
        base_queryset = base_queryset.annotate(**annotation)

    safe_fields = [f"{f}_safe" for f in fields]

    subquery = (
        base_queryset
        .filter(**{f: OuterRef(f) for f in safe_fields})
        .values(*safe_fields)
        .annotate(count=Count('pk'))
        .values('count')[:1]
    )

    queryset = queryset.annotate(count=Subquery(subquery))

    def insert_count(fields_list):
        if count_field in fields_list and 'count' not in fields_list:
            fields_list.insert(fields_list.index(count_field) + 1, 'count')

    if not export:
        insert_count(db_field_names)
    else:
        insert_count(exp_fields)

    total_count = queryset.count()

    if total:
        return queryset, total_count
    else:
        return queryset


def get_model(name: str = None):
    if name is None:
        current_model = VectorModel.objects.filter(current=True).first()
        if current_model:
            name = current_model.name
        else:
            name = "BAAI/bge-large-en-v1.5"
    return SentenceTransformer(name)


def to_sql_vector(text: str, model: SentenceTransformer = None):
    if model is None:
        model = get_model()
    vec = model.encode([text], normalize_embeddings=True)[0].astype(np.float32)
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
