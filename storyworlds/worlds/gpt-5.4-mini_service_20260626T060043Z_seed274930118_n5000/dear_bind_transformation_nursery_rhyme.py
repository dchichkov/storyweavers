#!/usr/bin/env python3
"""
storyworlds/worlds/dear_bind_transformation_nursery_rhyme.py
=============================================================

A small nursery-rhyme story world about a dear little helper who binds simple
things and sees them transform into something lovely.

Seed tale:
---
Dear little Pip found a plain straw bundle in the garden. Pip wanted to bind it
with a ribbon and turn it into a crown for the tiny parade. But the wind kept
tugging the loose ends apart, and the bundle looked shabby and sad. Pip's kind
nan smiled, helped bind the straw snugly, and the plain bundle transformed into
a bright crown that stayed together all day.

Story shape:
- setup: a dear character loves a small making activity
- tension: loose materials threaten the result
- turn: a helper offers a better binding method
- resolution: the bound thing transforms and the ending image proves it

This world keeps a classical physical/emotional state model and an ASP twin for
reasonableness checks and verification.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "nan", "lady"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
    breeze: bool = False


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    zone: set[str]
    weather: str
    keyword: str
    soil: str
    transformation: str
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
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.weather: str = ""
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
        return any((g.id in self.entities and region in g.tags) for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"bind"}, breeze=True),
    "nursery": Setting(place="the nursery", indoor=True, affords={"bind"}, breeze=False),
    "meadow": Setting(place="the meadow", indoor=False, affords={"bind"}, breeze=True),
}

ACTIVITIES = {
    "bind": Activity(
        id="bind",
        verb="bind the loose bundle",
        gerund="binding the loose bundle",
        mess="untidy",
        zone={"hands", "torso"},
        weather="breezy",
        keyword="bind",
        soil="too loose and untidy",
        transformation="bright and snug",
        tags={"bind", "transform"},
    ),
}

PRIZES = {
    "bundle": Prize(
        label="bundle",
        phrase="a plain straw bundle",
        type="bundle",
        region="hands",
    ),
    "ribbon": Prize(
        label="ribbon",
        phrase="a long red ribbon",
        type="ribbon",
        region="hands",
        plural=False,
    ),
    "crown": Prize(
        label="crown",
        phrase="a little parade crown",
        type="crown",
        region="head",
    ),
}

GEAR = [
    Gear(
        id="soft_string",
        label="soft string",
        covers={"hands"},
        guards={"untidy"},
        prep="use soft string first",
        tail="tied the bundle with soft string",
    ),
    Gear(
        id="neat_ribbon",
        label="a neat ribbon",
        covers={"hands"},
        guards={"untidy"},
        prep="wrap it with a neat ribbon first",
        tail="wrapped the bundle with a neat ribbon",
    ),
]

GIRL_NAMES = ["Pip", "Mina", "Luna", "Bess", "Nora"]
BOY_NAMES = ["Ben", "Tom", "Toby", "Finn", "Sam"]
TRAITS = ["dear", "gentle", "careful", "cheery", "tiny"]

# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------


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
    return prize.region in activity.zone or prize.label == "bundle"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region == "hands":
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, aid, pid))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not have a compatible way to keep "
        f"{prize.label} snug and safe.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: {PRIZES[prize_id].label} does not fit a {gender} here; try {ok}.)"


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "soiled": bool(prize.meters.get("untidy", 0) >= 1),
        "transform": bool(prize.memes.get("transform", 0) >= 1),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["hope"] = actor.memes.get("hope", 0) + 1
    for item in world.entities.values():
        if item.worn_by == actor.id and item.region in world.zone and not item.meters.get("protected", 0):
            item.meters[activity.mess] = item.meters.get(activity.mess, 0) + 1
            item.meters["untidy"] = item.meters.get("untidy", 0) + 1
    if narrate:
        world.say(f"The little one began {activity.gerund} in a soft, breezy way.")


def introduce(world: World, hero: Entity) -> None:
    world.say(f"Dear little {hero.id} was a {hero.type} who loved a tidy tune and a tidy task.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.keyword}, and the day felt light and merry.")


def wants(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(f"{hero.id} wanted to {activity.verb}, so the plain {prize.label} would not stay plain for long.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"Dear one," {parent.pronoun("subject")} said, "if you {activity.verb}, the {prize.label} may get '
        f"{activity.soil}."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["wobble"] = hero.memes.get("wobble", 0) + 1
    world.say(f"But {hero.id} still twirled and tried to {activity.verb}, with a little wobble in the air.")


def resolve(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    helper = world.add(Entity(id=gear.id, kind="thing", type="gear", label=gear.label, tags=set(gear.covers)))
    helper.worn_by = hero.id
    world.say(f"Then {parent.id} smiled and said, \"Let's {gear.prep}, dear child.\"")
    return gear


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    hero.memes["wobble"] = 0
    prize.memes["transform"] = prize.memes.get("transform", 0) + 1
    prize.meters["protected"] = prize.meters.get("protected", 0) + 1
    world.say(
        f"They {gear.tail}, and the plain {prize.label} transformed into something {activity.transformation}."
    )
    world.say(
        f"In the end, {hero.id} was {activity.gerund}, and the {prize.label} stayed bright and snug."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Pip",
    hero_type: str = "girl",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "grandmother",
) -> World:
    world = World(setting)
    world.weather = activity.weather if not setting.indoor else ""

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={},
        memes={"love": 0, "hope": 0, "joy": 0},
        tags=set(hero_traits or []),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="nan"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_activity(world, hero, activity)
    world.say(f"{hero.id} had {prize.phrase}, and {prize.label} looked very plain indeed.")
    wants(world, hero, activity, prize)

    world.para()
    world.say(f"One day in {setting.place}, the breeze was little but lively.")
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)

    world.para()
    gear = resolve(world, parent, hero, activity, prize)
    if gear is not None:
        accept(world, parent, hero, activity, prize, gear)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=gear is not None,
        conflict=hero.memes.get("wobble", 0) > 0,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short nursery rhyme about a dear little {hero.type} named {hero.id} who wants to {act.verb}.',
        f"Tell a gentle story where {hero.id} and {hero.pronoun('possessive')} {parent.type} bind a plain {prize.label} until it transforms.",
        f'Write a simple rhyme that includes the words "{act.keyword}", "dear", and "bind".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"What did dear {hero.id} want to do in {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, because the little making task seemed fun and bright.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label} worried because the {prize.label} could get {act.soil} if it stayed loose.",
        ),
        QAItem(
            question=f"What changed after they used something to bind the {prize.label}?",
            answer=f"The plain {prize.label} transformed into something {act.transformation}, and it stayed snug.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question="How did the helper make the change work?",
                answer="The helper used soft string and careful hands, so the loose bundle could stay together and become lovely.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bind mean?",
            answer="Bind means to tie or fasten things together so they stay together.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a new form or becomes quite different.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], ""]
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), splashes(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Sampling, parsing, emit
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about dear binding and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["grandmother", "grandfather"])
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
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait], params.parent)
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="garden", activity="bind", prize="bundle", name="Pip", gender="girl", parent="grandmother", trait="dear"),
    StoryParams(place="meadow", activity="bind", prize="bundle", name="Ben", gender="boy", parent="grandfather", trait="gentle"),
    StoryParams(place="nursery", activity="bind", prize="bundle", name="Luna", gender="girl", parent="grandmother", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print("  ", combo)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
