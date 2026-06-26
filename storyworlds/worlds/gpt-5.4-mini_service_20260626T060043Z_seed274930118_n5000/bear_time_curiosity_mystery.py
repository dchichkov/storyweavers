#!/usr/bin/env python3
"""
storyworlds/worlds/bear_time_curiosity_mystery.py
==================================================

A small mystery storyworld about a curious bear, a strange clock, and the way
time can seem to hide before it reveals itself again.

The seed image for this world is a child-facing mystery:
a bear notices that the time feels wrong, follows small clues, and discovers a
simple reason for the delay. The story stays close to mystery style: a quiet
setup, a puzzling middle, a careful turn, and a calm ending image that proves
what changed.

The world is intentionally small and constraint-checked. It models a few typed
entities, physical meters, and emotional memes. Story prose is driven by state:
the bear's curiosity rises, the mystery deepens, clues change the plan, and the
resolution settles the bear's worry.
"""

from __future__ import annotations

import argparse
import copy
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def __post_init__(self) -> None:
        for k in ("wait", "hint", "clockwork", "time", "dust"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "calm", "relief", "fear"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "bear":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    question: str
    answer: str
    clue: str
    sign: str
    site: str
    fix: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "cabin": Setting(place="the quiet cabin", mood="soft", affords={"clock"}),
    "forest": Setting(place="the pine forest", mood="shadowy", affords={"track"}),
    "museum": Setting(place="the little museum", mood="hushed", affords={"clock"}),
    "shop": Setting(place="the clock shop", mood="bright", affords={"clock"}),
}

MYSTERIES = {
    "stopped_clock": Mystery(
        id="stopped_clock",
        label="the stopped clock",
        question="why time felt stuck",
        answer="the clock needed a careful wind",
        clue="a tiny brass key",
        sign="the second hand had frozen",
        site="clock",
        fix="winding the little key",
        tags={"time", "clock"},
    ),
    "late_chime": Mystery(
        id="late_chime",
        label="the late chime",
        question="why the bell came late",
        answer="a loose string had tangled the bell pull",
        clue="a thin string on the floor",
        sign="the bell stayed silent",
        site="clock",
        fix="untying the string",
        tags={"time", "bell"},
    ),
    "missing_shadow": Mystery(
        id="missing_shadow",
        label="the missing shadow",
        question="where the shadow went at noon",
        answer="the sun had moved to the other side of the room",
        clue="a bright patch on the floor",
        sign="the shadow had slipped away",
        site="sun",
        fix="waiting for the light to turn",
        tags={"time", "sun"},
    ),
}

PLACES = ["cabin", "forest", "museum", "shop"]
HELPERS = ["friend", "grandparent", "ranger", "librarian"]
BEAR_NAMES = ["Milo", "Mira", "Nina", "Tobi", "Bram", "Luna"]
BEAR_TRAITS = ["curious", "gentle", "careful", "quiet", "brave"]


class ReasonGate:
    @staticmethod
    def valid_combo(place: str, mystery: str) -> bool:
        m = MYSTERIES[mystery]
        return m.site in SETTINGS[place].affords

    @staticmethod
    def explain_invalid(place: str, mystery: str) -> str:
        m = MYSTERIES[mystery]
        return (
            f"(No story: {m.label} does not fit {SETTINGS[place].place}. "
            f"Try a place that naturally supports {m.site} clues.)"
        )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a curious bear, a time mystery, and a calm answer."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = [
        (p, m)
        for p in PLACES
        for m in MYSTERIES
        if ReasonGate.valid_combo(p, m)
        and (args.place is None or args.place == p)
        and (args.mystery is None or args.mystery == m)
    ]
    if args.place and args.mystery and not ReasonGate.valid_combo(args.place, args.mystery):
        raise StoryError(ReasonGate.explain_invalid(args.place, args.mystery))
    if not combos:
        raise StoryError("(No valid story combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        mystery=mystery,
        name=args.name or rng.choice(BEAR_NAMES),
        helper=args.helper or rng.choice(HELPERS),
    )


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    bear = world.add(Entity(
        id=params.name,
        kind="character",
        type="bear",
        label="bear",
        meters={"wait": 0.0, "hint": 0.0, "clockwork": 0.0, "time": 0.0, "dust": 0.0},
        memes={"curiosity": 1.5, "worry": 0.0, "calm": 0.0, "relief": 0.0, "fear": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=params.helper,
        meters={"wait": 0.0, "hint": 0.0, "clockwork": 0.0, "time": 0.0, "dust": 0.0},
        memes={"curiosity": 0.5, "worry": 0.0, "calm": 0.0, "relief": 0.0, "fear": 0.0},
    ))
    clock = world.add(Entity(
        id="clock",
        type="clock",
        label="old clock",
        phrase="an old brass clock",
        owner=params.place,
        meters={"wait": 0.0, "hint": 0.0, "clockwork": 0.0, "time": 0.0, "dust": 1.0},
    ))
    clue = world.add(Entity(
        id="clue",
        type="clue",
        label=mystery.clue,
        phrase=mystery.clue,
        meters={"wait": 0.0, "hint": 1.0, "clockwork": 0.0, "time": 0.0, "dust": 0.0},
    ))

    world.facts.update(bear=bear, helper=helper, clock=clock, clue=clue, mystery=mystery, params=params)
    return world


def setup(world: World) -> None:
    b = world.facts["bear"]
    m: Mystery = world.facts["mystery"]
    world.say(f"{b.id} was a curious little bear who noticed little changes right away.")
    world.say(f"One day, {b.id} went to {world.setting.place}, where everything felt quiet and a little mysterious.")
    world.say(f"{b.id} loved to ask questions, and today {b.pronoun('subject')} was wondering about {m.question}.")
    world.say(f"Near the clock, {m.sign}.")


def investigate(world: World) -> None:
    b = world.facts["bear"]
    helper = world.facts["helper"]
    m: Mystery = world.facts["mystery"]
    clock = world.facts["clock"]
    clue = world.facts["clue"]

    world.para()
    b.memes["curiosity"] += 1.0
    b.meters["hint"] += 1.0
    world.say(f"{b.id} leaned closer and listened, because {b.pronoun('subject')} wanted to understand the hush.")
    world.say(f"{b.id} found {clue.label} and showed it to the {helper.label}.")
    helper.memes["curiosity"] += 0.5
    helper.meters["hint"] += 1.0
    world.say(f"The {helper.label} looked at the clue and said it might explain the strange timing.")
    if m.id == "stopped_clock":
        clock.meters["clockwork"] += 1.0
        b.meters["time"] += 1.0
        world.say(f"{b.id} noticed the clock was still and saw that the little key slot was empty.")
    elif m.id == "late_chime":
        clock.meters["wait"] += 1.0
        world.say(f"{b.id} spotted a thin string near the floor and followed it with careful eyes.")
    else:
        clock.meters["time"] += 1.0
        world.say(f"{b.id} stared at the bright patch on the floor and began to understand the light had moved.")


def turn_and_resolve(world: World) -> None:
    b = world.facts["bear"]
    helper = world.facts["helper"]
    m: Mystery = world.facts["mystery"]
    clock = world.facts["clock"]

    world.para()
    b.memes["worry"] += 0.5
    world.say(f"For a moment, {b.id} felt unsure, because mysteries can seem larger than a small paw.")
    if m.id == "stopped_clock":
        world.say(f"Then the {helper.label} found {m.fix}, and {b.id} helped turn it gently.")
        clock.meters["clockwork"] += 1.0
        b.memes["relief"] += 1.0
        b.memes["worry"] = 0.0
        world.say(f"The clock woke up with a soft tick, and the room felt like it had found its breath again.")
    elif m.id == "late_chime":
        world.say(f"Then the {helper.label} knelt down and untied the string, just as {b.id} had hoped.")
        clock.meters["wait"] += 1.0
        b.memes["relief"] += 1.0
        b.memes["worry"] = 0.0
        world.say(f"The bell gave a clear little ring, and the quiet corner no longer felt puzzled.")
    else:
        world.say(f"Then {b.id} and the {helper.label} simply waited, because the sun was the real clock.")
        clock.meters["time"] += 1.0
        b.memes["relief"] += 1.0
        b.memes["worry"] = 0.0
        world.say(f"When the light shifted, the shadow returned, and the answer was plain and kind.")


def build_story(params: StoryParams) -> World:
    world = make_world(params)
    setup(world)
    investigate(world)
    turn_and_resolve(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    m: Mystery = world.facts["mystery"]
    return [
        f"Write a short mystery story for young children about a curious bear named {p.name} and {m.label}.",
        f"Tell a gentle story in which a bear uses curiosity to solve {m.question} at {world.setting.place}.",
        f"Write a child-friendly mystery that includes a bear, a clue, and a calm answer about time.",
    ]


def story_qa(world: World) -> list[QAItem]:
    b = world.facts["bear"]
    helper = world.facts["helper"]
    m: Mystery = world.facts["mystery"]
    p: StoryParams = world.facts["params"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {b.id}, a curious little bear, and the {helper.label} who helped {b.id} think things through.",
        ),
        QAItem(
            question=f"What mystery did {b.id} want to solve at {world.setting.place}?",
            answer=f"{b.id} wanted to solve {m.question}. {m.sign.capitalize()}, so the place felt puzzling until the clue made sense.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {m.answer}. By the end, {b.id} felt calm and relieved, and the {helper.label} was close by.",
        ),
        QAItem(
            question=f"Why was {b.id} able to keep looking instead of giving up?",
            answer=f"{b.id} kept looking because curiosity was strong in the bear's heart, and the clue suggested the mystery had a simple answer.",
        ),
        QAItem(
            question=f"What part of the setting made the mystery feel believable?",
            answer=f"The story took place in {world.setting.place}, a quiet place where a small time mystery could seem very important.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    m: Mystery = world.facts["mystery"]
    out = [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to ask questions, look closely, and find out how something works.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a little bit of information that helps you figure out a mystery.",
        ),
    ]
    if "time" in m.tags:
        out.append(QAItem(
            question="What does a clock do?",
            answer="A clock helps people know the time by ticking, chiming, or showing the numbers on its face.",
        ))
    return out


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        for m in MYSTERIES.values():
            if m.site in SETTINGS[p].affords:
                lines.append(asp.fact("affords", p, m.site))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("site", mid, m.site))
        lines.append(asp.fact("tags", mid, *sorted(m.tags)) if False else "")
    return "\n".join(l for l in lines if l)


ASP_RULES = r"""
valid(Place,Mystery) :- affords(Place,Site), site(Mystery,Site).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str]]:
    return sorted((p, m) for p in PLACES for m in MYSTERIES if ReasonGate.valid_combo(p, m))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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
    StoryParams(place="shop", mystery="stopped_clock", name="Milo", helper="friend"),
    StoryParams(place="museum", mystery="late_chime", name="Mira", helper="librarian"),
    StoryParams(place="cabin", mystery="missing_shadow", name="Bram", helper="grandparent"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible story combos:\n")
        for place, mystery in combos:
            print(f"  {place:8} {mystery}")
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
