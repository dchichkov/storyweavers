#!/usr/bin/env python3
"""
Story world: tide hall curiosity bedtime story.

A tiny bedtime-style simulation about a curious child, a seaside hall, and the
gentle tide that comes and goes by moonlight.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the hall by the sea"
    tide_side: str = "outside the door"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    setting: str = "hall"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_damp_hall(world: World) -> list[str]:
    tide = world.get("tide")
    hall = world.get("hall")
    door = world.get("door")
    out: list[str] = []
    if tide.meters["high"] >= THRESHOLD and door.meters["open"] >= THRESHOLD:
        sig = ("damp",)
        if sig not in world.fired:
            world.fired.add(sig)
            hall.meters["damp"] += 1
            out.append("A little cool damp reached the hall floor.")
    return out


def _r_sleepy(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["curious"] >= THRESHOLD and child.memes["safe"] >= THRESHOLD:
        sig = ("sleepy",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["sleepy"] += 1
            return ["The child grew sleepier under the soft lantern light."]
    return []


RULES = [Rule("damp_hall", _r_damp_hall), Rule("sleepy", _r_sleepy)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_world() -> World:
    world = World(Setting())
    child = world.add(Entity(id="child", kind="character", type="girl", label="Mina"))
    parent = world.add(Entity(id="parent", kind="character", type="mother", label="Mama"))
    hall = world.add(Entity(id="hall", type="hall", label="the hall"))
    tide = world.add(Entity(id="tide", type="tide", label="the tide"))
    door = world.add(Entity(id="door", type="thing", label="the door"))
    lantern = world.add(Entity(id="lantern", type="thing", label="the lantern", protective=True))

    child.memes["curious"] = 0.0
    child.memes["safe"] = 0.0
    child.memes["sleepy"] = 0.0
    parent.memes["calm"] = 1.0
    hall.meters["dry"] = 1.0
    tide.meters["high"] = 0.0
    door.meters["open"] = 1.0
    lantern.meters["lit"] = 0.0

    world.facts.update(child=child, parent=parent, hall=hall, tide=tide, door=door, lantern=lantern)
    return world


def tell(world: World, params: StoryParams) -> World:
    child = world.get("child")
    parent = world.get("parent")
    hall = world.get("hall")
    tide = world.get("tide")
    door = world.get("door")
    lantern = world.get("lantern")

    world.say(
        f"On a quiet night, {child.label} and {parent.label} were in {world.setting.place}, "
        f"where the sea could be heard breathing nearby."
    )
    world.say(
        f"{child.label} loved to be curious. {child.pronoun().capitalize()} listened to tiny sounds, "
        f"wondering what the moon was doing to make the water move."
    )

    world.para()
    tide.meters["high"] = 1.0
    world.say(
        f"Outside, {tide.label} crept up with a silver hush. The front {door.label} was open a little, "
        f"and {child.label} leaned toward the shine."
    )
    child.memes["curious"] += 1.0
    world.say(
        f"{child.label} wanted to peek farther, but {parent.label} put out a gentle hand and smiled. "
        f'"First we keep the hall dry," {parent.pronoun("subject")} whispered, "then we can watch safely."'
    )

    world.para()
    door.meters["open"] = 0.0
    lantern.meters["lit"] = 1.0
    child.memes["safe"] += 1.0
    world.say(
        f"So {parent.label} closed the {door.label} and lit {lantern.it()} with a warm, gold glow. "
        f"The light made the hall look cozy, like it was tucking the night in."
    )
    propagate(world, narrate=True)

    world.say(
        f"{child.label} stood beside {parent.label}, looking through the glass while the tide sang softly outside. "
        f"{child.pronoun().capitalize()} learned that a curious question can wait for a safer moment."
    )

    world.para()
    child.memes["sleepy"] += 1.0
    world.say(
        f"When the story of the tide was finished, {child.label} yawned. "
        f"The hall stayed dry, the lantern stayed bright, and bedtime felt gentle as a wave on sand."
    )

    world.facts.update(
        child=child,
        parent=parent,
        hall=hall,
        tide=tide,
        door=door,
        lantern=lantern,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    return [
        'Write a bedtime story about curiosity, a hall, and the tide outside the door.',
        f"Tell a gentle story where {child.label} wonders about the tide and {parent.label} keeps the hall safe.",
        "Write a short sleepy tale with moonlight, a quiet hall, and a child who learns to wait for a safer look.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    hall = world.facts["hall"]
    tide = world.facts["tide"]
    return [
        QAItem(
            question=f"Who was curious about the tide in the hall?",
            answer=f"{child.label} was curious about the tide in the hall.",
        ),
        QAItem(
            question=f"What did {parent.label} do to keep the hall safe?",
            answer=f"{parent.label} closed the door and lit the lantern so the hall could stay dry and cozy.",
        ),
        QAItem(
            question=f"What happened at the end of the bedtime story?",
            answer=f"The hall stayed dry, the tide sang outside, and {child.label} grew sleepy enough for bedtime.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tide?",
            answer="A tide is the sea rising and falling in its own slow rhythm.",
        ),
        QAItem(
            question="What is a hall?",
            answer="A hall is a long room or passage inside a house or building.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to look, learn, and ask about things.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting != "hall":
        raise StoryError("This story world only supports the hall setting.")
    names = ["Mina", "Luna", "Ivy", "Nora", "Elsie"]
    genders = ["girl"]
    name = args.name or rng.choice(names)
    gender = args.gender or rng.choice(genders)
    parent = args.parent or "mother"
    return StoryParams(name=name, gender=gender, parent=parent, setting="hall")


def generate(params: StoryParams) -> StorySample:
    world = build_world()
    world.get("child").label = params.name
    world.get("child").type = params.gender
    world.get("parent").type = params.parent
    world = tell(world, params)
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
    ap = argparse.ArgumentParser(description="Bedtime story world: tide, hall, and curiosity.")
    ap.add_argument("--setting", choices=["hall"], default="hall")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl"], default=None)
    ap.add_argument("--parent", choices=["mother"], default=None)
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


ASP_RULES = r"""
setting(hall).
feature(curiosity).
place(hall).

compatible(hall, curiosity).
valid_story(hall, curiosity).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "hall"),
            asp.fact("feature", "curiosity"),
            asp.fact("place", "hall"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("hall", "curiosity")}
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: clingo matches Python gate ({len(py)} story).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("python:", sorted(py))
    print("clingo:", sorted(clingo))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story:")
        print("  hall  curiosity")
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, rng)
        samples.append(generate(params))
    else:
        for i in range(max(args.n, 1)):
            p = resolve_params(args, random.Random((args.seed or 0) + i if args.seed is not None else rng.randrange(2**31)))
            p.seed = args.seed
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
