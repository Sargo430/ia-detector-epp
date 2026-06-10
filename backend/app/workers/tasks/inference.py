from app.workers.celery_app import celery_app


@celery_app.task(name="inference.process_frame", bind=True, max_retries=2)
def process_frame(self, tenant_slug: str, camera_id: str, frame_s3_key: str):
    """
    Pull frame from S3 → run model → persist event → trigger alert.
    Replace the stub below with your actual model inference.
    """
    try:
        # 1. Download frame from S3  (use boto3 / aioboto3)
        # 2. Run model:  results = model.predict(frame)
        # 3. Save Event to DB
        # 4. If confidence >= threshold → send_alert.delay(...)
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)


@celery_app.task(name="inference.extract_clip")
def extract_clip(tenant_slug: str, camera_id: str, start_ts: str, end_ts: str):
    """Slice RTSP buffer → upload clip to S3."""
    pass
