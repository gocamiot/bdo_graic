import re, ast
import markdown2
from django import template
from home.models import JoinModel
from django.apps import apps
from django.shortcuts import get_object_or_404

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={'class': css_class})


@register.filter
def rename_field(field_name, join_model_instance):
    if join_model_instance is None:
        return field_name
    
    if isinstance(join_model_instance, JoinModel):
        join_model = join_model_instance
    else:
        join_model = JoinModel.objects.get(pk=join_model_instance)

    if field_name == "base":
        return join_model.base_model.model_class().__name__
    elif field_name == "delta":
        if join_model.delta_model:
            return join_model.delta_model.model_class().__name__
        return "Delta"
    return field_name


@register.filter
def default_values(field_name, join_model_instance):
    if join_model_instance is None:
        return None
    
    if isinstance(join_model_instance, JoinModel):
        join_model = join_model_instance
    else:
        join_model = JoinModel.objects.get(pk=join_model_instance)

    return getattr(join_model, field_name)


@register.filter
def get_base_rows(model):
    model_class = apps.get_model('tables', model)
    join_model = get_object_or_404(JoinModel, pk=model_class.join_model_instance)
    base_model_class = join_model.base_model.model_class()

    base_fields = [field.strip() for field in (join_model.base_f_key_fields or '').split(',') if field.strip()]
    rows = base_model_class.objects.values_list(*base_fields, flat=(len(base_fields) == 1))[:30]
    if len(base_fields) == 1:
        lines = [str(row) for row in rows]
    else:
        lines = [', '.join(str(col) for col in row) for row in rows]

    return 'First List:\n' + '\n'.join(lines)



@register.filter
def get_delta_rows(model):
    model_class = apps.get_model('tables', model)
    join_model = get_object_or_404(JoinModel, pk=model_class.join_model_instance)
    delta_model_class = join_model.delta_model.model_class()

    delta_fields = [field.strip() for field in (join_model.delta_f_key_fields or '').split(',') if field.strip()]
    rows = delta_model_class.objects.values_list(*delta_fields, flat=(len(delta_fields) == 1))[:30]
    if len(delta_fields) == 1:
        lines = [str(row) for row in rows]
    else:
        lines = [', '.join(str(col) for col in row) for row in rows]

    return 'Second List:\n' + '\n'.join(lines)


@register.filter
def format_response(response):
    return markdown2.markdown(response, extras=["fenced-code-blocks"])


@register.filter
def extract_table_data(value):
    try:
        if isinstance(value, str):
            value = re.sub(r'^<p>|</p>$', '', value.strip())

        data = ast.literal_eval(value) if isinstance(value, str) else value

        if not isinstance(data, list) or not data:
            return {'columns': [], 'data': []}

        exclude_fields = {'id', 'loader_instance', 'json_data', 'hash_data'}
        columns = [key for key in data[0].keys() if key not in exclude_fields]

        return {
            'columns': columns,
            'data': data,
        }

    except Exception as e:
        return {'columns': [], 'data': [], 'error': str(e)}