import uuid
from decimal import Decimal

from django import forms
from django.utils import timezone

from .models import Budget, Card, Entry
from .services import scoped


class EntryForm(forms.ModelForm):
    key = forms.UUIDField(widget=forms.HiddenInput, initial=uuid.uuid4)
    installments = forms.IntegerField(label="Parcelas", min_value=1, max_value=120, initial=1)

    class Meta:
        model = Entry
        fields = [
            "description",
            "kind",
            "amount",
            "category",
            "occurred_on",
            "due_on",
            "status",
            "paid_on",
            "card",
            "installments",
        ]
        labels = {
            "description": "Descrição",
            "kind": "Tipo",
            "amount": "Valor total (R$)",
            "category": "Categoria",
            "occurred_on": "Data da compra/competência",
            "due_on": "Vencimento",
            "status": "Situação",
            "paid_on": "Data do pagamento",
            "card": "Cartão (opcional)",
        }
        widgets = {
            key: forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
            for key in ["occurred_on", "due_on", "paid_on"]
        }

    def __init__(self, *args, user, workspace, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["card"].queryset = scoped(Card, user, workspace)
        self.fields["status"].choices = [("paid", "Pago"), ("pending", "Pendente")]
        self.fields["amount"].min_value = Decimal("0.01")
        for name in ["occurred_on", "due_on", "paid_on"]:
            self.fields[name].initial = timezone.localdate

    def clean(self):
        data = super().clean()
        card = data.get("card")
        if card and data.get("kind") != "expense":
            self.add_error("card", "Cartão aceita somente despesas.")
        if data.get("installments", 1) > 1 and not card:
            self.add_error("card", "Selecione um cartão para parcelar.")
        if data.get("amount") and data["amount"] * 100 < data.get("installments", 1):
            self.add_error("amount", "Cada parcela deve ter ao menos um centavo.")
        if not card and data.get("status") == "paid" and not data.get("paid_on"):
            self.add_error("paid_on", "Informe a data do pagamento.")
        if data.get("paid_on") and data["paid_on"] > timezone.localdate():
            self.add_error("paid_on", "Pagamento futuro deve ser registrado como pendente.")
        return data


class CardForm(forms.ModelForm):
    closing_day = forms.IntegerField(label="Dia do fechamento", min_value=1, max_value=31)
    due_day = forms.IntegerField(label="Dia do vencimento", min_value=1, max_value=31)

    class Meta:
        model = Card
        fields = ["name", "closing_day", "due_day"]
        labels = {"name": "Nome do cartão (sem número ou CVV)"}


class BudgetForm(forms.ModelForm):
    month = forms.DateField(
        label="Mês (dia 1)",
        widget=forms.DateInput(attrs={"type": "date"}),
        initial=lambda: timezone.localdate().replace(day=1),
    )

    class Meta:
        model = Budget
        fields = ["category", "month", "limit"]
        labels = {"category": "Categoria", "limit": "Limite mensal (R$)"}

    def clean_month(self):
        return self.cleaned_data["month"].replace(day=1)
