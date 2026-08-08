import atexit
import os
import tempfile
import shutil
import random
import re
import string
from pathlib import Path
from typing import Optional

# Custom type definitions
Log = str
ASPTrace = str
FilePath = str


def validate_spectra_file(file_path: str) -> None:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    if path.suffix.lower() != ".spectra":
        raise ValueError(f"Invalid file type: {file_path}. Expected a '.spectra' file.")


def get_line_from_file(filepath: FilePath, line_number: int) -> Optional[str]:
    try:
        with open(filepath, 'r') as f:
            for current_line_num, line in enumerate(f, start=1):
                if current_line_num == line_number:
                    return line.rstrip('\n')
        return None  # If line_number is beyond end of file
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return None


def write_file(filename: FilePath, content: list[str]):
    """
    NB: newline = '\\\\n' is necessary so that file is compatible with
    linux (ILASP is run from linux).\n
    :param content: List of lines to save.
    :param filename: filename to save to
    """
    filename = re.sub(r"\\", "/", filename)
    make_directories_if_needed(filename)
    output = ''.join(content)
    with open(filename, "w", newline='\n') as file:
        file.write(output)
        file.close()


def write_to_file(filename: FilePath, content: str):
    make_directories_if_needed(filename)
    with open(filename, 'w') as file:
        file.write(content)


def read_file(file_path: FilePath) -> str:
    with open(file_path, 'r') as file:
        file_content: str = file.read()
    return file_content


def read_file_lines(file_path: FilePath) -> list[str]:
    with open(file_path, "r") as file:
        spec: list[str] = file.readlines()
    return spec


def is_file_format(file_path: str, file_extension: str) -> bool:
    """
    Checks if the path to the (possibly not-existent file) exists,
    then makes sure the extension is the expected one.
    :param file_path: Complete path to a file
    :param file_extension: Expected extension of the file
    :return: True if the file format is expected
    """
    directory, _ = os.path.split(file_path)
    if not os.path.exists(directory):
        return False

    _, extension = os.path.splitext(file_path)
    return extension == file_extension


def generate_filename(spectra_file, replacement, output=False):
    if output:
        spectra_file = spectra_file.replace("input", "output")
    return spectra_file.replace(".spectra", replacement)


# Every temp file this process makes, under one directory that is removed when
# the process exits.
#
# They used to go loose into /tmp and were never deleted by anyone. On
# 2026-08-08 that filled a 32G tmpfs on every GPU box - 1.2M .lp files, 121k
# .las and 133k .spectra on gpu11 alone - and *every* run of case_study_2 ILASP
# and case_study_3 FastLAS failed with `OSError: [Errno 28] No space left on
# device`. The failure looked like a code regression and was a full disk.
_TEMP_DIR = os.path.join(
    os.environ.get("SPEC_REPAIR_TMP", tempfile.gettempdir()),
    f"spec_repair_{os.getpid()}")


def _cleanup_temp_dir() -> None:
    shutil.rmtree(_TEMP_DIR, ignore_errors=True)


atexit.register(_cleanup_temp_dir)


def generate_temp_filename(ext):
    """
    A path for a scratch file, inside this process's own temp directory.

    Grouping them per process means a killed run leaves one identifiable
    directory rather than scattering files that cannot be told from anyone
    else's, and a normal exit removes the lot. Callers on hot paths should
    still delete their own file as soon as it has been read - a long search
    makes thousands, and waiting for exit is what filled the disk.
    """
    assert is_file_extension(ext)
    os.makedirs(_TEMP_DIR, exist_ok=True)
    random_name = generate_random_string(length=10)
    return os.path.join(_TEMP_DIR, f"{random_name}{ext}")


def discard_temp_file(path: str) -> None:
    """
    Remove a scratch file, tolerating its absence.

    Deliberately silent: losing a temp file is never worth failing a repair
    over, and the caller is finished with it by definition.
    """
    try:
        os.remove(path)
    except OSError:
        pass


def generate_random_string(length: int = 10) -> str:
    return ''.join(random.choices(string.ascii_letters, k=length))


def is_file_extension(filename: str) -> bool:
    return bool(re.match(r"\.[a-zA-Z0-9_]+$", filename))


def make_directories_if_needed(output_filename):
    folder = re.sub(r"/[^/]*$", "", output_filename)
    if not os.path.isdir(folder):
        # infinite recursion if the path is not a directory, since
        # re.sub(r"/[^/]*$", "", folder) == folder
        make_directories_if_needed(folder)
        os.mkdir(folder)


def write_trace(trace, filename):
    # Traces are appended, each under the next trace_name_<n>. A file that does
    # not exist yet and one that exists but names no trace both mean "nothing
    # written so far" and must both start at 0 - only the first was handled, so
    # an existing empty file (as generate_trace_asp is routinely handed) reached
    # max() with an empty sequence and raised ValueError.
    try:
        prev = read_file_lines(filename)
    except FileNotFoundError:
        prev = []
    names = re.findall(r"trace_name_(\d*)", ''.join(prev))
    timepoint = int(max(names)) + 1 if names else 0
    trace_name = "trace_name_" + str(timepoint)
    output = ""
    for timepoint in trace.keys():
        variables = list(trace[timepoint])
        for var in variables:
            if not re.search(r"prev_", var):
                prefix = ""
                if var[0] == "!":
                    prefix = "not_"
                    var = var[1:]
                output += prefix + "holds_at(" + var + "," + str(timepoint) + "," + trace_name + ").\n"
        output += "\n"
    with open(filename, 'a', newline='\n') as file:
        file.write(output)
