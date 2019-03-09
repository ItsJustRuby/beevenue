
def test_cannot_get_present_tag_as_user(client):
    res = client.get('/tag/u:overwatch')
    assert res.status_code == 401


def test_present_tag_returns_200(adminClient):
    res = adminClient.get('/tag/u:overwatch')
    assert res.status_code == 200


def test_missing_tag_returns_404(adminClient):
    res = adminClient.get('/tag/someUnknownTag')
    assert res.status_code == 404
