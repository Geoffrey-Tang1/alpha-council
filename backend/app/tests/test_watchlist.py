def test_watchlist_crud(client):
    create_response = client.post(
        "/api/v1/watchlist",
        json={
            "ticker": "nvda",
            "market": "US",
            "notes": "AI infrastructure watch candidate.",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["ticker"] == "NVDA"
    assert created["market"] == "US"
    assert created["latest_signal"] == "WATCH"
    assert created["notes"] == "AI infrastructure watch candidate."

    list_response = client.get("/api/v1/watchlist")
    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1

    update_response = client.patch(
        f"/api/v1/watchlist/{created['id']}",
        json={
            "notes": "Updated research note.",
            "latest_risk_level": "MEDIUM",
            "latest_price": 123.45,
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["notes"] == "Updated research note."
    assert updated["latest_risk_level"] == "MEDIUM"
    assert updated["latest_price"] == 123.45

    get_response = client.get(f"/api/v1/watchlist/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]

    delete_response = client.delete(f"/api/v1/watchlist/{created['id']}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/watchlist/{created['id']}")
    assert missing_response.status_code == 404


def test_watchlist_rejects_duplicate_ticker_market(client):
    payload = {
        "ticker": "TSM",
        "market": "TW",
        "notes": "Duplicate test.",
    }

    first_response = client.post("/api/v1/watchlist", json=payload)
    second_response = client.post("/api/v1/watchlist", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
