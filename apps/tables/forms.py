from django import forms
from apps.tables.models import EmailActionStatus
from apps.common.forms import MultipleFileField
from django.contrib.auth import get_user_model
from django_quill.forms import QuillFormField

User = get_user_model()

class FindingForm(forms.Form):
    description = QuillFormField()
    recommendation = QuillFormField()

class TabNotesForm(forms.Form):
    notes = QuillFormField()

class RecommendationForm(forms.Form):
    audit_recommendation = QuillFormField()

class ActionForm(forms.Form):
    action_to = forms.MultipleChoiceField(
        choices=[], 
        required=False,
    )
    user_action_status = forms.ChoiceField(
        choices=EmailActionStatus.choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'shadow-sm bg-gray-50 border border-gray-300 text-gray-900 sm:text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
        })
    )

    def __init__(self, *args, action_to=True, action_status=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['action_to'].choices = [
            (email, email) for email in User.objects.exclude(email="").values_list('email', flat=True)
        ]
        if not action_status:
            self.fields.pop('user_action_status')
        
        if not action_to:
            self.fields.pop('action_to')

class ImageLoaderForm(forms.Form):
    files = MultipleFileField(label='Select files', required=False)
    description = QuillFormField()
    recommendation = QuillFormField()

    def __init__(self, *args, **kwargs):
        super(ImageLoaderForm, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            self.fields['files'].widget.attrs['class'] = 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400'
            self.fields['files'].widget.attrs['accept'] = 'image/*'
