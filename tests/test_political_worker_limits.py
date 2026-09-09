import pytest
from web_app.political_worker_limits import fetch_concurrency


@pytest.mark.parametrize("value,expected", [(None,4),("",4),("bad",4),("4",4),("6",6),("100",6),("0",1)])
def test_bounded_capacity_with_safe_default(monkeypatch,value,expected):
    if value is None:
        monkeypatch.delenv("POLITICAL_FETCH_CONCURRENCY",raising=False)
    else:
        monkeypatch.setenv("POLITICAL_FETCH_CONCURRENCY",value)
    assert fetch_concurrency()==expected
