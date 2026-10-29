import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from workspaces.models import Workspace

CATEGORIES = [
    (x, x)
    for x in [
        "Alimentação",
        "Transporte",
        "Moradia",
        "Saúde",
        "Educação",
        "Lazer",
        "Serviços",
        "Vendas",
        "Salário",
        "Outros",
    ]
]


class Card(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(max_length=60)
    closing_day = models.PositiveSmallIntegerField()
    due_day = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.name


class Purchase(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    key = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Entry(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    purchase = models.ForeignKey(Purchase, on_delete=models.PROTECT)
    description = models.CharField(max_length=180)
    category = models.CharField(max_length=30, choices=CATEGORIES)
    kind = models.CharField(max_length=10, choices=[("expense", "Despesa"), ("income", "Receita")])
    amount = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    occurred_on = models.DateField()
    due_on = models.DateField()
    paid_on = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=12,
        default="pending",
        choices=[
            ("pending", "Pendente"),
            ("paid", "Pago"),
            ("cancelled", "Cancelado"),
        ],
    )
    card = models.ForeignKey(Card, on_delete=models.PROTECT, null=True, blank=True)
    installment = models.PositiveSmallIntegerField(default=1)
    installments = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_on", "-id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="positive_entry_amount"),
            models.UniqueConstraint(
                fields=["purchase", "installment"], name="unique_purchase_part"
            ),
        ]


class Budget(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    category = models.CharField(max_length=30, choices=CATEGORIES)
    month = models.DateField()
    limit = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "creator", "category", "month"],
                name="unique_month_budget",
            )
        ]


class AuditEvent(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=30)
    details = models.JSONField(default=dict)
    entry_id = models.PositiveBigIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
