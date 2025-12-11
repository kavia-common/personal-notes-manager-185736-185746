from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from .views import health, NotesViewSet, token_logout, register

router = DefaultRouter()
router.register(r'notes', NotesViewSet, basename='note')

urlpatterns = [
    path('health/', health, name='Health'),
    # Auth
    path('auth/token/login/', obtain_auth_token, name='token_login'),
    path('auth/token/logout/', token_logout, name='token_logout'),
    path('auth/register/', register, name='auth_register'),
    # Notes
    path('', include(router.urls)),
]
