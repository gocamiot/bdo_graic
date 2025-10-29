FROM python:3.8-slim

RUN apt-get update && \
    apt-get install -y git procps tesseract-ocr build-essential python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ARG GITHUB_USERNAME
ARG GITHUB_TOKEN

RUN python -m pip install --upgrade pip setuptools wheel

COPY ./requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

RUN mkdir /app

COPY ./ /app

WORKDIR /app

RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
