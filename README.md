# MH-MR Architecting Tools Kafka interface

This repository contains the Kafka interface for the MH-MR Architecting tools components. 
It is recommended to use [Docker](#using-docker) for the deployment, as this takes care of the setup of the MAT components.

> [!NOTE]  
> This README documents the Kafka interface only. 
> If you are running the MAT components in a standalone mode and for component-specific information, please see the respective links for the documentation of the [FloorPlan DSL](https://secorolab.github.io/FloorPlan-DSL/) and the [scenery_builder](https://secorolab.github.io/scenery_builder/).

The Kafka interface is a Kafka consumer that listens to the `floorplan-model` topic, generates the corresponding artefacts, and publishes their path in the server in the `scenery-artefacts` topic.
As the interface currently doesn't allow to specify which artefacts to generate, we have added support for the following basic artefacts: 

| Artefact            | Inputs                    |
|---------------------|---------------------------|
|                     | **FloorPlan Model (FPM)** |
| Occupancy grid      | X                         |
| 3D Mesh             | X                         |
| Gazebo world/models | X                         |

Other artefacts supported by the `scenery_builder` can be added upon request.

## Local development
At the root of this repository you should create an `.env` file that contains the login information for Kafka.

### Requirements

This assumes you have a local installation of the [FloorPlan DSL](https://github.com/secorolab/FloorPlan-DSL) and the [scenery_builder](https://github.com/secorolab/scenery_builder).

You'll also need to install Confluent Kafka and other requirements:

```bash
pip install confluent-kafka requests dotenv

```

### Running

After activating your virtual environment and [configuring](#configuration) the interface, simply run the floorplan consumer:

```bash
python floorplan_consumer.py
```

The `floorplan_bim_producer.py` and `artefact_consumer.py` are mockup scripts to test subscribing and publishing to the Kafka topics.


## Configuration

We have included a sample [config](config.toml) file to parametrize the generation of artefacts.

### `.env` file

Create an `.env` file to store your credentials and the relevant API endpoints, for example:

```dotenv
KAFKA_USER=myuser
KAFKA_PASS=12345pass
KAFKA_URL=kafka-url:9000
REST_UPLOAD_ARTEFACT_URL=http://server-url:8000/api/upload/artefact
```

## Using Docker

After building or [pulling the Docker image](https://github.com/SOPRANO-Project/MH-MR-ArchitectingTools/pkgs/container/mh-mr-architectingtools), just run a container. 
The default `CMD` is already set for the Kafka consumer. 
You should use the argument `--env-file` to pass the path of the `.env` file containing the credentials to login and URLs (see [Configuration](#configuration)), for example:

```bash
docker run --env-file .env -it mat_kafka:latest
```

The [Dockerfile](Dockerfile) uses the images of the development branch of the two floorplan components. The images are built as part of the CI and hosted on GitHub. 
