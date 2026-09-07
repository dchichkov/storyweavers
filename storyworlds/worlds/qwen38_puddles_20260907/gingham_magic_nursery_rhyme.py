#!/usr/bin/env python3
"""A gingham patch, a magic button, and a nursery rhyme that makes the patch grow.

Build the physics first: a torn dress creates a problem. A magic gingham patch
offers a solution, but it only works if sung to properly. Different problems
permit different actions: sing the rhyme, fix the button, or sew the patch.
Record each turn after changing state, then derive QA from those events.
Names and wording are not the source of plot variation.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, replace
from typing import Callable, Optional

# The example must run directly as well as through the exporter.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Body regions, used for the patch-coverage constraint.
REGIONS = {"skirt", "bodice"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, mother, father, patch, dress, button ...
    label: str = ""                # short reference, e.g. "patch", "gingham"
    phrase: str = ""               # full noun phrase, e.g. "a red and white gingham patch"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None   # who has to clean up after this object
    worn_by: Optional[str] = None
    region: str = ""                  # where a worn item sits: skirt | bodice
    magical: bool = False
    covers: set[str] = field(default_factory=set)   # regions the patch mends
    guards: set[str] = field(default_factory=set)
    plural: bool = False              # "buttons" -> them, "patch" -> it
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the cottage"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)   # which activities this place supports


@dataclass
class Activity:
    """A magical thing the hero loves to do."""
    id: str
    verb: str            # after "wanted to ..."             : "sing the nursery rhyme"
    gerund: str          # after "loved playing ... and ..." : "singing the nursery rhyme"
    mess: str            # mess kind key, one of MESS_KINDS  : "torn"
    soil: str            # how the prize gets ruined         : "torn and ragged"
    zone: set[str]       # body regions the activity affects: {"skirt"}
    weather: str         # "rainy" | "sunny" | ""
    keyword: str = ""    # topic word for generation prompts : "gingham"
    tags: set[str] = field(default_factory=set)   # world-knowledge topics it touches


@dataclass
class Prize:
    """The thing the hero loves and wears, that the messy activity would ruin."""
    label: str
    phrase: str
    type: str
    region: str          # skirt | bodice  -- where it sits on the body
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})  # who plausibly wears it


@dataclass
class Gear:
    """A patch mends a mess; replacement clothes remove the prize from exposure."""
    id: str
    label: str
    covers: set[str]     # regions it shields
    guards: set[str]     # mess kinds it neutralizes
    plural: bool = False
    replaces: bool = False
    magical: bool = False


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str = ""
    result: str = ""


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()          # splash zone of the activity in play
        self.weather: str = ""
        self.activity: Optional[Activity] = None
        self.active_actor: str = ""
        self.turn = 0
        self.history: list[Event] = []
        self.facts: dict = {}

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str, mess: str) -> bool:
        """Is `region` shielded by some protective gear the actor is wearing?"""
        return any(g.protective and region in g.covers and mess in g.guards
                   for g in self.worn_items(actor))

    # -- narration helpers --------------------------------------------------
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def record(self, kind: str, text: str, *, cause: str = "", result: str = "",
               actor: str = "", target: str = "prize") -> None:
        self.history.append(Event(
            kind=kind, actor=actor or self.facts["hero"].id, target=target, text=text,
            cause=cause, result=result,
        ))
        self.say(text)

    def copy(self) -> "World":
        """Throwaway clone used for forward-simulation (prediction)."""
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.activity = self.activity
        clone.active_actor = self.active_actor
        clone.turn = self.turn
        clone.paragraphs = [[]]            # predictions are silent
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_tear(world: World) -> list[str]:
    """actor messy + worn item in the splash zone & uncovered -> mess + dirty."""
    out: list[str] = []
    if world.activity is None:
        return out
    actor = world.get(world.active_actor)
    mess = world.activity.mess
    for item in world.worn_items(actor):
        if item.protective or item.region not in world.zone:
            continue
        if world.covered(actor, item.region, mess):
            continue
        sig = ("tear", item.id, mess, world.turn)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters[mess] += 1
        item.meters["dirty"] += 1
        out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} "
                   f"got {world.activity.soil}.")
    return out


def _r_workload(world: World) -> list[str]:
    """worn item dirty -> its caretaker has more work."""
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        if item.meters["cleaning_due"] >= THRESHOLD:
            continue
        world.fired.add(("work", item.id, world.turn))
        item.meters["cleaning_due"] = 1
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"Now {carer.label} had some mending to do.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="tear", tag="physical", apply=_r_tear),
    Rule(name="workload", tag="physical", apply=_r_workload),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (forward chaining to fixpoint)."""
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* concern and a *reasonable* fix.
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    """Would this activity actually mess up this prize (right body region)?"""
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    """Match the mess and region, or replace the at-risk clothes entirely."""
    for gear in GEAR:
        if prize.region in gear.covers and (gear.replaces or activity.mess in gear.guards):
            return gear
    return None


# ---------------------------------------------------------------------------
# Prediction: the parent runs the world model forward on a copy to foresee the
# mess before deciding what to say.
# ---------------------------------------------------------------------------
def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    """Simulate the activity silently and report whether the prize is ruined."""
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "sing": "the melody made the air feel like a soft blanket",
        "sew": "the needle danced like a happy bee",
    }.get(activity.id, "it made the day feel full of magic")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was warm, and the sunbeam waited nearby."
    if activity.weather == "rainy":
        return f"The air smelled fresh, and {setting.place} shone after the rain."
    if setting.place == "the garden":
        return "The garden was bright, and the flowers looked ready for little visits."
    return f"{setting.place.capitalize()} looked wide and ready for play."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("This place does not support that activity.")
    world.turn += 1
    world.activity = activity
    world.active_actor = actor.id
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.meters["play_steps"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)

SOLUTIONS = {
    "temptation": ("sing", "sew"),
    "splash": ("sew", "change"),
    "wrong_cover": ("sew", "change"),
    "missing_gear": ("fetch", "dry_game"),
}


def dress(world: World, gear: Gear) -> None:
    hero, parent, prize = (world.facts[k] for k in ("hero", "parent", "prize"))
    for item in world.worn_items(hero):
        if item.id != prize.id:
            item.worn_by = None
    # Old clothes replace treasured clothes; they are not magically waterproof.
    changing = gear.replaces or (gear.id == "boots" and prize.type == "shoes")
    if changing:
        prize.worn_by = None
        prize.meters["stored"] = 1
    world.add(Entity(
        id=gear.id, type="gear", label=gear.label, owner=hero.id,
        caretaker=parent.id, worn_by=hero.id, region=prize.region,
        protective=not gear.replaces, covers=set(gear.covers),
        guards=set(gear.guards), plural=gear.plural,
    ))
    world.facts["gear"] = gear


def begin_problem(world: World) -> None:
    f = world.facts
    hero, parent, prize, act = (f[k] for k in ("hero", "parent", "prize", "activity"))
    name, pos, pw = hero.id, hero.pronoun("possessive"), parent.label_word.capitalize()
    risk = predict_mess(world, hero, act, prize.id)
    if not risk["soiled"]:
        raise StoryError("The story needs a real concern about these clothes.")
    f["predicted_soil"], f["predicted_workload"] = act.soil, risk["workload"]
    world.para()
    if f["problem"] == "temptation":
        hero.memes["conflict"] += 1
        cause = f"{name} wanted to {act.verb}, but {pos} {prize.label} could get {act.soil}."
        result = f"{name} paused to think of a way to play without spoiling {prize.it()}."
        text = (f'{cause} "Just a little?" {hero.pronoun()} asked, taking a step forward. '
                f'"Look at what you are wearing," {pw} said. {name} looked down, '
                f'then back at the tempting spot. {result}')
        if hero.memes["impatience"] >= THRESHOLD:
            text += f' {name} folded {pos} arms, then slowly let them fall.'
    elif f["problem"] == "splash":
        _do_activity(world, hero, act, narrate=False)
        hero.memes["regret"] += 1
        f["ever_soiled"] = True
        cause = f"{name} began {act.gerund} before protecting {pos} {prize.label}."
        result = f"The {prize.label} got {act.soil}, so there was mending to do."
        keep = "these" if prize.plural else "this"
        text = (f'{cause} {result} {name} stopped and touched the mark. '
                f'"Oh, I wanted to keep {keep} nice," {hero.pronoun()} whispered. '
                f'{pw.capitalize()} knelt nearby. "We can work out what to do next."')
    elif f["problem"] == "wrong_cover":
        wrong = next(g for g in GEAR if not g.replaces and prize.region not in g.covers)
        dress(world, wrong)
        if not predict_mess(world, hero, act, prize.id)["soiled"]:
            raise StoryError("The unsuitable cover must leave the prize exposed.")
        hero.memes["curiosity"] += 1
        body_words = {"skirt": "skirt", "bodice": "bodice"}
        covered = " and ".join(body_words[r] for r in sorted(wrong.covers))
        cause = (f"{name} tried {wrong.label}, which covered {pos} {covered} "
                 f"but left {pos} {prize.label} uncovered.")
        result = f"The {prize.label} were still exposed." if prize.plural else f"The {prize.label} was still exposed."
        text = (f'{cause} {result} "I thought I was ready," {name} said. '
                f'{pw.capitalize()} helped {hero.pronoun("object")} look at where '
                f'the mess would reach. "A cover has to be in the right place."')
        if hero.memes["curiosity"] >= THRESHOLD:
            text += f' {name} pointed from the cover to the clothes, checking the gap.'
    else:
        world.get("kit").meters["available"] = 0
        hero.memes["disappointment"] += 1
        cause = "Their bag of magic patches was still at home."
        result = f"{name} could not start {act.gerund} in {pos} treasured {prize.label} without getting {prize.it()} messy."
        text = (f'{name} searched beside {pw}, then behind the bench. No bag. '
                f'{cause} {result} "I forgot it," {pw} admitted. '
                f'{name} let out a long sigh. The whole outing seemed about to shrink.')
    world.record(f["problem"], text, cause=cause, result=result)


def choose_solution(world: World) -> None:
    f = world.facts
    hero, parent, prize, act = (f[k] for k in ("hero", "parent", "prize", "activity"))
    name, pos, pw = hero.id, hero.pronoun("possessive"), parent.label_word.capitalize()
    solution = f["solution"]
    world.para()
    if solution == "dry_game":
        hero.memes["curiosity"] += 1
        cause = f"{name} wanted to keep {pos} {prize.label} clean and stay with {pw}."
        result = f"{name} chose to draw their play idea instead of doing the messy activity."
        world.record("choose_drawing", f'{cause} "Could we make a picture of it?" '
                     f'{hero.pronoun()} asked. {pw.capitalize()} found paper and crayons '
                     f'in a pocket. {result}', cause=cause, result=result)
        return
    if solution == "fetch":
        world.get("kit").meters["available"] = 1
        hero.memes["patience"] += 1
        cause = "The magic patches were at home, so staying by the empty bench would not help."
        result = f"{name} and {pw} went home together and brought the bag back."
        world.record("fetch", f'"Let\'s go and get it," {name} decided. '
                     f'{result} On the way, {name} carried one handle and {pw} '
                     f'carried the other. This time they put the bag where they could see it.',
                     cause=cause, result=result)
    if solution == "clean":
        # Washing settles the actual cleaning debt; the next play can soil it again.
        parent.meters["workload"] -= prize.meters["cleaning_due"]
        for key in {"torn", "dirty", "cleaning_due"}:
            prize.meters[key] = 0
        hero.memes["care"] += 1
        cause = f"The mark on the {prize.label} would not disappear just because {name} stopped playing."
        result = f"{name} helped {pw} wash the mark out at home, and they waited until the {prize.label} dried."
        world.record("wash", f'"I can help with the cleaning," {name} said. {result} '
                     f'When they returned, {name} checked the clothes before taking another step.',
                     cause=cause, result=result)
    if solution == "change":
        if world.get("kit").meters["available"] < THRESHOLD:
            raise StoryError("The spare clothes are in the missing kit.")
        label = "spare socks and old shoes" if prize.region == "feet" else "old play clothes"
        spare = Gear(id="spares", label=label, covers={prize.region}, guards=set(),
                     plural=True, replaces=True)
        dress(world, spare)
        hero.memes["care"] += 1
        cause = f"{name} could put the treasured {prize.label} away instead of trying to cover {prize.it()}."
        result = f"With {pw}'s help, {name} changed into {label} and stored the {prize.label} in the bag."
        world.record("change", f'"Can I wear my old things?" {name} asked. {result} '
                     f'"These can get messy," {hero.pronoun()} said, giving a little twirl.',
                     cause=cause, result=result)
        return
    if world.get("kit").meters["available"] < THRESHOLD:
        raise StoryError("Fetch the missing kit before taking clothes out of it.")
    gear = select_gear(act, prize)
    if gear is None:
        raise StoryError("No suitable clothes are available.")
    dress(world, gear)
    # A forecast is a gate on the choice, not a substitute for the final action.
    if predict_mess(world, hero, act, prize.id)["soiled"]:
        raise StoryError("The chosen clothes do not protect the prize.")
    if prize.worn_by is None:
        cause = f"The {prize.label} could stay clean in the bag while {name} wore other clothes."
        result = f"{name} put on {gear.label} and packed the {prize.label} away with {pw}."
    else:
        cause = f"The {gear.label.removeprefix('an ').removeprefix('a ')} would cover the {prize.label} where the mess could reach {prize.it()}."
        result = f"{name} put on {gear.label}, and {pw} checked the fit."
    hero.memes["care"] += 1
    world.record("fit", f'{result} {cause} "Now I can try," {name} said. '
                 f'{pw.capitalize()} nodded and made room beside the play spot.',
                 cause=cause, result=result)


def finish(world: World) -> None:
    f = world.facts
    hero, parent, prize, act = (f[k] for k in ("hero", "parent", "prize", "activity"))
    name, pos, pw = hero.id, hero.pronoun("possessive"), parent.label_word.capitalize()
    world.para()
    if f["solution"] == "dry_game":
        picture = world.add(Entity(id="picture", type="drawing", label="picture", owner=hero.id))
        picture.meters["finished"] = 1
        hero.memes["joy"] += 1
        spot = "at the table" if world.setting.indoor else "under the shelter"
        cause = f"They drew {spot}, away from the mess, so the {prize.label} stayed clean."
        result = f"{name} drew a picture of {act.gerund}, and {pw} added two little smiling faces."
        world.record("draw", f'{result} {cause} At the bottom, {name} added a space '
                     f'for tomorrow\'s adventure. {pw.capitalize()} held up their picture '
                     f'while {name} pressed the last corner flat.', cause=cause, result=result,
                     target=picture.id)
    else:
        _do_activity(world, hero, act, narrate=False)
        f["played"] = True
        result_kind = {"sing": "melody", "sew": "stitch"}[act.id]
        result_object = world.add(Entity(id="play_result", type=result_kind,
                                         label=result_kind, owner=hero.id))
        result_object.meters["made"] = 1
        if prize.meters["dirty"] >= THRESHOLD:
            cause = f"The {prize.label} still had the earlier mark and were waiting in the bag to be washed." if prize.plural else f"The {prize.label} still had the earlier mark and was waiting in the bag to be washed."
        elif prize.worn_by is None:
            cause = f"The {prize.label} stayed clean inside the bag, away from the messy game."
        else:
            cause = f"The cover kept the {prize.label} clean even while {name} played."
        result = f"{name} finally enjoyed {act.gerund}, with {pw} watching nearby."
        image = {
            "sing": f"A ring of ripples spread out from {name}'s next small song.",
            "sew": f"{name} held out a hand, and stitches ticked a soft tune around them.",
        }[act.id]
        world.record("play", f'{result} {cause} {image}', cause=cause, result=result)
    hero.memes["conflict"] = 0
    hero.memes["disappointment"] = 0
    hero.memes["regret"] = 0
    hero.memes["love"] += 1
    f["resolved"] = True


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Lily", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother",
         *, problem: str = "temptation", solution: str = "cover") -> World:
    if problem not in SOLUTIONS or solution not in SOLUTIONS[problem]:
        raise StoryError("This response does not fit the problem.")
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["playful", "stubborn"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural, worn_by=hero.id,
    ))
    kit = world.add(Entity(id="kit", type="bag", label="bag of play clothes", owner=parent.id))
    kit.meters["available"] = 1
    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=None,
                       problem=problem, solution=solution, played=False,
                       ever_soiled=False, resolved=False)
    hero.memes.update(love_play=1, love=1, desire=1)
    hero.memes["curiosity"] = float("curious" in hero.traits)
    hero.memes["impatience"] = float("stubborn" in hero.traits)
    pos, pw = hero.pronoun("possessive"), parent.label_word
    openings = {
        "temptation": f"{hero.id} reached {setting.place} with {pos} {pw} and could hardly stand still.",
        "splash": f"{hero.id} had been looking forward to {activity.gerund} all morning.",
        "wrong_cover": f'"I can get ready by myself," {hero.id} told {pos} {pw} at {setting.place}.',
        "missing_gear": f"At {setting.place}, {hero.id} found the perfect spot for {activity.gerund}.",
    }
    world.record("arrive", f'{openings[problem]} {setting_detail(setting, activity)} '
                 f'{hero.id}, a {hero.traits[1]} child, was wearing {prize.phrase}, a gift from {pos} {pw}. '
                 f'{hero.pronoun().capitalize()} loved {prize.it()}, but '
                 f'{activity_delight(activity)}.')
    begin_problem(world)
    choose_solution(world)
    finish(world)
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "cottage": Setting(place="the cottage", indoor=True, affords={"sing", "sew"}),
}

ACTIVITIES = {
    # singing splashes skirt only -- NOT the bodice (so a bodice patch is
    # not at risk here, which is why bodice+sing is rejected, cf. the README).
    "sing": Activity(
        id="sing",
        verb="sing the nursery rhyme",
        gerund="singing the nursery rhyme",
        mess="torn",
        soil="torn and ragged",
        zone={"skirt"},
        weather="",
        keyword="gingham",
        tags={"gingham", "magic"},
    ),
    # sewing splashes everything, so it *does* reach the bodice -- bodice+sew is the
    # reasonable counterpart that a bodice patch genuinely fixes.
    "sew": Activity(
        id="sew",
        verb="sew with magic thread",
        gerund="sewing with magic thread",
        mess="torn",
        soil="torn and ragged",
        zone={"skirt", "bodice"},
        weather="",
        keyword="gingham",
        tags={"gingham", "magic", "sewing"},
    ),
}

# Order matters: more specific gear first, full-body fallback last.  Each gear
# only protects the regions it actually covers (the core reasonableness rule).
GEAR = [
    Gear(
        id="skirt_patch",
        label="a gingham skirt patch",
        covers={"skirt"},
        guards={"torn"},
        magical=True,
    ),
    Gear(
        id="bodice_patch",
        label="a gingham bodice patch",
        covers={"bodice"},
        guards={"torn"},
        magical=True,
    ),
    Gear(
        id="playclothes",
        label="old play clothes",
        covers={"skirt", "bodice"},
        guards=set(),
        plural=True,
        replaces=True,
    ),
]

PRIZES = {
    "skirt": Prize(
        label="skirt",
        phrase="a pretty gingham skirt",
        type="skirt",
        region="skirt",
        plural=False,
    ),
    "bodice": Prize(
        label="bodice",
        phrase="a red and white gingham bodice",
        type="bodice",
        region="bodice",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["playful", "curious", "stubborn", "cheerful", "spirited", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(place, activity, prize) triples that pass the reasonableness constraint."""
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in sorted(setting.affords):
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
    problem: str = "temptation"
    solution: str = "cover"


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.  These are answerable WITHOUT
# the story; they explain the *elements* the world is built from.
KNOWLEDGE = {
    "gingham": [("What is gingham?",
                 "Gingham is a type of checked fabric, often red and white, "
                 "that looks like a grid of squares.")],
    "magic": [("What is magic in a story?",
               "Magic is a special power that can do things we cannot do in real "
               "life, like making patches grow or mending tears.")],
    "sewing": [("Why can sewing be messy?",
                "Sewing can drop threads and needles, and fabric can get frayed. "
                "Magic thread can help, but it still takes care.")],
    "torn": [("Why do torn clothes need to be mended?",
              "Torn clothes are mended to close the gap so they stay strong and "
              "keep you warm and comfortable.")],
    "skirt_patch": [("What is a skirt patch for?",
                     "A skirt patch is a piece of fabric sewn over a tear in a "
                     "skirt to make it whole again.")],
    "bodice_patch": [("What does a bodice patch do?",
                      "A bodice patch is a piece of fabric sewn over a tear in the "
                      "top part of a dress or shirt to keep it from unraveling.")],
    "playclothes": [("What are old play clothes?",
                     "Old play clothes are clothes you do not mind getting dirty, "
                     "so it is fine if they get torn or messy.")],
}
KNOWLEDGE_ORDER = ["gingham", "magic", "sewing", "torn", "skirt_patch", "bodice_patch", "playclothes"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    premise = {
        "temptation": "pauses before getting treasured clothes torn",
        "splash": "gets treasured clothes torn before thinking ahead",
        "wrong_cover": "finds that a chosen patch does not protect the right place",
        "missing_gear": "discovers that the bag of magic patches was left at home",
    }[f["problem"]]
    response = {
        "cover": "chooses suitable patch before playing",
        "clean": "helps mend the clothes before returning to play",
        "change": "puts the treasured clothes away and changes into old things",
        "fetch": "goes home with the parent to fetch the missing bag",
        "dry_game": "chooses to draw the play idea instead",
    }[f["solution"]]
    return [
        f'Write a short story for a 3-to-5-year-old that includes "{kw}". '
        f'A child {premise}, then {response}.',
        f"Tell a gentle story about {hero.id}, {hero.pronoun('possessive')} "
        f"{parent.label_word}, and {prize.phrase} at {world.setting.place}. "
        f"The child wants to {act.verb}, but {premise} and {response}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """Explain recorded causes and outcomes, without smuggling answers into questions."""
    questions = {
        "temptation": "Why did the child pause before playing?",
        "splash": "What went wrong when the child first started playing?",
        "wrong_cover": "Why did the first patch not work?",
        "missing_gear": "Why could they not get ready right away?",
        "choose_drawing": "What different plan did the child choose, and why?",
        "fetch": "How did they get what was missing?",
        "wash": "What did they do about the tear?",
        "change": "Why did the child change clothes?",
        "fit": "How did they get ready to play?",
        "draw": "What did they make at the end?",
        "play": "What happened to the treasured clothes in the end?",
    }
    return [QAItem(question=questions[e.kind], answer=f"{e.cause} {e.result}")
            for e in world.history if e.kind in questions]


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
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
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.actor} -> {event.target}: {event.text}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="cottage",
        activity="sing",
        prize="skirt",
        name="Lily",
        gender="girl",
        parent="mother",
        trait="playful",
    ),
    StoryParams(
        place="cottage",
        activity="sew",
        prize="bodice",
        name="Mia",
        gender="girl",
        parent="mother",
        trait="curious",
        problem="splash",
        solution="change",
    ),
]
CURATED.extend([
    replace(CURATED[0], problem="temptation", solution="dry_game"),
    replace(CURATED[1], problem="wrong_cover", solution="change"),
])


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, "
                f"but {noun} {verb} on the {prize.region} -- it wouldn't get "
                f"{activity.mess}, so the parent has no honest warning. "
                f"Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the gear catalog protects {noun} "
            f"({prize.region}) from {activity.gerund}. The compromise must actually "
            f"cover the at-risk item, so this argument is rejected.)")


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return (f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s "
            f"item here; try --gender {ok}.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (prize_at_risk / select_gear / valid_combos).  The rules are inline below; the
# facts are generated from the registries above so the two can never drift.
# Uses the shared `asp` helper + clingo, imported lazily so the prose engine
# runs without them.  See `python gingham_magic_nursery_rhyme.py --verify`.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk when the activity splashes the region it is worn on.
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

% Gear is a compatible fix only when it both neutralises the mess kind AND
% covers the at-risk region (skirt patch guards torn but covers only skirt).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
% Replacement protects the prize by taking it out of the splash zone.
protects(G, A, P) :- changes_clothes(G), prize_at_risk(A, P),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
valid_plan(Place, A, P, Problem, Solution) :- valid(Place, A, P), response(Problem, Solution).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
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
        if g.replaces:
            lines.append(asp.fact("changes_clothes", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    for problem, solutions in SOLUTIONS.items():
        for solution in solutions:
            lines.append(asp.fact("response", problem, solution))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (place, activity, prize) triples."""
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    """(place, activity, prize, gender) -- gender-aware compatible stories."""
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def check_sample(sample: StorySample) -> None:
    """Check outcomes, not just the fact that generation returned some text."""
    world = sample.world
    f = world.facts
    hero, prize, act = (f[k] for k in ("hero", "prize", "activity"))
    played = f["solution"] != "dry_game"
    steps = int(f["problem"] == "splash") + int(played)
    assert hero.meters["play_steps"] == steps
    assert hero.meters[act.mess] == steps
    assert f["played"] == played and f["resolved"]
    assert bool(world.zone) == bool(steps)
    still_dirty = f["problem"] == "splash" and f["solution"] == "change"
    assert (prize.meters["dirty"] >= THRESHOLD) == still_dirty
    assert sum(e.meters["cleaning_due"] for e in world.entities.values()) == sum(
        e.meters["workload"] for e in world.characters())
    if not played:
        assert world.get("picture").meters["finished"] == 1
    if f["solution"] == "change":
        assert prize.worn_by is None and prize.meters["stored"] == 1
    assert len(world.paragraphs) >= 4 and 3 <= len(sample.story_qa) <= 4
    assert len({q.question for q in sample.story_qa}) == len(sample.story_qa)
    for event in world.history:
        assert event.actor in world.entities and event.target in world.entities
        assert event.text in sample.story
        if event.result:
            assert event.result in event.text
    assert all(q.answer.endswith(".") and len(q.answer.split()) >= 12 for q in sample.story_qa)
    assert not any(marker in sample.story for marker in ("{", "}", "__", "meters=", "memes="))


def asp_verify() -> int:
    """The static twin checks choices; executable checks prove their consequences."""
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    import asp
    plans = set(asp.atoms(asp.one_model(asp_program("#show valid_plan/5.")), "valid_plan"))
    expected = {(*combo, problem, solution) for combo in python_set
                for problem, solutions in SOLUTIONS.items() for solution in solutions}
    if clingo_set != python_set or plans != expected:
        print("MISMATCH: ASP and Python choices differ.")
        return 1
    signatures = set()
    checked = 0
    for place, activity, prize, problem, solution in sorted(expected):
        for gender in sorted(PRIZES[prize].genders):
            params = StoryParams(place=place, activity=activity, prize=prize,
                                 name="Robin", gender=gender, parent="mother",
                                 trait="curious", problem=problem, solution=solution)
            sample = generate(params)
            check_sample(sample)
            assert sample.to_dict() == generate(params).to_dict()
            signatures.add(tuple(event.kind for event in sample.world.history))
            checked += 1
    assert len(signatures) == sum(map(len, SOLUTIONS.values()))
    print(f"OK: {len(python_set)} ASP/Python combinations, {len(plans)} plans; "
          f"{checked} story/state/QA/replay checks and {len(signatures)} event paths.")
    return 0


# ---------------------------------------------------------------------------
# Standard storyworld interface (see storyworlds/AGENTS.md):
#   build_parser() -> ArgumentParser
#   resolve_params(args, rng) -> StoryParams        (random where unspecified)
#   generate(params) -> StorySample                  (the core; world -> story+QA)
#   emit(sample, ...) -> None                        (human-readable output)
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a tear, a magic patch. "
                    "Unspecified choices are picked at random (seeded).")
    # A small, debuggable set of pins; any omitted choice is randomized.
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--problem", choices=SOLUTIONS)
    ap.add_argument("--solution", choices=sorted({s for choices in SOLUTIONS.values() for s in choices}))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    # Clingo (ASP) modes -- the inline declarative reasoner (needs clingo).
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the *explicit* options describe an invalid story."""
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
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    problems = [p for p, choices in SOLUTIONS.items()
                if (args.problem is None or p == args.problem)
                and (args.solution is None or args.solution in choices)]
    if not problems:
        raise StoryError("That solution does not fit the requested problem.")
    problem = rng.choice(problems)
    solution = args.solution or rng.choice(SOLUTIONS[problem])
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        problem=problem,
        solution=solution,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    if (params.place, params.activity, params.prize) not in valid_combos():
        raise StoryError("The place, activity, and clothing do not form a valid combination.")
    if params.gender not in PRIZES[params.prize].genders:
        raise StoryError(explain_gender(params.prize, params.gender))
    if params.name in {"Parent", "prize", "kit", "picture", "play_result", "spares", *(g.id for g in GEAR)}:
        raise StoryError("The character name must not collide with an object id.")
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait], params.parent, problem=params.problem, solution=params.solution)
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
    if args.n < 1:
        raise SystemExit("-n must be at least 1")

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
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                raise SystemExit(str(err)) from err
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
