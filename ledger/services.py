import calendar
import re
from datetime import date, timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import AuditEvent, Entry, Purchase


def scoped(model, user, workspace):
    query = model.objects.filter(workspace=workspace)
    return query if workspace.owner_id == user.pk else query.filter(creator=user)


def month_add(value, offset):
    month_number = value.year * 12 + value.month - 1 + offset
    year, month = divmod(month_number, 12)
    return date(year, month + 1, 1)


def invoice_date(purchased, card, offset=0):
    closing = min(card.closing_day, calendar.monthrange(purchased.year, purchased.month)[1])
    cycle = month_add(purchased, int(purchased.day >= closing) + offset)
    due_month = month_add(cycle, int(card.due_day <= card.closing_day))
    day = min(card.due_day, calendar.monthrange(due_month.year, due_month.month)[1])
    return due_month.replace(day=day)


def split_amount(total, count):
    cents, remainder = divmod(int(total * 100), count)
    return [Decimal(cents + int(index < remainder)) / 100 for index in range(count)]


def create_entries(user, workspace, data):
    # The form validates cards against the authorized query; recheck in the service as well.
    card = data.get("card")
    if card and not scoped(type(card), user, workspace).filter(pk=card.pk).exists():
        raise ValueError("Cartão não autorizado.")
    count = data["installments"]
    if count > 1 and not card:
        raise ValueError("Parcelas exigem cartão nesta versão.")
    if card and data["kind"] != "expense":
        raise ValueError("Cartão é usado apenas para despesas.")
    amounts = split_amount(data["amount"], count)
    if min(amounts) <= 0:
        raise ValueError("O valor precisa permitir ao menos um centavo por parcela.")
    try:
        with transaction.atomic():
            purchase = Purchase.objects.create(workspace=workspace, creator=user, key=data["key"])
            for index, amount in enumerate(amounts):
                paid = data["status"] == "paid" and not card
                entry = Entry.objects.create(
                    workspace=workspace,
                    creator=user,
                    purchase=purchase,
                    description=data["description"],
                    category=data["category"],
                    kind=data["kind"],
                    amount=amount,
                    occurred_on=data["occurred_on"],
                    card=card,
                    due_on=invoice_date(data["occurred_on"], card, index)
                    if card
                    else data["due_on"],
                    paid_on=data["paid_on"] if paid else None,
                    status="paid" if paid else "pending",
                    installment=index + 1,
                    installments=count,
                )
                AuditEvent.objects.create(
                    workspace=workspace, actor=user, action="created", entry_id=entry.pk
                )
            return purchase
    except IntegrityError:
        existing = Purchase.objects.filter(
            key=data["key"], workspace=workspace, creator=user
        ).first()
        if existing:
            return existing
        raise


def parse_quick(text):
    if len(text) > 500:
        raise ValueError("Use uma frase curta de até 500 caracteres.")
    normalized = text.lower().strip()
    if re.search(r"[-−]\s*(?:r\$\s*)?\d", normalized):
        raise ValueError("Use valor positivo e escolha receita ou despesa na revisão.")
    moment = timezone.localdate()
    if "ontem" in normalized:
        moment -= timedelta(days=1)
    elif "amanhã" in normalized or "amanha" in normalized:
        moment += timedelta(days=1)
    dates = re.findall(r"\b\d{2}/\d{2}/\d{4}\b", normalized)
    if len(dates) > 1:
        raise ValueError("Informe apenas uma data.")
    if dates:
        day, month, year = map(int, dates[0].split("/"))
        moment = date(year, month, day)
        normalized = normalized.replace(dates[0], "")
    amounts = re.findall(
        r"(?<![\w/])(?:r\$\s*)?(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[,.]\d{1,2})?)(?![\w/])",
        normalized,
    )
    if len(amounts) != 1:
        raise ValueError("Informe um único valor, como: gastei 35,90 no almoço hoje.")
    amount = amounts[0]
    amount = Decimal(
        amount.replace(".", "").replace(",", ".")
        if "," in amount or amount.count(".") and len(amount.split(".")[-1]) == 3
        else amount
    )
    if not Decimal("0") < amount <= Decimal("999999999999.99"):
        raise ValueError("Informe um valor positivo válido.")
    category = "Outros"
    groups = {
        "Alimentação": ["almoço", "almoco", "mercado", "café", "jantar"],
        "Transporte": ["uber", "ônibus", "onibus", "gasolina"],
        "Moradia": ["aluguel", "condomínio"],
        "Salário": ["salário", "salario"],
        "Saúde": ["farmácia", "remédio", "consulta"],
        "Vendas": ["venda"],
    }
    for name, keywords in groups.items():
        if any(word in normalized for word in keywords):
            category = name
            break
    return {
        "amount": amount,
        "kind": "income"
        if any(word in normalized for word in ["recebi", "ganhei", "entrada"])
        else "expense",
        "description": text[:180],
        "category": category,
        "occurred_on": moment,
        "due_on": moment,
        "paid_on": moment if moment <= timezone.localdate() else None,
        "status": "paid" if moment <= timezone.localdate() else "pending",
        "installments": 1,
    }
