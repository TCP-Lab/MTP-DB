# syntax=docker/dockerfile:1

FROM python:3 AS base

WORKDIR /app

RUN mkdir ./out

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

FROM base AS test
CMD [ "python", "-m", "pytest", "-s", "./daedalus" ]

FROM base AS production
CMD [ "python", "-m", "daedalus" ]
