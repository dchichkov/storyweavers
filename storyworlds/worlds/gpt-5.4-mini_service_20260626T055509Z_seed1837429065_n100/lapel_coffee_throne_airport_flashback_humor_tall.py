#!/usr/bin/env python3
"""
storyworlds/worlds/lapel_coffee_throne_airport_flashback_humor_tall.py
======================================================================

A small standalone storyworld with an airport, a coffee mishap, a lapel,
a throne-like chair, a flashback, and a tall-tale comic voice.

The setup is intentionally simple and classical:
- A tall traveler arrives at an airport.
- A beloved travel coat has a bright lapel that can be stained by coffee.
- A funny airport "throne" in the lounge invites a grand pause.
- A flashback to an old family saying changes how the traveler sees the moment.
- A compatible fix keeps the lapel clean and lets the day end in laughter.

The story engine models physical meters and emotional memes, uses a reasonableness
gate for valid stories, and includes an inline ASP twin for parity checks.
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
# Core domain model
# ---------------------------------------------------------------------------
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
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "stained": 0.0, "tired": 0.0, "delight": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "humor": 0.0, "worry": 0.0, "nostalgia": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the airport"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
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


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
SETTINGS = {
    "airport": Setting(place="the airport", indoors=True, affords={"coffee"}),
}

ACTIVITIES = {
    "coffee": Activity(
        id="coffee",
        verb="sip coffee",
        gerund="sipping coffee",
        rush="dash toward the coffee cart",
        mess="stained",
        soil="spilled coffee on it",
        zone={"torso"},
        keyword="coffee",
        tags={"coffee", "wet", "humor"},
    ),
}

PRIZES = {
    "coat": Prize(
        label="lapel coat",
        phrase="a tall blue travel coat with a bright lapel",
        type="coat",
        region="torso",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="napkin",
        label="a big paper napkin",
        covers={"torso"},
        guards={"stained"},
        prep="fold a big paper napkin over the lapel first",
        tail="folded the napkin into place",
    ),
]

GIRL_NAMES = ["Mia", "Nora", "Ada", "Zoe"]
BOY_NAMES = ["Finn", "Leo", "Owen", "Noah"]
TRAITS = ["tall", "towering", "cheerful", "lively"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} traveler so tall the airport mirrors had to look up to {hero.pronoun('object')}."
    )


def setup(world: World, hero: Entity, guide: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} loved the airport because every hallway looked like a parade route."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {guide.label} had bought {hero.pronoun('object')} {prize.phrase} for the trip."
    )
    world.say(
        f"The bright lapel on that coat stood up straight like it was trying to salute the ceiling."
    )


def flashback(world: World, hero: Entity) -> None:
    hero.memes["nostalgia"] += 1
    hero.memes["humor"] += 1
    world.say(
        f"That reminded {hero.id} of a flashback from last summer, when {hero.id}'s grandpa said every airport chair could be a throne if a child sat in it with enough hope."
    )
    world.say(
        f"{hero.id} had laughed so hard then that {hero.id} nearly dropped a cookie into {hero.pronoun('possessive')} socks."
    )


def want(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 0.2
    world.say(
        f"{hero.id} wanted to {activity.verb}, but the coffee cart smelled so strong it felt like a tiny storm had moved indoors."
    )


def warn(world: World, guide: Entity, hero: Entity, prize: Entity, activity: Activity) -> None:
    if not prize_at_risk(activity, prize):
        return
    guide.memes["worry"] += 1
    world.say(
        f'"Careful," {guide.id} said. "If that coffee touches your lapel, your coat will look like it lost a dance with a mud pie."'
    )


def spill_and_fix(world: World, hero: Entity, guide: Entity, prize: Entity, activity: Activity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    helper = world.add(Entity(
        id=gear.id,
        type="thing",
        label=gear.label,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
        owner=hero.id,
        caretaker=guide.id,
    ))
    helper.worn_by = hero.id
    world.say(
        f"{guide.id} smiled and said, \"First the paper napkin, then the coffee.\""
    )
    world.say(
        f"They {gear.tail}, and the little shield covered the lapel just in time."
    )
    hero.memes["joy"] += 1
    hero.memes["humor"] += 1
    return gear


def throne_scene(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"After that, {hero.id} marched to a giant lounge chair that looked exactly like a throne made for a very polite giant."
    )
    world.say(
        f"{hero.id} sat down with {hero.pronoun('possessive')} clean lapel shining, sipped the coffee carefully, and grinned as if the whole airport had applauded."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Gus", hero_type: str = "boy",
         parent_type: str = "aunt", hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=hero_traits or ["tall", "spirited"],
    ))
    guide = world.add(Entity(id="Guide", kind="character", type=parent_type, label="aunt"))
    prize = world.add(Entity(
        id="coat",
        type="coat",
        label="coat",
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=guide.id,
        region=prize_cfg.region,
    ))

    intro(world, hero)
    setup(world, hero, guide, prize, activity)
    world.para()
    want(world, hero, activity)
    warn(world, guide, hero, prize, activity)
    flashback(world, hero)
    gear = spill_and_fix(world, hero, guide, prize, activity)
    world.para()
    throne_scene(world, hero, prize, activity)

    world.facts.update(
        hero=hero,
        guide=guide,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=gear is not None,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, guide, prize, activity = f["hero"], f["guide"], f["prize"], f["activity"]
    return [
        'Write a short tall-tale story set in an airport about a lapel, coffee, and a throne-like chair.',
        f"Tell a funny flashback story where {hero.id} wants to {activity.verb} at {world.setting.place} but {guide.id} worries about {prize.phrase}.",
        f"Write a child-friendly airport story with a tall hero, a coffee mishap, and a grand chair that feels like a throne.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, prize, activity = f["hero"], f["guide"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Where does the story take place?",
            answer=f"It takes place at {world.setting.place}, where the hallways, carts, and seats make the whole day feel busy and bright.",
        ),
        QAItem(
            question=f"What was {hero.id} wearing?",
            answer=f"{hero.id} was wearing {prize.phrase}, and the bright lapel was the part that needed the most care.",
        ),
        QAItem(
            question=f"Why did {guide.id} worry about the coffee?",
            answer=f"{guide.id} worried because if {hero.id} kept {activity.gerund}, the coffee could spill onto the lapel and stain the coat.",
        ),
        QAItem(
            question=f"What old memory came back to {hero.id} in the middle of the story?",
            answer=f"{hero.id} remembered a flashback about grandpa calling an airport chair a throne if a child sat in it with enough hope.",
        ),
    ]
    if f.get("gear"):
        qa.append(
            QAItem(
                question=f"How did {guide.id} help keep the lapel clean?",
                answer=f"{guide.id} helped by using a big paper napkin, which covered the lapel so {hero.id} could enjoy the coffee without making a mess.",
            )
        )
    qa.append(
        QAItem(
            question=f"What did the throne-like chair add to the ending?",
            answer=f"It gave the ending a funny, grand feeling, because the airport chair looked like a throne and made {hero.id} feel as proud as a tiny king of the terminal.",
        )
    )
    return qa


KNOWLEDGE = {
    "coffee": [
        QAItem(
            question="What is coffee?",
            answer="Coffee is a warm drink made from roasted beans, and grown-ups often sip it to feel awake and ready.",
        )
    ],
    "lapel": [
        QAItem(
            question="What is a lapel?",
            answer="A lapel is the folded front part of a jacket or coat that sits near the collar.",
        )
    ],
    "throne": [
        QAItem(
            question="What is a throne?",
            answer="A throne is a special chair for a king or queen, often made to look grand and important.",
        )
    ],
    "airport": [
        QAItem(
            question="What happens at an airport?",
            answer="At an airport, people buy tickets, carry bags, wait for flights, and walk through long halls to reach airplanes.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [item for key in ["airport", "coffee", "lapel", "throne"] for item in KNOWLEDGE[key]]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for r in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, r))
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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale airport storyworld with lapel, coffee, and throne humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["aunt", "uncle"])
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            raise StoryError("No valid airport story matches those explicit choices.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, [params.trait])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place="airport", activity="coffee", prize="coat", name="Gus", gender="boy", parent="aunt", trait="tall"))]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
