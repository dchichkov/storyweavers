#!/usr/bin/env python3
"""
A small Storyweavers world: a bedroom space adventure with a curious child,
a cockatoo, a little pulp mess, and a flashback that turns the problem into a
solution.
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

ROOMS = {"bedroom": "the bedroom"}
ACTIONS = {
    "orbit": {
        "verb": "build a pillow rocket",
        "doing": "building a pillow rocket",
        "mess": "pulp",
        "soil": "sticky pulp",
        "risk": "the blanket",
        "place_detail": "Beside the bed, a blanket fort looked like a tiny moon base.",
    },
    "signal": {
        "verb": "send a tiny space signal",
        "doing": "sending tiny space signals",
        "mess": "pulp",
        "soil": "sticky pulp",
        "risk": "the floor",
        "place_detail": "On the rug, a toy telescope pointed toward the corner like a watchful star.",
    },
}
COCKATOO_NAMES = ["Pip", "Nova", "Mango", "Comet"]
CHILD_NAMES = ["Luna", "Milo", "Iris", "Theo"]
TRAITS = ["curious", "brave", "careful", "bright"]

ASP_RULES = r"""
room(bedroom).
feature(curious).
feature(flashback).

character(child).
character(cockatoo).

risk(action_orbit, blanket).
risk(action_signal, floor).

mess(action_orbit, pulp).
mess(action_signal, pulp).

allows(room, action_orbit).
allows(room, action_signal).

compatible(Action) :- allows(bedroom, Action), mess(Action, pulp), risk(Action, _).
"""

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    perched_on: Optional[str] = None
    carried_by: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "child":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type == "cockatoo":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

@dataclass
class StoryParams:
    room: str = "bedroom"
    child: str = "Luna"
    bird: str = "Pip"
    trait: str = "curious"
    action: str = "orbit"
    seed: Optional[int] = None

class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("room", "bedroom"),
        asp.fact("feature", "curious"),
        asp.fact("feature", "flashback"),
        asp.fact("character", "child"),
        asp.fact("character", "cockatoo"),
    ]
    for act in ACTIONS:
        lines.append(asp.fact("risk", f"action_{act}", ACTIONS[act]["risk"]))
        lines.append(asp.fact("mess", f"action_{act}", ACTIONS[act]["mess"]))
        lines.append(asp.fact("allows", "bedroom", f"action_{act}"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedroom space adventure with curiosity and flashback.")
    ap.add_argument("--room", choices=ROOMS, default="bedroom")
    ap.add_argument("--action", choices=ACTIONS, default=None)
    ap.add_argument("--child")
    ap.add_argument("--bird")
    ap.add_argument("--trait", choices=TRAITS)
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
    action = args.action or rng.choice(list(ACTIONS))
    trait = args.trait or rng.choice(TRAITS)
    child = args.child or rng.choice(CHILD_NAMES)
    bird = args.bird or rng.choice(COCKATOO_NAMES)
    return StoryParams(room="bedroom", child=child, bird=bird, trait=trait, action=action)

def _flashback(world: World, child: Entity, bird: Entity, action: str) -> None:
    child.memes["flashback"] = 1
    bird.memes["memory"] = 1
    world.say(
        f"Then {child.id} had a flashback to yesterday, when {bird.id} had spilled "
        f"fruit pulp across the toys but used a cloth to wipe it away."
    )

def generate(params: StoryParams) -> StorySample:
    if params.room != "bedroom":
        raise StoryError("This world only supports the bedroom setting.")
    if params.action not in ACTIONS:
        raise StoryError("Unknown action.")
    data = ACTIONS[params.action]
    world = World()
    child = world.add(Entity(id=params.child, kind="character", label=params.child, type="child"))
    bird = world.add(Entity(id=params.bird, kind="character", label=params.bird, type="cockatoo"))
    bird.perched_on = "headboard"
    child.memes["curiosity"] = 1
    world.say(
        f"In the bedroom, {child.id} was feeling {params.trait} and curious, like a little astronaut "
        f"planning a launch from the bed."
    )
    world.say(
        f"{bird.id} the cockatoo hopped on the headboard and peered at the shiny bits near the lamp."
    )
    world.say(
        f"{child.id} wanted to {data['verb']} because the room looked like a tiny ship drifting through space."
    )
    world.say(data["place_detail"])
    world.say(
        f"But the fruit bowl had tipped, and pale {data['mess']} had smeared onto {bird.id}'s rump."
    )
    child.meters["curiosity"] = 1
    bird.meters["pulp"] = 1
    child.memes["worry"] = 1
    _flashback(world, child, bird, params.action)
    world.para()
    world.say(
        f"{child.id} remembered the cloth, gently wiped {bird.id}'s rump, and tucked the bowl higher."
    )
    world.say(
        f"With the mess gone, the bedroom felt calm again, and the pillow rocket lifted off in play."
    )
    world.say(
        f"{bird.id} flapped once, and the two friends watched their quiet little spaceship world glow."
    )
    world.facts = {"child": child, "bird": bird, "params": params, "action": data}
    story_qa = [
        QAItem(
            question=f"Where does the story happen?",
            answer="It happens in the bedroom, where the bed and toys become part of a little space adventure.",
        ),
        QAItem(
            question=f"What was {params.child} feeling at the start?",
            answer=f"{params.child} was feeling {params.trait} and curious, ready to explore like a tiny astronaut.",
        ),
        QAItem(
            question=f"What problem did {params.bird} have?",
            answer=f"{params.bird} had pale pulp smeared on {params.bird.lower()}'s rump, so the bird needed help cleaning up.",
        ),
        QAItem(
            question=f"What helped fix the trouble?",
            answer="A flashback reminded the child to use a cloth, so the mess could be wiped away before play continued.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a cockatoo?",
            answer="A cockatoo is a kind of parrot with a bright crest and a noisy, lively way of moving.",
        ),
        QAItem(
            question="What is pulp?",
            answer="Pulp is soft fruit flesh or mashed fruit pieces, and it can be sticky and messy.",
        ),
        QAItem(
            question="What does rump mean?",
            answer="A rump is the back part of an animal's body, like its rear end.",
        ),
    ]
    prompts = [
        'Write a short space-adventure story set in a bedroom with a curious child and a cockatoo.',
        f'Include the words "{params.child}", "cockatoo", "pulp", and "rump", and end with a calm fix.',
        "Tell a child-friendly story where a flashback helps solve a small messy problem.",
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        for section, items in [("Story Q&A", sample.story_qa), ("World Q&A", sample.world_qa)]:
            print(section)
            for item in items:
                print(f"Q: {item.question}")
                print(f"A: {item.answer}")

def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/1."))
    return sorted(set(asp.atoms(model, "compatible")))

def asp_verify() -> int:
    python_set = {(f"action_{k}",) for k in ACTIONS}
    clingo_set = set(asp_valid())
    return 0 if python_set == clingo_set else 1

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid())))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for idx, action in enumerate(ACTIONS):
            params = StoryParams(action=action, seed=base_seed + idx)
            samples.append(generate(params))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
