import logging

from celery import shared_task
from django.db import transaction

from apps.audits.models import Audit, AuditStatus
from apps.audits.services import scrape_seo_data

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_audit_task(self, audit_id):
    """
    Process a single audit asynchronously.

    Flow:
    pending -> scrape SEO data -> completed
    failed if scraping or processing fails
    """

    try:
        audit = Audit.objects.select_related("project").get(id=audit_id)

        if audit.status == AuditStatus.COMPLETED:
            return {
                "audit_id": audit.id,
                "url": audit.url,
                "status": "already_completed",
            }

        seo_data = scrape_seo_data(audit.url)

        with transaction.atomic():
            audit.title = seo_data.get("title", "")
            audit.meta_description = seo_data.get("meta_description", "")
            audit.h1_count = seo_data.get("h1_count", 0)
            audit.word_count = seo_data.get("word_count", 0)

            # Step 12 will calculate real SEO score.
            audit.seo_score = 0

            audit.status = AuditStatus.COMPLETED
            audit.error_message = ""

            audit.save(update_fields=[
                "title",
                "meta_description",
                "h1_count",
                "word_count",
                "seo_score",
                "status",
                "error_message",
                "updated_at",
            ])

        logger.info("Audit scraping completed. audit_id=%s", audit.id)

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