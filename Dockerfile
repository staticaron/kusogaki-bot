FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false

RUN poetry install --no-dev

COPY . .

ENV TOKEN=${TOKEN}
ENV STAFF_ROLE_ID=${STAFF_ROLE_ID}
ENV DB_HOST=${DB_HOST}
ENV DB_PORT=${DB_PORT}
ENV DB_PASSWORD=${DB_PASSWORD}

CMD ["python", "main.py"]