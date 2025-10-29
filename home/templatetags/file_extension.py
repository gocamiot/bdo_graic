from django import template
import os
import csv
from urllib.parse import quote

register = template.Library()

@register.filter
def file_extension(value):
    _, extension = os.path.splitext(value)
    return extension.lower()


@register.filter
def encoded_file_path(path):
    return path.replace('/', '%slash%')

@register.filter
def encoded_path(path):
    return path.replace('\\', '/')


@register.filter
def convert_csv_to_text(csv_file):
    decoded_file = csv_file.read().decode('utf-8').splitlines()
    csv_reader = csv.reader(decoded_file)
    headers = next(csv_reader)

    text = ''
    for row in csv_reader:
        text += ','.join(row) + '\n'

    return text

@register.filter(name='basename')
def basename(value):
    """Return the base name of the file from a full path."""
    return os.path.basename(value) if value else value