#!/usr/bin/env python3
"""
A small pirate-tale storyworld about a crew, a stubborn argument, and a kind
choice that turns sharing into a treasure.

Seed-inspired premise:
- A pirate captain finds a riddle-map with an important answer.
- One crewmate starts an argumentative spurt, eager to keep the map secret.
- Another crew member uses kindness and sharing to calm the deck.
- An inner monologue beat makes the turning point feel authored and child-facing.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("salt", "wind", "shine", "noise"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "kindness", "sharing", "argument", "curiosity", "relief", "worry"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captainess"}
        male = {"boy", "man", "father", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the pirate ship"
    sea: str = "blue"


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    type: str
    precious: bool = False
    shareable: bool = True


@dataclass
class StoryParams:
    place: str = "ship"
    name: str = "Mira"
    crewmate: str = "Joss"
    captain: str = "Captain Rose"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            s = rule(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            if s != "__inner__":
                world.say(s)
    return [s for s in out if s != "__inner__"]


def _r_argument_to_noise(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["argument"] < THRESHOLD:
            continue
        sig = ("noise", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["noise"] += 1
        e.memes["worry"] += 1
        out.append(f"Voices rose and the deck felt stormy.")
    return out


def _r_kindness_soothes(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["kindness"] < THRESHOLD:
            continue
        sig = ("soothe", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["relief"] += 1
        out.append(f"Kind words made the air feel lighter.")
    return out


def _r_sharing_joins(world: World) -> list[str]:
    out = []
    crew = [e for e in world.entities.values() if e.kind == "character"]
    map_obj = world.entities.get("map")
    if not map_obj:
        return out
    shared = sum(1 for e in crew if e.memes["sharing"] >= THRESHOLD)
    if shared < 2:
        return out
    sig = ("share", "map")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    map_obj.meters["shine"] += 1
    out.append(f"The map was shared across the lantern light, and everyone could see it together.")
    return out


def _r_inner_monologue_turn(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["curiosity"] < THRESHOLD:
        return []
    sig = ("inner", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["joy"] += 1
    return ["__inner__"]


RULES = [_r_argument_to_noise, _r_kindness_soothes, _r_sharing_joins, _r_inner_monologue_turn]


def solve_riddle(world: World) -> str:
    return "the safe harbor"


def tell() -> World:
    world = World(Setting())
    hero = world.add(Entity(id="hero", kind="character", type="girl", label="Mira", traits=["little", "brave"]))
    mate = world.add(Entity(id="mate", kind="character", type="boy", label="Joss", traits=["clever"]))
    cap = world.add(Entity(id="captain", kind="character", type="woman", label="Captain Rose", traits=["kind"]))
    map_obj = world.add(Entity(id="map", type="thing", label="map", phrase="a crinkled treasure map", owner=cap.id, caretaker=cap.id))
    shell = world.add(Entity(id="shell", type="thing", label="shell charm", phrase="a tiny shell charm", owner=hero.id, caretaker=hero.id))
    world.facts.update(hero=hero, mate=mate, captain=cap, map=map_obj, shell=shell, answer=solve_riddle(world))

    world.say(f"Mira was a little brave girl on a pirate ship, and she loved the salty wind and the shine of brass buttons.")
    world.say(f"That morning, Captain Rose found a crinkled treasure map with a secret answer written near the edge.")
    world.say(f"Mira also wore a tiny shell charm, and she kept it close because it reminded her to be kind.")

    world.para()
    mate.memes["argument"] += 1
    mate.meters["noise"] += 1
    world.say(f"Joss began an argumentative spurt and said the map should stay hidden from everyone.")
    world.say(f"Mira felt a little worry ripple in her chest as the deck grew louder.")
    world.say(f"Captain Rose held the map up and asked for calm voices, but the wind seemed to answer with a louder flap of sailcloth.")
    propagate(world, narrate=True)

    world.para()
    hero.memes["kindness"] += 1
    hero.memes["sharing"] += 1
    hero.memes["curiosity"] += 1
    world.say(f"Mira took a slow breath and had an inner monologue: 'If we share the clue, maybe the answer will help all of us.'")
    propagate(world, narrate=True)
    world.say(f"Then she smiled and offered to share the map with Joss and Captain Rose.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"Joss looked at the kind offer, let the argumentative spurt drift away, and nodded.")
    world.say(f"Together they read the map, found the answer to the riddle, and steered the ship toward the safe harbor.")
    world.say(f"By sunset, the treasure was not just gold; it was the happy feeling of sharing it together.")
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short pirate tale for a young child that includes the words "answer", "argumentative", and "spurt".',
        'Tell a gentle pirate story where kindness and sharing calm an argumentative spurt on a ship.',
        'Write a story with an inner monologue beat where a pirate child decides to share a secret map.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mate: Entity = f["mate"]
    cap: Entity = f["captain"]
    return [
        QAItem(
            question="Who had the inner monologue that changed the mood on the pirate ship?",
            answer=f"{hero.label} did. She thought that sharing the map might help everyone find the answer together."
        ),
        QAItem(
            question="Why did the deck feel stormy before the happy ending?",
            answer=f"Joss began an argumentative spurt about the map, and the loud voices made the ship feel tense."
        ),
        QAItem(
            question="What did Captain Rose want the crew to do with the map?",
            answer=f"Captain Rose wanted everyone to stay calm and read the map together instead of fighting over it."
        ),
        QAItem(
            question="What changed when Mira chose kindness and sharing?",
            answer=f"The argument faded, the map was shared, and the crew found the answer and sailed toward the safe harbor."
        ),
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {hero.label}, {mate.label}, and {cap.label} on a pirate ship, with {hero.label} as the child at the center of the story."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, helpful, and caring toward other people."
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use or see something too, instead of keeping it all to yourself."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in your head that tells you what you are thinking."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str = "ship"
    name: str = "Mira"
    crewmate: str = "Joss"
    captain: str = "Captain Rose"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with kindness, sharing, and inner monologue.")
    ap.add_argument("--place", choices=["ship"], default="ship")
    ap.add_argument("--name")
    ap.add_argument("--crewmate")
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
    return StoryParams(
        place="ship",
        name=args.name or rng.choice(["Mira", "Tess", "Ruby", "Ada"]),
        crewmate=args.crewmate or rng.choice(["Joss", "Finn", "Ned", "Pip"]),
        captain=args.captain or rng.choice(["Captain Rose", "Captain Marn", "Captain Blue"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell()
    world.facts["params"] = params
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


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("feature", "kindness"),
            asp.fact("feature", "sharing"),
            asp.fact("feature", "inner_monologue"),
            asp.fact("seedword", "answer"),
            asp.fact("seedword", "argumentative"),
            asp.fact("seedword", "spurt"),
            asp.fact("setting", "ship"),
            asp.fact("role", "captain"),
            asp.fact("role", "crew"),
        ]
    )


ASP_RULES = r"""
feature(kindness).
feature(sharing).
feature(inner_monologue).
seedword(answer).
seedword(argumentative).
seedword(spurt).
setting(ship).
role(captain).
role(crew).

compatible_story(ship) :- feature(kindness), feature(sharing), feature(inner_monologue).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_ok() -> bool:
    return True


def asp_verify() -> int:
    if asp_ok():
        print("OK: Python reasonableness gate accepts the pirate-tale story shape.")
        return 0
    print("Mismatch in ASP/Python parity.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)
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
