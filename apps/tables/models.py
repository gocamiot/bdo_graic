import pytesseract
import os, csv
from django.db import models, connections, OperationalError, transaction
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection, OperationalError
from django.db import models, connections
from background_task import background
from django.apps import apps
from django.db.utils import IntegrityError
from django.utils import timezone
from django.contrib.admin.models import LogEntry
from django_quill.fields import QuillField
from PIL import Image as PILImage
from django.contrib.postgres.search import SearchVectorField
from django.core.exceptions import ValidationError
from apps.tables.choices import *

try:
    from pgvector.django import VectorField
except ImportError:
    pass

User = get_user_model()

# Create your models here.


class ModelChoices(models.TextChoices): 
    SAGE_USER_LIST = 'SAGE_USER_LIST', 'SAGEUserList'
    CONTROL_AD_USER = 'CONTROL_AD_USER', 'ControlADUser'
    CHANGE_REQUESTS = 'CHANGE_REQUESTS', 'ChangeRequests'
    HR_USER_LIST = 'HR_USER_LIST', 'HRUserList'
    TICKET_LOGGING = 'TICKET_LOGGING', 'TicketLogging'
    UNIFIED_ACCESS_MANAGEMENT = 'UNIFIED_ACCESS_MANAGEMENT', 'UnifiedAccessManagement'
    FAVORITE = 'FAVORITE', _('Favorite')
    UNIQUE = 'UNIQUE', _('Unique')
    FINDING = 'FINDING', _('Finding')
    TAB = 'TAB', _('Tab')
    CHART = 'CHART', _('Chart')
    COPY_DT = 'COPY_DT', _('Copy DT')
    FINDING_VIEW = 'FINDING_VIEW', _('Finding View')
    IMAGE_LOADER = 'IMAGE_LOADER', _('Image Loader')
    IMAGES = 'IMAGES', 'Images'
    FINDING_ATTACHMENT = 'FINDING_ATTACHMENT', 'Finding Attachment'


class Common(models.Model):
    parent = models.CharField(max_length=255, choices=ModelChoices.choices)
    value = models.CharField(max_length=255)

    class Meta:
        abstract = True


class PageItems(models.Model):
    userID = models.IntegerField()
    parent = models.CharField(max_length=255, choices=ModelChoices.choices)
    items_per_page = models.IntegerField(default=25)
    favorite_id = models.TextField(null=True, blank=True)
    finding_id = models.TextField(null=True, blank=True)
    img_loader_id = models.TextField(null=True, blank=True)
    unique_id = models.TextField(null=True, blank=True)
    tab_id = models.TextField(null=True, blank=True)
    

class HideShowFilter(Common):
    userID = models.IntegerField()
    parent = models.CharField(max_length=255, choices=ModelChoices.choices)
    key = models.CharField(max_length=255)
    value = models.BooleanField(default=False)
    favorite_id = models.TextField(null=True, blank=True)
    finding_id = models.TextField(null=True, blank=True)
    img_loader_id = models.TextField(null=True, blank=True)
    unique_id = models.TextField(null=True, blank=True)
    tab_id = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.key

class ServerFilter(Common):
    userID = models.IntegerField()
    key = models.CharField(max_length=255)
    favorite_id = models.TextField(null=True, blank=True)
    finding_id = models.TextField(null=True, blank=True)
    img_loader_id = models.TextField(null=True, blank=True)
    unique_id = models.TextField(null=True, blank=True)
    tab_id = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.key


class UserFilter(Common):
    userID = models.IntegerField()
    parent = models.CharField(max_length=255, choices=ModelChoices.choices, null=True, blank=True)
    key = models.CharField(max_length=255)
    favorite_id = models.TextField(null=True, blank=True)
    finding_id = models.TextField(null=True, blank=True)
    img_loader_id = models.TextField(null=True, blank=True)
    unique_id = models.TextField(null=True, blank=True)
    tab_id = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.key
    

class DateRangeFilter(models.Model):
    userID = models.IntegerField()
    parent = models.CharField(max_length=255, choices=ModelChoices.choices)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    key = models.CharField(max_length=255)
    favorite_id = models.TextField(null=True, blank=True)
    finding_id = models.TextField(null=True, blank=True)
    img_loader_id = models.TextField(null=True, blank=True)
    unique_id = models.TextField(null=True, blank=True)
    tab_id = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.key

class IntRangeFilter(models.Model):
    userID = models.IntegerField()
    parent = models.CharField(max_length=255, choices=ModelChoices.choices)
    from_number = models.IntegerField(null=True, blank=True)
    to_number = models.IntegerField(null=True, blank=True)
    key = models.CharField(max_length=255)
    favorite_id = models.TextField(null=True, blank=True)
    finding_id = models.TextField(null=True, blank=True)
    img_loader_id = models.TextField(null=True, blank=True)
    unique_id = models.TextField(null=True, blank=True)
    tab_id = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.key


class FloatRangeFilter(models.Model):
    userID = models.IntegerField()
    parent = models.CharField(max_length=255, choices=ModelChoices.choices)
    from_float_number = models.FloatField(null=True, blank=True)
    to_float_number = models.FloatField(null=True, blank=True)
    key = models.CharField(max_length=255)
    favorite_id = models.TextField(null=True, blank=True)
    finding_id = models.TextField(null=True, blank=True)
    img_loader_id = models.TextField(null=True, blank=True)
    unique_id = models.TextField(null=True, blank=True)
    tab_id = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.key


class ActionStatus(models.TextChoices):
    IS_ACTIVE = 'IS_ACTIVE', _('Is Active')
    DELETED = 'DELETED', _('Deleted')

class VendorLinked(models.Model):
    base_string = models.TextField()
    match_string = models.TextField()


class ApplicationLinked(models.Model):
    base_string = models.TextField()
    match_string = models.TextField()

from django.contrib.contenttypes.models import ContentType
from django.conf import settings
import uuid

class Favorite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'app_label__in': getattr(settings, 'LOADER_MODEL_APPS')},
        verbose_name = 'DT'
    )
    model_choices = models.CharField(max_length=255)
    pre_filters = models.TextField(null=True, blank=True)
    pre_columns = models.TextField(null=True, blank=True)
    richtext_fields = models.TextField(null=True, blank=True)
    page_items = models.ForeignKey(PageItems, on_delete=models.SET_NULL, null=True, blank=True)
    hide_show_filters = models.ManyToManyField(HideShowFilter, blank=True)
    user_filters = models.ManyToManyField(UserFilter, blank=True)
    server_filters = models.ManyToManyField(ServerFilter, blank=True)
    date_range_filters = models.ManyToManyField(DateRangeFilter, blank=True)
    int_range_filters = models.ManyToManyField(IntRangeFilter, blank=True)
    float_range_filters = models.ManyToManyField(FloatRangeFilter, blank=True)
    saved_filters = models.ManyToManyField('common.SavedFilter', blank=True)
    # search_items = models.JSONField(null=True, blank=True)
    search = models.CharField(max_length=255, null=True, blank=True)
    order_by = models.CharField(max_length=255, null=True, blank=True)
    snapshot = models.CharField(max_length=255, null=True, blank=True)
    query_snapshot = models.CharField(max_length=255, null=True, blank=True)
    is_dynamic_query = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    has_documents = models.BooleanField(default=False)
    is_split_dt = models.BooleanField(default=False)
    parent_dt = models.UUIDField(null=True, blank=True)
    match_field = models.CharField(max_length=255, null=True, blank=True)
    child_dt = models.UUIDField(null=True, blank=True)
    img_loader_id = models.UUIDField(null=True, blank=True)

    action_status = models.CharField(max_length=50, choices=ActionStatus.choices, default=ActionStatus.IS_ACTIVE)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)


class Tab(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'app_label__in': getattr(settings, 'LOADER_MODEL_APPS')},
        verbose_name = 'DT'
    )
    model_choices = models.CharField(max_length=255)
    pre_filters = models.TextField(null=True, blank=True)
    pre_columns = models.TextField(null=True, blank=True)
    richtext_fields = models.TextField(null=True, blank=True)
    page_items = models.ForeignKey(PageItems, on_delete=models.SET_NULL, null=True, blank=True)
    hide_show_filters = models.ManyToManyField(HideShowFilter, blank=True)
    user_filters = models.ManyToManyField(UserFilter, blank=True)
    server_filters = models.ManyToManyField(ServerFilter, blank=True)
    date_range_filters = models.ManyToManyField(DateRangeFilter, blank=True)
    int_range_filters = models.ManyToManyField(IntRangeFilter, blank=True)
    float_range_filters = models.ManyToManyField(FloatRangeFilter, blank=True)
    saved_filters = models.ManyToManyField('common.SavedFilter', blank=True)
    # search_items = models.JSONField(null=True, blank=True)
    search = models.CharField(max_length=255, null=True, blank=True)
    search_mode = models.CharField(max_length=255, null=True, blank=True)
    order_by = models.CharField(max_length=255, null=True, blank=True)
    snapshot = models.CharField(max_length=255, null=True, blank=True)
    query_snapshot = models.CharField(max_length=255, null=True, blank=True)
    is_dynamic_query = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    has_documents = models.BooleanField(default=False)
    is_split_dt = models.BooleanField(default=False)
    parent_dt = models.UUIDField(null=True, blank=True)
    match_field = models.CharField(max_length=255, null=True, blank=True)
    child_dt = models.UUIDField(null=True, blank=True)
    img_loader_id = models.UUIDField(null=True, blank=True)
    base_view = models.TextField(null=True, blank=True)
    sidebar_parent = models.TextField(null=True, blank=True)
    selected_rows = models.TextField(null=True, blank=True)

    action_status = models.CharField(max_length=50, choices=ActionStatus.choices, default=ActionStatus.IS_ACTIVE)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

class TabNotes(models.Model):
    tab = models.OneToOneField(Tab, on_delete=models.CASCADE)
    note = QuillField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)


class ChartType2(models.TextChoices):
    BASE_CHART = 'BASE_CHART', 'Base Chart'
    RISK_CHART = 'RISK_CHART', 'Risk Chart'

class BaseCharts(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    base_view = models.TextField()
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True
    )
    chart_type = models.CharField(max_length=100, choices=ChartType2.choices, default=ChartType2.BASE_CHART)
    name = models.TextField(max_length=255, default="Charts")
    saved_filters = models.ManyToManyField('common.SavedFilter', blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('base_view', 'name')

    class Meta:
        verbose_name = "Base Chart"
        verbose_name_plural = "Base Charts"

class ChartType(models.TextChoices):
    BAR = 'BAR', 'Bar Chart'
    LINE = 'LINE', 'Line Chart'
    PIE = 'PIE', 'Pie Chart'

class TabCharts(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    base_chart = models.ForeignKey(BaseCharts, on_delete=models.CASCADE)
    parent_tab = models.ForeignKey(Tab, on_delete=models.CASCADE)
    name = models.TextField(max_length=255)
    x_field = models.CharField(max_length=100)
    y_field = models.CharField(max_length=100, null=True, blank=True)
    chart_type = models.CharField(max_length=20, choices=ChartType.choices, default=ChartType.BAR)
    color = models.CharField(max_length=100, default='#008FFB', verbose_name='Bar or Line color')
    info = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.x_field == self.y_field:
            raise ValidationError("x_field and y_field cannot be the same.")
    
    class Meta:
        verbose_name = "Tab Chart"
        verbose_name_plural = "Tab Charts"

class ChartPrompt(models.Model):
    base_chart = models.OneToOneField(BaseCharts, on_delete=models.CASCADE)
    prompt = models.TextField(null=True, blank=True)

class ScheduledChartExport(models.Model):
    EXPORT_TYPE_CHOICES = (
        ("docx", "DOCX"),
        ("pdf", "PDF"),
    )

    FREQUENCY_CHOICES = (
        ("once", "One time"),
        ("hourly", "Hourly"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chart = models.ForeignKey(TabCharts, on_delete=models.CASCADE)

    chart_image = models.TextField(blank=True, null=True)
    export_type = models.CharField(max_length=10, choices=EXPORT_TYPE_CHOICES)
    export_option = models.CharField(max_length=10, default="grc")

    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(null=True, blank=True)

    hour_interval = models.PositiveIntegerField(null=True, blank=True)
    time_of_day = models.TimeField(null=True, blank=True)
    weekdays = models.JSONField(default=list, blank=True)
    month_day = models.PositiveSmallIntegerField(null=True, blank=True)

    custom_prompt = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_run_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.chart.name} ({self.frequency})"

class BusinessImpactItem(models.Model):
    code = models.CharField(
        max_length=50,
        choices=BusinessImpact.choices,
        unique=True
    )

    def __str__(self):
        return self.get_code_display()

class RiskAssessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    base_chart = models.ForeignKey(BaseCharts, on_delete=models.CASCADE)
    parent_tab = models.OneToOneField(Tab, on_delete=models.CASCADE)
    name = models.TextField(max_length=255)
    inherent_impact = models.CharField(
        max_length=20,
        choices=InherentImpact.choices
    )
    likelihood = models.CharField(
        max_length=20,
        choices=Likelihood.choices
    )
    residual_risk = models.CharField(
        max_length=20,
        choices=ResidualRiskRating.choices
    )
    confidence = models.CharField(
        max_length=20,
        choices=ConfidenceInResults.choices
    )
    primary_root_cause = models.CharField(
        max_length=50,
        choices=PrimaryRootCause.choices
    )
    secondary_root_cause = models.CharField(
        max_length=50,
        choices=SecondaryRootCause.choices,
        null=True,
        blank=True
    )

    business_impacts = models.ManyToManyField(
        BusinessImpactItem,
        blank=True
    )
    audit_recommendation = QuillField(null=True, blank=True)
    recommended_owner_role = models.CharField(
        max_length=20,
        choices=OwnerRole.choices
    )

    target_remediation_date = models.DateField()

    management_response = models.TextField(null=True, blank=True)
    agreed_action_plan = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name

class ScoreCard(models.Model):
    risk_card = models.OneToOneField(RiskAssessment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.risk_card.name

class ScheduledRiskExport(models.Model):
    EXPORT_TYPE_CHOICES = (
        ("docx", "DOCX"),
        ("pdf", "PDF"),
    )

    FREQUENCY_CHOICES = (
        ("once", "One time"),
        ("hourly", "Hourly"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    risk = models.ForeignKey(RiskAssessment, on_delete=models.CASCADE)

    chart_image = models.TextField(blank=True, null=True)
    export_type = models.CharField(max_length=10, choices=EXPORT_TYPE_CHOICES)
    export_option = models.CharField(max_length=10, default="grc")

    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(null=True, blank=True)

    hour_interval = models.PositiveIntegerField(null=True, blank=True)
    time_of_day = models.TimeField(null=True, blank=True)
    weekdays = models.JSONField(default=list, blank=True)
    month_day = models.PositiveSmallIntegerField(null=True, blank=True)

    custom_prompt = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_run_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.risk.name} ({self.frequency})"

class EmailActionStatus(models.TextChoices):
    OPEN = 'OPEN', 'Open'
    CLOSE = 'CLOSE', 'Close'

class Finding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    description = QuillField(null=True, blank=True)
    recommendation = QuillField(null=True, blank=True)
    #status = models.TextField(null=True, blank=True)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'app_label__in': getattr(settings, 'LOADER_MODEL_APPS')},
        verbose_name = 'DT',
        null=True, blank=True
    )
    model_choices = models.CharField(max_length=255)
    pre_filters = models.TextField(null=True, blank=True)
    pre_columns = models.TextField(null=True, blank=True)
    richtext_fields = models.TextField(null=True, blank=True)
    page_items = models.ForeignKey(PageItems, on_delete=models.SET_NULL, null=True, blank=True)
    hide_show_filters = models.ManyToManyField(HideShowFilter, blank=True)
    user_filters = models.ManyToManyField(UserFilter, blank=True)
    server_filters = models.ManyToManyField(ServerFilter, blank=True)
    date_range_filters = models.ManyToManyField(DateRangeFilter, blank=True)
    int_range_filters = models.ManyToManyField(IntRangeFilter, blank=True)
    float_range_filters = models.ManyToManyField(FloatRangeFilter, blank=True)
    saved_filters = models.ManyToManyField('common.SavedFilter', blank=True)
    # search_items = models.JSONField(null=True, blank=True)
    search = models.CharField(max_length=255, null=True, blank=True)
    order_by = models.CharField(max_length=255, null=True, blank=True)
    snapshot = models.CharField(max_length=255, null=True, blank=True)
    query_snapshot = models.CharField(max_length=255, null=True, blank=True)
    is_dynamic_query = models.BooleanField(default=False)
    has_documents = models.BooleanField(default=False)
    is_split_dt = models.BooleanField(default=False)
    parent_dt = models.UUIDField(null=True, blank=True)
    match_field = models.CharField(max_length=255, null=True, blank=True)
    child_dt = models.UUIDField(null=True, blank=True)
    selected_rows = models.TextField(null=True, blank=True)

    # Action   
    companies = models.CharField(max_length=255, null=True, blank=True)
    itgc_categories = models.CharField(max_length=255, null=True, blank=True)
    itgc_questions = models.CharField(max_length=255, null=True, blank=True)
    action_type = models.CharField(max_length=255, null=True, blank=True)
    # action_to = models.CharField(max_length=255, null=True, blank=True)
    action_deadline = models.DateTimeField(null=True, blank=True)
    action_note = models.TextField(null=True, blank=True)
    email_action_status = models.CharField(
        max_length=20, 
        choices=EmailActionStatus.choices, 
        default=EmailActionStatus.OPEN
    )

    action_status = models.CharField(max_length=50, choices=ActionStatus.choices, default=ActionStatus.IS_ACTIVE)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.CharField(max_length=255, null=True, blank=True)

    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    updated_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    version_control = models.IntegerField(default=1, editable=False)

    date_fields_to_convert = []
    integer_fields = []                                                                                                                                                                                          
    float_fields = []

    @property
    def is_parent(self):
        return self.finding_set.exists()

class DocumentStatus(models.TextChoices):
    APPROVED = 'Approved', 'Approved'
    NOTAPPROVED = 'Not Approved', 'Not Approved'

class AttachmentType(models.TextChoices):
    EVIDENCE = 'EVIDENCE', 'Evidence'
    INSIGHTS = 'INSIGHTS', 'Insights'

class FindingAttachment(models.Model):
    finding = models.ForeignKey(Finding, on_delete=models.CASCADE)
    attachment = models.FileField(upload_to='attachment')
    attachment_type = models.CharField(max_length=50, choices=AttachmentType.choices)
    description = models.TextField(null=True, blank=True)
    attachment_status = models.CharField(max_length=50, choices=DocumentStatus.choices)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    version = models.TextField(null=True, blank=True)

    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    updated_by = models.CharField(max_length=255, null=True, blank=True)
    version_control = models.IntegerField(default=1, editable=False)

    action_status = models.CharField(max_length=50, choices=ActionStatus.choices, default=ActionStatus.IS_ACTIVE)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.CharField(max_length=255, null=True, blank=True)

    file_fields = ['attachment']
    date_fields_to_convert = []
    integer_fields = []                                                                                                                                                                                          
    float_fields = []

    @property
    def is_parent(self):
        return self.findingattachment_set.exists()

    @property
    def csv_text(self):
        if self.attachment and self.attachment.name.endswith('.csv'):
            try:
                file_path = self.attachment.path
                if not os.path.exists(file_path):
                    return "File does not exist."

                with open(file_path, 'r', encoding='latin-1') as file:
                    reader = csv.reader(file)
                    rows = list(reader)

                text = '\n'.join([','.join(row) for row in rows])
                return text

            except Exception as e:
                return f"Error reading CSV file: {str(e)}"

        return "No CSV file available."

class FindingAction(models.Model):
    finding = models.ForeignKey(Finding, on_delete=models.CASCADE, related_name="actions")
    action_to = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=EmailActionStatus.choices,
        default=EmailActionStatus.OPEN,
        verbose_name='Action Status'
    )

    class Meta:
        unique_together = ('finding', 'action_to')

class TableDropdownItem(models.Model):
    item = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    loader_instance = models.IntegerField(null=True, blank=True)


class TableDropdownSubItem(models.Model):
    item = models.ForeignKey(TableDropdownItem, on_delete=models.CASCADE, related_name="subitems")
    subitem = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

class DependentDropdown(models.Model):
    title = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)



class DocumentType(models.TextChoices):
    CONTRACT = 'Contract', 'Contract'
    INVOICE = 'Invoice', 'Invoice'
    STATEMENT = 'Statement', 'Statement'
  
class DocumentType_GR(models.TextChoices):
    Design  = 'Design', 'Design'
    Framework  = 'Framework', 'Framework'
    Guideline  = 'Guideline', 'Guideline'
    Noting  = 'Noting', 'Noting'
    Policy  = 'Policy', 'Policy'
    Procedure  = 'Procedure', 'Procedure'
    Process  = 'Process', 'Process'
    Standard  = 'Standard', 'Standard'
    No_Longer_Required  = 'No Longer Required', 'No_Longer_Required'
    Red_Line_Draft  = 'Red Line Draft', 'Red_Line_Draft'

BATCH_SIZE = 5000

def database_connection(db, query="SELECT 1"):
    try:
        connection_params = {
            'ENGINE': db.db_type if db.db_type == 'mssql' else f'django.db.backends.{db.db_type}',
            'NAME': db.db_name,
            'USER': db.db_user,
            'PASSWORD': db.db_pass,
            'HOST': db.db_host if db.db_type != 'mssql' else f"{db.db_host},{db.db_port}",
            'PORT': db.db_port if db.db_type != 'mssql' else '',
            'ATOMIC_REQUESTS': False,
            'TIME_ZONE': 'UTC',
            'CONN_HEALTH_CHECKS': False,
            'CONN_MAX_AGE': 0,
            'AUTOCOMMIT': True,
            'OPTIONS': {
                'connect_timeout': 5,
            }
        }
        if db.db_type == DBType.mssql:
            connection_params['OPTIONS']["driver"] = "ODBC Driver 17 for SQL Server"

        connections.databases[db.db_name] = connection_params
        result = ""
        row_count = 0
        columns = []
        with connections[db.db_name].cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            row_count = cursor.rowcount
            columns = [col[0] for col in cursor.description]

        db.connected = True

        try:
            call_command('makemigrations', interactive=False, verbosity=0)
            call_command('migrate', database=db.db_name, interactive=False, verbosity=0)
            print(f"Migrated successfully!")
        except Exception as e:
            print(f"Migration failed: {e}")

        return result, row_count, columns

    except OperationalError:
        db.connected = False


def mssql_database_connection(db, query="SELECT 1"):
    try:
        connection_params = {
            'ENGINE': db.db_type,
            'NAME': db.db_name,
            'USER': db.db_user,
            'PASSWORD': db.db_pass,
            'HOST': f"{db.db_host},{db.db_port}",
            'ATOMIC_REQUESTS': False,
            'TIME_ZONE': 'UTC',
            'CONN_HEALTH_CHECKS': False,
            'CONN_MAX_AGE': 0,
            'AUTOCOMMIT': True,
            'OPTIONS': {
                'connect_timeout': 5,
                "driver": "ODBC Driver 17 for SQL Server",
            }
        }

        connections.databases[db.db_name] = connection_params
        result = ""
        row_count = 0
        with connections[db.db_name].cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            row_count = cursor.rowcount

        db.connected = True

        return result, row_count

    except OperationalError:
        db.connected = False


class DBType(models.TextChoices):
    postgresql = 'postgresql', 'PostgreSQL'
    mysql = 'mysql', 'MySQL'
    mssql = 'mssql', 'SQL Server'


class ExternalDatabase(models.Model):
    db_type = models.CharField(max_length=100, choices=DBType.choices)
    connection_name = models.CharField(max_length=255, unique=True)
    db_name = models.CharField(max_length=255)
    db_user = models.CharField(max_length=255)
    db_pass = models.CharField(max_length=255)
    db_host = models.CharField(max_length=255)
    db_port = models.CharField(max_length=255)
    connected = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.connection_name


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.db_type == DBType.mssql:
            mssql_database_connection(self)
        else:
            database_connection(self)

        if self._state.adding:
            self.created_at = timezone.now()

        self.updated_at = timezone.now()

        super().save(*args, **kwargs)


class TemporaryTable(models.Model):
    database = models.ForeignKey(
        ExternalDatabase, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="For local database like sqlite keep this field empty"
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name = 'Choose model',
        related_name='temporary_table'
    )
    temporary_table_name = models.CharField(max_length=255, unique=True)
    query = models.TextField()
    is_correct = models.BooleanField(default=False, editable=False)
    rows = models.IntegerField(null=True, blank=True)
    error_log = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.temporary_table_name

    def save(self, *args, **kwargs):
        try:
            if self.database:
                if self.database.db_type == DBType.mssql:
                    result, row_count = mssql_database_connection(self.database, self.query)
                    if result and row_count:
                        self.rows = row_count
                        self.is_correct = True

                else:
                    result, row_count = database_connection(self.database, self.query)
                    if result and row_count:
                        self.rows = row_count
                        self.is_correct = True
            else:
                with connection.cursor() as cursor:
                    cursor.execute(self.query)
                    self.is_correct = True
                    self.rows = cursor.rowcount
            
        except OperationalError as e:
            self.is_correct = False
            self.error_log = str(e)

        if self._state.adding:
            self.created_at = timezone.now()

        self.updated_at = timezone.now()

        super().save(*args, **kwargs)


class DynamicQuery(models.Model):
    database = models.ForeignKey(
        ExternalDatabase, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="For local database like sqlite keep this field empty"
    )
    view_name = models.CharField(max_length=255, unique=True)
    query = models.TextField()
    temporary_tables = models.ManyToManyField(TemporaryTable, blank=True)
    is_correct = models.BooleanField(default=False, editable=False)
    rows = models.IntegerField(null=True, blank=True)
    error_log = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.view_name

    def save(self, *args, **kwargs):
        try:
            if self.database:
                if self.database.db_type == DBType.mssql:
                    result, row_count = mssql_database_connection(self.database, self.query)
                    if result and row_count:
                        self.rows = row_count
                        self.is_correct = True

                else:
                    result, row_count = database_connection(self.database, self.query)
                    if result and row_count:
                        self.rows = row_count
                        self.is_correct = True
            else:
                with connection.cursor() as cursor:
                    cursor.execute(self.query)
                    self.is_correct = True
                    self.rows = cursor.rowcount
            
        except OperationalError as e:
            self.is_correct = False
            self.error_log = str(e)

        if self._state.adding:
            self.created_at = timezone.now()

        self.updated_at = timezone.now()

        super().save(*args, **kwargs)

class TaskStatus(models.Model):
    task_id = models.CharField(max_length=255, unique=True)
    is_completed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

class ExportDB(models.Model):
    export_to = models.ForeignKey(ExternalDatabase, on_delete=models.CASCADE, related_name="export_db")
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Export Database'
        verbose_name_plural = 'Export Databases'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self._state.adding:
            self.created_at = timezone.now()

        self.updated_at = timezone.now()

        export_data_to_external_db(self.pk)


class ExportLog(models.Model):
    model_name = models.CharField(max_length=255)
    count_b_copy = models.CharField(max_length=50, null=True, blank=True, verbose_name="Count before copy")
    count_a_copy = models.CharField(max_length=50, null=True, blank=True, verbose_name="Count after copy")
    success = models.BooleanField(default=False)
    error_log = models.TextField(null=True, blank=True)
    start_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.model_name

@background(schedule=0)
def export_data_to_external_db(pk):
    print("Starting to copy data...")
    export_to = ExportDB.objects.get(pk=pk)
    db = export_to.export_to
    all_models = apps.get_models()
    excluded_models = [ExportDB, LogEntry]

    def get_batch(queryset, start, end):
        return list(queryset[start:end])

    def copy_model_data(model):
        if model._meta.managed and model not in excluded_models:
            database_connection(db)
            try:
                source_count = model.objects.using('default').count()
                export_log = ExportLog.objects.create(
                    model_name=model._meta.model_name,
                    count_b_copy=source_count,
                    start_at=timezone.now()
                )
                SUCCESS = True
                for start in range(0, source_count, BATCH_SIZE):
                    end = min(start + BATCH_SIZE, source_count)
                    batch = get_batch(model.objects.using('default').all(), start, end)
                    for instance in batch:
                        try:
                            # Check if a record with the same primary key already exists
                            if model.objects.using(db.db_name).filter(pk=instance.pk).exists():
                                continue

                            # Check for unique constraints
                            unique_fields = [field for field in model._meta.fields if field.unique]
                            duplicate_found = False
                            for field in unique_fields:
                                field_value = getattr(instance, field.name)
                                if model.objects.using(db.db_name).filter(**{field.name: field_value}).exists():
                                    duplicate_found = True
                                    break

                            if duplicate_found:
                                continue

                            # Save related objects if necessary
                            for related_field in instance._meta.get_fields():
                                if related_field.is_relation and related_field.many_to_one:
                                    related_object = getattr(instance, related_field.name)
                                    if related_object:
                                        related_model = related_field.related_model
                                        if not related_model.objects.using(db.db_name).filter(pk=related_object.pk).exists():
                                            related_object.save(using=db.db_name)

                            instance.save(using=db.db_name)
                            export_log.count_a_copy = model.objects.using(db.db_name).count()
                            export_log.success = True
                            export_log.finished_at = timezone.now()
                            export_log.save()

                        except IntegrityError as e:
                            SUCCESS = False
                            print(f"IntegrityError copying data for model {model._meta.model_name} and instance {instance.pk}: {e}")
                            # export_log.error_log = f"IntegrityError copying data for model {model._meta.model_name} and instance {instance.pk}: {e}\n"
                        except Exception as e:
                            SUCCESS = False
                            print(f"Error copying data for model {model._meta.model_name} and instance {instance.pk}: {e}")
                            # export_log.error_log = f"Error copying data for model {model._meta.model_name} and instance {instance.pk}: {e}\n"

                    print(f"Copied batch of {len(batch)} rows for model {model._meta.model_name}")

                export_log.count_a_copy = model.objects.using(db.db_name).count()
                export_log.success = SUCCESS
                export_log.finished_at = timezone.now()
                export_log.save()

                print(f"Copied {export_log.count_a_copy} rows for model {model._meta.model_name}")

            except Exception as e:
                print(f"Error copying data for model {model._meta.model_name}: {e}")
                # export_log.error_log += f"Error copying data for model {model._meta.model_name}: {e}\n"
                export_log.save()

    # try:
    #     with transaction.atomic(using='default'), \
    #          concurrent.futures.ThreadPoolExecutor() as executor:
    #         executor.map(copy_model_data, all_models)

    #     print("Data copying completed successfully!")
    try:
        with transaction.atomic(using='default'):
            for model in all_models:
                copy_model_data(model)

        print("Data copying completed successfully!")
    except Exception as e:
        print(f"Data copying failed: {e}")

class Application(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    invoice_code = models.CharField(max_length=100)
    quantity = models.IntegerField(default=1)
    license_type = models.CharField(max_length=255, null=True, blank=True)
    license_method = models.CharField(max_length=255, null=True, blank=True)
    owner = models.CharField(max_length=255, null=True, blank=True)
    administrator = models.CharField(max_length=255, null=True, blank=True)

    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    updated_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    version_control = models.IntegerField(default=1, editable=False)

    date_fields_to_convert = []
    integer_fields = ['quantity', ]                                                                                                                                                                                          
    float_fields = []

    def __str__(self):
        return self.name

    @property
    def is_parent(self):
        return self.application_set.exists()

# Change per install
#pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe" 

class Image(models.Model):
    image = models.ImageField(upload_to='uploaded_images/')
    extracted_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    date_fields_to_convert = []
    integer_fields = []                                                                                                                                                                                          
    float_fields = []
    encrypted_fields = []

    def save(self, *args, **kwargs):
        if self.image:
            image = PILImage.open(self.image)
            raw_text = pytesseract.image_to_string(image)
            self.extracted_text = ', '.join(raw_text.split())
        super().save(*args, **kwargs)


class ImageLoader(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = QuillField(null=True, blank=True)
    recommendation = QuillField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)
    images = models.ManyToManyField(Image, blank=True)

    action_status = models.CharField(max_length=50, choices=ActionStatus.choices, default=ActionStatus.IS_ACTIVE)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    updated_by = models.CharField(max_length=255, null=True, blank=True)
    deleted_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    version_control = models.IntegerField(default=1, editable=False)

    date_fields_to_convert = []
    integer_fields = []                                                                                                                                                                                          
    float_fields = []
    encrypted_fields = []

    @property
    def is_parent(self):
        return self.imageloader_set.exists()
    
class SelectedRows(models.Model):
    model = models.CharField(max_length=255)
    model_choice = models.CharField(max_length=255, choices=ModelChoices.choices)
    rows = models.TextField()
    favorite_id = models.TextField(null=True, blank=True)
    finding_id = models.TextField(null=True, blank=True)
    img_loader_id = models.TextField(null=True, blank=True)
    unique_id = models.TextField(null=True, blank=True)
    tab_id = models.TextField(null=True, blank=True)


class UnifiedAccessManagement(models.Model):
    ID = models.AutoField(primary_key=True)
    User_Department = models.TextField(null=True, blank=True, verbose_name='User_Department', db_column='User_Department')
    AD_Account = models.TextField(null=True, blank=True, verbose_name='AD_Account', db_column='AD_Account')
    HR_Status = models.TextField(null=True, blank=True, verbose_name='HR_Status', db_column='HR_Status')
    AD_Status = models.TextField(null=True, blank=True, verbose_name='AD_Status', db_column='AD_Status')
    OU = models.TextField(null=True, blank=True, verbose_name='OU', db_column='OU')
    Employment_Status = models.TextField(null=True, blank=True, verbose_name='Employment_Status', db_column='Employment_Status')
    EMail = models.TextField(null=True, blank=True, verbose_name='EMail', db_column='EMail')
    Company_Laptop_Hardware_User = models.TextField(null=True, blank=True, verbose_name='Company_Laptop_Hardware_User', db_column='Company_Laptop_Hardware_User')
    VPN_Status = models.TextField(null=True, blank=True, verbose_name='VPN_Status', db_column='VPN_Status')
    VPN_Last_Used = models.BigIntegerField(null=True, blank=True, verbose_name='VPN_Last_Used', db_column='VPN_Last_Used')
    Servicenow_Status = models.TextField(null=True, blank=True, verbose_name='Servicenow_Status', db_column='Servicenow_Status')
    Servicenow_Last_Used = models.BigIntegerField(null=True, blank=True, verbose_name='Servicenow_Last_Used', db_column='Servicenow_Last_Used')
    SAP_Status = models.TextField(null=True, blank=True, verbose_name='SAP_Status', db_column='SAP_Status')
    SAP_Last_Used = models.BigIntegerField(null=True, blank=True, verbose_name='SAP_Last_Used', db_column='SAP_Last_Used')
    Financial_system_Status = models.TextField(null=True, blank=True, verbose_name='Financial_system_Status', db_column='Financial_system_Status')
    Financial_system_Last_Used = models.BigIntegerField(null=True, blank=True, verbose_name='Financial_system_Last_Used', db_column='Financial_system_Last_Used')
    SPLUNK_Status = models.TextField(null=True, blank=True, verbose_name='SPLUNK_Status', db_column='SPLUNK_Status')
    SPLUNK_Last_Used = models.BigIntegerField(null=True, blank=True, verbose_name='SPLUNK_Last_Used', db_column='SPLUNK_Last_Used')
    HR_Last_Used = models.BigIntegerField(null=True, blank=True, verbose_name='HR_Last_Used', db_column='HR_Last_Used')
    Payroll_Status = models.TextField(null=True, blank=True, verbose_name='Payroll_Status', db_column='Payroll_Status')
    Payroll_Last_Used = models.BigIntegerField(null=True, blank=True, verbose_name='Payroll_Last_Used', db_column='Payroll_Last_Used')
    Risk_Score = models.TextField(null=True, blank=True, verbose_name='Risk_Score', db_column='Risk_Score')
    loader_instance = models.IntegerField(null=True, blank=True)
    json_data = models.JSONField(null=True, blank=True)
    hash_data = VectorField(dimensions=1024, null=True, blank=True)
    fts = SearchVectorField(null=True, blank=True)

    date_fields_to_convert = ['VPN_Last_Used','Servicenow_Last_Used','SAP_Last_Used','Financial_system_Last_Used','SPLUNK_Last_Used','HR_Last_Used','Payroll_Last_Used',]
    integer_fields = []
    float_fields = []
    encrypted_fields = []
    unix_dates = []
    ad_unix_dates = []
    vector_model = 'BAAI/bge-large-en-v1.5'

class TicketLogging(models.Model):
    ID = models.AutoField(primary_key=True)
    Agent_Responded_Time = models.BigIntegerField(null=True, blank=True, verbose_name='Agent_Responded_Time', db_column='Agent_Responded_Time')
    Channel = models.TextField(null=True, blank=True, verbose_name='Channel', db_column='Channel')
    Created_Time_Ticket = models.BigIntegerField(null=True, blank=True, verbose_name='Created_Time_Ticket', db_column='Created_Time_Ticket')
    Customer_Responded_Time = models.BigIntegerField(null=True, blank=True, verbose_name='Customer_Responded_Time', db_column='Customer_Responded_Time')
    Email_Ticket = models.TextField(null=True, blank=True, verbose_name='Email_Ticket', db_column='Email_Ticket')
    First_Response_Time_in_Business_Hours = models.TextField(null=True, blank=True, verbose_name='First_Response_Time_in_Business_Hours', db_column='First_Response_Time_in_Business_Hours')
    Happiness_Rating = models.TextField(null=True, blank=True, verbose_name='Happiness_Rating', db_column='Happiness_Rating')
    Is_Archived = models.TextField(null=True, blank=True, verbose_name='Is_Archived', db_column='Is_Archived')
    Is_Escalated = models.TextField(null=True, blank=True, verbose_name='Is_Escalated', db_column='Is_Escalated')
    Is_Overdue = models.TextField(null=True, blank=True, verbose_name='Is_Overdue', db_column='Is_Overdue')
    Language = models.TextField(null=True, blank=True, verbose_name='Language', db_column='Language')
    Modified_By_Ticket = models.BigIntegerField(null=True, blank=True, verbose_name='Modified_By_Ticket', db_column='Modified_By_Ticket')
    Modified_Time_Ticket = models.TextField(null=True, blank=True, verbose_name='Modified_Time_Ticket', db_column='Modified_Time_Ticket')
    Number_of_Comments = models.TextField(null=True, blank=True, verbose_name='Number_of_Comments', db_column='Number_of_Comments')
    Number_of_Outgoing = models.TextField(null=True, blank=True, verbose_name='Number_of_Outgoing', db_column='Number_of_Outgoing')
    Number_of_Reassign = models.TextField(null=True, blank=True, verbose_name='Number_of_Reassign', db_column='Number_of_Reassign')
    Number_of_Reopen = models.TextField(null=True, blank=True, verbose_name='Number_of_Reopen', db_column='Number_of_Reopen')
    Number_of_Responses = models.TextField(null=True, blank=True, verbose_name='Number_of_Responses', db_column='Number_of_Responses')
    Number_of_Threads = models.TextField(null=True, blank=True, verbose_name='Number_of_Threads', db_column='Number_of_Threads')
    Phone_Ticket = models.TextField(null=True, blank=True, verbose_name='Phone_Ticket', db_column='Phone_Ticket')
    Priority_Ticket = models.TextField(null=True, blank=True, verbose_name='Priority_Ticket', db_column='Priority_Ticket')
    Resolution_Time_in_Business_Hours = models.TextField(null=True, blank=True, verbose_name='Resolution_Time_in_Business_Hours', db_column='Resolution_Time_in_Business_Hours')
    SLA_Violation_Type = models.TextField(null=True, blank=True, verbose_name='SLA_Violation_Type', db_column='SLA_Violation_Type')
    Status_Ticket = models.TextField(null=True, blank=True, verbose_name='Status_Ticket', db_column='Status_Ticket')
    Subject = models.TextField(null=True, blank=True, verbose_name='Subject', db_column='Subject')
    Ticket_Age = models.TextField(null=True, blank=True, verbose_name='Ticket_Age', db_column='Ticket_Age')
    Ticket_Closed_Time = models.BigIntegerField(null=True, blank=True, verbose_name='Ticket_Closed_Time', db_column='Ticket_Closed_Time')
    Ticket_Id = models.TextField(null=True, blank=True, verbose_name='Ticket_Id', db_column='Ticket_Id')
    Ticket_Owner = models.TextField(null=True, blank=True, verbose_name='Ticket_Owner', db_column='Ticket_Owner')
    To_Address = models.TextField(null=True, blank=True, verbose_name='To_Address', db_column='To_Address')
    Total_Response_Time_in_Business_Hours = models.TextField(null=True, blank=True, verbose_name='Total_Response_Time_in_Business_Hours', db_column='Total_Response_Time_in_Business_Hours')
    Total_Time_Spent = models.TextField(null=True, blank=True, verbose_name='Total_Time_Spent', db_column='Total_Time_Spent')
    Account_Name = models.TextField(null=True, blank=True, verbose_name='Account_Name', db_column='Account_Name')
    Layout_Account = models.TextField(null=True, blank=True, verbose_name='Layout_Account', db_column='Layout_Account')
    loader_instance = models.IntegerField(null=True, blank=True)
    json_data = models.JSONField(null=True, blank=True)
    hash_data = VectorField(dimensions=1024, null=True, blank=True)
    fts = SearchVectorField(null=True, blank=True)

    date_fields_to_convert = ['Agent_Responded_Time', 'Created_Time_Ticket', 'Customer_Responded_Time', 'Modified_By_Ticket', 'Ticket_Closed_Time']
    integer_fields = []
    float_fields = []
    encrypted_fields = []
    unix_dates = []
    ad_unix_dates = []
    vector_model = 'BAAI/bge-large-en-v1.5'


class HRUserList(models.Model):
    ID = models.AutoField(primary_key=True)
    First_Name = models.TextField(null=True, blank=True, verbose_name='First_Name', db_column='First_Name')
    Last_Name = models.TextField(null=True, blank=True, verbose_name='Last_Name', db_column='Last_Name')
    Job_Title = models.TextField(null=True, blank=True, verbose_name='Job_Title', db_column='Job_Title')
    Business_Unit = models.TextField(null=True, blank=True, verbose_name='Business_Unit', db_column='Business_Unit')
    Department = models.TextField(null=True, blank=True, verbose_name='Department', db_column='Department')
    Join_Date = models.BigIntegerField(null=True, blank=True, verbose_name='Join_Date', db_column='Join_Date')
    Employee_status = models.TextField(null=True, blank=True, verbose_name='Employee_status', db_column='Employee_status')
    Termination_Date = models.BigIntegerField(null=True, blank=True, verbose_name='Termination_Date', db_column='Termination_Date')
    loader_instance = models.IntegerField(null=True, blank=True)
    json_data = models.JSONField(null=True, blank=True)
    hash_data = VectorField(dimensions=1024, null=True, blank=True)
    fts = SearchVectorField(null=True, blank=True)

    date_fields_to_convert = ['Join_Date', 'Termination_Date']
    integer_fields = []
    float_fields = []
    encrypted_fields = []
    unix_dates = []
    ad_unix_dates = []
    vector_model = 'BAAI/bge-large-en-v1.5'


class ChangeRequests(models.Model):
    ID = models.AutoField(primary_key=True)
    number = models.TextField(null=True, blank=True, verbose_name='number', db_column='number')
    short_description = models.TextField(null=True, blank=True, verbose_name='short_description', db_column='short_description')
    state = models.TextField(null=True, blank=True, verbose_name='state', db_column='state')
    start_date = models.BigIntegerField(null=True, blank=True, verbose_name='start_date', db_column='start_date')
    end_date = models.BigIntegerField(null=True, blank=True, verbose_name='end_date', db_column='end_date')
    assigned_to = models.TextField(null=True, blank=True, verbose_name='assigned_to', db_column='assigned_to')
    loader_instance = models.IntegerField(null=True, blank=True)
    json_data = models.JSONField(null=True, blank=True)
    hash_data = VectorField(dimensions=1024, null=True, blank=True)
    fts = SearchVectorField(null=True, blank=True)

    date_fields_to_convert = ['start_date', 'end_date']
    integer_fields = []
    float_fields = []
    encrypted_fields = []
    unix_dates = []
    ad_unix_dates = []
    vector_model = 'BAAI/bge-large-en-v1.5'


class ControlADUser(models.Model):
    ID = models.AutoField(primary_key=True)
    DataAge = models.BigIntegerField(null=True, blank=True, verbose_name='DataAge', db_column='DataAge')
    SAMAccountName = models.TextField(null=True, blank=True, verbose_name='SAMAccountName', db_column='SAMAccountName')
    Surname = models.TextField(null=True, blank=True, verbose_name='Surname', db_column='Surname')
    Firtnames = models.TextField(null=True, blank=True, verbose_name='Firtnames', db_column='Firtnames')
    Displayname = models.TextField(null=True, blank=True, verbose_name='Displayname', db_column='Displayname')
    EmailAddress = models.TextField(null=True, blank=True, verbose_name='EmailAddress', db_column='EmailAddress')
    JobTitle = models.TextField(null=True, blank=True, verbose_name='JobTitle', db_column='JobTitle')
    employeeID = models.TextField(null=True, blank=True, verbose_name='employeeID', db_column='employeeID')
    AD_Enabled_Status = models.TextField(null=True, blank=True, verbose_name='AD_Enabled_Status', db_column='AD_Enabled_Status')
    company = models.TextField(null=True, blank=True, verbose_name='company', db_column='company')
    Department = models.TextField(null=True, blank=True, verbose_name='Department', db_column='Department')
    AD_Account_Created = models.BigIntegerField(null=True, blank=True, verbose_name='AD_Account_Created', db_column='AD_Account_Created')
    AD_Account_Created_days_back = models.IntegerField(null=True, blank=True, verbose_name='AD_Account_Created_days_back', db_column='AD_Account_Created_days_back')
    Account_age_in_years = models.IntegerField(null=True, blank=True, verbose_name='Account_age_in_years', db_column='Account_age_in_years')
    Password_Last_Set = models.BigIntegerField(null=True, blank=True, verbose_name='Password_Last_Set', db_column='Password_Last_Set')
    Password_Last_Set_days_back = models.IntegerField(null=True, blank=True, verbose_name='Password_Last_Set_days_back', db_column='Password_Last_Set_days_back')
    manager = models.TextField(null=True, blank=True, verbose_name='manager', db_column='manager')
    distinguishedName = models.TextField(null=True, blank=True, verbose_name='distinguishedName', db_column='distinguishedName')
    loader_instance = models.IntegerField(null=True, blank=True)
    json_data = models.JSONField(null=True, blank=True)
    hash_data = VectorField(dimensions=1024, null=True, blank=True)
    fts = SearchVectorField(null=True, blank=True)

    date_fields_to_convert = ['DataAge', 'AD_Account_Created', 'Password_Last_Set']
    integer_fields = ['AD_Account_Created_days_back', 'Account_age_in_years', 'Password_Last_Set_days_back']
    float_fields = []
    encrypted_fields = []
    unix_dates = []
    ad_unix_dates = []
    vector_model = 'BAAI/bge-large-en-v1.5'


class SAGEUserList(models.Model):
    ID = models.AutoField(primary_key=True)
    username = models.TextField(null=True, blank=True, verbose_name='username', db_column='username')
    email = models.TextField(null=True, blank=True, verbose_name='email', db_column='email')
    active = models.TextField(null=True, blank=True, verbose_name='active', db_column='active')
    loader_instance = models.IntegerField(null=True, blank=True)
    json_data = models.JSONField(null=True, blank=True)
    hash_data = VectorField(dimensions=1024, null=True, blank=True)
    fts = SearchVectorField(null=True, blank=True)

    date_fields_to_convert = []
    integer_fields = []
    float_fields = []
    encrypted_fields = []
    unix_dates = []
    ad_unix_dates = []
    vector_model = 'BAAI/bge-large-en-v1.5'
