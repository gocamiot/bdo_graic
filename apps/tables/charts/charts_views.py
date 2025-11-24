import json
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import redirect, get_object_or_404, render
from apps.tables.models import (
    Tab, BaseCharts, TabCharts,
    SelectedRows, ModelChoices,
    ActionStatus
)
from apps.tables.utils import (
    software_filter, same_key_filter, common_date_filter,
    common_float_filter, common_integer_filter, common_count_filter, 
    common_unique_filter, get_model_fields
)
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from home.models import ColumnOrder
from apps.common.models import SavedFilter, FieldType
from loader.models import InstantUpload
from dateutil.parser import isoparse
from django.db.models import F, Case, When, IntegerField
from datetime import datetime
from collections import Counter


def add_chart(request, tab_id):
    tab = get_object_or_404(Tab, id=tab_id)
    if request.method == 'POST':
        base_view = request.POST.get('base_view')
        name = request.POST.get('name')
        x_field = request.POST.get('x_axis')
        y_field = request.POST.get('y_axis')
        chart_type = request.POST.get('chart_type')

        base_chart, created = BaseCharts.objects.get_or_create(base_view=base_view)

        TabCharts.objects.create(
            base_chart=base_chart,
            parent_tab=tab,
            name=name,
            x_field=x_field,
            y_field=y_field,
            chart_type=chart_type,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        return redirect(request.META.get('HTTP_REFERER'))
    
    return redirect(request.META.get('HTTP_REFERER'))


def chart_details(request, chart_id):
    base_chart = get_object_or_404(BaseCharts, id=chart_id)

    chart_data = {}
    for chart in TabCharts.objects.filter(base_chart=base_chart):
        tab = chart.parent_tab

        content_type = ContentType.objects.get(app_label=tab.content_type.app_label, model=tab.content_type.model)
        db_field_names = [field.name for field in content_type.model_class()._meta.get_fields() if not field.is_relation]
        chart_model = content_type.model_class()

        try:
            user_order = ColumnOrder.objects.get(user=request.user, table_name=f'{chart_model.__name__}', tab_id=f"{tab.id}")
            column_names = [col['key'] for col in user_order.column_order if col['key'] is not None]
            ordered_fields = column_names
        except ColumnOrder.DoesNotExist:
            ordered_fields = db_field_names

        field_dict = {field.key: field for field in tab.hide_show_filters.all()}
        field_names = [field_dict[key] for key in ordered_fields if key in field_dict]

        selected_rows = SelectedRows.objects.filter(
            model=f'{tab.content_type.model}', 
            model_choice=ModelChoices.TAB,
            tab_id=tab.id
        ).values_list('rows', flat=True)
        selected_rows = [int(item) for row in selected_rows for item in row.split(',')]

        # Snapshot
        latest_snapshot = ''
        summary = None
        snapshot_filter = {}

        if not tab.is_dynamic_query:
            try:
                content_type = ContentType.objects.get(model=chart_model.__name__.lower())
                snapshots = InstantUpload.objects.filter(content_type=content_type).order_by('-created_at')
                snapshot = request.GET.get('snapshot')

                if snapshot and not snapshot == 'all':
                    summary = InstantUpload.objects.get(id=snapshot)
                    snapshot_filter['loader_instance'] = summary.pk
                
                elif snapshot and snapshot == 'all':
                    snapshot_filter= {}
                
                elif tab.snapshot == 'latest':
                    latest_snapshot = snapshots.latest('created_at')
                    snapshot_filter['loader_instance'] = latest_snapshot.pk
                
                elif tab.snapshot and not tab.snapshot == 'all':
                    summary = InstantUpload.objects.get(id=int(tab.snapshot))
                    snapshot_filter['loader_instance'] = int(tab.snapshot)
                
                elif tab.snapshot and tab.snapshot == 'all':
                    snapshot_filter= {}
                
            except:
                pass
        
        else:
            snapshots = chart_model.objects.exclude(snapshot=None).values('snapshot').distinct()

        filter_string = {}
        combined_q_objects, user_unique_filter, user_query_conditions, user_count_filters = same_key_filter(tab.saved_filters.filter(field_type=FieldType.TEXT), return_count_filters=True)

        pre_filters = {}
        if tab.pre_filters:
            pre_filters = eval(tab.pre_filters)
        
        if tab.is_dynamic_query:
            query_snapshot = tab.query_snapshot
            if request.GET.get('query_snapshot'):
                query_snapshot = request.GET.get('query_snapshot')
            else:
                query_snapshot = tab.query_snapshot
            

            if query_snapshot and query_snapshot != 'all':
                parsed_datetime = isoparse(query_snapshot)
                snapshot_filter['snapshot'] = parsed_datetime
        
        # for date range
        date_string, date_unique_filter, date_query_conditions, date_count_filters = common_date_filter(tab.saved_filters.filter(field_type=FieldType.DATE), return_count_filters=True)
        filter_string.update(date_string)
        
        # for integer range
        int_string, int_unique_filter, int_query_conditions, int_count_filters = common_integer_filter(tab.saved_filters.filter(field_type=FieldType.INT), return_count_filters=True)
        filter_string.update(int_string)

        # for float range
        float_string, float_unique_filter, float_query_conditions, float_count_filters = common_float_filter(tab.saved_filters.filter(field_type=FieldType.FLOAT), return_count_filters=True)
        filter_string.update(float_string)


        base_queryset = chart_model.objects.filter(combined_q_objects).filter(**filter_string).filter(**snapshot_filter).filter(**pre_filters)
        order_by = tab.order_by
        if 'similarity' in order_by:
            order_by = 'pk'

        queryset = base_queryset
        if hasattr(chart_model, 'parent'):
            queryset = queryset.filter(parent=None)
            try:
                queryset = queryset.filter(action_status=ActionStatus.IS_ACTIVE)
            except:
                pass
        
        if user_query_conditions:
            queryset = queryset.filter(user_query_conditions)
        if date_query_conditions:
            queryset = queryset.filter(date_query_conditions)
        if int_query_conditions:
            queryset = queryset.filter(int_query_conditions)
        if float_query_conditions:
            queryset = queryset.filter(float_query_conditions)

        if user_count_filters:
            queryset = common_count_filter(user_count_filters, base_queryset, queryset, ordered_fields)
        elif date_count_filters:
            queryset = common_count_filter(date_count_filters, base_queryset, queryset, ordered_fields)
        elif int_count_filters:
            queryset = common_count_filter(int_count_filters, base_queryset, queryset, ordered_fields)
        elif float_count_filters:
            queryset = common_count_filter(float_count_filters, base_queryset, queryset, ordered_fields)
        else:
            if order_by in ['count', '-count']:
                order_by = 'pk'

        order_by = order_by or 'pk'
        queryset = queryset.order_by(order_by)

        table_name = f"{tab.content_type.app_label}_{tab.content_type.model}"
        if user_unique_filter:
            queryset = common_unique_filter(request, user_unique_filter, queryset, snapshot_filter, table_name)
        if date_unique_filter:
            queryset = common_unique_filter(request, date_unique_filter, queryset, snapshot_filter, table_name)
        if int_unique_filter:
            queryset = common_unique_filter(request, int_unique_filter, queryset, snapshot_filter, table_name)
        if float_unique_filter:
            queryset = common_unique_filter(request, float_unique_filter, queryset, snapshot_filter, table_name)

        if selected_rows:
            queryset = queryset.annotate(
                order_priority=Case(
                    *[When(pk=row_id, then=0) for row_id in selected_rows],
                    default=1,
                    output_field=IntegerField(),
                )
            ).order_by('order_priority')

        chart_list = software_filter(request, queryset, ordered_fields, search_value=tab.search, search_mode=tab.search_mode)
        mode = tab.search_mode
        if mode and mode == "graic" and chart_list:
            if 'similarity' not in ordered_fields:
                ordered_fields.insert(0, 'similarity')

        all_dates = []

        for item in chart_list:
            x_value = getattr(item, chart.x_field)

            if chart.x_field in chart_model.date_fields_to_convert and x_value:
                x_value = datetime.fromtimestamp(int(x_value)).strftime("%Y-%m-%d")

            all_dates.append(x_value)

        series_data = []

        if chart.y_field:
            for item in chart_list:
                x_value = getattr(item, chart.x_field)
                if chart.x_field in chart_model.date_fields_to_convert and x_value:
                    x_value = datetime.fromtimestamp(int(x_value)).strftime("%Y-%m-%d")
                y_value = getattr(item, chart.y_field)
                series_data.append({"x": x_value, "y": y_value})
        else:
            date_counts = Counter(all_dates)
            for x_value, count in date_counts.items():
                series_data.append({"x": x_value, "y": count})

        fields = get_model_fields(f'{chart_model.__name__}', tab.pre_columns)
        saved_filters = list(SavedFilter.objects.filter(
            parent=ModelChoices.TAB, tab_id=tab.id
        ).values())
        for filter in saved_filters:
            if 'created_at' in filter:
                filter['created_at'] = filter['created_at'].isoformat()

        saved_filters_json = json.dumps(saved_filters)

        chart_data[str(chart.id)] = {
            'name': chart.name,
            'type': chart.chart_type.lower(),
            'x_field': chart.x_field,
            'y_field': chart.y_field,
            'data': series_data,
            'db_field_names': db_field_names,
            'fields': fields,
            'tab_id': tab.id,
            'saved_filters': saved_filters_json
        }
            

    context = {
        'base_chart': base_chart,
        'tabs': Tab.objects.filter(base_view=base_chart.base_view).order_by('created_at'),
        'charts': BaseCharts.objects.filter(base_view=base_chart.base_view),
        'chart_data': json.dumps(chart_data, cls=DjangoJSONEncoder)
    }
    return render(request, 'apps/charts/chart_details.html', context)


def edit_chart(request, chart_id):
    chart = get_object_or_404(TabCharts, pk=chart_id)
    if request.method == 'POST':
        chart.name = request.POST.get('name', chart.name)
        chart.chart_type = request.POST.get('chart_type', chart.chart_type)
        # chart.x_field = request.POST.get('x_field', chart.x_field)
        # chart.y_field = request.POST.get('y_field', chart.y_field)
        chart.save()

        return redirect(request.META.get('HTTP_REFERER'))
    
    return redirect(request.META.get('HTTP_REFERER'))


def delete_chart(request, chart_id):
    chart = get_object_or_404(TabCharts, pk=chart_id)
    chart.delete()

    return redirect(request.META.get('HTTP_REFERER'))