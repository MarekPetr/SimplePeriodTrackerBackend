import pytest
from httpx import AsyncClient
from datetime import date, datetime, timedelta


class TestGetMonthData:
    """Tests for calendar month data endpoint."""

    @pytest.mark.asyncio
    async def test_get_month_data_empty(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting calendar data for month with no data."""
        year = 2025
        month = 1

        response = await client.get(
            f"/calendar/month?year={year}&month={month}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # January 2025 has 31 days
        assert len(data) == 31
        # All days should have type None (no special type) and no notes
        for day in data:
            assert day["type"] is None
            assert day["hasNote"] == False

    @pytest.mark.asyncio
    async def test_get_month_data_with_cycles(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test calendar data with period cycles."""
        # Create a cycle in January 2025
        cycle_data = {
            "period_start_date": "2025-01-10",
            "period_end_date": "2025-01-14",
        }
        await client.post("/cycles", json=cycle_data, headers=auth_headers)

        # Get January 2025 calendar
        response = await client.get(
            "/calendar/month?year=2025&month=1", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Find the period days (10th-14th)
        period_days = [d for d in data if d["date"] >= "2025-01-10" and d["date"] <= "2025-01-14"]
        assert len(period_days) == 5

        # These should be marked as period days
        for day in period_days:
            assert day["type"] == "period"

    @pytest.mark.asyncio
    async def test_get_month_data_with_notes(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test calendar data with notes."""
        # Create a note in January 2025
        note_data = {
            "date": datetime(2025, 1, 15).isoformat(),
            "text": "Test note",
        }
        await client.post("/notes", json=note_data, headers=auth_headers)

        # Get January 2025 calendar
        response = await client.get(
            "/calendar/month?year=2025&month=1", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Find January 15th
        jan_15 = next(d for d in data if d["date"] == "2025-01-15")
        assert jan_15["hasNote"] == True

        # Other days should not have notes
        other_days = [d for d in data if d["date"] != "2025-01-15"]
        for day in other_days:
            assert day["hasNote"] == False

    @pytest.mark.asyncio
    async def test_get_month_data_with_cycles_and_notes(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test calendar data with both cycles and notes."""
        # Create a cycle
        cycle_data = {
            "period_start_date": "2025-02-10",
            "period_end_date": "2025-02-14",
        }
        await client.post("/cycles", json=cycle_data, headers=auth_headers)

        # Create notes on some period days and some other days
        note_dates = [
            datetime(2025, 2, 12).isoformat(),  # During period
            datetime(2025, 2, 20).isoformat(),  # After period
        ]
        for note_date in note_dates:
            await client.post(
                "/notes", json={"date": note_date, "text": "Test"}, headers=auth_headers
            )

        # Get February 2025 calendar
        response = await client.get(
            "/calendar/month?year=2025&month=2", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Check period days
        feb_12 = next(d for d in data if d["date"] == "2025-02-12")
        assert feb_12["type"] == "period"
        assert feb_12["hasNote"] == True

        # Check non-period day with note
        feb_20 = next(d for d in data if d["date"] == "2025-02-20")
        assert feb_20["type"] is None  # Not a period day
        assert feb_20["hasNote"] == True

    @pytest.mark.asyncio
    async def test_get_month_data_different_months(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting data for different months returns correct day counts."""
        test_cases = [
            (2025, 1, 31),  # January - 31 days
            (2025, 2, 28),  # February non-leap - 28 days
            (2024, 2, 29),  # February leap - 29 days
            (2025, 4, 30),  # April - 30 days
            (2025, 12, 31),  # December - 31 days
        ]

        for year, month, expected_days in test_cases:
            response = await client.get(
                f"/calendar/month?year={year}&month={month}", headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == expected_days, f"Failed for {year}-{month}"

    @pytest.mark.asyncio
    async def test_get_month_data_invalid_year(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting calendar with invalid year fails."""
        response = await client.get(
            "/calendar/month?year=1999&month=1", headers=auth_headers
        )
        assert response.status_code == 422  # Validation error

        response = await client.get(
            "/calendar/month?year=2101&month=1", headers=auth_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_month_data_invalid_month(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting calendar with invalid month fails."""
        response = await client.get(
            "/calendar/month?year=2025&month=0", headers=auth_headers
        )
        assert response.status_code == 422

        response = await client.get(
            "/calendar/month?year=2025&month=13", headers=auth_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_month_data_unauthorized(self, client: AsyncClient):
        """Test getting calendar without authentication fails."""
        response = await client.get("/calendar/month?year=2025&month=1")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_month_data_spanning_cycles(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test calendar data with cycles spanning across month boundaries."""
        # Create a cycle that starts in January and ends in February
        cycle_data = {
            "period_start_date": "2025-01-28",
            "period_end_date": "2025-02-02",
        }
        await client.post("/cycles", json=cycle_data, headers=auth_headers)

        # Get January calendar
        jan_response = await client.get(
            "/calendar/month?year=2025&month=1", headers=auth_headers
        )
        jan_data = jan_response.json()

        # Days 28-31 in January should be period days
        jan_28_31 = [d for d in jan_data if d["date"] >= "2025-01-28"]
        for day in jan_28_31:
            assert day["type"] == "period"

        # Get February calendar
        feb_response = await client.get(
            "/calendar/month?year=2025&month=2", headers=auth_headers
        )
        feb_data = feb_response.json()

        # Days 1-2 in February should be period days
        feb_1_2 = [d for d in feb_data if d["date"] <= "2025-02-02"]
        for day in feb_1_2:
            assert day["type"] == "period"
