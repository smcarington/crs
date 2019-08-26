from channels.routing import ProtocolTypeRouter
from . import consumers
from django.urls import path
from django.conf import settings

websocket_urlpatterns = [
    path(f'{settings.URL_PREPEND}vote/<int:course_pk>/',
        consumers.PollVoteConsumer
    ),
    path(f'{settings.URL_PREPEND}query_live/<int:course_pk>/<int:poll_pk>/',
        consumers.PollAdminConsumer
    ),
]

#channel_routing = [
#    route('websocket.connect',    
#        consumers.admin_connect, 
#        path=r'^/{}query_live/(?P<course_pk>\d+)/(?P<poll_pk>\d+)/$'.format(
#            settings.WS_PREPEND)
#        ),
#    route('websocket.disconnect', 
#        consumers.admin_disconnect, 
#        path=r'^/{}query_live/(?P<course_pk>\d+)/(?P<poll_pk>\d+)/$'.format(
#            settings.WS_PREPEND)
#        ),
#    route('websocket.receive', 
#        consumers.admin_receive,
#        path=r'^/{}query_live/(?P<course_pk>\d+)/(?P<poll_pk>\d+)/$'.format(
#            settings.WS_PREPEND)
#        ),
#    route('websocket.connect',    
#        consumers.voter_connect, 
#        path=r'^/{}vote/(?P<course_pk>\d+)/$'.format(
#            settings.WS_PREPEND)
#        ),
#    route('websocket.disconnect', 
#        consumers.voter_disconnect, 
#        path=r'^/{}vote/(?P<course_pk>\d+)/$'.format(
#            settings.WS_PREPEND)
#        ),
#    route('websocket.receive', 
#        consumers.voter_receive,
#        path=r'^/{}vote/(?P<course_pk>\d+)/$'.format(
#            settings.WS_PREPEND)
#        ),
#]
