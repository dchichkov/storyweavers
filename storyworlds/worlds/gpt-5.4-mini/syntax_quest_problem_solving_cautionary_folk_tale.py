#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/syntax_quest_problem_solving_cautionary_folk_tale.py
====================================================================================

A tiny folk-tale storyworld about a child on a quest for a lost word, a syntax
mix-up, and a careful fix. The domain is built from the seed word "syntax" and
the requested features: Quest, Problem Solving, Cautionary, Folk Tale.

The world simulates:
- a seeker traveling through a small folk-tale setting,
- a syntax problem that blocks the quest,
- a cautious helper or elder warning about a risky shortcut,
- a problem-solving turn that repairs the syntax,
- a resolution image showing the quest outcome.

The story stays concrete and state-driven: physical meters track travel, damage,
and repair; emotional memes track worry, patience, courage, and relief.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CAUTIOUS_TRAITS = {"careful", "cautious", "wise", "gentle", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    path: str
    quest_goal: str
    dark_spot: str
    ending_image: str


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    where: str
    risky_use: str
    safe_use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SyntaxProblem:
    id: str
    label: str
    symptom: str
    caution_text: str
    fix_text: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["blocked"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for char in world.entities.values():
            if char.kind == "character":
                char.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["repaired"] < THRESHOLD:
            continue
        sig = ("relief", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for char in world.entities.values():
            if char.kind == "character":
                char.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("worry", "emotional", _r_worry),
    Rule("relief", "emotional", _r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def syntax_is_risky(item: QuestItem, problem: SyntaxProblem) -> bool:
    return "syntax" in item.tags and problem.severity >= 1


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= 2]


def best_solution() -> Solution:
    return max(SOLUTIONS.values(), key=lambda s: s.sense)


def can_fix(solution: Solution, problem: SyntaxProblem) -> bool:
    return solution.power >= problem.severity


def cautious_warning(world: World, helper: Entity, seeker: Entity, item: QuestItem,
                     problem: SyntaxProblem) -> None:
    helper.memes["caution"] += 1
    world.say(
        f'{helper.id} frowned and said, "{problem.caution_text} '
        f'{item.label} can tangle the quest if it is used the wrong way."'
    )
    if "wise" in helper.traits or helper.memes["caution"] >= 2:
        world.say(f"{helper.id} spoke softly, like an elder in a winter tale.")


def risky_shortcut(world: World, seeker: Entity, item: QuestItem, problem: SyntaxProblem) -> None:
    seeker.memes["impulse"] += 1
    world.say(
        f"{seeker.id} ignored the warning and tried the quick path with {item.label}."
    )
    world.say(
        f"But the words twisted; the quest speech lost its syntax and would not sit right."
    )


def solve(world: World, helper: Entity, seeker: Entity, item: QuestItem,
          problem: SyntaxProblem, solution: Solution) -> None:
    world.get("roadblock").meters["repaired"] += 1
    world.say(
        f"{helper.id} took a breath and used a better answer: {solution.text}."
    )
    world.say(
        f"Slowly, the broken words straightened. The syntax held again, and {item.label} became useful."
    )


def fail_solve(world: World, helper: Entity, seeker: Entity, item: QuestItem,
               problem: SyntaxProblem, solution: Solution) -> None:
    world.get("roadblock").meters["blocked"] += 1
    world.say(f"{helper.id} tried, but {solution.fail}.")
    world.say(
        f"The quest stayed tangled, and the little party had to stop before the path got worse."
    )


def ending(world: World, seeker: Entity, helper: Entity, item: QuestItem, problem: SyntaxProblem) -> None:
    world.say(
        f"In the end, {seeker.id} carried {item.phrase} across {world.setting.place}, "
        f"and {world.setting.ending_image}."
    )
    world.say(
        f"{helper.id} walked beside {seeker.id}, glad that caution and patience had won the day."
    )


def tale(world: World, seeker: Entity, helper: Entity, item: QuestItem, problem: SyntaxProblem,
         solution: Solution, outcome: str) -> None:
    world.say(
        f"Once in {world.setting.place}, {seeker.id} set out on a small quest through {world.setting.scene}."
    )
    world.say(
        f"{seeker.id} hoped to reach {world.setting.quest_goal}, but the path near {world.setting.dark_spot} was not simple."
    )
    world.para()
    world.say(
        f"{item.label} was meant to help, yet {problem.symptom}."
    )
    cautious_warning(world, helper, seeker, item, problem)
    risky_shortcut(world, seeker, item, problem)
    world.para()
    if outcome == "fixed":
        solve(world, helper, seeker, item, problem, solution)
        world.para()
        ending(world, seeker, helper, item, problem)
    else:
        fail_solve(world, helper, seeker, item, problem, solution)
        world.para()
        world.say(
            f"Their quest ended early, but the tale taught that a hasty syntax fix can make a small trouble grow."
        )


def outcome_of(params: "StoryParams") -> str:
    if params.problem not in PROBLEMS or params.item not in ITEMS or params.solution not in SOLUTIONS:
        return "?"
    return "fixed" if can_fix(SOLUTIONS[params.solution], PROBLEMS[params.problem]) else "stopped"


@dataclass
class StoryParams:
    setting: str
    item: str
    problem: str
    solution: str
    seeker: str
    seeker_type: str
    helper: str
    helper_type: str
    helper_trait: str
    seed: Optional[int] = None


SETTINGS = {
    "forest": Setting("forest", "the forest path", "pines, moss, and a whispering stream", "the rooty track", "the silver gate", "the hollow stump", "the gate of moonlit bark"),
    "village": Setting("village", "the village lane", "stone cottages, garden walls, and a baker's bell", "the narrow lane", "the painted arch", "the crooked signpost", "the market lanterns"),
    "hill": Setting("hill", "the hill road", "windy grass, bright clouds, and a fox's trail", "the steep road", "the far lookout", "the goat-stone", "the sunset over the hill"),
}

ITEMS = {
    "rhyme_book": QuestItem("rhyme_book", "the rhyme book", "a little rhyme book", "in a satchel", "read it too fast", "turn its pages carefully", {"syntax", "quest"}),
    "map_scroll": QuestItem("map_scroll", "the map scroll", "a rolled map scroll", "under a ribbon", "unroll it at once", "unroll it slowly", {"syntax", "quest"}),
    "key_charm": QuestItem("key_charm", "the key charm", "a brass key charm", "on a string", "use it like a shortcut", "use it as a guide", {"syntax", "quest"}),
}

PROBLEMS = {
    "mixed_order": SyntaxProblem("mixed_order", "mixed order", "the steps were out of order", "That shortcut can muddle the steps", "Put the steps back in the right order", 2, {"syntax", "caution"}),
    "broken_rule": SyntaxProblem("broken_rule", "broken rule", "one line broke the old rule of the quest", "A broken rule can trip the whole tale", "Check the rule and mend it slowly", 3, {"syntax", "caution"}),
    "missing_end": SyntaxProblem("missing_end", "missing ending", "the spell had no ending mark", "A missing ending can make the words drift away", "Add a proper ending and read again", 1, {"syntax", "caution"}),
}

SOLUTIONS = {
    "sort_steps": Solution("sort_steps", "sort the steps", 3, 3, "sorted the steps and laid them in the right order", "sorted the steps, but the tangle was too deep", "sorted the steps into a right order", {"syntax", "problem_solving"}),
    "mend_rule": Solution("mend_rule", "mend the rule", 3, 4, "mended the rule with a careful mark and a steady hand", "mended the rule, but not soon enough", "mended the rule with a careful mark", {"syntax", "problem_solving"}),
    "add_ending": Solution("add_ending", "add an ending mark", 2, 2, "added a proper ending mark and read the line once more", "added an ending mark, but it still wobbled", "added a proper ending mark", {"syntax", "problem_solving"}),
}

GIRL_NAMES = ["Mira", "Nina", "Lina", "Sera", "Tala", "Ira"]
BOY_NAMES = ["Oren", "Pavel", "Daro", "Kian", "Jori", "Milo"]
TRAITS = ["careful", "cautious", "wise", "gentle", "thoughtful", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for iid in ITEMS:
            for pid in PROBLEMS:
                if syntax_is_risky(ITEMS[iid], PROBLEMS[pid]):
                    for sol in sensible_solutions():
                        if can_fix(sol, PROBLEMS[pid]):
                            combos.append((sid, iid, pid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale quest story that includes the word "syntax" and ends with a careful solution.',
        f"Tell a cautionary tale where {f['seeker'].id} finds {f['item'].label} and must repair the syntax problem with help from {f['helper'].id}.",
        f'Write a short quest story for a child where a broken syntax pattern is fixed by patient problem solving.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    item = f["item"]
    problem = f["problem"]
    solution = f["solution"]
    outcome = f["outcome"]
    answers = [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {seeker.id} going on a little quest and trying to mend a syntax problem. {helper.id} helped by warning about a risky shortcut and showing a slower, safer way."
        ),
        QAItem(
            question=f"Why did {helper.id} warn {seeker.id}?",
            answer=f"{helper.id} warned {seeker.id} because {problem.symptom}. A quick shortcut could make the quest speech fall apart instead of helping it."
        ),
    ]
    if outcome == "fixed":
        answers.append(QAItem(
            question="How was the problem solved?",
            answer=f"They solved it by {solution.qa_text}. That careful fix let the syntax hold steady so the quest could continue."
        ))
        answers.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with {seeker.id} carrying {item.phrase} safely through the land. The old trouble was repaired, and the ending image showed the quest finished in a calm, folk-tale way."
        ))
    else:
        answers.append(QAItem(
            question="What happened when the fix did not work?",
            answer=f"The repair was too weak for the trouble, so the path stayed blocked. The tale ended early to show that hurrying a syntax fix can leave the whole quest stuck."
        ))
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is syntax?",
            answer="Syntax is the order that words or steps need to follow so they make sense together. If the order breaks, the message can become confusing."
        ),
        QAItem(
            question="Why is it wise to be cautious on a quest?",
            answer="Caution helps a traveler notice danger before it grows. A careful choice can save time and keep a small problem from becoming a bigger one."
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means looking at what is wrong and choosing a good way to fix it. Often that means slowing down, checking the pieces, and using the right tool."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(setting: Setting, item: QuestItem, problem: SyntaxProblem, solution: Solution,
         seeker_name: str, seeker_type: str, helper_name: str, helper_type: str,
         helper_trait: str, outcome: str) -> World:
    world = World(setting)
    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_type, role="seeker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper",
                              traits=[helper_trait]))
    roadblock = world.add(Entity(id="roadblock", label="the roadblock"))
    world.facts.update(seeker=seeker, helper=helper, item=item, problem=problem, solution=solution, outcome=outcome)

    seeker.memes["hope"] += 1
    helper.memes["caution"] += 1

    world.say(f"Once in {setting.place}, {seeker.id} began a small quest through {setting.scene}.")
    world.say(f"{seeker.id} hoped to reach {setting.quest_goal}, carrying {item.phrase} like a lucky charm.")
    world.para()
    world.say(f"Then a trouble arose: {problem.symptom}.")
    cautious_warning(world, helper, seeker, item, problem)
    risky_shortcut(world, seeker, item, problem)
    world.para()
    if outcome == "fixed":
        solve(world, helper, seeker, item, problem, solution)
        ending_line = f"In the end, {seeker.id} crossed the path with the syntax mended and the quest made whole."
        roadblock.meters["repaired"] += 1
    else:
        fail_solve(world, helper, seeker, item, problem, solution)
        ending_line = f"In the end, the quest remained blocked, and {seeker.id} learned to slow down before trying again."
        roadblock.meters["blocked"] += 1
    world.para()
    world.say(ending_line)
    world.say(f"The last sight was {setting.ending_image}, a quiet proof that caution had matters in hand.")
    propagate(world, narrate=False)
    return world


def outcome_is_fixed(problem: SyntaxProblem, solution: Solution) -> bool:
    return solution.power >= problem.severity


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for t in sorted(item.tags):
            lines.append(asp.fact("item_tag", iid, t))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("severity", pid, p.severity))
    for sid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("sense", sid, s.sense))
        lines.append(asp.fact("power", sid, s.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
risky(Item, Prob) :- item_tag(Item, syntax), problem(Prob), severity(Prob, S), S >= 1.
sensible(Sol) :- solution(Sol), sense(Sol, X), sense_min(M), X >= M.
fixable(Prob) :- problem(Prob), severity(Prob, S), power(Sol, P), sensible(Sol), P >= S.
valid(Setting, Item, Prob) :- setting(Setting), item(Item), risky(Item, Prob), fixable(Prob).
outcome(fixed) :- problem(Prob), solution(Sol), power(Sol, P), severity(Prob, S), P >= S.
outcome(stopped) :- problem(Prob), solution(Sol), power(Sol, P), severity(Prob, S), P < S.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("problem", params.problem),
        asp.fact("solution", params.solution),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = [CURATED[0]]
    rng = random.Random(777)
    for _ in range(10):
        try:
            args = argparse.Namespace(setting=None, item=None, problem=None, solution=None,
                                     seeker=None, seeker_type=None, helper=None,
                                     helper_type=None, helper_trait=None)
            params = resolve_params(args, rng)
            cases.append(params)
        except Exception:
            continue
    for p in CURATED:
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        assert sample.world is not None
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale quest about syntax, caution, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--seeker")
    ap.add_argument("--seeker-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy", "mother", "father"])
    ap.add_argument("--helper-trait", choices=sorted(CAUTIOUS_TRAITS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_pair(name: Optional[str], pool: list[str], rng: random.Random) -> str:
    return name or rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.solution and args.problem and not outcome_is_fixed(PROBLEMS[args.problem], SOLUTIONS[args.solution]):
        raise StoryError("That solution is too weak for the chosen syntax problem.")
    if args.item and args.problem and not syntax_is_risky(ITEMS[args.item], PROBLEMS[args.problem]):
        raise StoryError("That item would not create a real syntax trouble.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, problem = rng.choice(sorted(combos))
    solution = args.solution or rng.choice(sorted(s.id for s in sensible_solutions() if can_fix(s, PROBLEMS[problem])))
    seeker_type = args.seeker_type or rng.choice(["girl", "boy"])
    seeker = args.seeker or rng.choice(GIRL_NAMES if seeker_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["girl", "boy", "mother", "father"])
    helper = args.helper or rng.choice(GIRL_NAMES if helper_type == "girl" else BOY_NAMES)
    helper_trait = args.helper_trait or rng.choice(sorted(CAUTIOUS_TRAITS))
    return StoryParams(setting, item, problem, solution, seeker, seeker_type, helper, helper_type, helper_trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    item = ITEMS[params.item]
    problem = PROBLEMS[params.problem]
    solution = SOLUTIONS[params.solution]
    world = tell(setting, item, problem, solution, params.seeker, params.seeker_type,
                 params.helper, params.helper_type, params.helper_trait,
                 "fixed" if outcome_is_fixed(problem, solution) else "stopped")
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("forest", "rhyme_book", "mixed_order", "sort_steps", "Mira", "girl", "Oren", "boy", "careful"),
    StoryParams("village", "map_scroll", "broken_rule", "mend_rule", "Kian", "boy", "Tala", "girl", "wise"),
    StoryParams("hill", "key_charm", "missing_end", "add_ending", "Lina", "girl", "Milo", "boy", "thoughtful"),
]


def explain_rejection(item: QuestItem, problem: SyntaxProblem) -> str:
    return f"(No story: {item.label} would not make a true syntax problem with {problem.label}.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.seeker}: {p.item} + {p.problem} ({p.solution})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
