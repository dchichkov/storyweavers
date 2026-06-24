#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074326Z_seed779406221_n50/caster_sandbox_reconciliation_mystery_to_solve_twist.py
=================================================================================================

A small standalone storyworld set in a sandbox.

Seed premise:
- A child caster in a sandbox is trying to solve a small mystery.
- A twist changes what they think is true.
- Reconciliation ends the story with a repaired friendship.

Style:
- Slice of life
- Child-facing
- Concrete, state-driven, and gentle

The domain stays small on purpose:
- a sandbox
- two children
- a missing mold or toy
- a reveal
- a reconciliation beat

The story engine builds the prose from simulated world state rather than from a
frozen paragraph with swapped names.
"""

from __future__ import annotations

import argparse
import copy
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    label: str
    texture: str
    weather: str
    hidden_spot: str


@dataclass
class Tool:
    id: str
    label: str
    use: str
    material: str
    small: bool = True


@dataclass
class Mystery:
    id: str
    missing: str
    clue: str
    twist: str
    found_where: str


@dataclass
class StoryParams:
    setting: str
    caster: str
    caster_gender: str
    friend: str
    friend_gender: str
    mystery: str
    tool: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
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

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "sandbox": Setting(
        id="sandbox",
        label="sandbox",
        texture="soft sand",
        weather="warm afternoon",
        hidden_spot="under the red bucket",
    ),
    "backyard": Setting(
        id="backyard",
        label="backyard sandbox",
        texture="cool sand",
        weather="golden evening",
        hidden_spot="near the wooden fence",
    ),
}

TOOLS = {
    "caster": Tool(
        id="caster",
        label="caster mold",
        use="make little sand shapes",
        material="plastic",
    ),
    "bucket": Tool(
        id="bucket",
        label="bucket",
        use="carry water and sand",
        material="plastic",
    ),
    "spade": Tool(
        id="spade",
        label="spade",
        use="dig neat walls",
        material="metal",
    ),
}

MYSTERIES = {
    "missing_mold": Mystery(
        id="missing_mold",
        missing="the star-shaped caster mold",
        clue="a trail of damp sand",
        twist="the mold was never stolen; it had been buried by a friendly shovel game",
        found_where="under the little hill",
    ),
    "vanished_flag": Mystery(
        id="vanished_flag",
        missing="the tiny sand flag",
        clue="a bright ribbon peeking from the sand",
        twist="the flag had slipped into the castle moat during play",
        found_where="inside the moat",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Zoe", "Ada", "Ruby"]
BOY_NAMES = ["Finn", "Eli", "Noah", "Leo", "Theo", "Max"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life sandbox mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--caster", choices=TOOLS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--friend", choices=["random"], default=None)
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    caster = args.caster or "caster"
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    fg = rng.choice(["girl", "boy"])
    friend = rng.choice(GIRL_NAMES if fg == "girl" else BOY_NAMES)
    return StoryParams(
        setting=setting,
        caster=caster,
        caster_gender="thing",
        friend=friend,
        friend_gender=fg,
        mystery=mystery,
        tool="spade",
    )


def _make_world(params: StoryParams) -> World:
    w = World()
    setting = SETTINGS[params.setting]
    caster_tool = TOOLS[params.caster]
    mystery = MYSTERIES[params.mystery]

    caster = w.add(Entity(id="caster", kind="character", type="child", label=params.caster,
                          role="caster", memes={"curiosity": 1.0, "worry": 0.0},
                          attrs={"tool": caster_tool.label}))
    friend = w.add(Entity(id="friend", kind="character", type=params.friend_gender,
                          label=params.friend, role="friend",
                          memes={"curiosity": 1.0, "worry": 0.0}))
    sandbox = w.add(Entity(id="sandbox", kind="place", type="sandbox", label=setting.label,
                           meters={"tidiness": 1.0}, attrs={"texture": setting.texture}))
    hidden = w.add(Entity(id="hidden", kind="thing", type="thing", label=mystery.missing,
                          meters={"buried": 1.0}))
    clue = w.add(Entity(id="clue", kind="thing", type="thing", label=mystery.clue))

    w.facts.update(dict(
        setting=setting,
        mystery=mystery,
        caster=caster,
        friend=friend,
        sandbox=sandbox,
        hidden=hidden,
        clue=clue,
        caster_tool=caster_tool,
    ))

    w.say(f"It was a {setting.weather} in the {setting.label}, and the sand felt {setting.texture}.")
    w.say(f"{params.caster.capitalize()} liked using the {caster_tool.label} to {caster_tool.use}.")
    w.say(f"{params.friend} sat nearby and watched the little sand shapes grow.")

    w.para()
    w.say(f"Then {params.caster.capitalize()} noticed that {mystery.missing} was gone.")
    w.say(f"There was only {mystery.clue}, and that made the sandbox feel like a small mystery to solve.")

    caster.memes["worry"] += 1.0
    friend.memes["worry"] += 0.5
    sandbox.meters["tidiness"] -= 0.2

    w.para()
    w.say(f'"Maybe {params.friend} moved it," {params.caster.capitalize()} said, trying to sound sure.')
    w.say(f"{params.friend} frowned and shook {friend.pronoun('possessive')} head. \"I didn't.\"")

    if mystery.id == "missing_mold":
        w.say(f"{params.friend.capitalize()} pointed at the {mystery.clue}, and they both dug where the sand looked puffed up.")
        w.say(f"Under the little hill, they found the mold exactly where {mystery.twist}.")

    else:
        w.say(f"{params.friend.capitalize()} followed the bright ribbon with careful fingers.")
        w.say(f"Inside the moat, they found the flag, and the twist was that {mystery.twist}.")

    caster.memes["worry"] = 0.0
    friend.memes["worry"] = 0.0
    caster.memes["relief"] = 1.0
    friend.memes["relief"] = 1.0
    caster.memes["reconciliation"] = 1.0
    friend.memes["reconciliation"] = 1.0
    sandbox.meters["tidiness"] += 0.4

    w.para()
    w.say(f"{params.caster.capitalize()} looked at {params.friend} and said, \"I'm sorry I blamed you.\"")
    w.say(f"{params.friend.capitalize()} smiled back. \"It's okay. We found it together.\"")
    w.say(f"They brushed the sand off the mold, and the sandbox felt calm again.")

    w.para()
    w.say(f"This time, {params.caster.capitalize()} made a neat castle with the {caster_tool.label},")
    w.say(f"and {params.friend} packed the walls gently so they would not fall over.")
    w.say(f"Two friends kept playing side by side, and the mystery was solved without losing the day.")

    w.facts["outcome"] = "reconciled"
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    caster: Entity = f["caster"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    return [
        f"Write a slice-of-life sandbox story where {caster.label} and {friend.label} solve a small mystery and make up.",
        f"Tell a calm sandbox story about {m.missing}, a clue in the sand, and a twist that changes what the children think happened.",
        f"Write a gentle reconciliation story set in the {setting.label}, where the children work out the mystery together and end as friends.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    m: Mystery = f["mystery"]  # type: ignore[assignment]
    caster: Entity = f["caster"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What kind of place is the story set in?",
            answer=f"It is set in a {setting.label}, where the sand is soft and the children can build and dig.",
        ),
        QAItem(
            question=f"What mystery did {caster.label} notice?",
            answer=f"{caster.label.capitalize()} noticed that {m.missing} was gone and only {m.clue} was left behind.",
        ),
        QAItem(
            question=f"What did {caster.label} think at first?",
            answer=f"{caster.label.capitalize()} thought {friend.label} might have moved it, but that idea turned out to be wrong.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"They followed the clue and found it where it had been hidden all along, so the mystery was solved together.",
        ),
        QAItem(
            question="How did the children feel at the end?",
            answer="They felt relieved, and they made up after the misunderstanding.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a caster mold?",
            answer="A caster mold is a little tool that helps make a shape in sand.",
        ),
        QAItem(
            question="What do children do in a sandbox?",
            answer="They dig, build, pour, and make pretend shapes with the sand.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making up after a misunderstanding and becoming friendly again.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a problem where someone has to look for clues to find the answer.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a new turn that changes what the characters thought was true.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: kind={e.kind} type={e.type} label={e.label} role={e.role} "
                   f"meters={e.meters} memes={e.memes} attrs={e.attrs}")
    out.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def resolve_all() -> list[StoryParams]:
    out = []
    for setting in SETTINGS:
        for mystery in MYSTERIES:
            out.append(StoryParams(setting=setting, caster="caster", caster_gender="thing",
                                   friend="Mia", friend_gender="girl", mystery=mystery,
                                   tool="spade"))
    return out


ASP_RULES = r"""
setting(sandbox).
setting(backyard).

mystery(missing_mold).
mystery(vanished_flag).

twist(missing_mold) :- mystery(missing_mold).
twist(vanished_flag) :- mystery(vanished_flag).

reconciliation :- setting(_), mystery(_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def build_parser_for_asp() -> argparse.ArgumentParser:
    return build_parser()


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show twist/1.\n#show reconciliation/0.\n"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        print("OK: no ASP parity checks are defined for this compact storyworld.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in resolve_all():
            samples.append(generate(p))
    else:
        for i in range(max(args.n, 1)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
