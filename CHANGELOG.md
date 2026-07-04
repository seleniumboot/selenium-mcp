# Changelog

All notable changes to **seleniumboot-mcp** are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [0.4.1]

### Fixed
- `fill_form` now snapshots each field's accessibility attributes (label / role /
  test-id), same as the individual `type_text` / `click` tools. Previously,
  filling a form via `fill_form` recorded no attributes, so generated Selenium
  Boot code fell back to structural `$(By.id(...))` locators instead of the
  accessibility-first `getByLabel` / `getByRole`. A11y-first locators are now the
  default regardless of how the form is filled — no special prompt required.

## [0.4.0]

Framework-native code generation for [Selenium Boot](https://github.com/seleniumboot/selenium-boot) — when the MCP is used inside a Selenium Boot project it now emits idiomatic, accessibility-first framework code instead of raw Selenium.

### Added
- **`detect_selenium_boot` tool** — detects a Selenium Boot project (looks for `selenium-boot.yml` or the `io.github.seleniumboot` dependency in `pom.xml` / `build.gradle`, walking up parent directories) and recommends `framework="selenium_boot"`. Brings the total to **85 tools**.
- **`framework="selenium_boot"` for every Java generator** — previously only `generate_java_page_object` supported it. Now `generate_java_testng` (extends `BaseTest`), `generate_java_junit5` (extends `BaseJUnit5Test`) and `generate_gherkin` (steps extend `BaseCucumberSteps`) do too. JUnit 5 / Cucumber use the static `Locator.by*` factories, since their base classes don't expose the `getBy*` helpers.
- **Web-first assertions** — the `assert_*` tools now record passing checks to the session log, and Selenium Boot codegen emits `assertThat(locator).isVisible()/.hasText()/.hasAttribute()/.count()`. Page-title / URL checks fall back to the TestNG or JUnit 5 assertion API.
- **`getByLabel` locators** — the interaction snapshot now captures an element's associated `<label>` text (for/wrapping/`aria-labelledby`/`.labels`), and it ranks high in the accessibility-first locator ladder for form controls.
- **SmartLocator fallback** — brittle, low-confidence elements with multiple candidate strategies now resolve through a `smartFind(...)` helper in generated page objects.
- When a Selenium Boot project is detected, the raw (non-framework) generators prepend a banner recommending regeneration with `framework="selenium_boot"`.

### Changed
- Accessibility-first locator priority: `testid → role+name → label → placeholder → alt → title → id → name → SmartLocator/selector`.
- Server instructions guide the agent to call `detect_selenium_boot` before generating Java.

### Fixed
- Raw Java (TestNG / JUnit 5) and C# NUnit generators no longer redeclare the `field` / `dropdown` local variable when a flow has more than one text input or `<select>` (previously a duplicate-variable compile error); the variables are now uniquely numbered.

## [0.3.7]
- CI improvements; Jenkins / GitLab CI pipeline codegen; 84 tools.

Earlier releases predate this changelog — see the git history.
