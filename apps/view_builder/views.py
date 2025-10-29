import os
import re
import importlib
from django.shortcuts import render, redirect
from django.conf import settings
from django.apps import apps
from apps.common.models import Sidebar
from django.http import JsonResponse
from django.urls import reverse

# Create your views here.

def update_template_tags(model_class):
    spec = importlib.util.spec_from_file_location("template_tags_module", settings.TEMPLATE_TAG_PATH)
    template_tags_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(template_tags_module)

    if hasattr(template_tags_module, 'DATE_FIELDS'):
        date_fields_list = getattr(template_tags_module, 'DATE_FIELDS')
        
        date_fields_to_convert = getattr(model_class, 'date_fields_to_convert', None)
        
        if date_fields_to_convert:
            new_fields = [field for field in date_fields_to_convert if field not in date_fields_list]
            if new_fields:
                date_fields_list.extend(new_fields)

                with open(settings.TEMPLATE_TAG_PATH, 'r') as file:
                    lines = file.readlines()

                with open(settings.TEMPLATE_TAG_PATH, 'w') as file:
                    for line in lines:
                        if line.strip().startswith('DATE_FIELDS ='):
                            file.write(f"DATE_FIELDS = {date_fields_list}\n")
                        else:
                            file.write(line)

                print("DATE_FIELDS updated successfully.")


def view_function(request):
    parent_name = request.POST.get('parent_name')
    if selected_model := request.POST.get('model_name'):
        app_name, model_name = selected_model.split('.')
        model_class = apps.get_model(app_name, model_name)

    update_template_tags(model_class)

    fav_name = request.POST.get('fav_name')
    view_name = fav_name.replace(' ', '_').lower()
    view_name = re.sub(r'[^a-zA-Z0-9_]', '', view_name)

    # model_choice = '_'.join(re.findall(r'[A-Z]+(?![a-z])|[A-Z][a-z]*', model_name)).upper()
    model_choice = '_'.join(re.findall(r'[A-Z]+(?![a-z])|[A-Z][a-z]*|\d+', model_name)).upper()
    db_table = model_class._meta.db_table.split('_', 1)[-1]

    current_dir = os.path.dirname(os.path.abspath(__file__))

    template_path = os.path.join(current_dir, 'control', 'base_control_view.txt')
    with open(template_path, 'r') as file:
        template_content = file.read()

    
    updated_content = template_content

    readonly_fields = request.POST.getlist('readonly_fields')
    readonly_fields = list(set(readonly_fields + ['ID', 'loader_instance']))
    if readonly_fields:
        readonly_fields_str = ', '.join([f"'{field}'" for field in readonly_fields])
        updated_content = updated_content.replace(
            'read_only_fields = ()',
            f"read_only_fields = ({readonly_fields_str},)"
        )

    pre_columns = request.POST.getlist('pre_columns')
    pre_columns = list(set(pre_columns + ['ID', 'loader_instance']))
    if pre_columns:
        pre_columns_str = ', '.join([f"'{field}'" for field in pre_columns])
        updated_content = updated_content.replace(
            'pre_column = ()',
            f"pre_column = ({pre_columns_str},)"
        )

    compulsory_fields = request.POST.getlist('compulsory_fields')
    if compulsory_fields:
        compulsory_fields_str = ', '.join([f"'{field}'" for field in compulsory_fields])
        updated_content = updated_content.replace(
            'compulsory_fields = ()',
            f"compulsory_fields = ({compulsory_fields_str},)"
        )

    updated_content = updated_content.replace('VIEW_NAME', view_name).replace('MODEL_CHOICE', model_choice).replace('MODEL_NAME', model_name).replace('DB_TABLE', db_table).replace('PARENT_NAME', parent_name).replace('FAV_NAME', fav_name)


    view_dir_path = os.path.join(settings.VIEW_PATH, view_name)
    if not os.path.exists(view_dir_path):
        os.makedirs(view_dir_path)

    output_file_path = os.path.join(view_dir_path, f'{view_name}_views.py')
    with open(output_file_path, 'w') as output_file:
        output_file.write(updated_content)


def url_function(request):
    fav_name = request.POST.get('fav_name')
    view_name = fav_name.replace(' ', '_').lower()
    view_name = re.sub(r'[^a-zA-Z0-9_]', '', view_name)

    current_dir = os.path.dirname(os.path.abspath(__file__))

    template_path = os.path.join(current_dir, 'control', 'base_control_urls.txt')
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


def template_function(request):
    if selected_model := request.POST.get('model_name'):
        app_name, model_name = selected_model.split('.')
        model_class = apps.get_model(app_name, model_name)

    fav_name = request.POST.get('fav_name')
    view_name = fav_name.replace(' ', '_').lower()
    view_name = re.sub(r'[^a-zA-Z0-9_]', '', view_name)

    # model_choice = '_'.join(re.findall(r'[A-Z]+(?![a-z])|[A-Z][a-z]*', model_name)).upper()
    model_choice = '_'.join(re.findall(r'[A-Z]+(?![a-z])|[A-Z][a-z]*|\d+', model_name)).upper()

    current_dir = os.path.dirname(os.path.abspath(__file__))

    template_path = os.path.join(current_dir, 'control', 'base_control_template.txt')
    with open(template_path, 'r') as file:
        template_content = file.read()

    updated_content = template_content.replace('VIEW_NAME', view_name).replace('MODEL_CHOICE', model_choice).replace('MODEL_NAME', model_name).replace('FAV_NAME', fav_name).replace('URL_NAME', view_name.replace('_', '-'))

    output_file_path = os.path.join(settings.TEMPLATE_PATH, f'{view_name}.html')
    with open(output_file_path, 'w') as output_file:
        output_file.write(updated_content)


def index(request):
    if request.method == 'POST':
        view_function(request)
        url_function(request)
        template_function(request)

        return redirect(reverse('view_builder_index'))
    
    loader_model_apps = settings.LOADER_MODEL_APPS
    model_names = {}
    for app_name in loader_model_apps:
        app_config = apps.get_app_config(app_name)
        models = [model.__name__ for model in app_config.get_models()]
        model_names[app_name] = models

    sidebars = Sidebar.objects.filter(is_active=True).filter(parent__isnull=True)
    parent_names = sidebars.values_list('segment', flat=True)


    context = {
        'model_names': model_names,
        'parent_names': parent_names
    }
    return render(request, 'view_builder/index.html', context)


def get_model_fields(request):
    model_name = request.GET.get('model_name')
    if model_name:
        app_label, model_label = model_name.split('.')
        model = apps.get_model(app_label, model_label)
        fields = [field.name for field in model._meta.get_fields() if field.name not in ['ID', 'pk', 'id', 'loader_instance', 'hash_data', 'json_data']]
        return JsonResponse({'fields': fields})
    return JsonResponse({'fields': []})

from django.db import models

def get_model_data(request):
    model_name = request.GET.get('model_name')
    if model_name:
        app_label, model_label = model_name.split('.')
        model = apps.get_model(app_label, model_label)
        max_snapshot = model.objects.aggregate(models.Max('loader_instance'))['loader_instance__max']
        queryset = model.objects.filter(loader_instance=max_snapshot)
        total_rows = queryset.count()
        raw_data = list(queryset[:100].values())

        excluded_fields = {'id', 'loader_instance', 'ID'}
        data = [{k: v for k, v in row.items() if k not in excluded_fields} for row in raw_data]

        headers = list(data[0].keys()) if data else []

        return JsonResponse({
            'headers': headers,
            'rows': data,
            'total_rows': total_rows
        })

    return JsonResponse({'headers': [], 'rows': []})