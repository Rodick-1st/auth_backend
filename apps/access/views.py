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

    @extend_schema(responses=AccessRuleSerializer(many=True))
    def get(self, request):
        rules = AccessRule.objects.select_related('role', 'element').all()
        return Response(AccessRuleSerializer(rules, many=True).data)

    @extend_schema(request=AccessRuleWriteSerializer, responses=AccessRuleSerializer)
    def post(self, request):
        serializer = AccessRuleWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rule = serializer.save()
        return Response(AccessRuleSerializer(rule).data, status=status.HTTP_201_CREATED)


class AccessRuleDetailView(APIView):
    permission_classes = [IsAdmin]

    def _get_rule(self, pk):
        return get_object_or_404(AccessRule.objects.select_related('role', 'element'), pk=pk)

    @extend_schema(responses=AccessRuleSerializer)
    def get(self, request, pk):
        return Response(AccessRuleSerializer(self._get_rule(pk)).data)

    @extend_schema(request=AccessRuleWriteSerializer, responses=AccessRuleSerializer)
    def patch(self, request, pk):
        rule = self._get_rule(pk)
        serializer = AccessRuleWriteSerializer(rule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        rule = serializer.save()
        return Response(AccessRuleSerializer(rule).data)

    @extend_schema(responses=None)
    def delete(self, request, pk):
        self._get_rule(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserRoleUpdateView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(request=UserRoleUpdateSerializer, responses=UserSerializer)
    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = UserRoleUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(user).data)
