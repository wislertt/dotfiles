import json
import time
from pathlib import Path
from typing import Any

from bake import command, console
from bakelib.space import BaseSpace

from src.python.core.tmp import uv_cache as core

# Temporary. To remove: delete uv_cache.py from commands/tmp, core/tmp and tests/unit/core/tmp (test_),
# UvCacheMixin in src/python/bakefile.py, and `rm -rf ~/.local/state/dotfiles/uv-cache` on each machine
STATE = Path.home() / ".local/state/dotfiles/uv-cache"


class UvCacheMixin(BaseSpace):
    @command(help="Temporary: snapshot the uv cache and fail when something fills it")
    def uv_cache_watch(self) -> None:
        cache = Path(
            self.ctx.run(
                ["uv", "cache", "dir"],
                env={
                    "NO_COLOR": "1"
                },  # bake runs it in a pty, where uv colours the path
                capture_output=True,
                stream=False,
                echo=False,
            ).stdout.strip()
        )
        STATE.mkdir(parents=True, exist_ok=True)
        reports = sorted(STATE.glob("*.json"))
        previous = json.loads(reports[-1].read_text()) if reports else None
        now = time.time()
        current: dict[str, Any] = {
            "taken": now,
            "previous": str(reports[-1]) if reports else None,
            **core.snapshot(cache, previous["taken"] if previous else None),
        }
        report = STATE / f"{time.strftime('%Y%m%d-%H%M%S', time.localtime(now))}.json"
        report.write_text(json.dumps(current, indent=2))
        for name, usage in current["folders"].items():
            console.echo(
                f"{usage['bytes'] / core.GIB:7.2f} GiB {usage['files']:>9} files  {name}"
            )
        if found := core.problems(previous, current):
            for line in found:
                console.error(line)
            raise SystemExit(
                f"uv cache needs a look: ask the agent to investigate {report}"
            )
        console.success(f"uv cache looks normal; report in {report}")
