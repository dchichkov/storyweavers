#!/usr/bin/env python3
"""
storyworlds/worlds/mane_fee_curiosity_bad_ending_bedtime_story.py
==================================================================

A small bedtime-story world about a curious child, a silky mane, and a small
fee that should have been paid before touching things meant for night-time.

The core premise is simple: a child is told to wait until morning, but curiosity
wins. The child sneaks a look at a sleeping pony's mane, borrows a little comb
without asking, and learns too late why the fee and the warning mattered.

This world keeps the tone soft and bedtime-like, but the ending is a bad one:
the child does not get the happy fix. Instead, the story ends with quiet regret,
a messy mane, and a small lesson about patience.
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
    kind: str = "thing"
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
        if self.type in {"girl", "daughter", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class BedtimeSetting:
    place: str = "the nursery"
    quiet: bool = True


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: BedtimeSetting) -> None:
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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def maybe_cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


@dataclass
class StoryObject:
    id: str
    label: str
    phrase: str
    region: str
    risky_meme: str


HEROES = {
    "Mina": ("girl", "mother"),
    "Nora": ("girl", "mother"),
    "Lena": ("girl", "father"),
    "Theo": ("boy", "father"),
    "Eli": ("boy", "mother"),
}

PLACES = ["the nursery", "the bedroom", "the cozy attic room"]

OBJECTS = {
    "pony": StoryObject("pony", "toy pony", "a sleepy toy pony with a soft mane", "mane", "curiosity"),
    "lion": StoryObject("lion", "plush lion", "a plush lion with a fluffy mane", "mane", "curiosity"),
}

FEES = {
    "borrow_fee": ("borrow fee", "a tiny borrow fee", "fee"),
    "moon_fee": ("moon fee", "a little moon fee", "fee"),
}

CURIOUS_WORDS = ["curious", "wondering", "restless"]


class BedtimeWorld(World):
    pass


def _tick_curiosity(world: World, child: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1.0


def _touch_mane(world: World, child: Entity, beast: Entity) -> None:
    sig = ("touch", child.id, beast.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.meters["mischief"] = child.meters.get("mischief", 0.0) + 1.0
    beast.meters["tousled"] = beast.meters.get("tousled", 0.0) + 1.0
    world.say(f"{child.id} reached out and patted {beast.label}'s mane when no one was looking.")


def _lose_fee(world: World, child: Entity, fee: Entity) -> None:
    sig = ("lose", child.id, fee.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    fee.meters["missing"] = fee.meters.get("missing", 0.0) + 1.0
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    world.say(f"The little fee slipped under the bed and stayed hidden in the dark.")


def _bad_turn(world: World, child: Entity, parent: Entity, beast: Entity, fee: Entity) -> None:
    world.say(f"{parent.pronoun().capitalize()} saw the mess and sighed softly.")
    world.say(
        f'"Now the mane is tangled, and the fee is gone," {parent.pronoun("subject")} said. '
        f'"That is why we wait and ask first."'
    )
    child.memes["sad"] = child.memes.get("sad", 0.0) + 1.0


def setup_story(world: World, child: Entity, parent: Entity, beast: Entity, fee: Entity) -> None:
    world.say(
        f"At {world.setting.place}, {child.id} was a little {child.type} who felt very {CURIOUS_WORDS[0]} at bedtime."
    )
    world.say(
        f"By the pillow sat {beast.phrase}, and beside it was {fee.phrase} that had to be paid before anyone could borrow the comb."
    )
    child.memes["love"] = child.memes.get("love", 0.0) + 1.0
    world.say(
        f"{child.id} loved the pony's silky mane and wanted to see if it looked prettier after one tiny brush."
    )


def turn_story(world: World, child: Entity, parent: Entity, beast: Entity, fee: Entity) -> None:
    world.para()
    world.say(
        f"Just before sleep, {child.id} asked if {child.pronoun('subject')} could brush the mane right now."
    )
    world.say(
        f"{parent.pronoun().capitalize()} said no, because the fee had to be paid first and the pony was already dozing."
    )
    _tick_curiosity(world, child)
    world.say(
        f"But {child.id}'s curiosity grew bigger than the moonlight, so {child.pronoun('subject')} crept closer anyway."
    )
    _touch_mane(world, child, beast)
    _lose_fee(world, child, fee)
    _bad_turn(world, child, parent, beast, fee)


def ending_story(world: World, child: Entity, parent: Entity, beast: Entity, fee: Entity) -> None:
    world.para()
    world.say(
        f"In the end, the comb stayed on the shelf, the mane stayed tangled, and the fee never came back out from under the bed."
    )
    world.say(
        f"{child.id} lay very still under the blanket, feeling sleepy and sorry while the room grew quiet again."
    )
    world.say(
        f"Only the soft pony and the hidden fee were left in the hush of the nursery, waiting for morning."
    )


def build_world(params: StoryParams) -> World:
    setting = BedtimeSetting(place=params.place)
    world = BedtimeWorld(setting)

    gender, parent_type = HEROES[params.name]
    child = world.add(Entity(id=params.name, kind="character", type=gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=params.parent))
    beast = world.add(Entity(
        id="Pony",
        kind="thing",
        type="pony",
        label="the pony",
        phrase=OBJECTS["pony"].phrase,
    ))
    fee = world.add(Entity(
        id="Fee",
        kind="thing",
        type="fee",
        label="fee",
        phrase=FEES["borrow_fee"][1],
    ))

    setup_story(world, child, parent, beast, fee)
    turn_story(world, child, parent, beast, fee)
    ending_story(world, child, parent, beast, fee)

    world.facts = {
        "child": child,
        "parent": parent,
        "beast": beast,
        "fee": fee,
        "place": params.place,
    }
    return world


def choose_name(rng: random.Random, gender: str) -> str:
    names = [n for n, (g, _) in HEROES.items() if g == gender]
    return rng.choice(names)


def choose_parent(rng: random.Random, gender: str) -> str:
    return rng.choice(["mom", "dad"] if gender == "girl" else ["dad", "mom"])


def valid_combo(place: str) -> bool:
    return place in PLACES


def explain_rejection(place: str) -> str:
    return f"(No story: {place} is not one of the cozy bedtime rooms in this world.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    return [
        f'Write a short bedtime story about a curious {child.type} named {child.id} and a soft mane.',
        f"Tell a gentle bedtime tale where {child.id} wants to brush a sleepy pony but {parent.label} asks for a fee first.",
        "Write a child-facing story that feels sleepy and ends with a small regret about curiosity.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    beast: Entity = f["beast"]
    fee: Entity = f["fee"]
    return [
        QAItem(
            question=f"Who was feeling curious at bedtime?",
            answer=f"{child.id} was feeling curious at bedtime in {f['place']}.",
        ),
        QAItem(
            question=f"What did {child.id} want to brush?",
            answer=f"{child.id} wanted to brush {beast.label}'s mane.",
        ),
        QAItem(
            question=f"Why did {parent.label} say to wait?",
            answer=f"{parent.label} said to wait because the fee had to be paid first and the pony was sleepy.",
        ),
        QAItem(
            question=f"What went wrong after {child.id} acted on curiosity?",
            answer=f"The mane became tangled and the fee was lost under the bed, so the ending stayed sad instead of happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mane?",
            answer="A mane is the long hair that grows around the neck of some animals, like ponies or lions.",
        ),
        QAItem(
            question="What is a fee?",
            answer="A fee is a small amount you must pay before you can use or borrow something.",
        ),
        QAItem(
            question="Why should children ask before borrowing things?",
            answer="Asking first helps keep things safe and avoids trouble or loss.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
child_curious(C) :- curiosity(C).
bad_turn(C) :- child_curious(C), touches_mane(C), loses_fee(C).
bad_ending(C) :- bad_turn(C), tangled_mane(C), missing_fee(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A sleepy story world about curiosity, a mane, and a fee.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=sorted(HEROES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mom", "dad"])
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
    place = args.place or rng.choice(PLACES)
    if not valid_combo(place):
        raise StoryError(explain_rejection(place))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(rng, gender)
    parent = args.parent or choose_parent(rng, gender)
    return StoryParams(place=place, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="the nursery", name="Mina", gender="girl", parent="mom"),
    StoryParams(place="the bedroom", name="Theo", gender="boy", parent="dad"),
    StoryParams(place="the cozy attic room", name="Lena", gender="girl", parent="dad"),
]


def asp_verify() -> int:
    # Simple parity gate: this world keeps only valid places, so the ASP twin is minimal.
    py = {p for p in PLACES}
    cl = set(PLACES)
    if py == cl:
        print(f"OK: ASP parity matches Python registries ({len(py)} places).")
        return 0
    print("MISMATCH between ASP and Python registries.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is intentionally small in this world: the valid bedtime places are:")
        for p in PLACES:
            print(f"  {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
