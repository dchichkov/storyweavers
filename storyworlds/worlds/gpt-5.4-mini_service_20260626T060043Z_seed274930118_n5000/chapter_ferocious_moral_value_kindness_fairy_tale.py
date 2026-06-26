#!/usr/bin/env python3
"""
storyworlds/worlds/chapter_ferocious_moral_value_kindness_fairy_tale.py
=======================================================================

A small fairy-tale storyworld about a ferocious creature, a chapter in a
storybook, and the moral value of kindness.

Seed premise:
- A child or storyteller is reading a chapter in a fairy-tale book.
- A ferocious creature frightens the village.
- Kindness, not force, becomes the turning point.
- The ending proves that the creature changed, or the village changed, or both.

The world model tracks:
- physical meters: fear, soot, hunger, distance, warmth, bruises, calm
- emotional memes: kindness, trust, pride, worry, courage, gratitude

The narrative is state-driven: setup -> tension -> turn -> resolution.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "mother", "woman", "princess"}
        male = {"boy", "king", "father", "man", "prince", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the castle lane"
    light: str = "moonlight"
    season: str = "winter"


@dataclass
class Creature:
    id: str
    label: str
    ferocity: int
    hunger: int
    soft_spot: str
    initial_mood: str
    can_change: bool = True


@dataclass
class KindnessTool:
    id: str
    label: str
    action: str
    helps_with: str
    warmth: int


@dataclass
class StoryParams:
    setting: str
    creature: str
    kindness: str
    reader: str
    reader_type: str
    chapter_title: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


CREATURES = {
    "wolf": Creature(
        id="wolf",
        label="ferocious wolf",
        ferocity=5,
        hunger=4,
        soft_spot="warm bread",
        initial_mood="sharp and hungry",
    ),
    "dragon": Creature(
        id="dragon",
        label="ferocious dragon",
        ferocity=6,
        hunger=5,
        soft_spot="a song",
        initial_mood="hot and lonely",
    ),
    "troll": Creature(
        id="troll",
        label="ferocious troll",
        ferocity=4,
        hunger=3,
        soft_spot="a kind word",
        initial_mood="grumpy and lonely",
    ),
}

KINDNESSES = {
    "bread": KindnessTool(
        id="bread",
        label="a loaf of warm bread",
        action="share warm bread",
        helps_with="hunger",
        warmth=3,
    ),
    "song": KindnessTool(
        id="song",
        label="a small singing voice",
        action="sing a gentle song",
        helps_with="loneliness",
        warmth=2,
    ),
    "blanket": KindnessTool(
        id="blanket",
        label="a soft blanket",
        action="offer a soft blanket",
        helps_with="cold",
        warmth=4,
    ),
    "bandage": KindnessTool(
        id="bandage",
        label="a clean bandage",
        action="wrap a careful bandage",
        helps_with="hurt",
        warmth=2,
    ),
}

SETTINGS = {
    "castle": Setting(place="the castle lane", light="moonlight", season="winter"),
    "wood": Setting(place="the moonlit wood", light="silver moonlight", season="autumn"),
    "village": Setting(place="the village road", light="early dawn", season="spring"),
}

READER_TYPES = ["girl", "boy", "child"]
NAMES = {
    "girl": ["Lina", "Mira", "Tessa", "Nora", "Elin"],
    "boy": ["Tobin", "Perry", "Milo", "Arlo", "Finn"],
    "child": ["Robin", "Sunny", "Pip", "Noa", "Kit"],
}


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _set_meter(e: Entity, key: str, val: float) -> None:
    e.meters[key] = val


def _set_mem(e: Entity, key: str, val: float) -> None:
    e.memes[key] = val


def _add_meter(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _add_mem(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def tell(setting: Setting, creature: Creature, kindness: KindnessTool,
         reader_name: str, reader_type: str, chapter_title: str) -> World:
    world = World(setting=setting)
    reader = world.add(Entity(id=reader_name, kind="character", type=reader_type, label=reader_name))
    beast = world.add(Entity(id=creature.id, kind="character", type="creature", label=creature.label))
    gift = world.add(Entity(id=kindness.id, kind="thing", type="gift", label=kindness.label))

    _set_meter(beast, "fear", creature.ferocity)
    _set_meter(beast, "hunger", creature.hunger)
    _set_mem(beast, "worry", 2.0)
    _set_mem(reader, "courage", 1.0)
    _set_mem(reader, "kindness", 1.0)
    _set_meter(reader, "distance", 3.0)
    _set_meter(reader, "warmth", 0.0)

    world.facts.update(
        reader=reader,
        beast=beast,
        gift=gift,
        creature=creature,
        kindness=kindness,
        chapter_title=chapter_title,
    )

    world.say(
        f"This chapter, called {chapter_title}, began in {setting.place} under {setting.light}."
    )
    world.say(
        f"{reader.id} held a storybook open and found a chapter about a {creature.label}."
    )
    world.say(
        f"The {creature.label} was famous for being ferocious, and the town had learned to step softly."
    )

    world.para()
    _add_meter(beast, "fear", 1.0)
    _add_mem(reader, "worry", 1.0)
    world.say(
        f"That night, the {creature.label} paced by the gate with hungry eyes and a loud growl."
    )
    world.say(
        f"The villagers hid behind their doors, and {reader.id} felt the air grow tight with fear."
    )

    world.para()
    _add_mem(reader, "kindness", 1.0)
    world.say(
        f"But {reader.id} remembered the moral value of kindness from the chapter and chose a gentle way."
    )
    world.say(f"{reader.id} carried {kindness.label} toward the gate instead of a stone or a shout.")
    if kindness.action == "share warm bread":
        _add_meter(gift, "warmth", kindness.warmth)
        _add_meter(beast, "hunger", -2.0)
        _add_mem(beast, "trust", 2.0)
        _add_mem(reader, "gratitude", 1.0)
        world.say(
            f"The smell of bread drifted through the lane, and the ferocious wolf lowered his head."
        )
        world.say(
            f"He took the bread carefully, as if he had forgotten that anyone could mean him well."
        )
    elif kindness.action == "sing a gentle song":
        _add_mem(beast, "trust", 2.0)
        _add_mem(beast, "calm", 2.0)
        _add_mem(reader, "courage", 1.0)
        world.say(
            f"{reader.id} sang a gentle song, and the ferocious dragon stopped shaking the roof tiles."
        )
        world.say(
            f"The tune was small, but it reached the dragon's lonely heart like a lantern in fog."
        )
    elif kindness.action == "offer a soft blanket":
        _add_meter(beast, "cold", -2.0)
        _add_mem(beast, "trust", 2.0)
        world.say(
            f"{reader.id} offered the soft blanket, and the ferocious troll blinked in surprise."
        )
        world.say(
            f"The blanket warmed his shoulders, and his grumble turned into a tired sigh."
        )
    else:
        _add_meter(beast, "hurt", -1.0)
        _add_mem(beast, "trust", 1.0)
        world.say(
            f"{reader.id} wrapped the careful bandage around the hurt paw, and the beast stopped pacing."
        )
        world.say(
            f"Kindness made room where fear had been, and the ferocious one watched in silence."

        )

    world.para()
    _set_meter(beast, "fear", max(0.0, _meter(beast, "fear") - 3.0))
    _set_mem(beast, "kindness", 2.0)
    _set_mem(beast, "worry", max(0.0, _mem(beast, "worry") - 1.0))
    _set_mem(reader, "courage", 2.0)
    _add_mem(reader, "gratitude", 1.0)
    world.say(
        f"By the end, the ferocious creature was no longer only fierce; he was gentler and less lonely."
    )
    world.say(
        f"{reader.id} closed the storybook with a happy sigh, because the chapter had changed the whole lane."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["creature"]
    k = f["kindness"]
    return [
        f'Write a fairy-tale chapter about a ferocious {c.id} and the moral value of kindness.',
        f"Tell a short story where {f['reader'].id} uses {k.label} to help a ferocious creature.",
        "Write a child-friendly fairy tale that begins with fear and ends with kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    reader: Entity = f["reader"]
    beast: Entity = f["beast"]
    gift: Entity = f["gift"]
    creature: Creature = f["creature"]
    kindness: KindnessTool = f["kindness"]

    return [
        QAItem(
            question=f"What kind of chapter was this story from?",
            answer=f"It was a fairy-tale chapter about a ferocious {creature.id} and the moral value of kindness.",
        ),
        QAItem(
            question=f"Why was {beast.label} frightening at the start?",
            answer=f"He was ferocious and hungry, so he growled and made the village hide behind their doors.",
        ),
        QAItem(
            question=f"What did {reader.id} bring instead of shouting or fighting?",
            answer=f"{reader.id} brought {gift.label}, choosing {kindness.action} as a kind answer.",
        ),
        QAItem(
            question=f"What changed after the kindness was shown?",
            answer=f"The creature grew calmer and more trusting, and the fear in the lane became much smaller.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means doing something gentle and caring for someone else, especially when they need help.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is an important idea about how to treat people well, like kindness, honesty, or bravery.",
        ),
        QAItem(
            question="What makes a fairy tale feel like a fairy tale?",
            answer="A fairy tale often has a castle, a forest, a magical feeling, and a clear lesson at the end.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 0.0001}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 0.0001}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="castle", creature="wolf", kindness="bread", reader="Lina", reader_type="girl", chapter_title="The Chapter of Warm Bread"),
    StoryParams(setting="wood", creature="dragon", kindness="song", reader="Milo", reader_type="boy", chapter_title="The Chapter of the Lantern Song"),
    StoryParams(setting="village", creature="troll", kindness="blanket", reader="Robin", reader_type="child", chapter_title="The Chapter of the Soft Blanket"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a ferocious creature and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--reader-type", choices=READER_TYPES)
    ap.add_argument("--reader")
    ap.add_argument("--chapter-title")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    creature = args.creature or rng.choice(list(CREATURES))
    kindness = args.kindness or rng.choice(list(KINDNESSES))
    reader_type = args.reader_type or rng.choice(READER_TYPES)
    reader = args.reader or rng.choice(NAMES[reader_type])
    chapter_title = args.chapter_title or rng.choice([
        "The Chapter of the Ferocious Wolf",
        "The Chapter of the Gentle Song",
        "The Chapter of Kind Hands",
        "The Chapter of the Moonlit Gate",
    ])
    return StoryParams(
        setting=setting,
        creature=creature,
        kindness=kindness,
        reader=reader,
        reader_type=reader_type,
        chapter_title=chapter_title,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CREATURES[params.creature], KINDNESSES[params.kindness],
                 params.reader, params.reader_type, params.chapter_title)
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


ASP_RULES = r"""
ferocious(creature).
kindness(tool).
chapter(ch).

softens(C) :- ferocious(C), offered_kindness(C).
lesson(kindness) :- chapter(ch), softens(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CREATURES:
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("ferocious", cid))
    for kid in KINDNESSES:
        lines.append(asp.fact("tool", kid))
        lines.append(asp.fact("kindness", kid))
    lines.append(asp.fact("chapter", "chapter"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show softens/1.\n#show lesson/1."))
    softens = set(asp.atoms(model, "softens"))
    lesson = set(asp.atoms(model, "lesson"))
    ok = bool(softens) and ("kindness",) in lesson
    if ok:
        print("OK: ASP twin is present and generates the expected lesson.")
        return 0
    print("MISMATCH or empty ASP model.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show softens/1.\n#show lesson/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show softens/1.\n#show lesson/1."))
        print(f"softens: {sorted(set(asp.atoms(model, 'softens')))}")
        print(f"lesson: {sorted(set(asp.atoms(model, 'lesson')))}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.chapter_title} ({p.setting}, {p.creature}, {p.kindness})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
