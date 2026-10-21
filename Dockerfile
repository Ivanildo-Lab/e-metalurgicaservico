# =====================================================================
# Dockerfile para Django + MySQL  (MODELO para os 14 apps que usam MySQL)
# App: e-metalurgicaservicos  —  Django 5.2, MySQL via mysqlclient
# Settings: core.settings   |   WSGI: core.wsgi:application
#
# DIFERENÇA vs. e-cobrança (Supabase/Postgres):
#   - O mysqlclient NÃO tem wheel manylinux, então precisa compilar (build stage).
#   - O settings lê DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT (não DATABASE_URL).
# =====================================================================

# ---------------------- Estágio de BUILD (compila o mysqlclient) -----
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# Dependências de compilação do mysqlclient (headers do MySQL/MariaDB + gcc + pkg-config)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
# Instala tudo num prefixo temporário para copiar só as libs pro estágio final
RUN pip install --prefix=/install -r requirements.txt

# ---------------------- Estágio FINAL (leve) ------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Apenas a lib de RUNTIME do MySQL (a que o mysqlclient foi compilado contra).
# Mantém a imagem pequena sem levar o toolchain de compilação pra produção.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

# Copia as dependências Python instaladas no estágio de build
COPY --from=builder /install /usr/local

# Copia o código do projeto
COPY . .

# Diretórios de mídia (vira volume) e estáticos (gerados no collectstatic)
RUN mkdir -p media staticfiles

EXPOSE 8000

# Inicialização: migrations -> collectstatic -> gunicorn (core.wsgi)
# Workers configuráveis (padrão 2, por serem 15 apps no mesmo VPS)
CMD ["sh", "-c", "\
    python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    gunicorn core.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers ${GUNICORN_WORKERS:-2} \
      --timeout ${GUNICORN_TIMEOUT:-60} \
      --access-logfile - \
      --error-logfile -"]
