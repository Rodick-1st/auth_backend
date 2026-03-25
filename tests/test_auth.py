import pytest

from apps.users.models import TokenBlacklist, User
from core.jwt_utils import generate_token
from tests.factories import RoleFactory, UserFactory


REGISTER_URL = '/api/auth/register/'
LOGIN_URL = '/api/auth/login/'
LOGOUT_URL = '/api/auth/logout/'
ME_URL = '/api/auth/me/'

VALID_REGISTER_DATA = {
    'email': 'new@test.com',
    'password': 'secret123',
    'password_confirm': 'secret123',
    'first_name': 'Иван',
    'last_name': 'Иванов',
}


# --- Регистрация ---

@pytest.mark.django_db
def test_register_success(client):
    response = client.post(REGISTER_URL, VALID_REGISTER_DATA, content_type='application/json')
    assert response.status_code == 201
    assert User.objects.filter(email='new@test.com').exists()


@pytest.mark.django_db
def test_register_duplicate_email(client):
    UserFactory(email='new@test.com')
    response = client.post(REGISTER_URL, VALID_REGISTER_DATA, content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_register_password_mismatch(client):
    data = {**VALID_REGISTER_DATA, 'password_confirm': 'other'}
    response = client.post(REGISTER_URL, data, content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_register_missing_fields(client):
    response = client.post(REGISTER_URL, {'email': 'x@test.com'}, content_type='application/json')
    assert response.status_code == 400


# --- Логин ---

@pytest.mark.django_db
def test_login_success(client):
    UserFactory(email='login@test.com', password='pass123')
    response = client.post(LOGIN_URL, {'email': 'login@test.com', 'password': 'pass123'}, content_type='application/json')
    assert response.status_code == 200
    assert 'access_token' in response.json()


@pytest.mark.django_db
def test_login_wrong_password(client):
    UserFactory(email='login@test.com', password='pass123')
    response = client.post(LOGIN_URL, {'email': 'login@test.com', 'password': 'wrong'}, content_type='application/json')
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_nonexistent_email(client):
    response = client.post(LOGIN_URL, {'email': 'ghost@test.com', 'password': 'pass'}, content_type='application/json')
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_inactive_user(client):
    UserFactory(email='inactive@test.com', password='pass123', is_active=False)
    response = client.post(LOGIN_URL, {'email': 'inactive@test.com', 'password': 'pass123'}, content_type='application/json')
    assert response.status_code == 401


# --- Логаут ---

@pytest.mark.django_db
def test_logout_success(client):
    user = UserFactory()
    token = generate_token(user)
    response = client.post(LOGOUT_URL, HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 200
    assert TokenBlacklist.objects.count() == 1


@pytest.mark.django_db
def test_logout_already_blacklisted(client):
    user = UserFactory()
    token = generate_token(user)
    client.post(LOGOUT_URL, HTTP_AUTHORIZATION=f'Bearer {token}')
    response = client.post(LOGOUT_URL, HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 401


@pytest.mark.django_db
def test_logout_no_token(client):
    response = client.post(LOGOUT_URL)
    assert response.status_code == 401


@pytest.mark.django_db
def test_logout_invalid_token(client):
    response = client.post(LOGOUT_URL, HTTP_AUTHORIZATION='Bearer not.a.token')
    assert response.status_code == 401


# --- /me ---

@pytest.mark.django_db
def test_me_get_authenticated(client):
    user = UserFactory(email='me@test.com')
    token = generate_token(user)
    response = client.get(ME_URL, HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 200
    assert response.json()['email'] == 'me@test.com'


@pytest.mark.django_db
def test_me_get_unauthenticated(client):
    response = client.get(ME_URL)
    assert response.status_code == 401


@pytest.mark.django_db
def test_me_patch_update_name(client):
    user = UserFactory()
    token = generate_token(user)
    response = client.patch(ME_URL, {'first_name': 'Новое'}, content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.first_name == 'Новое'


@pytest.mark.django_db
def test_me_patch_change_password(client):
    UserFactory(email='pw@test.com', password='oldpass')
    user = User.objects.get(email='pw@test.com')
    token = generate_token(user)
    client.patch(
        ME_URL,
        {'new_password': 'newpass123', 'new_password_confirm': 'newpass123'},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    response = client.post(LOGIN_URL, {'email': 'pw@test.com', 'password': 'oldpass'}, content_type='application/json')
    assert response.status_code == 401


@pytest.mark.django_db
def test_me_delete_soft_delete(client):
    user = UserFactory()
    token = generate_token(user)
    response = client.delete(ME_URL, HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_active is False
    assert user.deleted_at is not None


@pytest.mark.django_db
def test_login_after_soft_delete(client):
    UserFactory(email='del@test.com', password='pass123', is_active=False)
    response = client.post(LOGIN_URL, {'email': 'del@test.com', 'password': 'pass123'}, content_type='application/json')
    assert response.status_code == 401
