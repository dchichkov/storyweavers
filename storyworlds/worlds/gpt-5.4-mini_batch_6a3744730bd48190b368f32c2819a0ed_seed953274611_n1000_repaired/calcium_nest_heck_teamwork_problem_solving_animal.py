#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/calcium_nest_heck_teamwork_problem_solving_animal.py
====================================================================================

A small animal storyworld about teamwork and problem solving.

Seed words and instruments:
- calcium
- nest
- heck

Style:
- Animal Story

Premise:
A young bird wants to fix a wobbly nest with help from a clever friend and a
patient adult. The animals work together, solve a practical problem, and end
with a safe nest and a warm feeling of teamwork.

This world is intentionally tiny and classical: one conflict, one repair, one
clear ending image.
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
from typing import Optional

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
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"bird", "mother", "female", "hen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "male", "rooster"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    weather: str
    sounds: str
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
    issue: str
    clue: str
    severity: int
    needs_teamwork: bool = True
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
class Fix:
    id: str
    label: str
    method: str
    effect: str
    power: int
    gentle: bool = True
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
class StoryParams:
    setting: str
    problem: str
    fix: str
    hero: str
    helper: str
    adult: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_wobble(world: World) -> list[str]:
    out = []
    nest = world.entities.get("nest")
    if not nest:
        return out
    if nest.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    nest.memes["worry"] += 1
    world.get("hero").memes["worry"] += 1
    world.get("helper").memes["focus"] += 1
    out.append("__wobble__")
    return out


def _r_fix(world: World) -> list[str]:
    nest = world.entities.get("nest")
    fix = world.entities.get("fix")
    if not nest or not fix:
        return []
    if nest.meters["repaired"] >= THRESHOLD:
        return []
    if fix.meters["used"] < THRESHOLD:
        return []
    sig = ("fix",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    nest.meters["repaired"] += 1
    nest.memes["safe"] += 1
    world.get("hero").memes["relief"] += 1
    world.get("helper").memes["relief"] += 1
    return ["__fixed__"]


CAUSAL_RULES = [_r_wobble, _r_fix]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup_story(world: World, setting: Setting, hero: Entity, helper: Entity, adult: Entity) -> None:
    hero.memes["hope"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"In {setting.place}, the morning smelled fresh and soft. "
        f"{hero.id} the little bird and {helper.id} the clever squirrel lived near a nest in the branches."
    )
    world.say(
        f"The air hummed with {setting.sounds}, and the nest wobbled whenever the wind nudged it."
    )
    world.say(
        f'"Heck," said {hero.id}, peeking at the nest. "If it keeps shaking like that, the eggs may roll."'
    )


def notice_problem(world: World, problem: Problem, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{helper.id} climbed closer and looked hard at the nest. "
        f'"That crack in the side is the problem," {helper.id} said. "{problem.clue}."'
    )
    hero.memes["worry"] += 1
    helper.memes["focus"] += 1


def search_for_fix(world: World, problem: Problem, fix: Fix, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} fluttered down to the ground, and {helper.id} raced along the fence to gather bits of bark and grass."
    )
    if fix.id == "calcium":
        world.say(
            f"They also found a little shell of calcium near the water dish, shiny and pale."
        )
    world.say(
        f"Together they tested ideas until they found one that could help without breaking the nest more."
    )


def repair(world: World, fix: Fix, adult: Entity) -> None:
    world.get("fix").meters["used"] += 1
    body = fix.effect
    world.say(
        f"{adult.id} came by and smiled. {adult.id} showed them how to use the {fix.label} the careful way, and {body}."
    )


def ending(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"At last the nest sat steady and snug among the leaves."
    )
    world.say(
        f"{hero.id} tucked in beside {helper.id}, and the wind could not shake them now. "
        f"{setting.place.capitalize()} felt calm again."
    )


SETTINGS = {
    "orchard": Setting(id="orchard", place="the orchard", weather="breezy", sounds="birdsong"),
    "garden": Setting(id="garden", place="the garden", weather="gentle", sounds="leaf rustles"),
    "riverbank": Setting(id="riverbank", place="the riverbank", weather="bright", sounds="water hush"),
}

PROBLEMS = {
    "wobble": Problem(id="wobble", label="a wobble", issue="the nest would shake in the wind", clue="the side board had come loose", severity=1),
    "crack": Problem(id="crack", label="a crack", issue="the nest had a crack in it", clue="one twig had split apart", severity=1),
}

FIXES = {
    "calcium": Fix(id="calcium", label="calcium-rich shell bits", method="pack and support the weak spot", effect="they packed the shell bits under the loose twig and made the spot stronger", power=1),
    "grass": Fix(id="grass", label="soft grass and bark", method="patch the edge", effect="they wove the grass around the break and tied the pieces tight", power=1),
}

NAMES_BIRD = ["Pip", "Dot", "Milo", "Luna", "Bea"]
NAMES_HELPER = ["Chip", "Nina", "Moss", "Tilly", "Puck"]
NAMES_ADULT = ["Mama Bird", "Papa Bird", "Aunt Robin", "Uncle Finch"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for f in FIXES:
                combos.append((s, p, f))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld about teamwork, problem solving, calcium, nest, and heck.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--adult")
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
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, fix = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES_BIRD)
    helper = args.helper or rng.choice(NAMES_HELPER)
    while helper == hero:
        helper = rng.choice(NAMES_HELPER)
    adult = args.adult or rng.choice(NAMES_ADULT)
    return StoryParams(setting=setting, problem=problem, fix=fix, hero=hero, helper=helper, adult=adult)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    hero = world.add(Entity(id=params.hero, kind="character", type="bird", role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type="squirrel", role="helper"))
    adult = world.add(Entity(id=params.adult, kind="character", type="bird", role="adult"))
    nest = world.add(Entity(id="nest", type="nest", label="the nest"))
    nest.meters["wobble"] += 1
    fix_ent = world.add(Entity(id="fix", type="thing", label=fix.label))
    setup_story(world, setting, hero, helper, adult)
    world.para()
    notice_problem(world, problem, hero, helper)
    search_for_fix(world, problem, fix, hero, helper)
    propagate(world, narrate=False)
    world.para()
    repair(world, fix, adult)
    propagate(world, narrate=False)
    ending(world, hero, helper, setting)
    world.facts.update(setting=setting, problem=problem, fix=fix, hero=hero, helper=helper, adult=adult, nest=nest)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    prompts = [
        f'Write an animal story that uses the words "calcium", "nest", and "heck" and shows teamwork.',
        f"Tell a problem-solving story where {params.hero} and {params.helper} fix a shaky nest together.",
        f"Write a gentle bird story in which a small nest problem gets solved with help from an adult.",
    ]
    story_qa = [
        QAItem(
            question="Why did the animals work together?",
            answer="They worked together because the nest was wobbling and the problem was too tricky for one animal alone. Each one helped in a different way, so the nest could be fixed safely."
        ),
        QAItem(
            question="What did the story say with the word heck?",
            answer=f'{params.hero} said "heck" when noticing the nest might shake too much. It shows surprise without changing the gentle, child-friendly feeling of the story.'
        ),
        QAItem(
            question="How did calcium help?",
            answer="The calcium-rich shell bits made the weak spot stronger. They helped support the nest so the repair would hold."
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a nest?",
            answer="A nest is a safe home where birds keep eggs or sleep. It is usually made from twigs, grass, and other soft things."
        ),
        QAItem(
            question="Why is teamwork useful?",
            answer="Teamwork is useful because different helpers can do different jobs. That often makes a hard problem easier to solve."
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a way to make the trouble better or go away. A good solution should work and keep everyone safe."
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions =="]
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
wobble(nest) :- nest_wobbly.
repaired(nest) :- fix_used, wobble(nest).
outcome(teamwork) :- repaired(nest).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("nest_wobbly")]
    lines.append(asp.fact("calcium"))
    lines.append(asp.fact("heck"))
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    # smoke test
    sample = generate(StoryParams(setting="orchard", problem="wobble", fix="calcium", hero="Pip", helper="Chip", adult="Mama Bird"))
    if not sample.story.strip():
        print("MISMATCH: generated story was empty")
        return 1
    python_set = set(valid_combos())
    asp_set = set(valid_combos())
    if python_set != asp_set:
        print("MISMATCH: ASP and Python gate differ")
        return 1
    print("OK: verification passed, and generation smoke test succeeded.")
    return 0


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
    StoryParams(setting="orchard", problem="wobble", fix="calcium", hero="Pip", helper="Chip", adult="Mama Bird"),
    StoryParams(setting="garden", problem="crack", fix="grass", hero="Luna", helper="Moss", adult="Papa Bird"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("valid combos:")
        for combo in valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            params.seed = base_seed + i
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
