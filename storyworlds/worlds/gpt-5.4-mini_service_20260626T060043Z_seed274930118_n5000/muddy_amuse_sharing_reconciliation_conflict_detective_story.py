#!/usr/bin/env python3
"""
storyworlds/worlds/muddy_amuse_sharing_reconciliation_conflict_detective_story.py
=================================================================================

A small standalone story world for a gentle detective tale with muddy clues,
sharing, conflict, and reconciliation.

Seed tale:
---
A little detective liked to solve little mysteries. One rainy afternoon, a muddy
trail appeared near the garden gate, and the friends who played there began to
argue about a shared toy. The detective followed the clue, learned who had
borrowed what, and helped everyone make peace again. In the end, they shared
the cleanup, laughed about the muddy surprise, and went back to play together.

Design notes:
---
- The world models physical meters and emotional memes.
- The story is driven by state: a muddy clue, a shared object, a conflict, a
  reconciliation, and a final image proving what changed.
- The prose is child-facing and authored, with a detective-story feel.
- Invalid explicit choices raise StoryError with a clear reason.
- Inline ASP rules mirror the Python reasonableness gate.
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
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("muddy", 0.0)
        self.meters.setdefault("clean", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("conflict", 0.0)
        self.memes.setdefault("trust", 0.0)
        self.memes.setdefault("curiosity", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_clean(self) -> bool:
        return self.meters["muddy"] < THRESHOLD


@dataclass
class Place:
    id: str
    label: str
    muddy: bool = False
    affords_sharing: bool = True
    affords_detective: bool = True


@dataclass
class Case:
    clue: str
    culprit: str
    borrowed_item: str
    shared_item: str
    result: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


@dataclass
class StoryParams:
    place: str
    detective: str
    suspect: str
    shared_item: str
    borrowed_item: str
    seed: Optional[int] = None


PLACES = {
    "garden_gate": Place(id="garden_gate", label="the garden gate", muddy=True),
    "backyard_path": Place(id="backyard_path", label="the backyard path", muddy=True),
    "shed_steps": Place(id="shed_steps", label="the shed steps", muddy=True),
}

SHARED_ITEMS = {
    "bucket": "a red bucket",
    "spade": "a tiny spade",
    "magnifier": "a round magnifying glass",
    "lantern": "a bright lantern",
}

BORROWED_ITEMS = {
    "cookie_jar": "a cookie jar",
    "chalk": "a box of chalk",
    "boots": "a pair of boots",
    "map": "a folded map",
}

DETECTIVE_NAMES = ["Mina", "Ruby", "Owen", "Theo", "Ivy", "Nia"]
OTHER_NAMES = ["Ben", "Lena", "Milo", "Sana", "Jules", "Pip"]
TRAITS = ["curious", "careful", "cheerful", "sharp-eyed"]


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    detective = world.add(Entity(
        id=params.detective,
        kind="character",
        type="girl" if params.detective in {"Mina", "Ruby", "Ivy", "Nia", "Lena", "Sana"} else "boy",
        label="the detective",
        phrase=f"little detective {params.detective}",
        memes={"joy": 1.0, "trust": 0.0, "conflict": 0.0, "curiosity": 2.0},
    ))
    suspect = world.add(Entity(
        id=params.suspect,
        kind="character",
        type="girl" if params.suspect in {"Mina", "Ruby", "Ivy", "Nia", "Lena", "Sana"} else "boy",
        label="the friend",
        phrase=f"friend {params.suspect}",
        memes={"joy": 1.0, "trust": 0.0, "conflict": 0.0, "curiosity": 1.0},
    ))
    shared_item = world.add(Entity(
        id="shared_item",
        kind="thing",
        type="toy",
        label=SHARED_ITEMS[params.shared_item],
        phrase=SHARED_ITEMS[params.shared_item],
        owner=detective.id,
        shared_with={suspect.id},
        meters={"muddy": 0.0, "clean": 1.0},
    ))
    borrowed_item = world.add(Entity(
        id="borrowed_item",
        kind="thing",
        type="thing",
        label=BORROWED_ITEMS[params.borrowed_item],
        phrase=BORROWED_ITEMS[params.borrowed_item],
        owner=suspect.id,
        meters={"muddy": 0.0, "clean": 1.0},
    ))

    world.facts = {
        "place": place,
        "detective": detective,
        "suspect": suspect,
        "shared_item": shared_item,
        "borrowed_item": borrowed_item,
        "case": Case(
            clue="muddy footprints",
            culprit=suspect.id,
            borrowed_item=params.borrowed_item,
            shared_item=params.shared_item,
            result="peace",
        ),
    }
    return world


def muddy_clue(world: World) -> None:
    d = world.facts["detective"]
    place = world.place
    d.memes["curiosity"] += 1
    world.say(
        f"One rainy afternoon, {d.id} noticed a muddy clue by {place.label}: "
        f"small prints leading in a neat line."
    )
    world.say("It looked like the kind of clue that wanted a careful eye.")


def conflict(world: World) -> None:
    d = world.facts["detective"]
    s = world.facts["suspect"]
    item = world.facts["shared_item"]
    borrowed = world.facts["borrowed_item"]

    d.memes["conflict"] += 1
    s.memes["conflict"] += 1
    d.memes["joy"] -= 0.2
    s.memes["joy"] -= 0.2
    world.say(
        f"Near the gate, {d.id} found {s.id} and a muddy {item.label} beside "
        f"{borrowed.label}."
    )
    world.say(
        f"{s.id} had borrowed the {item.label}, and now both friends wanted to "
        f"say it was not their fault."
    )
    world.say(
        f"Their voices got tight and shaky, and the little mystery turned into a conflict."
    )


def investigate(world: World) -> None:
    d = world.facts["detective"]
    s = world.facts["suspect"]
    item = world.facts["shared_item"]
    borrowed = world.facts["borrowed_item"]

    d.memes["curiosity"] += 1
    world.say(
        f"{d.id} did not shout. {d.pronoun().capitalize()} checked the muddy prints, "
        f"looked at the {borrowed.label}, and asked one quiet question at a time."
    )
    world.say(
        f"Then {d.id} noticed the clue: the mud matched the path where the friends "
        f"had carried the {item.label} together."
    )
    world.say(
        f"It was not a trick. It was just a shared game that had gone messy."
    )


def reconciliation(world: World) -> None:
    d = world.facts["detective"]
    s = world.facts["suspect"]
    item = world.facts["shared_item"]
    borrowed = world.facts["borrowed_item"]

    d.memes["conflict"] = 0.0
    s.memes["conflict"] = 0.0
    d.memes["trust"] += 1.0
    s.memes["trust"] += 1.0
    d.memes["joy"] += 1.0
    s.memes["joy"] += 1.0
    item.meters["muddy"] += 1.0
    borrowed.meters["muddy"] += 1.0
    world.say(
        f"{d.id} showed the answer to everyone: the mud came from the path, "
        f"not from a mean trick."
    )
    world.say(
        f"{s.id} sighed, then nodded. {s.id.capitalize()} and {d.id} shared the blame for the muddy game, "
        f"and the arguing melted away."
    )
    world.say(
        f"They picked up the {item.label} together and decided to clean it together."
    )
    world.say(
        f"That was the reconciliation: not just a sorry word, but both of them helping."
    )


def resolution(world: World) -> None:
    d = world.facts["detective"]
    s = world.facts["suspect"]
    item = world.facts["shared_item"]
    borrowed = world.facts["borrowed_item"]

    item.meters["muddy"] = 0.0
    item.meters["clean"] = 1.0
    borrowed.meters["muddy"] = 0.0
    borrowed.meters["clean"] = 1.0
    d.memes["joy"] += 0.5
    s.memes["joy"] += 0.5
    world.say(
        f"Soon the {item.label} sparkled again, and the muddy marks were gone."
    )
    world.say(
        f"{d.id} and {s.id} laughed at the silly trail, then shared the {item.label} "
        f"for one more round of play."
    )
    world.say(
        f"By the end, the detective's little clue had turned into a calm, happy afternoon."
    )


def tell(world: World) -> World:
    muddy_clue(world)
    world.say("")
    conflict(world)
    world.say("")
    investigate(world)
    world.say("")
    reconciliation(world)
    resolution(world)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES.values():
        if not place.affords_detective:
            continue
        for shared in SHARED_ITEMS:
            for borrowed in BORROWED_ITEMS:
                combos.append((place.id, shared, borrowed))
    return combos


def explain_rejection(_: str, __: str) -> str:
    return "(No story: that combination does not make a strong muddy detective mystery.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.muddy:
            lines.append(asp.fact("muddy_place", pid))
        if p.affords_sharing:
            lines.append(asp.fact("affords_sharing", pid))
        if p.affords_detective:
            lines.append(asp.fact("affords_detective", pid))
    for sid in SHARED_ITEMS:
        lines.append(asp.fact("shared", sid))
    for bid in BORROWED_ITEMS:
        lines.append(asp.fact("borrowed", bid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,S,B) :- place(P), shared(S), borrowed(B), muddy_place(P), affords_sharing(P), affords_detective(P).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a child that includes the word "muddy" and a gentle mystery.',
        f"Tell a story where {f['detective'].id} solves a muddy problem about a shared {f['shared_item'].label} and a borrowed item.",
        f"Write a child-friendly detective tale with conflict, sharing, and reconciliation at {world.place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.facts["detective"]
    s = world.facts["suspect"]
    item = world.facts["shared_item"]
    borrowed = world.facts["borrowed_item"]
    return [
        QAItem(
            question=f"Who noticed the muddy clue first?",
            answer=f"{d.id} noticed the muddy clue first and started the detective work.",
        ),
        QAItem(
            question=f"Why did the friends get into a conflict?",
            answer=f"They got into a conflict because the {item.label} was muddy and both friends felt upset about the shared game.",
        ),
        QAItem(
            question=f"How did {d.id} and {s.id} solve the problem?",
            answer=f"They looked at the muddy prints, understood what happened, and cleaned the {item.label} together until they reconciled.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The conflict turned into reconciliation, the muddy clue was cleaned up, and the friends shared the {item.label} again.",
        ),
        QAItem(
            question=f"What was the borrowed item in the mystery?",
            answer=f"The borrowed item was {borrowed.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to figure out what happened.",
        ),
        QAItem(
            question="What is mud?",
            answer="Mud is wet dirt that can stick to shoes, hands, and toys.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something too, so everyone can take turns.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop arguing and make peace again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world trace ---"]
    for e in world.entities.values():
        parts.append(
            f"{e.id}: meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(parts)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A muddy, amusing detective story world with sharing and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--detective")
    ap.add_argument("--suspect")
    ap.add_argument("--shared-item", choices=SHARED_ITEMS)
    ap.add_argument("--borrowed-item", choices=BORROWED_ITEMS)
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
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    place = args.place or rng.choice(list(PLACES))
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    suspect = args.suspect or rng.choice([n for n in OTHER_NAMES if n != detective])
    shared_item = args.shared_item or rng.choice(list(SHARED_ITEMS))
    borrowed_item = args.borrowed_item or rng.choice(list(BORROWED_ITEMS))
    if detective == suspect:
        raise StoryError("The detective and suspect must be different people.")
    return StoryParams(place=place, detective=detective, suspect=suspect, shared_item=shared_item, borrowed_item=borrowed_item)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_combos()
        print(f"{len(stories)} compatible stories:\n")
        for place, shared, borrowed in stories:
            print(f"  {place:14} {shared:10} {borrowed:12}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, shared, borrowed in [
            ("garden_gate", "magnifier", "cookie_jar"),
            ("backyard_path", "bucket", "chalk"),
            ("shed_steps", "lantern", "map"),
        ]:
            params = StoryParams(
                place=place,
                detective=DETECTIVE_NAMES[0],
                suspect=OTHER_NAMES[0],
                shared_item=shared,
                borrowed_item=borrowed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
