from django import forms
from django.forms import IntegerField
from django.db.models import F
from django.contrib.admin import widgets
from django.core.exceptions import ValidationError

from .models import *

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


class QuizForm(forms.ModelForm):
    """ Simple model form for creating/editing quizzes"""
    class Meta:
        model = Quiz
        exclude = ['out_of','_cat_list', 'course']


class MarkedQuestionForm(forms.ModelForm):
    """ For creating marked questions.  Note that "choices" is handled
        differently to allow for quiz testing.
    """
#    category = IntegerField(min_value=1, initial=1)
#
#    problem_str = forms.CharField(widget=forms.Textarea(text_area_attrs))

    def clean_problem_str(self):
        """ Validate that the index variables occur in the correct order """
        problem_str = self.cleaned_data['problem_str']
        list_of_vars = re.findall(r'{v\[(\d+)\]}', problem_str)
        # Find the distinct indices, convert them to integers, and sort
        list_of_vars = list(set(list_of_vars))
        list_of_vars = [int(var_ind) for var_ind in list_of_vars]
        list_of_vars = sorted(list_of_vars)
        # Now we check whether they are sequential
        if all(a==b for a,b in enumerate(list_of_vars, list_of_vars[0])):
            return problem_str
        else:
            raise ValidationError(
                "Variables have non-sequential indices {}".format(list_of_vars)
            )



    class Meta:
        text_area_attrs = {'cols':'80', 'rows': '5'}
        mc_attrs = dict(text_area_attrs, **{'visible': 'false'})
        model = MarkedQuestion
        fields = ['category', 'problem_str', 'answer', 'q_type', 'mc_choices', 'functions']
        help_texts = {
            'problem_str': 'Use {v[0]}, {v[1]}, ... to indicate variables.',
            'category': 'Used to group several questions into the same category for randomization',
            'answer': 'Use the same variables as in problem. Use python calculate the answer.<br> For example, myfun({v[0]},{v[1]}).',
            'functions': 'Define custom functions using a dictionary. For example, {"myfun": lambda x,y: max(x,y)}.<br>'
                         'Your answer must contain all variables. The "gobble" function returns 1, and can be used as such.',
            'mc_choices': 'Enter a list with possible values, seperated by a semi-colon. For example, <code>None of the above; 15*{v[0]}; At most \(@2*{v[0]}@\)</code>. Any functions '
                          'you define can be used here, for example {"rand": lambda x: math.randint(1,10)}',
        }
        labels = {
            'problem_str': 'Problem',
            'category': 'Category',
        }
        widgets = {
            'problem_str': forms.Textarea(text_area_attrs),
            'answer': forms.Textarea(text_area_attrs),
            'functions': forms.Textarea(text_area_attrs),
            'mc_choices': forms.Textarea(mc_attrs),
        }
        field_classes = {
            'category': forms.IntegerField
        }
