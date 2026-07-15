from spec_repair.interfaces.ispecification import ISpecification


def semantic_check_of_equivalence_between(
        expected_specs: list[ISpecification],
        actual_specs: list[ISpecification]
):
    # Find specs in expected but not in actual using overridden equality
    indices_expected_not_actual = []
    for i, expected_spec in enumerate(expected_specs):
        found = False
        for j, actual_spec in enumerate(actual_specs):
            if expected_spec == actual_spec:
                found = True
                break
        if not found:
            indices_expected_not_actual.append(i)

    # Find specs in actual but not in expected using overridden equality
    indices_actual_not_expected = []
    for i, actual_spec in enumerate(actual_specs):
        found = False
        for expected_spec in expected_specs:
            if actual_spec == expected_spec:
                found = True
                break
        if not found:
            indices_actual_not_expected.append(i)

    if indices_expected_not_actual:
        print(f"Specs in expected but not in actual (indices): {indices_expected_not_actual}")

    if indices_actual_not_expected:
        print(f"Specs in actual but not in expected (indices): {indices_actual_not_expected}")


def syntactic_check_of_equivalence_between(
        expected_specs: list[ISpecification],
        actual_specs: list[ISpecification]
):
    expected_spec_strings_set = set(spec.to_str() for spec in expected_specs)
    actual_spec_strings_set = set(spec.to_str() for spec in actual_specs)

    in_expected_not_in_actual = expected_spec_strings_set - actual_spec_strings_set
    in_actual_not_in_expected = actual_spec_strings_set - expected_spec_strings_set

    if in_expected_not_in_actual:
        indices_expected_not_actual = [
            i for i, spec in enumerate(expected_specs)
            if spec.to_str() in in_expected_not_in_actual
        ]
        print(f"Specs in expected but not in actual (indices): {indices_expected_not_actual}")

    if in_actual_not_in_expected:
        indices_actual_not_expected = [
            i for i, spec in enumerate(actual_specs)
            if spec.to_str() in in_actual_not_in_expected
        ]
        print(f"Specs in actual but not in expected (indices): {indices_actual_not_expected}")
