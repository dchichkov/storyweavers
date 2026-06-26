#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sherbet_cupie_cautionary_tall_tale.py
===============================================================================================================

A small cautionary tall-tale storyworld about sherbet, a cupie, and the trouble
that comes from taking too much too fast.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {"smell": 0.0, "melt": 0.0, "spill": 0.0, "dust": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"pride": 0.0, "greed": 0.0, "worry": 0.0, "alarm": 0.0, "relief": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    heat: float
    dust: float
    crowd: float


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    seed: Optional[int] = None


PLACES = {
    "sunny fair": Place(name="the sunny fair", heat=1.2, dust=0.7, crowd=0.9),
    "orchard lane": Place(name="Orchard Lane", heat=0.9, dust=0.4, crowd=0.5),
    "river road": Place(name="River Road", heat=1.0, dust=0.2, crowd=0.3),
}

NAMES = ["Mabel", "Benny", "Clara", "Jasper", "Nell", "Otis", "Ruby", "Toby"]
HELPERS = ["Aunt June", "Uncle Ned", "Mama Lou", "Papa Finn", "Old Sue", "Bess"]

TALL_TALE_TITLES = [
    "the finest sherbet scoop east of the moon",
    "the cupie who could count lightning twice",
    "the biggest spoon in three counties",
]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place=place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=params.helper_name))
    sherbet = world.add(Entity(
        id="sherbet",
        label="sherbet",
        phrase="a towering bowl of sherbet",
        type="food",
        caretaker=helper.id,
    ))
    cupie = world.add(Entity(
        id="cupie",
        kind="character",
        type="cupie",
        label="cupie",
        phrase="a tiny cupie with a big grin",
    ))
    world.facts.update(hero=hero, helper=helper, sherbet=sherbet, cupie=cupie)
    return world


def spill_risk(world: World) -> bool:
    return world.place.heat + world.place.crowd > 1.8


def tell_story(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    sherbet = world.get("sherbet")
    cupie = world.get("cupie")

    hero.memes["pride"] += 1
    cupie.memes["greed"] += 1

    world.say(
        f"At {world.place.name}, {hero.label} was known for a tall tale so lively it could "
        f"wake the barn cat and make the fence listen."
    )
    world.say(
        f"One afternoon, {hero.label} met {cupie.label}, a tiny cupie with a big grin, and "
        f"the two of them found {sherbet.phrase} cooling on the counter like a pink cloud."
    )
    world.say(
        f"{cupie.label} wanted the biggest lick in the whole county, and {hero.label} wanted to "
        f"show off by carrying the bowl all by {hero.pronoun('possessive')}self."
    )

    world.para()
    if spill_risk(world):
        hero.memes["alarm"] += 1
        helper.memes["worry"] += 1
        world.say(
            f"The day was hot enough to bend a spoon, and the air was dusty enough to sneeze a cow. "
            f"{helper.label} saw the danger at once and said, "
            f"\"That sherbet will melt quicker than a snowball on a skillet.\""
        )
        world.say(
            f"{hero.label} ignored the warning and marched off anyway, while {cupie.label} danced beside "
            f"{hero.pronoun('object')} and shouted for speed."
        )
        world.say(
            f"Before long, the bowl tipped, the sherbet slid, and a pink river ran over {hero.pronoun('possessive')} "
            f"shoes and onto the boards."
        )
        hero.memes["alarm"] += 1
        helper.memes["worry"] += 1
        helper.memes["relief"] += 0.5
        world.say(
            f"{helper.label} shook {helper.pronoun('possessive')} head and fetched a shaded tray, a wide spoon, "
            f"and a cupie-sized cup so the rest could be shared without another spill."
        )
        hero.memes["relief"] += 1
        cupie.memes["greed"] = 0.0
        world.para()
        world.say(
            f"This time, {hero.label} carried the tray carefully under the awning, and {cupie.label} took one tidy lick "
            f"at a time. The sherbet stayed in the bowl, the floor stayed clean, and the whole fair could smell sweetness "
            f"instead of trouble."
        )
    else:
        world.say(
            f"Even so, {helper.label} warned that hot weather and a crowded path could turn a good treat into a slippery mess."
        )
        world.say(
            f"{hero.label} listened, found a shady bench, and let {cupie.label} share the sherbet slowly while the bowl "
            f"rested safe and cool."
        )
        world.say(
            f"The tall tale of the day ended not with a splat, but with a careful grin and a clean napkin."
        )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def prompts_for(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    return [
        f"Write a cautionary tall tale about {hero.label}, {world.get('cupie').label}, and sherbet at {world.place.name}.",
        f"Tell a child-friendly story where {helper.label} warns about a sherbet spill and the characters learn to be careful.",
        f"Write a lively tall tale with a tiny cupie, a big bowl of sherbet, and a safer ending after trouble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    helper = world.get("helper")
    cupie = world.get("cupie")
    return [
        QAItem(
            question=f"Who was carrying the sherbet when the trouble started?",
            answer=f"{hero.label} was carrying the sherbet, trying to show off in front of {cupie.label}.",
        ),
        QAItem(
            question=f"Why did {helper.label} worry about the sherbet at {world.place.name}?",
            answer=f"{helper.label} worried because the day was hot and crowded, so the sherbet could melt and spill.",
        ),
        QAItem(
            question=f"What changed after the spill happened?",
            answer=f"They switched to a shaded tray and careful sharing, so the sherbet stayed in the bowl instead of running all over the floor.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sherbet?",
            answer="Sherbet is a cold, sweet frozen treat that can melt if it sits in warm weather too long.",
        ),
        QAItem(
            question="What is a cupie?",
            answer="A cupie is a tiny doll-like character in this storyworld, small enough to ride on a spoon of sherbet.",
        ),
        QAItem(
            question="Why should you be careful with frozen treats on hot days?",
            answer="You should be careful because heat can make them melt quickly, which can lead to sticky spills.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(sunny_fair).
place(orchard_lane).
place(river_road).

hot(sunny_fair).
crowded(sunny_fair).
hot(orchard_lane).
crowded(orchard_lane).
calm(river_road).

character(hero).
character(helper).
character(cupie).

item(sherbet).

risky(P) :- hot(P), crowded(P).
warning_needed(P) :- risky(P).
spill_happens(P) :- risky(P).
cautionary_story(P) :- warning_needed(P), spill_happens(P).

#show risky/1.
#show cautionary_story/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.heat > 1.05:
            lines.append(asp.fact("hot", pid))
        if place.crowd > 0.6:
            lines.append(asp.fact("crowded", pid))
        if place.crowd <= 0.6:
            lines.append(asp.fact("calm", pid))
    lines.append(asp.fact("character", "hero"))
    lines.append(asp.fact("character", "helper"))
    lines.append(asp.fact("character", "cupie"))
    lines.append(asp.fact("item", "sherbet"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    models = asp.solve(asp_program(), models=0)
    risky = set()
    cautionary = set()
    for model in models:
        risky.update(asp.atoms(model, "risky"))
        cautionary.update(asp.atoms(model, "cautionary_story"))
    py_risky = {(k,) for k, p in PLACES.items() if p.heat > 1.05 and p.crowd > 0.6}
    py_cautionary = set(py_risky)
    if risky == py_risky and cautionary == py_cautionary:
        print("OK: ASP and Python agree on risky and cautionary places.")
        return 0
    print("MISMATCH")
    print("ASP risky:", sorted(risky))
    print("PY  risky:", sorted(py_risky))
    print("ASP cautionary:", sorted(cautionary))
    print("PY  cautionary:", sorted(py_cautionary))
    return 1


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary tall tale about sherbet and a cupie.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--helper-name")
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
    place = args.place or rng.choice(list(PLACES))
    hero_name = args.hero_name or rng.choice(NAMES)
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    helper_name = args.helper_name or rng.choice(HELPERS)
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: round(v, 3) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 3) for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.label:
            bits.append(f"label={ent.label}")
        lines.append(f"{ent.id}: {ent.kind} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="sunny fair", hero_name="Mabel", hero_type="girl", helper_name="Aunt June"),
    StoryParams(place="orchard lane", hero_name="Benny", hero_type="boy", helper_name="Uncle Ned"),
    StoryParams(place="river road", hero_name="Ruby", hero_type="girl", helper_name="Mama Lou"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        print(sorted(asp.atoms(model, "risky")))
        print(sorted(asp.atoms(model, "cautionary_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
