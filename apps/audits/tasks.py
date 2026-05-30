import logging

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.db import transaction

from apps.audits.models import Audit, AuditStatus
from apps.audits.services import scrape_seo_data, calculate_seo_score, AuditScrapingError

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def process_audit_task(self, audit_id):
    """
    Production-style async audit processing.

    Flow:
    pending -> completed
    pending -> retry on temporary failure
    pending -> failed after max retries
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

        seo_score = calculate_seo_score(
            title=seo_data.get("title", ""),
            meta_description=seo_data.get("meta_description", ""),
            h1_count=seo_data.get("h1_count", 0),
            word_count=seo_data.get("word_count", 0),
        )

        with transaction.atomic():
            audit.title = seo_data.get("title", "")
            audit.meta_description = seo_data.get("meta_description", "")
            audit.h1_count = seo_data.get("h1_count", 0)
            audit.word_count = seo_data.get("word_count", 0)
            audit.seo_score = seo_score
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

        logger.info(
            "Audit completed successfully. audit_id=%s url=%s",
            audit.id,
            audit.url,
        )

        return {
            "audit_id": audit.id,
            "url": audit.url,
            "status": AuditStatus.COMPLETED,
            "seo_score": seo_score,
        }

    except Audit.DoesNotExist:
        logger.warning("Audit not found. audit_id=%s", audit_id)

        return {
            "audit_id": audit_id,
            "status": "not_found",
        }

    except AuditScrapingError as exc:
        logger.warning(
            "Audit scraping failed. audit_id=%s retry=%s/%s error=%s",
            audit_id,
            self.request.retries,
            self.max_retries,
            str(exc),
        )

        if self.request.retries >= self.max_retries:
            Audit.objects.filter(id=audit_id).update(
                status=AuditStatus.FAILED,
                error_message=str(exc),
            )

            logger.error(
                "Audit permanently failed after retries. audit_id=%s error=%s",
                audit_id,
                str(exc),
            )

            return {
                "audit_id": audit_id,
                "status": AuditStatus.FAILED,
                "error_message": str(exc),
            }

        raise self.retry(exc=exc)

    except Exception as exc:
        logger.exception(
            "Unexpected audit task failure. audit_id=%s retry=%s/%s",
            audit_id,
            self.request.retries,
            self.max_retries,
        )

        if self.request.retries >= self.max_retries:
            Audit.objects.filter(id=audit_id).update(
                status=AuditStatus.FAILED,
                error_message=f"Unexpected error: {str(exc)}",
            )

            return {
                "audit_id": audit_id,
                "status": AuditStatus.FAILED,
                "error_message": str(exc),
            }

        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            Audit.objects.filter(id=audit_id).update(
                status=AuditStatus.FAILED,
                error_message=f"Max retries exceeded: {str(exc)}",
            )

            return {
                "audit_id": audit_id,
                "status": AuditStatus.FAILED,
                "error_message": str(exc),
            }


@shared_task
def test_celery_task():
    return "Celery is working successfully!"
