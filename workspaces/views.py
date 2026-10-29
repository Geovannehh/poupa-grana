from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .access import accessible_spaces, selected_space
from .forms import MemberForm
from .models import Membership


@login_required
def home(request):
    space = selected_space(request)
    return render(request, "workspaces/home.html", {
        "workspace": space, "spaces": accessible_spaces(request.user),
        "is_owner": space.owner_id == request.user.pk,
    })


@login_required
@require_POST
def switch(request):
    try:
        workspace_id = int(request.POST.get("workspace", ""))
    except (ValueError, TypeError):
        raise Http404 from None
    space = get_object_or_404(accessible_spaces(request.user), pk=workspace_id)
    request.session["workspace_id"] = space.pk
    return redirect("home")


@login_required
def team(request):
    space = selected_space(request)
    if space.owner_id != request.user.pk or space.kind != "business":
        return HttpResponseForbidden("Apenas o proprietário da empresa gerencia a equipe.")
    form = MemberForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = get_user_model().objects.create_user(**form.cleaned_data)
            Membership.objects.create(workspace=space, user=user)
        messages.success(request, "Integrante criado. Ele verá apenas seus próprios lançamentos.")
        return redirect("team")
    return render(request, "workspaces/team.html", {
        "workspace": space, "spaces": accessible_spaces(request.user), "is_owner": True,
        "form": form, "members": Membership.objects.filter(workspace=space).select_related("user"),
    })


@login_required
@require_POST
def deactivate_member(request, member_id):
    space = selected_space(request)
    if space.owner_id != request.user.pk or space.kind != "business":
        return HttpResponseForbidden()
    member = get_object_or_404(Membership, pk=member_id, workspace=space)
    member.active = False
    member.save(update_fields=["active"])
    messages.success(request, "Acesso ao espaço revogado.")
    return redirect("team")
