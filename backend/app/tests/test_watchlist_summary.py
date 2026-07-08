def test_watchlist_summary_endpoint(client):
    payloads = [
        {"ticker": "WLS1", "market": "US", "notes": "summary test"},
        {"ticker": "WLS2", "market": "US", "notes": "summary test"},
        {"ticker": "WLS3", "market": "JP", "notes": "summary test"},
    ]
    created = []
    for payload in payloads:
        response = client.post("/api/v1/watchlist", json=payload)
        assert response.status_code in {201, 409}
        if response.status_code == 201:
            created.append(response.json())

    if created:
        high_risk_response = client.patch(
            f"/api/v1/watchlist/{created[0]['id']}",
            json={"latest_risk_level": "HIGH"},
        )
        assert high_risk_response.status_code == 200

    summary_response = client.get("/api/v1/watchlist/summary")

    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_items"] >= len(created)
    assert summary["count_by_market"]["US"] >= 2
    assert "WATCH" in summary["count_by_latest_signal"]
    assert summary["high_risk_count"] >= 1
    assert "data_quality_note" in summary
