from django.contrib.auth.middleware import RemoteUserMiddleware

class UtorAuthMiddleware(RemoteUserMiddleware):
    header = 'HTTP_EPPN'
