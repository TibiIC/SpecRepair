"""
What a repair run says about itself while it is running.

Two audiences, deliberately kept apart:

* **stdout** - one compact line per event, for reading over someone's shoulder
  or scrolling a tmux pane. No specification bodies, no multi-line stanzas.
* **`progress.log`** - the same events, appended, so a finished run can be
  reconstructed after the pane is gone.
* **`status.txt`** - the *current* state, rewritten in place. This is the one to
  `cat` when coming back to a run the next morning: it answers "what is it doing
  and how long has it been doing it" without reading any history.

The elapsed timer matters more than it looks. Spectra's BDD engine can sit in a
garbage-collection equilibrium that never errors and never finishes (see the
2026-08-06 notes), and a wall of `Garbage collection #3252` tells you nothing
about whether that started a minute or six hours ago. `status.txt` does.

The heartbeat thread that keeps that timer fresh sleeps between updates and
rewrites a file of a few hundred bytes, so it costs nothing measurable against a
run that is otherwise saturating a core in the JVM.
"""
import os
import threading
import time
from typing import Optional

# Long enough that an idle run writes ~120 bytes/minute, short enough that the
# number on screen is never misleading by much.
HEARTBEAT_SECONDS = 30


def format_duration(seconds: float) -> str:
    """`1h04m12s` / `4m12s` / `12.4s` - always three significant units at most."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h{minutes:02d}m{secs:02d}s"
    return f"{minutes}m{secs:02d}s"


class ProgressReporter:
    """
    Reports where a repair run is and how long it has been there.

    Every method is safe to call on a reporter with no output directory - the
    tests build orchestrators without one, and progress reporting must never be
    the reason a run fails.
    """

    def __init__(self, label: str = "run", out_dir: Optional[str] = None,
                 learner: str = "", to_stdout: bool = True,
                 heartbeat_seconds: int = HEARTBEAT_SECONDS):
        self.label = label
        self.learner = learner
        self.out_dir = out_dir
        self.to_stdout = to_stdout
        self.heartbeat_seconds = heartbeat_seconds

        self.started_at = time.time()
        self.depth = 0
        self.node = 0
        self.queue = 0
        self.phase = "starting"
        self.phase_started_at = time.time()
        self.finals = 0
        self.intermediates = 0
        self.explored = 0

        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._heartbeat: Optional[threading.Thread] = None
        self._progress_log = os.path.join(out_dir, "progress.log") if out_dir else None
        self._status_file = os.path.join(out_dir, "status.txt") if out_dir else None
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

    # ---- lifecycle -------------------------------------------------------

    def start(self) -> None:
        self.started_at = time.time()
        self.emit(f"START  {self.label}" + (f"  [{self.learner}]" if self.learner else ""))
        self._write_status()
        if self.heartbeat_seconds > 0 and self._status_file:
            self._heartbeat = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat.start()

    def finish(self, finals: int, intermediates: int) -> None:
        self.finals, self.intermediates = finals, intermediates
        self.phase = "done"
        self._stop.set()
        total = time.time() - self.started_at
        self.emit(f"DONE   {self.label}  {finals} final, {intermediates} intermediate, "
                  f"{self.explored} nodes explored, {format_duration(total)}")
        self._write_status()

    def _heartbeat_loop(self) -> None:
        # wait() rather than sleep() so finish() ends the thread immediately
        # instead of leaving it to time out.
        while not self._stop.wait(self.heartbeat_seconds):
            self._write_status()

    # ---- events ----------------------------------------------------------

    def node_started(self, depth: int, node: int, queue: int, learning_type: str) -> None:
        with self._lock:
            self.depth, self.node, self.queue = depth, node, queue
            self.explored += 1
        self.set_phase(f"node d{depth} ({learning_type})")
        self.emit(f"NODE   d{depth} n{node}  {learning_type:<4}  queue {queue}")

    def set_phase(self, phase: str) -> None:
        with self._lock:
            self.phase = phase
            self.phase_started_at = time.time()
        self._write_status()

    def event(self, kind: str, detail: str = "", seconds: Optional[float] = None) -> None:
        timing = f"  ({format_duration(seconds)})" if seconds is not None else ""
        self.emit(f"{kind:<6} d{self.depth} n{self.node}  {detail}{timing}")

    def emit(self, line: str) -> None:
        stamped = f"[{format_duration(time.time() - self.started_at):>9}] {line}"
        if self.to_stdout:
            print(stamped, flush=True)
        if self._progress_log:
            try:
                with open(self._progress_log, "a") as f:
                    f.write(stamped + "\n")
            except OSError:
                pass  # never let reporting break a run

    # ---- status file -----------------------------------------------------

    def _write_status(self) -> None:
        if not self._status_file:
            return
        now = time.time()
        with self._lock:
            body = (
                f"case study : {self.label}\n"
                f"learner    : {self.learner or '-'}\n"
                f"started    : {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.started_at))}\n"
                f"elapsed    : {format_duration(now - self.started_at)}\n"
                f"depth      : {self.depth}\n"
                f"node       : {self.node} (queue {self.queue}, {self.explored} explored)\n"
                f"phase      : {self.phase}\n"
                f"in phase   : {format_duration(now - self.phase_started_at)}\n"
                f"solutions  : {self.finals} final, {self.intermediates} intermediate\n"
                f"updated    : {time.strftime('%H:%M:%S')}\n"
            )
        try:
            # Write-then-rename so a reader never catches a half-written file.
            tmp = self._status_file + ".tmp"
            with open(tmp, "w") as f:
                f.write(body)
            os.replace(tmp, self._status_file)
        except OSError:
            pass


class Timed:
    """
    Time a phase, reporting it whether it succeeds or throws.

    A learning step that raises is exactly the one worth knowing the duration
    of, so the timing is reported however the block exits, not on the happy path
    only.

    :param min_seconds: below this, and with nothing to say and nothing thrown,
        the phase is not reported at all. Verification of an already-good
        candidate takes milliseconds and happens once per candidate; printing
        each one buries the lines that say where the run is. A slow one is worth
        a line precisely because it is slow.
    """

    def __init__(self, reporter: ProgressReporter, kind: str, phase: str,
                 min_seconds: float = 0.0):
        self.reporter, self.kind, self.phase = reporter, kind, phase
        self.min_seconds = min_seconds
        self.detail = ""
        self.started = 0.0

    def __enter__(self) -> "Timed":
        self.started = time.time()
        self.reporter.set_phase(self.phase)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        elapsed = time.time() - self.started
        if exc_type is None and not self.detail and elapsed < self.min_seconds:
            return False
        detail = self.detail or ("failed: " + exc_type.__name__ if exc_type else "")
        self.reporter.event(self.kind, detail, seconds=elapsed)
        return False

    def result(self, detail: str) -> None:
        self.detail = detail
