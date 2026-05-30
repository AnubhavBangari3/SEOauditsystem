from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AuthAPITests(APITestCase):

    def test_register_user_successfully(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "StrongPass123",
                "confirm_password": "StrongPass123",
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

    def test_login_user_successfully(self):
        self.client.post(
            "/api/auth/register/",
            {
                "username": "loginuser",
                "email": "login@example.com",
                "password": "StrongPass123",
                "confirm_password": "StrongPass123",
            },
            format="json"
        )

        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)