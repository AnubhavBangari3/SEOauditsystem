from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from apps.projects.models import Project
from apps.audits.models import Audit, AuditStatus


class AuditAPITests(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="StrongPass123")
        self.user2 = User.objects.create_user(username="user2", password="StrongPass123")

        self.project1 = Project.objects.create(
            owner=self.user1,
            name="User 1 Project",
            domain="https://example.com"
        )

        self.project2 = Project.objects.create(
            owner=self.user2,
            name="User 2 Project",
            domain="https://other.com"
        )

        self.client.force_authenticate(user=self.user1)

    def test_submit_urls_successfully(self):
        response = self.client.post(
            f"/api/audits/submit/{self.project1.id}/",
            {
                "urls": [
                    "https://example.com",
                    "https://www.djangoproject.com"
                ]
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(Audit.objects.count(), 2)
        self.assertEqual(
            Audit.objects.filter(project=self.project1, status=AuditStatus.PENDING).count(),
            2
        )

    def test_prevent_duplicate_url_in_same_project(self):
        Audit.objects.create(project=self.project1, url="https://example.com")

        response = self.client.post(
            f"/api/audits/submit/{self.project1.id}/",
            {"urls": ["https://example.com"]},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cannot_submit_url_to_other_user_project(self):
        response = self.client.post(
            f"/api/audits/submit/{self.project2.id}/",
            {"urls": ["https://notallowed.com"]},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_audit_results_list_with_pagination(self):
        Audit.objects.create(
            project=self.project1,
            url="https://example.com",
            status=AuditStatus.COMPLETED,
            seo_score=70
        )

        response = self.client.get("/api/audits/?page=1&page_size=2")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 1)

    def test_search_audit_by_url(self):
        Audit.objects.create(
            project=self.project1,
            url="https://www.djangoproject.com",
            status=AuditStatus.COMPLETED,
            seo_score=80
        )

        Audit.objects.create(
            project=self.project1,
            url="https://example.com",
            status=AuditStatus.COMPLETED,
            seo_score=40
        )

        response = self.client.get("/api/audits/?search=django")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertIn("django", response.data["results"][0]["url"])

    def test_filter_audit_by_status(self):
        Audit.objects.create(
            project=self.project1,
            url="https://completed.com",
            status=AuditStatus.COMPLETED,
            seo_score=70
        )

        Audit.objects.create(
            project=self.project1,
            url="https://failed.com",
            status=AuditStatus.FAILED,
            error_message="Failed"
        )

        response = self.client.get("/api/audits/?status=failed")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["status"], AuditStatus.FAILED)

    def test_filter_audit_by_score_range(self):
        Audit.objects.create(
            project=self.project1,
            url="https://high-score.com",
            status=AuditStatus.COMPLETED,
            seo_score=90
        )

        Audit.objects.create(
            project=self.project1,
            url="https://low-score.com",
            status=AuditStatus.COMPLETED,
            seo_score=20
        )

        response = self.client.get("/api/audits/?min_score=50&max_score=100")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["seo_score"], 90)

    def test_dashboard_api(self):
        Audit.objects.create(
            project=self.project1,
            url="https://completed.com",
            status=AuditStatus.COMPLETED,
            title="Completed Page",
            meta_description="Meta",
            seo_score=80
        )

        Audit.objects.create(
            project=self.project1,
            url="https://failed.com",
            status=AuditStatus.FAILED,
            title="",
            meta_description="",
            error_message="Failed"
        )

        response = self.client.get("/api/audits/dashboard/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_audited_urls"], 2)
        self.assertEqual(response.data["failed_audits"], 1)
        self.assertEqual(response.data["average_seo_score"], 80.0)
        self.assertEqual(response.data["missing_titles"], 1)
        self.assertEqual(response.data["missing_meta_descriptions"], 1)

    def test_csv_upload_successfully(self):
        csv_content = (
            "url\n"
            "https://www.python.org\n"
            "wrong-url\n"
            "https://www.djangoproject.com\n"
            "https://www.python.org\n"
        )

        csv_file = SimpleUploadedFile(
            "urls.csv",
            csv_content.encode("utf-8"),
            content_type="text/csv"
        )

        response = self.client.post(
            f"/api/audits/upload-csv/{self.project1.id}/",
            {"file": csv_file},
            format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created"], 2)
        self.assertEqual(response.data["queued"], 2)
        self.assertEqual(response.data["invalid_count"], 1)
        self.assertEqual(response.data["duplicate_count"], 1)
        self.assertEqual(
            Audit.objects.filter(project=self.project1, status=AuditStatus.PENDING).count(),
            2
        )

    def test_csv_upload_rejects_non_csv_file(self):
        txt_file = SimpleUploadedFile(
            "urls.txt",
            b"https://example.com",
            content_type="text/plain"
        )

        response = self.client.post(
            f"/api/audits/upload-csv/{self.project1.id}/",
            {"file": txt_file},
            format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_only_see_own_audits(self):
        Audit.objects.create(
            project=self.project1,
            url="https://own.com",
            status=AuditStatus.COMPLETED,
            seo_score=70
        )

        Audit.objects.create(
            project=self.project2,
            url="https://other.com",
            status=AuditStatus.COMPLETED,
            seo_score=90
        )

        response = self.client.get("/api/audits/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["url"], "https://own.com")