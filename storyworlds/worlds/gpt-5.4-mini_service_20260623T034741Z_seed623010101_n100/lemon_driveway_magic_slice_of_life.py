#!/usr/bin/env python3
"""
storyworlds/worlds/lemon_driveway_magic_slice_of_life.py
========================================================

A small slice-of-life storyworld about a driveway, a little bit of magic,
and a lemon that changes an ordinary afternoon into a warm surprise.

Seed tale:
---
On a quiet day, a child and a grown-up were standing in the driveway. The child
found a lemon on the pavement and wanted to make something nice with it. The
grown-up showed a little magic trick: a snap, a shimmer, and a simple bowl, so
the lemon could become lemonade instead of just sitting in the sun.

The child helped squeeze, stir, and taste. A few drops splashed on the ground,
but the magic kept the day cheerful. In the end, they sat on the driveway with
cold lemonade, smiling at the chalky sunshine and the little sparkle that made
an ordinary afternoon feel special.

World model notes:
---
    lemon on driveway         -> can be used to make lemonade
    magic used gently         -> adds sparkle and helps the task
    squeezing/stirring        -> drinks_meter += 1, joy += 1
    spill near driveway       -> a little mess on the ground
    shared lemonade           -> joy/love/resolution += 1
"""

from __future__ import annotations

import argparse
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    place: str = ""
    edible: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    requires: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Magic:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def place_allows(place: Place, item: Item, magic: Magic) -> bool:
    return item.kind in place.affords and magic.id in place.affords


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for iid, item in ITEMS.items():
            for mid, magic in MAGICS.items():
                if place_allows(place, item, magic):
                    out.append((pid, iid, mid))
    return out


@dataclass
class StoryParams:
    place: str = "driveway"
    item: str = "lemon"
    magic: str = "glimmer"
    name: str = "Mina"
    child_type: str = "girl"
    parent_type: str = "mother"
    trait: str = "curious"
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: driveway, lemon, and gentle magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.item is None or c[1] == args.item)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, magic = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, magic=magic, name=name,
                       child_type=child_type, parent_type=parent_type, trait=trait)


def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.child_type))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="the parent"))
    obj = world.add(Entity(id="item", type="thing", label=ITEMS[params.item].label,
                           phrase=ITEMS[params.item].phrase, owner=child.id, caretaker=parent.id,
                           place=params.place, edible=True))
    magic = world.add(Entity(id="magic", type="thing", label=MAGICS[params.magic].label,
                             phrase=MAGICS[params.magic].phrase, magical=True))
    world.facts.update(child=child, parent=parent, item=obj, magic=magic, params=params)
    return world


def story_text(world: World) -> str:
    f = world.facts
    child, parent, item, magic = f["child"], f["parent"], f["item"], f["magic"]
    world.say(f"On a quiet afternoon, {child.id} was in the {world.place.label} with {parent.label_word}.")
    world.say(f"{child.id} found {item.phrase} and held it like a tiny surprise.")
    world.para()
    world.say(f"{child.id} wanted to make something nice with the lemon, and {parent.label_word} smiled.")
    world.say(f'"Let me show you a little magic," {parent.label_word} said, and {magic.phrase}.')
    world.say(f"The air sparkled, and the lemon looked ready for a happier job than sitting in the sun.")
    world.para()
    child.memes["joy"] += 1
    parent.memes["calm"] += 1
    item.meters["squeezed"] += 1
    item.meters["juice"] += 1
    world.say(f"{child.id} helped squeeze and stir, and soon the lemon became lemonade.")
    world.say(f"A few drops splashed on the driveway, but nobody minded that little mess.")
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    parent.memes["love"] += 1
    world.para()
    world.say(f"At the end, they sat together with cold lemonade, watching the last sparkle fade in the driveway light.")
    world.say(f"{child.id} grinned at the bright cup and knew the ordinary afternoon had turned special.")
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, parent, item, magic = f["child"], f["parent"], f["item"], f["magic"]
    return [
        f'Write a gentle slice-of-life story for a 3-to-5-year-old about a child named {child.id}, a {item.label}, and a little bit of magic in the driveway.',
        f"Tell a small everyday story where {child.id} and {parent.label_word} use {magic.label} to make the {item.label} into something nice.",
        f'Write a short story set in a driveway that includes the word "lemon" and ends with a calm family moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, item, magic = f["child"], f["parent"], f["item"], f["magic"]
    return [
        QAItem(
            question=f"What did {child.id} find in the driveway?",
            answer=f"{child.id} found a lemon in the driveway. It was an ordinary little thing at first, but it became part of a special afternoon with {parent.label_word}.",
        ),
        QAItem(
            question=f"How did {parent.label_word} help {child.id} with the lemon?",
            answer=f"{parent.label_word.capitalize()} showed a little magic and helped turn the lemon into lemonade. That made the task feel playful and calm instead of plain.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The lemon turned into lemonade, and {child.id} ended up smiling with a cold cup in hand. The driveway went from ordinary to warm and cheerful.",
        ),
        QAItem(
            question=f"Why did the little mess on the driveway not cause trouble?",
            answer="It was only a few drops, so nobody worried about it. The small splash fit the slice-of-life mood and did not spoil the happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["magic"].tags) | set(world.facts["item"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
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


ASP_RULES = r"""
valid(P,I,M) :- place(P), item(I), magic(M), affords(P,I), affords(P,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("kind", iid, i.kind))
        lines.append(asp.fact("tags", iid, *sorted(i.tags)) if False else "")
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("tags", mid, *sorted(m.tags)) if False else "")
    return "\n".join(x for x in lines if x)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combo gates differ.")
        return 1
    rng = random.Random(777)
    try:
        params = resolve_params(argparse.Namespace(place=None, item=None, magic=None, name=None,
                                                   child_type=None, parent_type=None, trait=None),
                                rng)
        sample = generate(params)
        with redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as exc:  # noqa: BLE001
        print(f"MISMATCH: smoke test failed: {exc}")
        return 1
    print(f"OK: ASP parity and smoke test passed ({len(valid_combos())} combos).")
    return 0


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
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.item not in ITEMS or params.magic not in MAGICS:
        raise StoryError("(Invalid params.)")
    world = setup_world(params)
    story = story_text(world)
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(place="driveway", item="lemon", magic="glimmer", name="Mina", child_type="girl", parent_type="mother", trait="curious"),
    StoryParams(place="driveway", item="lemon", magic="spark", name="Theo", child_type="boy", parent_type="father", trait="gentle"),
    StoryParams(place="driveway", item="lemon", magic="twinkle", name="Lia", child_type="girl", parent_type="father", trait="cheerful"),
]

PLACES = {
    "driveway": Place(id="driveway", label="driveway", outdoors=True, affords={"fruit", "lemon", "glimmer", "spark", "twinkle"}),
}

ITEMS = {
    "lemon": Item(id="lemon", label="lemon", phrase="a bright lemon", kind="fruit", requires={"magic"}, tags={"lemon", "fruit"}),
}

MAGICS = {
    "glimmer": Magic(id="glimmer", label="glimmer", phrase="a glimmer and a tiny wink", effect="sparkle", tags={"magic", "shine"}),
    "spark": Magic(id="spark", label="spark", phrase="a spark of light", effect="make-change", tags={"magic", "shine"}),
    "twinkle": Magic(id="twinkle", label="twinkle", phrase="a twinkle and a soft shimmer", effect="sweeten", tags={"magic", "shine"}),
}

GIRL_NAMES = ["Mina", "Lia", "Ruby", "Nora", "Ella"]
BOY_NAMES = ["Theo", "Owen", "Milo", "Finn", "Ezra"]
TRAITS = ["curious", "gentle", "cheerful", "quiet", "helpful"]

KNOWLEDGE = {
    "lemon": [("What is a lemon?", "A lemon is a yellow fruit with a sour taste. People often squeeze it to make drinks.")],
    "magic": [("What is magic in a story?", "Magic is a pretend or wonderful force that can make surprising things happen in a story.")],
    "shine": [("What does sparkle mean?", "To sparkle means to shine in tiny bright bits, like little flashes of light.")],
}
KNOWLEDGE_ORDER = ["lemon", "magic", "shine"]


def valid_story_combo(params: StoryParams) -> bool:
    return params.place in PLACES and params.item in ITEMS and params.magic in MAGICS


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
