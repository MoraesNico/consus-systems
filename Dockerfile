# syntax=docker/dockerfile:1.7
# Consus — imagem multi-estágio (research R4): base → testes | producao.

# ---------- base: dependências de produção em /opt/venv ----------
FROM python:3.13-slim-bookworm AS base
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
# Segredo opcional "ca_bundle": builds atrás de proxy corporativo com CA própria
#   docker build --secret id=ca_bundle,src=/caminho/ca.crt .
RUN --mount=type=secret,id=ca_bundle,required=false \
    --mount=type=cache,target=/root/.cache/uv \
    if [ -s /run/secrets/ca_bundle ]; then export SSL_CERT_FILE=/run/secrets/ca_bundle; fi; \
    uv sync --frozen --no-dev --no-install-project

# ---------- testes: base + grupo dev (serviço "testes" do Compose) ----------
FROM base AS testes
RUN --mount=type=secret,id=ca_bundle,required=false \
    --mount=type=cache,target=/root/.cache/uv \
    if [ -s /run/secrets/ca_bundle ]; then export SSL_CERT_FILE=/run/secrets/ca_bundle; fi; \
    uv sync --frozen --no-install-project
COPY . .
CMD ["pytest"]

# ---------- producao: código + estáticos com hash + usuário sem privilégios ----------
FROM base AS producao
RUN groupadd --system --gid 1000 consus \
    && useradd --system --uid 1000 --gid consus --home-dir /app --no-create-home consus
COPY --chown=consus:consus . .
RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput \
    && chmod +x entrypoint.sh
USER consus
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "-"]
