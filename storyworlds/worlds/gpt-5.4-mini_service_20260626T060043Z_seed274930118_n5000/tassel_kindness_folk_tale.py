#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tassel_kindness_folk_tale.py
================================================================================

A small folk-tale storyworld about a found tassel, a lonely need, and a
kindness that turns the day.

Premise:
- A child in a little village finds a bright tassel.
- A townsfolk elder has lost the tassel from a treasured cloak.
- The child must choose between keeping the pretty thing and practicing kindness.

Story shape:
- Setup: introduce the child, the village, and the tassel.
- Turn: the child notices someone else's loss and feels the tug of kindness.
- Resolution: the child returns the tassel, and the village answers with warmth.

The world is deliberately tiny and constraint-driven:
- Only reasonable stories are generated.
- The simulation tracks physical state in meters and emotional state in memes.
- The prose is state-driven rather than template-swapped.

Includes:
- generation and Q&A output
- trace output for the live world model
- inline ASP twin plus Python reasonableness gate
- verification of Python/ASP parity
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str = "village"


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    color: str
    owner_role: str
    can_be_lost: bool = True


@dataclass
class StoryParams:
    place: str
    gift: str
    child_name: str
    child_gender: str
    child_trait: str
    elder_role: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "village_green": Place(id="village_green", label="the village green"),
    "market_lane": Place(id="market_lane", label="the market lane"),
    "stone_bridge": Place(id="stone_bridge", label="the stone bridge"),
    "quiet_lane": Place(id="quiet_lane", label="the quiet lane"),
}

GIFTS = {
    "tassel": Gift(
        id="tassel",
        label="tassel",
        phrase="a bright tassel with red and gold threads",
        color="red and gold",
        owner_role="elder",
    )
}

CHILD_NAMES = ["Mina", "Toby", "Lena", "Pip", "Nora", "Jory", "Anya", "Rowan"]
TRAITS = ["kind-hearted", "curious", "gentle", "brave", "soft-spoken", "cheerful"]
ELDER_ROLES = ["grandmother", "grandfather", "weaver", "baker", "market woman"]

CURATED = [
    StoryParams(
        place="village_green",
        gift="tassel",
        child_name="Mina",
        child_gender="girl",
        child_trait="kind-hearted",
        elder_role="grandmother",
    ),
    StoryParams(
        place="market_lane",
        gift="tassel",
        child_name="Toby",
        child_gender="boy",
        child_trait="gentle",
        elder_role="weaver",
    ),
]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def child_pronoun(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def place_opening(place: Place) -> str:
    return {
        "village_green": "The village green lay bright under the morning sun.",
        "market_lane": "The market lane smelled of bread and apples, and the stalls were just waking up.",
        "stone_bridge": "The stone bridge stood over the water, where the wind liked to play.",
        "quiet_lane": "The quiet lane was narrow and still, with little footpaths at its edges.",
    }[place.id]


def elder_label(role: str) -> str:
    return {"grandmother": "grandmother", "grandfather": "grandfather", "weaver": "weaver",
            "baker": "baker", "market woman": "market woman"}[role]


# ---------------------------------------------------------------------------
# State / simulation
# ---------------------------------------------------------------------------
def reasonableness_gate(place: Place, gift: Gift) -> bool:
    return place.id in PLACES and gift.id in GIFTS


def predict_kindness(world: World, child: Entity, elder: Entity, gift: Entity) -> dict:
    sim = world.copy()
    sim.get(child.id).memes["kindness"] = 1
    sim.get(gift.id).owner = elder.id
    sim.get(gift.id).worn_by = elder.id
    return {
        "returned": True,
        "warmth": 1,
    }


def tell_story(place: Place, gift_cfg: Gift, params: StoryParams) -> World:
    world = World(place)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        memes={"curiosity": 1.0, "kindness": 0.0, "want": 0.0, "glow": 0.0},
        meters={"steps": 0.0},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=params.elder_role,
        label=f"the {elder_label(params.elder_role)}",
        memes={"worry": 0.0, "relief": 0.0, "gratitude": 0.0},
        meters={"search": 0.0},
    ))
    gift = world.add(Entity(
        id=gift_cfg.id,
        kind="thing",
        type="gift",
        label=gift_cfg.label,
        phrase=gift_cfg.phrase,
        owner=elder.id,
        caretaker=elder.id,
        worn_by=elder.id,
        meters={"shine": 1.0},
    ))

    # Setup
    world.say(place_opening(place))
    world.say(f"{child.label} was a {params.child_trait} child who liked little wonders.")
    world.say(f"One day, {child.label} found {gift.phrase} lying near the path.")
    child.memes["want"] += 1
    gift.meters["found"] = 1.0
    world.facts["child"] = child
    world.facts["elder"] = elder
    world.facts["gift"] = gift
    world.facts["place"] = place
    world.facts["params"] = params

    # Turn
    world.para()
    world.say(
        f"{child.label} held the tassel up to the light and smiled, for it was as bright as a berry."
    )
    elder.meters["search"] += 1
    elder.memes["worry"] += 1
    world.say(
        f"Then {child.label} heard a soft sigh from the lane: the {elder_label(params.elder_role)} was looking around, "
        f"hands empty and face sad."
    )
    child.memes["kindness"] += 1
    world.say(
        f"{child.label}'s heart gave a little turn. {child.label} knew the shiny thing was not meant to be kept in a pocket."
    )

    # Resolution
    world.para()
    world.say(
        f"{child.label} ran back and held out the tassel, saying, "
        f"\"I found this. I think it belongs with you.\""
    )
    gift.owner = elder.id
    gift.worn_by = elder.id
    gift.meters["returned"] = 1.0
    elder.memes["relief"] += 1
    elder.memes["gratitude"] += 1
    child.memes["glow"] += 1
    world.say(
        f"The {elder_label(params.elder_role)} laughed with relief and tied the tassel back where it belonged. "
        f"\"Kindness is a fine thread,\" {elder.pronoun('subject')} said, \"and it holds the whole cloth together.\""
    )
    world.say(
        f"So {child.label} went home with empty hands and a warm chest, and the little lane looked brighter for it."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    gift: Entity = world.facts["gift"]
    return [
        f'Write a short folk tale for a small child about a found {gift.label} and a choice to be kind.',
        f"Tell a gentle story set in {world.facts['place'].label} where {p.child_name} notices an elder's lost {gift.label} and returns it.",
        f'Write a village story that includes the word "{gift.label}" and ends with kindness making someone happy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    child: Entity = world.facts["child"]
    elder: Entity = world.facts["elder"]
    gift: Entity = world.facts["gift"]

    return [
        QAItem(
            question=f"What did {child.label} find on the path?",
            answer=f"{child.label} found {gift.phrase} lying near the path.",
        ),
        QAItem(
            question=f"Why did {child.label} give the tassel back?",
            answer=f"{child.label} saw that the {elder.label} was sad and missing it, so kindness won over keeping the pretty thing.",
        ),
        QAItem(
            question=f"How did the story end for {child.label} and the {elder_label(p.elder_role)}?",
            answer=f"The tassel was returned, the {elder.label} felt relief and gratitude, and {child.label} went home feeling warm and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tassel?",
            answer="A tassel is a little bunch of threads or cords that can hang from a cloak, a hat, or a curtain.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, share, or return something when it is the right thing to do.",
        ),
        QAItem(
            question="Why do people return lost things?",
            answer="People return lost things so the owner can have them back and feel less worried.",
        ),
    ]


# ---------------------------------------------------------------------------
# Formatting / trace
# ---------------------------------------------------------------------------
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
        if e.kind == "thing":
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- village(P).
gift(G) :- tassel(G).

compatible(P,G) :- place(P), gift(G).

story_ok(P,G) :- compatible(P,G).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("village", pid))
    for gid in GIFTS:
        lines.append(asp.fact("tassel", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = sorted((p, g) for p in PLACES for g in GIFTS if reasonableness_gate(PLACES[p], GIFTS[g]))
    asp_set = asp_valid_combos()
    if py == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and clingo:")
    print("  python:", py)
    print("  asp:   ", asp_set)
    return 1


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale about a tassel and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--elder", choices=ELDER_ROLES)
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
    if args.place and args.gift:
        if not reasonableness_gate(PLACES[args.place], GIFTS[args.gift]):
            raise StoryError("No story: that place and gift cannot make a reasonable tassel folk tale.")
    place = args.place or rng.choice(list(PLACES))
    gift = args.gift or "tassel"
    name = args.name or rng.choice(CHILD_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    trait = args.trait or rng.choice(TRAITS)
    elder = args.elder or rng.choice(ELDER_ROLES)
    return StoryParams(place=place, gift=gift, child_name=name, child_gender=gender, child_trait=trait, elder_role=elder)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    gift_cfg = GIFTS[params.gift]
    if not reasonableness_gate(place, gift_cfg):
        raise StoryError("Invalid story parameters.")
    world = tell_story(place, gift_cfg, params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combo(s):")
        for p, g in combos:
            print(f"  {p} / {g}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.gift} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
