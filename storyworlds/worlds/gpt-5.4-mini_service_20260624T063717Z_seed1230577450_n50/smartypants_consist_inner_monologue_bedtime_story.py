#!/usr/bin/env python3
"""
storyworlds/worlds/smartypants_consist_inner_monologue_bedtime_story.py
=======================================================================

A tiny bedtime-story world about a child who thinks too hard, gets called a
smartypants, and learns that consistency can be gentler than cleverness.

Premise:
- A child wants to solve a small nighttime problem in a clever way.
- The parent asks them to keep a steady routine instead of changing plans.

Tension:
- The child keeps making fast, smart little plans in their head.
- Their inner monologue runs ahead of the actual bedtime routine.

Turn:
- The child notices that sticking with one calming plan works better.

Resolution:
- The child settles, the room grows quiet, and the bedtime feeling becomes
  warm and steady.

This script follows the Storyweavers contract:
- standalone stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
- includes a Python reasonableness gate plus an inline ASP twin
- emits registry facts through asp_facts()
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
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    room: str
    object: str
    soothing: str
    child_name: str
    parent_name: str
    seed: Optional[int] = None


@dataclass
class Room:
    id: str
    label: str
    dim: str
    cozy: str
    sounds: list[str] = field(default_factory=list)


@dataclass
class ObjectItem:
    id: str
    label: str
    phrase: str
    kind: str
    place: str
    helps: str
    can_stack: bool = False


@dataclass
class SoothingPlan:
    id: str
    label: str
    verb: str
    inner_monologue: str
    steady: bool
    quiet: bool


ROOMS = {
    "bedroom": Room(
        id="bedroom",
        label="the bedroom",
        dim="soft",
        cozy="warm",
        sounds=["the clock ticked gently", "the blanket whispered softly"],
    ),
    "nursery": Room(
        id="nursery",
        label="the nursery",
        dim="golden",
        cozy="snug",
        sounds=["the mobile turned in a slow circle", "the lamp made a sleepy glow"],
    ),
    "loft": Room(
        id="loft",
        label="the loft room",
        dim="moonlit",
        cozy="quiet",
        sounds=["the floor creaked once", "the window breathed with night air"],
    ),
}

OBJECTS = {
    "lamp": ObjectItem(
        id="lamp",
        label="lamp",
        phrase="a little lamp with a round shade",
        kind="light",
        place="bedside table",
        helps="makes the room feel safe",
    ),
    "blanket": ObjectItem(
        id="blanket",
        label="blanket",
        phrase="a striped blanket",
        kind="cover",
        place="bed",
        helps="keeps the child warm",
        can_stack=True,
    ),
    "book": ObjectItem(
        id="book",
        label="book",
        phrase="a picture book with soft pages",
        kind="story",
        place="pillow",
        helps="slows the child down",
    ),
    "pillow": ObjectItem(
        id="pillow",
        label="pillow",
        phrase="a cloud-puffy pillow",
        kind="rest",
        place="bed",
        helps="gives the head a place to settle",
    ),
}

SOOTHING = {
    "breathing": SoothingPlan(
        id="breathing",
        label="slow breathing",
        verb="breathe in and out slowly",
        inner_monologue="One breath, then another, and the room will stay still.",
        steady=True,
        quiet=True,
    ),
    "counting": SoothingPlan(
        id="counting",
        label="counting stars",
        verb="count ten tiny stars",
        inner_monologue="If I count the same way each time, my thoughts will line up.",
        steady=True,
        quiet=True,
    ),
    "story": SoothingPlan(
        id="story",
        label="one bedtime story",
        verb="listen to one story without switching",
        inner_monologue="A whole story at once feels easier than jumping around.",
        steady=True,
        quiet=True,
    ),
    "tidy_plan": SoothingPlan(
        id="tidy_plan",
        label="the tidy plan",
        verb="put each thing back in the same place",
        inner_monologue="If everything stays where it belongs, bedtime can keep its shape.",
        steady=True,
        quiet=True,
    ),
}

CHILD_NAMES = ["Mia", "Noah", "Luna", "Eli", "Nora", "Ava", "Theo", "Zoe"]
PARENT_NAMES = ["Mom", "Dad", "Mama", "Papa"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

    def trace(self) -> str:
        out = ["--- world trace ---"]
        out.append(f"room={self.room.id}")
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            if e.props:
                bits.append(f"props={e.props}")
            out.append(f"{e.id}: {e.kind} {e.label} {' '.join(bits)}")
        out.append(f"fired={sorted(self.fired)}")
        return "\n".join(out)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def story_reasonable(room: Room, obj: ObjectItem, plan: SoothingPlan) -> bool:
    if room.id == "loft" and obj.id == "book" and plan.id == "tidy_plan":
        return True
    if room.id == "bedroom" and obj.id in {"blanket", "pillow"} and plan.id in {"breathing", "story"}:
        return True
    if room.id == "nursery" and obj.id in {"lamp", "book"} and plan.id in {"breathing", "counting", "story"}:
        return True
    return False


def explain_rejection(room: Room, obj: ObjectItem, plan: SoothingPlan) -> str:
    return (
        f"(No story: in {room.label}, {plan.label} does not fit well with {obj.label}. "
        f"The bedtime routine needs one gentle, steady plan that matches the room and object.)"
    )


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def introduce(world: World, child: Entity, parent: Entity, obj: ObjectItem, plan: SoothingPlan) -> None:
    world.say(
        f"{child.label} was a little smartypants who liked to solve bedtime puzzles with a busy mind."
    )
    world.say(
        f"In {world.room.label}, {world.room.cozy} air and soft shadows waited while {parent.label} got {obj.phrase} ready."
    )


def inner_monologue(world: World, child: Entity, plan: SoothingPlan, obj: ObjectItem) -> None:
    child.memes["thinking"] = child.memes.get("thinking", 0.0) + 1.0
    child.memes["restless"] = child.memes.get("restless", 0.0) + 1.0
    world.say(
        f"Inside {child.label}'s head, a tiny voice raced ahead: '{plan.inner_monologue}'"
    )
    world.say(
        f"{child.label} thought maybe a clever trick would be faster than bedtime itself."
    )
    world.say(
        f"But the {obj.label} stayed on the bed, quiet and waiting, like it had all the time in the world."
    )


def parent_speaks(world: World, parent: Entity, child: Entity, plan: SoothingPlan) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{parent.label} smiled and said, 'You do not need a new plan every minute. Try to consist with one calm step.'"
    )
    world.say(
        f"{child.label} wrinkled {child.label.lower() if False else 'the'} nose for a moment, because the word felt big and serious."
    )


def steady_turn(world: World, child: Entity, parent: Entity, plan: SoothingPlan, obj: ObjectItem) -> None:
    child.memes["stability"] = child.memes.get("stability", 0.0) + 1.0
    child.memes["restless"] = max(0.0, child.memes.get("restless", 0.0) - 1.0)
    child.meters["sleepiness"] = child.meters.get("sleepiness", 0.0) + 1.0
    world.say(
        f"Then {child.label} tried it the same way twice: {plan.verb}, and then {plan.verb} again."
    )
    world.say(
        f"That steady rhythm felt kinder than all the smart new ideas tumbling through {child.label}'s head."
    )
    world.say(
        f"The {obj.label} helped too, because it made the bed feel ready and complete."
    )


def ending(world: World, child: Entity, parent: Entity, plan: SoothingPlan, obj: ObjectItem) -> None:
    child.memes["peace"] = child.memes.get("peace", 0.0) + 1.0
    world.say(
        f"At last, {child.label} lay still under the blanket, with {parent.label} nearby and the room hushed."
    )
    world.say(
        f"The {obj.label} stayed in its place, {plan.label} stayed the same, and {child.label} drifted toward sleep with a small, happy sigh."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def tell(room: Room, obj: ObjectItem, plan: SoothingPlan, child_name: str, parent_name: str) -> World:
    world = World(room)
    child = world.add(Entity(id="child", kind="character", label=child_name))
    parent = world.add(Entity(id="parent", kind="character", label=parent_name))
    item = world.add(Entity(id=obj.id, kind="thing", label=obj.label, props={"phrase": obj.phrase, "place": obj.place}))
    world.facts.update(child=child, parent=parent, object=obj, plan=plan, room=room)

    introduce(world, child, parent, obj, plan)
    world.para()
    inner_monologue(world, child, plan, obj)
    parent_speaks(world, parent, child, plan)
    world.para()
    steady_turn(world, child, parent, plan, obj)
    ending(world, child, parent, plan, obj)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    obj = f["object"]
    plan = f["plan"]
    room = f["room"]
    return [
        f"Write a bedtime story about a smartypants child in {room.label} who must consist with one calming plan.",
        f"Tell a gentle story where {child.label} keeps thinking up clever ideas, but {plan.label} helps {obj.label} feel part of bedtime.",
        f"Write a child-friendly inner-monologue story that ends when the same quiet routine works twice in a row.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    obj = f["object"]
    plan = f["plan"]
    room = f["room"]
    return [
        QAItem(
            question=f"Who is the story about in {room.label}?",
            answer=f"It is about {child.label}, a little smartypants child who is trying to settle for bedtime.",
        ),
        QAItem(
            question=f"What did {parent.label} ask {child.label} to do?",
            answer=f"{parent.label} asked {child.label} to consist with one calm step instead of changing the plan again and again.",
        ),
        QAItem(
            question=f"What helped {child.label} calm down in the end?",
            answer=f"{plan.label} helped, along with {obj.label} sitting ready and the room staying soft and quiet.",
        ),
        QAItem(
            question=f"Why did {child.label} stop making so many new ideas?",
            answer=f"{child.label} noticed that the same calm routine worked better than a rushed clever trick, so the busy thoughts could slow down.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be consistent?",
            answer="To be consistent means to keep doing something the same calm way instead of switching back and forth.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the little voice in your head that thinks and talks to itself without saying the words out loud.",
        ),
        QAItem(
            question="Why are bedtime routines helpful?",
            answer="Bedtime routines are helpful because the same gentle steps tell the body it is time to rest.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
room_ok(R, O, P) :- room(R), object(O), plan(P), consistent(R, O, P).
consistent(R, O, P) :- good_pair(R, O), quiet_plan(P).
consistent(R, O, P) :- good_pair2(R, O), quiet_plan(P).
good_pair(bedroom, blanket).
good_pair(bedroom, pillow).
good_pair2(nursery, lamp).
good_pair2(nursery, book).
quiet_plan(breathing).
quiet_plan(counting).
quiet_plan(story).
quiet_plan(tidy_plan).
#show room_ok/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for r in ROOMS.values():
        lines.append(asp.fact("room", r.id))
    for o in OBJECTS.values():
        lines.append(asp.fact("object", o.id))
    for p in SOOTHING.values():
        lines.append(asp.fact("plan", p.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_triples() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show room_ok/3."))
    return sorted(set(asp.atoms(model, "room_ok")))


def python_valid_triples() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for r in ROOMS.values():
        for o in OBJECTS.values():
            for p in SOOTHING.values():
                if story_reasonable(r, o, p):
                    out.append((r.id, o.id, p.id))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid_triples())
    b = set(python_valid_triples())
    if a == b:
        print(f"OK: ASP matches Python gate ({len(a)} valid triples).")
        return 0
    print("Mismatch between ASP and Python gates.")
    print("only in ASP:", sorted(a - b))
    print("only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime story world with inner monologue, smartypants, and consistency."
    )
    ap.add_argument("--room", choices=sorted(ROOMS))
    ap.add_argument("--object", dest="object_", choices=sorted(OBJECTS))
    ap.add_argument("--soothing", choices=sorted(SOOTHING))
    ap.add_argument("--name")
    ap.add_argument("--parent")
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
    room = ROOMS[args.room] if args.room else rng.choice(list(ROOMS.values()))
    obj = OBJECTS[args.object_] if args.object_ else rng.choice(list(OBJECTS.values()))
    plan = SOOTHING[args.soothing] if args.soothing else rng.choice(list(SOOTHING.values()))
    if not story_reasonable(room, obj, plan):
        raise StoryError(
            f"(No story: {plan.label} does not make sense with {obj.label} in {room.label}; "
            f"the bedtime routine needs a steadier pairing.)"
        )
    child_name = args.name or rng.choice(CHILD_NAMES)
    parent_name = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(room=room.id, object=obj.id, soothing=plan.id, child_name=child_name, parent_name=parent_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(ROOMS[params.room], OBJECTS[params.object], SOOTHING[params.soothing], params.child_name, params.parent_name)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show room_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_triples()
        print(f"{len(triples)} valid triples:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("bedroom", "blanket", "breathing", "Mia", "Mom"),
            StoryParams("bedroom", "pillow", "story", "Noah", "Dad"),
            StoryParams("nursery", "lamp", "counting", "Luna", "Mama"),
            StoryParams("nursery", "book", "story", "Eli", "Papa"),
            StoryParams("loft", "book", "tidy_plan", "Nora", "Mom"),
        ]
        samples = [generate(p) for p in curated]
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
