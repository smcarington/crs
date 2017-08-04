"""Mat237 URL Configuration
"""

from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib.auth import (login, logout)
from django.contrib.auth.views import *
from django.contrib import admin

url_prepend = settings.URL_PREPEND

urlpatterns = [
    url(r'^{prepend}superuser/'.format(prepend=url_prepend), admin.site.urls),
    url(r'^{prepend}accounts/login/$'.format(prepend=url_prepend),
        LoginView.as_view(), name='login'),
    url(r'^{prepend}accounts/logout/$'.format(prepend=url_prepend), 
        LogoutView.as_view(), {'next_page': '/courses/'}, name='logout'),
    url(r'^{prepend}accounts/password_change/$'.format(prepend=url_prepend),
        PasswordChangeView.as_view(
            template_name='registration/password_change.html',
            success_url='courses'), 
        name='password_change'
    ),
    url(r'^{prepend}accounts/password_change/done/$'.format(prepend=url_prepend), 
        PasswordChangeDoneView.as_view(
            template_name = 'registration/password_change_done.html',
        ), 
        name='password_change_done'
    ),
    url(r'^{prepend}accounts/password/reset/$'.format(prepend=url_prepend),
        PasswordResetView.as_view( 
            template_name = 'registration/password_reset.html',
            email_template_name = 'registration/password_reset_email.html'
         ),
        name='password_reset' 
    ),
    url(r'^{prepend}accounts/password/reset/done/$'.format(prepend=url_prepend),
        PasswordResetDoneView.as_view(
            template_name = 'registration/password_reset_done.html'
        ), 
        name='password_reset_done'
    ),
    url(r'^{prepend}accounts/password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$'.format(prepend=url_prepend),
        PasswordResetConfirmView.as_view(
            template_name = 'registration/password_reset_confirm.html'
        ), 
        name='password_reset_confirm'
    ),
    url(r'^{prepend}accounts/password/reset/complete/$'.format(prepend=url_prepend),
        PasswordResetCompleteView.as_view(
            template_name = 'registration/password_reset_complete.html'
        ), 
        name='password_reset_complete'
    ),
    url(r'^{prepend}'.format(prepend=url_prepend), include('polls.urls')),
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
