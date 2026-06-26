#!/usr/bin/env python3
"""
storyworlds/worlds/incense_fright_community_garden_cautionary_inner_monologue.py
==============================================================================

A small superhero-style storyworld in a community garden where a cautious
hero notices incense, feels fright, thinks through the risk, and chooses a
safer, kinder action.

Seed premise:
- A child with a heroic streak visits a community garden.
- Someone lights incense near the garden.
- The smoke startles the hero and makes the scene feel unsafe.
- The hero's inner monologue weighs what might happen.
- A cautionary response and a practical fix resolve the moment.

The world is intentionally narrow: we prefer one strong, readable premise over
many weak variations.
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
    kind: str = "thing"   # character | thing
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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the community garden"


@dataclass
class Threat:
    id: str
    label: str
    smell: str
    cause: str
    caution: str


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    protects_from: set[str]
    helps_with: set[str]
    action: str
    outcome: str


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def hero_title(hero: Entity) -> str:
    return {
        "girl": "young heroine",
        "boy": "young hero",
    }.get(hero.type, "young hero")


def inner_monologue(hero: Entity, threat: Threat) -> str:
    return (
        f"{hero.pronoun('subject').capitalize()} thought, "
        f"\"{threat.cause.capitalize()} can make people feel jumpy, "
        f"but if I stay calm I can figure out the safest move.\""
    )


def caution_line(hero: Entity, threat: Threat) -> str:
    return (
        f"{hero.pronoun('subject').capitalize()} told {hero.pronoun('object')}self, "
        f"\"Don't rush in. The smoke might bother the bees and scare the little kids.\""
    )


def select_gear(threat: Threat) -> Gear:
    for gear in GEAR:
        if threat.id in gear.protects_from:
            return gear
    raise StoryError("No safe gear exists for this threat.")


def tell(setting: Setting, threat: Threat, gear: Gear, hero_name: str, hero_type: str,
         caretaker_type: str = "mother", seed: Optional[int] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"courage": 1.0},
        memes={"fright": 0.0, "resolve": 0.0, "care": 0.0},
    ))
    caretaker = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=caretaker_type,
        label="the caretaker",
        meters={"patience": 1.0},
        memes={"calm": 1.0},
    ))
    incense = world.add(Entity(
        id="Incense",
        kind="thing",
        type="incense",
        label="incense stick",
        phrase="a fragrant incense stick",
        owner="Caretaker",
        caretaker="Caretaker",
    ))
    smoke = world.add(Entity(
        id="Smoke",
        kind="thing",
        type="smoke",
        label="smoke",
        phrase="soft curling smoke",
    ))
    gear_ent = world.add(Entity(
        id=gear.id,
        kind="thing",
        type=gear.id,
        label=gear.label,
        phrase=gear.phrase,
        owner=hero.id,
        caretaker=caretaker.id,
        plural=False,
    ))
    gear_ent.meters["ready"] = 1.0

    world.say(
        f"In {setting.place}, {hero.id} was a {hero_title(hero)} who loved helping "
        f"keep every bed neat and every path clear."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} had a bright cape in {hero.pronoun('possessive')} mind, "
        f"and {hero.pronoun('subject')} watched over the garden like a tiny champion."
    )

    world.para()
    world.say(
        f"Near the bean trellis, someone lit {incense.phrase}. "
        f"The scent drifted through {setting.place}, and the smoke curled between the tomato leaves."
    )
    hero.memes["fright"] += 1.0
    world.say(
        f"{hero.id} felt a quick fright in {hero.meters.get('courage', 0):.0f} heartbeat, "
        f"because {threat.cause} could make a calm place feel strange."
    )
    world.say(inner_monologue(hero, threat))
    world.say(caution_line(hero, threat))

    world.para()
    world.say(
        f"{hero.id} took one careful step back and listened instead of hurrying."
    )
    if threat.id in gear.protects_from:
        hero.memes["resolve"] += 1.0
        world.say(
            f"{hero.pronoun('subject').capitalize()} pulled on {gear_ent.label} and covered {hero.pronoun('possessive')} nose."
        )
        world.say(
            f"That helped {hero.id} stay steady while {gear.action}, and the garden air felt easier again."
        )

    world.para()
    hero.memes["fright"] = 0.0
    hero.memes["care"] += 1.0
    caretaker.memes["calm"] += 1.0
    world.say(
        f"{hero.id} pointed the incense away from the seedlings and asked the grown-up to move it near the walkway instead."
    )
    world.say(
        f"Soon the smoke drifted somewhere safer, the bees stayed busy, and the little superhero smiled because caution had saved the day."
    )

    world.facts.update(
        hero=hero,
        caretaker=caretaker,
        incense=incense,
        smoke=smoke,
        gear=gear_ent,
        threat=threat,
        setting=setting,
        seed=seed,
    )
    return world


SETTINGS = {
    "community_garden": Setting(place="the community garden"),
}

THREATS = {
    "incense": Threat(
        id="incense",
        label="incense",
        smell="strong",
        cause="the incense smoke",
        caution="keep the smoke away from the flowers and bees",
    ),
}

GEAR = [
    Gear(
        id="mask",
        label="a soft cloth mask",
        phrase="a soft cloth mask",
        protects_from={"incense"},
        helps_with={"smoke"},
        action="holding the mask over {hero}'s nose".format(hero="their face"),
        outcome="safer breathing",
    ),
    Gear(
        id="fan",
        label="a little hand fan",
        phrase="a little hand fan",
        protects_from={"incense"},
        helps_with={"smoke"},
        action="fanning the smoke away",
        outcome="clearer air",
    ),
]

HERO_NAMES = ["Maya", "Tari", "Niko", "Ari", "Lena", "Jo", "Ravi", "Kira"]
HERO_TYPES = ["girl", "boy"]
CAREGIVER_TYPES = ["mother", "father"]

CURATED = [
    ("Maya", "girl", "mother"),
    ("Niko", "boy", "father"),
    ("Ari", "girl", "father"),
]


@dataclass
class StoryParams:
    place: str
    threat: str
    gear: str
    name: str
    gender: str
    caretaker: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for threat_id in THREATS:
            for gear in GEAR:
                if threat_id in gear.protects_from:
                    combos.append((place, threat_id, gear.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style cautionary inner-monologue storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--gear", choices=[g.id for g in GEAR])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--caretaker", choices=CAREGIVER_TYPES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.threat is None or c[1] == args.threat)
              and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, threat, gear = rng.choice(combos)
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    caretaker = args.caretaker or rng.choice(CAREGIVER_TYPES)
    return StoryParams(place=place, threat=threat, gear=gear, name=name, gender=gender, caretaker=caretaker)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    threat = f["threat"]
    return [
        f'Write a short superhero story set in {f["setting"].place} where {hero.id} notices {threat.label} and thinks carefully before acting.',
        f"Tell a cautionary story with an inner monologue where {hero.id} feels fright from {threat.cause} but chooses a safer path.",
        f"Write a child-friendly superhero story about keeping {threat.label} away from the garden beds.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    caretaker = f["caretaker"]
    threat = f["threat"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel frightened in the garden?",
            answer=f"{hero.id} felt frightened because {threat.cause} drifted through the community garden and made the air feel strange.",
        ),
        QAItem(
            question=f"What did {hero.id} think about before acting?",
            answer=f"{hero.id} thought about how the smoke could bother the bees and scare little kids, so {hero.pronoun('subject')} decided to be careful.",
        ),
        QAItem(
            question=f"How did {hero.id} help fix the problem?",
            answer=f"{hero.id} used {gear.label} and asked the grown-up to move the incense somewhere safer, which helped the garden stay calm.",
        ),
        QAItem(
            question=f"Who helped {hero.id} stay calm?",
            answer=f"The caretaker helped by staying nearby, and {hero.id} also calmed down after taking a careful breath and thinking it through.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the incense smoke was moved away from the plants, {hero.id} felt brave again, and the garden was safer.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "incense": [
        QAItem(
            question="What is incense?",
            answer="Incense is a stick or bundle that gives off a strong smell when it burns, and the smoke can drift through the air.",
        )
    ],
    "fright": [
        QAItem(
            question="What is fright?",
            answer="Fright is a sudden scared feeling that can make your heart jump and your body want to step back.",
        )
    ],
    "garden": [
        QAItem(
            question="What grows in a community garden?",
            answer="A community garden can grow vegetables, herbs, flowers, and other plants that neighbors help care for together.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["incense"] + WORLD_KNOWLEDGE["fright"] + WORLD_KNOWLEDGE["garden"]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        THREATS[params.threat],
        next(g for g in GEAR if g.id == params.gear),
        params.name,
        params.gender,
        params.caretaker,
        params.seed,
    )
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


ASP_RULES = r"""
place(community_garden).
threat(incense).
gear(mask).
gear(fan).
protects_from(mask, incense).
protects_from(fan, incense).
valid(Place, Threat, Gear) :- place(Place), threat(Threat), gear(Gear), protects_from(Gear, Threat).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in THREATS:
        lines.append(asp.fact("threat", t))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for x in sorted(g.protects_from):
            lines.append(asp.fact("protects_from", g.id, x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
    return 1


def explain_rejection() -> str:
    return "(No story: this world only tells one cautious community-garden incense story, and every explicit choice must fit that premise.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (name, gender, caretaker) in enumerate(CURATED):
            params = StoryParams(place="community_garden", threat="incense", gear="mask",
                                 name=name, gender=gender, caretaker=caretaker, seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: incense in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
