#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/owie_cognitive_division_curiosity_humor_tall_tale.py
================================================================================================

A standalone story world for a tiny Tall Tale about curiosity, humor, and a
cognitive division mishap that ends with an owie and a cheerful fix.

Premise:
- A curious child wants to divide an enormous treat equally among a crowd.
- The child tries to do the division in a very literal, very grand way.
- The strain of thinking, climbing, measuring, and juggling the huge treat
  causes a small owie.
- A helper turns the moment funny and simple: count the pieces, make even
  groups, and share the treat safely.

The world uses both physical meters and emotional memes. State changes drive the
prose: curiosity leads to action, confusion can create a cognitive tangle, and a
division plan settles the crowd.
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
    caretakers: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"massive": 0.0, "messy": 0.0, "hurt": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "humor": 0.0, "confusion": 0.0, "confidence": 0.0, "care": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def subj(self) -> str:
        return self.pronoun("subject").capitalize()

    def obj(self) -> str:
        return self.pronoun("object")

    def poss(self) -> str:
        return self.pronoun("possessive")


@dataclass
class Setting:
    place: str
    feature: str
    crowd: str


@dataclass
class StoryParams:
    place: str
    treat: str
    hero: str
    gender: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


SETTINGS = {
    "barnyard": Setting(place="the barnyard", feature="a red barn", crowd="a whole wagonful of cousins"),
    "orchard": Setting(place="the orchard", feature="an apple tree taller than a church steeple", crowd="three sleepy uncles and five giggling kids"),
    "picnic": Setting(place="the picnic grounds", feature="a table long as a train car", crowd="neighbors from three fences away"),
}

TREATS = {
    "pie": {"label": "pie", "phrase": "one giant berry pie", "weight": "heavy"},
    "cake": {"label": "cake", "phrase": "one sky-high cake", "weight": "towering"},
    "bread": {"label": "bread", "phrase": "one mighty loaf", "weight": "bulky"},
}

HELPERS = {
    "grandma": "grandma",
    "uncle": "uncle",
    "teacher": "teacher",
}

BOY_NAMES = ["Milo", "Otis", "Ben", "Cal", "Arlo", "Finn"]
GIRL_NAMES = ["Nell", "Mabel", "June", "Ada", "Piper", "Ivy"]
GENDERS = {"boy", "girl"}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld about owie, curiosity, humor, and division.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--hero")
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(SETTINGS))
    treat = args.treat or rng.choice(list(TREATS))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, treat=treat, hero=hero, gender=gender, helper=helper)


def _hero_word(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def story_setup(world: World, p: StoryParams) -> None:
    hero = world.add(Entity(id="hero", kind="character", type=_hero_word(p.gender), label=p.hero))
    helper = world.add(Entity(id="helper", kind="character", type=p.helper, label=HELPERS[p.helper]))
    treat = world.add(Entity(id="treat", kind="thing", type=p.treat, label=TREATS[p.treat]["label"], phrase=TREATS[p.treat]["phrase"]))
    hero.memes["curiosity"] += 2
    hero.memes["humor"] += 1
    world.say(
        f"{hero.label} was a curious little {hero.type} with a grin as wide as a gate."
        f" {hero.subj()} loved to look at big things and wonder how they could be split just right."
    )
    world.say(
        f"At {world.setting.place}, beside {world.setting.feature}, there was {treat.phrase} waiting for {world.setting.crowd}."
        f" {hero.label} wanted to divide it into equal pieces so nobody got a smaller nibble."
    )
    world.facts.update(hero=hero, helper=helper, treat=treat, params=p)


def maybe_confuse_and_hurt(world: World) -> None:
    hero = world.facts["hero"]
    treat = world.facts["treat"]
    if hero.memes["curiosity"] >= THRESHOLD:
        hero.memes["confusion"] += 1
        treat.meters["massive"] += 1
        world.say(
            f"{hero.label} fetched a chalk stick, a bucket, and a spoon, then tried to count the pieces before anyone could blink."
            f" But the treat looked bigger and bigger the closer {hero.subj()} got, which made the numbers tangle up in {hero.poss()} head."
        )
    hero.meters["hurt"] += 1
    hero.memes["confidence"] -= 0.5
    world.say(
        f"Then {hero.label} bonked {hero.obj()} on the edge of the table with an owie that felt as loud as a door slam."
        f" It was only a little owie, but in a tall tale a little owie can still sound like a thunderclap."
    )


def helper_turn(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    treat = world.facts["treat"]
    hero.memes["humor"] += 2
    hero.memes["confusion"] = 0.0
    hero.memes["confidence"] += 1.5
    hero.meters["hurt"] = 0.0
    world.say(
        f"{helper.label} laughed kindly and said, 'No need to wrestle the whole sky to share a slice.'"
        f" Then {helper.label} drew three circles, then six, then nine, and called the circles 'the honest way to divide supper.'"
    )
    world.say(
        f"{hero.label} snorted a laugh, because the circles were so neat they looked like wagon wheels."
        f" Together they split {treat.phrase} into equal pieces, and every piece looked proud to belong."
    )


def ending(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    treat = world.facts["treat"]
    world.para()
    world.say(
        f"By sunset, the crowd had equal shares, {hero.label} had a little bandage on the owie, and {helper.label} had crumbs on {helper.pronoun('possessive')} chin."
        f" The biggest thing at the table was the laughter, and it was divided so fairly that everybody got plenty."
    )
    world.say(
        f"{hero.label} still looked curious, but now {hero.pronoun()} knew curiosity can ask the smartest questions when humor helps it along."
        f" And the giant {treat.label} was gone at last, not because it vanished, but because it was shared down to the very last happy bite."
    )


def tell(p: StoryParams) -> World:
    world = World(SETTINGS[p.place])
    story_setup(world, p)
    world.para()
    maybe_confuse_and_hurt(world)
    world.para()
    helper_turn(world)
    ending(world)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    treat = world.facts["treat"]
    prompts = [
        f"Write a tall-tale story for children about a curious child, a funny helper, and a giant {treat.label} that needs to be divided fairly.",
        f"Tell a playful story where {hero.label} gets a small owie while trying to do division, then learns a better way with {helper.label}.",
        f"Make a child-friendly tall tale about curiosity and humor at {world.setting.place} involving equal shares and a silly mistake.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {hero.label} want to divide the {treat.label}?",
            answer=f"{hero.label} wanted to divide it fairly so everyone at {world.setting.place} could get an equal share.",
        ),
        QAItem(
            question=f"What happened to {hero.label} while trying to do the division?",
            answer=f"{hero.label} got a little owie after bumping into the table while the numbers got tangled up.",
        ),
        QAItem(
            question=f"How did {helper.label} help {hero.label}?",
            answer=f"{helper.label} made the division simple by drawing circles and helping {hero.label} count the equal pieces.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is division?",
            answer="Division is a way to split something into equal parts so each part gets the same amount.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes a person want to look, ask, and learn more about something.",
        ),
        QAItem(
            question="Why can humor help?",
            answer="Humor can make a hard moment feel lighter and help people smile while they solve a problem.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
curious(hero).
humor(hero).
owie(hero) :- hurt(hero).
division_success :- curious(hero), humor(helper), equal_shares.
"""


def asp_facts() -> str:
    return "\n".join([
        'curious(hero).',
        'humor(helper).',
        'equal_shares.',
        'hurt(hero).',
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for treat in TREATS:
            for gender in GENDERS:
                combos.append((place, treat, gender))
    return combos


def asp_verify() -> int:
    try:
        import asp  # lazy
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show curious/1. #show humor/1. #show owie/1. #show division_success/0."))
    if model is None:
        print("ASP model missing")
        return 1
    print("OK: ASP twin loaded.")
    return 0


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="barnyard", treat="pie", hero="Milo", gender="boy", helper="grandma"),
        StoryParams(place="orchard", treat="cake", hero="Nell", gender="girl", helper="uncle"),
        StoryParams(place="picnic", treat="bread", hero="June", gender="girl", helper="teacher"),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in build_curated()]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        print(sample.story)
        if args.trace and sample.world:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
