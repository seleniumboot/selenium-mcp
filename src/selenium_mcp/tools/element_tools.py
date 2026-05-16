"""
Element Tools — find, click, type, select, hover, drag-and-drop, waits
Includes self-healing locators: when a primary selector fails, alternative
strategies are tried automatically and the successful one is cached.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from mcp.types import Tool
from selenium_mcp.tools._locators import BY_MAP

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
                name="get_healed_locators",
                description="Return all self-healed locator mappings from this session. Shows which selectors were automatically repaired and what they were replaced with.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="clear_healed_locators",
                description="Clear the self-healing locator cache so all selectors are re-evaluated from scratch.",
                inputSchema={"type": "object", "properties": {}},
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
            "get_healed_locators":  self._get_healed_locators,
            "clear_healed_locators":self._clear_healed_locators,
        }

    # ------------------------------------------------------------------ #
    #  Handlers                                                            #
    # ------------------------------------------------------------------ #

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
        el.click()
        self.browser.record("click", selector=args["selector"], by=args.get("by", "css"))
        return f"✅ Clicked '{args['selector']}'{self._heal_note()}"

    async def _type_text(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        if args.get("clear_first", True):
            el.clear()
        el.send_keys(args["text"])
        sel_lower = args["selector"].lower()
        logged_text = "***" if any(k in sel_lower for k in ("password", "passwd", "pwd")) else args["text"]
        self.browser.record("type_text", selector=args["selector"], by=args.get("by", "css"), text=logged_text)
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
        sel = Select(el)
        note = self._heal_note()
        if "by_text" in args:
            sel.select_by_visible_text(args["by_text"])
            self.browser.record("select_option", selector=args["selector"], by_text=args["by_text"])
            return f"✅ Selected by text: '{args['by_text']}'{note}"
        elif "by_value" in args:
            sel.select_by_value(args["by_value"])
            self.browser.record("select_option", selector=args["selector"], by_value=args["by_value"])
            return f"✅ Selected by value: '{args['by_value']}'{note}"
        elif "by_index" in args:
            sel.select_by_index(args["by_index"])
            self.browser.record("select_option", selector=args["selector"], by_index=args["by_index"])
            return f"✅ Selected by index: {args['by_index']}{note}"
        return "❌ Provide by_text, by_value, or by_index"

    async def _hover(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        ActionChains(self.browser.get_driver()).move_to_element(el).perform()
        self.browser.record("hover", selector=args["selector"], by=args.get("by", "css"))
        return f"✅ Hovered over '{args['selector']}'{self._heal_note()}"

    async def _double_click(self, args: dict) -> str:
        el = self._find_clickable(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        ActionChains(self.browser.get_driver()).double_click(el).perform()
        self.browser.record("double_click", selector=args["selector"], by=args.get("by", "css"))
        return f"✅ Double-clicked '{args['selector']}'{self._heal_note()}"

    async def _right_click(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        ActionChains(self.browser.get_driver()).context_click(el).perform()
        self.browser.record("right_click", selector=args["selector"], by=args.get("by", "css"))
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
        self.browser.get_driver().execute_script("arguments[0].scrollIntoView(true);", el)
        self.browser.record("scroll_to_element", selector=args["selector"], by=args.get("by", "css"))
        return f"✅ Scrolled to '{args['selector']}'{self._heal_note()}"

    async def _clear_field(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        el.clear()
        return f"✅ Cleared '{args['selector']}'{self._heal_note()}"

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
