def test_can_delete_medium_as_admin(client, asAdmin):
    res = client.delete("/medium/3")
    assert res.status_code == 200


# Note: This test doesn't really do anything since sqlite does not enforce
# foreign keys during testing. Feel free to use this to debug an issue
# when using postgres, though!
def test_can_delete_medium_even_if_it_still_has_tags(client, asAdmin):
    res = client.delete("/medium/4")
    assert res.status_code == 200


def test_cannot_delete_nonexistant_medium_as_admin(client, asAdmin):
    res = client.delete("/medium/9999999")
    assert res.status_code == 404
