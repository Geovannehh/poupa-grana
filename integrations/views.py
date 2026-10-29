import base64
import binascii
import secrets
import uuid

from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from ledger.models import Entry
from ledger.services import scoped
from ledger.views import context
from workspaces.access import accessible_spaces

from .models import ExportCredential


@login_required
def settings(request):
    ctx = context(request)
    if request.method == "POST":
        secret = secrets.token_urlsafe(40)
        key = ExportCredential.objects.create(
            user=request.user, workspace=ctx["workspace"], secret_hash=make_password(secret)
        )
        ctx.update(new_key=key, new_secret=secret)
    ctx["credentials"] = ExportCredential.objects.filter(
        user=request.user, workspace=ctx["workspace"]
    )
    response = render(request, "integrations/settings.html", ctx)
    response["Cache-Control"] = "no-store"
    return response


@login_required
@require_POST
def revoke(request, key_id):
    key = get_object_or_404(ExportCredential, pk=key_id, user=request.user)
    key.active = False
    key.save(update_fields=["active"])
    return redirect("integrations")


def denied():
    response = JsonResponse({"error": "Credencial ausente, inválida ou sem acesso."}, status=401)
    response["WWW-Authenticate"] = 'Basic realm="Poupa Grana BI", charset="UTF-8"'
    response["Cache-Control"] = "no-store"
    return response


@require_GET
def export_entries(request):
    header = request.headers.get("Authorization", "")
    if len(header) > 1024 or not header.startswith("Basic "):
        return denied()
    try:
        identifier, secret = base64.b64decode(header[6:], validate=True).decode().split(":", 1)
        identifier = uuid.UUID(identifier)
    except (ValueError, UnicodeError, binascii.Error):
        return denied()
    key = (
        ExportCredential.objects.select_related("user", "workspace")
        .filter(pk=identifier, active=True, user__is_active=True, expires_at__gt=timezone.now())
        .first()
    )
    if not key or not check_password(secret, key.secret_hash):
        return denied()
    if not accessible_spaces(key.user).filter(pk=key.workspace_id).exists():
        return denied()
    try:
        page_number = int(request.GET.get("page", "1"))
        if page_number < 1:
            raise ValueError
    except ValueError:
        return JsonResponse({"error": "Página inválida."}, status=400)
    query = scoped(Entry, key.user, key.workspace).order_by("id")
    page = Paginator(query, 200).get_page(page_number)
    if page_number > page.paginator.num_pages:
        return JsonResponse({"schema_version": 1, "results": [], "next_page": None})
    fields = [
        "id",
        "description",
        "category",
        "kind",
        "amount",
        "occurred_on",
        "due_on",
        "paid_on",
        "status",
        "installment",
        "installments",
        "creator_id",
        "card_id",
    ]
    response = JsonResponse(
        {
            "schema_version": 1,
            "workspace_id": key.workspace_id,
            "results": list(page.object_list.values(*fields)),
            "next_page": page.next_page_number() if page.has_next() else None,
        }
    )
    response["Cache-Control"] = "no-store"
    return response
