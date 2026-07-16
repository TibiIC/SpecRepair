import subprocess

from spec_repair.config import SETUP_DICT


def run_subprocess(cmd, encoding: str = 'utf-8', suppress=False, timeout=-1):
    if suppress:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    else:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.communicate()[0]
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
