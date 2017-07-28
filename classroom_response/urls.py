"""Mat237 URL Configuration
"""

from django.conf import settings
from django.conf.urls import url, include, patterns
from django.conf.urls.static import static
from django.contrib.auth.views import (login, logout, password_change,
    password_change_done, password_reset, password_reset_done,
    password_reset_confirm, password_reset_complete)
from django.contrib import admin

url_prepend = settings.URL_PREPEND

urlpatterns = [
    url(r'^{prepend}superuser/'.format(prepend=url_prepend), admin.site.urls),
    url(r'^{prepend}accounts/login/$'.format(prepend=url_prepend), login,
        {'template_name': 'register/login.html'},  name='login'),
    url(r'^{prepend}accounts/logout/$'.format(prepend=url_prepend), logout, {'next_page': '/'}, name='logout'),
    url(r'^{prepend}accounts/password_change/$'.format(prepend=url_prepend),
        password_change, {'template_name': 'register/password_change.html', 'post_change_redirect': 'announcements'}, name='password_change'),
    url(r'^{prepend}accounts/password_change/done/$'.format(prepend=url_prepend), password_change_done, name='password_change_done'),
    url(r'^{prepend}accounts/password/reset/$'.format(prepend=url_prepend),
        password_reset, 
        {'template_name': 'register/password_reset.html',
         'email_template_name': 'register/password_reset_email.html'}, 
        'password_reset' ),
    url(r'^{prepend}accounts/password/reset/done/$'.format(prepend=url_prepend),
        password_reset_done, {'template_name': 'register/password_reset_done.html'}, name='password_reset_done'),
    url(r'^{prepend}accounts/password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$'.format(prepend=url_prepend),
        password_reset_confirm, {'template_name': 'register/password_reset_confirm.html'}, name='password_reset_confirm'),
    url(r'^{prepend}accounts/password/reset/complete/$'.format(prepend=url_prepend),
        password_reset_complete, {'template_name': 'register/password_reset_complete.html'}, name='password_reset_complete'),
    url(r'^{prepend}'.format(prepend=url_prepend), include('polls.urls')),
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
