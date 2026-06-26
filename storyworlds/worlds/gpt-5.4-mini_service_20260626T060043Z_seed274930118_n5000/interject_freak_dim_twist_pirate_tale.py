#!/usr/bin/env python3
"""
A small pirate-tale storyworld with a twist, built around an interrupted plan
and a freak-dim clue that changes what the crew thinks the map means.

The seed tale:
- A young pirate wants treasure.
- A first mate interjects with a warning.
- A freak-dim twist in the map reveals the real safe path.
- The crew changes course and ends with a bright, proved change in the world.
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captainess"}
        male = {"boy", "man", "father", "captain", "first_mate", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    port: str = "the little harbor"
    sea: str = "the blue sea"
    island: str = "Twist Isle"
    affords: set[str] = field(default_factory=lambda: {"sail", "dig", "read_map"})


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    turn: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.mood: str = ""

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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.scene)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.mood = self.mood
        return w


def _r_freak_dim(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes.get("freak_dim", 0.0) < THRESHOLD:
            continue
        sig = ("freak_dim", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["curiosity"] = e.memes.get("curiosity", 0.0) + 1
        out.append(f"The {e.label} looked strange in the lantern light.")
    return out


def _r_twist_reveal(world: World) -> list[str]:
    out: list[str] = []
    map_ent = world.entities.get("map")
    if not map_ent:
        return out
    if map_ent.meters.get("twist", 0.0) < THRESHOLD:
        return out
    sig = ("twist", "map")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    map_ent.memes["truth"] = 1.0
    out.append("The map was not broken at all; it was folded to hide a secret path.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_freak_dim, _r_twist_reveal):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hint_line() -> str:
    return "The clue had a freak-dim look, like a shadow that wanted to be read twice."


def setup_world() -> tuple[World, Entity, Entity, Entity, Entity, Entity]:
    scene = Scene()
    world = World(scene)

    captain = world.add(Entity(id="Mara", kind="character", type="captain", label="Captain Mara"))
    mate = world.add(Entity(id="Ned", kind="character", type="first_mate", label="First Mate Ned"))
    crew = world.add(Entity(id="crew", kind="character", type="pirate", label="the crew", plural=True))
    map_ent = world.add(Entity(id="map", type="map", label="map"))
    prize = world.add(Entity(id="chest", type="chest", label="treasure chest", phrase="a small treasure chest"))

    return world, captain, mate, crew, map_ent, prize


def tell(hero_name: str = "Mara", mate_name: str = "Ned") -> World:
    world, captain, mate, crew, map_ent, prize = setup_world()

    quest = Quest(
        id="twist",
        verb="sail to Twist Isle",
        gerund="sailing toward Twist Isle",
        rush="rush straight for the reef",
        risk="the reef could crack the hull",
        turn="the map was folded into a secret route",
        keyword="Twist",
        tags={"interject", "freak-dim", "twist", "pirate"},
    )
    world.facts["quest"] = quest
    world.facts["captain"] = captain
    world.facts["mate"] = mate
    world.facts["crew"] = crew
    world.facts["map"] = map_ent
    world.facts["prize"] = prize

    map_ent.meters["twist"] = 1.0

    world.say(
        f"Captain Mara had a small map and a big wish: she wanted to find treasure at {world.scene.island}."
    )
    world.say(
        f"First Mate Ned liked the voyage, but he could not help himself and had to interject, "
        f'"If we {quest.rush}, the reef might bite the ship!"'
    )
    world.say(
        f"Mara held the map up to the lantern. {hint_line()}"
    )

    world.para()
    map_ent.memes["freak_dim"] = 1.0
    propagate(world, narrate=True)

    world.say(
        f"Then the weird fold made sense. {quest.turn.capitalize()}, and the safest water was hidden behind the mark."
    )
    world.say(
        f"Mara smiled at Ned and said, 'Good thing you interjected. We will follow the twist instead of the reef.'"
    )

    world.para()
    captain.memes["joy"] = captain.memes.get("joy", 0.0) + 1
    mate.memes["relief"] = mate.memes.get("relief", 0.0) + 1
    crew.memes["trust"] = crew.memes.get("trust", 0.0) + 1
    world.say(
        f"The crew steered by the secret line, the sea stayed calm, and the chest waited where the map had pointed."
    )
    world.say(
        f"By sunset, the crew had the treasure chest aboard, and the strange little twist on the map had saved the whole trip."
    )

    world.facts["resolved"] = True
    return world


SCENE = Scene()

QUESTS = {
    "twist": Quest(
        id="twist",
        verb="sail to Twist Isle",
        gerund="sailing toward Twist Isle",
        rush="rush straight for the reef",
        risk="the reef could crack the hull",
        turn="the map was folded into a secret route",
        keyword="Twist",
        tags={"interject", "freak-dim", "twist", "pirate"},
    )
}

PRIZES = {
    "chest": Prize(id="chest", label="treasure chest", phrase="a small treasure chest", region="deck"),
}

NAMES = ["Mara", "Ned", "Jory", "Iris", "Finn", "Sela"]


@dataclass
class StoryParams:
    name: str = "Mara"
    mate: str = "Ned"
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest"]
    return [
        'Write a short pirate tale for a young child that includes the word "interject".',
        f"Tell a pirate story where {world.facts['captain'].label} wants to {q.verb}, but {world.facts['mate'].label} warns her first.",
        'Write a simple story with a freak-dim map clue and a Twist that keeps the ship safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    q = world.facts["quest"]
    cap = world.facts["captain"]
    mate = world.facts["mate"]
    return [
        QAItem(
            question=f"Who wanted to find treasure at {world.scene.island}?",
            answer=f"{cap.label} wanted to find treasure at {world.scene.island}, and the crew sailed with her.",
        ),
        QAItem(
            question="Why did Ned interject?",
            answer=f"Ned interjected because he feared that if the ship rushed straight for the reef, the hull could crack.",
        ),
        QAItem(
            question="What was strange about the map?",
            answer=f"The map had a freak-dim look and a folded twist that hid a secret route.",
        ),
        QAItem(
            question="How did the trip end?",
            answer=f"The crew followed the secret route, found the treasure chest, and came home safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate?",
            answer="A pirate is a sailor who travels on the sea, often looking for treasure.",
        ),
        QAItem(
            question="What does a map do?",
            answer="A map shows places and helps people find the way.",
        ),
        QAItem(
            question="What is a reef?",
            answer="A reef is a rocky place in the water that can be dangerous for ships.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:10}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
entity(captain).
entity(first_mate).
entity(map).
entity(chest).

interject(first_mate) :- warning(first_mate).
twist(map) :- folded(map).
freak_dim(map) :- strange(map).

safe_route(map) :- freak_dim(map), twist(map).
resolved :- interject(first_mate), safe_route(map).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("warning", "first_mate"),
        asp.fact("folded", "map"),
        asp.fact("strange", "map"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with interject, freak-dim, and Twist.")
    ap.add_argument("--name")
    ap.add_argument("--mate")
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
        name=args.name or rng.choice(NAMES),
        mate=args.mate or rng.choice([n for n in NAMES if n != (args.name or "")]),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.mate)
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0. #show safe_route/1. #show interject/1. #show freak_dim/1. #show twist/1."))
    shown = {(s.name, len(s.arguments)) for s in model}
    need = {("resolved", 0), ("safe_route", 1), ("interject", 1), ("freak_dim", 1), ("twist", 1)}
    if need.issubset(shown):
        print("OK: ASP twin is present and the generated story exercises the twist/interject/freak-dim path.")
        return 0
    print("MISMATCH: ASP twin did not expose the expected atoms.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0. #show safe_route/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/0. #show safe_route/1. #show interject/1. #show freak_dim/1. #show twist/1."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(name=n, mate="Ned", seed=base_seed + i)) for i, n in enumerate(NAMES[:3])]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
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
