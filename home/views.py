import subprocess
import time, re, os
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from apps.tables.utils import device_filter
from django.conf import settings
from apps.tables.models import ( Favorite, UserFilter, 
	PageItems, HideShowFilter, ModelChoices, 
	DateRangeFilter, TableDropdownItem, 
	TableDropdownSubItem, DependentDropdown
)
from home.models import JoinModel
from apps.common.models import Sidebar
from django.http import JsonResponse
from datetime import datetime
from django.utils import timezone
from loader.models import (
    InstantUpload, TypeChoices, 
    SAPApi, DynamicQuery, VectorModel, 
    json_to_vector, is_pgvector_enabled, hash_json
)
from loader.views import update_model_choices_file, run_migrations, model_exists
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.apps import apps
from django.db import models, connections
from django.contrib import messages
from celery import shared_task, chain
from django.urls import reverse
from django.db import connection, transaction
from apps.view_builder.views import update_template_tags
from django.contrib.auth.models import Group
from loader.admin import get_selected_models
from django.conf import settings

try:
    from pgvector.django import VectorField
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False

def get_user_id(request):
	if request.user.is_authenticated:
		return request.user.pk
	else:
		return -1


# def get_device_data(request):
# 	snapshot_filter = {}
# 	content_type = ContentType.objects.get(model='controladuser')
# 	snapshots = InstantUpload.objects.filter(content_type=content_type).order_by('-created_at')
# 	latest_snapshot = snapshots.latest('created_at')
# 	snapshot_filter['loader_instance'] = latest_snapshot.pk
# 	devices = ControlADUser.objects.filter(**snapshot_filter).filter(
# 		Q(AD_Enabled_Status='TRUE') | Q(AD_Enabled_Status='True')
# 	)
# 	chart_data = {}
# 	consolidated_chart_data = []
# 	for device in devices:
# 		timestamp = device.AD_Account_Created
# 		dt_object = datetime.utcfromtimestamp(timestamp)
# 		month = dt_object.month
# 		if month not in chart_data:
# 			chart_data[month] = {}

# 		if 'count' not in chart_data[month]:
# 			chart_data[month]['count'] = 1
# 			chart_data[month]['date'] = device.AD_Account_Created
# 		else:
# 			chart_data[month]['count'] += 1


# 	for month, data in chart_data.items():
# 		consolidated_chart_data.append({
# 			'x': month,
# 			'y': data['count'],
# 			'date': data['date'],
# 			'deviceType': 'All',
# 		})

# 	return JsonResponse({'consolidatedChartData': consolidated_chart_data}, safe=False)


def index(request):
	# db_field_names = [field.name for field in Devices._meta.get_fields() if not field.is_relation if not '_Q_' in field.name]
	# field_names = []
	# for field_name in db_field_names:
	# 	fields, created = HideShowFilter.objects.get_or_create(key=field_name, userID=get_user_id(request), parent=ModelChoices.DEVICES)
	# 	field_names.append(fields)

	# page_items = PageItems.objects.filter(userID=get_user_id(request), parent=ModelChoices.DEVICES).last()
	# items = 25
	# if page_items:
	# 	items = page_items.items_per_page

	# filter_string = {}
	# Pre-FILTERS
	#filter_string['MatchedTitle__icontains'] = 'hdx'

	# filter_instance = UserFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.DEVICES)
	# for filter_data in filter_instance:
	# 	filter_string[f'{filter_data.key}__icontains'] = filter_data.value
	

	# date_filter_instance = DateRangeFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.DEVICES)
	# for date_filter in date_filter_instance:
	# 	from_date = datetime.strptime(date_filter.from_date.strftime('%Y-%m-%d'), "%Y-%m-%d").timestamp()
	# 	to_date = datetime.strptime((date_filter.to_date + timezone.timedelta(days=1)).strftime('%Y-%m-%d'), "%Y-%m-%d").timestamp()
	# 	filter_string[f'{date_filter.key}__range'] = [from_date, to_date]


	# order_by = request.GET.get('order_by', 'ID')
	# queryset = Devices.objects.filter(**filter_string).order_by(order_by)

	# device_list = device_filter(request, queryset, db_field_names)
	# form = DeviceForm()

	# page = request.GET.get('page', 1)
	# paginator = Paginator(device_list, items)

	# favorites = Favorite.objects.filter(user=request.user)

	
	# try:
	# 	devices = paginator.page(page)
	# except PageNotAnInteger:
	# 	return redirect('list_of_devices')
	# except EmptyPage:
	# 	return redirect('list_of_devices') 

	context = {
		'segment'  : 'dashboard',
		#'form'     : form,
		#'devices' : devices,
		#'db_field_names': db_field_names,
		#'favorites': favorites
	}

	return render(request, "dashboard/index.html", context)


def starter(request):

	context = {}
	return render(request, "pages/grc_starter.html", context)


# table dropdown

def create_table_dropdown(request):
	dropdown_qs = TableDropdownItem.objects.all()
	if request.method == 'POST':
		if item := request.POST.get('item'):
			dropdown, created = TableDropdownItem.objects.get_or_create(item=item)
			if created:
				dropdown.created_at = timezone.now()
				dropdown.updated_at = timezone.now()
				dropdown.save()
			
			return redirect(request.META.get('HTTP_REFERER'))
	

	page = request.GET.get('page', 1)
	items = 15
	paginator = Paginator(dropdown_qs, items)
	
	try:
		dropdowns = paginator.page(page)
	except PageNotAnInteger:
		return redirect('create_table_dropdown')
	except EmptyPage:
		return redirect('create_table_dropdown') 

	context = {
		'dropdowns': dropdowns,
		'parent': 'admin',
		'segment': 'table_dropdown'
	}
	return render(request, 'pages/dropdowns/create-items.html', context)


def update_table_dropdown(request, id):
	dropdown = TableDropdownItem.objects.get(pk=id)
	if request.method == 'POST':
		if item := request.POST.get('item'):
			dropdown.item = item
			dropdown.updated_at = timezone.now()
			dropdown.save()

		return redirect(request.META.get('HTTP_REFERER'))
	

def delete_table_dropdown(request, id):
	dropdown = TableDropdownItem.objects.get(pk=id)
	dropdown.delete()

	return redirect(request.META.get('HTTP_REFERER'))


def create_sub_items(request, id):
	item = TableDropdownItem.objects.get(pk=id)
	sub_items = TableDropdownSubItem.objects.filter(item=item)
	if request.method == 'POST':
		if sub_item := request.POST.get('subitem'):
			TableDropdownSubItem.objects.create(
				item=item, 
				subitem=sub_item,
				created_at=timezone.now(),
				updated_at=timezone.now()
			)

		return redirect(request.META.get('HTTP_REFERER'))
	
	context = {
		'item': item,
		'sub_items': sub_items
	}
	return render(request, 'pages/dropdowns/create-sub-items.html', context)


def update_sub_item(request, id):
	sub_item = TableDropdownSubItem.objects.get(pk=id)
	if request.method == 'POST':
		if subitem := request.POST.get('subitem'):
			sub_item.subitem = subitem
			sub_item.updated_at = timezone.now()
			sub_item.save()

		return redirect(request.META.get('HTTP_REFERER'))
	
def delete_sub_item(request, id):
	sub_item = TableDropdownSubItem.objects.get(pk=id)
	sub_item.delete()
	return redirect(request.META.get('HTTP_REFERER'))


# Dependent Dropdown

def create_dependent_dropdown(request):
	dropdown_qs = DependentDropdown.objects.filter(featured=True)
	if request.method == 'POST':
		if title := request.POST.get('title'):
			dropdown, created = DependentDropdown.objects.get_or_create(title=title)
			if created:
				dropdown.featured = True
				dropdown.created_at = timezone.now()
				dropdown.updated_at = timezone.now()
				dropdown.save()
			
			return redirect(request.META.get('HTTP_REFERER'))

	page = request.GET.get('page', 1)
	items = 15
	paginator = Paginator(dropdown_qs, items)
	
	try:
		dropdowns = paginator.page(page)
	except PageNotAnInteger:
		return redirect('create_dependent_dropdown')
	except EmptyPage:
		return redirect('create_dependent_dropdown') 

	context = {
		'dropdowns': dropdowns,
		'items': dropdown_qs,
		'parent': 'admin',
		'segment': 'dependent_dropdown'
	}
	return render(request, 'pages/dependent/create-items.html', context)

def update_dependent_dropdown(request, id):
	dropdown = DependentDropdown.objects.get(pk=id)
	if request.method == 'POST':
		if title := request.POST.get('title'):
			if not DependentDropdown.objects.filter(parent=dropdown, title=title).exists():
				dropdown.title = title
				dropdown.updated_at = timezone.now()
				dropdown.save()
			else:
				messages.error(request, 'Dropdown with this title already exists')

		return redirect(request.META.get('HTTP_REFERER'))


def delete_dependent_dropdown(request, id):
	dropdown = DependentDropdown.objects.get(pk=id)
	dropdown.delete()

	return redirect(request.META.get('HTTP_REFERER'))


def create_dependent_sub_items(request, id):
	item = DependentDropdown.objects.get(pk=id)
	sub_items = DependentDropdown.objects.filter(parent=item, featured=False)
	if request.method == 'POST':
		if title := request.POST.get('title'):
			dropdown, created = DependentDropdown.objects.get_or_create(title=title, parent=item)
			if created:
				dropdown.created_at = timezone.now()
				dropdown.updated_at = timezone.now()
				dropdown.save()
		return redirect(request.META.get('HTTP_REFERER'))
	
	context = {
		'item': item,
		'sub_items': sub_items
	}
	return render(request, 'pages/dependent/create-sub-items.html', context)



# Join







from django.conf import settings
from celery.result import AsyncResult



def view_function(request_data, selected_model):
    parent_name = get_object_or_404(Sidebar, id=request_data.get('parent_name'))
    if selected_model:
        app_name, model_name = selected_model.split('.')
        model_class = apps.get_model(app_name, model_name)

    update_template_tags(model_class)

    fav_name = request_data.get('fav_name')
    view_name = fav_name.replace(' ', '_').lower()
    view_name = re.sub(r'[^a-zA-Z0-9_]', '', view_name)

    model_choice = '_'.join(re.findall(r'[A-Z]+(?![a-z])|[A-Z][a-z]*|\d+', model_name)).upper()
    db_table = model_class._meta.db_table.split('_', 1)[-1]

    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(settings.BASE_DIR)
    template_path = os.path.join(base_dir, 'apps', 'view_builder', 'control', 'base_control_view.txt')
    with open(template_path, 'r') as file:
        template_content = file.read()

    
    updated_content = template_content

    readonly_fields = request_data.get('ro_fields') or []
    readonly_fields = list(set(readonly_fields + ['ID', 'loader_instance', 'json_data', 'hash_data', 'fts']))
    if readonly_fields:
        readonly_fields_str = ', '.join([f"'{field}'" for field in readonly_fields])
        updated_content = updated_content.replace(
            'read_only_fields = ()',
            f"read_only_fields = ({readonly_fields_str},)"
        )

    pre_columns = request_data.get('precol_fields') or []
    pre_columns = list(set(pre_columns + ['ID', 'loader_instance', 'json_data', 'hash_data', 'fts']))
    if pre_columns:
        pre_columns_str = ', '.join([f"'{field}'" for field in pre_columns])
        updated_content = updated_content.replace(
            'pre_column = ()',
            f"pre_column = ({pre_columns_str},)"
        )

    compulsory_fields = request_data.get('compulsory_fields') or []
    if compulsory_fields:
        compulsory_fields_str = ', '.join([f"'{field}'" for field in compulsory_fields])
        updated_content = updated_content.replace(
            'compulsory_fields = ()',
            f"compulsory_fields = ({compulsory_fields_str},)"
        )

    parent = parent_name.segment if parent_name.segment else parent_name.name

    updated_content = updated_content.replace('VIEW_NAME', view_name).replace('MODEL_CHOICE', model_choice).replace('MODEL_NAME', model_name).replace('DB_TABLE', db_table).replace('PARENT_NAME', parent).replace('FAV_NAME', fav_name)


    view_dir_path = os.path.join(settings.VIEW_PATH, view_name)
    if not os.path.exists(view_dir_path):
        os.makedirs(view_dir_path)

    output_file_path = os.path.join(view_dir_path, f'{view_name}_views.py')
    with open(output_file_path, 'w') as output_file:
        output_file.write(updated_content)


def url_function(request_data):
    fav_name = request_data.get('fav_name')
    view_name = fav_name.replace(' ', '_').lower()
    view_name = re.sub(r'[^a-zA-Z0-9_]', '', view_name)

    base_dir = os.path.join(settings.BASE_DIR)
    template_path = os.path.join(base_dir, 'apps', 'view_builder', 'control', 'base_control_urls.txt')

    with open(template_path, 'r') as file:
        template_content = file.read()

    updated_content = template_content.replace('VIEW_NAME', view_name).replace('URL_NAME', view_name.replace('_', '-'))

    url_dir_path = os.path.join(settings.VIEW_PATH, view_name)
    if not os.path.exists(url_dir_path):
        os.makedirs(url_dir_path)

    output_file_path = os.path.join(url_dir_path, f'{view_name}_urls.py')
    with open(output_file_path, 'w') as output_file:
        output_file.write(updated_content)
    

    urls_path = os.path.join(getattr(settings, 'URL_PATH'), 'urls.py')
    include_statement = f"\n    path('tables/', include('apps.tables.{view_name}.{view_name}_urls')),\n"

    with open(urls_path, 'r') as urls_file:
        existing_urls_content = urls_file.read()

    if include_statement.strip() not in existing_urls_content:
        if 'urlpatterns = [' in existing_urls_content:
            last_closing_bracket_pos = existing_urls_content.rfind(']')
            
            new_urls_content = (
                existing_urls_content[:last_closing_bracket_pos]
                + f"{include_statement}"
                + existing_urls_content[last_closing_bracket_pos:]
            )

            with open(urls_path, 'w') as urls_file:
                urls_file.write(new_urls_content)


def template_function(request_data, selected_model):
    if selected_model:
        app_name, model_name = selected_model.split('.')
        model_class = apps.get_model(app_name, model_name)

    fav_name = request_data.get('fav_name')
    view_name = fav_name.replace(' ', '_').lower()
    view_name = re.sub(r'[^a-zA-Z0-9_]', '', view_name)

    model_choice = '_'.join(re.findall(r'[A-Z]+(?![a-z])|[A-Z][a-z]*|\d+', model_name)).upper()

    base_dir = os.path.join(settings.BASE_DIR)
    template_path = os.path.join(base_dir, 'apps', 'view_builder', 'control', 'base_control_template.txt')

    with open(template_path, 'r') as file:
        template_content = file.read()

    updated_content = template_content.replace('VIEW_NAME', view_name).replace('MODEL_CHOICE', model_choice).replace('MODEL_NAME', model_name).replace('FAV_NAME', fav_name).replace('URL_NAME', view_name.replace('_', '-'))

    output_file_path = os.path.join(settings.TEMPLATE_PATH, f'{view_name}.html')
    with open(output_file_path, 'w') as output_file:
        output_file.write(updated_content)


def table_exists(table_name):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, [table_name])
        return cursor.fetchone()[0]

@shared_task
def run_local_migrations(result):
    try:
        print("Starting migrations...")
        subprocess.run('python manage.py makemigrations --noinput', shell=True, check=True)
        print("Makemigrations completed.")
        subprocess.run('python manage.py migrate --noinput', shell=True, check=True)
        print("Migrate completed.")
        result['status'] = 'completed'
        return result
    except subprocess.CalledProcessError as e:
        result['status'] = 'error'
        result['message'] = str(e)
        raise

@shared_task
def generate_views_urls_templates(result):
    try:
        if result['status'] == 'completed':
            request_data = result['request_data']
            selected_model = f"tables.{JoinModel.objects.get(id=result['join_model_id']).model_name}"
            view_function(request_data, selected_model)
            url_function(request_data)
            template_function(request_data, selected_model)
            print(f"Views, URLs, and templates for {selected_model} created successfully!")
        else:
            print("Failed to generate views, URLs, and templates due to model generation error.")
        return result
    except Exception as e:
        result['status'] = 'error'
        result['message'] = str(e)

@shared_task
def generate_model_and_migrate(join_model_id, request_data):
    try:
        join_model = JoinModel.objects.get(id=join_model_id)
        models_file_path = settings.MODELS_FILE_PATH

        model_name = join_model.model_name
        base_model_class = join_model.base_model.model_class()

        delta_model_class = None
        delta_fields = []
        delta_field_definitions = ""
        
        has_delta_model = bool(join_model.delta_model)
        if has_delta_model:
            delta_model_class = join_model.delta_model.model_class()
            delta_fields = join_model.delta_fields.split(',') if join_model.delta_fields else []

        base_fields = join_model.base_fields.split(',') if join_model.base_fields else []

        special_categories = [
            "date_fields_to_convert", 
            "integer_fields", 
            "float_fields", 
            "encrypted_fields", 
            "unix_dates", 
            "ad_unix_dates"
        ]
        special_field_dict = {category: set() for category in special_categories}

        def get_field_definition(model_class, field_name, prefix=""):
            field = model_class._meta.get_field(field_name)
            field_type = field.get_internal_type()

            for category in special_categories:
                if hasattr(model_class, category) and field_name in getattr(model_class, category):
                    special_field_dict[category].add(f"{prefix}{field_name}")

            field_name_with_prefix = f"{prefix}{field_name}"
            if isinstance(field, models.ForeignKey):
                return f"    {field_name_with_prefix} = models.ForeignKey('{field.related_model._meta.label}', on_delete=models.CASCADE)"
            elif isinstance(field, models.BigIntegerField):
                return f"    {field_name_with_prefix} = models.BigIntegerField(null=True, blank=True)"
            elif isinstance(field, models.IntegerField):
                return f"    {field_name_with_prefix} = models.IntegerField(null=True, blank=True)"
            elif isinstance(field, models.BooleanField):
                return f"    {field_name_with_prefix} = models.BooleanField(null=True, blank=True)"
            elif isinstance(field, models.DateTimeField):
                return f"    {field_name_with_prefix} = models.DateTimeField(null=True, blank=True)"
            elif isinstance(field, models.DateField):
                return f"    {field_name_with_prefix} = models.DateField(null=True, blank=True)"
            elif isinstance(field, models.FloatField):
                return f"    {field_name_with_prefix} = models.FloatField(null=True, blank=True)"
            elif isinstance(field, models.TextField):
                return f"    {field_name_with_prefix} = models.TextField(null=True, blank=True)"
            else:
                return f"    {field_name_with_prefix} = models.CharField(max_length=255, null=True, blank=True)"

        base_field_definitions = "\n".join([get_field_definition(base_model_class, field) for field in base_fields])
        if has_delta_model:
            delta_field_definitions = "\n".join([get_field_definition(delta_model_class, field, prefix="d_") for field in delta_fields])

        special_field_definitions = "\n".join([
            f"    {category} = {list(special_field_dict[category])}" for category in special_categories
        ])

        comparison_fields = ""
        if has_delta_model:
            comparison_fields = """
    both = models.IntegerField(null=True, blank=True)
    base = models.IntegerField(null=True, blank=True)
    delta = models.IntegerField(null=True, blank=True)
"""

        if is_pgvector_enabled():
            dim = get_current_vector_dimension()
            hash_data_field = f"    hash_data = VectorField(dimensions={dim}, null=True, blank=True)\n"
        else:
            hash_data_field = "    hash_data = models.TextField(null=True, blank=True)\n"

        model_code = f"""\n
class {model_name}(models.Model):
    ID = models.AutoField(primary_key=True)
{base_field_definitions}
{delta_field_definitions if has_delta_model else ''}
{comparison_fields}
    loader_instance = models.IntegerField(null=True, blank=True)
    json_data = models.JSONField(null=True, blank=True)
{hash_data_field}
    join_model_instance = {join_model.pk}  # Do not change this value
{special_field_definitions}
"""

        with open(models_file_path, "r") as f:
            original_content = f.read()

        with transaction.atomic():
            with open(models_file_path, "a") as f:
                f.write(model_code)
            update_model_choices_file(model_name)
            print("Model code added successfully!")

            task_chain = chain(
                run_local_migrations.s({'status': 'pending', 'join_model_id': join_model.id, 'request_data': request_data}),
                generate_views_urls_templates.s()
            )
            result = task_chain.apply_async()
            task_id = result.id

            return {
                'status': 'pending',
                'task_id': task_id,
                'message': 'Model creation in progress. Please wait...'
            }

    except Exception as e:
        print(f"Error encountered: {e}")
        with open(models_file_path, "w") as f:
            f.write(original_content)
        print(f"Failed to add Model {model_name}!")
        return {
            'status': 'error',
            'message': str(e)
        }

def join_models(request):
    if request.method == 'POST':
        join_model_name = request.POST.get('join_model_name')
        base_model_name = request.POST.get('base_model') 
        delta_model_name = request.POST.get('delta_model', '')
        base_fields = request.POST.getlist('base_model_fields', [])
        delta_fields = request.POST.getlist('delta_model_fields', [])
        base_f_key_fields = request.POST.getlist('base_foreign_key_fields', [])
        delta_f_key_fields = request.POST.getlist('delta_foreign_key_fields', [])
        join_method = request.POST.get('join_method')
        similarity_threshold = request.POST.get('similarity_threshold')
        split_char = request.POST.get('split_char')
        word_position = request.POST.get('word_position')
        split_space = request.POST.get('split_space') == 'on'

        jaro_winkler = request.POST.get('jaro_winkler') == 'on'
        levenshtein = request.POST.get('levenshtein') == 'on'
        token_set_ratio = request.POST.get('token_set_ratio') == 'on'
        phonetic = request.POST.get('phonetic') == 'on'
        fuzzy_wuzzy = request.POST.get('fuzzy_wuzzy') == 'on'

        py_function = request.POST.get('py_function')
        c_percent = request.POST.get('c_percent')

        left_split_char = request.POST.get('left_split_char')
        email_pre_char = request.POST.get('pre_char_email')
        email_post_char = request.POST.get('post_char_email')

        if table_exists(f'tables_{join_model_name.lower()}'):
            return JsonResponse({
                'status': 'error',
                'message': f'Table for model "{join_model_name}" already exists in the database.'
            })

        if JoinModel.objects.filter(model_name=join_model_name).exists():
            return JsonResponse({
                'status': 'error',
                'message': f'Model with name "{join_model_name}" already exists.'
            })

        base_model_parts = base_model_name.split('.')
        base_model_content_type = ContentType.objects.get(app_label=base_model_parts[0], model=base_model_parts[1].lower().replace('_', ''))
        
        delta_model_content_type = None
        if delta_model_name:
            delta_model_parts = delta_model_name.split('.')
            delta_model_content_type = ContentType.objects.get(app_label=delta_model_parts[0], model=delta_model_parts[1].lower().replace('_', ''))

        try:
            join_model = JoinModel.objects.create(
                model_name=join_model_name,
                base_model=base_model_content_type,
                delta_model=delta_model_content_type,
                base_fields=",".join(base_fields) if base_fields else "",
                delta_fields=",".join(delta_fields) if delta_fields else "",
                base_f_key_fields=",".join(base_f_key_fields) if base_f_key_fields else "",
                delta_f_key_fields=",".join(delta_f_key_fields) if delta_f_key_fields else "",
                join_method=join_method,
                similarity_threshold=similarity_threshold,
                split_character=split_char,
                split_by_space=split_space,
                match_word_position=word_position,
                jaro_winkler=jaro_winkler,
                levenshtein=levenshtein,
                token_set_ratio=token_set_ratio,
                phonetic=phonetic,
                fuzzy_wuzzy=fuzzy_wuzzy,
                python_function=py_function,
                c_similarity_threshold=c_percent,
                left_split_char=left_split_char,
                email_pre_char=email_pre_char,
                email_post_char=email_post_char
            )
            result = generate_model_and_migrate.apply_async(args=[join_model.id, request.POST.dict()])
            task_id = result.id

            fav_name = request.POST.get('fav_name')
            view_name = fav_name.replace(' ', '_').lower()
            view_name = re.sub(r'[^a-zA-Z0-9_]', '', view_name)

            sidebar_group = get_object_or_404(Group, name=request.POST.get('group_name'))
            sidebar_parent = get_object_or_404(Sidebar, id=request.POST.get('parent_name'))
            Sidebar.objects.create(
                group=sidebar_group,
                parent=sidebar_parent,
                name=fav_name,
                segment=view_name,
                url_name=view_name
            )

            return JsonResponse({
                'status': 'pending',
                'task_id': task_id,
                'view_name': view_name,
                'message': 'Model creation in progress. Please wait...'             
            })

        except Exception as e:
            return redirect(request.META.get('HTTP_REFERER'))

    loader_model_apps = ['tables']
    selected_models = get_selected_models()
    model_names = {}
    for app_name in loader_model_apps:
        app_config = apps.get_app_config(app_name)
        models = [model.__name__ for model in app_config.get_models()]

        filtered_models = sorted([model for model in models if f"{app_name}.{model}" not in selected_models])
        
        if filtered_models:
            model_names[app_name] = filtered_models

    sidebars = Sidebar.objects.filter(is_active=True, parent__isnull=True).values('id', 'name')
    groups = Group.objects.all()

    context = {
        'model_names': model_names,
        'sidebars': sidebars,
        'groups': groups,
        'segment': 'join_models',
        'parent' : 'home'
    }

    return render(request, 'pages/join_models.html', context)


def check_task_status(request):
    task_id = request.GET.get("task_id")

    if not task_id:
        return JsonResponse({"status": "error", "message": "Task ID is missing"})

    task_result = AsyncResult(task_id)

    if task_result.state == "SUCCESS":
        return JsonResponse({"status": "completed", "redirect_url": "/"})
    elif task_result.state in ["PENDING", "STARTED"]:
        return JsonResponse({"status": "pending"})
    elif task_result.state == "FAILURE":
        return JsonResponse({"status": "error", "message": str(task_result.result)})
    else:
        return JsonResponse({"status": "error", "message": "Unknown task state"})
	

def check_model_exists(request):
    model_name = request.GET.get('model_name')
    loader_model_apps = settings.LOADER_MODEL_APPS
    
    for app_name in loader_model_apps:
        if model_name in [model.__name__ for model in apps.get_app_config(app_name).get_models()]:
            return JsonResponse({'exists': True})
    
    return JsonResponse({'exists': False})


from home.models import IPE, PyFunction
from urllib.parse import urlparse
from rapidfuzz.fuzz import ratio, token_set_ratio, WRatio
from fuzzywuzzy import fuzz
import jellyfish

# def load_data_to_join_model(request, model_name, pk):
#     if request.method == 'POST':
#         method = request.POST.get('method')
#         percent = request.POST.get('percent')

#         c_full_word_match = request.POST.get('c_full_word_match') == 'on'

#         py_function = request.POST.get('py_function')
#         c_percent = request.POST.get('c_percent')
#         fields_to_pass = request.POST.getlist('fields_to_pass')

#         split_char = request.POST.get('split_char')
#         word_position = request.POST.get('word_position')
#         split_space = request.POST.get('split_space') == 'on'
#         s_full_word_match = request.POST.get('s_full_word_match') == 'on'

#         pre_char = request.POST.get('pre_char')
#         post_char = request.POST.get('post_char')
#         pp_full_word_match = request.POST.get('pp_full_word_match') == 'on'

#         jaro_winkler = request.POST.get('jaro_winkler')
#         levenshtein = request.POST.get('levenshtein')
#         v_token_set_ratio = request.POST.get('token_set_ratio')
#         phonetic = request.POST.get('phonetic')
#         fuzzy_wuzzy = request.POST.get('fuzzy_wuzzy')

#         left_split_char = request.POST.get('left_split_char')
#         email_pre_char = request.POST.get('email_pre_char')
#         email_post_char = request.POST.get('email_post_char')

#         join_model = JoinModel.objects.get(pk=pk)
#         model = apps.get_model('tables', model_name)

#         loader_instance = InstantUpload.objects.create(
#             type=TypeChoices.FILE,
#             content_type=ContentType.objects.get_for_model(model)
#         )

#         base_model_class = join_model.base_model.model_class()
#         has_delta_model = bool(join_model.delta_model)
#         delta_model_class = join_model.delta_model.model_class() if has_delta_model else None

#         max_base_loader_instance = base_model_class.objects.aggregate(models.Max('loader_instance'))['loader_instance__max']
#         base_records = list(base_model_class.objects.filter(loader_instance=max_base_loader_instance))

#         delta_records = []
#         max_delta_loader_instance = None
#         if has_delta_model:
#             max_delta_loader_instance = delta_model_class.objects.aggregate(models.Max('loader_instance'))['loader_instance__max']
#             delta_records = list(delta_model_class.objects.filter(loader_instance=max_delta_loader_instance))

#         base_field = join_model.base_f_key_fields
#         delta_f_fields = join_model.delta_f_key_fields.split(',') if join_model.delta_f_key_fields and has_delta_model else []

#         base_fields = join_model.base_fields.split(',') if join_model.base_fields else []
#         delta_fields = join_model.delta_fields.split(',') if join_model.delta_fields and has_delta_model else []

#         adjoin_instances = []

#         if has_delta_model:
#             delta_values_set = set()
#             delta_mapping = {}
#             for delta in delta_records:
#                 delta_values = [str(getattr(delta, field, None)) for field in delta_f_fields if getattr(delta, field, None) is not None]
#                 normalized_delta_value = "".join(delta_values).replace(" ", "").lower()
#                 delta_values_set.add(normalized_delta_value)
#                 delta_mapping[normalized_delta_value] = delta

#         for base_record in base_records:
#             base_value = str(getattr(base_record, base_field, None)) if base_record else None
#             normalized_base_value = base_value.replace(" ", "").lower() if base_value else None
#             raw_base_value = base_value if base_value else None

#             # Track all matches for this base record
#             matched_delta_records = []

#             if has_delta_model and normalized_base_value:

#                 if method == 'contains':
#                     for delta_value in delta_values_set:
#                         delta_values = [str(getattr(delta_mapping[delta_value], field, "")).strip() for field in delta_f_fields]
#                         delta_combined = "".join(delta_values).replace(" ", "").lower().strip()
#                         normalized_base = normalized_base_value.strip()
#                         current_delta_value = str(delta_value).strip()

#                         if c_full_word_match:
#                             if normalized_base == delta_combined:
#                                 matched_delta_records.append(delta_mapping[delta_value])
#                         else:
#                             if normalized_base in current_delta_value:
#                                 matched_delta_records.append(delta_mapping[delta_value])
                
#                 elif method == 'winkler_levenshtein':
#                     required_methods = []
                    
#                     if jaro_winkler:
#                         required_methods.append('jaro_winkler')
#                     if levenshtein:
#                         required_methods.append('levenshtein')
#                     if v_token_set_ratio:
#                         required_methods.append('token_set_ratio')
#                     if phonetic:
#                         required_methods.append('phonetic')
#                     if fuzzy_wuzzy:
#                         required_methods.append('fuzzy_wuzzy')

#                     if not required_methods:
#                         required_methods = ['jaro_winkler', 'levenshtein', 'token_set_ratio']

#                     for delta_value in delta_values_set:
#                         scores = {}
#                         meets_threshold = True
                        
#                         if 'jaro_winkler' in required_methods:
#                             scores['jaro_winkler'] = WRatio(normalized_base_value, delta_value)
#                             if scores['jaro_winkler'] < int(percent):
#                                 meets_threshold = False
                                
#                         if 'levenshtein' in required_methods:
#                             scores['levenshtein'] = ratio(normalized_base_value, delta_value)
#                             if scores['levenshtein'] < int(percent):
#                                 meets_threshold = False
                                
#                         if 'token_set_ratio' in required_methods:
#                             scores['token_set_ratio'] = token_set_ratio(normalized_base_value, delta_value)
#                             if scores['token_set_ratio'] < int(percent):
#                                 meets_threshold = False
                                
#                         if 'phonetic' in required_methods:
#                             soundex_base = jellyfish.soundex(normalized_base_value)
#                             soundex_delta = jellyfish.soundex(delta_value)
#                             scores['phonetic'] = 100 if soundex_base == soundex_delta else 0
#                             if scores['phonetic'] < int(percent):
#                                 meets_threshold = False
                                
#                         if 'fuzzy_wuzzy' in required_methods:
#                             scores['fuzzy_wuzzy'] = fuzz.ratio(normalized_base_value, delta_value)
#                             if scores['fuzzy_wuzzy'] < int(percent):
#                                 meets_threshold = False

#                         if meets_threshold:
#                             matched_delta_records.append(delta_mapping[delta_value])
                
#                 elif method == 'split':
#                     extracted_words = []
#                     if raw_base_value:
#                         temp_value = raw_base_value
#                         if split_char:
#                             try:
#                                 position = int(word_position) - 1
#                                 parts = raw_base_value.split(split_char)
#                                 if 0 <= position < len(parts):
#                                     temp_value = parts[position]
#                                 else:
#                                     temp_value = ""
#                             except (ValueError, IndexError):
#                                 temp_value = ""

#                         if split_space:
#                             words = temp_value.split()
#                             try:
#                                 position = int(word_position) - 1
#                                 if position < len(words):
#                                     extracted_words = words[position:]
#                             except (ValueError, IndexError):
#                                 extracted_words = []

#                     if extracted_words and has_delta_model:
#                         normalized_extracted_words = [word.lower() for word in extracted_words]
#                         for delta_value in delta_values_set:
#                             delta_values = [str(getattr(delta_mapping[delta_value], field, "")) for field in delta_f_fields]
#                             delta_combined = "".join(delta_values).replace(" ", "").lower()

#                             if s_full_word_match:
#                                 combined_extracted = "".join(normalized_extracted_words)
#                                 if combined_extracted == delta_combined:
#                                     matched_delta_records.append(delta_mapping[delta_value])
#                             else:
#                                 all_words_match = all(word in delta_combined for word in normalized_extracted_words)
#                                 if all_words_match:
#                                     matched_delta_records.append(delta_mapping[delta_value])
                
#                 elif method == 'pre_post':
#                     if normalized_base_value:
#                         modified_base_value = normalized_base_value

#                         if pre_char and pre_char.isdigit():
#                             remove_count = int(pre_char)
#                             if remove_count < len(modified_base_value):
#                                 modified_base_value = modified_base_value[remove_count:]
#                             else:
#                                 modified_base_value = ""

#                         if post_char and post_char.isdigit():
#                             remove_count = int(post_char)
#                             if remove_count < len(modified_base_value):
#                                 modified_base_value = modified_base_value[:-remove_count]
#                             else:
#                                 modified_base_value = ""

#                         for delta_value in delta_values_set:
#                             delta_values = [str(getattr(delta_mapping[delta_value], field, "")) for field in delta_f_fields]
#                             delta_combined = "".join(delta_values).replace(" ", "").lower()

#                             if pp_full_word_match:
#                                 if modified_base_value == delta_combined:
#                                     matched_delta_records.append(delta_mapping[delta_value])
#                             else:
#                                 if modified_base_value in delta_combined:
#                                     matched_delta_records.append(delta_mapping[delta_value])

#                 elif method == 'custom':
#                     local_vars = {}

#                     if py_function:
#                         py_func = get_object_or_404(PyFunction, id=py_function)
#                         try:
#                             exec(py_func.func, {}, local_vars)
#                             func = next((v for v in local_vars.values() if callable(v)), None)

#                             if func is None:
#                                 return JsonResponse({'error': 'No valid function defined'}, status=400)

#                             for delta_record in delta_records:
#                                 base_values = [str(getattr(base_record, field, "")) for field in fields_to_pass if not field.startswith('d_')]
#                                 delta_values = [str(getattr(delta_record, field[2:], "")) for field in fields_to_pass if field.startswith('d_')]

#                                 combined_args = base_values + delta_values

#                                 try:
#                                     result = func(*combined_args)
#                                 except Exception as e:
#                                     print(f"Error calling custom function: {e}")
#                                     continue

#                                 if isinstance(result, (bool, int, float)) and result:
#                                     matched_delta_records.append(delta_record)

#                         except Exception as e:
#                             print(f"Error executing custom function: {e}")
                
#                 elif method == 'email_join':
#                     extracted_words = []
#                     if normalized_base_value:
#                         temp_value = normalized_base_value

#                         parts = temp_value.split('@')
#                         temp_value = parts[0] if parts else ""

#                         if left_split_char:
#                             temp_value = temp_value.split(left_split_char)[0]

#                         if email_pre_char and email_pre_char.isdigit():
#                             remove_count = int(email_pre_char)
#                             if remove_count < len(temp_value):
#                                 temp_value = temp_value[remove_count:]
#                             else:
#                                 temp_value = ""

#                         if email_post_char and email_post_char.isdigit():
#                             remove_count = int(email_post_char)
#                             if remove_count < len(temp_value):
#                                 temp_value = temp_value[:-remove_count]
#                             else:
#                                 temp_value = ""

#                         for delta_value in delta_values_set:
#                             delta_values = [str(getattr(delta_mapping[delta_value], field, "")) for field in delta_f_fields]
#                             delta_combined = "".join(delta_values).replace(" ", "").lower()

#                             if temp_value in delta_combined:
#                                 matched_delta_records.append(delta_mapping[delta_value])


#             if has_delta_model:
#                 if matched_delta_records:
#                     for matched_delta_record in matched_delta_records:
#                         adjoin_data = {
#                             'loader_instance': loader_instance.pk,
#                             'both': 1,
#                             'base': 0,
#                             'delta': 0,
#                             'json_data': None,
#                             'hash_data': None
#                         }

#                         for field in base_fields:
#                             adjoin_data[field] = getattr(base_record, field, None)

#                         for field in delta_fields:
#                             adjoin_data[f"d_{field}"] = getattr(matched_delta_record, field, None)

#                         db_alias = model._default_manager.db
#                         database_path = connections[db_alias].settings_dict['NAME']
#                         database_name = os.path.basename(database_path) if database_path else database_path
#                         json_data = {
#                             "database": database_name,
#                             "table": model._meta.db_table,
#                             "loader_instance": loader_instance.pk,
#                             "snapshot_at": timezone.now().isoformat(),
#                             "both": 1,
#                             "base": 0,
#                             "delta": 0,
#                         }

#                         for field in base_fields:
#                             json_data[field] = adjoin_data.get(field)
                        
#                         for field in delta_fields:
#                             json_data[f"d_{field}"] = adjoin_data.get(f"d_{field}")

#                         hash_data = hash_json(json_data)
#                         adjoin_data['json_data'] = json_data
#                         adjoin_data['hash_data'] = hash_data

#                         adjoin_instances.append(model(**adjoin_data))
#                 else:
#                     adjoin_data = {
#                         'loader_instance': loader_instance.pk,
#                         'both': 0,
#                         'base': 1,
#                         'delta': 0,
#                         'json_data': None,
#                         'hash_data': None
#                     }

#                     for field in base_fields:
#                         adjoin_data[field] = getattr(base_record, field, None)

#                     db_alias = model._default_manager.db
#                     database_path = connections[db_alias].settings_dict['NAME']
#                     database_name = os.path.basename(database_path) if database_path else database_path
#                     json_data = {
#                         "database": database_name,
#                         "table": model._meta.db_table,
#                         "loader_instance": loader_instance.pk,
#                         "snapshot_at": timezone.now().isoformat(),
#                         "both": 0,
#                         "base": 1,
#                         "delta": 0,
#                     }

#                     for field in base_fields:
#                         json_data[field] = adjoin_data.get(field)

#                     hash_data = hash_json(json_data)
#                     adjoin_data['json_data'] = json_data
#                     adjoin_data['hash_data'] = hash_data

#                     adjoin_instances.append(model(**adjoin_data))
#             else:
#                 adjoin_data = {
#                     'loader_instance': loader_instance.pk,
#                     'both': 1,
#                     'base': 1,
#                     'delta': 0,
#                     'json_data': None,
#                     'hash_data': None
#                 }

#                 for field in base_fields:
#                     adjoin_data[field] = getattr(base_record, field, None)

#                 db_alias = model._default_manager.db
#                 database_path = connections[db_alias].settings_dict['NAME']
#                 database_name = os.path.basename(database_path) if database_path else database_path
#                 json_data = {
#                     "database": database_name,
#                     "table": model._meta.db_table,
#                     "loader_instance": loader_instance.pk,
#                     "snapshot_at": timezone.now().isoformat(),
#                     "both": 1,
#                     "base": 1,
#                     "delta": 0,
#                 }

#                 for field in base_fields:
#                     json_data[field] = adjoin_data.get(field)

#                 hash_data = hash_json(json_data)
#                 adjoin_data['json_data'] = json_data
#                 adjoin_data['hash_data'] = hash_data

#                 adjoin_instances.append(model(**adjoin_data))

#         model.objects.bulk_create(adjoin_instances)

#         user = request.user
#         timestamp_utc = timezone.now()
#         timestamp_local = timezone.localtime(timestamp_utc)
#         timestamp_str = timestamp_local.strftime('%Y-%m-%d %H:%M:%S')

#         description_parts = [
#             f'Data extraction: {base_model_class.__name__}' + 
#             (f' and {delta_model_class.__name__}' if has_delta_model else ''),
#             f'{base_model_class.__name__} rows: {len(base_records)}'
#         ]
        
#         if has_delta_model:
#             description_parts.append(f'{delta_model_class.__name__} rows: {len(delta_records)}')
        
#         original_method = method
#         if method == 'winkler_levenshtein':
#             methods = []

#             if jaro_winkler:
#                 methods.append("Jaro-Winkler")
#             if levenshtein:
#                 methods.append("Levenshtein")
#             if v_token_set_ratio:
#                 methods.append("Token Set Ratio")
#             if phonetic:
#                 methods.append("Phonetic")
#             if fuzzy_wuzzy:
#                 methods.append("Fuzzy-Wuzzy")

#             method = ", ".join(methods)
        

#         method_lower = original_method.lower()

#         if method_lower == 'contains':
#             description_parts.insert(3, f'Columns used: {join_model.base_f_key_fields}, {join_model.delta_f_key_fields}')
#             description_parts.insert(4, f'Join method: {method}')
#             if c_full_word_match:
#                 description_parts.insert(5, f'Full word match: Yes')


#         if method_lower == 'winkler_levenshtein':
#             description_parts.insert(3, f'Columns used: {join_model.base_f_key_fields}, {join_model.delta_f_key_fields}')
#             description_parts.insert(4, f'Join method: {method}')
#             description_parts.insert(5, f'Similarity Threshold: {percent}%')

#         if method_lower == 'split':
#             description_parts.insert(3, f'Columns used: {join_model.base_f_key_fields}, {join_model.delta_f_key_fields}')
#             description_parts.insert(4, f'Split column: {join_model.base_f_key_fields}')
#             description_parts.insert(5, f'Join method: {method}')
#             description_parts.insert(6, f'Split By Space: {"Yes" if split_space else "No"}')
#             if split_char:
#                 description_parts.insert(7, f'Split Character: {split_char}')
#             if word_position:
#                 description_parts.insert(8, f'Match Word Position: {word_position}')
#             if s_full_word_match:
#                 description_parts.insert(9, f'Full word match: Yes')

#         if method_lower == 'pre_post':
#             description_parts.insert(3, f'Columns used: {join_model.base_f_key_fields} (table: {base_model_class.__name__}), {join_model.delta_f_key_fields} (table: {delta_model_class.__name__})')
#             description_parts.insert(4, f'Adjusted column: {join_model.base_f_key_fields}')
#             description_parts.insert(5, f'Join method: {method}')
#             if pre_char:
#                 description_parts.insert(6, f'Pre Characters removed: {pre_char}')
#             if post_char:
#                 description_parts.insert(7, f'Post Characters removed: {post_char}')
#             if pp_full_word_match:
#                 description_parts.insert(8, f'Full word match: Yes')
#             else:
#                 description_parts.insert(8, f'Contains match: Yes')
        
#         if method_lower == 'custom':
#             py_func = get_object_or_404(PyFunction, id=py_function)
#             description_parts.insert(3, f'Python Function: {py_func.func}')
#             description_parts.insert(4, f'Column passed: {fields_to_pass}')

#         description_parts.extend([
#             f'New Join table name: {model.__name__}',
#             f'Extracted by: {user.get_full_name() or user.username}',
#             f'Extracted on: {timestamp_str}',
#             f'Rows extracted: {len(adjoin_instances)}',
#             f'Snapshot: {loader_instance.pk}',
#             f'Columns: {", ".join([field.name for field in model._meta.get_fields()])}'
#         ])
            
#         IPE.objects.create(
#             userID=user,
#             path=urlparse(request.META.get('HTTP_REFERER', request.path)).path,
#             description='\n'.join(description_parts)
#         )

#         # print(f"{max_count} {model_name} instances created.")
#         return redirect(request.META.get('HTTP_REFERER'))

#     return redirect(request.META.get('HTTP_REFERER'))



def load_data_to_join_model(request, model_name, pk):
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER'))

    # --- POST parameters ---
    method = request.POST.get('method')
    percent = request.POST.get('percent')

    c_full_word_match = request.POST.get('c_full_word_match') == 'on'
    py_function = request.POST.get('py_function')
    c_percent = request.POST.get('c_percent')
    fields_to_pass = request.POST.getlist('fields_to_pass')

    split_char = request.POST.get('split_char')
    word_position = request.POST.get('word_position')
    split_space = request.POST.get('split_space') == 'on'
    s_full_word_match = request.POST.get('s_full_word_match') == 'on'

    pre_char = request.POST.get('pre_char')
    post_char = request.POST.get('post_char')
    pp_full_word_match = request.POST.get('pp_full_word_match') == 'on'

    jaro_winkler = request.POST.get('jaro_winkler')
    levenshtein = request.POST.get('levenshtein')
    v_token_set_ratio = request.POST.get('token_set_ratio')
    phonetic = request.POST.get('phonetic')
    fuzzy_wuzzy = request.POST.get('fuzzy_wuzzy')

    left_split_char = request.POST.get('left_split_char')
    email_pre_char = request.POST.get('email_pre_char')
    email_post_char = request.POST.get('email_post_char')

    join_model = JoinModel.objects.get(pk=pk)
    model = apps.get_model('tables', model_name)
    vector_model_name = getattr(model, 'vector_model', 'BAAI/bge-large-en-v1.5')

    loader_instance = InstantUpload.objects.create(
        type=TypeChoices.SP,
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

    adjoin_instances = []

    # --- Preprocess delta mapping ---
    delta_values_set = set()
    delta_mapping = {}
    if has_delta_model:
        for delta in delta_records:
            delta_values = [str(getattr(delta, field, None)) for field in delta_f_fields if getattr(delta, field, None) is not None]
            normalized_delta_value = "".join(delta_values).replace(" ", "").lower()
            delta_values_set.add(normalized_delta_value)
            delta_mapping[normalized_delta_value] = delta

    # --- Iterate base records ---
    for base_record in base_records:
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
                        scores['jaro_winkler'] = WRatio(normalized_base_value, delta_value)
                        if scores['jaro_winkler'] < int(percent): meets_threshold=False
                    if 'levenshtein' in required_methods:
                        scores['levenshtein'] = ratio(normalized_base_value, delta_value)
                        if scores['levenshtein'] < int(percent): meets_threshold=False
                    if 'token_set_ratio' in required_methods:
                        scores['token_set_ratio'] = token_set_ratio(normalized_base_value, delta_value)
                        if scores['token_set_ratio'] < int(percent): meets_threshold=False
                    if 'phonetic' in required_methods:
                        soundex_base = jellyfish.soundex(normalized_base_value)
                        soundex_delta = jellyfish.soundex(delta_value)
                        scores['phonetic'] = 100 if soundex_base==soundex_delta else 0
                        if scores['phonetic'] < int(percent): meets_threshold=False
                    if 'fuzzy_wuzzy' in required_methods:
                        scores['fuzzy_wuzzy'] = fuzz.ratio(normalized_base_value, delta_value)
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

        # --- Build adjoin_data ---
        adjoin_data = {'loader_instance': loader_instance.pk, 'json_data': None, 'hash_data': None}
        if matched_delta_record:
            for rec in matched_delta_record:
                adjoin_copy = adjoin_data.copy()
                adjoin_copy.update({'both':1, 'base':0, 'delta':0})
                for f in base_fields:
                    adjoin_copy[f] = getattr(base_record, f, None)
                for f in delta_fields:
                    adjoin_copy[f"d_{f}"] = getattr(rec, f, None)

                # create json_data and hash for this copy
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
                for f in base_fields: json_data[f] = adjoin_copy.get(f)
                for f in delta_fields: json_data[f"d_{f}"] = adjoin_copy.get(f"d_{f}")
                adjoin_copy['json_data'] = json_data
                if is_pgvector_enabled():
                    adjoin_copy['hash_data'] = json_to_vector(json_data, model_name=vector_model_name)
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
            for f in base_fields: json_data[f] = adjoin_data.get(f)
            for f in delta_fields: json_data[f"d_{f}"] = adjoin_data.get(f"d_{f}")
            adjoin_data['json_data'] = json_data
            if is_pgvector_enabled():
                adjoin_data['hash_data'] = json_to_vector(json_data, model_name=vector_model_name)
            else:
                adjoin_data['hash_data'] = hash_json(json_data)

            adjoin_instances.append(model(**adjoin_data))

    # --- Add delta-only rows ---
    if has_delta_model:
        for delta_record in delta_records:
            adjoin_data = {'loader_instance': loader_instance.pk, 'both':0, 'base':0, 'delta':1, 'json_data':None, 'hash_data':None}
            for f in delta_fields: adjoin_data[f"d_{f}"] = getattr(delta_record, f, None)
            json_data = {'database': database_name, 'table': model._meta.db_table, 'loader_instance': loader_instance.pk,
                         'snapshot_at': timezone.now().isoformat(), 'both':0, 'base':0, 'delta':1}
            for f in delta_fields: json_data[f"d_{f}"] = adjoin_data.get(f"d_{f}")
            adjoin_data['json_data'] = json_data
            if is_pgvector_enabled():
                adjoin_data['hash_data'] = json_to_vector(json_data, model_name=vector_model_name)
            else:
                adjoin_data['hash_data'] = hash_json(json_data)
            adjoin_instances.append(model(**adjoin_data))

    # --- Bulk create ---
    model.objects.bulk_create(adjoin_instances)

    # --- Logging IPE ---
    user = request.user
    timestamp_local = timezone.localtime(timezone.now())
    timestamp_str = timestamp_local.strftime('%Y-%m-%d %H:%M:%S')
    description_parts = [f'Data extraction: {base_model_class.__name__}' + (f' and {delta_model_class.__name__}' if has_delta_model else ''),
                         f'{base_model_class.__name__} rows: {len(base_records)}']
    if has_delta_model: description_parts.append(f'{delta_model_class.__name__} rows: {len(delta_records)}')
    description_parts += [f'New Join table name: {model.__name__}',
                          f'Extracted by: {user.get_full_name() or user.username}',
                          f'Extracted on: {timestamp_str}',
                          f'Rows extracted: {len(adjoin_instances)}',
                          f'Snapshot: {loader_instance.pk}',
                          f'Columns: {", ".join([field.name for field in model._meta.get_fields()])}']
    IPE.objects.create(userID=user,
                       path=urlparse(request.META.get('HTTP_REFERER', request.path)).path,
                       description='\n'.join(description_parts))

    return redirect(request.META.get('HTTP_REFERER'))

# New

from home.tasks import async_load_data_to_join_model

def load_data_to_join_model(request, model_name, pk):

    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER'))

    params = request.POST.dict()
    params["fields_to_pass"] = request.POST.getlist("fields_to_pass")
	params['referer'] = request.META.get('HTTP_REFERER', request.path)

    task = async_load_data_to_join_model.delay(
        model_name=model_name,
        pk=pk,
        params=params
    )

    return redirect(request.META.get('HTTP_REFERER'))

########

def join_view_404(request):
    return render(request, 'pages/join_view_404.html')


# Model builder
import csv
from django.views.decorators.csrf import csrf_exempt
import pandas as pd

def sanitize_header(header):
    sanitized = header.strip()
    sanitized = re.sub(r'[!@#$%^&*()+\-=\[\]{}|;:\'",.<>?/`~]', '', sanitized)
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized

@csrf_exempt
def process_file(request):
    if request.method == "POST" and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        filename = uploaded_file.name
        extension = os.path.splitext(filename)[1].lower()

        try:
            if extension == '.csv':
                decoded_file = uploaded_file.read().decode('latin-1').splitlines()
                reader = csv.reader(decoded_file)
                headers = next(reader, [])
                sanitized_headers = [sanitize_header(h) for h in headers]

                data = []
                for row in reader:
                    row_dict = dict(zip(sanitized_headers, row))
                    data.append(row_dict)

            elif extension in ['.xlsx', '.xls']:
                df = pd.read_excel(uploaded_file)
                df.columns = [sanitize_header(col) for col in df.columns]
                data = df.to_dict(orient='records')

            else:
                return JsonResponse({'error': 'Unsupported file type'}, status=400)

            return JsonResponse({'headers': list(data[0].keys()) if data else []})

        except Exception as e:
            return JsonResponse({'error': f'Failed to process file: {str(e)}'}, status=500)

    return JsonResponse({'error': 'No file uploaded'}, status=400)

@csrf_exempt
def sap_api_headers(request, id):
    try:
        api_instance = SAPApi.objects.get(id=id)

        headers = {
            'APIKey': api_instance.api_key,
            'Accept': 'application/json',
            'DataServiceVersion': '2.0',
        }

        params = {
            '$top': api_instance.top
        }

        response = requests.get(api_instance.api_url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()

            if 'value' in data and isinstance(data['value'], list) and len(data['value']) > 0:
                headers = list(data['value'][0].keys())
                return JsonResponse({'headers': headers})
            else:
                return JsonResponse({'headers': []})

        return JsonResponse({'error': f'HTTP {response.status_code}: {response.text}'}, status=response.status_code)

    except SAPApi.DoesNotExist:
        return JsonResponse({'error': 'SAP API config not found'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt
def sql_query_headers(request, id):
    try:
        query = DynamicQuery.objects.get(id=id)

        with connection.cursor() as cursor:
            cursor.execute(query.query)
            column_names = [col[0] for col in cursor.description] if cursor.description else []
            exclude_fields = {'id', 'ID', 'loader_instance'}
            filtered_headers = [col for col in column_names if col not in exclude_fields]

        return JsonResponse({'headers': filtered_headers})

    except DynamicQuery.DoesNotExist:
        return JsonResponse({'error': 'DynamicQuery config not found'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def sap_api_data(request, id):
    try:
        api_instance = SAPApi.objects.get(id=id)

        headers = {
            'APIKey': api_instance.api_key,
            'Accept': 'application/json',
            'DataServiceVersion': '2.0',
        }

        params = {
            '$top': 100 
        }

        response = requests.get(api_instance.api_url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()

            if 'value' in data and isinstance(data['value'], list):
                rows = data['value'][:100]
                headers = list(rows[0].keys()) if rows else []
                return JsonResponse({
                    'headers': headers,
                    'rows': rows
                })

            return JsonResponse({'headers': [], 'rows': []})

        return JsonResponse({'error': f'HTTP {response.status_code}: {response.text}'}, status=response.status_code)

    except SAPApi.DoesNotExist:
        return JsonResponse({'error': 'SAP API config not found'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt
def sql_query_data(request, id):
    try:
        query = DynamicQuery.objects.get(id=id)

        with connection.cursor() as cursor:
            cursor.execute(query.query)
            column_names = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            exclude_fields = {'id', 'ID', 'loader_instance'}

            filtered_headers = [col for col in column_names if col not in exclude_fields]
            rows_dicts = [
                {col: val for col, val in zip(column_names, row) if col not in exclude_fields}
                for row in rows[:100]
            ]

        return JsonResponse({
            'headers': filtered_headers,
            'rows': rows_dicts
        })

    except DynamicQuery.DoesNotExist:
        return JsonResponse({'error': 'DynamicQuery config not found'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)    

@shared_task
def local_migrations(result):
    try:
        print("Starting migrations...")
        subprocess.run('python manage.py makemigrations --noinput', shell=True, check=True)
        print("Makemigrations completed.")
        subprocess.run('python manage.py migrate --noinput', shell=True, check=True)
        print("Migrate completed.")
        result['status'] = 'completed'
        return result
    except subprocess.CalledProcessError as e:
        result['status'] = 'error'
        result['message'] = str(e)
        raise

@shared_task
def create_pgvector_indexes(result):
    try:
        if not is_pgvector_enabled():
            print("PGVector not enabled, skipping index creation.")
            return result

        table_name = f"tables_{result['model_name']}".lower()
        pg_table_name = f'"{table_name}"'

        with connection.cursor() as cursor:
            cursor.execute(f"""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_{result['model_name'].lower()}_hash_l2_ivf
                ON public.{pg_table_name}
                USING ivfflat (hash_data vector_l2_ops)
                WITH (lists = 100);
            """)
            cursor.execute(f"ANALYZE public.{pg_table_name};")
            print(f"L2 index created on {pg_table_name}")

            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{result['model_name'].lower()}_hash_cos
                ON public.{pg_table_name}
                USING ivfflat (hash_data vector_cosine_ops)
                WITH (lists = 100);
            """)
            cursor.execute(f"ANALYZE public.{pg_table_name};")
            print(f"Cosine index created on {pg_table_name}")

        result['pgvector_indexes'] = 'created'
        return result

    except Exception as e:
        result['status'] = 'error'
        result['message'] = str(e)
        raise


@shared_task
def create_fts_index(result):
    try:
        table_name = f"tables_{result['model_name']}".lower()
        pg_table_name = f'"{table_name}"'

        with connection.cursor() as cursor:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{result['model_name'].lower()}_fts
                ON public.{pg_table_name}
                USING gin(fts);
            """)
            cursor.execute(f"ANALYZE public.{pg_table_name};")
            print(f"FTS index created on {pg_table_name}")

        result['fts_index'] = 'created'
        return result

    except Exception as e:
        result['status'] = 'error'
        result['message'] = str(e)
        raise


@shared_task
def create_fts_trigger(result):
    try:
        table_name = f"tables_{result['model_name']}".lower()
        pg_table_name = f'public."{table_name}"'

        model_class = apps.get_model('tables', result['model_name'])
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
            """, [table_name])
            existing_columns = {row[0].lower() for row in cursor.fetchall()}

        fields = []
        for field in model_class._meta.get_fields():
            if isinstance(field, (models.CharField, models.TextField)) and field.name not in ['id', 'fts']:
                db_col = field.db_column or field.name
                if db_col.lower() in existing_columns:
                    fields.append(f'coalesce(NEW."{db_col}", \'\')')
                else:
                    print(f"Skipping non-existent column {db_col} in table {table_name}")

        if not fields:
            print(f"No text fields found for {table_name}, skipping FTS trigger.")
            return result

        fields_concat = " || ' ' || ".join(fields)

        with connection.cursor() as cursor:
            cursor.execute(f"""
                CREATE OR REPLACE FUNCTION {table_name}_fts_trigger() RETURNS trigger AS $$
                BEGIN
                    NEW.fts := to_tsvector('english', {fields_concat});
                    RETURN NEW;
                END
                $$ LANGUAGE plpgsql;
            """)

            cursor.execute(f"DROP TRIGGER IF EXISTS {table_name}_fts_update ON {pg_table_name};")
            cursor.execute(f"""
                CREATE TRIGGER {table_name}_fts_update
                BEFORE INSERT OR UPDATE ON {pg_table_name}
                FOR EACH ROW EXECUTE FUNCTION {table_name}_fts_trigger();
            """)

        print(f"FTS trigger created on {pg_table_name}")
        result['fts_trigger'] = 'created'
        return result

    except Exception as e:
        result['status'] = 'error'
        result['message'] = str(e)
        raise

@shared_task
def create_views_urls_templates(result):
    try:
        if result['status'] == 'completed':
            request_data = result['request_data']
            model_name = f"tables.{result['model_name']}"
            view_function(request_data, model_name)
            url_function(request_data)
            template_function(request_data, model_name)
            print(f"Views, URLs, and templates for {model_name} created successfully!")
        else:
            print("Failed to generate views, URLs, and templates due to model generation error.")
        return result
    except Exception as e:
        result['status'] = 'error'
        result['message'] = str(e)

def get_current_vector_dimension(default: int = 1024) -> int:
    current = VectorModel.objects.filter(current=True).first()
    return current.dimension if current else default

def get_current_vector_model(default: str = "BAAI/bge-large-en-v1.5") -> str:
    current = VectorModel.objects.filter(current=True).first()
    return current.name if current else default

@shared_task
def create_model_and_migrate(request_data):
    model_name = request_data.get('model_name')

    columns = {}
    date_fields_to_convert = []
    integer_fields = []
    float_fields = []
    encrypted_fields = []
    unix_dates = []
    ad_unix_dates = []
    has_auto_field = False

    for key, value in request_data.items():
        if key.startswith('columns_') and not key.endswith('_type'):
            column_name = key.split('_', 1)[1]
            sanitized_column_name = column_name.strip().replace(' ', '_')
            column_type = request_data.get(f'columns_{column_name}_type', 'TextField')
            db_column = request_data.get(f'db_columns_{column_name}', sanitized_column_name)
            encryption_column = request_data.get(f'encryption_{column_name}') == 'on'
            
            db_column = db_column.strip()
            db_column = re.sub(r'[!@#$%^&*()+\-=[\]{}|;:\'",.<>/?]', '', db_column)
            db_column = re.sub(r'__+', '_', db_column)
            db_column = db_column.rstrip('_')
            db_column = re.sub(r'^\d+', '', db_column)

            if not db_column:
                db_column = sanitized_column_name

            if column_name.lower() == 'id' and not has_auto_field:
                columns[sanitized_column_name] = {
                    'type': 'AutoField',
                    'db_column': db_column,
                    'primary_key': True
                }
                has_auto_field = True
            else:
                columns[sanitized_column_name] = {'type': column_type, 'db_column': db_column}

            if column_type == 'DateField':
                date_fields_to_convert.append(sanitized_column_name)
            elif column_type == 'IntegerField':
                integer_fields.append(sanitized_column_name)
            elif column_type == 'FloatField':
                float_fields.append(sanitized_column_name)
            elif column_type == 'UnixDates':
                date_fields_to_convert.append(sanitized_column_name)
                unix_dates.append(sanitized_column_name)
            elif column_type == 'ADUnixDates':
                date_fields_to_convert.append(sanitized_column_name)
                ad_unix_dates.append(sanitized_column_name)
            

            if encryption_column:
                encrypted_fields.append(sanitized_column_name)

    model_code = f"\n\nclass {model_name}(models.Model):\n"
    if not has_auto_field:
        model_code += "    ID = models.AutoField(primary_key=True)\n"

    for column, column_info in columns.items():
        column_type = column_info['type']
        db_column = column_info['db_column']

        if column_type == 'AutoField':
            model_code += f"    {column} = models.AutoField(primary_key=True, verbose_name='{db_column}', db_column='{db_column}')\n"
        elif column_type == 'CharField':
            model_code += f"    {column} = models.CharField(max_length=255, null=True, blank=True, verbose_name='{db_column}', db_column='{db_column}')\n"
        elif column_type == 'IntegerField':
            model_code += f"    {column} = models.IntegerField(null=True, blank=True, verbose_name='{db_column}', db_column='{db_column}')\n"
        elif column_type == 'FloatField':
            model_code += f"    {column} = models.FloatField(null=True, blank=True, verbose_name='{db_column}', db_column='{db_column}')\n"
        elif column_type == 'DateField':
            model_code += f"    {column} = models.BigIntegerField(null=True, blank=True, verbose_name='{db_column}', db_column='{db_column}')\n"
        elif column_type == 'BigIntegerField':
            model_code += f"    {column} = models.BigIntegerField(null=True, blank=True, verbose_name='{db_column}', db_column='{db_column}')\n"
        elif column_type == 'UnixDates':
            model_code += f"    {column} = models.BigIntegerField(null=True, blank=True, verbose_name='{db_column}', db_column='{db_column}')\n"
        elif column_type == 'ADUnixDates':
            model_code += f"    {column} = models.BigIntegerField(null=True, blank=True, verbose_name='{db_column}', db_column='{db_column}')\n"
        else:
            model_code += f"    {column} = models.TextField(null=True, blank=True, verbose_name='{db_column}', db_column='{db_column}')\n"

    model_code += "    loader_instance = models.IntegerField(null=True, blank=True)\n"
    model_code += "    json_data = models.JSONField(null=True, blank=True)\n"
    if is_pgvector_enabled():
        dim = get_current_vector_dimension()
        model_code += f"    hash_data = VectorField(dimensions={dim}, null=True, blank=True)\n"
    else:
        model_code += "    hash_data = models.TextField(null=True, blank=True)\n"

    model_code += "    fts = SearchVectorField(null=True, blank=True)\n"
    model_code += f"\n    date_fields_to_convert = {date_fields_to_convert}\n"
    model_code += f"    integer_fields = {integer_fields}\n"
    model_code += f"    float_fields = {float_fields}\n"
    model_code += f"    encrypted_fields = {encrypted_fields}\n"
    model_code += f"    unix_dates = {unix_dates}\n"
    model_code += f"    ad_unix_dates = {ad_unix_dates}\n"
    if is_pgvector_enabled():
        model_code += f"    vector_model = {repr(get_current_vector_model())}\n"

    models_file_path = getattr(settings, 'MODELS_FILE_PATH')
    with open(models_file_path, 'a') as f:
        f.write(model_code)

    update_model_choices_file(model_name)

    task_chain = chain(
        local_migrations.s({'status': 'pending', 'request_data': request_data, 'model_name': model_name}),
        create_pgvector_indexes.s(),
        create_fts_index.s(),
        create_fts_trigger.s(),
        create_views_urls_templates.s()
    )
    result = task_chain.apply_async()
    task_id = result.id

    return {
        'status': 'pending',
        'task_id': task_id,
        'message': 'Model creation in progress. Please wait...'
    }


def model_builder(request):
    if request.method == 'POST':
        model_name = request.POST.get('model_name')
        if model_exists(model_name):
            return JsonResponse({
                'status': 'error',
                'message': f"Model '{model_name}' already exists."
            })
    
        if table_exists(f'tables_{model_name.lower()}'):
            return JsonResponse({
                'status': 'error',
                'message': f'Table for model "{model_name}" already exists in the database.'
            })
    
        post_data = request.POST.dict()
        for key in ['ro_fields', 'precol_fields', 'compulsory_fields']:
            post_data[key] = request.POST.getlist(key)

        result = create_model_and_migrate.apply_async(args=[post_data])
        task_id = result.id

        fav_name = request.POST.get('fav_name')
        view_name = fav_name.replace(' ', '_').lower()
        view_name = re.sub(r'[^a-zA-Z0-9_]', '', view_name)

        sidebar_group = get_object_or_404(Group, name=request.POST.get('group_name'))
        sidebar_parent = get_object_or_404(Sidebar, id=request.POST.get('parent_name'))
        Sidebar.objects.create(
            group=sidebar_group,
            parent=sidebar_parent,
            name=fav_name,
            segment=view_name,
            url_name=view_name
        )

        return JsonResponse({
            'status': 'pending',
            'task_id': task_id,
            'view_name': view_name,
            'message': 'Model creation in progress. Please wait...'
        })

    loader_model_apps = settings.LOADER_MODEL_APPS
    model_names = {}
    for app_name in loader_model_apps:
        app_config = apps.get_app_config(app_name)
        models = [model.__name__ for model in app_config.get_models()]
        model_names[app_name] = models

    sidebars = Sidebar.objects.filter(is_active=True, parent__isnull=True).values('id', 'name')
    groups = Group.objects.all()

    context = {
        'model_names': model_names,
        'sidebars': sidebars,
        'groups': groups,
        'sap_apis': SAPApi.objects.all(),
        'segment': 'model_builder',
        'parent' : 'home'
    }
    return render(request, 'pages/model_builder.html', context)
