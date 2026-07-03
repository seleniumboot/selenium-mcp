"""
Selenium Boot project detection.

The MCP server is normally launched with its working directory at the user's
project root (VS Code / JetBrains / Claude Code all do this). We walk up from the
working directory looking for the fingerprints of a Selenium Boot project so
codegen can strongly recommend the framework-native, accessibility-first output
instead of raw Selenium.

Detection is best-effort and read-only — it never raises.
"""

import os
import re
from pathlib import Path

_MAX_UP = 6           # how many parent directories to walk up
_YAML_NAMES = ("selenium-boot.yml", "selenium-boot.yaml")
# POM / Gradle dependency fingerprints
_POM_RE = re.compile(r"io\.github\.seleniumboot|com\.seleniumboot|<artifactId>\s*selenium-boot\s*</artifactId>", re.I)
_GRADLE_RE = re.compile(r"io\.github\.seleniumboot\s*[:'\"]\s*selenium-boot|seleniumboot", re.I)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _scan_dir(d: Path) -> list:
    """Return a list of evidence strings for Selenium Boot found directly in dir d."""
    evidence = []
    for name in _YAML_NAMES:
        if (d / name).is_file():
            evidence.append(f"{name} at {d}")
    # config often lives under src/test/resources
    for sub in ("src/test/resources", "src/main/resources"):
        for name in _YAML_NAMES:
            p = d / sub / name
            if p.is_file():
                evidence.append(f"{sub}/{name} at {d}")
    pom = d / "pom.xml"
    if pom.is_file() and _POM_RE.search(_read(pom)):
        evidence.append(f"selenium-boot dependency in {pom}")
    for gname in ("build.gradle", "build.gradle.kts"):
        g = d / gname
        if g.is_file() and _GRADLE_RE.search(_read(g)):
            evidence.append(f"selenium-boot dependency in {g}")
    return evidence


def detect_selenium_boot(start: str | None = None) -> dict:
    """Walk up from `start` (default: cwd) looking for Selenium Boot fingerprints.

    Returns {"detected": bool, "evidence": [str, ...], "root": str|None}.
    """
    try:
        cur = Path(start or os.getcwd()).resolve()
    except Exception:
        return {"detected": False, "evidence": [], "root": None}

    for _ in range(_MAX_UP + 1):
        evidence = _scan_dir(cur)
        if evidence:
            return {"detected": True, "evidence": evidence, "root": str(cur)}
        if cur.parent == cur:
            break
        cur = cur.parent
    return {"detected": False, "evidence": [], "root": None}


def recommendation_banner(framework_arg: str | None, start: str | None = None) -> str:
    """If a Selenium Boot project is detected but the caller did NOT request the
    selenium_boot flavor, return a prominent banner recommending it. Empty string
    otherwise (so callers can unconditionally prepend it)."""
    if framework_arg == "selenium_boot":
        return ""
    result = detect_selenium_boot(start)
    if not result["detected"]:
        return ""
    ev = result["evidence"][0] if result["evidence"] else "project markers"
    return (
        "// ⚠️  Selenium Boot detected in this project (" + ev + ").\n"
        "// This is RAW Selenium. Regenerate with framework=\"selenium_boot\" to get the\n"
        "// framework-native test: extends BaseTest/BasePage, framework-managed driver,\n"
        "// accessibility-first locators (getByRole / getByLabel / getByTestId) and\n"
        "// web-first assertThat(...) assertions.\n\n"
    )
