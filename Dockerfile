# syntax=docker/dockerfile:1
FROM ghcr.io/secorolab/floorplan-dsl:devel AS dsl

FROM ghcr.io/secorolab/scenery_builder:devel

# Install FloorPlan DSL from base image
WORKDIR /tmp/floorplan-dsl
COPY --from=dsl /usr/src/app .
RUN pip install . -t /usr/src/app/modules

# New requirements for Kafka script
RUN pip install confluent-kafka requests dotenv -t /usr/src/app/modules
COPY floorplan_consumer.py /usr/src/app/

WORKDIR /usr/src/app/

ENTRYPOINT []
CMD ["blender", "-b", "--python", "/usr/src/app/floorplan_consumer.py"]
