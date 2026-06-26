#!/usr/bin/env python3
"""
Standalone storyworld: underoos, teamwork, and a surprise in a rhyming style.
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
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    cozy: bool = True


@dataclass
class SurprisePlan:
    label: str
    reveal: str
    rhymes_with: str
    sparkle: str


@dataclass
class Outfit:
    label: str
    phrase: str
    color: str
    special: str


@dataclass
class StoryParams:
    place: str
    surprise: str
    outfit: str
    name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "playroom": Setting(place="the playroom"),
    "bedroom": Setting(place="the bedroom"),
    "hall": Setting(place="the hall"),
}

SURPRISES = {
    "song": SurprisePlan(
        label="a surprise song",
        reveal="a little song with a bouncy ding-dong ring",
        rhymes_with="ring",
        sparkle="sparkly",
    ),
    "snack": SurprisePlan(
        label="a surprise snack",
        reveal="a cheerful snack on a shiny little plate",
        rhymes_with="plate",
        sparkle="sweet",
    ),
    "card": SurprisePlan(
        label="a surprise card",
        reveal="a hand-made card with a red-gold heart",
        rhymes_with="heart",
        sparkle="bright",
    ),
}

OUTFITS = {
    "blue": Outfit("blue underoos", "soft blue underoos with stars on the side", "blue", "starry"),
    "red": Outfit("red underoos", "bright red underoos with a stripey band", "red", "stripey"),
    "green": Outfit("green underoos", "little green underoos with a leaf-like trim", "green", "leafy"),
}

NAMES = ["Milo", "Nina", "Poppy", "Leo", "Zara", "Finn", "June", "Ari"]
HELPERS = ["Mom", "Dad", "Auntie", "Uncle", "Big Sis", "Big Bro"]


def _rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}"


def tell(setting: Setting, surprise: SurprisePlan, outfit: Outfit, name: str, helper_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="child", label=name))
    helper = world.add(Entity(id=helper_name, kind="character", type="helper", label=helper_name))
    underoos = world.add(Entity(
        id="underoos",
        type="underoos",
        label=outfit.label,
        phrase=outfit.phrase,
        owner=child.id,
        worn_by=child.id,
        plural=True,
    ))
    gift = world.add(Entity(
        id="surprise",
        type="surprise",
        label=surprise.label,
        phrase=surprise.reveal,
        caretaker=helper.id,
    ))

    child.memes["hope"] = 1
    helper.memes["plan"] = 1

    world.say(
        f"{child.id} was a small child in {setting.place}, with {outfit.phrase} tucked close and neat."
    )
    world.say(
        f"{child.id} loved those underoos so much, they felt like a hug and a beat."
    )
    world.say(
        f"{helper.id} had a plan with a grin so grand: a surprise to share, by hand in hand."
    )

    world.para()
    world.say(
        f"First the room got set, with a table and chair, and a hidden little package sitting over there."
    )
    world.say(
        f"{child.id} wanted to help, so {child.pronoun()} brought tape and glue; {helper.id} brought ribbon, and scissors too."
    )

    child.memes["teamwork"] = 1
    helper.memes["teamwork"] = 1
    child.meters["helped"] = 1
    helper.meters["helped"] = 1

    world.say(
        f"They worked as a pair, with a snip and a cheer, and the quiet old room felt cozy and clear."
    )

    world.para()
    world.say(
        f"Then came the surprise: {helper.id} lifted the cloth with a swish and a slide."
    )
    world.say(
        f"Out popped {surprise.reveal}, all {surprise.sparkle} and wide."
    )
    world.say(
        f"{child.id} gasped, then laughed, then clapped with delight; the surprise was more lovely than moonbeam light."
    )

    child.memes["surprise"] = 1
    child.memes["joy"] = 2
    helper.memes["joy"] = 1
    gift.meters["revealed"] = 1

    world.para()
    world.say(
        f"At the end of the day, {child.id} stood proud in {outfit.label}, with {helper.id} nearby."
    )
    world.say(
        f"The teamwork had made the surprise come true, and the whole wide room felt soft as pie."
    )

    world.facts.update(
        child=child,
        helper=helper,
        underoos=underoos,
        surprise=gift,
        setting=setting,
        outfit=outfit,
        surprise_plan=surprise,
    )
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    outfit = f["outfit"]
    surprise = f["surprise_plan"]
    return [
        f'Write a short rhyming story about {child.id}, {helper.id}, teamwork, and {outfit.label}.',
        f"Tell a gentle surprise story where {child.id} helps {helper.id} make {surprise.label}.",
        f'Write a child-friendly rhyming tale that includes "underoos" and ends with a happy surprise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    outfit = f["outfit"]
    surprise = f["surprise_plan"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who was the story about in {place}?",
            answer=f"It was about {child.id}, a child who loved {outfit.label}, and {helper.id}, who had a surprise plan.",
        ),
        QAItem(
            question=f"What did {child.id} wear in the story?",
            answer=f"{child.id} wore {outfit.phrase}, and the story kept calling them underoos.",
        ),
        QAItem(
            question=f"What did {child.id} and {helper.id} do together?",
            answer=f"They used teamwork to get ready for {surprise.label} and make the surprise feel special.",
        ),
        QAItem(
            question=f"What was the surprise at the end?",
            answer=f"The surprise was {surprise.reveal}, and it made {child.id} clap and laugh with joy.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are underoos?",
            answer="Underoos are fun underwear or undershirt-style clothes that a child can wear under other clothes or as part of dress-up play.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help one another and do a job together so it goes better and faster.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that someone shows or gives when the other person does not know it is coming.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld about underoos, teamwork, and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--outfit", choices=OUTFITS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(SETTINGS))
    surprise = args.surprise or rng.choice(list(SURPRISES))
    outfit = args.outfit or rng.choice(list(OUTFITS))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != name])
    return StoryParams(place=place, surprise=surprise, outfit=outfit, name=name, helper_name=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], SURPRISES[params.surprise], OUTFITS[params.outfit], params.name, params.helper_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
place(playroom).
place(bedroom).
place(hall).

surprise(song).
surprise(snack).
surprise(card).

outfit(blue).
outfit(red).
outfit(green).

valid(P,S,O) :- place(P), surprise(S), outfit(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    for o in OUTFITS:
        lines.append(asp.fact("outfit", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, s, o) for p in SETTINGS for s in SURPRISES for o in OUTFITS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid combos:")
        for c in combos[:20]:
            print(*c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for surprise in SURPRISES:
                for outfit in OUTFITS:
                    p = StoryParams(place=place, surprise=surprise, outfit=outfit, name=NAMES[0], helper_name=HELPERS[0])
                    samples.append(generate(p))
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

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
