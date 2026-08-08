"""
A learner that uses FastLAS instead of ILASP.

Everything outside this file is untouched: FastLASSpecLearner subclasses
OptimisingSpecLearner and overrides exactly one method,
`find_adaptations_with_heuristic`, which is the seam where the learning task is
handed to the solver and the answer parsed back. The orchestrator, oracle,
mitigator, discriminator and encoder are all unaware which solver is in use.

Two things have to be bridged.

**The task syntax.** FastLAS 2.1.0 does not accept the ILASP dialect the encoder
emits, so `translate_ilasp_task_to_fastlas` rewrites it - see that function for
the specifics and for what FastLAS silently ignores.

**Multiple solutions.** FastLAS returns a single solution per run, where ILASP
returns every optimal one, and the BFS search needs a set of candidate
adaptations to branch on. `n_runs` therefore invokes FastLAS repeatedly and
collects the distinct solutions.

    FastLAS 2.1.0 *is* non-deterministic: given a hypothesis space with several
    equally-optimal candidates it returns different ones on different runs.
    (An earlier note here claimed the opposite. That was an artefact of a broken
    translation - the space was empty or held a single forced candidate, so
    every run trivially agreed.) The variance is stochastic, so a given batch of
    runs can still collapse to one answer; `n_runs` is how you sample the ties.
"""
import re
import subprocess
from typing import List, Optional, Tuple

from spec_repair.components.learners.optimising_final_spec_learner import OptimisingSpecLearner
from spec_repair.config import SETUP_DICT
from spec_repair.helpers.parsers.fastlas_interpreter import FastLASInterpreter
from spec_repair.interfaces.iheuristic_manager import IHeuristicManager
from spec_repair.components.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.model.adaptation_learned import Adaptation
from spec_repair.util.file_util import discard_temp_file, generate_temp_filename, write_to_file
from spec_repair.util.subprocess_util import create_cmd

# FastLAS keeps ILASP's recall bound and rejects only the (positive)/(negative)
# annotation ("syntax error, unexpected T_COMMA"). Confirmed against the FastLAS
# repo, which ships the same tasks in both dialects: the only difference between
# FastLAS2/data/agent/ilasp_tasks/X.las and .../fastnonopl_tasks/X.las is
#     #modeb(p(...), (positive)).  ->  #modeb(p(...)).
#     #modeb(p(...), (negative)).  ->  #modeb(not p(...)).
# with the recall untouched wherever it appeared.
_MODEB_POSITIVE = re.compile(r"#modeb\((\s*\d+\s*,\s*)?(.+?)\s*,\s*\(\s*positive\s*\)\s*\)\.")
_MODEB_NEGATIVE = re.compile(r"#modeb\((\s*\d+\s*,\s*)?(.+?)\s*,\s*\(\s*negative\s*\)\s*\)\.")
# FastLAS has no #constant directive - it errors with "Unknown token: '#'" - and
# instead draws const(t) values from a t/1 predicate in the background knowledge.
# Note the trailing `[ \t]*$` rather than `\s*$`: under re.MULTILINE a greedy
# `\s*` happily consumes the newline and matches `$` on a later line, which
# silently joined consecutive #constant lines together.
_CONSTANT = re.compile(r"^#constant\(\s*([^,]+?)\s*,\s*(.+?)\s*\)\.[ \t]*$", re.M)
# FastLAS requires an identifier as the first argument of an example.
_POS_NO_ID = re.compile(r"#pos\(\s*\{")

_BIAS_BLOCK = re.compile(r'#bias\("([\s\S]*?)"\)\.')
# Every var(T) appearing in a mode declaration.
_VAR_TYPE = re.compile(r"\bvar\(\s*(\w+)\s*\)")

# FastLAS grounds a var(T) placeholder from a T/1 predicate, and emits it into
# the learned rule as a type guard:
#     ... :- holds_at(highwater,V0,V1), time(V0), trace(V1).
# ILASP needs no such predicate - it types variables from the mode declarations
# alone - so the encoder never emits one. Without it FastLAS cannot build a
# single candidate rule: `SPACE SIZE: 0`, UNSATISFIABLE, and *no error*, which
# is indistinguishable from "this branch found no repair".
#
# `trace/1` already exists (each example's context asserts `trace(name).`) but
# `time/1` does not - the encoding uses `timepoint/2` throughout. That single
# omission made every ANTECEDENT_WEAKENING and CONSEQUENT_WEAKENING task
# unsolvable, while INVARIANT_TO_RESPONSE_WEAKENING worked because
# `#modeh(ev_temp_op(const(expression_v)))` carries no var() at all.
#
# The guards are harmless downstream: Adaptation.from_str reads only
# timepoint_of_op/holds_at/not_holds_at, so a guarded FastLAS rule and the
# equivalent ILASP rule parse to equal Adaptations.
_TYPE_DEFINITIONS = {
    "time": "time(T) :- timepoint(T,_).",
    "trace": None,  # asserted per-example in the context
}

DEFAULT_FASTLAS_ARGS = ("--nopl", "--force-safety")


class FastLASTypeError(RuntimeError):
    """Raised when a var(T) in the mode bias has no known T/1 definition."""


def _type_definitions_for(las: str) -> str:
    """
    A `T/1` definition for every `var(T)` in the mode declarations that the task
    does not already define. An unknown type raises rather than silently
    producing an empty hypothesis space.
    """
    needed = {t for line in las.splitlines() if line.lstrip().startswith("#mode")
              for t in _VAR_TYPE.findall(line)}
    unknown = needed - _TYPE_DEFINITIONS.keys()
    if unknown:
        raise FastLASTypeError(
            f"No FastLAS type definition for var({'), var('.join(sorted(unknown))}). "
            f"Add it to _TYPE_DEFINITIONS - without a T/1 predicate FastLAS builds "
            f"an empty hypothesis space and reports UNSATISFIABLE with no error.")
    lines = [_TYPE_DEFINITIONS[t] for t in sorted(needed)
             if _TYPE_DEFINITIONS[t] and not re.search(rf"^{t}\(", las, re.M)]
    if not lines:
        return ""
    return ("\n%% type predicates FastLAS needs to ground var(T) placeholders\n"
            + "\n".join(lines) + "\n")


def _translate_bias(las: str) -> str:
    """
    Rewrite ILASP's `#bias` block into FastLAS's meta-language.

    The two use different vocabularies for the same idea:

        ILASP    head(X)     body(X)
        FastLAS  in_head(X)  in_body(X)

    In FastLAS `body/1` is simply an undefined predicate, so an untranslated
    block is not *rejected*, it is **silently inert**: `:- body(X), ...` can
    never fire, and (worse) `:- not body(X)` always fires and makes the task
    instantly UNSATISFIABLE. Either way none of the encoder's constraints on
    rule shape are enforced, so FastLAS solves a visibly different problem -
    it returned `antecedent_exception(...) :- holds_at(highwater,...)` with no
    `timepoint_of_op` at all, which the bias exists to prevent.

    Two smaller fixes:

    * `:- constraint.` is dropped. `constraint` is ILASP's flag for "the learned
      rule is a constraint (empty head)". FastLAS only learns rules whose head
      comes from a `#modeh`, so there is nothing to forbid and the atom is
      undefined.
    * `==` becomes `=`; FastLAS's parser rejects `==` with
      "syntax error, unexpected T_EQUAL".
    """
    match = _BIAS_BLOCK.search(las)
    if not match:
        return las
    translated = []
    for line in match.group(1).splitlines():
        constraint = line.strip()
        if not constraint or constraint == ":- constraint.":
            continue
        constraint = re.sub(r"\bhead\(", "in_head(", constraint)
        constraint = re.sub(r"(?<!in_)\bbody\(", "in_body(", constraint)
        constraint = constraint.replace(" == ", " = ")
        translated.append(constraint)
    if not translated:
        return las[:match.start()] + las[match.end():]
    block = '#bias("\n' + "\n".join(translated) + '\n").'
    return las[:match.start()] + block + las[match.end():]


def translate_ilasp_task_to_fastlas(las: str) -> str:
    """
    Rewrite an ILASP learning task into the dialect FastLAS 2.1.0 accepts.

    Rewrites, each for a construct FastLAS rejects or reads differently:

    1. `#modeb(2, p(...), (positive)).` -> `#modeb(2, p(...)).` and
       `#modeb(2, p(...), (negative)).` -> `#modeb(2, not p(...)).`
       The recall bound is **kept** - only the annotation is rejected.
    2. `#constant(type, value).` -> `type(value).` as a background fact, which
       is where FastLAS looks for the values of a `const(type)` placeholder.
       Ranges survive this unchanged: `#constant(index,0..0).` becomes
       `index(0..0).`, still a valid clingo fact.
    3. `#pos({...},{...},{...}).` -> `#pos(eg1,{...},{...},{...}).`
    4. The `#bias` block is rewritten from ILASP's `head`/`body` vocabulary into
       FastLAS's `in_head`/`in_body` - see `_translate_bias`. Untranslated it is
       silently inert and FastLAS solves an unconstrained problem.

    Plus one *addition*: a `T/1` definition for every `var(T)` in the mode
    declarations, which FastLAS needs to ground them - see
    `_type_definitions_for`.

    With all of these in place FastLAS returns rules of the same shape as
    ILASP's, and `Adaptation.from_str` maps the two to equal Adaptations.
    FastLAS still returns *one* solution per run against ILASP's several, which
    is what `n_runs` samples.
    """
    las = _MODEB_POSITIVE.sub(lambda m: f"#modeb({m.group(1) or ''}{m.group(2)}).", las)
    las = _MODEB_NEGATIVE.sub(lambda m: f"#modeb({m.group(1) or ''}not {m.group(2)}).", las)
    las = _translate_bias(las)
    type_defs = _type_definitions_for(las)
    las = _CONSTANT.sub(r"\1(\2).", las)

    counter = [0]

    def _add_example_id(_match) -> str:
        counter[0] += 1
        return f"#pos(eg{counter[0]},{{"

    return _POS_NO_ID.sub(_add_example_id, las) + type_defs


class FastLASTaskError(RuntimeError):
    """Raised when FastLAS rejects the learning task itself."""


# FastLAS injects a type guard for every var(T) into the learned rule
# (`... :- holds_at(a,V0,V1), time(V0), trace(V1)`). They are an artefact of how
# it grounds var(), present in every rule, so constraining on them would exclude
# everything rather than one solution.
_TYPE_GUARD_RE = re.compile(r'^(?:' + '|'.join(_TYPE_DEFINITIONS) + r')\(')
# Split a rule body on commas that are not inside parentheses.
_BODY_SPLIT_RE = re.compile(r',\s*(?![^()]*\))')


def exclusion_constraint(rule: str) -> Optional[str]:
    """
    A `#bias` constraint forbidding the rule FastLAS just returned.

    This is what makes enumeration possible without relying on FastLAS picking
    differently between runs: block what has been found, ask again, repeat. It
    mirrors what ILASP's pylasp driver does by adding `:- nge_HYP(...)` for each
    hypothesis it has already reported.

    Only usable because the `#bias` block is translated into FastLAS's own
    meta-language (in_head/in_body). Against ILASP's `head`/`body` spelling the
    constraint is silently inert - which is why an earlier attempt at exclusion
    appeared to do nothing and the sampling approach was adopted instead.

    **Only the exact rule is blocked, never a superset of it.** A bare
    `:- in_head(h), in_body(a), in_body(b).` would forbid *any* rule whose body
    contains both `a` and `b`, so excluding

        antecedent_exception(...) :- not_holds_at(methane,...)

    would also silently exclude the genuinely different, more specific

        antecedent_exception(...) :- not_holds_at(methane,...), holds_at(highwater,...)

    which the search still needs to see. Pinning the body size with
    `#count{X : in_body(X)} = n` makes the constraint match that rule and no
    other - the same device pylasp uses for ILASP, where the alternative is
    spelled out as "if you want to allow non-subset-minimal solutions".

    The count excludes FastLAS's injected `time`/`trace` type guards: `in_body`
    ranges over the hypothesis-space literals, not the guards added when the
    rule is rendered (measured - a 2-literal body counts as 2, not 5).

    Returns None for a body-free fact (e.g. `ev_temp_op(a).`), which has no body
    literals to constrain on - there the head alone would block every rule with
    that head, which is far more than intended.
    """
    rule = rule.strip().rstrip('.')
    head, _, body = rule.partition(' :- ')
    if not body:
        return None
    literals = [lit.strip() for lit in _BODY_SPLIT_RE.split(body)]
    literals = [lit for lit in literals if lit and not _TYPE_GUARD_RE.match(lit)]
    if not literals:
        return None
    # The head is matched on its predicate only: the exception's own arguments
    # are the formula name and the time/trace variables, which are fixed for the
    # whole learning task and so carry no information about which solution this
    # is. What distinguishes solutions is the body.
    predicate = head.split('(')[0]
    arity = head.count(',') + 1 if '(' in head else 0
    head_pattern = f"{predicate}({','.join('_' * arity)})" if arity else predicate
    body_terms = ", ".join(f"in_body({lit})" for lit in literals)
    # The count is what keeps this from blocking supersets: without it the
    # constraint reads "never this head with at least these literals", with it
    # "never this head with exactly these literals".
    exact_size = f"#count{{X : in_body(X)}} = {len(literals)}"
    return f":- in_head({head_pattern}), {body_terms}, {exact_size}."


def with_exclusions(las: str, constraints: List[str]) -> str:
    """
    Add exclusion constraints to a task's `#bias` block.

    Appends to the existing block rather than adding a second one: FastLAS reads
    a `#bias` as a fragment of one meta-program, and the encoder always emits a
    block, so there is one to extend.
    """
    if not constraints:
        return las
    match = _BIAS_BLOCK.search(las)
    if not match:
        block = '#bias("\n' + "\n".join(constraints) + '\n").\n'
        return las + block
    body = match.group(1).rstrip("\n")
    new_block = '#bias("' + body + "\n" + "\n".join(constraints) + '\n").'
    return las[:match.start()] + new_block + las[match.end():]


def run_fastlas(las: str, extra_args: Tuple[str, ...] = DEFAULT_FASTLAS_ARGS) -> str:
    """
    Run FastLAS over an already-translated task and return its stdout.

    stderr is captured separately and turned into an exception rather than
    discarded. FastLAS reports a malformed task ("syntax error, unexpected
    T_COMMA", "Unknown token: '#'") on stderr and writes *nothing* to stdout, so
    ignoring it would make a translation bug indistinguishable from "this branch
    found no adaptations" - the search would quietly explore nothing and report
    no repair.
    """
    las_file = generate_temp_filename(ext=".las")
    write_to_file(las_file, las)
    cmd = create_cmd(["FastLAS", *extra_args, las_file])
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    stdout, stderr = stdout.decode("utf-8"), stderr.decode("utf-8")
    if stderr.strip() and not stdout.strip():
        # Deliberately not deleted: the message points at this file.
        raise FastLASTaskError(
            f"FastLAS rejected the learning task: {stderr.strip()}\nTask written to {las_file}")
    discard_temp_file(las_file)
    return stdout



def _append_unseen(adaptations: List[Tuple[int, List[Adaptation]]],
                   seen: set,
                   solutions: List[Tuple[int, List[Adaptation]]]) -> None:
    """
    Keep solutions not already recorded.

    Still deduplicated even though enumeration should not repeat itself: the
    exclusion constraint matches on the body literals, so two runs could in
    principle produce rules that differ only in something the constraint does
    not capture yet render to the same Adaptation - and a duplicate branch would
    make the search do the same work twice.
    """
    for score, solution in solutions:
        fingerprint = tuple(sorted(str(a) for a in solution))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        adaptations.append((score, solution))


def enumerate_solutions(
        fastlas_task: str,
        n_runs: int,
        fastlas_args: Tuple[str, ...] = DEFAULT_FASTLAS_ARGS,
        seed_constraints: Optional[List[str]] = None,
) -> List[Tuple[int, List[Adaptation]]]:
    """
    Enumerate up to `n_runs` distinct solutions of a FastLAS task.

    Enumerate rather than sample. FastLAS returns one solution per run, so the
    previous approach ran it n_runs times and kept whatever distinct answers
    turned up - which relied on it picking differently between runs, made the
    branching non-deterministic, and duplicated work whenever it did not. Here
    each solution found is added to the #bias as a constraint forbidding it, and
    the next run is asked for something else. When the task goes UNSATISFIABLE
    there is genuinely nothing left, so the loop stops early rather than burning
    the remaining runs, and `n_runs` is a ceiling rather than a cost.

    Only possible because the #bias is translated into FastLAS's own
    in_head/in_body meta-language; against ILASP's head/body spelling the
    constraints are silently ignored and every run returns the same answer.

    :param seed_constraints: exclusions to start from, as if already found.
        For testing what a given constraint does to the reachable space.
    """
    adaptations: List[Tuple[int, List[Adaptation]]] = []
    seen = set()
    constraints: List[str] = list(seed_constraints or [])

    for _ in range(n_runs):
        output = run_fastlas(with_exclusions(fastlas_task, constraints), fastlas_args)
        rules: Optional[List[str]] = FastLASInterpreter.extract_learned_rules(output)
        if rules is None:
            # UNSATISFIABLE, or nothing on stdout: no further solution exists
            # under the accumulated constraints.
            break
        solutions: Optional[List[Tuple[int, List[Adaptation]]]] = \
            FastLASInterpreter.extract_learned_possible_adaptations(output)
        if not solutions:
            break

        new_constraints = [c for c in (exclusion_constraint(r) for r in rules) if c]
        if not new_constraints:
            # A body-free fact cannot be excluded without blocking every rule
            # with that head, so asking again would only repeat it.
            _append_unseen(adaptations, seen, solutions)
            break
        constraints.extend(new_constraints)
        _append_unseen(adaptations, seen, solutions)
    return adaptations


class FastLASSpecLearner(OptimisingSpecLearner):
    """
    OptimisingSpecLearner with FastLAS as the solver.

    :param n_runs: ceiling on how many distinct solutions a learning step
        enumerates. FastLAS returns one solution per invocation, so the step
        runs it repeatedly, each time forbidding the solutions already found.
        This is a ceiling and not a count: once the constrained task goes
        UNSATISFIABLE the space is exhausted and the loop stops early, so a
        step with three solutions costs four invocations whatever n_runs says.
        The default of 1 matches FastLAS's own single-answer behaviour; the
        sweeps use 10, mirroring ILASP's MAX_ASP_HYPOTHESES.
    """

    def __init__(
            self,
            heuristic_manager: IHeuristicManager = NoFilterHeuristicManager(),
            n_runs: int = 1,
            fastlas_args: Tuple[str, ...] = DEFAULT_FASTLAS_ARGS,
    ):
        super().__init__(heuristic_manager=heuristic_manager)
        if n_runs < 1:
            raise ValueError(f"n_runs must be at least 1, got {n_runs}")
        self.n_runs = n_runs
        self.fastlas_args = tuple(fastlas_args)

    def find_adaptations_with_heuristic(self, spec, trace, cts, learning_type, violations, config):
        self.spec_encoder.set_learning_config(config)
        las: str = self.spec_encoder.encode_ILASP(spec, trace, cts, violations, learning_type)
        fastlas_task: str = translate_ilasp_task_to_fastlas(las)
        return enumerate_solutions(fastlas_task, self.n_runs, self.fastlas_args)
