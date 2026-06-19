#!/usr/bin/env python3
"""
storyworlds/worlds/crystal_river_hover.py
========================================

A standalone storyworld sketch for the seed prompt:

  Words: crystal river, misty sign, quiet garden, hover, bright hill
  Features: Reconciliation, Conflict, Cautionary
  Style: Comedy

The world models a child who wants to wander with a hoverboard toward a
crystal-river trail while mom tries to keep a treasured gift clean and safe.

Core shape:
  child wants a risky wet activity -> parent predicts a real risk -> parent warns
  and blocks -> child and parent choose a compatible compromise -> reconciliation.
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

# Make shared result containers resolvable when running this file directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MESS_KINDS = {"wet", "muddy"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
    indoors: bool
    affords: set[str]
    sign: str
    landmark: str


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

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

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


def _r_soaked(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD and actor.meters["muddy"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if not item.region or item.region not in world.zone or item.protective:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["muddy"] += 1
            item.meters["dirty"] += 1
            out.append(
                f"{actor.pronoun('possessive').capitalize()} {item.label} got wet and muddy."
            )
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
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would give {carer.label_word} extra cleaning work.")
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


CAUSAL_RULES: list[Rule] = [
    Rule("soak", "physical", _r_soaked),
    Rule("workload", "physical", _r_workload),
    Rule("grab_conflict", "social", _r_grab_conflict),
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
                produced.extend(s for s in sents if s != "__conflict__")
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


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.meters["joy"] += 1
    propagate(world, narrate=narrate)


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict[str, float]:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and (prize.meters["dirty"] >= THRESHOLD or prize.meters["wet"] >= THRESHOLD)),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def introduce(world: World, hero: Entity, parent: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "quick")
    world.say(
        f"Once upon a time, there was a little {trait} {hero.type} named {hero.id}, "
        f"and {hero.pronoun('subject')} loved exploring."
    )
    world.say(
        f"In that quiet garden, {hero.id} kept staring at {world.setting.landmark}, "
        f"where a sign read '{world.setting.sign}'."
    )


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(f"{hero.id} was especially excited to try {activity.gerund} near the crystal river.")


def buy_prize(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One day, {hero.pronoun('possessive')} {parent.label_word} bought "
        f"{hero.pronoun('object')} {prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    kept = "them" if prize.plural else "it"
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and kept {kept} on "
        f"as a badge of honor."
    )


def arrive(world: World, hero: Entity, parent: Entity) -> None:
    day = {"damp": "On a damp morning, ", "rainy": "On a damp morning, ", "": "One day, "}.get(
        world.weather, "One day, "
    )
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to the "
        f"quiet garden by the crystal river."
    )


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} "
        f"{parent.label_word} looked at the damp path and paused."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clean_target = "them" if prize.plural else "it"
    clause = f"Your {prize.label} will get {activity.soil}, and then we will have to clean {clean_target}"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said softly.')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} ignored the warning and tried to {activity.rush}.")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} held {hero.pronoun('object')} by the hand "
        f"and said, 'You can want to {activity.verb}, and we can still choose a safer way.'"
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] < THRESHOLD:
        return
    world.say(
        f"{hero.id} pouted. 'I can be brave and careful at the same time,' "
        f"{hero.pronoun()} said. 'Please let me {activity.verb} one last time.'"
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    prize_like = Prize(prize.id, prize.label, prize.phrase, prize.type, prize.region, prize.plural)
    gear_def = select_gear(activity, prize_like)
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
        worn_by=hero.id,
    ))
    if not predict_mess(world, hero, activity, prize.id)["soiled"]:
        world.say(
            f'{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled and said, '
            f'"Let\'s do this smarter. We can {gear_def.prep} and then {activity.verb} together."'
        )
        return gear_def
    gear.worn_by = None
    del world.entities[gear.id]
    return None


def accept(world: World, parent: Entity, hero: Entity, activity: Activity,
           prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s face brightened immediately. "
        f"{hero.pronoun().capitalize()} hugged {hero.pronoun('possessive')} {parent.label_word} "
        f"and said, 'Let's go!'"
    )
    world.say(
        f"After they {gear_def.tail}, {hero.id} was {activity.gerund} near the river, "
        f"and {hero.pronoun('possessive')} {prize.label} stayed clean."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mia",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["eager", "curious"]),
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
    ))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero, parent)
    loves_activity(world, hero, activity)
    buy_prize(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent)
    wants(world, hero, parent, activity)
    warned = warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    if warned:
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
        activity=activity,
        setting=setting,
        prize_cfg=prize_cfg,
        gear=gear_def,
        conflict=hero.memes["conflict"] >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "quiet_garden": Setting(
        place="the quiet garden",
        indoors=False,
        affords={"hover"},
        sign="Damp trail to Crystal River",
        landmark="a misty sign",
    ),
    "bright_hill": Setting(
        place="the bright hill",
        indoors=False,
        affords={"hover"},
        sign="Damp path to Crystal River",
        landmark="a weathered gate post",
    ),
}


ACTIVITIES = {
    "hover": Activity(
        id="hover",
        verb="hover the board",
        gerund="hovering with the board",
        rush="zoom past the misty sign on the board",
        mess="wet",
        soil="damp and muddy",
        zone={"feet", "legs"},
        weather="damp",
        keyword="hover",
        tags={"wet", "mud", "hover"},
    ),
    "river_dash": Activity(
        id="river_dash",
        verb="run to the crystal river",
        gerund="running down to the crystal river",
        rush="rush toward the bright hill and then the river",
        mess="muddy",
        soil="muddy",
        zone={"feet", "legs"},
        weather="damp",
        keyword="river",
        tags={"river", "mud"},
    ),
}

GEAR = [
    Gear(
        id="boots",
        label="rain boots",
        covers={"feet"},
        guards={"wet", "muddy"},
        prep="go home and get the rain boots first",
        tail="went home and got the rain boots first",
        plural=True,
    ),
    Gear(
        id="shin_guard",
        label="shin guards",
        covers={"legs"},
        guards={"muddy"},
        prep="get on the shin guards first",
        tail="put on protective shin guards",
    ),
    Gear(
        id="coveralls",
        label="waterproof overalls",
        covers={"feet", "legs"},
        guards={"wet", "muddy"},
        prep="pull on waterproof overalls",
        tail="put on waterproof overalls",
    ),
]

PRIZES = {
    "sneakers": Prize("sneakers", "white sneakers", "a pair of sneakers", "sneakers", "feet", plural=True),
    "socks": Prize("socks", "cozy socks", "a pair of cozy socks", "socks", "feet", plural=True),
    "dress": Prize("dress", "new dress", "a new dress", "dress", "legs", genders={"girl"}),
}

GIRL_NAMES = ["Mia", "Lena", "Nora", "Aria", "Sophia", "Ari"]
BOY_NAMES = ["Niko", "Leo", "Eli", "Ben", "Noah", "Jules"]
TRAITS = ["brave", "curious", "steady", "eager", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


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
    "hover": [("What does it mean to hover?", "To hover means to stay up off the ground for a short time.")],
    "wet": [("Why do wet shoes feel heavy?",
             "Wet shoes gain extra water weight, which makes them feel heavier and less comfortable.")],
    "muddy": [("What does muddy mean?",
               "Muddy means wet soil clings to things like shoes or trousers.")],
    "boots": [("Why are rain boots useful?",
               "Rain boots cover your feet and keep them drier when you go through damp areas.")],
    "shin_guard": [("What are shin guards for?",
                  "Shin guards protect your legs from bumps and scrapes while you move quickly.")],
    "coveralls": [("What do protective overalls do?",
                  "Coveralls are full-body coverings that protect clothes from dirt and water.")],
}
KNOWLEDGE_ORDER = ["hover", "wet", "muddy", "boots", "shin_guard", "coveralls"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act = f["hero"], f["parent"], f["activity"]
    p_poss = hero.pronoun("possessive")
    return [
        f'Write a short child story that includes the word "{act.keyword}".',
        f"Tell a gentle cautionary story where a child in a quiet garden wants to "
        f"{act.verb}, but {p_poss} {parent.label_word} disagrees and then they make "
        f"a safe compromise.",
        f"Create a reconciliation ending with a confident child saying thank you after finding a safer way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    p = parent.label_word
    qa: list[tuple[str, str]] = [
        (f"Who is the main character of this story?",
         f"It is about a little {hero.type} named {hero.id} and {hero.pronoun('possessive')} {p}."),
        (f"What did {hero.id} want to do?",
         f"{hero.id} wanted to {act.verb} and go toward the crystal river."),
        (f"What did {hero.id} worry about?",
         f"{hero.id} and {hero.pronoun('possessive')} {p} were worried that the {prize.label} could get {act.soil} on the damp path."),
    ]
    if f.get("conflict"):
        soiled = f.get("predicted_soil", "mud")
        qa.append((
            f"Explain why {hero.id} and {hero.pronoun('possessive')} {p} argued.",
            f"{hero.pronoun().capitalize()} {p} was worried that after {act.verb}, the "
            f"{prize.label} would get {soiled}, and wanted to avoid cleanup work. "
            f"{hero.id} still wanted the adventure, so they needed a safer plan."
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append((
            "How was the argument resolved?",
            f"{hero.id} and {hero.pronoun('possessive')} {p} chose {gear.label} and then "
            f"{hero.pronoun('subject')} could {act.verb} safely. The {prize.label} stayed clean while the adventure continued."
        ))
        qa.append((
            f"How did {hero.id} feel at the end?",
            f"{hero.id} felt brave, grateful, and happy after finding a safer way."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.region:
            bits.append(f"region={ent.region}")
        if ent.protective:
            bits.append(f"covers={sorted(ent.covers)}")
        lines.append(f"  {ent.id:9} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("quiet_garden", "hover", "sneakers", "Lena", "girl", "mother", "brave"),
    StoryParams("quiet_garden", "hover", "socks", "Leo", "boy", "father", "curious"),
    StoryParams("bright_hill", "river_dash", "socks", "Mia", "girl", "mother", "lively"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = f"{'two ' if prize.plural else 'a '}{prize.label}"
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} touches {sorted(activity.zone)} areas, but "
            f"{noun} sits on {prize.region}, so this is not an honest warning."
        )
    return (
        f"(No story: none of the available gear covers {prize.region} for {activity.gerund} "
        f"in a way that blocks {activity.soil}. Keep at-risk coverage and trial check.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    allowed = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {gender} wearing {PRIZES[prize_id].label} is out of domain. Try {allowed}.)"


ASP_RULES = r"""
% A prize is at risk if the activity splashes the region where it is worn.
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

% A gear is compatible when it guards the mess kind and covers the at-risk region.
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, G) :- valid(Place, A, P), wears(G, P).
"""


def asp_facts() -> str:
    import asp
    out: list[str] = []
    for pid, s in SETTINGS.items():
        out.append(asp.fact("setting", pid))
        if s.indoors:
            out.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            out.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        out.append(asp.fact("activity", aid))
        out.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            out.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        out.append(asp.fact("prize", pid))
        out.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            out.append(asp.fact("wears", g, pid))
        if p.plural:
            out.append(asp.fact("plural", pid))
    for g in GEAR:
        out.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            out.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            out.append(asp.fact("covers", g.id, r))
    return "\n".join(out)


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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if clingo_set - python_set:
        print("  only clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: crystal river hover cautionary tale with reconciliation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories")
    ap.add_argument("--seed", type=int, default=None, help="seed for deterministic sampling")
    ap.add_argument("--all", action="store_true", help="render curated stories")
    ap.add_argument("--trace", action="store_true", help="print world-model trace")
    ap.add_argument("--qa", action="store_true", help="print Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from ASP")
    ap.add_argument("--verify", action="store_true", help="assert ASP and Python gates match")
    ap.add_argument("--show-asp", action="store_true", help="print all ASP facts/rules")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        prize = PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    candidates = [c for c in valid_combos()
                  if (args.place is None or c[0] == args.place)
                  and (args.activity is None or c[1] == args.activity)
                  and (args.prize is None or c[2] == args.prize)
                  and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not candidates:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(candidates))
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
        hero_traits=[params.trait, "stubborn"],
        parent_type=params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        import asp
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos:")
        for place, act, prize in triples:
            genders = sorted(g for p, a, pr, g in stories if (p, a, pr) == (place, act, prize))
            print(f"  {place:12} {act:10} {prize:8}  {', '.join(genders)}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for cfg in CURATED:
            samples.append(generate(cfg))
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
