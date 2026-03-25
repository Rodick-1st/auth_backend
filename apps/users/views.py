from datetime import datetime, timezone

import bcrypt as _bcrypt
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import TokenExpiredError, TokenInvalidError, TokenBlacklistedError
from core.jwt_utils import generate_token, decode_token, blacklist_token, is_blacklisted
from .models import User
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, UserUpdateSerializer

tags = ["user"]


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=RegisterSerializer, responses=UserSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={
            '200': {
                'type': 'object',
                'properties': {
                    'access_token': {'type': 'string'},
                    'token_type': {'type': 'string'}
                                }
                 }
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'Неверные учётные данные'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'detail': 'Аккаунт деактивирован'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.password_hash or not _bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return Response({'detail': 'Неверные учётные данные'}, status=status.HTTP_401_UNAUTHORIZED)

        token = generate_token(user)
        return Response({'access_token': token, 'token_type': 'Bearer'}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=None,
        responses={'200': {'type': 'object', 'properties': {'detail': {'type': 'string'}}}},
        description='Передай токен в заголовке: Authorization: Bearer <token>',
    )
    def post(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return Response({'detail': 'Токен не предоставлен'}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header[len('Bearer '):]
        try:
            payload = decode_token(token)
        except TokenExpiredError:
            return Response({'detail': 'Токен истёк'}, status=status.HTTP_401_UNAUTHORIZED)
        except TokenInvalidError:
            return Response({'detail': 'Невалидный токен'}, status=status.HTTP_401_UNAUTHORIZED)

        jti = payload.get('jti')
        if is_blacklisted(jti):
            return Response({'detail': 'Токен уже инвалидирован'}, status=status.HTTP_401_UNAUTHORIZED)

        exp = payload.get('exp')
        expired_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        blacklist_token(jti, expired_at)

        return Response({'detail': 'Logged out successfully'}, status=status.HTTP_200_OK)


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer, tags=tags)
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(request=UserUpdateSerializer, responses=UserSerializer, tags=tags)
    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)

    @extend_schema(
        request=None,
        responses={'200': {'type': 'object', 'properties': {'detail': {'type': 'string'}}}},
        tags = tags
    )
    def delete(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[len('Bearer '):]
            try:
                payload = decode_token(token)
                jti = payload.get('jti')
                if not is_blacklisted(jti):
                    exp = payload.get('exp')
                    expired_at = datetime.fromtimestamp(exp, tz=timezone.utc)
                    blacklist_token(jti, expired_at)
            except (TokenExpiredError, TokenInvalidError):
                pass

        user = request.user
        user.is_active = False
        user.deleted_at = datetime.now(tz=timezone.utc)
        user.save(update_fields=['is_active', 'deleted_at'])

        return Response({'detail': 'Аккаунт деактивирован'}, status=status.HTTP_200_OK)
