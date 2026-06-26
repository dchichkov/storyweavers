#!/usr/bin/env python3
"""
A small storyworld: a space-adventure mystery at the pond.

Premise:
- A child explorer and a tiny robot visit a pond that feels like a quiet moon.
- Something electronic is missing or acting strange.
- A curious sprout near the water turns out to be the clue that solves the mystery.

The world is intentionally tiny and constraint-checked:
- It only generates a few plausible story variants.
- The mystery must have an honest solution grounded in the simulated world.
- The ending proves the change in state: the problem is found, fixed, and the pond is calm again.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    found_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the pond"
    style: str = "space adventure"
    affords: set[str] = field(default_factory=lambda: {"investigate", "scan", "search"})


@dataclass
class Clue:
    label: str
    phrase: str
    kind: str


@dataclass
class Mystery:
    title: str
    missing: str
    cause: str
    solved_by: str
    clue: str
    clue_kind: str = "sprout"
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _r_find_tool(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.entities.get("hero")
    tool = world.entities.get("scanner")
    clue = world.entities.get("sprout")
    if not seeker or not tool or not clue:
        return out
    if seeker.memes.get("curious", 0) < THRESHOLD:
        return out
    if world.facts.get("tool_found"):
        return out
    if clue.meters.get("glow", 0) >= THRESHOLD:
        world.facts["tool_found"] = True
        tool.carried_by = seeker.id
        out.append("The electronic scanner hummed back to life.")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("tool_found"):
        return out
    if world.facts.get("solved"):
        return out
    clue = world.entities.get("sprout")
    missing = world.entities.get("beacon")
    hero = world.entities.get("hero")
    if not clue or not missing or not hero:
        return out
    if clue.found_by == hero.id and missing.meters.get("fixed", 0) < THRESHOLD:
        missing.meters["fixed"] = 1
        world.facts["solved"] = True
        out.append("The mystery was solved.")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for fn in (_r_find_tool, _r_solve):
            sents = fn(world)
            if sents:
                changed = True
                if narrate:
                    for s in sents:
                        world.say(s)


SETTINGS = {
    "pond": Setting(place="the pond", style="space adventure", affords={"investigate", "scan", "search"}),
}

MYSTERIES = {
    "glow": Mystery(
        title="the glowing pond mystery",
        missing="a tiny electronic beacon",
        cause="it had slipped under a lily pad and blinked in the water",
        solved_by="the sprout pointing to the beacon",
        clue="sprout",
        clue_kind="sprout",
        tags={"sprout", "electronic", "pond"},
    ),
    "signal": Mystery(
        title="the silent signal mystery",
        missing="a little electronic radio",
        cause="it had fallen beside the reeds and turned itself off",
        solved_by="the sprout growing next to the radio",
        clue="sprout",
        clue_kind="sprout",
        tags={"sprout", "electronic", "pond"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Ada", "Nia", "Zoe"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Max", "Noah"]
TRAITS = ["curious", "brave", "gentle", "careful", "bright"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [("pond", mid) for mid in MYSTERIES]


def asp_facts() -> str:
    import asp

    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("style", sid, s.style.replace(" ", "_")))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing.replace(" ", "_")))
        lines.append(asp.fact("clue_kind", mid, m.clue_kind))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M) :- setting(S), mystery(M), tag(M,pond), tag(M,sprout), tag(M,electronic).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure pond mystery storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos() if (args.place is None or c[0] == args.place) and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, trait=trait)


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name))
    robot = world.add(Entity(id="robot", kind="character", type="thing", label="a tiny robot"))
    beacon = world.add(Entity(id="beacon", kind="thing", type="thing", label="electronic beacon", phrase="a tiny electronic beacon", owner=hero.id))
    scanner = world.add(Entity(id="scanner", kind="thing", type="thing", label="scanner", phrase="a small electronic scanner", owner=hero.id))
    sprout = world.add(Entity(id="sprout", kind="thing", type="thing", label="sprout", phrase="a bright green sprout"))
    mystery = MYSTERIES[params.mystery]

    world.facts.update(hero=hero, robot=robot, beacon=beacon, scanner=scanner, sprout=sprout, mystery=mystery)
    hero.memes["curious"] = 1
    robot.memes["helpful"] = 1

    world.say(f"{params.name} was a {params.trait} little explorer who loved space adventures.")
    world.say(f"One quiet day, {params.name} and a tiny robot went to {world.setting.place} to solve {mystery.title}.")
    world.para()
    world.say(f"They were looking for {mystery.missing}, because the water station had gone silent.")
    world.say(f"{params.name} held up a small electronic scanner, but it only gave a weak beep.")
    world.para()
    world.say(f"Then they noticed {mystery.clue} by the water. It looked like a little green antenna in the pond light.")
    sprout.meters["glow"] = 1
    sprout.found_by = hero.id
    beacon.meters["hidden"] = 1
    if params.mystery == "glow":
        beacon.meters["under_lily_pad"] = 1
    else:
        beacon.meters["beside_reeds"] = 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"{params.name} followed the sprout and found {mystery.missing} where it had been hiding.")
    world.say(f"The electronic beacon started blinking again, and the pond felt calm and bright, like a safe little moon base.")
    propagate(world, narrate=True)
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a child that takes place at a pond and includes the word "{f["mystery"].clue}".',
        f"Tell a gentle mystery where {f['hero'].label} and a tiny robot search for an electronic beacon at the pond.",
        "Write a simple story about a sprout helping solve a mystery in space style by the water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"Who went to the pond to solve the mystery?",
            answer=f"{hero.label} went to the pond with a tiny robot to solve the mystery.",
        ),
        QAItem(
            question=f"What electronic thing were they looking for?",
            answer=f"They were looking for {mystery.missing}.",
        ),
        QAItem(
            question=f"What clue helped them find the missing thing?",
            answer=f"The bright green sprout was the clue that led them to the missing electronic beacon.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The missing electronic beacon was found and started blinking again, so the pond felt calm and solved.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sprout?",
            answer="A sprout is a tiny new plant just beginning to grow out of the ground.",
        ),
        QAItem(
            question="What does electronic mean?",
            answer="Electronic means something uses electricity to work, like a scanner, light, or beacon.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or problem that people try to figure out by looking for clues.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], ""]
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.found_by:
            bits.append(f"found_by={e.found_by}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {e.label or e.type} {' '.join(bits)}")
    lines.append(f"  facts: {world.facts.get('solved', False)=}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(setting="pond", mystery="glow", name="Mina", gender="girl", trait="curious"),
    StoryParams(setting="pond", mystery="signal", name="Theo", gender="boy", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combo(s):")
        for combo in combos:
            print(" ", combo)
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
