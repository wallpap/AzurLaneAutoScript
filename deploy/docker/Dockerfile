# docker build -t hgjazhgj/alas:latest .
# docker run -v ${PWD}:/app/AzurLaneAutoScript -p 22267:22267 --name alas -it --rm hgjazhgj/alas

FROM python:3.8-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /usr/local/bin/uv

ENV UV_PROJECT_ENVIRONMENT=/opt/alas-venv \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/opt/alas-venv/bin:$PATH"

WORKDIR /app/AzurLaneAutoScript

COPY pyproject.toml uv.lock .python-version ./

RUN apt update \
 && apt install -y git adb libgomp1 openssh-client libgl1 libglib2.0-0 \
 && git config --global --add safe.directory '*' \
 && uv sync --locked --no-dev \
 && uv cache clean \
 && rm -rf /var/lib/apt/lists/*

CMD ["uv", "run", "--locked", "--no-dev", "python", "gui.py"]
