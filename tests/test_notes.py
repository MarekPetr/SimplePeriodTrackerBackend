import pytest
from httpx import AsyncClient
from datetime import datetime, timezone


class TestCreateNote:
    """Tests for creating notes."""

    @pytest.mark.asyncio
    async def test_create_note_success(self, client: AsyncClient, auth_headers: dict):
        """Test successful note creation."""
        note_data = {
            "date": datetime.now(timezone.utc).isoformat(),
            "text": "Feeling great today!",
            "emoji_notes": [
                {"emoji": "😊", "description": "Happy"},
                {"emoji": "💪", "description": "Energetic"},
            ],
        }

        response = await client.post("/notes", json=note_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["text"] == note_data["text"]
        assert len(data["emoji_notes"]) == 2
        assert "id" in data
        assert "user_id" in data

    @pytest.mark.asyncio
    async def test_create_note_minimal(self, client: AsyncClient, auth_headers: dict):
        """Test creating note with minimal data."""
        note_data = {"date": datetime.now(timezone.utc).isoformat(), "emoji_notes": []}

        response = await client.post("/notes", json=note_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["text"] is None
        assert data["emoji_notes"] == []

    @pytest.mark.asyncio
    async def test_create_duplicate_note_fails(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that creating duplicate note for same date fails."""
        note_date = datetime.now(timezone.utc).isoformat()
        note_data = {"date": note_date, "text": "First note"}

        # Create first note
        response1 = await client.post("/notes", json=note_data, headers=auth_headers)
        assert response1.status_code == 201

        # Try to create second note for same date
        note_data2 = {"date": note_date, "text": "Second note"}
        response2 = await client.post("/notes", json=note_data2, headers=auth_headers)

        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_note_unauthorized(self, client: AsyncClient):
        """Test creating note without authentication fails."""
        note_data = {"date": datetime.now(timezone.utc).isoformat(), "text": "Test"}

        response = await client.post("/notes", json=note_data)

        assert response.status_code == 401


class TestGetNote:
    """Tests for retrieving notes."""

    @pytest.mark.asyncio
    async def test_get_note_success(self, client: AsyncClient, auth_headers: dict):
        """Test successfully retrieving a note."""
        # Create a note
        note_date = datetime.now(timezone.utc)
        note_data = {
            "date": note_date.isoformat(),
            "text": "Test note",
            "emoji_notes": [{"emoji": "😊", "description": "Happy"}],
        }
        await client.post("/notes", json=note_data, headers=auth_headers)

        # Retrieve it
        response = await client.get(f"/notes/{note_date.isoformat()}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == note_data["text"]
        assert len(data["emoji_notes"]) == 1

    @pytest.mark.asyncio
    async def test_get_nonexistent_note(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent note fails."""
        future_date = "2099-12-31T00:00:00"
        response = await client.get(f"/notes/{future_date}", headers=auth_headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_note_unauthorized(self, client: AsyncClient):
        """Test getting note without authentication fails."""
        response = await client.get(f"/notes/{datetime.now(timezone.utc).isoformat()}")

        assert response.status_code == 401


class TestUpdateNote:
    """Tests for updating notes."""

    @pytest.mark.asyncio
    async def test_update_note_success(self, client: AsyncClient, auth_headers: dict):
        """Test successful note update."""
        # Create a note
        note_date = datetime.now(timezone.utc)
        note_data = {"date": note_date.isoformat(), "text": "Original text"}
        await client.post("/notes", json=note_data, headers=auth_headers)

        # Update it
        update_data = {
            "text": "Updated text",
            "emoji_notes": [{"emoji": "🎉", "description": "Celebration"}],
        }
        response = await client.put(
            f"/notes/{note_date.isoformat()}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Updated text"
        assert len(data["emoji_notes"]) == 1
        assert data["emoji_notes"][0]["emoji"] == "🎉"

    @pytest.mark.asyncio
    async def test_update_note_partial(self, client: AsyncClient, auth_headers: dict):
        """Test partial note update (only updating text)."""
        # Create a note
        note_date = datetime.now(timezone.utc)
        note_data = {
            "date": note_date.isoformat(),
            "text": "Original",
            "emoji_notes": [{"emoji": "😊", "description": "Happy"}],
        }
        await client.post("/notes", json=note_data, headers=auth_headers)

        # Update only text
        update_data = {"text": "Updated"}
        response = await client.put(
            f"/notes/{note_date.isoformat()}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Updated"
        # Emoji notes should still be there
        assert len(data["emoji_notes"]) == 1

    @pytest.mark.asyncio
    async def test_update_nonexistent_note(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test updating non-existent note fails."""
        future_date = "2099-12-31T00:00:00"
        update_data = {"text": "New text"}

        response = await client.put(
            f"/notes/{future_date}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_note_unauthorized(self, client: AsyncClient):
        """Test updating note without authentication fails."""
        update_data = {"text": "New text"}
        response = await client.put(
            f"/notes/{datetime.now(timezone.utc).isoformat()}", json=update_data
        )

        assert response.status_code == 401


class TestDeleteNote:
    """Tests for deleting notes."""

    @pytest.mark.asyncio
    async def test_delete_note_success(self, client: AsyncClient, auth_headers: dict):
        """Test successful note deletion."""
        # Create a note
        note_date = datetime.now(timezone.utc)
        note_data = {"date": note_date.isoformat(), "text": "To be deleted"}
        await client.post("/notes", json=note_data, headers=auth_headers)

        # Delete it
        response = await client.delete(
            f"/notes/{note_date.isoformat()}", headers=auth_headers
        )

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(
            f"/notes/{note_date.isoformat()}", headers=auth_headers
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_note(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test deleting non-existent note fails."""
        future_date = "2099-12-31T00:00:00"
        response = await client.delete(f"/notes/{future_date}", headers=auth_headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_note_unauthorized(self, client: AsyncClient):
        """Test deleting note without authentication fails."""
        response = await client.delete(f"/notes/{datetime.now(timezone.utc).isoformat()}")

        assert response.status_code == 401


class TestNoteAuthorization:
    """Tests to ensure users can only access their own notes."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_user_note(self, client: AsyncClient):
        """Test that users cannot access another user's notes."""
        # Create first user and their note
        user1_data = {
            "email": "noteuser1@example.com",
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

        # Create note for user1
        note_date = datetime.now(timezone.utc)
        note_data = {"date": note_date.isoformat(), "text": "User1's private note"}
        await client.post("/notes", json=note_data, headers=headers1)

        # Create second user
        user2_data = {
            "email": "noteuser2@example.com",
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

        # Try to access user1's note as user2
        response = await client.get(
            f"/notes/{note_date.isoformat()}", headers=headers2
        )
        assert response.status_code == 404  # Should not find it
