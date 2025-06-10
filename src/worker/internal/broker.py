import logging
import time
import pika

logger = logging.getLogger(__name__)


class BrokerClient:
    def __init__(self, url: str):
        self.url = url
        self._connection = None

    def connect(self):
        while True:
            try:
                params = pika.URLParameters(self.url)
                self._connection = pika.BlockingConnection(params)
                logger.info("Connected to broker")
                break
            except Exception as e:
                logger.error("Broker connection failed: %s", e)
                time.sleep(5)

    def subscribe(self, queue: str, callback):
        if not self._connection:
            self.connect()
        channel = self._connection.channel()
        channel.queue_declare(queue=queue, durable=True)

        def _cb(ch, method, properties, body):
            callback(body)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue, on_message_callback=_cb)
        channel.start_consuming()
