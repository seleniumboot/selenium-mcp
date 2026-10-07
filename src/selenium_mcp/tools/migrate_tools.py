"""migrate tool — run selenium-boot-migrator's read-only analysis and return its JSON report."""

import asyncio
import os
import shutil
from pathlib import Path
from mcp.types import Tool

JAR_ENV = "SELENIUM_BOOT_MIGRATOR_JAR"
TIMEOUT_SECONDS = 120

NOT_FOUND = (
    "selenium-boot-migrator not found. Build it (mvn package in "
    "github.com/seleniumboot/selenium-boot-migrator) and either set "
    f"{JAR_ENV} to the jar path or put a 'selenium-boot-migrator' launcher on PATH."
)


def _command() -> list[str] | None:
    jar = os.environ.get(JAR_ENV, "").strip()
    if jar:
        if not Path(jar).is_file():
            return None
        java = shutil.which("java")
        return [java, "-jar", jar] if java else None
    launcher = shutil.which("selenium-boot-migrator")
    return [launcher] if launcher else None


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
        cmd = _command()
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
        if proc.returncode not in (0, 1):
            return f"Error: migrator exited {proc.returncode}: {err.decode(errors='replace').strip()}"
        return out.decode(errors="replace")
