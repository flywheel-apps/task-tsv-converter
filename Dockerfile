FROM python:2.7-alpine3.7

RUN apk add --no-cache bash

MAINTAINER Flywheel <support@flywheel.io>

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY manifest.json ${FLYWHEEL}/manifest.json
COPY task_gen.py ${FLYWHEEL}/task_gen.py
ADD tests ${FLYWHEEL}