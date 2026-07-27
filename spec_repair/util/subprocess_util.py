import subprocess

from spec_repair.config import SETUP_DICT


def run_subprocess(cmd, encoding: str = 'utf-8', suppress=False, timeout=-1):
    if suppress:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    else:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        output = p.communicate(timeout=timeout if timeout != -1 else None)[0]
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
