from django.contrib import admin
from django.apps import apps
from guardian.admin import GuardedModelAdmin
from .models import *

# Register Courses with guardian for row level permissions
class CourseAdmin(GuardedModelAdmin):
    pass

admin.site.register(Course, CourseAdmin)

# Register everything else
app = apps.get_app_config('polls')
for model_name, model in app.models.items():
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered as e:
        continue
