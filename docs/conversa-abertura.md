# Poupa Grana — registro da abertura

Última atualização: 29/10/2026 00:44 (America/Sao_Paulo).

## Resumo vivo

Estado: versão funcional local implementada, PostgreSQL portátil oficial 17.11 autenticado em loopback, migrações aplicadas e 64 testes passando. Git próprio com commits por etapa; nenhum remoto, PR, CI remoto ou deploy comprovado. GitHub conectado via plugin, mas criação do repositório requer autenticação no navegador; Railway ainda não conectada. IA permanece por regras, com interface de provedor preparada; Power BI com API local testada e refresh externo pendente.

### Decisões do usuário

- Nome: Poupa Grana. Identificador técnico: poupa-grana.
- Começar do zero, sem planilha ou processo a importar.
- Separar espaço pessoal e espaço empresarial.
- Espaço pessoal exclusivo do proprietário.
- Equipe apenas no espaço empresarial, com login individual.
- Integrantes registram e veem apenas seus próprios lançamentos; proprietário acompanha todo o empresarial.
- Apenas o proprietário administra usuários, permissões e configurações.
- Controlar receitas, despesas, contas a pagar e receber, categorias, metas de orçamento, cartões de crédito e compras parceladas.
- Dashboard interativo e avisos dentro do sistema.
- Entrada principal por texto rápido; o sistema prepara uma proposta de lançamento para o usuário conferir antes de salvar.
- IA: preparar integração, deixando a escolha e configuração do provedor para depois. Na ausência de provedor, identificar campos por regras explicitamente apresentadas como regras, sem simular IA.
- Power BI: conexão autenticada que respeite as permissões de acesso.
- Stack escolhida: Django + PostgreSQL.
- Acesso on-line por computador e celular.
- Hospedagem escolhida: Railway. Nenhuma contratação ou despesa autorizada nesta etapa.
- GitHub público: exemplos fictícios; sem dados financeiros reais, senhas, chaves, bancos locais ou segredos no repositório.
- Editor: VS Code. Terminal: PowerShell no Windows.

### Recomendações e limites

- As recomendações de stack e hospedagem foram apresentadas como opções e escolhidas pelo usuário.
- Detalhes de autenticação do Power BI, atualização agendada, limites e eventual necessidade de gateway devem ser definidos com documentação atual antes da implementação; conexão ainda não executada ou validada.
- Regras de fechamento e vencimento de fatura, alocação de parcelas, estornos e efeitos no caixa devem ser especificadas na estrutura e verificadas com testes.
- Sugestões de IA devem exigir ação humana para salvar ou alterar lançamentos.
- Ambientes pessoal e empresarial precisam de isolamento de acesso também nas consultas, dashboard, exportação e integrações.

### Pendências

1. Concluído: confirmação do resumo pelo usuário.
2. Concluído: estrutura.md, CLAUDE.md, pedido-01-base-local-ci.txt, task.md e .gitignore gravados e relidos.
3. Verificar a documentação atual de Django, PostgreSQL, Railway, GitHub e Power BI antes de escolher versões e gerar configurações de integração/CI/hospedagem.
4. Identificar a conta/repositório e os acessos disponíveis para GitHub e Railway quando necessários, sem solicitar segredos pelo chat.
5. Base local e workflow preparados; concluir PostgreSQL local, migração e dois testes de integração antes de declarar validação completa.
6. Validar as regras de cartões e parcelas durante a especificação do módulo financeiro.

## Histórico geral desta abertura

1. O usuário pediu um sistema financeiro com dashboard interativo, assistente de IA para apoiar decisões e facilitar o registro de gastos diários, com possibilidade de integração ao Power BI. Indicou modelo-fluxo-novo-projeto.txt como referência.
2. O arquivo foi lido. A conversa passou a conduzir a abertura por escolhas curtas, uma por vez.
3. O usuário escolheu pessoal e empresa separados; depois, pessoal exclusivo e empresarial com equipe.
4. Escolheu começar do zero e limitar os integrantes aos próprios lançamentos, com visão geral do proprietário.
5. Escolheu receitas, despesas, contas, categorias, metas, cartões e parcelas; estoque e notas fiscais não foram incluídos.
6. Informou conhecer Python/Flask/Django e escolheu Django + PostgreSQL.
7. Escolheu acesso pela internet e Railway.
8. Nomeou o projeto Poupa Grana e escolheu GitHub público.
9. Definiu apenas um administrador: o proprietário; avisos internos.
10. Escolheu entrada por texto rápido com revisão antes de salvar.
11. Escolheu deixar a configuração do provedor de IA para depois. Foi explicado que o processamento inicial poderá usar regras sem se apresentar como IA.
12. Escolheu conexão autenticada com Power BI.
13. Escolheu VS Code e PowerShell.
14. Este registro foi criado para consolidar as escolhas. A confirmação do escopo será solicitada antes dos documentos de implementação.

15. O usuário confirmou o escopo. Foram preparados os documentos de arquitetura, regras e pedido inicial limitado à base local e CI; sem código ou deploy.
16. Consultadas fontes oficiais Railway, GitHub e Microsoft; identificado limite do Web API do Power BI no serviço, exigindo validação separada da autenticação e atualização no módulo 8.

17. O usuário pediu “leia o task.md e execute”. O pedido foi lido com todos os documentos e implementado apenas em seu escopo.
18. Ambiente virtual próprio criado com dependências fixadas. Identificados Git pai fora do projeto e ausência de PostgreSQL/Docker; sem alteração no Git pai ou instalação global.
19. Verificações: Ruff e Django check passaram; 20 testes passaram, dois tiveram erro de conexão PostgreSQL. Migração gerada, não aplicada; CI apenas preparado. README, task.md e RELATORIO.md atualizados com instruções e limites.

## Fontes

- Solicitações e respostas do usuário nesta conversa sobre o novo sistema.
- Referência local fornecida: modelo-fluxo-novo-projeto.txt, fornecido localmente pelo usuário.
- O projeto Conecta Campus pertence a uma solicitação anterior; seu banco, usuários, credenciais e regras não serão reutilizados no Poupa Grana.

- Fontes técnicas verificadas e vinculadas em estrutura.md. As regras detalhadas de finanças e a divisão técnica são propostas de implementação, não respostas adicionais do usuário.

## Continuação autorizada

O proprietário autorizou continuar e tomar as decisões técnicas por ele. Isso permite avançar nas entregas locais e definir regras reversíveis sem novas rodadas de perguntas. Permanecem as escolhas de Django/PostgreSQL, espaços separados, GitHub público e Railway. Integrações, custos e autenticação externa não são considerados concluídos sem acesso e evidência. Decisão técnica: PostgreSQL portátil oficial na pasta ignorada .local, escutando só em loopback, sem serviço Windows; completar a base antes de implementar o módulo 2.

## Histórico da continuação delegada

- O proprietário autorizou continuar e delegou decisões técnicas.
- Foram obtidos os binários oficiais PostgreSQL 17.11 da página EDB indicada pelo site PostgreSQL; cluster, senhas e bancos permanecem em .local/.env, ignorados pelo Git. Nenhum serviço Windows foi instalado. Resolvida limitação de caminho Windows acentuado com caminho curto ao iniciar PostgreSQL.
- Concluída a base: 22 testes passaram com banco real. Criado Git próprio sem alteração no Git pai, commit inicial na main e branches locais por etapa; nenhum merge ou remoto.
- Implementados login/logout, limite de tentativas, proprietário pessoal/empresa, equipe com criação/revogação e consultas autorizadas. Decisão visual: verde escuro, fundos claros e seletor explícito de espaço; conferida interface desktop e celular.
- Implementados receitas/despesas, datas, pendências, histórico com busca, cartões, faturas, parcelas, orçamento individual, avisos e dashboard com mês de caixa, gráfico interativo e tabela acessível.
- Texto rápido gera somente rascunho; formato de dinheiro brasileiro, datas explícitas/hoje/ontem/amanhã e rejeição de valores negativos ou múltiplos. Confirmação idempotente evita duplicidade.
- Regras delegadas: compra no dia do fechamento entra no próximo ciclo; dias inexistentes ajustados; parcelas somam o total em centavos. Pagamento de fatura baixa as parcelas uma única vez sem criar despesa adicional. Anular erro corrige registro incorreto e mantém evento; reembolso efetivo deve ser registrado como entrada, sem automação de devolução.
- Integração Power BI: credenciais Basic dedicadas com hash, 90 dias, revogação e autorização reavaliada; API somente GET paginada. Testes locais passaram; Desktop/Service não foram conectados nem o refresh comprovado.
- IA: resumo determinístico identificado como modo por regras e protocolo de provedor preparado; nenhuma chamada externa, chave ou contratação.
- Criado iniciador local e proprietário com senha aleatória exclusiva, guardada somente na pasta privada ignorada. Sem dados financeiros reais ou exemplos financeiros no banco de uso.
- Testes finais: 64 passaram; Ruff, Django check, migrações sem drift e sintaxe JS passaram. A interface de texto foi verificada sem salvar gasto fictício no banco do proprietário.
- Plugin GitHub conectado e perfil confirmado. Consulta ao repositório pretendido não encontrou repo acessível; navegador em criação de repo exigiu login, sem credencial CLI disponível. Railway foi oferecida como integração, mas ainda não está conectada. Não houve publicação ou cobrança.
- README, relatório e tarefa atualizados; ZIP apenas de fonte, sem bancos, senhas, .env, .local, .venv ou Git.

## Conexão GitHub confirmada

A instalação/conexão GitHub foi confirmada. O repositório público poupa-grana está acessível e contém um README inicial. O remoto foi conectado e seu commit inicial foi preservado como base da branch de entrega. Os commits locais anteriores continuam preservados em suas branches. A publicação seguirá por PR, sem enviar bancos, segredos ou runtime. Railway permanece pendente de conexão.
