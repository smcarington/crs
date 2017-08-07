from django import forms
from django.db.models import F
from .models import *
from django.contrib.admin import widgets

class CourseForm(forms.ModelForm):
    """ Used for creating a course, with the option of adding an administrator
    """
    default_admin = forms.CharField(label='Administrator', max_length=8)
    class Meta:
        model = Course
        fields = ('name', 'open_enrollment',)
        help_texts = {
            'name': 'Insert Course Name',
            'default_admin': 'Specify an initial administrator',
        }

class StaffForm(forms.Form):
    """ Adds staff members, which could be administrators """

    course = forms.ModelChoiceField(queryset=None)
    username = forms.CharField(max_length=8)
    admin = forms.BooleanField(required=False)

    def __init__(self, queryset, *args, **kwargs):
        super(StaffForm, self).__init__(*args, **kwargs)
        self.fields['course'].queryset = queryset

class AddStudentsForm(forms.ModelForm):
    """ Used for adding students to a course"""

    course   = forms.ModelChoiceField(queryset=None)
    doc_file = forms.FileField()

    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('queryset')
        super(AddStudentsForm, self).__init__(*args, **kwargs)
        self.fields['course'].queryset = queryset

    class Meta:
        model = CSVFile
        fields = ('doc_file',)

class PollForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ('title',)
