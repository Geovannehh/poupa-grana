# Railway — preparação da produção

Preparação em branch/PR próprio; não comprova serviço criado ou deploy. A plataforma financeira está na main com CI obrigatório. O perfil Railway é separado do local.

## Fonte e build

Conectar repositório poupa-grana, branch main; ativar Wait for CI. Dockerfile na raiz instala somente runtime de produção, usa usuário sem root e respeita PORT. Gunicorn serve WSGI; WhiteNoise serve estáticos versionados/comprimidos; collectstatic ocorre no início do container com ambiente válido. Nenhum segredo é necessário para construir a imagem, e .dockerignore exclui .env/.local/.venv/Git e dados.

Não foi criado railway.json/toml: documentação consultada em 29/10/2026 informa que Config as Code é obsoleto para serviços novos. Usar as configurações nativas do serviço ou a infraestrutura como código atual após verificar a documentação vigente.

## Serviço e banco

Criar projeto próprio Poupa Grana e PostgreSQL de produção separado. App e banco na mesma região. O app não precisa de volume persistente: finanças ficam no PostgreSQL. Banco deve ter volume e backups configurados/verificados na plataforma; não declarar backup pronto apenas por criar um banco. Não importar o banco de desenvolvimento.

Configurar por ambiente na plataforma (nunca no Git):
- DJANGO_SETTINGS_MODULE=config.settings.railway.
- SECRET_KEY: gerar valor único forte na hospedagem, mínimo 50 caracteres.
- DATABASE_URL: referência ao serviço PostgreSQL, com sslmode=require ou verificação de certificado suportada. Verificar URL e SSL do banco efetivamente criado antes de montar a referência.
- ALLOWED_HOSTS: hostname público exato, sem esquema, caminho ou curinga. healthcheck.railway.app é adicionado somente pelo perfil Railway.
- BOOTSTRAP_OWNER_USERNAME e BOOTSTRAP_OWNER_PASSWORD: primeiro acesso, gerado e guardado pelo proprietário na hospedagem. Nunca reutilizar senha do desenvolvimento ou colocá-la no chat. Remover após a primeira inicialização bem-sucedida.
- PORT: fornecido pela Railway; WEB_CONCURRENCY opcional entre 1 e 8 (padrão 2).

Pre-deploy, em ordem: `python manage.py migrate --noinput` e `python manage.py initialize_owner`. Esse comando usa lock transacional PostgreSQL, cria um único proprietário sem permissão global de superusuário e não altera senhas/usuários em deploys posteriores. Sem variáveis e sem usuários, falha de forma explícita em vez de permitir cadastro público de administrador.

Start: Dockerfile já usa `python scripts/start_production.py`.
Healthcheck: `/health/`, porta PORT, timeout sugerido 120 s. Requer banco acessível. Essa rota técnica mínima é a única dispensada do redirecionamento HTTPS para permitir a verificação interna. O restante usa HTTPS e cookies seguros.

O perfil Railway confia em X-Forwarded-Proto exclusivamente porque a documentação do proxy público informa que o header indica https. Não usar esse perfil atrás de proxy desconhecido. O healthcheck tem host exato e não libera wildcard para toda railway.app.

## Validação antes de declarar publicação

1. CI da main verde e Wait for CI confirmado no serviço; não fazer deploy manual de revisão sem CI.
2. Build e pre-deploy concluídos; migrações e bootstrap sem segredos nos logs.
3. /health/ HTTPS retorna 200 com corpo mínimo; HTTP da aplicação redireciona para HTTPS.
4. /entrar/ e CSS/JS funcionam com DEBUG=False; cookies seguros; Host alheio recusado.
5. Proprietário entra e tem os dois espaços; membro não vê pessoal ou dados de colegas.
6. Produção começa sem registros financeiros fictícios. Remover variáveis de bootstrap; testar backup e recuperação antes de inserir dados relevantes.
7. Só então configurar Power BI com o endereço HTTPS e comprovar refresh no Desktop/Service. IA externa continua sem provedor, como decidido.

## Referências oficiais consultadas

- https://docs.railway.com/config-as-code
- https://docs.railway.com/deployments/healthchecks
- https://docs.railway.com/deployments/pre-deploy-command
- https://docs.railway.com/networking/public-networking/specs-and-limits
- https://docs.railway.com/deployments/github-autodeploys
- https://whitenoise.readthedocs.io/en/stable/django.html
- https://gunicorn.org/run/
