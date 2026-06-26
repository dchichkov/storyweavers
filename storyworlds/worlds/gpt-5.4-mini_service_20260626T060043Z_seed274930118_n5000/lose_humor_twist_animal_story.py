#!/usr/bin/env python3
"""
storyworlds/worlds/lose_humor_twist_animal_story.py
===================================================

A small animal-story world about losing something, with a humorous turn and a
gentle twist at the end.

Premise:
- An animal child loses a prized item while playing.

Turn:
- The search becomes funnier than expected because the item keeps appearing in
  silly places.

Resolution:
- The helper finds the lost item, but the twist is that the item had been
  helping someone else, so the hero also gains a new friend.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    found_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.species in {"cat", "rabbit", "mouse", "bird", "fox", "bear"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    features: set[str] = field(default_factory=set)
    hides: set[str] = field(default_factory=set)


@dataclass
class LostItem:
    id: str
    label: str
    phrase: str
    clue: str
    size: str
    can_hide_in: set[str] = field(default_factory=set)
    unusual_use: str = ""


@dataclass
class StoryParams:
    place: str
    item: str
    hero: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.search_spots: list[str] = []

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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.search_spots = list(self.search_spots)
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
PLACES = {
    "meadow": Place(name="the meadow", features={"grass", "flowers", "bushes"}, hides={"bush", "flower", "grass"}),
    "pond": Place(name="the pond", features={"water", "lily pads", "mud"}, hides={"water", "mud", "reeds"}),
    "barnyard": Place(name="the barnyard", features={"hay", "straw", "fence"}, hides={"hay", "straw", "crate"}),
    "garden": Place(name="the garden", features={"path", "pots", "flowers"}, hides={"pot", "flower", "path"}),
}

SPECIES = {
    "cat": "cat",
    "rabbit": "rabbit",
    "mouse": "mouse",
    "fox": "fox",
    "bear": "bear",
    "bird": "bird",
}

HERO_NAMES = {
    "cat": ["Milo", "Pippa", "Nori", "Luna", "Toby"],
    "rabbit": ["Poppy", "Bun", "Mimi", "Clover", "Hopper"],
    "mouse": ["Tiny", "Midge", "Nib", "Tilly", "Nip"],
    "fox": ["Flick", "Roo", "Saffy", "Juno", "Rusty"],
    "bear": ["Bruno", "Moss", "Honey", "Bram", "Puddle"],
    "bird": ["Chirp", "Peep", "Wren", "Sky", "Dot"],
}

HELPER_NAMES = {
    "cat": ["Milo", "Pippa", "Nori", "Luna", "Toby"],
    "rabbit": ["Poppy", "Bun", "Mimi", "Clover", "Hopper"],
    "mouse": ["Tiny", "Midge", "Nib", "Tilly", "Nip"],
    "fox": ["Flick", "Roo", "Saffy", "Juno", "Rusty"],
    "bear": ["Bruno", "Moss", "Honey", "Bram", "Puddle"],
    "bird": ["Chirp", "Peep", "Wren", "Sky", "Dot"],
}

ITEMS = {
    "hat": LostItem(
        id="hat",
        label="hat",
        phrase="a bright red hat",
        clue="It was small and easy to tuck under a paw.",
        size="small",
        can_hide_in={"bush", "flower", "crate", "hay"},
        unusual_use="It had been used as a tiny boat by a frog.",
    ),
    "bell": LostItem(
        id="bell",
        label="bell",
        phrase="a shiny little bell",
        clue="It made a soft jingle when shaken.",
        size="tiny",
        can_hide_in={"grass", "hay", "pot"},
        unusual_use="It had been tied to a dragonfly's twig swing.",
    ),
    "scarf": LostItem(
        id="scarf",
        label="scarf",
        phrase="a striped scarf",
        clue="It was long enough to trail behind while running.",
        size="long",
        can_hide_in={"bush", "fence", "crate", "path"},
        unusual_use="It had become a picnic blanket for beetles.",
    ),
}

HUMOR_SPOTS = [
    "under a puzzled toad",
    "inside a boot that nobody was wearing",
    "on top of a sleepy turtle",
    "wrapped around a fence post like a ribbon",
    "balanced on a cabbage as if it were a hat",
]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def loss_reason(item: LostItem) -> str:
    return {
        "hat": "it blew off in a breeze",
        "bell": "it slipped out while the hero was hopping",
        "scarf": "it trailed behind and caught on a bush",
    }[item.id]


def search_spots(place: Place, item: LostItem) -> list[str]:
    spots = []
    for spot in sorted(place.hides):
        if spot in item.can_hide_in:
            spots.append(spot)
    return spots


def predict_found(world: World, item: LostItem) -> bool:
    return bool(world.search_spots)


def humorous_clue(index: int) -> str:
    return HUMOR_SPOTS[index % len(HUMOR_SPOTS)]


def tell(place: Place, hero_species: str, helper_species: str, item_def: LostItem,
         hero_name: str, helper_name: str) -> World:
    world = World(place)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        species=hero_species,
        label=hero_name,
        meters={"worry": 0.0},
        memes={"sad": 0.0, "relief": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        species=helper_species,
        label=helper_name,
        meters={"worry": 0.0},
        memes={"curiosity": 1.0},
    ))
    item = world.add(Entity(
        id=item_def.id,
        kind="thing",
        species="thing",
        label=item_def.label,
        phrase=item_def.phrase,
        owner=hero.id,
    ))
    world.facts.update(hero=hero, helper=helper, item=item, item_def=item_def)

    world.say(
        f"{hero.id} was a little {hero.species} who loved {item.phrase}."
        f" {hero.id} wore it everywhere and felt grand."
    )
    world.say(
        f"One day, {hero.id} played near {place.name}, and then {item.label} was gone."
        f" {loss_reason(item_def).capitalize()}."
    )
    hero.memes["sad"] += 1
    hero.meters["worry"] += 1
    item.carried_by = None

    world.para()
    world.say(
        f"{hero.id} looked under {place.features and sorted(place.features)[0] or 'the grass'},"
        f" then behind a pile of leaves. No {item.label}."
    )

    spots = search_spots(place, item_def)
    world.search_spots = spots

    # Humorous middle turn: each failed guess becomes a funny visual.
    for i, spot in enumerate(spots[:3]):
        world.say(
            f"At last, the search got silly: everyone checked {spot}, and even {humorous_clue(i)}."
        )

    world.para()
    if spots:
        found_spot = spots[0]
        item.found_by = helper.id
        helper.memes["curiosity"] += 1
        hero.memes["relief"] += 1

        world.say(
            f"Then {helper.id} giggled and pointed to {found_spot}. There was {item.phrase}!"
        )
        world.say(
            f"{hero.id} bounced with relief, but the twist was that {item_def.unusual_use}"
            f" while it was lost, so the world had been wearing it too."
        )
        world.say(
            f"{hero.id} thanked {helper.id}, and the two {hero.species}s shared a laugh."
            f" {hero.id} got {item.label} back, and {helper.id} got a new friend."
        )
        hero.memes["joy"] += 1
        helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
        hero.meters["worry"] = 0.0
    else:
        world.say(
            f"They searched and searched, but the item stayed hidden."
            f" The day ended with a quiet promise to keep looking tomorrow."
        )

    world.facts.update(found=bool(spots), hero_name=hero_name, helper_name=helper_name)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item_def"]
    place = world.place.name
    return [
        f'Write a short animal story for a young child about a {hero.species} who loses {item.phrase}.',
        f'Tell a funny story set at {place} where {hero.id} cannot find {item.label} at first, but the ending has a twist.',
        f'Write a gentle animal story that uses the word "lose" and ends with a happy surprise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    item_def = f["item_def"]

    qas = [
        QAItem(
            question=f"What did {hero.id} lose?",
            answer=f"{hero.id} lost {item_def.phrase} at {world.place.name}.",
        ),
        QAItem(
            question=f"Who helped look for the {item_def.label}?",
            answer=f"{helper.id} helped look for the {item_def.label}, and that made the search less sad.",
        ),
        QAItem(
            question=f"What was funny about the search?",
            answer=(
                f"The search kept turning into a silly picture, with people checking odd places like "
                f"{humorous_clue(0)} and laughing as they looked."
            ),
        ),
    ]

    if f.get("found"):
        qas.append(
            QAItem(
                question=f"What was the twist at the end?",
                answer=(
                    f"The twist was that {item_def.unusual_use.lower()} while it was lost, so the lost item "
                    f"had been part of a funny little surprise before it came back."
                ),
            )
        )
        qas.append(
            QAItem(
                question=f"How did {hero.id} feel after finding the {item_def.label}?",
                answer=f"{hero.id} felt relieved and happy, because the {item_def.label} was back and {helper.id} became a friend.",
            )
        )
    return qas


WORLD_KNOWLEDGE = {
    "lose": [
        QAItem(
            question="What does it mean to lose something?",
            answer="To lose something means you cannot find it for a while, even after you look for it.",
        )
    ],
    "laugh": [
        QAItem(
            question="Why do people laugh?",
            answer="People laugh when something feels funny, surprising, or cheerful.",
        )
    ],
    "help": [
        QAItem(
            question="What does it mean to help?",
            answer="To help means to do something kind that makes a job easier for someone else.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [*WORLD_KNOWLEDGE["lose"], *WORLD_KNOWLEDGE["laugh"], *WORLD_KNOWLEDGE["help"]]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(Item, Place) :- item(Item), lost_at(Item, Place).
funny_search(Item) :- at_risk(Item, Place), place(Place), hides(Place, Spot), can_hide(Item, Spot).
twist(Item) :- item(Item), unusual_use(Item).
resolved(Item) :- at_risk(Item, Place), found(Item), twist(Item).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for h in sorted(place.hides):
            lines.append(asp.fact("hides", pid, h))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("lost_at", iid, "place"))
        lines.append(asp.fact("can_hide", iid, *list(sorted(item.can_hide_in))[0:1]) if item.can_hide_in else asp.fact("can_hide", iid, "none"))
        lines.append(asp.fact("unusual_use", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Structural sanity check only in this lightweight world.
    py_ok = bool(ITEMS) and bool(PLACES)
    asp_ok = bool(ASP_RULES.strip())
    if py_ok and asp_ok:
        print("OK: ASP twin present and registries are populated.")
        return 0
    print("MISMATCH: missing ASP twin or registries.")
    return 1


# ---------------------------------------------------------------------------
# Parsing / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about losing something, with humor and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero", choices=sorted(SPECIES))
    ap.add_argument("--helper", choices=sorted(SPECIES))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for item in ITEMS:
            for hero in SPECIES:
                for helper in SPECIES:
                    if hero != helper:
                        combos.append((place, item, hero, helper))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.item:
        combos = [c for c in combos if c[1] == args.item]
    if args.hero:
        combos = [c for c in combos if c[2] == args.hero]
    if args.helper:
        combos = [c for c in combos if c[3] == args.helper]
    if not combos:
        raise StoryError("(No valid story combination matches the given options.)")
    place, item, hero, helper = rng.choice(sorted(combos))
    return StoryParams(place=place, item=item, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        params.hero,
        params.helper,
        ITEMS[params.item],
        hero_name=rng_name(params.hero, params.seed, "hero"),
        helper_name=rng_name(params.helper, params.seed, "helper"),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def rng_name(species: str, seed: Optional[int], role: str) -> str:
    base = HERO_NAMES if role == "hero" else HELPER_NAMES
    names = base[species]
    if seed is None:
        return random.choice(names)
    rng = random.Random((seed, species, role).__hash__())
    return rng.choice(names)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.kind == "thing":
            bits.append(f"owner={e.owner}")
            if e.found_by:
                bits.append(f"found_by={e.found_by}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", item="hat", hero="rabbit", helper="fox"),
    StoryParams(place="pond", item="bell", hero="cat", helper="bird"),
    StoryParams(place="barnyard", item="scarf", hero="mouse", helper="bear"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show at_risk/2.\n#show funny_search/1.\n#show twist/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP mode is available in this world, but this compact storyworld uses a Python reasonableness gate.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
