# Power BI — contrato de leitura v1

API: GET /api/bi/v1/entries/?page=1. Resposta JSON com schema_version=1, workspace_id, results e next_page. Valores monetários são strings decimais com ponto; datas são ISO; IDs de autor são internos. Cancelados continuam no histórico, portanto os relatórios devem filtrar status explicitamente. Caixa realizado: status=paid e paid_on; previsto: status=pending e due_on. Despesa de compra no cartão só entra no caixa quando sua parcela é baixada na fatura. Não somar compras e pagamentos como duas despesas.

Autenticação Basic dedicada: usuário = UUID da credencial; senha = segredo mostrado apenas na criação. Não usar a senha normal do aplicativo. Credenciais geradas no espaço ativo, válidas por 90 dias, com hash no servidor e revogação. Remoção de membership ou desativação do usuário invalida o acesso também na API. A sessão do navegador não autentica a API. Somente GET, páginas de até 200 registros. Mudanças concorrentes durante refresh não garantem snapshot; agende em momento de baixa movimentação para esta versão inicial.

## Power BI Desktop

1. Em Integrações, no espaço correto, gere uma credencial de leitura.
2. Obter dados → Web. Use a origem HTTPS publicada e o caminho da API.
3. Selecione autenticação Básica e informe a credencial dedicada no gerenciador do Power BI. Não grave o segredo em consultas M ou URLs.
4. Para paginar, use uma origem fixa e RelativePath/Query em Web.Contents. Exemplo de consulta M sem segredos:

```powerquery
let
    Origin = "https://SEU-DOMINIO.example.invalid",
    Fetch = (n as number) => Json.Document(Web.Contents(Origin, [
        RelativePath = "api/bi/v1/entries/", Query = [page = Text.From(n)]
    ])),
    Pages = List.Generate(() => [n = 1, data = Fetch(1)],
        each [data] <> null,
        each if [data][next_page] = null then [n = 0, data = null]
             else [n = [data][next_page], data = Fetch([data][next_page])],
        each [data][results]),
    Rows = List.Combine(Pages),
    Columns = {"id", "description", "category", "kind", "amount", "occurred_on", "due_on",
               "paid_on", "status", "installment", "installments", "creator_id", "card_id"},
    Table = Table.FromRecords(Rows, Columns, MissingField.UseNull),
    Typed = Table.TransformColumnTypes(Table, {{"amount", Currency.Type},
        {"occurred_on", type date}, {"due_on", type date}, {"paid_on", type date}}, "en-US")
in Typed
```

## Serviço on-line

A implementação local e o teste automatizado da API não comprovam refresh no Power BI Service. Após deploy HTTPS, configurar credenciais de fonte no serviço, testar validação de conexão, publicação do modelo e atualização agendada, verificando as políticas da conta/tenant e eventual necessidade de gateway. Não prometer que Desktop e serviço têm os mesmos tipos de autenticação. A opção Web API do conector tem limitações específicas no serviço; foi escolhida Basic dedicada para esta proposta, ainda sujeita ao teste de ponta a ponta.

Não há PBIX com credencial embutida nem dado financeiro publicado. Documentação oficial consultada: https://learn.microsoft.com/en-us/power-query/connectors/web/web .
