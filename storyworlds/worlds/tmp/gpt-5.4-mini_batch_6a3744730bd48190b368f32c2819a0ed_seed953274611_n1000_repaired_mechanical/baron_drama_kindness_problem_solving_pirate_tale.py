#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/baron_drama_kindness_problem_solving_pirate_tale.py
====================================================================================

A tiny pirate-tale storyworld about a baron, a burst of drama, and a kind,
problem-solving turn that makes the ending feel safe and bright.

The world is intentionally small and classical: a child-friendly pirate scene,
a proud baron with a fussy treasure room, a helpful crewmate, a broken puzzle,
and a choice between grumbling and kindness.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    scene: str
    dark_spot: str
    style: str
    level: str = "deck"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Problem:
    id: str
    label: str
    source: str
    breakable: bool
    mess: str
    danger: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class KindAct:
    id: str
    label: str
    method: str
    result: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Fix:
    id: str
    label: str
    method: str
    result: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    place: str
    problem: str
    kindness: str
    fix: str
    baron_name: str
    baron_gender: str
    helper_name: str
    helper_gender: str
    captain_name: str
    captain_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_drama(world: World) -> list[str]:
    out: list[str] = []
    baron = world.entities["baron"]
    problem = world.entities["problem"]
    if problem.meters["broken"] < THRESHOLD or ("drama", "rise") in world.fired:
        return out
    world.fired.add(("drama", "rise"))
    baron.memes["worry"] += 1
    baron.memes["drama"] += 1
    out.append("__drama__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities["helper"]
    if helper.memes["kindness"] < THRESHOLD or ("kindness", "soften") in world.fired:
        return out
    world.fired.add(("kindness", "soften"))
    world.entities["baron"].memes["hope"] += 1
    out.append("__kindness__")
    return out


RULES = [Rule("drama", _r_drama), Rule("kindness", _r_kindness)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def break_problem(world: World, problem: Entity) -> None:
    problem.meters["broken"] += 1
    problem.meters["mess"] += 1
    propagate(world, narrate=False)


def fix_problem(world: World, fix: Fix, problem: Entity) -> None:
    problem.meters["broken"] = 0
    problem.meters["mess"] = 0
    world.get("baron").memes["relief"] += 1
    world.get("helper").memes["joy"] += 1
    world.say(f"With a calm breath, the crew {fix.method}.")


def setup(world: World, place: Place, problem: Problem, kindness: KindAct, fix: Fix) -> None:
    baron = world.add(Entity(id="baron", kind="character", type="man", label="the baron", role="owner"))
    helper = world.add(Entity(id="helper", kind="character", type="girl", label="the deckhand", role="helper"))
    captain = world.add(Entity(id="captain", kind="character", type="man", label="the captain", role="captain"))
    treasure = world.add(Entity(id="problem", kind="thing", type="thing", label=problem.label, role="problem"))
    baron.memes["pride"] += 1
    helper.memes["kindness"] = 1.0
    world.facts.update(place=place, problem=problem, kindness=kindness, fix=fix)
    world.say(
        f"On a bright pirate morning, the baron stood on the {place.level} of "
        f"his ship, where {place.scene}. {place.style}"
    )
    world.say(
        f'Inside the little treasure room, {problem.source}. '
        f'The baron liked everything neat, so a tiny bit of drama felt huge.'
    )
    world.say(
        f'"If the {problem.label} stays broken, the whole map hunt stops," '
        f'said the baron.'
    )
    world.para()
    world.say(
        f'The deckhand watched the trouble and showed kindness first: '
        f'{kindness.method}.'
    )
    world.say(
        f'The captain nodded and helped them think: {fix.label} was the best fix.'
    )
    return None


def tell(place: Place, problem: Problem, kindness: KindAct, fix: Fix) -> World:
    world = World()
    setup(world, place, problem, kindness, fix)
    helper = world.get("helper")
    baron = world.get("baron")
    treasure = world.get("problem")

    world.para()
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.id.capitalize()} spoke gently to the baron and said, "
        f'"We can solve this together."'
    )
    world.say(
        f"The baron frowned at first, because the {problem.label} had turned into "
        f"a big piece of drama."
    )
    break_problem(world, treasure)
    if treasure.meters["broken"] >= THRESHOLD:
        world.say(
            f"The broken {problem.label} made the room feel noisy and tense."
        )
    world.para()
    fix_problem(world, fix, treasure)
    world.say(
        f"The baron thanked the deckhand, and the captain tied the final knot."
    )
    world.para()
    world.say(
        f"In the end, the {problem.label} was whole again, the drama was gone, "
        f"and the pirate crew sailed on with a kinder plan."
    )
    baron.memes["joy"] += 1
    helper.memes["joy"] += 1
    captain.memes["joy"] += 1
    world.facts.update(outcome="fixed")
    return world


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES:
        for pr in PROBLEMS.values():
            for ka in KIND_ACTS.values():
                for fx in FIXES.values():
                    if pr.breakable and fx.power >= pr.danger and ka.id == "kind":
                        combos.append((p.id, pr.id, ka.id, fx.id))
    return combos


def explain_rejection(problem: Problem, fix: Fix) -> str:
    return (
        f"(No story: the {problem.label} needs a real fix, but {fix.label} is too weak. "
        f"Choose a stronger problem-solving plan.)"
    )


def explain_kindness(kindness_id: str) -> str:
    return f"(No story: unknown kindness move '{kindness_id}'.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    problem: Problem = f["problem"]
    kindness: KindAct = f["kindness"]
    fix: Fix = f["fix"]
    return [
        f'Write a pirate story that includes the words "baron" and "drama" and shows kindness on the {place.scene}.',
        f"Tell a child-friendly pirate tale where the baron faces drama because {problem.label} is broken, and the crew solves it kindly.",
        f"Write a short story about a baron on a pirate ship who uses kindness and problem solving to fix {problem.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    problem: Problem = f["problem"]
    fix: Fix = f["fix"]
    return [
        ("Who is the story about?",
         "It is about a baron, a kind deckhand, and a captain on a pirate ship."),
        ("Why was there drama?",
         f"There was drama because the {problem.label} broke and the baron worried the map hunt would stop. The broken thing made the room feel tense until the crew worked together."),
        ("How did they fix it?",
         f"They used a calm problem-solving plan and {fix.method}. That kind choice made the broken {problem.label} whole again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is kindness?",
         "Kindness means helping with a gentle heart, especially when someone is upset."),
        ("What is problem solving?",
         "Problem solving means thinking carefully and choosing a good way to fix trouble."),
        ("What is a pirate crew?",
         "A pirate crew is a group of people who travel and work together on a ship."),
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


PLACES = [
    Place(id="deck", scene="the deck shone like a sea-shell", dark_spot="the shadow under the sail", style="The ropes swayed gently in the wind."),
    Place(id="hold", scene="the hold smelled like salt and wood", dark_spot="the back corner by the lantern", style="The crew had been sorting shiny maps all morning."),
]

PROBLEMS = {
    "map_case": Problem(id="map_case", label="map case", source="the map case slipped and snapped open", breakable=True, mess="papers", danger=2, tags={"map", "drama"}),
    "compass": Problem(id="compass", label="compass", source="the compass lid had come loose", breakable=True, mess="pieces", danger=3, tags={"compass", "drama"}),
}

KIND_ACTS = {
    "kind": KindAct(id="kind", label="kindness", method="the deckhand listened and stayed gentle", result="the room felt calmer", tags={"kindness"}),
}

FIXES = {
    "tape": Fix(id="tape", label="a careful tape fix", method="they taped the flap down and lined the pieces up", result="the map hunt could continue", power=2, sense=2, tags={"problem_solving"}),
    "knot": Fix(id="knot", label="a clever knot fix", method="they tied the cord tight and tucked the pieces safely inside", result="the compass stayed closed", power=3, sense=3, tags={"problem_solving"}),
}

CURATED = [
    StoryParams(place="deck", problem="map_case", kindness="kind", fix="tape",
                baron_name="baron", baron_gender="man", helper_name="deckhand", helper_gender="girl",
                captain_name="captain", captain_gender="man"),
    StoryParams(place="hold", problem="compass", kindness="kind", fix="knot",
                baron_name="baron", baron_gender="man", helper_name="crewmate", helper_gender="girl",
                captain_name="captain", captain_gender="man"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.kindness and args.kindness != "kind":
        raise StoryError(explain_kindness(args.kindness))
    if args.fix and args.problem:
        pr = PROBLEMS[args.problem]
        fx = FIXES[args.fix]
        if fx.power < pr.danger:
            raise StoryError(explain_rejection(pr, fx))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.kindness is None or c[2] == args.kindness)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, problem_id, kind_id, fix_id = rng.choice(sorted(combos))
    name_pool = ["baron"]
    return StoryParams(
        place=place_id,
        problem=problem_id,
        kindness=kind_id,
        fix=fix_id,
        baron_name="baron",
        baron_gender="man",
        helper_name=rng.choice(["deckhand", "mate", "crewmate"]),
        helper_gender="girl",
        captain_name="captain",
        captain_gender="man",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in {p.id for p in PLACES}:
        raise StoryError("Unknown place.")
    if params.problem not in PROBLEMS or params.kindness not in KIND_ACTS or params.fix not in FIXES:
        raise StoryError("Unknown story parameter.")
    world = tell(next(p for p in PLACES if p.id == params.place),
                 PROBLEMS[params.problem], KIND_ACTS[params.kindness], FIXES[params.fix])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale storyworld about baron, drama, kindness, and problem solving.")
    ap.add_argument("--place", choices=[p.id for p in PLACES])
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--kindness", choices=KIND_ACTS)
    ap.add_argument("--fix", choices=FIXES)
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


ASP_RULES = r"""
valid(P, Pr, K, F) :- place(P), problem(Pr), kindness(K), fix(F), breakable(Pr), power(F, Pow), danger(Pr, D), Pow >= D, K = kind.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p.id))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("breakable", pid))
        lines.append(asp.fact("danger", pid, pr.danger))
    for kid in KIND_ACTS:
        lines.append(asp.fact("kindness", kid))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, fx.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate/emit smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p.id, pr.id, "kind", fx.id) for p in PLACES for pr in PROBLEMS.values() for fx in FIXES.values() if pr.breakable and fx.power >= pr.danger]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ".join(map(str, row)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
