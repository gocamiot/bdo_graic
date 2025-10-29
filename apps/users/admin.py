from django.contrib import admin
from apps.users.models import Profile
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from apps.users.models import LoginLogs, Security, ChangeLog
from django import forms
from import_export import resources, fields
from django.contrib.auth.models import Group, Permission
from import_export.widgets import ManyToManyWidget
from import_export.admin import ImportExportModelAdmin

User = get_user_model()

admin.site.register(Profile)


class CustomUserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.blocked:
            self.fields['blocked'].disabled = True


class CustomUserAdmin(auth_admin.UserAdmin):
    form = CustomUserAdminForm

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email", "phone_number", "otp_method", "required_password", "blocked", "last_password_change", )}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_audituser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["username", "first_name", "email", "is_superuser", "is_active", "is_staff"]


    def save_model(self, request, obj, form, change):
        required_password = form.cleaned_data.get('required_password')
        if 'required_password' in form.changed_data:
            if required_password:
                obj.blocked = False 
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj=obj)
        
        if obj and request.user == obj:
            return readonly_fields + ('required_password',)

        if not request.user.is_audituser:
            return readonly_fields + ('is_audituser',)

        return readonly_fields

admin.site.register(User, CustomUserAdmin)


class LoginLogsAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_expired', 'login_time', 'logout_time', )

admin.site.register(LoginLogs, LoginLogsAdmin)

admin.site.register(Security)

class ChangeLogAdmin(admin.ModelAdmin):
    list_display = ('changed_by', 'model_name', 'field_name', 'old_value', 'new_value', 'change_date')

    def changed_by(self, obj):
        return obj.user

    changed_by.short_description = 'Changed By'

admin.site.register(ChangeLog, ChangeLogAdmin)

class GroupResource(resources.ModelResource):
    permissions = fields.Field(
        column_name='permissions',
        attribute='permissions',
        widget=ManyToManyWidget(Permission, field='codename')
    )

    class Meta:
        model = Group
        import_id_fields = ('name',)
        fields = ('name', 'permissions')

admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(ImportExportModelAdmin):
    resource_class = GroupResource