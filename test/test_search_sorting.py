from urllib import parse

import pytest


def _when_searching(c, query, page_number=1, page_size=10):
    q = parse.urlencode(
        {"q": query, "pageNumber": page_number, "pageSize": page_size}
    )
    print(q)
    return c.get(f"/search?{q}")


@pytest.mark.parametrize("prefix", ["sort:", "order:"])
@pytest.mark.parametrize(
    "term",
    ["id", "age", "filesize", "portrait", "landscape", "width", "height"],
)
@pytest.mark.parametrize("direction", ["", "_asc", "_desc"])
def test_search_sorting_try_all_sorters(
    client, asUser, prefix, term, direction
):
    query = f"+C {prefix}{term}{direction}"
    print(query)
    res = _when_searching(client, query)
    assert res.status_code == 200
    result = res.get_json()
    assert len(result["items"]) >= 1


def test_search_multiple_sorters_succeeds(client, asUser):
    res = _when_searching(client, f"+C sort:id order:width")
    assert res.status_code == 200
    result = res.get_json()
    assert len(result["items"]) >= 1
