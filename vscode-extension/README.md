# Selenium Boot MCP — AI Browser Automation

Control a real Chrome/Firefox browser directly from **GitHub Copilot** and **Claude Code** using the Model Context Protocol.
84 tools for navigation, interaction, assertions, codegen, and more — no ChromeDriver setup needed.

---

## What it does

Installing this extension:

1. **Auto-registers** the `seleniumboot-mcp` server with GitHub Copilot (via `contributes.mcpServers`)
2. **Writes `.mcp.json`** into your open workspace so Claude Code picks it up automatically
3. **Prompts you to install** `seleniumboot-mcp` via pip if it isn't already

Once active, your AI assistant can control a real browser just by asking.

---

## Requirements

- **Python 3.10+** with `pip`
- **Google Chrome** (ChromeDriver is managed automatically — nothing to download)
- **VS Code 1.99+** with GitHub Copilot or Claude Code

---

## Quick start

### 1. Install the Python package

```bash
pip install seleniumboot-mcp
```

If the package isn't installed, the extension shows a notification on startup with an **Install via pip** button.

### 2. Approve the MCP server

When you open a project, Claude Code will detect the `.mcp.json` written by this extension and ask:

> *"Allow MCP server seleniumboot?"* → click **Allow**

For GitHub Copilot, the server is registered automatically via `contributes.mcpServers` — no approval needed.

### 3. Start automating

In **Copilot Chat** (Agent mode) or a **Claude Code** chat:

```
Go to https://example.com and take a screenshot
```

```
Fill the login form at https://myapp.com with admin / password and click Login
```

```
Assert the dashboard heading is visible, then generate a Java TestNG test for the session
```

Chrome opens automatically on the first browser command — no explicit "start browser" step required.

---

## Commands

Open the Command Palette (`Ctrl+Shift+P`) to access:

| Command | Description |
|---|---|
| `Seleniumboot MCP: Install` | Runs `pip install seleniumboot-mcp` in a terminal |
| `Seleniumboot MCP: Upgrade to latest` | Runs `pip install --upgrade seleniumboot-mcp` |
| `Seleniumboot MCP: Check installation status` | Confirms the package is installed and ready |

---

## Available tools (84)

### Browser
`navigate`, `take_screenshot`, `get_page_source`, `execute_script`, `go_back`, `go_forward`, `refresh`, `scroll_to_top`, `scroll_to_bottom`, `scroll_by`, `get_page_title`, `get_current_url`, `open_new_tab`, `close_current_tab`, `switch_to_window`, `list_windows`, `close_browser`, `emulate_device`, `get_console_logs`, `get_cookies`, `set_cookie`, `delete_cookie`, `delete_all_cookies`, `get_local_storage`, `set_local_storage`, `get_session_storage`, `set_session_storage`, `wait_for_network_idle`, `inspect_page`, `get_network_logs`, `mock_response`, `clear_mock_responses`, `compare_screenshot`, `check_accessibility`

### Elements
`find_element`, `find_elements`, `click`, `type_text`, `get_text`, `get_attribute`, `select_option`, `hover`, `double_click`, `right_click`, `drag_and_drop`, `is_displayed`, `is_enabled`, `wait_for_element`, `scroll_to_element`, `clear_field`, `send_keys`, `upload_file`, `accept_alert`, `dismiss_alert`, `get_alert_text`, `type_in_alert`, `switch_to_frame`, `switch_to_default_content`, `find_shadow_element`, `get_table_data`, `fill_form`, `get_healed_locators`, `clear_healed_locators`

### Assertions
`assert_title`, `assert_url`, `assert_text`, `assert_element_visible`, `assert_element_not_visible`, `assert_attribute`, `assert_page_contains`, `assert_element_count`

### Code generation
`generate_java_testng`, `generate_java_junit5`, `generate_java_page_object`, `generate_gherkin`, `generate_python_test`, `generate_csharp_nunit`, `generate_github_actions`, `generate_playwright_hints`, `get_session_log`, `clear_session_log`

---

## Example: generate a Java test

```
Go to https://myapp.com/login
Enter "admin" in the username field and "password" in the password field
Click the Login button
Assert the text "Dashboard" is visible
Generate a Java TestNG test class for this session
```

Claude or Copilot records every step and outputs a ready-to-paste test:

```java
public class LoginTest {
    @BeforeMethod public void setUp() { driver = new ChromeDriver(); }
    @AfterMethod  public void tearDown() { driver.quit(); }

    @Test
    public void recordedFlowTest() {
        driver.get("https://myapp.com/login");
        wait.until(visibilityOfElementLocated(By.cssSelector("#username"))).sendKeys("admin");
        driver.findElement(By.cssSelector("#password")).sendKeys("password");
        wait.until(elementToBeClickable(By.cssSelector("button[type='submit']"))).click();
        wait.until(visibilityOfElementLocated(By.xpath("//*[contains(text(),'Dashboard')]")));
    }
}
```

---

## Troubleshooting

**MCP server not connecting in Claude Code**
- Open the Command Palette → `Seleniumboot MCP: Check installation status`
- Ensure a `.mcp.json` file exists in your project root (the extension creates it automatically)
- Do `Developer: Reload Window` and open a fresh Claude Code chat

**"seleniumboot-mcp not found" error**
- Run `pip install seleniumboot-mcp` in a terminal
- Make sure the Python `bin` directory is in your PATH

**Chrome doesn't open**
- Chrome must be installed; ChromeDriver is handled automatically by Selenium Manager
- For headless environments use: *"Start browser in headless mode"*

---

## Links

- [GitHub](https://github.com/seleniumboot/selenium-mcp)
- [PyPI package](https://pypi.org/project/seleniumboot-mcp/)
- [Demo video](https://youtu.be/54LoY2HNLrs)
- [Report an issue](https://github.com/seleniumboot/selenium-mcp/issues)
