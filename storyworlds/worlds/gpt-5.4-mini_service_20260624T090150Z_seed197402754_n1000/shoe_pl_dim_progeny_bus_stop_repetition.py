#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero tale at a bus stop.

Premise:
- A young hero and their progeny wait at a bus stop.
- A small mystery appears: the hero's shoe-pl-dim device keeps blinking dimly.
- The hero uses repetition, teamwork, and careful observation to solve the mystery.
- The ending proves the bus stop is calm again and the progeny feels proud.

This world is intentionally small and classical: one setting, one hero,
one child, one mystery, one fix.
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


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the bus stop"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    clue: str
    cause: str
    solved_by: str
    repeated_phrase: str
    needs_teamwork: bool = True


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    child_name: str
    child_type: str
    sidekick_name: str
    sidekick_type: str
    mystery: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting(place="the bus stop", affords={"wait", "watch", "solve"})

MYSTERIES = {
    "shoe-pl-dim": Mystery(
        id="shoe-pl-dim",
        label="shoe-pl-dim",
        clue="a tiny blinking light near the bench",
        cause="a loose sticker on the shoe-pl-dim panel",
        solved_by="checking the same spot again and again",
        repeated_phrase="look here, look here, look here",
    ),
    "progeny": Mystery(
        id="progeny",
        label="progeny",
        clue="a soft whisper from the back of a cape",
        cause="a folded note tucked into a pocket",
        solved_by="working together and reading the note aloud twice",
        repeated_phrase="we can do it together, together",
    ),
}

HERO_NAMES = ["Nova", "Blaze", "Orbit", "Comet", "Mira", "Torch"]
CHILD_NAMES = ["Pip", "Bean", "Moss", "Luna", "Toby", "Zia"]
SIDEKICK_NAMES = ["Zip", "Nim", "Spark", "Quill", "Dash", "Echo"]


# ---------------------------------------------------------------------------
# World model helpers
# ---------------------------------------------------------------------------
def _repetition(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["focus"] = hero.memes.get("focus", 0) + 1
    world.say(
        f'{hero.id} took a steady breath and said, "{mystery.repeated_phrase}." '
        f"Each repeat made the clue feel less slippery."
    )


def _teamwork(world: World, hero: Entity, child: Entity, sidekick: Entity, mystery: Mystery) -> None:
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    child.memes["pride"] = child.memes.get("pride", 0) + 1
    sidekick.memes["helpful"] = sidekick.memes.get("helpful", 0) + 1
    world.say(
        f"{child.id} held the flashlight while {sidekick.id} peered under the bench. "
        f"{hero.id} listened to both of them, and the three of them formed a small hero team."
    )
    world.say(
        f"Together they found that the mystery was {mystery.cause}."
    )


def _solve(world: World, hero: Entity, child: Entity, mystery: Mystery) -> None:
    hero.meters["mystery_solved"] = 1
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    world.say(
        f"{hero.id} lifted the sticker away, and the dim light turned bright at once. "
        f"{mystery.solved_by.capitalize()} worked."
    )
    world.say(
        f"{child.id} smiled because the bus stop felt safe and bright again, and the next bus could arrive in peace."
    )


def tell(params: StoryParams) -> World:
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    mystery = MYSTERIES[params.mystery]
    world = World(SETTING)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label="hero",
        phrase="superhero",
    ))
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        label="child",
    ))
    sidekick = world.add(Entity(
        id=params.sidekick_name,
        kind="character",
        type=params.sidekick_type,
        label="sidekick",
    ))

    world.facts.update(hero=hero, child=child, sidekick=sidekick, mystery=mystery)

    # Act 1: setup
    world.say(
        f"At {world.setting.place}, {hero.id} waited with {child.id} and {sidekick.id}. "
        f"Under the bench sat {mystery.label}, blinking dimly like a tiny secret."
    )
    world.say(
        f"{child.id} asked what the little glow meant, and {hero.id} promised to solve the mystery."
    )

    # Act 2: repeated attempts and teamwork
    world.para()
    _repetition(world, hero, mystery)
    world.say(
        f"But the dim light blinked the same way again, so {hero.id} repeated the plan more carefully."
    )
    _repetition(world, hero, mystery)
    world.say(
        f"The clue still stayed quiet, so {hero.id} knew this was not a solo job."
    )
    _teamwork(world, hero, child, sidekick, mystery)

    # Act 3: resolution
    world.para()
    _solve(world, hero, child, mystery)
    world.say(
        f"By the time the bus rounded the corner, {hero.id}, {child.id}, and {sidekick.id} were standing together, "
        f"ready for the ride with the mystery solved."
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    child: Entity = f["child"]
    mystery: Mystery = f["mystery"]
    return [
        f'Write a short superhero story set at a bus stop about {hero.id} and {child.id} solving the "{mystery.id}" mystery.',
        f"Tell a child-friendly adventure where repetition helps {hero.id} notice the clue and teamwork helps solve it.",
        f'Write a simple story at {world.setting.place} where a dim little device named "{mystery.label}" leads to a mystery solved by friends.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    child: Entity = f["child"]
    sidekick: Entity = f["sidekick"]
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            question=f"Where did {hero.id} and the others wait?",
            answer=f"They waited at {world.setting.place}.",
        ),
        QAItem(
            question=f"What was the mystery called?",
            answer=f"The mystery was called {mystery.label}.",
        ),
        QAItem(
            question=f"What helped {hero.id} solve the problem?",
            answer=f"{hero.id} used repetition, and then {child.id} and {sidekick.id} helped with teamwork.",
        ),
        QAItem(
            question=f"Why did the bus stop feel better at the end?",
            answer=f"It felt better because the dim clue was solved and the light turned bright again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other to do something together.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition is doing or saying something again and again.",
        ),
        QAItem(
            question="What is a bus stop for?",
            answer="A bus stop is a place where people wait for a bus.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
child(C) :- child_name(C).
sidekick(S) :- sidekick_name(S).
mystery(M) :- mystery_name(M).

needs_teamwork("shoe-pl-dim").
needs_teamwork("progeny").

solved(M) :- mystery_name(M), clue_found(M), teamwork_used(M).
clue_found(M) :- mystery_name(M), repeated_observation(M).
teamwork_used(M) :- mystery_name(M), helped_by_friend(M).

valid_story(H,C,S,M) :- hero(H), child(C), sidekick(S), mystery(M), solved(M).
#show valid_story/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("hero_name", "Nova"),
        asp.fact("child_name", "Pip"),
        asp.fact("sidekick_name", "Zip"),
    ]
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery_name", mid))
    lines.append(asp.fact("clue_found", "shoe-pl-dim"))
    lines.append(asp.fact("repeated_observation", "shoe-pl-dim"))
    lines.append(asp.fact("helped_by_friend", "shoe-pl-dim"))
    lines.append(asp.fact("clue_found", "progeny"))
    lines.append(asp.fact("repeated_observation", "progeny"))
    lines.append(asp.fact("helped_by_friend", "progeny"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    if atoms:
        print(f"OK: ASP produced {len(atoms)} valid_story atom(s).")
        return 0
    print("MISMATCH: ASP produced no valid stories.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld at a bus stop.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--sidekick-name", choices=SIDEKICK_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick-type", choices=["girl", "boy"])
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
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
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    sidekick_name = args.sidekick_name or rng.choice(SIDEKICK_NAMES)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    child_type = args.child_type or rng.choice(["girl", "boy"])
    sidekick_type = args.sidekick_type or rng.choice(["girl", "boy"])
    if len({hero_name, child_name, sidekick_name}) < 3:
        raise StoryError("Choose three different names for the hero, child, and sidekick.")
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        child_name=child_name,
        child_type=child_type,
        sidekick_name=sidekick_name,
        sidekick_type=sidekick_type,
        mystery=mystery,
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
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} valid stories")
        for atom in atoms:
            print(atom)
        return

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("Nova", "girl", "Pip", "boy", "Zip", "girl", "shoe-pl-dim"),
            StoryParams("Blaze", "boy", "Luna", "girl", "Spark", "boy", "progeny"),
            StoryParams("Mira", "girl", "Toby", "boy", "Echo", "girl", "shoe-pl-dim"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
