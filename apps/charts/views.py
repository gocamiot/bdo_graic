from django.shortcuts import render, redirect
#from apps.tables.models import Devices, ControlADUser, ControlADDevicesUnsupOS, ControlADDevices
from django.core import serializers
from datetime import datetime
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q
from apps.charts.models import UserFilter, DateFilter
from apps.tables.models import ModelChoices

# Create your views here.

def get_user_id(request):
    if request.user.is_authenticated:
        return request.user.pk
    else:
        return -1

def create_chart_filter(request):
    if request.method == 'POST':
        values = request.POST.getlist('device_type')
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')

        if values:
            UserFilter.objects.update(status=False)
            for value in values:
                obj, created = UserFilter.objects.update_or_create(
                    userID=get_user_id(request),
                    parent=ModelChoices.DEVICES,
                    key='DeviceType',
                    value=value
                )
                obj.status = True
                obj.save()
        
        if from_date or to_date:
            DateFilter.objects.update_or_create(
                userID=get_user_id(request),
                parent=ModelChoices.DEVICES,
                defaults={
                    'from_date':from_date,
                    'to_date':to_date
                }
            )

    return redirect(reverse('charts'))

def index(request):
    # Pre filter
    # pre_from_date_str = "Feb 27 2020 7:36AM"
    # pre_from_date = datetime.strptime(pre_from_date_str, "%b %d %Y %I:%M%p").timestamp()
    # pre_to_date = timezone.now().timestamp()
    # pre_filtered_devices = Devices.objects.filter(DeviceLastConnUtc__range=[pre_from_date, pre_to_date])


    # User filter
    device_type_list = UserFilter.objects.filter(parent=ModelChoices.DEVICES, userID=get_user_id(request), status=True).values_list('value', flat=True)
    device_type = [dt for dt in device_type_list if dt != 'All']
    filter_string = {}
    if device_type:
        filter_string['DeviceType__in'] = device_type
    

    # User Date filter
    date_filter_qs = DateFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.DEVICES)
    if date_filter_qs.exists():
        date_filter = date_filter_qs.first()
        from_date_str = date_filter.from_date.strftime('%Y-%m-%d')
        to_date_str = (date_filter.to_date + timezone.timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        from_date_str = timezone.datetime(2022, 2, 27).strftime('%Y-%m-%d')
        to_date_str = (timezone.now() + timezone.timedelta(days=1)).strftime("%Y-%m-%d")

    from_date = datetime.strptime(from_date_str, "%Y-%m-%d").timestamp()
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d").timestamp()

    if from_date and to_date:
        filter_string['DeviceLastConnUtc__range'] = [from_date, to_date]

    queryset = Devices.objects.filter(**filter_string)
    devices = serializers.serialize('json', queryset)

    COMBOS = {}
    COMBOS['DeviceType'] = ['All', 'Virtual Machine', 'PC', 'Server']



    date_range = {
        'from_date': from_date_str,
        'to_date': (datetime.strptime(to_date_str, '%Y-%m-%d') - timezone.timedelta(days=1)).strftime('%Y-%m-%d')
    }

    context = {
        'segment': 'charts',
        'parent': 'user_compliance',
        'sub_segment': 'Logins/day',
        'devices': devices,
        'COMBOS': COMBOS,
        'date_range': date_range,
        'device_type': device_type_list
    }
    return render(request, 'apps/charts/logins_per_day.html', context)




from django.http import JsonResponse
from loader.models import InstantUpload
from django.contrib.contenttypes.models import ContentType

def get_device_data(request):
    snapshot_filter = {}
    content_type = ContentType.objects.get(model='controladuser')
    snapshots = InstantUpload.objects.filter(content_type=content_type).order_by('-created_at')
    latest_snapshot = snapshots.latest('created_at')
    snapshot_filter['loader_instance'] = latest_snapshot.pk
    devices = ControlADUser.objects.filter(**snapshot_filter).filter(
        Q(AD_Enabled_Status='TRUE') | Q(AD_Enabled_Status='True')
    )
    chart_data = {}
    consolidated_chart_data = []
    for device in devices:
        timestamp = device.AD_Account_Created
        dt_object = datetime.utcfromtimestamp(timestamp)
        month = f"{dt_object.month}-{dt_object.year}"
        if month not in chart_data:
            chart_data[month] = {}

        if 'count' not in chart_data[month]:
            chart_data[month]['count'] = 1
            chart_data[month]['date'] = device.AD_Account_Created
        else:
            chart_data[month]['count'] += 1


    for month, data in chart_data.items():
        consolidated_chart_data.append({
            'x': month,
            'y': data['count'],
            'date': data['date'],
            'deviceType': 'All',
        })

    return JsonResponse({'consolidatedChartData': consolidated_chart_data}, safe=False)

from collections import Counter

def get_operating_data(request):
    snapshot_filter = {}
    content_type = ContentType.objects.get(model='controladdevicesunsupos')
    snapshots = InstantUpload.objects.filter(content_type=content_type).order_by('-created_at')
    latest_snapshot = snapshots.latest('created_at')
    snapshot_filter['loader_instance'] = latest_snapshot.pk
    devices = ControlADDevicesUnsupOS.objects.filter(**snapshot_filter).filter(
        Q(AD_Status='TRUE') | Q(AD_Status='True')
    )
    
    devices = devices.exclude(OperatingSystem__isnull=True)
    os_counts = Counter(device.OperatingSystem for device in devices)
    consolidated_chart_data = [{'x': os, 'y': count} for os, count in os_counts.items() if os]
    consolidated_chart_data = sorted(consolidated_chart_data, key=lambda x: x['y'], reverse=True)

    return JsonResponse({'consolidatedChartData': consolidated_chart_data}, safe=False)


def get_operating_supported_data(request):
    snapshot_filter = {}
    devices = ControlADDevices.objects.filter(**snapshot_filter).filter(
        Q(AD_Status='TRUE') | Q(AD_Status='True')
    )
    true_devices = devices.filter(OperatingSystem_Supported='True')
    false_devices = devices.filter(OperatingSystem_Supported='False')
    true_count = true_devices.count()
    false_count = false_devices.count()

    consolidated_chart_data = [
        {'x': 'True', 'y': true_count},
        {'x': 'False', 'y': false_count}
    ]
    return JsonResponse({'consolidatedChartData': consolidated_chart_data}, safe=False)


def get_ad_device_data(request):
    snapshot_filter = {}
    content_type = ContentType.objects.get(model='controladdevices')
    snapshots = InstantUpload.objects.filter(content_type=content_type).order_by('-created_at')
    latest_snapshot = snapshots.latest('created_at')
    snapshot_filter['loader_instance'] = latest_snapshot.pk
    devices = ControlADDevices.objects.filter(**snapshot_filter).filter(
        Q(AD_Status='TRUE') | Q(AD_Status='True')
    )
    chart_data = {}
    consolidated_chart_data = []
    for device in devices:
        timestamp = device.Created_in_AD
        dt_object = datetime.utcfromtimestamp(timestamp)
        month = dt_object.month
        if month not in chart_data:
            chart_data[month] = {}

        if 'count' not in chart_data[month]:
            chart_data[month]['count'] = 1
            chart_data[month]['date'] = device.Created_in_AD
        else:
            chart_data[month]['count'] += 1


    for month, data in chart_data.items():
        consolidated_chart_data.append({
            'x': month,
            'y': data['count'],
            'date': data['date'],
            'deviceType': 'All',
        })

    return JsonResponse({'consolidatedChartData': consolidated_chart_data}, safe=False)