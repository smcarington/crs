import os
import django
# Changed for channels 2.2
#import channels.asgi
from channels.routing import get_default_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "classroom_response.settings")
django.setup()
application = get_default_application()
#channel_layer = channels.asgi.get_channel_layer()
