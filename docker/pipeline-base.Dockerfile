FROM python:3.7.5-alpine3.9

WORKDIR /usr/simbad-server/app
RUN apk update && apk upgrade
RUN apk add boost-program_options \
    gcc \
    libc-dev \
    libc6-compat \
    libstdc++ \
    fortify-headers \
    linux-headers \
    make \
    openssl-dev \
    libffi-dev \
    --repository=http://dl-cdn.alpinelinux.org/alpine/edge/main

RUN pip install --upgrade pip

COPY ./docker/requirements.txt /usr/simbad-server/app
RUN pip install -r /usr/simbad-server/app/requirements.txt