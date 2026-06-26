#!/usr/bin/env python3
"""
storyworlds/worlds/sirloin_permanence_surprise_myth.py
======================================================

A small mythic storyworld about a feast, a surprise, and the wish that one
good thing might last forever.

The seed words point to a tale in which a humble kitchen offering -- a sirloin --
is chosen for a ritual feast, and the tension comes from permanence: whether the
gift can be kept, remembered, or made to endure. The surprise is the turning
instrument, as in a myth where an unexpected sign changes the meaning of the
meal and the people learn how to honor what cannot stay.

The world is modeled with physical meters and emotional memes:
- food can be shared, burned, hidden, offered, or preserved
- reverence, hope, worry, and wonder rise and fall as the rite unfolds
- the ending proves what changed in the world, not just in the wording

The story quality target is a child-facing myth:
- clear beginning with a small world and a cherished offering
- middle turn with a surprise omen or revelation
- ending image that shows the new understanding of permanence
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

MYTHIC_OPENERS = [
    "Long ago, when the hills still listened,",
    "In the first days of the valley,",
    "When the rivers were young and the stars seemed near,",
]

MYTHIC_TONES = [
    "old as a drumbeat",
    "bright as a temple bell",
    "quiet as moon-water",
    "deep as a cave prayer",
]

HERO_NAMES = [
    "Nera",
    "Ivo",
    "Sela",
    "Taro",
    "Mina",
    "Orin",
]

DEITY_NAMES = [
    "Ash",
    "Belen",
    "Cira",
    "Doro",
    "Esha",
    "Fenn",
]

# ---------------------------------------------------------------------------
# Shared model: physical meters and emotional memes.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    keeper: Optional[str] = None
    offered_by: Optional[str] = None
    eaten_by: Optional[str] = None
    placed_on: Optional[str] = None
    protected: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_food(self) -> bool:
        return self.kind == "food"


@dataclass
class Offering:
    id: str
    label: str
    phrase: str
    cost: str
    gives: str
    can_surprise: bool = False


@dataclass
class Place:
    id: str
    label: str
    mood: str
    affords: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.events = list(self.events)
        return clone


# ---------------------------------------------------------------------------
# Domain registries.
# ---------------------------------------------------------------------------
PLACES = {
    "hearth": Place(id="hearth", label="the hearth hall", mood="warm", affords={"feast", "offer", "preserve"}),
    "grove": Place(id="grove", label="the moon grove", mood="mysterious", affords={"feast", "offer", "surprise"}),
    "shore": Place(id="shore", label="the salt shore", mood="windy", affords={"feast", "offer", "surprise"}),
}

OFFERS = {
    "sirloin": Offering(
        id="sirloin",
        label="sirloin",
        phrase="a rich sirloin for the rite",
        cost="high",
        gives="satisfaction",
        can_surprise=True,
    ),
    "bread": Offering(
        id="bread",
        label="bread",
        phrase="a round loaf of bread",
        cost="small",
        gives="comfort",
    ),
    "honey": Offering(
        id="honey",
        label="honey",
        phrase="a clay jar of honey",
        cost="small",
        gives="sweetness",
    ),
}

RITES = {
    "feast": {
        "verb": "hold a feast",
        "action": "feasting",
        "result": "the people felt full and grateful",
    },
    "offer": {
        "verb": "make an offering",
        "action": "offering",
        "result": "the people bowed their heads and waited",
    },
    "preserve": {
        "verb": "keep something from fading",
        "action": "preserving",
        "result": "the people tried to make one good thing last",
    },
}

SURPRISES = {
    "sign": {
        "label": "a sign",
        "phrase": "a bright sign in the smoke",
        "turn": "The smoke rose in the shape of a spiral and pointed toward the stars.",
        "meaning": "the gift was not meant to stay whole forever; it was meant to be remembered",
    },
    "bird": {
        "label": "a bird",
        "phrase": "a white bird with ember eyes",
        "turn": "A white bird dropped a single feather into the fire and sang once.",
        "meaning": "what mattered could travel in a story even after the meal was gone",
    },
    "stone": {
        "label": "a stone",
        "phrase": "a stone that shone like milk",
        "turn": "A small stone warmed in the coals and revealed a bright mark.",
        "meaning": "the people could keep a mark of the feast, though the food itself would not last",
    },
}

WORLD_KNOWLEDGE = {
    "sirloin": [
        QAItem(
            question="What is sirloin?",
            answer="Sirloin is a tender cut of beef that people often cook for a special meal."
        )
    ],
    "permanence": [
        QAItem(
            question="What does permanence mean?",
            answer="Permanence means something lasts a long time and does not disappear quickly."
        )
    ],
    "surprise": [
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what the characters think or do."
        )
    ],
    "myth": [
        QAItem(
            question="What is a myth?",
            answer="A myth is an old-style story that explains something important with wonder and meaning."
        )
    ],
}

# ---------------------------------------------------------------------------
# Parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    rite: str
    offering: str
    surprise: str
    hero_name: str
    keeper_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about sirloin, permanence, and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--offering", choices=OFFERS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--keeper")
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


def _valid_combo(place: str, rite: str, offering: str, surprise: str) -> bool:
    if rite not in PLACES[place].affords:
        return False
    if offering == "sirloin" and rite not in {"feast", "offer", "preserve"}:
        return False
    if surprise == "sign" and place == "hearth":
        return True
    if surprise == "bird" and place in {"grove", "shore"}:
        return True
    if surprise == "stone" and rite == "preserve":
        return True
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in PLACES:
        for rite in RITES:
            for offering in OFFERS:
                for surprise in SURPRISES:
                    if _valid_combo(place, rite, offering, surprise):
                        out.append((place, rite, offering, surprise))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.rite is None or c[1] == args.rite)
              and (args.offering is None or c[2] == args.offering)
              and (args.surprise is None or c[3] == args.surprise)]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    place, rite, offering, surprise = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    keeper_name = args.keeper or rng.choice(DEITY_NAMES)
    return StoryParams(place=place, rite=rite, offering=offering, surprise=surprise,
                       hero_name=hero_name, keeper_name=keeper_name)


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_affords(P,R) :- affords(P,R).
valid(P,R,O,S) :- place_affords(P,R), offering(O), surprise(S), ok_combo(P,R,O,S).
#show valid/4.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for r in sorted(p.affords):
            lines.append(asp.fact("affords", pid, r))
    for oid in OFFERS:
        lines.append(asp.fact("offering", oid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for place in PLACES:
        for rite in RITES:
            for offering in OFFERS:
                for surprise in SURPRISES:
                    if _valid_combo(place, rite, offering, surprise):
                        lines.append(asp.fact("ok_combo", place, rite, offering, surprise))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP and Python match ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in python:", sorted(py - cl))
    print(" only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation.
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type="boy"))
    keeper = world.add(Entity(id=params.keeper_name, kind="character", type="deity"))
    offering = world.add(Entity(
        id=params.offering,
        kind="food",
        type=params.offering,
        label=OFFERS[params.offering].label,
        phrase=OFFERS[params.offering].phrase,
        owner=hero.id,
        keeper=keeper.id,
    ))
    surprise = world.add(Entity(
        id=params.surprise,
        kind="omen",
        type=params.surprise,
        label=SURPRISES[params.surprise]["label"],
        phrase=SURPRISES[params.surprise]["phrase"],
    ))

    world.facts.update(hero=hero, keeper=keeper, offering=offering, surprise=surprise, params=params)

    opener = random.choice(MYTHIC_OPENERS)
    tone = random.choice(MYTHIC_TONES)
    rite = RITES[params.rite]
    s = SURPRISES[params.surprise]

    world.say(f"{opener} {hero.id} came to {world.place.label} with a gift as {tone}.")
    world.say(f"{hero.id} carried {offering.phrase}, and {keeper.id} watched over the old custom.")
    world.say(f"That day, the people meant to {rite['verb']}, because they wanted {offering.label} to matter.")
    world.para()
    world.say(f"{hero.id} also wished for permanence, the kind that makes a good thing last.")
    world.say(f"But the old ones knew that some gifts are not kept forever; they are honored by being shared.")
    world.para()
    world.say(f"Then came the surprise: {s['turn']}")
    world.say(f"{hero.id} stared, and the crowd grew still, because the sign changed the meaning of the rite.")
    world.para()
    hero.memes["hope"] = 1
    hero.memes["wonder"] = 2
    hero.memes["worry"] = 0
    offering.meters["fresh"] = 0.0
    offering.meters["shared"] = 1.0
    offering.meters["remembered"] = 1.0
    world.say(f"So the people did not try to trap the moment. They let it pass, and let its meaning stay.")
    world.say(f"They shared the {offering.label}, and the surprise became a story that would last.")
    world.say(f"At the end, the {offering.label} was gone from the platter, but the lesson of permanence remained bright in every heart.")
    world.facts["turn"] = s["turn"]
    world.facts["meaning"] = s["meaning"]
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f"Write a short myth about {p.hero_name} bringing sirloin to {PLACES[p.place].label} and discovering what permanence really means.",
        f"Tell a child-friendly old-style story where a surprise changes the meaning of a feast and the people remember the sirloin.",
        f"Write a gentle myth with a clear beginning, surprise, and ending that explains how a gift can last as a memory.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    hero = f["hero"]
    offering = f["offering"]
    surprise = f["surprise"]
    qs = [
        QAItem(
            question=f"Who brought the sirloin to {PLACES[p.place].label}?",
            answer=f"{hero.id} brought the sirloin to {PLACES[p.place].label} for the old rite."
        ),
        QAItem(
            question=f"What did {hero.id} want to understand in the story?",
            answer=f"{hero.id} wanted to understand permanence, which means something can last a long time in memory or in the world."
        ),
        QAItem(
            question=f"What surprise changed the feast?",
            answer=f"The surprise was {surprise.phrase}, and it changed how everyone understood the offering."
        ),
        QAItem(
            question=f"What happened to the sirloin at the end?",
            answer=f"The sirloin was shared and eaten, so it did not stay on the platter, but the meaning of the gift stayed with the people."
        ),
    ]
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["sirloin"])
    out.extend(WORLD_KNOWLEDGE["permanence"])
    out.extend(WORLD_KNOWLEDGE["surprise"])
    out.extend(WORLD_KNOWLEDGE["myth"])
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:10} ({e.kind:8}) " + " ".join(bits))
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="grove", rite="feast", offering="sirloin", surprise="sign", hero_name="Nera", keeper_name="Ash"),
    StoryParams(place="shore", rite="offer", offering="sirloin", surprise="bird", hero_name="Ivo", keeper_name="Belen"),
    StoryParams(place="hearth", rite="preserve", offering="sirloin", surprise="stone", hero_name="Sela", keeper_name="Cira"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
