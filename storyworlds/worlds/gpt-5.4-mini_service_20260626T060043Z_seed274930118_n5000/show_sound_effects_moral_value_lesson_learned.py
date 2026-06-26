#!/usr/bin/env python3
"""
A standalone storyworld for a small rhyming tale about putting on a show,
with sound effects, a moral value, and a lesson learned.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    sound: str
    mess: str
    morale: str
    lesson: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    category: str
    sound: str
    helps: str
    plural: bool = False


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
    "backyard": Setting(place="the backyard", indoors=False, affords={"show"}),
    "playroom": Setting(place="the playroom", indoors=True, affords={"show"}),
    "garage": Setting(place="the garage", indoors=True, affords={"show"}),
}

ACTIVITIES = {
    "show": Activity(
        id="show",
        verb="put on a show",
        gerund="putting on a show",
        sound="clap-clap",
        mess="messy_confetti",
        morale="sharing joy feels good",
        lesson="practice makes the show shine",
        keyword="show",
        tags={"show", "music", "sharing"},
    ),
}

PROPS = {
    "bell": Prop(
        id="bell",
        label="little bell",
        phrase="a little shiny bell",
        category="sound",
        sound="ding-ding",
        helps="adds a bright ring",
    ),
    "drum": Prop(
        id="drum",
        label="toy drum",
        phrase="a round toy drum",
        category="sound",
        sound="boom-boom",
        helps="keeps the beat",
    ),
    "scarves": Prop(
        id="scarves",
        label="silk scarves",
        phrase="two silk scarves",
        category="dance",
        sound="swish-swish",
        helps="makes the dance feel light",
        plural=True,
    ),
    "stage_lights": Prop(
        id="lights",
        label="paper stage lights",
        phrase="paper stage lights",
        category="light",
        sound="twinkle-twinkle",
        helps="makes the stage glow",
        plural=True,
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ella", "Rose", "Lucy"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Theo", "Finn", "Noah", "Eli"]
TRAITS = ["brave", "cheerful", "curious", "gentle", "silly", "bright"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    trait: str
    prop: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def valid_props() -> list[str]:
    return list(PROPS.keys())


def explain_rejection(prop_id: str) -> str:
    prop = PROPS[prop_id]
    return f"(No story: {prop.label} doesn't fit this little show.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child prepares a rhyming show with sound effects."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--prop", choices=PROPS)
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
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    prop = args.prop or rng.choice(valid_props())
    name = args.name or pick_name(rng, gender)
    return StoryParams(place=place, name=name, gender=gender, parent=parent, trait=trait, prop=prop)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    act = ACTIVITIES["show"]
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    prop = world.add(Entity(
        id=params.prop,
        type=PROPS[params.prop].category,
        label=PROPS[params.prop].label,
        phrase=PROPS[params.prop].phrase,
        plural=PROPS[params.prop].plural,
        owner=hero.id,
        held_by=hero.id,
    ))

    # Act 1
    world.say(
        f"{hero.id} was a {params.trait} little {params.gender} who loved the word show."
    )
    world.say(
        f"{hero.id} liked to practice {act.gerund}, and {prop.phrase} made a bright little spark."
    )
    world.say(
        f"Every tap and jingle felt jolly, and the room hummed with a soft happy song."
    )

    # Act 2
    world.para()
    world.say(
        f"One day at {setting.place}, {hero.id} wanted to {act.verb} for {hero.pronoun('possessive')} {params.parent}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} shook {prop.it()} and went {PROPS[params.prop].sound}, with a {params.trait} little grin."
    )
    world.say(
        f"But the first try was all wibble and wobble, and the tune came out with a tumble."
    )
    hero.memes["disappointment"] = 1.0
    hero.memes["desire"] = 1.0
    parent.memes["worry"] = 1.0
    parent.memes["care"] = 1.0

    # Act 3
    world.para()
    world.say(
        f"{params.parent.capitalize()} smiled and said, \"Try again, slow and neat; a calm little heart makes a kind little beat.\""
    )
    world.say(
        f"So {hero.id} stood tall, took a breath, and gave {prop.it()} a gentler shake."
    )
    world.say(
        f"{PROPS[params.prop].sound.capitalize()}! {act.sound}! The show was sweet, and the mistake turned small beneath nimble feet."
    )
    world.say(
        f"{hero.id} bowed with joy, and {params.parent} clapped along: the lesson learned was {act.lesson}."
    )

    hero.memes["joy"] = 2.0
    hero.memes["confidence"] = 1.0
    parent.memes["pride"] = 1.0

    world.facts.update(
        hero=hero,
        parent=parent,
        prop=prop,
        activity=act,
        setting=setting,
        moral=act.morale,
        lesson=act.lesson,
    )
    return world


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prop = f["prop"]
    return [
        f'Write a rhyming story with the word "show" about a child named {hero.id}.',
        f"Tell a gentle story where {hero.id} uses {prop.phrase} and learns to try again.",
        f"Create a child-friendly show story with sound effects, a moral value, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prop = f["prop"]
    act = f["activity"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place}?",
            answer=f"{hero.id} wanted to {act.verb} at {place}.",
        ),
        QAItem(
            question=f"What sound did {prop.label} make in the story?",
            answer=f"{prop.label.capitalize()} went {PROPS[prop.id].sound} when {hero.id} shook it.",
        ),
        QAItem(
            question=f"What did {parent.id} tell {hero.id} to do?",
            answer=f"The {parent.type} told {hero.id} to try again slowly and neatly.",
        ),
        QAItem(
            question="What moral value was shown in the story?",
            answer=f"The moral value was that {act.morale}.",
        ),
        QAItem(
            question="What lesson was learned at the end?",
            answer=f"The lesson learned was that {act.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a show?",
            answer="A show is a performance that people put on to entertain others.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special noises like ding-ding or boom-boom that help tell a story.",
        ),
        QAItem(
            question="Why do people practice before a show?",
            answer="People practice before a show so they can remember the steps and perform more smoothly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.

valid(Place, show, Prop) :- setting(Place), affords(Place, show), prop(Prop).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for prop_id in PROPS:
        lines.append(asp.fact("prop", prop_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((p, "show", prop) for p in SETTINGS for prop in PROPS)
    cl = asp_valid_combos()
    if set(py) != set(cl):
        print("MISMATCH between ASP and Python:")
        print("  only in ASP:", sorted(set(cl) - set(py)))
        print("  only in Python:", sorted(set(py) - set(cl)))
        return 1
    print(f"OK: ASP matches Python ({len(py)} combos).")
    return 0


# ---------------------------------------------------------------------------
# Sample generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="backyard", name="Lily", gender="girl", parent="mother", trait="cheerful", prop="bell"),
    StoryParams(place="playroom", name="Leo", gender="boy", parent="father", trait="curious", prop="drum"),
    StoryParams(place="garage", name="Mia", gender="girl", parent="mother", trait="bright", prop="scarves"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.prop} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
