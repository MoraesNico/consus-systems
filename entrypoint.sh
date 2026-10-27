#!/bin/sh
# Prepara o banco antes de iniciar o servidor (FR-002/FR-003).
set -eu

tentativa=1
until python manage.py migrate --noinput; do
    if [ "$tentativa" -ge 15 ]; then
        echo "entrypoint: migrate falhou após 15 tentativas; encerrando." >&2
        exit 1
    fi
    echo "entrypoint: banco indisponível (tentativa $tentativa/15); nova tentativa em 2 s." >&2
    tentativa=$((tentativa + 1))
    sleep 2
done

if [ "${CONSUS_POPULAR_DEMO:-0}" = "1" ] && python manage.py help popular_demo >/dev/null 2>&1; then
    python manage.py popular_demo
fi

if [ -n "${CONSUS_USUARIO:-}" ] && [ -n "${CONSUS_SENHA:-}" ]; then
    python manage.py garantir_usuario
fi

exec "$@"
