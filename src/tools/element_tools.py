"""
Element Tools — find, click, type, select, hover, drag-and-drop, waits
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from mcp.types import Tool


BY_MAP = {
    "css":    By.CSS_SELECTOR,
    "xpath":  By.XPATH,
    "id":     By.ID,
    "name":   By.NAME,
    "tag":    By.TAG_NAME,
    "class":  By.CLASS_NAME,
    "link":   By.LINK_TEXT,
    "partial_link": By.PARTIAL_LINK_TEXT,
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

    def _by(self, strategy: str):
        return BY_MAP.get(strategy, By.CSS_SELECTOR)

    def _find(self, selector, by="css", timeout=10):
        driver = self.browser.get_driver()
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((self._by(by), selector))
        )

    def _find_clickable(self, selector, by="css", timeout=10):
        driver = self.browser.get_driver()
        return WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((self._by(by), selector))
        )

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
        ]

    def get_handlers(self) -> dict:
        return {
            "find_element":    self._find_element,
            "find_elements":   self._find_elements,
            "click":           self._click,
            "type_text":       self._type_text,
            "get_text":        self._get_text,
            "get_attribute":   self._get_attribute,
            "select_option":   self._select_option,
            "hover":           self._hover,
            "double_click":    self._double_click,
            "right_click":     self._right_click,
            "drag_and_drop":   self._drag_and_drop,
            "is_displayed":    self._is_displayed,
            "is_enabled":      self._is_enabled,
            "wait_for_element":self._wait_for_element,
            "scroll_to_element":self._scroll_to_element,
            "clear_field":     self._clear_field,
        }

    # ------------------------------------------------------------------ #
    #  Handlers                                                            #
    # ------------------------------------------------------------------ #
    async def _find_element(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        return f"tag={el.tag_name} | text='{el.text}' | displayed={el.is_displayed()}"

    async def _find_elements(self, args: dict) -> str:
        driver = self.browser.get_driver()
        els = driver.find_elements(self._by(args.get("by", "css")), args["selector"])
        results = [f"[{i}] tag={e.tag_name} text='{e.text[:60]}'" for i, e in enumerate(els)]
        return f"Found {len(els)} element(s):\n" + "\n".join(results)

    async def _click(self, args: dict) -> str:
        el = self._find_clickable(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        el.click()
        self.browser.record("click", selector=args["selector"], by=args.get("by", "css"))
        return f"✅ Clicked '{args['selector']}'"

    async def _type_text(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        if args.get("clear_first", True):
            el.clear()
        el.send_keys(args["text"])
        self.browser.record("type_text", selector=args["selector"], by=args.get("by", "css"), text=args["text"])
        return f"✅ Typed into '{args['selector']}'"

    async def _get_text(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        return el.text

    async def _get_attribute(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        val = el.get_attribute(args["attribute"])
        return str(val)

    async def _select_option(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        sel = Select(el)
        if "by_text" in args:
            sel.select_by_visible_text(args["by_text"])
            self.browser.record("select_option", selector=args["selector"], by_text=args["by_text"])
            return f"✅ Selected by text: '{args['by_text']}'"
        elif "by_value" in args:
            sel.select_by_value(args["by_value"])
            return f"✅ Selected by value: '{args['by_value']}'"
        elif "by_index" in args:
            sel.select_by_index(args["by_index"])
            return f"✅ Selected by index: {args['by_index']}"
        return "❌ Provide by_text, by_value, or by_index"

    async def _hover(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        ActionChains(self.browser.get_driver()).move_to_element(el).perform()
        return f"✅ Hovered over '{args['selector']}'"

    async def _double_click(self, args: dict) -> str:
        el = self._find_clickable(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        ActionChains(self.browser.get_driver()).double_click(el).perform()
        return f"✅ Double-clicked '{args['selector']}'"

    async def _right_click(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        ActionChains(self.browser.get_driver()).context_click(el).perform()
        return f"✅ Right-clicked '{args['selector']}'"

    async def _drag_and_drop(self, args: dict) -> str:
        by = self._by(args.get("by", "css"))
        driver = self.browser.get_driver()
        src = driver.find_element(by, args["source_selector"])
        tgt = driver.find_element(by, args["target_selector"])
        ActionChains(driver).drag_and_drop(src, tgt).perform()
        return f"✅ Dragged '{args['source_selector']}' → '{args['target_selector']}'"

    async def _is_displayed(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        return str(el.is_displayed())

    async def _is_enabled(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        return str(el.is_enabled())

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
        return f"✅ Scrolled to '{args['selector']}'"

    async def _clear_field(self, args: dict) -> str:
        el = self._find(args["selector"], args.get("by", "css"), args.get("timeout", 10))
        el.clear()
        return f"✅ Cleared '{args['selector']}'"