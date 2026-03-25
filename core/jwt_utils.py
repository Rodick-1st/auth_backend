import uuid
from datetime import datetime, timezone, timedelta

import jwt
from django.apps import apps
from django.conf import settings

from core.exceptions import TokenExpiredError, TokenInvalidError


def generate_token(user) -> str:
    jti = str(uuid.uuid4())
    exp = datetime.now(tz=timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    payload = {
        'sub': str(user.id),
        'email': user.email,
        'jti': jti,
        'exp': exp,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError('Токен истёк')
    except jwt.InvalidTokenError:
        raise TokenInvalidError('Невалидный токен')


def blacklist_token(jti: str, expired_at: datetime) -> None:
    TokenBlacklist = apps.get_model('users', 'TokenBlacklist')
    TokenBlacklist.objects.create(jti=jti, expired_at=expired_at)


def is_blacklisted(jti: str) -> bool:
    TokenBlacklist = apps.get_model('users', 'TokenBlacklist')
    return TokenBlacklist.objects.filter(jti=jti).exists()
