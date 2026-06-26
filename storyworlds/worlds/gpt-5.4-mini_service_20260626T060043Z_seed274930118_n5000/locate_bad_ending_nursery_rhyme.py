#!/usr/bin/env python3
"""
storyworlds/worlds/locate_bad_ending_nursery_rhyme.py
=====================================================

A tiny nursery-rhyme story world about a child trying to locate something lost.
The stories stay short, rhythmic, and concrete, but the ending is a *bad ending*:
the search fails, the night grows dark, and the child must go home without the
missing thing.

The world is still state-driven:
- characters have meters and memes
- places matter
- clues can help or mislead
- the final scene proves what changed in the world

The core premise is a child who loses a small beloved object and looks for it
around a few simple places: under the bed, by the gate, near the pond, and in
the grass. The child searches with a lantern, asks a helper, and ends with no
locate success.
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    visible: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.kind == "group" else "it"


@dataclass
class Place:
    id: str
    label: str
    rhyme: str
    clue: str
    hides: set[str] = field(default_factory=set)
    safe: bool = True


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    hides_in: set[str]
    precious: bool = True


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.places: dict[str, Place] = {}
        self.items: dict[str, Item] = {}
        self.search_targets: list[str] = []
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_place(self, place: Place) -> Place:
        self.places[place.id] = place
        return place

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

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

    def copy(self) -> "World":
        import copy

        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.places = copy.deepcopy(self.places)
        clone.items = copy.deepcopy(self.items)
        clone.search_targets = list(self.search_targets)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    item: str
    place: str
    helper: str
    seed: Optional[int] = None


NAMES_GIRL = ["Mia", "Lily", "Nora", "Ava", "Rose", "Ella"]
NAMES_BOY = ["Tom", "Ben", "Finn", "Leo", "Max", "Sam"]

ITEMS = {
    "bell": Item(
        id="bell",
        label="little bell",
        phrase="a little silver bell",
        type="bell",
        hides_in={"grass", "mud", "nest", "bed"},
    ),
    "sock": Item(
        id="sock",
        label="striped sock",
        phrase="a striped red sock",
        type="sock",
        hides_in={"grass", "bed", "basket"},
    ),
    "kite": Item(
        id="kite",
        label="paper kite",
        phrase="a paper kite with a red tail",
        type="kite",
        hides_in={"tree", "shed", "fence"},
    ),
}

PLACES = {
    "bed": Place(
        id="bed",
        label="the bed",
        rhyme="The bed was soft and wide and warm, a sleepy place to hide from storm.",
        clue="a blanket hump and a fluttering seam",
        hides={"sock", "bell"},
    ),
    "gate": Place(
        id="gate",
        label="the gate",
        rhyme="The gate was gray with paint so old, and squeaked like hinges in the cold.",
        clue="a crack of wood and a loop of string",
        hides={"kite"},
    ),
    "pond": Place(
        id="pond",
        label="the pond",
        rhyme="The pond was still as still could be, with reeds that nodded silently.",
        clue="a reed crown and a shining ripple",
        hides={"bell"},
    ),
    "grass": Place(
        id="grass",
        label="the grass",
        rhyme="The grass was green in morning light, and brushed the feet of birds in flight.",
        clue="a soft patch and a tiny gleam",
        hides={"bell", "sock"},
    ),
}

HELPERS = {
    "cat": "a sleepy cat",
    "duck": "a bright little duck",
    "grandma": "Grandma",
    "rabbit": "a quick white rabbit",
}


class SearchWorld(World):
    def __init__(self) -> None:
        super().__init__()
        self.search_place = ""
        self.search_item = ""
        self.search_success = False
        self.search_clue = ""
        self.search_attempts = 0
        self.dusk = False


def _narrate_lost(world: SearchWorld, child: Entity, item: Entity) -> None:
    world.say(
        f"Little {child.id} had {child.pronoun('possessive')} {item.label}, "
        f"and loved it dearly."
    )
    world.say(
        f"But one bright day, the {item.label} was gone, and {child.id} said, "
        f'"I must locate it before the stars come out."'
    )


def _narrate_search(world: SearchWorld, child: Entity, helper: Entity, place: Place) -> None:
    world.say(f"{child.id} went to {place.label}. {place.rhyme}")
    world.say(f"{child.id} looked by the {place.label.removeprefix('the ')} and saw {place.clue}.")
    if helper.id != "none":
        world.say(f"{helper.label} came near and peeped, but could not help much at all.")


def _try_locate(world: SearchWorld, child: Entity, item: Entity, place: Place) -> bool:
    sig = ("search", place.id, item.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.search_attempts += 1
    world.search_place = place.id
    world.search_item = item.id
    if item.id in place.hides:
        world.search_clue = place.clue
        return False
    return False


def tell(params: StoryParams) -> SearchWorld:
    world = SearchWorld()
    child = world.add_entity(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"hope": 1.0, "worry": 0.0, "tired": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "sad": 0.0},
    ))
    parent = world.add_entity(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="mother" if params.parent == "mother" else "father",
        meters={"care": 1.0},
    ))
    item = world.add_entity(Entity(
        id="Item",
        kind="thing",
        type=params.item,
        label=ITEMS[params.item].label,
        phrase=ITEMS[params.item].phrase,
        owner=child.id,
        location="lost",
        meters={"lostness": 1.0},
    ))
    helper = world.add_entity(Entity(
        id="Helper",
        kind="character",
        type="helper",
        label=HELPERS[params.helper],
        meters={"quiet": 1.0},
    ))

    place = world.add_place(PLACES[params.place])
    world.add_item(ITEMS[params.item])
    world.search_targets = sorted(list(place.hides))

    _narrate_lost(world, child, item)
    world.para()

    world.say(f"{child.id} went first to {place.label}.")
    _narrate_search(world, child, helper, place)
    _try_locate(world, child, item, place)

    world.para()
    child.memes["worry"] += 1.0
    child.meters["tired"] += 1.0
    world.say(
        f"{child.id} searched and searched, but the little thing did not appear."
    )
    world.say(
        f"{child.id}'s hope grew small, and {child.pronoun('possessive')} feet grew slow."
    )
    world.say(
        f"At last the sky turned dim, and {child.id} had to go home without it."
    )
    world.dusk = True

    world.facts.update(
        child=child,
        parent=parent,
        item=item,
        helper=helper,
        place=place,
        failed=True,
        dusk=world.dusk,
    )
    return world


def generation_prompts(world: SearchWorld) -> list[str]:
    f = world.facts
    return [
        f"Write a short nursery rhyme story where {f['child'].id} tries to locate {f['item'].phrase}.",
        f"Tell a gentle rhyming story about a lost {f['item'].label} and a search at {f['place'].label}.",
        f"Write a small story for young children that ends in a bad ending when the missing thing is not found.",
    ]


def story_qa(world: SearchWorld) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    item: Entity = f["item"]
    place: Place = f["place"]
    helper: Entity = f["helper"]

    return [
        QAItem(
            question=f"What was {child.id} trying to locate?",
            answer=f"{child.id} was trying to locate {child.pronoun('possessive')} {item.label}, {item.phrase}.",
        ),
        QAItem(
            question=f"Where did {child.id} search first?",
            answer=f"{child.id} searched first at {place.label}, where the air was quiet and the clue was {place.clue}.",
        ),
        QAItem(
            question=f"Who came near while {child.id} looked?",
            answer=f"{helper.label} came near, but could not bring back the lost {item.label}.",
        ),
        QAItem(
            question=f"Did {child.id} find the missing {item.label}?",
            answer=f"No. {child.id} looked and looked, but the {item.label} stayed hidden, and the child went home at dusk.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended sadly: the sky grew dim, {child.id} was tired, and the lost thing was still not found.",
        ),
    ]


def world_knowledge_qa(world: SearchWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to locate something?",
            answer="To locate something means to find where it is.",
        ),
        QAItem(
            question="Why can a small thing be hard to find?",
            answer="A small thing can be hard to find because it can hide in grass, under cloth, or in a dark corner.",
        ),
        QAItem(
            question="What happens when it gets to be dusk?",
            answer="At dusk, the light goes away and it gets harder to see things outside.",
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


def dump_trace(world: SearchWorld) -> str:
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  dusk={world.dusk}")
    lines.append(f"  search_place={world.search_place} search_item={world.search_item}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- place_name(P).
item(I) :- item_name(I).
helper(H) :- helper_name(H).

can_hide(I, P) :- hides_in(I, P).
valid_search(P, I) :- place(P), item(I), can_hide(I, P).
bad_ending(P, I) :- valid_search(P, I).
#show valid_search/2.
#show bad_ending/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_name", pid))
        for h in sorted(p.hides):
            lines.append(asp.fact("hides_in", h, pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item_name", iid))
        for p in sorted(item.hides_in):
            lines.append(asp.fact("hides_in", iid, p))
    for hid in HELPERS:
        lines.append(asp.fact("helper_name", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme locate story with a bad ending.")
    ap.add_argument("--name", choices=NAMES_GIRL + NAMES_BOY)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for item in ITEMS:
            if item in PLACES[place].hides:
                combos.append((place, item, "bad"))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = []
    for place, item, _ in valid_combos():
        if args.place and place != args.place:
            continue
        if args.item and item != args.item:
            continue
        combos.append((place, item))
    if not combos:
        raise StoryError("No valid bad-ending locate story matches the given options.")

    place, item = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(name=name, gender=gender, parent=parent, item=item, place=place, helper=helper)


def generate(params: StoryParams) -> StorySample:
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


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_search/2.\n"))
    return sorted(set(asp.atoms(model, "valid_search")))


def asp_verify() -> int:
    py = set((p, i) for p, i, _ in valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python validity:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(name="Mia", gender="girl", parent="mother", item="bell", place="grass", helper="cat"),
    StoryParams(name="Tom", gender="boy", parent="father", item="sock", place="bed", helper="grandma"),
    StoryParams(name="Nora", gender="girl", parent="mother", item="kite", place="gate", helper="rabbit"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_search/2.\n#show bad_ending/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        combos = asp_valid()
        print(f"{len(combos)} valid locate searches:")
        for p, i in combos:
            print(f"  {p:5} {i}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: locate {p.item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
