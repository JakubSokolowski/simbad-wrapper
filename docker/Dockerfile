FROM jsokolowski/pipeline-base:debian-edge
RUN pip install redis

COPY ./src /usr/simbad-server/app

COPY --from=jsokolowski/simbad-cli:gcc /code/build/cli/SimBaD-cli /simbad-cli