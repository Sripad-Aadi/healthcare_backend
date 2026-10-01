from rest_framework import serializers

from doctors.models import Doctor
from patients.models import Patient

from .models import Mapping


class MappingSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)
    doctor_specialization = serializers.CharField(
        source="doctor.specialization", read_only=True
    )

    class Meta:
        model = Mapping
        fields = [
            "id",
            "patient",
            "doctor",
            "patient_name",
            "doctor_name",
            "doctor_specialization",
            "assigned_at",
        ]
        read_only_fields = ["assigned_at"]


class MappingCreateSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()
    doctor_id = serializers.IntegerField()

    def validate(self, attrs):
        if not Patient.objects.filter(id=attrs["patient_id"]).exists():
            raise serializers.ValidationError({"patient_id": "Patient not found."})
        if not Doctor.objects.filter(id=attrs["doctor_id"]).exists():
            raise serializers.ValidationError({"doctor_id": "Doctor not found."})
        if Mapping.objects.filter(
            patient_id=attrs["patient_id"], doctor_id=attrs["doctor_id"]
        ).exists():
            raise serializers.ValidationError(
                "This doctor is already assigned to this patient."
            )
        return attrs

    def create(self, validated_data):
        return Mapping.objects.create(
            patient_id=validated_data["patient_id"],
            doctor_id=validated_data["doctor_id"],
        )
