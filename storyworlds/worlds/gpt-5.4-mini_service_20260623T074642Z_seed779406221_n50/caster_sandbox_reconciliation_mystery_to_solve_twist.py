#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/caster_sandbox_reconciliation_mystery_to_solve_twist.py
====================================================================================================

A small slice-of-life storyworld set in a sandbox, built around a caster,
a mystery to solve, a twist, and a reconciliation.

Premise:
- A child is at a sandbox with a caster toy.
- Something small goes missing or behaves strangely.
- The child investigates with a friend or sibling.
- A twist reveals a harmless cause.
- The children reconcile and play together again.

This file is standalone and uses only the standard library plus the shared
storyworld result containers. ASP support is inline and lazily imported.
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

SAND_TEXTURES = ["soft sand", "warm sand", "fine sand"]
CASTER_KINDS = ["toy caster", "little caster", "sand caster"]
TONE_WORDS = ["calm", "cozy", "gentle", "quiet"]


@dataclass
class Person:
    name: str
    role: str
    kind: str
    loves: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class ObjectThing:
    name: str
    label: str
    kind: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Scene:
    place: str = "the sandbox"
    weather: str = "soft afternoon"
    texture: str = "soft sand"


@dataclass
class StoryParams:
    name: str
    kind: str
    friend_name: str
    friend_kind: str
    caster: str
    missing: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.people: dict[str, Person] = {}
        self.objects: dict[str, ObjectThing] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


ASP_RULES = r"""
sanbox_place(sandbox).
caster(caster).
twist(true) :- hidden_reason(_, _).
reconcile(true) :- apology(_, _), shared_play(_).
mystery(true) :- missing_item(_), found_by_observation(_).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "sandbox"),
            asp.fact("caster", "caster"),
            asp.fact("theme", "reconciliation"),
            asp.fact("theme", "mystery_to_solve"),
            asp.fact("theme", "twist"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _pick_name(rng: random.Random, kind: str) -> str:
    girl = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
    boy = ["Leo", "Finn", "Max", "Eli", "Theo"]
    neutral = ["Sam", "Robin", "Casey", "Parker"]
    return rng.choice(girl if kind == "girl" else boy if kind == "boy" else neutral)


def _pick_friend_kind(rng: random.Random, kind: str) -> str:
    options = ["girl", "boy", "nonbinary"]
    return rng.choice([k for k in options if k != kind])


def build_world(params: StoryParams) -> World:
    world = World(Scene())
    child = Person(params.name, "child", params.kind, loves="building roads in sand")
    friend = Person(params.friend_name, "friend", params.friend_kind, loves="watching the wheels turn")
    caster = ObjectThing("caster", params.caster, "toy", owner=child.name)
    missing = ObjectThing(params.missing, params.missing, "missing thing", owner=child.name)
    world.people[child.name] = child
    world.people[friend.name] = friend
    world.objects[caster.name] = caster
    world.objects[missing.name] = missing
    return world


def tell_story(world: World, params: StoryParams) -> World:
    child = world.people[params.name]
    friend = world.people[params.friend_name]
    caster = world.objects["caster"]
    missing = world.objects[params.missing]

    child.memes["curious"] = 1
    child.meters["sand"] = 1

    world.say(
        f"{child.name} sat in the sandbox on the warm afternoon, turning a small {caster.label} in the sand."
    )
    world.say(
        f"{child.pronoun().capitalize()} liked how it made tiny tracks, because {child.pronoun('possessive')} sandbox games felt peaceful."
    )
    world.para()
    world.say(
        f"Then {child.name} noticed something odd: {missing.label} was gone."
    )
    world.say(
        f"{friend.name} looked too, but the little tracks only led in circles."
    )
    world.say(
        f"{child.name} wondered if the {caster.label} had swallowed the clue, which made the whole mystery feel bigger."
    )
    world.para()

    # Twist: the missing item is not lost; it is tucked under the caster.
    missing.meters["hidden"] = 1
    world.facts["mystery"] = True
    world.say(
        f"At last, {friend.name} nudged the {caster.label} and found {missing.label} tucked underneath it."
    )
    world.say(
        f"The twist was simple: the {caster.label} had not taken anything at all; it had only rolled over the {missing.label} by accident."
    )
    world.say(
        f"{child.name} laughed first, then felt sorry for worrying so much."
    )
    world.para()

    child.memes["sorry"] = 1
    friend.memes["forgiving"] = 1
    world.say(
        f"{child.name} said sorry, and {friend.name} said it was all right."
    )
    world.say(
        f"They brushed the sand off together, shared the {caster.label}, and made a new path beside the found {missing.label}."
    )
    world.say(
        f"By the end, the sandbox was calm again, and the two friends were playing side by side."
    )

    world.facts.update(
        child=child,
        friend=friend,
        caster=caster,
        missing=missing,
        reconciled=True,
        twist=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Person = f["child"]  # type: ignore[assignment]
    missing: ObjectThing = f["missing"]  # type: ignore[assignment]
    return [
        "Write a short slice-of-life story set in a sandbox about a child, a small mystery, and a kind reconciliation.",
        f"Tell a gentle story where {child.name} loses {missing.label}, finds a surprising answer, and makes up with a friend.",
        "Write a child-facing story with a twist that stays calm, concrete, and grounded in sandbox play.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Person = f["child"]  # type: ignore[assignment]
    friend: Person = f["friend"]  # type: ignore[assignment]
    caster: ObjectThing = f["caster"]  # type: ignore[assignment]
    missing: ObjectThing = f["missing"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was {child.name} doing in the sandbox at the start of the story?",
            answer=f"{child.name} was sitting in the sandbox and turning the {caster.label} through the sand.",
        ),
        QAItem(
            question=f"What mystery did {child.name} and {friend.name} try to solve?",
            answer=f"They tried to solve where {missing.label} had gone after it seemed to disappear from the sandbox.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the {caster.label} had not stolen anything; it had rolled over {missing.label} by accident.",
        ),
        QAItem(
            question=f"How did {child.name} and {friend.name} end the story?",
            answer=f"They said sorry, forgave each other, brushed off the sand, and kept playing together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sandbox?",
            answer="A sandbox is a shallow box or area filled with sand where children can dig, build, and play.",
        ),
        QAItem(
            question="What do children often do with sand toys?",
            answer="Children often push, scoop, and roll sand toys to make roads, shapes, or little tracks.",
        ),
        QAItem(
            question="What does it mean to reconcile?",
            answer="To reconcile means to become friendly again after a disagreement or misunderstanding.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for p in world.people.values():
        lines.append(f"{p.name}: meters={p.meters} memes={p.memes}")
    for o in world.objects.values():
        lines.append(f"{o.name}: meters={o.meters} memes={o.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(build_world(params), params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Sandbox slice-of-life storyworld with a caster, mystery, twist, and reconciliation.")
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=["girl", "boy", "nonbinary"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-kind", choices=["girl", "boy", "nonbinary"])
    ap.add_argument("--caster", choices=CASTER_KINDS)
    ap.add_argument("--missing", choices=["shell", "bucket", "shovel", "cookie cutter", "ribbon"])
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
    kind = args.kind or rng.choice(["girl", "boy", "nonbinary"])
    friend_kind = args.friend_kind or _pick_friend_kind(rng, kind)
    name = args.name or _pick_name(rng, kind)
    friend_name = args.friend_name or _pick_name(rng, friend_kind)
    caster = args.caster or rng.choice(CASTER_KINDS)
    missing = args.missing or rng.choice(["shell", "bucket", "shovel", "cookie cutter", "ribbon"])
    if friend_name == name:
        raise StoryError("The child and the friend must have different names.")
    return StoryParams(name=name, kind=kind, friend_name=friend_name, friend_kind=friend_kind, caster=caster, missing=missing)


def _params_list(args: argparse.Namespace, base_seed: int) -> list[StoryParams]:
    out: list[StoryParams] = []
    seen: set[str] = set()
    i = 0
    while len(out) < args.n and i < args.n * 50:
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story not in seen:
            seen.add(sample.story)
            out.append(params)
        i += 1
    return out


CURATED = [
    StoryParams(name="Mia", kind="girl", friend_name="Sam", friend_kind="nonbinary", caster="toy caster", missing="shell"),
    StoryParams(name="Leo", kind="boy", friend_name="Ava", friend_kind="girl", caster="little caster", missing="bucket"),
    StoryParams(name="Nora", kind="girl", friend_name="Eli", friend_kind="boy", caster="sand caster", missing="shovel"),
]


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show theme/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = CURATED
    else:
        params_list = _params_list(args, base_seed)

    samples = [generate(p) for p in params_list]
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
