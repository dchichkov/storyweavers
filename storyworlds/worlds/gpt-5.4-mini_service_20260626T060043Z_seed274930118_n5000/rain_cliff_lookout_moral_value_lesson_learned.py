#!/usr/bin/env python3
"""
A tiny detective-style story world set at a cliff lookout in the rain.

Premise:
- A lookout keeper finds a missing kite at the cliff lookout during a rainy
  afternoon.
- The investigation reveals that a friend had moved the kite to keep it dry.
- The hero learns a moral value: trust friends, ask before assuming, and help
  keep shared things safe.

The world uses meters for physical state and memes for emotional state.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    with_: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "mother"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "father"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the cliff lookout"
    weather: str = "rainy"
    afford: set[str] = field(default_factory=lambda: {"search", "walk", "hide"})


@dataclass
class StoryParams:
    place: str
    case: str
    clue: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


CLUES = {
    "footprints": "small wet footprints",
    "rope": "a damp rope knot",
    "umbrella": "a blue umbrella",
    "shell": "a shiny shell",
}

MORALS = [
    "ask before you blame a friend",
    "share the work when something goes missing",
    "trust careful help when the weather turns rough",
]

LESSONS = [
    "looking closely can solve a mystery faster than guessing",
    "a kind friend may be hiding a good surprise, not a bad secret",
    "when rain comes, safe hands and patient hearts matter most",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: rain at a cliff lookout.")
    ap.add_argument("--place", choices=["cliff lookout"], default="cliff lookout")
    ap.add_argument("--case", choices=list(CLUES), default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    case = args.case or rng.choice(list(CLUES))
    hero_name = rng.choice(["Milo", "Nia", "Tessa", "Arun", "Lena"])
    friend_name = rng.choice([n for n in ["Pip", "June", "Orla", "Ben", "Mira"] if n != hero_name])
    return StoryParams(
        place="cliff lookout",
        case=case,
        clue=CLUES[case],
        hero_name=hero_name,
        friend_name=friend_name,
    )


def generate(params: StoryParams) -> StorySample:
    setting = Setting()
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type="girl", label=params.hero_name))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="boy", label=params.friend_name))
    kite = world.add(Entity(
        id="kite",
        kind="thing",
        type="kite",
        label="kite",
        owner=hero.id,
        caretaker=hero.id,
        meters={"dry": 1.0},
    ))

    hero.memes["worry"] = 1.0
    friend.memes["care"] = 1.0
    kite.meters["missing"] = 1.0

    world.say(
        f"At the cliff lookout, rain tapped the stones like tiny fingers, and {hero.id} frowned at the empty kite string."
    )
    world.say(
        f'"My kite is gone," {hero.id} said. "This looks like a case for a careful detective."'
    )

    world.para()
    world.say(
        f"{hero.id} knelt by the wet ground and found {params.clue} near the railing."
    )
    world.say(
        f"{hero.id} followed the clue to a sheltered bench, where {friend.id} sat holding the kite under a coat."
    )
    friend.meters["hidden"] = 1.0
    friend.memes["nervous"] = 1.0

    world.para()
    world.say(
        f'"I did not steal it," {friend.id} said quickly. "I moved it so the rain would not spoil it."'
    )
    hero.memes["worry"] = 0.0
    hero.memes["trust"] = 1.0
    friend.memes["relief"] = 1.0
    kite.meters["missing"] = 0.0
    kite.meters["dry"] = 1.0
    kite.with_ = hero.id

    moral = MORALS[0 if params.case in {"footprints", "rope"} else 1]
    lesson = LESSONS[2 if params.case == "umbrella" else 0]

    world.para()
    world.say(
        f"{hero.id} smiled and thanked {friend.id}. The mystery was solved: the kite was safe, the rain could keep falling, and the two friends carried it back to the lookout together."
    )
    world.say(
        f"The moral value was clear: {moral}. The lesson learned was simple: {lesson}."
    )
    world.say(
        f"By the end, {hero.id} and {friend.id} were laughing under the gray sky, and the kite fluttered high again beside the cliff lookout."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        kite=kite,
        moral=moral,
        lesson=lesson,
        clue=params.clue,
        case=params.case,
        setting=setting,
    )

    prompts = [
        'Write a short detective story for a child set at a cliff lookout in the rain.',
        f'Write a mystery about {hero.id} and a missing kite, with friendship and a moral value.',
        'Tell a gentle story where a clue leads to a friend who was trying to help.',
    ]

    story_qa = [
        QAItem(
            question=f"What was missing at the cliff lookout?",
            answer=f"{hero.id}'s kite was missing at first, so {hero.id} had to investigate carefully.",
        ),
        QAItem(
            question=f"Who really had the kite?",
            answer=f"{friend.id} had the kite and was keeping it dry under a coat.",
        ),
        QAItem(
            question=f"What did {hero.id} learn from the mystery?",
            answer=f"{hero.id} learned to trust a friend, ask before blaming, and look closely at clues.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is rain?",
            answer="Rain is water that falls from clouds and can make stones and paths wet.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind relationship where people help, care, and trust each other.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good rule for how to act, like being honest, kind, or fair.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is an idea someone understands after an event, like why patience or trust matters.",
        ),
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
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


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "cliff_lookout"),
        asp.fact("weather", "rain"),
        asp.fact("feature", "moral_value"),
        asp.fact("feature", "lesson_learned"),
        asp.fact("feature", "friendship"),
    ])


ASP_RULES = r"""
#show compatible/1.
compatible(cliff_lookout).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show compatible/1."))
        ok = bool(asp.atoms(model, "compatible"))
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    if ok:
        print("OK: ASP twin is available.")
        return 0
    print("ASP verification failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible setting: cliff lookout")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for case in CLUES:
            params = StoryParams(place="cliff lookout", case=case, clue=CLUES[case], hero_name="Milo", friend_name="Pip")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
