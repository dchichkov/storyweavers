#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sting_profession_teamwork_sharing_conflict_adventure.py
===============================================================================================================

A small adventure storyworld about a child, a profession, and a risky sting.
The simulated premise is simple: a curious child visits a working place where
a professional helper is doing careful work around bees. If someone rushes, the
bees may sting. If they slow down, share the right gear, and work together,
the job becomes safe and satisfying.

The world uses:
- meters: physical state such as sting, tired, carried, safe, clean
- memes: emotional/social state such as curiosity, fear, trust, teamwork, sharing,
  conflict, pride

The story is intentionally constraint-checked: only reasonable combinations of
place, activity, and protective gear are generated.
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

THRESHOLD = 1.0

REGIONS = {"hands", "arms", "face", "torso"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["sting", "safe", "carried", "tired"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "fear", "trust", "teamwork", "sharing", "conflict", "pride"]:
            self.memes.setdefault(k, 0.0)

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
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    zone: set[str] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_sting(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["sting"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("sting", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["sting"] += 1
            actor.memes["fear"] += 1
            out.append(f"{actor.id}'s {item.label} got too close to the bees and was stung.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["fear"] < THRESHOLD or actor.memes["sharing"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        out.append(f"That made {actor.id} cross and upset for a moment.")
    return out


CAUSAL_RULES = [_r_sting, _r_conflict]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, gear: Gear) -> bool:
    return bool(activity.zone & gear.covers)


def select_gear(activity: Activity) -> Optional[Gear]:
    for gear in GEAR:
        if activity.keyword in gear.guards or "sting" in gear.guards:
            if prize_at_risk(activity, gear):
                return gear
    return None


def predict(world: World, actor: Entity, activity: Activity, gear: Gear) -> bool:
    sim = world.copy()
    sim.zone = set(activity.zone)
    actor2 = sim.get(actor.id)
    actor2.meters["sting"] += 1
    propagate(sim, narrate=False)
    return any(e.meters["sting"] >= THRESHOLD for e in sim.entities.values())


@dataclass
class StoryParams:
    place: str
    activity: str
    gear: str
    name: str
    gender: str
    profession: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "apiary": Setting(place="the apiary", indoor=False, affords={"hive_help", "honey_move"}),
    "garden": Setting(place="the garden", indoor=False, affords={"hive_help"}),
    "orchard": Setting(place="the orchard", indoor=False, affords={"honey_move"}),
}

ACTIVITIES = {
    "hive_help": Activity(
        id="hive_help",
        verb="help at the hive",
        gerund="helping at the hive",
        rush="run up to the hive",
        risk="sting",
        zone={"hands", "face"},
        keyword="sting",
        tags={"bee", "sting", "hive", "profession"},
    ),
    "honey_move": Activity(
        id="honey_move",
        verb="move the honey frames",
        gerund="moving the honey frames",
        rush="grab the frames alone",
        risk="sting",
        zone={"hands", "arms"},
        keyword="profession",
        tags={"bee", "sting", "honey", "profession"},
    ),
}

GEAR = [
    Gear(
        id="veil",
        label="a mesh veil",
        covers={"face"},
        guards={"sting"},
        prep="put on the mesh veil",
        tail="slipped on the mesh veil first",
    ),
    Gear(
        id="gloves",
        label="soft gloves",
        covers={"hands"},
        guards={"sting"},
        prep="share the soft gloves",
        tail="shared the soft gloves and took turns",
        plural=True,
    ),
    Gear(
        id="suit",
        label="a white beekeeping suit",
        covers={"hands", "face", "torso"},
        guards={"sting"},
        prep="wear the white beekeeping suit",
        tail="wore the white beekeeping suit and worked slowly",
    ),
]

PROFESSIONS = ["beekeeper", "gardener", "ranger", "honey seller"]
HELPERS = ["mom", "dad", "Aunt Jo", "Uncle Ben"]
GIRL_NAMES = ["Maya", "Luna", "Nia", "Sara", "Ivy"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Finn", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            if select_gear(act) is None:
                continue
            for gear in GEAR:
                if prize_at_risk(act, gear):
                    combos.append((place, act_id, gear.id))
    return combos


def introduce(world: World, hero: Entity, pro: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved adventure and new things to learn."
    )
    world.say(
        f"{hero.id} met {pro.id}, a {pro.type} who worked as a {pro.label}."
    )


def setup(world: World, hero: Entity, pro: Entity, activity: Activity, gear: Gear) -> None:
    hero.memes["curiosity"] += 1
    pro.memes["trust"] += 1
    world.say(
        f"At {world.setting.place}, {pro.id} was busy with {activity.gerund}, and the bees hummed all around."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {pro.id} warned that a rushed hand could get a sting."
    )


def warn(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["fear"] += 1
    world.say(
        f'"Slow hands are safest," {hero.pronoun("possessive")} helper said. '
        f'"If you {activity.rush}, the bees may sting."'
    )


def conflict(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["conflict"] += 1
    hero.memes["sharing"] += 1
    world.say(
        f"{hero.id} wanted to rush anyway, but that did not feel brave once the bees buzzed closer."
    )
    world.say(
        f"{hero.id} stopped, frowned, and took a breath instead of {activity.rush}."
    )


def teamwork(world: World, hero: Entity, pro: Entity, activity: Activity, gear: Gear) -> None:
    hero.memes["teamwork"] += 1
    hero.memes["sharing"] += 1
    pro.memes["teamwork"] += 1
    world.zone = set(activity.zone)
    world.say(
        f"Then {hero.id} and {pro.id} worked together."
    )
    world.say(
        f"They chose to {gear.prep}, and they moved slowly so the bees stayed calm."
    )


def resolution(world: World, hero: Entity, pro: Entity, activity: Activity, gear: Gear) -> None:
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1)
    hero.memes["pride"] += 1
    pro.memes["trust"] += 1
    world.say(
        f"With {gear.label}, {hero.id} could {activity.verb} safely."
    )
    world.say(
        f"By the end, {hero.id} felt proud, {pro.id} smiled, and the job was finished together."
    )


def tell(setting: Setting, activity: Activity, gear: Gear, name: str, gender: str, profession: str, helper: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        traits=["little", "curious", "brave"],
    ))
    pro = world.add(Entity(
        id=helper,
        kind="character",
        type="adult",
        label=profession,
        traits=["patient", "careful"],
    ))
    world.add(Entity(
        id="gear",
        type="thing",
        label=gear.label,
        phrase=gear.label,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    introduce(world, hero, pro)
    world.para()
    setup(world, hero, pro, activity, gear)
    warn(world, hero, activity)
    conflict(world, hero, activity)
    teamwork(world, hero, pro, activity, gear)
    resolution(world, hero, pro, activity, gear)
    world.facts.update(hero=hero, pro=pro, activity=activity, gear=gear, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    pro: Entity = f["pro"]
    act: Activity = f["activity"]
    return [
        f'Write a short adventure story for a young child about {hero.id} helping a {pro.label} at {world.setting.place}.',
        f'Tell a gentle story where {hero.id} wants to {act.verb}, but teamwork and sharing keep everyone safe from a sting.',
        f'Write a child-friendly adventure story that includes the word "{act.keyword}" and ends with a happy job done together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    pro: Entity = f["pro"]
    act: Activity = f["activity"]
    gear: Gear = f["gear"]
    return [
        QAItem(
            question=f"Who went on the adventure at {world.setting.place}?",
            answer=f"{hero.id} went there with {pro.id}, who was working as a {pro.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"{hero.id} wanted to {act.verb}, because the day felt exciting and full of adventure.",
        ),
        QAItem(
            question=f"Why did {pro.id} worry about a sting?",
            answer=f"{pro.id} worried that a rushed hand could get too close to the bees, so someone might get a sting.",
        ),
        QAItem(
            question=f"How did {hero.id} and {pro.id} fix the problem?",
            answer=f"They used {gear.label} and worked together slowly, which kept the bees calm and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beekeeper?",
            answer="A beekeeper is a person whose job is to care for bees and help collect honey safely.",
        ),
        QAItem(
            question="Why can bees sting?",
            answer="Bees sting when they feel scared or need to protect their home, so people move gently around them.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together instead of trying to do everything alone.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means taking turns or using things together kindly, like sharing safety gear.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(A,G) :- activity(A), gear(G), zone(A,R), covers(G,R), guards(G,sting).
valid(P,A,G) :- setting(P), affords(P,A), risk(A,G).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("riskword", aid, a.risk))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for gid, g in [(g.id, g) for g in GEAR]:
        lines.append(asp.fact("gear", gid))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", gid, r))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", gid, m))
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
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


@dataclass
class StoryParams:
    place: str
    activity: str
    gear: str
    name: str
    gender: str
    profession: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about a sting-risk profession and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gear", choices=[g.id for g in GEAR])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--profession", choices=PROFESSIONS)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, gear = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    profession = args.profession or rng.choice(PROFESSIONS)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, activity=activity, gear=gear, name=name, gender=gender, profession=profession, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        next(g for g in GEAR if g.id == params.gear),
        params.name,
        params.gender,
        params.profession,
        params.helper,
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            gear = select_gear(act)
            if gear is not None:
                combos.append((place, act_id, gear.id))
    return combos


def select_gear(activity: Activity) -> Optional[Gear]:
    for gear in GEAR:
        if activity.keyword in gear.guards and prize_at_risk(activity, gear):
            return gear
    return None


def explain_rejection(activity: Activity, gear: Gear) -> str:
    return f"(No story: {gear.label} does not fit the risky parts of {activity.verb}.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, gear) combos:\n")
        for place, act, gear in combos:
            print(f"  {place:10} {act:12} {gear}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, act, gear in valid_combos():
            params = StoryParams(
                place=place,
                activity=act,
                gear=gear,
                name="Maya",
                gender="girl",
                profession="beekeeper",
                helper="Aunt Jo",
            )
            samples.append(generate(params))
    else:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
