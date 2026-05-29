from rest_framework import serializers

from apps.audits.models import Audit


class AuditSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = Audit
        fields = [
            "id",
            "project",
            "project_name",
            "url",
            "status",
            "title",
            "meta_description",
            "h1_count",
            "word_count",
            "seo_score",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "title",
            "meta_description",
            "h1_count",
            "word_count",
            "seo_score",
            "error_message",
            "created_at",
            "updated_at",
        ]


class URLSubmitSerializer(serializers.Serializer):
    urls = serializers.ListField(
        child=serializers.URLField(max_length=1000),
        allow_empty=False
    )

    def validate_urls(self, urls):
        cleaned_urls = []

        for url in urls:
            cleaned_url = url.strip()

            if cleaned_url in cleaned_urls:
                raise serializers.ValidationError(
                    f"Duplicate URL in request: {cleaned_url}"
                )

            cleaned_urls.append(cleaned_url)

        return cleaned_urls

    def validate(self, attrs):
        project = self.context["project"]
        urls = attrs["urls"]

        existing_urls = Audit.objects.filter(
            project=project,
            url__in=urls
        ).values_list("url", flat=True)

        if existing_urls:
            raise serializers.ValidationError({
                "urls": f"These URLs already exist in this project: {list(existing_urls)}"
            })

        return attrs