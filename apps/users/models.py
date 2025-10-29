import random
import datetime
import requests
from django.db import models
# from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError

TOKEN = getattr(settings, 'WHAPI_TOKEN')

# Create your models here.

def generate_otp():
    return random.randint(100000, 999999)


class OTPMethodChoices(models.TextChoices):
    EMAIL = 'EMAIL', _('Email')
    WHATSAPP = 'WHATSAPP', _('WhatsApp')
    PHONE = 'PHONE', _('Phone')

class User(AbstractUser):
    is_audituser = models.BooleanField(
        default=False, 
        help_text="Designates that this user has all permissions with tampered reports.",
        verbose_name="Audit user status"
    )
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    otp = models.IntegerField(null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_method = models.CharField(max_length=100, choices=OTPMethodChoices.choices, default=OTPMethodChoices.EMAIL)
    required_password = models.BooleanField(
        default=True, 
        verbose_name="Reset password", 
        help_text="To reset or unblock a user, check reset password"
    )
    blocked = models.BooleanField(default=False)
    last_password_change = models.DateTimeField(null=True, blank=True)


    def is_otp_valid(self):
        if self.otp_created_at:
            now = timezone.now()
            if now < self.otp_created_at + datetime.timedelta(minutes=30):
                return True
            return False
        return True


    def clean(self):
        super().clean()

        if self.phone_number:
            url = "https://gate.whapi.cloud/contacts"
            data = {
                'contacts': [self.phone_number]
            }
            headers = {
                "accept": "application/json",
                "authorization": f"Bearer {TOKEN}"
            }

            try:
                response = requests.post(url, json=data, headers=headers)
                if response.status_code != 200:
                    raise ValidationError({'phone_number': _('Invalid phone number.')})
            except requests.RequestException:
                raise ValidationError({'phone_number': _('There was an error connecting to the WHAPI service. Please try again later.')})
            except Exception as e:
                raise ValidationError({'phone_number': _('There was an error connecting to the WHAPI service. Please try again later.')})


    def save(self, *args, **kwargs):
        if self._state.adding and not self.otp:
            self.otp = generate_otp()
            self.otp_created_at = timezone.now()
        super().save(*args, **kwargs)


ROLE_CHOICES = (
    ('admin'  , 'Admin'),
    ('user'  , 'User'),
)

class Profile(models.Model):
    user      = models.OneToOneField(User, on_delete=models.CASCADE)
    role      = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    full_name = models.CharField(max_length=255, null=True, blank=True)
    country   = models.CharField(max_length=255, null=True, blank=True)
    city      = models.CharField(max_length=255, null=True, blank=True)
    zip_code  = models.CharField(max_length=255, null=True, blank=True)
    address   = models.CharField(max_length=255, null=True, blank=True)
    phone     = models.CharField(max_length=255, null=True, blank=True)
    avatar    = models.ImageField(upload_to='avatar', null=True, blank=True)
    timezone  = models.CharField(max_length=255, default='UTC')

    def __str__(self):
        return self.user.username


class ExpiredChoices(models.TextChoices):
    YES = 'YES', 'Yes'
    NO = 'NO', 'No'

class LoginLogs(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_expired = models.CharField(max_length=20, choices=ExpiredChoices.choices, default=ExpiredChoices.NO)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Login log for {self.user.username}"
    
    class Meta:
        verbose_name = 'Login Log'
        verbose_name_plural = 'Login Logs'



class Security(models.Model):
    EVERY_MINUTE = 60
    HOURLY = EVERY_MINUTE * 60
    DAILY = 24 * HOURLY
    WEEKLY = 7 * DAILY
    EVERY_2_WEEKS = 2 * WEEKLY
    MONTHLY = 30 * DAILY
    EVERY_3_MONTHS = 3 * MONTHLY
    EVERY_6_MONTHS = 6 * MONTHLY
    YEARLY = 365 * DAILY

    REPEAT_CHOICES = (
        (EVERY_MINUTE, 'every minute'),
        (HOURLY, 'hourly'),
        (DAILY, 'daily'),
        (WEEKLY, 'weekly'),
        (EVERY_2_WEEKS, 'every 2 weeks'),
        (MONTHLY, 'every month'),
        (EVERY_3_MONTHS, 'every 3 months'),
        (EVERY_6_MONTHS, 'every 6 months'),
        (YEARLY, 'every year')
    )

    change_password = models.BigIntegerField(choices=REPEAT_CHOICES, default=WEEKLY)


class UserPasswordHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"



class ChangeLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    model_name = models.CharField(max_length=255)
    field_name = models.CharField(max_length=255)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    change_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user} changed {self.field_name} in {self.model_name} from {self.old_value} to {self.new_value}"