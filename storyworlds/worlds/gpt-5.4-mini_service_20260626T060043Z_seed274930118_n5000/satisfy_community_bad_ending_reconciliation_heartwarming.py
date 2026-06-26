#!/usr/bin/env python3
"""
A heartwarming storyworld about a small community, a hard-to-satisfy need, a bad
ending that gets repaired, and a reconciliation that leaves everyone kinder.

Premise:
A little community shares one small warm place and one important wish: everyone
wants to feel included and satisfied. One child, one helper, and one stubborn
problem create a hurt feeling that could end badly if nobody listens.

Story shape:
- beginning: the community gathers around a shared event
- middle: someone tries to satisfy the wish in the wrong way, causing a bad ending
- turn: a clearer explanation and a gentle apology
- resolution: reconciliation, shared care, and a warmer ending image

The domain is intentionally small and state-driven. Physical meters track items
and places; emotional memes track belonging, hurt, relief, and trust.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["warmth", "crowd", "hunger", "cleanliness", "noise", "quiet"]:
            self.meters.setdefault(k, 0.0)
        for k in ["belonging", "hurt", "trust", "worry", "relief", "joy", "shame", "pride"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    warmth: int
    can_share: bool = True


@dataclass
class Need:
    id: str
    label: str
    satisfies: str
    risk: str
    fix: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    promise: str
    repair: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    place: str
    need: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "hall": Place("hall", "the community hall", warmth=3, can_share=True),
    "kitchen": Place("kitchen", "the kitchen", warmth=4, can_share=True),
    "garden": Place("garden", "the garden", warmth=2, can_share=True),
}

NEEDS = {
    "food": Need(
        "food",
        "a warm snack",
        satisfies="fills bellies and eases grumbling",
        risk="some children get left out and hungry",
        fix="share the food fairly",
        keyword="satisfy",
        tags={"food", "share"},
    ),
    "song": Need(
        "song",
        "a group song",
        satisfies="brings voices together",
        risk="someone feels forgotten if they are not invited",
        fix="make room for every voice",
        keyword="community",
        tags={"song", "voice"},
    ),
    "game": Need(
        "game",
        "a circle game",
        satisfies="helps everybody join in",
        risk="the smallest child may be pushed aside",
        fix="slow the game and include everyone",
        keyword="community",
        tags={"game", "play"},
    ),
}

HELPERS = {
    "bowl": Helper("bowl", "a big bowl", promise="share portions", repair="passed the bowl around again"),
    "songbook": Helper("songbook", "the songbook", promise="pick a gentler song", repair="started the song over with a quieter tune"),
    "bench": Helper("bench", "a low bench", promise="make room", repair="moved the bench into a better circle"),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ada", "Ivy", "Zoe"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Owen", "Theo", "Leo"]
TRAITS = ["kind", "shy", "brave", "patient", "curious", "gentle"]


def choose_helper(need: Need) -> Helper:
    if need.id == "food":
        return HELPERS["bowl"]
    if need.id == "song":
        return HELPERS["songbook"]
    return HELPERS["bench"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in PLACES.values():
        if not place.can_share:
            continue
        for need in NEEDS.values():
            out.append((place.id, need.id))
    return out


def story_possible(place: Place, need: Need) -> bool:
    return place.can_share and bool(choose_helper(need))


def satisfy_move(world: World, child: Entity, need: Need) -> None:
    child.meters["crowd"] += 1
    child.memes["belonging"] += 1
    world.say(f"{child.id} wanted {need.label}, because it would {need.satisfies}.")


def bad_choice(world: World, child: Entity, need: Need) -> None:
    child.memes["worry"] += 1
    child.memes["hurt"] += 1
    child.memes["shame"] += 1
    world.say(
        f"But the first try was too hurried. It left {need.risk}, and that felt like a bad ending."
    )


def apology(world: World, helper: Entity, child: Entity, need: Need) -> None:
    helper.memes["trust"] += 1
    child.memes["trust"] += 1
    child.memes["hurt"] = max(0.0, child.memes["hurt"] - 1)
    world.say(
        f"{helper.id} slowed down, looked at {child.id}, and said sorry. "
        f"'{need.fix.capitalize()},' {helper.pronoun()} said softly."
    )


def reconcile(world: World, helper: Entity, child: Entity, need: Need) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.memes["belonging"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"Then they chose a kinder way. {helper.id} {choose_helper(need).repair}, "
        f"and the whole room felt warmer."
    )
    world.say(
        f"In the end, {child.id} was smiling again, and the community felt like one circle."
    )


def tell(place: Place, need: Need, name: str = "Mia", gender: str = "girl", helper: str = "grandparent") -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    guide = world.add(Entity(id=helper, kind="character", type=helper, label=helper))
    shared = world.add(Entity(id="shared", kind="thing", type=need.id, label=need.label, phrase=need.label, caretaker=guide.id))
    world.facts.update(child=child, guide=guide, shared=shared, need=need, place=place)

    child.memes["belonging"] += 1
    guide.memes["worry"] += 1
    world.say(f"{child.id} lived near {place.label}, where people tried to look after one another.")
    world.say(f"That day, everyone hoped for {need.label}, because it could {need.satisfies}.")
    satisfy_move(world, child, need)

    world.para()
    world.say(f"People gathered in {place.label} to make a little community moment.")
    world.say(f"{guide.id} tried to help quickly, but the first plan did not truly fit the feeling in the room.")
    bad_choice(world, child, need)

    world.para()
    apology(world, guide, child, need)
    reconcile(world, guide, child, need)

    shared.meters["cleanliness"] += 1
    shared.meters["quiet"] += 1
    child.memes["hurt"] = 0.0
    guide.memes["worry"] = 0.0
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    need = f["need"]
    place = f["place"]
    return [
        f'Write a heartwarming story about a small community in {place.label} where {child.id} wants {need.label}.',
        f'Tell a simple story where a helper tries to satisfy a need but makes a bad ending, then repairs it with reconciliation.',
        f'Write a child-friendly story that uses the words "satisfy" and "community" and ends with everyone feeling included again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    need = f["need"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {child.id} want in {place.label}?",
            answer=f"{child.id} wanted {need.label}, because it could {need.satisfies}.",
        ),
        QAItem(
            question=f"Why did the first plan feel like a bad ending?",
            answer=f"The first plan was too rushed, so it left {need.risk}. That hurt feelings instead of helping the community.",
        ),
        QAItem(
            question=f"How did {guide.id} help fix things?",
            answer=f"{guide.id} apologized, slowed down, and chose a kinder way. That helped everyone reconcile and feel included again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a community?",
            answer="A community is a group of people who live, work, or play near one another and try to help each other.",
        ),
        QAItem(
            question="What does it mean to satisfy a need?",
            answer="To satisfy a need means to give what is needed so a person can feel better, safer, or more comfortable.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who felt upset make peace again and treat each other kindly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(hall). place(kitchen). place(garden).
need(food). need(song). need(game).

valid(Place, Need) :- place(Place), need(Need), not impossible(Place, Need).

impossible(Place, Need) :- place(Place), need(Need), false.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for n in NEEDS.values():
        lines.append(asp.fact("need", n.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(valid_asp_combos())
    if py == lp:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch:")
    print("python only:", sorted(py - lp))
    print("asp only:", sorted(lp - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming community storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["grandparent", "neighbor", "teacher"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.need:
        combos = [c for c in combos if c[1] == args.need]
    if not combos:
        raise StoryError("No valid community story matches those choices.")
    place_id, need_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["grandparent", "neighbor", "teacher"])
    return StoryParams(place=place_id, need=need_id, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], NEEDS[params.need], params.name, params.gender, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="hall", need="food", name="Mia", gender="girl", helper="grandparent"),
    StoryParams(place="kitchen", need="song", name="Eli", gender="boy", helper="teacher"),
    StoryParams(place="garden", need="game", name="Nora", gender="girl", helper="neighbor"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_asp_combos()
        print(f"{len(combos)} compatible combos:")
        for p, n in combos:
            print(f"  {p} {n}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} at {p.place} with {p.need}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
