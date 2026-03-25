from django.apps import apps
from django.contrib.auth.models import AnonymousUser

from core.exceptions import TokenExpiredError, TokenInvalidError
from core.jwt_utils import decode_token, is_blacklisted


class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user = self._get_user(request)
        return self.get_response(request)

    def _get_user(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return AnonymousUser()

        token = auth_header.removeprefix('Bearer ')
        try:
            payload = decode_token(token)
        except (TokenExpiredError, TokenInvalidError):
            return AnonymousUser()

        jti = payload.get('jti')
        if jti and is_blacklisted(jti):
            return AnonymousUser()

        User = apps.get_model('users', 'User')
        try:
            user = User.objects.get(id=int(payload['sub']))
            if not user.is_active:
                return AnonymousUser()
            return user
        except User.DoesNotExist:
            return AnonymousUser()
