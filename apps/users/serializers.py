import bcrypt as _bcrypt
from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)
    password_confirm = serializers.CharField(min_length=6, write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    patronymic = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует')
        return value

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают'})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            patronymic=validated_data.get('patronymic', ''),
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'patronymic', 'role')


class UserUpdateSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(min_length=6, write_only=True, required=False)
    new_password_confirm = serializers.CharField(min_length=6, write_only=True, required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'patronymic', 'new_password', 'new_password_confirm')

    def validate(self, data):
        has_new = 'new_password' in data
        has_confirm = 'new_password_confirm' in data
        if has_new != has_confirm:
            raise serializers.ValidationError({'new_password_confirm': 'Необходимо передать оба поля для смены пароля'})
        if has_new and data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Пароли не совпадают'})
        return data

    def update(self, instance, validated_data):
        validated_data.pop('new_password_confirm', None)
        new_password = validated_data.pop('new_password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if new_password:
            instance.password_hash = _bcrypt.hashpw(
                new_password.encode('utf-8'), _bcrypt.gensalt()
            ).decode('utf-8')

        instance.save()
        return instance
