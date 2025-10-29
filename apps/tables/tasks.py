from background_task import background
from apps.tables.models import DynamicQuery, TaskStatus, ActionStatus, EmailActionStatus
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from apps.tables.utils import query_shoot_func
from django.apps import apps
from django.conf import settings
from loader.models import encrypt_value, ENCRYPTION_PREFIX

@background(schedule=1)
def async_fetch_data(model_name, view_name, task_id):
    model = apps.get_model('tables', model_name)
    model.objects.filter(snapshot=None).delete()
    dynamic_query = get_object_or_404(DynamicQuery, view_name=view_name, is_correct=True)


    if dynamic_query.temporary_tables.all():
        for table in dynamic_query.temporary_tables.all():
            content_type = ContentType.objects.get(app_label=table.content_type.app_label, model=table.content_type.model)
            temporary_model = content_type.model_class()
            temporary_model.objects.all().delete()

            instances_to_temp_create = query_shoot_func(temporary_model, table)
            temporary_model.objects.bulk_create(instances_to_temp_create)

    instances_to_create = query_shoot_func(model, dynamic_query)
    model.objects.bulk_create(instances_to_create)

    TaskStatus.objects.filter(task_id=task_id).update(is_completed=True)

    print(f'Data has been uploaded successfully for {model_name}')



@background(schedule=1)
def encrypt_existing_fields():
    encryption_models = settings.ENCRYPTION_MODELS

    for model_path in encryption_models:
        model_class = apps.get_model(model_path)
        instances = model_class.objects.all()
        encrypted_fields = getattr(model_class, 'encrypted_fields', [])

        for instance in instances:
            needs_save = False
            for field in encrypted_fields:
                value = getattr(instance, field)
                if value and not value.startswith(ENCRYPTION_PREFIX):
                    encrypted_value = encrypt_value(value)
                    setattr(instance, field, encrypted_value)
                    needs_save = True

            if needs_save:
                instance.save()




from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import localtime
from apps.tables.models import Finding


@shared_task
def send_open_status_emails():
    findings = Finding.objects.filter(email_action_status=EmailActionStatus.OPEN, action_status=ActionStatus.IS_ACTIVE)
    for software in findings:
        if software.action_to:
            subject = "Action Subject"
            message = software.description.html

            if software.action_note:
                message += f"<br><strong>Note:</strong> {software.action_note}"
            if software.action_deadline:
                message += f"<br><strong>Deadline:</strong> {localtime(software.action_deadline).strftime('%Y-%m-%d %H:%M')}"

            current_page_link = f"{settings.SITE_URL}/tables/my-actions/"
            message += f"<br><a href='{current_page_link}'>View More Details</a>"

            send_mail(
                subject=subject,
                message="",
                html_message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[software.action_to],
            )