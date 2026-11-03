# Poupa Grana

Controle financeiro local em Django + PostgreSQL, com espaços pessoal e empresarial separados. O proprietário tem visão da empresa; integrantes acessam somente seus registros empresariais. Nenhum dado financeiro real foi pré-carregado.

## Funcionalidades locais

- Login individual, proteção contra tentativas repetidas, logout por POST e CSRF.
- Troca explícita entre Pessoal e Empresa. Criação e revogação de integrantes pelo proprietário.
- Receitas/despesas pagas ou pendentes, vencimento, baixa e histórico pesquisável.
- Texto rápido (ex.: “gastei 35,90 no almoço hoje”) prepara rascunho editável e exige confirmação. É processamento por regras, sem IA externa.
- Cartões por usuário, fechamento/vencimento, parcelas exatas em centavos e baixa de fatura sem despesa duplicada.
- Orçamentos por pessoa/categoria/mês, avisos de limite e compromissos vencidos dentro do sistema.
- Dashboard por mês de caixa, gráfico interativo com tabela acessível, categorias e resumo por regras.
- API de leitura autenticada para Power BI, validade de 90 dias e revogação. Veja docs/power-bi.md.
- Protocolo de provedor IA em assistant/providers.py, propositalmente sem provedor habilitado.
