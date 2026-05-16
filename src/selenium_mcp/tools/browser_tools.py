"""
Browser Tools — start, stop, navigate, screenshot, window management
"""

import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from mcp.types import Tool


class BrowserTools:
    def __init__(self):
        self.driver = None
        self._session_log = []  # records all actions for codegen

    # ------------------------------------------------------------------ #
    #  Session helpers                                                     #
    # ------------------------------------------------------------------ #
    def record(self, action: str, **kwargs):
        """Append an action to the session log for code generation."""
        self._session_log.append({"action": action, **kwargs})

    def get_driver(self):
        if not self.driver:
            opts = ChromeOptions()
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            self.driver = webdriver.Chrome(options=opts)
            # Do NOT reset _session_log here — only explicit start_browser should do that.
            # Resetting here would wipe recorded actions if the browser crashes mid-session.
            self.record("start_browser", browser="chrome", headless=False)
        return self.driver

    # ------------------------------------------------------------------ #
    #  MCP tool definitions                                                #
    # ------------------------------------------------------------------ #
    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="start_browser",
                description="Start a browser session. Optional — any tool will auto-start Chrome if no browser is open. Use this to choose Firefox, enable headless mode, or set a custom window size.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "browser": {
                            "type": "string",
                            "enum": ["chrome", "firefox"],
                            "default": "chrome"
                        },
                        "headless": {
                            "type": "boolean",
                            "default": False
                        },
                        "window_size": {
                            "type": "string",
                            "description": "e.g. 1920x1080",
                            "default": "1920x1080"
                        }
                    },
                },
            ),
            Tool(
                name="navigate",
                description="Navigate the browser to a URL.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Full URL including https://"}
                    },
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
                name="switch_to_window",
                description="Switch to a browser window/tab by index.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer", "default": 0}
                    },
                },
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
                        "args": {"type": "array", "default": []}
                    },
                    "required": ["script"],
                },
            ),
        ]

    # ------------------------------------------------------------------ #
    #  Handlers                                                            #
    # ------------------------------------------------------------------ #
    def get_handlers(self) -> dict:
        return {
            "start_browser":    self._start_browser,
            "navigate":         self._navigate,
            "take_screenshot":  self._take_screenshot,
            "get_page_source":  self._get_page_source,
            "get_page_title":   self._get_page_title,
            "get_current_url":  self._get_current_url,
            "close_browser":    self._close_browser,
            "switch_to_window": self._switch_to_window,
            "go_back":          self._go_back,
            "go_forward":       self._go_forward,
            "refresh":          self._refresh,
            "execute_script":   self._execute_script,
        }

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
            self.driver = webdriver.Chrome(options=opts)
        elif browser == "firefox":
            opts = FirefoxOptions()
            if headless:
                opts.add_argument("--headless")
            self.driver = webdriver.Firefox(options=opts)
            self.driver.set_window_size(int(w), int(h))
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

    async def _switch_to_window(self, args: dict) -> str:
        idx = args.get("index", 0)
        handles = self.get_driver().window_handles
        if idx >= len(handles):
            return f"No window at index {idx}. Available: {len(handles)}"
        self.get_driver().switch_to.window(handles[idx])
        return f"✅ Switched to window {idx}"

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