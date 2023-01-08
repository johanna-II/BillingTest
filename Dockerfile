FROM  python:3.8-slim-buster

USER root
RUN apt-get update && \
apt-get install python3-dev default-libmysqlclient-dev \
build-essential libffi6 -y

# pip upgrade and install poetry
RUN pip install --upgrade pip
RUN pip install poetry

# install packages via poetry
COPY poetry.lock ./poetry.lock
COPY pyproject.toml ./pyproject.toml
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction
