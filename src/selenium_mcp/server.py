"""
Selenium MCP Server
A Python-based MCP server for Selenium WebDriver automation.
Serves both Python and Java test automation users.
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent

from selenium_mcp.tools.browser_tools import BrowserTools
from selenium_mcp.tools.element_tools import ElementTools
from selenium_mcp.tools.assertion_tools import AssertionTools
from selenium_mcp.tools.codegen_tools import CodegenTools

_log_path = Path(tempfile.gettempdir()) / "selenium-mcp.log"
_log_path.touch(mode=0o600, exist_ok=True)
logging.basicConfig(
    filename=str(_log_path),
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

SERVER_INSTRUCTIONS = """\
Selenium Boot MCP — real-browser automation plus test-code generation.

GOLDEN RULE: never hand-write test or page-object source. After driving the
browser, ALWAYS produce code with the generate_* codegen tools and save their
output verbatim. Hand-written code drifts from the framework API (wrong driver
access, non-existent helpers) and invents UI elements that do not exist.

Workflow for "automate X" / "write a test for the X form":
1. start_browser, then navigate to the page.
2. Inspect the live DOM (get_page_source) and interact ONLY with elements that
   are really there. Do NOT assume a form has fields it does not render — e.g.
   only fill username / password if the page actually shows them.
3. Generate code from the recorded session with the matching tool:
     - Java in a Selenium Boot project -> generate_java_page_object with
       framework="selenium_boot" (Test extends BaseTest, Page extends BasePage,
       framework-managed driver via getDriver(), accessibility-first locators —
       getByRole / getByTestId / getByText; compiles against the framework as-is).
     - Plain Selenium -> framework="testng" or "junit5".
     - Also: generate_python_test, generate_csharp_nunit, generate_gherkin.
4. Write each emitted file at the path in its "File:" header, unchanged.
5. close_browser when finished.

Generated code contains ONLY the elements and actions actually performed, so it
compiles and never references non-existent fields. To cover more, interact with
more real elements first, then regenerate — do not pad the test by hand.
"""

app = Server("selenium-mcp", instructions=SERVER_INSTRUCTIONS)

browser = BrowserTools()
element = ElementTools(browser)
assertion = AssertionTools(browser)
codegen = CodegenTools(browser)

ALL_TOOLS = [
    *browser.get_tools(),
    *element.get_tools(),
    *assertion.get_tools(),
    *codegen.get_tools(),
]

TOOL_HANDLERS = {
    **browser.get_handlers(),
    **element.get_handlers(),
    **assertion.get_handlers(),
    **codegen.get_handlers(),
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    return ALL_TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    log.info(f"Tool called: {name} | args: {arguments}")
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    try:
        result = await handler(arguments)
        if isinstance(result, str) and result.startswith("screenshot:base64:"):
            b64 = result[len("screenshot:base64:"):]
            return [ImageContent(type="image", data=b64, mimeType="image/png")]
        return [TextContent(type="text", text=result)]
    except Exception as e:
        log.error(f"Tool error [{name}]: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
