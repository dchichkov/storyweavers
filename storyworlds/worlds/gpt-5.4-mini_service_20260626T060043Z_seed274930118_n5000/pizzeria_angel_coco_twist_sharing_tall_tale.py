#!/usr/bin/env python3
"""
Tall-tale storyworld: a pizzeria, an angel, and a coco twist about sharing.

A small, constraint-checked story domain inspired by a classic tall-tale shape:
someone wants something big, one thing gets tangled, a twist changes the plan,
and sharing turns the ending warm.

The world is intentionally narrow:
- The child wants to make or deliver a special pizza.
- A radiant helper angel can only help with a compatible twist.
- Coco is a beloved sweet topping or drink mix that can go wrong if hoarded.
- Sharing is the resolution that makes the pizzeria feel generous again.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the pizzeria"
    sparkle: str = "golden"
    affords: set[str] = field(default_factory=lambda: {"twist", "sharing"})


@dataclass
class StoryThing:
    label: str
    phrase: str
    region: str
    mess: str
    kind: str = "thing"
    plural: bool = False


@dataclass
class StoryAction:
    id: str
    verb: str
    gerund: str
    rush: str
    turn: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "pizzeria": Setting(place="the pizzeria", sparkle="bright", affords={"twist", "sharing"}),
    "corner": Setting(place="the little corner pizzeria", sparkle="warm", affords={"twist", "sharing"}),
    "kitchen": Setting(place="the back kitchen", sparkle="busy", affords={"twist", "sharing"}),
}

ACTIONS = {
    "twist": StoryAction(
        id="twist",
        verb="twist the dough into a giant round crust",
        gerund="twisting the dough into a giant round crust",
        rush="spin the dough faster and faster",
        turn="a sky-high twist",
        keyword="twist",
        tags={"twist"},
    ),
    "sharing": StoryAction(
        id="sharing",
        verb="share the coco topping with everybody",
        gerund="sharing coco with everybody",
        rush="hoard the coco bowl",
        turn="a sharing twist",
        keyword="sharing",
        tags={"sharing"},
    ),
}

PRIZES = {
    "coco": StoryThing(
        label="coco",
        phrase="a bowl of sweet coco dust",
        region="table",
        mess="sticky",
        kind="thing",
        plural=False,
    ),
    "cocoa_cup": StoryThing(
        label="coco cup",
        phrase="a frothy coco cup with a cinnamon cap",
        region="hands",
        mess="sticky",
        kind="thing",
        plural=False,
    ),
    "coco_sprinkles": StoryThing(
        label="coco sprinkles",
        phrase="a jar of coco sprinkles",
        region="table",
        mess="sticky",
        kind="thing",
        plural=False,
    ),
}

GIRL_NAMES = ["Coco", "Mina", "Lia", "Tia", "Rosa", "Nina"]
BOY_NAMES = ["Tom", "Leo", "Milo", "Finn", "Omar", "Jude"]
TRAITS = ["brave", "bright", "curious", "bouncy", "bold"]


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def action_needs_sharing(action: StoryAction, prize: StoryThing) -> bool:
    return action.id == "sharing" or prize.label.startswith("coco")


def valid_combo(place: str, action: str, prize: str) -> bool:
    return place in SETTINGS and action in ACTIONS and prize in PRIZES


def explain_rejection(action: StoryAction, prize: StoryThing) -> str:
    return (
        f"(No story: this tall tale needs a twist or a sharing beat, and the "
        f"{prize.label} must matter in the pizzeria. Try a coco-related prize "
        f"or a sharing action.)"
    )


# ---------------------------------------------------------------------------
# Story beats
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"Down at {world.setting.place}, there lived a little {hero.type} with a {hero.label} smile, "
        f"and {hero.pronoun('possessive')} name was {hero.id}."
    )


def setup_love(world: World, hero: Entity, action: StoryAction, prize: Entity) -> None:
    world.say(
        f"{hero.id} loved {action.gerund}, because every swirl of flour felt like a parade "
        f"and every smell from the ovens felt like a song."
    )
    world.say(
        f"Most of all, {hero.id} loved {prize.phrase}, which gleamed on the counter like treasure."
    )


def arrive(world: World, hero: Entity, parent: Entity) -> None:
    world.para()
    world.say(
        f"One busy afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}."
    )
    world.say(
        f"The room was full of warm light, and the pizza pans shone like little moons."
    )


def desire(world: World, hero: Entity, action: StoryAction) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(
        f"{hero.id} wanted to {action.verb}, but the dough was stubborn and kept springing back."
    )


def twist(world: World, hero: Entity, action: StoryAction) -> None:
    hero.memes["determination"] = hero.memes.get("determination", 0) + 1
    hero.meters["flour"] = hero.meters.get("flour", 0) + 1
    world.say(
        f"Then {hero.id} gave the dough {action.turn}, and the crust curled up tall as a town hall tower."
    )


def problem(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["greed"] = hero.memes.get("greed", 0) + 1
    prize.meters["sticky"] = prize.meters.get("sticky", 0) + 1
    world.say(
        f"But when the {prize.label} bowl landed near the edge of the counter, {hero.id} tried to keep it all close."
    )


def angel_help(world: World, angel: Entity, hero: Entity, action: StoryAction, prize: Entity) -> None:
    world.say(
        f"Up fluttered {angel.id}, an angel with a grin as wide as a crescent moon."
    )
    world.say(
        f'{angel.id} said, "A tall twist is good, but a bigger heart is better. '
        f"Why not {action.verb if action.id == 'sharing' else 'save some coco and share it'}?"'
    )
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1


def share(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    hero.memes["sharing"] = hero.memes.get("sharing", 0) + 1
    hero.memes["greed"] = 0
    prize.meters["shared"] = prize.meters.get("shared", 0) + 1
    world.say(
        f"{hero.id} opened {hero.pronoun('possessive')} hands and shared the {prize.label} with the cooks, the customers, and {hero.pronoun('possessive')} {parent.label}."
    )
    world.say(
        f"Everyone laughed, and the sweet coco smell floated through the pizzeria like a happy flag."
    )


def ending(world: World, hero: Entity, action: StoryAction, prize: Entity) -> None:
    world.para()
    world.say(
        f"By sunset, the crust was tall, the {prize.label} was shared, and {hero.id} stood smiling beside the oven."
    )
    world.say(
        f"In that little pizzeria, the biggest thing of all was how much room there was for everybody."
    )


# ---------------------------------------------------------------------------
# World builder
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if not valid_combo(params.place, params.action, params.prize):
        raise StoryError("(No valid combination matches the given options.)")
    action = ACTIONS[params.action]
    prize_cfg = PRIZES[params.prize]
    if not action_needs_sharing(action, prize_cfg):
        raise StoryError(explain_rejection(action, prize_cfg))

    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.trait))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    angel = world.add(Entity(id="Angel", kind="character", type="angel", label="angel"))
    prize = world.add(Entity(id=prize_cfg.label, label=prize_cfg.label, type="topping", plural=False, owner=hero.id))
    world.facts.update(hero=hero, parent=parent, angel=angel, prize=prize, action=action, prize_cfg=prize_cfg)
    return world


def tell(world: World) -> World:
    f = world.facts
    hero, parent, angel, prize, action = f["hero"], f["parent"], f["angel"], f["prize"], f["action"]

    introduce(world, hero)
    setup_love(world, hero, action, prize)
    arrive(world, hero, parent)
    desire(world, hero, action)
    twist(world, hero, action)
    problem(world, hero, prize)
    angel_help(world, angel, hero, action, prize)
    share(world, hero, parent, prize)
    ending(world, hero, action, prize)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, action, prize = f["hero"], f["action"], f["prize_cfg"]
    return [
        f'Write a tall-tale style story for a young child about a pizzeria, an angel, and {prize.label}.',
        f"Tell a playful story where {hero.id} needs a twist at {world.setting.place} and learns to share {prize.phrase}.",
        f'Write a story that includes the words "pizzeria," "angel," and "coco," and ends with sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, angel, prize, action = f["hero"], f["parent"], f["angel"], f["prize"], f["action"]
    return [
        QAItem(
            question=f"Where did {hero.id} go with {hero.pronoun('possessive')} {parent.label}?",
            answer=f"{hero.id} went to {world.setting.place} with {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the angel spoke up?",
            answer=f"{hero.id} wanted to {action.verb}.",
        ),
        QAItem(
            question=f"What did the angel help {hero.id} learn?",
            answer=f"The angel helped {hero.id} learn to share the {prize.label} instead of keeping it all close.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The crust got its tall twist, the coco was shared, and the pizzeria felt warm and generous.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pizzeria?",
            answer="A pizzeria is a place where people make and eat pizza.",
        ),
        QAItem(
            question="What is an angel in stories?",
            answer="In stories, an angel is a gentle helper who can bring hope and good advice.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people have some of what you have, too.",
        ),
        QAItem(
            question="What is coco?",
            answer="Coco is a sweet chocolate flavor people often put in drinks or treats.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(pizzeria).
place(corner).
place(kitchen).

action(twist).
action(sharing).

prize(coco).
prize(cocoa_cup).
prize(coco_sprinkles).

compatible(P, A, R) :- place(P), action(A), prize(R).
needs_sharing(coco).
needs_sharing(cocoa_cup).
needs_sharing(coco_sprinkles).

valid_story(P, A, R) :- compatible(P, A, R), needs_sharing(R).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, a, r) for p in SETTINGS for a in ACTIONS for r in PRIZES if action_needs_sharing(ACTIONS[a], PRIZES[r])}
    clingo_set = set(asp_valid())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: pizzeria, angel, coco, twist, sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"], default=None)
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    action = args.action or rng.choice(list(ACTIONS))
    prize = args.prize or rng.choice(list(PRIZES))
    if not valid_combo(place, action, prize):
        raise StoryError("(No valid combination matches the given options.)")
    if not action_needs_sharing(ACTIONS[action], PRIZES[prize]):
        raise StoryError(explain_rejection(ACTIONS[action], PRIZES[prize]))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prize=prize, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for action in ACTIONS:
                for prize in PRIZES:
                    if not action_needs_sharing(ACTIONS[action], PRIZES[prize]):
                        continue
                    params = StoryParams(place=place, action=action, prize=prize, name="Coco", parent="mother", trait="bright")
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
