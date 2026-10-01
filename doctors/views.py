from rest_framework import viewsets

from .models import Doctor
from .serializers import DoctorSerializer


class DoctorViewSet(viewsets.ModelViewSet):
    """CRUD for doctors. All endpoints require authentication."""

    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
