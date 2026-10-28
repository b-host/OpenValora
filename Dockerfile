# Dockerfile para OpenValora
# Utiliza uv para instalação ultrarrápida de dependências

FROM python:3.11-slim

# Instala a ferramenta UV oficial da Astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Configurações de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    DOCKER_CONTAINER=1

WORKDIR /app

# Instala dependências do sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivos de requisitos e instala com uv
COPY requirements.txt pyproject.toml ./
RUN uv pip install --system --no-cache -r requirements.txt

# Copia o código-fonte da aplicação
COPY app/ ./app/
COPY sample_data/ ./sample_data/
COPY var_catalog.json OpenValora.png ValoraOpen.png main.py ./

# Porta padrão de acesso web
EXPOSE 8000

# Executa em modo servidor local
CMD ["python3", "main.py", "--server", "--host", "0.0.0.0", "--port", "8000"]
