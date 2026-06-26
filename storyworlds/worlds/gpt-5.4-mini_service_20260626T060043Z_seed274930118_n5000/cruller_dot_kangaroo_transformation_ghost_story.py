#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cruller_dot_kangaroo_transformation_ghost_story.py
=============================================================================================================

A small, standalone story world for a gentle ghost story about a child named
Dot, a cruller, and a kangaroo-shaped transformation.

Seed premise:
---
Late one foggy evening, Dot found a warm cruller on the kitchen table and
heard a soft thump-thump at the window. A shy kangaroo ghost had come to
visit. Dot wanted to use the cruller to make a spooky treat for the ghost,
but the grown-up in the room worried the pastry would be ruined if the magic
worked too fast. With a careful plan, the cruller was transformed into a
kangaroo-shaped snack, and the little ghost bounced away happy.

World model:
---
    child = Dot
    setting = moonlit kitchen / bakery nook
    prize = cruller
    visitor = kangaroo ghost
    tension = an unsafe, rushed transformation might spoil the cruller
    resolution = a careful transformation with a simple helper tool

This script follows the Storyworld contract:
- self-contained stdlib script
- typed entities with meters and memes
- eager import of results, lazy import of asp
- parser, resolution, generation, emit, main
- ASP twin and verification
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    indoor: bool = True
    mood: str = "foggy"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    protects_from: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.visitor: Optional[Entity] = None

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _default_meters() -> dict[str, float]:
    return {"mess": 0.0, "soiled": 0.0, "workload": 0.0, "wonder": 0.0}


def _default_memes() -> dict[str, float]:
    return {"joy": 0.0, "fear": 0.0, "curiosity": 0.0, "tension": 0.0, "relief": 0.0}


def _say_spooky(world: World, sentence: str) -> None:
    world.say(sentence)


def _transform(world: World, actor: Entity, prize: Entity, tool: Optional[Tool], careful: bool, narrate: bool = True) -> None:
    sig = ("transform", prize.id, careful)
    if sig in world.fired:
        return
    world.fired.add(sig)
    if careful:
        prize.meters["soiled"] = 0.0
        actor.memes["relief"] += 1
        if tool:
            actor.memes["joy"] += 1
        if narrate:
            world.say(f"With a careful touch, the cruller changed shape without losing its sweet smell.")
    else:
        prize.meters["soiled"] += 1
        actor.memes["tension"] += 1
        if narrate:
            world.say(f"The magic rushed too hard, and the cruller came out messy and sad.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, tool_cfg: Tool,
         name: str = "Dot", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=hero_type,
        traits=["little", "curious", "spooky-minded"],
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the grown-up",
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    prize = world.add(Entity(
        id="cruller",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        meters={"soiled": 0.0},
        memes={"glow": 0.0},
    ))
    visitor = world.add(Entity(
        id="KangarooGhost",
        kind="character",
        type="kangaroo",
        label="a kangaroo ghost",
        traits=["shy", "gentle", "bouncy"],
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    world.visitor = visitor

    # Act 1: the spooky setup.
    _say_spooky(world, f"Dot was a little curious {hero_type} who liked quiet nights and strange visitors.")
    _say_spooky(world, f"On the table sat {hero.pronoun('possessive')} {prize.label}, warm and golden, like a small promise.")
    _say_spooky(world, f"Then a soft thump-thump came at the window, and a shy kangaroo ghost peered in with moon-white eyes.")
    _say_spooky(world, f"Dot loved the idea of making a {prize.label} fit for a ghost, especially one with hopping feet.")

    world.para()

    # Act 2: the warning and the worry.
    _say_spooky(world, f"{hero.id} wanted to {activity.verb}, but {parent.label_word if hasattr(parent, 'label_word') else 'the grown-up'} shook a head.")
    _say_spooky(world, f'"If we rush the spell, your {prize.label} will get {activity.soil}," the grown-up said.')
    _say_spooky(world, f"Dot still tried to {activity.rush}, and the room grew tighter with worry.")
    hero.memes["curiosity"] += 1
    hero.memes["fear"] += 1
    parent.memes["tension"] += 1

    # The unsafe attempt is only for contrast; the story chooses the careful path.
    prize.meters["soiled"] = 1.0
    parent.meters["workload"] += 1

    world.para()

    # Act 3: the compromise and transformation.
    _say_spooky(world, f"Then Dot noticed {tool_cfg.label}, sitting nearby like a little star in the dark.")
    _say_spooky(world, f"{tool_cfg.prep.capitalize()}, the grown-up said, and the kangaroo ghost nodded from the window.")
    prize.meters["soiled"] = 0.0
    _transform(world, hero, prize, tool_cfg, careful=True, narrate=True)
    hero.memes["joy"] += 1
    parent.memes["relief"] += 1
    visitor.memes["joy"] += 1

    _say_spooky(world, f"At last, {tool_cfg.tail}, and the {prize.label} became a neat kangaroo-shaped treat.")
    _say_spooky(world, f"The ghost took one happy sniff, then bounced away through the fog with a polite little wave.")
    _say_spooky(world, f"Dot watched the moon through the glass, smiling at the empty plate and the happy, hopping night.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        tool=tool_cfg,
        visitor=visitor,
        transformed=True,
        careful=True,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the moonlit kitchen", indoor=True, mood="foggy", affords={"transform"}),
    "bakery": Setting(place="the old bakery", indoor=True, mood="ghostly", affords={"transform"}),
    "porch": Setting(place="the porch", indoor=False, mood="misty", affords={"transform"}),
}

ACTIVITIES = {
    "transform": Activity(
        id="transform",
        verb="transform the cruller",
        gerund="transforming the cruller",
        rush="spin the spell too fast",
        mess="twisted",
        soil="twisted up",
        keyword="transform",
        tags={"transform", "ghost", "kangaroo", "cruller"},
    )
}

PRIZES = {
    "cruller": Prize(
        label="cruller",
        phrase="a sugar-dusted cruller",
        type="pastry",
        genders={"girl", "boy"},
    )
}

TOOLS = [
    Tool(
        id="dot",
        label="a tiny dot-shaped cutter",
        prep="the tiny dot-shaped cutter was just right for a careful spell",
        tail="the little cutter traced a neat curve",
        guards={"twisted"},
        protects_from={"rushed"},
    ),
    Tool(
        id="lantern",
        label="a paper lantern",
        prep="the paper lantern glowed softly beside the plate",
        tail="the lantern light made the edges easy to see",
        guards={"twisted"},
        protects_from={"dark"},
    ),
]

GIRL_NAMES = ["Dot", "Mia", "Nora", "Lily", "Ava"]
BOY_NAMES = ["Ben", "Theo", "Leo", "Max", "Sam"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    tool: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                for tool in TOOLS:
                    combos.append((place, act_id, prize_id, tool.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world about Dot, a cruller, and a kangaroo ghost.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.tool is None or c[3] == args.tool)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize, tool = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, prize=prize, tool=tool, name=name, gender=gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short ghost story for young children that includes a cruller, a dot, and a kangaroo ghost.",
        f"Tell a cozy spooky story about {f['hero'].id} meeting a kangaroo ghost and carefully transforming a cruller.",
        f"Write a gentle transformation story where a {f['prize'].label} changes shape without becoming a mess.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    visitor = f["visitor"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little curious child who met a kangaroo ghost.",
        ),
        QAItem(
            question=f"What was {hero.id} trying to do with the {prize.label}?",
            answer=f"{hero.id} wanted to transform the {prize.label} into a spooky snack for the kangaroo ghost.",
        ),
        QAItem(
            question=f"Why did the grown-up worry?",
            answer=f"The grown-up worried that if the spell moved too fast, the {prize.label} would get twisted up.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The {prize.label} was transformed carefully into a kangaroo-shaped treat, and the ghost left happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cruller?",
            answer="A cruller is a sweet, twisted pastry that is often glazed or dusted with sugar.",
        ),
        QAItem(
            question="What is a dot?",
            answer="A dot is a tiny round mark, like a small circle or a little spot.",
        ),
        QAItem(
            question="What is a kangaroo?",
            answer="A kangaroo is an animal with strong back legs and a pouch, and it can hop very fast.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
valid(P,A,R,T) :- setting(P), affords(P,A), prize(R), tool(T).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        next(t for t in TOOLS if t.id == params.tool),
        name=params.name,
        hero_type=params.gender,
        parent_type=params.parent,
    )
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        params = [
            StoryParams(place="kitchen", activity="transform", prize="cruller", tool="dot", name="Dot", gender="girl", parent="mother"),
            StoryParams(place="bakery", activity="transform", prize="cruller", tool="lantern", name="Dot", gender="girl", parent="mother"),
        ]
        samples = [generate(p) for p in params]
    else:
        seen: set[str] = set()
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
