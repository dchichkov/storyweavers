#!/usr/bin/env python3
"""
storyworlds/worlds/commemorate_arrow_qrs_teamwork_dialogue_rhyming_story.py
============================================================================

A small story world about a child, a shared job, and a keepsake to
commemorate a special day. The child and a helper work together, talk through
the problem, and use an arrow sign and a row of qrs tiles to guide everyone to
the celebration spot.

Seed tale:
---
Once there was a child who wanted to commemorate a little neighborhood parade.
The child found a bent arrow sign in a box, plus three tiny qrs tiles that
could help guests find the party table. But the sign was dull and the tiles
were mixed up. A friend arrived, and they talked, sorted, and worked together
until the arrow pointed the right way and the qrs row sat in a neat line.
Then the child smiled because the keepsake made the day feel special.

This world models:
- physical meters: shine, bend, order, crowding, and placement
- emotional memes: hope, worry, teamwork, and delight

The prose is intended to feel like a Rhyming Story: short lines, mild rhythm,
and a cheerful ending image.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "mother", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "father", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the town hall room"
    indoors: bool = True


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    role: str  # arrow or qrs
    repairs: str
    celebratory: str


@dataclass
class StoryParams:
    place: str
    item: str
    hero_name: str
    helper_name: str
    hero_gender: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n".join(self.lines)


ITEMS = {
    "arrow": Item(
        id="arrow",
        label="arrow sign",
        phrase="a bent arrow sign for the parade",
        role="arrow",
        repairs="straightened",
        celebratory="pointed the way",
    ),
    "qrs": Item(
        id="qrs",
        label="qrs tiles",
        phrase="three tiny qrs tiles in a bright row",
        role="qrs",
        repairs="sorted",
        celebratory="sat in a neat line",
    ),
}

SETTINGS = {
    "hall": Setting(place="the town hall room", indoors=True),
    "library": Setting(place="the library nook", indoors=True),
    "porch": Setting(place="the sunny porch", indoors=False),
}

GIRL_NAMES = ["Mia", "Nora", "Lena", "Zoe", "Ivy", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Max", "Owen"]
HELPER_NAMES = ["Sam", "June", "Rae", "Tess", "Ben", "Pia"]


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender))
    item = world.add(Entity(
        id=params.item,
        kind="thing",
        type=params.item,
        label=ITEMS[params.item].label,
        phrase=ITEMS[params.item].phrase,
        plural=(params.item == "qrs"),
        owner=hero.id,
    ))
    world.facts.update(hero=hero, helper=helper, item=item, item_cfg=ITEMS[params.item], setting=world.setting)
    return world


def poem_line(a: str, b: str) -> str:
    return f"{a} {b}"


def tell_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    cfg: Item = f["item_cfg"]
    place = world.setting.place

    world.say(f"At {place}, {hero.id} had a kind little plan,")
    world.say(f"to commemorate a bright day with hands that can.")

    world.say(f"But {hero.id} sighed at {cfg.phrase},")
    if item.id == "arrow":
        world.say(f"The bend made the sign look wobbly and small.")
    else:
        world.say(f"The tiles were jumbled, not tidy at all.")

    world.say(f"Then {helper.id} came near and said, “Let’s not fret;")
    world.say(f"we can talk it through and make it right yet.”")

    hero.memes["worry"] = 1.0
    hero.memes["hope"] = 1.0
    helper.memes["teamwork"] = 1.0
    helper.memes["dialogue"] = 1.0

    world.say(f"“You hold the top,” {helper.id} said with a grin,")
    world.say(f"“and I’ll hold the base; then we’ll tuck it in.”")

    if item.id == "arrow":
        item.meters["bend"] = 0.0
        item.meters["shine"] = 1.0
        item.meters["place"] = 1.0
        world.say(f"The arrow was straightened, smooth, and bright,")
        world.say(f"and it pointed the way in the warm soft light.")
    else:
        item.meters["order"] = 1.0
        item.meters["place"] = 1.0
        item.meters["shine"] = 1.0
        world.say(f"The qrs tiles were sorted with careful grace,")
        world.say(f"and they sat in a neat little picture place.")

    hero.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    world.say(f"{hero.id} laughed, “Now our keepsake feels grand!”")
    world.say(f"{helper.id} laughed, “We made it by hand!”")
    world.say(f"So the day was commended, with care and with cheer,")
    world.say(f"and the tidy little arrow stayed bright through the year.")


def build_story_world(params: StoryParams) -> World:
    world = setup_world(params)
    tell_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    item: Entity = f["item"]
    return [
        f"Write a rhyming story about {hero.id} and a helper who use teamwork and dialogue to fix a {item.label}.",
        f"Tell a child-friendly story that includes the words commemorate, arrow, and qrs.",
        f"Make a short rhyming tale where friends work together to make a keepsake look special.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    cfg: Item = f["item_cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {cfg.label}?",
            answer=f"{hero.id} wanted to commemorate a bright day by making the {cfg.label} look special.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} fix the {cfg.label}?",
            answer=f"They used teamwork and dialogue. They talked, held it carefully, and made it neat again.",
        ),
        QAItem(
            question=f"What changed for the {cfg.label} by the end?",
            answer=f"It was straightened or sorted, and it looked bright and ready to guide the celebration.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does commemorate mean?",
            answer="To commemorate means to remember and honor something special.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue means people talk and listen to each other.",
        ),
        QAItem(
            question="What is an arrow used for?",
            answer="An arrow can point the way so people know where to go.",
        ),
        QAItem(
            question="What are qrs tiles in this story?",
            answer="They are small tiles that are lined up neatly to help mark the celebration spot.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(X) :- helper_name(X).
item(I) :- item_name(I).

good_story(P, I) :- place(P), item(I), hero_name(_), helper_name(_).
used_teamwork :- teamwork.
used_dialogue :- dialogue.
resolved(I) :- item(I), fixed(I).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for iid in ITEMS:
        lines.append(asp.fact("item_name", iid))
    for n in GIRL_NAMES + BOY_NAMES + HELPER_NAMES:
        lines.append(asp.fact("name", n))
    lines.append(asp.fact("teamwork"))
    lines.append(asp.fact("dialogue"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world about commemorating an arrow or qrs display.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--helper-gender", choices=["girl", "boy"], default=None)
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
    item = args.item or rng.choice(list(ITEMS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if hero_name == helper_name:
        helper_name = rng.choice([n for n in HELPER_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        item=item,
        hero_name=hero_name,
        helper_name=helper_name,
        hero_gender=hero_gender,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
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


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    program = asp_program("#show good_story/2.\n#show used_teamwork/0.\n#show used_dialogue/0.")
    model = asp.one_model(program)
    shown = [str(a) for a in model]
    if not shown:
        print("MISMATCH: ASP produced no model.")
        return 1
    print("OK: ASP program parsed and solved.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2.\n#show used_teamwork/0.\n#show used_dialogue/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show good_story/2.\n#show used_teamwork/0.\n#show used_dialogue/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="hall", item="arrow", hero_name="Mia", helper_name="Sam", hero_gender="girl", helper_gender="boy"),
            StoryParams(place="library", item="qrs", hero_name="Leo", helper_name="Rae", hero_gender="boy", helper_gender="girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
