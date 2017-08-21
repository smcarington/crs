
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib.auth import (login, logout)
from django.contrib.auth.views import *
from django.contrib import admin

urlpatterns = [
    url(r'login/$',
        LoginView.as_view(
            template_name='registration/login.html',
            ), name='login'),
    url(r'^logout/$', 
        LogoutView.as_view(), {'next_page': '/courses/'}, name='logout'),
    url(r'^password_change/$',
        PasswordChangeView.as_view(
            template_name='registration/password_change.html',
            success_url='courses'), 
        name='password_change'
    ),
    url(r'^password_change/done/$', 
        PasswordChangeDoneView.as_view(
            template_name = 'registration/password_change_done.html',
        ), 
        name='password_change_done'
    ),
    url(r'^password/reset/$',
        PasswordResetView.as_view( 
            template_name = 'registration/password_reset.html',
            email_template_name = 'registration/password_reset_email.html'
         ),
        name='password_reset' 
    ),
    url(r'^password/reset/done/$',
        PasswordResetDoneView.as_view(
            template_name = 'registration/password_reset_done.html'
        ), 
        name='password_reset_done'
    ),
    url(r'^password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        PasswordResetConfirmView.as_view(
            template_name = 'registration/password_reset_confirm.html'
        ), 
        name='password_reset_confirm'
    ),
    url(r'^password/reset/complete/$',
        PasswordResetCompleteView.as_view(
            template_name = 'registration/password_reset_complete.html'
        ), 
        name='password_reset_complete'
    ),
]
