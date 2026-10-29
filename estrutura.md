# Poupa Grana — estrutura do projeto

Escopo confirmado pelo proprietário em 29/10/2026. Este documento especifica o sistema a construir; não indica funcionalidades já implementadas.

## Decisões confirmadas

Sistema on-line, responsivo, em português brasileiro e BRL, com espaços pessoal e empresarial separados. Pessoal exclusivo do proprietário. Equipe apenas no empresarial, com login individual: cada membro vê seus próprios lançamentos; proprietário vê tudo e administra acessos. Começar do zero. Receitas, despesas, contas a pagar/receber, categorias, metas, cartões e parcelas; dashboard interativo; avisos internos; entrada por texto com revisão antes de salvar. IA com provedor futuro. Power BI autenticado. GitHub público, Railway, VS Code e PowerShell.

## Arquitetura proposta

- Monólito Django e PostgreSQL no desenvolvimento, CI e produção. Não substituir por SQLite silenciosamente.
- Templates Django com HTML/CSS e JavaScript progressivo; gráficos acessíveis com alternativa em tabela. Biblioteca visual e identidade serão apresentadas no pedido de telas antes de implementação.
- Psycopg para PostgreSQL; pytest-django e ruff para testes e verificação de código. Gunicorn e WhiteNoise para a etapa Railway. Fixar versões compatíveis consultando documentação oficial na implementação.
- Apps previstos: accounts, workspaces, ledger, cards, budgets, dashboard, assistant e integrations. Criar somente os necessários a cada módulo.
- Sessões Django, CSRF e validação no servidor. Não reutilizar usuários ou credenciais de projetos anteriores.
- Configuração por ambiente. Segredos fora do Git e dos logs. .env.example somente com campos vazios ou fictícios. URL de banco nunca no frontend.
- Português brasileiro, datas locais em America/Sao_Paulo, instantes armazenados com timezone, valores monetários Decimal/centavos, nunca float.

## Regras de negócio propostas para os módulos

1. Toda entidade financeira pertence a um espaço; usuário autor e beneficiário são distintos quando necessário. Negar acesso por padrão. O servidor deriva o usuário autenticado; não confiar em autor ou workspace do formulário sem validar.
2. O filtro de autorização deve existir em detalhes, listas, alterações, dashboard, totais, busca, avisos, assistente e Power BI. O integrante não recebe totais que revelem finanças de colegas. Ser staff não substitui automaticamente o papel de proprietário.
3. Lançamentos têm valor positivo, tipo receita/despesa, descrição, categoria, competência, vencimento, situação e data de pagamento. Saldo realizado soma pagamentos, não previsões. Valores pendentes aparecem separadamente em projeções.
4. Contas liquidadas alteram caixa uma única vez; ações repetidas precisam ser idempotentes. Cancelamento e estorno mantêm trilha de auditoria. Transferências entre contas não são receita nem despesa.
5. Compra no cartão gera obrigação/parcelas, não saída imediata da conta bancária. Pagamento da fatura reduz caixa e obrigação sem contar a despesa duas vezes. Relatórios distinguem caixa e competência.
6. Parcelas devem somar exatamente o total da compra; distribuir centavos de forma determinística. Datas respeitam fim de mês, fechamento e vencimento. Política de compra no dia de fechamento e tratamento de estorno parcial serão apresentados no pedido de cartões antes da implementação.
7. Orçamentos por espaço, categoria e mês, com realizado e percentual; definir a base caixa/competência visivelmente. Avisos internos por orçamento e vencimento; sem envio externo nesta versão.
8. Texto rápido produz rascunho editável (valor, tipo, categoria, data, espaço). Campo ausente/ambíguo deve pedir correção; não salvar ao interpretar. Repetir confirmação não pode duplicar lançamento.
9. Sem provedor, a interface identifica o modo por regras. A integração de IA terá interface substituível; não transmitir dados a terceiros antes de configurar provedor e escopo. IA não executa pagamento, altera registro ou decide acesso. Resumos exibem período, base e dados utilizados.
10. Power BI: API versionada somente leitura, autenticação dedicada revogável e vinculada ao usuário/espaço, paginação e contrato estável. Não expor PostgreSQL publicamente como atalho. Testar autenticação no Desktop e atualização no serviço separadamente; não colocar segredos em URL, exemplos ou PBIX de demonstração. O conector Web tem diferenças de suporte entre Desktop e serviço; escolher mecanismo suportado no módulo 8.

## Modelos de dados previstos

| Modelo | Responsabilidade / campos principais |
| --- | --- |
| User | Modelo próprio desde a primeira migração, baseado no usuário Django; credenciais e estado ativo |
| Workspace | Tipo pessoal/empresarial e proprietário |
| Membership | Usuário, espaço, papel, ativo; unicidade usuário/espaço |
| Account | Conta financeira, espaço e saldo inicial com data de referência |
| Category | Espaço, nome e tipo |
| Entry | Espaço, autor, conta, categoria, tipo, Decimal, datas, situação e chave de idempotência |
| Payment | Liquidação de uma obrigação, conta, data e valor, sem duplicação |
| Transfer | Origem/destino no mesmo espaço; débito/crédito vinculados |
| Card / Statement | Espaço, responsável, fechamento/vencimento e ciclo de fatura; sem número completo ou CVV |
| Purchase / Installment | Total, número de parcelas, ordinal, valor e fatura vinculada |
| Budget | Espaço, categoria, mês, limite e base do cálculo |
| Notification | Destinatário, espaço, evento e estado de leitura |
| IntegrationCredential | Usuário, espaço, escopo somente leitura, hash do segredo, validade e revogação |
| AuditEvent | Ator, espaço, ação, entidade e instante; sem segredos ou payload sensível desnecessário |

Este é um desenho para detalhar por módulo; não criar todas as tabelas na base inicial.

## Entregas — um PR por assunto

| Ordem | Pedido / módulo | Critério principal |
| --- | --- | --- |
| 1A | Base local + CI | Django inicia com PostgreSQL, migrações, health e check lint-e-testes |
| 1B | Railway | Após 1A e acessos, configurar deploy da main com Wait for CI e health, sem publicar dados reais |
| 2 | Login e isolamento | Proprietário, equipe e espaços com testes negativos de acesso |
| 3 | Lançamentos e contas | CRUD, liquidação, caixa/competência e auditoria |
| 4 | Cartões e parcelas | Ciclo de faturas, arredondamento, pagamentos e estornos sem duplicidade |
| 5 | Orçamentos e dashboard | Filtros interativos por período/espaço, gráficos, tabelas e avisos internos |
| 6 | Texto rápido | Rascunho por regras, revisão e salvamento idempotente |
| 7 | Assistente | Interface de provedor, modo desligado explícito e análises apoiadas nos dados autorizados |
| 8 | Power BI | API autenticada e documentação; testes Desktop e serviço antes de declarar atualização automática pronta |

Módulos maiores podem ser subdivididos em pedidos por assunto. Não incluir publicação no pedido 1A.

## Fora da primeira versão

Estoque, emissão de notas fiscais, Open Finance, pagamentos bancários, captura de senha bancária, WhatsApp/e-mail, aplicativo nativo, OCR, voz, múltiplas moedas e escolha automática de provedor de IA. Não assumir manutenção contábil/fiscal ou recomendação de investimentos.

## Situação e referências verificadas em 29/10/2026

Ainda sem código, CI executado, GitHub ou Railway provisionados. As escolhas de bibliotecas secundárias e versões são propostas técnicas a validar no pedido inicial.

- Railway Django: https://docs.railway.com/guides/django
- Railway Wait for CI: https://docs.railway.com/deployments/github-autodeploys
- GitHub CI Python: https://docs.github.com/en/actions/tutorials/build-and-test-code/python
- GitHub proteção: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- Power Query Web (limites de autenticação por produto): https://learn.microsoft.com/en-us/power-query/connectors/web/web


## Estado após continuação delegada — 29/10/2026

Versão local funcional com 64 testes passando em PostgreSQL real. Implementados accounts, workspaces, ledger e integrations; assistant contém o protocolo de provedor desligado. O usuário delegou decisões para continuar além do pedido inicial.

O desenho inicial de tabelas foi simplificado para a primeira versão: Entry representa compromissos e sua baixa; Purchase agrupa operações idempotentes e parcelas; Card representa o cartão e as faturas são agrupadas por cartão/vencimento. Budget é individual por categoria. AuditEvent registra eventos. Não há Account bancária, saldo inicial, Transfer ou Payment independente nesta versão: a tela apresenta resultado mensal, nunca saldo bancário completo. Categorias iniciais são fixas. Anulação corrige erro de registro e não é uma devolução bancária automática. Esses limites aparecem no README e na interface quando relevantes.

Base/isolamento/financeiro/dashboard/texto rápido estão implementados localmente. A integração Power BI é uma API autenticada local testada, com Desktop/Service ainda pendentes. IA permanece por regras como escolhido. Hospedagem Railway, CI remoto, proteção de main e acesso público seguro não foram realizados; dependem de repositório e conexão da hospedagem.
