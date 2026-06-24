#!/usr/bin/env python3
"""
A standalone story world for a small superhero-style tale with teamwork, a
mystery to solve, and a lesson learned.

Seed premise:
- A young hero notices a mystery in their city.
- A teammate helps track clues.
- The solution requires cooperation, not just powers.
- The ending should show a clear lesson learned and a changed emotional state.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "character"  # character | thing
    role: str = ""
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.role in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in {"boy", "man", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    city: str
    place: str
    vibe: str


@dataclass
class Mystery:
    id: str
    missing: str
    clue1: str
    clue2: str
    cause: str
    solved_by: str


@dataclass
class Team:
    leader: str
    partner: str
    strength: str
    helper_method: str


@dataclass
class StoryParams:
    city: str
    place: str
    hero: str
    hero_role: str
    partner: str
    partner_role: str
    mystery: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    hero: Entity
    partner: Entity
    mystery: Mystery
    team: Team
    objects: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_object(self, obj: Entity) -> Entity:
        self.objects[obj.id] = obj
        return obj

    def get_object(self, oid: str) -> Entity:
        return self.objects[oid]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "neon_city": Setting(city="Neon City", place="the clock tower plaza", vibe="bright"),
    "harbor": Setting(city="Harbor Bay", place="the lighthouse dock", vibe="windy"),
    "skyline": Setting(city="Skyline", place="the roof garden", vibe="high"),
    "suburb": Setting(city="Maple Suburb", place="the community square", vibe="quiet"),
}

MYSTERIES = {
    "vanishing_map": Mystery(
        id="vanishing_map",
        missing="the mayor's map",
        clue1="a silver dust trail",
        clue2="a tiny stamp shaped like a moon",
        cause="a playful wind machine in the tower",
        solved_by="following the clues together",
    ),
    "silent_alarm": Mystery(
        id="silent_alarm",
        missing="the museum alarm",
        clue1="a bent wire",
        clue2="a sticky blue sticker",
        cause="a loose panel behind a poster",
        solved_by="checking high and low as a team",
    ),
    "lost_medal": Mystery(
        id="lost_medal",
        missing="the captain's medal",
        clue1="muddy footprints",
        clue2="a shiny ribbon thread",
        cause="the medal slipped into a storm drain",
        solved_by="lifting the grate with both heroes",
    ),
    "hidden_cookie": Mystery(
        id="hidden_cookie",
        missing="the bake-sale cookies",
        clue1="crumbs near the bench",
        clue2="a trail of flour prints",
        cause="a sneaky squirrel stash",
        solved_by="sharing the job and looking carefully",
    ),
}

TEAM_STRENGTHS = [
    ("speed", "dash between the clues"),
    ("listening", "hear what others miss"),
    ("stretching", "reach places one hero cannot"),
    ("lifting", "move heavy things together"),
]

HERO_NAMES = ["Milo", "Nia", "Kai", "Zara", "Tess", "Rafi", "Ivy", "Theo"]
PARTNER_NAMES = ["June", "Pip", "Orion", "Maya", "Ben", "Luna", "Eli", "Sage"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.city]
    mystery = MYSTERIES[params.mystery]
    team_strength = random.choice(TEAM_STRENGTHS)
    hero = Entity(
        id=params.hero,
        role=params.hero_role,
        label=params.hero,
        meters={"courage": 1.0, "curiosity": 1.0},
        memes={"worry": 0.2, "hope": 1.0},
    )
    partner = Entity(
        id=params.partner,
        role=params.partner_role,
        label=params.partner,
        meters={"courage": 0.8, "curiosity": 1.2},
        memes={"worry": 0.2, "hope": 1.0},
    )
    team = Team(
        leader=hero.id,
        partner=partner.id,
        strength=team_strength[0],
        helper_method=team_strength[1],
    )
    return World(setting=setting, hero=hero, partner=partner, mystery=mystery, team=team)


def solve_mystery(world: World) -> None:
    hero = world.hero
    partner = world.partner
    mystery = world.mystery

    world.say(
        f"In {world.setting.city}, {hero.id} and {partner.id} were the city's little heroes."
    )
    world.say(
        f"One day, something strange happened at {world.setting.place}: {mystery.missing} was gone."
    )
    world.say(
        f"{hero.id} noticed {mystery.clue1}, and {partner.id} spotted {mystery.clue2}."
    )

    hero.memes["worry"] = 1.0
    partner.memes["worry"] = 0.9
    world.facts["mystery_missing"] = mystery.missing
    world.facts["clues"] = [mystery.clue1, mystery.clue2]
    world.facts["setting_place"] = world.setting.place

    world.para()
    world.say(
        f"{hero.id} wanted to solve it fast, but {partner.id} said, "
        f'"Let us look together. Two sets of eyes are better than one."'
    )
    hero.meters["focus"] = 1.0
    partner.meters["focus"] = 1.0

    world.say(
        f"So {hero.id} used {world.team.strength}, while {partner.id} used {world.team.helper_method}."
    )

    world.para()
    world.say(
        f"They followed the clues from the plaza to a hidden spot near the tower."
        if world.setting.city == "Neon City"
        else f"They followed the clues across {world.setting.place}, step by step."
    )

    solved = mystery.cause
    world.facts["cause"] = solved
    world.facts["solved_by"] = mystery.solved_by

    world.say(
        f"At last, they found the answer: {mystery.missing} had been lost because {solved}."
    )
    world.say(
        f"{hero.id} laughed, because the mystery was not too big for teamwork after all."
    )

    world.para()
    hero.memes["worry"] = 0.0
    partner.memes["worry"] = 0.0
    hero.memes["pride"] = 1.0
    partner.memes["pride"] = 1.0
    hero.memes["lesson_learned"] = 1.0
    partner.memes["lesson_learned"] = 1.0

    world.say(
        f"{hero.id} learned that a hero does not need to do everything alone."
    )
    world.say(
        f"{partner.id} learned that a mystery gets solved faster when friends share the job."
    )
    world.say(
        f"Together they returned {mystery.missing} and stood side by side, smiling under the city lights."
    )


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
def random_choice(rng: random.Random, items: list[str]) -> str:
    return rng.choice(items)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    city = args.city or random_choice(rng, list(SETTINGS))
    mystery = args.mystery or random_choice(rng, list(MYSTERIES))
    hero_role = args.hero_role or rng.choice(["girl", "boy"])
    partner_role = args.partner_role or ("boy" if hero_role == "girl" else "girl")
    hero = args.hero or random_choice(rng, [n for n in HERO_NAMES if n != args.partner])
    partner = args.partner or random_choice(rng, [n for n in PARTNER_NAMES if n != hero])

    if hero == partner:
        raise StoryError("The hero and partner must be different characters.")

    return StoryParams(
        city=city,
        place=SETTINGS[city].place,
        hero=hero,
        hero_role=hero_role,
        partner=partner,
        partner_role=partner_role,
        mystery=mystery,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a superhero story about {world.hero.id} and {world.partner.id} solving a mystery together.",
        f"Tell a child-friendly story in {world.setting.city} where teamwork helps find {world.mystery.missing}.",
        f"Write a short story with a lesson learned about sharing clues and working as a team.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.hero
    partner = world.partner
    mystery = world.mystery
    return [
        QAItem(
            question=f"What mystery did {hero.id} and {partner.id} need to solve?",
            answer=f"They needed to solve the mystery of {mystery.missing}.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice first?",
            answer=f"{hero.id} noticed {world.facts['clues'][0]}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn at the end?",
            answer="The hero learned that teamwork helps solve hard problems and that asking for help can be a strength.",
        ),
        QAItem(
            question=f"Where did the mystery happen?",
            answer=f"It happened at {world.setting.place} in {world.setting.city}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together and each person helps with part of the job.",
        ),
        QAItem(
            question="Why is a clue helpful in a mystery?",
            answer="A clue is helpful because it gives a hint that can lead to the answer.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="Learning a lesson means understanding something important that helps you act better next time.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    solve_mystery(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero mystery story world with teamwork and lesson learned.")
    ap.add_argument("--city", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--hero")
    ap.add_argument("--partner")
    ap.add_argument("--hero-role", choices=["girl", "boy"])
    ap.add_argument("--partner-role", choices=["girl", "boy"])
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


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world trace ---",
            f"setting.city={world.setting.city}",
            f"setting.place={world.setting.place}",
            f"hero.memes={world.hero.memes}",
            f"partner.memes={world.partner.memes}",
            f"facts={world.facts}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))

    if args.show_asp:
        print("#show not implemented for this world.")
        return
    if args.verify:
        print("OK: no ASP twin is defined for this world.")
        return
    if args.asp:
        print("This world does not expose an ASP mode.")
        return

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("neon_city", SETTINGS["neon_city"].place, "Milo", "boy", "June", "girl", "vanishing_map"),
            StoryParams("harbor", SETTINGS["harbor"].place, "Nia", "girl", "Ben", "boy", "lost_medal"),
            StoryParams("skyline", SETTINGS["skyline"].place, "Kai", "boy", "Maya", "girl", "silent_alarm"),
            StoryParams("suburb", SETTINGS["suburb"].place, "Zara", "girl", "Eli", "boy", "hidden_cookie"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            local_rng = random.Random(rng.randint(0, 2**31 - 1))
            params = resolve_params(args, local_rng)
            params.seed = args.seed
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
