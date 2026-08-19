"""Tests for registration and cookie JWT authentication."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class AuthApiTests(TestCase):
    """Cover the public authentication endpoints."""

    def setUp(self):
        """Create an API client for each test."""
        self.client = APIClient()

    def test_register_success(self):
        """Registration creates a user and returns HTTP 201."""
        response = self.client.post("/api/register/", user_payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username="marvin").exists())

    def test_register_rejects_password_mismatch(self):
        """Registration rejects a wrong confirmation password."""
        payload = user_payload(confirmed_password="Otherpass1")
        response = self.client.post("/api/register/", payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_register_rejects_duplicate_user_data(self):
        """Registration rejects duplicate usernames and emails."""
        create_user()
        response = self.client.post("/api/register/", user_payload(), format="json")
        self.assertEqual(response.status_code, 400)

    def test_login_success_sets_cookies(self):
        """Login returns user data and sets both auth cookies."""
        create_user()
        response = self.client.post("/api/login/", login_payload(), format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    def test_login_wrong_credentials_is_generic(self):
        """Wrong login data returns a generic error."""
        response = self.client.post("/api/login/", login_payload(), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid credentials", str(response.data))

    def test_refresh_sets_new_access_cookie(self):
        """Refresh reads the refresh cookie and sets access again."""
        login = login_client(self.client)
        self.client.cookies["refresh_token"] = login.cookies["refresh_token"].value
        response = self.client.post("/api/token/refresh/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.cookies)

    def test_logout_clears_cookies_and_invalidates_refresh(self):
        """Logout clears cookies and blacklists the refresh token."""
        login = login_client(self.client)
        copy_auth_cookies(self.client, login)
        response = self.client.post("/api/logout/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.cookies["access_token"].value, "")
        self.assertEqual(refresh_after_logout(self.client).status_code, 401)


def user_payload(**overrides):
    """Return valid registration data with optional overrides."""
    data = {
        "username": "marvin",
        "email": "marvin@example.com",
        "password": "Validpass1",
        "confirmed_password": "Validpass1",
    }
    data.update(overrides)
    return data


def login_payload():
    """Return valid login data."""
    return {"username": "marvin", "password": "Validpass1"}


def create_user():
    """Create the default test user."""
    return User.objects.create_user(
        username="marvin",
        email="marvin@example.com",
        password="Validpass1",
    )


def login_client(client):
    """Create a user and log in through the API."""
    create_user()
    return client.post("/api/login/", login_payload(), format="json")


def copy_auth_cookies(client, response):
    """Copy auth cookies from a response into the client."""
    client.cookies["access_token"] = response.cookies["access_token"].value
    client.cookies["refresh_token"] = response.cookies["refresh_token"].value


def refresh_after_logout(client):
    """Try to refresh after a logout."""
    return client.post("/api/token/refresh/")
