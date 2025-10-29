from django.contrib import admin
from .models import (
    TableDropdownItem, TableDropdownSubItem, HideShowFilter, DynamicQuery, 
    ExternalDatabase, TemporaryTable, ExportDB, ExportLog, Finding,
    Image, ImageLoader, FindingAction, Tab
)

# Register your models here.
admin.site.register(TableDropdownItem)
admin.site.register(TableDropdownSubItem)

class FindingAdmin(admin.ModelAdmin):
    list_display = ('id', 'parent', 'email_action_status', 'action_status', )

admin.site.register(Finding, FindingAdmin)

class FindingActionAdmin(admin.ModelAdmin):
    list_display = ('finding', 'status', )

admin.site.register(FindingAction, FindingActionAdmin)

class ExportDBAdmin(admin.ModelAdmin):
    list_display = ('export_to', 'created_at', )

admin.site.register(ExportDB, ExportDBAdmin)


class ExportLogAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'count_b_copy', 'count_a_copy', 'success', 'start_at', 'finished_at',  )

admin.site.register(ExportLog, ExportLogAdmin)


class HideShowFilterAdmin(admin.ModelAdmin):
    list_display = ('parent', 'key', 'value', )
    list_filter = ('parent', )

admin.site.register(HideShowFilter, HideShowFilterAdmin)

class DynamicQueryAdmin(admin.ModelAdmin):
    filter_horizontal = ('temporary_tables', )
    list_display = ('id', 'view_name', 'is_correct', 'rows', )

class TemporaryTableAdmin(admin.ModelAdmin):
    list_display = ('id', 'temporary_table_name', 'is_correct', 'rows', )

class ExternalDBAdmin(admin.ModelAdmin):
    list_display = ('db_type', 'db_name', 'db_host', 'db_port', 'connected', )
    

admin.site.register(DynamicQuery, DynamicQueryAdmin)
admin.site.register(TemporaryTable, TemporaryTableAdmin)
admin.site.register(ExternalDatabase, ExternalDBAdmin)

admin.site.site_title = "GRC Server"

admin.site.register(Image)
admin.site.register(ImageLoader)
admin.site.register(Tab)