#!/usr/bin/env python3
"""
storyworlds/worlds/cozy_bridge_lamp.py
======================================

A standalone story-world sketch built from a fresh seed:

  Words: spill, shiny flower, twinkling lamp, rainbow, cozy bridge
  Features: Lesson Learned, Rhyme, Teamwork
  Style: Nursery Rhyme

A child wants to rush with a shiny flower project across a cozy bridge
while a careful parent predicts a likely spill and proposes a safer plan.
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

# Allow running this file directly as ``python storyworlds/worlds/cozy_bridge_lamp.py``.
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
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    fixture: str
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


def _r_spill(world: World) -> list[str]:
    """Running through splashy ground soils worn items that are in-zone and uncovered."""
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["slip"] < THRESHOLD and actor.meters["muddy"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if not item.region or item.region not in world.zone or item.protective:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("spill", actor.id, item.id, world.weather, item.region)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["slip"] += 1
            item.meters["muddy"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} became muddy.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        parent = world.get(item.caretaker)
        parent.meters["workload"] += 1
        out.append(f"That would give {parent.label_word} one more messy chore.")
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


CAUSAL_RULES: list[Rule] = [
    Rule("spill", "physical", _r_spill),
    Rule("workload", "physical", _r_workload),
    Rule("conflict", "social", _r_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(x for x in s if x != "__conflict__")
    if narrate:
        for sentence in out:
            world.say(sentence)
    return out


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    """Whether this activity can ruin this prize, by region of contact."""
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    """Pick the first gear that both guards the mess and covers the prize region."""
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["slip"] += 1
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict[str, float]:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def introduce(world: World, hero: Entity, parent: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "quick")
    world.say(
        f"Once upon a time, there was a little {trait} {hero.type} named {hero.id}."
    )
    world.say(
        f"One day at {world.setting.place}, {hero.id} noticed a {world.setting.landmark} "
        f"that shimmered like a {world.setting.fixture} and wanted to add a shiny flower sticker."
    )


def loves_activity(world: World, hero: Entity, activity: Activity, prize: Prize) -> None:
    hero.memes["love_play"] += 1
    world.say(
        f"{hero.id} loved making a tiny rainbow with a twinkling lamp and "
        f"kept dreaming of {activity.gerund} to get home in style."
    )
    world.say(f"{hero.id} also cared a lot about {hero.pronoun('possessive')} new {prize.label}.")


def give_prize(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One day, {hero.pronoun('possessive')} {parent.label_word} brought "
        f"{hero.pronoun('object')} {prize.phrase}."
    )


def wear_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    feeling = "they were" if prize.plural else "it was"
    world.say(f"{hero.id} wore {prize.it} and said {feeling} very precious.")


def go_place(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"damp": "On a damp afternoon, ", "": "One afternoon, "}.get(world.weather, "One afternoon, ")
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to "
        f"{world.setting.place}."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, but the stones were slippery."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    prize_subject = "they" if prize.plural else "it"
    world.say(
        f'"If we hurry, we might spill everything and {prize_subject} would get {activity.soil}," '
        f"{hero.pronoun('possessive')} {parent.label_word} said."
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} said no, then tried to {activity.rush}.")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.pronoun('subject').capitalize()} held {hero.pronoun('object')} by the hand. "
        f'"Let us do this together and stay safe."'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] < THRESHOLD:
        return
    world.say(
        f'{hero.id} pouted and said, "I can still make a rainbow if we do it carefully together."'
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, Prize(prize.id, prize.label, prize.phrase, prize.type, prize.region, prize.plural))
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
            f'"Good idea," {parent.pronoun("subject")} said. '
            f'"Let us {gear_def.prep} and then {activity.verb} as a team."'
        )
        return gear_def
    gear.worn_by = None
    del world.entities[gear.id]
    return None


def resolve(world: World, parent: Entity, hero: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"Together, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} smiled. "
        f'{hero.pronoun("subject").capitalize()} said, "We did it without spills!" and they crossed together.'
    )
    world.say(
        f'By sharing the work, they made the twinkling lamp glow like a tiny rainbow and the shiny flower '
        f"{'stood' if hero.pronoun('subject') == 'it' else 'looked'} bright."
    )
    gear = world.entities.get(gear_def.id)
    if gear is not None and not gear.plural:
        gear.memes["love"] += 1


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["eager"]),
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
    loves_activity(world, hero, activity, prize)
    give_prize(world, parent, hero, prize)
    wear_prize(world, hero, prize)

    world.para()
    go_place(world, hero, parent, activity)
    warned = warn(world, parent, hero, activity, prize)
    if warned:
        defies(world, hero, activity)
        grab_hand(world, parent, hero, activity)

    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        resolve(world, parent, hero, gear_def)

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
    "cozy_bridge": Setting(
        place="the cozy bridge",
        indoor=False,
        affords={"bridge_rush", "bridge_slow"},
        fixture="twinkling lamp",
        landmark="shiny flower garland",
    )
}


ACTIVITIES = {
    "bridge_rush": Activity(
        id="bridge_rush",
        verb="hurry across",
        gerund="crossing it safely",
        rush="run across the cozy bridge",
        mess="muddy",
        soil="muddy",
        zone={"feet", "legs"},
        weather="damp",
        keyword="rainbow",
        tags={"bridge", "mud", "careful"},
    ),
    "bridge_slow": Activity(
        id="bridge_slow",
        verb="pace across the cozy bridge",
        gerund="crossing the bridge carefully",
        rush="walk slowly across",
        mess="slip",
        soil="slippery",
        zone={"feet", "legs"},
        weather="damp",
        keyword="lamp",
        tags={"bridge", "teamwork", "safety"},
    ),
}


GEAR = [
    Gear(
        id="boots",
        label="rain boots",
        covers={"feet", "legs"},
        guards={"muddy", "slip"},
        prep="put on our rain boots",
        tail="put on the rain boots",
        plural=True,
    ),
    Gear(
        id="shin_guard",
        label="shin guards",
        covers={"legs"},
        guards={"slip"},
        prep="put on leg guards",
        tail="put on leg guards",
    ),
    Gear(
        id="glove_pair",
        label="grippy gloves",
        covers={"hands"},
        guards={"slip"},
        prep="use grippy gloves",
        tail="found grippy gloves for the climb",
    ),
]


PRIZES = {
    "sandals": Prize(
        id="sandals",
        label="sparkly sandals",
        phrase="a pair of sparkly sandals",
        type="sandals",
        region="feet",
        plural=True,
    ),
    "sock_ponchos": Prize(
        id="sock_ponchos",
        label="comfy socks",
        phrase="a pair of comfy socks",
        type="socks",
        region="feet",
        plural=True,
    ),
    "dress": Prize(
        id="dress",
        label="new dress",
        phrase="a new dress",
        type="dress",
        region="legs",
        genders={"girl"},
    ),
}


GIRL_NAMES = ["Nora", "Mia", "Lena", "Ari", "Zoe"]
BOY_NAMES = ["Ben", "Niko", "Leo", "Tavi", "Noah"]
TRAITS = ["bright", "brave", "curious", "steady", "playful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


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
    "bridge": [("Why do bridges need care when wet?",
                "Wet stone can get slick, so people move slowly and hold on to avoid falls.")],
    "muddy": [("What does muddy mean?", "Muddy means covered with wet dirt that can make shoes and ground slippery.")],
    "slip": [("How can you stop a spill?", "You can hold objects close, take smaller steps, and move at a slower pace.")],
    "boots": [("What do rain boots do?", "Rain boots protect your feet from mud and water.")],
    "rainbow": [("Where do rainbows come from?", "Rainbows come from light reflecting through water droplets.")],
}
KNOWLEDGE_ORDER = ["bridge", "muddy", "slip", "boots", "rainbow"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act = f["hero"], f["parent"], f["activity"]
    return [
        f'Write a short story about a cozy bridge that includes the word "{act.keyword}".',
        f"Tell a gentle cautionary story where {hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} had a team moment about a twinkling lamp and a shiny flower.",
        "End with a clear lesson about working together to stay safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    p = parent.label_word
    qa: list[tuple[str, str]] = [
        (f"Who is the main child in the story?",
         f"It is {hero.id}, a little {hero.type}, and {hero.pronoun('possessive')} {p}."),
        (f"What did {hero.id} want to do at the cozy bridge?",
         f"{hero.id} wanted to {act.verb}."),
        (f"What item did {hero.id} care about the most?",
         f"It was {hero.pronoun('possessive')} new {prize.label}, and {hero.pronoun('subject')} wanted {prize.it} to stay clean."),
    ]
    if f.get("conflict"):
        why = (
            f"{hero.id} argued for rushing because {hero.pronoun('subject')} wanted to reach the twinkling lamp fast, "
            f"but {hero.pronoun('possessive')} {p} warned about a possible {f.get('predicted_soil', 'mess')}. "
            f"That disagreement created the argument."
        )
        qa.append((f"Explain why there was a disagreement.", why))
    if f.get("resolved"):
        g = f["gear"]
        qa.append((
            "How did they make it work?",
            f"They chose {g.label} and crossed together, so the plan worked without the feared spill."
        ))
        qa.append((
            f"What lesson does the story teach {hero.id} and the readers?",
            "When a place is risky, teamwork and safer choices prevent trouble."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
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
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
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
        out.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(out)


CURATED = [
    StoryParams("cozy_bridge", "bridge_rush", "sandals", "Nora", "girl", "mother", "bright"),
    StoryParams("cozy_bridge", "bridge_slow", "sandals", "Ben", "boy", "father", "brave"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} impacts {sorted(activity.zone)}, but {prize.label} "
            f"is worn on {prize.region}, so there is no direct honest risk."
        )
    return (
        f"(No story: {prize.label} has no compatible cover against {activity.verb} from our gear table.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    allowed = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {gender} with {PRIZES[prize_id].label} is out of typical domain. Try {allowed}.)"


ASP_RULES = r"""
% A prize is at risk when its worn region is in the activity zone.
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

% A compatible gear protects by guarding the mess and covering that region.
protects(G, A, P) :-
    gear(G), prize_at_risk(A, P),
    mess_of(A, M), guards(G, M),
    covers(G, R), worn_on(P, R).

has_fix(A, P) :- protects(_, A, P).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, G) :- valid(Place, A, P), wears(G, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for area in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, area))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
        if prize.plural:
            lines.append(asp.fact("plural", pid))
        for gender in sorted(prize.genders):
            lines.append(asp.fact("wears", gender, pid))
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
    ap = argparse.ArgumentParser(description="Cozy bridge cautionary world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories")
    ap.add_argument("--seed", type=int, default=None, help="random seed")
    ap.add_argument("--all", action="store_true", help="render curated stories")
    ap.add_argument("--trace", action="store_true", help="print world trace")
    ap.add_argument("--qa", action="store_true", help="print QA output")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible stories via ASP")
    ap.add_argument("--verify", action="store_true", help="verify ASP matches python gates")
    ap.add_argument("--show-asp", action="store_true", help="print ASP facts and rules")
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

    place, act, prize_id = rng.choice(sorted(candidates))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, act, prize_id, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        hero_name=params.name,
        hero_type=params.gender,
        hero_traits=[params.trait, "steady"],
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
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible (place, activity, prize) combos:")
        for place, act, prize in combos:
            genders = sorted(g for p, a, pr, g in stories if (p, a, pr) == (place, act, prize))
            print(f"  {place:12} {act:12} {prize:10}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(c) for c in CURATED]
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
            header = f"### {p.name}: {p.activity} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
