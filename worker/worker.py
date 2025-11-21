import os
import json
import signal
import time
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from app.emailer import send_email

import base64

DLQ_TOPIC = os.environ.get('EMAIL_DLQ_TOPIC', 'email-dlq')
MAX_RETRIES = int(os.environ.get('EMAIL_MAX_RETRIES', '3'))

def publish_to_dlq(publisher_client, payload, original_attributes=None):
    """Publish the failed payload to a dead-letter topic with original attributes."""
    try:
        topic_path = publisher_client.topic_path(PROJECT, DLQ_TOPIC)
        # ensure DLQ topic exists
        try:
            publisher_client.get_topic(topic=topic_path)
        except Exception:
            try:
                publisher_client.create_topic(name=topic_path)
            except Exception as e:
                print('Could not create DLQ topic:', e)
        data = json.dumps(payload).encode('utf-8')
        # attach original attributes if provided
        attrs = original_attributes or {}
        future = publisher_client.publish(topic_path, data=data, **attrs)
        future.result(timeout=10)
        print('Published message to DLQ:', DLQ_TOPIC)
    except Exception as e:
        print('Failed to publish to DLQ:', e)

SUBSCRIPTION_NAME = os.environ.get('EMAIL_SUBSCRIPTION', 'email-subscription')
TOPIC_NAME = os.environ.get('EMAIL_TOPIC', 'email-topic')
PROJECT = os.environ.get('GCP_PROJECT', 'local-project')

subscriber = None
streaming_pull_future = None


def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    print(f"Received message: {message.message_id}")
    try:
        data = json.loads(message.data.decode('utf-8'))
    except Exception as e:
        print('Invalid message payload', e)
        message.ack()
        return

    # read retry count from attributes
    attrs = dict(message.attributes) if message.attributes else {}
    retries = int(attrs.get('retries', '0'))
    publisher = pubsub_v1.PublisherClient()
    success = send_email(data)
    if success:
        message.ack()
    else:
        retries += 1
        if retries >= MAX_RETRIES:
            print(f"Max retries reached ({retries}). Sending to DLQ.")
            # publish to DLQ with original attributes and ack
            publish_to_dlq(publisher, data, original_attributes=attrs)
            message.ack()
        else:
            print(f"Message failed, will retry later (attempt {retries}). Nacking message.")
            # nack so Pub/Sub will redeliver; but also re-publish with updated retry count as attribute
            try:
                # republish with updated retries attribute so downstream DLQ logic has info
                topic_path = publisher.topic_path(PROJECT, TOPIC_NAME)
                future = publisher.publish(topic_path, data=json.dumps(data).encode('utf-8'), retries=str(retries))
                future.result(timeout=5)
            except Exception as e:
                print('Failed to republish message with updated retries:', e)
            message.ack()

    def create_subscription_if_needed(publisher_client, subscriber_client):
    topic_path = publisher_client.topic_path(PROJECT, TOPIC_NAME)
    sub_path = subscriber_client.subscription_path(PROJECT, SUBSCRIPTION_NAME)
    try:
        publisher_client.get_topic(topic=topic_path)
    except Exception:
        try:
            publisher_client.create_topic(name=topic_path)
        except Exception as e:
            print('Could not create topic:', e)
    try:
        subscriber_client.get_subscription(subscription=sub_path)
    except Exception:
        try:
            subscriber_client.create_subscription(name=sub_path, topic=topic_path)
        except Exception as e:
            print('Could not create subscription:', e)
    return sub_path

def main():
    global subscriber, streaming_pull_future
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()
    sub_path = create_subscription_if_needed(publisher, subscriber)

    streaming_pull_future = subscriber.subscribe(sub_path, callback=callback)
    print(f"Listening for messages on {sub_path}..")

    def shutdown(signum, frame):
        print('Received shutdown signal, cancelling subscription...')
        if streaming_pull_future:
            streaming_pull_future.cancel()
        # give some time to shutdown gracefully
        time.sleep(1)
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # Block the main thread while messages are processed in the background
    try:
        streaming_pull_future.result()
    except TimeoutError:
        streaming_pull_future.cancel()
    except SystemExit:
        pass
    except Exception as e:
        print('Worker exception:', e)

if __name__ == '__main__':
    main()
