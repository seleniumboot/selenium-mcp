"""
Codegen Tools — generate Python (pytest) and Java (TestNG/JUnit5) test scripts
from the recorded session log. This is the key differentiator for Java users.
"""

from mcp.types import Tool


class CodegenTools:
    def __init__(self, browser_tools):
        self.browser = browser_tools

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="generate_python_test",
                description=(
                    "Generate a pytest + Selenium test script from the current browser session. "
                    "Captures all recorded actions (navigate, click, type, hover, drag, select, etc.) into a runnable test."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "test_name": {
                            "type": "string",
                            "default": "test_recorded_flow",
                            "description": "Name of the test function"
                        },
                        "class_name": {
                            "type": "string",
                            "default": "TestRecordedFlow",
                            "description": "Name of the test class"
                        },
                    },
                },
            ),
            Tool(
                name="generate_java_testng",
                description=(
                    "Generate a Java TestNG test class from the current browser session. "
                    "Includes @BeforeMethod, @Test, @AfterMethod and WebDriverWait patterns."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "test_name": {
                            "type": "string",
                            "default": "RecordedFlowTest"
                        },
                        "package_name": {
                            "type": "string",
                            "default": "com.tests.selenium"
                        }
                    },
                },
            ),
            Tool(
                name="generate_java_junit5",
                description=(
                    "Generate a Java JUnit 5 test class from the current browser session. "
                    "Includes @BeforeEach, @Test, @AfterEach and proper WebDriverWait usage."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "test_name": {
                            "type": "string",
                            "default": "RecordedFlowTest"
                        },
                        "package_name": {
                            "type": "string",
                            "default": "com.tests.selenium"
                        }
                    },
                },
            ),
            Tool(
                name="get_session_log",
                description="Return the raw list of recorded actions in the current session.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="clear_session_log",
                description="Clear the recorded action log and start fresh.",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    def get_handlers(self) -> dict:
        return {
            "generate_python_test":  self._generate_python,
            "generate_java_testng":  self._generate_java_testng,
            "generate_java_junit5":  self._generate_java_junit5,
            "get_session_log":       self._get_session_log,
            "clear_session_log":     self._clear_session_log,
        }

    # ------------------------------------------------------------------ #
    #  Session log utils                                                   #
    # ------------------------------------------------------------------ #
    async def _get_session_log(self, args: dict) -> str:
        log = self.browser._session_log
        if not log:
            return "Session log is empty. Perform some browser actions first."
        lines = [f"[{i}] {entry}" for i, entry in enumerate(log)]
        return "\n".join(lines)

    async def _clear_session_log(self, args: dict) -> str:
        self.browser._session_log = []
        return "✅ Session log cleared."

    # ------------------------------------------------------------------ #
    #  Python / pytest codegen                                             #
    # ------------------------------------------------------------------ #
    async def _generate_python(self, args: dict) -> str:
        log = self.browser._session_log
        test_name = args.get("test_name", "test_recorded_flow")
        class_name = args.get("class_name", "TestRecordedFlow")

        steps = self._log_to_python_steps(log)

        code = f'''import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class {class_name}:

    def setup_method(self):
        opts = Options()
        # opts.add_argument("--headless=new")
        self.driver = webdriver.Chrome(options=opts)
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 10)

    def teardown_method(self):
        if self.driver:
            self.driver.quit()

    def {test_name}(self):
{steps}
'''
        return code

    def _log_to_python_steps(self, log: list) -> str:
        lines = []
        indent = "        "
        for entry in log:
            action = entry.get("action")
            by = entry.get("by", "css")
            sel = entry.get("selector", "")
            by_const = self._py_by(by)

            if action == "start_browser":
                lines.append(f"{indent}# Browser started — handled in setup_method")
            elif action == "navigate":
                lines.append(f'{indent}self.driver.get("{entry["url"]}")')
            elif action == "click":
                lines.append(f'{indent}self.wait.until(EC.element_to_be_clickable(({by_const}, "{sel}"))).click()')
            elif action == "type_text":
                text = entry.get("text", "")
                lines.append(f'{indent}el = self.wait.until(EC.visibility_of_element_located(({by_const}, "{sel}")))')
                lines.append(f'{indent}el.clear()')
                lines.append(f'{indent}el.send_keys("{text}")')
            elif action == "hover":
                lines.append(f'{indent}el = self.wait.until(EC.visibility_of_element_located(({by_const}, "{sel}")))')
                lines.append(f'{indent}ActionChains(self.driver).move_to_element(el).perform()')
            elif action == "double_click":
                lines.append(f'{indent}el = self.wait.until(EC.element_to_be_clickable(({by_const}, "{sel}")))')
                lines.append(f'{indent}ActionChains(self.driver).double_click(el).perform()')
            elif action == "right_click":
                lines.append(f'{indent}el = self.wait.until(EC.visibility_of_element_located(({by_const}, "{sel}")))')
                lines.append(f'{indent}ActionChains(self.driver).context_click(el).perform()')
            elif action == "scroll_to_element":
                lines.append(f'{indent}el = self.wait.until(EC.presence_of_element_located(({by_const}, "{sel}")))')
                lines.append(f'{indent}self.driver.execute_script("arguments[0].scrollIntoView(true);", el)')
            elif action == "select_option":
                lines.append(f'{indent}el = self.wait.until(EC.visibility_of_element_located(({by_const}, "{sel}")))')
                lines.append(f'{indent}sel_obj = Select(el)')
                if "by_text" in entry:
                    lines.append(f'{indent}sel_obj.select_by_visible_text("{entry["by_text"]}")')
                elif "by_value" in entry:
                    lines.append(f'{indent}sel_obj.select_by_value("{entry["by_value"]}")')
                elif "by_index" in entry:
                    lines.append(f'{indent}sel_obj.select_by_index({entry["by_index"]})')
            elif action == "go_back":
                lines.append(f"{indent}self.driver.back()")
            elif action == "go_forward":
                lines.append(f"{indent}self.driver.forward()")
            elif action == "refresh":
                lines.append(f"{indent}self.driver.refresh()")
            elif action == "execute_script":
                script = entry.get("script", "").replace('"', '\\"')
                lines.append(f'{indent}self.driver.execute_script("{script}")')
            else:
                lines.append(f"{indent}# TODO: {entry}")
        if not lines:
            lines.append(f'{indent}pass  # No actions recorded')
        return "\n".join(lines)

    def _py_by(self, by: str) -> str:
        return {
            "css":          "By.CSS_SELECTOR",
            "xpath":        "By.XPATH",
            "id":           "By.ID",
            "name":         "By.NAME",
            "tag":          "By.TAG_NAME",
            "class":        "By.CLASS_NAME",
            "link":         "By.LINK_TEXT",
            "partial_link": "By.PARTIAL_LINK_TEXT",
        }.get(by, "By.CSS_SELECTOR")

    # ------------------------------------------------------------------ #
    #  Java TestNG codegen                                                 #
    # ------------------------------------------------------------------ #
    async def _generate_java_testng(self, args: dict) -> str:
        log = self.browser._session_log
        test_name = args.get("test_name", "RecordedFlowTest")
        package = args.get("package_name", "com.tests.selenium")
        steps = self._log_to_java_steps(log)

        code = f'''package {package};

import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.interactions.Actions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.Select;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;
import java.time.Duration;

public class {test_name} {{

    private WebDriver driver;
    private WebDriverWait wait;

    @BeforeMethod
    public void setUp() {{
        ChromeOptions options = new ChromeOptions();
        // options.addArguments("--headless=new");
        driver = new ChromeDriver(options);
        driver.manage().window().maximize();
        wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }}

    @AfterMethod
    public void tearDown() {{
        if (driver != null) {{
            driver.quit();
        }}
    }}

    @Test
    public void recordedFlowTest() {{
{steps}
    }}
}}
'''
        return code

    # ------------------------------------------------------------------ #
    #  Java JUnit 5 codegen                                                #
    # ------------------------------------------------------------------ #
    async def _generate_java_junit5(self, args: dict) -> str:
        log = self.browser._session_log
        test_name = args.get("test_name", "RecordedFlowTest")
        package = args.get("package_name", "com.tests.selenium")
        steps = self._log_to_java_steps(log)

        code = f'''package {package};

import org.junit.jupiter.api.*;
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.interactions.Actions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.Select;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

import static org.junit.jupiter.api.Assertions.*;

public class {test_name} {{

    private WebDriver driver;
    private WebDriverWait wait;

    @BeforeEach
    void setUp() {{
        ChromeOptions options = new ChromeOptions();
        // options.addArguments("--headless=new");
        driver = new ChromeDriver(options);
        driver.manage().window().maximize();
        wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }}

    @AfterEach
    void tearDown() {{
        if (driver != null) {{
            driver.quit();
        }}
    }}

    @Test
    @DisplayName("Recorded Flow Test")
    void recordedFlowTest() {{
{steps}
    }}
}}
'''
        return code

    def _log_to_java_steps(self, log: list) -> str:
        lines = []
        indent = "        "
        for entry in log:
            action = entry.get("action")
            by = entry.get("by", "css")
            sel = entry.get("selector", "")
            by_java = self._java_by(by, sel)

            if action == "start_browser":
                lines.append(f"{indent}// Browser started — handled in setUp()")
            elif action == "navigate":
                lines.append(f'{indent}driver.get("{entry["url"]}");')
            elif action == "click":
                lines.append(f'{indent}wait.until(ExpectedConditions.elementToBeClickable({by_java})).click();')
            elif action == "type_text":
                text = entry.get("text", "")
                lines.append(f'{indent}WebElement field = wait.until(ExpectedConditions.visibilityOfElementLocated({by_java}));')
                lines.append(f'{indent}field.clear();')
                lines.append(f'{indent}field.sendKeys("{text}");')
            elif action == "hover":
                lines.append(f'{indent}new Actions(driver).moveToElement(wait.until(ExpectedConditions.visibilityOfElementLocated({by_java}))).perform();')
            elif action == "double_click":
                lines.append(f'{indent}new Actions(driver).doubleClick(wait.until(ExpectedConditions.elementToBeClickable({by_java}))).perform();')
            elif action == "right_click":
                lines.append(f'{indent}new Actions(driver).contextClick(wait.until(ExpectedConditions.visibilityOfElementLocated({by_java}))).perform();')
            elif action == "scroll_to_element":
                lines.append(f'{indent}((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView(true);", wait.until(ExpectedConditions.presenceOfElementLocated({by_java})));')
            elif action == "select_option":
                lines.append(f'{indent}Select dropdown = new Select(wait.until(ExpectedConditions.visibilityOfElementLocated({by_java})));')
                if "by_text" in entry:
                    lines.append(f'{indent}dropdown.selectByVisibleText("{entry["by_text"]}");')
                elif "by_value" in entry:
                    lines.append(f'{indent}dropdown.selectByValue("{entry["by_value"]}");')
                elif "by_index" in entry:
                    lines.append(f'{indent}dropdown.selectByIndex({entry["by_index"]});')
            elif action == "go_back":
                lines.append(f"{indent}driver.navigate().back();")
            elif action == "go_forward":
                lines.append(f"{indent}driver.navigate().forward();")
            elif action == "refresh":
                lines.append(f"{indent}driver.navigate().refresh();")
            elif action == "execute_script":
                script = entry.get("script", "").replace('"', '\\"')
                lines.append(f'{indent}((JavascriptExecutor) driver).executeScript("{script}");')
            else:
                lines.append(f"{indent}// TODO: {entry}")
        if not lines:
            lines.append(f"{indent}// No actions recorded")
        return "\n".join(lines)

    def _java_by(self, by: str, selector: str) -> str:
        sel = selector.replace('"', '\\"')
        return {
            "css":          f'By.cssSelector("{sel}")',
            "xpath":        f'By.xpath("{sel}")',
            "id":           f'By.id("{sel}")',
            "name":         f'By.name("{sel}")',
            "tag":          f'By.tagName("{sel}")',
            "class":        f'By.className("{sel}")',
            "link":         f'By.linkText("{sel}")',
            "partial_link": f'By.partialLinkText("{sel}")',
        }.get(by, f'By.cssSelector("{sel}")')
