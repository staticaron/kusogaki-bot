FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libraqm0 \
    libharfbuzz0b \
    libfribidi0 \
    libfreetype6 \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv pip install --system -r pyproject.toml

COPY . .

CMD ["python", "main.py"]
