import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from apps.tables.utils import software_filter
from apps.tables.models import UserFilter, PageItems, HideShowFilter, ModelChoices, FindingAttachment, Finding, ActionStatus, AttachmentType, DocumentStatus
from django.http import HttpResponse
from django.views import View
import json
from django.http import JsonResponse, FileResponse, Http404
from django.utils import timezone


# Create your views here.

def get_user_id(request):
    if request.user.is_authenticated:
        return request.user.pk
    else:
        return -1

def create_finding_attachment_filter(request):
    if request.method == "POST":
        keys = request.POST.getlist('key')
        values = request.POST.getlist('value')
        for i in range(len(keys)):
            key = keys[i]
            value = values[i]

            UserFilter.objects.update_or_create(
                userID=get_user_id(request),
                parent=ModelChoices.FINDING_ATTACHMENT,
                key=key,
                defaults={'value': value}
            )

        return redirect(request.META.get('HTTP_REFERER'))

def create_finding_attachment_page_items(request):
    if request.method == 'POST':
        items = request.POST.get('items')
        page_items, created = PageItems.objects.update_or_create(
            userID=get_user_id(request),
            parent=ModelChoices.FINDING_ATTACHMENT,
            defaults={'items_per_page':items}
        )
        return redirect(request.META.get('HTTP_REFERER'))

def create_finding_attachment_hide_show_filter(request):
    if request.method == "POST":
        data_str = list(request.POST.keys())[0]
        data = json.loads(data_str)


        HideShowFilter.objects.update_or_create(
            userID=get_user_id(request),
            parent=ModelChoices.FINDING_ATTACHMENT,
            key=data.get('key'),
            defaults={'value': data.get('value')}
        )

        response_data = {'message': 'Model updated successfully'}
        return JsonResponse(response_data)

    return JsonResponse({'error': 'Invalid request'}, status=400)
    

def delete_finding_attachment_filter(request, id):
    filter_instance = UserFilter.objects.get(id=id, userID=get_user_id(request), parent=ModelChoices.FINDING_ATTACHMENT)
    filter_instance.delete()
    return redirect(request.META.get('HTTP_REFERER'))


def finding_attachment(request, id):
    finding = get_object_or_404(Finding, id=id)
    db_field_names = [field.name for field in FindingAttachment._meta.get_fields() if not field.is_relation]

    field_names = []

    for field_name in db_field_names:
        fields, created = HideShowFilter.objects.get_or_create(key=field_name, userID=get_user_id(request), parent=ModelChoices.FINDING_ATTACHMENT)
        field_names.append(fields)

    page_items = PageItems.objects.filter(userID=get_user_id(request), parent=ModelChoices.FINDING_ATTACHMENT).last()
    items = 25
    if page_items:
        items = page_items.items_per_page

    filter_string = {}
    filter_string['finding'] = finding

    filter_instance = UserFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.FINDING_ATTACHMENT)
    for filter_data in filter_instance:
        filter_string[f'{filter_data.key}__icontains'] = filter_data.value

    order_by = request.GET.get('order_by', 'id')
    queryset = FindingAttachment.objects.filter(action_status=ActionStatus.IS_ACTIVE).filter(**filter_string).filter(parent=None).order_by(order_by)

    software_list = software_filter(request, queryset, db_field_names)

    page = request.GET.get('page', 1)
    paginator = Paginator(software_list, items)
    
    try:
        softwares = paginator.page(page)
    except PageNotAnInteger:
        return redirect('finding_attachment')
    except EmptyPage:
        return redirect('finding_attachment') 

    read_only_fields = ()
    pre_column = ('id', 'created_at', 'updated_at', 'action_status', 'deleted_at', 'deleted_by', )
    compulsory_fields=('attachment_type','attachment_status', 'version', 'description', 'attachment', )
    date_picker_fields = ()

    COMBOS = {}

    context = {
        'segment'  : 'finding_attachment',
        'parent'   : 'finding',
        'softwares' : softwares,
        'field_names': field_names,
        'db_field_names': db_field_names,
        'filter_instance': filter_instance,
        'items': items,
        'read_only_fields': read_only_fields,
        'total_items': FindingAttachment.objects.filter(action_status=ActionStatus.IS_ACTIVE, finding=finding).filter(parent=None).count(),
        'pre_column': pre_column,
        'COMBOS': COMBOS,
        'date_picker_fields': date_picker_fields,
        'compulsory_fields': compulsory_fields,
        'fav_name': 'Actions Attachment',
        'attachment_type': AttachmentType.choices,
        'attachment_status': DocumentStatus.choices,
        'finding': finding
    }
    
    return render(request, 'apps/finding_attachment.html', context)



@login_required(login_url='/users/signin/')
def create_finding_attachment(request, id):
    finding = get_object_or_404(Finding, id=id)

    finding_attachment = FindingAttachment.objects.create(
        finding=finding,
        attachment_type=request.POST.get('attachment_type'),
        attachment_status=request.POST.get('attachment_status'),
        attachment=request.FILES.get('attachment'),
        version=request.POST.get('version'),
        description=request.POST.get('description'),
        created_by=request.user.email if request.user.email else request.user.username,
        created_at=timezone.now(),
        updated_at=timezone.now()
    )

    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='/users/signin/')
def delete_finding_attachment(request, id):
    software = FindingAttachment.objects.get(id=id)
    software.action_status = ActionStatus.DELETED
    software.deleted_at = timezone.now()
    software.deleted_by = request.user.email if request.user.email else request.user.username
    software.save()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='/users/signin/')
def update_finding_attachment(request, id):
    software = FindingAttachment.objects.get(id=id)
    existing_attachment = software.attachment
    finding = software.finding

    if request.method == 'POST':
        updated_attributes = {}
        for attribute, value in request.POST.items():
            if attribute == 'csrfmiddlewaretoken':
                continue

            updated_attributes[attribute] = getattr(software, attribute)
            setattr(software, attribute, value)
            
        attachment = request.FILES.get('attachment')
        if attachment is not None:
            setattr(software, 'attachment', attachment)
        else:
            software.attachment = existing_attachment
        
        software.updated_by = request.user.email if request.user.email else request.user.username

        software.version_control += 1
        software.updated_at = timezone.now()
        software.save()

        # Create a new instance with the previous attributes
        if 'attachment' in updated_attributes:
            updated_attributes.pop('attachment')

        prev_software = FindingAttachment.objects.create(
            **updated_attributes,
            finding=finding,
            attachment=existing_attachment,
            version_control=software.version_control - 1
        )
        prev_software.parent = software
        prev_software.created_by = software.created_by
        prev_software.updated_by = software.updated_by
        prev_software.created_at = software.created_at
        prev_software.updated_at = timezone.now()
        prev_software.save()
    
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='/users/signin/')
def finding_attachment_duplicate_row(request, id):
    software = FindingAttachment.objects.get(id=id)
    software.pk = None
    software.save()
    return redirect(request.META.get('HTTP_REFERER'))

# Export as CSV
class ExportCSVView(View):
    def get(self, request):
        db_field_names = [field.name for field in FindingAttachment._meta.get_fields() if not field.is_relation]


        fields = []
        pre_column = ('id', 'created_at', 'updated_at', 'document', )

        show_fields = HideShowFilter.objects.filter(value=False, userID=get_user_id(request), parent=ModelChoices.FINDING_ATTACHMENT)
        for field in show_fields:
            if field.key not in pre_column:
                fields.append(field.key)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="finding_attachment.csv"'

        writer = csv.writer(response)
        writer.writerow(fields) 


        filter_string = {}
        filter_instance = UserFilter.objects.filter(userID=get_user_id(request), parent=ModelChoices.FINDING_ATTACHMENT)
        for filter_data in filter_instance:
            filter_string[f'{filter_data.key}__icontains'] = filter_data.value

        order_by = request.GET.get('order_by', 'id')
        queryset = FindingAttachment.objects.filter(**filter_string).order_by(order_by)

        softwares = software_filter(request, queryset, db_field_names)

        for software in softwares:
            row_data = [getattr(software, field) for field in fields]
            writer.writerow(row_data)

        return response


def finding_attachments_version_control_dt(request, id):
    parent = FindingAttachment.objects.get(id=id)
    db_field_names = [field.name for field in FindingAttachment._meta.get_fields() if not field.is_relation]

    child_qs = FindingAttachment.objects.filter(parent=parent)

    context = {
        'segment'  : 'finding_attachments',
        'parent'   : 'vendors',
        # 'form'     : form,
        'softwares' : child_qs,
        'db_field_names': db_field_names,
        'parent': parent
    }

    return render(request, 'apps/version_control/finding_attachment.html', context)


def download_attachment(request, id):
    finding_attachment = get_object_or_404(FindingAttachment, id=id)
    file_path = finding_attachment.attachment.path

    try:
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=finding_attachment.attachment.name)
    except FileNotFoundError:
        raise Http404("File not found.")