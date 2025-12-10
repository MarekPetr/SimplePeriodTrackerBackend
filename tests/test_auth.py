import pytest
from httpx import AsyncClient


class TestUserRegistration:
    """Tests for user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "password": "password123",
            "gender": "woman",
        }

        response = await client.post("/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["gender"] == user_data["gender"]
        assert "id" in data
        assert "sharing_settings" in data
        assert data["sharing_settings"]["share_periods"] == True

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: dict):
        """Test registration with duplicate email fails."""
        user_data = {
            "email": test_user["email"],
            "password": "differentpassword",
            "gender": "man",
        }

        response = await client.post("/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_gender(self, client: AsyncClient):
        """Test registration with invalid gender fails."""
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "gender": "invalid",
        }

        response = await client.post("/auth/register", json=user_data)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format fails."""
        user_data = {
            "email": "notanemail",
            "password": "password123",
            "gender": "woman",
        }

        response = await client.post("/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error


class TestLogin:
    """Tests for login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: dict):
        """Test successful login."""
        login_data = {
            "username": test_user["email"],
            "password": test_user["password"],
        }

        response = await client.post("/auth/login", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: dict):
        """Test login with wrong password fails."""
        login_data = {"username": test_user["email"], "password": "wrongpassword"}

        response = await client.post("/auth/login", data=login_data)

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user fails."""
        login_data = {"username": "nonexistent@example.com", "password": "password123"}

        response = await client.post("/auth/login", data=login_data)

        assert response.status_code == 401


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, test_user: dict):
        """Test successful token refresh."""
        refresh_data = {"refresh_token": test_user["refresh_token"]}

        response = await client.post("/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token fails."""
        refresh_data = {"refresh_token": "invalid_token"}

        response = await client.post("/auth/refresh", json=refresh_data)

        assert response.status_code == 401


class TestGetCurrentUser:
    """Tests for get current user endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self, client: AsyncClient, test_user: dict, auth_headers: dict
    ):
        """Test getting current user info."""
        response = await client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert "id" in data
        assert "sharing_settings" in data

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without auth fails."""
        response = await client.get("/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/auth/me", headers=headers)

        assert response.status_code == 401


class TestSharingSettings:
    """Tests for sharing settings endpoint."""

    @pytest.mark.asyncio
    async def test_update_sharing_settings_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test successful sharing settings update."""
        new_settings = {
            "share_periods": False,
            "share_ovulation": True,
            "share_notes": False,
        }

        response = await client.put(
            "/auth/sharing-settings", json=new_settings, headers=auth_headers
        )

        assert response.status_code == 200
        assert "success" in response.json()["message"].lower()

        # Verify the settings were actually updated
        response = await client.get("/auth/me", headers=auth_headers)
        user_data = response.json()
        assert user_data["sharing_settings"]["share_periods"] == False
        assert user_data["sharing_settings"]["share_ovulation"] == True
        assert user_data["sharing_settings"]["share_notes"] == False

    @pytest.mark.asyncio
    async def test_update_sharing_settings_invalid_keys(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test updating sharing settings with invalid keys fails."""
        invalid_settings = {"invalid_key": True, "share_periods": False}

        response = await client.put(
            "/auth/sharing-settings", json=invalid_settings, headers=auth_headers
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_sharing_settings_unauthorized(self, client: AsyncClient):
        """Test updating sharing settings without auth fails."""
        settings = {"share_periods": False}

        response = await client.put("/auth/sharing-settings", json=settings)

        assert response.status_code == 401
