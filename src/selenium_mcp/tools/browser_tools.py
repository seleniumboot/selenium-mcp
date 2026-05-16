"""
Browser Tools — start, stop, navigate, screenshot, window management,
cookies, localStorage/sessionStorage, console logs, mobile emulation, page scroll
"""

import asyncio
import base64
import io
import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from mcp.types import Tool

_DEVICES = {
    "iphone_se":  {"width": 375,  "height": 667,  "pixelRatio": 2, "mobile": True},
    "iphone_12":  {"width": 390,  "height": 844,  "pixelRatio": 3, "mobile": True},
    "ipad":       {"width": 768,  "height": 1024, "pixelRatio": 2, "mobile": False},
    "galaxy_s20": {"width": 360,  "height": 800,  "pixelRatio": 3, "mobile": True},
    "pixel_5":    {"width": 393,  "height": 851,  "pixelRatio": 2, "mobile": True},
    "desktop_hd": {"width": 1920, "height": 1080, "pixelRatio": 1, "mobile": False},
}


class BrowserTools:
    def __init__(self):
        self.driver = None
        self._session_log = []
        self._healer_cache: dict[str, tuple[str, str]] = {}

    # ------------------------------------------------------------------ #
    #  Session helpers                                                     #
    # ------------------------------------------------------------------ #
    def record(self, action: str, **kwargs):
        self._session_log.append({"action": action, **kwargs})

    def get_driver(self):
        if not self.driver:
            opts = ChromeOptions()
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})
            self.driver = webdriver.Chrome(options=opts)
            self.record("start_browser", browser="chrome", headless=False)
        return self.driver

    # ------------------------------------------------------------------ #
    #  MCP tool definitions                                                #
    # ------------------------------------------------------------------ #
    def get_tools(self) -> list[Tool]:
        return [
            # ── Browser lifecycle ────────────────────────────────────── #
            Tool(
                name="start_browser",
                description="Start a browser session. Optional — any tool will auto-start Chrome if no browser is open. Use this to choose Firefox, enable headless mode, or set a custom window size.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "browser":     {"type": "string", "enum": ["chrome", "firefox"], "default": "chrome"},
                        "headless":    {"type": "boolean", "default": False},
                        "window_size": {"type": "string", "description": "e.g. 1920x1080", "default": "1920x1080"},
                    },
                },
            ),
            Tool(
                name="navigate",
                description="Navigate the browser to a URL.",
                inputSchema={
                    "type": "object",
                    "properties": {"url": {"type": "string"}},
                    "required": ["url"],
                },
            ),
            Tool(
                name="take_screenshot",
                description="Take a screenshot and return it as base64.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_page_source",
                description="Return the current page HTML source.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_page_title",
                description="Return the current page title.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_current_url",
                description="Return the current URL.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="close_browser",
                description="Close and quit the browser session.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="go_back",
                description="Navigate back in browser history.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="go_forward",
                description="Navigate forward in browser history.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="refresh",
                description="Refresh the current page.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="execute_script",
                description="Execute JavaScript in the browser.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "script": {"type": "string"},
                        "args":   {"type": "array", "default": []},
                    },
                    "required": ["script"],
                },
            ),
            # ── Window / tab management ──────────────────────────────── #
            Tool(
                name="switch_to_window",
                description="Switch to a browser window/tab by index.",
                inputSchema={
                    "type": "object",
                    "properties": {"index": {"type": "integer", "default": 0}},
                },
            ),
            Tool(
                name="open_new_tab",
                description="Open a new browser tab, optionally navigating to a URL.",
                inputSchema={
                    "type": "object",
                    "properties": {"url": {"type": "string", "description": "URL to open in the new tab (optional)"}},
                },
            ),
            Tool(
                name="close_current_tab",
                description="Close the currently active tab and switch to the previous one.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="list_windows",
                description="List all open browser tabs/windows with their index, title, and URL.",
                inputSchema={"type": "object", "properties": {}},
            ),
            # ── Page scroll ──────────────────────────────────────────── #
            Tool(
                name="scroll_to_top",
                description="Scroll the page to the very top.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="scroll_to_bottom",
                description="Scroll the page to the very bottom.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="scroll_by",
                description="Scroll the page by a given number of pixels (positive = down/right).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "default": 0, "description": "Horizontal pixels"},
                        "y": {"type": "integer", "default": 300, "description": "Vertical pixels"},
                    },
                },
            ),
            # ── Mobile emulation ─────────────────────────────────────── #
            Tool(
                name="emulate_device",
                description="Emulate a mobile device using Chrome DevTools Protocol. Adjusts viewport, pixel ratio, and touch.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device": {
                            "type": "string",
                            "enum": list(_DEVICES.keys()),
                            "description": "Preset device name",
                        },
                        "width":       {"type": "integer", "description": "Custom width (overrides device preset)"},
                        "height":      {"type": "integer", "description": "Custom height"},
                        "mobile":      {"type": "boolean", "description": "Mobile flag"},
                        "pixel_ratio": {"type": "number", "default": 2},
                    },
                },
            ),
            # ── Console logs ─────────────────────────────────────────── #
            Tool(
                name="get_console_logs",
                description="Return browser console logs (errors, warnings, info). Chrome only.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "level": {
                            "type": "string",
                            "enum": ["ALL", "SEVERE", "WARNING", "INFO"],
                            "default": "ALL",
                        }
                    },
                },
            ),
            # ── Cookies ──────────────────────────────────────────────── #
            Tool(
                name="get_cookies",
                description="Return all cookies for the current page, or a single cookie by name.",
                inputSchema={
                    "type": "object",
                    "properties": {"name": {"type": "string", "description": "Cookie name (optional — omit for all)"}},
                },
            ),
            Tool(
                name="set_cookie",
                description="Set a cookie on the current page.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name":   {"type": "string"},
                        "value":  {"type": "string"},
                        "domain": {"type": "string"},
                        "path":   {"type": "string", "default": "/"},
                    },
                    "required": ["name", "value"],
                },
            ),
            Tool(
                name="delete_cookie",
                description="Delete a specific cookie by name.",
                inputSchema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            ),
            Tool(
                name="delete_all_cookies",
                description="Delete all cookies for the current session.",
                inputSchema={"type": "object", "properties": {}},
            ),
            # ── Local / session storage ───────────────────────────────── #
            Tool(
                name="get_local_storage",
                description="Get a value from localStorage, or return all keys if no key is given.",
                inputSchema={
                    "type": "object",
                    "properties": {"key": {"type": "string", "description": "localStorage key (omit for all)"}},
                },
            ),
            Tool(
                name="set_local_storage",
                description="Set a localStorage key-value pair.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "key":   {"type": "string"},
                        "value": {"type": "string"},
                    },
                    "required": ["key", "value"],
                },
            ),
            Tool(
                name="get_session_storage",
                description="Get a value from sessionStorage, or return all keys if no key is given.",
                inputSchema={
                    "type": "object",
                    "properties": {"key": {"type": "string", "description": "sessionStorage key (omit for all)"}},
                },
            ),
            Tool(
                name="set_session_storage",
                description="Set a sessionStorage key-value pair.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "key":   {"type": "string"},
                        "value": {"type": "string"},
                    },
                    "required": ["key", "value"],
                },
            ),
            # ── Page inspection ──────────────────────────────────────── #
            Tool(
                name="inspect_page",
                description=(
                    "Discover all interactive elements on the current page — inputs, buttons, "
                    "selects, checkboxes, textareas, and links — with their best CSS selectors and labels. "
                    "Use this before writing locators so the AI knows exactly what's on the page."
                ),
                inputSchema={"type": "object", "properties": {}},
            ),
            # ── Network interception ─────────────────────────────────── #
            Tool(
                name="get_network_logs",
                description="Return captured XHR/fetch network requests (method, URL, status, timing). Chrome only.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url_filter": {"type": "string", "description": "Only show requests whose URL contains this string"},
                        "method":     {"type": "string", "description": "Filter by HTTP method e.g. GET, POST"},
                        "limit":      {"type": "integer", "default": 50, "description": "Max requests to return"},
                    },
                },
            ),
            Tool(
                name="mock_response",
                description=(
                    "Intercept fetch/XHR requests matching a URL pattern and return a canned response. "
                    "Useful for testing without a real backend. Injection survives until the page is reloaded."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url_pattern":   {"type": "string", "description": "Substring or regex pattern to match the request URL"},
                        "status":        {"type": "integer", "default": 200},
                        "body":          {"type": "string", "default": "{}", "description": "Response body string"},
                        "content_type":  {"type": "string", "default": "application/json"},
                    },
                    "required": ["url_pattern"],
                },
            ),
            Tool(
                name="clear_mock_responses",
                description="Remove all active mock response rules injected by mock_response.",
                inputSchema={"type": "object", "properties": {}},
            ),
            # ── Visual regression ─────────────────────────────────────── #
            Tool(
                name="compare_screenshot",
                description=(
                    "Compare the current page screenshot against a saved baseline. "
                    "On first run (or with update_baseline=true) saves the baseline. "
                    "Returns the pixel diff percentage. Install Pillow for accurate pixel comparison."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name":            {"type": "string", "default": "default", "description": "Baseline name e.g. 'homepage'"},
                        "update_baseline": {"type": "boolean", "default": False},
                        "threshold":       {"type": "number", "default": 0.1, "description": "Max allowed diff % before failure"},
                    },
                },
            ),
            # ── Accessibility ─────────────────────────────────────────── #
            Tool(
                name="check_accessibility",
                description=(
                    "Run a built-in accessibility audit on the current page. "
                    "Checks for missing alt text, unlabelled inputs, empty buttons/links, "
                    "missing page title, HTML lang, heading structure, and keyboard accessibility."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "level": {
                            "type": "string",
                            "enum": ["all", "critical", "serious", "moderate", "minor"],
                            "default": "all",
                        }
                    },
                },
            ),
            # ── Network idle ─────────────────────────────────────────── #
            Tool(
                name="wait_for_network_idle",
                description=(
                    "Wait until there are no active XHR/fetch requests for a quiet period. "
                    "Essential for SPAs and pages that load data asynchronously. "
                    "Also waits for document.readyState to be 'complete'."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "idle_time_ms": {
                            "type": "integer",
                            "default": 500,
                            "description": "Milliseconds of network silence required",
                        },
                        "timeout": {
                            "type": "integer",
                            "default": 15,
                            "description": "Max seconds to wait before giving up",
                        },
                        "max_inflight": {
                            "type": "integer",
                            "default": 0,
                            "description": "Tolerate up to N in-flight requests (0 = fully idle)",
                        },
                    },
                },
            ),
        ]

    # ------------------------------------------------------------------ #
    #  Handlers                                                            #
    # ------------------------------------------------------------------ #
    def get_handlers(self) -> dict:
        return {
            "start_browser":       self._start_browser,
            "navigate":            self._navigate,
            "take_screenshot":     self._take_screenshot,
            "get_page_source":     self._get_page_source,
            "get_page_title":      self._get_page_title,
            "get_current_url":     self._get_current_url,
            "close_browser":       self._close_browser,
            "go_back":             self._go_back,
            "go_forward":          self._go_forward,
            "refresh":             self._refresh,
            "execute_script":      self._execute_script,
            "switch_to_window":    self._switch_to_window,
            "open_new_tab":        self._open_new_tab,
            "close_current_tab":   self._close_current_tab,
            "list_windows":        self._list_windows,
            "scroll_to_top":       self._scroll_to_top,
            "scroll_to_bottom":    self._scroll_to_bottom,
            "scroll_by":           self._scroll_by,
            "emulate_device":      self._emulate_device,
            "get_console_logs":    self._get_console_logs,
            "get_cookies":         self._get_cookies,
            "set_cookie":          self._set_cookie,
            "delete_cookie":       self._delete_cookie,
            "delete_all_cookies":  self._delete_all_cookies,
            "get_local_storage":   self._get_local_storage,
            "set_local_storage":   self._set_local_storage,
            "get_session_storage":    self._get_session_storage,
            "set_session_storage":    self._set_session_storage,
            "wait_for_network_idle":  self._wait_for_network_idle,
            "inspect_page":           self._inspect_page,
            "get_network_logs":       self._get_network_logs,
            "mock_response":          self._mock_response,
            "clear_mock_responses":   self._clear_mock_responses,
            "compare_screenshot":     self._compare_screenshot,
            "check_accessibility":    self._check_accessibility,
        }

    # ── Browser lifecycle ────────────────────────────────────────────── #

    async def _start_browser(self, args: dict) -> str:
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

        browser = args.get("browser", "chrome")
        headless = args.get("headless", False)
        try:
            w, h = args.get("window_size", "1920x1080").lower().replace(" ", "").split("x")
            w, h = int(w), int(h)
        except (ValueError, AttributeError):
            w, h = 1920, 1080

        if browser == "chrome":
            opts = ChromeOptions()
            if headless:
                opts.add_argument("--headless=new")
            opts.add_argument(f"--window-size={w},{h}")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})
            self.driver = webdriver.Chrome(options=opts)
        elif browser == "firefox":
            opts = FirefoxOptions()
            if headless:
                opts.add_argument("--headless")
            self.driver = webdriver.Firefox(options=opts)
            self.driver.set_window_size(w, h)
        else:
            return f"Unsupported browser: {browser}"

        self._session_log = []
        self.record("start_browser", browser=browser, headless=headless)
        return f"✅ {browser.capitalize()} started ({w}x{h}, headless={headless})"

    async def _navigate(self, args: dict) -> str:
        url = args["url"]
        self.get_driver().get(url)
        self.record("navigate", url=url)
        return f"✅ Navigated to {url}"

    async def _take_screenshot(self, args: dict) -> str:
        png = self.get_driver().get_screenshot_as_png()
        b64 = base64.b64encode(png).decode()
        return f"screenshot:base64:{b64}"

    async def _get_page_source(self, args: dict) -> str:
        return self.get_driver().page_source

    async def _get_page_title(self, args: dict) -> str:
        return self.get_driver().title

    async def _get_current_url(self, args: dict) -> str:
        return self.get_driver().current_url

    async def _close_browser(self, args: dict) -> str:
        if self.driver:
            self.driver.quit()
            self.driver = None
        return "✅ Browser closed"

    async def _go_back(self, args: dict) -> str:
        self.get_driver().back()
        self.record("go_back")
        return "✅ Navigated back"

    async def _go_forward(self, args: dict) -> str:
        self.get_driver().forward()
        self.record("go_forward")
        return "✅ Navigated forward"

    async def _refresh(self, args: dict) -> str:
        self.get_driver().refresh()
        self.record("refresh")
        return "✅ Page refreshed"

    async def _execute_script(self, args: dict) -> str:
        result = self.get_driver().execute_script(args["script"], *args.get("args", []))
        self.record("execute_script", script=args["script"])
        return str(result)

    # ── Window / tab management ──────────────────────────────────────── #

    async def _switch_to_window(self, args: dict) -> str:
        idx = args.get("index", 0)
        handles = self.get_driver().window_handles
        if idx >= len(handles):
            return f"No window at index {idx}. Available: {len(handles)}"
        self.get_driver().switch_to.window(handles[idx])
        return f"✅ Switched to window {idx}"

    async def _open_new_tab(self, args: dict) -> str:
        url = args.get("url", "")
        driver = self.get_driver()
        driver.execute_script("window.open(arguments[0]);", url)
        driver.switch_to.window(driver.window_handles[-1])
        self.record("open_new_tab", url=url)
        return f"✅ Opened new tab{' at ' + url if url else ''} (now active)"

    async def _close_current_tab(self, args: dict) -> str:
        driver = self.get_driver()
        handles = driver.window_handles
        if len(handles) <= 1:
            return "Only one tab open — use close_browser to quit."
        driver.close()
        driver.switch_to.window(driver.window_handles[-1])
        self.record("close_current_tab")
        return "✅ Closed current tab, switched to previous"

    async def _list_windows(self, args: dict) -> str:
        driver = self.get_driver()
        current = driver.current_window_handle
        lines = []
        for i, handle in enumerate(driver.window_handles):
            driver.switch_to.window(handle)
            marker = " ◄ current" if handle == current else ""
            lines.append(f"[{i}] {driver.title!r} — {driver.current_url}{marker}")
        driver.switch_to.window(current)
        return "\n".join(lines) if lines else "No windows open."

    # ── Page scroll ──────────────────────────────────────────────────── #

    async def _scroll_to_top(self, args: dict) -> str:
        self.get_driver().execute_script("window.scrollTo(0, 0);")
        self.record("scroll_to_top")
        return "✅ Scrolled to top"

    async def _scroll_to_bottom(self, args: dict) -> str:
        self.get_driver().execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.record("scroll_to_bottom")
        return "✅ Scrolled to bottom"

    async def _scroll_by(self, args: dict) -> str:
        x = args.get("x", 0)
        y = args.get("y", 300)
        self.get_driver().execute_script(f"window.scrollBy({x}, {y});")
        self.record("scroll_by", x=x, y=y)
        return f"✅ Scrolled by ({x}, {y})"

    # ── Mobile emulation ─────────────────────────────────────────────── #

    async def _emulate_device(self, args: dict) -> str:
        device_name = args.get("device", "")
        preset = _DEVICES.get(device_name, {})

        width  = args.get("width",  preset.get("width",  390))
        height = args.get("height", preset.get("height", 844))
        mobile = args.get("mobile", preset.get("mobile", True))
        dpr    = args.get("pixel_ratio", preset.get("pixelRatio", 2))

        self.get_driver().execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
            "width": width, "height": height,
            "deviceScaleFactor": dpr, "mobile": mobile,
        })
        label = device_name or f"{width}x{height}"
        self.record("emulate_device", device=label, width=width, height=height, mobile=mobile)
        return f"✅ Emulating {label} ({width}x{height}, mobile={mobile}, dpr={dpr})"

    # ── Console logs ─────────────────────────────────────────────────── #

    async def _get_console_logs(self, args: dict) -> str:
        level = args.get("level", "ALL").upper()
        try:
            logs = self.get_driver().get_log("browser")
        except Exception as e:
            return f"Could not retrieve console logs: {e}"
        if not logs:
            return "No console logs."
        filtered = logs if level == "ALL" else [l for l in logs if l.get("level") == level]
        lines = [f"[{l['level']}] {l['message']}" for l in filtered]
        return "\n".join(lines) if lines else f"No {level} logs."

    # ── Cookies ──────────────────────────────────────────────────────── #

    async def _get_cookies(self, args: dict) -> str:
        name = args.get("name")
        driver = self.get_driver()
        if name:
            cookie = driver.get_cookie(name)
            return json.dumps(cookie, indent=2) if cookie else f"Cookie '{name}' not found."
        cookies = driver.get_cookies()
        return json.dumps(cookies, indent=2) if cookies else "No cookies."

    async def _set_cookie(self, args: dict) -> str:
        cookie: dict = {"name": args["name"], "value": args["value"]}
        if "domain" in args:
            cookie["domain"] = args["domain"]
        cookie["path"] = args.get("path", "/")
        self.get_driver().add_cookie(cookie)
        self.record("set_cookie", name=args["name"], value=args["value"])
        return f"✅ Cookie '{args['name']}' set"

    async def _delete_cookie(self, args: dict) -> str:
        self.get_driver().delete_cookie(args["name"])
        return f"✅ Cookie '{args['name']}' deleted"

    async def _delete_all_cookies(self, args: dict) -> str:
        self.get_driver().delete_all_cookies()
        return "✅ All cookies deleted"

    # ── Local / session storage ───────────────────────────────────────── #

    async def _get_local_storage(self, args: dict) -> str:
        key = args.get("key")
        driver = self.get_driver()
        if key:
            val = driver.execute_script(f"return window.localStorage.getItem(arguments[0]);", key)
            return str(val) if val is not None else f"Key '{key}' not found in localStorage."
        all_items = driver.execute_script(
            "return Object.fromEntries(Object.entries(window.localStorage));"
        )
        return json.dumps(all_items, indent=2) if all_items else "localStorage is empty."

    async def _set_local_storage(self, args: dict) -> str:
        self.get_driver().execute_script(
            "window.localStorage.setItem(arguments[0], arguments[1]);",
            args["key"], args["value"]
        )
        self.record("set_local_storage", key=args["key"], value=args["value"])
        return f"✅ localStorage['{args['key']}'] = '{args['value']}'"

    async def _get_session_storage(self, args: dict) -> str:
        key = args.get("key")
        driver = self.get_driver()
        if key:
            val = driver.execute_script("return window.sessionStorage.getItem(arguments[0]);", key)
            return str(val) if val is not None else f"Key '{key}' not found in sessionStorage."
        all_items = driver.execute_script(
            "return Object.fromEntries(Object.entries(window.sessionStorage));"
        )
        return json.dumps(all_items, indent=2) if all_items else "sessionStorage is empty."

    async def _set_session_storage(self, args: dict) -> str:
        self.get_driver().execute_script(
            "window.sessionStorage.setItem(arguments[0], arguments[1]);",
            args["key"], args["value"]
        )
        self.record("set_session_storage", key=args["key"], value=args["value"])
        return f"✅ sessionStorage['{args['key']}'] = '{args['value']}'"

    # ── Network idle ─────────────────────────────────────────────────── #

    _INJECT_TRACKER = """
    if (!window.__smcpNet) {
        window.__smcpNet = { active: 0, last: Date.now() };
        const _track = (d) => {
            window.__smcpNet.active = Math.max(0, window.__smcpNet.active + d);
            window.__smcpNet.last = Date.now();
        };
        const _xhrOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function() {
            _track(1);
            this.addEventListener('loadend', () => _track(-1));
            _xhrOpen.apply(this, arguments);
        };
        if (window.fetch) {
            const _fetch = window.fetch;
            window.fetch = function() {
                _track(1);
                return _fetch.apply(this, arguments).finally(() => _track(-1));
            };
        }
    }
    """

    _POLL_TRACKER = """
    const t = window.__smcpNet || { active: 0, last: Date.now() };
    return { active: t.active, quietMs: Date.now() - t.last, readyState: document.readyState };
    """

    async def _wait_for_network_idle(self, args: dict) -> str:
        idle_ms      = args.get("idle_time_ms", 500)
        timeout      = args.get("timeout", 15)
        max_inflight = args.get("max_inflight", 0)
        driver = self.get_driver()

        driver.execute_script(self._INJECT_TRACKER)

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            state     = driver.execute_script(self._POLL_TRACKER)
            active    = state.get("active", 0)
            quiet_ms  = state.get("quietMs", 0)
            ready     = state.get("readyState", "")

            if ready == "complete" and active <= max_inflight and quiet_ms >= idle_ms:
                elapsed = round(time.monotonic() - (deadline - timeout), 2)
                return (
                    f"✅ Network idle — active={active}, "
                    f"quiet for {quiet_ms}ms, readyState={ready} ({elapsed}s)"
                )
            await asyncio.sleep(0.1)

        state = driver.execute_script(self._POLL_TRACKER)
        return (
            f"⚠️ Timed out after {timeout}s — "
            f"active={state.get('active', '?')}, readyState={state.get('readyState', '?')}"
        )

    # ── Page inspection ──────────────────────────────────────────────── #

    _INSPECT_SCRIPT = """
    function bestSel(el) {
        if (el.id) return '#' + CSS.escape(el.id);
        if (el.name) return '[name="' + el.name + '"]';
        const cls = (el.className || '').trim().split(/\\s+/)[0];
        if (cls) return el.tagName.toLowerCase() + '.' + CSS.escape(cls);
        return el.tagName.toLowerCase();
    }
    function labelFor(el) {
        if (el.id) {
            const l = document.querySelector('label[for="' + el.id + '"]');
            if (l) return l.textContent.trim();
        }
        const p = el.closest('label');
        if (p) return p.textContent.replace(el.value||'','').trim();
        return el.getAttribute('placeholder') || el.getAttribute('aria-label') || el.name || '';
    }
    const r = {url: location.href, inputs:[], checkboxes:[], radios:[], textareas:[], selects:[], buttons:[], links:[]};
    const vis = el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);

    document.querySelectorAll('input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]):not([type="submit"]):not([type="button"]):not([type="image"]):not([type="reset"])').forEach(el => {
        if (!vis(el)) return;
        r.inputs.push({selector: bestSel(el), type: el.type||'text', label: labelFor(el)});
    });
    document.querySelectorAll('input[type="checkbox"]').forEach(el => {
        r.checkboxes.push({selector: bestSel(el), label: labelFor(el), checked: el.checked});
    });
    document.querySelectorAll('input[type="radio"]').forEach(el => {
        r.radios.push({selector: bestSel(el), label: labelFor(el), checked: el.checked, value: el.value});
    });
    document.querySelectorAll('textarea').forEach(el => {
        if (!vis(el)) return;
        r.textareas.push({selector: bestSel(el), label: labelFor(el)});
    });
    document.querySelectorAll('select').forEach(el => {
        if (!vis(el)) return;
        const opts = Array.from(el.options).map(o => o.text.trim()).filter(Boolean);
        r.selects.push({selector: bestSel(el), label: labelFor(el), options: opts});
    });
    document.querySelectorAll('button,input[type="submit"],input[type="button"],input[type="reset"]').forEach(el => {
        if (!vis(el)) return;
        r.buttons.push({selector: bestSel(el), text: (el.textContent||el.value||'').trim(), type: el.type||'button'});
    });
    document.querySelectorAll('a[href]').forEach(el => {
        if (!vis(el)) return;
        const text = el.textContent.trim();
        if (!text) return;
        r.links.push({selector: bestSel(el), text: text.substring(0,60), href: el.getAttribute('href')});
    });
    return r;
    """

    async def _inspect_page(self, args: dict) -> str:
        result = self.get_driver().execute_script(self._INSPECT_SCRIPT)
        lines = [f"Page: {result['url']}", ""]

        def section(title, items, fmt):
            if not items:
                return
            lines.append(f"{title} ({len(items)}):")
            for el in items:
                lines.append("  " + fmt(el))

        section("INPUTS", result["inputs"],
                lambda e: f"[{e['type']}] {e['selector']}" + (f" — {e['label']}" if e["label"] else ""))
        section("CHECKBOXES", result["checkboxes"],
                lambda e: f"{e['selector']} — {e['label'] or 'unlabeled'} (checked={e['checked']})")
        section("RADIOS", result["radios"],
                lambda e: f"{e['selector']} value='{e['value']}'" + (" ✓" if e["checked"] else ""))
        section("TEXTAREAS", result["textareas"],
                lambda e: f"{e['selector']}" + (f" — {e['label']}" if e["label"] else ""))
        section("SELECTS", result["selects"],
                lambda e: f"{e['selector']} — {e['label'] or 'unlabeled'} → [{', '.join(e['options'][:6])}"
                          + (f" +{len(e['options'])-6} more" if len(e['options']) > 6 else "") + "]")

        if result["buttons"]:
            lines.append(f"\nBUTTONS ({len(result['buttons'])}):")
            for e in result["buttons"]:
                lines.append(f"  [{e['type']}] {e['selector']} — '{e['text']}'")

        if result["links"]:
            shown = result["links"][:15]
            lines.append(f"\nLINKS ({len(result['links'])}):")
            for e in shown:
                lines.append(f"  {e['selector']} — '{e['text']}' → {e['href']}")
            if len(result["links"]) > 15:
                lines.append(f"  … +{len(result['links'])-15} more")

        total = sum(len(result[k]) for k in result if k != "url")
        if total == 0:
            return f"No interactive elements found on {result['url']}"
        return "\n".join(lines)

    # ── Network interception ─────────────────────────────────────────── #

    async def _get_network_logs(self, args: dict) -> str:
        url_filter    = args.get("url_filter", "")
        method_filter = args.get("method", "").upper()
        limit         = args.get("limit", 50)

        try:
            perf_logs = self.get_driver().get_log("performance")
        except Exception as e:
            return f"Could not get performance logs: {e}"

        requests: dict = {}
        for entry in perf_logs:
            try:
                msg    = json.loads(entry["message"])["message"]
                method = msg.get("method", "")
                params = msg.get("params", {})
                rid    = params.get("requestId", "")

                if method == "Network.requestWillBeSent":
                    req = params.get("request", {})
                    requests[rid] = {
                        "url":    req.get("url", ""),
                        "method": req.get("method", "GET"),
                        "status": None,
                        "ms":     None,
                        "ts":     params.get("timestamp", 0),
                    }
                elif method == "Network.responseReceived" and rid in requests:
                    resp = params.get("response", {})
                    requests[rid]["status"] = resp.get("status")
                    elapsed = params.get("timestamp", requests[rid]["ts"]) - requests[rid]["ts"]
                    requests[rid]["ms"] = round(elapsed * 1000)
            except Exception:
                continue

        entries = list(requests.values())
        if url_filter:
            entries = [e for e in entries if url_filter.lower() in e["url"].lower()]
        if method_filter:
            entries = [e for e in entries if e["method"] == method_filter]
        entries = entries[-limit:]

        if not entries:
            return "No network requests captured." + ("" if perf_logs else " Performance logging requires Chrome.")

        lines = [f"Network requests ({len(entries)}):"]
        for e in entries:
            status = str(e["status"]) if e["status"] else "---"
            ms     = f"{e['ms']}ms" if e["ms"] is not None else "?"
            url    = e["url"][:80] + ("…" if len(e["url"]) > 80 else "")
            lines.append(f"  {e['method']:<6} {status}  {url}  ({ms})")
        return "\n".join(lines)

    _MOCK_INJECT = """
    window.__smcpMocks = window.__smcpMocks || [];
    window.__smcpMocks.push({pattern: arguments[0], status: arguments[1], body: arguments[2], ct: arguments[3]});
    if (!window.__smcpMockOn) {
        window.__smcpMockOn = true;
        const _f = window.fetch;
        window.fetch = function(url, opts) {
            const u = typeof url === 'string' ? url : (url && url.url) || '';
            for (const m of (window.__smcpMocks || [])) {
                try { if (u.includes(m.pattern) || new RegExp(m.pattern).test(u))
                    return Promise.resolve(new Response(m.body, {status: m.status, headers: {'Content-Type': m.ct}}));
                } catch(e) {}
            }
            return _f.apply(this, arguments);
        };
    }
    return window.__smcpMocks.length;
    """

    async def _mock_response(self, args: dict) -> str:
        pattern = args["url_pattern"]
        status  = args.get("status", 200)
        body    = args.get("body", "{}")
        ct      = args.get("content_type", "application/json")
        count   = self.get_driver().execute_script(self._MOCK_INJECT, pattern, status, body, ct)
        self.record("mock_response", url_pattern=pattern, status=status)
        return f"✅ Mock added ({count} active): '{pattern}' → {status} {ct}"

    async def _clear_mock_responses(self, args: dict) -> str:
        self.get_driver().execute_script(
            "window.__smcpMocks = []; window.__smcpMockOn = false;"
        )
        return "✅ All mock responses cleared"

    # ── Visual regression ─────────────────────────────────────────────── #

    async def _compare_screenshot(self, args: dict) -> str:
        name      = args.get("name", "default").replace("/", "_")
        update    = args.get("update_baseline", False)
        threshold = args.get("threshold", 0.1)

        baseline_dir = os.path.join(os.getcwd(), ".smcp_baselines")
        os.makedirs(baseline_dir, exist_ok=True)
        baseline_path = os.path.join(baseline_dir, f"{name}.png")

        current = self.get_driver().get_screenshot_as_png()

        if update or not os.path.exists(baseline_path):
            with open(baseline_path, "wb") as f:
                f.write(current)
            return f"✅ Baseline saved: '{name}' ({len(current):,} bytes → {baseline_path})"

        with open(baseline_path, "rb") as f:
            baseline = f.read()

        try:
            from PIL import Image, ImageChops
            img1 = Image.open(io.BytesIO(baseline)).convert("RGB")
            img2 = Image.open(io.BytesIO(current)).convert("RGB")

            if img1.size != img2.size:
                return (f"⚠️ Size mismatch — baseline {img1.size} vs current {img2.size}. "
                        f"Use update_baseline=true to reset.")

            diff    = ImageChops.difference(img1, img2)
            pixels  = list(diff.getdata())
            changed = sum(1 for p in pixels if any(c > 10 for c in p))
            pct     = round(100.0 * changed / len(pixels), 3)

            if pct <= threshold:
                return f"✅ Match ({pct:.3f}% diff ≤ {threshold}% threshold) — '{name}'"
            return f"❌ Diff detected ({pct:.3f}% > {threshold}% threshold) — '{name}'"

        except ImportError:
            if current == baseline:
                return f"✅ Identical (byte match) — '{name}' (install Pillow for pixel diff)"
            diff  = sum(a != b for a, b in zip(current, baseline))
            pct   = round(100.0 * diff / max(len(current), len(baseline)), 2)
            verdict = "✅" if pct <= threshold else "⚠️"
            return (f"{verdict} {pct:.2f}% byte diff — '{name}' "
                    f"(install Pillow for accurate pixel comparison: pip install Pillow)")

    # ── Accessibility audit ───────────────────────────────────────────── #

    _A11Y_SCRIPT = """
    const issues = [];
    const $ = s => Array.from(document.querySelectorAll(s));
    const el2str = el => el.outerHTML.substring(0, 100).replace(/\\n/g, ' ');

    if (!document.title || !document.title.trim())
        issues.push({impact:'serious', id:'document-title', desc:'Page must have a title', el:'<title>'});

    if (!document.documentElement.lang)
        issues.push({impact:'serious', id:'html-has-lang', desc:'<html> must have a lang attribute', el:'<html>'});

    $('img').forEach(el => {
        if (!el.hasAttribute('alt'))
            issues.push({impact:'critical', id:'image-alt', desc:'Images must have alt text', el:el2str(el)});
    });

    $('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=image]):not([type=reset])').forEach(el => {
        const hasLabel = el.id && document.querySelector('label[for="'+el.id+'"]');
        if (!hasLabel && !el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby') && !el.getAttribute('title'))
            issues.push({impact:'serious', id:'label', desc:'Form inputs must have a label', el:el2str(el)});
    });

    $('button').forEach(el => {
        if (!el.textContent.trim() && !el.getAttribute('aria-label') && !el.getAttribute('title'))
            issues.push({impact:'serious', id:'button-name', desc:'Buttons must have accessible names', el:el2str(el)});
    });

    $('a').forEach(el => {
        if (!el.textContent.trim() && !el.getAttribute('aria-label') && !el.querySelector('img[alt]'))
            issues.push({impact:'serious', id:'link-name', desc:'Links must have accessible names', el:el2str(el)});
    });

    const h1s = $('h1');
    if (!h1s.length)
        issues.push({impact:'moderate', id:'page-has-h1', desc:'Page should have an <h1>', el:'<body>'});
    else if (h1s.length > 1)
        issues.push({impact:'moderate', id:'multiple-h1', desc:'Page should not have more than one <h1>', el:'<body>'});

    $('[onclick]:not(a):not(button):not(input):not(select):not(textarea)').forEach(el => {
        if (!el.getAttribute('tabindex') && !el.getAttribute('role'))
            issues.push({impact:'serious', id:'keyboard', desc:'onClick elements need tabindex and role for keyboard access', el:el2str(el)});
    });

    $('input[type=password]').forEach(el => {
        if (!el.getAttribute('autocomplete'))
            issues.push({impact:'minor', id:'autocomplete', desc:'Password inputs should have autocomplete attribute', el:el2str(el)});
    });

    return {url: location.href, issues};
    """

    _IMPACT_ORDER = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3}

    async def _check_accessibility(self, args: dict) -> str:
        level  = args.get("level", "all")
        result = self.get_driver().execute_script(self._A11Y_SCRIPT)
        issues = result.get("issues", [])

        if level != "all":
            issues = [i for i in issues if i["impact"] == level]

        issues.sort(key=lambda i: self._IMPACT_ORDER.get(i["impact"], 4))

        if not issues:
            return f"✅ No accessibility issues found on {result['url']}"

        counts: dict = {}
        for i in issues:
            counts[i["impact"]] = counts.get(i["impact"], 0) + 1
        summary = ", ".join(
            f"{v} {k}" for k, v in sorted(counts.items(), key=lambda x: self._IMPACT_ORDER.get(x[0], 4))
        )

        lines = [
            f"Accessibility audit: {len(issues)} issue(s) — {summary}",
            f"Page: {result['url']}",
            "",
        ]
        for i in issues:
            lines.append(f"[{i['impact']}] {i['id']}: {i['desc']}")
            lines.append(f"  {i['el']}")
        return "\n".join(lines)
