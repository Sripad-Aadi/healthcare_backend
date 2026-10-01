from rest_framework import serializers

from .models import Doctor


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = [
            "id",
            "name",
            "specialization",
            "email",
            "phone_number",
            "years_of_experience",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
