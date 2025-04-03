# soprano_scenery_kafka

At the root of this repository you should create an `.env` file that contains the login information for Kafka.

The consumer listens to the `floorplan-model` topic, generates the corresponding artefacts, and publishes their path in the server in the `scenery-artefacts` topic.

## Requirements

This assumes you have a local installation of the [FloorPlan DSL]() and the [scenery_builder]().

You'll also need to install Confluent Kafka:

```bash
pip install confluent-kafka

```

## Running 

After activating your virutal environment, simply run the floorplan consumer:

```bash
python floorplan_consumer.py
```

The `floorplan_bim_producer.py` and `artefact_consumer.py` are mockup scripts to test subscribing and publishing to the Kafka topics.
