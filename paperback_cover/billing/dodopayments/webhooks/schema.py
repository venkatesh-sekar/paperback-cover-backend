from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class WebhookEventType(str, Enum):
    """Types of webhook events from Dodo Payments"""

    SUBSCRIPTION_ACTIVE = "subscription.active"
    SUBSCRIPTION_ON_HOLD = "subscription.on_hold"
    SUBSCRIPTION_RENEWED = "subscription.renewed"
    SUBSCRIPTION_PAUSED = "subscription.paused"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    SUBSCRIPTION_FAILED = "subscription.failed"
    SUBSCRIPTION_EXPIRED = "subscription.expired"
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_PROCESSING = "payment.processing"
    PAYMENT_FAILED = "payment.failed"
    REFUND_SUCCEEDED = "refund.succeeded"
    REFUND_FAILED = "refund.failed"
    DISPUTE_OPENED = "dispute.opened"
    DISPUTE_CLOSED = "dispute.closed"


class WebhookHeaders(BaseModel):
    """Webhook headers for signature verification"""

    webhook_id: str
    webhook_signature: str
    webhook_timestamp: str


class CustomerInfo(BaseModel):
    """Customer information from webhook payload"""

    customer_id: str
    email: str
    name: str


class PaymentInfo(BaseModel):
    """Payment information from webhook payload"""

    payment_id: str
    amount: float
    currency: str
    status: str


class SubscriptionWebhookPayloadDetail(BaseModel):
    """Subscription payload details from Dodo Payments under 'data'."""

    subscription_id: str
    product_id: str
    customer: CustomerInfo
    status: Literal["active", "cancelled", "past_due", "trialing"]
    created_at: datetime
    cancelled_at: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    recurring_pre_tax_amount: float
    currency: str
    quantity: int = 1
    payment_frequency_interval: str
    payment_frequency_count: int
    subscription_period_interval: str
    subscription_period_count: int
    trial_period_days: int = 0
    tax_inclusive: bool = False
    discount_id: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class PaymentWebhookPayloadDetail(BaseModel):
    """Payment payload details from Dodo Payments under 'data'."""

    status: str
    payment_id: str
    total_amount: int
    currency: str
    settlement_amount: int
    settlement_currency: str
    customer: CustomerInfo
    subscription_id: str
    metadata: dict = Field(default_factory=dict)


class RefundWebhookPayloadDetail(BaseModel):
    """Refund payload details from Dodo Payments under 'data'."""

    refund_id: str
    payment_id: str
    amount: float
    currency: str
    status: str
    customer: CustomerInfo
    metadata: dict = Field(default_factory=dict)


class DisputeWebhookPayloadDetail(BaseModel):
    """Dispute payload details from Dodo Payments under 'data'."""

    dispute_id: str
    payment_id: str
    amount: float
    currency: str
    status: str
    reason: str
    customer: CustomerInfo
    metadata: dict = Field(default_factory=dict)


class BaseWebhookPayload(BaseModel):
    """
    Top-level webhook payload that matches the actual JSON structure:
    - business_id, type, timestamp at the top
    - 'data' is one of SubscriptionWebhookPayload,
      PaymentWebhookPayload, RefundWebhookPayload, or DisputeWebhookPayload
    """

    business_id: str
    type: WebhookEventType
    timestamp: datetime


class WebhookPayload(BaseWebhookPayload):
    """
    Top-level webhook payload that matches the actual JSON structure:
    - business_id, type, timestamp at the top
    - 'data' is one of SubscriptionWebhookPayload,
      PaymentWebhookPayload, RefundWebhookPayload, or DisputeWebhookPayload
    """

    business_id: str
    type: WebhookEventType
    timestamp: datetime
    data: dict


class SubscriptionWebhookPayload(BaseWebhookPayload):
    """Subscription payload details from Dodo Payments under 'data'."""

    data: SubscriptionWebhookPayloadDetail


class PaymentWebhookPayload(BaseWebhookPayload):
    """Payment payload details from Dodo Payments under 'data'."""

    data: PaymentWebhookPayloadDetail


class RefundWebhookPayload(BaseWebhookPayload):
    """Refund payload details from Dodo Payments under 'data'."""

    data: RefundWebhookPayloadDetail


class DisputeWebhookPayload(BaseWebhookPayload):
    """Dispute payload details from Dodo Payments under 'data'."""

    data: DisputeWebhookPayloadDetail
