#!/usr/bin/env python3
"""
storyworlds/worlds/rental_flashback_pirate_tale.py
===================================================

A small standalone story world about a pirate, a rental, and a flashback.

Premise:
- A young pirate needs to rent a small boat or tool for a sea outing.
- The harbor keeper worries about return, damage, or late payment.
- A flashback explains why the pirate is extra careful or extra nervous.
- The story turns on a promise, a smart compromise, and a clean return.

This is intentionally tiny and classical: one domain, one tension, one turn,
one ending image.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    borrowed_from: Optional[str] = None
    borrowed_item: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {
                "wet": 0.0,
                "damage": 0.0,
                "dirt": 0.0,
                "coins": 0.0,
            }
        if not self.memes:
            self.memes = {
                "joy": 0.0,
                "worry": 0.0,
                "pride": 0.0,
                "embarrassment": 0.0,
                "trust": 0.0,
                "memory": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Harbor:
    place: str = "the harbor"
    weather: str = "windy"
    affords: set[str] = field(default_factory=lambda: {"rowboat", "lantern", "net"})


@dataclass
class RentalItem:
    id: str
    label: str
    phrase: str
    kind: str
    price: int
    risk: str
    splash: str
    repair: str
    return_detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    item: str
    name: str
    gender: str
    keeper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.flashback_used = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone = World(self.harbor)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.flashback_used = self.flashback_used
        return clone


ITEMS = {
    "rowboat": RentalItem(
        id="rowboat",
        label="rowboat",
        phrase="a small rowboat with blue paint",
        kind="boat",
        price=3,
        risk="scratched",
        splash="wet and scratched",
        repair="rub the scuffs with a cloth",
        return_detail="tied it neatly at the dock",
        tags={"boat", "water", "rental"},
    ),
    "lantern": RentalItem(
        id="lantern",
        label="lantern",
        phrase="a brass lantern with a glass door",
        kind="tool",
        price=1,
        risk="sooty",
        splash="smudged and sooty",
        repair="wipe the soot from the glass",
        return_detail="set it back on the counter",
        tags={"light", "rental"},
    ),
    "net": RentalItem(
        id="net",
        label="fishing net",
        phrase="a wide fishing net with a long handle",
        kind="tool",
        price=2,
        risk="tangled",
        splash="tangled and sandy",
        repair="shake out the knots",
        return_detail="rolled it up by the door",
        tags={"fish", "rental"},
    ),
}

KEEPERS = {
    "dockkeeper": "the dockkeeper",
    "captain": "the old captain",
}

NAMES = {
    "girl": ["Mira", "Nell", "Tia", "Ruby"],
    "boy": ["Finn", "Jace", "Oren", "Pip"],
}

TRAITS = ["brave", "eager", "curious", "careful", "stubborn", "lively"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for item_id, item in ITEMS.items():
        for gender in ("girl", "boy"):
            combos.append((item_id, gender))
    return combos


def explain_rejection(item: RentalItem) -> str:
    return f"(No story: the harbor does not have a sensible rental plan for {item.label}.)"


def explain_gender(item_id: str, gender: str) -> str:
    return f"(No story: try a different name for a {gender} pirate with the {ITEMS[item_id].label}.)"


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(NAMES[gender])


def flashback_line(pirate: Entity, item: RentalItem) -> str:
    if item.id == "rowboat":
        return (
            f"{pirate.id} remembered the day {pirate.pronoun('subject')} had once "
            f"borrowed a boat and brought it back late, with a torn rope and a red face."
        )
    if item.id == "lantern":
        return (
            f"{pirate.id} remembered a dark night when {pirate.pronoun('subject')} "
            f"had dropped a lamp and had to sweep up tiny glass beads."
        )
    return (
        f"{pirate.id} remembered a windy day when {pirate.pronoun('subject')} "
        f"had left a net in a heap and had to untangle it for a long time."
    )


def can_rent(item: RentalItem, pirate: Entity) -> bool:
    return pirate.memes["worry"] < 10


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for item in ITEMS.values():
        lines.append(asp.fact("item", item.id))
        lines.append(asp.fact("price", item.id, item.price))
        lines.append(asp.fact("risk", item.id, item.risk))
    for g in ("girl", "boy"):
        lines.append(asp.fact("gender", g))
    return "\n".join(lines)


ASP_RULES = r"""
can_rent(I) :- item(I), price(I, _), risk(I, _).
valid_story(I, G) :- can_rent(I), gender(G).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate rental story with a flashback.")
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--keeper", choices=list(KEEPERS))
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
    if args.item:
        item = ITEMS[args.item]
    else:
        item = ITEMS[rng.choice(list(ITEMS))]
    if args.gender and args.gender not in ("girl", "boy"):
        raise StoryError("bad gender")
    if args.gender and args.name is None:
        name = choose_name(args.gender, rng)
    else:
        gender = args.gender or rng.choice(["girl", "boy"])
        name = args.name or choose_name(gender, rng)
    gender = args.gender or ("girl" if name in NAMES["girl"] else "boy")
    keeper = args.keeper or rng.choice(list(KEEPERS))
    trait = args.trait or rng.choice(TRAITS)
    if not can_rent(item, Entity(id=name, type=gender)):
        raise StoryError(explain_rejection(item))
    return StoryParams(item=item.id, name=name, gender=gender, keeper=keeper, trait=trait)


def tell(params: StoryParams) -> World:
    harbor = Harbor()
    world = World(harbor)
    item = ITEMS[params.item]

    pirate = world.add(Entity(id=params.name, kind="character", type="pirate", traits=[params.trait]))
    keeper = world.add(Entity(id="keeper", kind="character", type=params.keeper, label=KEEPERS[params.keeper]))
    rental = world.add(Entity(
        id="rental",
        type=item.kind,
        label=item.label,
        phrase=item.phrase,
        owner=keeper.id,
        caretaker=keeper.id,
    ))
    rental.borrowed_from = keeper.id
    pirate.meters["coins"] = float(item.price)
    pirate.memes["trust"] = 1.0

    world.say(
        f"At {harbor.place}, a {params.trait} pirate named {pirate.id} came to rent {item.phrase}."
    )
    world.say(
        f"{KEEPERS[params.keeper].capitalize()} asked for {item.price} shiny coin{'s' if item.price != 1 else ''}, "
        f"and {pirate.id} counted them out carefully."
    )
    world.say(
        f"{pirate.id} liked the rental because it looked ready for a proper sea day."
    )

    world.para()
    world.say(
        f"Then the wind tugged at the mast, and {pirate.id} wanted to hurry off at once."
    )
    world.say(flashback_line(pirate, item))
    pirate.memes["memory"] += 1.0
    pirate.memes["worry"] += 1.0
    keeper.memes["worry"] += 1.0
    world.say(
        f"That memory made {pirate.id} slow down and hold the {item.label} with extra care."
    )

    world.para()
    if item.id == "rowboat":
        world.say(
            f"{pirate.id} tied a soft cloth on the oar handles so the hands would not slip."
        )
        pirate.meters["wet"] += 0.0
        rental.meters["damage"] += 0.0
    elif item.id == "lantern":
        world.say(
            f"{pirate.id} kept the lantern high and out of the splash, away from the sea spray."
        )
    else:
        world.say(
            f"{pirate.id} shook the net open first, so no knot could turn into a snag later."
        )

    pirate.memes["joy"] += 1.0
    keeper.memes["trust"] += 1.0
    world.say(
        f"The pirate finished the trip, came back at sunset, and returned the rental in good order."
    )
    world.say(
        f"{pirate.id} {item.return_detail}, and {KEEPERS[params.keeper]} nodded with a smile."
    )
    world.say(
        f"Because of the flashback, {pirate.id} had been careful, and the little rental stayed neat."
    )

    world.facts.update(
        pirate=pirate,
        keeper=keeper,
        rental=rental,
        item=item,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item: RentalItem = f["item"]
    pirate: Entity = f["pirate"]
    return [
        f'Write a short pirate story about a rental {item.label} and a remembered mistake.',
        f"Tell a child-friendly tale where {pirate.id} rents {item.phrase} at the harbor and thinks back to an older mistake.",
        f"Write a tiny pirate story with a flashback, a rental, and a neat return to the dock.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pirate: Entity = f["pirate"]
    item: RentalItem = f["item"]
    keeper: Entity = f["keeper"]
    return [
        QAItem(
            question=f"What did {pirate.id} rent at the harbor?",
            answer=f"{pirate.id} rented {item.phrase} from {KEEPERS[keeper.type]}.",
        ),
        QAItem(
            question=f"Why did {pirate.id} slow down before leaving?",
            answer=(
                f"{pirate.id} remembered an old mistake in a flashback, so "
                f"{pirate.pronoun('subject')} chose to be extra careful with the {item.label}."
            ),
        ),
        QAItem(
            question=f"How did the story end for the rental?",
            answer=(
                f"The rental came back neat and safe. {pirate.id} returned it at sunset, "
                f"and {KEEPERS[keeper.type]} smiled because the promise was kept."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    item: RentalItem = world.facts["item"]
    if item.id == "rowboat":
        return [QAItem("What is a rowboat?", "A rowboat is a small boat that people move with oars.")]
    if item.id == "lantern":
        return [QAItem("What is a lantern for?", "A lantern gives light in dark places.")]
    return [QAItem("What is a fishing net for?", "A fishing net helps catch fish or haul things from water.")]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:7}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(item="rowboat", name="Mira", gender="girl", keeper="dockkeeper", trait="careful"),
    StoryParams(item="lantern", name="Finn", gender="boy", keeper="captain", trait="curious"),
    StoryParams(item="net", name="Tia", gender="girl", keeper="dockkeeper", trait="brave"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_stories())} compatible stories")
        for item, gender in asp_valid_stories():
            print(f"  {item} {gender}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
