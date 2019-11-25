FROM jsokolowski/pipeline-base:debian-edge
RUN pip install redis
RUN conda install -c conda-forge python-igraph
COPY ./src /usr/simbad-server/app

COPY --from=jsokolowski/simbad-cli:gcc /code/build/cli/SimBaD-cli /simbad-cli