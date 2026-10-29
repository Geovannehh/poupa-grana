import calendar
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import ExtractDay
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from workspaces.access import accessible_spaces, selected_space

from .forms import BudgetForm, CardForm, EntryForm
from .models import AuditEvent, Budget, Card, Entry
from .services import create_entries, month_add, parse_quick, scoped


def context(request):
    space = selected_space(request)
    return {
        "workspace": space,
        "spaces": accessible_spaces(request.user),
        "is_owner": space.owner_id == request.user.pk,
    }


def aggregate(query):
    return query.aggregate(total=Sum("amount"))["total"] or Decimal("0")


@login_required
def dashboard(request):
    ctx = context(request)
    try:
        month = date.fromisoformat(
            request.GET.get("month", timezone.localdate().strftime("%Y-%m")) + "-01"
        )
    except ValueError:
        return HttpResponseBadRequest("Mês inválido.")
    if not 1900 <= month.year <= 2100:
        return HttpResponseBadRequest("Ano fora do intervalo suportado (1900 a 2100).")
    end = month_add(month, 1)
    entries = scoped(Entry, request.user, ctx["workspace"])
    paid = entries.filter(status="paid", paid_on__gte=month, paid_on__lt=end)
    income = aggregate(paid.filter(kind="income"))
    expense = aggregate(paid.filter(kind="expense"))
    pending = entries.filter(status="pending", due_on__gte=month, due_on__lt=end)
    distribution = list(
        paid.filter(kind="expense")
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    for row in distribution:
        row["width"] = int(row["total"] / expense * 100) if expense else 0
    budgets = scoped(Budget, request.user, ctx["workspace"]).filter(month=month)
    budget_rows = []
    for budget in budgets:
        # An individual's budget must not include coworkers, even in owner's overview.
        used = aggregate(
            paid.filter(category=budget.category, kind="expense", creator_id=budget.creator_id)
        )
        budget_rows.append(
            {"item": budget, "used": used, "percent": min(100, int(used / budget.limit * 100))}
        )
    daily = {
        (row["day"], row["kind"]): row["total"]
        for row in paid.annotate(day=ExtractDay("paid_on"))
        .values("day", "kind")
        .annotate(total=Sum("amount"))
        .order_by()
    }
    ctx.update(
        month=month,
        income=income,
        expense=expense,
        balance=income - expense,
        pending_expense=aggregate(pending.filter(kind="expense")),
        pending_income=aggregate(pending.filter(kind="income")),
        overdue=entries.filter(status="pending", due_on__lt=timezone.localdate()).count(),
        entries=entries.select_related("creator", "card")[:12],
        distribution=distribution,
        budgets=budget_rows,
        flow=[
            {
                "day": day,
                "income": str(daily.get((day, "income"), 0)),
                "expense": str(daily.get((day, "expense"), 0)),
            }
            for day in range(1, calendar.monthrange(month.year, month.month)[1] + 1)
        ],
    )
    return render(request, "ledger/dashboard.html", ctx)


@login_required
def entry_new(request):
    ctx = context(request)
    initial = {}
    notice = ""
    if request.method == "POST" and "quick" in request.POST:
        try:
            initial = parse_quick(request.POST["quick"])
            notice = (
                "Rascunho por regras. Confira os campos antes de salvar. Nenhum dado foi salvo."
            )
        except ValueError as error:
            messages.error(request, str(error))
        form = EntryForm(initial=initial, user=request.user, workspace=ctx["workspace"])
    else:
        form = EntryForm(request.POST or None, user=request.user, workspace=ctx["workspace"])
        if request.method == "POST" and form.is_valid():
            try:
                create_entries(request.user, ctx["workspace"], form.cleaned_data)
            except ValueError as error:
                form.add_error(None, str(error))
            else:
                messages.success(
                    request, "Lançamento salvo. Parcelas de cartão ficam pendentes na fatura."
                )
                return redirect("home")
    ctx.update(form=form, heading="Confira seu lançamento", notice=notice)
    return render(request, "ledger/form.html", ctx)


@login_required
@require_POST
@transaction.atomic
def entry_action(request, entry_id):
    space = selected_space(request)
    entry = get_object_or_404(scoped(Entry, request.user, space).select_for_update(), pk=entry_id)
    previous = {"status": entry.status, "paid_on": str(entry.paid_on)}
    action = request.POST.get("action")
    if action == "pay" and not entry.card_id and entry.status == "pending":
        entry.status, entry.paid_on = "paid", timezone.localdate()
    elif action == "cancel" and entry.status != "cancelled":
        entry.status = "cancelled"
        entry.paid_on = None
    else:
        return redirect("home")
    entry.save(update_fields=["status", "paid_on"])
    AuditEvent.objects.create(
        workspace=space,
        actor=request.user,
        action=action,
        entry_id=entry.pk,
        details={"before": previous, "after": entry.status},
    )
    messages.success(request, "Registro atualizado com histórico de auditoria.")
    return redirect("home")


@login_required
def cards(request):
    ctx = context(request)
    form = CardForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        card = form.save(commit=False)
        card.creator, card.workspace = request.user, ctx["workspace"]
        card.save()
        return redirect("cards")
    invoices = (
        scoped(Entry, request.user, ctx["workspace"])
        .filter(card__isnull=False, status="pending")
        .values("card_id", "card__name", "due_on")
        .annotate(total=Sum("amount"))
    )
    ctx.update(form=form, cards=scoped(Card, request.user, ctx["workspace"]), invoices=invoices)
    return render(request, "ledger/cards.html", ctx)


@login_required
@require_POST
@transaction.atomic
def invoice_pay(request, card_id, due):
    space = selected_space(request)
    card = get_object_or_404(scoped(Card, request.user, space), pk=card_id)
    try:
        due = date.fromisoformat(due)
    except ValueError:
        raise Http404 from None
    for entry in (
        scoped(Entry, request.user, space)
        .select_for_update()
        .filter(card=card, due_on=due, status="pending")
    ):
        entry.status, entry.paid_on = "paid", timezone.localdate()
        entry.save(update_fields=["status", "paid_on"])
        AuditEvent.objects.create(
            workspace=space, actor=request.user, action="invoice_paid", entry_id=entry.pk
        )
    messages.success(request, "Fatura baixada uma única vez no caixa; não gera despesa duplicada.")
    return redirect("cards")


@login_required
def budgets(request):
    ctx = context(request)
    form = BudgetForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        Budget.objects.update_or_create(
            workspace=ctx["workspace"],
            creator=request.user,
            category=form.cleaned_data["category"],
            month=form.cleaned_data["month"],
            defaults={"limit": form.cleaned_data["limit"]},
        )
        messages.success(request, "Orçamento mensal salvo para seus próprios gastos pagos.")
        return redirect("home")
    ctx.update(
        form=form,
        heading="Planeje seu orçamento",
        notice="Base: gastos pagos no mês, por pessoa e categoria.",
    )
    return render(request, "ledger/form.html", ctx)


@login_required
def history(request):
    from django.core.paginator import Paginator

    ctx = context(request)
    query = scoped(Entry, request.user, ctx["workspace"]).select_related("creator", "card")
    term = request.GET.get("q", "")[:180]
    if term:
        query = query.filter(description__icontains=term)
    page = Paginator(query, 30).get_page(request.GET.get("page"))
    ctx.update(page=page, entries=page.object_list, q=term)
    return render(request, "ledger/history.html", ctx)
