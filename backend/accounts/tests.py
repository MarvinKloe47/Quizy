"""Tests for registration and cookie JWT authentication."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from accounts.tokens import token_version

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

    def test_register_rejects_invalid_email_and_empty_fields(self):
        """Registration rejects invalid email and required empty fields."""
        response = self.client.post("/api/register/", bad_user_payload())
        self.assertEqual(response.status_code, 400)

    def test_register_hashes_password(self):
        """Registration never stores the clear text password."""
        self.client.post("/api/register/", user_payload(), format="json")
        user = User.objects.get(username="marvin")
        self.assertNotEqual(user.password, "Validpass1")

    def test_login_success_sets_cookies(self):
        """Login returns user data and sets both auth cookies."""
        create_user()
        response = self.client.post("/api/login/", login_payload(), format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)
        self.assertTrue(response.cookies["access_token"]["httponly"])

    def test_login_wrong_credentials_is_generic(self):
        """Wrong login data returns a generic error."""
        response = self.client.post("/api/login/", login_payload(), format="json")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid credentials", str(response.data))

    def test_login_wrong_password_is_generic(self):
        """Wrong passwords return the same generic login error."""
        create_user()
        payload = {"username": "marvin", "password": "Wrongpass1"}
        response = self.client.post("/api/login/", payload, format="json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "Invalid credentials.")

    def test_refresh_sets_new_access_cookie(self):
        """Refresh reads the refresh cookie and sets access again."""
        login = login_client(self.client)
        self.client.cookies["refresh_token"] = login.cookies["refresh_token"].value
        response = self.client.post("/api/token/refresh/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.cookies)

    def test_refresh_rejects_missing_or_invalid_cookie(self):
        """Refresh rejects missing and manipulated refresh cookies."""
        self.assertEqual(self.client.post("/api/token/refresh/").status_code, 401)
        self.client.cookies["refresh_token"] = "bad.token.value"
        self.assertEqual(self.client.post("/api/token/refresh/").status_code, 401)

    def test_manipulated_access_cookie_is_rejected(self):
        """Protected endpoints reject a manipulated access cookie."""
        self.client.cookies["access_token"] = "bad.token.value"
        response = self.client.get("/api/quizzes/")
        self.assertEqual(response.status_code, 401)

    def test_expired_access_cookie_is_rejected(self):
        """Protected endpoints reject expired access cookies."""
        user = create_user()
        self.client.cookies["access_token"] = str(expired_access(user))
        response = self.client.get("/api/quizzes/")
        self.assertEqual(response.status_code, 401)

    def test_expired_refresh_cookie_is_rejected(self):
        """Refresh rejects expired refresh cookies."""
        user = create_user()
        self.client.cookies["refresh_token"] = str(expired_refresh(user))
        response = self.client.post("/api/token/refresh/")
        self.assertEqual(response.status_code, 401)

    def test_logout_clears_cookies_and_invalidates_refresh(self):
        """Logout clears cookies and blacklists the refresh token."""
        login = login_client(self.client)
        copy_auth_cookies(self.client, login)
        response = self.client.post("/api/logout/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.cookies["access_token"].value, "")
        self.assertEqual(refresh_after_logout(self.client).status_code, 401)

    def test_logout_invalidates_existing_access_token(self):
        """Logout revokes already issued access tokens immediately."""
        login = login_client(self.client)
        old_access = login.cookies["access_token"].value
        copy_auth_cookies(self.client, login)
        self.client.post("/api/logout/")
        self.client.cookies["access_token"] = old_access
        response = self.client.get("/api/quizzes/")
        self.assertEqual(response.status_code, 401)


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


def bad_user_payload():
    """Return invalid registration data."""
    return {
        "username": "",
        "email": "not-an-email",
        "password": "",
        "confirmed_password": "",
    }


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


def expired_access(user):
    """Return an already expired access token."""
    token = AccessToken.for_user(user)
    token["token_version"] = token_version(user)
    token.set_exp(lifetime=timedelta(seconds=-1))
    return token


def expired_refresh(user):
    """Return an already expired refresh token."""
    token = RefreshToken.for_user(user)
    token["token_version"] = token_version(user)
    token.set_exp(lifetime=timedelta(seconds=-1))
    return token
