# from django.contrib.auth.models import User
from apps.users.models import Profile, ChangeLog
from django.db.models.signals import post_save, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from apps.users.models import LoginLogs, ExpiredChoices
from django.utils import timezone
from apps.users.middleware import get_current_request, get_current_user
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)
        if instance.is_superuser:
            profile.role = "admin"
            profile.save()


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    LoginLogs.objects.create(user=user, )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    last_login_log = LoginLogs.objects.filter(user=user).order_by('-login_time').first()
    if last_login_log:
        last_login_log.logout_time = timezone.now()
        last_login_log.session_expired = ExpiredChoices.YES
        last_login_log.save()



@receiver(pre_save, sender=User)
@receiver(pre_save, sender=Profile)
def log_changes(sender, instance, **kwargs):
    request = get_current_request()
    if request and request.path.startswith('/admin'):
        if instance.pk:
            previous_instance = sender.objects.get(pk=instance.pk)
            current_user = get_current_user()
            for field in instance._meta.fields:
                field_name = field.name
                old_value = getattr(previous_instance, field_name)
                new_value = getattr(instance, field_name)
                if old_value != new_value:
                    ChangeLog.objects.create(
                        user=current_user,
                        model_name=sender.__name__,
                        field_name=field_name,
                        old_value=old_value,
                        new_value=new_value,
                        change_date=timezone.now()
                    )
