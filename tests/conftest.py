import pytest

from core.jwt_utils import generate_token
from tests.factories import AccessRuleFactory, BusinessElementFactory, RoleFactory, UserFactory


@pytest.fixture
def role_admin(db):
    return RoleFactory(name='admin')


@pytest.fixture
def role_user(db):
    return RoleFactory(name='user')


@pytest.fixture
def role_guest(db):
    return RoleFactory(name='guest')


@pytest.fixture
def admin_user(db, role_admin):
    return UserFactory(role=role_admin, is_staff=True)


@pytest.fixture
def regular_user(db, role_user):
    return UserFactory(role=role_user)


@pytest.fixture
def admin_token(admin_user):
    return generate_token(admin_user)


@pytest.fixture
def user_token(regular_user):
    return generate_token(regular_user)


@pytest.fixture
def auth_client(client):
    def _make(token):
        client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return client
    return _make


@pytest.fixture
def element_products(db):
    return BusinessElementFactory(name='products')


@pytest.fixture
def rule_user_can_read_products(db, role_user, element_products):
    return AccessRuleFactory(role=role_user, element=element_products, read=True)
