# seleniumboot-mcp

A Python **Model Context Protocol (MCP)** server for Selenium WebDriver automation.
Let Claude or GitHub Copilot control a real browser — navigate pages, interact with elements,
run assertions, and generate ready-to-run **Java TestNG / JUnit 5 / Cucumber / pytest** test code from recorded sessions.
43 tools. No ChromeDriver setup. Browser auto-starts on first use.

[![PyPI](https://img.shields.io/pypi/v/seleniumboot-mcp)](https://pypi.org/project/seleniumboot-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/seleniumboot-mcp)](https://pypi.org/project/seleniumboot-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Installation

```bash
pip install seleniumboot-mcp
```

> Requires Python 3.10+ and Chrome. No separate ChromeDriver needed — Selenium Manager handles it automatically.

---

## Setup

### VS Code (Claude / Copilot)

Add `.vscode/mcp.json` to your project root:

```json
{
  "servers": {
    "selenium": {
      "type": "stdio",
      "command": "seleniumboot-mcp"
    }
  }
}
```

Open the project in VS Code → click the **Start** button that appears above the config → done.

### Claude Desktop

Edit your Claude Desktop config:

- **Windows:** `%APPDATA%\claude-desktop\config.json`
- **macOS:** `~/.config/claude-desktop/config.json`

```json
{
  "mcpServers": {
    "selenium": {
      "command": "seleniumboot-mcp"
    }
  }
}
```

Restart Claude Desktop.

---

## How to use

Once the server is running, talk to Claude naturally — no `start_browser` call needed, Chrome launches automatically on first use:

```
Go to https://myapp.com and fill the login form with admin/password, then click Login
```

```
Assert the dashboard heading is visible
```

```
Generate a Java TestNG test class for everything we just did
```

```
Generate a Gherkin feature file and step definitions for the login flow
```

Claude controls the real browser, records every action, and on request generates complete test code ready to paste into your Maven or Gradle project.

---

## Tools (43 total)

### Browser
| Tool | Description |
|---|---|
| `start_browser` | Optional — Chrome auto-starts on first use. Use this to pick Firefox, enable headless, or set window size |
| `navigate` | Go to a URL |
| `take_screenshot` | Capture page as an inline image |
| `get_page_title` | Return page title |
| `get_current_url` | Return current URL |
| `get_page_source` | Return full HTML source |
| `execute_script` | Run JavaScript |
| `go_back` / `go_forward` | Browser history |
| `refresh` | Reload page |
| `switch_to_window` | Switch between tabs by index |
| `close_browser` | Quit the browser |

### Elements
| Tool | Description |
|---|---|
| `find_element` | Find element, return tag/text/state |
| `find_elements` | Find all matching elements |
| `click` | Click with explicit wait |
| `type_text` | Clear + type into input |
| `get_text` | Get visible text |
| `get_attribute` | Get any attribute value |
| `select_option` | Select from `<select>` by text, value, or index |
| `hover` | Mouse hover |
| `double_click` | Double click |
| `right_click` | Context menu click |
| `drag_and_drop` | Drag source → target |
| `is_displayed` | Check visibility |
| `is_enabled` | Check enabled state |
| `wait_for_element` | Wait: visible / clickable / present / invisible |
| `scroll_to_element` | Scroll element into view |
| `clear_field` | Clear input field |

### Assertions
| Tool | Description |
|---|---|
| `assert_title` | Page title equals/contains |
| `assert_url` | URL equals/contains |
| `assert_text` | Element text equals/contains |
| `assert_element_visible` | Element is visible |
| `assert_element_not_visible` | Element is hidden or absent |
| `assert_attribute` | Element attribute has expected value |
| `assert_page_contains` | Page body contains a string |
| `assert_element_count` | Count of matching elements equals expected |

### Codegen
| Tool | Description |
|---|---|
| `generate_java_testng` | Java TestNG test class from session |
| `generate_java_junit5` | Java JUnit 5 test class from session |
| `generate_java_page_object` | Java Page Object class + test class from session |
| `generate_gherkin` | Gherkin `.feature` file + Java step definitions from session |
| `generate_python_test` | pytest class from session |
| `get_session_log` | View recorded actions |
| `clear_session_log` | Reset the session recording |

---

## Codegen Examples

### Java TestNG

```
Go to https://myapp.com/login, enter admin/password, click Login
→ Generate a Java TestNG test
```

```java
public class LoginTest {
    @BeforeMethod public void setUp() { driver = new ChromeDriver(); ... }
    @AfterMethod  public void tearDown() { driver.quit(); }

    @Test
    public void recordedFlowTest() {
        driver.get("https://myapp.com/login");
        WebElement f = wait.until(visibilityOf(By.cssSelector("#username")));
        f.clear(); f.sendKeys("admin");
        wait.until(elementToBeClickable(By.cssSelector("button[type='submit']"))).click();
    }
}
```

### Page Object Model

```
Generate a Java Page Object for the login page
```

```java
// LoginPage.java
public class LoginPage {
    private final By usernameField = By.cssSelector("#username");
    private final By submitButton  = By.cssSelector("button[type='submit']");

    public LoginPage enterUsernameField(String text) { ... return this; }
    public LoginPage clickSubmitButton()              { ... return this; }
}

// LoginTest.java
public class LoginTest {
    @Test public void recordedFlowTest() {
        driver.get("https://myapp.com/login");
        page.enterUsernameField("admin").clickSubmitButton();
    }
}
```

### Cucumber / Gherkin

```
Generate a Gherkin feature file and step definitions for the login flow
```

```gherkin
Feature: Login

  Scenario: User logs in with valid credentials
    Given I navigate to "https://myapp.com/login"
    And I enter "admin" in the username field
    And I enter "password" in the password field
    And I click the submit button
```

```java
// LoginSteps.java
public class LoginSteps {
    @Given("I navigate to {string}")
    public void iNavigateTo(String url) { driver.get(url); }

    @And("I enter {string} in the username field")
    public void iEnterInUsernameField(String text) { ... el.sendKeys(text); }

    @And("I click the submit button")
    public void iClickTheSubmitButton() { wait.until(...).click(); }
}
```

---

## Links

- **GitHub:** [github.com/seleniumboot/selenium-mcp](https://github.com/seleniumboot/selenium-mcp)
- **PyPI:** [pypi.org/project/seleniumboot-mcp](https://pypi.org/project/seleniumboot-mcp/)

---

## Roadmap

- [x] Java TestNG / JUnit 5 / Python pytest code generation
- [x] Screenshot returned as `ImageContent` (renders inline in Claude)
- [x] Full session recording — hover, double_click, right_click, scroll, select_option
- [x] Codegen for hover, drag-and-drop, select, scroll in Java and Python templates
- [x] Auto-start browser on first use (no explicit `start_browser` needed)
- [x] Page Object Model generation (`generate_java_page_object`)
- [x] Cucumber / Gherkin step generation (`generate_gherkin`)
- [ ] CI/CD config generator (GitHub Actions, Jenkins)
- [ ] Self-healing locators

---

## License

MIT
