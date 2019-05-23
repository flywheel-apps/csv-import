FROM python:3.7.3-alpine3.9
MAINTAINER Flywheel <support@flywheel.io>
ENV FLYWHEEL /flywheel/v0
WORKDIR ${FLYWHEEL}

RUN apk add --no-cache bash zip
ENTRYPOINT ["bash"]

RUN pip install \
    chardet==3.0.4 \
    flywheel-sdk==8.1.2

COPY manifest.json run.py ${FLYWHEEL}/
