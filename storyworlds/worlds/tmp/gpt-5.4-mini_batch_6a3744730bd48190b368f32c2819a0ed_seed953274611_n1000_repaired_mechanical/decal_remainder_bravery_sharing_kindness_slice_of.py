#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/decal_remainder_bravery_sharing_kindness_slice_of.py
=====================================================================================

A small slice-of-life storyworld about a child finishing a craft project with
stickers, a leftover remainder of supplies, and a kind act of sharing.

The world supports a few close variations around one gentle premise:
a child notices there is only a remainder of a special decal sheet, gets
brave about offering it, and kindness turns the moment into a shared craft
instead of a disappointment.

The story always includes the seed words "decal" and "remainder".
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_MIN = 3.5


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
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Location:
    id: str
    scene: str
    place_line: str
    mood: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Supply:
    id: str
    label: str
    phrase: str
    remainder_label: str
    kind: str = "decal"
    shared: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
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
        clone = World(self.location)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    location: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    supply: str
    gift: str
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


LOCATIONS = {
    "kitchen_table": Location(
        id="kitchen_table",
        scene="a warm kitchen table covered in paper, crayons, and tape",
        place_line="The kitchen table was warm and sunny, with a little bowl of crayons and a scrap of tape nearby.",
        mood="cozy",
        tags={"home", "table", "craft"},
    ),
    "porch": Location(
        id="porch",
        scene="a porch craft corner with a small chair and a box of art supplies",
        place_line="The porch was quiet and bright, and the craft box sat beside a little chair.",
        mood="open",
        tags={"home", "porch", "craft"},
    ),
    "living_room_floor": Location(
        id="living_room_floor",
        scene="a living room floor with a blanket, markers, and a cardboard box",
        place_line="The living room floor felt soft and calm, and the blanket made a good place to spread things out.",
        mood="calm",
        tags={"home", "living_room", "craft"},
    ),
}

SUPPLIES = {
    "sticker_sheet": Supply(
        id="sticker_sheet",
        label="decal sheet",
        phrase="a shiny decal sheet",
        remainder_label="the remainder of the decal sheet",
        kind="decal",
        tags={"decal", "sticker"},
    ),
    "letter_set": Supply(
        id="letter_set",
        label="letter stickers",
        phrase="a sheet of letter stickers",
        remainder_label="the remainder of the letter stickers",
        kind="decal",
        tags={"decal", "letter"},
    ),
    "star_roll": Supply(
        id="star_roll",
        label="star decals",
        phrase="a roll of star decals",
        remainder_label="the remainder of the star decals",
        kind="decal",
        tags={"decal", "star"},
    ),
}

GIFTS = {
    "book_fair_tag": Gift(
        id="book_fair_tag",
        label="bookmark",
        phrase="a bright bookmark for the class box",
        tags={"bookmark", "school"},
    ),
    "name_tag": Gift(
        id="name_tag",
        label="name tag",
        phrase="a name tag for the door",
        tags={"name_tag", "home"},
    ),
    "lunch_note": Gift(
        id="lunch_note",
        label="lunch note",
        phrase="a cheerful lunch note",
        tags={"note", "kind"},
    ),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Ava", "Zoe", "Ella", "Mia", "Rose"]
BOY_NAMES = ["Leo", "Finn", "Owen", "Theo", "Sam", "Noah", "Ben", "Max"]
TRAITS = ["gentle", "curious", "quiet", "thoughtful", "careful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(l, s, g, "kindness") for l in LOCATIONS for s in SUPPLIES for g in GIFTS]


def explain_rejection() -> str:
    return "(No story: the requested options do not fit this gentle decal-and-sharing world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about decals, a remainder, bravery, sharing, and kindness.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--supply", choices=SUPPLIES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--child1")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2")
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    candidates = [n for n in pool if n != avoid]
    return rng.choice(candidates)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combo_keys = [(l, s, g) for l, s, g, _ in valid_combos()]
    if args.location and args.location not in LOCATIONS:
        raise StoryError(explain_rejection())
    if args.supply and args.supply not in SUPPLIES:
        raise StoryError(explain_rejection())
    if args.gift and args.gift not in GIFTS:
        raise StoryError(explain_rejection())
    combos = [c for c in combo_keys
              if (args.location is None or c[0] == args.location)
              and (args.supply is None or c[1] == args.supply)
              and (args.gift is None or c[2] == args.gift)]
    if not combos:
        raise StoryError(explain_rejection())
    location, supply, gift = rng.choice(sorted(combos))
    c1_gender = args.child1_gender or rng.choice(["girl", "boy"])
    c2_gender = args.child2_gender or ("boy" if c1_gender == "girl" and rng.random() < 0.5 else "girl")
    child1 = args.child1 or _pick_name(rng, c1_gender)
    child2 = args.child2 or _pick_name(rng, c2_gender, avoid=child1)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        location=location,
        child1=child1,
        child1_gender=c1_gender,
        child2=child2,
        child2_gender=c2_gender,
        parent=parent,
        supply=supply,
        gift=gift,
    )


def _setup(world: World, p: StoryParams) -> tuple[Entity, Entity, Entity, Entity, Entity]:
    a = world.add(Entity(id=p.child1, kind="character", type=p.child1_gender, role="sharer"))
    b = world.add(Entity(id=p.child2, kind="character", type=p.child2_gender, role="receiver"))
    parent = world.add(Entity(id="Parent", kind="character", type=p.parent, role="parent", label="the parent"))
    supply = world.add(Entity(id="supply", kind="thing", type="supply", label=SUPPLIES[p.supply].label))
    gift = world.add(Entity(id="gift", kind="thing", type="gift", label=GIFTS[p.gift].label))
    a.memes["bravery"] = 4.0
    b.memes["gratitude"] = 0.0
    parent.memes["kindness"] = 4.0
    world.facts["supply_cfg"] = SUPPLIES[p.supply]
    world.facts["gift_cfg"] = GIFTS[p.gift]
    return a, b, parent, supply, gift


def _scene_open(world: World, a: Entity, b: Entity, parent: Entity, supply: Supply, gift: Gift) -> None:
    world.say(
        f"On a quiet afternoon at the {world.location.id.replace('_', ' ')}, {a.id} and {b.id} sat with {world.location.scene}. "
        f"They were making something special together, and the last piece they needed was {supply.phrase}."
    )
    world.say(world.location.place_line)
    world.say(
        f'{a.id} wanted to finish {gift.phrase}, and {b.id} watched the tiny pile of scraps. '
        f'There was only {supply.remainder_label} left.'
    )


def _offer(world: World, a: Entity, b: Entity, parent: Entity, supply: Supply, gift: Gift) -> None:
    a.memes["bravery"] += 1.0
    b.memes["sharing"] += 1.0
    world.say(
        f"{a.id} took a small breath and smiled. \"I can share the remainder,\" {a.id} said, even though it was the last one."
    )
    world.say(
        f"{b.id} looked surprised, then pleased. {b.id} had wanted a turn too, and now both children could help."
    )


def _kindness_turn(world: World, a: Entity, b: Entity, parent: Entity, supply: Supply, gift: Gift) -> None:
    parent.memes["kindness"] += 1.0
    a.memes["kindness"] += 1.0
    b.memes["kindness"] += 1.0
    world.say(
        f"The parent smiled and said, \"That was brave of you, {a.id}. Sharing the remainder is kind, and kind choices make a home feel bigger.\""
    )
    world.say(
        f"{a.id} handed over the decal sheet carefully, and {b.id} pressed the last little decal onto the paper."
    )


def _finish(world: World, a: Entity, b: Entity, parent: Entity, supply: Supply, gift: Gift) -> None:
    world.say(
        f"At last, {gift.phrase} was done. The last decal made a bright little shine, and the remainder had become part of a gift."
    )
    world.say(
        f"{a.id} and {b.id} stood back and laughed. {parent.label_word.capitalize()} looked at the finished piece and said it was lovely."
    )


def tell(params: StoryParams) -> World:
    world = World(LOCATIONS[params.location])
    a, b, parent, supply, gift = _setup(world, params)
    _scene_open(world, a, b, parent, supply, gift)
    world.para()
    _offer(world, a, b, parent, supply, gift)
    world.para()
    _kindness_turn(world, a, b, parent, supply, gift)
    world.para()
    _finish(world, a, b, parent, supply, gift)
    world.facts.update(
        child1=a, child2=b, parent=parent, supply=supply, gift=gift,
        outcome="shared", remainder_used=True, bravery=a.memes["bravery"],
        sharing=b.memes["sharing"], kindness=parent.memes["kindness"],
        location=world.location,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    supply = f["supply_cfg"]
    gift = f["gift_cfg"]
    return [
        f'Write a slice-of-life story for a young child that includes the words "decal" and "remainder" and ends with sharing.',
        f"Tell a gentle story where {f['child1'].id} has only {supply.remainder_label} left, gets brave, and shares it with {f['child2'].id}.",
        f"Write a warm family story about kindness, where a last decal becomes part of {gift.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    parent = f["parent"]
    supply = f["supply_cfg"]
    gift = f["gift_cfg"]
    return [
        QAItem(
            question="What was the last piece the children had?",
            answer=f"They had only the remainder of the decal sheet left. That tiny leftover was enough for one more careful choice, and it became part of the finished craft."
        ),
        QAItem(
            question=f"What did {a.id} do that was brave?",
            answer=f"{a.id} said they could share the remainder instead of keeping it all. That brave choice let both children take part, and it turned a small leftover into something kind."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the craft finished and everyone smiling. The remainder was used up, the decal made the page shine, and the parent praised the children for being kind."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a decal?",
            answer="A decal is a picture or sticker you press onto a surface. It can decorate paper, boxes, cups, or other smooth things."
        ),
        QAItem(
            question="What does remainder mean?",
            answer="A remainder is what is left after the larger part has been used. It can be small, but it may still be useful."
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something with you. It is a kind way to make sure everyone gets a turn."
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is choosing actions that help, comfort, or include other people. Small kind choices can change a whole moment."
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something a little hard even when you feel nervous. It does not mean you are never scared."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
shared(X) :- child(X).
kind(X) :- child(X), kindness(X).
brave(X) :- child(X), bravery(X).
finished :- shared_remainder, kind(X).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for lid in LOCATIONS:
        lines.append(asp.fact("location", lid))
    for sid in SUPPLIES:
        lines.append(asp.fact("supply", sid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    lines.append(asp.fact("bravery_min", int(BRAVERY_MIN)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    import asp
    py = set(valid_combos())
    # simple smoke: solve a tiny normal story via python
    try:
        sample = generate(resolve_params(argparse.Namespace(location=None, supply=None, gift=None, child1=None, child1_gender=None, child2=None, child2_gender=None, parent=None), random.Random(7)))
        assert sample.story
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        return 1
    if set(asp_valid_combos()) != py:
        rc = 1
        print("MISMATCH: ASP and Python combo sets differ.")
    else:
        print(f"OK: ASP and Python combo sets match ({len(py)} combos).")
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    return [(l, s, g) for l, s, g, _ in [(x[0], x[1], x[2], "kindness") for x in valid_combos()]]

def valid_combos() -> list[tuple[str, str, str, str]]:  # type: ignore[no-redef]
    return [(l, s, g, "kindness") for l in LOCATIONS for s in SUPPLIES for g in GIFTS]


def generate(params: StoryParams) -> StorySample:
    if params.location not in LOCATIONS or params.supply not in SUPPLIES or params.gift not in GIFTS:
        raise StoryError("Invalid story parameters.")
    world = tell(params)
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
    StoryParams(location="kitchen_table", child1="Maya", child1_gender="girl", child2="Noah", child2_gender="boy", parent="mother", supply="sticker_sheet", gift="book_fair_tag"),
    StoryParams(location="porch", child1="Theo", child1_gender="boy", child2="Ella", child2_gender="girl", parent="father", supply="letter_set", gift="name_tag"),
    StoryParams(location="living_room_floor", child1="Lily", child1_gender="girl", child2="Ben", child2_gender="boy", parent="mother", supply="star_roll", gift="lunch_note"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
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
