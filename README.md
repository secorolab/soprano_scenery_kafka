# soprano_scenery_kafka

At the root of this repository you should create an `.env` file that contains the login information for Kafka.

The consumer listens to the `floorplan-model` topic, generates the corresponding artefacts, and publishes their path in the server in the `scenery-artefacts` topic.

## Requirements

This assumes you have a local installation of the [FloorPlan DSL](https://github.com/secorolab/FloorPlan-DSL) and the [scenery_builder](https://github.com/secorolab/scenery_builder).

You'll also need to install Confluent Kafka and other requirements:

```bash
pip install confluent-kafka requests dotenv

```

## Running 

After activating your virutal environment, simply run the floorplan consumer:

```bash
python floorplan_consumer.py
```

The `floorplan_bim_producer.py` and `artefact_consumer.py` are mockup scripts to test subscribing and publishing to the Kafka topics.


### Using Docker

After building or pulling the Docker image, just run a container. The default `CMD` is already set for the Kafka consumer. 
You should use the argument `--env-file` to pass the path of the `.env` file containing the credentials to login and URLs, for example:

```bash
docker run --env-file .env -it mat_kafka:latest
```

The [Dockerfile](Dockerfile) uses the images of the development branch of the two map components. The images are built as part of the CI and hosted on GitHub. 

