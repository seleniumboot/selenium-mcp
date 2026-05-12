# Selenium MCP Server 🤖🌐

A Python-based **Model Context Protocol (MCP)** server for Selenium WebDriver automation.
Built for AI assistants like Claude Desktop — with first-class support for generating
**Java TestNG** and **JUnit 5** test scripts.

---

## Features

| Category       | Tools                                                             |
|----------------|-------------------------------------------------------------------|
| **Browser**    | start, navigate, screenshot, page source, title, URL, JS exec    |
| **Elements**   | click, type, find, hover, drag-drop, select, scroll, wait        |
| **Assertions** | title, URL, text, visibility, attribute, page content, count     |
| **Codegen**    | Generate Python pytest · Java TestNG · Java JUnit 5 test scripts |

---

## Installation

```bash
# Clone
git clone https://github.com/yourname/selenium-mcp
cd selenium-mcp

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

**requirements.txt**
```
mcp>=1.0.0
selenium>=4.6.0
```
> Selenium 4.6+ ships with **Selenium Manager** — no separate driver manager needed.

---

## Configure Claude Desktop

Edit `claude_desktop_config.json`:

**macOS/Linux:** `~/.config/claude-desktop/config.json`  
**Windows:** `%APPDATA%\claude-desktop\config.json`

```json
{
  "mcpServers": {
    "selenium-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/selenium-mcp/src/server.py"]
    }
  }
}
```

Restart Claude Desktop.

---

## Usage with Claude

### Browser automation
```
"Start Chrome browser, go to https://github.com, search for selenium, click the first result"
```

### Assertion example
```
"Navigate to https://example.com and assert the page title contains 'Example Domain'"
```

### Java codegen — the killer feature
```
"Generate a Java TestNG test class for everything we just did"
```
Claude will produce a ready-to-run Java class with WebDriverWait, @BeforeMethod,
@Test, @AfterMethod — drop it straight into your Maven/Gradle project.

---

## Tool Reference

### Browser Tools
| Tool               | Description                              |
|--------------------|------------------------------------------|
| `start_browser`    | Start Chrome or Firefox                  |
| `navigate`         | Go to URL                                |
| `take_screenshot`  | Capture page as base64 PNG               |
| `get_page_title`   | Return page title                        |
| `get_current_url`  | Return current URL                       |
| `get_page_source`  | Return full HTML source                  |
| `execute_script`   | Run JavaScript                           |
| `go_back/forward`  | Browser history navigation               |
| `refresh`          | Reload current page                      |
| `switch_to_window` | Switch between tabs/windows              |
| `close_browser`    | Quit the browser                         |

### Element Tools
| Tool                | Description                             |
|---------------------|-----------------------------------------|
| `find_element`      | Find element, return tag/text/state     |
| `find_elements`     | Find all matching elements              |
| `click`             | Click with explicit wait                |
| `type_text`         | Clear + type into input                 |
| `get_text`          | Get visible text                        |
| `get_attribute`     | Get any attribute value                 |
| `select_option`     | Select from `<select>` dropdown         |
| `hover`             | Mouse hover                             |
| `double_click`      | Double click                            |
| `right_click`       | Context menu click                      |
| `drag_and_drop`     | Drag source → target                    |
| `is_displayed`      | Check visibility                        |
| `is_enabled`        | Check enabled state                     |
| `wait_for_element`  | Wait: visible/clickable/present/hidden  |
| `scroll_to_element` | Scroll element into view                |
| `clear_field`       | Clear input field                       |

### Assertion Tools
| Tool                       | Description                         |
|----------------------------|-------------------------------------|
| `assert_title`             | Page title equals/contains          |
| `assert_url`               | URL equals/contains                 |
| `assert_text`              | Element text equals/contains        |
| `assert_element_visible`   | Element is visible                  |
| `assert_element_not_visible` | Element is hidden/absent          |
| `assert_attribute`         | Element attribute value             |
| `assert_page_contains`     | Body text contains string           |
| `assert_element_count`     | Count of matching elements          |

### Codegen Tools
| Tool                    | Description                                  |
|-------------------------|----------------------------------------------|
| `generate_python_test`  | Generate pytest class from session           |
| `generate_java_testng`  | Generate Java TestNG class from session      |
| `generate_java_junit5`  | Generate Java JUnit 5 class from session     |
| `get_session_log`       | View recorded actions                        |
| `clear_session_log`     | Reset the session recording                  |

---

## Java Output Example

After a session: navigate → fill login form → click submit

```java
// Generated by selenium-mcp
package com.tests.selenium;

import org.testng.annotations.*;
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.*;
import java.time.Duration;

public class LoginTest {

    private WebDriver driver;
    private WebDriverWait wait;

    @BeforeMethod
    public void setUp() {
        driver = new ChromeDriver();
        driver.manage().window().maximize();
        wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    @AfterMethod
    public void tearDown() {
        if (driver != null) driver.quit();
    }

    @Test
    public void recordedFlowTest() {
        driver.get("https://app.example.com/login");
        WebElement field = wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("#email")));
        field.clear();
        field.sendKeys("user@example.com");
        wait.until(ExpectedConditions.elementToBeClickable(By.cssSelector("button[type='submit']"))).click();
    }
}
```

---

## Logs

Debug logs: `/tmp/selenium-mcp.log`

---

## Roadmap

- [ ] Self-healing locators (TestHeal integration)
- [ ] TestFlow export
- [ ] Page Object Model generation
- [ ] Cucumber/Gherkin step generation
- [ ] CI/CD config generator (GitHub Actions, Jenkins)

---

## License
MIT