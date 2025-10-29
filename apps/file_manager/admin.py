from django.contrib import admin
from apps.file_manager.models import File, FileManager, FileChunk, DefaultValues
from django.db import transaction
from apps.common.signals import create_file_chunks_task

# Register your models here.

@admin.register(FileManager)
class FileManagerAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'action_status', 'created_by', 'created_at')
    search_fields = ('name',)
    list_filter = ('action_status', 'created_by')


@admin.action(description="Re-chunk selected files")
def rechunk_files(modeladmin, request, queryset):
    for file_instance in queryset:
        with transaction.atomic():
            FileChunk.objects.filter(file=file_instance).delete()
            create_file_chunks_task.delay(file_instance.id)

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('file_manager', 'file', 'action_status', 'file_status',)
    search_fields = ('file',)
    list_filter = ('file_status', 'file_type', 'action_status')
    actions = [rechunk_files]


@admin.register(FileChunk)
class FileChunkAdmin(admin.ModelAdmin):
    list_display = ('file', 'vector_model', 'chunk_index', 'created_at', )
    search_fields = ('vector_model', )


admin.site.register(DefaultValues)