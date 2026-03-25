import pytest

from core.jwt_utils import generate_token
from tests.factories import (
    AccessRuleFactory, BusinessElementFactory, RoleFactory, UserFactory,
)

PRODUCTS_URL = '/api/products/'
ACCESS_RULES_URL = '/api/admin/access-rules/'
USER_ROLE_URL = '/api/admin/users/{}/role/'


# --- RBACPermission ---

@pytest.mark.django_db
def test_anonymous_gets_401(client):
    response = client.get(PRODUCTS_URL)
    assert response.status_code == 401


@pytest.mark.django_db
def test_no_access_rule_gets_403(client):
    role = RoleFactory(name='norule_role')
    user = UserFactory(role=role)
    token = generate_token(user)
    # Нет AccessRule для этой роли + products
    BusinessElementFactory(name='products')
    response = client.get(PRODUCTS_URL, HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 403


@pytest.mark.django_db
def test_read_false_gets_403(client):
    role = RoleFactory(name='readonly_false')
    user = UserFactory(role=role)
    token = generate_token(user)
    element = BusinessElementFactory(name='products')
    AccessRuleFactory(role=role, element=element, read=False)
    response = client.get(PRODUCTS_URL, HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 403


@pytest.mark.django_db
def test_read_true_gets_200(client):
    role = RoleFactory(name='can_read')
    user = UserFactory(role=role)
    token = generate_token(user)
    element = BusinessElementFactory(name='products')
    AccessRuleFactory(role=role, element=element, read=True)
    response = client.get(PRODUCTS_URL, HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 200


@pytest.mark.django_db
def test_role_without_rule_gets_403(client):
    role = RoleFactory(name='no_element_role')
    user = UserFactory(role=role)
    token = generate_token(user)
    # Элемент 'products' не создан вообще
    response = client.get(PRODUCTS_URL, HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 403


# --- IsAdmin / Admin API ---

@pytest.mark.django_db
def test_admin_can_list_access_rules(client):
    role = RoleFactory(name='admin')
    user = UserFactory(role=role, is_staff=True)
    token = generate_token(user)
    response = client.get(ACCESS_RULES_URL, HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 200


@pytest.mark.django_db
def test_non_admin_gets_403_on_admin_endpoint(client):
    role = RoleFactory(name='user')
    user = UserFactory(role=role)
    token = generate_token(user)
    response = client.get(ACCESS_RULES_URL, HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 403


@pytest.mark.django_db
def test_anonymous_gets_401_on_admin_endpoint(client):
    response = client.get(ACCESS_RULES_URL)
    assert response.status_code == 401


@pytest.mark.django_db
def test_admin_can_create_access_rule(client):
    role_admin = RoleFactory(name='admin')
    admin = UserFactory(role=role_admin, is_staff=True)
    token = generate_token(admin)

    role_target = RoleFactory(name='target')
    element = BusinessElementFactory(name='products')

    data = {'role': role_target.id, 'element': element.id, 'read': True}
    response = client.post(ACCESS_RULES_URL, data, content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 201


@pytest.mark.django_db
def test_admin_can_update_access_rule(client):
    role_admin = RoleFactory(name='admin')
    admin = UserFactory(role=role_admin, is_staff=True)
    token = generate_token(admin)

    rule = AccessRuleFactory(read=False)
    url = f'{ACCESS_RULES_URL}{rule.id}/'
    response = client.patch(url, {'read': True}, content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 200
    rule.refresh_from_db()
    assert rule.read is True


@pytest.mark.django_db
def test_admin_can_delete_access_rule(client):
    role_admin = RoleFactory(name='admin')
    admin = UserFactory(role=role_admin, is_staff=True)
    token = generate_token(admin)

    rule = AccessRuleFactory()
    url = f'{ACCESS_RULES_URL}{rule.id}/'
    response = client.delete(url, HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 204


@pytest.mark.django_db
def test_admin_can_change_user_role(client):
    role_admin = RoleFactory(name='admin')
    admin = UserFactory(role=role_admin, is_staff=True)
    token = generate_token(admin)

    role_new = RoleFactory(name='manager')
    target_user = UserFactory()
    url = USER_ROLE_URL.format(target_user.id)

    response = client.patch(url, {'role': role_new.id}, content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 200
    target_user.refresh_from_db()
    assert target_user.role == role_new


@pytest.mark.django_db
def test_non_admin_cannot_change_user_role(client):
    role_user = RoleFactory(name='user')
    user = UserFactory(role=role_user)
    token = generate_token(user)

    role_new = RoleFactory(name='manager')
    target = UserFactory()
    url = USER_ROLE_URL.format(target.id)

    response = client.patch(url, {'role': role_new.id}, content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token}')
    assert response.status_code == 403
