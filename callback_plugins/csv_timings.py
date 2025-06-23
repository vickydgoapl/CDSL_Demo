# csv_timings.py  (Python ≥3.6)
from __future__ import annotations
from ansible.plugins.callback import CallbackBase
import csv, os, datetime, pathlib, typing as T

class CallbackModule(CallbackBase):
    """
    Aggregate callback: dump per-task start & end times to a CSV.
    Enable with   callback_whitelist = csv_timings
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "aggregate"
    CALLBACK_NAME = "csv_timings"
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super().__init__()
        self._tasks: dict[str, dict[str, str]] = {}
        # path can come from env var or default to ./task_times.csv
        self._outfile = pathlib.Path(
            os.getenv("ANSIBLE_CSV_PATH", "task_times.csv")
        ).expanduser()

    # ---------- helpers ----------
    @staticmethod
    def _utc_iso() -> str:
        return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # ---------- event hooks ----------
    def v2_runner_on_start(self, host, task, **kwargs):          # noqa: N802
        self._tasks[task.get_name()] = {"start": self._utc_iso()}

    def v2_runner_on_ok(self, result, **kwargs):                 # noqa: N802
        self._tasks[result.task_name]["end"] = self._utc_iso()

    # mirror failures/skips so end time still gets written
    v2_runner_on_failed = v2_runner_on_ok
    v2_runner_on_skipped = v2_runner_on_ok

    def v2_playbook_on_stats(self, stats):                       # noqa: N802
        # write once, at the very end
        self._outfile.parent.mkdir(parents=True, exist_ok=True)
        with self._outfile.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["task", "start", "end"])
            writer.writeheader()
            for name, times in self._tasks.items():
                writer.writerow({"task": name,
                                 "start": times.get("start", ""),
                                 "end":   times.get("end", "")})
        self._display.display(f"\nCSV timing written to {self._outfile}\n")
