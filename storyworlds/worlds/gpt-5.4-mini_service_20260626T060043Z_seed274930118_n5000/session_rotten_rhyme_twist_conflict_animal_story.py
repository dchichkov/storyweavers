#!/usr/bin/env python3
"""
A small Animal-Story-style world about a rhyme session that goes wrong when
something rotten starts a conflict, then turns into a gentler twist.

The child-facing premise:
- A group of animals gather for a rhyme session.
- One animal brings a rotten treat, which causes a smell and a squabble.
- A helper notices the problem, switches the plan, and the group ends happily
  with a new rhyme and a fresh snack.

This script follows the Storyweavers world contract:
- standalone stdlib script
- shared results containers imported eagerly
- ASP helpers imported lazily inside ASP helpers
- generate / emit / main interface
- reasoning gate plus inline ASP_RULES twin
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("smell", "mess", "noise", "freshness"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "conflict", "shame", "curiosity", "kindness"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.species


@dataclass
class Place:
    name: str = "the meadow"
    indoor: bool = False


@dataclass
class Event:
    id: str
    title: str
    rhyme_line: str
    twist_line: str
    conflict_line: str
    fix_line: str
    snack: str
    mess_source: str
    atmosphere: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "meadow": Place("the meadow", indoor=False),
    "porch": Place("the porch", indoor=False),
    "den": Place("the den", indoor=True),
}

EVENTS = {
    "rotten_rhyme": Event(
        id="rotten_rhyme",
        title="rotten rhyme session",
        rhyme_line="They wanted to rhyme in a bright little ring, and every voice was ready to sing.",
        twist_line="Then one basket tipped, and a rotten smell rose up like a cloud.",
        conflict_line="The bad smell made the animals wrinkle their noses, and they began to argue over who should leave.",
        fix_line="A small helper swapped in fresh berries, opened the windows, and turned the quarrel into a new rhyme game.",
        snack="fresh berries",
        mess_source="rot",
        atmosphere="warm and bouncy",
    )
}

ANIMALS = {
    "bunny": {"species": "bunny", "label": "bunny", "trait": "bouncy"},
    "fox": {"species": "fox", "label": "fox", "trait": "clever"},
    "mouse": {"species": "mouse", "label": "mouse", "trait": "tiny"},
    "bear": {"species": "bear", "label": "bear", "trait": "steady"},
}

NAMES = ["Pip", "Milo", "Tia", "Nina", "Bram", "Wren", "Sage", "Clover"]


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A rhyme session is reasonable when there is a place, a group, and a way to
% turn the rotten conflict into a fresh ending.
reason(place(meadow)) :- place(meadow).
reason(place(porch)) :- place(porch).
reason(place(den)) :- place(den).

rotten_event(rotten_rhyme).
has_conflict(E) :- event(E), conflict(E).
has_fix(E) :- event(E), fix(E), fresh_snack(E).

valid_story(P, E) :- reason(P), event(E), has_conflict(E), has_fix(E).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for eid, ev in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("conflict", eid))
        lines.append(asp.fact("fix", eid))
        lines.append(asp.fact("fresh_snack", eid))
        lines.append(asp.fact("mess_source", eid, ev.mess_source))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    event: str
    hero: str
    hero_kind: str
    helper: str
    helper_kind: str
    seed: Optional[int] = None


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("The chosen place is not in this small animal world.")
    if params.event not in EVENTS:
        raise StoryError("The chosen event is not in this small animal world.")
    if params.hero_kind not in ANIMALS:
        raise StoryError("Unknown hero animal type.")
    if params.helper_kind not in ANIMALS:
        raise StoryError("Unknown helper animal type.")
    if params.hero_kind == params.helper_kind and params.hero == params.helper:
        raise StoryError("Hero and helper should not be the exact same character.")


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    place = PLACES[params.place]
    ev = EVENTS[params.event]
    world = World(place)

    hero_info = ANIMALS[params.hero_kind]
    helper_info = ANIMALS[params.helper_kind]

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        species=hero_info["species"],
        label=params.hero,
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        species=helper_info["species"],
        label=params.helper,
    ))
    snack = world.add(Entity(
        id="snack",
        kind="thing",
        species="berries",
        label=ev.snack,
        phrase=f"a bowl of {ev.snack}",
        owner=hero.id,
    ))
    rotten_snack = world.add(Entity(
        id="rotten_snack",
        kind="thing",
        species="berries",
        label="rotten berries",
        phrase="a basket of rotten berries",
        owner=hero.id,
    ))

    # Setup
    world.say(f"At {place.name}, {hero.id} the {hero_info['label']} and {helper.id} the {helper_info['label']} were ready for a rhyme session.")
    world.say(ev.rhyme_line)
    world.say(f"{hero.id} brought {rotten_snack.phrase}, hoping the group would still share a snack after the songs.")
    world.para()

    # Turn
    world.say(ev.twist_line)
    world.say(f"The rotten smell made {hero.id}'s nose crinkle and gave the air a sour, swirly feeling.")
    hero.meters["smell"] += 1
    hero.memes["curiosity"] += 1
    rotten_snack.meters["smell"] += 3
    rotten_snack.meters["mess"] += 2
    world.para()

    # Conflict
    hero.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    world.say(ev.conflict_line)
    world.say(f"{hero.id} wanted to keep the session going, but {helper.id} said the rotten basket had to go first.")
    world.say(f"They spoke over each other until the little rhyme circle felt bumpy and unkind.")
    world.para()

    # Resolution / twist
    helper.memes["kindness"] += 1
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0
    helper.memes["conflict"] = 0
    snack.meters["freshness"] += 3
    world.say(ev.fix_line)
    world.say(f"{helper.id} carried out the rotten basket, and {hero.id} placed {snack.phrase} in the middle of the circle.")
    world.say(f"Soon they were smiling again, making a new rhyme about {ev.snack} and the bright, clean air.")
    world.say(f"By the end, the little group was laughing in {place.name}, with the rotten smell gone and the fresh snack shining in the sun.")

    world.facts.update(
        place=params.place,
        event=params.event,
        hero=params.hero,
        helper=params.helper,
        hero_kind=params.hero_kind,
        helper_kind=params.helper_kind,
        snack=ev.snack,
        rotten=True,
        conflict=True,
        resolved=True,
    )
    return world


def valid_pairs() -> list[tuple[str, str]]:
    return [(place, event) for place in PLACES for event in EVENTS]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Animal Story about a {f["hero_kind"]} named {f["hero"]} who starts a rhyme session at {f["place"]} and runs into a rotten problem.',
        f"Tell a gentle story where {f['hero']} and {f['helper']} have a conflict about a rotten snack, then solve it with a twist.",
        f"Write a child-friendly story with rhyme, twist, and conflict that ends with fresh berries and a happy animal circle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Where did {f['hero']} and {f['helper']} hold the rhyme session?",
            answer=f"They held it at {PLACES[f['place']].name}.",
        ),
        QAItem(
            question=f"What caused the conflict in the story?",
            answer="The conflict started when a basket of rotten berries made the air smell bad and the animals began to argue.",
        ),
        QAItem(
            question=f"What fixed the problem at the end?",
            answer="The helper carried out the rotten snack and brought in fresh berries, which helped the group start a new rhyme game.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does rotten food mean?",
            answer="Rotten food is spoiled food that smells bad and should not be eaten.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound similar at the end, like cat and hat.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a problem or disagreement between characters.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a change that surprises the reader and turns the story in a new direction.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

HERO_KINDS = sorted(ANIMALS.keys())
HELPER_KINDS = sorted(ANIMALS.keys())


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: rhyme, twist, conflict, and a rotten surprise.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--event", choices=sorted(EVENTS))
    ap.add_argument("--hero")
    ap.add_argument("--hero-kind", choices=HERO_KINDS)
    ap.add_argument("--helper")
    ap.add_argument("--helper-kind", choices=HELPER_KINDS)
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
    place = args.place or rng.choice(sorted(PLACES))
    event = args.event or rng.choice(sorted(EVENTS))
    hero_kind = args.hero_kind or rng.choice(HERO_KINDS)
    helper_kind = args.helper_kind or rng.choice([k for k in HELPER_KINDS if k != hero_kind])
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    params = StoryParams(
        place=place,
        event=event,
        hero=hero,
        hero_kind=hero_kind,
        helper=helper,
        helper_kind=helper_kind,
    )
    reasonableness_gate(params)
    return params


CURATED = [
    StoryParams(place="meadow", event="rotten_rhyme", hero="Pip", hero_kind="bunny", helper="Wren", helper_kind="fox"),
    StoryParams(place="porch", event="rotten_rhyme", hero="Milo", hero_kind="mouse", helper="Sage", helper_kind="bear"),
    StoryParams(place="den", event="rotten_rhyme", hero="Tia", hero_kind="fox", helper="Clover", helper_kind="bunny"),
]


def asp_verify() -> int:
    import asp

    # Minimal parity check: the ASP twin should at least enumerate the same
    # event/place shape as the Python registry.
    program = asp_program("#show valid_story/2.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "valid_story"))
    expected = set((place, "rotten_rhyme") for place in PLACES)
    if atoms != expected:
        print("MISMATCH between ASP and Python registry gate.")
        print("ASP:", sorted(atoms))
        print("PY :", sorted(expected))
        return 1
    print(f"OK: ASP gate matches Python registry gate ({len(atoms)} combinations).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/2."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid story shapes:")
        for place, event in vals:
            print(f"  {place} / {event}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
            header = f"### {p.hero} / {p.helper} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
