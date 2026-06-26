#!/usr/bin/env python3
"""
storyworlds/worlds/monster_stack_dialogue_friendship_myth.py
=============================================================

A small myth-style story world about a child and a friendly monster building
a stack, speaking carefully, and finding a kinder way to finish the tale.

The premise is simple:
- a monster and a child want to build a stack,
- the stack gets wobbly when they rush,
- dialogue slows them down,
- friendship turns the ending into a proud, steady image.

This script keeps the world model tiny but stateful:
- entities have physical meters and emotional memes,
- spoken dialogue changes meme state,
- stack height and wobble change by actions,
- the ending proves what changed in the physical world.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the old hill"
    indoor: bool = False
    kind: str = "mythic"


@dataclass
class StackKind:
    id: str
    label: str
    material: str
    unit: str
    height_goal: int
    wobble_limit: int
    dangerous_after: int
    can_sing: bool = False


@dataclass
class StoryParams:
    place: str
    stack_kind: str
    hero_name: str
    hero_type: str
    monster_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, stack_kind: StackKind) -> None:
        self.place = place
        self.stack_kind = stack_kind
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def paragraph(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def copy(self) -> "World":
        import copy

        w = World(self.place, self.stack_kind)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world: a child, a monster, a stack, and friendship."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--stack-kind", choices=STACKS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "child"], default="child")
    ap.add_argument("--monster-name")
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


PLACES = {
    "hill": Place(name="the old hill", indoor=False),
    "clearing": Place(name="the moonlit clearing", indoor=False),
    "cave": Place(name="the echoing cave", indoor=True),
}

STACKS = {
    "stones": StackKind(
        id="stones",
        label="stone stack",
        material="stones",
        unit="stone",
        height_goal=5,
        wobble_limit=2,
        dangerous_after=4,
        can_sing=True,
    ),
    "shells": StackKind(
        id="shells",
        label="shell stack",
        material="shells",
        unit="shell",
        height_goal=6,
        wobble_limit=2,
        dangerous_after=5,
        can_sing=False,
    ),
    "logs": StackKind(
        id="logs",
        label="log stack",
        material="logs",
        unit="log",
        height_goal=4,
        wobble_limit=1,
        dangerous_after=3,
        can_sing=False,
    ),
}

HERO_NAMES = ["Mira", "Toma", "Lio", "Nara", "Ari", "Kito", "Sera", "Bren"]
MONSTER_NAMES = ["Grom", "Moro", "Vesh", "Tarn", "Luma", "Brug", "Ivo", "Sola"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    stack_kind = args.stack_kind or rng.choice(list(STACKS))
    hero_type = args.hero_type
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    monster_name = args.monster_name or rng.choice(MONSTER_NAMES)
    return StoryParams(
        place=place,
        stack_kind=stack_kind,
        hero_name=hero_name,
        hero_type=hero_type,
        monster_name=monster_name,
    )


def myth_opening(world: World, hero: Entity, monster: Entity) -> None:
    world.say(
        f"Long ago at {world.place.name}, {hero.id} met {monster.id}, a kind monster with a slow grin."
    )
    world.say(
        f"They had one wish between them: to build a {world.stack_kind.label} that could touch the night."
    )
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    monster.memes["friendship"] = monster.memes.get("friendship", 0.0) + 1


def start_stack(world: World, hero: Entity, monster: Entity) -> None:
    stack = world.add(Entity(id="stack", type=world.stack_kind.id, label=world.stack_kind.label))
    stack.meters["height"] = 1
    stack.meters["wobble"] = 0
    stack.meters["finished"] = 0
    world.say(
        f"{hero.id} set the first {world.stack_kind.unit} down, and {monster.id} laid the next one gently on top."
    )


def add_piece(world: World, actor: Entity, careful: bool = True) -> None:
    stack = world.get("stack")
    stack.meters["height"] += 1
    if careful:
        stack.meters["wobble"] = max(0, stack.meters["wobble"] - 1)
        actor.memes["pride"] = actor.memes.get("pride", 0.0) + 0.5
    else:
        stack.meters["wobble"] += 1
        actor.memes["rush"] = actor.memes.get("rush", 0.0) + 1


def predict_collapse(world: World, extra_wobble: int = 0) -> bool:
    stack = world.get("stack")
    wobble = int(stack.meters.get("wobble", 0)) + extra_wobble
    height = int(stack.meters.get("height", 0))
    return height >= world.stack_kind.dangerous_after and wobble > world.stack_kind.wobble_limit


def dialogue_turn(world: World, speaker: Entity, listener: Entity) -> None:
    stack = world.get("stack")
    if stack.meters["height"] < 3:
        world.say(
            f'"Let us be patient," said {speaker.id}. "A stack grows strong when hands are gentle."'
        )
    else:
        world.say(
            f'"Wait," said {listener.id}. "The top is swaying like a reed in wind."'
        )
    speaker.memes["trust"] = speaker.memes.get("trust", 0.0) + 1
    listener.memes["trust"] = listener.memes.get("trust", 0.0) + 1


def tension(world: World, hero: Entity, monster: Entity) -> None:
    stack = world.get("stack")
    stack.meters["wobble"] += 1
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(
        f"As the {world.stack_kind.label} rose, it began to wobble, and the air itself seemed to hold its breath."
    )
    if predict_collapse(world):
        world.say(
            f'{hero.id} whispered, "If we rush now, the whole wonder may tumble."'
        )
        world.say(
            f'{monster.id} answered, "Then let us speak first and build second."'
        )


def resolve(world: World, hero: Entity, monster: Entity) -> None:
    stack = world.get("stack")
    while stack.meters["height"] < world.stack_kind.height_goal:
        careful = stack.meters["wobble"] <= world.stack_kind.wobble_limit
        add_piece(world, hero if stack.meters["height"] % 2 == 0 else monster, careful=careful)
        if careful:
            world.say(
                f"Together they placed another {world.stack_kind.unit}, and the {world.stack_kind.label} stood a little straighter."
            )
        else:
            world.say(
                f"They slowed their hands and steadied the next {world.stack_kind.unit} before it could slip."
            )
        if stack.meters["wobble"] > world.stack_kind.wobble_limit:
            stack.meters["wobble"] -= 1
    stack.meters["finished"] = 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    monster.memes["joy"] = monster.memes.get("joy", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    monster.memes["friendship"] = monster.memes.get("friendship", 0.0) + 1
    world.say(
        f'At last they stepped back and smiled. "We made it," said {hero.id}, and {monster.id} laughed like thunder far away.'
    )
    world.say(
        f"The {world.stack_kind.label} stood tall on {world.place.name}, steady and bright, because friendship had taught both of them to be careful."
    )


def tell_story(world: World) -> World:
    hero = world.add(Entity(id=world.facts["hero_name"], kind="character", type=world.facts["hero_type"]))
    monster = world.add(Entity(id=world.facts["monster_name"], kind="character", type="monster"))
    world.facts["hero"] = hero
    world.facts["monster"] = monster

    myth_opening(world, hero, monster)
    world.paragraph()
    start_stack(world, hero, monster)
    dialogue_turn(world, hero, monster)
    add_piece(world, monster, careful=True)
    add_piece(world, hero, careful=False)
    tension(world, hero, monster)
    world.paragraph()
    resolve(world, hero, monster)
    return world


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    monster = world.facts["monster"]
    stack = world.get("stack")
    return [
        QAItem(
            question=f"Who built the {world.stack_kind.label} together?",
            answer=f"{hero.id} and {monster.id} built it together, one careful piece at a time.",
        ),
        QAItem(
            question="Why did they slow down near the end?",
            answer=(
                f"They slowed down because the {world.stack_kind.label} began to wobble, "
                f"and they did not want the whole stack to tumble."
            ),
        ),
        QAItem(
            question="What did the ending prove?",
            answer=(
                f"It proved that the {world.stack_kind.label} became steady and tall on {world.place.name}, "
                f"because the two friends listened to each other."
            ),
        ),
        QAItem(
            question=f"How tall did the stack become?",
            answer=f"It reached {int(stack.meters['height'])} pieces high.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    stack = world.stack_kind
    return [
        QAItem(
            question=f"What is a {stack.unit} stack?",
            answer=f"A {stack.unit} stack is a pile made by placing {stack.unit}s one on top of another.",
        ),
        QAItem(
            question="What does friendship help people do?",
            answer="Friendship helps people listen, share, and work together without giving up when something gets tricky.",
        ),
        QAItem(
            question="Why are careful hands important when building?",
            answer="Careful hands keep a stack from wobbling too much, so the pieces do not fall.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a myth-style story about a child and a monster building a {world.stack_kind.label} together.",
        f"Tell a short story where dialogue helps {world.facts['hero_name']} and {world.facts['monster_name']} save a wobbling stack.",
        f"Write a gentle friendship myth ending with a tall {world.stack_kind.label} standing safely at {world.place.name}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story_params() -> list[tuple[str, str]]:
    return [(p, s) for p in PLACES for s in STACKS]


ASP_RULES = r"""
place(P) :- setting(P).
stack_kind(S) :- stack(S).

can_build(P,S) :- setting(P), stack(S).
myth_story(P,S) :- can_build(P,S), friendship(S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for sid in STACKS:
        lines.append(asp.fact("stack", sid))
    lines.append(asp.fact("friendship", "yes"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show can_build/2."))
    return sorted(set(asp.atoms(model, "can_build")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_story_params())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_story_params() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python combos:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def explain_rejection(_: str, __: str) -> str:
    return "(No story: invalid combination.)"


CURATED = [
    StoryParams(place="hill", stack_kind="stones", hero_name="Mira", hero_type="child", monster_name="Grom"),
    StoryParams(place="clearing", stack_kind="shells", hero_name="Ari", hero_type="child", monster_name="Luma"),
    StoryParams(place="cave", stack_kind="logs", hero_name="Toma", hero_type="child", monster_name="Vesh"),
]


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place], STACKS[params.stack_kind])
    world.facts.update(
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        monster_name=params.monster_name,
        place=params.place,
        stack_kind=params.stack_kind,
    )
    tell_story(world)
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
        print(asp_program("#show can_build/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show can_build/2."))
        combos = sorted(set(asp.atoms(model, "can_build")))
        print(f"{len(combos)} compatible combos:\n")
        for place, stk in combos:
            print(f"  {place:10} {stk}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.stack_kind} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
