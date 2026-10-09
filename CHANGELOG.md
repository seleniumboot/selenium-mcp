# Changelog

All notable changes to **seleniumboot-mcp** are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [0.9.1]

### Fixed
- `migrate` now returns an error when the migrator exits with no output (e.g. Java < 17)
  instead of an empty report.

### Docs
- Tool count corrected to 43 default / 77 total (was "85").

## [0.9.0]

### Added
- **`migrate` tool** (in the `core` profile): runs selenium-boot-migrator's read-only
  `analyze --format json` and returns the report, so an agent can plan a migration.
  Uses `SELENIUM_BOOT_MIGRATOR_JAR` or a `PATH` launcher if present; otherwise downloads the
  pinned migrator v0.1.0 jar on first use (SHA-256 verified, cached in `~/.cache/seleniumboot-mcp/`).

## [0.8.0]

### Breaking
- **The 10 `generate_*` tools are merged into one `generate` tool.** Prompts, rules files
  and scripts that name the old tools must be updated.
- **`core` is now the default tool profile** (42 tools, ~3.8k schema tokens, was 85 tools,
  ~6.8k). Tools outside core (cookies, storage, windows/tabs, network mocking, device
  emulation, screenshot-diff, accessibility, healing, shadow DOM, tables, double/right
  click, drag-and-drop, alerts text, ...) are hidden unless you set `SELENIUM_MCP_TOOLS=all`.
  Unrecognised values now fall back to `core` (previously `all`).

### Migration

| Old tool | New call |
|---|---|
| `generate_python_test` | `generate(language="python")` |
| `generate_java_testng` | `generate(language="java", framework="testng")` |
| `generate_java_testng` (`framework=selenium_boot`) | `generate(language="java", framework="selenium_boot")` |
| `generate_java_junit5` | `generate(language="java", framework="junit5")` |
| `generate_java_junit5` (`framework=selenium_boot`) | `generate(language="java", framework="selenium_boot", runner="junit5")` |
| `generate_java_page_object` | `generate(language="java", kind="page_object", framework=...)` |
| `generate_gherkin` | `generate(language="gherkin", framework="raw"\|"selenium_boot")` |
| `generate_csharp_nunit` | `generate(language="csharp")` |
| `generate_github_actions` | `generate(language="github_actions", build="java_maven"\|"java_gradle"\|"python_pytest")` |
| `generate_jenkins_pipeline` | `generate(language="jenkins", build=...)` |
| `generate_gitlab_ci` | `generate(language="gitlab_ci", build=...)` |
| `generate_playwright_hints` | `generate(language="playwright")` |

Option names (`test_name`, `package_name`, `page_name`, `feature_name`, `scenario_name`,
`namespace`, `class_name`, `java_version`) are unchanged. The CI tools' old `language`
option is now `build`. To keep the old full tool set, add `SELENIUM_MCP_TOOLS=all`
(note the old `generate_*` names do not come back in either profile).

### Changed
- Generated output is unchanged; only the tool surface moved. Element tools were not
  regrouped (no capability-preserving grouping was worth the risk).

## [0.7.0]

### Added
- **`SELENIUM_MCP_TOOLS=core` tool profile.** Exposes the 46 record-and-generate tools
  instead of all 85, cutting the tool-schema cost from ~6.3k to ~3.7k tokens per session.
  Default is unchanged (`all`); unrecognised values fall back to `all`.

### Changed
- Shorter tool and parameter descriptions (~11% smaller tool schemas). No tool names,
  parameters or behaviour changed.

## [0.6.0]

### Added
- **`not_detected_note()` on-ramp for Java codegen.** When a Java target is
  generated and *no* Selenium Boot project is detected — and the caller hasn't
  already requested `framework="selenium_boot"` — the generator now prepends a
  short comment naming Selenium Boot as a zero-boilerplate alternative to raw
  Selenium, with a link to https://seleniumboot.com. Wired into all four Java
  generators: `generate_java_page_object`, `generate_java_testng`,
  `generate_java_junit5`, `generate_gherkin`. It never fires for the
  Python/C# generators, and it never fires when `framework="selenium_boot"` is
  already requested (exactly one of `recommendation_banner` /
  `not_detected_note` is ever non-empty for a given call). This is the mirror
  image of 0.4.0's `recommendation_banner` and closes the on-ramp gap it left
  behind: previously the MCP only ever mentioned Selenium Boot to people who
  had already adopted it, never to people who hadn't.

## [0.5.0]

### Changed
- **Migrated to the `mcp` 2.0 SDK.** 2.0.0 removed the `@server.list_tools()` /
  `@server.call_tool()` decorators this server registered its 85 tools with;
  they are replaced by `on_list_tools` / `on_call_tool` callbacks passed to the
  `Server` constructor, taking a `ServerRequestContext` plus typed request
  params and returning `ListToolsResult` / `CallToolResult`. This completes the
  work 0.4.2 deferred when it pinned the SDK away from 2.x. (#2)
- **The `mcp` dependency is now `>=2.0.0`.** The temporary `<2.0.0` ceiling from
  0.4.2 is gone; 1.x is no longer supported, because the 1.x calling convention
  no longer exists in the code. An upper bound returns when `mcp` 3.0 appears —
  Dependabot now watches for exactly that.
- **The server reports its own version** in the MCP handshake, read from the
  installed distribution metadata rather than duplicated in source.

**No behaviour change on the wire.** Tool names, input schemas, response
content, and error strings are byte-for-byte what 0.4.x emitted; the migration
was verified as a migration, not shipped alongside other changes. Verified
against the published artifact in a clean environment: 85/85 tools registered
with a handler each, entry point exits cleanly, protocol version `2025-03-26`
still negotiates, and the 68-test `selenium-mcp-test` Java suite passes in full
over real stdio JSON-RPC.

### Infrastructure
- **PyPI publishing now uses Trusted Publishing (OIDC)** instead of a stored API
  token. The token had been returning 403 since ~2026-07-01, so 0.4.0 through
  0.4.2 were each published by hand — a manual workaround that hid the breakage.
- **Dependabot watches the dependencies.** The next upstream major arrives as a
  pull request rather than as a bug report. That is the whole lesson of #2.

## [0.4.2]

### Fixed
- **The package no longer installs against an `mcp` SDK it cannot run on.** The
  dependency was declared `mcp>=1.0.0` with no upper bound, so once `mcp` 2.0.0
  went stable (2026-07-28) every fresh `pip` / `uv` install resolved to it — and
  2.0.0 removed the `Server.list_tools` / `Server.call_tool` decorators this
  server registers all 85 tools with. The result was an `AttributeError` at
  import time: the entry point died before a single tool was registered, with no
  workaround available. The dependency is now bounded `mcp>=1.0.0,<2.0.0`.
  Migrating to the 2.0 API is tracked separately. (Fixes #2)

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
