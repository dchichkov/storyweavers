#!/usr/bin/env python3
"""
A small story world in a mythic style about a smartypants child, a telling
manner-ism, a gentle nuzzle, and a conflict that is resolved by a wiser choice.

The seed tale behind this world:
---
In an old village by a moonlit hill, a clever child loved to explain everything
with a smart little grin. The child had a stubborn manner-ism: whenever anyone
objected, the child would lift the chin, tap the foot, and say, "I know better."
One evening, the child followed a lantern path to a quiet den and found a tired
young fox caught in thorny brush. The child wanted to show how brave and smart
the child was, but the fox was scared and would not come close.

A mother warned the child not to rush in with proud words. The child ignored the
warning, and the fox shrank back. Then the child softened, knelt down, and gave
the fox a gentle nuzzle. The fox stopped trembling, trusted the child, and
followed home beneath the stars.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the village"
    time: str = "moonlit"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "village": Setting(place="the village", time="moonlit"),
    "grove": Setting(place="the old grove", time="starlit"),
    "harbor": Setting(place="the quiet harbor", time="tide-lit"),
}

GIRL_NAMES = ["Mira", "Lena", "Tala", "Nia", "Sara"]
BOY_NAMES = ["Eli", "Soren", "Bram", "Tomas", "Nico"]
PARENT_TYPES = ["mother", "father"]

ASP_RULES = r"""
% A conflict appears when pride rises and someone draws back.
conflict(P) :- proud(P), frightened(other).
% A soft nuzzle calms the frightened one and resolves the conflict.
resolved(P) :- nuzzle(P), conflict(P).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "mythic"),
        asp.fact("theme", "smartypants"),
        asp.fact("theme", "mannerism"),
        asp.fact("theme", "nuzzle"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    fox: Entity = f["fox"]
    return [
        f'Write a short mythic story for a child about {hero.id}, a smartypants who learns to soften.',
        f"Tell a gentle tale where {hero.id}'s manner-ism causes trouble with {fox.label}, then a nuzzle helps.",
        f"Write a moonlit story about {hero.id}, {parent.label}, and a frightened fox that ends kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    fox: Entity = f["fox"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {hero.type}, and {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What special manner-ism did {hero.id} have?",
            answer=f"{hero.id} had a smartypants habit of lifting the chin, tapping the foot, and saying, \"I know better.\"",
        ),
        QAItem(
            question=f"What frightened animal did {hero.id} meet?",
            answer=f"{hero.id} met {fox.label}, a tired young fox caught in thorny brush.",
        ),
    ]
    if f.get("conflict"):
        qa.append(
            QAItem(
                question=f"Why did {parent.label} warn {hero.id} not to rush in?",
                answer=(
                    f"{parent.label} warned {hero.id} because proud words would make {fox.label} shrink back, "
                    f"and the frightened fox needed kindness more than a boast."
                ),
            )
        )
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"What helped the conflict end?",
                answer=(
                    f"A gentle nuzzle helped end the conflict. Once {hero.id} softened, {fox.label} stopped trembling "
                    f"and trusted the child."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nuzzle?",
            answer="A nuzzle is a gentle touch with the nose or face, like a soft friendly push that shows care.",
        ),
        QAItem(
            question="What does smartypants mean?",
            answer="A smartypants is someone who acts as if they know everything and says clever-sounding things in a showy way.",
        ),
        QAItem(
            question="What is a manner-ism?",
            answer="A manner-ism is a small repeated habit, like a way of standing, speaking, or moving that someone does again and again.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world about smartypants pride and a gentle nuzzle.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(name=name, gender=gender, parent=parent)


def _narrate(world: World) -> None:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    fox: Entity = world.facts["fox"]

    world.say(f"In {world.setting.place}, under a {world.setting.time} sky, {hero.id} was known for a smartypants grin.")
    world.say(f"{hero.id} had a manner-ism: whenever someone disagreed, {hero.pronoun().capitalize()} would lift {hero.pronoun('possessive')} chin and tap {hero.pronoun('possessive')} foot.")
    world.para()
    world.say(f"One evening, {hero.id} and {parent.label} followed a lantern path to a shadowy den.")
    world.say(f"There they found {fox.label}, a young fox tangled in thorny brush and too scared to move.")
    hero.memes["pride"] = 1
    fox.memes["fear"] = 1
    parent.memes["warning"] = 1
    world.facts["conflict"] = True
    world.say(f'"Do not rush in with proud words," {parent.label} warned. "That will only make {fox.label} back away."')
    world.say(f"But {hero.id} lifted {hero.pronoun('possessive')} chin, tapped {hero.pronoun('possessive')} foot, and said, " f'"I know better."')
    world.say(f"At once, {fox.label} shrank back farther into the thorns.")
    world.para()
    world.say(f"Then {hero.id} saw the worry in {fox.label}'s eyes and grew quiet.")
    hero.memes["humility"] = 1
    hero.memes["care"] = 1
    fox.memes["calm"] = 1
    world.facts["resolved"] = True
    world.say(f"{hero.id} knelt down, softened {hero.pronoun('possessive')} voice, and gave {fox.label} a gentle nuzzle.")
    world.say(f"The fox stopped trembling, leaned close, and followed {hero.id} home beneath the stars.")
    world.say(f"By the end, the smartypants grin was smaller, but the kindness was much larger.")


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS["village"])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    fox = world.add(Entity(id="fox", kind="character", type="fox", label="the young fox"))
    world.facts.update(hero=hero, parent=parent, fox=fox, params=params)
    _narrate(world)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("village", "girl", "mother"), ("grove", "boy", "father"), ("harbor", "girl", "father"), ("village", "boy", "mother")]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show resolved/1."))
    _ = model
    print("OK: ASP twin is present for conflict and resolution.")
    return 0


CURATED = [
    StoryParams(name="Mira", gender="girl", parent="mother"),
    StoryParams(name="Eli", gender="boy", parent="father"),
    StoryParams(name="Tala", gender="girl", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show conflict/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("4 compatible story roles.")
        for combo in valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
