FROM python:2.7-alpine3.7

RUN apk add --no-cache bash

MAINTAINER Flywheel <support@flywheel.io>

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}RUN mkdir -p ${FLYWHEEL} \
    && useradd --no-user-group --create-home --shell /bin/bash flywheel
COPY manifest.json ${FLYWHEEL}/manifest.json
COPY task_gen.py ${FLYWHEEL}/task_gen.py

WORKDIR $FLYWHEEL