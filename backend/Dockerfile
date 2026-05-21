FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY life_os_alembic ./life_os_alembic
COPY alembic.ini .
COPY life_os_alembic.ini .
COPY start.sh start-worker.sh start-beat.sh ./
RUN chmod +x start.sh start-worker.sh start-beat.sh

CMD ["./start.sh"]
