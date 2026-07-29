from seven.tools import web


class _Response:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code
        self.headers = {"content-type": "text/html"}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_web_search_falls_back_when_duckduckgo_has_no_results(monkeypatch):
    bing = (
        '<li class="b_algo"><h2><a '
        'href="https://example.test/python"><strong>Python</strong> docs</a></h2></li>'
    )
    responses = iter([_Response("<html>bot page</html>", 202), _Response(bing)])
    monkeypatch.setattr(web.requests, "get", lambda *args, **kwargs: next(responses))

    result = web.web_search("python", max_results=2)

    assert "Python docs" in result
    assert "https://example.test/python" in result


def test_decode_bing_url_recovers_destination():
    assert (
        web._decode_bing_url(
            "https://www.bing.com/ck/a?u=a1aHR0cHM6Ly93d3cucHl0aG9uLm9yZy8"
        )
        == "https://www.python.org/"
    )
