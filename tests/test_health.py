def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200

    body = resp.get_json()
    assert body["status"] == "up"
    assert body["environment"] == "testing"


def test_blueprint_is_registered(app):
    # Regression test: the API blueprint used to be commented out.
    rules = {str(r) for r in app.url_map.iter_rules()}
    assert "/api/v1/ingest" in rules
    assert "/api/v1/query" in rules
    assert "/api/v1/stats" in rules
