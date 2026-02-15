"""Tests for daily analysis endpoint."""

from datetime import date

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
class TestDailyAnalysis:
    async def test_analysis_with_full_data(
        self, client: AsyncClient, test_user: User
    ):
        # Setup targets
        await client.put(
            "/api/v1/targets",
            json={"calorie_target": 2000, "protein_target": 150, "sleep_target": 7.5},
        )
        today = date.today().isoformat()
        await client.put(
            f"/api/v1/logs/{today}",
            json={
                "calories": 1850,
                "protein": 160,
                "sleep": 7.25,
                "workout_completed": True,
            },
        )

        response = await client.get(f"/api/v1/logs/{today}/analysis")
        assert response.status_code == 200
        data = response.json()

        # Calories: 1850 < 2000 → under
        assert data["metrics"]["calories"]["status"] == "under"
        assert data["metrics"]["calories"]["delta"] == -150

        # Protein: 160 >= 150 → met
        assert data["metrics"]["protein"]["status"] == "met"
        assert data["metrics"]["protein"]["delta"] == 10

        # Sleep: 7.25 < 7.5 → under
        assert data["metrics"]["sleep"]["status"] == "under"

        assert data["habits"]["workout_completed"] is True
        assert data["habits"]["is_period_day"] is False

    async def test_analysis_with_null_actuals(
        self, client: AsyncClient, test_user: User
    ):
        await client.put(
            "/api/v1/targets",
            json={"calorie_target": 2000, "protein_target": 150, "sleep_target": 7.5},
        )
        today = date.today().isoformat()
        # Log with only workout — all metrics null
        await client.put(
            f"/api/v1/logs/{today}",
            json={"workout_completed": True},
        )

        response = await client.get(f"/api/v1/logs/{today}/analysis")
        assert response.status_code == 200
        data = response.json()

        assert data["metrics"]["calories"]["status"] == "no_data"
        assert data["metrics"]["calories"]["actual"] is None
        assert data["metrics"]["calories"]["delta"] is None

    async def test_analysis_returns_404_for_missing_log(
        self, client: AsyncClient, test_user: User
    ):
        response = await client.get("/api/v1/logs/2020-01-01/analysis")
        assert response.status_code == 404
