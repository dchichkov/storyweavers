#!/usr/bin/env python3
"""
storyworlds/worlds/down_heinie_sharing_comedy.py
=================================================

A tiny comedy storyworld about sharing, sitting down, and the ridiculous
trouble caused by a very crowded seat.

Seed tale sketch:
---
A child wanted to sit down on a small seat with a friend. Their heinie kept
sliding, they giggled, and an adult helped them share a bigger spot so nobody
had to wobble off the edge.
---

The world turns that sketch into a small simulation with:
- physical state: seat size, occupied space, wobble, and comfort
- emotional state: eagerness, embarrassment, laughter, and pride
- a shared fix: a better way to share the seat or cushion
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    shared_with: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("size", "wobble", "comfort", "occupied", "mess"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "embarrassment", "pride", "alarm", "laugh", "sharing"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    indoors: bool = True
    seat: str = "bench"


@dataclass
class Seat:
    id: str
    label: str
    phrase: str
    capacity: int
    bouncy: bool = False
    comfy: bool = False


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    bonus_capacity: int = 0
    bonus_comfort: float = 0.0
    bonus_wobble_reduction: float = 0.0


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

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    seat: str
    name: str
    friend: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, seat="bench"),
    "porch": Setting(place="the porch", indoors=False, seat="bench"),
    "playroom": Setting(place="the playroom", indoors=True, seat="cushion"),
    "yard": Setting(place="the yard", indoors=False, seat="blanket"),
}

SEATS = {
    "bench": Seat(id="bench", label="bench", phrase="a short wooden bench", capacity=2, comfy=False),
    "cushion": Seat(id="cushion", label="cushion", phrase="a puffy floor cushion", capacity=1, bouncy=True, comfy=True),
    "blanket": Seat(id="blanket", label="blanket", phrase="a big picnic blanket", capacity=3, comfy=True),
}

FIXES = {
    "big_cushion": Fix(id="big_cushion", label="bigger cushion", phrase="a bigger cushion", bonus_capacity=1, bonus_comfort=1.0),
    "extra_blanket": Fix(id="extra_blanket", label="extra blanket", phrase="an extra blanket", bonus_capacity=1, bonus_wobble_reduction=0.5),
    "soft_pillow": Fix(id="soft_pillow", label="soft pillow", phrase="a soft pillow", bonus_comfort=1.0, bonus_wobble_reduction=0.3),
}

GIRL_NAMES = ["Mia", "Lila", "Nora", "Zoe", "Penny", "Ada"]
BOY_NAMES = ["Ben", "Theo", "Max", "Leo", "Finn", "Sam"]
PARENTS = ["mother", "father"]
TRAITS = ["silly", "curious", "cheerful", "bouncy", "sly"]


def seat_is_tight(seat: Seat, people: int) -> bool:
    return people > seat.capacity


def choose_fix(seat: Seat, people: int) -> Optional[Fix]:
    for fix in FIXES.values():
        if people <= seat.capacity + fix.bonus_capacity:
            return fix
    return None


def asp_facts() -> str:
    import asp
    lines = []
    for sid, seat in SEATS.items():
        lines.append(asp.fact("seat", sid))
        lines.append(asp.fact("capacity", sid, seat.capacity))
        if seat.bouncy:
            lines.append(asp.fact("bouncy", sid))
        if seat.comfy:
            lines.append(asp.fact("comfy", sid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("bonus_capacity", fid, fix.bonus_capacity))
    return "\n".join(lines)


ASP_RULES = r"""
tight(Seat, People) :- seat(Seat), capacity(Seat, Cap), people(People), People > Cap.
solves(Fix, Seat, People) :- fix(Fix), bonus_capacity(Fix, B), seat(Seat), capacity(Seat, Cap), People =< Cap + B.
valid(Seat, People) :- seat(Seat), people(People), not tight(Seat, People).
valid_with_fix(Seat, People, Fix) :- tight(Seat, People), solves(Fix, Seat, People).
#show valid/2.
#show valid_with_fix/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid_combos() -> list[tuple[str, int]]:
    combos = []
    for sid, seat in SEATS.items():
        for people in range(1, 5):
            if not seat_is_tight(seat, people):
                combos.append((sid, people))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("people(1..4). #show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(python_valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches python gate ({len(p)} combos).")
        return 0
    print("MISMATCH:")
    if p - a:
        print(" only in python:", sorted(p - a))
    if a - p:
        print(" only in clingo:", sorted(a - p))
    return 1


def _sit(world: World, hero: Entity, friend: Entity, seat: Entity) -> None:
    people = 2
    seat.meters["occupied"] = people
    if seat_is_tight(SEATS[seat.type], people):
        seat.meters["wobble"] += 1
        hero.memes["embarrassment"] += 1
        friend.memes["laugh"] += 1
        world.say(f"{hero.id} and {friend.id} tried to sit down together, but the {seat.label} was a tight squeeze.")
        world.say(f"{hero.pronoun('possessive').capitalize()} heinie slid to the edge, and both kids started giggling.")
    else:
        seat.meters["comfort"] += 1
        hero.memes["joy"] += 1
        friend.memes["joy"] += 1
        world.say(f"{hero.id} and {friend.id} sat down on the {seat.label} with room to spare.")


def tell(place: Setting, seat_cfg: Seat, params: StoryParams) -> World:
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type="boy" if params.name in BOY_NAMES else "girl"))
    friend = world.add(Entity(id=params.friend, kind="character", type="boy" if params.friend in BOY_NAMES else "girl"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    seat = world.add(Entity(id=seat_cfg.id, type=seat_cfg.id, label=seat_cfg.label, phrase=seat_cfg.phrase))
    seat.meters["size"] = float(seat_cfg.capacity)
    world.facts.update(hero=hero, friend=friend, parent=parent, seat=seat, seat_cfg=seat_cfg, setting=place)

    hero.memes["sharing"] += 1
    world.say(f"{hero.id} was a {random.choice(TRAITS)} child who liked sharing, even when the seat looked small.")
    world.say(f"At {place.place}, {hero.id} found {seat.phrase} and wanted to share it with {friend.id}.")

    world.para()
    world.say(f"They both moved over and tried to fit.")
    _sit(world, hero, friend, seat)

    world.para()
    if seat_is_tight(seat_cfg, 2):
        fix = choose_fix(seat_cfg, 2)
        if fix is None:
            raise StoryError("No reasonable fix exists for that seat and number of kids.")
        fix_ent = world.add(Entity(id=fix.id, type="fix", label=fix.label, phrase=fix.phrase))
        seat.meters["comfort"] += fix.bonus_comfort
        seat.meters["wobble"] = max(0.0, seat.meters["wobble"] - fix.bonus_wobble_reduction)
        hero.memes["pride"] += 1
        hero.memes["embarrassment"] = 0
        world.say(f"{parent.label} smiled and brought {fix.phrase}, because sharing works better with a bigger spot.")
        world.say(f"After that, {hero.id} and {friend.id} sat down again, and this time the {seat.label} held them both.")
        world.say(f"{hero.pronoun('possessive').capitalize()} heinie stayed put, nobody wobbled off, and everybody laughed.")
        world.facts["fix"] = fix_ent
        world.facts["resolved"] = True
    else:
        world.say(f"The {seat.label} was big enough, so sharing felt easy from the start.")
        world.facts["fix"] = None
        world.facts["resolved"] = True

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    seat = f["seat"]
    return [
        f'Write a funny story for little kids about sharing {seat.label} and saying "down" with a wobbly heinie.',
        f"Tell a comedy where {hero.id} and {friend.id} try to sit down together and learn to share a {seat.label}.",
        f'Write a short cheerful story that includes the words "down" and "heinie" in a gentle sharing scene.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    seat = f["seat"]
    parent = f["parent"]
    items = [
        QAItem(
            question=f"Who tried to share the {seat.label}?",
            answer=f"{hero.id} and {friend.id} tried to share the {seat.label} together.",
        ),
        QAItem(
            question=f"Why did the kids giggle when they sat down?",
            answer=f"They giggled because the {seat.label} was a tight squeeze and {hero.id}'s heinie slid to the edge.",
        ),
        QAItem(
            question=f"What did {parent.label} do to help?",
            answer=f"{parent.label} brought a better sharing fix so the kids could sit down without wobbling.",
        ),
    ]
    if f.get("resolved"):
        items.append(
            QAItem(
                question=f"What changed at the end?",
                answer=f"At the end, the kids had a better place to share, so {hero.id}'s heinie stayed put and everyone laughed.",
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use part of something with you, like a seat or a toy.",
        ),
        QAItem(
            question="What is a heinie?",
            answer="A heinie is a kid-friendly word for the bottom part of your body that you sit on.",
        ),
        QAItem(
            question="What does it mean to sit down?",
            answer="To sit down means to lower your body until you are resting on a chair, bench, cushion, or the floor.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        ms = {k: round(v, 3) for k, v in e.meters.items() if v}
        mm = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if ms:
            bits.append(f"meters={ms}")
        if mm:
            bits.append(f"memes={mm}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", seat="bench", name="Mia", friend="Ben", parent="mother"),
    StoryParams(place="playroom", seat="cushion", name="Leo", friend="Nora", parent="father"),
    StoryParams(place="yard", seat="blanket", name="Zoe", friend="Sam", parent="mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about sharing a seat.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--seat", choices=SEATS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--parent", choices=PARENTS)
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
    place = args.place or rng.choice(list(SETTINGS))
    seat = args.seat or SETTINGS[place].seat
    if seat not in SEATS:
        raise StoryError("Unknown seat choice.")
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    parent = args.parent or rng.choice(PARENTS)
    if seat_is_tight(SEATS[seat], 2) and choose_fix(SEATS[seat], 2) is None:
        raise StoryError("That seat is too small for the sharing story to make sense.")
    return StoryParams(place=place, seat=seat, name=name, friend=friend, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], SEATS[params.seat], params)
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
        print(asp_program("#show valid/2.\n#show valid_with_fix/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp.solve(asp_program("people(1..4). #show valid/2. #show valid_with_fix/3."), models=0)
        if not models:
            print("No answer sets.")
            return
        for idx, model in enumerate(models, 1):
            print(f"Model {idx}:")
            for atom in model:
                print(f"  {atom}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
