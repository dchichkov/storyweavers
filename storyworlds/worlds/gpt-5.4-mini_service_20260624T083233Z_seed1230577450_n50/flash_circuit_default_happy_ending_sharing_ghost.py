#!/usr/bin/env python3
"""
A tiny ghost-story world about a lost flash, a broken circuit, and a kind
sharing fix that leads to a happy ending.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wears: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "mother", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "father", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old attic"


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    problem: str
    fix: str
    tag: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    object_: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


OBJECTS = {
    "flash": ObjectCfg(
        label="flashlight",
        phrase="a little flashlight with a yellow button",
        problem="went dark",
        fix="shared the light",
        tag="flash",
    ),
    "circuit": ObjectCfg(
        label="toy circuit",
        phrase="a toy circuit board with bright wires",
        problem="stopped sparking",
        fix="reconnected the pieces",
        tag="circuit",
    ),
    "default": ObjectCfg(
        label="default lantern",
        phrase="a default lantern from the shelf",
        problem="faded",
        fix="passed it around",
        tag="default",
    ),
}

PLACES = {
    "attic": Setting("the old attic"),
    "hall": Setting("the quiet hall"),
    "basement": Setting("the basement stairs"),
}

NAMES = ["Mia", "Noah", "Lena", "Theo", "Ava", "Finn"]
TRAITS = ["curious", "gentle", "brave", "patient", "kind"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with a sharing happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["ghost", "friend", "sibling"])
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
    place = args.place or rng.choice(list(PLACES))
    obj = args.object_ or rng.choice(list(OBJECTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(["ghost", "friend", "sibling"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, object_=obj, name=name, gender=gender, helper=helper, trait=trait)


def _do_problem(world: World, child: Entity, obj: Entity, cfg: ObjectCfg) -> None:
    if ("problem", obj.id) in world.fired:
        return
    world.fired.add(("problem", obj.id))
    obj.meters["broken"] = 1
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(f"Then the {obj.label} {cfg.problem} in the dark, and {child.id} felt a tiny shiver.")


def _share_fix(world: World, child: Entity, helper: Entity, obj: Entity, cfg: ObjectCfg) -> None:
    if ("fix", obj.id) in world.fired:
        return
    world.fired.add(("fix", obj.id))
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    helper.memes["care"] = helper.memes.get("care", 0) + 1
    obj.meters["fixed"] = 1
    world.say(
        f"{helper.id} showed {child.id} how to {cfg.fix}, and they decided to share the glow."
    )
    world.say(
        f"After that, the room felt warm again. The little {obj.label} shone softly, "
        f"and {child.id} smiled beside the friendly ghost."
    )


def tell(setting: Setting, cfg: ObjectCfg, params: StoryParams) -> World:
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="Ghost", kind="character", type=params.helper, label="the ghost"))
    obj = world.add(Entity(id="obj", type=cfg.label, label=cfg.label, phrase=cfg.phrase, owner=child.id, plural=cfg.plural))

    world.say(
        f"On a quiet night in {setting.place}, little {child.id} walked with a brave heart and a curious gaze."
    )
    world.say(
        f"{child.id} carried {cfg.phrase}, because the strange little {obj.label} was their favorite light."
    )
    world.para()
    world.say(
        f"Inside the shadows, a soft ghost waited near a wall, and the room's old circuit hummed a sleepy hum."
    )
    _do_problem(world, child, obj, cfg)
    world.say(
        f"{child.id} did not run away. Instead, {child.pronoun().capitalize()} looked at {helper.label} and asked for help."
    )
    world.para()
    _share_fix(world, child, helper, obj, cfg)
    world.facts.update(child=child, helper=helper, obj=obj, cfg=cfg, setting=setting, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a young child that includes the word "{f["cfg"].tag}".',
        f"Tell a gentle story where {f['child'].id} meets a friendly ghost in {f['setting'].place} and they share a light.",
        f"Write a happy-ending story about a {f['cfg'].label} that goes dark and then becomes useful again by sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c: Entity = f["child"]
    o: Entity = f["obj"]
    cfg: ObjectCfg = f["cfg"]
    return [
        QAItem(
            question=f"Who is the story about in {f['setting'].place}?",
            answer=f"It is about {c.id}, a {f['params'].trait']} {c.type} who meets a friendly ghost.",
        ),
        QAItem(
            question=f"What happened to the {o.label} in the dark?",
            answer=f"The {o.label} {cfg.problem}, which made {c.id} a little worried.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{f['helper'].id if isinstance(f['helper'], Entity) else 'The ghost'} helped {c.id} {cfg.fix}, and they shared the light for a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a flashlight for?", answer="A flashlight gives light in dark places."),
        QAItem(question="What is a circuit?", answer="A circuit is a path that lets electricity move and power things."),
        QAItem(question="Why is sharing nice?", answer="Sharing is nice because it helps everyone enjoy the same thing together."),
        QAItem(question="What is a ghost story?", answer="A ghost story is a tale about a spooky or friendly ghost, often told at night."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
object_kind(flash). object_kind(circuit). object_kind(default).
happy_ending(O) :- object_kind(O).
sharing_fix(O) :- object_kind(O).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("object_kind", k) for k in OBJECTS])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    setting = PLACES[params.place]
    cfg = OBJECTS[params.object_]
    world = tell(setting, cfg, params)
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
        print("--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show happy_ending/1. #show sharing_fix/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams("attic", "flash", "Mia", "girl", "ghost", "curious"),
            StoryParams("hall", "circuit", "Noah", "boy", "friend", "gentle"),
            StoryParams("basement", "default", "Ava", "girl", "sibling", "kind"),
        ]
        samples = [generate(p) for p in combos]
    else:
        for _ in range(args.n):
            p = resolve_params(args, rng)
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
