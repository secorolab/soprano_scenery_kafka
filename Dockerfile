# syntax=docker/dockerfile:1
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install -y software-properties-common git \
    python3 python3-pip \
    blender

# New requirements for Kafka script and scenery_builder
RUN pip install confluent-kafka requests dotenv git+https://github.com/secorolab/scenery_builder.git@devel -t /usr/src/app/modules --upgrade
COPY floorplan_consumer.py /usr/src/app/
COPY config.toml /usr/src/app/

ENV BLENDER_USER_SCRIPTS=/usr/src/app
WORKDIR /usr/src/app/

ENTRYPOINT []
CMD ["blender", "-b", "--python", "/usr/src/app/floorplan_consumer.py"]
