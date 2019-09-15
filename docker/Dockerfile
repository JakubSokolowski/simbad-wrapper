FROM python:3.6-alpine3.7

WORKDIR /usr/simbad-server/app
RUN apk add --update gcc libc-dev fortify-headers linux-headers && rm -rf /var/cache/apk/

RUN pip install --upgrade pip

COPY ./docker/requirements.txt /usr/simbad-server/app
RUN pip install -r /usr/simbad-server/app/requirements.txt

COPY ./src/server /usr/simbad-server/app/server
COPY ./src/entrypoint_api.py /usr/simbad-server/app
COPY ./src/entrypoint_celery.py /usr/simbad-server/app
