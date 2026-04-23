def test_ingest_rejects_empty_body(client):
    resp = client.post("/api/v1/ingest", json={})
    assert resp.status_code == 400
    assert "s3_url" in resp.get_json()["fields"]


def test_ingest_rejects_non_s3_url(client):
    resp = client.post("/api/v1/ingest", json={"s3_url": "https://example.com/x.pdf"})
    assert resp.status_code == 400


def test_query_rejects_empty_string(client):
    resp = client.post("/api/v1/query", json={"query": "   "})
    assert resp.status_code == 400


def test_query_rejects_missing_field(client):
    resp = client.post("/api/v1/query", json={})
    assert resp.status_code == 400
    assert "query" in resp.get_json()["fields"]
