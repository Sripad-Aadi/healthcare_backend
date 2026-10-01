"""Custom exception handler for consistent API error responses."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Keep DRF's default field-level validation errors (400), but normalize
    other errors (401/403/404/500) into a consistent {"error": ...} shape.
    """
    response = exception_handler(exc, context)
    if response is None:
        return None

    if response.status_code == status.HTTP_400_BAD_REQUEST:
        return response

    message = response.data
    if isinstance(response.data, dict) and "detail" in response.data:
        message = response.data["detail"]

    return Response({"error": message}, status=response.status_code)
