#!/usr/bin/env python3
"""
A small bedtime-story world set in a storm drain, with humor and a brief
flashback. A child or small creature wants to use a laser toy near a hidden
yam in the drain, learns a gentle lesson, and ends with a cozy resolution.
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


@dataclass
class StoryParams:
    name: str
    companion: str
    prize: str
    setting: str = "storm drain"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.flashback_used = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.name] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


NAMES = ["Milo", "Pia", "Nora", "Otto", "Luna", "Ivy", "Finn", "June"]
COMPANIONS = ["mouse", "cat", "sparrow", "puppy", "frog"]
PRIZES = ["yam", "sweet yam", "tiny yam", "golden yam"]

SETTINGS = {
    "storm drain": {
        "place_fact": "storm_drain",
        "has_water": True,
        "echo": True,
        "safe_end": True,
    }
}

ASP_RULES = r"""
#show valid/1.
#show story_ok/1.

valid(P) :- params(P), setting(P, storm_drain), prize(P, yam), companion(P, _).

story_ok(P) :- valid(P), humored(P), flashback(P), resolved(P).
"""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime Story world: a humorous flashback in a storm drain.")
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--prize", choices=PRIZES)
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
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    prize = args.prize or rng.choice(PRIZES)
    if "yam" not in prize:
        raise StoryError("This world only tells stories about a yam in the storm drain.")
    return StoryParams(name=name, companion=companion, prize=prize)


def aspire() -> str:
    import asp
    facts = [
        asp.fact("setting", "p1", "storm_drain"),
        asp.fact("prize", "p1", "yam"),
        asp.fact("companion", "p1", "mouse"),
        asp.fact("params", "p1"),
        asp.fact("humored", "p1"),
        asp.fact("flashback", "p1"),
        asp.fact("resolved", "p1"),
        asp.fact("valid", "p1"),
        asp.fact("story_ok", "p1"),
    ]
    return "\n".join(facts) + "\n" + ASP_RULES


def asp_facts() -> str:
    import asp
    lines = []
    for _name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", "p1", setting["place_fact"]))
    lines.append(asp.fact("prize", "p1", "yam"))
    for c in COMPANIONS:
        lines.append(asp.fact("companion", "p1", c))
    lines.append(asp.fact("params", "p1"))
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    program = asp_facts() + "\n" + ASP_RULES
    model = asp.one_model(program)
    valid_atoms = set(asp.atoms(model, "valid"))
    story_ok_atoms = set(asp.atoms(model, "story_ok"))
    if ("p1",) in valid_atoms and ("p1",) in story_ok_atoms:
        print("OK: ASP rules produce a valid bedtime story.")
        return 0
    print("Mismatch: ASP rules did not accept the sample story.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    child = world.add(Entity(name=params.name, kind="character", label=params.name))
    companion = world.add(Entity(name=params.companion, kind="creature", label=f"the {params.companion}"))
    yam = world.add(Entity(name="yam", kind="object", label=params.prize))

    child.memes["curious"] = 1.0
    child.memes["humor"] = 1.0
    yam.meters["hidden"] = 1.0
    world.facts["setting"] = "storm drain"
    world.facts["humored"] = True
    world.facts["flashback"] = True
    world.facts["resolved"] = True

    world.say(f"On a sleepy night, {params.name} tiptoed beside the storm drain, where water sang softly under the street.")
    world.say(f"A {params.companion} peeped from a grate and made {params.name} { 'chuckle' } at the echo, because even the rain seemed to giggle there.")
    world.say(f"Down below, something round and brown waited in the dim water: a little {params.prize}. {params.name} was surprised, then delighted, as if the drain had hidden a bedtime snack for the moon.")
    world.say(f"{params.name} reached for a toy { 'laser' }, but the bright dot skittered on the wet stone and bumped into a memory.")
    world.say(f"In a small flashback, {params.name} remembered earlier that day, when the same laser had scared away the {params.companion} and made everyone feel too busy to laugh.")
    world.say(f"So {params.name} turned the toy off, smiled at the {params.companion}, and used the flashlight instead, which was much kinder and much quieter.")
    world.say(f"Together they carried the {params.prize} home, and the storm drain fell still again, humming like a cradle. {params.name} chuckled one last time and went to bed with a warm, gentle heart.")

    world.facts.update(
        child=child,
        companion=companion,
        yam=yam,
    )
    story_qa = [
        QAItem(
            question=f"What did {params.name} find in the storm drain?",
            answer=f"{params.name} found a little {params.prize} hidden in the storm drain water.",
        ),
        QAItem(
            question=f"Why did {params.name} chuckle near the drain?",
            answer=f"{params.name} chuckled because the water echoed back and the {params.companion} made the moment feel funny.",
        ),
        QAItem(
            question=f"What did {params.name} remember in the flashback?",
            answer=f"{params.name} remembered that the toy laser had once frightened the {params.companion} and made the moment feel less gentle.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a storm drain?",
            answer="A storm drain is a street opening that helps rainwater flow away so puddles do not stay everywhere.",
        ),
        QAItem(
            question="Why can a laser dot be playful?",
            answer="A laser dot can be playful because it moves quickly and can make a pet or child want to chase it.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a short part of the story that shows something that happened earlier.",
        ),
        QAItem(
            question="Why can humor help at bedtime?",
            answer="Humor can help at bedtime because a small laugh can make a child feel calm and safe before sleep.",
        ),
    ]
    prompts = [
        'Write a gentle bedtime story about a child, a storm drain, and a hidden yam.',
        f'Write a cozy story where {params.name} hears a funny echo in a storm drain and remembers an earlier moment with a laser.',
        'Tell a child-friendly story with humor, a flashback, and a calm ending image.',
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.name}: kind={e.kind}, meters={e.meters}, memes={e.memes}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(aspire())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_facts() + "\n" + ASP_RULES)
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Milo", companion="mouse", prize="yam"),
            StoryParams(name="Luna", companion="frog", prize="tiny yam"),
            StoryParams(name="Pia", companion="cat", prize="sweet yam"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
