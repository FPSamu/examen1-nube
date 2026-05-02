import json
import logging
import time

import boto3

from src.config import settings
from src.db.database import SessionLocal
from src.worker import process_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

_sqs = boto3.client("sqs", region_name=settings.aws_region)


def run() -> None:
    logger.info("receipt-worker started, polling queue: %s", settings.sqs_queue_url)
    while True:
        try:
            response = _sqs.receive_message(
                QueueUrl=settings.sqs_queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,  # long-polling
            )
            messages = response.get("Messages", [])
            if not messages:
                continue

            for msg in messages:
                receipt_handle = msg["ReceiptHandle"]
                body = json.loads(msg["Body"])
                sell_note_id = body.get("sell_note_id")

                if not sell_note_id:
                    logger.warning("Message missing sell_note_id, skipping: %s", body)
                    _sqs.delete_message(
                        QueueUrl=settings.sqs_queue_url, ReceiptHandle=receipt_handle
                    )
                    continue

                db = SessionLocal()
                try:
                    process_message(db, sell_note_id)
                    _sqs.delete_message(
                        QueueUrl=settings.sqs_queue_url, ReceiptHandle=receipt_handle
                    )
                    logger.info("Message deleted from queue for sell note %s", sell_note_id)
                except Exception as exc:
                    logger.error(
                        "Failed to process sell note %s: %s", sell_note_id, exc, exc_info=True
                    )
                    # Message stays in queue; SQS visibility timeout will re-expose it
                finally:
                    db.close()

        except Exception as exc:
            logger.error("Unexpected error in polling loop: %s", exc, exc_info=True)
            time.sleep(5)


if __name__ == "__main__":
    run()
