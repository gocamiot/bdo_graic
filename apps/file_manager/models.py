import os
from django.db import models
from apps.tables.models import ActionStatus, DocumentStatus, DocumentType
from home.models import Sidebar
from django.contrib.auth import get_user_model
from autoslug import AutoSlugField
from django.conf import settings
from loader.models import VectorModel
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

User = get_user_model()

# Create your models here.


class FileManager(models.Model):
    name = models.TextField()
    slug = AutoSlugField(populate_from='name', unique=True)
    sidebar = models.ForeignKey(Sidebar, on_delete=models.SET_NULL, null=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    action_status = models.CharField(max_length=50, choices=ActionStatus.choices, default=ActionStatus.IS_ACTIVE)
    folder_status = models.CharField(max_length=50, choices=DocumentStatus.choices, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_file_managers'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_file_managers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


def upload_file_with_dir(instance, filename):
    parts = []
    file_manager = instance.file_manager
    while file_manager:
        parts.insert(0, file_manager.name)
        file_manager = file_manager.parent

    folder_path = os.path.join(*parts)
    base_name, ext = os.path.splitext(filename)

    media_folder_path = os.path.join(settings.MEDIA_ROOT, folder_path)
    os.makedirs(media_folder_path, exist_ok=True)

    final_filename = filename
    full_file_path = os.path.join(media_folder_path, final_filename)

    counter = 2
    while os.path.exists(full_file_path):
        final_filename = f"{base_name}_{counter}{ext}"
        full_file_path = os.path.join(media_folder_path, final_filename)
        counter += 1

    return os.path.join(folder_path, final_filename)

class File(models.Model):
    file_manager = models.ForeignKey(
        FileManager,
        on_delete=models.CASCADE,
        related_name='files'
    )
    file = models.FileField(upload_to=upload_file_with_dir, max_length=500)
    action_status = models.CharField(max_length=50, choices=ActionStatus.choices, default=ActionStatus.IS_ACTIVE)
    file_status = models.CharField(max_length=50, choices=DocumentStatus.choices, null=True, blank=True)
    file_type = models.CharField(max_length=50, choices=DocumentType.choices, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_files'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_files'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return os.path.basename(self.file.name)

    def file_name(self):
        return os.path.basename(self.file.name)
        
    def file_size(self):
        if self.file and hasattr(self.file, 'size'):
            size = self.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.2f} KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size / (1024 * 1024):.2f} MB"
            else:
                return f"{size / (1024 * 1024 * 1024):.2f} GB"
        return "0 B"
    
    def short_file_name(self, length=20):
        name, ext = os.path.splitext(os.path.basename(self.file.name))
        if len(name) <= length:
            return f"{name}{ext}"

        keep = (length - 1) // 2
        start = name[:keep]
        end = name[-keep:]
        return f"{start}....{end}{ext}"


def get_current_vector_dimension(default: int = 1024) -> int:
    try:
        current = VectorModel.objects.filter(current=True).first()
        return current.dimension if current else default
    except Exception:
        return default

def get_current_vector_model(default: str = "BAAI/bge-large-en-v1.5") -> str:
    try:
        current = VectorModel.objects.filter(current=True).first()
        return current.name if current else default
    except Exception:
        return default

try:
    from pgvector.django import VectorField

    def VECTOR_FIELD():
        dim = get_current_vector_dimension()
        return VectorField(dimensions=dim, null=True, blank=True)
except ImportError:
    def VECTOR_FIELD():
        return models.TextField(null=True, blank=True)

class FileChunk(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    vector = VECTOR_FIELD()
    vector_model = models.CharField(
        max_length=255,
        default=get_current_vector_model
    )
    fts = SearchVectorField(null=True, blank=True)
    chunk_text = models.TextField(null=True, blank=True)
    chunk_index = models.IntegerField() 
    page_number = models.IntegerField(null=True, blank=True)
    position = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            GinIndex(fields=["fts"]),
        ]


class FilterMethod(models.TextChoices):
    vector = 'vector', 'Vector'
    graic = 'graic', 'grAIc'

class DefaultValues(models.Model):
    similarity_threshold = models.IntegerField(null=True, blank=True)
    dynamic_similarity = models.BooleanField(default=False)
    dynamic_rows = models.IntegerField(null=True, blank=True)
    extract_keywords = models.BooleanField(default=True)
    filter_method = models.CharField(max_length=20, choices=FilterMethod.choices, default=FilterMethod.vector)