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
    Image,
    ImageLoader
)
from django.http import HttpResponse
from django.views import View
from django.http import JsonResponse
from datetime import datetime
from django.db.models import F

from apps.tables.calculations import calculate_contract_value, calculate_remaining_days
    

# Create your views here.

def create_images_filter(request, img_loader_id):
    img_loader = ImageLoader.objects.get(id=img_loader_id)
    # ==== Date range filter ======
    if request.method == "POST":
        from_dates = request.POST.getlist('from_date')
        to_dates = request.POST.getlist('to_date')
        keys = request.POST.getlist('key_date_range')

        if len(from_dates) == len(to_dates) == len(keys):
            for key, from_date, to_date in zip(keys, from_dates, to_dates):
                existing_record = DateRangeFilter.objects.filter(
                    userID=get_user_id(request),
                    parent=ModelChoices.IMAGES,
                    key=key,
                    img_loader_id=img_loader.id
                ).first()

                if existing_record:
                    if from_date:
                        existing_record.from_date = from_date
                    else:
                        existing_record.from_date = None
                    if to_date:
                        existing_record.to_date = to_date
                    else:
                        existing_record.to_date = None
                    existing_record.save()
                else:
                    date_filter = DateRangeFilter.objects.create(
                        userID=get_user_id(request),
                        parent=ModelChoices.IMAGES,
                        key=key,
                        img_loader_id=img_loader.id
                    )
                    if from_date:
                        date_filter.from_date = from_date
                    if to_date:
                        date_filter.to_date = to_date
                    
                    date_filter.save()

        # ==== Integer value range ======
        from_numbers = request.POST.getlist('from_number')
        to_numbers = request.POST.getlist('to_number')
        keys = request.POST.getlist('key_int_range')


        if len(from_numbers) == len(to_numbers) == len(keys):
            for key, from_number, to_number in zip(keys, from_numbers, to_numbers):
                existing_record = IntRangeFilter.objects.filter(
                    userID=get_user_id(request),
                    parent=ModelChoices.IMAGES,
                    key=key,
                    img_loader_id=img_loader.id
                ).first()

                if existing_record:
                    if from_number:
                        existing_record.from_number = from_number
                    else:
                        existing_record.from_number = None

                    if to_number:
                        existing_record.to_number = to_number
                    else:
                        existing_record.to_number = None
                        
                    existing_record.save()
                else:
                    int_filter = IntRangeFilter.objects.create(
                        userID=get_user_id(request),
                        parent=ModelChoices.IMAGES,
                        key=key,
                        img_loader_id=img_loader.id
                    )
                    if from_number:
                        int_filter.from_number = from_number
                    if to_number:
                        int_filter.to_number = to_number
                    
                    int_filter.save()
    
        # ==== Float value range ======
        from_float_numbers = request.POST.getlist('from_float_number')
        to_float_numbers = request.POST.getlist('to_float_number')
        float_keys = request.POST.getlist('key_float_range')

        
        if len(from_float_numbers) == len(to_float_numbers) == len(float_keys):
            for key, from_float_number, to_float_number in zip(float_keys, from_float_numbers, to_float_numbers):
                existing_record = FloatRangeFilter.objects.filter(
                    userID=get_user_id(request),
                    parent=ModelChoices.IMAGES,
                    key=key,
                    img_loader_id=img_loader.id
                ).first()

                if existing_record:
                    if from_float_number:
                        existing_record.from_float_number = from_float_number
                    else:
                        existing_record.from_float_number = None

                    if to_float_number:
                        existing_record.to_float_number = to_float_number
                    else:
                        existing_record.to_float_number = None
                        
                    existing_record.save()
                else:
                    float_filter = FloatRangeFilter.objects.create(
                        userID=get_user_id(request),
                        parent=ModelChoices.IMAGES,
                        key=key,
                        img_loader_id=img_loader.id
                    )
                    if from_float_number:
                        float_filter.from_float_number = from_float_number
                    if to_float_number:
                        float_filter.to_float_number = to_float_number
                    
                    float_filter.save()
        
        # ==== normal user filter ======
        values = request.POST.getlist('value')
        value_change = request.POST.getlist('value_change')

        keys = request.POST.getlist('key')
        keys_change = request.POST.getlist('key_change')
        change_field_id = request.POST.getlist('change_field_id')


        if keys and value_change:
            key = keys[0]
            value = value_change[len(value_change) - 1]

            UserFilter.objects.create(
                userID=get_user_id(request),
                parent=ModelChoices.IMAGES,
                key=key,
                img_loader_id=img_loader.id,
                value=value
            )
        
        elif keys_change and value_change:
            for i in range(len(value_change)):
                key = keys_change[i]
                value = value_change[i]

                id = change_field_id[i]
                existing_record = UserFilter.objects.get(
                    userID=get_user_id(request),
                    parent=ModelChoices.IMAGES,
                    id=id,
                    img_loader_id=img_loader.id
                )
                if existing_record:
                    existing_record.value = value
                    existing_record.key = key
                    existing_record.save()
        
        else:
            for i in range(len(value_change)):
                key = keys_change[i]
                value = value_change[i]
                id = change_field_id[i]

                existing_record = UserFilter.objects.get(
                    userID=get_user_id(request),
                    parent=ModelChoices.IMAGES,
                    id=id,
                    img_loader_id=img_loader.id
                )

                if existing_record:
                    existing_record.value = value
                    existing_record.key = key
                    existing_record.save()

        return redirect(request.META.get('HTTP_REFERER'))
    

def create_images_page_items(request, img_loader_id):
    img_loader = ImageLoader.objects.get(id=img_loader_id)
    if request.method == 'POST':
        items = request.POST.get('items')
        page_items, created = PageItems.objects.update_or_create(
            userID=get_user_id(request),
            parent=ModelChoices.IMAGES,
            img_loader_id=img_loader.id,
            defaults={'items_per_page':items}
        )
        return redirect(request.META.get('HTTP_REFERER'))

def create_images_hide_show_filter(request, img_loader_id):
    img_loader = ImageLoader.objects.get(id=img_loader_id)
    if request.method == "POST":
        data_str = list(request.POST.keys())[0]
        data = json.loads(data_str)


        HideShowFilter.objects.update_or_create(
            userID=get_user_id(request),
            parent=ModelChoices.IMAGES,
            key=data.get('key'),
            img_loader_id=img_loader.id,
            defaults={'value': data.get('value')}
        )

        response_data = {'message': 'Model updated successfully'}
        return JsonResponse(response_data)

    return JsonResponse({'error': 'Invalid request'}, status=400)
    
def delete_images_filter(request, id):
    filter_instance = UserFilter.objects.get(id=id, userID=get_user_id(request), parent=ModelChoices.IMAGES)
    filter_instance.delete()
    return redirect(request.META.get('HTTP_REFERER'))

def delete_images_daterange_filter(request, id):
    date_filter = DateRangeFilter.objects.get(id=id, userID=get_user_id(request), parent=ModelChoices.IMAGES)
    date_filter.delete()
    return redirect(request.META.get('HTTP_REFERER'))

def delete_images_intrange_filter(request, id):
    int_filter = IntRangeFilter.objects.get(id=id, userID=get_user_id(request), parent=ModelChoices.IMAGES)
    int_filter.delete()
    return redirect(request.META.get('HTTP_REFERER'))

def delete_images_floatrange_filter(request, id):
    float_filter = FloatRangeFilter.objects.get(id=id, userID=get_user_id(request), parent=ModelChoices.IMAGES)
    float_filter.delete()
    return redirect(request.META.get('HTTP_REFERER'))


def images(request, id):
    image_loader = ImageLoader.objects.get(id=id)
    db_field_names = [field.name for field in Image._meta.get_fields() if not field.is_relation]

    # Snapshot
    latest_snapshot, summary, snapshot_filter, snapshots = common_snapshot_filter(request, 'image')

    field_names = []
    for field_name in db_field_names:
        fields, created = HideShowFilter.objects.get_or_create(
            key=field_name, 
            userID=get_user_id(request), 
            parent=ModelChoices.IMAGES,
            img_loader_id=image_loader.id
        )
        field_names.append(fields)

    page_items = PageItems.objects.filter(
        userID=get_user_id(request), 
        parent=ModelChoices.IMAGES,
        img_loader_id=image_loader.id
    ).last()
    items = 25
    if page_items:
        items = page_items.items_per_page

    filter_string = {}
    pre_filter_string = {}
    # pre_filter_string['Surname__icontains'] = ''

    filter_instance = UserFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGES, img_loader_id=image_loader.id)
    combined_q_objects, unique_filter, count_filters = same_key_filter(filter_instance, return_count_filters=True)

    # for date range
    date_filter_instance = DateRangeFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGES, img_loader_id=image_loader.id)
    date_string = common_date_filter(date_filter_instance)
    filter_string.update(date_string)
    
    # for integer range
    int_filter_instance = IntRangeFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGES, img_loader_id=image_loader.id)
    int_string = common_integer_filter(int_filter_instance)
    filter_string.update(int_string)

    # for float range
    float_filter_instance = FloatRangeFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGES, img_loader_id=image_loader.id)
    float_string = common_float_filter(float_filter_instance)
    filter_string.update(float_string)

    order_by = request.GET.get('order_by', 'id')
    base_queryset = image_loader.images.filter(**filter_string).filter(**pre_filter_string).filter(combined_q_objects).filter(**snapshot_filter)
    queryset = base_queryset
    
    if count_filters:
        queryset = common_count_filter(count_filters, base_queryset, queryset, db_field_names)
    else:
        if order_by == 'count' or order_by == '-count':
            order_by = 'id'

    queryset = queryset.order_by(order_by)

    if unique_filter:
        queryset = common_unique_filter(request, unique_filter, queryset, snapshot_filter, 'tables_image')

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
        return redirect('images')
    except EmptyPage:
        return redirect('images') 

    read_only_fields = ('id',)
    pre_column = ('id',)
    compulsory_fields = ()
    
    COMBOS = {}
    #COMBOS['Contract_Type'] = TableDropdownSubItem.objects.filter(item__item='Contract_Type').values_list('subitem', flat=True)

    context = {
        'segment'  : 'images',
        'parent'   : 'dashboard',
        'softwares' : softwares,
        'field_names': field_names,
        'db_field_names': db_field_names,
        'filter_instance': filter_instance,
        'date_filter_instance': date_filter_instance,
        'items': items,
        'read_only_fields': read_only_fields,
        'total_items': image_loader.images.filter(**pre_filter_string).filter(**snapshot_filter).count(),
        'pre_column': pre_column,
        'COMBOS': COMBOS,
        'date_picker_fields': Image.date_fields_to_convert,
        'compulsory_fields': compulsory_fields,
        'fav_name': 'Images',
        'int_filter_instance': int_filter_instance,
        'int_fields': Image.integer_fields,
        'float_filter_instance': float_filter_instance,
        'float_fields': Image.float_fields,
        'encrypted_fields': Image.encrypted_fields,
        'image_loader': image_loader,

        # snapshots
        'snapshots': snapshots,
        'latest_snapshot': latest_snapshot,
        'selected_snapshot': summary
    }
    
    return render(request, 'apps/images.html', context)


@login_required(login_url='/users/signin/')
def create_images(request):
    if request.method == 'POST':
        software_data = {}
        for attribute, value in request.POST.items():
            if attribute == 'csrfmiddlewaretoken':
                continue

            if attribute not in Image.date_fields_to_convert:
                if attribute in Image.integer_fields:
                    software_data[attribute] = int(value) if value else None
                elif attribute in Image.float_fields:
                    software_data[attribute] = float(value) if value else None
                else:
                    software_data[attribute] = value if value else ''
            else:
                unix_time = datetime.strptime(datetime.now().strftime("%Y-%m-%dT%H:%M"), "%Y-%m-%dT%H:%M").timestamp()
                if value:
                    unix_time = datetime.strptime(value, "%Y-%m-%dT%H:%M").timestamp()
                software_data[attribute] = unix_time

        Image.objects.create(**software_data)

    return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='/users/signin/')
def delete_images(request, id):
    software = Image.objects.get(id=id)
    software.delete()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='/users/signin/')
def update_images(request, id):
    software = Image.objects.get(id=id)

    if request.method == 'POST':
        for attribute, value in request.POST.items():
            if attribute == 'csrfmiddlewaretoken':
                continue

            if value == '':
                if attribute in Image.integer_fields:
                    value = None
                elif attribute in Image.float_fields:
                    value = None
                else:
                    continue
            
            setattr(software, 'Total_Contract_Value_Per_Month_Excluding_VAT', calculate_contract_value(request))
            setattr(software, 'Contract_Remainder_In_Days', calculate_remaining_days(request))
           

            if not attribute in Image.date_fields_to_convert:
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
    def get(self, request, id):
        image_loader = ImageLoader.objects.get(id=id)
        db_field_names = [field.name for field in Image._meta.get_fields() if not field.is_relation]

        # Snapshot
        latest_snapshot, summary, snapshot_filter, snapshots = common_snapshot_filter(request, 'image')

        fields = []
        pre_column = ('id',)

        show_fields = HideShowFilter.objects.filter(
            value=False, 
            userID=get_user_id(request), 
            parent=ModelChoices.IMAGES,
            img_loader_id=image_loader.id
        )
        for field in show_fields:
            if field.key not in pre_column:
                fields.append(field.key)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="images.csv"'       

        filter_string = {}
        filter_instance = UserFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGES, img_loader_id=image_loader.id)
        combined_q_objects, unique_filter, count_filters = same_key_filter(filter_instance, return_count_filters=True)

        # for date range
        date_filter_instance = DateRangeFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGES, img_loader_id=image_loader.id)
        date_string = common_date_filter(date_filter_instance)
        filter_string.update(date_string)
        
        # for integer range
        int_filter_instance = IntRangeFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGES, img_loader_id=image_loader.id)
        int_string = common_integer_filter(int_filter_instance)
        filter_string.update(int_string)

        # for float range
        float_filter_instance = FloatRangeFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.IMAGES, img_loader_id=image_loader.id)
        float_string = common_float_filter(float_filter_instance)
        filter_string.update(float_string)

        order_by = request.GET.get('order_by', 'id')
        base_queryset = image_loader.images.filter(**filter_string).filter(combined_q_objects).filter(**snapshot_filter)
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
            queryset = common_unique_filter(request, unique_filter, queryset, snapshot_filter, 'tables_image')

        softwares = software_filter(request, queryset, db_field_names)

        writer = csv.writer(response)
        writer.writerow(fields) 

        for software in softwares:
            row_data = []
            for field in fields:
                if field in Image.date_fields_to_convert:
                    unix_timestamp = getattr(software, field)
                    if unix_timestamp:
                        date_time = datetime.utcfromtimestamp(unix_timestamp)
                        formatted_date = date_time.strftime('%b %d %Y %I:%M%p')
                        row_data.append(formatted_date)
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
        response_pdf['Content-Disposition'] = 'attachment; filename="images.pdf"'

        pdf = canvas.Canvas(buffer)

        page_number = request.GET.get('page', 1)
        items_per_page = 25

        softwares = Image.objects.all()
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
