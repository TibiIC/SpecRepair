import os
from datetime import datetime
from typing import List, Tuple

from main.mutated_spec_generator import generate_stronger_specs_with_violations
from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import write_to_file
from tests.base_test_case import BaseTestCase


class TestMutatedSpecGenerator(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.date_str = datetime.now().strftime("%Y-%m-%d")

    def test_generate_stronger_specs_minepump(self):
        self._generate_and_check("minepump")

    def test_generate_stronger_specs_arbiter(self):
        self._generate_and_check("arbiter")

    def test_generate_stronger_specs_lift(self):
        self._generate_and_check("lift")

    def test_generate_stronger_specs_traffic_single(self):
        self._generate_and_check("traffic_single")

    def test_generate_stronger_specs_traffic_updated(self):
        self._generate_and_check("traffic_updated")

    def test_generate_stronger_specs_elevator(self):
        self._generate_and_check("elevator")

    def test_generate_stronger_specs_gyro(self):
        self._generate_and_check("gyro")

    def _generate_and_check(self, case_study_name: str, n_mutations: int = 3, n_traces_per_mutation: int = 1):
        ideal_file = f"../input-files/case-studies/spectra/{case_study_name}/ideal.spectra"
        ideal_spec = SpectraSpecification.from_file(ideal_file)
        self.assertTrue(
            SpectraGR1Oracle.is_realisable(ideal_spec),
            f"{case_study_name}'s ideal.spectra should itself be realisable"
        )

        results: List[Tuple[SpectraSpecification, List[List[str]]]] = generate_stronger_specs_with_violations(
            ideal_spec, n_mutations, n_traces_per_mutation
        )
        self.assertGreaterEqual(
            len(results), 1,
            f"Expected at least one mutated-spec/violation-trace pair for {case_study_name}"
        )

        out_dir = f"test_files/out/generate_stronger/{case_study_name}_{self.date_str}"
        os.makedirs(out_dir, exist_ok=True)

        for i, (mutated_spec, traces) in enumerate(results):
            self.assertTrue(
                SpectraGR1Oracle.is_realisable(mutated_spec),
                f"Mutation {i} of {case_study_name} should be realisable"
            )
            self.assertTrue(
                mutated_spec.implies(ideal_spec, GR1FormulaType.ASM),
                f"Mutation {i} of {case_study_name} should have assumptions at least as strong as the ideal spec's"
            )
            self.assertFalse(
                mutated_spec.equivalent_to(ideal_spec, GR1FormulaType.ASM),
                f"Mutation {i} of {case_study_name} should be strictly stronger than the ideal spec, not equivalent"
            )
            self.assertTrue(
                mutated_spec.implies(ideal_spec, GR1FormulaType.GAR),
                f"Mutation {i} of {case_study_name} should have guarantees at least as strong as the ideal spec's "
                f"(guarantees may be untouched by a given mutation, but never weakened)"
            )

            write_to_file(f"{out_dir}/mutation_{i}.spectra", mutated_spec.to_str())
            self.assertGreater(len(traces), 0, f"Mutation {i} of {case_study_name} should have at least one violation trace")
            for j, trace in enumerate(traces):
                self.assertGreater(len(trace), 0, f"Violation trace {j} for mutation {i} of {case_study_name} should be non-empty")
                write_to_file(f"{out_dir}/mutation_{i}_violation_trace_{j}.txt", "\n".join(trace))
