# syntax=docker/dockerfile:1
FROM ghcr.io/secorolab/scenery_builder:devel

WORKDIR /app

USER root
RUN --mount=type=cache,target=/root/.cache/pip
RUN python -m pip install confluent-kafka requests dotenv

RUN addgroup --gid 1000 soprano
RUN adduser -G soprano -h /home/appuser -D appuser

USER appuser
WORKDIR /home/mat
COPY floorplan_consumer.py .
COPY config.toml .
RUN touch mat.log

ENTRYPOINT []
CMD ["python", "floorplan_consumer.py"]
