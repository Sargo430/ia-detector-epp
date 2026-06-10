from app.workers.celery_app import celery_app


@celery_app.task(name="reports.generate_daily")
def generate_daily(tenant_slug: str, date_iso: str):
    """Generate and store daily report artifacts for a tenant."""
    # TODO: implement report aggregation/persistence flow.
    pass


@celery_app.task(name="reports.export_csv")
def export_csv(tenant_slug: str, report_id: str):
    """Build CSV export for a previously generated report."""
    # TODO: implement CSV export and upload to object storage.
    pass
