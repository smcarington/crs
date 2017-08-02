from django import forms
from django.db.models import F
from .models import *
from django.contrib.admin import widgets

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        help_texts = {
            'name': 'Insert Course Name',
        }


