#!/usr/bin/env python3
"""
storyworlds/worlds/collision_cautionary_myth.py
================================================

A small mythic storyworld about a warning, a near-collision, and a wiser turn.

Seed tale imagined from the prompt:
---
Long ago, the village of Ember Hill kept a golden bell on a stone arch above the river.
A proud child loved to race a bright wheel down the slope, but the elders said the
wheel could collide with the bell and break the blessing for the whole village.

The child did not want to stop. Then the grandmother remembered an old rope track
that could guide the wheel safely around the arch. The child agreed, the wheel rang
softly on the rope path, and the bell stayed whole while the villagers praised the
careful choice.

Domain shape:
- A hero wants to do a risky, joyous motion through a sacred place.
- A revered prize object is at risk of collision.
- An elder foresees the harm and warns.
- The child resists, tension rises, then a protective or redirecting solution is found.
- The ending proves the world changed: the prize remains whole, and the hero learns caution.

This script follows the storyworld contract:
- standalone stdlib script
- StoryParams and registries
- generate/emit/main
- QA, JSON, trace, ASP twin, and verification support
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "elder"}
        male = {"boy", "father", "dad", "man", "grandfather", "elder"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the village road"
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
    weather: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in {"crash"}:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("damage", item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["broken"] += 1
                out.append(f"{actor.id}'s {item.label} cracked from the collision.")
    return out


def _r_grief(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["broken"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("grief", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.memes["worry"] += 1
        out.append(f"That would bring worry to the keeper of the relic.")
    return out


def _r_alarm(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["warning_heard"] < THRESHOLD or actor.memes["stubborn"] < THRESHOLD:
            continue
        sig = ("alarm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] += 1
        return ["__alarm__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule("damage", "physical", _r_damage),
    Rule("grief", "social", _r_grief),
    Rule("alarm", "social", _r_alarm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__alarm__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_collision(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "broken": bool(prize and prize.meters["broken"] >= THRESHOLD),
        "worry": sum(e.memes["worry"] for e in sim.characters()),
    }


def activity_delight(activity: Activity) -> str:
    return {
        "wheel": "the bright spin of the wheel looked like a small sun rolling home",
        "drum": "the deep beat of the drum made the air feel awake",
        "torch": "the torchlight shivered like a little star caught in a hand",
    }.get(activity.id, "it made the old road feel alive")


def setting_detail(setting: Setting, activity: Activity) -> str:
    return f"{setting.place.capitalize()} stood still and solemn, as if it remembered old promises."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "young"), "")
    world.say(f"Long ago, {hero.id} was a young {trait} {hero.type} who listened for omens in the wind.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved to {activity.gerund}; {activity_delight(activity)}.")


def prizes(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"{hero.id}'s {parent.label or parent.type} kept {hero.pronoun('possessive')} {prize.label} in trust.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} treasured {hero.pronoun('possessive')} {prize.label} and carried {prize.it()} with pride.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label or parent.type} came to {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent.label or parent.type} lifted a warning hand.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_collision(world, hero, activity, prize.id)
    if not pred["broken"]:
        return False
    world.facts["predicted_broken"] = True
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'"If you {activity.verb}, your {prize.label} will meet the stone and crack," '
        f"{hero.pronoun('possessive')} {parent.label or parent.type} said. "
        f'"A broken thing can wound a whole house."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["stubborn"] += 1
    world.say(f"{hero.id} frowned, for the wish to hurry still burned in {hero.pronoun('possessive')} chest.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}.")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["warning_heard"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.pronoun('possessive')} {parent.label or parent.type} caught {hero.pronoun('possessive')} hand and said, "
        f'"The wise path is slower, but it does not bring sorrow."'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["fear"] >= THRESHOLD or hero.memes["stubborn"] >= THRESHOLD:
        world.say(f"{hero.id} stood silent, with pride and fear tugging on the same thread.")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_collision(world, hero, activity, prize.id)["broken"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"At last {hero.pronoun('possessive')} {parent.label or parent.type} pointed to {gear_def.label} and said, "
        f'"We can still {activity.verb}, if we take the rope path first."'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["stubborn"] = 0.0
    world.say(f"{hero.id}'s face softened, and {hero.id} bowed to {hero.pronoun('possessive')} {parent.label or parent.type}.")
    world.say(
        f"They took the {gear_def.tail}, and soon {hero.id} was {activity.gerund}, "
        f"{hero.pronoun('possessive')} {prize.label} still whole, while the old bell kept its clear voice."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Lina",
    hero_type: str = "girl",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "grandmother",
) -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["young"] + (hero_traits or ["bold", "restless"]),
    ))
    parent = world.add(Entity(id="Elder", kind="character", type=parent_type, label="the elder"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_activity(world, hero, activity)
    prizes(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def,
        conflict=hero.memes["warning_heard"] >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "village": Setting(place="the village road", indoor=False, affords={"wheel", "drum"}),
    "shrine": Setting(place="the shrine steps", indoor=False, affords={"wheel", "torch"}),
    "bridge": Setting(place="the river bridge", indoor=False, affords={"wheel", "torch"}),
}

ACTIVITIES = {
    "wheel": Activity(
        id="wheel",
        verb="race the wheel downhill",
        gerund="racing the wheel downhill",
        rush="run after the wheel",
        mess="crash",
        soil="broken at the stones",
        zone={"feet", "legs", "torso"},
        weather="",
        keyword="collision",
        tags={"collision", "stone"},
    ),
    "drum": Activity(
        id="drum",
        verb="beat the drum in the procession",
        gerund="beating the drum in the procession",
        rush="strike the drum faster",
        mess="crash",
        soil="shaken by the clash",
        zone={"hands", "torso"},
        weather="",
        keyword="collision",
        tags={"drum", "sound"},
    ),
    "torch": Activity(
        id="torch",
        verb="carry the torch near the arch",
        gerund="carrying the torch near the arch",
        rush="hurry toward the arch",
        mess="crash",
        soil="singed by the clash",
        zone={"hands", "torso"},
        weather="",
        keyword="collision",
        tags={"fire", "collision"},
    ),
}

GEAR = [
    Gear(
        id="rope",
        label="an old rope track",
        covers={"legs", "torso"},
        guards={"crash"},
        prep="take the rope track",
        tail="rope track around the safe curve",
        plural=False,
    ),
    Gear(
        id="gloves",
        label="stiff gloves",
        covers={"hands"},
        guards={"crash"},
        prep="put on stiff gloves first",
        tail="stiff gloves on and the gentler route in mind",
        plural=True,
    ),
]

PRIZES = {
    "bell": Prize(
        label="golden bell",
        phrase="a golden bell from the shrine arch",
        type="bell",
        region="torso",
    ),
    "crown": Prize(
        label="river crown",
        phrase="a river crown of hammered bronze",
        type="crown",
        region="torso",
    ),
    "lantern": Prize(
        label="lantern",
        phrase="a painted lantern",
        type="lantern",
        region="hands",
    ),
}

HERO_NAMES = ["Lina", "Mara", "Tavi", "Sera", "Niko", "Ari"]
TRAITS = ["bold", "restless", "dreamy", "proud", "quick-footed"]

KNOWLEDGE = {
    "collision": [(
        "What is a collision?",
        "A collision is when two things hit each other with force."
    )],
    "stone": [(
        "Why can a stone path be dangerous for a fast wheel?",
        "A stone path can be dangerous because a wheel can bounce, wobble, or smash if it hits a hard edge."
    )],
    "drum": [(
        "What does a drum do in a procession?",
        "A drum gives a strong beat that helps people march together."
    )],
    "fire": [(
        "Why should a torch be carried carefully?",
        "A torch should be carried carefully because flame can burn things that are too close."
    )],
}
KNOWLEDGE_ORDER = ["collision", "stone", "drum", "fire"]


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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a myth-like cautionary story for a young child about "{act.keyword}" and a safe choice.',
        f"Tell a short legend where {hero.id} wants to {act.verb} near {world.setting.place} but {hero.pronoun('possessive')} {parent.label} fears for {prize.phrase}.",
        f'Write a gentle myth in which the word "{act.keyword}" appears and the ending shows a wiser path.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the myth about when {hero.id} goes to {world.setting.place} with {hero.pronoun('possessive')} {prize.label}?",
            answer=f"It is about {hero.id}, a young {hero.type}, and {hero.pronoun('possessive')} {parent.label} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the elder warned about the {prize.label}?",
            answer=f"{hero.id} wanted to {act.verb}. That made trouble likely because the {prize.label} could meet the stones.",
        ),
        QAItem(
            question=f"Why did the elder warn {hero.id} about the journey?",
            answer=f"The elder warned because the elder could see that if {hero.id} tried to {act.verb}, the {prize.label} might be hurt by a collision.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help the child avoid the collision?",
            answer=f"They used {gear.label} so {hero.id} could {act.verb} without ruining the {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end of the story?",
            answer=f"{hero.id} felt calmer and happier, because the safe route let {hero.id} play and keep the {prize.label} whole.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="village", activity="wheel", prize="bell", name="Lina", gender="girl", parent="grandmother", trait="bold"),
    StoryParams(place="shrine", activity="torch", prize="lantern", name="Mara", gender="girl", parent="grandmother", trait="dreamy"),
    StoryParams(place="bridge", activity="wheel", prize="crown", name="Niko", gender="boy", parent="grandfather", trait="restless"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"the {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not threaten {noun}, so there is no honest caution to tell.)"
    return f"(No story: nothing in the gear catalog can safely guard {noun} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: {PRIZES[prize_id].label} is not a typical {gender}'s prize here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
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
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a cautionary myth of collision and wiser paths.")
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

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait, "young"], params.parent)
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
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
