"""
Element Tools — find, click, type, select, hover, drag-and-drop, waits
Includes self-healing locators: when a primary selector fails, alternative
strategies are tried automatically and the successful one is cached.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from mcp.types import Tool
from selenium_mcp.tools._locators import BY_MAP
from selenium_mcp.tools._attrs import semantic_attrs

_SPECIAL_KEYS: dict[str, str] = {
    "tab": Keys.TAB, "enter": Keys.RETURN, "escape": Keys.ESCAPE,
    "space": Keys.SPACE, "backspace": Keys.BACK_SPACE, "delete": Keys.DELETE,
    "up": Keys.ARROW_UP, "down": Keys.ARROW_DOWN,
    "left": Keys.ARROW_LEFT, "right": Keys.ARROW_RIGHT,
    "home": Keys.HOME, "end": Keys.END,
    "page_up": Keys.PAGE_UP, "page_down": Keys.PAGE_DOWN,
    "f1": Keys.F1, "f2": Keys.F2, "f3": Keys.F3, "f4": Keys.F4,
    "f5": Keys.F5, "f6": Keys.F6, "f7": Keys.F7, "f8": Keys.F8,
    "f9": Keys.F9, "f10": Keys.F10, "f11": Keys.F11, "f12": Keys.F12,
}
_MODIFIERS: dict[str, str] = {
    "ctrl": Keys.CONTROL, "shift": Keys.SHIFT,
    "alt": Keys.ALT, "meta": Keys.META,
}

LOCATOR_SCHEMA = {
    "selector": {
        "type": "string",
        "description": "CSS selector, XPath, or other locator value"
    },
    "by": {
        "type": "string",
        "enum": list(BY_MAP.keys()),
        "default": "css",
        "description": "Locator strategy"
    },
    "timeout": {
        "type": "integer",
        "default": 10,
        "description": "Wait timeout in seconds"
    }
}


class ElementTools:
    def __init__(self, browser_tools):
        self.browser = browser_tools
        self._last_heal: tuple[str, str, str, str] | None = None  # (orig_sel, orig_by, new_sel, new_by)

    def _by(self, strategy: str):
        return BY_MAP.get(strategy, By.CSS_SELECTOR)

    # ------------------------------------------------------------------ #
    #  Self-healing core                                                   #
    # ------------------------------------------------------------------ #

    def _alternatives(self, selector: str, by: str) -> list[tuple[str, str]]:
        """Generate alternative (selector, by) pairs to try when primary fails."""
        alts: list[tuple[str, str]] = []

        if by == "css":
            # Multi-selector fallback: split on top-level commas
            parts = [p.strip() for p in selector.split(",") if p.strip()]
            if len(parts) > 1:
                alts.extend((p, "css") for p in parts)

            # #id → by ID
            if selector.startswith("#") and " " not in selector:
                alts.append((selector[1:], "id"))

            # .class → by class name (simple single class only)
            if selector.startswith(".") and " " not in selector and "." not in selector[1:]:
                cls = selector[1:]
                alts.append((cls, "class"))
                alts.append((f"[class*='{cls}']", "css"))

            # tag[attr='val'] → XPath
            if "[" in selector and not selector.startswith("["):
                tag = selector.split("[")[0]
                rest = selector[len(tag):]
                xpath = f"//{tag}{rest.replace('[', '[@').replace('=', '=').replace(']', ']')}"
                alts.append((xpath, "xpath"))

            # Strip CSS pseudo-classes/elements like :not(...), :first-child, ::before
            import re
            stripped = re.sub(r':{1,2}[\w-]+(\([^)]*\))?', '', selector).strip()
            if stripped and stripped != selector:
                alts.append((stripped, "css"))

            # Try XPath contains on text if it looks like a label
            if not any(c in selector for c in ("#", ".", "[", ":")):
                alts.append((f"//*[contains(text(),'{selector}')]", "xpath"))

        elif by == "xpath":
            # Try without axis prefix variations
            if selector.startswith("//"):
                alts.append((selector.lstrip("/"), "xpath"))
            # Try CSS conversion for simple tag[@attr] xpaths
            import re
            m = re.match(r'^//(\w+)\[@(\w+)=[\'"]([^\'"]+)[\'"]\]$', selector)
            if m:
                tag, attr, val = m.groups()
                alts.append((f"{tag}[{attr}='{val}']", "css"))
                if attr == "id":
                    alts.append((val, "id"))
                elif attr == "name":
                    alts.append((val, "name"))

        elif by == "id":
            alts.append((f"#{selector}", "css"))
            alts.append((f"[id='{selector}']", "css"))
            alts.append((f"//*[@id='{selector}']", "xpath"))

        elif by == "name":
            alts.append((f"[name='{selector}']", "css"))
            alts.append((f"//*[@name='{selector}']", "xpath"))

        return alts

    def _locate(self, selector: str, by: str, timeout: int, condition_fn=None):
        """
        Find an element using primary selector, falling back to alternatives.
        Caches successful healed selectors via browser._healer_cache.
        Sets self._last_heal when a fallback was used.
        """
        self._last_heal = None
        driver = self.browser.get_driver()
        cache_key = (selector, by)

        # Check if we already have a healed locator for this selector
        if cache_key in self.browser._healer_cache:
            healed_sel, healed_by = self.browser._healer_cache[cache_key]
            by_val = self._by(healed_by)
            cond = condition_fn or EC.presence_of_element_located
            try:
                el = WebDriverWait(driver, timeout).until(cond((by_val, healed_sel)))
                self._last_heal = (selector, by, healed_sel, healed_by)
                return el
            except (TimeoutException, NoSuchElementException):
                # Cached heal no longer works — invalidate and retry fresh
                del self.browser._healer_cache[cache_key]

        # Try primary
        by_val = self._by(by)
        cond = condition_fn or EC.presence_of_element_located
        original_exc = None
        try:
            return WebDriverWait(driver, timeout).until(cond((by_val, selector)))
        except (TimeoutException, NoSuchElementException) as e:
            original_exc = e

        # Primary failed — try alternatives with a short timeout
        for alt_sel, alt_by in self._alternatives(selector, by):
            try:
                alt_by_val = self._by(alt_by)
                el = WebDriverWait(driver, 3).until(cond((alt_by_val, alt_sel)))
                # Cache the successful alternative
                self.browser._healer_cache[cache_key] = (alt_sel, alt_by)
                self._last_heal = (selector, by, alt_sel, alt_by)
                return el
            except (TimeoutException, NoSuchElementException):
                continue

        raise original_exc

    def _heal_note(self) -> str:
        if self._last_heal:
            orig_sel, orig_by, new_sel, new_by = self._last_heal
            return f" [⚕ healed: '{orig_sel}' ({orig_by}) → '{new_sel}' ({new_by})]"
        return ""

    # ------------------------------------------------------------------ #
    #  Legacy helpers kept for drag_and_drop (needs two separate locates)  #
    # ------------------------------------------------------------------ #

    def _find(self, selector, by="css", timeout=10):
        return self._locate(selector, by, timeout, EC.presence_of_element_located)

    def _find_clickable(self, selector, by="css", timeout=10):
        return self._locate(selector, by, timeout, EC.element_to_be_clickable)

    # ------------------------------------------------------------------ #
    #  MCP tool definitions                                                #
    # ------------------------------------------------------------------ #

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="find_element",
                description="Find an element and return its text, tag, and attributes.",
                inputSchema={
                    "type": "object",
                    "properties": LOCATOR_SCHEMA,
                    "required": ["selector"],
                },
            ),
            Tool(
                name="find_elements",
                description="Find all matching elements and return their texts.",
                inputSchema={
                    "type": "object",
                    "properties": LOCATOR_SCHEMA,
                    "required": ["selector"],
                },
            ),
            Tool(
                name="click",
                description="Click on an element.",
                inputSchema={
                    "type": "object",
                    "properties": LOCATOR_SCHEMA,
                    "required": ["selector"],
                },
            ),
            Tool(
                name="type_text",
                description="Clear and type text into an input field.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **LOCATOR_SCHEMA,
                        "text": {"type": "string", "description": "Text to type"},
                        "clear_first": {"type": "boolean", "default": True}
                    },
                    "required": ["selector", "text"],
                },
            ),
            Tool(
                name="get_text",
                description="Get the visible text content of an element.",
                inputSchema={
                    "type": "object",
                    "properties": LOCATOR_SCHEMA,
                    "required": ["selector"],
                },
            ),
            Tool(
                name="get_attribute",
                description="Get an attribute value from an element.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **LOCATOR_SCHEMA,
                        "attribute": {"type": "string", "description": "Attribute name e.g. href, value, class"}
                    },
                    "required": ["selector", "attribute"],
                },
            ),
            Tool(
                name="select_option",
                description="Select an option from a <select> dropdown by visible text, value, or index.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **LOCATOR_SCHEMA,
                        "by_text":  {"type": "string"},
                        "by_value": {"type": "string"},
                        "by_index": {"type": "integer"},
                    },
                    "required": ["selector"],
                },
            ),
            Tool(
                name="hover",
                description="Hover the mouse over an element.",
                inputSchema={
                    "type": "object",
                    "properties": LOCATOR_SCHEMA,
                    "required": ["selector"],
                },
            ),
            Tool(
                name="double_click",
                description="Double-click on an element.",
                inputSchema={
                    "type": "object",
                    "properties": LOCATOR_SCHEMA,
                    "required": ["selector"],
                },
            ),
            Tool(
                name="right_click",
                description="Right-click (context menu) on an element.",
                inputSchema={
                    "type": "object",
                    "properties": LOCATOR_SCHEMA,
                    "required": ["selector"],
                },
            ),
            Tool(
                name="drag_and_drop",
                description="Drag one element and drop it onto another.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source_selector": {"type": "string"},
                        "target_selector": {"type": "string"},
                        "by": {"type": "string", "default": "css"},
                    },
                    "required": ["source_selector", "target_selector"],
                },
            ),
            Tool(
                name="is_displayed",
                description="Check if an element is visible on the page.",
                inputSchema={
                    "type": "object",
                    "properties": LOCATOR_SCHEMA,
                    "required": ["selector"],
                },
            ),
            Tool(
                name="is_enabled",
                description="Check if an element is enabled (not disabled).",
                inputSchema={
                    "type": "object",
                    "properties": LOCATOR_SCHEMA,
                    "required": ["selector"],
                },
            ),
            Tool(
                name="wait_for_element",
                description="Wait until an element is visible on the page.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **LOCATOR_SCHEMA,
                        "condition": {
                            "type": "string",
                            "enum": ["visible", "clickable", "present", "invisible"],
                            "default": "visible"
                        }
                    },
                    "required": ["selector"],
                },
            ),
            Tool(
                name="scroll_to_element",
                description="Scroll the page to bring an element into view.",
                inputSchema={
                    "type": "object",
                    "properties": LOCATOR_SCHEMA,
                    "required": ["selector"],
                },
            ),
            Tool(
                name="clear_field",
                description="Clear the text in an input field.",
                inputSchema={
                    "type": "object",
                    "properties": LOCATOR_SCHEMA,
                    "required": ["selector"],
                },
            ),
            Tool(
                name="fill_form",
                description=(
                    "Fill multiple form fields in a single call. Pass a map of CSS selector → value. "
                    "Automatically handles text inputs, textareas, checkboxes (true/false), "
                    "radio buttons, and <select> dropdowns. Optionally clicks a submit button at the end."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fields": {
                            "type": "object",
                            "description": "Map of selector → value. Checkboxes: 'true'/'false'. Selects: visible text or value.",
                            "additionalProperties": {"type": "string"},
                        },
                        "by":      {"type": "string", "default": "css"},
                        "timeout": {"type": "integer", "default": 10},
                        "submit":  {"type": "string", "description": "Selector of submit button to click after filling (optional)"},
                    },
                    "required": ["fields"],
                },
            ),
            Tool(
                name="get_healed_locators",
                description="Return all self-healed locator mappings from this session. Shows which selectors were automatically repaired and what they were replaced with.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="clear_healed_locators",
                description="Clear the self-healing locator cache so all selectors are re-evaluated from scratch.",
                inputSchema={"type": "object", "properties": {}},
            ),
            # ── Alerts / dialogs ──────────────────────────────────────── #
            Tool(
                name="accept_alert",
                description="Accept (OK) a JavaScript alert, confirm, or prompt dialog.",
                inputSchema={"type": "object", "properties": {
                    "timeout": {"type": "integer", "default": 5}
                }},
            ),
            Tool(
                name="dismiss_alert",
                description="Dismiss (Cancel) a JavaScript confirm or prompt dialog.",
                inputSchema={"type": "object", "properties": {
                    "timeout": {"type": "integer", "default": 5}
                }},
            ),
            Tool(
                name="get_alert_text",
                description="Return the text message of a currently open JavaScript alert/confirm/prompt.",
                inputSchema={"type": "object", "properties": {
                    "timeout": {"type": "integer", "default": 5}
                }},
            ),
            Tool(
                name="type_in_alert",
                description="Type text into a JavaScript prompt dialog, then accept it.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "timeout": {"type": "integer", "default": 5},
                    },
                    "required": ["text"],
                },
            ),
            # ── Frame / iframe switching ──────────────────────────────── #
            Tool(
                name="switch_to_frame",
                description="Switch focus into an iframe. Provide index (integer), name/id (string), or a CSS/XPath selector.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "index":    {"type": "integer", "description": "Frame index"},
                        "name":     {"type": "string",  "description": "Frame name or id attribute"},
                        "selector": {"type": "string",  "description": "CSS/XPath to locate the iframe element"},
                        "by":       {"type": "string",  "default": "css"},
                        "timeout":  {"type": "integer", "default": 10},
                    },
                },
            ),
            Tool(
                name="switch_to_default_content",
                description="Switch back to the main page content from inside a frame.",
                inputSchema={"type": "object", "properties": {}},
            ),
            # ── Keyboard ─────────────────────────────────────────────── #
            Tool(
                name="send_keys",
                description=(
                    "Send a key or key combination to the focused element (or a specific element if selector is given). "
                    "Use key names like 'tab', 'enter', 'escape', 'up', 'down', 'f5', or combos like 'ctrl+a', 'shift+tab'."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "key":      {"type": "string", "description": "Key name or combo e.g. 'tab', 'ctrl+a', 'enter'"},
                        "selector": {"type": "string", "description": "Element to focus before sending (optional)"},
                        "by":       {"type": "string", "default": "css"},
                        "timeout":  {"type": "integer", "default": 10},
                    },
                    "required": ["key"],
                },
            ),
            # ── File upload ───────────────────────────────────────────── #
            Tool(
                name="upload_file",
                description="Upload a file by sending its absolute path to an <input type='file'> element.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **LOCATOR_SCHEMA,
                        "file_path": {"type": "string", "description": "Absolute path to the file to upload"},
                    },
                    "required": ["selector", "file_path"],
                },
            ),
            # ── Shadow DOM ────────────────────────────────────────────── #
            Tool(
                name="find_shadow_element",
                description="Find an element inside a shadow DOM. Provide the host element selector and then the selector for the element inside the shadow root.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "host_selector":   {"type": "string", "description": "CSS selector of the shadow host element"},
                        "shadow_selector": {"type": "string", "description": "CSS selector inside the shadow root"},
                        "timeout":         {"type": "integer", "default": 10},
                    },
                    "required": ["host_selector", "shadow_selector"],
                },
            ),
            # ── Table extraction ──────────────────────────────────────── #
            Tool(
                name="get_table_data",
                description="Extract data from an HTML table as a formatted text grid.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS/XPath selector for the <table> element"},
                        "by":       {"type": "string", "default": "css"},
                        "timeout":  {"type": "integer", "default": 10},
                    },
                    "required": ["selector"],
                },
            ),
        ]

    def get_handlers(self) -> dict:
        return {
            "find_element":         self._find_element,
            "find_elements":        self._find_elements,
            "click":                self._click,
            "type_text":            self._type_text,
            "get_text":             self._get_text,
            "get_attribute":        self._get_attribute,
            "select_option":        self._select_option,
            "hover":                self._hover,
            "double_click":         self._double_click,
            "right_click":          self._right_click,
            "drag_and_drop":        self._drag_and_drop,
            "is_displayed":         self._is_displayed,
            "is_enabled":           self._is_enabled,
            "wait_for_element":     self._wait_for_element,
            "scroll_to_element":    self._scroll_to_element,
            "clear_field":          self._clear_field,
            "fill_form":                self._fill_form,
            "get_healed_locators":      self._get_healed_locators,
            "clear_healed_locators":    self._clear_healed_locators,
            "accept_alert":             self._accept_alert,
            "dismiss_alert":            self._dismiss_alert,
            "get_alert_text":           self._get_alert_text,
            "type_in_alert":            self._type_in_alert,
            "switch_to_frame":          self._switch_to_frame,
            "switch_to_default_content":self._switch_to_default_content,
            "send_keys":                self._send_keys,
            "upload_file":              self._upload_file,
            "find_shadow_element":      self._find_shadow_element,
            "get_table_data":           self._get_table_data,
        }

    # ------------------------------------------------------------------ #
    #  Handlers                                                            #
    # ------------------------------------------------------------------ #

    def _semantic_attrs(self, el) -> dict:
        """Snapshot an element's accessibility-relevant attributes at interaction
        time, so codegen can prefer advanced locators (getByTestId / getByRole /
        getByLabel / getByPlaceholder / ...) no matter which selector was used to
        interact. One JS round-trip; best-effort — never raises."""
        return semantic_attrs(self.browser.get_driver(), el)

    async def _find_element(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        return f"tag={el.tag_name} | text='{el.text}' | displayed={el.is_displayed()}{self._heal_note()}"

    async def _find_elements(self, args: dict) -> str:
        driver = self.browser.get_driver()
        els = driver.find_elements(self._by(args.get("by", "css")), args["selector"])
        results = [f"[{i}] tag={e.tag_name} text='{e.text[:60]}'" for i, e in enumerate(els)]
        return f"Found {len(els)} element(s):\n" + "\n".join(results)

    async def _click(self, args: dict) -> str:
        el = self._find_clickable(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        attrs = self._semantic_attrs(el)
        el.click()
        self.browser.record("click", selector=args["selector"], by=args.get("by", "css"), attrs=attrs)
        return f"✅ Clicked '{args['selector']}'{self._heal_note()}"

    async def _type_text(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        attrs = self._semantic_attrs(el)
        if args.get("clear_first", True):
            el.clear()
        el.send_keys(args["text"])
        sel_lower = args["selector"].lower()
        logged_text = "***" if any(k in sel_lower for k in ("password", "passwd", "pwd")) else args["text"]
        self.browser.record("type_text", selector=args["selector"], by=args.get("by", "css"), text=logged_text, attrs=attrs)
        return f"✅ Typed into '{args['selector']}'{self._heal_note()}"

    async def _get_text(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        note = self._heal_note()
        return el.text + note if note else el.text

    async def _get_attribute(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        val = el.get_attribute(args["attribute"])
        note = self._heal_note()
        return str(val) + note if note else str(val)

    async def _select_option(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        attrs = self._semantic_attrs(el)
        sel = Select(el)
        note = self._heal_note()
        if "by_text" in args:
            sel.select_by_visible_text(args["by_text"])
            self.browser.record("select_option", selector=args["selector"], by_text=args["by_text"], attrs=attrs)
            return f"✅ Selected by text: '{args['by_text']}'{note}"
        elif "by_value" in args:
            sel.select_by_value(args["by_value"])
            self.browser.record("select_option", selector=args["selector"], by_value=args["by_value"], attrs=attrs)
            return f"✅ Selected by value: '{args['by_value']}'{note}"
        elif "by_index" in args:
            sel.select_by_index(args["by_index"])
            self.browser.record("select_option", selector=args["selector"], by_index=args["by_index"], attrs=attrs)
            return f"✅ Selected by index: {args['by_index']}{note}"
        return "❌ Provide by_text, by_value, or by_index"

    async def _hover(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        attrs = self._semantic_attrs(el)
        ActionChains(self.browser.get_driver()).move_to_element(el).perform()
        self.browser.record("hover", selector=args["selector"], by=args.get("by", "css"), attrs=attrs)
        return f"✅ Hovered over '{args['selector']}'{self._heal_note()}"

    async def _double_click(self, args: dict) -> str:
        el = self._find_clickable(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        attrs = self._semantic_attrs(el)
        ActionChains(self.browser.get_driver()).double_click(el).perform()
        self.browser.record("double_click", selector=args["selector"], by=args.get("by", "css"), attrs=attrs)
        return f"✅ Double-clicked '{args['selector']}'{self._heal_note()}"

    async def _right_click(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        attrs = self._semantic_attrs(el)
        ActionChains(self.browser.get_driver()).context_click(el).perform()
        self.browser.record("right_click", selector=args["selector"], by=args.get("by", "css"), attrs=attrs)
        return f"✅ Right-clicked '{args['selector']}'{self._heal_note()}"

    async def _drag_and_drop(self, args: dict) -> str:
        by = self._by(args.get("by", "css"))
        driver = self.browser.get_driver()
        timeout = args.get("timeout", 10)
        src = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, args["source_selector"])))
        tgt = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, args["target_selector"])))
        ActionChains(driver).drag_and_drop(src, tgt).perform()
        return f"✅ Dragged '{args['source_selector']}' → '{args['target_selector']}'"

    async def _is_displayed(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        return str(el.is_displayed()) + self._heal_note()

    async def _is_enabled(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        return str(el.is_enabled()) + self._heal_note()

    async def _wait_for_element(self, args: dict) -> str:
        driver = self.browser.get_driver()
        by = self._by(args.get("by", "css"))
        sel = args["selector"]
        timeout = args.get("timeout", 10)
        condition = args.get("condition", "visible")

        cond_map = {
            "visible":   EC.visibility_of_element_located,
            "clickable": EC.element_to_be_clickable,
            "present":   EC.presence_of_element_located,
            "invisible": EC.invisibility_of_element_located,
        }
        WebDriverWait(driver, timeout).until(cond_map[condition]((by, sel)))
        return f"✅ Element '{sel}' is {condition}"

    async def _scroll_to_element(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        attrs = self._semantic_attrs(el)
        self.browser.get_driver().execute_script("arguments[0].scrollIntoView(true);", el)
        self.browser.record("scroll_to_element", selector=args["selector"], by=args.get("by", "css"), attrs=attrs)
        return f"✅ Scrolled to '{args['selector']}'{self._heal_note()}"

    async def _clear_field(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        el.clear()
        return f"✅ Cleared '{args['selector']}'{self._heal_note()}"

    # ------------------------------------------------------------------ #
    #  fill_form handler                                                   #
    # ------------------------------------------------------------------ #

    def _fill_one(self, el, selector: str, value: str, by: str) -> str:
        """Fill a single element; return a short summary line."""
        tag = el.tag_name.lower()
        input_type = (el.get_attribute("type") or "text").lower()

        if tag == "select":
            sel_obj = Select(el)
            try:
                sel_obj.select_by_visible_text(value)
                self.browser.record("select_option", selector=selector, by=by, by_text=value)
            except Exception:
                sel_obj.select_by_value(value)
                self.browser.record("select_option", selector=selector, by=by, by_value=value)
            return f"  select  {selector!r} → '{value}'"

        elif input_type == "checkbox":
            want = value.strip().lower() in ("true", "1", "yes", "on", "checked")
            if el.is_selected() != want:
                el.click()
                self.browser.record("click", selector=selector, by=by)
            state = "checked" if want else "unchecked"
            return f"  checkbox {selector!r} → {state}"

        elif input_type == "radio":
            if not el.is_selected():
                el.click()
                self.browser.record("click", selector=selector, by=by)
            return f"  radio   {selector!r} → selected"

        elif input_type == "file":
            el.send_keys(value)
            self.browser.record("upload_file", selector=selector, by=by, file_path=value)
            return f"  file    {selector!r} → '{value}'"

        else:
            el.clear()
            el.send_keys(value)
            sel_lower = selector.lower()
            logged = "***" if any(k in sel_lower for k in ("password", "passwd", "pwd")) else value
            self.browser.record("type_text", selector=selector, by=by, text=logged)
            return f"  input   {selector!r} → '{logged}'"

    async def _fill_form(self, args: dict) -> str:
        fields: dict = args.get("fields", {})
        by = args.get("by", "css")
        timeout = args.get("timeout", 10)
        submit_sel = args.get("submit", "")

        if not fields:
            return "❌ No fields provided."

        results = []
        errors  = []
        for selector, value in fields.items():
            try:
                el = self._find(selector, by, timeout)
                results.append(self._fill_one(el, selector, value, by))
            except Exception as e:
                errors.append(f"  ❌ {selector!r}: {e}")

        if submit_sel:
            try:
                self._find_clickable(submit_sel, by, timeout).click()
                self.browser.record("click", selector=submit_sel, by=by)
                results.append(f"  submit  {submit_sel!r} → clicked")
            except Exception as e:
                errors.append(f"  ❌ submit {submit_sel!r}: {e}")

        summary = f"✅ Filled {len(results)} field(s)"
        if errors:
            summary += f", {len(errors)} error(s)"
        lines = [summary] + results + errors
        return "\n".join(lines)

    async def _get_healed_locators(self, args: dict) -> str:
        cache = self.browser._healer_cache
        if not cache:
            return "No healed locators in this session."
        lines = ["Healed locators this session:"]
        for (orig_sel, orig_by), (new_sel, new_by) in cache.items():
            lines.append(f"  [{orig_by}] '{orig_sel}'  →  [{new_by}] '{new_sel}'")
        return "\n".join(lines)

    async def _clear_healed_locators(self, args: dict) -> str:
        count = len(self.browser._healer_cache)
        self.browser._healer_cache.clear()
        return f"✅ Cleared {count} healed locator(s) from cache."

    # ------------------------------------------------------------------ #
    #  Alert / dialog handlers                                            #
    # ------------------------------------------------------------------ #

    def _wait_alert(self, timeout: int):
        return WebDriverWait(self.browser.get_driver(), timeout).until(
            EC.alert_is_present()
        )

    async def _accept_alert(self, args: dict) -> str:
        alert = self._wait_alert(args.get("timeout", 5))
        text = alert.text
        alert.accept()
        self.browser.record("accept_alert")
        return f"✅ Alert accepted: '{text}'"

    async def _dismiss_alert(self, args: dict) -> str:
        alert = self._wait_alert(args.get("timeout", 5))
        text = alert.text
        alert.dismiss()
        self.browser.record("dismiss_alert")
        return f"✅ Alert dismissed: '{text}'"

    async def _get_alert_text(self, args: dict) -> str:
        alert = self._wait_alert(args.get("timeout", 5))
        return alert.text

    async def _type_in_alert(self, args: dict) -> str:
        alert = self._wait_alert(args.get("timeout", 5))
        alert.send_keys(args["text"])
        alert.accept()
        self.browser.record("type_in_alert", text=args["text"])
        return f"✅ Typed '{args['text']}' in alert and accepted"

    # ------------------------------------------------------------------ #
    #  Frame / iframe handlers                                            #
    # ------------------------------------------------------------------ #

    async def _switch_to_frame(self, args: dict) -> str:
        driver = self.browser.get_driver()
        if "index" in args:
            driver.switch_to.frame(args["index"])
            self.browser.record("switch_to_frame", index=args["index"])
            return f"✅ Switched to frame[{args['index']}]"
        elif "name" in args:
            driver.switch_to.frame(args["name"])
            self.browser.record("switch_to_frame", name=args["name"])
            return f"✅ Switched to frame '{args['name']}'"
        elif "selector" in args:
            el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
            driver.switch_to.frame(el)
            self.browser.record("switch_to_frame", selector=args["selector"])
            return f"✅ Switched to frame '{args['selector']}'"
        return "❌ Provide index, name, or selector"

    async def _switch_to_default_content(self, args: dict) -> str:
        self.browser.get_driver().switch_to.default_content()
        self.browser.record("switch_to_default_content")
        return "✅ Switched back to main content"

    # ------------------------------------------------------------------ #
    #  Keyboard handler                                                   #
    # ------------------------------------------------------------------ #

    async def _send_keys(self, args: dict) -> str:
        key_str = args["key"].lower().strip()
        driver = self.browser.get_driver()

        # Parse modifier+key combos like "ctrl+a", "shift+tab"
        parts = [p.strip() for p in key_str.split("+")]
        if len(parts) > 1:
            modifier_keys = [_MODIFIERS[p] for p in parts[:-1] if p in _MODIFIERS]
            last = parts[-1]
            key_val = _SPECIAL_KEYS.get(last, last)
            chain = ActionChains(driver)
            for mod in modifier_keys:
                chain = chain.key_down(mod)
            chain = chain.send_keys(key_val)
            for mod in reversed(modifier_keys):
                chain = chain.key_up(mod)
            chain.perform()
        else:
            key_val = _SPECIAL_KEYS.get(key_str, key_str)
            if "selector" in args:
                el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
                el.send_keys(key_val)
            else:
                ActionChains(driver).send_keys(key_val).perform()

        self.browser.record("send_keys", key=args["key"],
                            selector=args.get("selector", ""), by=args.get("by", "css"))
        return f"✅ Sent key '{args['key']}'"

    # ------------------------------------------------------------------ #
    #  File upload handler                                                #
    # ------------------------------------------------------------------ #

    async def _upload_file(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        el.send_keys(args["file_path"])
        self.browser.record("upload_file", selector=args["selector"],
                            by=args.get("by", "css"), file_path=args["file_path"])
        return f"✅ Uploaded '{args['file_path']}' to '{args['selector']}'"

    # ------------------------------------------------------------------ #
    #  Shadow DOM handler                                                 #
    # ------------------------------------------------------------------ #

    async def _find_shadow_element(self, args: dict) -> str:
        driver = self.browser.get_driver()
        timeout = args.get("timeout", 10)
        host = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, args["host_selector"]))
        )
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", host)
        if shadow_root is None:
            return f"❌ No shadow root on '{args['host_selector']}'"
        el = shadow_root.find_element(By.CSS_SELECTOR, args["shadow_selector"])
        return f"tag={el.tag_name} | text='{el.text}' | displayed={el.is_displayed()}"

    # ------------------------------------------------------------------ #
    #  Table extraction handler                                           #
    # ------------------------------------------------------------------ #

    async def _get_table_data(self, args: dict) -> str:
        table = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        rows = table.find_elements(By.TAG_NAME, "tr")
        grid: list[list[str]] = []
        for row in rows:
            cells = row.find_elements(By.XPATH, "th|td")
            grid.append([c.text.strip() for c in cells])

        if not grid:
            return "Table found but no rows."

        # Calculate column widths for aligned output
        col_count = max(len(r) for r in grid)
        widths = [0] * col_count
        for row in grid:
            for ci, cell in enumerate(row):
                widths[ci] = max(widths[ci], len(cell))

        lines = []
        for ri, row in enumerate(grid):
            padded = [row[ci].ljust(widths[ci]) if ci < len(row) else " " * widths[ci]
                      for ci in range(col_count)]
            lines.append(" | ".join(padded))
            if ri == 0:
                lines.append("-+-".join("-" * w for w in widths))

        return f"{len(rows)} row(s), {col_count} column(s):\n" + "\n".join(lines)
