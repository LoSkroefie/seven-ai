import json

from seven.tools import browser


class _Runtime:
    stopped = False

    def stop(self):
        self.stopped = True


class _Context:
    closed = False

    def close(self):
        self.closed = True


class _Locator:
    def __init__(self):
        self.clicked = False
        self.filled = None
        self.pressed = None
        self.first = self

    def click(self, timeout):
        assert timeout == 15_000
        self.clicked = True

    def fill(self, text, timeout):
        assert timeout == 15_000
        self.filled = text

    def press(self, key, timeout):
        assert timeout == 15_000
        self.pressed = key

    def inner_text(self, timeout):
        assert timeout == 15_000
        return "Seven browser text"


class _Page:
    url = "https://example.com/after"

    def __init__(self):
        self.item = _Locator()
        self.waited = []

    def locator(self, selector):
        assert selector
        return self.item

    def wait_for_timeout(self, value):
        self.waited.append(value)

    def title(self):
        return "Example"


def _fake_open(_url):
    return _Runtime(), _Context(), _Page()


def test_browser_click_fill_extract_close_owned_runtime(monkeypatch):
    opened = []

    def factory(url):
        result = _fake_open(url)
        opened.append(result)
        return result

    monkeypatch.setattr(browser, "_open_page", factory)

    clicked = json.loads(browser.browser_click("example.com", "#go", 250))
    assert clicked["ok"] is True
    runtime, context, page = opened[-1]
    assert page.item.clicked is True
    assert page.waited == [250]
    assert runtime.stopped is True
    assert context.closed is True

    filled = json.loads(
        browser.browser_fill("example.com", "input[name=q]", "hello", submit=True)
    )
    assert filled["action"] == "fill_and_submit"
    runtime, context, page = opened[-1]
    assert page.item.filled == "hello"
    assert page.item.pressed == "Enter"
    assert runtime.stopped is True
    assert context.closed is True

    extracted = browser.browser_extract("example.com", "main", 500)
    header, text = extracted.split("\n\n", 1)
    assert json.loads(header)["ok"] is True
    assert text == "Seven browser text"


def test_browser_actions_validate_inputs_without_opening(monkeypatch):
    monkeypatch.setattr(
        browser,
        "_open_page",
        lambda _url: (_ for _ in ()).throw(AssertionError("must not open")),
    )
    assert browser.browser_click("example.com", "", 0).startswith("ERROR: selector")
    assert browser.browser_fill("example.com", "#x", "x" * 100_001).startswith(
        "ERROR: browser text"
    )
    assert browser.browser_extract("example.com", "x" * 1_001, 100).startswith(
        "ERROR: selector"
    )


def test_browser_status_declares_isolated_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("SEVEN_BROWSER_PROFILE", str(tmp_path / "profile"))
    status = json.loads(browser.browser_status())
    assert status["profile"] == str((tmp_path / "profile").resolve())
    assert status["existing_chrome_profile_used"] is False
