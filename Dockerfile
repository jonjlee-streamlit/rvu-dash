ARG PYTHON_VERSION=3.10-slim-buster

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /code
WORKDIR /code
COPY . /code

RUN apt-get update && apt-get install -y \
    curl

RUN set -ex && \
    pip install --upgrade pipenv && \
    pip install --upgrade pip && \
    pipenv install --deploy && \
    rm -rf /root/.cache/

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

CMD ["pipenv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]