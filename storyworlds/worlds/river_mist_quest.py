#!/usr/bin/env python3
"""
river_mist_quest.py
===================

Fresh seed sample:
Words: snail, misty wagon, fuzzy lamp, rusty village, riverbank
Features: Curiosity, Misunderstanding, Moral Value
Style: Fairy Tale

A child wants to go hunting snail tracks with a misty wagon near the riverbank.
The parent predicts a likely mess to a prized item and guides the child toward a
safer compromise.
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
from typing import Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MESS_KINDS = {"mud", "wet"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str | None = None
    caretaker: str | None = None
    worn_by: str | None = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it_word(self) -> str:
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
    genders_allowed: set[str] = field(default_factory=set)


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


def _r_wet_chain(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD and actor.meters["mud"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.region not in world.zone or item.protective:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("wet_chain", item.id, actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] += 1
            if actor.meters["wet"] >= THRESHOLD:
                item.meters["wet"] += 1
            if actor.meters["mud"] >= THRESHOLD:
                item.meters["mud"] += 1
            out.append(f"{actor.id}'s {item.label} got {', '.join(k for k in item.meters if item.meters[k] >= THRESHOLD)}.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if not item.caretaker or item.meters["dirty"] < THRESHOLD:
            continue
        sig = ("workload", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.meters["workload"] += 1
        out.append(f"That would mean {caretaker.id} would have extra washing work.")
    return out


def _r_conflict(world: World) -> list[str]:
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
    Rule("mud_and_wet", "physical", _r_wet_chain),
    Rule("workload", "physical", _r_workload),
    Rule("conflict", "social", _r_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            new = rule.apply(world)
            if new:
                changed = True
                if narrate:
                    produced.extend([n for n in new if n != "__conflict__"])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Gear | None:
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
    world.say(f"Once upon a time, there was a little {hero.type} named {hero.id}, who loved the riverbank.")


def curious_about_snail(world: World, hero: Entity) -> None:
    hero.memes["love"] += 1
    world.say(
        f"{hero.id} was curious and followed a tiny snail trail toward a little wonder."
    )


def setup_lamp(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} carried a fuzzy lamp close to {hero.pronoun('possessive')} {prize.label} and loved its warm glow."
    )


def loves_and_wears(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    proud_target = "them" if prize.plural else "it"
    world.say(f"{hero.id} wore the {prize.label} every day and was very proud of {proud_target}.")


def arrive(world: World, hero: Entity, parent: Entity) -> None:
    day = "In the misty morning" if world.weather else "One morning"
    world.say(f"{day}, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to {world.setting.place}.")


def wants_to_roll(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    extra = " with the misty wagon" if activity.id == "misty_wagon" and "wagon" not in activity.verb else ""
    world.say(f"{hero.id} wanted to {activity.verb}{extra}.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clean_target = "them" if prize.plural else "it"
    warning = (
        f"If you {activity.verb}, your {prize.label} will get {activity.soil}. "
        f"I will have to clean {clean_target} later."
    )
    world.say(f'{parent.label_word.capitalize()} said, "{warning}"')
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} shook {hero.pronoun('possessive')} head and tried to {activity.rush}.")


def grab_hand(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But {parent.label_word} held {hero.pronoun("object")} by the hand and said, '
        f'"I know you want to go. Let us make the path safe first."'
    )


def confusion(world: World, hero: Entity) -> None:
    if hero.memes["defiance"] >= THRESHOLD:
        hero.memes["confusion"] += 1
        world.say(f"{hero.pronoun().capitalize()} had thought the warning meant the adventure was over, and grew quiet for a moment.")


def compromise(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> Gear | None:
    gear = select_gear(activity, PRIZES[prize.id])
    if gear is None:
        return None
    # add gear before rechecking the actual prediction
    offered = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        protective=True,
        owner=hero.id,
        caretaker=parent.id,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    offered.worn_by = hero.id
    # If gear doesn't actually prevent the issue, the actor would reject it.
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        offered.worn_by = None
        del world.entities[offered.id]
        return None
    world.say(
        f"{parent.label_word.capitalize()} said, \"Let's {gear.prep} first, and then the river path can still be ours.\""
    )
    return gear


def accept(world: World, hero: Entity, parent: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} nodded, took a breath, and followed {parent.label_word} as they {gear.tail}."
    )
    world.facts["resolved"] = True


def final_triumph(world: World, hero: Entity, parent: Entity) -> None:
    if not world.facts.get("resolved"):
        world.say(f"In the end, {hero.id} listened and stayed careful, and both were proud.")
        return
    world.say(
        f"Together, {hero.id} and {parent.label_word} walked along the riverbank. The snail trail silvered the mud ahead, and the little lamp glowed over safe steps."
    )
    world.facts["resolved"] = True


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         hero_traits: list[str] | None, parent_type: str) -> World:
    world = World(setting)
    world.weather = activity.weather
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["curious"] + (hero_traits or []),
    ))
    parent = world.add(Entity(
        id="Parent" if parent_type == "mother" else "Grandparent",
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
    curious_about_snail(world, hero)
    setup_lamp(world, hero, prize)
    loves_and_wears(world, hero, prize)

    world.para()
    arrive(world, hero, parent)
    wants_to_roll(world, hero, parent, activity)
    warned = warn(world, parent, hero, activity, prize)
    if warned:
        defy(world, hero, activity)
        grab_hand(world, hero, parent, activity)
        confusion(world, hero)

    world.para()
    gear = compromise(world, hero, parent, activity, prize)
    if gear:
        accept(world, hero, parent, gear)
        final_triumph(world, hero, parent)
    else:
        world.say(f"{hero.id} and {parent.label_word} stayed in a safer place and watched the river for a while.")
        world.facts["resolved"] = False

    world.facts["warned"] = warned
    world.facts["setting"] = setting
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    world.facts["prize"] = prize
    world.facts["activity"] = activity
    world.facts["prize_cfg"] = prize_cfg
    world.facts["gear"] = gear
    world.facts["conflict"] = hero.memes["conflict"] >= THRESHOLD
    return world


SETTINGS = {
    "rusty_village": Setting("the rusted wagon yard in the misty village", False, {"misty_wagon", "riverbank_stroll"}),
    "riverbank_lookout": Setting("the riverbank lookout", False, {"riverbank_stroll"}),
    "village_hall": Setting("the warm village hall", True, {"misty_wagon"}),
}

ACTIVITIES = {
    "misty_wagon": Activity(
        "misty_wagon",
        "try to push the misty wagon",
        "pushing the misty wagon",
        "wheel through the misty path",
        "mud",
        "muddy and heavy",
        {"feet", "legs"},
        "mist",
        keyword="misty wagon",
        tags={"wagon", "mud", "misunderstanding"},
    ),
    "riverbank_stroll": Activity(
        "riverbank_stroll",
        "walk the riverbank path",
        "walking the riverbank path",
        "run across the edge of the bank",
        "wet",
        "damp and cold",
        {"feet", "torso"},
        "river mist",
        keyword="riverbank",
        tags={"riverbank", "wet"},
    ),
}

GEAR = [
    Gear(
        "river_boots",
        "a pair of river boots",
        covers={"feet", "legs"},
        guards={"mud"},
        prep="wear river boots",
        tail="wore the boots",
        plural=True,
    ),
    Gear(
        "snug_jacket",
        "a snug jacket",
        covers={"torso"},
        guards={"wet"},
        prep="put on the snug jacket",
        tail="put on the snug jacket",
    ),
    Gear(
        "windproof_coat",
        "a windproof coat",
        covers={"torso", "legs"},
        guards={"wet", "mud"},
        prep="pull on the windproof coat",
        tail="put on the windproof coat",
    ),
]

PRIZES = {
    "boots": Prize("boots", "warm wool boots", "boots", "feet", plural=True),
    "scarf": Prize("scarf", "soft scarf", "scarf", "torso", genders={"girl"}),
    "jacket": Prize("jacket", "new jacket", "jacket", "torso"),
}

BOY_NAMES = ("Noah", "Milo", "Rory", "Finn", "Eli")
GIRL_NAMES = ("Lina", "Maya", "Iris", "Nora", "Lark")
TRAITS = ("brave", "curious", "gentle", "clever")
KINDS = ("boy", "girl")


def valid_combo(place: str, activity: str, prize: str) -> bool:
    if place not in SETTINGS or activity not in ACTIVITIES or prize not in PRIZES:
        return False
    act = ACTIVITIES[activity]
    p = PRIZES[prize]
    return prize_at_risk(act, p) and select_gear(act, p) is not None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} affects {sorted(activity.zone)}, "
            f"while {prize.label} is worn on the {prize.region}."
        )
    return (
        f"(No story: no gear in this world protects {prize.label} for {activity.gerund}. "
        f"We keep only reasonable compromises.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    allowed = sorted(PRIZES[prize_id].genders)
    if not allowed:
        return f"(No story: a {PRIZES[prize_id].label} is not in the catalog for this child.)"
    return f"(No story: {PRIZES[prize_id].label} is unusual for a {gender}. Try --gender {' / '.join(allowed)}.)"


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for act_id in sorted(setting.affords):
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place_id, act_id, prize_id))
    return sorted(out)


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: int | None = None


KNOWLEDGE = {
    "wagon": [("What is a wagon used for?", "A wagon is a small cart on wheels used to carry things or roll along a path. In this story, it gives the child a tempting action that still needs a safe route.")],
    "mud": [("Why do boots get muddy?", "Mud is wet dirt. Walking on soft earth and puddles puts it onto shoes and socks, which is why the parent worries about cleaning.")],
    "snail": [("How do snails move?", "Snails leave thin silver lines in damp places while slowly creeping forward. The trail gives the child something interesting to follow without inventing a new character.")],
    "riverbank": [("What is a riverbank?", "A riverbank is the edge of a river. It can be soft and sometimes slippery, so the story treats quick movement there as risky.")],
    "rusty": [("Why are metal parts rusty?", "Rusted metal has been damp and has slowly changed color from oxidation. That detail fits a misty or river setting where moisture matters.")],
    "lamp": [("Why might a lamp be useful in mist?", "A lamp helps people see better and feel safer when it is foggy. It also keeps the story focused on careful movement instead of sudden running.")],
    "wet": [("Why get wet in mist?", "Mist can cling to fabric and make clothes feel cool and damp. That gives the warning a concrete reason instead of making the parent seem unfair.")],
    "boat": [("Why is caution important near water?", "Edges near water can be slippery and need careful footing. A child can still explore there, but the safe plan must slow the movement down.")],
    "river": [("What makes riverbank mud slippery?", "When the ground is wet and compact, it can become slick. That is why boots or a slower path are useful in a riverbank scene.")],
    "snug_jacket": [("How does a snug jacket help?", "It keeps wind off and helps keep a child dry for a while. In the compromise, it protects the thing the parent was worried about.")],
    "windproof_coat": [("What is a windproof coat?", "It is a thick outer layer that reduces wind and spray. It makes outdoor play more realistic when the weather is misty or cold.")],
    "river_boots": [("What do boots do on a riverbank?", "Boots cover the feet and help a child keep balance in mud and wet ground. They solve the practical risk without canceling the outing.")],
}
KNOWLEDGE_ORDER = ["wagon", "mud", "snail", "riverbank", "rusty", "lamp", "wet", "boat", "river", "snug_jacket", "windproof_coat", "river_boots"]


def generation_prompts(world: World) -> list[str]:
    act = world.facts["activity"]
    hero = world.facts["hero"]
    place = world.facts["setting"].place
    key = act.keyword or act.mess
    return [
        f'Write a story that includes "snail", "misty wagon", "fuzzy lamp", "rusty village", and "riverbank".',
        f'Tell a fairy tale with a misunderstanding and a moral about listening: {hero.id} wants to {act.verb} in {place}.',
        f'Use the words "{key}" and "moral value" in a gentle child story about a compromise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    out = [
        QAItem(
            "Who are the main characters?",
            f"{hero.id} is the child who wants to keep exploring, and {parent.label_word} is the parent setting the safety boundary. Their disagreement drives the compromise rather than a simple yes-or-no ending.",
        ),
        QAItem(
            "What did the parent warn about?",
            f"The parent warned that the {prize.label} could get {act.soil}. The warning makes sense because the activity threatens the same part of the child or clothing that the prize protects.",
        ),
    ]
    if f.get("warned"):
        soil = f.get("predicted_soil", "ruined")
        work = f.get("predicted_workload", 0)
        warn_reason = (
            f"{parent.label_word.capitalize()} warned because {act.gerund} could make the {prize.label} get {soil}."
        )
        if work >= THRESHOLD:
            warn_reason += " That would add extra cleanup work."
        out.append(QAItem(f"Why did {parent.label_word} warn {hero.id}?", warn_reason))
    if f.get("conflict"):
        out.append(QAItem("How did conflict start?", f"{hero.id} tried to ignore the warning first, so {parent.label_word} held {hero.pronoun('object')} by the hand. The conflict came from misunderstanding the warning as punishment rather than protection."))
    if f.get("resolved"):
        gear = f.get("gear")
        plan = gear.prep if gear is not None else "chose a slower plan"
        out.append(QAItem("How was the argument resolved?", f"They agreed to {plan} as a compromise, and then {hero.pronoun('subject')} could continue safely. The ending preserves the child's goal and shows the riverbank becoming possible again under safer conditions."))
    else:
        out.append(QAItem("How was it resolved in the end?", "They did not ride far and stayed safe instead. The story closes by choosing restraint when there is no honest protective fix nearby."))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear") is not None:
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    rows = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        rows.append(f"{i}. {prompt}")
    rows.append("")
    rows.append("== (2) Story questions -- answerable from the story text ==")
    for qa in sample.story_qa:
        rows.append(f"Q: {qa.question}")
        rows.append(f"A: {qa.answer}")
    rows.append("")
    rows.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for qa in sample.world_qa:
        rows.append(f"Q: {qa.question}")
        rows.append(f"A: {qa.answer}")
    return "\n".join(rows)


def dump_trace(world: World) -> str:
    rows = ["--- world model state ---"]
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
        rows.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    rows.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(rows)


CURATED = [
    StoryParams("rusty_village", "misty_wagon", "boots", "Noah", "boy", "mother", "brave"),
    StoryParams("riverbank_lookout", "riverbank_stroll", "jacket", "Lina", "girl", "father", "curious"),
    StoryParams("village_hall", "misty_wagon", "jacket", "Maya", "girl", "mother", "gentle"),
]


ASP_RULES = r"""
splashes(Act, Reg) :- activity(Act, Reg).
prize_at_risk(Act, Prize) :- splashes(Act, Reg), worn_on(Prize, Reg).
protects(G, Act, Prize) :-
  gear(G), guards(G, Mess), mess_of(Act, Mess),
  prize_at_risk(Act, Prize), covers(G, Reg), worn_on(Prize, Reg).

valid(Place, Act, Prize) :-
  affords(Place, Act), prize_at_risk(Act, Prize), protects(_, Act, Prize).
valid_story(Place, Act, Prize, Gender) :-
  valid(Place, Act, Prize), wears(Gender, Prize).

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
            rows.append(asp.fact("splashes", aid, region))
    for pid, prize in PRIZES.items():
        rows.append(asp.fact("prize", pid))
        rows.append(asp.fact("worn_on", pid, prize.region))
        for g in sorted(prize.genders):
            rows.append(asp.fact("wears", g, pid))
    for gear in GEAR:
        rows.append(asp.fact("gear", gear.id))
        for mess in sorted(gear.guards):
            rows.append(asp.fact("guards", gear.id, mess))
        for region in sorted(gear.covers):
            rows.append(asp.fact("covers", gear.id, region))
    return "\n".join(rows)


def asp_program(show: str) -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n" + show


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple[str, str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    if clingo - py:
        print(f"  only in clingo: {sorted(clingo - py)}")
    if py - clingo:
        print(f"  only in python: {sorted(py - clingo)}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: riverbank curiosity and safe compromise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=KINDS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of variants")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render curated set")
    ap.add_argument("--trace", action="store_true", help="dump world state")
    ap.add_argument("--qa", action="store_true", help="print Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos via clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP vs Python gate")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        prize = PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if args.gender:
        combos = [c for c in combos if args.gender in PRIZES[c[2]].genders]

    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize = rng.choice(combos)
    g = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if g == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, activity, prize, name, g, parent, trait)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        for place, activity, prize in combos:
            genders = [g for (p, a, pr, g) in stories if (p, a, pr) == (place, activity, prize)]
            print(f"{place:15} {activity:14} {prize:7} [{', '.join(sorted(genders))}]")
        print(f"{len(combos)} valid (place, activity, prize) combos, {len(stories)} with gender.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            header = f"### {sample.params.name}: {sample.params.place} / {sample.params.activity} / {sample.params.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i != len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
