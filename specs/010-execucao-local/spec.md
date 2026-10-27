# Feature 010 — Execução só com Python

**Origem**: pedido do cliente ("fazer funcionar apenas com Python na máquina, sem Docker, mas mantendo o Docker") · **Contrato**: `docs/arquitetura.md` v1.2, "Execução local só com Python (010)".

## História
Como avaliador, quero rodar o Consus num computador que só tem Python, com poucos comandos,
e levar o projeto (e os dados) para outra máquina.

## Requisitos
- **FR-001** `requirements.txt` e `requirements-dev.txt` são exportados do `uv.lock`, e um teste confere as versões.
- **FR-002** `requires-python >= 3.11` e Ruff `py311`. A imagem Docker continua em 3.13, e a suíte passa em 3.11, 3.12 e 3.13.
- **FR-003** `iniciar.py` usa só a biblioteca padrão e funciona em Windows, macOS e Linux. Ele:
  - confere a versão do Python e se o Django está instalado;
  - usa SQLite sem `DATABASE_URL`;
  - roda `migrate`, `popular_demo` na primeira vez (`--sem-demo` pula), `garantir_usuario` (admin / `CONSUS_SENHA` ou `consus`) e `runserver`.
- **FR-004** `--porta`, `--host` e `--help`.
- **FR-005** O README ganha as seções "Rodar só com Python" (PowerShell e bash), "Levar para outra máquina", "Usar PostgreSQL sem Docker" e "Paleta de cores". O Docker continua sendo o caminho principal.

Verificação manual feita: venv limpo com Python 3.11 → `pip install -r requirements-dev.txt` → suíte verde; `python iniciar.py` numa cópia limpa → login 200, painel 302 (exige login).
