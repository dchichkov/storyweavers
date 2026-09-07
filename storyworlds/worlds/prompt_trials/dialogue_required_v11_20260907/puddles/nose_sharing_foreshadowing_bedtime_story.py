#!/usr/bin/env python3
"""A gentle bedtime story about sharing a nose-shaped night-light.

Nora wants the little moon lamp beside her bed all to herself. Her brother needs
its soft glow to find his lost blanket, and a tiny clue planted earlier helps
the children solve the problem kindly. The simulated state tracks ownership,
comfort, searching, sharing, and the bedtime resolution.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass(frozen=True)
class Room:
    id: str
    label: str
    quiet: bool = True


@dataclass(frozen=True)
class Lamp:
    id: str
    label: str
    shape: str
    brightness: str


@dataclass(frozen=True)
class Plan:
    id: str
    label: str
    sharing: str


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str = ""
    result: str = ""


@dataclass
class StoryParams:
    room: str
    lamp: str
    helper: str
    plan: str
    name: str = "Nora"
    sibling: str = "Sam"
    parent: str = "Mom"
    seed: Optional[int] = None


ROOMS = {
    "bedroom": Room("bedroom", "the cozy bedroom"),
    "attic": Room("attic", "the little attic room"),
    "guestroom": Room("guestroom", "the quiet guest room"),
}

LAMPS = {
    "nose_moon": Lamp("nose_moon", "a small moon lamp with a round nose", "nose", "soft"),
    "nose_star": Lamp("nose_star", "a star lamp with a tiny nose", "nose", "warm"),
    "nose_cloud": Lamp("nose_cloud", "a cloud lamp with a button nose", "nose", "gentle"),
}

PLANS = {
    "share_lamp": Plan("share_lamp", "share the lamp", "take turns"),
    "follow_glow": Plan("follow_glow", "carry the lamp together", "hold together"),
    "use_nightlight": Plan("use_nightlight", "leave the lamp by the doorway", "leave nearby"),
}

HELPERS = {
    "blanket": "Sam's blue blanket",
    "button": "the small brass button",
    "slipper": "Sam's red slipper",
}

NAMES = ["Nora", "Mina", "Lila", "Pia", "June"]
SIBLINGS = ["Sam", "Owen", "Theo", "Milo", "Ben"]
PARENTS = ["Mom", "Dad", "Auntie"]

ASP_RULES = r"""
needs_light(C) :- lost(C), afraid(C).
can_share(L, C) :- lamp(L), needs_light(C), soft(L).
can_solve(Plan, L, C) :- plan(Plan), can_share(L, C).
valid(Room, Lamp, Helper, Plan) :-
    room(Room), lamp(Lamp), helper(Helper), plan(Plan),
    can_solve(Plan, Lamp, Helper).
foreshadowed(Helper) :- clue(Helper).
resolved(Room, Lamp, Helper, Plan) :-
    valid(Room, Lamp, Helper, Plan),
    can_solve(Plan, Lamp, Helper).
#show valid/4.
#show resolved/4.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.room = ROOMS[params.room]
        self.lamp = LAMPS[params.lamp]
        self.helper = params.helper
        self.plan = PLANS[params.plan]
        self.entities: dict[str, Entity] = {}
        self.events: list[Event] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.turn = 0

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, kind: str, actor: str, target: str, text: str,
               cause: str = "", result: str = "") -> None:
        self.events.append(Event(kind, actor, target, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def add_fact_entity(world: World) -> None:
    p = world.params
    child = world.add(Entity(p.name, "child", p.name, location=p.room))
    sibling = world.add(Entity(p.sibling, "child", p.sibling, location=p.room))
    parent = world.add(Entity(p.parent, "adult", p.parent, location=p.room))
    lamp = world.add(Entity("lamp", "lamp", world.lamp.label, owner=p.name, location=p.room))
    lost = world.add(Entity("lost_item", "object", HELPERS[p.helper], owner=p.sibling, location="unknown"))
    child.memes.update({"coziness": 1, "possessiveness": 1})
    sibling.memes.update({"worry": 1, "trust": 0})
    lamp.meters.update({"glow": 1, "shared": 0})
    lost.meters.update({"lost": 1, "found": 0})
    world.facts.update(child=child, sibling=sibling, parent=parent, lamp=lamp, lost=lost)


def tell(params: StoryParams) -> World:
    if params.room not in ROOMS:
        raise StoryError("That room is not in the bedtime house.")
    if params.lamp not in LAMPS:
        raise StoryError("That lamp is not in the bedtime collection.")
    if params.helper not in HELPERS:
        raise StoryError("That lost bedtime object is not known.")
    if params.plan not in PLANS:
        raise StoryError("That sharing plan is not available.")

    world = World(params)
    add_fact_entity(world)
    child = world.facts["child"]
    sibling = world.facts["sibling"]
    parent = world.facts["parent"]
    lamp = world.facts["lamp"]
    lost = world.facts["lost"]

    world.record(
        "bedtime",
        child.id,
        lamp.id,
        f"In {world.room.label}, {child.label} tucked the little moon lamp with its round nose close to the pillow. "
        f"{parent.label} kissed both children good night, and the lamp made a soft pool of light.",
        cause="The children were getting ready for sleep.",
        result="The room became calm and warm.",
    )

    world.para()
    world.record(
        "foreshadow",
        parent.id,
        lost.id,
        f"Before closing the door, {parent.label} noticed {lost.label} near the foot of the bed. "
        f'"We should remember that little thing," {parent.label} said softly. '
        f'Then the blanket slipped, and nobody saw where it went.',
        cause=f"{lost.label} was left near the bed before the room grew dark.",
        result="A small clue waited near the bed.",
    )

    world.para()
    child.memes["possessiveness"] += 1
    sibling.memes["worry"] += 1
    world.record(
        "problem",
        sibling.id,
        lamp.id,
        f'When {sibling.label} reached for the covers, {sibling.pronoun if hasattr(sibling, "pronoun") else "they"} could not find {lost.label}. '
        f'"I need a little light," {sibling.label} whispered. '
        f'{child.label} hugged the lamp. "But it is my nose lamp. I want it beside me."',
        cause=f"{sibling.label} needed the soft lamp to search for {lost.label}.",
        result=f"{child.label} wanted the lamp to stay all alone by the pillow.",
    )

    world.para()
    child.memes["sharing"] = 1
    world.record(
        "turn",
        child.id,
        sibling.id,
        f'"You may hold one side," {child.label} said after a quiet moment. '
        f'"And you may hold the other," {sibling.label} replied. '
        f'Together they carried the lamp slowly, its funny nose pointing toward the floor.',
        cause="The children listened to each other's needs.",
        result="They chose to share the lamp and search together.",
    )

    world.para()
    lamp.meters["shared"] = 1
    lamp.location = params.room
    lost.location = params.room
    lost.meters["lost"] = 0
    lost.meters["found"] = 1
    sibling.memes["worry"] = 0
    sibling.memes["trust"] = 1
    world.record(
        "discovery",
        child.id,
        lost.id,
        f'The nose-shaped glow slid over the rug and touched a blue corner. '
        f'"There!" cried {sibling.label}. The children found {lost.label} tucked beneath the bed, '
        f'right beside the place where {parent.label} had seen it earlier.',
        cause=f"The earlier clue showed that {lost.label} had been near the bed.",
        result=f"{sibling.label} found {lost.label} with help from the shared lamp.",
    )

    world.para()
    child.memes["possessiveness"] = 0
    child.memes["coziness"] += 1
    world.record(
        "resolution",
        child.id,
        lamp.id,
        f'{child.label} smiled and carried the lamp back with {sibling.label}. '
        f'"It is nicer when its nose shines for both of us," {child.label} said. '
        f'{sibling.label} placed {lost.label} beside the pillow, and the lamp rested between them.',
        cause="Sharing helped both children feel safe and solved the search.",
        result="The lamp became a shared bedtime light.",
    )

    world.para()
    world.record(
        "ending",
        parent.id,
        lamp.id,
        f'{parent.label} peeked in and saw two sleepy heads beneath the covers. '
        f'The tiny nose on the lamp glowed between them like a friendly moon. '
        f'"Good night, little sharers," {parent.label} whispered, and the room dreamed quietly.',
        cause="The children had found the missing object and made room for one another.",
        result="Both children settled peacefully to sleep.",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a gentle bedtime story about {p.name} sharing a nose-shaped lamp with {p.sibling}.",
        f"Tell a story in {world.room.label} where a small clue foreshadows finding {HELPERS[p.helper]} and sharing solves the bedtime worry.",
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "bedtime": "Why was the little lamp beside the pillow?",
        "foreshadow": "What clue appeared before the search?",
        "problem": "Why did the children need the lamp?",
        "turn": "How did the children decide to share?",
        "discovery": "Where did they find the missing object?",
        "resolution": "What changed after the children shared?",
        "ending": "How did the bedtime story end?",
    }
    return [
        QAItem(question=questions[e.kind], answer=f"{e.cause} {e.result}")
        for e in world.events
        if e.kind in questions
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why is sharing helpful?",
            "Sharing lets people use something together and helps everyone feel included.",
        ),
        QAItem(
            "What is foreshadowing?",
            "Foreshadowing is a small clue early in a story that hints at something that happens later.",
        ),
        QAItem(
            "Why are night-lights useful?",
            "A night-light gives a gentle glow that can help children feel safe without making the room too bright.",
        ),
        QAItem(
            "What is a nose?",
            "A nose is the part of a face used for smelling and helping air move in and out.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: kind={e.kind}, location={e.location}, meters={meters}, memes={memes}")
    lines.append("--- events ---")
    for e in world.events:
        lines.append(f"  {e.kind}: {e.text}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.extend([f"Q: {q.question}", f"A: {q.answer}"])
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.extend([f"Q: {q.question}", f"A: {q.answer}"])
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        (room, lamp, helper, plan)
        for room in ROOMS
        for lamp in LAMPS
        for helper in HELPERS
        for plan in PLANS
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for room in ROOMS:
        lines.append(asp.fact("room", room))
    for lamp, cfg in LAMPS.items():
        lines.append(asp.fact("lamp", lamp))
        lines.append(asp.fact("soft", lamp))
    for helper in HELPERS:
        lines.append(asp.fact("helper", helper))
        lines.append(asp.fact("lost", helper))
        lines.append(asp.fact("clue", helper))
        lines.append(asp.fact("afraid", helper))
    for plan in PLANS:
        lines.append(asp.fact("plan", plan))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def generate(params: StoryParams) -> StorySample:
    if (params.room, params.lamp, params.helper, params.plan) not in valid_combos():
        raise StoryError("Those bedtime choices do not form a valid story.")
    if params.name in {params.sibling, params.parent, "lamp", "lost_item"}:
        raise StoryError("The child name must be different from the other story characters and objects.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def check_sample(sample: StorySample) -> None:
    world = sample.world
    assert world is not None
    assert world.facts["lamp"].meter("shared") == 1
    assert world.facts["lost"].meter("found") == 1
    assert "nose" in sample.story.lower()
    assert len(sample.story_qa) == 7
    assert all(q.answer.endswith(".") for q in sample.story_qa)
    assert not any(x in sample.story for x in ("{", "}", "__", "meters=", "memes="))
    for event in world.events:
        assert event.text in sample.story
        assert event.actor in world.entities
        assert event.target in world.entities


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py != asp_set:
        print("MISMATCH: ASP and Python choices differ.")
        return 1
    for combo in sorted(py)[:12]:
        sample = generate(StoryParams(*combo))
        check_sample(sample)
    print(f"OK: {len(py)} ASP/Python combinations and generated story checks.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A bedtime story about a nose-shaped lamp and sharing.")
    parser.add_argument("--room", choices=ROOMS)
    parser.add_argument("--lamp", choices=LAMPS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--plan", choices=PLANS)
    parser.add_argument("--name")
    parser.add_argument("--sibling")
    parser.add_argument("--parent")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or rng.choice(sorted(ROOMS))
    lamp = args.lamp or rng.choice(sorted(LAMPS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    plan = args.plan or rng.choice(sorted(PLANS))
    name = args.name or rng.choice(NAMES)
    sibling = args.sibling or rng.choice([x for x in SIBLINGS if x != name])
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(room, lamp, helper, plan, name, sibling, parent)


CURATED = [
    StoryParams("bedroom", "nose_moon", "blanket", "share_lamp", "Nora", "Sam", "Mom"),
    StoryParams("attic", "nose_star", "button", "follow_glow", "Mina", "Owen", "Dad"),
    StoryParams("guestroom", "nose_cloud", "slipper", "use_nightlight", "Lila", "Theo", "Auntie"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print("  " + " ".join(map(str, combo)))
        return

    base = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name}: {sample.params.room}"
        elif len(samples) > 1:
            header = f"### bedtime story {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
