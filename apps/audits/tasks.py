import logging

from celery import shared_task
from django.db import transaction

from apps.audits.models import Audit, AuditStatus

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_audit_task(self, audit_id):
    """
    Step 10:
    Background task for processing one audit.

    Actual scraping logic will come in Step 11.
    For now, this proves async audit flow:
    pending -> completed
    """

    try:
        audit = Audit.objects.select_related("project").get(id=audit_id)

        if audit.status == AuditStatus.COMPLETED:
            return {
                "audit_id": audit.id,
                "status": "already_completed",
            }

        with transaction.atomic():
            audit.status = AuditStatus.COMPLETED

            # Temporary mock values.
            # Step 11/12 will replace this with real scraper + SEO score logic.
            audit.title = "Pending real scraper integration"
            audit.meta_description = "Pending real meta description extraction"
            audit.h1_count = 0
            audit.word_count = 0
            audit.seo_score = 0
            audit.error_message = ""

            audit.save(update_fields=[
                "status",
                "title",
                "meta_description",
                "h1_count",
                "word_count",
                "seo_score",
                "error_message",
                "updated_at",
            ])

        logger.info("Audit processed successfully. audit_id=%s", audit_id)

        return {
            "audit_id": audit.id,
            "url": audit.url,
            "status": audit.status,
        }

    except Audit.DoesNotExist:
        logger.warning("Audit does not exist. audit_id=%s", audit_id)
        return {
            "audit_id": audit_id,
            "status": "not_found",
        }

    except Exception as exc:
        logger.exception("Audit task failed. audit_id=%s", audit_id)

        try:
            Audit.objects.filter(id=audit_id).update(
                status=AuditStatus.FAILED,
                error_message=str(exc),
            )
        except Exception:
            logger.exception("Could not mark audit as failed. audit_id=%s", audit_id)

        raise self.retry(exc=exc)


@shared_task
def test_celery_task():
    return "Celery is working successfully!"