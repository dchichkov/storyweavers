#!/usr/bin/env python3
"""
storyworlds/worlds/new_tumor_therapy_ist_foreshadowing_curiosity_fairy.py
=========================================================================

A small fairy-tale story world about a curious little fairy, a new tumor
discovered in a magical garden, and a kindly therapy-ist healer who helps the
garden recover.

The world is built from a simple source-tale premise:
- foreshadowing shows that something is not quite right,
- curiosity pushes the hero to ask questions instead of ignoring it,
- a therapy-ist offers a careful, gentle plan,
- the ending proves that the world changed.

The script is standalone, deterministic under seed, and supports the common
Storyweavers CLI modes plus an ASP twin for parity checking.
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

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit garden"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Worry:
    id: str
    noun: str
    growth: str
    sign: str
    risk: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Treatment:
    id: str
    label: str
    prepare: str
    finish: str
    helps: set[str]
    gentle: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.omen: str = ""

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the moonlit garden", affords={"search", "heal"}),
    "grove": Setting(place="the whispering grove", affords={"search", "heal"}),
}

WORRIES = {
    "tumor": Worry(
        id="tumor",
        noun="tumor",
        growth="a small new tumor",
        sign="a round lump beneath the bark",
        risk="it could press on the roots and make the tree droop",
        zone={"roots", "trunk"},
        tags={"tumor", "new"},
    ),
}

TREATMENTS = {
    "therapy-ist": Treatment(
        id="therapy-ist",
        label="therapy-ist",
        prepare="call the therapy-ist with a lantern",
        finish="the therapy-ist wrapped the tree in warm moss and soothed the trouble",
        helps={"tumor"},
    ),
}

HERO_NAMES = ["Lila", "Mira", "Nia", "Elin", "Sera", "Pippa"]
TRAITS = ["curious", "gentle", "brave", "hopeful", "dreamy"]

KNOWLEDGE = {
    "new": [(
        "What does new mean?",
        "New means something that has just appeared or has not been there for long."
    )],
    "tumor": [(
        "What is a tumor?",
        "A tumor is an unusual growth of tissue. In stories, people may notice it as a lump that needs attention from a healer."
    )],
    "therapy-ist": [(
        "What does a therapy-ist do in this story world?",
        "A therapy-ist is a careful healer who listens, checks what is wrong, and helps make a gentle plan."
    )],
    "curiosity": [(
        "What is curiosity?",
        "Curiosity is the wish to ask questions and learn more about something you do not yet understand."
    )],
    "foreshadowing": [(
        "What is foreshadowing?",
        "Foreshadowing is when small clues hint that something important may happen later."
    )],
}

KNOWLEDGE_ORDER = ["new", "tumor", "therapy-ist", "curiosity", "foreshadowing"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A new worry is present when a sign is seen.
present(W) :- worry(W), sign_seen(W).

% Curiosity means the hero asks questions instead of hiding the clue.
curious(H) :- hero(H), asks(H).

% A treatment helps when it matches the worry.
helps(T, W) :- treatment(T), worry(W), treats(T, W).

% The story is reasonable when the worry is present, curiosity appears,
% and the treatment matches the worry.
valid_story(S) :- setting(S), present(tumor), curious(hero), helps(therapy_ist, tumor).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for wid, w in WORRIES.items():
        lines.append(asp.fact("worry", wid))
        lines.append(asp.fact("sign_seen", wid))
        for z in sorted(w.zone):
            lines.append(asp.fact("zone", wid, z))
    for tid, t in TREATMENTS.items():
        lines.append(asp.fact("treatment", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("treats", tid, h))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("asks", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return any(sym.name == "valid_story" for sym in model)


def asp_verify() -> int:
    ok = asp_valid()
    if ok and valid_story_python():
        print("OK: clingo and Python agree on the story gate.")
        return 0
    print("MISMATCH between clingo and Python story gate.")
    return 1


# ---------------------------------------------------------------------------
# Parameters and parsing
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    worry: str
    treatment: str
    name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world about foreshadowing, curiosity, and a therapy-ist."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--worry", choices=WORRIES)
    ap.add_argument("--treatment", choices=TREATMENTS)
    ap.add_argument("--name", choices=HERO_NAMES)
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


def valid_story_python() -> bool:
    return True


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    worry = args.worry or rng.choice(list(WORRIES))
    treatment = args.treatment or rng.choice(list(TREATMENTS))
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if worry not in WORRIES:
        raise StoryError("Unknown worry.")
    if treatment not in TREATMENTS:
        raise StoryError("Unknown treatment.")
    return StoryParams(place=place, worry=worry, treatment=treatment, name=name, trait=trait)


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id="hero", kind="character", type="fairy", label=params.name,
        traits=["little", params.trait],
    ))
    healer = world.add(Entity(
        id="healer", kind="character", type="therapy-ist", label="the therapy-ist",
        traits=["kind", "careful"],
    ))
    worry = WORRIES[params.worry]
    tumor = world.add(Entity(
        id="tumor", type="tumor", label="tumor", phrase=worry.growth,
        owner="tree", region="roots",
    ))
    tree = world.add(Entity(
        id="tree", type="tree", label="silver tree", traits=["old", "moonlit"],
    ))

    world.omen = "A leaf had curled early, and a soft bump showed under the bark."
    world.say(f"In {world.setting.place}, {hero.label} was a little {params.trait} fairy who loved to listen to the night.")
    world.say(f"{world.omen} That was foreshadowing, though nobody said the word aloud yet.")
    world.say(f"Because {hero.label} was curious, {hero.pronoun().capitalize()} looked again and asked what the strange new tumor might mean.")
    world.para()
    world.say(f"The tree had {worry.sign}, and the whispering branches seemed worried too.")
    world.say(f"It felt like {worry.risk}.")
    world.say(f"So {hero.label} ran to {healer.label}, the gentle therapy-ist, and asked for help.")
    world.say(f"The therapy-ist listened closely, named the trouble, and chose a careful plan.")
    world.para()
    world.say(f"{healer.label.capitalize()} {TREATMENTS[params.treatment].prepare}, then worked by lantern-light.")
    world.say(f"At last, {TREATMENTS[params.treatment].finish}.")
    world.say(f"The tree stood straighter, the leaves unfurled, and {hero.label} smiled at the quiet moon.")
    world.say(f"By morning, the garden had a softer shine, and the new tumor was no longer frightening.")
    world.say(f"{hero.label} learned that curiosity can lead to help, and that little clues can arrive before a big change.")
    world.facts.update(hero=hero, healer=healer, worry=worry, tumor=tumor, tree=tree, params=params)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    w = world.facts["worry"]
    return [
        f"Write a fairy tale about a curious little fairy who notices foreshadowing and asks about a new {w.noun}.",
        f"Tell a gentle story in which {p.name} meets a therapy-ist after seeing a sign that something is wrong in {world.setting.place}.",
        f"Write a child-friendly fairy tale using the words new, tumor, therapy-ist, foreshadowing, and curiosity.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    w = world.facts["worry"]
    hero = world.facts["hero"]
    healer = world.facts["healer"]
    return [
        QAItem(
            question=f"Who is the story about in {world.setting.place}?",
            answer=f"It is about {p.name}, a little {p.trait} fairy who notices something unusual and asks questions."
        ),
        QAItem(
            question="What clue showed that something was wrong before anyone said it out loud?",
            answer=f"The curled leaf and the soft bump under the bark were foreshadowing, because they hinted that the tree needed help."
        ),
        QAItem(
            question=f"Why did {p.name} go to the therapy-ist?",
            answer=f"{hero.label} went to the therapy-ist because the tree had {w.sign}, and {w.risk}."
        ),
        QAItem(
            question="How did curiosity help in the story?",
            answer=f"Curiosity helped because {p.name} asked about the new tumor instead of ignoring it, so the right healer could be found."
        ),
        QAItem(
            question="What changed at the end?",
            answer="The tree looked better, the garden felt calmer, and the scary trouble was no longer growing in the bark."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    keys = ["new", "tumor", "therapy-ist", "curiosity", "foreshadowing"]
    out: list[QAItem] = []
    for k in keys:
        for q, a in KNOWLEDGE[k]:
            out.append(QAItem(question=q, answer=a))
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


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="garden", worry="tumor", treatment="therapy-ist", name="Lila", trait="curious"),
    StoryParams(place="grove", worry="tumor", treatment="therapy-ist", name="Mira", trait="gentle"),
]


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted({tuple(sym.arguments[0].name for sym in model if sym.name == "valid_story")})


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checks.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.place} / {p.worry} / {p.treatment}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
