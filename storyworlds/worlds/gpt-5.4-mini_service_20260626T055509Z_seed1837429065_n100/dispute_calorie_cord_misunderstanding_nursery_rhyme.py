#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/dispute_calorie_cord_misunderstanding_nursery_rhyme.py
================================================================================================

A tiny nursery-rhyme storyworld about a misunderstanding, a dispute, a calorie cord,
and a gentle fix.

Seed tale imagined for this world:
---
In the nursery, Pip found a bright cord with tiny paper stars. On the tag it said
"calorie cord." Pip thought it was a magic cord for candy counts. Mum thought it
was a measuring cord for snack time. They both reached for it, and a small dispute
bubbled up. Then they looked closer, laughed, and saw the cord was only for a
game of counting hops and skipping steps.

World shape:
- One child, one grownup, one special cord, one snack table.
- A misunderstanding can raise dispute.
- Looking closely lowers misunderstanding.
- A calm explanation resolves the dispute.
- The ending shows the cord is still safe, and the child feels lighter in heart.

The tone stays close to nursery rhyme: short beats, concrete images, rhythmic lines,
and a soft ending image that proves what changed.
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mum"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the nursery"
    indoors: bool = True


@dataclass
class Cord:
    label: str
    phrase: str
    use: str
    clue: str
    can_clear_misunderstanding: bool = True


@dataclass
class Snack:
    label: str
    phrase: str
    calories: int
    is_treat: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_misunderstanding(world: World) -> list[str]:
    child = world.get("child")
    cord = world.get("cord")
    if child.memes.get("misunderstanding", 0.0) < THRESHOLD:
        return []
    if ("misunderstanding", "dispute") in world.fired:
        return []
    world.fired.add(("misunderstanding", "dispute"))
    child.memes["dispute"] = child.memes.get("dispute", 0.0) + 1
    return [f"A little dispute rose like steam around the {cord.label}."]


def _r_clear_clue(world: World) -> list[str]:
    child = world.get("child")
    adult = world.get("adult")
    cord = world.get("cord")
    if child.memes.get("looked_closer", 0.0) < THRESHOLD:
        return []
    if ("clue", cord.id) in world.fired:
        return []
    world.fired.add(("clue", cord.id))
    child.memes["misunderstanding"] = 0.0
    adult.memes["misunderstanding"] = 0.0
    return [f"They looked at the tag and saw the clue: {cord.phrase}."]


def _r_resolve(world: World) -> list[str]:
    child = world.get("child")
    adult = world.get("adult")
    cord = world.get("cord")
    if child.memes.get("misunderstanding", 0.0) >= THRESHOLD:
        return []
    if child.memes.get("dispute", 0.0) < THRESHOLD:
        return []
    if ("resolve", cord.id) in world.fired:
        return []
    world.fired.add(("resolve", cord.id))
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    adult.memes["warmth"] = adult.memes.get("warmth", 0.0) + 1
    return [f"Their voices softened, and the dispute drifted away like a cloud."]


CAUSAL_RULES = [Rule("misunderstanding", _r_misunderstanding),
                Rule("clear_clue", _r_clear_clue),
                Rule("resolve", _r_resolve)]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    for line in produced:
        world.say(line)
    return produced


@dataclass
class StoryParams:
    name: str
    adult_name: str
    seed: Optional[int] = None


SETTING = Setting(place="the nursery", indoors=True)

CORD = Cord(
    label="calorie cord",
    phrase="a cord for counting hops, not for counting sweets",
    use="counting hops",
    clue="It was only a play cord with paper stars.",
)

SNACK = Snack(
    label="jam tart",
    phrase="a tiny jam tart",
    calories=120,
)

GIRL_NAMES = ["Pip", "Mia", "Lily", "Nora", "Zoe", "Ada"]
ADULT_NAMES = ["Mum", "Mama", "Mom", "Nana"]


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id="child",
        kind="character",
        type="girl",
        label=params.name,
        owner="adult",
        meters={"meters": 0.0},
        memes={"curiosity": 1.0, "misunderstanding": 1.0, "dispute": 0.0},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type="mother",
        label=params.adult_name,
        meters={"meters": 0.0},
        memes={"patience": 1.0, "misunderstanding": 1.0},
    ))
    cord = world.add(Entity(
        id="cord",
        kind="thing",
        type="cord",
        label=CORD.label,
        phrase=CORD.phrase,
        owner="adult",
        caretaker="adult",
        held_by="child",
    ))
    snack = world.add(Entity(
        id="snack",
        kind="thing",
        type="snack",
        label=SNACK.label,
        phrase=SNACK.phrase,
        owner="adult",
        caretaker="adult",
    ))

    world.facts.update(child=child, adult=adult, cord=cord, snack=snack, setting=SETTING)
    world.say(f"{params.name} was in {SETTING.place}, where soft toys sat in a row.")
    world.say(f"{params.name} found the {CORD.label} and blinked at its bright tag.")
    world.say(f"{params.name} thought it might be a candy cord, fit for a sweet parade.")
    world.para()
    world.say(f"{params.adult_name} came close and said the {CORD.label} was for {CORD.use}.")
    world.say(f"{params.name} still frowned, for {params.name} thought it meant {SNACK.phrase}.")
    child.memes["misunderstanding"] = 1.0
    adult.memes["misunderstanding"] = 1.0
    child.meters["reach"] = 1.0
    return world


def tell(world: World) -> None:
    child = world.get("child")
    adult = world.get("adult")
    cord = world.get("cord")
    snack = world.get("snack")

    world.para()
    world.say(f'"But I want the {CORD.label} for the tart," {child.label} said in a tiny pout.')
    child.memes["dispute"] = 1.0
    propagate(world)

    world.para()
    world.say(f"{adult.label} bent low and tapped the tag with a finger.")
    world.say(f'"Look again," {adult.label} said. "See the stars? It is for {CORD.use}."')
    child.memes["looked_closer"] = 1.0
    propagate(world)

    world.para()
    world.say(f"{child.label} gave a giggle and hugged the cord as a game rope instead.")
    world.say(
        f"The {SNACK.label} stayed on the dish, the {cord.label} stayed bright, "
        f"and the nursery felt light and neat."
    )
    child.meters["hops"] = 1.0
    adult.meters["smile"] = 1.0


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    return [
        f'Write a short nursery-rhyme story about a child named {child.label} who '
        f'misunderstands a {f["cord"].label} and has a small dispute with {adult.label}.',
        f'Tell a gentle rhyme where the words "dispute", "calorie", and "cord" '
        f'appear, and the misunderstanding gets fixed by looking closely.',
        f'Write a cozy nursery story about a calorie cord, a snack, and a mix-up '
        f'that ends with laughter.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    cord = f["cord"]
    snack = f["snack"]
    return [
        QAItem(
            question=f"What did {child.label} think the {cord.label} was for at first?",
            answer=f"{child.label} thought the {cord.label} was for {snack.phrase}, not for a game.",
        ),
        QAItem(
            question=f"Why did a dispute start over the {cord.label}?",
            answer=f"The dispute started because {child.label} and {adult.label} had a misunderstanding about what the {cord.label} was for.",
        ),
        QAItem(
            question=f"What fixed the misunderstanding in the nursery?",
            answer=f"Looking closely at the tag fixed it, because the clue showed the {cord.label} was only for {CORD.use}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cord?",
            answer="A cord is a long, flexible string or rope used for tying, pulling, or playing games.",
        ),
        QAItem(
            question="What is a calorie?",
            answer="A calorie is a way to measure energy in food and in the body.",
        ),
        QAItem(
            question="What does misunderstanding mean?",
            answer="A misunderstanding happens when people think the same thing means different things.",
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
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase!r}")
        lines.append(f"  {ent.id}: {ent.label} ({ent.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(child) :- child_misunderstands(child).
dispute(child) :- misunderstanding(child).
clarified(child) :- looked_closer(child).
resolved(child) :- dispute(child), clarified(child).
#show misunderstanding/1.
#show dispute/1.
#show clarified/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("child_misunderstands", "child"),
        asp.fact("looked_closer", "child"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    shown = set((s.name, tuple(a.name if a.type != a.type else getattr(a, 'number', None) for a in s.arguments)) for s in model)
    if ("misunderstanding", ("child",)) in shown and ("dispute", ("child",)) in shown:
        print("OK: ASP twin produced the expected misunderstanding and dispute.")
        return 0
    print("Mismatch in ASP twin.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about a dispute over a calorie cord.")
    ap.add_argument("--name")
    ap.add_argument("--adult-name")
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
    return StoryParams(
        name=args.name or rng.choice(GIRL_NAMES),
        adult_name=args.adult_name or rng.choice(ADULT_NAMES),
        seed=args.seed,
    )


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples.append(generate(StoryParams(name="Pip", adult_name="Mum", seed=base_seed)))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
