"""
Browser Tools — start, stop, navigate, screenshot, window management,
cookies, localStorage/sessionStorage, console logs, mobile emulation, page scroll
"""

import base64
import json
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
            opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
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
            "get_session_storage": self._get_session_storage,
            "set_session_storage": self._set_session_storage,
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
            opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
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
