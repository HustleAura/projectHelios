"""Tests for target configuration endpoints."""

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
class TestGetTargets:
    async def test_returns_404_when_no_targets_configured(
        self, client: AsyncClient, test_user: User
    ):
        response = await client.get("/api/v1/targets")
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "TARGETS_NOT_CONFIGURED"

    async def test_returns_targets_after_setting(
        self, client: AsyncClient, test_user: User
    ):
        # Set targets first
        await client.put(
            "/api/v1/targets",
            json={"calorie_target": 2000, "protein_target": 150, "sleep_target": 7.5},
        )
        response = await client.get("/api/v1/targets")
        assert response.status_code == 200
        data = response.json()
        assert data["calorie_target"] == 2000
        assert data["protein_target"] == 150


@pytest.mark.asyncio
class TestUpdateTargets:
    async def test_creates_targets_on_first_put(
        self, client: AsyncClient, test_user: User
    ):
        response = await client.put(
            "/api/v1/targets",
            json={"calorie_target": 2000, "protein_target": 150, "sleep_target": 7.5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["calorie_target"] == 2000
        assert data["protein_target"] == 150

    async def test_updates_existing_targets(
        self, client: AsyncClient, test_user: User
    ):
        await client.put(
            "/api/v1/targets",
            json={"calorie_target": 2000, "protein_target": 150, "sleep_target": 7.5},
        )
        response = await client.put(
            "/api/v1/targets",
            json={"calorie_target": 2200, "protein_target": 160, "sleep_target": 8.0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["calorie_target"] == 2200
        assert data["protein_target"] == 160

    async def test_rejects_negative_target(
        self, client: AsyncClient, test_user: User
    ):
        response = await client.put(
            "/api/v1/targets",
            json={"calorie_target": -100, "protein_target": 150, "sleep_target": 7.5},
        )
        assert response.status_code == 422
