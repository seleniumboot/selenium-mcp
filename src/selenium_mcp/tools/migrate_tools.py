"""migrate tool — run selenium-boot-migrator's read-only analysis and return its JSON report."""

import asyncio
import hashlib
import os
import shutil
import urllib.request
from pathlib import Path
from mcp.types import Tool

JAR_ENV = "SELENIUM_BOOT_MIGRATOR_JAR"
TIMEOUT_SECONDS = 120

# Pinned release, verified by hash. Bump both together when the migrator releases.
MIGRATOR_VERSION = "0.1.1"
MIGRATOR_URL = (
    "https://github.com/seleniumboot/selenium-boot-migrator/releases/download/"
    f"v{MIGRATOR_VERSION}/selenium-boot-migrator.jar"
)
MIGRATOR_SHA256 = "bd7200fd7ee0aa5c46e35112e648891fa1177460fde73b2a9c7a17ebf46ee286"
CACHE_DIR = Path.home() / ".cache" / "seleniumboot-mcp"

NOT_FOUND = (
    "selenium-boot-migrator unavailable. Set "
    f"{JAR_ENV} to a jar built with mvn package from "
    "github.com/seleniumboot/selenium-boot-migrator, or put a 'selenium-boot-migrator' "
    "launcher on PATH. Java 17+ is required."
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _download_jar() -> Path | None:
    """Fetch the pinned release jar into the cache; None if it cannot be verified."""
    jar = CACHE_DIR / f"selenium-boot-migrator-{MIGRATOR_VERSION}.jar"
    if jar.is_file() and _sha256(jar) == MIGRATOR_SHA256:
        return jar
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = jar.with_suffix(".part")
        with urllib.request.urlopen(MIGRATOR_URL, timeout=60) as resp:
            tmp.write_bytes(resp.read())
        if _sha256(tmp) != MIGRATOR_SHA256:
            tmp.unlink(missing_ok=True)
            return None
        tmp.replace(jar)
        return jar
    except OSError:
        return None


def _command() -> list[str] | None:
    java = shutil.which("java")
    jar = os.environ.get(JAR_ENV, "").strip()
    if jar:
        return [java, "-jar", jar] if java and Path(jar).is_file() else None
    launcher = shutil.which("selenium-boot-migrator")
    if launcher:
        return [launcher]
    if not java:
        return None
    cached = _download_jar()
    return [java, "-jar", str(cached)] if cached else None


class MigrateTools:
    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="migrate",
                description=(
                    "Analyze an existing Selenium Java project for migration to Selenium Boot "
                    "(read-only, via selenium-boot-migrator). Returns the JSON report: what maps "
                    "cleanly and what needs manual work."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_dir": {
                            "type": "string",
                            "description": "Path to the Selenium project to analyze.",
                        }
                    },
                    "required": ["project_dir"],
                },
            )
        ]

    def get_handlers(self) -> dict:
        return {"migrate": self._migrate}

    async def _migrate(self, args: dict) -> str:
        project = Path(args.get("project_dir") or "").expanduser()
        if not args.get("project_dir") or not project.is_dir():
            return f"Error: project_dir not found: {args.get('project_dir')!r}"
        cmd = await asyncio.to_thread(_command)
        if cmd is None:
            return f"Error: {NOT_FOUND}"
        proc = await asyncio.create_subprocess_exec(
            *cmd, "analyze", str(project), "--format", "json",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return f"Error: migrator timed out after {TIMEOUT_SECONDS}s"
        # exit 0 = ok, 1 = confidence gate (not used here); 2/3 = usage or runtime error
        # An unsupported JVM (Java < 17) also exits 1, with nothing on stdout.
        if proc.returncode not in (0, 1) or not out.strip():
            return f"Error: migrator exited {proc.returncode} with no report (Java 17+ required): {err.decode(errors='replace').strip()}"
        return out.decode(errors="replace")
