import os
from django.db import models
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

User = get_user_model()

# Create your models here.

class Sidebar(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    segment = models.CharField(max_length=255, null=True, blank=True)
    url_name = models.CharField(max_length=255, null=True, blank=True)
    dynamic_url = models.CharField(max_length=255, null=True, blank=True)
    icon = models.TextField(null=True, blank=True, help_text="SVG image only")
    info = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    order = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    def clean(self):
        if self.order and self.parent:
            raise ValidationError({'order': 'Order is only available for parent items.'})

        if self.order and not self.parent:
            if Sidebar.objects.filter(order=self.order).exclude(pk=self.pk).exists():
                raise ValidationError({'order': 'A parent with this order already exists.'})
        
        super().clean()
    class Meta:
        ordering = ['order'] 


class FileStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    DELETED = 'DELETED', 'Deleted'


class File(models.Model):
    file = models.FileField(upload_to='secure_file')
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=FileStatus.choices, default=FileStatus.ACTIVE)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='updated_by'
    )
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.file.name
    
    def get_filename(self):
        return os.path.basename(self.file.name)

    def file_size(self):
        size = self.file.size
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"

class AuditTrail(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    field_name = models.CharField(max_length=255)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="By")
    change_date = models.DateTimeField(auto_now_add=True, verbose_name="Date")

    def __str__(self):
        return f"{self.content_type} - {self.field_name} changed"


# New filter
from apps.tables.models import ModelChoices

class FieldType(models.TextChoices):
    TEXT = 'TEXT', 'Text or Character'
    DATE = 'DATE', 'Date'
    INT = 'INT', 'Integer'
    FLOAT = 'FLOAT', 'Float'

class SavedFilter(models.Model):
    userID = models.IntegerField()
    parent = models.CharField(max_length=255, choices=ModelChoices.choices)
    field_name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FieldType.choices)
    value_start = models.CharField(max_length=100, blank=True, null=True)
    value_end = models.CharField(max_length=100, blank=True, null=True)
    
    # Checkbox fields
    is_not = models.BooleanField(default=False)
    is_null = models.BooleanField(default=False)
    is_not_null = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    is_count = models.BooleanField(default=False)
    
    s_model_choice = models.CharField(max_length=255, choices=ModelChoices.choices, null=True, blank=True, verbose_name='Source Model Choice')
    is_hidden = models.BooleanField(default=False)
    favorite_id = models.TextField(null=True, blank=True)
    finding_id = models.TextField(null=True, blank=True)
    img_loader_id = models.TextField(null=True, blank=True)
    unique_id = models.TextField(null=True, blank=True)
    tab_id = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.userID} - {self.parent} - {self.field_name}"