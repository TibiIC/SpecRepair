import re
from typing import Optional

from spec_repair.components.interfaces.ioracle import IOracle
from spec_repair.components.spec_oracle import SpecOracle
from spec_repair.config import PATH_TO_CLI
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import CounterStrategy
from spec_repair.old.specification_helper import run_subprocess
from spec_repair.util.file_util import generate_temp_filename, write_to_file


class NewSpecOracle(IOracle):
    def is_valid_or_counter_arguments(self, new_spec):
        return self.synthesise_and_check(new_spec)

    def synthesise_and_check(self, spec: SpectraSpecification) -> Optional[CounterStrategy]:
        """
        Uses Spectra under the hood to check whether specifcation is realisable.
        If it is, nothing is returned. Otherwise, it returns a CounterStrategy.
        """
        output = self._synthesise(spec)
        if re.search("Result: Specification is unrealizable", output):
            output = str(output).split("\n")
            counter_strategy = list(filter(re.compile(r"\s*->\s*[^{]*{[^}]*").search, output))
            return counter_strategy
        elif re.search("Result: Specification is realizable", output):
            return None
        else:
            raise Exception(output)

    def _synthesise(self, spec: SpectraSpecification):
        spec_str = spec.to_str(is_to_compile=True)
        spectra_file: str = generate_temp_filename(ext=".spectra")
        write_to_file(spectra_file, spec_str)
        cmd = ['java', '-jar', PATH_TO_CLI, '-i', spectra_file, '--counter-strategy', '--jtlv']
        return run_subprocess(cmd)