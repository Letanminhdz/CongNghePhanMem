FROM python:3.10

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend

WORKDIR /app/

# Copy requirements and install
COPY ./backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY ./backend/scripts /app/backend/scripts
COPY ./backend/alembic.ini /app/backend/
COPY ./backend/app /app/backend/app

WORKDIR /app/backend/

CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
