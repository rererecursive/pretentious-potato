FROM python:3.8-alpine

RUN apk update && apk add \
    npm \
    ruby

RUN gem install bundler

WORKDIR /app
RUN addgroup -S mygroup && adduser -S myuser -G mygroup -u 1000
USER myuser

COPY requirements.txt /app
RUN pip3 install -r /app/requirements.txt

COPY main.py install.sh /app/
