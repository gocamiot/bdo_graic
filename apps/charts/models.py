from django.db import models
from apps.tables.models import ModelChoices

# Create your models here.


class DateFilter(models.Model):
    userID = models.IntegerField()
    parent = models.CharField(max_length=255, choices=ModelChoices.choices)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)


class UserFilter(models.Model):
    userID = models.IntegerField()
    parent = models.CharField(max_length=255, choices=ModelChoices.choices)
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    status = models.BooleanField(default=False)