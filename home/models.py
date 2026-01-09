from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from apps.common.models import Sidebar
from apps.tables.models import ModelChoices
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.

class FileInfo(models.Model):
    path = models.URLField()
    info = models.CharField(max_length=255)

    def __str__(self):
        return self.path


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class JoinModel(BaseModel):
    model_name = models.CharField(max_length=255, unique=True)
    sidebar = models.ForeignKey(Sidebar, on_delete=models.SET_NULL, null=True, blank=True)
    base_model = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'app_label__in': getattr(settings, 'LOADER_MODEL_APPS')},
        related_name='base_model'
    )
    delta_model = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'app_label__in': getattr(settings, 'LOADER_MODEL_APPS')},
        related_name='delta_model',
        null=True, blank=True
    )
    base_fields = models.TextField(null=True, blank=True, help_text='Comma separated')
    delta_fields = models.TextField(null=True, blank=True, help_text='Comma separated')

    base_f_key_fields = models.TextField(null=True, blank=True, help_text='Comma separated')
    delta_f_key_fields = models.TextField(null=True, blank=True, help_text='Comma separated')

    join_method = models.CharField(max_length=255, null=True, blank=True)
    similarity_threshold = models.IntegerField(null=True, blank=True)
    split_by_space = models.BooleanField(default=False)
    split_character = models.CharField(max_length=20, null=True, blank=True)
    match_word_position = models.IntegerField(null=True, blank=True)
    pre_char = models.IntegerField(null=True, blank=True)
    post_char = models.IntegerField(null=True, blank=True)

    jaro_winkler = models.BooleanField(default=False)
    levenshtein = models.BooleanField(default=False)
    token_set_ratio = models.BooleanField(default=False)
    phonetic = models.BooleanField(default=False)
    fuzzy_wuzzy = models.BooleanField(default=False)

    python_function = models.TextField(null=True, blank=True)
    c_similarity_threshold = models.IntegerField(null=True, blank=True)

    split_at = models.CharField(max_length=20, null=True, blank=True)
    left_split_char = models.CharField(max_length=20, null=True, blank=True)
    email_pre_char = models.IntegerField(null=True, blank=True)
    email_post_char = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.model_name
    
import re
class IPE(models.Model):
    userID = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    parent = models.CharField(max_length=255, choices=ModelChoices.choices, null=True, blank=True)
    description = models.TextField()
    path = models.CharField(max_length=255, null=True, blank=True)
    favorite_id = models.TextField(null=True, blank=True)
    finding_id = models.TextField(null=True, blank=True)
    img_loader_id = models.TextField(null=True, blank=True)
    unique_id = models.TextField(null=True, blank=True)
    tab_id = models.TextField(null=True, blank=True)
    chart_id = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_description_dict(self):
        excluded_keys = {'Field', 'Start', 'End', 'Null', 'Not Null', 'Unique', 'Count'}
        result = {}
        current_key = None
        current_value_lines = []

        lines = self.description.splitlines()
        for line in lines:
            match = re.match(r'^([\w\s]+):\s*(.*)', line)
            if match:
                key, value = match.groups()
                key = key.strip()
                value = value.strip()

                if key in excluded_keys:
                    if current_key:
                        current_value_lines.append(line)
                    continue

                if current_key is not None:
                    result[current_key] = "\n".join(current_value_lines).strip()

                current_key = key
                current_value_lines = [value] if value else []
            else:
                if current_key:
                    current_value_lines.append(line)

        if current_key:
            result[current_key] = "\n".join(current_value_lines).strip()

        return result
    
class ColumnOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    table_name = models.CharField(max_length=100)
    column_order = models.JSONField()
    favorite_id = models.TextField(null=True, blank=True)
    finding_id = models.TextField(null=True, blank=True)
    img_loader_id = models.TextField(null=True, blank=True)
    unique_id = models.TextField(null=True, blank=True)
    tab_id = models.TextField(null=True, blank=True)

    # class Meta:
    #     unique_together = ('user', 'table_name')


class PyFunctionPrompt(models.Model):
    prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PyFunction(models.Model):
    name = models.CharField(max_length=255, unique=True)
    func = models.TextField()
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name