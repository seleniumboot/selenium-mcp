"""
Codegen Tools — generate Python (pytest) and Java (TestNG/JUnit5) test scripts
from the recorded session log. This is the key differentiator for Java users.
"""

import re
from urllib.parse import urlparse
from mcp.types import Tool
from selenium_mcp.tools._detect import detect_selenium_boot, recommendation_banner


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
                    "framework='testng' (default) emits standalone Selenium with a "
                    "ChromeDriver setUp/tearDown; framework='selenium_boot' emits a "
                    "Selenium Boot test (extends BaseTest, framework-managed driver, "
                    "accessibility-first getByRole/getByLabel/getByTestId locators and "
                    "web-first assertThat assertions — no driver lifecycle boilerplate). "
                    "In a Selenium Boot project, use framework='selenium_boot'."
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
                        },
                        "framework": {
                            "type": "string",
                            "enum": ["testng", "selenium_boot"],
                            "default": "testng",
                            "description": "Output flavor. Use 'selenium_boot' inside a Selenium Boot project."
                        }
                    },
                },
            ),
            Tool(
                name="generate_java_junit5",
                description=(
                    "Generate a Java JUnit 5 test class from the current browser session. "
                    "framework='junit5' (default) emits standalone Selenium with a "
                    "ChromeDriver setUp/tearDown; framework='selenium_boot' emits a "
                    "Selenium Boot test (extends BaseJUnit5Test, framework-managed driver, "
                    "accessibility-first locators and web-first assertThat assertions). "
                    "In a Selenium Boot project, use framework='selenium_boot'."
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
                        },
                        "framework": {
                            "type": "string",
                            "enum": ["junit5", "selenium_boot"],
                            "default": "junit5",
                            "description": "Output flavor. Use 'selenium_boot' inside a Selenium Boot project."
                        }
                    },
                },
            ),
            Tool(
                name="detect_selenium_boot",
                description=(
                    "Detect whether the current working directory is inside a Selenium Boot "
                    "project (looks for selenium-boot.yml or the io.github.seleniumboot "
                    "dependency in pom.xml / build.gradle, walking up parent directories). "
                    "Call this BEFORE generating Java code: if it reports detected=true, "
                    "generate with framework=\"selenium_boot\" so the output uses the "
                    "framework's accessibility-first locators and managed driver."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_dir": {
                            "type": "string",
                            "description": "Optional path to start detection from. Defaults to the server's working directory."
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
                    "and wired to Java code. framework='raw' (default) emits standalone "
                    "Selenium with a ChromeDriver @Before/@After; framework='selenium_boot' "
                    "emits steps extending BaseCucumberSteps with framework-managed driver "
                    "and accessibility-first locators. Use 'selenium_boot' in a Selenium Boot project."
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
                        },
                        "framework": {
                            "type": "string",
                            "enum": ["raw", "selenium_boot"],
                            "default": "raw",
                            "description": "Step-definition flavor. Use 'selenium_boot' inside a Selenium Boot project."
                        }
                    },
                },
            ),
            Tool(
                name="generate_csharp_nunit",
                description="Generate a C# NUnit + Selenium test class from the current browser session.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "test_name":   {"type": "string", "default": "RecordedFlowTests"},
                        "namespace":   {"type": "string", "default": "SeleniumTests"},
                    },
                },
            ),
            Tool(
                name="generate_github_actions",
                description="Generate a GitHub Actions CI workflow YAML for running the recorded test session.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "enum": ["java_maven", "java_gradle", "python_pytest"],
                            "default": "java_maven",
                        },
                        "java_version": {"type": "string", "default": "17"},
                    },
                },
            ),
            Tool(
                name="generate_jenkins_pipeline",
                description="Generate a declarative Jenkinsfile for running the recorded test session (Maven, Gradle, or pytest).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "enum": ["java_maven", "java_gradle", "python_pytest"],
                            "default": "java_maven",
                        },
                        "java_version": {"type": "string", "default": "17"},
                    },
                },
            ),
            Tool(
                name="generate_gitlab_ci",
                description="Generate a .gitlab-ci.yml pipeline for running the recorded test session (Maven, Gradle, or pytest).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "enum": ["java_maven", "java_gradle", "python_pytest"],
                            "default": "java_maven",
                        },
                        "java_version": {"type": "string", "default": "17"},
                    },
                },
            ),
            Tool(
                name="generate_playwright_hints",
                description="Generate equivalent Playwright (TypeScript) code hints from the recorded browser session.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "test_name": {"type": "string", "default": "recordedFlow"},
                    },
                },
            ),
            Tool(
                name="generate_java_page_object",
                description=(
                    "Generate a Java Page Object class + matching test class from the recorded session. "
                    "USE THIS INSTEAD OF WRITING JAVA BY HAND — the output compiles as-is and contains only "
                    "the elements/actions actually performed, so it never invents fields or uses non-existent "
                    "framework APIs. Produces two files: a Page Object (locators + fluent action methods) and a "
                    "Test class that uses it. Supports raw Selenium (TestNG / JUnit 5) and the Selenium Boot "
                    "framework (selenium_boot): Page Object extends BasePage, Test extends BaseTest, no manual "
                    "driver lifecycle — the framework manages it — with accessibility-first locators. "
                    "For any Java test in a Selenium Boot repo, use framework=\"selenium_boot\"."
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
                            "description": ("Base package, e.g. com.demo. The Page Object is placed in "
                                            "<base>.pages and the Test in <base>.tests. A trailing .pages "
                                            "or .tests is stripped, so passing either the base or a pages "
                                            "package works."),
                            "default": "com.example"
                        },
                        "framework": {
                            "type": "string",
                            "enum": ["testng", "junit5", "selenium_boot"],
                            "description": (
                                "Output flavor: 'testng'/'junit5' emit standalone Selenium with a "
                                "ChromeDriver setUp/tearDown; 'selenium_boot' emits Selenium Boot "
                                "(BasePage/BaseTest, framework-managed driver, web-first assertions)."
                            ),
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
            "detect_selenium_boot":       self._detect_selenium_boot,
            "generate_gherkin":           self._generate_gherkin,
            "generate_csharp_nunit":      self._generate_csharp_nunit,
            "generate_github_actions":    self._generate_github_actions,
            "generate_jenkins_pipeline":  self._generate_jenkins_pipeline,
            "generate_gitlab_ci":         self._generate_gitlab_ci,
            "generate_playwright_hints":  self._generate_playwright_hints,
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

    async def _detect_selenium_boot(self, args: dict) -> str:
        result = detect_selenium_boot(args.get("project_dir"))
        if result["detected"]:
            ev = "\n".join(f"  - {e}" for e in result["evidence"])
            return (
                "✅ Selenium Boot project DETECTED"
                f" (root: {result['root']}).\n{ev}\n\n"
                "Generate Java with framework=\"selenium_boot\" so the code uses the "
                "framework's accessibility-first locators (getByRole / getByLabel / "
                "getByTestId), framework-managed driver (BaseTest / BasePage, no "
                "ChromeDriver setUp/tearDown) and web-first assertThat(...) assertions."
            )
        return (
            "No Selenium Boot markers found near the working directory. "
            "If this IS a Selenium Boot project, pass project_dir or generate with "
            "framework=\"selenium_boot\" explicitly; otherwise use the plain "
            "testng / junit5 flavors."
        )

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

            if (action or "").startswith("assert_"):
                continue  # assertions are emitted only in the Selenium Boot flavor
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
            elif action == "send_keys":
                key = entry.get("key", "")
                sel = entry.get("selector", "")
                if sel:
                    lines.append(f'{indent}self.wait.until(EC.presence_of_element_located(({by_const}, "{sel}"))).send_keys(Keys.{key.upper().replace("+", "_")})')
                else:
                    lines.append(f'{indent}ActionChains(self.driver).send_keys(Keys.{key.upper().replace("+", "_")}).perform()')
            elif action == "accept_alert":
                lines.append(f'{indent}self.wait.until(EC.alert_is_present())')
                lines.append(f'{indent}self.driver.switch_to.alert.accept()')
            elif action == "dismiss_alert":
                lines.append(f'{indent}self.wait.until(EC.alert_is_present())')
                lines.append(f'{indent}self.driver.switch_to.alert.dismiss()')
            elif action == "type_in_alert":
                text = entry.get("text", "")
                lines.append(f'{indent}self.wait.until(EC.alert_is_present())')
                lines.append(f'{indent}alert = self.driver.switch_to.alert')
                lines.append(f'{indent}alert.send_keys("{text}")')
                lines.append(f'{indent}alert.accept()')
            elif action == "switch_to_frame":
                if "index" in entry:
                    lines.append(f'{indent}self.driver.switch_to.frame({entry["index"]})')
                elif "name" in entry:
                    lines.append(f'{indent}self.driver.switch_to.frame("{entry["name"]}")')
                elif "selector" in entry:
                    lines.append(f'{indent}self.driver.switch_to.frame(self.driver.find_element({by_const}, "{entry["selector"]}"))')
            elif action == "switch_to_default_content":
                lines.append(f'{indent}self.driver.switch_to.default_content()')
            elif action == "upload_file":
                sel = entry.get("selector", "")
                path = entry.get("file_path", "")
                lines.append(f'{indent}self.driver.find_element({by_const}, "{sel}").send_keys("{path}")')
            elif action == "set_cookie":
                lines.append(f'{indent}self.driver.add_cookie({{"name": "{entry["name"]}", "value": "{entry["value"]}"}})')
            elif action == "set_local_storage":
                lines.append(f'{indent}self.driver.execute_script("window.localStorage.setItem(\'{entry["key"]}\', \'{entry["value"]}\');")')
            elif action == "set_session_storage":
                lines.append(f'{indent}self.driver.execute_script("window.sessionStorage.setItem(\'{entry["key"]}\', \'{entry["value"]}\');")')
            elif action == "open_new_tab":
                url = entry.get("url", "")
                lines.append(f'{indent}self.driver.execute_script("window.open(\'{url}\');")')
                lines.append(f'{indent}self.driver.switch_to.window(self.driver.window_handles[-1])')
            elif action == "close_current_tab":
                lines.append(f'{indent}self.driver.close()')
                lines.append(f'{indent}self.driver.switch_to.window(self.driver.window_handles[-1])')
            elif action == "scroll_to_top":
                lines.append(f'{indent}self.driver.execute_script("window.scrollTo(0, 0);")')
            elif action == "scroll_to_bottom":
                lines.append(f'{indent}self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")')
            elif action == "scroll_by":
                lines.append(f'{indent}self.driver.execute_script("window.scrollBy({entry.get("x", 0)}, {entry.get("y", 300)});")')
            elif action == "emulate_device":
                lines.append(f'{indent}# Device emulation: {entry.get("device", "")} — set via ChromeOptions or CDP before driver init')
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

        if args.get("framework") == "selenium_boot":
            return self._java_sb_inline_test(
                test_name, package, log, base_class="BaseTest",
                base_class_import="import com.seleniumboot.test.BaseTest;",
                test_annotation="@Test",
                test_annotation_import="import org.testng.annotations.Test;",
                static_ctx=False, assert_api="testng")

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
        return recommendation_banner(args.get("framework")) + code

    # ------------------------------------------------------------------ #
    #  Java JUnit 5 codegen                                                #
    # ------------------------------------------------------------------ #
    async def _generate_java_junit5(self, args: dict) -> str:
        log = self.browser._session_log
        test_name = args.get("test_name", "RecordedFlowTest")
        package = args.get("package_name", "com.tests.selenium")

        if args.get("framework") == "selenium_boot":
            # BaseJUnit5Test exposes $()/assertThat()/open() but NOT the getBy*
            # factories, so inline locators use the static Locator.by* forms.
            return self._java_sb_inline_test(
                test_name, package, log, base_class="BaseJUnit5Test",
                base_class_import="import com.seleniumboot.junit5.BaseJUnit5Test;",
                test_annotation="@Test",
                test_annotation_import="import org.junit.jupiter.api.Test;",
                static_ctx=True, assert_api="junit5")

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
        return recommendation_banner(args.get("framework")) + code

    def _log_to_java_steps(self, log: list) -> str:
        lines = []
        indent = "        "
        # Unique local-variable names so repeated type/select actions don't
        # redeclare `field` / `dropdown` (which fails to compile in Java).
        n_field = 0
        n_dropdown = 0
        for entry in log:
            action = entry.get("action")
            by = entry.get("by", "css")
            sel = entry.get("selector", "")
            by_java = self._java_by(by, sel)

            if (action or "").startswith("assert_"):
                continue  # assertions are emitted only in the Selenium Boot flavor
            if action == "start_browser":
                lines.append(f"{indent}// Browser started — handled in setUp()")
            elif action == "navigate":
                lines.append(f'{indent}driver.get("{entry["url"]}");')
            elif action == "click":
                lines.append(f'{indent}wait.until(ExpectedConditions.elementToBeClickable({by_java})).click();')
            elif action == "type_text":
                text = entry.get("text", "")
                n_field += 1
                field = "field" if n_field == 1 else f"field{n_field}"
                lines.append(f'{indent}WebElement {field} = wait.until(ExpectedConditions.visibilityOfElementLocated({by_java}));')
                lines.append(f'{indent}{field}.clear();')
                lines.append(f'{indent}{field}.sendKeys("{text}");')
            elif action == "hover":
                lines.append(f'{indent}new Actions(driver).moveToElement(wait.until(ExpectedConditions.visibilityOfElementLocated({by_java}))).perform();')
            elif action == "double_click":
                lines.append(f'{indent}new Actions(driver).doubleClick(wait.until(ExpectedConditions.elementToBeClickable({by_java}))).perform();')
            elif action == "right_click":
                lines.append(f'{indent}new Actions(driver).contextClick(wait.until(ExpectedConditions.visibilityOfElementLocated({by_java}))).perform();')
            elif action == "scroll_to_element":
                lines.append(f'{indent}((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView(true);", wait.until(ExpectedConditions.presenceOfElementLocated({by_java})));')
            elif action == "select_option":
                n_dropdown += 1
                dropdown = "dropdown" if n_dropdown == 1 else f"dropdown{n_dropdown}"
                lines.append(f'{indent}Select {dropdown} = new Select(wait.until(ExpectedConditions.visibilityOfElementLocated({by_java})));')
                if "by_text" in entry:
                    lines.append(f'{indent}{dropdown}.selectByVisibleText("{entry["by_text"]}");')
                elif "by_value" in entry:
                    lines.append(f'{indent}{dropdown}.selectByValue("{entry["by_value"]}");')
                elif "by_index" in entry:
                    lines.append(f'{indent}{dropdown}.selectByIndex({entry["by_index"]});')
            elif action == "go_back":
                lines.append(f"{indent}driver.navigate().back();")
            elif action == "go_forward":
                lines.append(f"{indent}driver.navigate().forward();")
            elif action == "refresh":
                lines.append(f"{indent}driver.navigate().refresh();")
            elif action == "execute_script":
                script = entry.get("script", "").replace('"', '\\"')
                lines.append(f'{indent}((JavascriptExecutor) driver).executeScript("{script}");')
            elif action == "send_keys":
                key = entry.get("key", "").upper().replace("+", "_")
                sel = entry.get("selector", "")
                if sel:
                    lines.append(f'{indent}wait.until(ExpectedConditions.presenceOfElementLocated({by_java})).sendKeys(Keys.{key});')
                else:
                    lines.append(f'{indent}new Actions(driver).sendKeys(Keys.{key}).perform();')
            elif action == "accept_alert":
                lines.append(f'{indent}wait.until(ExpectedConditions.alertIsPresent());')
                lines.append(f'{indent}driver.switchTo().alert().accept();')
            elif action == "dismiss_alert":
                lines.append(f'{indent}wait.until(ExpectedConditions.alertIsPresent());')
                lines.append(f'{indent}driver.switchTo().alert().dismiss();')
            elif action == "type_in_alert":
                text = entry.get("text", "")
                lines.append(f'{indent}wait.until(ExpectedConditions.alertIsPresent());')
                lines.append(f'{indent}driver.switchTo().alert().sendKeys("{text}");')
                lines.append(f'{indent}driver.switchTo().alert().accept();')
            elif action == "switch_to_frame":
                if "index" in entry:
                    lines.append(f'{indent}driver.switchTo().frame({entry["index"]});')
                elif "name" in entry:
                    lines.append(f'{indent}driver.switchTo().frame("{entry["name"]}");')
                elif "selector" in entry:
                    lines.append(f'{indent}driver.switchTo().frame(driver.findElement({by_java}));')
            elif action == "switch_to_default_content":
                lines.append(f'{indent}driver.switchTo().defaultContent();')
            elif action == "upload_file":
                path = entry.get("file_path", "").replace("\\", "\\\\")
                lines.append(f'{indent}driver.findElement({by_java}).sendKeys("{path}");')
            elif action == "set_cookie":
                lines.append(f'{indent}driver.manage().addCookie(new Cookie("{entry["name"]}", "{entry["value"]}"));')
            elif action == "set_local_storage":
                lines.append(f'{indent}((JavascriptExecutor) driver).executeScript("window.localStorage.setItem(\'{entry["key"]}\', \'{entry["value"]}\');");')
            elif action == "set_session_storage":
                lines.append(f'{indent}((JavascriptExecutor) driver).executeScript("window.sessionStorage.setItem(\'{entry["key"]}\', \'{entry["value"]}\');");')
            elif action == "open_new_tab":
                url = entry.get("url", "")
                lines.append(f'{indent}((JavascriptExecutor) driver).executeScript("window.open(\'{url}\');");')
                lines.append(f'{indent}driver.switchTo().window(driver.getWindowHandles().toArray(new String[0])[driver.getWindowHandles().size() - 1]);')
            elif action == "close_current_tab":
                lines.append(f'{indent}driver.close();')
                lines.append(f'{indent}driver.switchTo().window(driver.getWindowHandles().toArray(new String[0])[driver.getWindowHandles().size() - 1]);')
            elif action == "scroll_to_top":
                lines.append(f'{indent}((JavascriptExecutor) driver).executeScript("window.scrollTo(0, 0);");')
            elif action == "scroll_to_bottom":
                lines.append(f'{indent}((JavascriptExecutor) driver).executeScript("window.scrollTo(0, document.body.scrollHeight);");')
            elif action == "scroll_by":
                lines.append(f'{indent}((JavascriptExecutor) driver).executeScript("window.scrollBy({entry.get("x", 0)}, {entry.get("y", 300)});");')
            elif action == "emulate_device":
                lines.append(f'{indent}// Device emulation: {entry.get("device", "")} — configure via ChromeOptions before driver init')
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
        raw_pkg = args.get("package_name", "com.example")
        # Accept a base package (com.demo) OR a *.pages / *.tests package and derive
        # a clean base, so the Page lands in <base>.pages and the Test in <base>.tests
        # — never a doubled ".pages.pages", and the test never sits in the pages folder.
        base_package = re.sub(r"\.(pages|tests)$", "", raw_pkg)
        pages_package = f"{base_package}.pages"
        tests_package = f"{base_package}.tests"
        framework = args.get("framework", "testng")

        base_url = next((e["url"] for e in log if e.get("action") == "navigate"), "")
        inferred = self._url_to_page_name(base_url)
        page_name = args.get("page_name", f"{inferred}Page")
        test_name = page_name[:-4] + "Test" if page_name.endswith("Page") else f"{page_name}Test"

        elements = self._build_element_map(log)

        if framework == "selenium_boot":
            page_code = self._java_sb_page_class(page_name, pages_package, elements)
            test_code = self._java_sb_test(test_name, tests_package, pages_package, page_name, base_url, log, elements)
        else:
            page_code = self._java_page_class(page_name, pages_package, elements)
            test_code = self._java_pom_test(test_name, tests_package, pages_package, page_name, framework, base_url, log, elements)

        sep = "=" * 60
        return (
            recommendation_banner(framework) +
            f"{sep}\n"
            f"File: {pages_package.replace('.', '/')}/{page_name}.java\n"
            f"{sep}\n"
            f"{page_code}\n\n"
            f"{sep}\n"
            f"File: {tests_package.replace('.', '/')}/{test_name}.java\n"
            f"{sep}\n"
            f"{test_code}"
        )

    def _url_to_page_name(self, url: str) -> str:
        try:
            segment = urlparse(url).path.strip("/").split("/")[-1]
            return segment.capitalize() if segment else "Home"
        except Exception:
            return "Recorded"

    def _url_path(self, url: str) -> str:
        """Path (+query/fragment) of a URL for baseUrl-relative open() calls."""
        try:
            p = urlparse(url)
            path = p.path or "/"
            if p.query:
                path += f"?{p.query}"
            if p.fragment:
                path += f"#{p.fragment}"
            return path or "/"
        except Exception:
            return "/"

    def _same_origin(self, a: str, b: str) -> bool:
        try:
            pa, pb = urlparse(a), urlparse(b)
            return (pa.scheme, pa.netloc) == (pb.scheme, pb.netloc)
        except Exception:
            return False

    def _selector_to_name(self, selector: str, by: str) -> str:
        sel = selector.strip()
        if by in ("id", "name"):
            return self._to_camel(sel)
        if by == "css":
            if sel.startswith("#"):
                return self._to_camel(sel[1:])
            if sel.startswith("."):
                return self._to_camel(sel[1:].split(".")[0])
            am = re.search(
                r"\[\s*(?:data-testid|placeholder|alt|title|aria-label|name)\s*=\s*['\"]([^'\"]+)['\"]",
                sel)
            if am:
                return self._to_camel(re.sub(r"[^\w]+", "_", am.group(1).strip())) or "element"
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
            # Prefer a human-readable literal (text/aria-label/title/...) when present.
            lit = re.search(r"(?:text\(\)|normalize-space\(\)|\.)\s*=\s*['\"]([^'\"]+)['\"]", sel) \
                or re.search(r"@(?:aria-label|title|alt|placeholder|value|name|id)=['\"]([^'\"]+)['\"]", sel)
            if lit:
                return self._to_camel(re.sub(r"[^\w]+", "_", lit.group(1).strip())) or "element"
            parts = [p for p in re.split(r"[/\[\]@=]", sel)
                     if p and p[0].isalpha() and not p.endswith("()")]
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
                attrs = entry.get("attrs") or {}
                raw = self._element_name(sel, by, attrs)
                name = raw
                suffix = 2
                while name in elements:
                    name = f"{raw}{suffix}"
                    suffix += 1
                key_to_name[key] = name
                elements[name] = {"selector": sel, "by": by, "actions": set(), "meta": {}, "attrs": attrs}

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
    #  Selenium Boot flavor (BasePage / BaseTest)                          #
    # ------------------------------------------------------------------ #
    _ROLE_ENUM = {
        "button": "BUTTON", "link": "LINK", "checkbox": "CHECKBOX", "radio": "RADIO",
        "switch": "SWITCH", "textbox": "TEXTBOX", "searchbox": "SEARCHBOX",
        "combobox": "COMBOBOX", "option": "OPTION", "heading": "HEADING", "img": "IMG",
        "tab": "TAB", "menuitem": "MENUITEM", "slider": "SLIDER", "spinbutton": "SPINBUTTON",
    }

    def _element_name(self, selector: str, by: str, attrs: dict) -> str:
        """Field name — prefer a human-readable attribute (aria-label / testid /
        name / id) captured from the DOM; else fall back to the selector."""
        a = attrs or {}
        for key in ("ariaLabel", "label", "testid", "nameAttr", "idAttr"):
            val = (a.get(key) or "").strip()
            if val:
                cleaned = re.sub(r"[-_](input|select|field|btn|button|dropdown|checkbox|radio)$",
                                 "", val, flags=re.I)
                camel = self._to_camel(re.sub(r"[^\w]+", "_", cleaned))
                if camel and camel != "element":
                    return camel
        if a.get("tag") in ("button", "a") and (a.get("text") or "").strip():
            return self._to_camel(re.sub(r"[^\w]+", "_", a["text"].strip()[:30])) or "element"
        return self._selector_to_name(selector, by)

    def _role_enum_from(self, a: dict):
        role = (a.get("role") or "").strip().lower()
        if role in self._ROLE_ENUM:
            return self._ROLE_ENUM[role]
        tag = (a.get("tag") or "").lower()
        typ = (a.get("type") or "").lower()
        if tag == "button" or (tag == "input" and typ in ("submit", "button", "reset")):
            return "BUTTON"
        if tag == "a":
            return "LINK"
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            return "HEADING"
        return None

    # Factory names for the two calling contexts. Instance methods (getBy* / $)
    # exist on BaseTest and BasePage; Cucumber step classes only have the static
    # Locator.by* factories, so they must use static_ctx=True.
    def _fac(self, kind: str, static_ctx: bool) -> str:
        instance = {
            "role": "getByRole", "text": "getByText", "label": "getByLabel",
            "placeholder": "getByPlaceholder", "testid": "getByTestId",
            "alt": "getByAltText", "title": "getByTitle",
        }
        static = {
            "role": "Locator.byRole", "text": "Locator.byText", "label": "Locator.byLabel",
            "placeholder": "Locator.byPlaceholder", "testid": "Locator.byTestId",
            "alt": "Locator.byAltText", "title": "Locator.byTitle",
        }
        return (static if static_ctx else instance)[kind]

    def _role_expr(self, role: str, name: str, static_ctx: bool, level=None) -> str:
        q = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')
        if static_ctx:
            expr = f'Locator.byRole(Role.{role}).withName("{q(name)}")'
        else:
            expr = f'getByRole(Role.{role}, "{q(name)}")'
        if level:
            expr += f".withLevel({level})"
        return expr

    def _by_wrap(self, by_expr: str, static_ctx: bool) -> str:
        """$(By.x(...)) in instance context; Locator.of(By.x(...)) in static context."""
        return f"Locator.of({by_expr})" if static_ctx else f"$({by_expr})"

    def _css_wrap(self, css: str, static_ctx: bool) -> str:
        q = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')
        return f'Locator.ofCss("{q(css)}")' if static_ctx else f'$("{q(css)}")'

    def _sb_semantic_confidence(self, attrs: dict, by: str, selector: str) -> bool:
        """True when the element has a single clearly-best, stable locator — an
        accessibility-first one (role+name, label, placeholder, alt, title, text)
        or a unique hook (testid, id). Such elements get a clean single Locator.

        Deliberately excludes a bare ``name`` attribute: name alone is weaker, so
        name-plus-structural-selector elements drop to the SmartLocator fallback."""
        a = attrs or {}
        if any((a.get(k) or "").strip() for k in
               ("testid", "label", "placeholder", "alt", "title", "idAttr")):
            return True
        if self._role_enum_from(a) in ("BUTTON", "LINK", "HEADING") and \
                (a.get("ariaLabel") or a.get("text") or a.get("title") or "").strip():
            return True
        if by in ("id", "link"):
            return True
        sel = (selector or "").strip()
        if by == "css" and (re.fullmatch(r"#([\w-]+)", sel) or
                            re.search(r"\[\s*(?:data-testid|placeholder|alt|title)\s*=", sel)):
            return True
        if by == "xpath" and re.search(
                r"(?:text\(\)|normalize-space\(\)|@id|@aria-label|@title|@alt|@placeholder)", sel):
            return True
        return False

    def _sb_candidate_bys(self, attrs: dict, by: str, selector: str) -> list:
        """Ordered, de-duplicated list of raw By expressions for an element, used
        by the SmartLocator fallback when no confident semantic locator exists.
        Redundant candidates (e.g. a ``#id`` CSS selector when the id is already
        present) are collapsed so smartFind only lists genuinely distinct tries."""
        a = attrs or {}
        q = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')
        cands = []
        namev = (a.get("nameAttr") or "").strip()
        if namev:
            cands.append(f'By.name("{q(namev)}")')
        # Add the raw selector actually used, unless it just restates the name.
        redundant = (
            (by == "name" and selector == namev) or
            (by == "css" and namev and re.fullmatch(
                rf"\[\s*name\s*=\s*['\"]{re.escape(namev)}['\"]\s*\]", (selector or "").strip()))
        )
        if not redundant:
            used = self._java_by(by, selector)
            if used not in cands:
                cands.append(used)
        # de-dup, preserve order
        seen, out = set(), []
        for c in cands:
            if c not in seen:
                seen.add(c)
                out.append(c)
        return out

    def _sb_locator_from_attrs(self, attrs: dict, by: str, selector: str,
                               static_ctx: bool = False) -> str:
        """Accessibility-first Locator expression, prioritising the element's real
        DOM attributes (captured at interaction time) over the selector that was
        used to interact. Priority: data-testid > role+name (button/link/heading)
        > label (form controls) > placeholder > alt > title > id > name >
        selector-based inference."""
        a = attrs or {}
        q = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')

        testid = (a.get("testid") or "").strip()
        if testid:
            return f'{self._fac("testid", static_ctx)}("{q(testid)}")'

        role = self._role_enum_from(a)
        name = (a.get("ariaLabel") or a.get("text") or a.get("title") or "").strip()
        if role in ("BUTTON", "LINK", "HEADING") and name:
            tag = (a.get("tag") or "")
            level = tag[1] if (role == "HEADING" and re.fullmatch(r"h[1-6]", tag)) else None
            return self._role_expr(role, name, static_ctx, level)

        # Associated <label> — the most robust locator for form controls.
        label = (a.get("label") or "").strip()
        if label:
            return f'{self._fac("label", static_ctx)}("{q(label)}")'

        for key in ("placeholder", "alt", "title"):
            val = (a.get(key) or "").strip()
            if val:
                fac = {"placeholder": "placeholder", "alt": "alt", "title": "title"}[key]
                return f'{self._fac(fac, static_ctx)}("{q(val)}")'

        idv = (a.get("idAttr") or "").strip()
        if idv:
            return self._by_wrap(f'By.id("{q(idv)}")', static_ctx)
        namev = (a.get("nameAttr") or "").strip()
        if namev:
            return self._by_wrap(f'By.name("{q(namev)}")', static_ctx)

        # No usable attributes recorded (older sessions) — infer from the selector.
        return self._sb_locator_expr(by, selector, static_ctx)

    def _sb_locator_expr(self, by: str, selector: str, static_ctx: bool = False) -> str:
        """Map a recorded (by, selector) to a Selenium Boot Locator expression.

        Prefers accessibility-first locators (getByRole/getByText/getByTestId/
        getByPlaceholder/getByAltText/getByTitle) when the selector encodes that
        semantic; otherwise falls back to $() wrapping a plain By, keeping every
        element inside the framework's Locator strategy.
        """
        sel = (selector or "").strip()
        q = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')

        if by == "link":
            return self._role_expr("LINK", sel, static_ctx)

        if by == "xpath":
            tm = re.search(r"(?:text\(\)|normalize-space\(\)|\.)\s*=\s*['\"]([^'\"]+)['\"]", sel)
            tag_m = re.match(r"^/{0,2}(\w+)", sel)
            tag = tag_m.group(1).lower() if tag_m else ""
            if tm:
                txt = tm.group(1).strip()
                if tag == "button" or re.search(r"@type=['\"](?:submit|button)['\"]", sel):
                    return self._role_expr("BUTTON", txt, static_ctx)
                if tag == "a":
                    return self._role_expr("LINK", txt, static_ctx)
                if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                    return self._role_expr("HEADING", txt, static_ctx, tag[1])
                return f'{self._fac("text", static_ctx)}("{q(txt)}")'
            idm = re.search(r"@id=['\"]([^'\"]+)['\"]", sel)
            if idm:
                return self._by_wrap(f'By.id("{q(idm.group(1))}")', static_ctx)
            return self._by_wrap(f'By.xpath("{q(sel)}")', static_ctx)

        if by == "css":
            for attr, fac in (("data-testid", "testid"),
                              ("placeholder", "placeholder"),
                              ("alt", "alt"),
                              ("title", "title")):
                m = re.search(rf"\[\s*{attr}\s*=\s*['\"]([^'\"]+)['\"]\s*\]", sel)
                if m:
                    return f'{self._fac(fac, static_ctx)}("{q(m.group(1))}")'

            m = re.fullmatch(r"#([\w-]+)", sel)
            if m:
                return self._by_wrap(f'By.id("{q(m.group(1))}")', static_ctx)
            return self._css_wrap(sel, static_ctx)

        if by == "id":
            return self._by_wrap(f'By.id("{q(sel)}")', static_ctx)
        if by == "name":
            return self._by_wrap(f'By.name("{q(sel)}")', static_ctx)
        if by == "tag":
            return self._by_wrap(f'By.tagName("{q(sel)}")', static_ctx)
        if by == "class":
            return self._by_wrap(f'By.className("{q(sel)}")', static_ctx)
        return self._by_wrap(f'By.cssSelector("{q(sel)}")', static_ctx)

    def _java_sb_page_class(self, page_name: str, package: str, elements: dict) -> str:
        """Page Object extending com.seleniumboot.test.BasePage.

        Locators are accessibility-first (getByRole/getByLabel/getByText/
        getByTestId/...), stored as Locator fields, with fluent action methods.
        Actions the Locator API doesn't cover natively (double/right-click,
        select) bridge to BasePage helpers via Locator.toBy().

        When an element only has a brittle, structural selector (no accessible
        name, testid, label, id, …) and more than one candidate strategy is
        available, it falls back to a SmartLocator resolver that tries each
        strategy in order — resilient to CSS/DOM refactors.
        """
        i = "    "
        i2 = i + i

        # Decide per element: accessibility-first Locator field, or a low-confidence
        # SmartLocator resolver (multiple By strategies tried in order).
        for name, el in elements.items():
            confident = self._sb_semantic_confidence(el.get("attrs"), el["by"], el["selector"])
            cands = self._sb_candidate_bys(el.get("attrs"), el["by"], el["selector"])
            el["_smart"] = (not confident) and len(cands) >= 2
            el["_cands"] = cands

        field_lines = []
        for name, el in elements.items():
            if el["_smart"]:
                continue  # smart elements resolve via a private method, not a field
            field_lines.append(
                f"{i}private final Locator {name} = "
                f"{self._sb_locator_from_attrs(el.get('attrs'), el['by'], el['selector'])};"
            )

        body = [
            f"{i}public {page_name}(WebDriver driver) {{",
            f"{i}{i}super(driver);",
            f"{i}}}",
            "",
        ]

        # Private SmartLocator resolvers for low-confidence elements.
        for name, el in elements.items():
            if not el["_smart"]:
                continue
            args = ", ".join(el["_cands"])
            body += [
                f"{i}// Brittle selector — SmartLocator tries each strategy in order.",
                f"{i}private WebElement {name}() {{",
                f"{i2}return smartFind({args});",
                f"{i}}}",
                "",
            ]

        for name, el in elements.items():
            cap = name[0].upper() + name[1:]
            acts = el["actions"]
            smart = el["_smart"]
            # How to refer to the element in an action:
            #  - Locator field:   name.click(), name.type(...), name.toBy()
            #  - Smart resolver:  name() -> WebElement, wrapped in Actions/Select/JS
            if "type_text" in acts:
                if smart:
                    body += [f"{i}public {page_name} enter{cap}(String text) {{",
                             f"{i2}WebElement el = {name}();", f"{i2}el.clear();",
                             f"{i2}el.sendKeys(text);", f"{i2}return this;", f"{i}}}", ""]
                else:
                    body += [f"{i}public {page_name} enter{cap}(String text) {{",
                             f"{i2}{name}.type(text);", f"{i2}return this;", f"{i}}}", ""]
            if "click" in acts:
                target = f"{name}().click();" if smart else f"{name}.click();"
                body += [f"{i}public {page_name} click{cap}() {{",
                         f"{i2}{target}", f"{i2}return this;", f"{i}}}", ""]
            if "hover" in acts:
                if smart:
                    body += [f"{i}public {page_name} hover{cap}() {{",
                             f"{i2}new Actions(driver).moveToElement({name}()).perform();",
                             f"{i2}return this;", f"{i}}}", ""]
                else:
                    body += [f"{i}public {page_name} hover{cap}() {{",
                             f"{i2}{name}.hover();", f"{i2}return this;", f"{i}}}", ""]
            if "scroll_to_element" in acts:
                if smart:
                    body += [f"{i}public {page_name} scrollTo{cap}() {{",
                             f'{i2}((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({{block:\'center\'}});", {name}());',
                             f"{i2}return this;", f"{i}}}", ""]
                else:
                    body += [f"{i}public {page_name} scrollTo{cap}() {{",
                             f"{i2}{name}.scrollIntoView();", f"{i2}return this;", f"{i}}}", ""]
            if "double_click" in acts:
                if smart:
                    body += [f"{i}public {page_name} doubleClick{cap}() {{",
                             f"{i2}new Actions(driver).doubleClick({name}()).perform();",
                             f"{i2}return this;", f"{i}}}", ""]
                else:
                    body += [f"{i}public {page_name} doubleClick{cap}() {{",
                             f"{i2}doubleClick({name}.toBy());", f"{i2}return this;", f"{i}}}", ""]
            if "right_click" in acts:
                if smart:
                    body += [f"{i}public {page_name} rightClick{cap}() {{",
                             f"{i2}new Actions(driver).contextClick({name}()).perform();",
                             f"{i2}return this;", f"{i}}}", ""]
                else:
                    body += [f"{i}public {page_name} rightClick{cap}() {{",
                             f"{i2}rightClick({name}.toBy());", f"{i2}return this;", f"{i}}}", ""]
            if "select_option" in acts:
                if smart:
                    body += [f"{i}public {page_name} select{cap}ByText(String text) {{",
                             f"{i2}new Select({name}()).selectByVisibleText(text);", f"{i2}return this;", f"{i}}}", "",
                             f"{i}public {page_name} select{cap}ByValue(String value) {{",
                             f"{i2}new Select({name}()).selectByValue(value);", f"{i2}return this;", f"{i}}}", ""]
                else:
                    body += [f"{i}public {page_name} select{cap}ByText(String text) {{",
                             f"{i2}selectByText({name}.toBy(), text);", f"{i2}return this;", f"{i}}}", "",
                             f"{i}public {page_name} select{cap}ByValue(String value) {{",
                             f"{i2}selectByValue({name}.toBy(), value);", f"{i2}return this;", f"{i}}}", ""]

        rendered = "\n".join(field_lines + body)

        imports = [
            "import com.seleniumboot.test.BasePage;",
            "import com.seleniumboot.locator.Locator;",
        ]
        if "Role." in rendered:
            imports.append("import com.seleniumboot.locator.Role;")
        if "By." in rendered:
            imports.append("import org.openqa.selenium.By;")
        imports.append("import org.openqa.selenium.WebDriver;")
        if "WebElement " in rendered or "WebElement>" in rendered:
            imports.append("import org.openqa.selenium.WebElement;")
        if "new Actions(" in rendered:
            imports.append("import org.openqa.selenium.interactions.Actions;")
        if "JavascriptExecutor" in rendered:
            imports.append("import org.openqa.selenium.JavascriptExecutor;")
        if "new Select(" in rendered:
            imports.append("import org.openqa.selenium.support.ui.Select;")

        lines = [f"package {package};", ""]
        lines += imports
        lines += ["", f"public class {page_name} extends BasePage {{", ""]
        lines += field_lines
        lines.append("")
        lines += body
        lines.append("}")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  Web-first assertion emission (assertThat)                           #
    # ------------------------------------------------------------------ #
    def _sb_assertion_lines(self, entry: dict, static_ctx: bool = False,
                            assert_api: str = "testng") -> list:
        """Map a recorded assert_* action to Selenium Boot web-first assertions
        (assertThat(locator).isVisible()/.hasText()/...). Page/title/url checks
        fall back to the JUnit/TestNG assertion API on the framework-managed driver.
        Returns a list of Java statements (no indentation) or []."""
        action = entry.get("action", "")
        q = lambda s: (s or "").replace("\\", "\\\\").replace('"', '\\"')

        # assertEquals argument order differs between the two APIs.
        def eq(actual_expr, literal):
            if assert_api == "junit5":
                return f'org.junit.jupiter.api.Assertions.assertEquals("{literal}", {actual_expr});'
            return f'org.testng.Assert.assertEquals({actual_expr}, "{literal}");'

        def tru(cond, msg):
            if assert_api == "junit5":
                return f'org.junit.jupiter.api.Assertions.assertTrue({cond}, "{msg}");'
            return f'org.testng.Assert.assertTrue({cond}, "{msg}");'

        if action == "assert_title":
            exp = q(entry.get("expected", ""))
            if entry.get("exact"):
                return [eq("getDriver().getTitle()", exp)]
            return [tru(f'getDriver().getTitle().contains("{exp}")', f"page title should contain: {exp}")]
        if action == "assert_url":
            exp = q(entry.get("expected", ""))
            if entry.get("exact"):
                return [eq("getDriver().getCurrentUrl()", exp)]
            return [tru(f'getDriver().getCurrentUrl().contains("{exp}")', f"url should contain: {exp}")]
        if action == "assert_page_contains":
            txt = q(entry.get("text", ""))
            return [f'assertThat({self._fac("text", static_ctx)}("{txt}")).isVisible();']

        loc = self._sb_locator_from_attrs(entry.get("attrs"), entry.get("by", "css"),
                                          entry.get("selector", ""), static_ctx)
        if action == "assert_visible":
            return [f"assertThat({loc}).isVisible();"]
        if action == "assert_hidden":
            return [f"assertThat({loc}).isHidden();"]
        if action == "assert_text":
            exp = q(entry.get("expected", ""))
            method = "hasText" if entry.get("exact") else "containsText"
            return [f'assertThat({loc}).{method}("{exp}");']
        if action == "assert_attribute":
            attr = q(entry.get("attribute", ""))
            exp = q(entry.get("expected", ""))
            return [f'assertThat({loc}).hasAttribute("{attr}", "{exp}");']
        if action == "assert_count":
            try:
                n = int(entry.get("expected_count", 0))
            except (TypeError, ValueError):
                n = 0
            return [f"assertThat({loc}).count({n});"]
        return []

    def _sb_inline_statements(self, log: list, base_url: str,
                              static_ctx: bool, assert_api: str) -> list:
        """Build the statements for a single self-contained Selenium Boot @Test /
        step body — inline accessibility-first locators, no page object. Used by
        the TestNG / JUnit 5 / Cucumber selenium_boot flavors. Actions the Locator
        API lacks (double/right-click, select) bridge through Locator.element()."""
        q = lambda s: (s or "").replace("\\", "\\\\").replace('"', '\\"')
        out = []
        for entry in log:
            action = entry.get("action", "")
            by = entry.get("by", "css")
            sel = entry.get("selector", "")

            if action == "start_browser":
                continue
            if action == "navigate":
                url = entry.get("url", "")
                if base_url and (url == base_url or self._same_origin(url, base_url)):
                    out.append(f'open("{self._url_path(url)}");')
                elif url:
                    out.append(f'getDriver().get("{q(url)}");')
                continue
            if action.startswith("assert_"):
                out += self._sb_assertion_lines(entry, static_ctx=static_ctx, assert_api=assert_api)
                continue
            if action == "go_back":
                out.append("getDriver().navigate().back();"); continue
            if action == "go_forward":
                out.append("getDriver().navigate().forward();"); continue
            if action == "refresh":
                out.append("getDriver().navigate().refresh();"); continue

            loc = self._sb_locator_from_attrs(entry.get("attrs"), by, sel, static_ctx)
            if action == "type_text":
                out.append(f'{loc}.type("{q(entry.get("text", ""))}");')
            elif action == "click":
                out.append(f"{loc}.click();")
            elif action == "hover":
                out.append(f"{loc}.hover();")
            elif action == "scroll_to_element":
                out.append(f"{loc}.scrollIntoView();")
            elif action == "double_click":
                out.append(f"new Actions(getDriver()).doubleClick({loc}.element()).perform();")
            elif action == "right_click":
                out.append(f"new Actions(getDriver()).contextClick({loc}.element()).perform();")
            elif action == "select_option":
                if "by_text" in entry:
                    out.append(f'new Select({loc}.element()).selectByVisibleText("{q(entry["by_text"])}");')
                elif "by_value" in entry:
                    out.append(f'new Select({loc}.element()).selectByValue("{q(entry["by_value"])}");')
                elif "by_index" in entry:
                    out.append(f'new Select({loc}.element()).selectByIndex({entry["by_index"]});')
        return out

    def _sb_inline_imports(self, rendered: str, base_class_import: str,
                           test_annotation_import: str, static_ctx: bool) -> list:
        """Assemble the import block for an inline Selenium Boot test/steps class
        by scanning the rendered body for the tokens that need each import."""
        imports = [base_class_import]
        if static_ctx and ("Locator." in rendered):
            imports.append("import com.seleniumboot.locator.Locator;")
        if "Role." in rendered:
            imports.append("import com.seleniumboot.locator.Role;")
        if "By." in rendered:
            imports.append("import org.openqa.selenium.By;")
        if "new Actions(" in rendered:
            imports.append("import org.openqa.selenium.interactions.Actions;")
        if "new Select(" in rendered:
            imports.append("import org.openqa.selenium.support.ui.Select;")
        if test_annotation_import:
            imports.append(test_annotation_import)
        return imports

    def _java_sb_inline_test(self, test_name: str, package: str, log: list,
                             base_class: str, base_class_import: str,
                             test_annotation: str, test_annotation_import: str,
                             static_ctx: bool, assert_api: str) -> str:
        """A single self-contained Selenium Boot test class (no page object) —
        extends BaseTest / BaseJUnit5Test, inline accessibility-first locators and
        web-first assertions, framework-managed driver (no setUp/tearDown)."""
        i = "    "
        base_url = next((e.get("url") for e in log if e.get("action") == "navigate"), "")
        stmts = self._sb_inline_statements(log, base_url, static_ctx, assert_api)
        if not stmts:
            stmts = ["// No actions recorded"]
        body = "\n".join(f"{i}{i}{s}" for s in stmts)

        imports = self._sb_inline_imports(body, base_class_import,
                                          test_annotation_import, static_ctx)
        lines = [f"package {package};", ""]
        lines += imports
        lines += [
            "",
            f"public class {test_name} extends {base_class} {{",
            "",
            f"{i}{test_annotation}",
            f"{i}public void recordedFlowTest() {{",
            body,
            f"{i}}}",
            "}",
        ]
        return "\n".join(lines)

    def _java_sb_test(self, test_name, package, pages_package, page_name,
                      base_url, log, elements) -> str:
        """Test extending com.seleniumboot.test.BaseTest.

        No setUp/tearDown or ChromeDriver — the framework owns the driver
        lifecycle. Navigation uses open("/path"), which resolves against
        execution.baseUrl in selenium-boot.yml; a cross-origin hop falls back to
        getDriver().get(absoluteUrl).
        """
        i = "    "
        key_to_name = {(v["selector"], v["by"]): n for n, v in elements.items()}

        body_lines = []
        if base_url:
            body_lines.append(f"{i}{i}// baseUrl (execution.baseUrl in selenium-boot.yml) should be the site origin")
            body_lines.append(f'{i}{i}open("{self._url_path(base_url)}");')
        body_lines.append(f"{i}{i}{page_name} page = new {page_name}(getDriver());")

        for entry in log:
            action = entry.get("action", "")
            sel = entry.get("selector", "")
            by = entry.get("by", "css")
            name = key_to_name.get((sel, by))

            if action.startswith("assert_"):
                # Web-first assertions run inline in the test (BaseTest exposes
                # assertThat / getBy* / $); page objects hold actions, not assertions.
                for stmt in self._sb_assertion_lines(entry, static_ctx=False):
                    body_lines.append(f"{i}{i}{stmt}")
            elif action == "navigate" and entry.get("url") != base_url:
                url = entry["url"]
                if self._same_origin(url, base_url):
                    body_lines.append(f'{i}{i}open("{self._url_path(url)}");')
                else:
                    body_lines.append(f'{i}{i}getDriver().get("{url}");')
            elif action == "go_back":
                body_lines.append(f"{i}{i}getDriver().navigate().back();")
            elif action == "go_forward":
                body_lines.append(f"{i}{i}getDriver().navigate().forward();")
            elif action == "refresh":
                body_lines.append(f"{i}{i}getDriver().navigate().refresh();")
            elif name:
                cap = name[0].upper() + name[1:]
                if action == "type_text":
                    body_lines.append(f'{i}{i}page.enter{cap}("{entry.get("text", "")}");')
                elif action == "click":
                    body_lines.append(f"{i}{i}page.click{cap}();")
                elif action == "hover":
                    body_lines.append(f"{i}{i}page.hover{cap}();")
                elif action == "double_click":
                    body_lines.append(f"{i}{i}page.doubleClick{cap}();")
                elif action == "scroll_to_element":
                    body_lines.append(f"{i}{i}page.scrollTo{cap}();")
                elif action == "select_option":
                    meta = elements[name]["meta"]
                    if meta.get("select_key") == "by_text":
                        body_lines.append(f'{i}{i}page.select{cap}ByText("{meta["select_val"]}");')
                    else:
                        body_lines.append(f'{i}{i}page.select{cap}ByValue("{meta.get("select_val", "")}");')

        rendered = "\n".join(body_lines)
        imports = [
            f"import {pages_package}.{page_name};",
            "import com.seleniumboot.test.BaseTest;",
        ]
        if "Role." in rendered:
            imports.append("import com.seleniumboot.locator.Role;")
        if "By." in rendered:
            imports.append("import org.openqa.selenium.By;")
        imports.append("import org.testng.annotations.Test;")

        lines = [f"package {package};", ""]
        lines += imports
        lines += [
            "",
            f"public class {test_name} extends BaseTest {{",
            "",
            f"{i}@Test",
            f"{i}public void recordedFlowTest() {{",
        ]
        lines += body_lines
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
        if args.get("framework") == "selenium_boot":
            steps = self._gherkin_steps_sb(steps_class, steps_package, log, elements, key_to_name)
        else:
            steps = self._gherkin_steps(steps_class, steps_package, log, elements, key_to_name)

        sep = "=" * 60
        return (
            recommendation_banner(args.get("framework")) +
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

    def _gherkin_steps_sb(self, class_name: str, package: str, log: list,
                          elements: dict, key_to_name: dict) -> str:
        """Selenium Boot Cucumber step definitions — extends BaseCucumberSteps
        (framework-managed driver, no @Before/@After), accessibility-first
        locators via the static Locator.by* factories and web-first assertThat.
        Step phrasings match those emitted into the .feature file exactly."""
        i = "    "
        seen = set()
        methods = []

        def loc_for(name, entry):
            el = elements.get(name)
            if el:
                return self._sb_locator_from_attrs(el.get("attrs"), el["by"], el["selector"], static_ctx=True)
            return self._sb_locator_expr(entry.get("by", "css"), entry.get("selector", ""), static_ctx=True)

        for entry in log:
            action = entry.get("action")
            if action == "start_browser":
                continue
            sel = entry.get("selector", "")
            by = entry.get("by", "css")
            name = key_to_name.get((sel, by), self._selector_to_name(sel, by))
            readable = self._name_to_readable(name)

            if action == "navigate":
                if "navigate" not in seen:
                    seen.add("navigate")
                    methods.append(
                        f'{i}@Given("I navigate to {{string}}")\n'
                        f'{i}public void iNavigateTo(String url) {{\n'
                        f'{i}{i}getDriver().get(url);\n'
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
                        f'{i}{i}{loc_for(name, entry)}.type(text);\n'
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
                        f'{i}{i}{loc_for(name, entry)}.click();\n'
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
                        f'{i}{i}{loc_for(name, entry)}.hover();\n'
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
                        f'{i}{i}new Actions(getDriver()).doubleClick({loc_for(name, entry)}.element()).perform();\n'
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
                        f'{i}{i}new Select({loc_for(name, entry)}.element()).selectByVisibleText(value);\n'
                        f'{i}}}'
                    )
            elif action == "go_back":
                if "go_back" not in seen:
                    seen.add("go_back")
                    methods.append(
                        f'{i}@And("I navigate back")\n'
                        f'{i}public void iNavigateBack() {{\n'
                        f'{i}{i}getDriver().navigate().back();\n'
                        f'{i}}}'
                    )
            elif action == "go_forward":
                if "go_forward" not in seen:
                    seen.add("go_forward")
                    methods.append(
                        f'{i}@And("I navigate forward")\n'
                        f'{i}public void iNavigateForward() {{\n'
                        f'{i}{i}getDriver().navigate().forward();\n'
                        f'{i}}}'
                    )
            elif action == "refresh":
                if "refresh" not in seen:
                    seen.add("refresh")
                    methods.append(
                        f'{i}@And("I refresh the page")\n'
                        f'{i}public void iRefreshThePage() {{\n'
                        f'{i}{i}getDriver().navigate().refresh();\n'
                        f'{i}}}'
                    )

        body = f"\n\n".join(methods) if methods else f"{i}// No steps recorded"
        rendered = body

        imports = [
            "import com.seleniumboot.cucumber.BaseCucumberSteps;",
            "import com.seleniumboot.locator.Locator;",
        ]
        if "Role." in rendered:
            imports.append("import com.seleniumboot.locator.Role;")
        if "By." in rendered:
            imports.append("import org.openqa.selenium.By;")
        if "new Actions(" in rendered:
            imports.append("import org.openqa.selenium.interactions.Actions;")
        if "new Select(" in rendered:
            imports.append("import org.openqa.selenium.support.ui.Select;")
        imports.append("import io.cucumber.java.en.*;")

        header = "\n".join([f"package {package};", ""] + imports + [
            "",
            f"public class {class_name} extends BaseCucumberSteps {{",
            "",
        ])
        return header + body + "\n\n}"

    # ------------------------------------------------------------------ #
    #  C# NUnit codegen                                                    #
    # ------------------------------------------------------------------ #

    async def _generate_csharp_nunit(self, args: dict) -> str:
        log = self.browser._session_log
        test_name = args.get("test_name", "RecordedFlowTests")
        namespace = args.get("namespace", "SeleniumTests")
        steps = self._log_to_csharp_steps(log)

        return f'''using NUnit.Framework;
using OpenQA.Selenium;
using OpenQA.Selenium.Chrome;
using OpenQA.Selenium.Interactions;
using OpenQA.Selenium.Support.UI;
using SeleniumExtras.WaitHelpers;
using System;

namespace {namespace}
{{
    [TestFixture]
    public class {test_name}
    {{
        private IWebDriver driver;
        private WebDriverWait wait;

        [SetUp]
        public void SetUp()
        {{
            var options = new ChromeOptions();
            // options.AddArgument("--headless=new");
            driver = new ChromeDriver(options);
            driver.Manage().Window.Maximize();
            wait = new WebDriverWait(driver, TimeSpan.FromSeconds(10));
        }}

        [TearDown]
        public void TearDown()
        {{
            driver?.Quit();
        }}

        [Test]
        public void RecordedFlowTest()
        {{
{steps}
        }}
    }}
}}
'''

    def _log_to_csharp_steps(self, log: list) -> str:
        lines = []
        indent = "            "
        # Unique local names so repeated type/select actions don't redeclare
        # `field` / `dropdown` (a compile error in C#).
        n_field = 0
        n_dropdown = 0
        for entry in log:
            action = entry.get("action")
            by = entry.get("by", "css")
            sel = entry.get("selector", "")
            by_cs = self._csharp_by(by, sel)

            if (action or "").startswith("assert_"):
                continue  # assertions are emitted only in the Selenium Boot flavor
            if action == "start_browser":
                lines.append(f"{indent}// Browser started — handled in SetUp()")
            elif action == "navigate":
                lines.append(f'{indent}driver.Navigate().GoToUrl("{entry["url"]}");')
            elif action == "click":
                lines.append(f'{indent}wait.Until(ExpectedConditions.ElementToBeClickable({by_cs})).Click();')
            elif action == "type_text":
                text = entry.get("text", "")
                n_field += 1
                field = "field" if n_field == 1 else f"field{n_field}"
                lines.append(f'{indent}var {field} = wait.Until(ExpectedConditions.ElementIsVisible({by_cs}));')
                lines.append(f'{indent}{field}.Clear();')
                lines.append(f'{indent}{field}.SendKeys("{text}");')
            elif action == "hover":
                lines.append(f'{indent}new Actions(driver).MoveToElement(wait.Until(ExpectedConditions.ElementIsVisible({by_cs}))).Perform();')
            elif action == "double_click":
                lines.append(f'{indent}new Actions(driver).DoubleClick(wait.Until(ExpectedConditions.ElementToBeClickable({by_cs}))).Perform();')
            elif action == "right_click":
                lines.append(f'{indent}new Actions(driver).ContextClick(wait.Until(ExpectedConditions.ElementIsVisible({by_cs}))).Perform();')
            elif action == "select_option":
                n_dropdown += 1
                dropdown = "dropdown" if n_dropdown == 1 else f"dropdown{n_dropdown}"
                lines.append(f'{indent}var {dropdown} = new SelectElement(wait.Until(ExpectedConditions.ElementIsVisible({by_cs})));')
                if "by_text" in entry:
                    lines.append(f'{indent}{dropdown}.SelectByText("{entry["by_text"]}");')
                elif "by_value" in entry:
                    lines.append(f'{indent}{dropdown}.SelectByValue("{entry["by_value"]}");')
                elif "by_index" in entry:
                    lines.append(f'{indent}{dropdown}.SelectByIndex({entry["by_index"]});')
            elif action == "scroll_to_element":
                lines.append(f'{indent}((IJavaScriptExecutor)driver).ExecuteScript("arguments[0].scrollIntoView(true);", wait.Until(ExpectedConditions.ElementExists({by_cs})));')
            elif action == "send_keys":
                key = entry.get("key", "").replace("+", ".")
                lines.append(f'{indent}new Actions(driver).SendKeys(Keys.{key.title()}).Perform();')
            elif action == "accept_alert":
                lines.append(f'{indent}wait.Until(ExpectedConditions.AlertIsPresent()).Accept();')
            elif action == "dismiss_alert":
                lines.append(f'{indent}wait.Until(ExpectedConditions.AlertIsPresent()).Dismiss();')
            elif action == "type_in_alert":
                lines.append(f'{indent}var alert = wait.Until(ExpectedConditions.AlertIsPresent());')
                lines.append(f'{indent}alert.SendKeys("{entry.get("text", "")}");')
                lines.append(f'{indent}alert.Accept();')
            elif action == "switch_to_frame":
                if "index" in entry:
                    lines.append(f'{indent}driver.SwitchTo().Frame({entry["index"]});')
                elif "name" in entry:
                    lines.append(f'{indent}driver.SwitchTo().Frame("{entry["name"]}");')
            elif action == "switch_to_default_content":
                lines.append(f'{indent}driver.SwitchTo().DefaultContent();')
            elif action == "upload_file":
                path = entry.get("file_path", "").replace("\\", "\\\\")
                lines.append(f'{indent}driver.FindElement({by_cs}).SendKeys("{path}");')
            elif action == "set_cookie":
                lines.append(f'{indent}driver.Manage().Cookies.AddCookie(new Cookie("{entry["name"]}", "{entry["value"]}"));')
            elif action == "go_back":
                lines.append(f'{indent}driver.Navigate().Back();')
            elif action == "go_forward":
                lines.append(f'{indent}driver.Navigate().Forward();')
            elif action == "refresh":
                lines.append(f'{indent}driver.Navigate().Refresh();')
            elif action == "scroll_to_top":
                lines.append(f'{indent}((IJavaScriptExecutor)driver).ExecuteScript("window.scrollTo(0, 0);");')
            elif action == "scroll_to_bottom":
                lines.append(f'{indent}((IJavaScriptExecutor)driver).ExecuteScript("window.scrollTo(0, document.body.scrollHeight);");')
            elif action == "open_new_tab":
                url = entry.get("url", "")
                lines.append(f'{indent}((IJavaScriptExecutor)driver).ExecuteScript("window.open(\'{url}\');");')
                lines.append(f'{indent}driver.SwitchTo().Window(driver.WindowHandles[^1]);')
            else:
                lines.append(f"{indent}// TODO: {entry}")
        if not lines:
            lines.append(f"{indent}// No actions recorded")
        return "\n".join(lines)

    def _csharp_by(self, by: str, selector: str) -> str:
        sel = selector.replace('"', '\\"')
        return {
            "css":          f'By.CssSelector("{sel}")',
            "xpath":        f'By.XPath("{sel}")',
            "id":           f'By.Id("{sel}")',
            "name":         f'By.Name("{sel}")',
            "tag":          f'By.TagName("{sel}")',
            "class":        f'By.ClassName("{sel}")',
            "link":         f'By.LinkText("{sel}")',
            "partial_link": f'By.PartialLinkText("{sel}")',
        }.get(by, f'By.CssSelector("{sel}")')

    # ------------------------------------------------------------------ #
    #  GitHub Actions YAML codegen                                         #
    # ------------------------------------------------------------------ #

    async def _generate_github_actions(self, args: dict) -> str:
        language = args.get("language", "java_maven")
        java_ver = args.get("java_version", "17")

        if language == "java_maven":
            run_step = "- name: Run Selenium tests\n          run: mvn test -B"
            setup = f"""      - name: Set up JDK {java_ver}
        uses: actions/setup-java@v4
        with:
          java-version: '{java_ver}'
          distribution: 'temurin'
          cache: maven"""
        elif language == "java_gradle":
            run_step = "- name: Run Selenium tests\n          run: ./gradlew test"
            setup = f"""      - name: Set up JDK {java_ver}
        uses: actions/setup-java@v4
        with:
          java-version: '{java_ver}'
          distribution: 'temurin'
          cache: gradle"""
        else:  # python_pytest
            run_step = "- name: Run Selenium tests\n          run: pytest --tb=short -v"
            setup = """      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt"""

        return f'''name: Selenium Tests

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

{setup}

      - name: Set up Chrome
        uses: browser-actions/setup-chrome@v1

      - {run_step}
'''

    # ------------------------------------------------------------------ #
    #  Jenkins pipeline codegen                                            #
    # ------------------------------------------------------------------ #

    async def _generate_jenkins_pipeline(self, args: dict) -> str:
        language = args.get("language", "java_maven")
        java_ver = args.get("java_version", "17")

        chrome_install = (
            "sh 'apt-get update && apt-get install -y wget gnupg && "
            "wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && "
            "echo \"deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main\" "
            "| tee /etc/apt/sources.list.d/google-chrome.list && "
            "apt-get update && apt-get install -y google-chrome-stable'"
        )

        if language == "java_maven":
            tools_block = f"""    tools {{
        jdk 'jdk{java_ver}'
        maven '3.9'
    }}"""
            test_stage = "sh 'mvn test -B'"
            reports = "junit '**/target/surefire-reports/*.xml'"
        elif language == "java_gradle":
            tools_block = f"""    tools {{
        jdk 'jdk{java_ver}'
    }}"""
            test_stage = "sh './gradlew test'"
            reports = "junit '**/build/test-results/test/*.xml'"
        else:  # python_pytest
            tools_block = ""
            test_stage = (
                "sh 'python3 -m venv .venv && . .venv/bin/activate && "
                "pip install -r requirements.txt && "
                "pytest --tb=short -v --junitxml=report.xml'"
            )
            reports = "junit 'report.xml'"

        tools_section = f"\n{tools_block}\n" if tools_block else ""

        return f'''pipeline {{
    agent any
{tools_section}
    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
            }}
        }}

        stage('Install Chrome') {{
            steps {{
                {chrome_install}
            }}
        }}

        stage('Run Selenium Tests') {{
            steps {{
                {test_stage}
            }}
        }}
    }}

    post {{
        always {{
            {reports}
        }}
    }}
}}
'''

    # ------------------------------------------------------------------ #
    #  GitLab CI codegen                                                   #
    # ------------------------------------------------------------------ #

    async def _generate_gitlab_ci(self, args: dict) -> str:
        language = args.get("language", "java_maven")
        java_ver = args.get("java_version", "17")

        chrome_setup = """    - apt-get update && apt-get install -y wget gnupg
    - wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
    - echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list
    - apt-get update && apt-get install -y google-chrome-stable"""

        if language == "java_maven":
            image = f"maven:3.9-eclipse-temurin-{java_ver}"
            script = "    - mvn test -B"
            artifacts = """  artifacts:
    when: always
    reports:
      junit: target/surefire-reports/*.xml"""
        elif language == "java_gradle":
            image = f"gradle:8-jdk{java_ver}"
            script = "    - ./gradlew test"
            artifacts = """  artifacts:
    when: always
    reports:
      junit: build/test-results/test/*.xml"""
        else:  # python_pytest
            image = "python:3.12"
            chrome_setup += "\n    - pip install -r requirements.txt"
            script = "    - pytest --tb=short -v --junitxml=report.xml"
            artifacts = """  artifacts:
    when: always
    reports:
      junit: report.xml"""

        return f'''stages:
  - test

selenium-tests:
  stage: test
  image: {image}
  before_script:
{chrome_setup}
  script:
{script}
{artifacts}
'''

    # ------------------------------------------------------------------ #
    #  Playwright hints codegen                                            #
    # ------------------------------------------------------------------ #

    async def _generate_playwright_hints(self, args: dict) -> str:
        log = self.browser._session_log
        test_name = args.get("test_name", "recordedFlow")
        steps = self._log_to_playwright_steps(log)

        return f'''import {{ test, expect }} from "@playwright/test";

test("{test_name}", async ({{ page }}) => {{
{steps}
}});
'''

    def _log_to_playwright_steps(self, log: list) -> str:
        lines = []
        indent = "  "
        for entry in log:
            action = entry.get("action")
            sel = entry.get("selector", "")
            loc = f'page.locator("{sel}")' if sel else ""

            if (action or "").startswith("assert_"):
                continue  # assertions are emitted only in the Selenium Boot flavor
            if action == "start_browser":
                lines.append(f"{indent}// Browser handled by Playwright test runner")
            elif action == "navigate":
                lines.append(f'{indent}await page.goto("{entry["url"]}");')
            elif action == "click":
                lines.append(f'{indent}await page.locator("{sel}").click();')
            elif action == "type_text":
                lines.append(f'{indent}await page.locator("{sel}").fill("{entry.get("text", "")}");')
            elif action == "get_text":
                lines.append(f'{indent}const text = await page.locator("{sel}").textContent();')
            elif action == "hover":
                lines.append(f'{indent}await page.locator("{sel}").hover();')
            elif action == "double_click":
                lines.append(f'{indent}await page.locator("{sel}").dblclick();')
            elif action == "right_click":
                lines.append(f'{indent}await page.locator("{sel}").click({{ button: "right" }});')
            elif action == "scroll_to_element":
                lines.append(f'{indent}await page.locator("{sel}").scrollIntoViewIfNeeded();')
            elif action == "select_option":
                if "by_text" in entry:
                    lines.append(f'{indent}await page.locator("{sel}").selectOption({{ label: "{entry["by_text"]}" }});')
                elif "by_value" in entry:
                    lines.append(f'{indent}await page.locator("{sel}").selectOption("{entry["by_value"]}");')
                elif "by_index" in entry:
                    lines.append(f'{indent}await page.locator("{sel}").selectOption({{ index: {entry["by_index"]} }});')
            elif action == "send_keys":
                key = entry.get("key", "").replace("ctrl+", "Control+").replace("shift+", "Shift+")
                lines.append(f'{indent}await page.keyboard.press("{key}");')
            elif action == "upload_file":
                lines.append(f'{indent}await page.locator("{sel}").setInputFiles("{entry.get("file_path", "")}");')
            elif action == "accept_alert":
                lines.append(f'{indent}page.on("dialog", dialog => dialog.accept());')
            elif action == "dismiss_alert":
                lines.append(f'{indent}page.on("dialog", dialog => dialog.dismiss());')
            elif action == "type_in_alert":
                lines.append(f'{indent}page.on("dialog", async dialog => {{ await dialog.accept("{entry.get("text", "")}"); }});')
            elif action == "switch_to_frame":
                sel_f = entry.get("selector", entry.get("name", str(entry.get("index", ""))))
                lines.append(f'{indent}const frame = page.frameLocator("{sel_f}");')
            elif action == "switch_to_default_content":
                lines.append(f'{indent}// Playwright does not need explicit default content switch')
            elif action == "go_back":
                lines.append(f'{indent}await page.goBack();')
            elif action == "go_forward":
                lines.append(f'{indent}await page.goForward();')
            elif action == "refresh":
                lines.append(f'{indent}await page.reload();')
            elif action == "open_new_tab":
                url = entry.get("url", "")
                lines.append(f'{indent}const newPage = await context.newPage();')
                if url:
                    lines.append(f'{indent}await newPage.goto("{url}");')
            elif action == "scroll_to_top":
                lines.append(f'{indent}await page.evaluate(() => window.scrollTo(0, 0));')
            elif action == "scroll_to_bottom":
                lines.append(f'{indent}await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));')
            elif action == "scroll_by":
                lines.append(f'{indent}await page.evaluate(() => window.scrollBy({entry.get("x", 0)}, {entry.get("y", 300)}));')
            elif action == "set_cookie":
                lines.append(f'{indent}await context.addCookies([{{ name: "{entry["name"]}", value: "{entry["value"]}", url: page.url() }}]);')
            elif action == "set_local_storage":
                lines.append(f'{indent}await page.evaluate(() => localStorage.setItem("{entry["key"]}", "{entry["value"]}"));')
            elif action == "execute_script":
                script = entry.get("script", "").replace('"', '\\"')
                lines.append(f'{indent}await page.evaluate(() => {{{entry.get("script", "")}}});')
            else:
                lines.append(f"{indent}// TODO: {entry}")
        if not lines:
            lines.append(f"{indent}// No actions recorded")
        return "\n".join(lines)
