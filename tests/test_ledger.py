import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from ledger.models import Card, Entry
from ledger.services import create_entries, invoice_date, parse_quick, split_amount
from workspaces.models import Membership, Workspace


@pytest.mark.parametrize("total,count", [("100.00", 3), ("0.10", 3), ("12345.67", 120)])
def test_installments_preserve_exact_cents(total, count):
    parts = split_amount(Decimal(total), count)
    assert sum(parts) == Decimal(total)
    assert max(parts) - min(parts) <= Decimal("0.01")


@pytest.mark.parametrize(
    "purchase,closing,due,expected",
    [
        (date(2026, 1, 10), 20, 10, date(2026, 2, 10)),
        (date(2026, 1, 20), 20, 10, date(2026, 3, 10)),
        (date(2026, 1, 30), 31, 31, date(2026, 2, 28)),
        (date(2026, 12, 29), 5, 15, date(2027, 1, 15)),
    ],
)
def test_invoice_calendar(purchase, closing, due, expected):
    assert invoice_date(purchase, SimpleNamespace(closing_day=closing, due_day=due)) == expected


def test_quick_draft_handles_brazilian_money():
    result = parse_quick("gastei R$ 1.250,90 no mercado ontem")
    assert result["amount"] == Decimal("1250.90")
    assert result["category"] == "Alimentação"
    assert result["kind"] == "expense"


@pytest.mark.parametrize(
    "text", ["gastei no mercado", "gastei 10 no café e 20 no almoço", "gastei 10 em 31/02/2026"]
)
def test_ambiguous_or_invalid_quick_text_requires_correction(text):
    with pytest.raises(ValueError):
        parse_quick(text)


@pytest.fixture
def people(db):
    User = get_user_model()
    owner = User.objects.create_user(username="finance_owner", password=None)
    member = User.objects.create_user(username="finance_member", password=None)
    other = User.objects.create_user(username="finance_other", password=None)
    company = Workspace.objects.create(name="Company", kind="business", owner=owner)
    personal = Workspace.objects.create(name="Personal", kind="personal", owner=owner)
    Membership.objects.create(workspace=company, user=member)
    Membership.objects.create(workspace=company, user=other)
    return owner, member, other, company, personal


def payload(**overrides):
    today = timezone.localdate()
    return {
        "key": uuid.uuid4(),
        "description": "Café",
        "kind": "expense",
        "amount": Decimal("100.00"),
        "category": "Alimentação",
        "occurred_on": today,
        "due_on": today,
        "paid_on": today,
        "status": "paid",
        "installments": 1,
        "card": None,
        **overrides,
    }


@pytest.mark.postgres
@pytest.mark.django_db
def test_duplicate_submission_is_idempotent(people):
    owner, _, _, company, _ = people
    data = payload()
    first = create_entries(owner, company, data)
    second = create_entries(owner, company, data)
    assert first.pk == second.pk
    assert Entry.objects.count() == 1


@pytest.mark.postgres
@pytest.mark.django_db
def test_member_dashboard_and_history_hide_colleagues(client, people):
    owner, member, other, company, personal = people
    create_entries(owner, personal, payload(description="PERSONAL_SECRET"))
    create_entries(other, company, payload(description="COWORKER_SECRET"))
    create_entries(member, company, payload(description="OWN_RECORD", amount=Decimal("3.50")))
    client.force_login(member)
    response = client.get("/")
    assert response.status_code == 200
    assert response.context["expense"] == Decimal("3.50")
    assert b"PERSONAL_SECRET" not in response.content
    assert b"COWORKER_SECRET" not in response.content
    assert b"COWORKER_SECRET" not in client.get("/historico/").content


@pytest.mark.postgres
@pytest.mark.django_db
def test_member_cannot_mutate_other_entry(client, people):
    _, member, other, company, _ = people
    purchase = create_entries(other, company, payload())
    entry = purchase.entry_set.get()
    client.force_login(member)
    response = client.post(f"/lancamento/{entry.pk}/", {"action": "cancel"})
    assert response.status_code == 404
    entry.refresh_from_db()
    assert entry.status == "paid"


@pytest.mark.postgres
@pytest.mark.django_db
def test_card_payment_does_not_duplicate_expense(client, people):
    owner, *_rest, company, _personal = people
    card = Card.objects.create(
        workspace=company, creator=owner, name="Example", closing_day=5, due_day=15
    )
    create_entries(owner, company, payload(card=card, installments=3))
    entries = Entry.objects.filter(card=card)
    assert sum(x.amount for x in entries) == Decimal("100.00")
    assert set(entries.values_list("status", flat=True)) == {"pending"}
    client.force_login(owner)
    client.post("/espaco/", {"workspace": company.pk})
    entry = entries.order_by("due_on").first()
    url = f"/fatura/{card.pk}/{entry.due_on.isoformat()}/pagar/"
    client.post(url)
    client.post(url)
    assert Entry.objects.count() == 3
    assert Entry.objects.filter(status="paid").count() == 1
    assert client.get("/").context["expense"] == entry.amount


@pytest.mark.postgres
@pytest.mark.django_db
def test_other_users_card_is_rejected_in_form(client, people):
    _, member, other, company, _ = people
    card = Card.objects.create(
        workspace=company, creator=other, name="PRIVATE_CARD", closing_day=5, due_day=15
    )
    client.force_login(member)
    data = payload(card=card.pk)
    response = client.post("/novo/", data)
    assert response.status_code == 200
    assert "card" in response.context["form"].errors
    assert not Entry.objects.exists()
    assert b"PRIVATE_CARD" not in response.content


@pytest.mark.postgres
@pytest.mark.django_db
def test_quick_input_only_prepares_draft(client, people):
    client.force_login(people[1])
    response = client.post("/novo/", {"quick": "gastei 35 no almoço hoje"})
    assert response.status_code == 200
    assert response.context["form"].initial["amount"] == Decimal("35")
    assert not Entry.objects.exists()


@pytest.mark.postgres
@pytest.mark.django_db
def test_confirmed_form_saves_and_repeated_post_does_not_duplicate(client, people):
    client.force_login(people[1])
    data = payload()
    data.pop("card")
    assert client.post("/novo/", data).status_code == 302
    assert client.post("/novo/", data).status_code == 302
    assert Entry.objects.count() == 1


@pytest.mark.postgres
@pytest.mark.django_db
def test_empty_dashboard_and_budget_form_render(client, people):
    client.force_login(people[1])
    assert client.get("/").status_code == 200
    assert client.get("/orcamentos/").status_code == 200
    assert client.get("/cartoes/").status_code == 200
    assert client.get("/?month=invalid").status_code == 400


def test_negative_quick_amount_is_not_silently_converted():
    with pytest.raises(ValueError):
        parse_quick("gastei -35 no almoço")


def test_tomorrow_is_prepared_as_pending():
    from datetime import timedelta

    draft = parse_quick("gastei 35 no almoço amanhã")
    assert draft["status"] == "pending"
    assert draft["paid_on"] is None
    assert draft["due_on"] == timezone.localdate() + timedelta(days=1)
