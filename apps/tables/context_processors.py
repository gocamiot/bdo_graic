from datetime import datetime
from apps.tables.models import DocumentStatus, DocumentType, DocumentType_GR
from apps.common.models import Sidebar
from loader.models import DynamicQuery, SAPApi
from django.contrib.auth.models import Group
from home.models import PyFunctionPrompt, PyFunction
from apps.file_manager.models import DefaultValues
from apps.graic.models import Chat
from django.utils.timezone import now

def get_greeting():
    current_hour = datetime.now().hour
    
    if 5 <= current_hour < 12:
        return "Good Morning"
    elif 12 <= current_hour < 17:
        return "Good Afternoon"
    elif 17 <= current_hour < 21:
        return "Good Evening"
    else:
        return "Hello"

def humanize_date(dt):
    today = now().date()
    diff = (today - dt.date()).days

    if diff == 0:
        return "Today"
    elif diff == 1:
        return "Yesterday"
    elif diff < 7:
        return f"{diff} days ago"
    elif diff < 30:
        return "1 week ago"
    else:
        return "Last month"

def dt_context(request):
    sidebar_dict = {}
    greeting = get_greeting()
    last_prompt = PyFunctionPrompt.objects.last()
    chats = []
    
    if request.user.is_authenticated:
        user_groups = request.user.groups.all()
        sidebar_items = Sidebar.objects.filter(is_active=True, group__in=user_groups)
        parents = sidebar_items.filter(parent__isnull=True)
        children = sidebar_items.filter(parent__isnull=False)
        greeting = f"{greeting}, {request.user.username}!"
        chats = Chat.objects.filter(user=request.user).order_by('-created_at')

        for chat in chats:
            chat.humanized_date = humanize_date(chat.created_at)
        
        for parent in parents:
            sidebar_dict[parent] = children.filter(parent=parent)

    return {
        'device_context': 'All Devices',
        'software_context': 'All Software',
        'document_types': DocumentType,
        'Document_Types': DocumentType_GR,
        'document_status': DocumentStatus,
        'sidebar_dict': sidebar_dict,
        'queries': DynamicQuery.objects.all(),
        'sap_apis': SAPApi.objects.all(),
        'sidebars': Sidebar.objects.filter(is_active=True, parent__isnull=True).values('id', 'name'),
        'groups': Group.objects.all(),
        'py_prompt': last_prompt.prompt if last_prompt else None,
        'py_functions': PyFunction.objects.all(),
        'default_value': DefaultValues.objects.first(),
        'greeting': greeting,
        'chats': chats
    }