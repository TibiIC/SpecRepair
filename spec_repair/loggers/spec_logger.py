from datetime import datetime

from spec_repair.interfaces.ispecification import ISpecification
from spec_repair.components.repair_data import RepairData


class SpecLogger:
    def __init__(self, filename: str = "spec_repair.log", on_record=None):
        self.filename = filename
        self._on_record = on_record  # optional callback(idx, spec, data)
        with open(self.filename, 'a') as f:
            f.write(f"[SpecLogger] Started at: {datetime.now()}\n")

    def set_on_record(self, on_record):
        """
        Attach (or replace) the per-record callback after construction.

        Needed because the usual callback wants to inspect the orchestrator that
        owns this logger - e.g. to snapshot its search graph - and that
        orchestrator takes the logger as a constructor argument, so it cannot
        exist yet when the logger is built. See BFSRepairOrchestratorBuilder,
        which uses this to wire the two together once both exist.
        """
        self._on_record = on_record

    def record(self, idx: int, spec: ISpecification, data: RepairData, type: str = "Learned"):
        log_message = f"[SpecLogger] {type} Index: {idx}, learning_type: {data.learning_type}, learning_steps: {data.learning_steps}, learning_time: {data.learning_time}\n"
        with open(self.filename, 'a') as f:
            f.write(log_message)
        if self._on_record:
            self._on_record(idx, spec, data)
