import subprocess

from spec_repair.config import SETUP_DICT
from spec_repair.exceptions import SolverInvocationError


def run_subprocess(cmd, encoding: str = 'utf-8', suppress=False, timeout=-1,
                   ok_returncodes=None):
    """
    Run a command and return its stdout.

    :param ok_returncodes: exit codes that count as success. When given, any
        other code raises `SolverInvocationError` carrying the code and stderr.

    Off by default, because the existing callers each have their own idea of
    what a failure looks like and read it out of the output. It exists because
    the silent alternative is worse than a crash: this function returned stdout
    alone, discarding both stderr and the exit code, so a solver that never ran
    was indistinguishable from one that ran and found nothing.

    Measured on the Slurm compute nodes, where clingo could not load
    `liblua5.1.so.0` and exited 127 with empty output: the repair reported "the
    violation trace violates no assumption at all" for a trace that passes the
    same check locally. A missing library became a wrong answer about a
    specification.
    """
    if suppress:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    else:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = p.communicate(timeout=timeout if timeout != -1 else None)
        output = stdout
    except subprocess.TimeoutExpired:
        # Without this, a caller-supplied timeout (e.g. run_ILASP_raw's 60s)
        # was silently never applied - communicate() had no timeout at all,
        # so a hung/slow child (ILASP is the current caller that sets one)
        # could block forever. Worse, if the calling Python process is later
        # killed (e.g. a test run cancelled), this child is orphaned and
        # keeps running - one such orphaned ILASP process ran unbounded for
        # 10+ hours, starving the machine of memory and contributing to a
        # JVM native crash (Bus error) in an unrelated Spectra synthesis call.
        p.kill()
        p.communicate()
        raise
    output = output.decode(encoding)
    if ok_returncodes is not None and p.returncode not in ok_returncodes:
        detail = (stderr or b"").decode(encoding, errors="replace").strip()
        raise SolverInvocationError(
            f"{cmd[0] if cmd else 'command'} exited {p.returncode} "
            f"(expected one of {sorted(ok_returncodes)}).\n"
            f"stderr: {detail[:500] or '(empty)'}\n"
            f"stdout: {output.strip()[:300] or '(empty)'}")
    return output


def create_cmd(param):
    cmd = []
    if SETUP_DICT['wsl']:
        cmd.append('wsl')
    cmd.append(SETUP_DICT[param[0]])
    if len(param) == 1:
        return cmd
    cmd += param[1:]
    return cmd
