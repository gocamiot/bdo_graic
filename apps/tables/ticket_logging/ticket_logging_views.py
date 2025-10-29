import csv, json
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from apps.tables.utils import (
    software_filter, 
    same_key_filter, 
    common_unique_filter,
    common_count_filter,
    get_user_id,
    user_filter_common_func,
    create_page_items,
    create_hide_show_filter,
    common_snapshot_filter, get_model_fields,
    common_date_filter, common_integer_filter, common_float_filter
)
from apps.tables.models import (
    UserFilter, 
    PageItems, 
    HideShowFilter, 
    DateRangeFilter, 
    IntRangeFilter, 
    FloatRangeFilter, 
    ModelChoices, 
    TicketLogging,
    Tab, SelectedRows
)
from home.models import ColumnOrder
from apps.common.models import SavedFilter, FieldType
from django.http import HttpResponse
from django.views import View
from django.http import JsonResponse
from datetime import datetime, timedelta, timezone
from django.db.models import F, Case, When, IntegerField
from openpyxl import Workbook


from apps.tables.calculations import calculate_contract_value, calculate_remaining_days
    

# Create your views here.

def create_ticket_logging_filter(request):
    if request.method == 'POST':
        user_filter_common_func(request, 'TicketLogging', 'TICKET_LOGGING')
    return redirect(request.META.get('HTTP_REFERER'))

def create_ticket_logging_page_items(request):
    if request.method == 'POST':
        create_page_items(request, 'TICKET_LOGGING')
        return redirect(request.META.get('HTTP_REFERER'))

def create_ticket_logging_hide_show_filter(request):
    if request.method == "POST":
        response_data = create_hide_show_filter(request, 'TICKET_LOGGING')
        return JsonResponse(response_data)

    return JsonResponse({'error': 'Invalid request'}, status=400)
    
def delete_ticket_logging_filter(request, id):
    filter_instance = UserFilter.objects.get(id=id, userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING)
    filter_instance.delete()
    return redirect(request.META.get('HTTP_REFERER'))

def delete_ticket_logging_daterange_filter(request, id):
    date_filter = DateRangeFilter.objects.get(id=id, userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING)
    date_filter.delete()
    return redirect(request.META.get('HTTP_REFERER'))

def delete_ticket_logging_intrange_filter(request, id):
    int_filter = IntRangeFilter.objects.get(id=id, userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING)
    int_filter.delete()
    return redirect(request.META.get('HTTP_REFERER'))

def delete_ticket_logging_floatrange_filter(request, id):
    float_filter = FloatRangeFilter.objects.get(id=id, userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING)
    float_filter.delete()
    return redirect(request.META.get('HTTP_REFERER'))

def ticket_logging(request):
    db_field_names = [field.name for field in TicketLogging._meta.get_fields() if not field.is_relation]
    try:
        user_order = ColumnOrder.objects.get(
            user=request.user, 
            table_name='TicketLogging',
            favorite_id__isnull=True,
            finding_id__isnull=True,
            img_loader_id__isnull=True,
            unique_id__isnull=True,
            tab_id__isnull=True
        )
        column_names = [col['key'] for col in user_order.column_order if col['key'] is not None]
        ordered_fields = column_names
    except ColumnOrder.DoesNotExist:
        ordered_fields = db_field_names

    selected_rows = SelectedRows.objects.filter(
        model='ticketlogging', 
        model_choice=ModelChoices.TICKET_LOGGING
    ).values_list('rows', flat=True)
    selected_rows = [int(item) for row in selected_rows for item in row.split(',')]

    # Snapshot
    latest_snapshot, summary, snapshot_filter, snapshots = common_snapshot_filter(request, 'ticketlogging')

    field_names = []
    for field_name in ordered_fields:
        fields, created = HideShowFilter.objects.get_or_create(key=field_name, userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING)
        field_names.append(fields)

    page_items = PageItems.objects.filter(userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING).last()
    items = 25
    if page_items:
        items = page_items.items_per_page

    filter_string = {}
    pre_filter_string = {}
    # pre_filter_string['Surname__icontains'] = ''

    filter_instance = SavedFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING, field_type=FieldType.TEXT)
    combined_q_objects, user_unique_filter, user_query_conditions, user_count_filters = same_key_filter(filter_instance, return_count_filters=True)

    # for date range
    date_filter_instance = SavedFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING, field_type=FieldType.DATE)
    date_string, date_unique_filter, date_query_conditions, date_count_filters = common_date_filter(date_filter_instance, return_count_filters=True)
    filter_string.update(date_string)
    
    # for integer range
    int_filter_instance = SavedFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING, field_type=FieldType.INT)
    int_string, int_unique_filter, int_query_conditions, int_count_filters = common_integer_filter(int_filter_instance, return_count_filters=True)
    filter_string.update(int_string)

    # for float range
    float_filter_instance = SavedFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING, field_type=FieldType.FLOAT)
    float_string, float_unique_filter, float_query_conditions, float_count_filters = common_float_filter(float_filter_instance, return_count_filters=True)
    filter_string.update(float_string)

    order_by = request.GET.get('order_by', 'ID')
    if 'similarity' in order_by:
        order_by = 'pk'

    base_queryset = TicketLogging.objects.filter(**filter_string).filter(**pre_filter_string).filter(combined_q_objects).filter(**snapshot_filter)
    queryset = base_queryset
    
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
        if order_by == 'count' or order_by == '-count':
            order_by = 'ID'

    queryset = queryset.order_by(order_by)

    if user_unique_filter:
        queryset = common_unique_filter(request, user_unique_filter, queryset, snapshot_filter, 'tables_ticketlogging')
    if date_unique_filter:
        queryset = common_unique_filter(request, date_unique_filter, queryset, snapshot_filter, 'tables_ticketlogging')
    if int_unique_filter:
        queryset = common_unique_filter(request, int_unique_filter, queryset, snapshot_filter, 'tables_ticketlogging')
    if float_unique_filter:
        queryset = common_unique_filter(request, float_unique_filter, queryset, snapshot_filter, 'tables_ticketlogging')

    # Order by
    if order_by == 'count' and 'count' not in ordered_fields:
        queryset = queryset.order_by(F('count').desc(nulls_last=True))
    else:
        queryset = queryset.order_by(order_by)
    
    if selected_rows:
        queryset = queryset.annotate(
            order_priority=Case(
                *[When(ID=row_id, then=0) for row_id in selected_rows],
                default=1,
                output_field=IntegerField(),
            )
        ).order_by('order_priority')

    software_list = software_filter(request, queryset, ordered_fields)
    mode = request.GET.get('mode')
    if mode == "graic" and software_list:
        if 'similarity' not in ordered_fields:
            ordered_fields.insert(0, 'similarity')

    page = request.GET.get('page', 1)
    paginator = Paginator(software_list, items)
    
    try:
        softwares = paginator.page(page)
    except PageNotAnInteger:
        return redirect('ticket_logging')
    except EmptyPage:
        return redirect('ticket_logging') 

    read_only_fields = ('fts', 'ID', 'loader_instance', 'json_data', 'hash_data',)
    pre_column = ('fts', 'ID', 'loader_instance', 'json_data', 'hash_data',)
    compulsory_fields = ()
    
    COMBOS = {}
    #COMBOS['Contract_Type'] = TableDropdownSubItem.objects.filter(item__item='Contract_Type').values_list('subitem', flat=True)

    fields = get_model_fields('TicketLogging', pre_column)
    saved_filters = list(SavedFilter.objects.filter(
        userID=request.user.id, parent=ModelChoices.TICKET_LOGGING
    ).values())
    for filter in saved_filters:
        if 'created_at' in filter:
            filter['created_at'] = filter['created_at'].isoformat()
    saved_filters_json = json.dumps(saved_filters)

    context = {
        'segment'  : 'ticket_logging',
        'parent'   : 'tl',
        'softwares' : softwares,
        'field_names': field_names,
        'db_field_names': ordered_fields,
        'filter_instance': filter_instance,
        'date_filter_instance': date_filter_instance,
        'items': items,
        'read_only_fields': read_only_fields,
        'total_items': TicketLogging.objects.filter(**pre_filter_string).filter(**snapshot_filter).count(),
        'pre_column': pre_column,
        'COMBOS': COMBOS,
        'date_picker_fields': TicketLogging.date_fields_to_convert,
        'compulsory_fields': compulsory_fields,
        'fav_name': 'Ticket Logging',
        'int_filter_instance': int_filter_instance,
        'int_fields': TicketLogging.integer_fields,
        'float_filter_instance': float_filter_instance,
        'float_fields': TicketLogging.float_fields,
        'encrypted_fields': TicketLogging.encrypted_fields,
        'unique_filter': list(set(user_unique_filter + date_unique_filter + int_unique_filter + float_unique_filter)),
        'table_name': 'ticketlogging',
        'fields': fields,
        'saved_filters': saved_filters_json,
        'tabs': Tab.objects.filter(base_view='ticket_logging').order_by('created_at'),
        'join_model_instance': TicketLogging.join_model_instance if hasattr( TicketLogging, 'join_model_instance') else None,
        'selected_rows': selected_rows,
        'selected_rows_qs': software_list.filter(ID__in=selected_rows),

        # snapshots
        'snapshots': snapshots,
        'latest_snapshot': latest_snapshot,
        'selected_snapshot': summary
    }
    
    return render(request, 'apps/ticket_logging.html', context)


@login_required(login_url='/users/signin/')
def create_ticket_logging(request):
    if request.method == 'POST':
        software_data = {}
        for attribute, value in request.POST.items():
            if attribute == 'csrfmiddlewaretoken':
                continue

            if attribute not in TicketLogging.date_fields_to_convert:
                if attribute in TicketLogging.integer_fields:
                    software_data[attribute] = int(value) if value else None
                elif attribute in TicketLogging.float_fields:
                    software_data[attribute] = float(value) if value else None
                else:
                    software_data[attribute] = value if value else ''
            else:
                unix_time = datetime.strptime(datetime.now().strftime("%Y-%m-%dT%H:%M"), "%Y-%m-%dT%H:%M").timestamp()
                if value:
                    unix_time = datetime.strptime(value, "%Y-%m-%dT%H:%M").timestamp()
                software_data[attribute] = unix_time

        TicketLogging.objects.create(**software_data)

    return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='/users/signin/')
def delete_ticket_logging(request, id):
    software = TicketLogging.objects.get(ID=id)
    software.delete()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='/users/signin/')
def update_ticket_logging(request, id):
    software = TicketLogging.objects.get(ID=id)

    if request.method == 'POST':
        for attribute, value in request.POST.items():
            if attribute == 'csrfmiddlewaretoken':
                continue

            if value == '':
                if attribute in TicketLogging.integer_fields:
                    value = None
                elif attribute in TicketLogging.float_fields:
                    value = None
                else:
                    continue
            
            setattr(software, 'Total_Contract_Value_Per_Month_Excluding_VAT', calculate_contract_value(request))
            setattr(software, 'Contract_Remainder_In_Days', calculate_remaining_days(request))
           

            if not attribute in TicketLogging.date_fields_to_convert:
                setattr(software, attribute, value)
            else:
                unix_time = setattr(software, attribute, value)
                possible_formats = ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
                for format_str in possible_formats:
                    try:
                        if value:
                            unix_time = datetime.strptime(value, format_str).timestamp()
                            setattr(software, attribute, unix_time)
                            break
                    except ValueError:
                        pass 

        software.save()

    return redirect(request.META.get('HTTP_REFERER'))


# Export as CSV
class ExportCSVView(View):
    def get(self, request):
        db_field_names = [field.name for field in TicketLogging._meta.get_fields() if not field.is_relation]
        try:
            user_order = ColumnOrder.objects.get(
                user=request.user, 
                table_name='TicketLogging',
                favorite_id__isnull=True,
                finding_id__isnull=True,
                img_loader_id__isnull=True,
                unique_id__isnull=True,
                tab_id__isnull=True
            )
            column_names = [col['key'] for col in user_order.column_order if col['key'] is not None]
            ordered_fields = column_names
        except ColumnOrder.DoesNotExist:
            ordered_fields = db_field_names

        selected_rows = SelectedRows.objects.filter(
            model='ticketlogging', 
            model_choice=ModelChoices.TICKET_LOGGING
        ).values_list('rows', flat=True)
        selected_rows = [int(item) for row in selected_rows for item in row.split(',')]

        # Snapshot
        latest_snapshot, summary, snapshot_filter, snapshots = common_snapshot_filter(request, 'ticketlogging')

        fields = []
        pre_column = ('ID', 'loader_instance', 'hash_data', 'json_data', )

        # Show/Hide Filter Fields
        show_fields = HideShowFilter.objects.filter(value=False, userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING)
        show_fields_keys = {field.key for field in show_fields}

        # Construct final fields list respecting original model order
        for field in ordered_fields:
            # Ensure pre_column fields are not included
            if field not in pre_column and field in show_fields_keys:
                fields.append(field)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="ticket_logging.csv"'       

        filter_string = {}
        filter_instance = SavedFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING, field_type=FieldType.TEXT)
        combined_q_objects, user_unique_filter, user_query_conditions, user_count_filters = same_key_filter(filter_instance, return_count_filters=True)

        # for date range
        date_filter_instance = SavedFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING, field_type=FieldType.DATE)
        date_string, date_unique_filter, date_query_conditions, date_count_filters = common_date_filter(date_filter_instance, return_count_filters=True)
        filter_string.update(date_string)
        
        # for integer range
        int_filter_instance = SavedFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING, field_type=FieldType.INT)
        int_string, int_unique_filter, int_query_conditions, int_count_filters = common_integer_filter(int_filter_instance, return_count_filters=True)
        filter_string.update(int_string)

        # for float range
        float_filter_instance = SavedFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING, field_type=FieldType.FLOAT)
        float_string, float_unique_filter, float_query_conditions, float_count_filters = common_float_filter(float_filter_instance, return_count_filters=True)
        filter_string.update(float_string)

        order_by = request.GET.get('order_by', 'ID')
        base_queryset = TicketLogging.objects.filter(**filter_string).filter(combined_q_objects).filter(**snapshot_filter)
        queryset = base_queryset

        if user_query_conditions:
            queryset = queryset.filter(user_query_conditions)
        if date_query_conditions:
            queryset = queryset.filter(date_query_conditions)
        if int_query_conditions:
            queryset = queryset.filter(int_query_conditions)
        if float_query_conditions:
            queryset = queryset.filter(float_query_conditions)

        if user_count_filters:
            queryset = common_count_filter(user_count_filters, base_queryset, queryset, fields)
        elif date_count_filters:
            queryset = common_count_filter(date_count_filters, base_queryset, queryset, fields)
        elif int_count_filters:
            queryset = common_count_filter(int_count_filters, base_queryset, queryset, fields)
        elif float_count_filters:
            queryset = common_count_filter(float_count_filters, base_queryset, queryset, fields)
        else:
            if order_by == 'count' or order_by == '-count':
                order_by = 'ID'

        queryset = queryset.order_by(order_by)

        # Apply unique filters
        if user_unique_filter:
            queryset = common_unique_filter(request, user_unique_filter, queryset, snapshot_filter, 'tables_ticketlogging')
        if date_unique_filter:
            queryset = common_unique_filter(request, date_unique_filter, queryset, snapshot_filter, 'tables_ticketlogging')
        if int_unique_filter:
            queryset = common_unique_filter(request, int_unique_filter, queryset, snapshot_filter, 'tables_ticketlogging')
        if float_unique_filter:
            queryset = common_unique_filter(request, float_unique_filter, queryset, snapshot_filter, 'tables_ticketlogging')

        softwares = software_filter(request, queryset, ordered_fields)

        if 'selected_rows' in request.GET:
            softwares = softwares.filter(ID__in=selected_rows)

        writer = csv.writer(response)
        writer.writerow(fields) # Writes headers in the correct order

        for software in softwares:
            row_data = []
            for field in fields:
                if field in TicketLogging.date_fields_to_convert:
                    unix_timestamp = getattr(software, field)
                    if unix_timestamp:
                        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
                        date_time = epoch + timedelta(seconds=unix_timestamp)
                        formatted_date = date_time.strftime('%b %d %Y %I:%M%p')
                        row_data.append(formatted_date)
                    else: 
                        row_data.append("")
                else:
                    row_data.append(getattr(software, field))

            writer.writerow(row_data)

        return response

class ExportExcelView(View):
    def get_excel_workbook(self, request):
        db_field_names = [field.name for field in TicketLogging._meta.get_fields() if not field.is_relation]
        try:
            user_order = ColumnOrder.objects.get(
                user=request.user, 
                table_name='TicketLogging',
                favorite_id__isnull=True,
                finding_id__isnull=True,
                img_loader_id__isnull=True,
                unique_id__isnull=True,
                tab_id__isnull=True
            )
            column_names = [col['key'] for col in user_order.column_order if col['key'] is not None]
            ordered_fields = column_names
        except ColumnOrder.DoesNotExist:
            ordered_fields = db_field_names

        selected_rows = SelectedRows.objects.filter(
            model='ticketlogging',
            model_choice=ModelChoices.TICKET_LOGGING
        ).values_list('rows', flat=True)
        selected_rows = [int(item) for row in selected_rows for item in row.split(',')]

        latest_snapshot, summary, snapshot_filter, snapshots = common_snapshot_filter(request, 'ticketlogging')

        fields = []
        pre_column = ('ID', 'loader_instance', 'hash_data', 'json_data', )
        show_fields = HideShowFilter.objects.filter(value=False, userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING)
        show_fields_keys = {field.key for field in show_fields}

        for field in ordered_fields:
            if field not in pre_column and field in show_fields_keys:
                fields.append(field)

        filter_string = {}
        filter_instance = SavedFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING, field_type=FieldType.TEXT)
        combined_q_objects, user_unique_filter, user_query_conditions, user_count_filters = same_key_filter(filter_instance, return_count_filters=True)

        date_filter_instance = SavedFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING, field_type=FieldType.DATE)
        date_string, date_unique_filter, date_query_conditions, date_count_filters = common_date_filter(date_filter_instance, return_count_filters=True)
        filter_string.update(date_string)

        int_filter_instance = SavedFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING, field_type=FieldType.INT)
        int_string, int_unique_filter, int_query_conditions, int_count_filters = common_integer_filter(int_filter_instance, return_count_filters=True)
        filter_string.update(int_string)

        float_filter_instance = SavedFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.TICKET_LOGGING, field_type=FieldType.FLOAT)
        float_string, float_unique_filter, float_query_conditions, float_count_filters = common_float_filter(float_filter_instance, return_count_filters=True)
        filter_string.update(float_string)

        order_by = request.GET.get('order_by', 'ID')
        base_queryset = TicketLogging.objects.filter(**filter_string).filter(combined_q_objects).filter(**snapshot_filter)
        queryset = base_queryset

        if user_query_conditions:
            queryset = queryset.filter(user_query_conditions)
        if date_query_conditions:
            queryset = queryset.filter(date_query_conditions)
        if int_query_conditions:
            queryset = queryset.filter(int_query_conditions)
        if float_query_conditions:
            queryset = queryset.filter(float_query_conditions)

        if user_count_filters:
            queryset = common_count_filter(user_count_filters, base_queryset, queryset, fields)
        elif date_count_filters:
            queryset = common_count_filter(date_count_filters, base_queryset, queryset, fields)
        elif int_count_filters:
            queryset = common_count_filter(int_count_filters, base_queryset, queryset, fields)
        elif float_count_filters:
            queryset = common_count_filter(float_count_filters, base_queryset, queryset, fields)
        else:
            if order_by == 'count' or order_by == '-count':
                order_by = 'ID'

        queryset = queryset.order_by(order_by)

        if user_unique_filter:
            queryset = common_unique_filter(request, user_unique_filter, queryset, snapshot_filter, 'tables_ticketlogging')
        if date_unique_filter:
            queryset = common_unique_filter(request, date_unique_filter, queryset, snapshot_filter, 'tables_ticketlogging')
        if int_unique_filter:
            queryset = common_unique_filter(request, int_unique_filter, queryset, snapshot_filter, 'tables_ticketlogging')
        if float_unique_filter:
            queryset = common_unique_filter(request, float_unique_filter, queryset, snapshot_filter, 'tables_ticketlogging')

        softwares = software_filter(request, queryset, ordered_fields)

        if 'selected_rows' in request.GET:
            softwares = softwares.filter(ID__in=selected_rows)

        wb = Workbook()
        ws = wb.active
        ws.append(fields)
        
        for software in softwares:
            row_data = []
            for field in fields:
                value = getattr(software, field)
                if field in TicketLogging.date_fields_to_convert:
                    if value:
                        epoch = datetime(1970, 1, 1)
                        date_time = epoch + timedelta(seconds=value)
                        formatted_date = date_time.strftime('%b %d %Y %I:%M%p')
                        row_data.append(formatted_date)
                    else:
                        row_data.append("")
                else:
                    if isinstance(value, datetime):
                        value = value.replace(tzinfo=None)
                    row_data.append(value)
            ws.append(row_data)

        return wb

    def get(self, request):
        wb = self.get_excel_workbook(request)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="ticket_logging.xlsx"'
        wb.save(response)
        return response

from reportlab.pdfgen import canvas
from io import BytesIO
# Export as PDF
class ExportPDFView(View):
    def get(self, request):
        buffer = BytesIO()
        response_pdf = HttpResponse(content_type='application/pdf')
        response_pdf['Content-Disposition'] = 'attachment; filename="ticket_logging.pdf"'

        pdf = canvas.Canvas(buffer)

        page_number = request.GET.get('page', 1)
        items_per_page = 25

        softwares = TicketLogging.objects.all()
        paginator = Paginator(softwares, items_per_page)
        current_page_devices = paginator.get_page(page_number)

        y_position = 800

        for device in current_page_devices:
            pdf.drawString(100, y_position, f"ID: {device.ID}, DeviceName: {device.DeviceName}, OperatingSystem: {device.OperatingSystem}")
            y_position -= 20

        pdf.save()

        buffer.seek(0)
        response_pdf.write(buffer.getvalue())

        return response_pdf
