import asyncio
from app.workers.celery_app import celery_app
from app.services.redis import publish_alert


@celery_app.task(name="notifications.send_alert", bind=True, max_retries=3)
def send_alert(self, tenant_slug: str, alert_payload: dict):
    """Push alert to Redis pubsub → dashboard SSE."""
    try:
        asyncio.run(publish_alert(tenant_slug, alert_payload))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)


@celery_app.task(name="notifications.send_email")
def send_email(tenant_slug: str, recipients: list[str], subject: str, body: str):
    """Placeholder — wire to SendGrid / SES."""
    # TODO: integrate email provider
    pass


@celery_app.task(name="notifications.send_webhook")
def send_webhook(tenant_slug: str, url: str, payload: dict):
    import httpx
    httpx.post(url, json=payload, timeout=10)
