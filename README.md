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

## Publicação e integrações externas

Existe Git próprio com commits locais e branches por etapa. A plataforma está integrada à main após CI remoto verde, com PR e check lint-e-testes obrigatórios; o histórico e as evidências estão no relatório local. Ainda não há deploy comprovado. O workflow GitHub Actions está pronto com Python 3.12, PostgreSQL e check lint-e-testes. Para publicar: criar/conectar repositório GitHub próprio, executar o CI e proteger main; em pedido próprio, configurar Railway, servidor WSGI, estáticos, proxy HTTPS, domínio, backups e Wait for CI. Não usar runserver em produção.

Configuração de produção exige SECRET_KEY forte, ALLOWED_HOSTS sem curingas e PostgreSQL com SSL explícito. A confiança em proxy só pode ser configurada após verificar o proxy da hospedagem. A preparação de produção está em docs/railway.md: Dockerfile, Gunicorn/WhiteNoise e perfil Railway com validação de contexto. O deploy ainda depende da conexão com a plataforma e da configuração/verificação de banco, domínio, variáveis e backups.

A API Power BI está testada localmente; o Desktop e o Power BI Service não foram conectados à conta do usuário. A atualização agendada depende de endereço HTTPS acessível, credenciais e teste no serviço. Não afirmar refresh on-line antes disso. O provedor de IA será habilitado em etapa própria, sem chaves no frontend.


