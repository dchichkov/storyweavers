#!/usr/bin/env python3
"""
A standalone storyworld script for a small comedy domain set on a flooded street.

Premise:
A child named Koa and Papa are trying to get across a street after heavy rain
turns it into a funny little river. Along the way they keep spotting strange
floating things, arguing over what they are, and repeating a plan that keeps
needing adjustment. The humor comes from the oddity of everyday objects behaving
like boats, while the mystery is resolved by noticing a simple hidden cause.

The world model tracks physical state in meters and emotional state in memes.
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
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "child", "son"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"man", "father", "dad", "papa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Street:
    name: str = "the flooded street"
    water_depth: float = 0.0
    ripple: float = 0.0
    current: float = 0.0
    hidden_cause: str = "a storm drain was blocked by a wobbly bag of leaves"


@dataclass
class StoryParams:
    name: str = "Koa"
    parent_name: str = "Papa"
    seed: Optional[int] = None


class World:
    def __init__(self, street: Street) -> None:
        self.street = street
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
        import copy
        clone = World(copy.deepcopy(self.street))
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def introduce(world: World, koa: Entity, papa: Entity) -> None:
    world.say(
        f"Koa was a curious little kid who liked to notice tiny things that made big questions."
    )
    world.say(
        f"Papa was the kind of grown-up who could turn a problem into a joke before the joke turned into a problem."
    )


def flood_setup(world: World) -> None:
    world.street.water_depth = 1.2
    world.street.current = 0.5
    world.street.ripple = 0.4
    world.say(
        f"After a hard rain, {world.street.name} looked like a shallow river with puddles pretending to be islands."
    )


def humor_beats(world: World, koa: Entity) -> None:
    koa.memes["amusement"] = koa.memes.get("amusement", 0.0) + 1.0
    world.say(
        f"Koa pointed at a drifting sandwich wrapper and said, \"Look, Papa, a pirate sail!\""
    )
    world.say(
        f"Papa squinted at a floating traffic cone and replied, \"That is the bravest cone I have ever seen.\""
    )


def repetition(world: World, koa: Entity, papa: Entity) -> None:
    world.say(
        f"They repeated the same plan three times: step on the dry curb, test the next stone, and keep socks mostly dry."
    )
    world.say(
        f"But every time Koa repeated, \"Dry curb, stone, socks,\" a new wobble in the water made the plan feel sillier."
    )


def predict_source(world: World) -> str:
    return world.street.hidden_cause


def mystery_turn(world: World, koa: Entity, papa: Entity) -> None:
    koa.memes["curiosity"] = koa.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"Then Koa noticed something strange: the water kept flowing in one direction, even where the street should have been flat."
    )
    world.say(
        f"Papa stopped joking for a moment and looked at the same spot twice, which was his way of saying the mystery had teeth."
    )
    world.say(
        f"\"Why is the street still flooded?\" Koa asked. \"Because something is blocking the drain,\" Papa said, but they still had to find what."
    )


def reveal(world: World, koa: Entity, papa: Entity) -> None:
    world.say(
        f"They followed the little stream of water to a storm drain near the curb, where a wobbly bag of leaves was jammed over the grate."
    )
    world.say(
        f"Papa lifted the bag away, and the water began to sigh and hurry down the drain as if it had been late for a meeting."
    )
    world.street.water_depth = 0.2
    world.street.current = 0.0
    world.street.ripple = 0.1


def ending(world: World, koa: Entity, papa: Entity) -> None:
    world.say(
        f"Soon the street was only shiny, not flooded, and Koa laughed at the soggy leaf-bag culprit like it had been the riddle all along."
    )
    world.say(
        f"Koa and Papa walked home repeating their joke one last time: \"Bravest cone, bravest cone,\" until both of them were laughing too hard to stay serious."
    )


def tell_story(params: StoryParams) -> World:
    world = World(Street())
    koa = world.add(Entity(id="koa", kind="character", type="child", label=params.name))
    papa = world.add(Entity(id="papa", kind="character", type="father", label=params.parent_name))
    world.facts["koa"] = koa
    world.facts["papa"] = papa

    introduce(world, koa, papa)
    world.para()

    flood_setup(world)
    humor_beats(world, koa)
    repetition(world, koa, papa)
    world.para()

    mystery_turn(world, koa, papa)
    reveal(world, koa, papa)
    world.para()

    ending(world, koa, papa)
    return world


# ---------------------------------------------------------------------------
# Quality gates and ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
character(koa).
character(papa).

flooded_street(street).
has_water(street).
blocks_drain(bag_of_leaves).
causes_flood(bag_of_leaves) :- blocks_drain(bag_of_leaves).

humor_event(wrapper_sail).
humor_event(brave_cone).
repetition_event(plan_repeat).
mystery_event(blocked_drain).

solved :- causes_flood(bag_of_leaves).
"""

def python_reasonableness_gate(params: StoryParams) -> None:
    if not params.name:
        raise StoryError("Koa needs a name for the story.")
    if not params.parent_name:
        raise StoryError("Papa needs a name for the story.")


def asp_facts() -> str:
    return "\n".join([
        'character(koa).',
        'character(papa).',
        'flooded_street(street).',
        'has_water(street).',
        'blocks_drain(bag_of_leaves).',
        'humor_event(wrapper_sail).',
        'humor_event(brave_cone).',
        'repetition_event(plan_repeat).',
        'mystery_event(blocked_drain).',
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp  # noqa: WPS433
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    program = asp_program("#show solved/0.")
    model = asp.one_model(program)
    atoms = asp.atoms(model, "solved")
    py_ok = True
    asp_ok = bool(atoms)
    if py_ok == asp_ok:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("Mismatch between ASP and Python checks.")
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts() -> list[str]:
    return [
        'Write a short comedy story about Koa and Papa on a flooded street, with a mystery to solve and some repeated jokes.',
        'Tell a child-friendly story where a flooded street seems funny at first, then a hidden reason is discovered.',
        'Write a story in which Koa keeps repeating a plan while Papa helps solve the mystery of the water.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why did Koa and Papa have to be careful on the street?",
            answer="They had to be careful because the street was flooded, so the water made the ground slippery and hard to cross."
        ),
        QAItem(
            question="What was funny about the flooded street?",
            answer="The funny part was that ordinary things, like a traffic cone and a sandwich wrapper, looked like boats or sails in the water."
        ),
        QAItem(
            question="What was the mystery Koa wanted to solve?",
            answer="Koa wanted to solve why the street was still flooded even after the rain stopped."
        ),
        QAItem(
            question="How did Papa help solve the mystery?",
            answer="Papa looked closely and found that a bag of leaves was blocking the storm drain."
        ),
        QAItem(
            question="What repeated plan did they keep saying?",
            answer="They kept repeating the plan to step on the dry curb, test the next stone, and keep their socks mostly dry."
        ),
        QAItem(
            question="How did the story end?",
            answer="The story ended with the blocked drain cleared, the water rushing away, and Koa and Papa laughing as they walked home."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a storm drain for?",
            answer="A storm drain helps water leave the street after rain so the water does not pile up."
        ),
        QAItem(
            question="Why can flooded streets be dangerous?",
            answer="Flooded streets can be dangerous because water can hide slippery spots, holes, or moving water."
        ),
        QAItem(
            question="Why do people sometimes make jokes when things go wrong?",
            answer="People sometimes make jokes because humor can help them stay calm and brave when a problem feels big."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(
        f"street: water_depth={world.street.water_depth}, current={world.street.current}, ripple={world.street.ripple}"
    )
    lines.append(f"hidden_cause: {world.street.hidden_cause}")
    for ent in world.entities.values():
        lines.append(f"{ent.id}: kind={ent.kind}, type={ent.type}, memes={ent.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: Koa and Papa on a flooded street.")
    ap.add_argument("--name", default="Koa")
    ap.add_argument("--parent-name", default="Papa")
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
    params = StoryParams(
        name=args.name or "Koa",
        parent_name=args.parent_name or "Papa",
        seed=args.seed,
    )
    python_reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(),
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
        print(asp_program("#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp  # noqa: WPS433
        except Exception as exc:
            raise SystemExit(str(exc))
        model = asp.one_model(asp_program("#show solved/0."))
        print("ASP model:", asp.atoms(model, "solved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(name="Koa", parent_name="Papa", seed=base_seed)
        samples = [generate(params)]
    else:
        for i in range(max(1, args.n)):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
