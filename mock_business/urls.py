from django.urls import path

from .views import ProductsView, OrdersView, ShopsView

urlpatterns = [
    path('products/', ProductsView.as_view(), name='products'),
    path('orders/', OrdersView.as_view(), name='orders'),
    path('shops/', ShopsView.as_view(), name='shops'),
]
