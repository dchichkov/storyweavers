#!/usr/bin/env python3
"""
A small story world in a nursery-rhyme style:
a child, a parasol, bamboo, a twist, and a cautionary turn that still ends warmly.

Premise:
- A child loves a bright parasol.
- They go near bamboo in a breezy place.
- The parasol can tangle or bend in the wind.

Tension:
- The child wants to twirl the parasol near the bamboo.
- A careful grown-up warns that a careless twist could snag the parasol and poke a leaf.

Turn:
- The grown-up shows a safer way to use both hands and keep the parasol high and still.

Resolution:
- The child learns the caution, adjusts the twist, and the bamboo sways harmlessly while the parasol stays whole.

This world is deliberately compact and constraint-driven, with a reasonableness gate
and an ASP twin mirroring the Python legality checks.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bamboo grove"
    indoor: bool = False
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
    weather: str = ""
    keyword: str = ""
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.weather = ""
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "grove": Setting(place="the bamboo grove", affords={"twist", "walk"}),
    "path": Setting(place="the garden path", affords={"twist", "walk"}),
    "pond": Setting(place="the pond edge", affords={"twist", "walk"}),
}

ACTIVITIES = {
    "twist": Activity(
        id="twist",
        verb="twirl the parasol",
        gerund="twirling the parasol",
        rush="spin the parasol too fast",
        mess="snagged",
        soil="caught and bent",
        zone={"hands", "torso"},
        weather="breezy",
        keyword="twist",
        tags={"parasol", "bamboo", "wind"},
    ),
    "tap": Activity(
        id="tap",
        verb="tap the bamboo stalks",
        gerund="tapping bamboo",
        rush="reach out too far",
        mess="bruised",
        soil="sore and scuffed",
        zone={"hands"},
        weather="",
        keyword="bamboo",
        tags={"bamboo"},
    ),
}

PRIZES = {
    "parasol": Prize(
        label="parasol",
        phrase="a bright little parasol",
        type="parasol",
        region="hands",
        plural=False,
    ),
    "ribbon": Prize(
        label="ribbon",
        phrase="a red ribbon on a sleeve",
        type="ribbon",
        region="torso",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="two_hands",
        label="both hands",
        covers={"hands"},
        guards={"snagged", "bruised"},
        prep="hold it with both hands",
        tail="held the parasol steady",
    ),
    Gear(
        id="hat",
        label="a straw hat",
        covers={"torso"},
        guards={"bruised"},
        prep="set the parasol down and wear a straw hat",
        tail="let the bamboo sway in peace",
    ),
]

GIRL_NAMES = ["Mina", "Luna", "Tilly", "Nell", "Pip"]
BOY_NAMES = ["Robin", "Toby", "Finn", "Milo", "Otto"]
TRAITS = ["tiny", "cheerful", "curious", "careful", "spry"]


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
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} does not reach the {prize.region}, "
            f"so the parasol tale would have no honest cautionary twist.)"
        )
    return (
        f"(No story: nothing in the gear list reasonably fixes a {prize.label} "
        f"for {activity.gerund}, so the turn would not feel earned.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting) -> str:
    if setting.place == "the bamboo grove":
        return "The bamboo stood tall and green, and the leaves made a soft hiss."
    if setting.place == "the garden path":
        return "The path was neat and bright, with bamboo in a row like little reeds."
    return "The pond was still, and the bamboo nodded near the water."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "tiny"), "tiny")
    world.say(f"{hero.id} was a {trait} child who liked little rhymes and bright things.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label}, bright as a song in the sun.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One breezy day,"
    world.say(f"{day} {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(setting_detail(world.setting))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(f"{hero.id} wanted to {activity.verb}, with a skip and a grin.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    if not prize_at_risk(activity, prize):
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"Careful now," {parent.pronoun("possessive")} parent said. '
        f'"A quick little twist may leave your {prize.label} {activity.soil}."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0) + 1
    world.say(f"But {hero.id} still tried to {activity.rush}, with a hop and a skip.")


def twist_turn(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["nervous"] = hero.memes.get("nervous", 0) + 1
    world.say(f"{parent.id} reached out and steadied the parasol tip, slow as a lullaby.")


def offer_fix(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    world.say(
        f'"Let us {gear.prep}," said {parent.id}. "Then you may still {activity.verb}, '
        f"only kindly and slow."'
    )
    return gear


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["conflict"] = 0
    world.say(f"{hero.id} nodded and took a deep breath.")
    world.say(
        f"They {gear.tail}. Soon {hero.id} was {activity.gerund}, and the {prize.label} stayed safe and bright."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["tiny", trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the grown-up"))
    prize = world.add(Entity(
        id=prize_cfg.label,
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
    ))

    introduce(world, hero)
    loves_prize(world, hero, prize)
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    twist_turn(world, hero, parent, activity)
    world.para()
    gear = offer_fix(world, parent, hero, activity, prize)
    if gear:
        accept(world, hero, parent, activity, prize, gear)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        'Write a short nursery-rhyme-like story about a child, a parasol, and bamboo.',
        f"Tell a cautionary tale where {hero.id} wants to {act.verb} near {world.setting.place} "
        f"and {parent.id} helps with a safer twist.",
        f'Write a gentle rhyme that includes the words "{prize.label}" and "bamboo".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} love to carry in the bamboo grove?",
            answer=f"{hero.id} loved {hero.pronoun('possessive')} {prize.label}, a bright little parasol.",
        ),
        QAItem(
            question=f"Why did the grown-up warn {hero.id} about the twist?",
            answer=(
                f"The grown-up warned {hero.id} because a fast {act.gerund} could leave the "
                f"{prize.label} {act.soil}."
            ),
        ),
        QAItem(
            question=f"What safer way helped {hero.id} enjoy the bamboo without trouble?",
            answer=(
                f"They used both hands and kept the parasol steady, so {hero.id} could still "
                f"{act.verb} without ruining the {prize.label}."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bamboo?",
            answer="Bamboo is a tall, fast-growing plant with hollow stalks that can sway in the wind.",
        ),
        QAItem(
            question="What is a parasol for?",
            answer="A parasol is a light umbrella used to shade someone from sun or drizzle.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
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
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
        for g in sorted(prize.genders):
            lines.append(asp.fact("wears", g, pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for r in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, r))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
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
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    if args.gender and args.gender not in prize.genders:
        raise StoryError(f"(No story: {prize.label} is not a typical {args.gender}'s item here.)")
    name = args.name or choose_name(gender, rng)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.parent,
        params.trait,
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
TRAITS = ["careful", "curious", "cheerful", "spry", "gentle"]
CURATED = [
    StoryParams(place="grove", activity="twist", prize="parasol", name="Mina", gender="girl", parent="mother", trait="careful"),
    StoryParams(place="path", activity="twist", prize="parasol", name="Robin", gender="boy", parent="father", trait="curious"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about parasol, bamboo, twist, and caution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
