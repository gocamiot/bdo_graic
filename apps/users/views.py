from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView, PasswordResetConfirmView
from django.views.generic import CreateView
from apps.users.models import Profile
from apps.users.forms import SigninForm, SignupForm, UserPasswordChangeForm, UserSetPasswordForm, UserPasswordResetForm, ProfileForm, OTPForm
from django.contrib.auth import logout
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib import messages
# from django.contrib.auth.models import User
from django.core.paginator import Paginator
from apps.users.utils import user_filter, username_in_admin_username, is_password_reset, send_otp
from django.contrib.auth import login, authenticate
from django.views import View
from apps.users.models import generate_otp
from django.contrib.auth import get_user_model, update_session_auth_hash
from apps.users.models import Security, UserPasswordHistory
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required

import time
import pytz

User = get_user_model()

# Create your views here.

def index(request):

    prodName = ''
        
    return HttpResponse("INDEX Users" + ' ' + prodName)


def username_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        user = User.objects.filter(username=username)
        if user.exists():
            request.session['username'] = username
            original_url = request.GET.get('next', None)

            if user.first().required_password:
                # redirect to password change form
                password_url = reverse('change_password_view')
            else:
                # redirect to password form
                if not username_in_admin_username(username):
                    delta = timezone.now() - user.first().last_password_change
                    change_password = Security.objects.last().change_password if Security.objects.last() else 86400
                    if delta.total_seconds() > change_password:
                        messages.error(request, 'Your password has expired. Please change your password.')
                        password_url = reverse('change_password_view')
                    else:
                        password_url = reverse('password_view')
                else:
                    password_url = reverse('password_view')

            if original_url:
                password_url += f'?next={original_url}'

            return redirect(password_url)
        
        else:
            messages.error(request, "User with this username doesn't exists")
            return redirect(request.META.get('HTTP_REFERER'))
        
    return render(request, 'authentication/username-form.html')


@is_password_reset
def password_view(request):
    if request.method == 'POST':
        username = request.session.get('username')
        password = request.POST.get('password')

        temp_user = get_object_or_404(User, username=username)

        if 'failed_attempts' not in request.session:
            request.session['failed_attempts'] = 0

        if temp_user.blocked:
            messages.error(request, "Your account is blocked. Please contact to the admin.")
            return redirect(request.META.get('HTTP_REFERER'))
            
        user = authenticate(request, username=username, password=password)
        if user is not None:
            request.session['failed_attempts'] = 0
            request.session['user_id'] = user.id
            original_url = request.GET.get('next', None)

            if not user.required_password:
                if not username_in_admin_username(user.username):
                    if not user.is_otp_valid():
                        user.otp = generate_otp()
                        user.otp_created_at = timezone.now()
                        user.save()
                        send_otp(user, request)
                    else:
                        send_otp(user, request)
                        
                otp_url = reverse('otp_view')
                
            else:
                otp_url = reverse('change_password_view')
            
            if original_url:
                otp_url += f'?next={original_url}'
                
            return redirect(otp_url)
        
        else:
            request.session['failed_attempts'] += 1
            if request.session['failed_attempts'] >= 3:
                temp_user.blocked = True
                temp_user.save()
                messages.error(request, "Your account is blocked due to too many failed login attempts.")
            else:
                messages.error(request, "Incorrect password!")

            return redirect(request.META.get('HTTP_REFERER'))
        
    return render(request, 'authentication/password-form.html')


def change_password_view(request):
    username = request.session.get('username')
    user = get_object_or_404(User, username=username)

    if request.method == 'POST':
        form = UserSetPasswordForm(user=user, data=request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            request.session['new_password'] = new_password

            previous_passwords = UserPasswordHistory.objects.filter(user=user)
            for previous_password in previous_passwords:
                if check_password(new_password, previous_password.password):
                    messages.error(request, "You cannot reuse a previous password. Please choose a different password.")
                    return redirect(request.META.get('HTTP_REFERER'))

            request.session['user_id'] = user.id
            if not username_in_admin_username(user.username):
                send_otp(user, request)
            original_url = request.GET.get('next', None)
            otp_url = reverse('otp_view')
            if original_url:
                otp_url += f'?next={original_url}'

            return redirect(otp_url)

    else:
        form = UserSetPasswordForm(user=user)

    context = {
        'form': form
    }
    return render(request, 'authentication/password-change-form.html', context)

class OTPVerificationView(View):
    form_class = OTPForm
    template_name = 'authentication/otp-verification.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            user_id = request.session.get('user_id')
            new_password = request.session.get('new_password')

            if user_id:
                user = User.objects.get(id=user_id)
                if not username_in_admin_username(user.username):
                    if user.otp == int(otp) and user.is_otp_valid():
                        if new_password:
                            update_session_auth_hash(request, user)
                            user.set_password(new_password)
                            user.last_password_change = timezone.now()
                            user.required_password = False
                            user.save()

                            UserPasswordHistory.objects.create(user=user, password=user.password)

                        return self._login_and_redirect(request, user)
                    else:
                        form.add_error('otp', 'OTP is invalid or expired')
                else:
                    if new_password:
                        update_session_auth_hash(request, user)
                        user.set_password(new_password)
                        user.last_password_change = timezone.now()
                        user.required_password = False
                        user.save()

                        UserPasswordHistory.objects.create(user=user, password=user.password)
                        
                    return self._login_and_redirect(request, user)
                
        return render(request, self.template_name, {'form': form})
    
    def _login_and_redirect(self, request, user):
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        if request.session.get('user_id'):
            del request.session['user_id']
        if request.session.get('username'):
            del request.session['username']
        if request.session.get('new_password'):
            del request.session['new_password']
            
        user.otp = generate_otp()
        user.otp_created_at = timezone.now()
        user.save()
        original_url = request.GET.get('next', '/index/')
        return redirect(original_url)


def resend_otp(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        user.otp = generate_otp()
        user.otp_created_at = timezone.now()
        user.save()

        last_otp_sent = request.session.get('last_otp_sent', 0)
        current_time = time.time()
        if current_time - last_otp_sent >= 60:
            send_otp(user, request)
            messages.success(request, "OTP has been resent.")

    return redirect(request.META.get('HTTP_REFERER'))

class UserPasswordChangeView(PasswordChangeView):
    template_name = 'authentication/password-change.html'
    form_class = UserPasswordChangeForm

class UserPasswordResetView(PasswordResetView):
    template_name = 'authentication/forgot-password.html'
    form_class = UserPasswordResetForm

class UserPasswrodResetConfirmView(PasswordResetConfirmView):
    template_name = 'authentication/reset-password.html'
    form_class = UserSetPasswordForm


def signout_view(request):
    logout(request)
    return redirect(reverse('signin'))


@login_required(login_url='/users/signin/')
def profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    user = User.objects.get(pk=request.user.pk)
    p_change_form = UserSetPasswordForm(user=user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)

        if form.is_valid():
            email = request.POST.get('email', '')
            user.email = email
            user.save()
            form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect(request.META.get('HTTP_REFERER'))
    else:
        form = ProfileForm(instance=profile)
    
    context = {
        'form': form,
        'p_change_form': p_change_form,
        'parent': 'admin',
        'segment': 'profile',
        'timezones': pytz.all_timezones
    }
    return render(request, 'dashboard/profile.html', context)


@login_required(login_url='/users/signin/')
def upload_avatar(request):
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        profile.avatar = request.FILES.get('avatar')
        profile.save()
        messages.success(request, 'Avatar uploaded successfully')
    return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='/users/signin/')
def update_user_timezone(request):
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        profile.timezone = request.POST.get('timezone')
        profile.save()
        messages.success(request, 'Timezone updated')
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='/users/signin/')
def change_password(request):
    user = request.user
    if request.method == 'POST':
        form = UserSetPasswordForm(user=user, data=request.POST)

        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            previous_passwords = UserPasswordHistory.objects.filter(user=user)
            for previous_password in previous_passwords:
                if check_password(new_password, previous_password.password):
                    messages.error(request, "You cannot reuse a previous password. Please choose a different password.")
                    return redirect(request.META.get('HTTP_REFERER'))
                
            form.save()
            UserPasswordHistory.objects.create(user=user, password=user.password)
            return redirect(request.META.get('HTTP_REFERER'))
        else:
            for field in form:
                for error in field.errors:
                    messages.error(request, error)
        
    return redirect(request.META.get('HTTP_REFERER'))


@staff_member_required(login_url='/users/signin/')
def user_list(request):
    filters = user_filter(request)
    user_list = User.objects.filter(**filters)
    form = SignupForm()

    page = request.GET.get('page', 1)
    paginator = Paginator(user_list, 5)
    users = paginator.page(page)

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            return post_request_handling(request, form)

    context = {
        'users': users,
        'form': form,
        'parent': 'admin',
        'segment': 'users'
    }
    return render(request, 'apps/users.html', context)


@staff_member_required(login_url='/users/signin/')
def post_request_handling(request, form):
    form.save()
    return redirect(request.META.get('HTTP_REFERER'))

@staff_member_required(login_url='/users/signin/')
def delete_user(request, id):
    user = User.objects.get(id=id)
    user.delete()
    return redirect(request.META.get('HTTP_REFERER'))


@staff_member_required(login_url='/users/signin/')
def update_user(request, id):
    user = User.objects.get(id=id)
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
    return redirect(request.META.get('HTTP_REFERER'))


@staff_member_required(login_url='/users/signin/')
def user_change_password(request, id):
    user = User.objects.get(id=id)
    form = UserSetPasswordForm(user=user)
    if request.method == 'POST':
        form = UserSetPasswordForm(user=user, data=request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            previous_passwords = UserPasswordHistory.objects.filter(user=user)
            for previous_password in previous_passwords:
                if check_password(new_password, previous_password.password):
                    messages.error(request, "You cannot reuse a previous password. Please choose a different password.")
                    return redirect(request.META.get('HTTP_REFERER'))
                
            form.save()
            UserPasswordHistory.objects.create(user=user, password=user.password)
            return redirect(reverse('user_list'))

    context = {
        'form': form
    }
    return render(request, 'authentication/password-change-form.html', context)


@staff_member_required
def custom_password_change(request):
    messages.error(request, "Password change functionality is disabled. Please contact the administrator if you need to change your password.")
    return redirect('admin:index')

@staff_member_required
def custom_password_change_done(request):
    messages.error(request, "Password change functionality is disabled. Please contact the administrator if you need to change your password.")
    return redirect('admin:index')


def noperms_view(request):     
    return render(request, 'authentication/403.html')