from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from apps.projects.models import Project


class ProjectAPITests(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1",
            password="StrongPass123"
        )

        self.user2 = User.objects.create_user(
            username="user2",
            password="StrongPass123"
        )

        self.client.force_authenticate(user=self.user1)

    def test_create_project(self):
        response = self.client.post(
            "/api/projects/",
            {
                "name": "SEO Project",
                "domain": "https://example.com"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Project.objects.first().owner, self.user1)

    def test_list_only_own_projects(self):
        Project.objects.create(
            owner=self.user1,
            name="User 1 Project",
            domain="https://user1.com"
        )

        Project.objects.create(
            owner=self.user2,
            name="User 2 Project",
            domain="https://user2.com"
        )

        response = self.client.get("/api/projects/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "User 1 Project")

    def test_update_project(self):
        project = Project.objects.create(
            owner=self.user1,
            name="Old Project",
            domain="https://old.com"
        )

        response = self.client.patch(
            f"/api/projects/{project.id}/",
            {
                "name": "Updated Project"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.name, "Updated Project")

    def test_delete_project(self):
        project = Project.objects.create(
            owner=self.user1,
            name="Delete Project",
            domain="https://delete.com"
        )

        response = self.client.delete(
            f"/api/projects/{project.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 0)

    def test_user_cannot_access_other_user_project(self):
        other_project = Project.objects.create(
            owner=self.user2,
            name="Other Project",
            domain="https://other.com"
        )

        response = self.client.get(
            f"/api/projects/{other_project.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)