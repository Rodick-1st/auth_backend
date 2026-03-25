import factory

from apps.access.models import AccessRule, BusinessElement
from apps.users.models import Role, User


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f'role_{n}')
    description = ''


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@test.com')
    first_name = 'Test'
    last_name = 'User'
    is_active = True
    role = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop('password', 'testpass123')
        return model_class.objects.create_user(*args, password=password, **kwargs)


class BusinessElementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BusinessElement
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f'element_{n}')
    description = ''


class AccessRuleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AccessRule

    role = factory.SubFactory(RoleFactory)
    element = factory.SubFactory(BusinessElementFactory)
    read = False
    read_all = False
    # 'create' намеренно не объявляем — это зарезервированное имя classmethod в factory-boy.
    # Поле create модели имеет default=False, при необходимости передаётся явно через kwargs.
    update = False
    update_all = False
    delete = False
    delete_all = False
