from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers import UserSerializer
from core.permissions import IsAdmin
from .models import AccessRule
from .serializers import AccessRuleSerializer, AccessRuleWriteSerializer, UserRoleUpdateSerializer


class AccessRuleListCreateView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        summary='Список правил доступа',
        description='Возвращает все правила RBAC. Доступно только администратору.',
        responses=AccessRuleSerializer(many=True),
    )
    def get(self, request):
        rules = AccessRule.objects.select_related('role', 'element').all()
        return Response(AccessRuleSerializer(rules, many=True).data)

    @extend_schema(
        summary='Создать правило доступа',
        description='Создаёт новое правило для пары (роль, элемент). '
                    'Комбинация роль+элемент должна быть уникальной.',
        request=AccessRuleWriteSerializer,
        responses=AccessRuleSerializer,
    )
    def post(self, request):
        serializer = AccessRuleWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rule = serializer.save()
        return Response(AccessRuleSerializer(rule).data, status=status.HTTP_201_CREATED)


class AccessRuleDetailView(APIView):
    permission_classes = [IsAdmin]

    def _get_rule(self, pk):
        return get_object_or_404(AccessRule.objects.select_related('role', 'element'), pk=pk)

    @extend_schema(
        summary='Получить правило доступа',
        description='Возвращает одно правило RBAC по его ID.',
        responses=AccessRuleSerializer,
    )
    def get(self, request, pk):
        return Response(AccessRuleSerializer(self._get_rule(pk)).data)

    @extend_schema(
        summary='Обновить правило доступа',
        description='Частичное обновление булевых полей правила (read, create, update, delete и их _all варианты).',
        request=AccessRuleWriteSerializer,
        responses=AccessRuleSerializer,
    )
    def patch(self, request, pk):
        rule = self._get_rule(pk)
        serializer = AccessRuleWriteSerializer(rule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        rule = serializer.save()
        return Response(AccessRuleSerializer(rule).data)

    @extend_schema(
        summary='Удалить правило доступа',
        description='Полностью удаляет правило RBAC. После удаления роль теряет доступ к элементу.',
        responses=None,
    )
    def delete(self, request, pk):
        self._get_rule(pk)  # проверяем существование (404 если нет)
        AccessRule.objects.filter(pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserRoleUpdateView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        summary='Сменить роль пользователя',
        description='Назначает указанную роль пользователю по его ID. '
                    'Доступно только администратору.',
        request=UserRoleUpdateSerializer,
        responses=UserSerializer,
    )
    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = UserRoleUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(user).data)
