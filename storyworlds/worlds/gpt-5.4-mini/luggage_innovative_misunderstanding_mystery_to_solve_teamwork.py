#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/luggage_innovative_misunderstanding_mystery_to_solve_teamwork.py
===================================================================================================

A standalone storyworld for a small animal-story domain: curious animals at a
train station, an odd piece of luggage, a misunderstanding, a mystery to solve,
and a teamwork ending. The world is built from a simulated state, not a frozen
template paragraph.

The seed words are "luggage" and "innovative". The story style is child-facing,
concrete, and animal-centered, with a complete beginning, middle turn, and
ending image that proves what changed.
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
        if self.type in {"cat", "tomcat", "lion", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"dog", "fox", "rabbit", "girl", "mouse"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Setting:
    id: str
    place: str
    weather: str
    detail: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Luggage:
    id: str
    label: str
    color: str
    clue: str
    secret: str
    can_open: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Misunderstanding:
    id: str
    mistaken_meaning: str
    true_meaning: str
    reaction: str
    clue_action: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    innovative: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        return clone


@dataclass
@dataclass
class StoryParams:
    setting: str
    animal1: str
    animal2: str
    luggage: str
    misunderstanding: str
    tool: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    "station": Setting("station", "the train station", "windy", "benches and bright signs"),
    "forest_stop": Setting("forest_stop", "the forest station", "misty", "tall pines and a tiny platform"),
    "harbor": Setting("harbor", "the harbor pier", "salt-bright", "ropes and seagulls"),
}

ANIMALS = {
    "fox": ("fox", "curious", "quick paws"),
    "rabbit": ("rabbit", "gentle", "long ears"),
    "bear": ("bear", "kind", "soft steps"),
    "mouse": ("mouse", "tiny", "bright eyes"),
    "otter": ("otter", "playful", "wet whiskers"),
}

LUGGAGE = {
    "red_case": Luggage("red_case", "red luggage", "red", "a paper tag that read 'Milo' ", "it belonged to a lost passenger", tags={"luggage"}),
    "blue_bag": Luggage("blue_bag", "blue luggage", "blue", "a little sticker of a star", "it held a lost violin bow", tags={"luggage"}),
    "green_trunk": Luggage("green_trunk", "green luggage", "green", "a shiny lock", "it held a picnic basket and a note", tags={"luggage"}),
}

MISUNDERSTANDINGS = {
    "lost": Misunderstanding("lost", "it was lost", "it was waiting for its owner", "worried everyone", "look closely at the clues", tags={"mystery", "misunderstanding"}),
    "secret": Misunderstanding("secret", "it was a secret prize", "it was a helpful delivery", "made the animals whisper", "ask the station helper", tags={"mystery", "misunderstanding"}),
    "trap": Misunderstanding("trap", "it was a trap", "it was only a stuck latch", "made them tiptoe backward", "test it with a gentle tug", tags={"mystery", "misunderstanding"}),
}

TOOLS = {
    "tag_reader": Tool("tag_reader", "a tag reader", "an innovative tag reader", "read tiny tags from far away", True, tags={"innovative"}),
    "wheel_cart": Tool("wheel_cart", "a wheel cart", "an innovative wheel cart", "roll luggage without bumping it", True, tags={"innovative"}),
    "chalk_map": Tool("chalk_map", "a chalk map", "an innovative chalk map", "mark clues and connect them", True, tags={"innovative"}),
}

GREETINGS = {
    "station": "The platform was busy with little paws, soft tails, and shiny shoes.",
    "forest_stop": "The mist made the platform look like a secret nest.",
    "harbor": "The pier smelled of salt, and gulls called over the water.",
}


def hazard_at_risk(luggage: Luggage, misunderstanding: Misunderstanding) -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a1 in ANIMALS:
            for a2 in ANIMALS:
                if a1 == a2:
                    continue
                for lg in LUGGAGE:
                    for ms in MISUNDERSTANDINGS:
                        for tl in TOOLS:
                            combos.append((s, a1, a2, lg, ms, tl))
    return combos


def sensible_tools() -> list[Tool]:
    return list(TOOLS.values())


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld: luggage, misunderstanding, mystery, teamwork, and an innovative tool.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal1", choices=ANIMALS)
    ap.add_argument("--animal2", choices=ANIMALS)
    ap.add_argument("--luggage", choices=LUGGAGE)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--tool", choices=TOOLS)
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
    choices = list(valid_combos())
    if args.setting:
        choices = [c for c in choices if c[0] == args.setting]
    if args.animal1:
        choices = [c for c in choices if c[1] == args.animal1]
    if args.animal2:
        choices = [c for c in choices if c[2] == args.animal2]
    if args.luggage:
        choices = [c for c in choices if c[3] == args.luggage]
    if args.misunderstanding:
        choices = [c for c in choices if c[4] == args.misunderstanding]
    if args.tool:
        choices = [c for c in choices if c[5] == args.tool]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    setting, a1, a2, luggage, misunderstanding, tool = rng.choice(sorted(choices))
    return StoryParams(setting, a1, a2, luggage, misunderstanding, tool)


def introduce(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    world.say(f"{a.id} and {b.id} were two animal friends at {setting.place}.")
    world.say(GREETINGS[setting.id])
    world.say(f"They noticed a piece of {world.facts['luggage'].label} sitting by a bench.")


def explain_confusion(world: World, a: Entity, b: Entity, lug: Luggage, ms: Misunderstanding, tool: Tool) -> None:
    world.say(f"{a.id} thought the {lug.label} looked {ms.mistaken_meaning}.")
    world.say(f"{b.id} was not so sure and said it might be {ms.true_meaning}.")
    world.say(f"Still, the sight of the tag made the mystery feel important.")
    world.say(f"Then {a.id} fetched {tool.phrase}, an innovative helper that could {tool.use}.")


def solve_mystery(world: World, a: Entity, b: Entity, lug: Luggage, ms: Misunderstanding, tool: Tool) -> None:
    world.say(f"Together, they used {tool.phrase} to {tool.use}.")
    world.say(f"The little clue showed that the luggage had {lug.clue.strip()}.")
    world.say(f"That meant it was not a danger at all. It was just {lug.secret}.")
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1


def ending(world: World, a: Entity, b: Entity, lug: Luggage, tool: Tool, setting: Setting) -> None:
    world.say(f"{a.id} and {b.id} rolled the {lug.label} to the helper with a grin.")
    world.say(f"Their innovative plan had solved the mystery, and the station felt calm again.")
    world.say(f"By the end, the two friends were walking side by side, proud of their teamwork.")


def tell(setting: Setting, a1: str, a2: str, luggage: Luggage, misunderstanding: Misunderstanding, tool: Tool) -> World:
    world = World()
    one = world.add(Entity(id=a1, kind="character", type=ANIMALS[a1][0], role="solver", traits=[ANIMALS[a1][1], ANIMALS[a1][2]]))
    two = world.add(Entity(id=a2, kind="character", type=ANIMALS[a2][0], role="solver", traits=[ANIMALS[a2][1], ANIMALS[a2][2]]))
    world.add(Entity(id="luggage", type="thing", label=luggage.label, attrs={"clue": luggage.clue, "secret": luggage.secret}))
    world.facts.update(setting=setting, animal1=one, animal2=two, luggage=luggage, misunderstanding=misunderstanding, tool=tool)

    introduce(world, one, two, setting)
    world.para()
    explain_confusion(world, one, two, luggage, misunderstanding, tool)
    world.para()
    solve_mystery(world, one, two, luggage, misunderstanding, tool)
    world.para()
    ending(world, one, two, luggage, tool, setting)
    world.facts.update(solved=True, teamwork=True, innovative=tool.innovative)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story that includes the words "luggage" and "innovative".',
        f"Tell a short story where {f['animal1'].id} and {f['animal2'].id} misunderstand a piece of luggage, then solve the mystery together.",
        f"Write a teamwork story for a young child in which an innovative tool helps two animals learn what the luggage really is.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["animal1"], f["animal2"]
    lug, ms, tool = f["luggage"], f["misunderstanding"], f["tool"]
    return [
        QAItem(
            question="What is the story about?",
            answer=f"It is about {a.id} and {b.id}, two animal friends who find some {lug.label} and try to figure out what it means. The story turns on a misunderstanding that they solve together."
        ),
        QAItem(
            question="Why did the animals need to work together?",
            answer=f"They each noticed different clues, so teamwork helped them solve the mystery. One friend worried first, and the other used an innovative tool to check the truth."
        ),
        QAItem(
            question="What did they learn about the luggage?",
            answer=f"They learned that it was not {ms.mistaken_meaning}, because the clue showed it was {ms.true_meaning}. That made the ending calm instead of scary."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question="What is luggage?", answer="Luggage is a bag or suitcase that carries a person's things when they travel."),
        QAItem(question="What does innovative mean?", answer="Innovative means new and clever, made in a smart way that helps solve a problem."),
        QAItem(question="What is teamwork?", answer="Teamwork means people or animals help each other and do a job together."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A1,A2,L,M,T) :- setting(S), animal(A1), animal(A2), A1 != A2, luggage(L), misunderstanding(M), tool(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for l in LUGGAGE:
        lines.append(asp.fact("luggage", l))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH between clingo and valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.animal1, params.animal2, LUGGAGE[params.luggage], MISUNDERSTANDINGS[params.misunderstanding], TOOLS[params.tool])
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
    StoryParams("station", "fox", "rabbit", "red_case", "lost", "tag_reader"),
    StoryParams("forest_stop", "mouse", "otter", "blue_bag", "secret", "chalk_map"),
    StoryParams("harbor", "bear", "fox", "green_trunk", "trap", "wheel_cart"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = [generate(p) for p in CURATED] if args.all else []
    if not samples:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                p = resolve_params(args, random.Random((args.seed or 0) + i))
            except StoryError as err:
                print(err)
                return
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
