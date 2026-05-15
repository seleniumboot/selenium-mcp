"""
Assertion Tools — validate page state, element state, text, URL, title
Returns PASS/FAIL with detail — useful for AI-driven test verification.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from mcp.types import Tool

BY_MAP = {
    "css":          By.CSS_SELECTOR,
    "xpath":        By.XPATH,
    "id":           By.ID,
    "name":         By.NAME,
    "tag":          By.TAG_NAME,
    "class":        By.CLASS_NAME,
    "link":         By.LINK_TEXT,
    "partial_link": By.PARTIAL_LINK_TEXT,
}


class AssertionTools:
    def __init__(self, browser_tools):
        self.browser = browser_tools

    def _driver(self):
        return self.browser.get_driver()

    def _by(self, strategy: str):
        return BY_MAP.get(strategy, By.CSS_SELECTOR)

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="assert_title",
                description="Assert the page title equals or contains expected text.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "expected": {"type": "string"},
                        "exact": {"type": "boolean", "default": False}
                    },
                    "required": ["expected"],
                },
            ),
            Tool(
                name="assert_url",
                description="Assert the current URL equals or contains expected value.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "expected": {"type": "string"},
                        "exact": {"type": "boolean", "default": False}
                    },
                    "required": ["expected"],
                },
            ),
            Tool(
                name="assert_text",
                description="Assert element text equals or contains expected value.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string"},
                        "by": {"type": "string", "default": "css"},
                        "expected": {"type": "string"},
                        "exact": {"type": "boolean", "default": False},
                        "timeout": {"type": "integer", "default": 10}
                    },
                    "required": ["selector", "expected"],
                },
            ),
            Tool(
                name="assert_element_visible",
                description="Assert an element is visible on the page.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string"},
                        "by": {"type": "string", "default": "css"},
                        "timeout": {"type": "integer", "default": 10}
                    },
                    "required": ["selector"],
                },
            ),
            Tool(
                name="assert_element_not_visible",
                description="Assert an element is NOT visible (hidden or absent).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string"},
                        "by": {"type": "string", "default": "css"},
                        "timeout": {"type": "integer", "default": 3}
                    },
                    "required": ["selector"],
                },
            ),
            Tool(
                name="assert_attribute",
                description="Assert an element attribute has the expected value.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string"},
                        "by": {"type": "string", "default": "css"},
                        "attribute": {"type": "string"},
                        "expected": {"type": "string"},
                        "exact": {"type": "boolean", "default": True},
                        "timeout": {"type": "integer", "default": 10}
                    },
                    "required": ["selector", "attribute", "expected"],
                },
            ),
            Tool(
                name="assert_page_contains",
                description="Assert the full page source or visible text contains a string.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "source_only": {
                            "type": "boolean",
                            "default": False,
                            "description": "If true, checks page source; otherwise checks body visible text"
                        }
                    },
                    "required": ["text"],
                },
            ),
            Tool(
                name="assert_element_count",
                description="Assert number of elements matching selector equals expected count.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string"},
                        "by": {"type": "string", "default": "css"},
                        "expected_count": {"type": "integer"}
                    },
                    "required": ["selector", "expected_count"],
                },
            ),
        ]

    def get_handlers(self) -> dict:
        return {
            "assert_title":               self._assert_title,
            "assert_url":                 self._assert_url,
            "assert_text":                self._assert_text,
            "assert_element_visible":     self._assert_element_visible,
            "assert_element_not_visible": self._assert_element_not_visible,
            "assert_attribute":           self._assert_attribute,
            "assert_page_contains":       self._assert_page_contains,
            "assert_element_count":       self._assert_element_count,
        }

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #
    def _pass(self, msg): return f"✅ PASS | {msg}"
    def _fail(self, msg): return f"❌ FAIL | {msg}"

    # ------------------------------------------------------------------ #
    #  Handlers                                                            #
    # ------------------------------------------------------------------ #
    async def _assert_title(self, args: dict) -> str:
        actual = self._driver().title
        exp = args["expected"]
        ok = (actual == exp) if args.get("exact", False) else (exp.lower() in actual.lower())
        return self._pass(f"title='{actual}'") if ok else self._fail(f"expected='{exp}' | actual='{actual}'")

    async def _assert_url(self, args: dict) -> str:
        actual = self._driver().current_url
        exp = args["expected"]
        ok = (actual == exp) if args.get("exact", False) else (exp in actual)
        return self._pass(f"url='{actual}'") if ok else self._fail(f"expected='{exp}' | actual='{actual}'")

    async def _assert_text(self, args: dict) -> str:
        by = self._by(args.get("by", "css"))
        timeout = args.get("timeout", 10)
        try:
            el = WebDriverWait(self._driver(), timeout).until(
                EC.visibility_of_element_located((by, args["selector"]))
            )
        except Exception:
            return self._fail(f"element '{args['selector']}' not found within {timeout}s")
        actual = el.text
        exp = args["expected"]
        ok = (actual == exp) if args.get("exact", False) else (exp.lower() in actual.lower())
        return self._pass(f"text='{actual}'") if ok else self._fail(f"expected='{exp}' | actual='{actual}'")

    async def _assert_element_visible(self, args: dict) -> str:
        by = self._by(args.get("by", "css"))
        timeout = args.get("timeout", 10)
        try:
            WebDriverWait(self._driver(), timeout).until(
                EC.visibility_of_element_located((by, args["selector"]))
            )
            return self._pass(f"'{args['selector']}' is visible")
        except Exception:
            return self._fail(f"'{args['selector']}' is NOT visible")

    async def _assert_element_not_visible(self, args: dict) -> str:
        by = self._by(args.get("by", "css"))
        timeout = args.get("timeout", 3)
        try:
            WebDriverWait(self._driver(), timeout).until(
                EC.invisibility_of_element_located((by, args["selector"]))
            )
            return self._pass(f"'{args['selector']}' is not visible")
        except Exception:
            return self._fail(f"'{args['selector']}' IS visible (expected hidden)")

    async def _assert_attribute(self, args: dict) -> str:
        by = self._by(args.get("by", "css"))
        timeout = args.get("timeout", 10)
        try:
            el = WebDriverWait(self._driver(), timeout).until(
                EC.presence_of_element_located((by, args["selector"]))
            )
        except Exception:
            return self._fail(f"element '{args['selector']}' not found within {timeout}s")
        actual = el.get_attribute(args["attribute"])
        exp = args["expected"]
        ok = (actual == exp) if args.get("exact", True) else (exp in (actual or ""))
        return self._pass(f"{args['attribute']}='{actual}'") if ok else self._fail(f"expected='{exp}' | actual='{actual}'")

    async def _assert_page_contains(self, args: dict) -> str:
        text = args["text"]
        if args.get("source_only", False):
            content = self._driver().page_source
        else:
            content = self._driver().find_element(By.TAG_NAME, "body").text
        ok = text.lower() in content.lower()
        return self._pass(f"page contains '{text}'") if ok else self._fail(f"'{text}' not found on page")

    async def _assert_element_count(self, args: dict) -> str:
        by = self._by(args.get("by", "css"))
        els = self._driver().find_elements(by, args["selector"])
        actual = len(els)
        exp = args["expected_count"]
        ok = actual == exp
        return self._pass(f"count={actual}") if ok else self._fail(f"expected={exp} | actual={actual}")
