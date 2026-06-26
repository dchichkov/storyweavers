#!/usr/bin/env python3
"""
storyworlds/worlds/nozzle_bad_ending_curiosity_tall_tale.py
============================================================

A tall‑tale storyworld about a curious child and a giant water nozzle that
always ends in a flood (bad ending).  Domain: a ranch or town where a colossal
brass nozzle is the source of mischief.  The child’s curiosity leads to ignoring
a parent’s warning, the nozzle is pulled, and a geyser destroys everything.

Style: tall tale – exaggeration, hyperbole, folk‑tale rhythm.  The story
includes the word “nozzle” prominently.
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
MESS_KINDS = {"soaked", "flooded", "splashed"}
REGIONS = {"feet", "legs", "torso", "head"}


# ---------------------------------------------------------------------------
# Entity – one class for characters and objects
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"             # "character" | "thing"
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
# Typed registries
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# World: state + narration
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


def _r_soak(world: World) -> list[str]:
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
                sig = ("soak", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"got {mess} and dirty."
                )
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
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for {carer.label}.")
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
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="grab_conflict", tag="social", apply=_r_grab_conflict),
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
# Constraint helpers – based on regions and mess kinds
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


# ---------------------------------------------------------------------------
# Prediction – used by parent to warn
# ---------------------------------------------------------------------------
def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Tall‑tale flavour helpers
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "nozzle": "the brass nozzle gleamed like a giant acorn, and the thought of water made his fingers tingle",
    }.get(activity.id, "it felt grand as a rodeo")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, and the nozzle hung on the wall like a sleeping dragon."
    return f"The {setting.place.removeprefix('the ')} stretched wide, and the sun beat down on the brass nozzle as if daring anyone to touch it."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive').capitalize()} {prize.label} stayed clean"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


# ---------------------------------------------------------------------------
# Screenplay verbs (tall‑tale tone)
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was the most curious {hero.type} in all of {world.setting.place} – "
              f"eyes like a hawk, hands like a bear cub, and a heart full of wonder.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} lived for {activity.gerund}; "
        f"{activity_delight(activity)}."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"That week, {hero.id}'s {parent.label_word} bought "
        f"{hero.pronoun('object')} {prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"wore {prize.it()} like a badge of honour."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} were at {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} spotted the big brass nozzle and wanted right then to {activity.verb}. "
        f"But {hero.pronoun('possessive')} {parent.label_word} held up a hand."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"That nozzle will drench your {prize.label} {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += ", and I’ll be scrubbing for a week"
    world.say(f'"{clause}!" warned {hero.pronoun("possessive")} {parent.label_word}.')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"But curiosity burned in {hero.id}’s belly like a hot coal.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} grabbed "
        f"{hero.pronoun('possessive')} hand and said, "
        f'"Curiosity is a fine thing, but that nozzle is a giant’s toy!"'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{hero.id} pouted and stomped. "I just want to {activity.verb}!" '
            f'{hero.pronoun()} cried.'
        )


def disaster_bad_ending(world: World, hero: Entity, parent: Entity,
                        activity: Activity, prize: Entity) -> None:
    """The nozzle is pulled, a geyser erupts, and everything is flooded.
    This is the bad ending – no compromise."""
    world.say(
        f"Before {parent.label_word} could stop {hero.pronoun('object')}, "
        f"{hero.id} yanked the great brass nozzle."
    )
    world.say(
        f"A wall of water shot up – as high as a barn, as loud as thunder! "
        f"The geyser soaked {world.setting.place}, carrying away fences, "
        f"chicken coops, and {hero.pronoun('possessive')} brand‑new {prize.label}."
    )
    world.say(
        f"{parent.label_word} let out a sigh as wide as the prairie. "
        f"{hero.id} stood dripping, eyes wide, knowing the damage was done."
    )
    # Record bad ending fact
    world.facts["bad_ending"] = True
    world.facts["flood"] = True


# ---------------------------------------------------------------------------
# Main tell function – three acts with bad ending
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Billy", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["curious"] + (hero_traits or ["bold", "fearless"]),
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="the parent"
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    # The nozzle as a world object (not worn)
    world.add(Entity(
        id="nozzle", kind="thing", type="nozzle", label="brass nozzle",
        phrase="a giant brass nozzle as big as a horse's head",
    ))

    # Act 1 – setup
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2 – conflict
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    # Act 3 – bad ending (no compromise, no gear offered)
    world.para()
    pout(world, hero, activity)
    disaster_bad_ending(world, hero, parent, activity, prize)

    world.facts.update(
        hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
        activity=activity, setting=setting,
        conflict=hero.memes["grabbed_by"] >= THRESHOLD,
        bad_ending=True,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries (tall‑tale flavoured)
# ---------------------------------------------------------------------------
SETTINGS = {
    "ranch": Setting(place="the ranch", indoor=False, affords={"nozzle"}),
    "farm": Setting(place="the farm", indoor=False, affords={"nozzle"}),
    "town_square": Setting(place="the town square", indoor=False, affords={"nozzle"}),
}

ACTIVITIES = {
    "nozzle": Activity(
        id="nozzle",
        verb="play with the big water nozzle",
        gerund="playing with the big water nozzle",
        rush="grab the brass nozzle",
        mess="soaked",
        soil="soaked through and through",
        zone={"feet", "legs", "torso", "head"},
        weather="",
        keyword="nozzle",
        tags={"nozzle", "water", "flood"},
    ),
}

PRIZES = {
    "boots": Prize(label="boots", phrase="cowboy boots with shiny spurs",
                   type="boots", region="feet", plural=True),
    "hat": Prize(label="hat", phrase="a ten‑gallon hat as wide as a wagon wheel",
                 type="hat", region="head"),
    "shirt": Prize(label="shirt", phrase="a colourful bandana shirt",
                   type="shirt", region="torso"),
}

GEAR = []   # No gear – every story ends badly (bad ending)

GIRL_NAMES = ["Annie", "Sue", "Daisy", "Belle", "Calamity"]
BOY_NAMES = ["Billy", "Pecos", "Jed", "Cody", "Tex"]
TRAITS = ["curious", "bold", "fearless", "adventurous", "stubborn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# StoryParams (domain‑specific)
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
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "nozzle": [("What is a nozzle?",
                "A nozzle is the end of a hose or pipe that water shoots out of. "
                "Some nozzles are small, but in tall tales they can be as big as a horse.")],
    "water": [("Why can a water nozzle cause a flood?",
               "If the nozzle is huge and nobody turns it off, water can pour out "
               "faster than a river and cover everything nearby.")],
    "flood": [("What happens during a flood?",
               "Water rises and covers the land, soaking everything and sometimes "
               "carrying things away. It can be very scary.")],
}
KNOWLEDGE_ORDER = ["nozzle", "water", "flood"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = "nozzle"
    return [
        f'Write a tall‑tale story for a young child that includes the word "{kw}".',
        f"Tell a wild, exaggerated story about a {hero.type} named {hero.id} "
        f"whose curiosity leads to trouble with a giant {kw}.",
        f'Write a story where a {prize.label} is ruined by a huge spray of water '
        f'from a {kw}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "curious"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the story about when {hero.id} visits {place}?",
            answer=f"It is about a curious {trait} {hero.type} named {hero.id} "
                   f"and {pos} {pw}. They are at {place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the nozzle?",
            answer=f"{hero.id} wanted to {act.verb}. {sub} was so curious that "
                   f"{sub} could not resist.",
        ),
        QAItem(
            question=f"What did {pw} say when {hero.id} reached for the nozzle?",
            answer=f"{pw} warned {obj} that {pos} {prize.label} would get {act.soil}, "
                   f"but {hero.id} was too curious to listen.",
        ),
    ]
    if f.get("bad_ending"):
        qa.append(QAItem(
            question=f"What happened after {hero.id} pulled the nozzle?",
            answer=f"A giant geyser exploded, flooding {place} and ruining "
                   f"{pos} {prize.label}. The whole place was soaked and {pw} "
                   f"was very upset. It was a bad ending.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
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
        if hasattr(e, 'protective') and e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ranch", activity="nozzle", prize="boots",
                name="Billy", gender="boy", parent="mother", trait="curious"),
    StoryParams(place="farm", activity="nozzle", prize="hat",
                name="Sue", gender="girl", parent="father", trait="bold"),
    StoryParams(place="town_square", activity="nozzle", prize="shirt",
                name="Pecos", gender="boy", parent="mother", trait="fearless"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    return (f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, "
            f"but {noun} is worn on the {prize.region} – it wouldn't get "
            f"{activity.mess}. Choose a prize worn on {sorted(activity.zone)}.)")


# ---------------------------------------------------------------------------
# ASP twin (inline)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P).
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
    # No gear facts – no gear exists
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
    ap = argparse.ArgumentParser(
        description="Tall‑tale storyworld: a curious child, a giant nozzle, a bad ending. "
                    "Unspecified choices are random. Always a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="curated set")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true", help="list valid combos via clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP gate")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not prize_at_risk(act, pr):
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
    return StoryParams(
        place=place, activity=activity, prize=prize_id,
        name=name, gender=gender, parent=parent, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "stubborn"], params.parent)
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
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories
                             if (pl, a, pr) == (place, act, prize))
            print(f"  {place:12} {act:8} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
