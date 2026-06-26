#!/usr/bin/env python3
"""
storyworlds/worlds/pewter_bravery_ghost_story.py
=================================================

A small classical story world for a gentle Ghost Story with a bravery turn.

Seed image:
- An old house is quiet at night.
- A child hears a ghost in the dark.
- The ghost has lost a pewter keepsake.
- The child is scared, but bravery grows.
- Together they search, find the pewter thing, and the house feels warm again.

This script builds that premise as a tiny simulated world with physical meters
and emotional memes, plus a matching ASP twin for reasonableness checks.
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

ROOMS = {
    "attic": {"dark", "dusty", "quiet"},
    "hall": {"quiet", "echoing"},
    "cellar": {"dark", "cool"},
    "nursery": {"quiet", "soft"},
}

ACTIONS = {
    "search": {
        "verb": "search the room",
        "gerund": "searching the room",
        "risk": "missing clues in the dark",
        "need": "bravery",
    },
    "listen": {
        "verb": "listen for the ghost",
        "gerund": "listening for the ghost",
        "risk": "getting too frightened to hear the clues",
        "need": "bravery",
    },
    "follow": {
        "verb": "follow the soft glow",
        "gerund": "following the soft glow",
        "risk": "losing the glow in the shadows",
        "need": "bravery",
    },
}

RELICS = {
    "bell": {"label": "pewter bell", "room": "attic", "shine": "small and silver-gray"},
    "key": {"label": "pewter key", "room": "cellar", "shine": "cool and bright"},
    "cup": {"label": "pewter cup", "room": "hall", "shine": "dull and moonlike"},
}

NAMES = ["Maya", "Nora", "Eli", "Finn", "Lia", "Owen", "June", "Iris"]
GHOST_NAMES = ["Mottle", "Whisper", "Pale", "Tilly"]
TRAITS = ["curious", "gentle", "quiet", "bold", "careful"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    room: str = ""
    glowing: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    room: str
    action: str
    relic: str
    name: str
    gender: str
    ghost_name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: str) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def _ghost_known(world: World) -> bool:
    return world.get("ghost").memes.get("heard", 0) >= 1


def _brave(world: World) -> bool:
    return world.get("hero").memes.get("bravery", 0) >= 1


def tell(params: StoryParams) -> World:
    world = World(params.room)
    hero = world.add(Entity(
        id="hero", kind="character", type=params.gender, label=params.name,
        room=params.room, meters={"fear": 0.0}, memes={"bravery": 0.0, "curiosity": 1.0},
    ))
    ghost = world.add(Entity(
        id="ghost", kind="character", type="ghost", label=params.ghost_name,
        room=params.room, glowing=True, meters={"loneliness": 1.0}, memes={"sad": 1.0},
    ))
    relic_def = RELICS[params.relic]
    relic = world.add(Entity(
        id="relic", kind="thing", type="relic", label=relic_def["label"],
        phrase=f"a {relic_def['shine']} {relic_def['label']}",
        room=relic_def["room"], glowing=False,
    ))

    world.say(f"On a quiet night, {hero.label} walked into the {params.room} of the old house.")
    world.say(f"{hero.pronoun().capitalize()} liked brave stories, but the house still felt a little spooky.")
    world.say(f"Then {ghost.label} drifted out of the shadows and whispered, \"I lost my {relic.label}.\"")
    ghost.memes["heard"] = 1.0
    hero.meters["fear"] += 1.0
    world.say(f"{hero.label}'s heart skipped, because the dark felt bigger than before.")

    world.say(f"{hero.label} took a slow breath and decided to be brave.")
    hero.memes["bravery"] += 1.0
    hero.meters["fear"] = max(0.0, hero.meters["fear"] - 1.0)
    world.say(f"{hero.pronoun().capitalize()} said, \"I can help you look.\"")

    action = ACTIONS[params.action]
    if params.action == "search":
        world.say(f"{hero.label} began {action['gerund']}, peeking behind boxes and old trunks.")
    elif params.action == "listen":
        world.say(f"{hero.label} stood still, {action['gerund']}, until a tiny clink answered from the dust.")
    else:
        world.say(f"{hero.label} kept close to the ghost and went {action['gerund']} toward the softest glow.")

    if params.room == relic_def["room"]:
        relic.glowing = True
        world.say(f"Under a dusty board, there it was: {relic.phrase}.")
        world.say(f"{hero.label} picked it up carefully and placed it back in {ghost.label}'s waiting hand.")
        ghost.memes["sad"] = 0.0
        ghost.meters["loneliness"] = 0.0
        ghost.glowing = True
        world.say(f"{ghost.label} shone brighter, and the room felt warm instead of spooky.")
    else:
        world.say(f"The clue led to an empty corner, so {hero.label} kept looking until {ghost.label} pointed the way.")
        relic.glowing = True
        world.say(f"At last they found {relic.phrase} waiting where the room was darkest.")
        world.say(f"{hero.label} laughed with relief when {ghost.label} floated it back into place.")
        ghost.memes["sad"] = 0.0
        ghost.meters["loneliness"] = 0.0

    world.say(f"By the end, {hero.label} was still in the {params.room}, but {hero.pronoun()} did not feel afraid anymore.")
    world.facts.update(hero=hero, ghost=ghost, relic=relic, params=params, action=action)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for room in ROOMS:
        for action in ACTIONS:
            for relic, rel in RELICS.items():
                if room == rel["room"]:
                    out.append((room, action, relic))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a gentle ghost story for a young child that includes the word "pewter" and ends with bravery winning over fear.',
        f"Tell a short story where {p.name} meets a ghost in the {p.room} and helps find a lost pewter {p.relic}.",
        f"Write a spooky-but-kind story about {p.name}, {p.ghost_name}, and a brave search through an old house.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    hero: Entity = f["hero"]
    ghost: Entity = f["ghost"]
    relic: Entity = f["relic"]
    return [
        QAItem(
            question=f"Who was the story about in the {p.room}?",
            answer=f"The story was about {hero.label}, a {p.trait} child who met {ghost.label} in the {p.room}.",
        ),
        QAItem(
            question=f"What did {ghost.label} lose?",
            answer=f"{ghost.label} lost the {relic.label}, which was a pewter keepsake the ghost wanted back.",
        ),
        QAItem(
            question=f"How did {hero.label} feel before being brave?",
            answer=f"{hero.label} felt scared when the ghost appeared, because the dark felt bigger all at once.",
        ),
        QAItem(
            question=f"What changed after the {relic.label} was found?",
            answer=f"After the {relic.label} was found, {ghost.label} became bright and happy, and {hero.label} felt safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pewter?",
            answer="Pewter is a soft, gray metal that can look shiny or dull, like moonlight on a cloudy night.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something even when you feel scared, especially if it helps someone else.",
        ),
        QAItem(
            question="Why do people use a lamp in the dark?",
            answer="People use a lamp in the dark so they can see where they are going and feel safer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
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
    bits = ["--- world trace ---"]
    for e in world.entities.values():
        bits.append(f"{e.id}: type={e.type} room={e.room} meters={e.meters} memes={e.memes}")
    return "\n".join(bits)


ASP_RULES = r"""
room_has_relic(R, Relic) :- relic_in(Relic, R).
valid(R, A, Relic) :- room(R), action(A), relic(Relic), room_has_relic(R, Relic).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for room in ROOMS:
        lines.append(asp.fact("room", room))
    for action in ACTIONS:
        lines.append(asp.fact("action", action))
    for relic, rel in RELICS.items():
        lines.append(asp.fact("relic", relic))
        lines.append(asp.fact("relic_in", relic, rel["room"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world with pewter and bravery.")
    ap.add_argument("--room", choices=sorted(ROOMS))
    ap.add_argument("--action", choices=sorted(ACTIONS))
    ap.add_argument("--relic", choices=sorted(RELICS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--ghost-name", dest="ghost_name")
    ap.add_argument("--trait", choices=sorted(TRAITS))
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
    combos = valid_combos()
    if args.room and args.action and args.relic:
        if (args.room, args.action, args.relic) not in combos:
            raise StoryError("That room, action, and relic do not fit together in this ghost story.")
    eligible = [c for c in combos
                if (not args.room or c[0] == args.room)
                and (not args.action or c[1] == args.action)
                and (not args.relic or c[2] == args.relic)]
    if not eligible:
        raise StoryError("No valid combination matches the given options.")
    room, action, relic = rng.choice(sorted(eligible))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(room=room, action=action, relic=relic, name=name, gender=gender, ghost_name=ghost_name, trait=trait)


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for room, action, relic in valid_combos():
            params = StoryParams(
                room=room,
                action=action,
                relic=relic,
                name=NAMES[(len(samples)) % len(NAMES)],
                gender="girl" if len(samples) % 2 == 0 else "boy",
                ghost_name=GHOST_NAMES[len(samples) % len(GHOST_NAMES)],
                trait=TRAITS[len(samples) % len(TRAITS)],
                seed=base_seed + len(samples),
            )
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
