#!/usr/bin/env python3
"""
A small story world about a puppet theater, curiosity, and a bad ending.

A curious puppet in a Chinese puppet theater forsakes the stage rule,
slips past the curtain, and learns why the lantern room is off-limits.
The tale keeps a pirate-story flavor: a crew, a captain, a treasure-like
secret, and a cautionary turn that ends with a poor result instead of a tidy
fix.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    room: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "boy", "man", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Theater:
    name: str = "the puppet theater"
    style: str = "pirate tale"
    places: set[str] = field(default_factory=lambda: {"stage", "curtain", "back room", "lantern room"})
    off_limits: set[str] = field(default_factory=lambda: {"lantern room"})


class World:
    def __init__(self, theater: Theater) -> None:
        self.theater = theater
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy as _copy

        w = World(self.theater)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        return w


def finalize(world: World) -> None:
    actor = world.get("Puppet")
    captain = world.get("Captain")
    stage = world.get("Stage")
    secret = world.get("Secret")

    if actor.meters.get("curiosity", 0.0) >= THRESHOLD and actor.room == "lantern room":
        actor.meters["lost"] = 1.0
        stage.meters["broken"] = 1.0
        captain.memes["worry"] = captain.memes.get("worry", 0.0) + 1.0
        world.say(
            "The lantern rope snapped, a bright glow rolled across the floor, and the show went dark."
        )
        world.say(
            "The captain had to forsake the night's grand performance and pull the curtain down early."
        )
        world.say(
            f"In the end, {actor.id} stood in the hush with {secret.label} still out of reach, "
            "and the theater had a bad ending for the evening."
        )


@dataclass
class StoryParams:
    seed: Optional[int] = None


THEATER = Theater()

NAMES = ["Puppet", "Nimble", "Milo", "Jory", "Timo"]
CAPTAIN_NAMES = ["Captain Reed", "Captain Sable", "Captain Wren"]
TAGS = ["curious", "restless", "little"]


def build_world() -> World:
    world = World(THEATER)
    puppet = world.add(
        Entity(
            id="Puppet",
            kind="character",
            type="puppet",
            label="a small puppet",
            phrase="a small wooden puppet with painted eyes",
            traits=["curious", "little", "restless"],
            room="stage",
            meters={"curiosity": 0.0, "fear": 0.0, "mess": 0.0},
            memes={"curiosity": 0.0, "loyalty": 0.0, "worry": 0.0},
        )
    )
    captain = world.add(
        Entity(
            id="Captain",
            kind="character",
            type="captain",
            label="the captain",
            phrase="the captain of the puppet crew",
            traits=["stern", "proud"],
            room="back room",
            meters={"order": 1.0, "tired": 0.0},
            memes={"worry": 0.0, "pride": 1.0},
        )
    )
    stage = world.add(
        Entity(
            id="Stage",
            kind="thing",
            type="stage",
            label="the stage",
            phrase="the bright little stage",
            room="stage",
            meters={"sound": 1.0, "broken": 0.0},
            memes={"busy": 1.0},
        )
    )
    secret = world.add(
        Entity(
            id="Secret",
            kind="thing",
            type="lantern",
            label="the red lantern secret",
            phrase="a red lantern that made the shadows dance like waves",
            room="lantern room",
            meters={"glow": 1.0, "revealed": 0.0},
            memes={"mystery": 1.0},
        )
    )
    rope = world.add(
        Entity(
            id="Rope",
            kind="thing",
            type="rope",
            label="the curtain rope",
            phrase="a thick curtain rope",
            room="curtain",
            meters={"fray": 0.0},
        )
    )

    world.say(
        "At the Chinese puppet theater, the little crew loved to tell a pirate tale with drums, "
        "splashes, and a brave ship made of painted cloth."
    )
    world.say(
        f"{puppet.id} was a curious little puppet who loved the secret lantern glow behind the curtain."
    )
    world.say(
        f"{captain.id} warned, \"Do not forsake the stage, little matey. The back rooms are for the crew only.\""
    )
    world.para()
    puppet.meters["curiosity"] += 1.0
    puppet.memes["curiosity"] += 1.0
    world.say(
        f"But curiosity tugged hard on {puppet.pronoun('possessive')} strings."
    )
    world.say(
        f"{puppet.id} slipped past the curtain, tiptoed through the back room, and went where the lantern room was locked."
    )
    puppet.room = "lantern room"
    secret.meters["revealed"] = 1.0
    rope.meters["fray"] = 1.0
    world.say(
        "The little puppet found the lantern glow, but the floorboards creaked like a warning bell."
    )
    finalize(world)

    world.facts = {
        "puppet": puppet,
        "captain": captain,
        "stage": stage,
        "secret": secret,
        "rope": rope,
        "setting": THEATER,
        "bad_ending": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short pirate-tale style story set in a Chinese puppet theater about curiosity and a bad ending.',
        'Tell a child-friendly story where a curious puppet forsakes the stage and sneaks toward a lantern room.',
        'Write a simple story with drums, curtains, and a red lantern secret that ends badly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    puppet = f["puppet"]
    captain = f["captain"]
    secret = f["secret"]
    return [
        QAItem(
            question="What kind of place was the story set in?",
            answer="It was set in a Chinese puppet theater, where the crew put on a pirate tale with painted cloth and drums.",
        ),
        QAItem(
            question="Why did the puppet leave the stage?",
            answer="The puppet left because curiosity tugged hard on its strings, and it wanted to see the red lantern secret behind the curtain.",
        ),
        QAItem(
            question="What did the captain warn about?",
            answer="The captain warned the puppet not to forsake the stage and not to wander into the back rooms, because the lantern room was off-limits.",
        ),
        QAItem(
            question="What happened when the puppet reached the lantern room?",
            answer="The lantern rope snapped, the stage went dark, and the captain had to pull the curtain down early.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly, with the puppet stuck in the lantern room and the night's show ruined.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a puppet theater?",
            answer="A puppet theater is a place where people use puppets, strings, and a small stage to act out stories.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more about something, even when you have been told to stay back.",
        ),
        QAItem(
            question="What does it mean to forsake something?",
            answer="To forsake something means to leave it behind or stop doing it, even though you were supposed to stay with it.",
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is when things go wrong at the end instead of working out well.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.room:
            parts.append(f"room={e.room}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(parts)}")
    return "\n".join(lines)


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines = []
    lines.append(asp.fact("setting", "puppet_theater"))
    lines.append(asp.fact("style", "pirate_tale"))
    lines.append(asp.fact("feature", "curiosity"))
    lines.append(asp.fact("feature", "bad_ending"))
    lines.append(asp.fact("place", "stage"))
    lines.append(asp.fact("place", "curtain"))
    lines.append(asp.fact("place", "back_room"))
    lines.append(asp.fact("place", "lantern_room"))
    lines.append(asp.fact("off_limits", "lantern_room"))
    lines.append(asp.fact("character", "puppet"))
    lines.append(asp.fact("character", "captain"))
    lines.append(asp.fact("object", "lantern_secret"))
    lines.append(asp.fact("curious", "puppet"))
    lines.append(asp.fact("warns", "captain", "puppet"))
    lines.append(asp.fact("wants", "puppet", "lantern_secret"))
    return "\n".join(lines)


ASP_RULES = r"""
% The puppet has a bad ending if curiosity leads it into the off-limits lantern room.
bad_move(P) :- curious(P), wants(P, S), off_limits(R), reaches(P, R), secret(S).
bad_ending :- bad_move(puppet).

% A ship-shape cautionary tale includes a warning and a rule broken.
warning_given :- warns(captain, puppet).
rule_broken :- reaches(puppet, lantern_room), off_limits(lantern_room).

#show bad_ending/0.
#show warning_given/0.
#show rule_broken/0.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    atoms = {sym.name for sym in model}
    needed = {"bad_ending", "warning_given", "rule_broken"}
    if needed.issubset(atoms):
        print("OK: ASP model matches the story world.")
        return 0
    print("MISMATCH: ASP model missing expected atoms.")
    print("Got:", sorted(atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Curiosity, puppet theater, pirate tale, bad ending.")
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
    return StoryParams(seed=args.seed if args.seed is not None else rng.randrange(2**31))


def generate(params: StoryParams) -> StorySample:
    world = build_world()
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern: curiosity -> warning -> rule broken -> bad ending")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(seed=base_seed))]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

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
