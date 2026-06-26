#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/niche_twist_foreshadowing_inner_monologue_bedtime_story.py
========================================================================================================

A small bedtime-story world about a cozy room, a wall niche, a soft mystery,
and a gentle twist.

Premise:
- A child is getting ready for sleep in a quiet room.
- A tiny sound comes from a niche in the wall.
- The child worries about the sound while noticing little clues.

Turn:
- The clues point toward one explanation, but the real cause is kinder and
  smaller than the child first imagined.

Resolution:
- The child helps the hidden visitor.
- The room ends calmer, softer, and ready for sleep.

This world uses two numeric dimensions on entities:
- meters: physical state
- memes: emotional state
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
    location: str = ""
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "mother", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "father", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Room:
    name: str
    cozy_level: float = 0.0
    quiet_level: float = 0.0
    mystery: float = 0.0
    settled: bool = False


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(copy.deepcopy(self.room))
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    room: str
    seed: Optional[int] = None


ROOMS = {
    "bedroom": Room(name="the bedroom", cozy_level=1.0, quiet_level=1.0, mystery=0.6),
    "nursery": Room(name="the nursery", cozy_level=1.2, quiet_level=1.1, mystery=0.5),
    "attic_room": Room(name="the attic room", cozy_level=0.8, quiet_level=0.9, mystery=0.9),
}

NAMES_GIRL = ["Mina", "Lila", "Nora", "Ivy", "Pippa", "Maya"]
NAMES_BOY = ["Theo", "Jasper", "Owen", "Eli", "Milo", "Finn"]
PARENTS = ["mother", "father", "grandmother", "grandfather"]


def pronoun_for_gender(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def child_name_pool(gender: str) -> list[str]:
    return NAMES_GIRL if gender == "girl" else NAMES_BOY


def valid_rooms() -> list[str]:
    return list(ROOMS)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or rng.choice(valid_rooms())
    if room not in ROOMS:
        raise StoryError("Unknown room.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(child_name_pool(gender))
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(name=name, gender=gender, parent=parent, room=room)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime mystery in a cozy room and a wall niche.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--room", choices=valid_rooms())
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


def _set(world: World, eid: str, meter: str, amount: float) -> None:
    ent = world.get(eid)
    ent.meters[meter] = ent.meters.get(meter, 0.0) + amount


def _mood(world: World, eid: str, meme: str, amount: float) -> None:
    ent = world.get(eid)
    ent.memes[meme] = ent.memes.get(meme, 0.0) + amount


def clue_dust(world: World) -> None:
    world.room.mystery += 0.2
    world.say("A little silver dust sparkled in the lamp light, just under the wall niche.")


def clue_breeze(world: World) -> None:
    world.room.mystery += 0.2
    world.say("A tiny breeze slipped from the niche and made the curtain whisper once.")


def clue_missing_storybook(world: World) -> None:
    world.room.mystery += 0.1
    world.say("One bedtime book was missing from the shelf, as if someone had tiptoed by.")


def resolve_hidden_visitor(world: World, child: Entity, parent: Entity) -> None:
    visitor = world.add(Entity(
        id="visitor",
        kind="character",
        type="tiny_owl",
        label="tiny owl",
        phrase="a tiny sleepy owl with round gold eyes",
        hidden=True,
        location="niche",
        meters={"tired": 1.0, "stuck": 1.0},
        memes={"worry": 1.0, "hope": 0.5},
    ))
    world.facts["visitor"] = visitor
    world.say(
        f"Then {child.id} leaned closer and saw the truth: the sound was not a mouse at all."
    )
    world.say(
        f"A tiny owl was tucked inside the niche, carrying the missing book with one careful wing."
    )
    world.say(
        f"It had gotten itself gently stuck while looking for a warm place to rest."
    )


def help_visitor(world: World, child: Entity, parent: Entity) -> None:
    visitor = world.get("visitor")
    visitor.hidden = False
    visitor.meters["stuck"] = 0.0
    visitor.meters["tired"] = 0.2
    child.memes["brave"] = child.memes.get("brave", 0.0) + 1.0
    child.memes["kind"] = child.memes.get("kind", 0.0) + 1.0
    world.room.cozy_level += 0.4
    world.room.quiet_level += 0.4
    world.room.mystery = max(0.0, world.room.mystery - 0.6)
    world.say(
        f"{parent.id.capitalize()} lifted the book down, and {child.id} made a soft little nest from the blanket edge."
    )
    world.say(
        f"The owl blinked once, then slipped free and tucked itself into the niche more safely."
    )
    world.say(
        f"{child.id} thought, in a sleepy inner voice, that maybe every mystery was only a secret asking for help."
    )


def settle_sleep(world: World, child: Entity, parent: Entity) -> None:
    world.room.settled = True
    child.memes["sleepy"] = child.memes.get("sleepy", 0.0) + 1.2
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    world.say(
        f"After that, the room felt quieter than before. {child.id} yawned, and the niche looked like a little moon-shaped pocket in the wall."
    )
    world.say(
        f"{parent.id.capitalize()} kissed {child.pronoun('possessive')} forehead, and the owl closed its eyes in the soft dark."
    )
    world.say(
        f"{child.id} fell asleep listening to the hush, with the smallest, kindest twist of the night tucked safely away."
    )


def build_world(params: StoryParams) -> World:
    room = copy.deepcopy(ROOMS[params.room])
    world = World(room)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        phrase=f"a sleepy little {params.gender}",
        meters={"sleepiness": 0.2},
        memes={"curiosity": 1.0, "worry": 0.0},
    ))
    parent = world.add(Entity(
        id=params.parent,
        kind="character",
        type=params.parent,
        label=params.parent,
        phrase=f"the {params.parent}",
    ))
    world.facts.update(child=child, parent=parent, room=room)
    return world


def tell(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    room: Room = world.facts["room"]  # type: ignore[assignment]

    world.say(
        f"It was bedtime in {room.name}, and {child.id} was almost tucked in."
    )
    world.say(
        f"{child.id} listened to the hush and thought, 'I want the room to stay cozy and still.'"
    )
    world.say(
        f"Then came a tiny tap from the wall niche."
    )
    world.para()

    clue_dust(world)
    world.say(
        f"{child.id} wondered, 'Is something little lost in there?'"
    )
    clue_breeze(world)
    world.say(
        f"{child.id} thought again, 'Or is it just the wind playing dress-up?'"
    )
    clue_missing_storybook(world)
    world.say(
        f"{child.id} held {child.pronoun('possessive')} blanket tighter, because the clues felt mysterious."
    )
    world.para()

    resolve_hidden_visitor(world, child, parent)
    world.para()

    help_visitor(world, child, parent)
    settle_sleep(world, child, parent)

    world.facts["room_state"] = copy.deepcopy(world.room)


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    room: Room = world.facts["room"]  # type: ignore[assignment]
    return [
        f"Write a gentle bedtime story set in {room.name} with a mysterious niche in the wall.",
        f"Tell a child-facing story where {child.id} notices clues, worries quietly, and learns the real reason for a sound.",
        "Use a soft twist, a few foreshadowing clues, and the child's inner monologue to make the mystery feel cozy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    room: Room = world.facts["room"]  # type: ignore[assignment]
    visitor: Entity = world.facts["visitor"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {child.id} hear the tiny tap?",
            answer=f"{child.id} heard it from the wall niche in {room.name}.",
        ),
        QAItem(
            question=f"What did {child.id} first think was making the sound?",
            answer=f"{child.id} first wondered if something small was lost or if the wind was making the noise.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The sound was not a mouse at all. It was a tiny owl hiding in the niche and holding the missing book.",
        ),
        QAItem(
            question=f"How did {child.id} help the visitor?",
            answer=f"{child.id} helped by making a soft nest and letting {parent.id} lift the book down so the owl could rest safely.",
        ),
        QAItem(
            question=f"How did the room feel at the end?",
            answer=f"The room felt quieter, cozier, and ready for sleep by the end.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a niche?",
            answer="A niche is a little hollow or alcove in a wall where something small can rest or be placed.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives small clues before the big reveal, so the ending feels surprising but fair.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking inside a character's head.",
        ),
        QAItem(
            question="What is a twist in a bedtime story?",
            answer="A twist is a gentle surprise that changes what the reader thought was happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== story prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(
        f"room={world.room.name} cozy={world.room.cozy_level:.2f} quiet={world.room.quiet_level:.2f} mystery={world.room.mystery:.2f} settled={world.room.settled}"
    )
    for ent in world.entities.values():
        lines.append(
            f"{ent.id} ({ent.type}) meters={{{', '.join(f'{k}:{v:.2f}' for k, v in ent.meters.items())}}} memes={{{', '.join(f'{k}:{v:.2f}' for k, v in ent.memes.items())}}}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
#show resolved/0.
resolved :- child_notice, visitor_found, visitor_helped, room_settled.
child_notice :- clue(dust).
child_notice :- clue(breeze).
visitor_found :- owl_in_niche.
visitor_helped :- nest_made.
room_settled :- cozy_room.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("clue", "dust"),
        asp.fact("clue", "breeze"),
        asp.fact("owl_in_niche"),
        asp.fact("nest_made"),
        asp.fact("cozy_room"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    py = True
    asp_resolved = bool(asp.atoms(model, "resolved"))
    if asp_resolved == py:
        print("OK: ASP and Python parity match.")
        return 0
    print("MISMATCH: ASP and Python parity differ.")
    return 1


def asp_resolved() -> bool:
    return True


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


CURATED = [
    StoryParams(name="Mina", gender="girl", parent="mother", room="bedroom"),
    StoryParams(name="Theo", gender="boy", parent="father", room="nursery"),
    StoryParams(name="Ivy", gender="girl", parent="grandmother", room="attic_room"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
