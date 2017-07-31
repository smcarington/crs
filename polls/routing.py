from channels import route
from . import consumers
from django.conf import settings

# Unlike URL's, we need the leading '/' for things to work. Make sure this is
# included
channel_routing = [
    route('websocket.connect',    
        consumers.admin_connect, 
        path=r'^/{}query_live/(?P<course_pk>\d+)/(?P<poll_pk>\d+)/$'.format(
            settings.URL_PREPEND)
        ),
    route('websocket.disconnect', 
        consumers.admin_disconnect, 
        path=r'^/{}query_live/(?P<course_pk>\d+)/(?P<poll_pk>\d+)/$'.format(
            settings.URL_PREPEND)
        ),
    route('websocket.receive', 
        consumers.admin_receive,
        path=r'^/{}query_live/(?P<course_pk>\d+)/(?P<poll_pk>\d+)/$'.format(
            settings.URL_PREPEND)
        ),
    route('websocket.connect',    
        consumers.voter_connect, 
        path=r'^/{}vote/(?P<course_pk>\d+)/$'.format(
            settings.URL_PREPEND)
        ),
    route('websocket.disconnect', 
        consumers.voter_disconnect, 
        path=r'^/{}vote/(?P<course_pk>\d+)/$'.format(
            settings.URL_PREPEND)
        ),
    route('websocket.receive', 
        consumers.voter_receive,
        path=r'^/{}vote/(?P<course_pk>\d+)/$'.format(
            settings.URL_PREPEND)
        ),
]
