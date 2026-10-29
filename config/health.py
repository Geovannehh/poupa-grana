"""Readiness probe with a minimal, non-cacheable response."""
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_safe


@require_safe
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            healthy = cursor.fetchone() == (1,)
    except DatabaseError:
        healthy = False
    response = JsonResponse({"status": "ok" if healthy else "unavailable"},
                            status=200 if healthy else 503)
    response["Cache-Control"] = "no-store"
    return response
