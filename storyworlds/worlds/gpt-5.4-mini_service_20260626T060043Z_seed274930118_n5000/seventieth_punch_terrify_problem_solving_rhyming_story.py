#!/usr/bin/env python3
"""
Story world: seventieth punch terrify problem solving rhyming story.

A small classical simulation inspired by a rhyming TinyStories-style seed:
a child helps at a seventieth birthday party, a punch bowl causes a scare,
and the characters solve the problem together with a simple fix.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the bright party hall"


@dataclass
class StoryParams:
    place: str = "hall"
    hero_name: str = "Mina"
    hero_type: str = "girl"
    helper_name: str = "Grandma"
    helper_type: str = "grandmother"
    age: int = 70
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING_WORDS = {
    "hall": Setting(place="the bright party hall"),
    "kitchen": Setting(place="the cozy kitchen"),
    "garden": Setting(place="the sunny garden"),
}

RHYMES = {
    "party": "sparkly and hearty",
    "punch": "sweet as a crunch",
    "terrify": "made hearts fly",
    "problem": "trouble to solve them",
    "solve": "smartly resolve",
}

GREETINGS = [
    "The room was warm and light, and everything felt just right.",
    "The bunting swayed with cheerful cheer, and little bells rang near and near.",
    "The table shone with bowls so bright, like tiny moons in morning light.",
]

DECOR = [
    "There were streamers by the wall, and paper stars that loved to fall.",
    "A candle crown was set to glow for someone turning seventy, slow and slow.",
    "The cake stood tall with frosting white, a rosy swirl, a happy sight.",
]

ALERTS = [
    "But then the punch bowl gave a wobble, and that tiny wobble caused a problem.",
    "The punch looked red and ruby sweet, but one hard bump could spill the treat.",
    "A clink, a bump, a lurch, a sway—then worry jumped into the day.",
]

FIXES = [
    "So Mina slid a tray right under, and Grandma smiled like summer thunder.",
    "They moved the bowl to center space, then set a napkin at its base.",
    "They tucked the ladle in a cup and lifted the punch bowl safely up.",
]

ENDING = [
    "The punch stayed safe, the cake stayed neat, and all the guests danced to the beat.",
    "No spill came out, no mess could grow, so happy laughter started to flow.",
    "The scare was gone, the fix was neat, and seventy candles lit the sweet.",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def maybe_article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def age_ordinal(n: int) -> str:
    if n == 70:
        return "seventieth"
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def reasonableness_check(params: StoryParams) -> None:
    if params.age < 70:
        raise StoryError("This world is built for a seventieth celebration.")
    if params.hero_name.strip() == params.helper_name.strip():
        raise StoryError("The helper must be a different person from the hero.")
    if params.hero_type not in {"girl", "boy"}:
        raise StoryError("The hero must be a girl or boy in this small world.")


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    reasonableness_check(params)
    world = World(SETTING_WORDS[params.place])

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"care": 1.0},
        memes={"joy": 1.0, "worry": 0.0, "solve": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        meters={"care": 2.0},
        memes={"joy": 1.0, "worry": 0.0, "solve": 1.0},
    ))
    punch = world.add(Entity(
        id="punch",
        kind="thing",
        type="punch",
        label="punch bowl",
        location=world.setting.place,
        meters={"full": 1.0, "steady": 0.0, "spill": 0.0},
    ))
    cake = world.add(Entity(
        id="cake",
        kind="thing",
        type="cake",
        label=f"{age_ordinal(params.age)} birthday cake",
        location=world.setting.place,
        meters={"safe": 1.0},
    ))
    world.facts.update(
        hero=hero,
        helper=helper,
        punch=punch,
        cake=cake,
        age=params.age,
        place=world.setting.place,
    )
    return world


def tell_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    punch: Entity = f["punch"]
    cake: Entity = f["cake"]
    age = f["age"]

    world.say(
        f"{hero.label} came to the party with a grin so wide, "
        f"for Grandma was turning her {age_ordinal(age)} beside."
    )
    world.say(
        f"{random.choice(GREETINGS)} {random.choice(DECOR)}"
    )

    world.para()
    world.say(
        f"{hero.label} loved the sweet punch, bright and red, "
        f"and the punch bowl sat near the cake ahead."
    )
    world.say(
        f"Then a small elbow gave the table a tap, and the punch bowl wobbled with a tiny clap."
    )
    punch.meters["steady"] = 0.0
    punch.meters["spill"] = 1.0
    hero.memes["worry"] = 1.0
    helper.memes["worry"] = 1.0
    world.say(random.choice(ALERTS))
    world.say(
        f"{hero.label} blinked and gasped, \"Oh no!\" "
        f"For a spill would make the party feel low."
    )

    world.para()
    hero.memes["solve"] = 1.0
    helper.memes["solve"] = 2.0
    punch.meters["steady"] = 1.0
    punch.meters["spill"] = 0.0
    cake.meters["safe"] = 1.0
    world.say(
        f"{helper.label} said, \"Let's fix this fast.\" "
        f"{hero.label} nodded, ready to make it last."
    )
    world.say(random.choice(FIXES))
    world.say(
        f"They moved the bowl by the wall so wide, and kept the cake in a safer spot beside."
    )

    world.para()
    hero.memes["joy"] = 2.0
    helper.memes["worry"] = 0.0
    world.say(random.choice(ENDING))
    world.say(
        f"{hero.label} laughed at the happy sight: a seventieth party shining bright."
    )
    world.say(
        f"The punch stayed still, the guests all cheered, and the little scare disappeared."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    age = f["age"]
    return [
        f"Write a rhyming story about a child who helps at a {age_ordinal(age)} birthday party.",
        f"Tell a gentle problem-solving story where {hero.label} and {helper.label} fix a punch spill before it ruins the cake.",
        "Write a short, child-facing rhyming tale with a surprise, a worry, and a smart fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    age = f["age"]
    return [
        QAItem(
            question=f"What kind of party was this story about?",
            answer=f"It was a {age_ordinal(age)} birthday party, and everyone was celebrating with bright decorations and sweet punch.",
        ),
        QAItem(
            question=f"What problem scared {hero.label}?",
            answer=f"The punch bowl wobbled and looked like it might spill, which made {hero.label} worry about the cake and the party mess.",
        ),
        QAItem(
            question=f"How did {hero.label} and {helper.label} solve the problem?",
            answer=f"They moved the punch bowl to a safer spot and set it steady so the drink would not spill on the cake or the table.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The punch stayed safe, the cake stayed clean, and the party ended with happy laughter and dancing.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is punch at a party?",
        answer="Punch is a sweet drink served in a bowl or big cup, often for guests to share.",
    ),
    QAItem(
        question="Why can a punch bowl cause trouble?",
        answer="A punch bowl can cause trouble if it tips over, because the drink may spill and make a mess.",
    ),
    QAItem(
        question="What does it mean to solve a problem?",
        answer="To solve a problem means to find a useful way to fix what is wrong.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(hall).
place(kitchen).
place(garden).

hero_type(girl).
hero_type(boy).

age(70).

punch_problem :- punch_wobbles, near_cake.
solved :- moved_punch, steady_punch, safe_cake.

valid_story(Place, HeroType) :- place(Place), hero_type(HeroType), age(70).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for key in SETTING_WORDS:
        lines.append(asp.fact("place", key))
    lines.append("age(70).")
    lines.append("hero_type(girl).")
    lines.append("hero_type(boy).")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_pairs = sorted(set(asp.atoms(model, "valid_story")))
    py_pairs = sorted((p, g) for p in SETTING_WORDS for g in ("girl", "boy"))
    if asp_pairs == py_pairs:
        print(f"OK: ASP and Python agree on {len(py_pairs)} valid story settings.")
        return 0
    print("MISMATCH:")
    print("ASP:", asp_pairs)
    print("PY :", py_pairs)
    return 1


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming problem-solving story world.")
    ap.add_argument("--place", choices=SETTING_WORDS.keys(), default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--helper", default=None)
    ap.add_argument("--age", type=int, default=70)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
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
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(["Mina", "Lena", "Toby", "Ari", "Nia", "Pip"])
    helper_name = args.helper or ("Grandma" if rng.random() < 0.5 else "Grandpa")
    helper_type = "grandmother" if helper_name == "Grandma" else "grandfather"
    place = args.place or rng.choice(list(SETTING_WORDS))
    age = args.age
    if age != 70:
        raise StoryError("This storyworld is centered on a seventieth celebration.")
    if hero_name == helper_name:
        raise StoryError("The hero and helper must be different characters.")
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type,
                       helper_name=helper_name, helper_type=helper_type, age=age)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="hall", hero_name="Mina", hero_type="girl", helper_name="Grandma", helper_type="grandmother", age=70),
    StoryParams(place="kitchen", hero_name="Toby", hero_type="boy", helper_name="Grandpa", helper_type="grandfather", age=70),
    StoryParams(place="garden", hero_name="Nia", hero_type="girl", helper_name="Grandma", helper_type="grandmother", age=70),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(pairs)} valid story settings:")
        for p in pairs:
            print(" ", p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.hero_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
