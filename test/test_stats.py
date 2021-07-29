def test_stats(client, asAdmin):
    res = client.get("/stats")
    assert res.status_code == 200
    result_json = res.get_json()
    assert set(["s", "q", "e", "u"]) == set(result_json.keys())
