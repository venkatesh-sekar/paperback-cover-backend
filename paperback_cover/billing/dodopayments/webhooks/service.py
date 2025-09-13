import json
import logging

from standardwebhooks import Webhook

from paperback_cover.billing.dodopayments.webhooks.schema import WebhookHeaders
from paperback_cover.config import settings

logger = logging.getLogger(__name__)


wh = Webhook(settings.billing.dodopayments.webhook_secret)


def verify_webhook_signature(
    payload: str,
    headers: WebhookHeaders,
) -> bool:
    """Verify webhook signature using HMAC SHA256"""
    try:
        raw_str_body = payload if isinstance(payload, str) else payload.decode("utf-8")
        return wh.verify(
            json.dumps(json.loads(raw_str_body), separators=(",", ":")),
            {
                "webhook-id": headers.webhook_id,
                "webhook-signature": headers.webhook_signature,
                "webhook-timestamp": headers.webhook_timestamp,
            },
        )
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False


async def handle_webhook(dict_payload: dict) -> None:
    """Handle webhook payload"""
    raise NotImplementedError("Handle webhook payload")
