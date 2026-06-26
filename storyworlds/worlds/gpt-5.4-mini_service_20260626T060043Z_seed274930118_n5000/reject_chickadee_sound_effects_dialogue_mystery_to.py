#!/usr/bin/env python3
"""
Space-adventure story world: a small ship, a mysterious sound, a chickadee,
and a careful rejection of the wrong guess before the real answer is found.

The domain is built around:
- reject / rejection of a bad explanation
- chickadee as the surprising small visitor
- sound effects as an important clue
- dialogue as the main social instrument
- mystery to solve with a clear resolution
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "captain"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "pilot"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    ship_name: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        import copy
        clone = World(self.ship_name)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    ship: str
    room: str
    mystery: str
    culprit: str
    child_name: str
    child_type: str
    captain_name: str
    seed: Optional[int] = None


SHIPS = {
    "starling": "the Starling",
    "comet": "the Comet",
    "aurora": "the Aurora",
}

ROOMS = {
    "bridge": "the bridge",
    "corridor": "the silver corridor",
    "engine_room": "the engine room",
    "cargo_bay": "the cargo bay",
}

MYSTERIES = {
    "chirp": {
        "sound": "chirp-chirp",
        "clue": "a tiny set of feather marks near the vent",
        "wrong_guess": "a broken radio",
        "solution": "a chickadee hiding in the vent",
        "effect": "chirped softly",
    },
    "tap": {
        "sound": "tap-tap-tap",
        "clue": "three little pecks on the metal grate",
        "wrong_guess": "a loose wrench",
        "solution": "a chickadee tapping for crumbs",
        "effect": "tapped quickly",
    },
    "flutter": {
        "sound": "flutter-flip",
        "clue": "a tiny shadow that darted across the light",
        "wrong_guess": "a drifting glove",
        "solution": "a chickadee fluttering near the snack box",
        "effect": "fluttered past",
    },
}

CHILD_NAMES = ["Mina", "Leo", "Ari", "Nia", "Toby", "Ivy"]
CHILD_TYPES = ["girl", "boy"]
CAPTAIN_NAMES = ["Captain Rook", "Captain Vale", "Captain Sora", "Captain Quill"]


# ---------------------------------------------------------------------------
# Story utilities
# ---------------------------------------------------------------------------
def clean_article(text: str) -> str:
    return re.sub(r"\b(a|an)\s+([aeiouAEIOU])", r"an \2", text)


def ind_article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def title_for_ship(ship: str) -> str:
    return SHIPS[ship]


def room_for(room: str) -> str:
    return ROOMS[room]


def mystery_for(mystery: str) -> dict:
    return MYSTERIES[mystery]


def build_world(params: StoryParams) -> World:
    world = World(title_for_ship(params.ship))
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    captain = world.add(Entity(id="captain", kind="character", type="captain", label=params.captain_name))
    chickadee = world.add(Entity(id="chickadee", kind="thing", type="chickadee", label="a chickadee"))
    panel = world.add(Entity(id="panel", kind="thing", type="panel", label="a vent panel", location=room_for(params.room)))
    clue = mystery_for(params.mystery)

    world.facts.update(
        child=child,
        captain=captain,
        chickadee=chickadee,
        panel=panel,
        ship=params.ship,
        room=params.room,
        mystery=params.mystery,
        clue=clue,
        culprit=params.culprit,
    )

    # emotional baseline
    child.memes["curiosity"] = 1.0
    child.memes["surprise"] = 0.5
    captain.memes["calm"] = 1.0
    chickadee.meters["smallness"] = 1.0
    chickadee.meters["feather"] = 1.0
    return world


def predict_wrong_guess(world: World, mystery: dict) -> bool:
    # A deliberate reasonableness gate: the wrong guess is always rejected.
    return True


# ---------------------------------------------------------------------------
# Narrative beats
# ---------------------------------------------------------------------------
def act1(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    captain: Entity = f["captain"]
    clue = f["clue"]

    world.say(
        f"On {world.ship_name}, {child.label} loved listening to the quiet hum of the engines "
        f"and watching the stars slide past the windows."
    )
    world.say(
        f"One evening, a strange sound echoed through {room_for(f['room'])}: "
        f"'{mystery_for(f['mystery'])['sound']}!'"
    )
    world.say(
        f"{child.label} pointed at {clue['clue']} and said, "
        f"\"Did you hear that?\""
    )
    world.say(
        f"{captain.label} leaned in. \"I heard it,\" {captain.pronoun()} said, "
        f"\"but we should not jump to a wild guess.\""
    )


def act2(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    captain: Entity = f["captain"]
    clue = f["clue"]

    world.para()
    world.say(
        f"The first guess was {ind_article(clue['wrong_guess'])} {clue['wrong_guess']}, "
        f"but {child.label} shook {child.pronoun('possessive')} head."
    )
    world.say(
        f"\"No,\" {child.label} said, \"that would not leave {clue['clue']}.\""
    )
    world.say(
        f"{captain.label} nodded. \"Good thinking. We will reject that idea.\""
    )
    world.say(
        f"They followed the sound to the vent, where the little noise went "
        f"{mystery_for(f['mystery'])['effect']} again."
    )
    world.say(
        f"\"Look!\" {child.label} whispered. \"Something tiny is there.\""
    )


def act3(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    captain: Entity = f["captain"]
    chickadee: Entity = f["chickadee"]
    clue = f["clue"]

    world.para()
    world.say(
        f"Inside the vent, they found {clue['solution']}. "
        f"The chickadee had been stealing crumbs from a snack box and making the sound all along."
    )
    world.say(
        f"{captain.label} opened the hatch a little and said, \"Hello there, little traveler.\""
    )
    world.say(
        f"{child.label} laughed. \"So the mystery was a chickadee!\""
    )
    world.say(
        f"They slid a bowl of seeds near the opening, and the chickadee "
        f"fluttered out, chirped once, and hopped safely away."
    )
    world.say(
        f"By bedtime, the ship was quiet again, and {child.label} smiled at the "
        f"tiny feather tracks left by the solved mystery."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    act1(world)
    act2(world)
    act3(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short space-adventure story about {f['child'].label} hearing "
        f"a mysterious sound on {world.ship_name} and solving it without making a silly guess.",
        f"Tell a child-friendly mystery story with dialogue, a small sound clue, "
        f"and a chickadee hidden in a spaceship vent.",
        f"Write a story where the crew rejects the wrong explanation and finds "
        f"the real source of '{mystery_for(f['mystery'])['sound']}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    captain: Entity = f["captain"]
    clue = f["clue"]
    mystery = mystery_for(f["mystery"])
    return [
        QAItem(
            question=f"What mysterious sound did {child.label} hear on {world.ship_name}?",
            answer=f"{child.label} heard the sound '{mystery['sound']}' in {room_for(f['room'])}.",
        ),
        QAItem(
            question=f"What wrong guess did {captain.label} reject?",
            answer=f"They rejected the idea that it was {ind_article(clue['wrong_guess'])} {clue['wrong_guess']}.",
        ),
        QAItem(
            question=f"What really made the sound?",
            answer=f"The sound came from {mystery['solution']}.",
        ),
        QAItem(
            question=f"How did the story end after the mystery was solved?",
            answer=f"The chickadee got seeds, flew out safely, and the ship became quiet again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chickadee?",
            answer="A chickadee is a small bird with quick movements and a lively chirp.",
        ),
        QAItem(
            question="Why do people listen carefully when they hear a mystery sound?",
            answer="People listen carefully so they can find clues and figure out what is really happening.",
        ),
        QAItem(
            question="What does it mean to reject a guess?",
            answer="To reject a guess means to decide it is not the right answer.",
        ),
        QAItem(
            question="Why can sound effects help in a story?",
            answer="Sound effects can make the scene feel real and give clues about what is going on.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
ship(S) :- ship_fact(S).
room(R) :- room_fact(R).
mystery(M) :- mystery_fact(M).

wrong_guess(M, G) :- wrong_guess_fact(M, G).
solution(M, S) :- solution_fact(M, S).
sound(M, X) :- sound_fact(M, X).

valid_story(S, R, M) :- ship(S), room(R), mystery(M),
                        sound(M, _), wrong_guess(M, _), solution(M, _).

reject_guess(M) :- wrong_guess(M, _), solution(M, _).
solve_mystery(M) :- reject_guess(M), solution(M, _).
#show valid_story/3.
#show reject_guess/1.
#show solve_mystery/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SHIPS:
        lines.append(asp.fact("ship_fact", sid))
    for rid in ROOMS:
        lines.append(asp.fact("room_fact", rid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery_fact", mid))
        lines.append(asp.fact("sound_fact", mid, m["sound"]))
        lines.append(asp.fact("wrong_guess_fact", mid, m["wrong_guess"]))
        lines.append(asp.fact("solution_fact", mid, m["solution"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, r, m) for s in SHIPS for r in ROOMS for m in MYSTERIES}
    clingo = set(asp_valid_stories())
    if py == clingo:
        print(f"OK: ASP matches Python story space ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only python:", sorted(py - clingo))
    print("only asp:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# Sample generation and CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space mystery storyworld with a chickadee and a rejected guess.")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=CHILD_TYPES)
    ap.add_argument("--captain")
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
    ship = args.ship or rng.choice(list(SHIPS))
    room = args.room or rng.choice(list(ROOMS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(CHILD_TYPES)
    name = args.name or rng.choice(CHILD_NAMES)
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    return StoryParams(ship=ship, room=room, mystery=mystery, culprit="chickadee", child_name=name, child_type=gender, captain_name=captain)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for s, r, m in combos:
            print(f"{s:8} {r:12} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for ship in SHIPS:
            for room in ROOMS:
                for mystery in MYSTERIES:
                    params = StoryParams(
                        ship=ship,
                        room=room,
                        mystery=mystery,
                        culprit="chickadee",
                        child_name=random.choice(CHILD_NAMES),
                        child_type=random.choice(CHILD_TYPES),
                        captain_name=random.choice(CAPTAIN_NAMES),
                    )
                    samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
