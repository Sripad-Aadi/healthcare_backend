from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — register a new user (name, email, password)."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — body: {email, password} -> {access, refresh} JWT tokens."""

    permission_classes = [permissions.AllowAny]
