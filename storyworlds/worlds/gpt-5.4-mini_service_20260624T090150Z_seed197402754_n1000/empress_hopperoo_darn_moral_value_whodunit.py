#!/usr/bin/env python3
"""
A small whodunit storyworld about an empress, a hopperoo, and a missing darn
moral value charm.

The domain premise:
- A gentle empress keeps a prized Moral Value medallion in her bright hall.
- A small hopperoo helper helps with chores and notices clues.
- One day the medallion goes missing, and the court must figure out who moved it.
- The solution is not villainy but a mistaken good deed: the object was put away
  for safety, then returned with an honest apology.

The world model tracks physical state in meters and emotional state in memes.
The prose is driven by the simulated investigation, not by a frozen template.
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


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def pronoun(self) -> str:
        if self.kind == "person" and self.role == "empress":
            return "she"
        return "it"

    def possessive(self) -> str:
        if self.kind == "person" and self.role == "empress":
            return "her"
        return "its"


@dataclass
class Setting:
    place: str = "the golden hall"


@dataclass
class StoryParams:
    name: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


NAMES = ["Iris", "Mira", "Luna", "Tessa", "Nora", "Ada"]
HOPPEROOS = ["Pip", "Moss", "Dart", "Bean", "Tully", "Wren"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Whodunit storyworld: an empress, a hopperoo, and a moral value mystery."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HOPPEROOS)
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
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HOPPEROOS)
    return StoryParams(name=name, helper=helper)


def _moral_value_story() -> str:
    return "a moral value"


def tell(params: StoryParams) -> World:
    world = World(Setting())
    empress = world.add(Entity(id=params.name, kind="person", label="the empress", role="empress"))
    hopperoo = world.add(Entity(id=params.helper, kind="creature", label="the hopperoo", role="helper"))
    value = world.add(Entity(
        id="value",
        kind="thing",
        label="Moral Value medallion",
        location="on the velvet stand",
        meters={"shine": 1.0},
        memes={"importance": 1.0},
    ))
    hidden = world.add(Entity(
        id="drawer",
        kind="thing",
        label="a wooden drawer",
        location="behind the blue curtain",
        meters={"closed": 1.0},
    ))

    world.say(
        f"In {world.setting.place}, {empress.label} kept a small prize called the Moral Value medallion."
    )
    world.say(
        f"{hopperoo.label.capitalize()} liked to tidy the hall and bow to the empress when the bells rang."
    )
    world.para()

    world.say(
        f"One morning, the medallion was gone from the stand. The empress frowned, but she did not shout."
    )
    world.say(
        f"Instead, she looked for clues: a half-open curtain, a soft hop-print, and a drawer that had been shut in a hurry."
    )
    world.facts["clues"] = ["curtain", "hop-print", "drawer"]
    world.facts["missing"] = True
    world.para()

    hopperoo.memes["worry"] = 1.0
    hopperoo.meters["dust"] = 1.0
    world.say(
        f"The hopperoo noticed the hop-print and remembered moving the medallion yesterday."
    )
    world.say(
        f"It had heard thunder, feared the stand would tip, and tucked the medallion into the drawer to keep it safe."
    )
    world.say(
        f"That was a careful act, not a sneaky one, but the empress still needed the truth."
    )
    world.para()

    value.location = "inside the drawer"
    hidden.location = "by the curtain"
    world.say(
        f"The empress opened the drawer. There was the Moral Value medallion, resting quietly in the dark."
    )
    world.say(
        f"The hopperoo stepped forward, admitted the mistake, and offered a clean cloth to wipe the dust away."
    )
    hopperoo.memes["relief"] = 1.0
    empress.memes["forgiveness"] = 1.0
    world.say(
        f"The empress smiled and said the best mystery endings are the honest ones."
    )
    world.say(
        f"She placed the medallion back on its stand, and the hall looked bright and fair again."
    )

    world.facts.update(empress=empress, hopperoo=hopperoo, value=value, hidden=hidden, resolved=True)
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    empress: Entity = f["empress"]  # type: ignore[assignment]
    hopperoo: Entity = f["hopperoo"]  # type: ignore[assignment]
    return [
        "Write a gentle whodunit for a young child about an empress and a hopperoo, using the phrase moral value.",
        f"Tell a mystery story where {empress.label} looks for a missing Moral Value medallion and {hopperoo.label} helps explain the clues.",
        "Write a short, clue-based story that ends with an honest apology and a returned treasure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    empress: Entity = f["empress"]  # type: ignore[assignment]
    hopperoo: Entity = f["hopperoo"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question="What was missing from the hall at the start of the mystery?",
            answer="The Moral Value medallion was missing from the velvet stand.",
        ),
        QAItem(
            question="What clue helped the empress begin solving the mystery?",
            answer="She noticed the half-open curtain, a soft hop-print, and a drawer that had been shut in a hurry.",
        ),
        QAItem(
            question=f"Why did the hopperoo move the medallion?",
            answer="It moved the medallion because it heard thunder and wanted to keep it safe in the drawer.",
        ),
        QAItem(
            question=f"How did {empress.label} respond when the truth was explained?",
            answer="The empress smiled, forgave the hopperoo, and put the medallion back on its stand.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the characters look for clues to find out what really happened.",
        ),
        QAItem(
            question="What does it mean to be honest?",
            answer="Being honest means telling the truth, even when it is a little uncomfortable.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good idea about how to treat others, like honesty, kindness, or fairness.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        bits = []
        if ent.location:
            bits.append(f"location={ent.location}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"  {ent.id:8} ({ent.kind:7}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
#show story/1.
story("an empress and a hopperoo solve a moral value mystery") :- ok.
ok.
"""


def asp_facts() -> str:
    return "moral_value(value).\nempress(role_empress).\nhopperoo(helper).\n"


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(name="Iris", helper="Pip"),
    StoryParams(name="Mira", helper="Moss"),
    StoryParams(name="Luna", helper="Dart"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
            header = f"### {p.name} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
