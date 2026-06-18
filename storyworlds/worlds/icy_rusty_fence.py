#!/usr/bin/env python3
"""
icy_rusty_fence.py
===================

Seed:
  words: icy flower, damp, rusty river, sleepy, fence
  features: Rhyme, Bravery, Moral Value
  style: Detective Story

A child wants to wander to a river-side place, the parent predicts a risk to a
cherished item, and then guides a safer compromise.
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
MESS_KINDS = {"wet", "mud"}


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
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "mother":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "father":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        if self.type == "mother":
            return "mom"
        if self.type == "father":
            return "dad"
        return self.type


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
    id: str
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

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def characters(self) -> list[Entity]:
        return [ent for ent in self.entities.values() if ent.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [ent for ent in self.entities.values() if ent.worn_by == actor.id]

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


def _r_soaked(world: World) -> list[str]:
    produced: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if not item.region or item.region not in world.zone or item.protective:
                    continue
                if world.covered(actor, item.region):
                    continue
                key = ("soak", actor.id, item.id, mess)
                if key in world.fired:
                    continue
                world.fired.add(key)
                if mess == "wet":
                    item.meters["wet"] += 1
                if mess == "mud":
                    item.meters["mud"] += 1
                item.meters["dirty"] += 1
                produced.append(
                    f"{item.label} became {mess} from the {actor.id}'s adventure."
                )
    return produced


def _r_cleanup(world: World) -> list[str]:
    produced: list[str] = []
    for item in world.entities.values():
        if not item.caretaker or item.meters["dirty"] < THRESHOLD:
            continue
        key = ("cleanup", item.id)
        if key in world.fired:
            continue
        world.fired.add(key)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        produced.append(f"{carer.id} would have extra cleaning work.")
    return produced


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed_by"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        key = ("conflict", actor.id)
        if key in world.fired:
            continue
        world.fired.add(key)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    Rule("soak", "physical", _r_soaked),
    Rule("cleanup", "physical", _r_cleanup),
    Rule("conflict", "social", _r_conflict),
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
                    produced.extend([x for x in got if x != "__conflict__"])
    if narrate:
        for sentence in produced:
            world.say(sentence)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Gear | None:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["bravery"] += 1
    propagate(world, narrate=narrate)


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict[str, float]:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(c.meters["workload"] for c in sim.characters()),
    }


def introduce(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"Once upon a time, there was a little {hero.type} named {hero.id}, and {hero.pronoun('subject')} was curious and brave."
    )
    world.say(f"{parent.label_word.capitalize()} promised to keep a close watch.")


def present_prize(world: World, hero: Entity, prize: Entity) -> None:
    liked = "them" if prize.plural else "it"
    world.say(
        f"One afternoon, {hero.pronoun('possessive')} {world.get(hero.owner).label_word} had bought {hero.pronoun('object')} {prize.phrase}, "
        f"and {hero.pronoun('subject')} liked {liked} dearly."
    )


def wants_activity(world: World, hero: Entity, activity: Activity, parent: Entity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} and find the icy flower by the river.")
    world.say(
        f"{hero.pronoun().capitalize()} said, \"I want to go, and you can trust my judgment.\""
    )
    world.say(f"{parent.label_word.capitalize()} said no because the {activity.keyword} edge can be dangerous.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clean_target = "them" if prize.plural else "it"
    world.say(
        f'"If you go too close, your {prize.label} will get {activity.soil}, and we will have to clean {clean_target}."'
    )
    world.say(f"{parent.label_word.capitalize()} added, \"I am not stopping your adventure. I am stopping the mess.\"")
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} insisted, \"I can do it,\" and tried to {activity.rush}."
    )


def grab(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{parent.label_word.capitalize()} grabbed {hero.pronoun("object")} by the hand and said, "Keep your promise and stay with me."'
    )
    world.say(f'They stood by the old fence and talked it through.')


def misunderstanding_clear(world: World, hero: Entity) -> None:
    if hero.memes["conflict"] < THRESHOLD:
        return
    hero.memes["confusion"] += 1
    world.say(f"{hero.id} realized the silence was not punishment, just care.")


def propose_compromise(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> Gear | None:
    selected = select_gear(activity, PRIZES[prize.id])
    if selected is None:
        return None
    gear = world.add(
        Entity(
            id=selected.id,
            kind="thing",
            type="gear",
            label=selected.label,
            protective=True,
            owner=hero.id,
            caretaker=parent.id,
            covers=set(selected.covers),
            plural=selected.plural,
        )
    )
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f'{parent.label_word.capitalize()} said, "Here is my idea: {selected.prep}."')
    return selected


def accept(world: World, hero: Entity, parent: Entity, selected: Gear, activity: Activity) -> None:
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id} laughed and hugged {parent.label_word}.")
    world.say(f'They {selected.tail}, then {hero.id} could {activity.verb} safely.')


def finish(world: World, hero: Entity, resolved: bool) -> None:
    if resolved:
        world.facts["outcome"] = "compromise"
        world.say(f"{hero.id} found a bright icy flower near the river and felt glad.")
        world.say("The night stayed gentle, and both stayed safe.")
    else:
        world.facts["outcome"] = "deferred"
        world.say(
            f"{hero.id} stayed near the fence, watched the mist move, and waited with sleepy eyes."
        )
        world.say("Being careful kept the family together.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str,
         trait: str, parent_type: str) -> World:
    world = World(setting)
    world.weather = activity.weather
    hero = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            traits=[trait],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label=f"the {parent_type}",
        )
    )
    hero.owner = parent.id
    prize = world.add(
        Entity(
            id=prize_cfg.id,
            kind="thing",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            region=prize_cfg.region,
            owner=hero.id,
            caretaker=parent.id,
            worn_by=hero.id,
            plural=prize_cfg.plural,
        )
    )

    introduce(world, hero, parent)
    present_prize(world, hero, prize)
    wants_activity(world, hero, activity, parent)

    world.para()
    warned = warn(world, parent, hero, activity, prize)
    if warned:
        defy(world, hero, activity)
        grab(world, hero, parent, activity)
        misunderstanding_clear(world, hero)

    world.para()
    selected = propose_compromise(world, hero, parent, activity, prize)
    if selected:
        accept(world, hero, parent, selected, activity)
        finish(world, hero, resolved=True)
    else:
        finish(world, hero, resolved=False)

    world.facts.update(
        setting=setting,
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        prize_cfg=prize_cfg,
        warned=warned,
        gear=selected,
        resolved=selected is not None,
        conflict=hero.memes["conflict"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "rusty_river_meadow": Setting("the dusty meadow by the rusty river", False, {"river_walk", "fence_walk"}),
    "frost_village_fence": Setting("the old fence path by the village", False, {"fence_walk"}),
    "village_hall": Setting("the warm village hall", True, {"river_walk"}),
}

ACTIVITIES = {
    "river_walk": Activity(
        id="river_walk",
        verb="walk near the rusty river",
        gerund="walking near the river",
        rush="run toward the icy flower",
        mess="wet",
        soil="wet and clammy",
        zone={"feet", "legs", "torso"},
        weather="damp",
        keyword="rusty river",
        tags={"river", "wet", "fence"},
    ),
    "fence_walk": Activity(
        id="fence_walk",
        verb="walk along the fence",
        gerund="walking by the fence",
        rush="cross the old gate",
        mess="mud",
        soil="muddy and damp",
        zone={"feet", "legs"},
        weather="damp",
        keyword="fence",
        tags={"fence", "mud"},
    ),
}

GEAR = [
    Gear(
        id="river_boots",
        label="river boots",
        covers={"feet", "legs"},
        guards={"wet", "mud"},
        prep="wear river boots",
        tail="got the boots on",
        plural=True,
    ),
    Gear(
        id="wind_jacket",
        label="wind jacket",
        covers={"torso"},
        guards={"wet"},
        prep="put on the wind jacket",
        tail="pulled on the jacket",
    ),
    Gear(
        id="mud_gaiters",
        label="mud gaiters",
        covers={"legs", "feet"},
        guards={"mud"},
        prep="put on the mud gaiters",
        tail="slid on the gaiters",
        plural=True,
    ),
]

PRIZES = {
    "fuzzy_blanket": Prize("fuzzy_blanket", "fuzzy blanket", "a soft fuzzy blanket", "clothing", "torso", genders={"girl"}),
    "wool_boots": Prize("wool_boots", "wool boots", "a pair of wool boots", "boots", "feet", plural=True),
    "fleece_scarf": Prize("fleece_scarf", "fleece scarf", "a soft fleece scarf", "clothing", "torso"),
}

BOY_NAMES = ["Niko", "Tobias", "Rafi", "Lio", "Emil"]
GIRL_NAMES = ["Lina", "Ivy", "Mara", "Nia", "Sora"]
TRAITS = ("sleepy", "brave", "quiet", "curious")


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for activity_id in setting.affords:
            activity = ACTIVITIES[activity_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(activity, prize) and select_gear(activity, prize):
                    combos.append((place, activity_id, prize_id))
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
    seed: int | None = None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} affects {sorted(activity.zone)}, but {prize.label} is worn on "
            f"the {prize.region}; no honest warning applies.)"
        )
    return (
        f"(No story: no catalog gear protects {prize.label} for {activity.gerund}. "
        "A compromise must actually reduce the risk.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    allowed = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is unusual for a {gender}. Try --gender {allowed}.)"


KNOWLEDGE = {
    "fence": [("Why is an old fence risky?", "Old rails and planks can be slippery or weak, so children should stay close.")],
    "river": [("Why can a riverbank be damp?", "Water and fog make the bank wet and slippery.")],
    "wet": [("Why does wet fabric feel cold?", "Water carries heat away from skin quickly when a material is wet.")],
    "mud": [("Why is mud sticky?", "Mud is wet soil, so it clings to shoes and can trip you.")],
    "river_boots": [("What are river boots for?", "They help your feet stay dry and steady around water and mud.")],
    "wind_jacket": [("What does a wind jacket do?", "It reduces chill and wet spray from reaching your torso.")],
    "mud_gaiters": [("What are gaiters for?", "They cover lower legs and reduce mud splash when walking on rough ground.")],
}
KNOWLEDGE_ORDER = ["fence", "river", "wet", "mud", "river_boots", "wind_jacket", "mud_gaiters"]


def generation_prompts(world: World) -> list[str]:
    activity = world.facts["activity"]
    hero = world.facts["hero"]
    return [
        'Write a detective-style rhyme using the words "icy flower", "rusty river", "sleepy", and "fence".',
        f"Tell a moral story where {hero.id} learns bravery means listening to {world.facts['parent'].label_word}.",
        f"Show a misunderstanding and a compromise around the phrase '{activity.keyword}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    out = [
        QAItem("Who are the characters?", f"{hero.id} and {parent.label_word.capitalize()}."),
        QAItem("What did the child want to do?", f"{hero.id} wanted to {act.verb}."),
    ]
    if f.get("warned"):
        workload = f.get("predicted_workload", 0)
        soil = f.get("predicted_soil", "damage")
        out.append(QAItem(
            "Why did the parent caution the child?",
            f"The parent warned that the {prize.label} could get {soil} and there would be extra cleaning work."
        ))
        if workload >= THRESHOLD:
            out.append(QAItem(
                "What extra work was expected?",
                f"{parent.label_word.capitalize()} expected extra cleaning if the {prize.label} got {soil}."
            ))
    if f.get("conflict"):
        out.append(QAItem(
            "How did misunderstanding happen?",
            f"{hero.id} wanted to do the action first, and {parent.label_word} held {hero.pronoun('object')} by the hand."
        ))
    if f.get("resolved"):
        out.append(QAItem(
            "How was the conflict resolved?",
            "With a specific compromise that protected the item, so they continued safely."
        ))
        out.append(QAItem("What is the moral?", "Bravery is better with safety and listening."))
    else:
        out.append(QAItem("What happened instead?", "The family waited safely rather than taking a risky route."))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question, answer) for question, answer in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


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
        rows.append(f"  {ent.id:14} ({ent.type:8}) {' '.join(bits)}")
    rows.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(rows)


CURATED = [
    StoryParams("rusty_river_meadow", "river_walk", "fuzzy_blanket", "Mia", "girl", "mother", "sleepy"),
    StoryParams("frost_village_fence", "fence_walk", "wool_boots", "Niko", "boy", "father", "brave"),
    StoryParams("village_hall", "river_walk", "fleece_scarf", "Lina", "girl", "mother", "curious"),
]


ASP_RULES = r"""
activity_zone(A,R) :- splashes(A,R).
at_risk(A,P) :- activity_zone(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), guards(G,M), mess_of(A,M), at_risk(A,P), covers(G,R), worn_on(P,R).

valid(Place,Act,Prize) :-
  affords(Place,Act), at_risk(Act,Prize), protects(_,Act,Prize).
valid_story(Place,Act,Prize,Gender) :-
  valid(Place,Act,Prize), wears(Gender,Prize).

#show valid/3.
#show valid_story/4.
"""


def asp_facts() -> str:
    from asp import fact
    rows: list[str] = []
    for pid, setting in SETTINGS.items():
        rows.append(fact("place", pid))
        for act in sorted(setting.affords):
            rows.append(fact("affords", pid, act))
    for aid, act in ACTIVITIES.items():
        rows.append(fact("activity", aid))
        rows.append(fact("mess_of", aid, act.mess))
        for z in sorted(act.zone):
            rows.append(fact("splashes", aid, z))
    for pid, prize in PRIZES.items():
        rows.append(fact("prize", pid))
        rows.append(fact("worn_on", pid, prize.region))
        for gender in sorted(prize.genders):
            rows.append(fact("wears", gender, pid))
    for g in GEAR:
        rows.append(fact("gear", g.id))
        for msg in sorted(g.guards):
            rows.append(fact("guards", g.id, msg))
        for cover in sorted(g.covers):
            rows.append(fact("covers", g.id, cover))
    return "\n".join(rows)


def asp_program(show: str) -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n" + show


def asp_valid_combos() -> list[tuple[str, str, str]]:
    from asp import atoms, one_model
    model = one_model(asp_program("#show valid/3."))
    return sorted(set(atoms(model, "valid")))


def asp_valid_stories() -> list[tuple[str, str, str, str]]:
    from asp import atoms, one_model
    model = one_model(asp_program("#show valid_story/4."))
    return sorted(set(atoms(model, "valid_story")))


def asp_verify() -> int:
    from asp import atoms, one_model
    py = set(valid_combos())
    model = one_model(asp_program("#show valid/3."))
    clingo = set(atoms(model, "valid"))
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    if py - clingo:
        print(f"  only in python: {sorted(py - clingo)}")
    if clingo - py:
        print(f"  only in clingo: {sorted(clingo - py)}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Storyworld: river, fence, and sleepy bravery with a safe compromise."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--activity", choices=ACTIVITIES)
    parser.add_argument("--prize", choices=PRIZES)
    parser.add_argument("--gender", choices=["boy", "girl"])
    parser.add_argument("--parent", choices=["mother", "father"])
    parser.add_argument("--name")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1, help="number of stories")
    parser.add_argument("--all", action="store_true", help="render curated stories")
    parser.add_argument("--trace", action="store_true", help="show model state")
    parser.add_argument("--qa", action="store_true", help="show Q&A sets")
    parser.add_argument("--json", action="store_true", help="json output")
    parser.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    parser.add_argument("--verify", action="store_true", help="verify ASP and Python parity")
    parser.add_argument("--show-asp", action="store_true", help="print complete asp program")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        prize = PRIZES[args.prize]
        if not prize_at_risk(act, prize) or not select_gear(act, prize):
            raise StoryError(explain_rejection(act, prize))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [
        (p, a, pr)
        for p, a, pr in valid_combos()
        if (args.place is None or p == args.place)
        and (args.activity is None or a == args.activity)
        and (args.prize is None or pr == args.prize)
    ]
    if args.gender:
        combos = [c for c in combos if args.gender in PRIZES[c[2]].genders]

    if not combos:
        raise StoryError("(No valid combination matches those options.)")
    place, activity, prize = rng.choice(combos)
    selected_prize = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(selected_prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, activity, prize, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.trait,
        params.parent,
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
        for place, act, prize in combos:
            genders = [g for (p, a, pr, g) in stories if (p, a, pr) == (place, act, prize)]
            print(f"  {place:18} {act:10} {prize:14} {'/'.join(sorted(genders))}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(x) for x in CURATED]
    else:
        samples = []
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
            header = f"### {sample.params.name} / {sample.params.place} / {sample.params.activity}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 68 + "\n")


if __name__ == "__main__":
    main()
