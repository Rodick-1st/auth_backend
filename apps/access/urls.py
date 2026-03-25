from django.urls import path

from .views import AccessRuleListCreateView, AccessRuleDetailView, UserRoleUpdateView

urlpatterns = [
    path('access-rules/', AccessRuleListCreateView.as_view(), name='access-rule-list'),
    path('access-rules/<int:pk>/', AccessRuleDetailView.as_view(), name='access-rule-detail'),
    path('users/<int:pk>/role/', UserRoleUpdateView.as_view(), name='user-role-update'),
]
