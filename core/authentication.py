from rest_framework.authentication import BaseAuthentication


class JWTMiddlewareAuthentication(BaseAuthentication):
    """
    Передаёт в DRF пользователя, уже установленного JWTAuthMiddleware.
    Сама аутентификацию не выполняет — только сообщает DRF о результате middleware.
    """

    def authenticate(self, request):
        user = request._request.user
        if user and user.is_authenticated:
            return (user, None)
        return None

    def authenticate_header(self, request):
        return 'Bearer'



