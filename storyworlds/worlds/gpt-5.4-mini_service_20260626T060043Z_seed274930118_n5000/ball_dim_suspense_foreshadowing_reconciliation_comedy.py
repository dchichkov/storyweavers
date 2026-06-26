#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ball_dim_suspense_foreshadowing_reconciliation_comedy.py
=================================================================================================

A small storyworld about a dim room, a rolling ball, a bit of suspense,
some foreshadowing, and a comic reconciliation.

Premise:
- A child loves a ball.
- The room is dim, so it is hard to see where the ball goes.

Tension:
- The ball rolls away and seems lost.
- The child and caregiver worry it may have vanished somewhere silly.

Turn:
- Earlier clues in the room hint where the ball went.
- A lamp, a rug bump, or a basket shadow points toward the answer.

Resolution:
- The child and caregiver find the ball.
- They reconcile, laugh, and continue playing together.

The domain is intentionally small and state-driven: physical meters track
light, distance, hiding, and found-ness; emotional memes track worry, surprise,
relief, and laughter.
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
# Registries
# ---------------------------------------------------------------------------

ROOMS = {
    "hall": {
        "name": "the hall",
        "dim": True,
        "places": ["rug", "bench", "umbrella stand"],
    },
    "playroom": {
        "name": "the playroom",
        "dim": True,
        "places": ["toy chest", "beanbag", "window curtain"],
    },
    "basement": {
        "name": "the basement room",
        "dim": True,
        "places": ["laundry basket", "shelf", "cardboard box"],
    },
}

BALLS = {
    "red": {
        "label": "red ball",
        "phrase": "a bright red ball",
        "bounce": "bounced",
    },
    "blue": {
        "label": "blue ball",
        "phrase": "a shiny blue ball",
        "bounce": "wobbled",
    },
    "yellow": {
        "label": "yellow ball",
        "phrase": "a cheerful yellow ball",
        "bounce": "rolled",
    },
}

HELPERS = {
    "mom": "mom",
    "dad": "dad",
    "aunt": "aunt",
    "grandpa": "grandpa",
}

NAMES = ["Mia", "Leo", "Nina", "Owen", "Ivy", "Noah", "Ava", "Finn"]
BALL_NAMES = list(BALLS)
ROOM_NAMES = list(ROOMS)
HELPER_NAMES = list(HELPERS)

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(Place,Ball,Helper) :- room(Place), ball(Ball), helper(Helper).
valid_story(Place,Ball,Helper,Child) :- valid(Place,Ball,Helper), child(Child).
"""


@dataclass
class StoryParams:
    room: str
    ball: str
    child: str
    helper: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["distance", "hidden", "found", "brightness", "toy_lost"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "surprise", "relief", "laughter", "curiosity", "affection"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self) -> str:
        return "they" if self.kind == "character" else "it"

    def poss(self) -> str:
        return "their" if self.kind == "character" else "its"


@dataclass
class World:
    room: dict
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def is_dim_room(room_key: str) -> bool:
    return bool(ROOMS[room_key]["dim"])


def ball_at_risk(room_key: str) -> bool:
    return is_dim_room(room_key)


def choose_reasonable_combo(rng: random.Random, args: argparse.Namespace) -> tuple[str, str, str]:
    combos = []
    for room in ROOM_NAMES:
        for ball in BALL_NAMES:
            for helper in HELPER_NAMES:
                combos.append((room, ball, helper))
    if args.room:
        combos = [c for c in combos if c[0] == args.room]
    if args.ball:
        combos = [c for c in combos if c[1] == args.ball]
    if args.helper:
        combos = [c for c in combos if c[2] == args.helper]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    return rng.choice(sorted(combos))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room, ball, helper = choose_reasonable_combo(rng, args)
    child = args.child or rng.choice(NAMES)
    return StoryParams(room=room, ball=ball, child=child, helper=helper)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small comedic suspense storyworld with a dim ball.")
    ap.add_argument("--room", choices=ROOM_NAMES)
    ap.add_argument("--ball", choices=BALL_NAMES)
    ap.add_argument("--child")
    ap.add_argument("--helper", choices=HELPER_NAMES)
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


def asp_facts() -> str:
    import asp
    lines = []
    for room in ROOM_NAMES:
        lines.append(asp.fact("room", room))
    for ball in BALL_NAMES:
        lines.append(asp.fact("ball", ball))
    for helper in HELPER_NAMES:
        lines.append(asp.fact("helper", helper))
    for child in NAMES:
        lines.append(asp.fact("child", child))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((r, b, h) for r in ROOM_NAMES for b in BALL_NAMES for h in HELPER_NAMES)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python registry ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def play(world: World, child: Entity, ball: Entity) -> None:
    child.memes["curiosity"] += 1
    ball.meters["distance"] += 1
    world.say(f"{child.id} loved playing with the {ball.label}, even when the room felt dim and sleepy.")


def foreshadow(world: World, child: Entity, ball: Entity) -> None:
    place = world.room["places"][0]
    child.meters["distance"] += 1
    world.say(
        f"At the edge of the {world.room['name']}, {place} made a strange little bump in the shadows."
    )
    world.say(
        f"{child.id} noticed it, but just laughed and kept bouncing the {ball.label}."
    )


def lose_ball(world: World, child: Entity, ball: Entity) -> None:
    ball.meters["hidden"] = 1.0
    ball.meters["found"] = 0.0
    child.memes["worry"] += 1
    world.say(
        f"Then the {ball.label} rolled away with a tiny boing and disappeared into the dimness."
    )
    world.say(f"{child.id} blinked hard. \"Uh-oh,\" {child.pronoun()} said. \"It was here a second ago!\"")


def suspense(world: World, child: Entity, helper: Entity, ball: Entity) -> None:
    helper.memes["surprise"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"{helper.id} leaned down with a careful smile. \"Let's not panic,\" {helper.pronoun()} said."
    )
    world.say(
        f"They looked under the {world.room['places'][0]}, then at the dark corner by the wall."
    )


def clue(world: World, child: Entity, ball: Entity) -> None:
    hint = world.room["places"][0]
    world.say(
        f"That little bump in the shadows turned out to be a clue: the {ball.label} had rolled behind the {hint}."
    )
    ball.meters["distance"] = 0.0
    ball.meters["hidden"] = 0.0
    ball.meters["found"] = 1.0
    child.memes["surprise"] += 1


def reconcile(world: World, child: Entity, helper: Entity, ball: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["laughter"] += 1
    helper.memes["relief"] += 1
    helper.memes["laughter"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f"{child.id} and {helper.id} found the {ball.label} at last, and both of them laughed at how it had hidden in such an obvious place."
    )
    world.say(
        f"{child.id} hugged {helper.id}. \"You were right to look carefully,\" {child.pronoun()} said."
    )
    world.say(
        f"{helper.id} grinned back. \"Next time, the ball can try to hide, but we will be quicker.\""
    )


def build_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room=room)
    child = world.add(Entity(id=params.child, kind="character", type="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type="helper"))
    ball = world.add(Entity(
        id=params.ball,
        kind="thing",
        type="ball",
        label=f"{params.ball} ball",
        phrase=BALLS[params.ball]["phrase"],
        owner=child.id,
    ))
    world.facts.update(child=child, helper=helper, ball=ball, room=params.room)
    world.say(f"{child.id} was playing in {room['name']} with {ball.phrase}.")
    world.say(f"The room was dim, so the ball seemed extra quick and a little mysterious.")
    world.para()
    play(world, child, ball)
    foreshadow(world, child, ball)
    world.para()
    if ball_at_risk(params.room):
        lose_ball(world, child, ball)
        suspense(world, child, helper, ball)
        clue(world, child, ball)
        reconcile(world, child, helper, ball)
    else:
        world.say(f"Nothing mysterious happened, which was almost suspicious in its own way.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    ball = f["ball"]
    room = f["room"]
    return [
        f'Write a short, funny story for a young child about {child.id}, a {ball.label}, and a dim room.',
        f"Tell a suspenseful but gentle story where {child.id} and {helper.id} search for a lost ball in {ROOMS[room]['name']}.",
        f'Write a comedic story with foreshadowing: a child notices a clue, loses a ball, and then finds it with a helper.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    ball = f["ball"]
    room = f["room"]
    return [
        QAItem(
            question=f"Where was {child.id} playing at the start of the story?",
            answer=f"{child.id} was playing in {ROOMS[room]['name']} with the {ball.label}.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful when the {ball.label} rolled away?",
            answer=f"The room was dim, so it was hard to see where the {ball.label} went, and that made both {child.id} and {helper.id} worry for a moment.",
        ),
        QAItem(
            question=f"What was the clue that foreshadowed where the {ball.label} went?",
            answer=f"The little bump near the {ROOMS[room]['places'][0]} was a clue. It hinted that the {ball.label} had not vanished at all.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and {helper.id}?",
            answer=f"They found the {ball.label}, laughed together, and hugged after the scare was over.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    room = world.facts["room"]
    return [
        QAItem(
            question="What does dim mean?",
            answer="Dim means there is only a little light, so things are harder to see.",
        ),
        QAItem(
            question="Why can a ball be hard to find in a dim room?",
            answer="A ball can be hard to find because shadows hide it and the low light makes small things blend in.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a clue early that hints at something that will matter later.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were worried or upset make up, feel better, and get along again.",
        ),
        QAItem(
            question=f"What kind of room was {ROOMS[room]['name']} in this story?",
            answer=f"{ROOMS[room]['name']} was a dim room with places like the {ROOMS[room]['places'][0]} and the {ROOMS[room]['places'][1]}.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
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
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(r, b, h) for r in ROOM_NAMES for b in BALL_NAMES for h in HELPER_NAMES]


def explain_rejection() -> str:
    return "No valid combination matches the given options."


CURATED = [
    StoryParams(room="hall", ball="red", child="Mia", helper="mom"),
    StoryParams(room="playroom", ball="blue", child="Leo", helper="dad"),
    StoryParams(room="basement", ball="yellow", child="Nina", helper="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with child):")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
