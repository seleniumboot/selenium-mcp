"""
Codegen Tools — generate Python (pytest) and Java (TestNG/JUnit5) test scripts
from the recorded session log. This is the key differentiator for Java users.
"""

import re
from urllib.parse import urlparse
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
            Tool(
                name="generate_gherkin",
                description=(
                    "Generate a Cucumber Gherkin .feature file + Java step definitions class "
                    "from the recorded browser session. Steps are written in plain English "
                    "and wired to full Selenium WebDriver code."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "feature_name": {
                            "type": "string",
                            "description": "Feature name e.g. 'Login'. Auto-inferred from URL if omitted."
                        },
                        "scenario_name": {
                            "type": "string",
                            "default": "Recorded user flow"
                        },
                        "package_name": {
                            "type": "string",
                            "default": "com.tests.selenium"
                        }
                    },
                },
            ),
            Tool(
                name="generate_java_page_object",
                description=(
                    "Generate a Java Page Object class + matching test class from the recorded session. "
                    "Produces two files: a Page Object (locators + fluent action methods) and a Test class "
                    "that uses it. Supports TestNG and JUnit 5."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_name": {
                            "type": "string",
                            "description": "Name of the page class e.g. LoginPage. Auto-inferred from URL if omitted."
                        },
                        "package_name": {
                            "type": "string",
                            "default": "com.tests.selenium"
                        },
                        "framework": {
                            "type": "string",
                            "enum": ["testng", "junit5"],
                            "default": "testng"
                        }
                    },
                },
            ),
        ]

    def get_handlers(self) -> dict:
        return {
            "generate_python_test":       self._generate_python,
            "generate_java_testng":       self._generate_java_testng,
            "generate_java_junit5":       self._generate_java_junit5,
            "get_session_log":            self._get_session_log,
            "clear_session_log":          self._clear_session_log,
            "generate_java_page_object":  self._generate_java_page_object,
            "generate_gherkin":           self._generate_gherkin,
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

    # ------------------------------------------------------------------ #
    #  Page Object Model codegen                                           #
    # ------------------------------------------------------------------ #

    async def _generate_java_page_object(self, args: dict) -> str:
        log = self.browser._session_log
        package = args.get("package_name", "com.tests.selenium")
        pages_package = f"{package}.pages"
        framework = args.get("framework", "testng")

        base_url = next((e["url"] for e in log if e.get("action") == "navigate"), "")
        inferred = self._url_to_page_name(base_url)
        page_name = args.get("page_name", f"{inferred}Page")
        test_name = page_name[:-4] + "Test" if page_name.endswith("Page") else f"{page_name}Test"

        elements = self._build_element_map(log)

        page_code = self._java_page_class(page_name, pages_package, elements)
        test_code = self._java_pom_test(test_name, package, pages_package, page_name, framework, base_url, log, elements)

        sep = "=" * 60
        return (
            f"{sep}\n"
            f"File: {pages_package.replace('.', '/')}/{page_name}.java\n"
            f"{sep}\n"
            f"{page_code}\n\n"
            f"{sep}\n"
            f"File: {package.replace('.', '/')}/{test_name}.java\n"
            f"{sep}\n"
            f"{test_code}"
        )

    def _url_to_page_name(self, url: str) -> str:
        try:
            segment = urlparse(url).path.strip("/").split("/")[-1]
            return segment.capitalize() if segment else "Home"
        except Exception:
            return "Recorded"

    def _selector_to_name(self, selector: str, by: str) -> str:
        sel = selector.strip()
        if by in ("id", "name"):
            return self._to_camel(sel)
        if by == "css":
            if sel.startswith("#"):
                return self._to_camel(sel[1:])
            if sel.startswith("."):
                return self._to_camel(sel[1:].split(".")[0])
            m = re.search(r"\[type=['\"]?(\w+)['\"]?\]", sel)
            if m:
                typ = m.group(1)
                tag_m = re.match(r"^(\w+)", sel)
                tag = tag_m.group(1) if tag_m else "element"
                suffix = "Button" if tag == "button" else "Field"
                return self._to_camel(f"{typ}_{suffix}")
            tag_m = re.match(r"^(\w+)$", sel)
            if tag_m:
                return self._to_camel(tag_m.group(1))
            clean = re.sub(r"[^\w]", "_", sel).strip("_")
            return self._to_camel(clean[:30]) or "element"
        if by == "xpath":
            parts = [p for p in re.split(r"[/\[\]@=]", sel) if p and p[0].isalpha()]
            name = parts[-1] if parts else "element"
            return self._to_camel(re.sub(r"[^\w]", "_", name))
        if by in ("tag", "class"):
            return self._to_camel(selector)
        if by == "link":
            return self._to_camel("_".join(selector.split()[:2]).lower())
        return "element"

    def _to_camel(self, s: str) -> str:
        parts = [p for p in re.split(r"[_\-\s]+", s.strip()) if p]
        return (parts[0].lower() + "".join(p.capitalize() for p in parts[1:])) if parts else "element"

    def _build_element_map(self, log: list) -> dict:
        """Return ordered dict: field_name → {selector, by, actions: set}."""
        ELEMENT_ACTIONS = {"click", "type_text", "hover", "double_click",
                           "right_click", "scroll_to_element", "select_option"}
        elements = {}   # field_name → info
        key_to_name = {}  # (selector, by) → field_name

        for entry in log:
            action = entry.get("action")
            if action not in ELEMENT_ACTIONS:
                continue
            sel = entry.get("selector", "")
            by = entry.get("by", "css")
            if not sel:
                continue

            key = (sel, by)
            if key not in key_to_name:
                raw = self._selector_to_name(sel, by)
                name = raw
                suffix = 2
                while name in elements:
                    name = f"{raw}{suffix}"
                    suffix += 1
                key_to_name[key] = name
                elements[name] = {"selector": sel, "by": by, "actions": set(), "meta": {}}

            name = key_to_name[key]
            elements[name]["actions"].add(action)
            if action == "select_option":
                for k in ("by_text", "by_value", "by_index"):
                    if k in entry:
                        elements[name]["meta"]["select_key"] = k
                        elements[name]["meta"]["select_val"] = entry[k]

        return elements

    def _java_page_class(self, page_name: str, package: str, elements: dict) -> str:
        i = "    "
        lines = [
            f"package {package};",
            "",
            "import org.openqa.selenium.By;",
            "import org.openqa.selenium.JavascriptExecutor;",
            "import org.openqa.selenium.WebDriver;",
            "import org.openqa.selenium.WebElement;",
            "import org.openqa.selenium.interactions.Actions;",
            "import org.openqa.selenium.support.ui.ExpectedConditions;",
            "import org.openqa.selenium.support.ui.Select;",
            "import org.openqa.selenium.support.ui.WebDriverWait;",
            "import java.time.Duration;",
            "",
            f"public class {page_name} {{",
            "",
            f"{i}private final WebDriver driver;",
            f"{i}private final WebDriverWait wait;",
            "",
        ]

        for name, el in elements.items():
            lines.append(f"{i}private final By {name} = {self._java_by(el['by'], el['selector'])};")
        lines.append("")

        lines += [
            f"{i}public {page_name}(WebDriver driver) {{",
            f"{i}{i}this.driver = driver;",
            f"{i}{i}this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));",
            f"{i}}}",
            "",
        ]

        for name, el in elements.items():
            cap = name[0].upper() + name[1:]
            acts = el["actions"]

            if "type_text" in acts:
                lines += [
                    f"{i}public {page_name} enter{cap}(String text) {{",
                    f"{i}{i}WebElement el = wait.until(ExpectedConditions.visibilityOfElementLocated({name}));",
                    f"{i}{i}el.clear();",
                    f"{i}{i}el.sendKeys(text);",
                    f"{i}{i}return this;",
                    f"{i}}}",
                    "",
                ]
            if "click" in acts:
                lines += [
                    f"{i}public {page_name} click{cap}() {{",
                    f"{i}{i}wait.until(ExpectedConditions.elementToBeClickable({name})).click();",
                    f"{i}{i}return this;",
                    f"{i}}}",
                    "",
                ]
            if "hover" in acts:
                lines += [
                    f"{i}public {page_name} hover{cap}() {{",
                    f"{i}{i}new Actions(driver).moveToElement(wait.until(ExpectedConditions.visibilityOfElementLocated({name}))).perform();",
                    f"{i}{i}return this;",
                    f"{i}}}",
                    "",
                ]
            if "double_click" in acts:
                lines += [
                    f"{i}public {page_name} doubleClick{cap}() {{",
                    f"{i}{i}new Actions(driver).doubleClick(wait.until(ExpectedConditions.elementToBeClickable({name}))).perform();",
                    f"{i}{i}return this;",
                    f"{i}}}",
                    "",
                ]
            if "right_click" in acts:
                lines += [
                    f"{i}public {page_name} rightClick{cap}() {{",
                    f"{i}{i}new Actions(driver).contextClick(wait.until(ExpectedConditions.visibilityOfElementLocated({name}))).perform();",
                    f"{i}{i}return this;",
                    f"{i}}}",
                    "",
                ]
            if "scroll_to_element" in acts:
                lines += [
                    f"{i}public {page_name} scrollTo{cap}() {{",
                    f"{i}{i}((JavascriptExecutor) driver).executeScript(\"arguments[0].scrollIntoView(true);\", wait.until(ExpectedConditions.presenceOfElementLocated({name})));",
                    f"{i}{i}return this;",
                    f"{i}}}",
                    "",
                ]
            if "select_option" in acts:
                lines += [
                    f"{i}public {page_name} select{cap}ByText(String text) {{",
                    f"{i}{i}new Select(wait.until(ExpectedConditions.visibilityOfElementLocated({name}))).selectByVisibleText(text);",
                    f"{i}{i}return this;",
                    f"{i}}}",
                    "",
                    f"{i}public {page_name} select{cap}ByValue(String value) {{",
                    f"{i}{i}new Select(wait.until(ExpectedConditions.visibilityOfElementLocated({name}))).selectByValue(value);",
                    f"{i}{i}return this;",
                    f"{i}}}",
                    "",
                ]

        lines.append("}")
        return "\n".join(lines)

    def _java_pom_test(self, test_name, package, pages_package, page_name,
                       framework, base_url, log, elements) -> str:
        i = "    "
        key_to_name = {(v["selector"], v["by"]): n for n, v in elements.items()}

        if framework == "testng":
            fw_imports = ["import org.testng.annotations.*;"]
            before, after, test = "@BeforeMethod", "@AfterMethod", "@Test"
        else:
            fw_imports = ["import org.junit.jupiter.api.*;", "import static org.junit.jupiter.api.Assertions.*;"]
            before, after, test = "@BeforeEach", "@AfterEach", "@Test"

        lines = [
            f"package {package};",
            "",
            f"import {pages_package}.{page_name};",
            "import org.openqa.selenium.WebDriver;",
            "import org.openqa.selenium.chrome.ChromeDriver;",
            "import org.openqa.selenium.chrome.ChromeOptions;",
            *fw_imports,
            "",
            f"public class {test_name} {{",
            "",
            f"{i}private WebDriver driver;",
            f"{i}private {page_name} page;",
            "",
            f"{i}{before}",
            f"{i}public void setUp() {{",
            f"{i}{i}ChromeOptions options = new ChromeOptions();",
            f"{i}{i}// options.addArguments(\"--headless=new\");",
            f"{i}{i}driver = new ChromeDriver(options);",
            f"{i}{i}driver.manage().window().maximize();",
            f"{i}{i}page = new {page_name}(driver);",
            f"{i}}}",
            "",
            f"{i}{after}",
            f"{i}public void tearDown() {{",
            f"{i}{i}if (driver != null) driver.quit();",
            f"{i}}}",
            "",
            f"{i}{test}",
            f"{i}public void recordedFlowTest() {{",
        ]

        if base_url:
            lines.append(f'{i}{i}driver.get("{base_url}");')

        for entry in log:
            action = entry.get("action")
            sel = entry.get("selector", "")
            by = entry.get("by", "css")
            name = key_to_name.get((sel, by))

            if action == "navigate" and entry.get("url") != base_url:
                lines.append(f'{i}{i}driver.get("{entry["url"]}");')
            elif action == "go_back":
                lines.append(f"{i}{i}driver.navigate().back();")
            elif action == "go_forward":
                lines.append(f"{i}{i}driver.navigate().forward();")
            elif action == "refresh":
                lines.append(f"{i}{i}driver.navigate().refresh();")
            elif name:
                cap = name[0].upper() + name[1:]
                if action == "type_text":
                    lines.append(f'{i}{i}page.enter{cap}("{entry.get("text", "")}");')
                elif action == "click":
                    lines.append(f"{i}{i}page.click{cap}();")
                elif action == "hover":
                    lines.append(f"{i}{i}page.hover{cap}();")
                elif action == "double_click":
                    lines.append(f"{i}{i}page.doubleClick{cap}();")
                elif action == "scroll_to_element":
                    lines.append(f"{i}{i}page.scrollTo{cap}();")
                elif action == "select_option":
                    meta = elements[name]["meta"]
                    if meta.get("select_key") == "by_text":
                        lines.append(f'{i}{i}page.select{cap}ByText("{meta["select_val"]}");')
                    else:
                        lines.append(f'{i}{i}page.select{cap}ByValue("{meta.get("select_val", "")}");')

        lines += [f"{i}}}", "}"]
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  Cucumber / Gherkin codegen                                          #
    # ------------------------------------------------------------------ #

    async def _generate_gherkin(self, args: dict) -> str:
        log = self.browser._session_log
        package = args.get("package_name", "com.tests.selenium")
        steps_package = f"{package}.steps"
        scenario = args.get("scenario_name", "Recorded user flow")

        base_url = next((e["url"] for e in log if e.get("action") == "navigate"), "")
        inferred = self._url_to_page_name(base_url)
        feature_name = args.get("feature_name", inferred)
        steps_class = f"{feature_name}Steps"
        feature_file = f"{feature_name.lower()}.feature"

        elements = self._build_element_map(log)
        key_to_name = {(v["selector"], v["by"]): n for n, v in elements.items()}

        feature = self._gherkin_feature(feature_name, scenario, log, key_to_name)
        steps = self._gherkin_steps(steps_class, steps_package, log, elements, key_to_name)

        sep = "=" * 60
        return (
            f"{sep}\n"
            f"File: src/test/resources/features/{feature_file}\n"
            f"{sep}\n"
            f"{feature}\n\n"
            f"{sep}\n"
            f"File: {steps_package.replace('.', '/')}/{steps_class}.java\n"
            f"{sep}\n"
            f"{steps}"
        )

    def _name_to_readable(self, name: str) -> str:
        return re.sub(r'([A-Z])', r' \1', name).strip().lower()

    def _gherkin_step_text(self, entry: dict, key_to_name: dict, prefix: str) -> str:
        action = entry.get("action")
        sel = entry.get("selector", "")
        by = entry.get("by", "css")
        name = key_to_name.get((sel, by), self._selector_to_name(sel, by))
        readable = self._name_to_readable(name)

        if action == "navigate":
            return f'{prefix} I navigate to "{entry["url"]}"'
        elif action == "type_text":
            return f'{prefix} I enter "{entry["text"]}" in the {readable}'
        elif action == "click":
            return f'{prefix} I click the {readable}'
        elif action == "hover":
            return f'{prefix} I hover over the {readable}'
        elif action == "double_click":
            return f'{prefix} I double-click the {readable}'
        elif action == "right_click":
            return f'{prefix} I right-click the {readable}'
        elif action == "scroll_to_element":
            return f'{prefix} I scroll to the {readable}'
        elif action == "select_option":
            if "by_text" in entry:
                return f'{prefix} I select "{entry["by_text"]}" from the {readable}'
            elif "by_value" in entry:
                return f'{prefix} I select value "{entry["by_value"]}" from the {readable}'
            elif "by_index" in entry:
                return f'{prefix} I select option at index {entry["by_index"]} from the {readable}'
        elif action == "go_back":
            return f"{prefix} I navigate back"
        elif action == "go_forward":
            return f"{prefix} I navigate forward"
        elif action == "refresh":
            return f"{prefix} I refresh the page"
        return None

    def _gherkin_feature(self, feature_name: str, scenario: str,
                         log: list, key_to_name: dict) -> str:
        lines = [f"Feature: {feature_name}", "", f"  Scenario: {scenario}"]
        first = True
        for entry in log:
            if entry.get("action") == "start_browser":
                continue
            prefix = "Given" if first else "And"
            step = self._gherkin_step_text(entry, key_to_name, prefix)
            if step:
                lines.append(f"    {step}")
                first = False
        if not any(l.strip().startswith(("Given", "And", "When", "Then")) for l in lines):
            lines.append("    Given no actions were recorded")
        return "\n".join(lines)

    def _gherkin_steps(self, class_name: str, package: str, log: list,
                       elements: dict, key_to_name: dict) -> str:
        i = "    "
        seen = set()
        methods = []

        for entry in log:
            action = entry.get("action")
            if action == "start_browser":
                continue
            sel = entry.get("selector", "")
            by = entry.get("by", "css")
            name = key_to_name.get((sel, by), self._selector_to_name(sel, by))
            readable = self._name_to_readable(name)
            by_java = self._java_by(by, sel)

            if action == "navigate":
                if "navigate" not in seen:
                    seen.add("navigate")
                    methods.append(
                        f'{i}@Given("I navigate to {{string}}")\n'
                        f'{i}public void iNavigateTo(String url) {{\n'
                        f'{i}{i}driver.get(url);\n'
                        f'{i}}}'
                    )
            elif action == "type_text":
                key = f"enter_{name}"
                if key not in seen:
                    seen.add(key)
                    method = self._to_camel(f"i_enter_in_{name}")
                    methods.append(
                        f'{i}@And("I enter {{string}} in the {readable}")\n'
                        f'{i}public void {method}(String text) {{\n'
                        f'{i}{i}WebElement el = wait.until(ExpectedConditions.visibilityOfElementLocated({by_java}));\n'
                        f'{i}{i}el.clear();\n'
                        f'{i}{i}el.sendKeys(text);\n'
                        f'{i}}}'
                    )
            elif action == "click":
                key = f"click_{name}"
                if key not in seen:
                    seen.add(key)
                    method = self._to_camel(f"i_click_the_{name}")
                    methods.append(
                        f'{i}@And("I click the {readable}")\n'
                        f'{i}public void {method}() {{\n'
                        f'{i}{i}wait.until(ExpectedConditions.elementToBeClickable({by_java})).click();\n'
                        f'{i}}}'
                    )
            elif action == "hover":
                key = f"hover_{name}"
                if key not in seen:
                    seen.add(key)
                    method = self._to_camel(f"i_hover_over_the_{name}")
                    methods.append(
                        f'{i}@And("I hover over the {readable}")\n'
                        f'{i}public void {method}() {{\n'
                        f'{i}{i}new Actions(driver).moveToElement(wait.until(ExpectedConditions.visibilityOfElementLocated({by_java}))).perform();\n'
                        f'{i}}}'
                    )
            elif action == "double_click":
                key = f"dclick_{name}"
                if key not in seen:
                    seen.add(key)
                    method = self._to_camel(f"i_double_click_the_{name}")
                    methods.append(
                        f'{i}@And("I double-click the {readable}")\n'
                        f'{i}public void {method}() {{\n'
                        f'{i}{i}new Actions(driver).doubleClick(wait.until(ExpectedConditions.elementToBeClickable({by_java}))).perform();\n'
                        f'{i}}}'
                    )
            elif action == "select_option":
                key = f"select_{name}"
                if key not in seen:
                    seen.add(key)
                    method = self._to_camel(f"i_select_from_the_{name}")
                    methods.append(
                        f'{i}@And("I select {{string}} from the {readable}")\n'
                        f'{i}public void {method}(String value) {{\n'
                        f'{i}{i}new Select(wait.until(ExpectedConditions.visibilityOfElementLocated({by_java}))).selectByVisibleText(value);\n'
                        f'{i}}}'
                    )
            elif action == "go_back":
                if "go_back" not in seen:
                    seen.add("go_back")
                    methods.append(
                        f'{i}@And("I navigate back")\n'
                        f'{i}public void iNavigateBack() {{\n'
                        f'{i}{i}driver.navigate().back();\n'
                        f'{i}}}'
                    )
            elif action == "go_forward":
                if "go_forward" not in seen:
                    seen.add("go_forward")
                    methods.append(
                        f'{i}@And("I navigate forward")\n'
                        f'{i}public void iNavigateForward() {{\n'
                        f'{i}{i}driver.navigate().forward();\n'
                        f'{i}}}'
                    )
            elif action == "refresh":
                if "refresh" not in seen:
                    seen.add("refresh")
                    methods.append(
                        f'{i}@And("I refresh the page")\n'
                        f'{i}public void iRefreshThePage() {{\n'
                        f'{i}{i}driver.navigate().refresh();\n'
                        f'{i}}}'
                    )

        header = "\n".join([
            f"package {package};",
            "",
            "import io.cucumber.java.After;",
            "import io.cucumber.java.Before;",
            "import io.cucumber.java.en.*;",
            "import org.openqa.selenium.By;",
            "import org.openqa.selenium.WebDriver;",
            "import org.openqa.selenium.WebElement;",
            "import org.openqa.selenium.chrome.ChromeDriver;",
            "import org.openqa.selenium.chrome.ChromeOptions;",
            "import org.openqa.selenium.interactions.Actions;",
            "import org.openqa.selenium.support.ui.ExpectedConditions;",
            "import org.openqa.selenium.support.ui.Select;",
            "import org.openqa.selenium.support.ui.WebDriverWait;",
            "import java.time.Duration;",
            "",
            f"public class {class_name} {{",
            "",
            f"{i}private WebDriver driver;",
            f"{i}private WebDriverWait wait;",
            "",
            f"{i}@Before",
            f"{i}public void setUp() {{",
            f"{i}{i}ChromeOptions options = new ChromeOptions();",
            f"{i}{i}// options.addArguments(\"--headless=new\");",
            f"{i}{i}driver = new ChromeDriver(options);",
            f"{i}{i}driver.manage().window().maximize();",
            f"{i}{i}wait = new WebDriverWait(driver, Duration.ofSeconds(10));",
            f"{i}}}",
            "",
            f"{i}@After",
            f"{i}public void tearDown() {{",
            f"{i}{i}if (driver != null) driver.quit();",
            f"{i}}}",
            "",
        ])

        body = f"\n\n".join(methods) if methods else f"{i}// No steps recorded"
        return header + body + "\n\n}"
