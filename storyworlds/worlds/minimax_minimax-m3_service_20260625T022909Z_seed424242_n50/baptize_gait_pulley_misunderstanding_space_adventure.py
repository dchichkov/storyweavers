#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/baptize_gait_pulley_misunderstanding_space_adventure.py
============================================================================================================================

A standalone *story world* sketch: a small TinyStories-style "space adventure"
with a *misunderstanding* at its heart, dressed in the vocabulary of a moon base
where gear, helpers, and a tricky climb have to come together.

Seed premise (the tale we are modeling):
---
Mira is a little astronaut in training at Moon Base Three. She has a brand-new
silver helmet she is supposed to be *baptized* into today -- that is, the base
captain has a small ceremony to mark a brand-new helmet being used for the
very first time on an actual walk. Mira loves her helmet.

Outside, near the crater rim, the team is using a long rope and a *pulley* to
haul heavy crates up the slope. Mira wants to be the one to climb the rope and
help. Her *gait* (the way she walks in her bulky suit) is wobbly, and the
captain warns her: the rope is tricky, the *pulley* sings a sharp warning, and
she could fall if she tries to climb in a hurry.

Mira hears only "you can climb" and thinks the captain *misunderstood* her --
she was only going to *baptize* her helmet, not race up the rope. She stamps
her boot, marches toward the rope, and the pulley whirs in the thin moon air.

The pulley operator (a kind engineer) gently stops her. The misunderstanding
clears: Mira was never in trouble; she just wanted to *baptize* her new helmet
on the rim, and the captain only meant she could climb after the ceremony.
Mira laughs, ties her boots tighter, and together they haul the rope so Mira
can take her slow, careful first walk along the crater rim. The pulley sings
softly, her new helmet catches the sun, and her gait is steady at last.

Causal state updates:
---
    do "climb_rope"            -> actor.tiredness += 1
                                 actor.altitude += 1
    gear (helmet) on actor     -> actor.protected = true
    pulley whirs in alert      -> risk.winch = true
    helper stops actor         -> actor.misunderstanding_cleared += 1
    gait wobbles               -> actor.balance -= 1   (recovered by tied boots)

Scripted social/emotional beats:
---
    promise misunderstood      -> actor.misunderstanding += 1
    helper explains kindly     -> actor.misunderstanding -> 0 ; actor.joy += 1
    slow careful first walk    -> actor.gait_steady = true
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

# Make the shared result containers importable when this script is run directly
# (``python storyworlds/worlds/<this>.py``): add the package dir (storyworlds/)
# to the path so ``results`` resolves regardless of the current directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Regions on a suited astronaut, used for the gear-coverage constraint.
REGIONS = {"feet", "legs", "torso", "head"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, captain, engineer, helmet, rope, pulley ...
    label: str = ""                # short reference, e.g. "helmet", "pulley"
    phrase: str = ""               # full noun phrase, e.g. "a brand-new silver helmet"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""                  # where a worn item sits: feet | legs | torso | head
    protective: bool = False          # gear that protects the wearer
    covers: set[str] = field(default_factory=set)   # regions the gear shields
    plural: bool = False              # "boots" -> them, "helmet" -> it
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "captain_f", "engineer_f", "woman"}
        male = {"boy", "captain_m", "engineer_m", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"captain_m": "captain", "captain_f": "captain",
                "engineer_m": "engineer", "engineer_f": "engineer"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the moon base"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)   # which activities this place supports


@dataclass
class Activity:
    """A small mission beat the hero can do on the moon base."""
    id: str
    verb: str            # after "wanted to ..."              : "baptize my new helmet"
    gerund: str          # after "loved ... and ..."          : "baptizing her new helmet"
    rush: str            # after "tried to ..."               : "march right up to the rope"
    mess: str            # risk kind key, one of MESS_KINDS  : "tall"
    soil: str            # how the gear gets ruined          : "set the wrong way"
    zone: set[str]       # body regions the activity stresses : {"head"}
    weather: str         # "starry" | "dusty" | ""
    keyword: str = ""    # topic word for generation prompts : "baptize"
    tags: set[str] = field(default_factory=set)   # world-knowledge topics it touches


@dataclass
class Prize:
    """The thing the hero loves and wears, that the misadventure would ruin."""
    label: str
    phrase: str
    type: str
    region: str          # feet | legs | torso | head -- where it sits on the body
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})  # who plausibly wears it


@dataclass
class Gear:
    """A piece of safety gear the base officer offers as a *steady* alternative."""
    id: str
    label: str
    covers: set[str]     # regions it shields / steadies
    guards: set[str]     # risk kinds it neutralizes
    prep: str            # body of the offer: "tie your boots tight first"
    tail: str            # closing clause: "tied their boots tight and waited"
    plural: bool = False


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()          # risk zone of the activity in play
        self.weather: str = ""
        # Facts recorded during the screenplay, read back by the Q&A generators.
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

    def covered(self, actor: Entity, region: str) -> bool:
        """Is `region` shielded by some protective gear the actor is wearing?"""
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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

    def copy(self) -> "World":
        """Throwaway clone used for forward-simulation (prediction)."""
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
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


def _r_dizzy(world: World) -> list[str]:
    """actor dizzy + worn item in the risk zone & uncovered -> ruined gear."""
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["dizzy"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("dizzy", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["tall"] += 1
            item.meters["ruined"] += 1
            out.append(
                f"{actor.pronoun('possessive').capitalize()} {item.label} was "
                f"set the wrong way in the wobble."
            )
    return out


def _r_winch(world: World) -> list[str]:
    """pulleymeter high -> winch warning (recorded as a fact)."""
    for ent in world.entities.values():
        if ent.type != "pulley":
            continue
        if ent.meters["whir"] < THRESHOLD:
            continue
        sig = ("winch", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.facts["winch_warning"] = True
        return ["__winch__"]               # marker; narrated by the screenplay beat
    return []


def _r_clear(world: World) -> list[str]:
    """Helper explained -> misunderstanding counter resets, joy ticks up."""
    for actor in world.characters():
        if actor.memes["explained"] < THRESHOLD or actor.memes["misunderstanding"] < THRESHOLD:
            continue
        sig = ("clear", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["misunderstanding"] = 0.0
        actor.memes["joy"] += 1
        return ["__clear__"]
    return []


def _r_steady(world: World) -> list[str]:
    """Boots tied + balance recovered -> gait_steady flag (narrated in finale)."""
    for actor in world.characters():
        if actor.meters["boots_tied"] < THRESHOLD or actor.meters["balance"] <= 0.0:
            continue
        sig = ("steady", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["gait_steady"] += 1
        return ["__steady__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="dizzy_gear", tag="physical", apply=_r_dizzy),
    Rule(name="winch", tag="physical", apply=_r_winch),
    Rule(name="clear_misunderstanding", tag="social", apply=_r_clear),
    Rule(name="steady_gait", tag="physical", apply=_r_steady),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* ceremony + a *reasonable* fix.
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    """Would this activity actually stress this prize (right body region)?"""
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    """The compatible steadying move: gear that guards the risk AND covers
    the at-risk region.  Returns None when no reasonable gear exists (e.g.
    a chest harness for a helmet), which is exactly the case we refuse."""
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


# ---------------------------------------------------------------------------
# Prediction: the helper runs the world model forward on a copy to foresee the
# wobble before deciding what to say.
# ---------------------------------------------------------------------------
def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    """Simulate the activity silently and report whether the prize is ruined."""
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["ruined"] >= THRESHOLD),
        "balance": sim.get(actor.id).meters.get("balance", 0.0),
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def activity_detail(activity: Activity) -> str:
    return {
        "baptize": "today the silver helmet was going to catch its very first moonlight",
        "rim_walk": "the rim was waiting, lit soft and gold along the edge",
        "rope_climb": "the rope climbed up to a quiet ring of rocks",
        "winch_test": "the winch hummed in the thin air like a small song",
    }.get(activity.id, "the day felt ready for a careful first try")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return (f"Inside, the {setting.place.removeprefix('the ')} hummed softly, "
                f"and the helmet rack waited in the corner.")
    if activity.weather == "starry":
        return f"The sky above {setting.place} was bright with a thousand small stars."
    if activity.weather == "dusty":
        return f"A soft moon-dust haze drifted over {setting.place}."
    return f"{setting.place.capitalize()} shimmered, quiet and round, under a thin silver sky."


def prize_was_safe(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed safe"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return                                  # this place can't host the activity
    world.zone = set(activity.zone)
    actor.meters["dizzy"] += 1
    actor.meters["tiredness"] += 1
    actor.meters["balance"] -= 0.5
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who lived on a small moon base in a quiet silver suit.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund} on slow afternoons; "
        f"{activity_detail(activity)}."
    )


def gets_gear(world: World, officer: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"This week, {officer.label_word} {officer.id} handed "
        f"{hero.id} {hero.pronoun('object')} {prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"wore {prize.it()} as if the whole moon had been saved for {hero.pronoun('object')}."
    )


def arrive(world: World, hero: Entity, officer: Entity, activity: Activity) -> None:
    day = {"starry": "One starry morning, ", "dusty": "One dusty morning, "}.get(
        world.weather, "One quiet morning, ")
    go = "was inside" if world.setting.indoor else "stepped out to"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} "
        f"{officer.label_word} {go} {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, officer: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, and {hero.pronoun()} "
        f"tugged {hero.pronoun('possessive')} {officer.label_word}'s sleeve."
    )


def warn(world: World, officer: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    """The officer foresees the wobble via the world model and warns about it."""
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_balance"] = pred["balance"]
    clause = (f"You'll wobble on the line, and your {prize.label} could be "
              f"{activity.soil}")
    if pred["balance"] <= 0.0:
        clause += ", and we don't want a tumble today"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {officer.label_word} said. '
              f'"Let\'s make a small plan first."')
    return True


def misunderstands(world: World, hero: Entity, officer: Entity, activity: Activity) -> None:
    """The misunderstanding: hero heard a *promise* where the officer said *prepare*."""
    hero.memes["misunderstanding"] += 1
    world.say(
        f"But {hero.id} only caught the words 'you can climb' and thought "
        f"{officer.label_word} meant right now."
    )
    world.say(
        f"It was a small misunderstanding -- {hero.pronoun()} thought the ceremony "
        f"was already done, and {hero.pronoun('possessive')} {officer.label_word} "
        f"thought {hero.pronoun()} had heard the careful part."
    )


def rush(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} nodded too fast and tried to {activity.rush},")


def stop(world: World, helper: Entity, hero: Entity, officer: Entity, activity: Activity) -> None:
    hero.memes["explained"] += 1
    propagate(world, narrate=False)             # fires the clear->joy rule
    world.say(
        f"but the kind {helper.label_word}, {helper.id}, stepped in front of the rope "
        f"and said it gently: 'You can climb -- after the baptism. Let's do the "
        f"small ceremony first, and then we go together.'"
    )


def pouts(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["misunderstanding"] >= THRESHOLD:
        world.say(
            f'{hero.id} pouted and stamped one soft moon-boot. '
            f'"But I really want to {activity.verb}!" {hero.pronoun()} said.'
        )


def compromise(world: World, officer: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    """Offer gear -- but only the gear that actually steadies the at-risk prize,
    and only if the world model then predicts no wobble (a compatible move)."""
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {officer.label_word} looked at the '
        f'{prize.label}, then back at {hero.id}, and smiled. '
        f'"How about we {gear_def.prep}, and then {activity.verb} together?"'
    )
    return gear_def


def accept(world: World, officer: Entity, hero: Entity, activity: Activity, prize: Entity,
           gear_def: Gear, helper: Entity) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["misunderstanding"] = 0.0
    hero.meters["boots_tied"] += 1
    hero.meters["balance"] += 1.0
    propagate(world, narrate=False)             # fires the steady-gait rule
    world.say(
        f"{hero.id}'s face lit up and {hero.pronoun()} hugged "
        f"{hero.pronoun('possessive')} {officer.label_word}. "
        f'"Yay, let\'s do it!" {hero.pronoun()} said.'
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"{prize_was_safe(hero, prize)}, and {helper.label_word} {helper.id} was "
        f"smiling beside {hero.pronoun('object')} as the small silver pulley "
        f"sang its quiet song."
    )


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mira", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None,
         officer_type: str = "captain_m",
         helper_type: str = "engineer_f") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["playful", "stubborn"]),
    ))
    officer = world.add(Entity(
        id="Officer", kind="character", type=officer_type, label="the officer"))
    helper = world.add(Entity(
        id="Helper", kind="character", type=helper_type, label="the helper"))
    pulley = world.add(Entity(
        id="Pulley", type="pulley", label="the small silver pulley"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1 -- setup: who, what they love, the new gear they wear.
    introduce(world, hero)
    loves_activity(world, hero, activity)
    gets_gear(world, officer, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2 -- the misunderstanding: hero hears a promise where the officer
    # said a plan, and tries to march up to the rope.
    world.para()
    arrive(world, hero, officer, activity)
    wants(world, hero, officer, activity)
    warn(world, officer, hero, activity, prize)
    misunderstands(world, hero, officer, activity)
    rush(world, hero, activity)
    pulley.meters["whir"] += 1
    stop(world, helper, hero, officer, activity)
    pulley.meters["whir"] += 1

    # Act 3 -- resolution: a compatible move (steadying gear) clears the
    # misunderstanding and gives the hero a slow, careful first walk.
    world.para()
    pouts(world, hero, activity)
    gear_def = compromise(world, officer, hero, activity, prize)
    if gear_def:
        accept(world, officer, hero, activity, prize, gear_def, helper)

    # Record facts for the Q&A generators (grounded in the simulated world).
    world.facts.update(hero=hero, officer=officer, helper=helper, prize=prize,
                       prize_cfg=prize_cfg, activity=activity, setting=setting,
                       gear=gear_def,
                       conflict=hero.memes["misunderstanding"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "crater": Setting(place="the crater rim", indoor=False,
                      affords={"baptize", "rim_walk", "rope_climb", "winch_test"}),
    "hangar": Setting(place="the airlock hangar", indoor=True,
                      affords={"baptize", "winch_test"}),
    "outpost": Setting(place="the south outpost", indoor=False,
                       affords={"baptize", "rim_walk", "winch_test"}),
}

ACTIVITIES = {
    # baptize = a small ceremony to mark a brand-new helmet's first use on a
    # real moon walk. It stresses the head, not the feet.
    "baptize": Activity(
        id="baptize",
        verb="baptize my new helmet",
        gerund="baptizing her new helmet in the soft moon light",
        rush="march right up to the rope to climb first",
        mess="tall",
        soil="set the wrong way in the wobble",
        zone={"head"},
        weather="starry",
        keyword="baptize",
        tags={"baptize", "helmet", "ceremony"},
    ),
    "rim_walk": Activity(
        id="rim_walk",
        verb="walk the rim at sunset",
        gerund="walking the rim at sunset",
        rush="march right up to the rope to climb first",
        mess="tall",
        soil="set the wrong way in the wobble",
        zone={"legs", "torso"},
        weather="starry",
        keyword="rim_walk",
        tags={"rim", "gait", "steady"},
    ),
    "rope_climb": Activity(
        id="rope_climb",
        verb="climb the rope by the pulley",
        gerund="climbing the rope by the pulley",
        rush="march right up to the rope to climb first",
        mess="tall",
        soil="set the wrong way in the wobble",
        zone={"feet", "legs", "torso"},
        weather="dusty",
        keyword="pulley",
        tags={"pulley", "gait", "rope"},
    ),
    "winch_test": Activity(
        id="winch_test",
        verb="test the little silver pulley",
        gerund="testing the little silver pulley",
        rush="march right up to the rope to climb first",
        mess="tall",
        soil="set the wrong way in the wobble",
        zone={"torso"},
        weather="",
        keyword="pulley",
        tags={"pulley", "winch"},
    ),
}

# Order matters: more specific gear first, full-body fallback last.  Each gear
# only steadies the regions it actually covers (the core reasonableness rule).
GEAR = [
    Gear(
        id="boots",
        label="moon boots",
        covers={"feet"},
        guards={"tall"},
        prep="tie your moon boots tight first",
        tail="tied their moon boots tight and waited",
        plural=True,
    ),
    Gear(
        id="harness",
        label="a small chest harness",
        covers={"torso"},
        guards={"tall"},
        prep="clip the small chest harness on first",
        tail="clipped the small chest harness on",
    ),
    Gear(
        id="belt",
        label="a steady walking belt",
        covers={"torso", "legs"},
        guards={"tall"},
        prep="buckle on the steady walking belt first",
        tail="buckled on the steady walking belt",
    ),
    Gear(
        id="hood",
        label="a soft cloth hood",
        covers={"head"},
        guards={"tall"},
        prep="tuck a soft cloth hood under the helmet first",
        tail="tucked the soft cloth hood under the helmet",
    ),
    Gear(
        id="full_suit",
        label="the full moon suit",
        covers={"feet", "legs", "torso", "head"},
        guards={"tall"},
        prep="zip into the full moon suit first",
        tail="zipped into the full moon suit",
    ),
]

PRIZES = {
    "helmet": Prize(
        label="helmet",
        phrase="a brand-new silver helmet",
        type="helmet",
        region="head",
    ),
    "boots": Prize(
        label="boots",
        phrase="sturdy new moon boots",
        type="boots",
        region="feet",
        plural=True,
    ),
    "suit": Prize(
        label="suit",
        phrase="a new soft grey suit",
        type="suit",
        region="torso",
    ),
    "belt": Prize(
        label="belt",
        phrase="a new steady walking belt",
        type="belt",
        region="torso",
    ),
    "hood": Prize(
        label="hood",
        phrase="a new soft cloth hood",
        type="hood",
        region="head",
    ),
}

GIRL_NAMES = ["Mira", "Nova", "Lyra", "Vega", "Iris", "Juno", "Luna", "Stella", "Thea", "Wren"]
BOY_NAMES = ["Orin", "Pip", "Kai", "Tomo", "Rin", "Soren", "Aki", "Beck", "Cato", "Eli"]
OFFICER_TYPES = ["captain_m", "captain_f"]
HELPER_TYPES = ["engineer_f", "engineer_m"]
TRAITS = ["playful", "curious", "stubborn", "cheerful", "spirited", "lively"]


def valid_combos() -> list[tuple[str, str]]:
    """(place, activity, prize) triples that pass the reasonableness constraint."""
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
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
    officer: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.  These are answerable WITHOUT
# the story; they explain the *elements* the world is built from.
KNOWLEDGE = {
    "baptize": [("What does it mean to baptize a new helmet?",
                 "To baptize a helmet means to mark the first time it is worn on a "
                 "real moon walk, usually with a small quiet ceremony so the helmet "
                 "is ready to keep the wearer safe.")],
    "helmet": [("Why do astronauts wear helmets on the moon?",
                "Astronauts wear helmets on the moon because the air is very thin "
                "and the helmet holds the air they need to breathe.")],
    "gait": [("What does gait mean?",
              "A gait is the way someone walks, especially when their suit makes "
              "each step a little wobbly.")],
    "pulley": [("What is a pulley?",
                "A pulley is a small wheel that a rope slides over to lift heavy "
                "things, and on the moon it sings a thin song as it turns.")],
    "rope": [("Why do astronauts use ropes on the moon?",
              "Astronauts use ropes on the moon so they can pull themselves up "
              "slopes and stay safe on the rim.")],
    "winch": [("What is a winch?",
               "A winch is a small machine that pulls a rope tight so heavy crates "
               "can be lifted without anyone getting tired.")],
    "moon": [("Why is the moon a good place for an adventure?",
              "The moon is a good place for an adventure because the air is thin, "
              "the sky is dark, and every step is light and careful.")],
    "boots": [("What are moon boots for?",
               "Moon boots are sturdy boots that keep small astronaut feet warm "
               "and steady on the soft moon dust.")],
    "harness": [("What does a chest harness do?",
                 "A chest harness clips around the chest and ties to a rope so the "
                 "wearer cannot fall far if they slip.")],
    "belt": [("What is a steady walking belt?",
              "A steady walking belt is a strap you buckle on to help you walk "
              "in a straight line in a heavy suit.")],
    "hood": [("Why wear a soft cloth hood under a helmet?",
              "A soft cloth hood sits under the helmet to keep the head warm and "
              "to help the helmet sit just right.")],
    "full_suit": [("What does the full moon suit do?",
                   "The full moon suit covers the whole body and keeps the wearer "
                   "warm, safe, and ready for a careful walk.")],
}
KNOWLEDGE_ORDER = ["baptize", "helmet", "gait", "pulley", "rope", "winch", "moon",
                   "boots", "harness", "belt", "hood", "full_suit"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, officer, act, prize = f["hero"], f["officer"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a small '
        f'misunderstanding, a kind helper, a careful first try" that includes '
        f'the word "{kw}".',
        f"Tell a gentle space-adventure story where a little {hero.type} named "
        f"{hero.id} wants to {act.verb} but hears a promise where the officer "
        f"said a plan, and a kind helper clears the small misunderstanding.",
        f'Write a simple story that uses the noun "{kw}" and ends with a careful '
        f"first walk and a steady gait.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, officer, helper, prize, act = (f["hero"], f["officer"], f["helper"],
                                         f["prize"], f["activity"])
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    where = "inside" if world.setting.indoor else "outside"
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    day = {"starry": "starry morning", "dusty": "dusty morning"}.get(
        world.weather, "quiet morning")
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} steps out at {place} to "
                f"{act.verb} in {pos} {prize.label}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pos} {officer.label_word}. They step out at {place} on a "
                f"{day}, and {hero.id} is wearing {pos} {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do {where} at {place} before "
                f"the small misunderstanding about the rope climb?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved {act.gerund} {where} at "
                f"{place}. That wish got tricky when {pos} {prize.label} was "
                f"brand new and the rope waited by the pulley."
            ),
        ),
        QAItem(
            question=(
                f"What new {prize.label} did {officer.label_word} {officer.id} hand "
                f"to the {trait} {hero.type} before the misunderstanding at {place}?"
            ),
            answer=(
                f"{officer.label_word.capitalize()} {officer.id} handed {obj} "
                f"{prize.phrase}. {hero.id} loved {prize.it()} and wore "
                f"{prize.it()} for the outing."
            ),
        ),
    ]
    # The featured question: how the misunderstanding happened and how the
    # kind helper cleared it.
    if f.get("conflict"):
        soil = f.get("predicted_soil", "set the wrong way")
        why = (f"{pos.capitalize()} {officer.label_word} was being careful because "
               f"if {hero.id} ran to the rope, {pos} {prize.label} could be {soil}.")
        why += (f" But {hero.id} heard only the words 'you can climb' and thought "
                f"the ceremony was already done. That was the small misunderstanding.")
        why += (f" {helper.label_word.capitalize()} {helper.id} stepped in and said it "
                f"gently: the climb could happen -- after the baptism, together.")
        qa.append(QAItem(
            question=(
                f"What was the small misunderstanding between {hero.id} and "
                f"{pos} {officer.label_word} about the rope at {place}?"
            ),
            answer=why,
        ))
    if f.get("resolved"):
        gear = f["gear"]
        gear_plan = gear.label
        if gear_plan.startswith(("a ", "an ")):
            gear_plan = gear_plan.split(" ", 1)[1]
        qa.append(QAItem(
            question=(
                f"How did {gear.label} help {trait} {hero.id} {act.verb} at {place} "
                f"after the misunderstanding about the rope?"
            ),
            answer=(
                f"They agreed to use {gear.label} first, so {hero.id} could "
                f"{act.verb} at {place} without {pos} {prize.label} being set "
                f"the wrong way. The plan let {obj} try while the gear kept "
                f"{pos} steps steady."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel after {officer.label_word} and "
                f"{helper.label_word} {helper.id} agreed to the {gear_plan} plan?"
            ),
            answer=(
                f"{hero.id} felt happy and hugged {pos} {officer.label_word} once "
                f"they agreed on the plan. At the end, {sub} was "
                f"{act.gerund} with {pos} gait steady and the small silver pulley "
                f"singing its quiet song."
            ),
        ))
    return qa


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
        lines.append(f"  {e.id:8} ({e.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="crater",
        activity="baptize",
        prize="helmet",
        name="Mira",
        gender="girl",
        officer="captain_f",
        helper="engineer_m",
        trait="playful",
    ),
    StoryParams(
        place="outpost",
        activity="rim_walk",
        prize="boots",
        name="Orin",
        gender="boy",
        officer="captain_m",
        helper="engineer_f",
        trait="curious",
    ),
    StoryParams(
        place="crater",
        activity="rope_climb",
        prize="suit",
        name="Nova",
        gender="girl",
        officer="captain_f",
        helper="engineer_f",
        trait="lively",
    ),
    StoryParams(
        place="hangar",
        activity="winch_test",
        prize="belt",
        name="Kai",
        gender="boy",
        officer="captain_m",
        helper="engineer_m",
        trait="spirited",
    ),
    StoryParams(
        place="crater",
        activity="baptize",
        prize="hood",
        name="Lyra",
        gender="girl",
        officer="captain_m",
        helper="engineer_f",
        trait="cheerful",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} stresses {sorted(activity.zone)}, "
                f"but {noun} {verb} on the {prize.region} -- it wouldn't be set "
                f"the wrong way, so the officer has no honest warning. Try a "
                f"prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the gear catalog steadies {noun} "
            f"({prize.region}) for {activity.gerund}. The compromise must actually "
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
# runs without them.  See `python <this>.py --verify`.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk when the activity stresses the region it is worn on.
prize_at_risk(A, P) :- stresses(A, R), worn_on(P, R).

% Gear is a compatible fix only when it both neutralises the risk AND
% covers the at-risk region (boots guard the wobble but cover only feet).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     risk_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
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
        lines.append(asp.fact("risk_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("stresses", aid, r))
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
    """Clingo's version of valid_combos(): (place, activity, prize) triples."""
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    """(place, activity, prize, gender) -- gender-aware compatible stories."""
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
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
# Standard storyworld interface (see storyworlds/AGENTS.md):
#   build_parser() -> ArgumentParser
#   resolve_params(args, rng) -> StoryParams        (random where unspecified)
#   generate(params) -> StorySample                  (the core; world -> story+QA)
#   emit(sample, ...) -> None                        (human-readable output)
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small space adventure with a "
                    "misunderstanding, steadying gear, and a careful first try. "
                    "Unspecified choices are picked at random (seeded).")
    # A small, debuggable set of pins; any omitted choice is randomized.
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--officer", choices=OFFICER_TYPES)
    ap.add_argument("--helper", choices=HELPER_TYPES)
    ap.add_argument("--name")
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
    officer = args.officer or rng.choice(OFFICER_TYPES)
    helper = args.helper or rng.choice(HELPER_TYPES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        officer=officer,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "stubborn"], params.officer, params.helper)
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
            print(f"  {place:9} {act:11} {prize:8}  [{', '.join(genders)}]")
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
