"""
Single source of truth for starting/stopping the JVM shared by every module
that resolves Java classes via jpype (spectra_toolbox.py, controller_shield.py).

JPype only allows one JVM per process, and its classpath is fixed at the
first startJVM() call - so every jar any Java-backed module needs must be
known here before that call happens. Importing this module is enough:
starting the JVM is a side effect of the import, guarded so re-imports are
no-ops, matching jpype's own recommended idempotent-startup pattern.
"""
import atexit
import os
import threading

import jpype
import jpype.imports

from spec_repair.config import PATH_TO_JVM, PATH_TO_TOOLBOX, PATH_TO_CLI, PATH_TO_SHIELD

if not jpype.isJVMStarted():
    jpype.startJVM(
        "-ea",
        "--enable-native-access=ALL-UNNAMED",
        jvmpath=PATH_TO_JVM,
        classpath=[PATH_TO_TOOLBOX, PATH_TO_CLI, PATH_TO_SHIELD],
        convertStrings=False,
    )
    print("JVM started successfully")


def _shutdown_jvm() -> None:
    if not jpype.isJVMStarted():
        return

    def force_exit():
        print("Shutdown taking too long, forcing exit.")
        os._exit(1)

    print("Shutting down JVM...")
    timer = threading.Timer(10, force_exit)
    timer.start()
    jpype.shutdownJVM()
    print("JVM shutdown initiated...")
    timer.cancel()
    print("JVM shutdown complete.")


atexit.register(_shutdown_jvm)
