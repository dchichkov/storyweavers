#!/usr/bin/env python3
"""
storyworlds/worlds/wed_surprise_superhero_story.py
==================================================

A small superhero story world built from the seed word "wed" and the feature
"surprise".

Premise:
- A young superhero wants to wed their favorite helper in a bright city park.
- The day is supposed to be calm and special, but a surprise problem appears:
  the rings are missing right before the ceremony.
- The hero uses their powers and teamwork to recover the rings and turn the
  surprise into a happy celebration.

The world is intentionally small, concrete, and state-driven:
- physical meters: distance, danger, shine, crowd, carry, strength
- emotional memes: joy, worry, surprise, pride, relief

The prose engine, Python reasonableness gate, and inline ASP twin all model the
same tiny story logic.
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

# Story-shaping thresholds
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def them(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the city park"
    backdrop: str = "bright banners and tall trees"


@dataclass
class Power:
    id: str
    label: str
    verb: str
    effect: str
    meter: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    location: str
    carries: str


@dataclass
class Surprise:
    id: str
    label: str
    problem: str
    recovery: str
    meter: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.story_events: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.story_events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_gender: str
    partner_name: str
    partner_gender: str
    power: str
    prize: str
    surprise: str
    seed: Optional[int] = None


SETTINGS = {
    "city_park": Setting(place="the city park", backdrop="bright banners and tall trees"),
}

POWERS = {
    "lift": Power(id="lift", label="lifting power", verb="lifted", effect="raised high above the path", meter="strength"),
    "dash": Power(id="dash", label="speed burst", verb="dashed", effect="raced across the grass", meter="carry"),
    "shine": Power(id="shine", label="shine beam", verb="shone", effect="made the whole place glow", meter="shine"),
}

PRIZES = {
    "rings": Prize(id="rings", label="rings", phrase="a pair of golden rings", location="the gazebo", carries="pocket"),
    "cake": Prize(id="cake", label="cake", phrase="a strawberry cake with blue icing", location="the picnic table", carries="tray"),
}

SURPRISES = {
    "missing_rings": Surprise(
        id="missing_rings",
        label="missing rings",
        problem="the rings were gone from the ribbon box",
        recovery="the rings were found in a tiny nest in a tree",
        meter="worry",
    ),
    "rain_cloud": Surprise(
        id="rain_cloud",
        label="rain cloud",
        problem="a little cloud drifted over the park and made everyone worry",
        recovery="the hero used a shine beam to keep the path bright",
        meter="surprise",
    ),
}

GIRL_NAMES = ["Ava", "Mia", "Zoe", "Nina", "Luna", "Ivy", "Ruby", "Ella"]
BOY_NAMES = ["Leo", "Max", "Noah", "Eli", "Theo", "Ben", "Finn", "Owen"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("city_park", power_id, surprise_id) for power_id in POWERS for surprise_id in SURPRISES]


ASP_RULES = r"""
place(city_park).
power(lift). power(dash). power(shine).
surprise(missing_rings). surprise(rain_cloud).

has_resolution(S) :- surprise(S), S = missing_rings.
has_resolution(S) :- surprise(S), S = rain_cloud.

valid_story(P, Pow, Sur) :- place(P), power(Pow), surprise(Sur), has_resolution(Sur).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for pid in POWERS:
        lines.append(asp.fact("power", pid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero story world: a wed day with a surprise and a rescue."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--partner")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
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
    place = args.place or "city_park"
    power = args.power or rng.choice(list(POWERS))
    surprise = args.surprise or rng.choice(list(SURPRISES))

    if args.gender:
        hero_gender = args.gender
    else:
        hero_gender = rng.choice(["girl", "boy"])
    if args.partner_gender:
        partner_gender = args.partner_gender
    else:
        partner_gender = "boy" if hero_gender == "girl" else "girl"

    hero_name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    partner_name = args.partner or rng.choice(BOY_NAMES if partner_gender == "boy" else GIRL_NAMES)

    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_gender=hero_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        power=power,
        prize="rings",
        surprise=surprise,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("That place does not fit this small superhero story world.")
    if params.power not in POWERS:
        raise StoryError("Unknown superhero power.")
    if params.surprise not in SURPRISES:
        raise StoryError("Unknown surprise.")
    if params.prize != "rings":
        raise StoryError("This story world only supports the wedding rings as the prize.")


def _entity_name(e: Entity) -> str:
    return e.id


def generate_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        label="hero",
        role="hero",
        meters={"strength": 0.0, "shine": 0.0, "carry": 0.0, "danger": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "surprise": 0.0, "pride": 0.0, "relief": 0.0},
    ))
    partner = world.add(Entity(
        id=params.partner_name,
        kind="character",
        type=params.partner_gender,
        label="partner",
        role="partner",
        meters={"strength": 0.0, "shine": 0.0, "carry": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "surprise": 0.0, "relief": 0.0},
    ))
    prize = world.add(Entity(
        id="rings",
        type="thing",
        label="rings",
        phrase="a pair of golden rings",
        role="wedding rings",
        carried_by=partner.id,
        meters={"distance": 0.0, "shine": 0.0},
    ))
    surprise = SURPRISES[params.surprise]
    world.facts.update(hero=hero, partner=partner, prize=prize, surprise=surprise, power=POWERS[params.power])

    return world


def simulate(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    partner: Entity = world.facts["partner"]  # type: ignore[assignment]
    prize: Entity = world.facts["prize"]  # type: ignore[assignment]
    surprise: Surprise = world.facts["surprise"]  # type: ignore[assignment]
    power: Power = world.facts["power"]  # type: ignore[assignment]

    world.say(f"{hero.id} was a little superhero who loved bright days and brave plans.")
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"At {world.setting.place}, {hero.id} and {partner.id} were getting ready to wed, "
        f"with {world.setting.backdrop} all around them."
    )

    world.para()
    world.say(
        f"{hero.id} held a small hand out and promised a perfect day, but then a surprise came."
    )
    if surprise.id == "missing_rings":
        partner.memes["worry"] += 1
        hero.memes["surprise"] += 1
        hero.memes["worry"] += 1
        world.say(f"The big surprise was that {surprise.problem}.")
        world.say(f"{partner.id} looked worried because the wedding could not start without the rings.")
        world.say(f"{hero.id} used {power.label} and {power.verb} toward the trees to search fast.")
        hero.meters[power.meter] += 1
        hero.meters["carry"] += 1
        world.say(f"{power.effect.capitalize()}, and that made the search feel like a real rescue.")
        world.say(f"Then {hero.id} spotted the rings in {surprise.recovery.split(' in ')[-1]}.")
        prize.carried_by = hero.id
        hero.memes["pride"] += 1
        partner.memes["surprise"] += 1
        world.say(f"{hero.id} brought the rings back and smiled, because the surprise had turned into help.")
    else:
        hero.memes["surprise"] += 1
        partner.memes["surprise"] += 1
        world.say(f"The surprise was that {surprise.problem}.")
        world.say(f"{hero.id} answered at once: {surprise.recovery}.")
        hero.meters["shine"] += 1
        world.say(f"{hero.id}'s power kept the path bright, and everyone stayed calm.")
        partner.memes["relief"] += 1

    world.para()
    hero.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(
        f"At last the happy wed day could begin, and {hero.id} stood beside {partner.id} "
        f"with the rings safe and the crowd cheering."
    )
    world.say(
        f"The little superhero had turned a surprise into a happy rescue, and the park shone like a shiny comic page."
    )


def tell_story(params: StoryParams) -> World:
    world = generate_world(params)
    simulate(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    partner: Entity = world.facts["partner"]  # type: ignore[assignment]
    surprise: Surprise = world.facts["surprise"]  # type: ignore[assignment]
    return [
        'Write a short superhero story for a young child about a wed day and a surprise.',
        f"Tell a gentle superhero story where {hero.id} tries to wed {partner.id} but a {surprise.label} changes the plan.",
        f"Write a child-friendly rescue story with the word 'wed' and a happy surprise ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    partner: Entity = world.facts["partner"]  # type: ignore[assignment]
    surprise: Surprise = world.facts["surprise"]  # type: ignore[assignment]
    power: Power = world.facts["power"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.id}, who used {power.label} to help on the wed day.",
        ),
        QAItem(
            question=f"Who was {hero.id} going to wed?",
            answer=f"{hero.id} was going to wed {partner.id} at the city park.",
        ),
        QAItem(
            question=f"What surprise happened before the wed ceremony?",
            answer=f"The surprise was that {surprise.problem}.",
        ),
        QAItem(
            question=f"How did {hero.id} fix the surprise?",
            answer=f"{hero.id} searched with {power.label} and brought the rings back safely.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended with the rings safe, the couple ready to wed, and everyone cheering.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave character who uses special powers to help others.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens suddenly.",
        ),
        QAItem(
            question="What does it mean to wed?",
            answer="To wed means to get married in a ceremony where two people join together as a family.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def explain_rejection() -> str:
    return "(No story: this world only supports a wed day with a surprise rescue in the city park.)"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify_gate() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(
        place="city_park",
        hero_name="Ava",
        hero_gender="girl",
        partner_name="Leo",
        partner_gender="boy",
        power="lift",
        prize="rings",
        surprise="missing_rings",
    ),
    StoryParams(
        place="city_park",
        hero_name="Max",
        hero_gender="boy",
        partner_name="Mia",
        partner_gender="girl",
        power="shine",
        prize="rings",
        surprise="rain_cloud",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify_gate())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for p, powr, sur in stories:
            print(f"  {p:10} {powr:8} {sur:14}")
        return

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
            header = f"### {p.hero_name}: {p.power} with {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
