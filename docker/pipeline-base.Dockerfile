FROM continuumio/miniconda3:4.7.12
RUN apt-get update && apt-get install -y libboost-program-options-dev libc-dev libc6 libstdc++6
WORKDIR /usr/simbad-server/app
COPY ./docker/conda-req.txt /usr/simbad-server/app
RUN conda install -c conda-forge --file /usr/simbad-server/app/conda-req.txt
RUN pip install redis reportlab
COPY --from=simbadbot/simbad /SimBaD/SimBaD-cli /simbad-cli
