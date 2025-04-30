#!/usr/bin/env python
import os
import subprocess
from zipfile import ZipFile
import glob

import requests

from textx import generator_for_language_target, metamodel_for_language
from confluent_kafka import Consumer, Producer
from dotenv import load_dotenv


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
        print("ERROR: Message failed delivery: {}".format(err))
    else:
        print(
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


def get_floorplan_model(model, url):
    response = requests.get(url, stream=True)

    model_file_path = os.path.basename(url)

    with open(model_file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=128):
            f.write(chunk)
    return model_file_path


def upload_artefacts_to_server(file_path):
    url = os.getenv("REST_UPLOAD_ARTEFACT_URL")
    files = {"zipFile": open(file_path, "rb")}

    response = requests.post(url, files=files)
    return response.json().get("filePath")


def transform_to_jsonld(file_path):
    dest_path = "/tmp/floorplan"
    generator = generator_for_language_target("fpm", "json-ld")
    mm = metamodel_for_language("fpm")
    model = mm.model_from_file(file_path)
    generator(mm, model, dest_path, overwrite=True)
    return dest_path


def generate_artefacts(model_path):
    out_path = "/tmp/scenery"
    os.makedirs(out_path, exist_ok=True)
    e = subprocess.run(
        ["floorplan", "generate", "-i", model_path, "--output-path", out_path]
    )
    print(e)
    return out_path


if __name__ == "__main__":

    consumer_config = dict(**BASIC_CONFIG, **CONSUMER_CONFIG)

    # Create Consumer instance
    consumer = Consumer(consumer_config)

    # Subscribe to topic
    topic = "floorplan-model"
    consumer.subscribe([topic])

    msg_count = 0

    # Poll for new messages from Kafka and print them.
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                # Initial message consumption may take up to
                # `session.timeout.ms` for the consumer group to
                # rebalance and start consuming
                print("Waiting...")
                continue
            elif msg.error():
                print("ERROR: %s".format(msg.error()))
            else:
                msg_count += 1
                print("Processing message {}".format(msg_count))
                key = msg.key().decode("utf-8") if msg.key() is not None else ""
                value = msg.value().decode("utf-8") if msg.value() is not None else ""

                url = value
                scenery_id = key  # This should be the model
                print(
                    "Notification received. {} model stored at {}".format(
                        scenery_id, url
                    )
                )

                # Getting model from server
                print("Get model from KB via REST API")
                file_path = get_floorplan_model(scenery_id, url)

                if file_path.endswith(".zip"):
                    print("Got zip file from server: {}".format(file_path))
                    file_path = (
                        "/Users/argen/100 Projects/floorplan/dsl/models/hospital.fpm"
                    )

                print("Converting to json-ld...")
                # M2M transformation to json-ld representation
                json_models_path = transform_to_jsonld(file_path)

                print("Generating execution arfefacts...")
                # Call scenery_builder
                artefacts_path = generate_artefacts(json_models_path)

                # Store artefacts in zip file
                # TODO part of previous step? Needed at all for server?
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
                print("Uploading {} to server".format(artefact_zip_path))
                artefact_path_server = upload_artefacts_to_server(artefact_zip_path)

                # Call publish_artefact_url
                print("Sending Kafka notification about local path")
                producer_config = dict(**BASIC_CONFIG, **PRODUCER_CONFIG)
                publish_artefacts_url(
                    producer_config,
                    scenery_id=scenery_id,
                    use_case="KUKA",
                    url=artefact_path_server,
                )

    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        consumer.close()
