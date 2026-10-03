"""Tool profiles — expose a subset of tools to cut the per-session schema cost.

Every tool definition is sent to the model on every session, so a smaller set
costs fewer tokens. Select with the SELENIUM_MCP_TOOLS environment variable:

  all   (default) every tool
  core  the record-and-generate workflow: drive the page, assert, generate code

Unset, empty or unrecognised values mean "all", so nothing changes unless a
user opts in.
"""

import os

CORE_TOOLS = frozenset({
    # browser
    "start_browser", "navigate", "take_screenshot", "get_page_source",
    "get_page_title", "get_current_url", "close_browser", "go_back", "refresh",
    "execute_script", "inspect_page",
    # element
    "find_element", "find_elements", "click", "type_text", "get_text",
    "get_attribute", "select_option", "hover", "is_displayed",
    "wait_for_element", "clear_field", "fill_form", "send_keys",
    "scroll_to_element", "switch_to_frame", "switch_to_default_content",
    "accept_alert", "dismiss_alert", "upload_file",
    # assertion
    "assert_title", "assert_url", "assert_text", "assert_element_visible",
    "assert_element_not_visible", "assert_attribute", "assert_page_contains",
    "assert_element_count",
    # codegen
    "detect_selenium_boot", "generate_java_page_object", "generate_java_testng",
    "generate_java_junit5", "generate_gherkin", "generate_python_test",
    "get_session_log", "clear_session_log",
})

PROFILE_ENV = "SELENIUM_MCP_TOOLS"


def selected_profile() -> str:
    value = os.environ.get(PROFILE_ENV, "all").strip().lower()
    return value if value in ("all", "core") else "all"


def select_tools(tools: list, handlers: dict) -> tuple[list, dict]:
    """Return (tools, handlers) restricted to the active profile."""
    if selected_profile() == "all":
        return tools, handlers
    return (
        [t for t in tools if t.name in CORE_TOOLS],
        {n: h for n, h in handlers.items() if n in CORE_TOOLS},
    )
