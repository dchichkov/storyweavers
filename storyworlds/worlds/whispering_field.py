#!/usr/bin/env python3
"""
whispering_field.py
===================

Story world built from the generated seed:

    words: echo, icy field, whispering storm, whispering tent, syrup
    features: Inner Monologue, Happy Ending, Quest
    style: Heartwarming

A child wants to run across an icy field, the parent predicts the risk to a
cherished item and proposes a concrete, region-aware compromise.
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
MESS_KINDS = {"slip", "wet", "cold"}
REGIONS = {"feet", "legs", "torso"}


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str]


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
        clone = copy.deepcopy(self)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_scrape(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("scrape", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                if mess == "slip":
                    out.append(f"{item.label} would get scraped and scraped again by ice.")
                else:
                    out.append(f"{item.label} would get marked and damp.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("workload", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.meters["workload"] += 1
        out.append(f"That would mean extra cleaning work for {caretaker.label}.")
    return out


def _r_grab_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed_by"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    Rule("scrape", "physical", _r_scrape),
    Rule("workload", "physical", _r_workload),
    Rule("grab_conflict", "social", _r_grab_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                if narrate:
                    produced.extend([g for g in got if g != "__conflict__"])
    if narrate:
        for sentence in produced:
            world.say(sentence)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def introduce(world: World, hero: Entity) -> None:
    traits = ", ".join(t for t in hero.traits[:2])
    if traits:
        traits = f"{traits} "
    world.say(f"Once upon a time, there was {hero.pronoun('subject')} little {hero.type} named {hero.id}, and {hero.pronoun()} was {traits}curious.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    where = "inside" if world.setting.indoor else "outside"
    world.say(f"{hero.pronoun().capitalize()} loved being {where} and {activity.gerund}.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One day, {parent.id} bought {hero.pronoun('possessive')} new {prize.phrase} "
        f"for a special outing."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} new {prize.label} "
        f"and wore {prize.it} for every adventure."
    )


def arrive(world: World, hero: Entity, parent: Entity) -> None:
    loc = "were in" if world.setting.indoor else "went to"
    storm = "One evening, " if world.weather else "One day, "
    world.say(
        f"{storm}{hero.id} and {parent.id} {loc} {world.setting.place}."
    )


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent.label_word} said no."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"if you {activity.verb}, your {prize.label} will get {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then {parent.id} will have to clean it."
    world.say(f'"{clause}," said {parent.id}.')
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} did not listen and tried to {activity.rush}.")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But {parent.id} grabbed {hero.pronoun("object")} by the hand and said, '
        f'"This field can be wild. You need to resist the urge to {activity.verb} today."'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] < THRESHOLD:
        return
    world.say(
        f'{hero.id} pouted and crossed {hero.pronoun("possessive")} arms. '
        f'"But I really want to {activity.verb}!" {hero.pronoun()} said.'
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, PRIZES[prize.id])
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        kind="thing",
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    gear.region = "feet"  # metadata for debug, not used by mechanics

    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None

    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled. '
        f'"How about we {gear_def.prep}, then we can {activity.verb} together?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f'"I like this better," {hero.id} said. {hero.pronoun().capitalize()} hugged {parent.id} and '
        f'followed after they {gear_def.tail}.'
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Nora",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["curious"] + (hero_traits or ["brave"]),
    ))
    parent = world.add(Entity(
        id="Parent" if parent_type == "mother" else "Guardian",
        kind="character",
        type=parent_type,
        label=f"the {parent_type}",
    ))
    prize = world.add(Entity(
        id=prize_cfg.label,
        kind="thing",
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
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent)
    wants(world, hero, parent, activity)
    warned = warn(world, parent, hero, activity, prize)
    if warned:
        defy(world, hero, activity)
        grab_hand(world, parent, hero, activity)

    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        prize_cfg=prize_cfg,
        gear=gear_def,
        warned=warned,
        conflict=hero.memes["conflict"] >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "frozen_field": Setting("the frozen field near Whispering Hill", False, {"ice_run", "storm_dash"}),
    "pine_camp": Setting("the pine camp with a warm whispering tent", False, {"ice_run", "storm_dash"}),
    "play_tent": Setting("a wooden play tent at home", True, {"ice_run"}),
}

ACTIVITIES = {
    "ice_run": Activity(
        "ice_run",
        "run across the icy field",
        "running across the icy field",
        "run across the field",
        "slip",
        "scraped and dusty with ice",
        {"feet", "legs"},
        "cold",
        keyword="icy field",
        tags={"ice", "field", "slip"},
    ),
    "storm_dash": Activity(
        "storm_dash",
        "run through the whispering storm",
        "running through the whispering storm",
        "dash through the wind",
        "wet",
        "soaked and shivering",
        {"torso", "legs"},
        "storm",
        keyword="whispering storm",
        tags={"storm", "wet", "cold"},
    ),
)

GEAR = [
    Gear(
        "ice_cleats",
        "a pair of ice cleats",
        {"feet"},
        {"slip"},
        "put on the ice cleats",
        "went to put on the ice cleats",
        plural=True,
    ),
    Gear(
        "wind_shell",
        "a windproof shell",
        {"torso", "legs"},
        {"wet", "cold"},
        "put on the wind shell",
        "walked to the wind shell",
    ),
    Gear(
        "waterproof_coat",
        "a waterproof coat",
        {"torso", "legs"},
        {"wet"},
        "wear the waterproof coat",
        "went to get the waterproof coat",
    ),
]

PRIZES = {
    "boots": Prize("boots", "shiny black boots", "boots", "feet", plural=True),
    "scarf": Prize("scarf", "a soft blue scarf", "scarf", "torso", genders={"girl"}),
    "jacket": Prize("jacket", "a new winter jacket", "jacket", "torso"),
}

BOY_NAMES = ["Kai", "Noah", "Liam", "Milo", "Rory"]
GIRL_NAMES = ["Nora", "Mia", "Lena", "Ivy", "Rose"]
TRAITS = ["brave", "restless", "curious", "gentle", "playful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return sorted(combos)


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


KNOWLEDGE = {
    "ice": [("What is ice?", "Ice is water that has frozen and become hard and slippery when it gets very cold.")],
    "slip": [("Why can ice make you fall?", "Ice is slippery, so feet can lose traction and you can slide or skid.")],
    "wet": [("Why does wet clothing feel cold?", "Wet fabric lets heat escape from the body faster, which can make you feel chilled.")],
    "storm": [("Why can a storm feel scary in the cold?", "Wind and fast-changing sounds can feel loud and sharp, so adults ask children to stay careful in a storm.")],
    "cold": [("Why are storms colder on exposed fields?", "Cold air and wind carry heat away quickly when you are outside.")],
    "field": [("Why does a field get slippery in winter?", "When snow and water freeze, the ground can become slick.")],
    "boots": [("What are ice cleats for?", "They give your boots better grip so your feet are less likely to slip.")],
    "wind_shell": [("Why wear a wind shell?", "A wind shell helps block wind and limits how quickly your body gets cold.")],
    "waterproof_coat": [("Why can a waterproof coat help in a storm?", "It blocks a lot of wind and rain so your clothes stay drier and warmer.")],
    "ice_cleats": [("How do ice cleats work?", "They create extra bite against ice and help a person keep their footing.")],
}
KNOWLEDGE_ORDER = ["ice", "slip", "wet", "storm", "cold", "field", "boots", "wind_shell", "waterproof_coat", "ice_cleats"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    key = act.keyword or act.mess
    return [
        f'Write a tiny story with the words "{key}" and "syrup" about a child and a parent making a safe compromise.',
        f"Tell a warm story where {hero.id} wants to {act.verb}, but {parent.id} worries about the new {prize.label} getting ruined.",
        f'Use a heartwarming "parent, warning, compromise, and resolution" arc for a child on {f["setting"].place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    out: list[QAItem] = []
    out.append(QAItem("Who is the story about?", f"{hero.id} and {parent.id}."))
    out.append(QAItem(f"What did {hero.id} want to do?", f"{hero.id} wanted to {act.verb}."))
    out.append(QAItem(f"Why was {hero.id} {hero.id} upset?", f"{hero.id} wanted to {act.verb} but still wanted to protect {hero.pronoun('possessive')} {prize.label}."))

    if f.get("warned"):
        soil = f.get("predicted_soil", "damage")
        work = f.get("predicted_workload", 0)
        why = (
            f"{parent.id} warned that if {hero.id} went out, the {prize.label} would get {soil}. "
            f"That would mean {parent.id} had more cleaning work" + (
                ", so this mattered" if work >= THRESHOLD else "."
            )
        )
        if work >= THRESHOLD:
            why += "."
        out.append(QAItem(f"Why did {parent.id} warn {hero.id}?", why))

    if f.get("conflict"):
        out.append(QAItem(
            "What made the argument happen?",
            f"{hero.id} tried to act before the warning was accepted, and {parent.id} grabbed {hero.pronoun('object')} to keep {hero.pronoun('object')} safe."
        ))

    if f.get("resolved"):
        gear = f["gear"]
        out.append(QAItem(
            "How was the problem solved?",
            f"They agreed on a safer choice first: they {gear.prep if gear else 'used a safer plan'}, then did the activity safely."
        ))
        out.append(QAItem(
            f"How did {hero.id} feel at the end?",
            "Relieved and happy. The compromise felt fair, and the parent and child finished together."
        ))

    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child-level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.protective:
            bits.append(f"covers={sorted(ent.covers)}")
        elif ent.region:
            bits.append(f"region={ent.region}")
        lines.append(f"  {ent.id:12} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("frozen_field", "ice_run", "boots", "Milo", "boy", "mother", "brave"),
    StoryParams("pine_camp", "storm_dash", "jacket", "Lena", "girl", "father", "gentle"),
    StoryParams("frozen_field", "storm_dash", "jacket", "Kai", "boy", "mother", "restless"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} affects {sorted(activity.zone)}, but "
            f"{noun} {verb} on the {prize.region}; no honest warning would be made."
        )
    return (
        f"(No story: {noun} is not fixed by any gear in the catalog for {activity.gerund}. "
        f"The compromise must actually protect the item that is at risk.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    allowed = " / ".join(sorted(PRIZES[prize_id].genders))
    return (
        f"(No story: a {PRIZES[prize_id].label} is not typical for a {gender}; "
        f"try --gender {allowed}.)"
    )


ASP_RULES = r"""
valid(Place, Activity, Prize) :-
    affords(Place, Activity),
    splash(Activity, Region),
    worn_on(Prize, Region),
    guards(gear(_, Activity), Mess),
    mess_of(Activity, Mess),
    at_risk(Activity, Prize).

at_risk(Activity, Prize) :- splash(Activity, Region), worn_on(Prize, Region).
has_fix(Activity, Prize) :-
    at_risk(Activity, Prize),
    gear(G),
    mess_of(Activity, Mess),
    guards(G, Mess),
    covers(G, Region),
    worn_on(Prize, Region).
valid_story(Place, Activity, Prize, Gender) :-
    valid(Place, Activity, Prize), wears(Gender, Prize).

#show valid/3.
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    rows: list[str] = []
    for pid, setting in SETTINGS.items():
        rows.append(asp.fact("place", pid))
        for act in sorted(setting.affords):
            rows.append(asp.fact("affords", pid, act))
    for aid, act in ACTIVITIES.items():
        rows.append(asp.fact("activity", aid))
        rows.append(asp.fact("mess_of", aid, act.mess))
        for region in sorted(act.zone):
            rows.append(asp.fact("splash", aid, region))
    for name, prize in PRIZES.items():
        rows.append(asp.fact("prize", name))
        rows.append(asp.fact("worn_on", name, prize.region))
        for g in sorted(prize.genders):
            rows.append(asp.fact("wears", g, name))
    for gear in GEAR:
        rows.append(asp.fact("gear", gear.id))
        for mess in sorted(gear.guards):
            rows.append(asp.fact("guards", gear.id, mess))
        for reg in sorted(gear.covers):
            rows.append(asp.fact("covers", gear.id, reg))
    return "\n".join(rows)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple[str, str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo = set(asp_valid_combos())
    py = set(valid_combos())
    if clingo == py:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    if clingo - py:
        print(f"  only in clingo: {sorted(clingo - py)}")
    if py - clingo:
        print(f"  only in python: {sorted(py - clingo)}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a risky field activity, and a safe compromise."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world state")
    ap.add_argument("--qa", action="store_true", help="print all three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON output")
    ap.add_argument("--asp", action="store_true", help="list valid (place, activity, prize, gender) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP and Python compatibility")
    ap.add_argument("--show-asp", action="store_true", help="print full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        activity = ACTIVITIES[args.activity]
        prize = PRIZES[args.prize]
        if not (prize_at_risk(activity, prize) and select_gear(activity, prize)):
            raise StoryError(explain_rejection(activity, prize))

    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if args.gender:
        combos = [c for c in combos if args.gender in PRIZES[c[2]].genders]

    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, activity, prize_id, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        hero_name=params.name,
        hero_type=params.gender,
        hero_traits=[params.trait],
        parent_type=params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("")
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} valid (place, activity, prize) combos ({len(stories)} with gender):")
        for place, activity, prize in combos:
            genders = sorted(g for (p, a, pr, g) in stories if (p, a, pr) == (place, activity, prize))
            print(f"  {place:12} {activity:10} {prize:8}  ({', '.join(genders)})")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} @ {p.place} - {p.activity} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
