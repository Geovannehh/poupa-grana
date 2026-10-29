from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Workspace


def accessible_spaces(user):
    return Workspace.objects.filter(
        Q(owner=user) | Q(kind="business", memberships__user=user, memberships__active=True)
    ).distinct()


def selected_space(request):
    spaces = accessible_spaces(request.user)
    selected = request.session.get("workspace_id")
    # Never silently fall back when a saved space is no longer authorized.
    if selected is not None:
        return get_object_or_404(spaces, pk=selected)
    space = spaces.order_by("kind").first()
    if space is None:
        from django.http import Http404
        raise Http404("Nenhum espaço autorizado.")
    return space
