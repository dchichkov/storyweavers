#!/usr/bin/env python3
"""
A small storyworld: a dining-room space adventure with a bid for the captain's
chair, a brief quarrel, and a reconciliation that lets the mission continue.
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


@dataclass
class Person:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Item:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the dining room"


@dataclass
class Bid:
    object_id: str
    bid_text: str
    turn_text: str
    risky: str
    resolution: str


@dataclass
class StoryParams:
    bid: str
    place: str = "dining_room"
    hero: str = "Ari"
    hero_type: str = "boy"
    friend: str = "Mina"
    friend_type: str = "girl"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, obj):
        self.entities[obj.id] = obj
        return obj

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_bid() -> Bid:
    return Bid(
        object_id="starpad",
        bid_text="bid",
        turn_text="take turns at the starboard chair",
        risky="bump the juice cups",
        resolution="split the mission into captain turns",
    )


def ask_reasonable(world: World, bid: Bid) -> None:
    if "dining room" not in world.setting.place:
        raise StoryError("This story must happen in the dining room.")
    if bid.bid_text != "bid":
        raise StoryError("The seed word bid must appear in the story domain.")


def calm_meters(ent) -> None:
    ent.meters.setdefault("tension", 0.0)
    ent.meters.setdefault("joy", 0.0)
    ent.meters.setdefault("mess", 0.0)
    ent.memes.setdefault("hurt", 0.0)
    ent.memes.setdefault("pride", 0.0)
    ent.memes.setdefault("kindness", 0.0)
    ent.memes.setdefault("apology", 0.0)


def tell(params: StoryParams) -> World:
    setting = Setting(place="the dining room")
    world = World(setting)
    bid = build_bid()
    ask_reasonable(world, bid)

    hero = world.add(Person(id=params.hero, type=params.hero_type, traits=["bold", "curious"]))
    friend = world.add(Person(id=params.friend, type=params.friend_type, traits=["bright", "quick"]))
    table = world.add(Item(id="table", type="table", label="the dining table", phrase="a shiny dining table"))
    cups = world.add(Item(id="cups", type="cups", label="juice cups", phrase="two juice cups"))
    ship = world.add(Item(id=bid.object_id, type="control", label="cardboard starpad", phrase="a cardboard starpad for the ship"))
    hero.held_by = hero.id
    friend.held_by = friend.id

    for ent in [hero, friend, table, cups, ship]:
        calm_meters(ent)

    world.say(
        f"In the dining room, {hero.id} and {friend.id} turned the table into a tiny space station. "
        f"The cardboard starpad blinked in their imaginations, and the juice cups stood nearby like two round moons."
    )
    world.say(
        f"{hero.id} wanted to {bid.turn_text}, because {hero.pronoun('subject')} liked being the captain."
    )
    world.say(
        f"{friend.id} wanted the same chair, so the two friends made a loud {bid.bid_text} for the best seat."
    )
    hero.meters["tension"] += 1
    friend.meters["tension"] += 1
    hero.memes["pride"] += 1
    friend.memes["pride"] += 1

    world.para()
    world.say(
        f"They tugged a little too hard, and the starpad slid close to the juice cups. "
        f"That could make a sticky mess across the mission map."
    )
    hero.meters["mess"] += 1
    friend.meters["mess"] += 1
    hero.memes["hurt"] += 1
    friend.memes["hurt"] += 1

    world.say(
        f"Then {hero.id} stopped and looked at {friend.id}. {hero.pronoun('subject').capitalize()} took a breath and said, "
        f'"I do not want to wreck our ship."'
    )
    world.say(
        f"{friend.id} nodded. {friend.pronoun('subject').capitalize()} said, 'Me too. Let's fix this together.'"
    )
    hero.memes["apology"] += 1
    friend.memes["apology"] += 1
    hero.memes["kindness"] += 1
    friend.memes["kindness"] += 1

    world.para()
    world.say(
        f"So they made a reconciliation: first {friend.id} got the captain's chair, then {hero.id} got the next turn. "
        f"They moved the juice cups to the side, shared the starpad, and held the map with two careful hands."
    )
    hero.meters["tension"] = 0.0
    friend.meters["tension"] = 0.0
    hero.meters["joy"] += 1
    friend.meters["joy"] += 1

    world.say(
        f"Soon the dining room felt like a quiet launch bay again. {hero.id} and {friend.id} were smiling, "
        f"and their little space adventure was safe, fair, and fun."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        setting=setting,
        bid=bid,
        ship=ship,
        cups=cups,
        table=table,
        reconciled=True,
    )
    return world


KNOWLEDGE = {
    "bid": [
        (
            "What does it mean to bid for a turn?",
            "To bid for a turn means to ask strongly for a chance to go next or to use something first.",
        )
    ],
    "space": [
        (
            "Why do astronauts use careful steps in space?",
            "Astronauts use careful steps because floating or moving too fast can make it hard to stay safe and in control.",
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation means making up after a disagreement so people can be friendly again.",
        )
    ],
    "table": [
        (
            "What is a table used for?",
            "A table is a flat piece of furniture where people can eat, play, draw, or set things down.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    bid = f["bid"]
    return [
        f'Write a short story for a young child about a "{bid.bid_text}" in the dining room and a happy reconciliation.',
        f"Tell a space adventure where {hero.id} and {friend.id} argue over a chair, then make up and share the mission.",
        f'Write a gentle story set in the dining room that includes the word "{bid.bid_text}" and ends with friends working together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    bid = f["bid"]
    return [
        QAItem(
            question=f"What did {hero.id} and {friend.id} make in the dining room?",
            answer="They made a tiny space station out of the dining room table and played a make-believe space adventure.",
        ),
        QAItem(
            question=f"What did {hero.id} do when {hero.pronoun('subject')} wanted the captain's chair?",
            answer=f"{hero.id} made a bid for the captain's chair by asking to take turns at the starboard seat.",
        ),
        QAItem(
            question="How did the friends solve their problem?",
            answer="They reconciled by taking turns, moving the juice cups away, and sharing the starpad so the mission could continue safely.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["bid", "space", "reconciliation", "table"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
#show reconciled/1.
#show bid_for/2.
bid_for(H, chair) :- hero(H).
reconciled(H) :- bid_for(H, chair), friend(F), make_up(H, F).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("hero", "ari"),
            asp.fact("friend", "mina"),
            asp.fact("place", "dining_room"),
            asp.fact("object", "starpad"),
            asp.fact("problem", "cup_spill"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show bid_for/2.\n#show reconciled/1."))
    atoms = set(asp.atoms(model, "bid_for")) | set(asp.atoms(model, "reconciled"))
    expected = {("ari", "chair"), ("ari",)}
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness shape.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("got:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A dining-room space adventure with a bid and reconciliation.")
    ap.add_argument("--bid", default="bid", choices=["bid"])
    ap.add_argument("--place", default="dining_room", choices=["dining_room"])
    ap.add_argument("--name", default=None)
    ap.add_argument("--friend", default=None)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        bid=args.bid,
        place=args.place,
        hero=args.name or rng.choice(["Ari", "Nova", "Lena", "Milo", "Tess"]),
        hero_type=rng.choice(["boy", "girl"]),
        friend=args.friend or rng.choice(["Mina", "Zed", "Pia", "Rin", "Ollie"]),
        friend_type=rng.choice(["girl", "boy"]),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in getattr(ent, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(ent, "memes", {}).items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{ent.id}: {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bid_for/2.\n#show reconciled/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show bid_for/2.\n#show reconciled/1."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    for i in range(args.n):
        params = resolve_params(args, random.Random(base_seed + i))
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
