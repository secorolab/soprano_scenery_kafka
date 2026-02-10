#!/usr/bin/env python
import os
import subprocess
from zipfile import ZipFile
import glob
import logging

import requests
from fpm.generators.scenery import generate_fpm_rep_from_rdf

from textx import generator_for_language_target, metamodel_for_language
from confluent_kafka import Consumer, Producer
from dotenv import load_dotenv
from ifcld.transformations import transform_ifc_to_jsonld

logger = logging.getLogger("mat.kafka_consumer")
logger.setLevel(logging.DEBUG)

load_dotenv()

BASIC_CONFIG = {
    # User-specific properties that you must set
    "bootstrap.servers": "kafka-soprano.atb-bremen.de:9094",
    "sasl.username": os.getenv("KAFKA_USER"),
    "sasl.password": os.getenv("KAFKA_PASS"),
    # Fixed properties
    "security.protocol": "SASL_SSL",
    "sasl.mechanisms": "PLAIN",
}

CONSUMER_CONFIG = {
    # Fixed properties
    "group.id": "my-super-group",
    "auto.offset.reset": "earliest",
}

PRODUCER_CONFIG = {
    "acks": "all",
}


def delivery_callback(err, msg):
    if err:
        logger.error("Message failed delivery: {}".format(err))
    else:
        logger.debug(
            "Sent message: {timestamp}, {value}".format(
                timestamp=msg.timestamp(), value=msg.value().decode("utf-8")
            )
        )


def publish_artefacts_url(config, scenery_id, url, description=None, use_case="KUKA"):
    if description is None:
        description = "Artefacts for a {} floor plan for the {} early prototype".format(
            scenery_id, use_case
        )
    topic = "scenery-artefacts"

    producer = Producer(config)

    headers = {
        "title": "{} environment".format(scenery_id),  # Descriptive for the GUI
        "description": description,
        "use_case": use_case,
        "content-type": "application/zip",
    }

    producer.produce(
        topic, key=scenery_id, value=url, headers=headers, callback=delivery_callback
    )
    producer.flush()


def get_floorplan_model(url):
    response = requests.get(url, stream=True)
    logger.debug(
        "Response status code: %s. Headers: %s", response.status_code, response.headers
    )

    model_file_path = os.path.basename(url)

    with open(model_file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=128):
            f.write(chunk)

    logger.debug("Download finished")
    logger.debug("Model file path: {}".format(model_file_path))
    return model_file_path


def upload_artefacts_to_server(file_path):
    url = os.getenv("REST_UPLOAD_ARTEFACT_URL")
    files = {"zipFile": open(file_path, "rb")}

    response = requests.post(url, files=files)
    logger.debug(
        "Response status code: %s. Headers: %s", response.status_code, response.headers
    )
    logger.debug("Response: %s", response.json())
    return response.json().get("filePath")


def transform_fpm_to_jsonld(file_path, dest_path="/tmp/floorplan"):
    generator = generator_for_language_target("fpm", "json-ld")
    mm = metamodel_for_language("fpm")
    model = mm.model_from_file(file_path)
    generator(mm, model, dest_path, overwrite=True)
    return dest_path


def generate_artefacts(model_path, out_path="/tmp/scenery"):

    os.makedirs(out_path, exist_ok=True)
    e = subprocess.run(
        [
            "floorplan",
            "generate",
            "--config",
            "config.toml",
            "-i",
            model_path,
            "--output-path",
            out_path,
            "occ-grid",
            "gazebo",
            "mesh",
            "tts",
        ]
    )
    logger.info(e)
    return out_path


if __name__ == "__main__":

    logger.info("Starting the scenery kafka consumer")
    consumer_config = dict(**BASIC_CONFIG, **CONSUMER_CONFIG)

    # Create Consumer instance
    consumer = Consumer(consumer_config)

    # Subscribe to topic
    topic = "floorplan-model"
    consumer.subscribe([topic])
    logger.debug("Subscribed to topic %s", topic)

    msg_count = 0

    # Poll for new messages from Kafka and print them.
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                # Initial message consumption may take up to
                # `session.timeout.ms` for the consumer group to
                # rebalance and start consuming
                logger.debug("Waiting...")
                continue
            elif msg.error():
                logger.error(msg.error())
            else:
                msg_count += 1
                logger.info("Processing message {}".format(msg_count))
                key = msg.key().decode("utf-8") if msg.key() is not None else ""
                value = msg.value().decode("utf-8") if msg.value() is not None else ""
                logger.debug("Message key: %s", key)
                logger.debug("Message value: %s", value)
                logger.debug("Message headers: %s", msg.headers())

                url = value
                scenery_id = key  # This should be the model
                logger.info(
                    "Notification received. {} model stored at {}".format(
                        scenery_id, url
                    )
                )

                # Getting model from server
                logger.debug("Get model from KB via REST API")
                file_path = get_floorplan_model(url)

                logger.debug("Converting to json-ld...")
                if file_path.endswith(".fpm"):
                    # M2M transformation to json-ld representation
                    json_models_path = transform_fpm_to_jsonld(file_path)
                elif file_path.endswith(".ifc"):
                    try:
                        model_name = transform_ifc_to_jsonld(file_path, "/tmp/ifcld")
                    except Exception as e:
                        logger.error("Transformation from ifc to jsonld failed: %s", e)
                        continue

                    ifcld_model_path = os.path.join(
                        "/tpm/ifcld", f"{model_name}.ifc.json"
                    )
                    try:
                        generate_fpm_rep_from_rdf(ifcld_model_path, "/tmp/floorplan")
                    except Exception as e:
                        logger.error(
                            "Transformation from ifc.json to fpm.json failed: %s", e
                        )
                        continue
                    json_models_path = os.path.join("/tmp/floorplan")
                else:
                    logger.warning(
                        "Got unsupported file type from server ({})... ignoring.".format(
                            file_path
                        )
                    )
                    continue

                logger.debug("Generating execution artefacts...")
                # Call scenery_builder
                artefacts_path = generate_artefacts(json_models_path)

                # Store artefacts in zip file
                rel_paths = glob.glob(
                    "**/*.**", root_dir=artefacts_path, recursive=True
                )
                full_paths = glob.glob(
                    "{}/**/*.*".format(artefacts_path), recursive=True
                )
                artefact_zip_path = "{}.zip".format(scenery_id)
                with ZipFile(artefact_zip_path, "w") as artefacts_zip:
                    for r, f in zip(rel_paths, full_paths):
                        artefacts_zip.write(f, arcname=r)

                # Upload artefact to server
                logger.debug("Uploading {} to server".format(artefact_zip_path))
                artefact_path_server = upload_artefacts_to_server(artefact_zip_path)
                logger.info("Uploaded successfully at %s", artefact_path_server)

                # Call publish_artefact_url
                logger.debug("Sending Kafka notification about local path")
                producer_config = dict(**BASIC_CONFIG, **PRODUCER_CONFIG)
                publish_artefacts_url(
                    producer_config,
                    scenery_id=scenery_id,
                    use_case="KUKA",
                    url=artefact_path_server,
                )
                logger.info("Notification sent via Kafka")

    except KeyboardInterrupt:
        logger.debug("Received keyboard interrupt...")
    finally:
        # Leave group and commit final offsets
        consumer.close()
