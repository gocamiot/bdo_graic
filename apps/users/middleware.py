from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from apps.common.models import Sidebar
import threading

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and not request.path_info.startswith('/users/') and request.path_info != '/':
            original_url = request.get_full_path()
            redirect_url = reverse('signin') + f'?next={original_url}'
            return redirect(redirect_url)
        response = self.get_response(request)
        return response



_request_local = threading.local()

class CurrentRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request_local.request = request
        response = self.get_response(request)
        return response

def get_current_request():
    return getattr(_request_local, 'request', None)

def get_current_user():
    request = get_current_request()
    if request:
        return request.user
    return None


class SidebarPermissionMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            url_name = request.resolver_match.url_name
            user_groups = request.user.groups.all()

            if request.path.startswith(reverse('admin:index')):
                return None
            
            sidebar_entry = None
            try:
                if url_name:
                    sidebar_entry = Sidebar.objects.filter(url_name=url_name, is_active=True).first()
            except Sidebar.DoesNotExist:
                sidebar_entry = None
            
            if sidebar_entry:
                if sidebar_entry.group not in user_groups:
                    return redirect(reverse('403'))
                
        return None


_user = threading.local()
class AuditUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _user.value = request.user

        response = self.get_response(request)
        _user.value = None
        return response

    @staticmethod
    def get_current_user():
        return getattr(_user, 'value', None)