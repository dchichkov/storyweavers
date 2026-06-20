#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/qrs_inner_monologue_animal_story.py
==================================================================

A standalone story world for a tiny animal tale with inner monologue.

Domain sketch:
- A small animal wants to solve a simple problem in a garden.
- A surprising clue with the seed word "qrs" makes the animal pause and think.
- A cautious helper helps turn worry into a calm plan.
- The ending shows a concrete change in the world: the animal uses the right
  tool, the small trouble is fixed, and the animal feels proud and safe.

The story style is intentionally child-facing and animal-story-like, with a
clear beginning, inner thoughts, a turn, and a gentle ending.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/qrs_inner_monologue_animal_story.py
    python storyworlds/worlds/gpt-5.4-mini/qrs_inner_monologue_animal_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/qrs_inner_monologue_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/qrs_inner_monologue_animal_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "female", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "male", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Setting:
    id: str
    place: str
    detail: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    label: str
    thing: str
    risk: str
    need: str
    spread: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    label: str
    text: str
    reveal: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Solution:
    id: str
    label: str
    action: str
    fix: str
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    setting: str
    animal: str
    helper: str
    problem: str
    clue: str
    solution: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "garden": Setting("garden", "the garden", "The garden was soft with grass and bright with daisies."),
    "orchard": Setting("orchard", "the orchard", "The orchard was full of apple trees and sleepy shade."),
    "pond": Setting("pond", "the pond", "The pond shimmered behind tall reeds and tiny ripples."),
}

ANIMALS = {
    "squirrel": {"type": "girl", "label": "squirrel", "name": "Pip"},
    "rabbit": {"type": "boy", "label": "rabbit", "name": "Bram"},
    "hedgehog": {"type": "girl", "label": "hedgehog", "name": "Mina"},
    "fox": {"type": "boy", "label": "fox", "name": "Toby"},
}

HELPERS = {
    "mole": {"type": "boy", "label": "mole", "name": "Milo"},
    "mouse": {"type": "girl", "label": "mouse", "name": "Nina"},
    "owl": {"type": "girl", "label": "owl", "name": "Wren"},
}

PROBLEMS = {
    "stuck_hole": Problem("stuck_hole", "the little hole", "a seed pouch", "stuck tight", "find a smooth stick", 2, {"seed", "hole"}),
    "snagged_cart": Problem("snagged_cart", "the snagged cart", "a berry cart", "caught on a root", "find a flat stone", 3, {"cart", "root"}),
    "tangled_string": Problem("tangled_string", "the tangled string", "a kite string", "all knotted up", "find a tiny comb", 2, {"string", "knot"}),
}

CLUES = {
    "qrs_note": Clue("qrs_note", "the note with qrs", "a little note that said qrs", "It felt like a puzzle, not a warning.", {"qrs", "note"}),
    "qrs_sticks": Clue("qrs_sticks", "the qrs sticks", "three sticks lined up as qrs", "Maybe qrs meant a shape to copy.", {"qrs", "sticks"}),
    "qrs_scrape": Clue("qrs_scrape", "the qrs scratch", "a scratch mark shaped like qrs", "Maybe qrs pointed to something hidden nearby.", {"qrs", "scratch"}),
}

SOLUTIONS = {
    "stick": Solution("stick", "a smooth stick", "carefully nudged it", "the little hole opened", 2, {"stick"}),
    "stone": Solution("stone", "a flat stone", "pried it loose", "the cart rolled free", 3, {"stone"}),
    "comb": Solution("comb", "a tiny comb", "worked the knots apart", "the string untangled", 2, {"comb"}),
}

ANIMAL_NAMES = ["Pip", "Bram", "Mina", "Toby", "Luna", "Otis", "Sage", "Mabel"]
HELPER_NAMES = ["Milo", "Nina", "Wren", "Benny", "Iris"]
TRAITS = ["curious", "careful", "brave", "gentle", "patient", "thoughtful"]


def problem_needs_solution(problem: Problem, solution: Solution) -> bool:
    return problem.id in {"stuck_hole", "snagged_cart", "tangled_string"} and solution.power >= 2


def sensible_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for sol in SOLUTIONS:
                if problem_needs_solution(PROBLEMS[p], SOLUTIONS[sol]):
                    out.append((s, p, sol))
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["blocked"] >= THRESHOLD:
            sig = ("relief", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["worry"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", "social", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def predict(world: World, problem: Problem) -> dict:
    sim = world.copy()
    sim.get("problem").meters["blocked"] += 1
    propagate(sim, narrate=False)
    return {"blocked": sim.get("problem").meters["blocked"] >= THRESHOLD}


def introduce(world: World, hero: Entity, setting: Setting) -> None:
    world.say(f"On a quiet morning, {hero.id} the {hero.label_word} wandered into {setting.place}.")
    world.say(setting.detail)


def inner_monologue(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} saw {clue.text}. "
        f"*{hero.id} thought, 'Hmm, qrs. That looks important. I should look carefully.'*"
    )


def fear_turn(world: World, hero: Entity, problem: Problem, clue: Clue) -> None:
    world.say(
        f"Near the {problem.label}, {hero.id} paused. *'{clue.reveal}'* "
        f"the {hero.id} thought. *'If I tug too hard, I might make it worse.'*"
    )


def ask_helper(world: World, hero: Entity, helper: Entity) -> None:
    world.say(f"{hero.id} looked up and called for {helper.id}.")
    world.say(f"*'{helper.id} always thinks before acting,'* {hero.id} told {pron(hero)} themself.")


def pron(ent: Entity) -> str:
    return ent.pronoun("subject")


def advise(world: World, helper: Entity, hero: Entity, problem: Problem, solution: Solution) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"{helper.id} listened and said, \"Let's use {solution.label}. "
        f"It should help without breaking anything.\""
    )
    world.say(
        f"*'{That_solution(solution)},'* {hero.id} thought. *'That sounds much safer than guessing.'*"
    )


def That_solution(solution: Solution) -> str:
    return solution.action


def solve(world: World, problem: Problem, solution: Solution) -> None:
    world.get("problem").meters["blocked"] = 0.0
    world.get("solution").meters["used"] = 1.0
    world.say(
        f"{solution.label.capitalize()} {solution.action}, and {problem.thing} {solution.fix}."
    )
    world.say(
        "The tight place was not tight anymore, and the small trouble turned into a small success."
    )


def ending(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    hero.memes["pride"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{hero.id} smiled at {helper.id}. "
        f"*'I thought carefully and found the right way,'* {hero.id} thought, warm and proud."
    )
    world.say(
        f"Together they sat in {setting.place} with the clue still tucked away, "
        f"and the day felt calm and bright."
    )


def tell(setting: Setting, animal: dict, helper: dict, problem: Problem, clue: Clue, solution: Solution) -> World:
    world = World()
    hero = world.add(Entity(id=animal["name"], kind="character", type=animal["type"], label=animal["label"], traits=["curious"]))
    h = world.add(Entity(id=helper["name"], kind="character", type=helper["type"], label=helper["label"], traits=["helpful"]))
    world.add(Entity(id="problem", type="thing", label=problem.label))
    world.add(Entity(id="solution", type="thing", label=solution.label))
    world.facts.update(setting=setting, animal=animal, helper=helper, problem=problem, clue=clue, solution=solution)

    introduce(world, hero, setting)
    world.para()
    inner_monologue(world, hero, clue)
    fear_turn(world, hero, problem, clue)
    if predict(world, problem)["blocked"]:
        ask_helper(world, hero, h)
        world.para()
        advise(world, h, hero, problem, solution)
        solve(world, problem, solution)
        world.para()
        ending(world, hero, h, setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a young child that includes the word "qrs" and shows the character thinking to themself.',
        f"Tell a gentle story about a {f['animal']['label']} named {f['animal']['name']} who notices qrs, thinks about what it might mean, and gets help.",
        f"Write a short story with inner monologue where qrs leads an animal friend to solve a small problem calmly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["animal"]["name"]
    h = f["helper"]["name"]
    p = f["problem"].label
    sol = f["solution"].label
    return [
        ("Who is the story about?", f"It is about {a}, a small {f['animal']['label']} who wanted to solve a tiny problem. {h} also helped when the worry got bigger."),
        ("What did the animal think about qrs?", f"{a} thought qrs looked important and wanted to look carefully. That inner thought helped {a} stay calm instead of rushing."),
        (f"How did {a} fix the problem?", f"{a} used {sol} with help from {h}, and the {p} was no longer stuck. The small trouble changed into a safe and solved one."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does it mean to think to yourself?", "Thinking to yourself means having a quiet thought in your own mind without saying it out loud. Stories often show that as an inner monologue."),
        ("Why is it good to ask for help?", "Asking for help can keep a small problem from becoming a bigger one. A helper may know a safer or smarter way to fix things."),
        ("What can careful thinking do?", "Careful thinking helps you notice clues, avoid mistakes, and choose a safe plan. That often makes the ending happier."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "squirrel", "mouse", "stuck_hole", "qrs_note", "stick"),
    StoryParams("orchard", "rabbit", "owl", "snagged_cart", "qrs_sticks", "stone"),
    StoryParams("pond", "hedgehog", "mole", "tangled_string", "qrs_scrape", "comb"),
]


def explain_rejection(problem: Problem, solution: Solution) -> str:
    return f"(No story: {solution.label} does not fit this problem well enough. Pick a problem-solution pair that can truly solve the trouble.)"


def valid_combos() -> list[tuple[str, str, str]]:
    return sensible_combos()


ASP_RULES = r"""
problem_ok(S, P, Sol) :- setting(S), problem(P), solution(Sol).
valid(S, P, Sol) :- problem(P), solution(Sol), can_solve(P, Sol), setting(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("spread", pid, p.spread))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
    for sid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("power", sid, s.power))
        if s.power >= 2:
            lines.append(asp.fact("can_solve", sid, sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP gate and Python gate differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, animal=None, helper=None, problem=None, clue=None, solution=None, seed=None), random.Random(1)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"FAIL: generate() smoke test crashed: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story with inner monologue and a qrs clue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--solution", choices=SOLUTIONS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, solution = rng.choice(sorted(combos))
    animal = args.animal or rng.choice(sorted(ANIMALS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    clue = args.clue or rng.choice(sorted(CLUES))
    return StoryParams(setting, animal, helper, problem, clue, solution)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ANIMALS[params.animal], HELPERS[params.helper], PROBLEMS[params.problem], CLUES[params.clue], SOLUTIONS[params.solution])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
