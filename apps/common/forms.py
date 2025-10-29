from django import forms
from apps.common.models import File

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs.update({'multiple': True})
        super().__init__(attrs)


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return [single_file_clean(data, initial)]


class FileForm(forms.ModelForm):
    files = MultipleFileField(label='Select files', required=False)
    class Meta:
        model = File
        exclude = ('file', 'status', 'created_by', 'updated_by', )

    def __init__(self, *args, **kwargs):
        super(FileForm, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            self.fields[field_name].widget.attrs['placeholder'] = field.label
            self.fields[field_name].widget.attrs['class'] = 'shadow-sm bg-gray-50 border border-gray-300 text-gray-900 sm:text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500'
            self.fields['files'].widget.attrs['class'] = 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400'