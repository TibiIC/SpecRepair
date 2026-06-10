from datetime import datetime

from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.components.repair_data import RepairData


class SpecLogger:
    def __init__(self, filename: str = "spec_repair.log", on_record=None):
        self.filename = filename
        self._on_record = on_record  # optional callback(idx, spec, data)
        with open(self.filename, 'a') as f:
            f.write(f"[SpecLogger] Started at: {datetime.now()}\n")

    def record(self, idx: int, spec: ISpecification, data: RepairData, type: str = "Learned"):
        log_message = f"[SpecLogger] {type} Index: {idx}, learning_type: {data.learning_type}, learning_steps: {data.learning_steps}, learning_time: {data.learning_time}\n"
        with open(self.filename, 'a') as f:
            f.write(log_message)
        if self._on_record:
            self._on_record(idx, spec, data)
