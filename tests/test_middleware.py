import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from core.jwt_utils import blacklist_token, generate_token
from core.middleware import JWTAuthMiddleware
from tests.factories import UserFactory

from datetime import datetime, timezone, timedelta


def make_request(auth_header=None):
    factory = RequestFactory()
    request = factory.get('/')
    if auth_header:
        request.META['HTTP_AUTHORIZATION'] = auth_header
    return request


def get_user(request):
    middleware = JWTAuthMiddleware(get_response=lambda r: r)
    return middleware._get_user(request)


@pytest.mark.django_db
def test_valid_token_sets_user():
    user = UserFactory()
    token = generate_token(user)
    request = make_request(f'Bearer {token}')
    result = get_user(request)
    assert result == user


@pytest.mark.django_db
def test_no_auth_header_sets_anonymous():
    request = make_request()
    result = get_user(request)
    assert isinstance(result, AnonymousUser)


@pytest.mark.django_db
def test_malformed_token_sets_anonymous():
    request = make_request('Bearer not.valid.token')
    result = get_user(request)
    assert isinstance(result, AnonymousUser)


@pytest.mark.django_db
def test_blacklisted_token_sets_anonymous():
    user = UserFactory()
    token = generate_token(user)
    import jwt
    from django.conf import settings
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
    expired_at = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
    blacklist_token(payload['jti'], expired_at)

    request = make_request(f'Bearer {token}')
    result = get_user(request)
    assert isinstance(result, AnonymousUser)


@pytest.mark.django_db
def test_inactive_user_token_sets_anonymous():
    user = UserFactory(is_active=False)
    token = generate_token(user)
    request = make_request(f'Bearer {token}')
    result = get_user(request)
    assert isinstance(result, AnonymousUser)
