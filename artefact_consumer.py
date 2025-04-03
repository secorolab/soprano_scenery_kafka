#!/usr/bin/env python

from confluent_kafka import Consumer

if __name__ == '__main__':
    from dotenv import load_dotenv
    import os

    load_dotenv()

    config = {
        # User-specific properties that you must set
        'bootstrap.servers': 'kafka-soprano.atb-bremen.de:9094',
        "sasl.username": os.getenv("KAFKA_USER"),
        "sasl.password": os.getenv("KAFKA_PASS"),

        # Fixed properties
        'security.protocol': 'SASL_SSL',
        'sasl.mechanisms':   'PLAIN',
        'group.id':          'my-super-group',
        'auto.offset.reset': 'earliest'
    }

    # Create Consumer instance
    consumer = Consumer(config)

    # Subscribe to topic
    topic = "scenery-artefacts"
    consumer.subscribe([topic])

    # Poll for new messages from Kafka and print them.
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                # Initial message consumption may take up to
                # `session.timeout.ms` for the consumer group to
                # rebalance and start consuming
                print("Waiting...")
            elif msg.error():
                print("ERROR: %s".format(msg.error()))
            else:
                key = msg.key().decode('utf-8') if msg.key() is not None else ""
                value = msg.value().decode('utf-8') if msg.value() is not None else ""

                # Extract the (optional) key and value, and print
                print(f"Consumed event from topic {msg.topic()}: key = {key:12} value = {value:12}")
                print(msg.headers())
    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        consumer.close()
