#!/usr/bin/env python3
"""
Space-adventure storyworld: a small crew, a tiny quest, a lesson learned.

Premise:
- A curious child crew member finds a thing-dim gadget that can shrink one
  object down to a delight-sized helper.
- A mission goes funny when an important tool becomes too small for the job.
- The crew must use a careful quest through a little station to restore the
  tool and learn that cleverness beats rushing.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

CREW_NAMES = ["Nova", "Milo", "Zuri", "Ada", "Rex", "Lina", "Jett", "Pip"]
ROLE_NAMES = ["captain", "pilot", "mechanic", "navigator", "scout"]
SHIP_NAMES = ["Starling", "Comet", "Aurora", "Pebble", "Orbit", "Sunbeam"]
PLACE_NAMES = ["the small starport", "the moon dock", "the bright corridor", "the cargo bay"]
OBJECT_NAMES = ["laser wrench", "map chip", "repair key", "signal lens", "glow battery"]
CREATURE_NAMES = ["a sleepy moon mouse", "a shuttle beetle", "a tiny robot crab", "a cloud puff"]
LESSONS = [
    "slow hands make fewer mistakes",
    "small helpers can still do big jobs",
    "it is wise to check a gadget before using it",
]

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

@dataclass
class StoryParams:
    crew: str
    role: str
    ship: str
    place: str
    object: str
    creature: str
    seed: Optional[int] = None

@dataclass
class World:
    crew: Entity
    object: Entity
    creature: Entity
    ship: Entity
    place: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with a thing-dim quest and lesson learned.")
    ap.add_argument("--crew", choices=CREW_NAMES)
    ap.add_argument("--role", choices=ROLE_NAMES)
    ap.add_argument("--ship", choices=SHIP_NAMES)
    ap.add_argument("--place", choices=PLACE_NAMES)
    ap.add_argument("--object", dest="object_name", choices=OBJECT_NAMES)
    ap.add_argument("--creature", choices=CREATURE_NAMES)
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
    crew = args.crew or rng.choice(CREW_NAMES)
    role = args.role or rng.choice(ROLE_NAMES)
    ship = args.ship or rng.choice(SHIP_NAMES)
    place = args.place or rng.choice(PLACE_NAMES)
    obj = args.object_name or rng.choice(OBJECT_NAMES)
    creature = args.creature or rng.choice(CREATURE_NAMES)
    return StoryParams(crew=crew, role=role, ship=ship, place=place, object=obj, creature=creature)

def _make_world(params: StoryParams) -> World:
    crew = Entity(id=params.crew, kind="character", type=params.role, label=params.role)
    obj = Entity(id=params.object, type="tool", label=params.object, phrase=f"a {params.object}")
    creature = Entity(id=params.creature, type="creature", label=params.creature)
    ship = Entity(id=params.ship, type="ship", label=params.ship)
    return World(crew=crew, object=obj, creature=creature, ship=ship, place=params.place)

def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    crew = world.crew
    obj = world.object
    creature = world.creature
    ship = world.ship

    crew.memes["curious"] = 1
    crew.memes["delight"] = 1

    world.say(f"{crew.id} was the {crew.label} on the ship {ship.label}, and {crew.pronoun('subject')} loved a delight-sized surprise.")
    world.say(f"One day at {world.place}, {crew.id} found a thing-dim gadget tucked under a panel beside {obj.phrase}.")
    world.say(f"{crew.id} giggled at the shiny button and pressed it, because {crew.pronoun('subject')} wanted to see what thing-dim could do.")

    world.para()
    obj.meters["size"] = 0.2
    crew.memes["surprise"] = 1
    world.say(f"The gadget made the {obj.label} shrink down until it was too tiny to help fix the ship.")
    world.say(f"That was a problem, because a small {creature.label} had slipped into the control nook and the ship needed the tool right away.")
    crew.memes["quest"] = 1

    world.para()
    world.say(f"So {crew.id} began a careful quest through {world.place}, following little blue lights and listening for the soft beep of the lost tool.")
    world.say(f"{crew.pronoun('subject').capitalize()} crawled past crates, checked a vent, and finally found the tiny {obj.label} riding on {creature.label}'s back like a joke.")
    world.say(f"{crew.id} laughed, gently pressed the gadget again, and made the {obj.label} return to its proper size.")

    world.para()
    crew.memes["lesson"] = 1
    world.say(f"With the tool back to normal, the ship hummed again and the crew finished the repair.")
    world.say(f"{crew.id} smiled and learned a lesson learned: {LESSONS[0]}; {LESSONS[1]}.")
    world.say(f"After that, the thing-dim gadget stayed in its box, and the crew kept the {obj.label} ready for the next space adventure.")

    world.facts.update(
        crew=crew,
        obj=obj,
        creature=creature,
        ship=ship,
        place=world.place,
        lesson=LESSONS[0],
    )

    story_qa = [
        QAItem(
            question=f"What did {crew.id} find at {world.place}?",
            answer=f"{crew.id} found a thing-dim gadget tucked near {obj.phrase}.",
        ),
        QAItem(
            question=f"Why was the tiny {obj.label} a problem?",
            answer=f"It was too small to help fix the ship, so the crew could not finish the repair until it was made big again.",
        ),
        QAItem(
            question=f"What lesson learned did {crew.id} get at the end?",
            answer=f"{crew.id} learned that {LESSONS[0]}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does thing-dim mean in this story?",
            answer="Thing-dim is a made-up gadget power that makes an object smaller for a moment.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission to find something important or solve a problem.",
        ),
        QAItem(
            question="Why can delight be a good feeling?",
            answer="Delight is a happy, bright feeling that makes a hard job feel fun for a while.",
        ),
    ]
    prompts = [
        f"Write a short space adventure about {crew.id}, a {crew.label}, and a thing-dim gadget.",
        f"Tell a child-friendly quest story where {crew.id} uses a tiny tool, then learns a lesson learned.",
        f"Make a funny ship repair story with delight, a creature, and a surprising gadget mistake.",
    ]
    story = world.render()
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)

ASP_RULES = r"""
crew(C) :- crew_name(C).
tool(O) :- object_name(O).
place(P) :- place_name(P).

tiny_object(O) :- dimmed(O).
problem(C,O) :- tiny_object(O), needs_fix(O), crew(C).
quest(C) :- problem(C,_).
lesson(C) :- quest(C), solved(C).

#show quest/1.
#show lesson/1.
#show problem/2.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for n in CREW_NAMES:
        lines.append(asp.fact("crew_name", n))
    for n in OBJECT_NAMES:
        lines.append(asp.fact("object_name", n))
    for n in PLACE_NAMES:
        lines.append(asp.fact("place_name", n))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    program = asp_program("#show quest/1.\n#show lesson/1.")
    model = asp.one_model(program)
    qs = set(asp.atoms(model, "quest"))
    ls = set(asp.atoms(model, "lesson"))
    if qs == set() and ls == set():
        print("OK: ASP twin loads, but this world's narrative gates are Python-driven.")
        return 0
    print("MISMATCH: unexpected ASP output.")
    return 1

def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in [world.crew, world.object, world.creature, world.ship]:
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
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

CURATED = [
    StoryParams(crew="Nova", role="mechanic", ship="Starling", place="the cargo bay", object="laser wrench", creature="a tiny robot crab"),
    StoryParams(crew="Milo", role="pilot", ship="Comet", place="the moon dock", object="map chip", creature="a sleepy moon mouse"),
    StoryParams(crew="Zuri", role="scout", ship="Aurora", place="the bright corridor", object="signal lens", creature="a shuttle beetle"),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show quest/1.\n#show lesson/1.\n#show problem/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this world is primarily driven by the Python simulation.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
