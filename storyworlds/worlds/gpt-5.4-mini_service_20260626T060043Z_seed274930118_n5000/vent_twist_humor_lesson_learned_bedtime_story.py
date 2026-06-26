#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/vent_twist_humor_lesson_learned_bedtime_story.py
============================================================================================================

A small bedtime-story world about a noisy vent, a funny misunderstanding,
and a gentle lesson learned.

Premise:
- A child is winding down for bed.
- A vent makes a silly whistling sound.
- The child imagines a twisty, spooky explanation.
- A grown-up investigates, finds the real cause, and fixes it.
- The room becomes calm again, and the child learns a small bedtime lesson.

The story is driven by a simple world model with physical meters and emotional
memes so the prose follows the simulated change rather than a frozen template.
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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def p(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    cozy: bool = True
    has_vent: bool = True
    sounds: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    sound: str
    twist: str
    mess: str
    can_fix: str


@dataclass
class Fix:
    id: str
    label: str
    action: str
    ending: str
    kind: str


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.story: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


@dataclass
class StoryParams:
    room: str
    cause: str
    fix: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


ROOMS = {
    "bedroom": Room(name="the bedroom", cozy=True, has_vent=True, sounds={"whistle"}),
    "hallway": Room(name="the hallway", cozy=False, has_vent=True, sounds={"whistle"}),
}

CAUSES = {
    "paper": Cause(
        id="paper",
        label="a scrap of paper",
        sound="a tiny whistle",
        twist="the vent was not a monster at all; it was singing through the paper",
        mess="wobbly and noisy",
        can_fix="paper",
    ),
    "sock": Cause(
        id="sock",
        label="a little sock",
        sound="a funny flutter",
        twist="the vent was only trying to breathe through the sock",
        mess="stuck and grumpy",
        can_fix="sock",
    ),
    "toy": Cause(
        id="toy",
        label="a soft toy feather",
        sound="a feathery squeak",
        twist="the vent sounded silly because the toy was tickling it",
        mess="tickled and squeaky",
        can_fix="toy",
    ),
}

FIXES = {
    "ask_parent": Fix(
        id="ask_parent",
        label="ask a grown-up to help",
        action="pulled the little troublemaker away",
        ending="The vent gave one last puff, then settled into a sleepy hum.",
        kind="gentle",
    ),
    "clear_grate": Fix(
        id="clear_grate",
        label="gently clear the vent grate",
        action="lifted the troublemaker out",
        ending="Soon the air moved softly again, like a quiet lullaby.",
        kind="careful",
    ),
}


GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Noah", "Eli"]
TRAITS = ["sleepy", "curious", "brave", "gentle", "bouncy", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for cause in CAUSES:
            for fix in FIXES:
                if cause == "paper" or fix == "ask_parent":
                    combos.append((room, cause, fix))
    return combos


def reason_reject(cause: Cause, fix: Fix) -> str:
    return (
        f"(No story: the fix '{fix.label}' does not fit the vent problem "
        f"for '{cause.label}'. This world only tells stories when the solution "
        f"is gentle and believable.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world about a noisy vent, a twist, humor, and a lesson learned."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.cause and args.fix:
        c, f = CAUSES[args.cause], FIXES[args.fix]
        if not ((c.id == "paper") or f.id == "ask_parent"):
            raise StoryError(reason_reject(c, f))

    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.cause is None or c[1] == args.cause)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid bedtime-vent story matches those options.)")

    room, cause, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(room=room, cause=cause, fix=fix, name=name, gender=gender, parent=parent)


def narrate_opening(world: World, child: Entity, parent: Entity, cause: Cause) -> None:
    world.say(
        f"{child.id} was a little {next(t for t in child.memes.get('traits', []) if t != 'little') if child.memes.get('traits') else 'sleepy'} {child.type} who was nearly ready for bed."
    )
    world.say(
        f"{child.p('subject').capitalize()} loved the soft blanket, the dim lamp, and the last quiet minutes before sleep."
    )
    world.say(
        f"That night, the vent in {world.room.name} made {cause.sound}, and {child.id} sat up with wide eyes."
    )


def narrate_twist(world: World, child: Entity, cause: Cause) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{child.id} whispered, 'Is the vent making a spooky face?'"
    )
    world.say(
        f"But the twist was funny: {cause.twist}."
    )


def narrate_humor(world: World, child: Entity) -> None:
    child.memes["humor"] = child.memes.get("humor", 0.0) + 1
    world.say(
        f"{child.id} giggled because the vent sounded less like a ghost and more like a flute that had forgotten its lesson."
    )


def narrate_fix(world: World, child: Entity, parent: Entity, cause: Cause, fix: Fix) -> None:
    world.say(
        f"{parent.id} leaned closer, listened, and smiled. '{child.id}, let's {fix.label}.'"
    )
    world.say(
        f"Together, they found {cause.label}; {fix.action}, and the room felt calmer at once."
    )
    child.memes["worry"] = 0.0
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    world.say(fix.ending)


def narrate_lesson(world: World, child: Entity, parent: Entity) -> None:
    child.memes["lesson"] = child.memes.get("lesson", 0.0) + 1
    world.say(
        f"{child.id} snuggled under the blanket and learned a bedtime lesson: when something seems strange, it helps to ask for help instead of guessing the scariest thing."
    )
    world.say(
        f"Then {child.id} yawned, {child.p('possessive')} eyes grew heavy, and the quiet room kept watch while {child} drifted off to sleep."
    )


def tell_story(params: StoryParams) -> World:
    world = World(ROOMS[params.room])
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        memes={"traits": ["little", TRAITS[0]]},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    cause = CAUSES[params.cause]
    fix = FIXES[params.fix]

    child.memes["sleepy"] = 1.0
    narrate_opening(world, child, parent, cause)
    world.para()
    narrate_twist(world, child, cause)
    narrate_humor(world, child)
    world.para()
    narrate_fix(world, child, parent, cause, fix)
    narrate_lesson(world, child, parent)

    world.facts.update(child=child, parent=parent, cause=cause, fix=fix)
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    cause = f["cause"]
    fix = f["fix"]
    return [
        f"Write a bedtime story about {child.id}, a vent, and a silly misunderstanding.",
        f"Tell a gentle story where a noisy vent turns out to be caused by {cause.label} and a grown-up helps.",
        f"Write a child-friendly bedtime story with a twist, a little humor, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    cause = f["cause"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"What made {child.id} sit up in bed?",
            answer=f"{cause.sound.capitalize()} made {child.id} sit up in bed because the vent in the bedroom sounded strange.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the vent was not a monster at all; it was only acting strange because of {cause.label}.",
        ),
        QAItem(
            question=f"How did the grown-up help?",
            answer=f"{parent.type.capitalize()} {fix.label}, which helped calm the room and make the vent quiet again.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer=f"{child.id} learned that when something seems scary or odd, it is wise to ask a grown-up for help instead of guessing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vent?",
            answer="A vent is an opening that lets air move into or out of a room.",
        ),
        QAItem(
            question="Why can a vent make a whistling sound?",
            answer="A vent can whistle when air squeezes through a small opening or when something blocks part of the airflow.",
        ),
        QAItem(
            question="Why is bedtime a good time to notice small sounds?",
            answer="At bedtime, the house is usually quiet, so little sounds can seem bigger and easier to hear.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Room,Cause,Fix) :- room(Room), cause(Cause), fix(Fix), good_pair(Cause,Fix).
good_pair(paper,ask_parent).
good_pair(paper,clear_grate).
good_pair(sock,ask_parent).
good_pair(toy,ask_parent).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for r in ROOMS:
        lines.append(asp.fact("room", r))
    for c in CAUSES:
        lines.append(asp.fact("cause", c))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    for c in CAUSES:
        if c == "paper":
            for f in FIXES:
                lines.append(asp.fact("good_pair", c, f))
        else:
            lines.append(asp.fact("good_pair", c, "ask_parent"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


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
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(room="bedroom", cause="paper", fix="clear_grate", name="Mia", gender="girl", parent="mother"),
    StoryParams(room="bedroom", cause="sock", fix="ask_parent", name="Leo", gender="boy", parent="father"),
    StoryParams(room="hallway", cause="toy", fix="ask_parent", name="Nora", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: vent bedtime story ({p.cause} / {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
