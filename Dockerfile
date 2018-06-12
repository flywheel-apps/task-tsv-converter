FROM python:2.7-alpine3.7

MAINTAINER Flywheel <support@flywheel.io>

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run ${FLYWHEEL}/run
COPY manifest.json ${FLYWHEEL}/manifest.json

# Set the entrypoint
ENTRYPOINT ["/flywheel/v0/run"]
