from django.urls import path
from .views import RegisterView, LoginView, LogoutView, UserMeView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),

    path('me/', UserMeView.as_view(), name='user-me'),
]
