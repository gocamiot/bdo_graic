from django.contrib import admin
from apps.common.models import Sidebar, AuditTrail, File
from django.contrib.auth.models import Group
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin
from tablib import Dataset

# Register your models here.

class ParentFilter(admin.SimpleListFilter):
    title = 'Parent'
    parameter_name = 'parent'

    def lookups(self, request, model_admin):
        parents = Sidebar.objects.filter(parent__isnull=True, is_active=True)
        return [(parent.id, parent.name) for parent in parents]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(parent_id=self.value())
        return queryset

class SafeForeignKeyWidget(ForeignKeyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None
        try:
            return self.model.objects.get(**{self.field: value})
        except self.model.DoesNotExist:
            return None

class SidebarResource(resources.ModelResource):
    group = fields.Field(
        column_name='group',
        attribute='group',
        widget=SafeForeignKeyWidget(Group, field='name')
    )

    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=SafeForeignKeyWidget(Sidebar, 'name')
    )

    class Meta:
        model = Sidebar
        import_id_fields = ('name', )
        fields = (
            'group',
            'name',
            'segment',
            'url_name',
            'icon',
            'info',
            'is_active',
            'parent',
            'order',
        )
        export_order = fields

    def import_data(self, dataset, dry_run=False, raise_errors=False, use_transactions=None, collect_failed_rows=False, **kwargs):
        parent_rows = []
        child_rows = []
        for row in dataset.dict:
            if not row.get('parent'):
                parent_rows.append(row)
            else:
                child_rows.append(row)

        reordered_dataset = Dataset(headers=dataset.headers)
        for row in parent_rows + child_rows:
            reordered_dataset.append([row.get(col) for col in dataset.headers])

        return super().import_data(
            reordered_dataset,
            dry_run=dry_run,
            raise_errors=raise_errors,
            use_transactions=use_transactions,
            collect_failed_rows=collect_failed_rows,
            **kwargs
        )

class SidebarAdmin(ImportExportModelAdmin):
    resource_class = SidebarResource
    list_display = ('name', 'segment', 'url_name', 'parent', 'order', 'is_active')
    search_fields = ('name', 'segment', 'url_name')
    list_filter = (ParentFilter, 'is_active', )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = Sidebar.objects.filter(parent__isnull=True, is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Sidebar, SidebarAdmin)


class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'object_id', 'field_name', 'old_value', 'new_value', 'changed_by', 'change_date')
    list_filter = ('changed_by', 'change_date', )
    search_fields = ('field_name', 'old_value', 'new_value', 'changed_by__username', 'content_type__model', 'object_id')
    readonly_fields = ('content_type', 'object_id', 'field_name', 'old_value', 'new_value', 'changed_by', 'change_date')

admin.site.register(AuditTrail, AuditTrailAdmin)


class FileAdmin(admin.ModelAdmin):
    list_display = ('description', 'created_by', 'created_at', 'status', )

admin.site.register(File, FileAdmin)