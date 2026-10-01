from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from doctors.models import Doctor
from doctors.serializers import DoctorSerializer
from patients.models import Patient

from .models import Mapping
from .serializers import MappingCreateSerializer, MappingSerializer


class MappingListCreateView(generics.ListCreateAPIView):

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MappingCreateSerializer
        return MappingSerializer

    def get_queryset(self):
        return Mapping.objects.filter(
            patient__created_by=self.request.user
        ).select_related("patient", "doctor")

    def create(self, request, *args, **kwargs):
        serializer = MappingCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        mapping = serializer.save()
        return Response(
            MappingSerializer(mapping).data, status=status.HTTP_201_CREATED
        )


class MappingDetailView(APIView):

    def get(self, request, pk):
        if not Patient.objects.filter(id=pk, created_by=request.user).exists():
            return Response(
                {"error": "Patient not found."}, status=status.HTTP_404_NOT_FOUND
            )
        doctors = Doctor.objects.filter(mappings__patient_id=pk).distinct()
        return Response(DoctorSerializer(doctors, many=True).data)

    def delete(self, request, pk):
        mapping = Mapping.objects.filter(
            id=pk, patient__created_by=request.user
        ).first()
        if not mapping:
            return Response(
                {"error": "Mapping not found."}, status=status.HTTP_404_NOT_FOUND
            )
        mapping.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
