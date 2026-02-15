"""Tests for daily log endpoints."""

from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
class TestUpsertDailyLog:
    async def test_create_log_returns_201(
        self, client: AsyncClient, test_user: User
    ):
        # Set targets first
        await client.put(
            "/api/v1/targets",
            json={"calorie_target": 2000, "protein_target": 150, "sleep_target": 7.5},
        )
        today = date.today().isoformat()
        response = await client.put(
            f"/api/v1/logs/{today}",
            json={"calories": 1850, "protein": 140, "sleep": 7.25},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["calories"] == 1850
        assert data["targets"]["calorie_target"] == 2000

    async def test_update_existing_log_returns_200(
        self, client: AsyncClient, test_user: User
    ):
        await client.put(
            "/api/v1/targets",
            json={"calorie_target": 2000, "protein_target": 150, "sleep_target": 7.5},
        )
        today = date.today().isoformat()
        # Create
        await client.put(
            f"/api/v1/logs/{today}",
            json={"calories": 1850},
        )
        # Update
        response = await client.put(
            f"/api/v1/logs/{today}",
            json={"protein": 160, "workout_completed": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["protein"] == 160
        assert data["workout_completed"] is True

    async def test_rejects_future_date(
        self, client: AsyncClient, test_user: User
    ):
        await client.put(
            "/api/v1/targets",
            json={"calorie_target": 2000, "protein_target": 150, "sleep_target": 7.5},
        )
        future = (date.today() + timedelta(days=1)).isoformat()
        response = await client.put(
            f"/api/v1/logs/{future}",
            json={"calories": 1850},
        )
        assert response.status_code == 422

    async def test_rejects_log_without_targets(
        self, client: AsyncClient, test_user: User
    ):
        today = date.today().isoformat()
        response = await client.put(
            f"/api/v1/logs/{today}",
            json={"calories": 1850},
        )
        # Should fail because targets not configured
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "TARGETS_NOT_CONFIGURED"

    async def test_partial_log_allows_null_fields(
        self, client: AsyncClient, test_user: User
    ):
        await client.put(
            "/api/v1/targets",
            json={"calorie_target": 2000, "protein_target": 150, "sleep_target": 7.5},
        )
        today = date.today().isoformat()
        response = await client.put(
            f"/api/v1/logs/{today}",
            json={"workout_completed": True},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["calories"] is None
        assert data["workout_completed"] is True

    async def test_rejects_negative_calories(
        self, client: AsyncClient, test_user: User
    ):
        await client.put(
            "/api/v1/targets",
            json={"calorie_target": 2000, "protein_target": 150, "sleep_target": 7.5},
        )
        today = date.today().isoformat()
        response = await client.put(
            f"/api/v1/logs/{today}",
            json={"calories": -100},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestGetDailyLog:
    async def test_returns_404_for_missing_log(
        self, client: AsyncClient, test_user: User
    ):
        response = await client.get("/api/v1/logs/2020-01-01")
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "DAILY_LOG_NOT_FOUND"


@pytest.mark.asyncio
class TestGetDailyLogsByRange:
    async def test_returns_logs_in_range(
        self, client: AsyncClient, test_user: User
    ):
        await client.put(
            "/api/v1/targets",
            json={"calorie_target": 2000, "protein_target": 150, "sleep_target": 7.5},
        )
        today = date.today()
        await client.put(
            f"/api/v1/logs/{today.isoformat()}",
            json={"calories": 1850},
        )
        response = await client.get(
            "/api/v1/logs",
            params={
                "start_date": today.isoformat(),
                "end_date": today.isoformat(),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1


@pytest.mark.asyncio
class TestDeleteDailyLog:
    async def test_delete_and_recreate(
        self, client: AsyncClient, test_user: User
    ):
        await client.put(
            "/api/v1/targets",
            json={"calorie_target": 2000, "protein_target": 150, "sleep_target": 7.5},
        )
        today = date.today().isoformat()
        await client.put(
            f"/api/v1/logs/{today}",
            json={"calories": 1850},
        )
        # Delete
        response = await client.delete(f"/api/v1/logs/{today}")
        assert response.status_code == 204

        # Verify deleted
        response = await client.get(f"/api/v1/logs/{today}")
        assert response.status_code == 404

        # Recreate
        response = await client.put(
            f"/api/v1/logs/{today}",
            json={"calories": 1900},
        )
        assert response.status_code == 201

    async def test_delete_nonexistent_returns_404(
        self, client: AsyncClient, test_user: User
    ):
        response = await client.delete("/api/v1/logs/2020-01-01")
        assert response.status_code == 404
