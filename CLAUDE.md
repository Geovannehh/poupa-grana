# Poupa Grana — regras de desenvolvimento

## Contexto e leitura

O proprietário define o escopo e autoriza merge. A conversa de análise prepara pedidos, verifica diffs/CI e registra decisões. O programador executa o pedido atual. Não pressupor que outra ferramenta ou agente tem autorização adicional.

Leia task.md, o pedido apontado, estrutura.md e docs/conversa-abertura.md antes de editar. Confirme o estado real e os arquivos por conteúdo; não invente resultados, commits, PRs ou CI. Se estiver sem remoto/acesso, complete o trabalho local possível e reporte precisamente a pendência.

## Regras de ouro

- Uma tarefa, um assunto; sem refatorações ou dependências fora do pedido. Decisões simples e reversíveis podem ser resolvidas e reportadas; ambiguidades de regra financeira precisam de definição antes do código dependente.
- Dados de demonstração fictícios; nenhum dado pessoal real, extrato, segredo, banco local ou credencial em Git, logs, screenshots e PRs. Nunca reutilizar credenciais de outro projeto. Não solicitar senhas pelo chat.
- Django + PostgreSQL. Não usar SQLite como substituto silencioso. Modelo User próprio antes da primeira migração.
- Consultas e mutações exigem autorização de usuário/espaço no servidor. Reutilizar a política em API, dashboard, assistente e exportação. Valores Decimal, transações atômicas e idempotência nas operações financeiras.
- Não acessar produção ou painel de hospedagem dentro de um pedido de código. A tarefa de hospedagem será separada. Não contratar ou publicar sem escopo/autorização correspondente.
- Não apresentar regras como IA nem declarar integração externa concluída sem evidência. Nunca salvar decisão da IA sem revisão humana.
- Antes de telas novas ou alterações visuais, apresentar resultado esperado ao proprietário. No pedido inicial, sem tela de produto.

## Git e CI

Primeiro confira se a pasta pertence a repositório próprio ou a repositório pai. Não tocar no Git de outros projetos. Main aceita PR com check lint-e-testes; sem force push e sem exclusão. Exceção: primeiro commit mínimo de bootstrap, quando autorizado, pois ainda não há main.

Uma branch por assunto, criada da main atualizada, um PR. Não fazer merge sem pedido explícito do proprietário. Se autorizado, verificar novamente CI e head do PR, fazer merge commit sem squash, atualizar main local, conferir igualdade com remoto e limpar branches do assunto sem apagar trabalho alheio. Nunca forçar merge recusado. Deploy automático só depois do CI; não executar deploy manual. Reversão com git revert.

Proteger main após a primeira execução do check. Não declarar proteção ativada sem verificar no GitHub. Não inventar URL de remoto ou PR.

## Testes e verificações

Testar regras financeiras e limites de acesso (incluindo dois membros e espaço pessoal). Usar banco temporário PostgreSQL e credenciais de teste fictícias. Novos testes de regressão precisam demonstrar falha no defeito e sucesso na correção quando aplicável; base nova sem comportamento anterior deve declarar esse limite.

Rodar testes do assunto durante a implementação, suíte completa uma vez no fechamento e ruff. Falha deve ser reportada e corrigida no escopo; não desabilitar testes nem usar xfail para ocultar defeito. Problemas fora do pedido são registrados sem correção não autorizada. Verificação visual não substitui teste de autorização.

Conferir o conteúdo efetivamente gravado, não apenas tamanho. Executar git status e git diff --stat antes de reportar. Encerrar processos temporários próprios. Não apagar dados ou processos alheios.

## Relatório local

Sobrescrever RELATORIO.md com: (1) divergências; (2) PR, commit, CI e arquivos com justificativas; (3) antes/depois; (4) contagem e resultados de testes/lint e limites de verificação; (5) comandos PowerShell para reprodução; (6) achados fora do escopo; (7) correções durante a execução. Terminar com “Aguardo sua conferência antes do merge.” Se não houver PR, explicar o bloqueio real, sem inventar link.

/task.md, /RELATORIO.md e /pedidos/ ficam ignorados no Git. Atualizar registro da conversa nos avanços relevantes, distinguindo decisão do usuário de proposta técnica. Não realizar publicação nem criação de repositório nesta etapa de documentação.
