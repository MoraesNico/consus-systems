# Feature 006 — Login interativo

**Origem**: pedido do cliente junto ao Passo 3 · **Contrato**: `docs/arquitetura.md` v1.2, "Autenticação"; constituição 1.1.0, princípio VI.

## História
Como responsável pelo sistema, quero que só pessoas autorizadas vejam o estoque e o financeiro,
entrando por uma tela de login agradável e segura.

## Requisitos
- **FR-001** Todas as páginas exigem login (`LoginObrigatorioMiddleware`). Um anônimo é redirecionado (302) para `/contas/entrar/?next=…`.
- **FR-002** Uma requisição HTMX anônima recebe `HX-Redirect` para o login, preservando a URL atual.
- **FR-003** Só `/contas/entrar/` e `/saude/` são públicas. A tela de login tem layout próprio, sem navegação.
- **FR-004** O erro é sempre genérico: "Usuário ou senha incorretos." (422), inclusive para usuário inativo.
- **FR-005** O `next` é validado (sem redirecionamento aberto). "Manter conectado" estende a sessão a 14 dias; sem ele, a sessão expira ao fechar o navegador. A boas-vindas vira toast.
- **FR-006** Com HTMX, o login bem-sucedido responde `HX-Redirect`. O erro troca só o cartão, que treme.
- **FR-007** Após 5 falhas em 15 min por usuário (ou 20 por IP), novas tentativas recebem 429 "Muitas tentativas. Tente novamente em N min."
- **FR-008** O login bem-sucedido apaga as falhas daquele usuário.
- **FR-009** Sair só por POST.
- **FR-010** Troca de senha com os validadores do Django.
- **FR-011** `manage.py garantir_usuario` (ou `CONSUS_USUARIO`/`CONSUS_SENHA` no entrypoint) cria o usuário sem nunca trocar a senha de um existente.
- **FR-012** Movimentações gravam `registrado_por`, e o histórico financeiro mostra quem registrou.
- **FR-013** No modo demonstração, a tela de login dá a dica do usuário sem exibir a senha.

Interatividade: mostrar/ocultar senha (`aria-pressed`), aviso de Caps Lock, botão "Entrando…", cartão animado e menu do usuário com Trocar senha e Sair.
