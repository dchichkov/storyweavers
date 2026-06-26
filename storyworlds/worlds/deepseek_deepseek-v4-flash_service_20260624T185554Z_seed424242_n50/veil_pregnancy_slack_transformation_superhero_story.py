#!/usr/bin/env python3
"""
storyworlds/worlds/veil_pregnancy_slack_transformation_superhero_story.py
==========================================================================

A standalone story world sketch for a gentle superhero tale where a pregnant
hero's veil has too much slack and a child helps transform the problem into
a shared adventure.
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

# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "mom", "woman", "heroine"}
        male = {"boy", "father", "dad", "man", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Setting, Activity, Prize, Gear
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the house"
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


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_transformation_fail(world: World) -> list[str]:
    """If the hero wears the veil but slack >= threshold, no transformation."""
    out: list[str] = []
    for actor in world.characters():
        if actor.type not in {"heroine", "hero"}:
            continue
        veil = next((e for e in world.worn_items(actor) if e.type == "veil"), None)
        if veil is None:
            continue
        if veil.meters["slack"] >= THRESHOLD and veil.meters["slack"] > veil.meters["tight"]:
            sig = ("fail_transform", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["frustration"] += 1
            out.append("The veil hung loose. No sparkle, no power.")
    return out


def _r_transform_success(world: World) -> list[str]:
    """If veil tight enough and worn, transformation succeeds."""
    out: list[str] = []
    for actor in world.characters():
        if actor.type not in {"heroine", "hero"}:
            continue
        veil = next((e for e in world.worn_items(actor) if e.type == "veil"), None)
        if veil is None:
            continue
        if veil.meters["tight"] >= THRESHOLD:
            sig = ("success_transform", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["power"] += 1
            actor.memes["joy"] += 1
            out.append(f"The veil tightened with a soft glow, and {actor.label_word} felt ready.")
    return out


def _r_child_help(world: World) -> list[str]:
    """When child suggests a fix (gear) and parent accepts, reduce slack."""
    out: list[str] = []
    for child in world.characters():
        if child.type not in {"girl", "boy"}:
            continue
        if child.memes["suggested"] < THRESHOLD:
            continue
        parent = next((e for e in world.characters() if e.caretaker == child.id or e.owner == child.id), None)
        if parent is None:
            continue
        veil = next((e for e in world.worn_items(parent) if e.type == "veil"), None)
        if veil is None:
            continue
        sig = ("tighten", veil.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        veil.meters["slack"] = max(0.0, veil.meters["slack"] - 1.0)
        veil.meters["tight"] += 1.0
        child.memes["joy"] += 1
        parent.memes["love"] += 1
        out.append("Together they made the veil snug again.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="transform_fail", tag="physical", apply=_r_transformation_fail),
    Rule(name="transform_success", tag="physical", apply=_r_transform_success),
    Rule(name="child_help", tag="social", apply=_r_child_help),
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


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_success(world: World, actor: Entity, veil_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["power"] = 0
    sim.get(actor.id).memes["joy"] = 0
    _wear_veil(sim, sim.get(actor.id), sim.get(veil_id), narrate=False)
    propagate(sim, narrate=False)
    return {"power": sim.get(actor.id).meters["power"] >= THRESHOLD,
            "joy": sim.get(actor.id).memes["joy"] >= THRESHOLD}


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return "the veil shimmered like a secret only the two of them shared"


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return "The living room was warm, and the mirror on the wall still shone."
    return "The backyard was quiet, except for a soft breeze."


def prize_was_tight(hero: Entity, veil: Entity) -> str:
    return f"{hero.pronoun('possessive')} veil stayed snug and ready"


def _wear_veil(world: World, actor: Entity, veil: Entity, narrate: bool = True) -> None:
    if veil.id not in world.entities:
        return
    veil.worn_by = actor.id
    world.zone = {"head", "shoulders"}
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    desc = f"little {trait} {hero.type}".strip()
    if hero.kind == "character" and hero.type in {"heroine", "hero"}:
        world.say(f"{hero.id} was a {desc} who wore a magical veil when duty called.")
    else:
        world.say(f"{hero.id} was a {desc} who always noticed when something was wrong.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}; {activity_delight(activity)}.")


def gives(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"{hero.label_word} gave {parent.label_word} {prize.phrase} long ago, a gift of trust.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} held {hero.pronoun('possessive')} {prize.label} carefully, as if it held all the stars.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One ordinary morning, "
    go = "were in" if world.setting.indoor else "went to"
    world.say(f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} {go} {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} right away, but the magic in the veil felt dull.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_success(world, parent, prize.id)
    if pred["power"]:
        return False
    world.facts["predicted_fail"] = True
    world.facts["predicted_help"] = not pred["joy"]
    clause = "The veil is too loose. I won't be able to transform safely."
    if not pred["joy"]:
        clause += " And that makes me a little sad."
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. "We need a plan."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the worry, but {hero.pronoun('possessive')} heart still sparkled.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(f"but {hero.pronoun('possessive')} {parent.label_word} gently took {hero.pronoun('possessive')} hand and said, 'We can still be heroes. Let's do this together.'")


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["frustration"] >= THRESHOLD:
        world.say(f'{hero.id} pouted and crossed {hero.pronoun("possessive")} arms. "But I wanted the sparkle!" {hero.pronoun()} said.')


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
    if predict_success(world, parent, prize.id)["power"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f'{hero.pronoun("possessive").capitalize()} {parent.label_word} looked at the veil, then at {hero.id}, and smiled. "How about we {gear_def.prep} and try again?"')
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id}'s face lit up and {hero.pronoun()} hugged {hero.pronoun('possessive')} {parent.label_word}. 'Yes! Let's make it work!'")
    world.say(f"They {gear_def.tail}. The veil glowed. {prize_was_tight(parent, prize)}, and {parent.label_word} was a hero again, with {hero.id} cheering beside {hero.pronoun('object')}.")


# ---------------------------------------------------------------------------
# tell
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Emma", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = ""

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "helpful"]),
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="the parent",
        caretaker=hero.id,
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
        meters={"slack": 2.0, "tight": 0.0},
    ))

    # Act 1
    introduce(world, hero)
    loves_activity(world, hero, activity)
    gives(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    # Act 3
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "living_room": Setting(place="the living room", indoor=True, affords={"transform"}),
    "bedroom": Setting(place="the bedroom", indoor=True, affords={"transform"}),
    "backyard": Setting(place="the backyard", indoor=False, affords={"transform"}),
}

ACTIVITIES = {
    "transform": Activity(
        id="transform",
        verb="transform into a superhero",
        gerund="turning the veil into superhero power",
        rush="throw the veil over her shoulders",
        mess="loose",
        soil="too loose to work",
        zone={"head", "shoulders"},
        keyword="veil",
        tags={"veil", "superhero", "transformation"},
    ),
}

PRIZES = {
    "veil": Prize(
        label="veil",
        phrase="a shimmering, secret veil",
        type="veil",
        region="shoulders",
    ),
}

GEAR = [
    Gear(
        id="belt",
        label="a tiny belt",
        covers={"shoulders"},
        guards={"loose"},
        prep="fasten the veil with this tiny belt",
        tail="fastened the tiny belt around the veil",
    ),
    Gear(
        id="pin",
        label="a safety pin",
        covers={"shoulders"},
        guards={"loose"},
        prep="pin the veil in place with this safety pin",
        tail="pinned the veil snugly",
    ),
    Gear(
        id="ribbon",
        label="a ribbon",
        covers={"shoulders"},
        guards={"loose"},
        prep="tie the veil with this ribbon",
        tail="tied the ribbon around the veil",
    ),
]

GIRL_NAMES = ["Emma", "Mia", "Zoe", "Lily", "Ava", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["brave", "curious", "stubborn", "cheerful", "spirited", "helpful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
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
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "veil": [("What is a veil?", "A veil is a piece of cloth that can hide your face or make you feel magical.")],
    "superhero": [("What does a superhero do?", "A superhero uses special powers to help people and keep them safe.")],
    "transformation": [("What does transformation mean?", "Transformation means changing into something different, like putting on a costume and becoming a hero.")],
    "slack": [("What does 'slack' mean in a piece of cloth?", "Slack means the cloth is loose and not pulled tight.")],
}
KNOWLEDGE_ORDER = ["veil", "superhero", "transformation", "slack"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or "veil"
    return [
        f'Write a short story for a child that includes the words "{kw}" and "transformation".',
        f"Tell a gentle story where a {hero.type} named {hero.id} helps {hero.pronoun('possessive')} {parent.label_word} fix a loose veil so the superhero transformation can work.",
        f'Write a simple story that uses the noun "{kw}" and ends with a parent and child working together to make magic happen.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the story about when {hero.id} visits {place} to {act.verb}?",
            answer=f"It is about a little {trait} {hero.type} named {hero.id} and {pos} {pw}. They are at {place}, and the magic veil is loose."
        ),
        QAItem(
            question=f"What did {trait} {hero.id} love to do with the veil before {pw} worried about the slack?",
            answer=f"{trait.capitalize()} {hero.id} loved {act.gerund}. That wish became tricky because the veil had too much slack."
        ),
        QAItem(
            question=f"What gift did {pw} give to {hero.id} long ago?",
            answer=f"{pw.capitalize()} gave {obj} {prize.phrase}. {hero.id} held it like a treasure."
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"Why did {pw} worry about the veil when {trait} {hero.id} wanted to {act.verb}?",
            answer=f"{pos.capitalize()} {pw} worried because the veil was too loose. It would not transform into superhero power. When {hero.id} tried to {act.rush.rstrip(', ')}, {pw} took {pos} hand and said they could fix it together."
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help {trait} {hero.id} and {pw} achieve the transformation?",
            answer=f"They used {gear.label} to make the veil tight. Then the glow returned and {pw} transformed."
        ))
        qa.append(QAItem(
            question=f"How did {trait} {hero.id} feel after the veil was fixed and the transformation worked?",
            answer=f"{hero.id} felt happy and hugged {pos} {pw}. At the end they were a team, and everyone was safe."
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
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
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
# CLI / trace
# ---------------------------------------------------------------------------
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
    StoryParams(
        place="living_room",
        activity="transform",
        prize="veil",
        name="Emma",
        gender="girl",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        place="bedroom",
        activity="transform",
        prize="veil",
        name="Leo",
        gender="boy",
        parent="father",
        trait="brave",
    ),
    StoryParams(
        place="backyard",
        activity="transform",
        prize="veil",
        name="Mia",
        gender="girl",
        parent="mother",
        trait="helpful",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    return (f"(No story: the veil slack problem only happens with shoulders. "
            f"Gear must help tighten it.)")


def explain_gender(prize_id: str, gender: str) -> str:
    return ""


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp as asp_mod
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp_mod.fact("setting", pid))
        if s.indoor:
            lines.append(asp_mod.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp_mod.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp_mod.fact("activity", aid))
        lines.append(asp_mod.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp_mod.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp_mod.fact("prize", pid))
        lines.append(asp_mod.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp_mod.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp_mod.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp_mod.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp_mod.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp_mod.fact("covers", g.id, r))
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


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero veil slack transformation story.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id,
                       name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "helpful"], params.parent)
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
        print(f"{len(triples)} compatible (place, activity, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories
                             if (pl, a, pr) == (place, act, prize))
            print(f"  {place:14} {act:10} {prize:6}  [{', '.join(genders)}]")
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
