def test_stats(client, asAdmin):
    res = client.get("/stats")
    assert res.status_code == 200
