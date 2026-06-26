#!/usr/bin/env python3
"""
Space Adventure: a small, happy-ending storyworld about a walk, a lost feta,
and a gentle rescue in a tiny starport.

A child goes on a space walk with a snack, the snack gets at risk, the crew
notices, and the ending image proves the snack and friendship were both saved.
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

    def __post_init__(self) -> None:
        for k in ("dust", "drift", "hunger", "tired", "joy", "worry", "relief", "care"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "pilot"}
        male = {"boy", "father", "man", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Station:
    place: str = "the starport"
    indoor: bool = True
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
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


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
    def __init__(self, setting: Station) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


THRESHOLD = 1.0


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if actor.meters["dust"] >= THRESHOLD and item.region in world.zone and not world.covered(actor, item.region):
                sig = ("soil", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["dust"] += 1
                item.memes["worry"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} picked up stardust.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["joy"] >= THRESHOLD and e.memes["worry"] >= THRESHOLD:
            sig = ("relief", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["relief"] += 1
            out.append(f"{e.id} felt relieved.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_soil, _r_relief):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = copy_world(world)
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters["dust"] >= THRESHOLD}


def copy_world(world: World) -> World:
    import copy
    clone = World(world.setting)
    clone.entities = copy.deepcopy(world.entities)
    clone.fired = set(world.fired)
    clone.zone = set(world.zone)
    return clone


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"{world.setting.place} cannot host {activity.id}.")
    world.zone = set(activity.zone)
    actor.meters["dust"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def tell(world: World, activity: Activity, prize: Prize, hero_name: str, parent_type: str) -> World:
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom"))
    prize_ent = world.add(Entity(
        id="prize",
        type=prize.type,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize.region,
        plural=prize.plural,
    ))
    hero.memes["love"] = 1
    prize_ent.worn_by = hero.id

    world.say(f"{hero.id} was a small space traveler who loved quiet walks between the ships.")
    world.say(f"One day, {hero.id}'s mom bought {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} loved {prize_ent.label} and wore {prize_ent.it()} like a treasure.")

    world.para()
    world.say(f"At the starport, {hero.id} wanted to {activity.verb}.")
    world.say(f"The corridor lights blinked softly, and the air smelled clean and cold.")

    if predict_mess(world, hero, activity, prize_ent.id)["soiled"]:
        hero.memes["worry"] += 1
        world.say(f'"If you go now, your {prize_ent.label} will get {activity.soil}," mom said.')
        world.say(f"{hero.id} frowned and tried to {activity.rush}.")
        hero.memes["stubborn"] += 1
        world.say(f"But mom held up a hand and gently guided {hero.id} back.")
        gear = select_gear(activity, prize_ent)
        if gear is None:
            raise StoryError("No safe gear exists for this story.")
        safe = world.add(Entity(
            id=gear.id, type="gear", label=gear.label, owner=hero.id,
            caretaker=parent.id, protective=True, covers=set(gear.covers), plural=gear.plural
        ))
        safe.worn_by = hero.id
        world.say(f'"How about we {gear.prep} first?" mom asked.')
        world.say(f"{hero.id} nodded and hugged {hero.pronoun('possessive')} mom.")
        hero.memes["joy"] += 1
        hero.memes["worry"] = 0
        do_activity(world, hero, activity, narrate=True)
        world.para()
        world.say(f"They {gear.tail}, and then {hero.id} went {activity.gerund} with a happy smile.")
        world.say(f"{prize_ent.label} stayed clean, and mom laughed beside {hero.id}.")
    else:
        do_activity(world, hero, activity, narrate=True)

    world.facts.update(hero=hero, parent=parent, prize=prize_ent, activity=activity, gear=gear if 'gear' in locals() else None)
    return world


SETTINGS = {
    "starport": Station(place="the starport", indoor=True, affords={"walk"}),
    "moonwalk": Station(place="the moon dock", indoor=False, affords={"walk"}),
}

ACTIVITIES = {
    "walk": Activity(
        id="walk",
        verb="take a moon walk",
        gerund="walking by the silver rails",
        rush="run toward the open hatch",
        mess="dust",
        soil="dusty",
        zone={"feet"},
        keyword="walk",
        tags={"walk", "space", "dust"},
    ),
}

PRIZES = {
    "feta": Prize(
        label="feta",
        phrase="a little wrapped block of feta",
        type="cheese",
        region="torso",
        plural=False,
    )
}

GEAR = [
    Gear(
        id="boots",
        label="moon boots",
        covers={"feet"},
        guards={"dust"},
        prep="put on the moon boots",
        tail="walked back through the hatch in their moon boots",
    ),
    Gear(
        id="satchel",
        label="a sealed snack satchel",
        covers={"torso"},
        guards={"dust"},
        prep="put the feta in a sealed snack satchel",
        tail="carried the feta in the sealed snack satchel",
    ),
]

GIRL_NAMES = ["Luna", "Mina", "Nova", "Iris"]
PARENT_TYPES = ["mother", "father"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    parent: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a short happy space adventure about a child named {hero.id} and a {prize.label} on a {act.keyword}.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but keeps the feta safe.",
        f'Write a child-friendly space story with the words "{prize.label}" and "{act.keyword}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who wanted to {act.verb} in the story?",
            answer=f"{hero.id} wanted to {act.verb}, because the walk looked exciting under the ship lights.",
        ),
        QAItem(
            question=f"What did mom buy for {hero.id}?",
            answer=f"Mom bought {hero.id} {prize.phrase}, and {hero.id} loved it right away.",
        ),
        QAItem(
            question=f"Why did mom worry about the {prize.label}?",
            answer=f"Mom worried because a moon walk would make the {prize.label} get {act.soil}.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How was the {prize.label} kept safe?",
            answer=f"They used {gear.label} first, so {hero.id} could {act.verb} without ruining the {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and relieved, because the walk happened and the feta stayed clean.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is feta?",
            answer="Feta is a soft, salty cheese that people often keep wrapped or chilled.",
        ),
        QAItem(
            question="What is a moon walk?",
            answer="A moon walk is a careful walk in a place with low gravity or space gear, like on a moon dock.",
        ),
        QAItem(
            question="Why do boots help in dusty places?",
            answer="Boots help because they keep dust off your feet and make it easier to walk safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="starport", activity="walk", prize="feta", name="Luna", parent="mother", seed=None),
    StoryParams(place="moonwalk", activity="walk", prize="feta", name="Nova", parent="father", seed=None),
]


def explain_rejection() -> str:
    return "No story: this tiny world only supports a careful walk that can end happily."


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny happy-ending space adventure storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=GIRL_NAMES)
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    activity = args.activity or "walk"
    prize = args.prize or "feta"
    if activity != "walk" or prize != "feta":
        raise StoryError(explain_rejection())
    name = args.name or rng.choice(GIRL_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, parent=parent, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    world = tell(world, ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.parent)
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
place(starport). place(moonwalk).
activity(walk). prize(feta).
affords(starport,walk). affords(moonwalk,walk).
worn_on(feta,torso).
splashes(walk,feet).
mess_of(walk,dust).
guards(boots,dust). covers(boots,feet).
guards(satchel,dust). covers(satchel,torso).
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        for a in SETTINGS[pid].affords:
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in act.zone:
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in g.guards:
            lines.append(asp.fact("guards", g.id, m))
        for c in g.covers:
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, a, pr) for p in SETTINGS for a in SETTINGS[p].affords for pr in PRIZES if prize_at_risk(ACTIVITIES[a], PRIZES[pr]) and select_gear(ACTIVITIES[a], PRIZES[pr])}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < args.n * 20:
            p = resolve_params(args, random.Random(base_seed + i))
            sample = generate(p)
            if sample.story not in seen:
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
