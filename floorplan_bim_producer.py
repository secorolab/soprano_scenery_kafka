#!/usr/bin/env python

from confluent_kafka import Producer
from datetime import datetime
import time

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()
    config = {
        "bootstrap.servers": "kafka-soprano.atb-bremen.de:9094",
        "sasl.username": os.getenv("KAFKA_USER"),
        "sasl.password": os.getenv("KAFKA_PASS"),
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "PLAIN",
        "acks": "all",
    }

    producer = Producer(config)

    # Optional per-message delivery callback (triggered by poll() or flush())
    # when a message has been successfully delivered
    # or permanently failed delivery (after retries).
    def delivery_callback(err, msg):
        if err:
            print("ERROR: Message failed delivery: {}".format(err))
        else:
            print(
                "Sent message: {timestamp}, {value}".format(
                    timestamp=msg.timestamp(), value=msg.value().decode("utf-8")
                )
            )

    # Produce data by selecting random values from these lists.
    topic = "floorplan-model"

    producer.produce(topic, key="hospital", value="/Users/argen/100 Projects/floorplan/dsl/models/examples/hospital.fpm2", callback=delivery_callback)
    producer.flush()
    # wait
    time.sleep(3)
