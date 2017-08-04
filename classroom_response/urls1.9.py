"""Mat237 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
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
        {'template_name': 'registration/login.html'},  name='login'),
    url(r'^{prepend}accounts/logout/$'.format(prepend=url_prepend), logout, {'next_page': '/'}, name='logout'),
    url(r'^{prepend}accounts/password_change/$'.format(prepend=url_prepend),
        password_change, {'template_name': 'registration/password_change.html', 'post_change_redirect': 'announcements'}, name='password_change'),
    url(r'^{prepend}accounts/password_change/done/$'.format(prepend=url_prepend), password_change_done, name='password_change_done'),
    url(r'^{prepend}accounts/password/reset/$'.format(prepend=url_prepend),
        password_reset, 
        {'template_name': 'registration/password_reset.html',
         'email_template_name': 'registration/password_reset_email.html'}, 
        'password_reset' ),
    url(r'^{prepend}accounts/password/reset/done/$'.format(prepend=url_prepend),
        password_reset_done, {'template_name': 'registration/password_reset_done.html'}, name='password_reset_done'),
    url(r'^{prepend}accounts/password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$'.format(prepend=url_prepend),
        password_reset_confirm, {'template_name': 'registration/password_reset_confirm.html'}, name='password_reset_confirm'),
    url(r'^{prepend}accounts/password/reset/complete/$'.format(prepend=url_prepend),
        password_reset_complete, {'template_name': 'registration/password_reset_complete.html'}, name='password_reset_complete'),
    url(r'^{prepend}'.format(prepend=url_prepend), include('polls.urls')),
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
