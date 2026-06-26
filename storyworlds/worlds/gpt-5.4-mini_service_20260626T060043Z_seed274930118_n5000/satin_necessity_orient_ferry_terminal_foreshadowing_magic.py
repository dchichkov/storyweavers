#!/usr/bin/env python3
"""
A standalone storyworld script for a tiny fable set at a ferry terminal.

Premise:
A careful child or small animal wants to cross the water by ferry, but the
route is confusing. A satin keepsake matters for appearances, yet the real
necessity is to orient correctly before boarding. A little magic helps the
hero notice what matters and choose the right way.

The world model tracks:
- physical meters: distance, wetness, readiness, confusion, safety, magic
- emotional memes: hope, worry, courage, calm, delight
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
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
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
    place: str = "the ferry terminal"
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    category: str
    tags: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    item: str
    challenge: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
SETTING = Setting(place="the ferry terminal", affords={"orient", "magic"})

ITEMS = {
    "satin": Item(
        id="satin",
        label="satin ribbon",
        phrase="a bright satin ribbon",
        type="ribbon",
        category="keepsake",
        tags={"satin", "beauty"},
    ),
    "compass": Item(
        id="compass",
        label="little compass",
        phrase="a little compass with a brass face",
        type="compass",
        category="tool",
        tags={"orient", "need"},
    ),
    "lamp": Item(
        id="lamp",
        label="lantern",
        phrase="a small lantern with a warm flame",
        type="lantern",
        category="light",
        tags={"magic", "foreshadowing"},
    ),
}

TRAITS = ["careful", "curious", "gentle", "brave", "patient"]
GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Elsa"]
BOY_NAMES = ["Timo", "Eli", "Oren", "Theo", "Nico"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def threshold() -> float:
    return 1.0


def _say_intro(world: World, hero: Entity, parent: Entity, item: Entity, challenge: str) -> None:
    world.say(
        f"{hero.id} was a small {hero.type} who lived by the ferry terminal and liked to keep {hero.pronoun('possessive')} things tidy."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved {item.label}, but the real necessity was to {challenge} before the ferry whistle blew."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.type} always said that a child should know where the shore begins and where the water ends."
    )


def _foreshadow(world: World, hero: Entity, item: Entity, challenge: str) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"That morning, a gull circled once above the dock, as if warning that the way ahead would need a steady eye."
    )
    world.say(
        f"{hero.id} noticed the satin ribbon fluttering in the salt wind, and for a moment {hero.pronoun('subject')} feared it might hide the path."
    )
    world.say(
        f"Yet the little compass in {hero.pronoun('possessive')} pocket seemed to promise that {hero.pronoun('subject')} could still {challenge}."
    )


def _magic(world: World, hero: Entity, item: Entity) -> None:
    hero.meters["magic"] = hero.meters.get("magic", 0) + 1
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    world.say(
        f"When {hero.id} held the compass in both hands, the brass face glowed softly, and the fog around the pier thinned like a curtain."
    )
    world.say(
        f"The glow did not move the ferry; it only helped {hero.id} orient {item.it()} and the shore at the same time."
    )


def _resolve(world: World, hero: Entity, parent: Entity, item: Entity, challenge: str) -> None:
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    hero.memes["delight"] = hero.memes.get("delight", 0) + 1
    world.say(
        f"{hero.id} stood straight, chose the right sign, and {challenge} without losing {item.label}."
    )
    world.say(
        f"Then {hero.pronoun('subject')} boarded the ferry beside {hero.pronoun('possessive')} {parent.type}, feeling wiser than before."
    )
    world.say(
        f"The satin ribbon stayed bright, the compass stayed warm, and the terminal looked less puzzling than it had at dawn."
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTING)

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            meters={"readiness": 0.0, "confusion": 0.0, "safety": 0.0, "magic": 0.0},
            memes={"hope": 1.0, "worry": 0.0, "courage": 0.0, "calm": 0.0, "delight": 0.0},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=params.parent,
            label=params.parent,
            meters={"watchfulness": 1.0},
            memes={"love": 1.0},
        )
    )
    item = world.add(
        Entity(
            id=params.item,
            type="thing",
            label=ITEMS[params.item].label,
            phrase=ITEMS[params.item].phrase,
            owner=hero.id,
            caretaker=parent.id,
            carried_by=hero.id,
            plural=ITEMS[params.item].plural,
            meters={"brightness": 1.0, "mess": 0.0},
        )
    )
    compass = world.add(
        Entity(
            id="compass",
            type="thing",
            label=ITEMS["compass"].label,
            phrase=ITEMS["compass"].phrase,
            owner=hero.id,
            carried_by=hero.id,
            meters={"true": 1.0},
            memes={"trust": 1.0},
        )
    )

    _say_intro(world, hero, parent, item, params.challenge)
    world.para()
    _foreshadow(world, hero, item, params.challenge)
    world.para()
    _magic(world, hero, compass)
    world.para()
    _resolve(world, hero, parent, item, params.challenge)

    world.facts.update(hero=hero, parent=parent, item=item, compass=compass, params=params)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    return [
        "Write a short fable about a child at a ferry terminal who learns that necessity is more important than decoration.",
        f"Tell a gentle story where {hero.id} must {f['params'].challenge} and a {item.label} matters less than staying oriented.",
        "Make the story include foreshadowing, a little magic, and a calm ending at the ferry terminal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    item = f["item"]
    params = f["params"]
    return [
        QAItem(
            question=f"What did {hero.id} need to do before the ferry whistle blew?",
            answer=f"{hero.id} needed to {params.challenge} before the ferry whistle blew, because being oriented mattered more than looking fancy.",
        ),
        QAItem(
            question=f"Why did the satin ribbon matter in the story?",
            answer=f"The satin ribbon mattered because it was beautiful and special to {hero.id}, but it was not the most important thing at the ferry terminal.",
        ),
        QAItem(
            question=f"How did the magic help {hero.id} with the compass?",
            answer=f"The magic made the compass glow softly, which helped {hero.id} orient toward the shore and choose the right way.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end of the story?",
            answer=f"{hero.id} felt calmer, braver, and pleased after {hero.id.lower() if False else 'the child'} succeeded and boarded the ferry with {parent.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ferry terminal?",
            answer="A ferry terminal is a place where people wait for ferries, buy tickets, and board boats that carry them across water.",
        ),
        QAItem(
            question="What is satin?",
            answer="Satin is a smooth, shiny cloth that feels soft and looks bright.",
        ),
        QAItem(
            question="What does it mean to orient yourself?",
            answer="To orient yourself means to figure out which direction you are facing and where you should go.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue that hints something important may happen later.",
        ),
        QAItem(
            question="What is magic in a fable?",
            answer="Magic in a fable is a special, impossible help that makes the lesson feel vivid and memorable.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/4.
#show valid_story/6.

at_risk(Item) :- item(Item), category(Item, keepsake).
needed(Item) :- item(Item), category(Item, tool).

compatible(Item) :- at_risk(Item), needed(compass).

valid(Place, Challenge, Item, Theme) :- place(Place), challenge(Challenge), item(Item), theme(Theme),
                                        Place = ferry_terminal,
                                        Theme = fable,
                                        challenge_requires_orientation(Challenge),
                                        compatible(Item).

valid_story(Place, Challenge, Item, Theme, Feature1, Feature2) :- valid(Place, Challenge, Item, Theme),
                                                                  feature(Feature1), feature(Feature2),
                                                                  Feature1 = foreshadowing,
                                                                  Feature2 = magic.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("place", "ferry_terminal"))
    lines.append(asp.fact("theme", "fable"))
    lines.append(asp.fact("feature", "foreshadowing"))
    lines.append(asp.fact("feature", "magic"))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("category", iid, item.category))
    lines.append(asp.fact("challenge_requires_orientation", "orient"))
    lines.append(asp.fact("challenge_requires_orientation", "navigate"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid combinations.")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for challenge in {"orient"}:
        for item in ITEMS:
            combos.append(("ferry terminal", challenge, item, "fable"))
    return combos


def explain_invalid(challenge: str, item: str) -> str:
    if challenge != "orient":
        return "No story: this world is about orienting at a ferry terminal."
    if item not in ITEMS:
        return "No story: unknown item."
    return "No story: the chosen details do not fit this small fable."


# ---------------------------------------------------------------------------
# Params / generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable set at a ferry terminal.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--item", choices=list(ITEMS))
    ap.add_argument("--challenge", choices=["orient"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    item = args.item or "satin"
    challenge = args.challenge or "orient"
    if challenge != "orient":
        raise StoryError(explain_invalid(challenge, item))
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait, item=item, challenge=challenge)


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
    lines = ["--- world model ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
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
    StoryParams(name="Mina", gender="girl", parent="mother", trait="careful", item="satin", challenge="orient"),
    StoryParams(name="Oren", gender="boy", parent="father", trait="curious", item="satin", challenge="orient"),
    StoryParams(name="Ivy", gender="girl", parent="mother", trait="patient", item="satin", challenge="orient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
