from rest_framework import serializers

from apps.users.models import Role, User
from .models import BusinessElement, AccessRule

_PERMISSION_FIELDS = ('read', 'read_all', 'create', 'update', 'update_all', 'delete', 'delete_all')


class BusinessElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessElement
        fields = ('id', 'name', 'description')


class RoleShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name')


class AccessRuleSerializer(serializers.ModelSerializer):
    role = RoleShortSerializer(read_only=True)
    element = BusinessElementSerializer(read_only=True)

    class Meta:
        model = AccessRule
        fields = ('id', 'role', 'element') + _PERMISSION_FIELDS


class AccessRuleWriteSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())
    element = serializers.PrimaryKeyRelatedField(queryset=BusinessElement.objects.all())

    class Meta:
        model = AccessRule
        fields = ('id', 'role', 'element') + _PERMISSION_FIELDS

    def validate(self, data):
        role = data.get('role', getattr(self.instance, 'role', None))
        element = data.get('element', getattr(self.instance, 'element', None))
        qs = AccessRule.objects.filter(role=role, element=element)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Правило для этой роли и элемента уже существует')
        return data


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())

    class Meta:
        model = User
        fields = ('role',)
