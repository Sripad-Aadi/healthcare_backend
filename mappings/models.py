from django.db import models

from doctors.models import Doctor
from patients.models import Patient


class Mapping(models.Model):
    """Assignment of a doctor to a patient."""

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="mappings"
    )
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="mappings"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("patient", "doctor")
        ordering = ["-assigned_at"]

    def __str__(self):
        return f"{self.patient.name} -> {self.doctor.name}"
