"""Provider seam: external AI is deliberately not enabled yet."""

from typing import Protocol


class FinancialProvider(Protocol):
    def analyze(self, *, question: str, authorized_summary: dict) -> str:
        """Use only the authorized summary; never execute financial changes."""
        ...


class ProviderNotConfigured(RuntimeError):
    pass


def get_provider() -> FinancialProvider:
    raise ProviderNotConfigured("Provedor de IA não configurado; use o modo por regras.")
