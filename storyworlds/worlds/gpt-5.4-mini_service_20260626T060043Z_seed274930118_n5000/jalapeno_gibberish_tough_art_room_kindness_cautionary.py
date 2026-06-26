#!/usr/bin/env python3
"""
A small whodunit-style storyworld set in an art room.

Premise:
- A child brings a jalapeno snack into an art room.
- Mysterious gibberish begins appearing on the craft board.
- A tough old glue cap goes missing.
- Kindness and caution turn the mystery into a gentle solution.

The simulation keeps track of physical state in meters and emotional state
in memes, then turns that state into a short child-facing story.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class Room:
    name: str = "the art room"
    clues: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    name: str
    helper: str
    prankster: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.steps: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

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


def pronoun(kind: str, case: str = "subject") -> str:
    if kind in {"girl", "mother", "woman"}:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if kind in {"boy", "father", "man"}:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


class ArtRoomWorld(World):
    pass


def build_world(params: StoryParams) -> World:
    world = World(Room())
    hero = world.add(Entity(id="hero", kind="character", type="child", label=params.name, memes={"curiosity": 1.0}))
    helper = world.add(Entity(id="helper", kind="character", type="child", label=params.helper, memes={"kindness": 1.0}))
    prankster = world.add(Entity(id="prankster", kind="character", type="child", label=params.prankster, memes={"nervousness": 1.0}))
    jalapeno = world.add(Entity(id="jalapeno", kind="thing", type="snack", label="jalapeno", phrase="a bright jalapeno snack"))
    board = world.add(Entity(id="board", kind="thing", type="board", label="message board", phrase="the big message board"))
    cap = world.add(Entity(id="cap", kind="thing", type="cap", label="tough glue cap", phrase="a tough little glue cap", caretaker=helper.id))

    world.facts.update(hero=hero, helper=helper, prankster=prankster, jalapeno=jalapeno, board=board, cap=cap)
    return world


def setup(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    prankster = world.get("prankster")
    jalapeno = world.get("jalapeno")
    cap = world.get("cap")

    world.say(f"{hero.label} was in the art room with {helper.label} and {prankster.label}.")
    world.say(f"{hero.label} had {jalapeno.phrase} tucked in a lunch box, because the day had started with a little spice.")
    world.say("The art room smelled like markers, paper, and old paint.")
    world.para()
    world.say(f"Near the sink sat {cap.phrase}, the one thing in the room that felt tough enough to handle sticky glue.")
    world.say("But by cleanup time, the cap was missing.")
    world.room.clues.append("gibberish on the board")
    world.room.clues.append("jalapeno crumbs")
    world.room.clues.append("sticky hands near the sink")
    world.facts["missing_cap"] = True


def mystery(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    prankster = world.get("prankster")
    board = world.get("board")
    jalapeno = world.get("jalapeno")

    world.para()
    world.say(f"Then something stranger happened: gibberish appeared on {board.label}.")
    world.say("It was not a real message. It looked like a joke with no punchline.")
    world.say(f"{hero.label} stared at the scribbles and felt a chill of worry, because the room suddenly seemed full of clues.")
    world.facts["gibberish_seen"] = True

    if jalapeno.label in {"jalapeno"}:
        world.say(f"One clue was easy to spot: tiny jalapeno crumbs glittered on the floor like orange dots.")
        world.facts["crumbs"] = True

    world.say(f"{helper.label} noticed that {prankster.label} had glue on {pronoun(prankster.type)} fingers.")
    world.facts["sticky_fingers"] = True


def turn(world: World) -> None:
    helper = world.get("helper")
    prankster = world.get("prankster")
    cap = world.get("cap")

    world.para()
    world.say(f"{helper.label} did not shout. Instead, {pronoun(helper.type)} spoke kindly and asked everyone to look together.")
    world.say(f"{helper.label} said the clue board was not for blaming, only for helping.")
    world.say(f"At that, {prankster.label} lowered {pronoun(prankster.type, 'possessive')} head and whispered that {pronoun(prankster.type)} had borrowed the tough glue cap to make a secret sign.")
    world.say("But the sign had turned into gibberish when the glue dripped and the marker slipped.")
    cap.meters["found"] = 1.0
    world.facts["confession"] = True
    world.facts["cap_found"] = True


def resolution(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    prankster = world.get("prankster")
    cap = world.get("cap")

    world.para()
    world.say(f"{hero.label} picked up the tough glue cap and handed it back without a mean word.")
    world.say(f"{helper.label} smiled at {prankster.label} and showed how to wipe the board clean.")
    world.say("Then everyone helped make a new picture card with careful lines instead of messy marks.")
    world.say(f"By the end, the gibberish was gone, the jalapeno crumbs were swept away, and the tough cap was back where it belonged.")
    world.say(f"{prankster.label} thanked {hero.label} for being kind enough to solve the mystery without turning it into a fight.")
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = build_world(params)
    setup(world)
    mystery(world)
    turn(world)
    resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    return [
        "Write a short whodunit story for a small child set in an art room, and include the words jalapeno, gibberish, and tough.",
        f"Tell a gentle mystery where {hero.label} notices gibberish on the art-room board and {helper.label} solves the puzzle with kindness.",
        "Create a cautionary but friendly story about a missing tough glue cap, a spicy snack, and a clue that turns out to be harmless.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    helper = world.get("helper")
    prankster = world.get("prankster")
    cap = world.get("cap")
    return [
        QAItem(
            question=f"Where was {hero.label} when the mystery began?",
            answer=f"{hero.label} was in the art room with {helper.label} and {prankster.label}.",
        ),
        QAItem(
            question="What strange thing appeared on the board?",
            answer="Gibberish appeared on the message board, which made the room feel like a mystery.",
        ),
        QAItem(
            question="What missing object was important in the story?",
            answer=f"The missing object was {cap.phrase}. It was the tough glue cap that belonged near the sink.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{helper.label} stayed kind, asked everyone to look together, and {prankster.label} admitted borrowing the cap. Then the children cleaned up the room and put everything back.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a jalapeno?",
            answer="A jalapeno is a spicy pepper. People can eat it in food, but its strong taste can surprise someone who is not expecting it.",
        ),
        QAItem(
            question="What does gibberish mean?",
            answer="Gibberish is writing or speech that does not make sense. It can look silly, confusing, or like a secret code that nobody can read.",
        ),
        QAItem(
            question="What does tough mean?",
            answer="Tough means strong and not easy to break, tear, or bend.",
        ),
        QAItem(
            question="Why is kindness helpful in a mystery?",
            answer="Kindness helps because people are more likely to tell the truth and work together when they feel safe.",
        ),
        QAItem(
            question="What should someone do with art supplies after using them?",
            answer="They should put art supplies back where they belong and clean up any spills so the room stays safe and neat.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== Prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for eid, ent in world.entities.items():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"{eid}: {ent.label} ({ent.type}) {' '.join(bits)}")
    lines.append(f"clues: {world.room.clues}")
    lines.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "art_room"),
            asp.fact("feature", "kindness"),
            asp.fact("feature", "cautionary"),
            asp.fact("word", "jalapeno"),
            asp.fact("word", "gibberish"),
            asp.fact("word", "tough"),
            asp.fact("clue", "board_scribble"),
            asp.fact("clue", "missing_cap"),
        ]
    )


ASP_RULES = r"""
setting_ok(art_room).
includes_word(jalapeno).
includes_word(gibberish).
includes_word(tough).
has_feature(kindness).
has_feature(cautionary).

mystery_story :- setting_ok(art_room), includes_word(jalapeno), includes_word(gibberish), includes_word(tough),
                 has_feature(kindness), has_feature(cautionary).

#show mystery_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_story/0."))
    ok = any(sym.name == "mystery_story" for sym in model)
    if not ok:
        print("MISMATCH: ASP did not prove mystery_story.")
        return 1
    print("OK: ASP twin proves mystery_story.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A whodunit-style art room storyworld with kindness and cautionary clues.")
    ap.add_argument("--name", default="Mina")
    ap.add_argument("--helper", default="June")
    ap.add_argument("--prankster", default="Ollie")
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
    return StoryParams(
        name=args.name or rng.choice(["Mina", "Luca", "Ivy", "Tessa", "Noah"]),
        helper=args.helper or rng.choice(["June", "Sage", "Nina", "Arlo", "Pia"]),
        prankster=args.prankster or rng.choice(["Ollie", "Milo", "Bea", "Ren", "Elsie"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_story/0."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(resolve_params(args, random.Random(base_seed + i))) for i in range(3)]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
