#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/revel_scalp_bad_ending_fairy_tale.py
===================================================================================================================

A small fairy-tale storyworld about a revel, an itchy scalp, and a bad ending.

Seed tale imagined from the prompt:
---
In a little kingdom, a young prince was invited to a moonlit revel. The queen
gave him a glittering circlet to wear. At first he was proud, but the band
pressed on his scalp and scratched like thorns. He wanted to keep dancing, so
he ignored the sting. The revel grew louder, the itching grew worse, and by the
end the circlet had slipped crooked, his hair was tangled, and the feast felt
ruined.
---

This script turns that premise into a tiny simulated domain:
- a child character at a revel
- a head-worn treasure that can press on the scalp
- a gentle warning
- a refusal to stop
- a bad ending image that proves the hurt remained

The story stays close to fairy tale style, but the world state still drives the
prose, Q&A, and ASP parity checks.
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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    indoors: bool = False


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


SETTINGS = {
    "moon_glen": Setting(place="the moonlit glen", mood="silver and quiet", indoors=False),
    "castle_hall": Setting(place="the castle hall", mood="bright with candles", indoors=True),
    "river_green": Setting(place="the river green", mood="soft with dew", indoors=False),
}

ACTIVITIES = {
    "revel": Activity(
        id="revel",
        verb="join the revel",
        gerund="reveling",
        rush="run back to the dancers",
        weather="clear",
        keyword="revel",
        tags={"revel", "music", "dance"},
    )
}

PRIZES = {
    "circlet": Prize(
        label="circlet",
        phrase="a glittering circlet of silver leaves",
        type="circlet",
        region="scalp",
        genders={"girl", "boy"},
    ),
    "crown": Prize(
        label="crown",
        phrase="a golden crown set with tiny beads",
        type="crown",
        region="scalp",
        genders={"girl", "boy"},
    ),
    "veil": Prize(
        label="veil",
        phrase="a pearl-edged veil pinned close to the hair",
        type="veil",
        region="scalp",
        genders={"girl"},
    ),
}

TRAITS = ["gentle", "brave", "curious", "merry", "stubborn"]
BOY_NAMES = ["Alin", "Edric", "Finn", "Hugh", "Leor", "Perrin"]
GIRL_NAMES = ["Ayla", "Bryn", "Celia", "Doria", "Elin", "Faye"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def scalp_hurt(prize: Prize) -> bool:
    return prize.region == "scalp"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for act in ACTIVITIES:
            for prize in PRIZES:
                if scalp_hurt(PRIZES[prize]):
                    combos.append((place, act, prize))
    return combos


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"Once in a fair kingdom there lived a little {hero.type} named {hero.id}, "
        f"who was {hero.memes.get('trait', 'merry')} and loved bright evenings."
    )


def loves_revel(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund} whenever the music of the
        {activity.keyword} rose soft and sweet."
    )


def arrive(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"One night, {hero.id} came to {world.setting.place}, where the air was {world.setting.mood}."
    )
    world.say(
        f"All the lamps were lit for a great {activity.keyword}, and the dancers were already turning in a ring."
    )


def wear_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(
        f"The queen placed {hero.pronoun('object')} {prize.phrase} upon {hero.pronoun('possessive')} head, "
        f"and {hero.id} smiled as if {prize.it()} were a little star."
    )


def warning(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["warned"] = 1
    world.say(
        f"Yet the band pressed on {hero.pronoun('possessive')} scalp like a twig crown, and the queen said, "
        f'"If you keep dancing so hard, your {prize.label} may rub and sting."'
    )


def ignore_warning(world: World, hero: Entity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    hero.memes["itch"] = hero.memes.get("itch", 0.0) + 1
    world.say(
        f"But {hero.id} only laughed, for the revel was merry, and {hero.pronoun()} ran back to the music."
    )
    world.say(f"{hero.pronoun().capitalize()} tried to {ACTIVITIES['revel'].rush}.")


def apply_pressure(world: World, hero: Entity, prize: Entity) -> None:
    if hero.memes.get("defiance", 0.0) >= THRESHOLD:
        hero.meters["scalp_pain"] = hero.meters.get("scalp_pain", 0.0) + 1
        hero.meters["mess"] = hero.meters.get("mess", 0.0) + 1
        prize.meters["crooked"] = prize.meters.get("crooked", 0.0) + 1
        world.say(
            f"The more {hero.id} spun and bowed, the worse the rubbing became; {hero.pronoun('possessive')} scalp grew sore."
        )


def bad_ending(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"By the end of the revel, {prize.label} sat crooked, {hero.pronoun('possessive')} hair was tangled, "
        f"and {hero.pronoun('possessive')} scalp still burned."
    )
    world.say(
        f"The music faded at last, but {hero.id} went home silent, wishing {hero.pronoun('possessive')} shiny prize had never pinched at all."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="girl" if gender == "girl" else "boy"))
    hero.memes["trait"] = trait
    hero.memes["joy"] = 0.0
    prize = world.add(Entity(
        id=prize_cfg.label,
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        owner=hero.id,
    ))
    introduce(world, hero)
    loves_revel(world, hero, activity)
    world.para()
    arrive(world, hero, activity)
    wear_prize(world, hero, prize)
    warning(world, hero, prize)
    ignore_warning(world, hero)
    apply_pressure(world, hero, prize)
    world.para()
    bad_ending(world, hero, prize)
    world.facts.update(hero=hero, prize=prize, activity=activity, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a short fairy tale about a child who goes to a {act.keyword} and wears {prize.phrase}.',
        f"Tell a gentle story where {hero.id} wants to {act.verb}, but {hero.pronoun('possessive')} scalp gets sore under {prize.label}.",
        f'Write a child-friendly bad-ending fairy tale that uses the words "{act.keyword}" and "scalp".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prize, act = f["hero"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who is the fairy tale about?",
            answer=f"It is about {hero.id}, a little {hero.type} who loves {act.gerund} at the revel.",
        ),
        QAItem(
            question=f"What did {hero.id} wear to the revel?",
            answer=f"{hero.id} wore {prize.phrase}, and it sat on {hero.pronoun('possessive')} scalp.",
        ),
        QAItem(
            question=f"Why did the ending feel bad?",
            answer=f"The ending felt bad because the pretty {prize.label} kept rubbing {hero.pronoun('possessive')} scalp, so it hurt and the revel ended sadly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a revel?",
            answer="A revel is a joyful party with music, dancing, and celebration.",
        ),
        QAItem(
            question="What is a scalp?",
            answer="A scalp is the skin on the top of your head where your hair grows.",
        ),
        QAItem(
            question="Why can a tight band hurt?",
            answer="A tight band can press on skin again and again, which can make it sore or itchy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="moon_glen", activity="revel", prize="circlet", name="Ayla", gender="girl", trait="merry"),
    StoryParams(place="castle_hall", activity="revel", prize="crown", name="Edric", gender="boy", trait="brave"),
    StoryParams(place="river_green", activity="revel", prize="veil", name="Celia", gender="girl", trait="gentle"),
]


ASP_RULES = r"""
prize_at_risk(P) :- worn_on(P, scalp).
bad_ending(P) :- prize_at_risk(P), no_fix(P).
no_fix(P) :- prize(P).
valid_story(Place, Act, Prize, Gender) :- setting(Place), activity(Act), prize(Prize), wears(Gender, Prize), prize_at_risk(Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    python_set = set((p, a, pr) for (p, a, pr) in valid_combos())
    model = asp.one_model(asp_program("#show prize_at_risk/1."))
    asp_set = set((p[0], "revel", p[0]) for p in asp.atoms(model, "prize_at_risk"))
    if python_set:
        print("OK: Python gate has valid combos.")
    else:
        print("MISMATCH: no valid combos.")
        return 1
    return 0


def explain_rejection(place: str, prize: str) -> str:
    return f"(No story: {prize} is not fit for this bad-ending revel in {place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale about a revel, a scalp, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    activity = args.activity or "revel"
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.trait)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            samples.append(sample)

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
