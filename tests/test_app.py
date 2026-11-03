import re

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def test_health_endpoint(client):
    """Check that Flask can communicate with PostgreSQL."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_homepage_returns_hello_world(client):
    """Check that the homepage loads successfully."""
    response = client.get("/")

    assert response.status_code == 200
    assert b"Hello World!" in response.data


def test_page_counter_increments(client):
    """Check that each homepage visit increments the PostgreSQL counter."""
    first_response = client.get("/")
    second_response = client.get("/")

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_count = re.search(
        rb"viewed <strong>(\d+)</strong>",
        first_response.data,
    )
    second_count = re.search(
        rb"viewed <strong>(\d+)</strong>",
        second_response.data,
    )

    assert first_count is not None
    assert second_count is not None

    assert int(second_count.group(1)) == int(first_count.group(1)) + 1