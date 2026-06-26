#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/wax_scalp_smash_kindness_adventure.py
=================================================================================================================

A standalone *story world* sketch for "Wax, Scalp, and the Smash of Kindness".

Initial story (used to build a world model):
---
Once upon a time, there was a little cheerful boy named Theo with a tuft of
soft hair on his scalp. He loved going to the bright harbor with his big
sister Ada. One warm day, Ada bought Theo a brand-new yellow boat. The hull
was painted in cheerful stripes and the deck shone with a clean coat of wax.
Theo carried the boat everywhere and called her the "Yellow Star."

One sunny morning, Theo and Ada walked down to the rocky shore. Theo wanted
to push the boat straight into the surf, but Ada held up a gentle hand.
"The waves will smash the wax off and leave the hull scratched," Ada said.
"You'll get the deck scuffed and the paint chipped." Theo didn't want to
listen. He tried to dash into the surf anyway, but Ada caught his shoulder.

Theo pouted and crossed his arms. "But I want to launch the Yellow Star
right now!" he said. Ada smiled and said, "How about we go home and pack
your boat in the soft travel sack first, then launch from the calm inlet
together?" Theo's face lit up and he hugged Ada. "Yay, let's do it!" he
said as they went to find the travel sack.

Causal state updates:
---
    launch a boat                 -> actor.<risk> += 1
                                    actor.joy += 1
    actor risky + carried craft   -> craft.<risk>++, craft.dirty++
    craft damaged                 -> craft.caretaker.workload += 1
    child warned & tries to dash  -> actor.defiance += 1
    sibling holds child back      -> actor.conflict += 1
    kind compromise accepted      -> actor.joy/love += 1 ; actor.conflict -> 0

Scripted social/emotional beats:
---
    warning grounded in the world model
    sibling-takes-care-of-younger sibling tone
    kindness-as-a-fix: a soft preparation that genuinely protects the prize
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

RISK_KINDS = {"wet", "scratched", "chipped", "smashed", "sandy"}

REGIONS = {"deck", "hull", "mast", "keel"}

ADVENTURE_HOOKS = {
    "harbor": "the gulls cried loud over the bright water",
    "inlet": "the small bay was still, and the water glittered like glass",
    "lagoon": "the tide pools reflected the sky and the warm sand",
    "riverbank": "the river ran quick and clear over smooth stones",
    "raft": "the raft rocked gently in the soft current",
    "pier": "the wooden pier smelled of salt and dry rope",
}

KIND_NOTES = {
    "harbor": "the dockmaster waved to the children with a kind smile",
    "inlet": "an old sailor tipped his hat and said hello",
    "lagoon": "a heron stood still in the shallows and watched them play",
    "riverbank": "a kind woman pointed to the calm spot where small boats float safely",
    "raft": "a pair of ducks swam past without fear",
    "pier": "a fisherman shared a piece of orange with the children",
}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # boy, girl, sibling, boat, sack ...
    label: str = ""                # short reference, e.g. "boat", "travel sack"
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None   # who has to mend/clean up after this object
    carried_by: Optional[str] = None
    region: str = ""                  # body region OR part of the craft
    protective: bool = False          # gear/casing that doesn't get ruined
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "sister", "woman", "aunt"}
        male = {"boy", "brother", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"sister": "sister", "brother": "brother",
                "mother": "mom", "father": "dad",
                "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    outdoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    """A risky thing the hero loves to do with the craft."""
    id: str
    verb: str            # after "wanted to ..."              : "launch the boat"
    gerund: str          # after "loved playing ... and ..." : "launching the boat"
    rush: str            # after "tried to ..."              : "run into the surf"
    risk: str            # risk kind key, one of RISK_KINDS  : "smashed"
    ruin: str            # how the prize gets ruined         : "wax stripped and hull scratched"
    zone: set[str]       # parts of the craft the activity reaches: {"deck", "hull"}
    weather: str         # "sunny" | "rainy" | "windy" | ""
    keyword: str = ""    # topic word for generation prompts
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    """The thing the hero loves and carries, that the risky activity would ruin."""
    label: str
    phrase: str
    type: str
    region: str          # deck | hull | mast | keel
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    """Protective casing / preparation offered as the kindness compromise."""
    id: str
    label: str
    covers: set[str]     # parts of the craft it shields
    guards: set[str]     # risk kinds it neutralizes
    prep: str            # body of the offer: "go home and pack the boat in the travel sack"
    tail: str            # closing clause
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

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.carried_items(actor))

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
# Causal rules.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_damage(world: World) -> list[str]:
    """actor risky + carried prize in zone & uncovered -> damage + dirty."""
    out: list[str] = []
    for actor in world.characters():
        for risk in RISK_KINDS:
            if actor.meters[risk] < THRESHOLD:
                continue
            for item in world.carried_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("damage", item.id, risk)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[risk] += 1
                item.meters["damaged"] += 1
                out.append(
                    f"The {item.label} got {risk} from the {world.setting.place}."
                )
    return out


def _r_workload(world: World) -> list[str]:
    """damaged carried prize -> its caretaker has more mending work."""
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["damaged"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("mend", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more mending for {carer.label}.")
    return out


def _r_hold_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["held_back"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="damage", tag="physical", apply=_r_damage),
    Rule(name="mending", tag="physical", apply=_r_workload),
    Rule(name="hold_conflict", tag="social", apply=_r_hold_conflict),
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
# Constraint helpers.
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear_def in GEAR:
        if activity.risk in gear_def.guards and prize.region in gear_def.covers:
            return gear_def
    return None


def predict_damage(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "ruined": bool(prize and prize.meters["damaged"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs.
# ---------------------------------------------------------------------------
def activity_spark(activity: Activity) -> str:
    return {
        "launch_surf": "the salt spray smelled bright, and the white foam looked like a race",
        "launch_inlet": "the inlet water shone flat and friendly under the sun",
        "launch_river": "the river tugged at the keel and made the deck feel alive",
        "launch_lagoon": "the lagoon glittered with tiny fish and warm sand",
        "launch_raft": "the raft rocked like a cradle in the slow current",
        "launch_pier": "the pier smelled of rope and tar, and the craft begged to be set free",
    }.get(activity.id, "it made the day feel full of small adventures")


def setting_detail(setting: Setting, activity: Activity) -> str:
    hook = ADVENTURE_HOOKS.get(setting.place, "the place felt bright and ready")
    return f"{hook.capitalize()}."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed safe and whole"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.risk] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} whose scalp caught the breeze at every new place.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved adventures at {world.setting.place} and "
        f"{activity.gerund}; {activity_spark(activity)}."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"That week, {hero.id}'s {parent.label_word} bought "
        f"{hero.pronoun('object')} {prize.phrase} with a coat of soft wax."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.carried_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"carried {prize.it()} as if the {prize.label} had been made just for "
        f"{hero.pronoun('object')}."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"rainy": "One rainy morning, ", "sunny": "One sunny morning, ",
           "windy": "One windy morning, "}.get(world.weather, "One bright morning, ")
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} "
        f"walked down to {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))
    note = KIND_NOTES.get(world.setting.place)
    if note:
        world.say(note.capitalize() + ".")


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but "
        f"{hero.pronoun('possessive')} {parent.label_word} held up a gentle hand."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_damage(world, hero, activity, prize.id)
    if not pred["ruined"]:
        return False
    world.facts["predicted_ruin"] = activity.ruin
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"The waves will smash the wax off and the hull will get {activity.ruin}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I'll have to mend {prize.it()}"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. '
              f'"Let\'s think of a kinder way."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the wish to launch was tugging hard.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_shoulder(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["held_back"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} caught "
        f"{hero.pronoun('possessive')} shoulder and said, "
        f'"You can want to {activity.verb}, and we can still choose the kind way."'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{hero.id} pouted and crossed {hero.pronoun("possessive")} arms. '
            f'"But I really want to {activity.verb}!" {hero.pronoun()} said.'
        )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.carried_by = hero.id
    if predict_damage(world, hero, activity, prize.id)["ruined"]:
        gear.carried_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} looked at the '
        f'{prize.label}, then back at {hero.id}, and smiled with kind eyes. '
        f'"How about we {gear_def.prep} and {activity.verb} together?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity,
           gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["kindness"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s face lit up and {hero.pronoun()} hugged "
        f"{hero.pronoun('possessive')} {parent.label_word}. "
        f'"Yay, let\'s do it the kind way!" {hero.pronoun()} said.'
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"{prize_was_clean(hero, prize)}, and {parent.label_word} was laughing "
        f"beside {hero.pronoun('object')} in the kind morning light."
    )


# ---------------------------------------------------------------------------
# The screenplay.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Theo", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None, parent_type: str = "sister") -> World:
    world = World(setting)
    world.weather = "" if setting.outdoor is False else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["cheerful", "bold"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the sibling"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1 -- setup.
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2 -- conflict.
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_shoulder(world, parent, hero, activity)

    # Act 3 -- kindness resolution.
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["held_back"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor": Setting(place="the harbor", outdoor=True, affords={"launch_surf", "launch_pier"}),
    "inlet": Setting(place="the inlet", outdoor=True, affords={"launch_inlet", "launch_surf"}),
    "lagoon": Setting(place="the lagoon", outdoor=True, affords={"launch_lagoon", "launch_inlet"}),
    "riverbank": Setting(place="the riverbank", outdoor=True, affords={"launch_river", "launch_raft"}),
    "raft": Setting(place="the raft dock", outdoor=True, affords={"launch_raft", "launch_river"}),
    "pier": Setting(place="the old pier", outdoor=True, affords={"launch_pier", "launch_surf"}),
}

ACTIVITIES = {
    "launch_surf": Activity(
        id="launch_surf",
        verb="launch the boat into the surf",
        gerund="launching into the surf",
        rush="run toward the surf with the boat",
        risk="smashed",
        ruin="wax stripped and the hull scratched",
        zone={"deck", "hull"},
        weather="sunny",
        keyword="surf",
        tags={"surf", "wax"},
    ),
    "launch_inlet": Activity(
        id="launch_inlet",
        verb="launch the boat in the inlet",
        gerund="launching in the inlet",
        rush="splash toward the inlet",
        risk="wet",
        ruin="wax streaked and the deck water-spotted",
        zone={"deck"},
        weather="sunny",
        keyword="inlet",
        tags={"inlet", "wax"},
    ),
    "launch_river": Activity(
        id="launch_river",
        verb="launch the boat on the river",
        gerund="launching on the river",
        rush="dash toward the river current",
        risk="chipped",
        ruin="rocks chipping the keel and scratching the wax",
        zone={"hull", "keel"},
        weather="windy",
        keyword="river",
        tags={"river", "stone"},
    ),
    "launch_lagoon": Activity(
        id="launch_lagoon",
        verb="launch the boat across the lagoon",
        gerund="launching across the lagoon",
        rush="run across the sand to the lagoon",
        risk="sandy",
        ruin="sand sticking to the wax and dulling the paint",
        zone={"deck", "hull"},
        weather="sunny",
        keyword="lagoon",
        tags={"lagoon", "sand"},
    ),
    "launch_raft": Activity(
        id="launch_raft",
        verb="push the boat off the raft",
        gerund="pushing off from the raft",
        rush="climb onto the raft with the boat",
        risk="scratched",
        ruin="planks scratching the wax and the hull",
        zone={"hull", "keel"},
        weather="windy",
        keyword="raft",
        tags={"raft", "wood"},
    ),
    "launch_pier": Activity(
        id="launch_pier",
        verb="launch the boat off the pier",
        gerund="launching off the pier",
        rush="sprint down the pier with the boat",
        risk="smashed",
        ruin="salt smashing the wax and dinging the hull",
        zone={"deck", "hull"},
        weather="sunny",
        keyword="pier",
        tags={"pier", "salt"},
    ),
}

GEAR = [
    Gear(
        id="travel_sack",
        label="travel sack",
        covers={"deck", "hull", "mast", "keel"},
        guards={"smashed", "scratched", "chipped", "sandy", "wet"},
        prep="go home and pack your boat in the soft travel sack",
        tail="walked back home to pack the boat in the soft travel sack",
    ),
    Gear(
        id="wax_cover",
        label="wax cover",
        covers={"deck"},
        guards={"wet", "sandy"},
        prep="go home and put the soft wax cover on the deck",
        tail="went to get the soft wax cover for the deck",
    ),
    Gear(
        id="hull_sleeve",
        label="hull sleeve",
        covers={"hull", "keel"},
        guards={"chipped", "scratched"},
        prep="go home and slip the hull sleeve over the bottom",
        tail="went to get the protective hull sleeve",
    ),
    Gear(
        id="burlap_wrap",
        label="burlap wrap",
        covers={"hull", "keel"},
        guards={"smashed", "scratched", "chipped"},
        prep="go home and wrap the boat in the burlap wrap",
        tail="walked home to wrap the boat in the burlap wrap",
    ),
]

PRIZES = {
    "boat": Prize(
        label="boat",
        phrase="a brand-new yellow boat with a waxed deck",
        type="boat",
        region="deck",
        genders={"girl", "boy"},
    ),
    "skiff": Prize(
        label="skiff",
        phrase="a small blue skiff with bright wax",
        type="skiff",
        region="hull",
        genders={"girl", "boy"},
    ),
    "canoe": Prize(
        label="canoe",
        phrase="a sleek red canoe with a polished wax finish",
        type="canoe",
        region="hull",
        genders={"girl", "boy"},
    ),
    "raft_model": Prize(
        label="raft",
        phrase="a toy raft with careful wax seams",
        type="raft",
        region="keel",
        genders={"girl", "boy"},
    ),
    "keelboat": Prize(
        label="keelboat",
        phrase="a stout little keelboat with a waxed shine",
        type="keelboat",
        region="keel",
        genders={"boy"},
    ),
}

GIRL_NAMES = ["Ada", "Mira", "Cleo", "Ivy", "Nora", "Wren", "Tess", "Sage"]
BOY_NAMES = ["Theo", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Otto"]
SIBLING_TYPES = ["sister", "brother"]
TRAITS = ["cheerful", "bold", "curious", "spirited", "lively", "kind"]


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
# Per-world parameters.
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
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "wax": [("What is wax used for on a boat?",
             "A coat of wax on a boat keeps water from soaking into the wood and "
             "makes the surface shine so it slips through the water more easily.")],
    "scalp": [("Why does a child's scalp need a hat in the sun?",
               "A child's scalp is thin and easily sunburned, so a hat keeps the "
               "head cool and shaded when playing outside.")],
    "surf": [("What is surf?",
              "Surf is the foamy top of waves as they roll in and break near the "
              "shore.")],
    "inlet": [("What is an inlet?",
               "An inlet is a small, calm body of water that reaches into the "
               "land from a larger sea or lake.")],
    "river": [("What makes a river run fast?",
               "A river runs fast where the ground slopes down sharply, and the "
               "water tumbles over stones as it goes.")],
    "lagoon": [("What is a lagoon?",
                "A lagoon is a shallow stretch of water cut off from the open sea "
                "by a strip of sand or coral.")],
    "raft": [("What is a raft?",
              "A raft is a flat platform of logs or planks tied together so "
              "people can float on the water.")],
    "pier": [("What is a pier?",
              "A pier is a raised wooden walkway that stretches out over the "
              "water, where boats can tie up and people can fish.")],
    "stone": [("Why are river stones slippery?",
               "River stones are slippery because the water rubs them smooth and "
               "leaves a thin film of slime on top.")],
    "sand": [("What is sand?",
              "Sand is made of tiny bits of rock and shell, and it can stick to "
              "waxed surfaces and dull their shine.")],
    "salt": [("What does salt do to a boat?",
              "Salt leaves crystals on a boat that can scratch the wax and slowly "
              "eat at the paint if it is not rinsed off.")],
    "wood": [("Why does wood need a coat of wax?",
              "Wood needs a coat of wax to keep water out, because water makes "
              "wood swell and crack.")],
}
KNOWLEDGE_ORDER = ["wax", "scalp", "surf", "inlet", "river", "lagoon",
                   "raft", "pier", "stone", "sand", "salt", "wood"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.risk
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a child, a '
        f'mess, a kindness" that includes the word "{kw}".',
        f"Tell a gentle adventure story where a {hero.type} named {hero.id} wants to "
        f"{act.verb} but {hero.pronoun('possessive')} {parent.label_word} worries "
        f"about {prize.phrase}, and they find a kind compromise.",
        f'Write a simple story that uses the noun "{kw}" and ends with a sibling '
        f"and child pausing to choose a kinder way to play.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    where = "outside" if world.setting.outdoor else "inside"
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    day = {"rainy": "rainy morning", "sunny": "sunny morning",
           "windy": "windy morning"}.get(world.weather, "bright morning")
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} visits {place} to "
                f"{act.verb} with {pos} {prize.label}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pos} {pw}. They go to {place} on a {day}, and {hero.id} is "
                f"carrying {pos} {prize.label} under one arm."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do {where} at {place} before "
                f"{pw} worried about {pos} {prize.label}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved adventures {where} and "
                f"{act.gerund}. That wish became tricky because {pos} "
                f"{prize.label} could get ruined."
            ),
        ),
        QAItem(
            question=(
                f"What new {prize.label} did {hero.id}'s {pw} buy for the "
                f"{trait} {hero.type} before "
                f"the {act.keyword or act.risk} trip to {place}?"
            ),
            answer=(
                f"{pos.capitalize()} {pw} bought {obj} {prize.phrase}. "
                f"{hero.id} loved {prize.it()} and carried {prize.it()} for the outing."
            ),
        ),
    ]
    if f.get("conflict"):
        ruin = f.get("predicted_ruin", "ruined")
        work = f.get("predicted_workload", 0)
        why = (f"{pos.capitalize()} {pw} was upset because if {hero.id} went to "
               f"{act.verb}, {pos} {prize.label} would get {ruin}")
        why += (f", and then {pw} would have to mend {prize.it()}. "
                if work >= THRESHOLD else ". ")
        why += (f"When {hero.id} tried to {act.rush.rstrip(', ')}, {pos} {pw} "
                f"held {pos} shoulder and reminded {obj} they could still want "
                f"to {act.verb} while choosing a kinder way.")
        qa.append(QAItem(
            question=(
                f"Why did {hero.id}'s {pw} worry about {pos} {prize.label} "
                f"when {trait} {hero.id} wanted to {act.verb} at {place}?"
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
                f"without ruining {pos} {prize.label}?"
            ),
            answer=(
                f"They agreed to use {gear.label} first, so {hero.id} could "
                f"{act.verb} at {place} without ruining {pos} {prize.label}. "
                f"The plan let {obj} play while {pos} {prize.label} stayed safe."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel after {pw} agreed to the {gear_plan} "
                f"plan for {act.keyword or act.risk} at {place}?"
            ),
            answer=(
                f"{hero.id} felt happy and hugged {pos} {pw} once they agreed "
                f"on the plan for {pos} {prize.label}. At the end, {sub} was "
                f"{act.gerund} with {pw} laughing nearby."
            ),
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="harbor",
        activity="launch_surf",
        prize="boat",
        name="Theo",
        gender="boy",
        parent="sister",
        trait="cheerful",
    ),
    StoryParams(
        place="inlet",
        activity="launch_inlet",
        prize="boat",
        name="Ada",
        gender="girl",
        parent="brother",
        trait="curious",
    ),
    StoryParams(  # keelboat on river
        place="riverbank",
        activity="launch_river",
        prize="keelboat",
        name="Ben",
        gender="boy",
        parent="sister",
        trait="lively",
    ),
    StoryParams(  # canoe on lagoon -> burlap wrap
        place="lagoon",
        activity="launch_lagoon",
        prize="canoe",
        name="Mira",
        gender="girl",
        parent="sister",
        trait="bold",
    ),
    StoryParams(
        place="raft",
        activity="launch_raft",
        prize="raft_model",
        name="Otto",
        gender="boy",
        parent="brother",
        trait="spirited",
    ),
    StoryParams(  # skiff off the pier
        place="pier",
        activity="launch_pier",
        prize="skiff",
        name="Cleo",
        gender="girl",
        parent="brother",
        trait="kind",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} reaches {sorted(activity.zone)}, "
                f"but {noun} {verb} on the {prize.region} -- it wouldn't get "
                f"{activity.risk}, so the sibling has no honest warning. "
                f"Try a prize carried on {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the gear catalog protects {noun} "
            f"({prize.region}) from {activity.gerund}. The kindness compromise "
            f"must actually cover the at-risk item, so this argument is rejected.)")


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return (f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s "
            f"item here; try --gender {ok}.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), carried_on(P, R).

protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     risk_of(A, M), guards(G, M),
                     covers(G, R), carried_on(P, R).
has_fix(A, P) :- protects(_, A, P).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.outdoor:
            lines.append(asp.fact("outdoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk_of", aid, a.risk))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("carried_on", pid, pr.region))
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


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a waxed boat, a kind compromise. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=SIBLING_TYPES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
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
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(SIBLING_TYPES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "bold"], params.parent)
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
            print(f"  {place:11} {act:14} {prize:11}  [{', '.join(genders)}]")
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
