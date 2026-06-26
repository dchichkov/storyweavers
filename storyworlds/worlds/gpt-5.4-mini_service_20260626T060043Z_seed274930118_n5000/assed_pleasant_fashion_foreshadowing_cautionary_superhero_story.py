#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/assed_pleasant_fashion_foreshadowing_cautionary_superhero_story.py
====================================================================================================================

A small superhero storyworld with foreshadowing and cautionary tension.

Premise:
- A young hero loves fashion and wants to wear a flashy outfit in public.
- A mentor notices a clue that the outfit is not safe for the mission.
- The hero ignores the warning at first, then learns why the caution mattered.
- A safer costume lets the hero help others and still look stylish.

This world keeps the story concrete: costumes have physical coverage, weather
can damage them, and emotions shift from pride to worry to relief.
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
# Domain model
# ---------------------------------------------------------------------------
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the city square"
    weather: str = "windy"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    soil: str
    zone: set[str]
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Outfit:
    id: str
    label: str
    phrase: str
    region: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    mission: str
    outfit: str
    hero_name: str
    hero_kind: str
    mentor_kind: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.weather: str = setting.weather

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(it.protective and region in it.covers for it in self.worn_items(actor))

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
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.weather = self.weather
        return c


# ---------------------------------------------------------------------------
# World content
# ---------------------------------------------------------------------------
SETTINGS = {
    "city": Setting(place="the city square", weather="windy", affords={"rescue", "parade"}),
    "dock": Setting(place="the harbor dock", weather="stormy", affords={"rescue"}),
    "museum": Setting(place="the museum steps", weather="rainy", affords={"parade", "rescue"}),
}

MISSIONS = {
    "rescue": Mission(
        id="rescue",
        verb="help the crowd",
        gerund="helping the crowd",
        rush="dash into the wind",
        danger="a loose cape could tangle on a railing",
        soil="swept dirty",
        zone={"torso", "legs"},
        weather="windy",
        keyword="rescue",
        tags={"wind", "danger"},
    ),
    "parade": Mission(
        id="parade",
        verb="wave to the crowd",
        gerund="waving to the crowd",
        rush="run onto the parade route",
        danger="bright confetti could stain a fancy suit",
        soil="spotted",
        zone={"torso"},
        weather="rainy",
        keyword="fashion",
        tags={"fashion", "rain"},
    ),
}

OUTFITS = {
    "cape": Outfit(
        id="cape",
        label="cape",
        phrase="a bright fashion cape with gold trim",
        region="torso",
        covers={"torso"},
        guards={"wind"},
        prep="put on the cape first",
        tail="slipped off the cape and chose the safer gear",
    ),
    "boots": Outfit(
        id="boots",
        label="boots",
        phrase="sturdy boots with strong soles",
        region="legs",
        covers={"legs"},
        guards={"rain"},
        prep="pull on the boots first",
        tail="buttoned the boots tight and hurried out",
        plural=True,
    ),
    "mask": Outfit(
        id="mask",
        label="mask",
        phrase="a shiny mask for the hero costume",
        region="torso",
        covers={"torso"},
        guards={"confetti"},
        prep="wear the mask first",
        tail="tied on the mask and went to help",
    ),
}

TRAITS = ["pleasant", "brave", "kind", "careful", "cheerful"]
HERO_NAMES = ["Nova", "Milo", "Tara", "Iris", "Pax", "Juno"]
KINDS = ["girl", "boy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mission is risky if the weather can damage the outfit in the mission zone.
risky(M, O) :- mission(M), outfit(O), mission_weather(M, W), guards(O, W),
               mission_zone(M, R), outfit_region(O, R).

% A fix is valid if the outfit guards the weather and covers the risky region.
valid_fix(M, O) :- risky(M, O), mission(M), outfit(O).

valid_story(Place, M, O, Kind) :- setting(Place), affords(Place, M), valid_fix(M, O), hero_kind(Kind).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", sid, m))
            lines.append(asp.fact("mission", m))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mission_weather", mid, m.weather))
        for z in sorted(m.zone):
            lines.append(asp.fact("mission_zone", mid, z))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    for oid, o in OUTFITS.items():
        lines.append(asp.fact("outfit", oid))
        lines.append(asp.fact("outfit_region", oid, o.region))
        for g in sorted(o.guards):
            lines.append(asp.fact("guards", oid, g))
        for c in sorted(o.covers):
            lines.append(asp.fact("covers", oid, c))
    for k in KINDS:
        lines.append(asp.fact("hero_kind", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def prize_at_risk(mission: Mission, outfit: Outfit) -> bool:
    return outfit.region in mission.zone and any(g in mission.tags for g in outfit.guards)


def select_outfit(mission: Mission, outfit: Outfit) -> bool:
    return prize_at_risk(mission, outfit)


def build_story(world: World, hero: Entity, mentor: Entity, mission: Mission, outfit: Outfit) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} young hero who loved fashion almost as much as helping people."
    )
    world.say(
        f"{hero.id} had found {outfit.phrase}, and the bright style made {hero.pronoun()} smile."
    )
    world.say(
        f"On the way to {world.setting.place}, {hero.id} noticed a small clue: the clouds were heavy, and {mission.danger}."
    )
    world.para()
    world.say(
        f"{hero.id} wanted to {mission.verb} right away, but {mentor.id} lifted a careful hand."
    )
    world.say(
        f"\"That outfit looks splendid, but {mission.danger},\" {mentor.pronoun()} said. "
        f"\"Let's think before we rush.\""
    )
    hero.memes["wish"] = hero.memes.get("wish", 0) + 1
    mentor.memes["warning"] = mentor.memes.get("warning", 0) + 1
    world.para()
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0) + 1
    world.say(
        f"{hero.id} tried to {mission.rush}, because {hero.pronoun()} still wanted to look stylish and be the first to help."
    )
    world.say(
        f"Then {hero.id} saw a sign on the wall: wet confetti from the festival had already ruined one costume earlier that day."
    )
    safe = outfit
    safe.worn_by = hero.id
    world.say(
        f"{mentor.id} smiled and offered a safer choice: \"How about we {safe.prep}?\""
    )
    world.say(
        f"{hero.id} nodded, changed into the safer gear, and went back out to {mission.verb}."
    )
    world.say(
        f"This time {hero.id} kept {hero.pronoun('possessive')} outfit neat, and the crowd cheered while {hero.id} moved quickly and carefully."
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    mission: Mission = f["mission"]
    outfit: Outfit = f["outfit"]
    return [
        QAItem(
            question=f"Why did {hero.id} pause before {mission.verb}?",
            answer=f"{hero.id} saw a clue that the weather could spoil {hero.pronoun('possessive')} {outfit.label}, so {mentor.id} warned {hero.pronoun('object')} to think first.",
        ),
        QAItem(
            question=f"What did {mentor.id} worry would happen to the {outfit.label}?",
            answer=f"{mentor.id} worried that {mission.danger}, so the fancy outfit might be ruined during the mission.",
        ),
        QAItem(
            question=f"How did {hero.id} finish the story?",
            answer=f"{hero.id} changed into safer gear, then {hero.pronoun()} went out and {mission.verb} while keeping the costume neat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fashion?",
            answer="Fashion is the style of clothes people choose to wear. It can be bright, neat, fancy, or simple.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue that something important might happen later.",
        ),
        QAItem(
            question="What makes a warning cautionary?",
            answer="A cautionary warning helps someone avoid trouble by showing what could go wrong if they are not careful.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    mission: Mission = f["mission"]
    return [
        f'Write a short superhero story for a young child about "{hero.id}" and the theme "{mission.keyword}".',
        f"Tell a cautionary story where {hero.id} loves fashion, but a foreshadowed clue helps {hero.pronoun('object')} choose safer gear.",
        f"Write a gentle superhero tale with a bright outfit, a warning, and a happy rescue ending.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== story questions =="]
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        parts.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid in setting.affords:
            mission = MISSIONS[mid]
            for oid, outfit in OUTFITS.items():
                if select_outfit(mission, outfit):
                    out.append((place, mid, oid))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mission and args.outfit:
        if not select_outfit(MISSIONS[args.mission], OUTFITS[args.outfit]):
            raise StoryError("That outfit would not realistically protect the hero on this mission.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mission is None or c[1] == args.mission)
              and (args.outfit is None or c[2] == args.outfit)]
    if not combos:
        raise StoryError("No valid story matches those options.")
    place, mission, outfit = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        mission=mission,
        outfit=outfit,
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_kind=args.kind or rng.choice(KINDS),
        mentor_kind=args.mentor or "adult",
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_kind,
        traits=[params.trait, "fashionable"],
        memes={},
        meters={},
    ))
    mentor = world.add(Entity(
        id="Mentor",
        kind="character",
        type=params.mentor_kind,
        traits=["careful"],
        memes={},
        meters={},
    ))
    mission = MISSIONS[params.mission]
    outfit = OUTFITS[params.outfit]
    world.add(Entity(
        id=outfit.id,
        type="outfit",
        label=outfit.label,
        phrase=outfit.phrase,
        owner=hero.id,
        caretaker=mentor.id,
        region=outfit.region,
        protective=True,
        covers=set(outfit.covers),
        plural=outfit.plural,
        worn_by=hero.id,
    ))
    build_story(world, hero, mentor, mission, outfit)
    world.facts = {"hero": hero, "mentor": mentor, "mission": mission, "outfit": outfit}
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
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_fix/2."))
    return sorted(set(asp.atoms(model, "valid_fix")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set((m, o) for _, m, o in valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP and Python agree on {len(python_set)} valid mission/outfit pairs.")
        return 0
    print("Mismatch between ASP and Python.")
    print("only python:", sorted(python_set - asp_set))
    print("only asp:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld with foreshadowing and cautionary tension.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--outfit", choices=OUTFITS)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--mentor", choices=["adult"])
    ap.add_argument("--trait", choices=TRAITS)
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


CURATED = [
    StoryParams("city", "rescue", "cape", "Nova", "girl", "adult", "pleasant"),
    StoryParams("museum", "parade", "boots", "Milo", "boy", "adult", "cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} valid mission/outfit pairs:")
        for t in triples:
            print(t)
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.mission} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
