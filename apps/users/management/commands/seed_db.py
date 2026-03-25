from django.core.management.base import BaseCommand

from apps.access.models import AccessRule, BusinessElement
from apps.users.models import Role, User

_ROLES = [
    {'name': 'admin', 'description': 'Администратор системы'},
    {'name': 'manager', 'description': 'Менеджер'},
    {'name': 'user', 'description': 'Пользователь'},
    {'name': 'guest', 'description': 'Гость'},
]

_ELEMENTS = [
    {'name': 'products', 'description': 'Товары'},
    {'name': 'orders', 'description': 'Заказы'},
    {'name': 'shops', 'description': 'Магазины'},
    {'name': 'users', 'description': 'Пользователи'},
    {'name': 'access_rules', 'description': 'Правила доступа'},
]

# (role_name, element_name): {поле: значение, ...}
_RULES = {
    # admin — всё разрешено на все элементы
    **{
        ('admin', el['name']): {
            'read': True, 'read_all': True, 'create': True,
            'update': True, 'update_all': True, 'delete': True, 'delete_all': True,
        }
        for el in _ELEMENTS
    },
    # manager
    ('manager', 'products'): {
        'read': True, 'read_all': True, 'create': True,
        'update': True, 'update_all': False, 'delete': False, 'delete_all': False,
    },
    ('manager', 'orders'): {
        'read': True, 'read_all': True, 'create': True,
        'update': True, 'update_all': False, 'delete': False, 'delete_all': False,
    },
    ('manager', 'shops'): {
        'read': True, 'read_all': True, 'create': False,
        'update': False, 'update_all': False, 'delete': False, 'delete_all': False,
    },
    ('manager', 'users'): {
        'read': True, 'read_all': False, 'create': False,
        'update': False, 'update_all': False, 'delete': False, 'delete_all': False,
    },
    ('manager', 'access_rules'): {
        'read': False, 'read_all': False, 'create': False,
        'update': False, 'update_all': False, 'delete': False, 'delete_all': False,
    },
    # user
    ('user', 'products'): {
        'read': True, 'read_all': False, 'create': False,
        'update': False, 'update_all': False, 'delete': False, 'delete_all': False,
    },
    ('user', 'orders'): {
        'read': True, 'read_all': False, 'create': True,
        'update': True, 'update_all': False, 'delete': False, 'delete_all': False,
    },
    ('user', 'shops'): {
        'read': True, 'read_all': False, 'create': False,
        'update': False, 'update_all': False, 'delete': False, 'delete_all': False,
    },
    ('user', 'users'): {
        'read': False, 'read_all': False, 'create': False,
        'update': False, 'update_all': False, 'delete': False, 'delete_all': False,
    },
    ('user', 'access_rules'): {
        'read': False, 'read_all': False, 'create': False,
        'update': False, 'update_all': False, 'delete': False, 'delete_all': False,
    },
    # guest
    ('guest', 'products'): {
        'read': True, 'read_all': False, 'create': False,
        'update': False, 'update_all': False, 'delete': False, 'delete_all': False,
    },
    ('guest', 'orders'): {
        'read': False, 'read_all': False, 'create': False,
        'update': False, 'update_all': False, 'delete': False, 'delete_all': False,
    },
    ('guest', 'shops'): {
        'read': True, 'read_all': False, 'create': False,
        'update': False, 'update_all': False, 'delete': False, 'delete_all': False,
    },
    ('guest', 'users'): {
        'read': False, 'read_all': False, 'create': False,
        'update': False, 'update_all': False, 'delete': False, 'delete_all': False,
    },
    ('guest', 'access_rules'): {
        'read': False, 'read_all': False, 'create': False,
        'update': False, 'update_all': False, 'delete': False, 'delete_all': False,
    },
}

_TEST_USERS = [
    {'email': 'admin@test.com', 'role': 'admin', 'first_name': 'Admin', 'last_name': 'System', 'is_staff': True},
    {'email': 'manager@test.com', 'role': 'manager', 'first_name': 'Иван', 'last_name': 'Менеджеров', 'is_staff': False},
    {'email': 'user@test.com', 'role': 'user', 'first_name': 'Пётр', 'last_name': 'Пользователев', 'is_staff': False},
    {'email': 'guest@test.com', 'role': 'guest', 'first_name': 'Анна', 'last_name': 'Гостева', 'is_staff': False},
]

_TEST_PASSWORD = 'test1234'


class Command(BaseCommand):
    help = 'Заполняет БД начальными данными: роли, элементы, правила доступа, тестовые пользователи'

    def handle(self, *args, **options):
        self._seed_roles()
        self._seed_elements()
        self._seed_rules()
        self._seed_users()
        self.stdout.write(self.style.SUCCESS('Seed завершён успешно'))

    def _seed_roles(self):
        for data in _ROLES:
            _, created = Role.objects.get_or_create(name=data['name'], defaults={'description': data['description']})
            status = 'создана' if created else 'уже существует'
            self.stdout.write(f'  Роль [{data["name"]}] — {status}')

    def _seed_elements(self):
        for data in _ELEMENTS:
            _, created = BusinessElement.objects.get_or_create(
                name=data['name'], defaults={'description': data['description']}
            )
            status = 'создан' if created else 'уже существует'
            self.stdout.write(f'  Элемент [{data["name"]}] — {status}')

    def _seed_rules(self):
        for (role_name, element_name), permissions in _RULES.items():
            role = Role.objects.get(name=role_name)
            element = BusinessElement.objects.get(name=element_name)
            _, created = AccessRule.objects.update_or_create(
                role=role, element=element, defaults=permissions
            )
            status = 'создано' if created else 'обновлено'
            self.stdout.write(f'  Правило [{role_name} → {element_name}] — {status}')

    def _seed_users(self):
        for data in _TEST_USERS:
            if User.objects.filter(email=data['email']).exists():
                self.stdout.write(f'  Пользователь [{data["email"]}] — уже существует')
                continue
            role = Role.objects.get(name=data['role'])
            User.objects.create_user(
                email=data['email'],
                password=_TEST_PASSWORD,
                first_name=data['first_name'],
                last_name=data['last_name'],
                role=role,
                is_staff=data['is_staff'],
                is_active=True,
            )
            self.stdout.write(f'  Пользователь [{data["email"]}] — создан')
