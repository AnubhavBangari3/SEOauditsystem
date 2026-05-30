import django_filters

from apps.audits.models import Audit, AuditStatus


class AuditFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=AuditStatus.choices
    )

    min_score = django_filters.NumberFilter(
        field_name="seo_score",
        lookup_expr="gte"
    )

    max_score = django_filters.NumberFilter(
        field_name="seo_score",
        lookup_expr="lte"
    )

    project = django_filters.NumberFilter(
        field_name="project_id"
    )

    class Meta:
        model = Audit
        fields = [
            "status",
            "min_score",
            "max_score",
            "project",
        ]