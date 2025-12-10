import pytest
from httpx import AsyncClient
from datetime import date, timedelta


class TestCreateCycle:
    """Tests for creating cycles."""

    @pytest.mark.asyncio
    async def test_create_cycle_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test successful cycle creation."""
        cycle_data = {
            "period_start_date": str(date.today()),
            "period_end_date": str(date.today() + timedelta(days=5)),
        }

        response = await client.post("/cycles", json=cycle_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["period_start_date"] == cycle_data["period_start_date"]
        assert data["period_end_date"] == cycle_data["period_end_date"]
        assert data["period_length"] == 6  # 5 days + 1
        assert "id" in data
        assert "user_id" in data

    @pytest.mark.asyncio
    async def test_create_cycle_without_end_date(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating cycle without end date."""
        cycle_data = {"period_start_date": str(date.today())}

        response = await client.post("/cycles", json=cycle_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["period_start_date"] == cycle_data["period_start_date"]
        assert data["period_end_date"] is None
        assert data["period_length"] is None

    @pytest.mark.asyncio
    async def test_create_cycle_unauthorized(self, client: AsyncClient):
        """Test creating cycle without authentication fails."""
        cycle_data = {"period_start_date": str(date.today())}

        response = await client.post("/cycles", json=cycle_data)

        assert response.status_code == 401


class TestGetCycles:
    """Tests for retrieving cycles."""

    @pytest.mark.asyncio
    async def test_get_cycles_empty(self, client: AsyncClient, auth_headers: dict):
        """Test getting cycles when none exist."""
        response = await client.get("/cycles", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_cycles_with_data(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting cycles returns all user's cycles."""
        # Create multiple cycles
        cycles_data = [
            {
                "period_start_date": str(date.today() - timedelta(days=60)),
                "period_end_date": str(date.today() - timedelta(days=55)),
            },
            {
                "period_start_date": str(date.today() - timedelta(days=30)),
                "period_end_date": str(date.today() - timedelta(days=25)),
            },
            {"period_start_date": str(date.today())},
        ]

        for cycle_data in cycles_data:
            await client.post("/cycles", json=cycle_data, headers=auth_headers)

        response = await client.get("/cycles", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Verify they're sorted by period_start_date descending (most recent first)
        assert data[0]["period_start_date"] == cycles_data[2]["period_start_date"]

    @pytest.mark.asyncio
    async def test_get_cycles_unauthorized(self, client: AsyncClient):
        """Test getting cycles without authentication fails."""
        response = await client.get("/cycles")

        assert response.status_code == 401


class TestUpdateCycle:
    """Tests for updating cycles."""

    @pytest.mark.asyncio
    async def test_update_cycle_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test successful cycle update."""
        # Create a cycle
        cycle_data = {"period_start_date": str(date.today())}
        create_response = await client.post(
            "/cycles", json=cycle_data, headers=auth_headers
        )
        cycle_id = create_response.json()["id"]

        # Update it
        update_data = {
            "period_start_date": str(date.today()),
            "period_end_date": str(date.today() + timedelta(days=4)),
        }
        response = await client.put(
            f"/cycles/{cycle_id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["period_end_date"] == update_data["period_end_date"]
        assert data["period_length"] == 5

    @pytest.mark.asyncio
    async def test_update_nonexistent_cycle(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test updating non-existent cycle fails."""
        update_data = {
            "period_start_date": str(date.today()),
            "period_end_date": str(date.today() + timedelta(days=4)),
        }

        # Use a UUID that doesn't exist
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.put(
            f"/cycles/{fake_id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_cycle_unauthorized(self, client: AsyncClient):
        """Test updating cycle without authentication fails."""
        update_data = {"period_start_date": str(date.today())}

        response = await client.put("/cycles/some-id", json=update_data)

        assert response.status_code == 401


class TestDeleteCycle:
    """Tests for deleting cycles."""

    @pytest.mark.asyncio
    async def test_delete_cycle_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test successful cycle deletion."""
        # Create a cycle
        cycle_data = {"period_start_date": str(date.today())}
        create_response = await client.post(
            "/cycles", json=cycle_data, headers=auth_headers
        )
        cycle_id = create_response.json()["id"]

        # Delete it
        response = await client.delete(f"/cycles/{cycle_id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get("/cycles", headers=auth_headers)
        assert len(get_response.json()) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_cycle(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test deleting non-existent cycle fails."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(f"/cycles/{fake_id}", headers=auth_headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_cycle_unauthorized(self, client: AsyncClient):
        """Test deleting cycle without authentication fails."""
        response = await client.delete("/cycles/some-id")

        assert response.status_code == 401


class TestCycleAuthorization:
    """Tests to ensure users can only access their own cycles."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_user_cycle(self, client: AsyncClient):
        """Test that users cannot access another user's cycles."""
        # Create first user and their cycle
        user1_data = {
            "email": "user1@example.com",
            "password": "password123",
            "gender": "woman",
        }
        await client.post("/auth/register", json=user1_data)
        login1 = await client.post(
            "/auth/login",
            data={"username": user1_data["email"], "password": user1_data["password"]},
        )
        token1 = login1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        # Create cycle for user1
        cycle_data = {"period_start_date": str(date.today())}
        create_response = await client.post(
            "/cycles", json=cycle_data, headers=headers1
        )
        cycle_id = create_response.json()["id"]

        # Create second user
        user2_data = {
            "email": "user2@example.com",
            "password": "password123",
            "gender": "man",
        }
        await client.post("/auth/register", json=user2_data)
        login2 = await client.post(
            "/auth/login",
            data={"username": user2_data["email"], "password": user2_data["password"]},
        )
        token2 = login2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Try to delete user1's cycle as user2
        response = await client.delete(f"/cycles/{cycle_id}", headers=headers2)
        assert response.status_code == 404  # Should not find it
