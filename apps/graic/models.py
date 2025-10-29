import uuid, os
from django.db import models
from datetime import date, datetime
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.

class AIPrePrompt(models.Model):
    role = models.CharField(max_length=255, default='Analyst')
    name = models.CharField(max_length=255, default='grAIc')
    date = models.DateField(verbose_name="Today's date", default=date.today)
    time = models.TimeField(verbose_name="Current time", default=datetime.now)

    def __str__(self):
        return self.name

class Chat(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"


TYPE_CHOICES = [
    ('file', 'File'),
    ('dt', 'DT')
]

class Graic(models.Model):
    FEEDBACK_CHOICES = [
        ('like', 'Like'),
        ('dislike', 'Dislike'),
        ('none', 'None'),
    ]
    
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, null=True, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    prompt = models.TextField()
    reasoning = models.TextField(null=True, blank=True)
    thinking = models.TextField(null=True, blank=True)
    response = models.TextField(null=True, blank=True)
    time_take = models.FloatField(null=True, blank=True)
    is_dt = models.BooleanField(default=False)
    summary_response = models.TextField(null=True, blank=True)
    generated_file = models.FileField(upload_to='generated_files/', null=True, blank=True)
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='file'
    )
    feedback = models.CharField(
        max_length=10,
        choices=FEEDBACK_CHOICES,
        default='none'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'grAIc'
        verbose_name_plural = 'grAIc'

    def file_name(self):
        if self.generated_file:
            return os.path.basename(self.generated_file.name)
        return None

class WorkflowType(models.TextChoices):
    summary = 'summary', 'Summary'


class PrePrompt(models.Model):
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='file'
    )
    workflow = models.CharField(max_length=255, choices=WorkflowType.choices, default=WorkflowType.summary)
    prompt = models.TextField()
    email_prompt = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('type', 'workflow', )


class Agent(models.Model):
    name = models.CharField(max_length=255, unique=True)
    manifest = models.TextField()
    system_prompt = models.TextField()
    llm = models.CharField(max_length=255, null=True, blank=True)
    online = models.BooleanField(default=True)

    def __str__(self):
        return self.name