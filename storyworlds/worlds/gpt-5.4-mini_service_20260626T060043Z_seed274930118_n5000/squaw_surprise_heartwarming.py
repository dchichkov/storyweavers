#!/usr/bin/env python3
"""
storyworlds/worlds/squaw_surprise_heartwarming.py
==================================================

A small heartwarming storyworld about a gentle surprise for a shy little bird
named Squaw.

Premise:
- A child wants to surprise Squaw with something cozy and kind.
- The parent worries the surprise may startle Squaw.
- They choose a softer, quieter plan.
- Squaw is delighted, and the story ends with warmth, gratitude, and a happy
  little scene proving the change.

The world is intentionally tiny and constraint-checked: one setting, one core
surprise plan, and one compatible gentle fix. The narrative is driven by the
simulated world state rather than a frozen paragraph template.
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
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    supports: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"warmth": 0.0, "care": 0.0, "surprise": 0.0, "tired": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "love": 0.0, "relief": 0.0, "startle": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the quiet garden"
    indoors: bool = False


@dataclass
class Plan:
    id: str
    verb: str
    gerund: str
    hush: str
    reveal: str
    risk: str
    effect: str
    keyword: str = "squaw"
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    supports: set[str]
    carries: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


def _apply_surprise(world: World, child: Entity, bird: Entity, gift: Entity, plan: Plan) -> list[str]:
    out: list[str] = []
    if child.meters["surprise"] < THRESHOLD:
        return out
    if gift.protective:
        return out
    if ("startle", bird.id) in world.fired:
        return out
    world.fired.add(("startle", bird.id))
    bird.memes["startle"] += 1
    bird.memes["worry"] += 1
    out.append(f"The quiet plan almost made {bird.label} flutter back.")
    return out


def _apply_warmth(world: World, bird: Entity, gift: Entity) -> list[str]:
    out: list[str] = []
    if gift.worn_by != bird.id:
        return out
    if bird.meters["warmth"] >= THRESHOLD:
        return out
    sig = ("warmth", bird.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bird.meters["warmth"] += 1
    bird.memes["joy"] += 1
    bird.memes["relief"] += 1
    out.append(f"{bird.label} tucked into the gift and stopped shivering.")
    return out


def _apply_love(world: World, child: Entity, parent: Entity, bird: Entity) -> list[str]:
    out: list[str] = []
    if bird.memes["joy"] < THRESHOLD:
        return out
    sig = ("love", bird.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["love"] += 1
    parent.memes["love"] += 1
    out.append(f"That made the child and the parent smile at the same time.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_apply_surprise, _apply_warmth, _apply_love):
            if fn is _apply_surprise:
                sents = fn(world, world.get("child"), world.get("bird"), world.get("gift"), world.facts["plan"])
            elif fn is _apply_warmth:
                sents = fn(world, world.get("bird"), world.get("gift"))
            else:
                sents = fn(world, world.get("child"), world.get("parent"), world.get("bird"))
            if sents:
                produced.extend(sents)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: "StoryParams") -> World:
    world = World(Setting())
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label=f"{params.parent_role}"))
    bird = world.add(Entity(id="bird", kind="character", type="bird", label="Squaw"))
    gift = world.add(Entity(
        id="gift",
        type="blanket",
        label="little blanket",
        phrase="a soft little blanket",
        owner=bird.id,
        caretaker=parent.id,
        protective=True,
        supports={"warmth"},
    ))
    world.facts["plan"] = PLAN

    # Act 1
    world.say(f"{child.label} liked the quiet garden because that was where Squaw lived.")
    world.say(f"One chilly afternoon, {child.label} wanted to {PLAN.verb} for Squaw.")

    # Act 2
    world.para()
    world.say(f"{parent.label} saw the little bundle and worried it might {PLAN.risk}.")
    world.say(f"{child.label} listened, then chose the softer way: {PLAN.hush}.")
    child.meters["surprise"] += 1
    parent.memes["worry"] += 1

    # Act 3
    world.para()
    gift.worn_by = bird.id
    bird.meters["surprise"] += 1
    world.say(f"They {PLAN.reveal}.")
    propagate(world, narrate=True)
    world.say(f"In the end, Squaw was {PLAN.effect}, and the garden felt warmer than before.")

    world.facts.update(child=child, parent=parent, bird=bird, gift=gift, params=params)
    return world


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    parent_role: str
    parent_type: str
    seed: Optional[int] = None


SETTING = Setting(place="the quiet garden", indoors=False)

PLAN = Plan(
    id="surprise_blanket",
    verb="make a surprise for Squaw",
    gerund="making a surprise for Squaw",
    hush="wrap the gift in cloth and tiptoe instead of rushing",
    reveal="placed the blanket beside Squaw's nest with a tiny bow",
    risk="startle Squaw",
    effect="snug and delighted",
    keyword="squaw",
    tags={"squaw", "surprise", "heartwarming"},
)

GIFT = Gift(
    id="blanket",
    label="little blanket",
    phrase="a soft little blanket",
    supports={"warmth"},
    carries={"warmth"},
)

CHILD_NAMES = ["Mina", "Toby", "Lena", "Arlo", "Nia", "Pip"]
CHILD_TYPES = ["girl", "boy"]
PARENT_ROLES = [("mom", "mother"), ("dad", "father")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming story about a gentle surprise for Squaw.")
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def valid_story() -> bool:
    return True


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(CHILD_TYPES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    return StoryParams(
        child_name=child_name,
        child_type=gender,
        parent_role="mom" if parent_type == "mother" else "dad",
        parent_type=parent_type,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        'Write a short heartwarming story about a child making a surprise for Squaw in a quiet garden.',
        f"Tell a gentle story where {p.child_name} tries to {PLAN.verb} and the parent worries it may {PLAN.risk}.",
        f'Create a child-friendly story that includes the word "{PLAN.keyword}" and ends with a cozy reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    bird = world.get("bird")
    child = world.get("child")
    parent = world.get("parent")
    return [
        QAItem(
            question=f"Who was the surprise for in the garden?",
            answer=f"The surprise was for Squaw, the little bird living in the quiet garden.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the surprise?",
            answer=f"{parent.label.capitalize()} worried the surprise might startle Squaw before {child.label} softened the plan.",
        ),
        QAItem(
            question=f"How did {child.label} help Squaw feel better?",
            answer=f"{child.label} chose a quieter plan, then left the soft blanket beside Squaw's nest.",
        ),
        QAItem(
            question=f"How did Squaw feel at the end?",
            answer=f"Squaw felt snug and delighted, and the bird's warmth meter ended high enough to show the gift helped.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a blanket for?",
            answer="A blanket is for keeping someone warm and cozy.",
        ),
        QAItem(
            question="Why can a surprise sometimes be gentle?",
            answer="A gentle surprise is quiet, kind, and safe so it feels happy instead of scary.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"supports={sorted(e.supports)}")
        lines.append(f"  {e.id:5} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(name for name, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
warmthing(B) :- gift(B), supports(B, warmth).
gentle_story :- child(C), bird(B), gift(G), warmthing(G).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "garden"),
        asp.fact("child", "child"),
        asp.fact("parent", "parent"),
        asp.fact("bird", "bird"),
        asp.fact("gift", "gift"),
        asp.fact("supports", "gift", "warmth"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show gentle_story/0."))
    has = any(sym.name == "gentle_story" for sym in model)
    if has == valid_story():
        print("OK: ASP and Python agree.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show gentle_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible gentle story: Squaw + child + blanket + garden")
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(child_name="Mina", child_type="girl", parent_role="mom", parent_type="mother")
        samples = [generate(params)]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random((args.seed or 0) + i))
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
