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

## Abrir neste computador

Execute `iniciar.cmd` na raiz. Ele usa .venv e, quando presente, o PostgreSQL portátil em .local, sem instalar serviço Windows e escutando somente em 127.0.0.1:55432.

URL: http://127.0.0.1:5089 . O primeiro usuário local e sua senha aleatória estão em `.local/ACESSO.txt`, ignorado pelo Git. Não compartilhe esse arquivo nem o .env. Não existe senha padrão no código. O proprietário local não é superusuário Django; sua autoridade é definida pela propriedade dos espaços.

Encerre com Ctrl+C. Se o iniciador tiver iniciado o cluster portátil, ele o para ao encerrar. Se o cluster já estava ativo, ele é preservado. Não apague .local/pg-data: essa pasta contém seus dados locais.

## Instalar em outro computador

Requisitos: Python 3.12, PostgreSQL 17 e PowerShell. Baixe PostgreSQL pela página oficial: https://www.postgresql.org/download/windows/ . A distribuição ZIP do código não inclui binários, banco ou credenciais deste computador.

```powershell
py -3.12 -m venv .venv
& ./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Gere uma chave de aplicação sem exibir no terminal:

```powershell
$financeKey = & ./.venv/Scripts/python.exe -c 'import secrets; print(secrets.token_urlsafe(64))'
$financeEnv = Get-Content .env -Raw
$financeEnv.Replace('SECRET_KEY=', "SECRET_KEY=$financeKey") | Set-Content -Encoding utf8 .env
Remove-Variable financeKey,financeEnv
```

No PostgreSQL local, usando psql como administrador, crie bancos e papéis exclusivos. Senhas são solicitadas interativamente; os nomes abaixo são fictícios. Se existirem, confira sua origem antes de reutilizar. Não apague banco alheio.

```sql
CREATE ROLE poupa_local LOGIN;
\password poupa_local
CREATE DATABASE poupa_grana_local OWNER poupa_local;
CREATE ROLE poupa_test LOGIN CREATEDB;
\password poupa_test
CREATE DATABASE poupa_grana_ci OWNER poupa_test;
```

Edite .env localmente: preencha DATABASE_URL (banco local) e TEST_DATABASE_URL (banco de teste) com os papéis e senhas definidos; faça o escape de caracteres especiais da URL. As credenciais em .env.example são exemplos e não concedem acesso. Apenas o papel de teste precisa de CREATEDB.

```powershell
& ./.venv/Scripts/python.exe manage.py migrate
& ./.venv/Scripts/python.exe manage.py bootstrap_owner
& ./.venv/Scripts/python.exe scripts/run_local.py
```

bootstrap_owner é interativo, valida a senha sem imprimi-la e cria os espaços. Recusa alterar uma instalação com usuários existentes. Para mudar a própria senha em uma instalação local administrada pelo proprietário, use o comando interativo padrão `manage.py changepassword`.

## Verificações

```powershell
& ./.venv/Scripts/python.exe -m ruff check .
& ./.venv/Scripts/python.exe manage.py check
& ./.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
$env:DJANGO_SETTINGS_MODULE = 'config.settings.test'
& ./.venv/Scripts/python.exe -c 'from dotenv import load_dotenv; load_dotenv(".env"); import pytest; raise SystemExit(pytest.main(["-p", "no:cacheprovider"]))'
Remove-Item Env:DJANGO_SETTINGS_MODULE
```

pytest cria/remove test_poupa_grana no servidor indicado por TEST_DATABASE_URL. Use um servidor descartável de desenvolvimento, nunca produção, sem testes concorrentes usando o mesmo nome. Os testes nunca usam DATABASE_URL como alternativa. Nenhum SQLite é usado.

/health/ retorna 200 somente se SELECT 1 funcionar; falhas retornam 503 sem detalhes internos. /admin/ não é exposto. O dashboard exige login.

## Decisões financeiras e limites

- O resultado mensal é receitas menos despesas pagas, não saldo bancário completo. Não há integração bancária ou saldo inicial de contas nesta versão.
- Pendências usam vencimento; caixa usa data efetiva do pagamento; competência usa a data da compra. Cartão só entra no caixa ao dar baixa na respectiva parcela/fatura.
- Compra no dia do fechamento entra no ciclo seguinte. Vencimentos em dias inexistentes são ajustados ao último dia do mês. Parcelas somam o total com distribuição determinística de centavos.
- “Anular erro” é uma correção de registro incorreto: remove seu efeito dos totais e mantém evento de auditoria. Não representa um reembolso bancário; para reembolso efetivamente recebido, registre a entrada correspondente identificando a origem. Não há transferência de dinheiro pelo aplicativo.
- Orçamentos são individuais por categoria; a visão do proprietário pode listar os de todos, sem confundir gastos de um com o limite de outro.
- Não há anexos, importação bancária, conciliação, notas fiscais, estoque ou recuperação de senha por e-mail. A entrada por regras não entende todas as frases; campos ambíguos exigem correção humana.
- As categorias iniciais são fixas. O assistente mostra apenas resumo calculado, sem recomendação de investimento e sem uso de provedor externo.

## Publicação e integrações externas

Existe Git próprio com commits locais e branches por etapa. O remoto público do Poupa Grana já está conectado; a plataforma está sendo enviada por PR e o resultado remoto do CI será registrado no relatório. Ainda não há deploy comprovado. O workflow GitHub Actions está pronto com Python 3.12, PostgreSQL e check lint-e-testes. Para publicar: criar/conectar repositório GitHub próprio, executar o CI e proteger main; em pedido próprio, configurar Railway, servidor WSGI, estáticos, proxy HTTPS, domínio, backups e Wait for CI. Não usar runserver em produção.

Configuração de produção exige SECRET_KEY forte, ALLOWED_HOSTS sem curingas e PostgreSQL com SSL explícito. A confiança em proxy só pode ser configurada após verificar o proxy da hospedagem. Gunicorn e WhiteNoise não estão instalados nesta etapa local. Não publicar esta configuração sem concluir essa preparação.

A API Power BI está testada localmente; o Desktop e o Power BI Service não foram conectados à conta do usuário. A atualização agendada depende de endereço HTTPS acessível, credenciais e teste no serviço. Não afirmar refresh on-line antes disso. O provedor de IA será habilitado em etapa própria, sem chaves no frontend.

## Referências

- Django: https://docs.djangoproject.com/en/5.2/faq/install/ e https://docs.djangoproject.com/en/5.2/topics/auth/default/
- Psycopg: https://www.psycopg.org/psycopg3/docs/basic/install.html
- pytest-django: https://pytest-django.readthedocs.io/en/latest/
- Ruff: https://docs.astral.sh/ruff/configuration/
- CI: https://docs.github.com/en/actions/tutorials/build-and-test-code/python
- Actions verificadas: https://github.com/actions/checkout e https://github.com/actions/setup-python (v7).
- Power BI: https://learn.microsoft.com/en-us/power-query/connectors/web/web
- Railway: https://docs.railway.com/guides/django e https://docs.railway.com/deployments/github-autodeploys
