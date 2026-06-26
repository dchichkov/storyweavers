#!/usr/bin/env python3
"""
friend_inner_monologue_comedy.py
================================

A small story world about a friend, a very loud inner monologue, and a
comedic misunderstanding that turns out fine.

Premise:
- A child wants to help a friend with a tiny problem.
- The child overthinks every step in an inner monologue.
- The comedy comes from the mismatch between what the child thinks and what
  actually happens.
- The ending proves the friendship got warmer, not cooler.

This script is standalone and uses the shared Storyweavers result containers.
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
    kind: str = "person"
    label: str = ""
    type: str = "child"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the playground"
    mood: str = "bright"


@dataclass
class Task:
    id: str
    verb: str
    tiny_problem: str
    misunderstanding: str
    fix: str
    punchline: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    task: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "playground": Setting(place="the playground", mood="sunny"),
    "kitchen": Setting(place="the kitchen", mood="busy"),
    "library": Setting(place="the library", mood="quiet"),
}

TASKS = {
    "kite": Task(
        id="kite",
        verb="fly a kite",
        tiny_problem="the string is tangled",
        misunderstanding="the child imagines the kite is about to file a formal complaint",
        fix="carefully untangle the string",
        punchline="the kite only wanted to go up, not quit its job",
        tags={"string", "wind", "toy"},
    ),
    "cookie": Task(
        id="cookie",
        verb="bake cookies",
        tiny_problem="the bowl is missing the spoon",
        misunderstanding="the child acts like the spoon has vanished into a dramatic mystery",
        fix="find a spoon in the drawer",
        punchline="the spoon was in the drawer the whole time, being extremely unhelpful by hiding there",
        tags={"food", "spoon", "baking"},
    ),
    "blocks": Task(
        id="blocks",
        verb="build a tower",
        tiny_problem="one block keeps wobbling",
        misunderstanding="the child thinks the tower is practicing a secret dance routine",
        fix="move the bottom block to make it steady",
        punchline="the tower was not dancing; it was simply losing balance with commitment",
        tags={"blocks", "tower", "balance"},
    ),
}

HERO_NAMES = ["Maya", "Noah", "Lina", "Eli", "Zoe", "Iris", "Owen", "Tess"]
FRIEND_NAMES = ["Pip", "Juno", "Milo", "Rae", "Nina", "Bea", "Otis", "June"]
TRAITS = ["careful", "curious", "silly", "nervous", "brave", "chatty"]


def inner_monologue(hero: Entity, task: Task) -> str:
    mood = {
        "kite": [
            "Okay, stay calm. Tangled string is not a catastrophe. Probably.",
            "Maybe the kite is thinking about its feelings. Maybe I should not mention that out loud.",
        ],
        "cookie": [
            "No spoon? That is suspicious. This is how legends begin.",
            "What if the spoon ran away because it did not want to become cookie dough?",
        ],
        "blocks": [
            "The tower is wobbling on purpose. I knew it. It wants attention.",
            "If I breathe too loudly, will the blocks stage a rebellion?",
        ],
    }
    return random.choice(mood[task.id])


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.hero_name, kind="person", type=params.hero_type, traits=[params.trait]))
    friend = world.add(Entity(id=params.friend_name, kind="person", type=params.friend_type, traits=["friendly"]))
    task = TASKS[params.task]
    world.facts.update(hero=hero, friend=friend, task=task)
    return world


def act(world: World, params: StoryParams) -> None:
    hero = world.entities[params.hero_name]
    friend = world.entities[params.friend_name]
    task = TASKS[params.task]

    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1

    world.say(f"At {world.setting.place}, {hero.id} wanted to {task.verb} with {friend.id}.")
    world.say(f"{friend.id} had a tiny problem: {task.tiny_problem}.")
    world.say(f"In {hero.id}'s head, the inner voice said, “{inner_monologue(hero, task)}”")
    world.say(f"Then {hero.id} got extra serious and thought {task.misunderstanding}.")

    hero.memes["embarrassment"] = hero.memes.get("embarrassment", 0.0) + 1
    world.say(
        f"But instead of making a big fuss, {hero.id} did the simple thing and chose to {task.fix}."
    )

    friend.memes["relief"] = friend.memes.get("relief", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1

    world.say(
        f"{friend.id} grinned, because the fix worked, and {task.punchline}."
    )
    world.say(
        f"{hero.id} laughed at the whole mix-up, and the two friends kept going, "
        f"now with less drama and more giggles."
    )


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    task = world.facts["task"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, who spent the day with {friend.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with {friend.id}?",
            answer=f"{hero.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"What was the tiny problem?",
            answer=f"The tiny problem was that {task.tiny_problem}.",
        ),
        QAItem(
            question=f"How did {hero.id} solve it?",
            answer=f"{hero.id} solved it by choosing to {task.fix}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {friend.id} laughing together and feeling more like good friends.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice a character hears in their own head when they think to themselves.",
        ),
        QAItem(
            question="Why can a small problem be funny in a comedy story?",
            answer="A small problem can be funny when someone reacts too dramatically, then the simple fix turns out to be easy.",
        ),
        QAItem(
            question="What does a friend do in a story?",
            answer="A friend helps, listens, or shares an activity, and being kind can make the whole scene feel warmer.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    task = world.facts["task"]
    return [
        f"Write a funny short story about {hero.id} and {friend.id} who try to {task.verb}.",
        f"Tell a comedy story where {hero.id} has an exaggerated inner monologue about {task.tiny_problem}.",
        "Write a child-friendly story with a friend, a tiny mishap, and a simple fix that ends in laughter.",
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: friend + inner monologue comedy.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, t) for s in SETTINGS for t in TASKS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.task:
        if (args.setting, args.task) not in combos:
            raise StoryError("That setting and task do not fit together.")
    valid = [c for c in combos if (not args.setting or c[0] == args.setting) and (not args.task or c[1] == args.task)]
    if not valid:
        raise StoryError("No valid combination matches the chosen options.")

    setting, task = rng.choice(valid)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    if hero_name == friend_name:
        friend_name = rng.choice([n for n in FRIEND_NAMES if n != friend_name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        task=task,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    act(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(out)


ASP_RULES = r"""
valid(setting,task) :- setting(setting), task(task).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a}, {b}" for a, b in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for setting in SETTINGS:
            for task in TASKS:
                params = StoryParams(
                    setting=setting,
                    task=task,
                    hero_name=random.choice(HERO_NAMES),
                    hero_type="girl",
                    friend_name=random.choice(FRIEND_NAMES),
                    friend_type="boy",
                    trait="curious",
                    seed=base_seed,
                )
                samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
