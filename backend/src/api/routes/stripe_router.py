"""
Stripe Checkout and Subscription Management API
"""
import stripe
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core.config import get_settings
from src.auth.models import get_user_by_id, update_user_subscription, get_user_subscription
from src.auth.security import get_current_user

# Configure Stripe
settings = get_settings()
stripe.api_key = settings.stripe_secret_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stripe", tags=["Stripe"])


class CreateCheckoutRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str


class SubscriptionResponse(BaseModel):
    stripe_customer_id: Optional[str]
    subscription_tier: str
    subscription_status: str
    subscription_end_date: Optional[str]
    credits_remaining: int


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CreateCheckoutRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a Stripe Checkout session for subscription purchase."""
    try:
        user_id = current_user["id"]
        user_email = current_user["email"]
        
        # Create or retrieve Stripe customer
        customer_id = current_user.get("stripe_customer_id")
        if not customer_id:
            customer = stripe.Customer.create(
                email=user_email,
                metadata={"user_id": str(user_id)}
            )
            customer_id = customer.id
            # Update user with customer ID
            update_user_subscription(user_id, stripe_customer_id=customer_id)
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": request.price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                "user_id": str(user_id)
            },
            subscription_data={
                "metadata": {
                    "user_id": str(user_id)
                }
            }
        )
        
        return {"url": checkout_session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription_info(current_user: dict = Depends(get_current_user)):
    """Get current user's subscription information."""
    try:
        user_id = current_user["id"]
        subscription = get_user_subscription(user_id)
        
        if not subscription:
            # Return default free tier info
            return SubscriptionResponse(
                stripe_customer_id=None,
                subscription_tier="free",
                subscription_status="inactive",
                subscription_end_date=None,
                credits_remaining=current_user.get("credits_remaining", 0)
            )
        
        return SubscriptionResponse(**subscription)
        
    except Exception as e:
        logger.error(f"Error getting subscription info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription information"
        )


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        if not settings.stripe_webhook_secret:
            logger.warning("Stripe webhook secret not configured")
            return JSONResponse({"status": "webhook secret not configured"})
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )
        except ValueError:
            logger.error("Invalid payload")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            await handle_checkout_completed(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            await handle_subscription_updated(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            await handle_subscription_cancelled(event['data']['object'])
        elif event['type'] == 'invoice.payment_succeeded':
            await handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            await handle_payment_failed(event['data']['object'])
        else:
            logger.info(f"Unhandled event type: {event['type']}")
        
        return JSONResponse({"status": "success"})
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


async def handle_checkout_completed(session):
    """Handle successful checkout completion."""
    try:
        user_id = int(session['metadata']['user_id'])
        subscription_id = session.get('subscription')
        
        if subscription_id:
            # Retrieve subscription details
            subscription = stripe.Subscription.retrieve(subscription_id)
            price_id = subscription['items']['data'][0]['price']['id']
            
            # Map price ID to subscription tier
            tier = get_tier_from_price_id(price_id)
            status = subscription['status']
            
            # Calculate end date
            current_period_end = datetime.fromtimestamp(
                subscription['current_period_end'], tz=timezone.utc
            ).isoformat()
            
            # Update user subscription
            update_user_subscription(
                user_id=user_id,
                subscription_tier=tier,
                subscription_status=status,
                subscription_end_date=current_period_end
            )
            
            logger.info(f"Updated subscription for user {user_id}: {tier} - {status}")
        
    except Exception as e:
        logger.error(f"Error handling checkout completed: {str(e)}")


async def handle_subscription_updated(subscription):
    """Handle subscription updates."""
    try:
        user_id = int(subscription['metadata']['user_id'])
        price_id = subscription['items']['data'][0]['price']['id']
        
        tier = get_tier_from_price_id(price_id)
        status = subscription['status']
        
        current_period_end = datetime.fromtimestamp(
            subscription['current_period_end'], tz=timezone.utc
        ).isoformat()
        
        update_user_subscription(
            user_id=user_id,
            subscription_tier=tier,
            subscription_status=status,
            subscription_end_date=current_period_end
        )
        
        logger.info(f"Updated subscription for user {user_id}: {tier} - {status}")
        
    except Exception as e:
        logger.error(f"Error handling subscription updated: {str(e)}")


async def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation."""
    try:
        user_id = int(subscription['metadata']['user_id'])
        
        update_user_subscription(
            user_id=user_id,
            subscription_tier="free",
            subscription_status="cancelled",
            subscription_end_date=None
        )
        
        logger.info(f"Cancelled subscription for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling subscription cancelled: {str(e)}")


async def handle_payment_succeeded(invoice):
    """Handle successful payment."""
    try:
        subscription_id = invoice.get('subscription')
        if subscription_id:
            subscription = stripe.Subscription.retrieve(subscription_id)
            user_id = int(subscription['metadata']['user_id'])
            
            # Extend subscription period
            current_period_end = datetime.fromtimestamp(
                subscription['current_period_end'], tz=timezone.utc
            ).isoformat()
            
            update_user_subscription(
                user_id=user_id,
                subscription_status="active",
                subscription_end_date=current_period_end
            )
            
            logger.info(f"Payment succeeded for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling payment succeeded: {str(e)}")


async def handle_payment_failed(invoice):
    """Handle failed payment."""
    try:
        subscription_id = invoice.get('subscription')
        if subscription_id:
            subscription = stripe.Subscription.retrieve(subscription_id)
            user_id = int(subscription['metadata']['user_id'])
            
            update_user_subscription(
                user_id=user_id,
                subscription_status="past_due"
            )
            
            logger.info(f"Payment failed for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling payment failed: {str(e)}")


def get_tier_from_price_id(price_id: str) -> str:
    """Map Stripe price ID to subscription tier."""
    price_tier_map = {
        "price_1T8V4SGSVXwaPFBEtTmydTHl": "pro",  # Monthly Pro $19
        "price_1T8V4SGSVXwaPFBEnSZVoN6V": "pro",  # Annual Pro $182.40
        "price_1T8V4TGSVXwaPFBEijoJWWai": "business",  # Monthly Business $49
        "price_1T8V4TGSVXwaPFBEGpbLSTKy": "business",  # Annual Business $470.40
        "price_1T8V4TGSVXwaPFBEzNNqyZ6Z": "credits",  # 50 Credits $5
    }
    return price_tier_map.get(price_id, "free")