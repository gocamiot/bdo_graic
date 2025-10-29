import csv
import json
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
    common_snapshot_filter,
    common_date_filter, common_integer_filter, 
    common_float_filter, global_filter
)
from apps.tables.models import (
    UserFilter, 
    PageItems, 
    HideShowFilter, 
    DateRangeFilter, 
    IntRangeFilter, 
    FloatRangeFilter, 
    ModelChoices, 
    ImageLoader,
    Image,
    ActionStatus
)
from apps.tables.forms import ImageLoaderForm
from django.http import HttpResponse
from django.views import View
from django.http import JsonResponse
from datetime import datetime
from django.db.models import F
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse

from apps.tables.calculations import calculate_contract_value, calculate_remaining_days
    

# Create your views here.

def create_image_loader_filter(request):
    if request.method == 'POST':
        user_filter_common_func(request, 'IMAGE_LOADER')
    return redirect(request.META.get('HTTP_REFERER'))


def create_image_loader_page_items(request):
    if request.method == 'POST':
        create_page_items(request, 'IMAGE_LOADER')
        return redirect(request.META.get('HTTP_REFERER'))

def create_image_loader_hide_show_filter(request):
    if request.method == "POST":
        response_data = create_hide_show_filter(request, 'IMAGE_LOADER')
        return JsonResponse(response_data)

    return JsonResponse({'error': 'Invalid request'}, status=400)
    
def delete_image_loader_filter(request, id):
    filter_instance = UserFilter.objects.get(id=id, userID=get_user_id(request), parent=ModelChoices.IMAGE_LOADER)
    filter_instance.delete()
    return redirect(request.META.get('HTTP_REFERER'))

def delete_image_loader_daterange_filter(request, id):
    date_filter = DateRangeFilter.objects.get(id=id, userID=get_user_id(request), parent=ModelChoices.IMAGE_LOADER)
    date_filter.delete()
    return redirect(request.META.get('HTTP_REFERER'))

def delete_image_loader_intrange_filter(request, id):
    int_filter = IntRangeFilter.objects.get(id=id, userID=get_user_id(request), parent=ModelChoices.IMAGE_LOADER)
    int_filter.delete()
    return redirect(request.META.get('HTTP_REFERER'))

def delete_image_loader_floatrange_filter(request, id):
    float_filter = FloatRangeFilter.objects.get(id=id, userID=get_user_id(request), parent=ModelChoices.IMAGE_LOADER)
    float_filter.delete()
    return redirect(request.META.get('HTTP_REFERER'))

def image_loader(request):
    db_field_names = [field.name for field in ImageLoader._meta.get_fields() if not field.is_relation]

    # Snapshot
    latest_snapshot, summary, snapshot_filter, snapshots = common_snapshot_filter(request, 'imageloader')

    field_names = []
    for field_name in db_field_names:
        fields, created = HideShowFilter.objects.get_or_create(key=field_name, userID=get_user_id(request), parent=ModelChoices.IMAGE_LOADER)
        field_names.append(fields)

    page_items = PageItems.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGE_LOADER).last()
    items = 25
    if page_items:
        items = page_items.items_per_page

    filter_string = {}
    pre_filter_string = {}
    # pre_filter_string['Surname__icontains'] = ''

    filter_instance = UserFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGE_LOADER)
    combined_q_objects, unique_filter, count_filters = same_key_filter(filter_instance, return_count_filters=True)

    # for date range
    date_filter_instance = DateRangeFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGE_LOADER)
    date_string = common_date_filter(date_filter_instance)
    filter_string.update(date_string)
    
    # for integer range
    int_filter_instance = IntRangeFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGE_LOADER)
    int_string = common_integer_filter(int_filter_instance)
    filter_string.update(int_string)

    # for float range
    float_filter_instance = FloatRangeFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGE_LOADER)
    float_string = common_float_filter(float_filter_instance)
    filter_string.update(float_string)

    order_by = request.GET.get('order_by', 'id')
    base_queryset = ImageLoader.objects.filter(parent=None).filter(action_status=ActionStatus.IS_ACTIVE).filter(**filter_string).filter(**pre_filter_string).filter(combined_q_objects).filter(**snapshot_filter)
    queryset = base_queryset
    
    if count_filters:
        queryset = common_count_filter(count_filters, base_queryset, queryset, db_field_names)
    else:
        if order_by == 'count' or order_by == '-count':
            order_by = 'id'

    queryset = queryset.order_by(order_by)

    if unique_filter:
        queryset = common_unique_filter(request, unique_filter, queryset, snapshot_filter, 'tables_imageloader')

    # Order by
    if order_by == 'count' and 'count' not in db_field_names:
        queryset = queryset.order_by(F('count').desc(nulls_last=True))
    else:
        queryset = queryset.order_by(order_by)

    software_list = software_filter(request, queryset, db_field_names)

    page = request.GET.get('page', 1)
    paginator = Paginator(software_list, items)
    
    try:
        softwares = paginator.page(page)
    except PageNotAnInteger:
        return redirect('image_loader')
    except EmptyPage:
        return redirect('image_loader') 

    read_only_fields = ('id', 'version_control', 'images', 'action_status', 'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by', 'deleted_by', )
    pre_column = ('id', 'version_control', 'action_status', )
    compulsory_fields = ()
    richtext_fields = ('description', 'recommendation', )
    form = ImageLoaderForm()

    COMBOS = {}
    #COMBOS['Contract_Type'] = TableDropdownSubItem.objects.filter(item__item='Contract_Type').values_list('subitem', flat=True)

    context = {
        'segment'  : 'image_loader',
        'parent'   : 'dashboard',
        'softwares' : softwares,
        'field_names': field_names,
        'db_field_names': db_field_names,
        'filter_instance': filter_instance,
        'date_filter_instance': date_filter_instance,
        'items': items,
        'read_only_fields': read_only_fields,
        'total_items': ImageLoader.objects.filter(parent=None).filter(action_status=ActionStatus.IS_ACTIVE).filter(**pre_filter_string).filter(**snapshot_filter).count(),
        'pre_column': pre_column,
        'COMBOS': COMBOS,
        'date_picker_fields': ImageLoader.date_fields_to_convert,
        'compulsory_fields': compulsory_fields,
        'richtext_fields': richtext_fields,
        'fav_name': 'Image Loader',
        'int_filter_instance': int_filter_instance,
        'int_fields': ImageLoader.integer_fields,
        'float_filter_instance': float_filter_instance,
        'float_fields': ImageLoader.float_fields,
        'encrypted_fields': ImageLoader.encrypted_fields,
        'form': form,

        # snapshots
        'snapshots': snapshots,
        'latest_snapshot': latest_snapshot,
        'selected_snapshot': summary
    }
    
    return render(request, 'apps/image_loader.html', context)


@login_required(login_url='/users/signin/')
def create_image_loader(request):
    if request.method == 'POST':
        software_data = {}
        for attribute, value in request.POST.items():
            if attribute == 'csrfmiddlewaretoken':
                continue

            if attribute not in ImageLoader.date_fields_to_convert:
                if attribute in ImageLoader.integer_fields:
                    software_data[attribute] = int(value) if value else None
                elif attribute in ImageLoader.float_fields:
                    software_data[attribute] = float(value) if value else None
                else:
                    software_data[attribute] = value if value else ''
            else:
                unix_time = datetime.strptime(datetime.now().strftime("%Y-%m-%dT%H:%M"), "%Y-%m-%dT%H:%M").timestamp()
                if value:
                    unix_time = datetime.strptime(value, "%Y-%m-%dT%H:%M").timestamp()
                software_data[attribute] = unix_time
        
        software_data['created_by'] = request.user.email if request.user.email else request.user.username
        software_data['created_at'] = timezone.now()
        image_loader = ImageLoader.objects.create(**software_data)
        
        files = request.FILES.getlist('files')
        for file in files:
            image = Image.objects.create(image=file)
            image_loader.images.add(image)
            
            image_loader.save()

    return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='/users/signin/')
def delete_image_loader(request, id):
    software = ImageLoader.objects.get(id=id)
    software.action_status = ActionStatus.DELETED
    software.deleted_at = timezone.now()
    software.deleted_by = request.user.email if request.user.email else request.user.username
    software.images.all().delete()
    software.save()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='/users/signin/')
def update_image_loader(request, id):
    software = ImageLoader.objects.get(id=id)
    if request.method == 'POST':
        description = request.POST.get('description', '').strip()
        description_json = json.loads(description)
        description_html = description_json.get('html', '').strip()

        if not description_html or description_html == '<p><br></p>':
            messages.error(request, 'Description cannot be empty.')
            return redirect(request.META.get('HTTP_REFERER'))


        # fields = software._meta.get_fields()
        fields = [field.name for field in software._meta.get_fields() if not field.is_relation]

        fields_and_values = {}
        for field in fields:
            try:
                field_value = getattr(software, field)
                fields_and_values[field] = field_value
            except:
                continue

        fields_and_values.pop('id')
        # fields_and_values.pop('parent')
        fields_and_values.pop('created_at')
        fields_and_values.pop('created_by')
        fields_and_values.pop('updated_at')
        fields_and_values.pop('updated_by')
        fields_and_values.pop('version_control')

        if request.method == 'POST':
            for attribute, value in request.POST.items():
                if attribute == 'csrfmiddlewaretoken':
                    continue

                if value == '':
                    if attribute in ImageLoader.integer_fields:
                        value = None
                    elif attribute in ImageLoader.float_fields:
                        value = None
                    else:
                        continue

                if not attribute in ImageLoader.date_fields_to_convert:
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
            

            software.updated_by = request.user.email if request.user.email else request.user.username
            software.updated_at = timezone.now()
            software.version_control += 1
            software.save()

            files = request.FILES.getlist('files')
            for file in files:
                image = Image.objects.create(image=file)
                software.images.add(image)
                software.save()

            prev_software = ImageLoader.objects.create(
                **fields_and_values,
                version_control=software.version_control - 1
            )

            prev_software.parent = software
            prev_software.updated_by = software.updated_by
            prev_software.created_by = software.created_by
            prev_software.created_at = software.created_at
            prev_software.updated_at = timezone.now()
            prev_software.save()

            return redirect(reverse('image_loader'))

    db_field_names = [field.name for field in ImageLoader._meta.get_fields() if not field.is_relation]
    read_only_fields = ('id', 'version_control', 'images', 'action_status', 'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by', 'deleted_by', )
    pre_column = ('id', 'version_control', 'action_status', )
    compulsory_fields = ()
    richtext_fields = ('description', 'recommendation', )
    
    COMBOS = {}
    form = ImageLoaderForm(initial={
        'description': software.description,
        'recommendation': software.recommendation
    })

    context = {
        'segment'  : 'image_loader',
        'parent'   : 'audit_report',
        'software': software,
        'db_field_names': db_field_names,
        'read_only_fields': read_only_fields,
        'pre_column': pre_column,
        'date_picker_fields': ImageLoader.date_fields_to_convert,
        'compulsory_fields': compulsory_fields,
        'richtext_fields': richtext_fields,
        'fav_name': 'AD Users',
        'int_fields': ImageLoader.integer_fields,
        'float_fields': ImageLoader.float_fields,
        'COMBOS': COMBOS,
        'form': form
    }
    


    return render(request, 'apps/edit/image_loader.html', context)


# Export as CSV
class ExportCSVView(View):
    def get(self, request):
        db_field_names = [field.name for field in ImageLoader._meta.get_fields() if not field.is_relation]

        # Snapshot
        latest_snapshot, summary, snapshot_filter, snapshots = common_snapshot_filter(request, 'imageloader')

        fields = []
        pre_column = ('id', 'version_control',)
        richtext_fields = ('description', 'recommendation', )

        show_fields = HideShowFilter.objects.filter(value=False, userID=get_user_id(request), parent=ModelChoices.IMAGE_LOADER)
        for field in show_fields:
            if field.key not in pre_column:
                fields.append(field.key)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="image_loader.csv"'       

        filter_string = {}
        filter_instance = UserFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGE_LOADER)
        combined_q_objects, unique_filter, count_filters = same_key_filter(filter_instance, return_count_filters=True)

        # for date range
        date_filter_instance = DateRangeFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGE_LOADER)
        date_string = common_date_filter(date_filter_instance)
        filter_string.update(date_string)
        
        # for integer range
        int_filter_instance = IntRangeFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGE_LOADER)
        int_string = common_integer_filter(int_filter_instance)
        filter_string.update(int_string)

        # for float range
        float_filter_instance = FloatRangeFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGE_LOADER)
        float_string = common_float_filter(float_filter_instance)
        filter_string.update(float_string)

        order_by = request.GET.get('order_by', 'id')
        base_queryset = ImageLoader.objects.filter(parent=None).filter(action_status=ActionStatus.IS_ACTIVE).filter(**filter_string).filter(combined_q_objects).filter(**snapshot_filter)
        queryset = base_queryset

        if count_filters:
            queryset = common_count_filter(count_filters, base_queryset, queryset, db_field_names, fields, True)
        else:
            if order_by == 'count' or order_by == '-count':
                order_by = 'id'
            if 'count' in fields:
                fields.remove('count')

        queryset = queryset.order_by(order_by)

        if unique_filter:
            queryset = common_unique_filter(request, unique_filter, queryset, snapshot_filter, 'tables_imageloader')

        softwares = software_filter(request, queryset, db_field_names)

        writer = csv.writer(response)
        writer.writerow(fields) 

        for software in softwares:
            row_data = []
            for field in fields:
                if field in ImageLoader.date_fields_to_convert:
                    unix_timestamp = getattr(software, field)
                    if unix_timestamp:
                        date_time = datetime.utcfromtimestamp(unix_timestamp)
                        formatted_date = date_time.strftime('%b %d %Y %I:%M%p')
                        row_data.append(formatted_date)
                    else: 
                        row_data.append("")
                elif field in richtext_fields:
                    attribute = getattr(software, field, None)
                    if attribute and hasattr(attribute, 'html'):
                        row_data.append(attribute.html)
                    else:
                        row_data.append("")
                else:
                    row_data.append(getattr(software, field))

            writer.writerow(row_data)

        return response


from reportlab.pdfgen import canvas
from io import BytesIO
# Export as PDF
class ExportPDFView(View):
    def get(self, request):
        buffer = BytesIO()
        response_pdf = HttpResponse(content_type='application/pdf')
        response_pdf['Content-Disposition'] = 'attachment; filename="image_loader.pdf"'

        pdf = canvas.Canvas(buffer)

        page_number = request.GET.get('page', 1)
        items_per_page = 25

        softwares = ImageLoader.objects.all()
        paginator = Paginator(softwares, items_per_page)
        current_page_devices = paginator.get_page(page_number)

        y_position = 800

        for device in current_page_devices:
            pdf.drawString(100, y_position, f"id: {device.id}, DeviceName: {device.DeviceName}, OperatingSystem: {device.OperatingSystem}")
            y_position -= 20

        pdf.save()

        buffer.seek(0)
        response_pdf.write(buffer.getvalue())

        return response_pdf



def image_loader_version_control_dt(request, id):
    parent = ImageLoader.objects.get(id=id)
    db_field_names = [field.name for field in ImageLoader._meta.get_fields() if not field.is_relation]
    pre_column = ('id', 'version_control', 'action_status', )
    richtext_fields = ('description', 'recommendation', )

    order_by = request.GET.get('order_by', '-version_control')
    child_qs = ImageLoader.objects.filter(parent=parent).order_by(order_by)

    context = {
        'segment'  : 'image_loader',
        'parent'   : 'audit_report',
        # 'form'     : form,
        'softwares' : child_qs,
        'db_field_names': db_field_names,
        'pre_column': pre_column,
        'richtext_fields': richtext_fields
    }

    return render(request, 'apps/version_control/image_loader.html', context)