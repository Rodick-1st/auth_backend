from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import RBACPermission


class ProductsView(APIView):
    permission_classes = [RBACPermission]
    rbac_element = 'products'

    @extend_schema(
        summary='Список товаров',
        description='Возвращает каталог товаров. Требует право read на элемент products.',
        responses={'200': {'type': 'array', 'items': {'type': 'object'}}},
    )
    def get(self, request):
        return Response([
            {'id': 1, 'name': 'Ноутбук', 'price': 75000},
            {'id': 2, 'name': 'Мышь', 'price': 1500},
            {'id': 3, 'name': 'Клавиатура', 'price': 3500},
        ])


class OrdersView(APIView):
    permission_classes = [RBACPermission]
    rbac_element = 'orders'

    @extend_schema(
        summary='Список заказов',
        description='Возвращает список заказов. Требует право read на элемент orders. '
                    'Пользователи с read_all видят все заказы, с read — только свои.',
        responses={'200': {'type': 'array', 'items': {'type': 'object'}}},
    )
    def get(self, request):
        return Response([
            {'id': 1, 'product': 'Ноутбук', 'user_id': 1, 'status': 'pending'},
            {'id': 2, 'product': 'Мышь', 'user_id': 2, 'status': 'delivered'},
        ])


class ShopsView(APIView):
    permission_classes = [RBACPermission]
    rbac_element = 'shops'

    @extend_schema(
        summary='Список магазинов',
        description='Возвращает список магазинов и складов. Требует право read на элемент shops.',
        responses={'200': {'type': 'array', 'items': {'type': 'object'}}},
    )
    def get(self, request):
        return Response([
            {'id': 1, 'name': 'Главный склад', 'city': 'Москва'},
            {'id': 2, 'name': 'Филиал Север', 'city': 'Санкт-Петербург'},
        ])
