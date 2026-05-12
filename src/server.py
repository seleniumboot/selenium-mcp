"""
Selenium MCP Server
A Python-based MCP server for Selenium WebDriver automation.
Serves both Python and Java test automation users.
"""

import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from tools.browser_tools import BrowserTools
from tools.element_tools import ElementTools
from tools.assertion_tools import AssertionTools
from tools.codegen_tools import CodegenTools

logging.basicConfig(
    filename="/tmp/selenium-mcp.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

app = Server("selenium-mcp")

# Tool registry
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
        return [TextContent(type="text", text=result)]
    except Exception as e:
        log.error(f"Tool error [{name}]: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())