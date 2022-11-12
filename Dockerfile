FROM python:3.9-slim-buster

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && apt-get install -y --no-install-recommends gcc \
    && apt-get purge -y --auto-remove

COPY ./server.py /app
COPY requirements.txt /app

RUN python -m pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "80"]