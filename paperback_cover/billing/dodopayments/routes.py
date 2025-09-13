import json

from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from paperback_cover.billing.dodopayments.webhooks.schema import WebhookHeaders
from paperback_cover.billing.dodopayments.webhooks.service import (
    handle_webhook,
    verify_webhook_signature,
)

router = APIRouter(
    prefix="/billing/dodopayments",
    tags=["billing", "dodopayments"],
)


@router.post("/webhook")
async def dodo_payments_webhook(
    request: Request,
    webhook_id: str = Header(..., alias="webhook-id"),
    webhook_signature: str = Header(..., alias="webhook-signature"),
    webhook_timestamp: str = Header(..., alias="webhook-timestamp"),
) -> JSONResponse:
    """
    Webhook endpoint for Dodo Payments events.
    Handles subscription, payment, refund, and dispute events.
    """
    try:
        # Get raw request body
        body = await request.body()

        # Verify webhook signature
        headers = WebhookHeaders(
            webhook_id=webhook_id,
            webhook_signature=webhook_signature,
            webhook_timestamp=webhook_timestamp,
        )

        if not verify_webhook_signature(
            payload=body.decode(),
            headers=headers,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

        dict_webhook_payload = json.loads(body)
        # Handle the webhook
        await handle_webhook(dict_payload=dict_webhook_payload)

        return JSONResponse(
            content={"status": "success"},
            status_code=status.HTTP_200_OK,
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}",
        )
