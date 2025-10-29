import time

from functools import wraps
from whap.models import Recipient
from whap.views import send_message
from django.conf import settings
from apps.users.models import OTPMethodChoices
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage
from django.contrib.staticfiles import finders
from functools import lru_cache

User = get_user_model()

def user_filter(request):
    filter_string = {}
    filter_mappings = {
        'search': 'username__icontains'
    }
    for key in request.GET:
        if request.GET.get(key) and key != 'page':
            filter_string[filter_mappings[key]] = request.GET.get(key)

    return filter_string


def is_audit_user(user):
    return user.is_authenticated and user.is_active and user.is_audituser


def is_password_reset(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if user_id:
            user = User.objects.get(id=user_id)
            if user.required_password:
                return redirect(reverse('change_password_view'))
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def send_otp_email(user, request):

    msg_html = render_to_string('email_otp/email_otp.html', {'user_otp': user.otp})

    message = EmailMultiAlternatives(
    subject="Your OTP Code",
    body=msg_html,
    from_email=settings.DEFAULT_FROM_EMAIL,
    to=[user.email],
    )
    message.mixed_subtype = 'related'
    message.attach_alternative(msg_html, "text/html")
    message.attach(logo_data())
    message.send(fail_silently=False)

    request.session['last_otp_sent'] = time.time()

#@lru_cache()
def logo_data():
    with open(finders.find('dist/images/bdo_logo.png'), 'rb') as f:
        logo_data = f.read()
    logo = MIMEImage(logo_data)
    logo.add_header('Content-ID', '<logo>')
    return logo


def send_otp_whatsapp(user, request):
    if user.phone_number:
        msg = f"Your OTP code is: {user.otp}"
        status_code = send_message(msg, user.phone_number)
        if status_code == 200:
            request.session['last_otp_sent'] = time.time()
    else:
        print("Invalid recipient")
        pass


def send_otp_phone(user, request):
    pass


def send_otp(user, request):
    if user.otp_method == OTPMethodChoices.EMAIL:
        send_otp_email(user, request)
    elif user.otp_method == OTPMethodChoices.WHATSAPP:
        send_otp_whatsapp(user, request)
    elif user.otp_method == OTPMethodChoices.PHONE:
        send_otp_phone(user, request)
    else:
        pass


def username_in_admin_username(username):
    return username in getattr(settings, 'ADMIN_USERNAMES')