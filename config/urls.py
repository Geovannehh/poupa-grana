from django.contrib.auth import views as auth_views
from django.urls import path

from accounts.views import LimitedLoginView
from integrations import views as integrations
from ledger import views as ledger
from workspaces import views

from .health import health

urlpatterns = [
    path("integracoes/", integrations.settings, name="integrations"),
    path("integracoes/<uuid:key_id>/revogar/", integrations.revoke, name="revoke_credential"),
    path("api/bi/v1/entries/", integrations.export_entries, name="bi_entries"),
    path("health/", health, name="health"),
    path("", ledger.dashboard, name="home"),
    path("historico/", ledger.history, name="entries"),
    path("novo/", ledger.entry_new, name="entry_new"),
    path("lancamento/<int:entry_id>/", ledger.entry_action, name="entry_action"),
    path("cartoes/", ledger.cards, name="cards"),
    path("fatura/<int:card_id>/<str:due>/pagar/", ledger.invoice_pay, name="invoice_pay"),
    path("orcamentos/", ledger.budgets, name="budgets"),
    path("entrar/", LimitedLoginView.as_view(), name="login"),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    path("espaco/", views.switch, name="switch"),
    path("equipe/", views.team, name="team"),
    path("equipe/<int:member_id>/revogar/", views.deactivate_member, name="deactivate_member"),
]
