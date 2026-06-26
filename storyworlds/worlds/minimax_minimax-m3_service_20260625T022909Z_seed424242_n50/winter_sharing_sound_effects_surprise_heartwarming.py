#!/usr/bin/env python3
"""
storyworlds/worlds/winter_sharing_sound_effects_surprise_heartwarming.py
======================================================================

A standalone *story world* for the "Winter Sharing / Sound Effects / Surprise"
tale and its close, constraint-checked variations.  The world is modelled as
typed entities with physical ``meters`` and emotional ``memes``; simulated
state drives prose.

Source tale (used to seed the world model):
---
On a snowy afternoon, Mira and her little brother Theo walked to the town
square with their grandmother. A small bell on the bakery door made a soft
*ting* when they pushed it open. The baker smiled and offered them two warm
blueberry scones. Mira thought about keeping the bigger one for herself, but
she heard Theo shiver and saw his cold hands. She split the scones fairly and
handed him the bigger half. A tiny bell from the door chime rang again --
*ting ting!* -- and the baker surprised them with two hot mugs of cocoa on the
house. They sat by the window, sipped cocoa, and the world outside felt softer.

Causal state updates:
---
    share a treat   -> giver.warmth += 1, receiver.warmth += 1
                       giver.kindness += 1, receiver.joy += 1
    sibling shivers -> sibling.chill  += 1 (drives the consideration beat)
    surprise gift   -> receiver.surprise += 1, giver.kindness += 1
                       receiver.warmth += 1
    bell ring       -> world.bells += 1 (a recorded counter; cues the chime)

Scripted social/emotional beats:
---
    notice shiver   -> hero.consideration += 1
    equal split     -> hero.fairness += 1, hero.kindness += 1
    kind helper     -> hero.love += 1, hero.joy += 1, hero.shyness += 1
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Body states / affordances used by the activity rules.
MESS_KINDS = {"chilled", "damp"}        # winter-specific physical states

# Sibling relationship types the world recognises.
SIB_RELATIONS = {"sister", "brother"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, grandma, baker, scone, mug, bell ...
    label: str = ""                # short reference, e.g. "cocoa", "scone"
    phrase: str = ""               # full noun phrase, e.g. "a warm blueberry scone"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    giver: Optional[str] = None
    receiver: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "grandma", "woman", "lady", "baker_f"}
        male = {"boy", "father", "dad", "grandpa", "man", "baker_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the bakery"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    """The kind act the hero performs on a wintry afternoon."""
    id: str
    verb: str                  # after "decided to ..."   : "share the scone"
    gerund: str                # after "loved ..."        : "sharing scones"
    rush: str                  # after "tried to ..."     : "reach for the bigger scone"
    mess: str                  # mess kind key            : "chilled"
    zone: set[str]             # body regions affected   : {"hands"}
    season: str                # "winter"
    keyword: str = ""          # topic word for prompts   : "scone"
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    """The thing the hero has and shares."""
    label: str
    phrase: str
    type: str
    plural: bool = False
    shareable: bool = True
    pair_with: set[str] = field(default_factory=set)   # what gift goes with it


@dataclass
class SurpriseGift:
    """The unexpected thing the helper gives after the bell rings."""
    label: str
    phrase: str
    type: str
    plural: bool = False
    goes_with: set[str] = field(default_factory=set)   # treat it pairs with


@dataclass
class Helper:
    """A kind grown-up who notices and surprises the children."""
    id: str
    type: str                  # "baker" | "librarian" | "park_ranger" | "shopkeeper"
    label: str
    phrase: str                # "the friendly baker"
    verbs: list[str]           # plausible verbs for the surprise beat
    prep: str                  # after "would ..." : "warm two mugs of cocoa"
    tail: str                  # closing clause   : "brought out two warm mugs of cocoa"
    gender_pool: set[str] = field(default_factory=lambda: {"woman", "man"})


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.season: str = ""
        self.facts: dict = {}

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def held_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.held_by == actor.id]

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.season = self.season
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_warm_transfer(world: World) -> list[str]:
    """share a treat -> giver & receiver warmth / joy / kindness."""
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["shared"] < THRESHOLD or not item.giver or not item.receiver:
            continue
        sig = ("warm", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        giver = world.get(item.giver)
        receiver = world.get(item.receiver)
        giver.meters["warmth"] += 1
        receiver.meters["warmth"] += 1
        giver.memes["kindness"] += 1
        receiver.memes["joy"] += 1
        out.append(
            f"The {item.label} made {receiver.label_word or receiver.id} feel warm "
            f"all the way down to {receiver.pronoun('possessive')} toes."
        )
    return out


def _r_chill_to_warm(world: World) -> list[str]:
    """A chilled sibling who receives warmth resolves back to comfortable."""
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["chilled"] < THRESHOLD or actor.meters["warmth"] < THRESHOLD:
            continue
        sig = ("thaw", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["chilled"] = 0.0
        actor.memes["comfort"] += 1
        out.append(
            f"{actor.id} stopped shivering, and a small smile came back to "
            f"{actor.pronoun('possessive')} face."
        )
    return out


def _r_surprise_kindness(world: World) -> list[str]:
    """surprise gift -> receiver surprise + warmth, helper kindness."""
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["surprise_meter"] < THRESHOLD or not item.receiver:
            continue
        sig = ("surprise", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        receiver = world.get(item.receiver)
        receiver.memes["surprise"] += 1
        receiver.meters["warmth"] += 1
        if item.giver:
            helper = world.get(item.giver)
            helper.memes["kindness"] += 1
        out.append(
            f"It was a happy surprise, and {receiver.id}'s eyes went wide."
        )
    return out


def _r_bell_ring(world: World) -> list[str]:
    """Each bell ring adds to the world bell counter and a little chime."""
    out: list[str] = []
    if world.meters_bells is None:
        world.meters_bells = 0
    sig = ("bell", world.meters_bells)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.meters_bells += 1
    return out  # the screenplay itself narrates the onomatopoeia


CAUSAL_RULES: list[Rule] = [
    Rule(name="warm_transfer", tag="physical", apply=_r_warm_transfer),
    Rule(name="chill_to_warm", tag="physical", apply=_r_chill_to_warm),
    Rule(name="surprise_kindness", tag="social", apply=_r_surprise_kindness),
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
                if narrate:
                    produced.extend(sents)
    return produced


# World bell counter (used by the bell-ring rule + trace).
def _init_world_meters(world: World) -> None:
    world.meters_bells = 0            # type: ignore[attr-defined]


# Attach the bell-ring rule after meters_bells exists.
def _r_bell_ring_attached(world: World) -> list[str]:
    if not hasattr(world, "meters_bells"):
        world.meters_bells = 0
    if world.meters_bells >= 2:
        return []
    world.meters_bells += 1
    return [f"*ting{'!' if world.meters_bells > 1 else ''}*"]


def bell_chime(world: World, onomatopoeia: str = "*ting!*") -> None:
    """Record a bell ring; advance the rule counter; narrate the onomatopoeia."""
    if not hasattr(world, "meters_bells"):
        world.meters_bells = 0
    if world.meters_bells < 2:
        world.meters_bells += 1
        world.say(onomatopoeia)


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* story and a *reasonable* surprise.
# ---------------------------------------------------------------------------
def surprise_pairs_with(surprise: SurpriseGift, treat: Treat) -> bool:
    """Would the helper's surprise gift naturally go with the shared treat?

    Examples:
        cocoa goes with scones
        hot chocolate goes with cookies
        storybook goes with cocoa (cold day, sit and read)
    """
    if not surprise.goes_with and not treat.pair_with:
        return True
    return bool(surprise.goes_with & treat.pair_with) or surprise.type in treat.pair_with


def helper_matches(helper: Helper, setting: Setting) -> bool:
    """Helper is plausible in this setting (librarian in library, etc.)."""
    return helper.id in setting.affords


def pick_helper_for_setting(setting: Setting, rng: random.Random) -> Helper:
    """Choose a helper that actually belongs to the chosen setting."""
    pool = [h for h in HELPERS if helper_matches(h, setting)]
    return rng.choice(pool)


# ---------------------------------------------------------------------------
# Prediction: the hero simulates "what if I keep the bigger share?" to motivate
# the kind beat.  Returns whether the sibling stays cold / hungry / sad.
# ---------------------------------------------------------------------------
def predict_if_hoard(world: World, hero: Entity, sibling: Entity,
                     treat: Treat) -> dict:
    sim = world.copy()
    _do_hoard(sim, sim.get(hero.id), sim.get(sibling.id), treat)
    return {
        "chilled": sibling.meters["chilled"] >= THRESHOLD,
        "cold_hands": sibling.meters["chilled"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def season_open(season: str) -> str:
    return {
        "winter": "On a snowy afternoon,",
    }.get(season, "One day,")


def setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return (
            f"Inside {setting.place}, the windows were foggy at the edges and "
            f"a little bell hung over the door."
        )
    return f"{setting.place.capitalize()} glittered white, and breath made tiny clouds."


def bell_open(world: World) -> str:
    """The first onomatopoeia: a small bell on the door."""
    return "*ting*"


def introduce(world: World, hero: Entity, sibling: Entity, elder: Entity) -> None:
    world.say(
        f"{hero.id} and {hero.pronoun('possessive')} little "
        f"{sibling.label_word or sibling.type} {sibling.id} walked with "
        f"{hero.pronoun('possessive')} {elder.label_word} {elder.id}."
    )


def arrive_at_setting(world: World, setting: Setting) -> None:
    world.say(f"{season_open(world.season)} they arrived at {setting.place}.")
    world.say(setting_detail(setting))


def door_bell(world: World) -> None:
    """Push the door open -- the first bell ring (the entrance chime)."""
    world.say("They pushed the door, and a little bell rang from above.")
    bell_chime(world, "*ting*")


def helper_greets(world: World, helper: Entity) -> None:
    world.say(
        f"{helper.phrase} waved hello and offered them two {world.facts['treat'].label}s."
    )


def treats_appear(world: World, treat: Treat) -> None:
    world.say(
        f"The {treat.plural and 'scones' or treat.label}s smelled warm and sweet, "
        f"and a little steam rose from the top."
    )


def hero_reaches(world: World, hero: Entity, treat: Treat) -> None:
    world.memes_consideration_seen = True
    world.say(
        f"{hero.id} looked at the bigger {treat.label} and almost reached for it first."
    )


def sibling_shivers(world: World, sibling: Entity) -> None:
    sibling.meters["chilled"] += 1
    sibling.memes["shiver"] += 1
    world.say(
        f"But then {sibling.id} shivered a little, and {sibling.pronoun('possessive')} "
        f"hands looked very cold."
    )


def hero_notice(world: World, hero: Entity) -> None:
    hero.memes["consideration"] += 1
    world.say(
        f"{hero.id} noticed, and something soft stirred in {hero.pronoun('possessive')} chest."
    )


def hero_shares(world: World, hero: Entity, sibling: Entity, treat: Treat) -> None:
    """The kind beat: split the treat and give the bigger half to the sibling."""
    treat.meters["shared"] += 1
    treat.giver = hero.id
    treat.receiver = sibling.id
    sibling.held_items = []  # type: ignore[attr-defined]
    sibling.memes["loved"] += 1
    hero.memes["fairness"] += 1
    hero.memes["kindness"] += 1
    propagate(world, narrate=True)
    world.say(
        f"So {hero.id} broke the {treat.label} in two, and gave the bigger half "
        f"to {sibling.id}, and kept the smaller one for {hero.pronoun('object')}."
    )


def second_bell(world: World) -> None:
    """After the share beat, a second bell chime -- the helper signals surprise."""
    world.say("Just then, the little bell on the door rang again.")
    bell_chime(world, "*ting ting!*")
    world.facts["surprise_signal"] = "*ting ting!*"


def helper_surprises(world: World, helper: Entity, gift: SurpriseGift,
                     hero: Entity, sibling: Entity) -> None:
    """The kind helper gives an unexpected, related treat to both children."""
    hero_item = world.add(Entity(
        id=f"gift_{hero.id}", kind="thing", type=gift.type, label=gift.label,
        phrase=gift.phrase, giver=helper.id, receiver=hero.id, plural=gift.plural,
    ))
    sib_item = world.add(Entity(
        id=f"gift_{sibling.id}", kind="thing", type=gift.type, label=gift.label,
        phrase=gift.phrase, giver=helper.id, receiver=sibling.id, plural=gift.plural,
    ))
    hero_item.meters["surprise_meter"] += 1
    sib_item.meters["surprise_meter"] += 1
    sibling.memes["shy_joy"] += 1
    hero.memes["shyness"] += 1
    hero.memes["joy"] += 1
    sibling.memes["joy"] += 1
    hero.memes["love"] += 1
    sibling.memes["love"] += 1
    propagate(world, narrate=True)
    world.say(
        f'"{helper.prep.capitalize()}, on the house," {helper.pronoun("subject")} said, smiling. '
        f"{helper.phrase} {helper.tail}, one for each child."
    )


def ending_image(world: World, hero: Entity, sibling: Entity,
                 elder: Entity, gift: SurpriseGift, treat: Treat) -> None:
    g = "s" if gift.plural else ""
    world.say(
        f"They sat by the foggy window and sipped the warm {gift.label}{g}. "
        f"{sibling.id} leaned against {hero.id}, and the {treat.label} tasted even "
        f"sweeter for being shared. Outside, the snow fell softly, and inside, "
        f"{hero.pronoun('possessive')} {elder.label_word} {elder.id} smiled at "
        f"the two small hands wrapped around the warm cup{g}."
    )


def _do_hoard(world: World, hero: Entity, sibling: Entity, treat: Treat) -> None:
    """Simulation branch: if hero kept the bigger half, sibling stays cold."""
    treat.meters["hoarded"] = treat.meters.get("hoarded", 0.0) + 1
    sibling.meters["chilled"] += 1


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, treat: Treat,
         surprise: SurpriseGift, helper_id: str,
         hero_name: str = "Mira", hero_type: str = "girl",
         sibling_type: str = "brother",
         sibling_name: str = "Theo",
         elder_type: str = "grandmother",
         elder_name: str = "Nana",
         helper_gender: str = "woman") -> World:
    world = World(setting)
    world.season = activity.season
    _init_world_meters(world)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", "thoughtful"],
    ))
    sibling = world.add(Entity(
        id=sibling_name, kind="character", type=sibling_type,
        traits=["little", "quiet"],
    ))
    elder = world.add(Entity(
        id=elder_name, kind="character", type=elder_type, label=elder_type,
        traits=["warm"],
    ))
    # Build the helper entity from the registry.
    helper_def = next(h for h in HELPERS if h.id == helper_id)
    helper_type = helper_def.type + ("_f" if helper_gender == "woman" else "_m")
    helper = world.add(Entity(
        id="Helper", kind="character", type=helper_type,
        label=helper_def.label, traits=["kind"],
    ))

    # Act 1 -- setup: who, where they are going, what they smell and see.
    introduce(world, hero, sibling, elder)
    world.para()
    arrive_at_setting(world, setting)
    door_bell(world)
    helper_greets(world, helper)
    treats_appear(world, treat)
    world.facts["treat"] = treat

    # Act 2 -- conflict: hero almost grabs the bigger half, but sees the shiver.
    world.para()
    hero_reaches(world, hero, treat)
    sibling_shivers(world, sibling)
    hero_notice(world, hero)
    hero_shares(world, hero, sibling, treat)

    # Act 3 -- resolution: a second bell chime and a kind surprise.
    world.para()
    second_bell(world)
    helper_surprises(world, helper, surprise, hero, sibling)

    # Final image.
    world.para()
    ending_image(world, hero, sibling, elder, surprise, treat)

    # Record facts for the Q&A generators (grounded in the simulated world).
    world.facts.update(
        hero=hero, sibling=sibling, elder=elder, helper=helper,
        treat=treat, surprise=surprise, setting=setting,
        helper_def=helper_def, activity=activity,
        helper_gender=helper_gender,
        shared=treat.meters["shared"] >= THRESHOLD,
        surprised=(hero.memes["surprise"] >= THRESHOLD
                   and sibling.memes["surprise"] >= THRESHOLD),
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "bakery": Setting(place="the bakery", indoor=True, affords={"baker"}),
    "library": Setting(place="the library", indoor=True, affords={"librarian"}),
    "park": Setting(place="the snowy park", indoor=False, affords={"park_ranger"}),
    "shop": Setting(place="the corner shop", indoor=True, affords={"shopkeeper"}),
    "museum": Setting(place="the little museum", indoor=True, affords={"librarian"}),
}

ACTIVITIES = {
    "scone": Activity(
        id="scone",
        verb="share the scone",
        gerund="sharing scones",
        rush="reach for the bigger scone",
        mess="chilled",
        zone={"hands"},
        season="winter",
        keyword="scone",
        tags={"scone", "share", "warm"},
    ),
    "cookie": Activity(
        id="cookie",
        verb="share the cookie",
        gerund="sharing cookies",
        rush="grab the bigger cookie",
        mess="chilled",
        zone={"hands"},
        season="winter",
        keyword="cookie",
        tags={"cookie", "share", "warm"},
    ),
    "mittens": Activity(
        id="mittens",
        verb="share the mittens",
        gerund="sharing mittens",
        rush="pull the mittens on first",
        mess="chilled",
        zone={"hands"},
        season="winter",
        keyword="mittens",
        tags={"mittens", "share", "warm"},
    ),
    "blanket": Activity(
        id="blanket",
        verb="share the blanket",
        gerund="sharing a blanket",
        rush="wrap the blanket around first",
        mess="chilled",
        zone={"torso"},
        season="winter",
        keyword="blanket",
        tags={"blanket", "share", "warm"},
    ),
}

TREATS = {
    "scone": Treat(
        label="scone",
        phrase="a warm blueberry scone",
        type="scone",
        plural=False,
        shareable=True,
        pair_with={"cocoa", "hot_chocolate", "tea", "storybook"},
    ),
    "cookie": Treat(
        label="cookie",
        phrase="a soft chocolate-chip cookie",
        type="cookie",
        plural=False,
        shareable=True,
        pair_with={"cocoa", "hot_chocolate", "milk", "storybook"},
    ),
    "mittens": Treat(
        label="mittens",
        phrase="a pair of woolly mittens",
        type="mittens",
        plural=True,
        shareable=True,
        pair_with={"cocoa", "tea", "blanket"},
    ),
    "blanket": Treat(
        label="blanket",
        phrase="a small wool blanket",
        type="blanket",
        plural=False,
        shareable=True,
        pair_with={"cocoa", "tea", "storybook", "mittens"},
    ),
}

SURPRISES = {
    "cocoa": SurpriseGift(
        label="mug of cocoa",
        phrase="a small mug of cocoa",
        type="cocoa",
        plural=False,
        goes_with={"scone", "cookie", "mittens", "blanket"},
    ),
    "hot_chocolate": SurpriseGift(
        label="cup of hot chocolate",
        phrase="a small cup of hot chocolate",
        type="hot_chocolate",
        plural=False,
        goes_with={"scone", "cookie", "mittens", "blanket"},
    ),
    "tea": SurpriseGift(
        label="cup of tea",
        phrase="a small cup of warm tea",
        type="tea",
        plural=False,
        goes_with={"scone", "cookie", "mittens", "blanket"},
    ),
    "milk": SurpriseGift(
        label="glass of milk",
        phrase="a small glass of warm milk",
        type="milk",
        plural=False,
        goes_with={"cookie", "scone"},
    ),
    "storybook": SurpriseGift(
        label="storybook",
        phrase="a small picture storybook",
        type="storybook",
        plural=False,
        goes_with={"scone", "cookie", "blanket"},
    ),
}

HELPERS = [
    Helper(
        id="baker",
        type="baker",
        label="the baker",
        phrase="the friendly baker",
        verbs=["bring", "set down", "carry over"],
        prep="warm two mugs of cocoa",
        tail="brought out two warm mugs of cocoa",
        gender_pool={"woman", "man"},
    ),
    Helper(
        id="librarian",
        type="librarian",
        label="the librarian",
        phrase="the kind librarian",
        verbs=["pull out", "set on the desk", "open to the first page"],
        prep="find a small picture storybook",
        tail="set a small picture storybook between them",
        gender_pool={"woman", "man"},
    ),
    Helper(
        id="park_ranger",
        type="park_ranger",
        label="the park ranger",
        phrase="the friendly park ranger",
        verbs=["unfold", "tuck around", "hand over"],
        prep="bring a small warm blanket",
        tail="unfolded a small warm blanket for them",
        gender_pool={"woman", "man"},
    ),
    Helper(
        id="shopkeeper",
        type="shopkeeper",
        label="the shopkeeper",
        phrase="the kind shopkeeper",
        verbs=["pour", "set on the counter", "bring over"],
        prep="pour two small cups of warm tea",
        tail="poured two small cups of warm tea",
        gender_pool={"woman", "man"},
    ),
]

# Sibling relationships we are willing to generate.
SIBLING_KINDS = {
    "girl": [("brother", "boy"), ("sister", "girl")],
    "boy": [("sister", "girl"), ("brother", "boy")],
}

# Elder kinds the children walk with.
ELDERS = {
    "grandmother": "grandma",
    "grandfather": "grandpa",
    "mother": "mom",
    "father": "dad",
}

GIRL_NAMES = ["Mira", "Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose", "Iris"]
BOY_NAMES = ["Theo", "Ben", "Max", "Sam", "Leo", "Finn", "Noah", "Eli", "Otis", "Wren"]
SIB_GIRL_NAMES = ["Mia", "Lila", "Ada", "Eva", "June", "Sage", "Wren", "Ivy"]
SIB_BOY_NAMES = ["Theo", "Ben", "Jude", "Kit", "Lou", "Ari", "Cy", "Reo"]
TRAITS = ["thoughtful", "gentle", "kind", "quiet", "cheerful", "soft-spoken"]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    """(place, activity, treat, surprise, helper) tuples that pass constraints."""
    out: list[tuple[str, str, str, str, str]] = []
    for place, s in SETTINGS.items():
        for act_id, act in ACTIVITIES.items():
            treat = TREATS.get(act.id)
            if treat is None:
                continue
            for surprise_id, surprise in SURPRISES.items():
                if not surprise_pairs_with(surprise, treat):
                    continue
                for helper_id in s.affords:
                    out.append((place, act_id, treat.label, surprise_id, helper_id))
    return out


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    activity: str
    treat: str
    surprise: str
    helper: str
    name: str
    gender: str
    sibling_name: str
    sibling_kind: str
    sibling_gender: str
    elder_name: str
    elder_kind: str
    helper_gender: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "winter": [
        ("What is winter?",
         "Winter is the coldest season of the year, when snow often falls and "
         "the days are short and chilly."),
        ("Why is winter cold?",
         "Winter is cold because the sun is lower in the sky and the air holds "
         "less warmth from it, so the world feels chilly."),
    ],
    "scone": [
        ("What is a scone?",
         "A scone is a soft, crumbly baked treat, sometimes with fruit inside, "
         "that people like to eat warm with a drink."),
    ],
    "cookie": [
        ("What is a cookie?",
         "A cookie is a small sweet baked treat, often soft in the middle and "
         "crisp at the edges."),
    ],
    "mittens": [
        ("What are mittens for?",
         "Mittens are warm covers for your hands that keep your fingers toasty "
         "when it is cold outside."),
    ],
    "blanket": [
        ("What is a blanket for?",
         "A blanket is a soft, warm cover that you wrap around yourself to stay "
         "cozy when the air is cold."),
    ],
    "cocoa": [
        ("What is cocoa?",
         "Cocoa is a warm drink made with cocoa powder and milk, and it tastes "
         "sweet and chocolatey."),
    ],
    "hot_chocolate": [
        ("What is hot chocolate?",
         "Hot chocolate is a warm drink made with melted chocolate and milk, "
         "and it is sweet and cozy."),
    ],
    "tea": [
        ("What is tea?",
         "Tea is a warm drink made by pouring hot water over dried leaves, and "
         "it can taste gentle and a little flowery."),
    ],
    "milk": [
        ("What is warm milk?",
         "Warm milk is milk that has been gently heated so it is not cold, and "
         "it feels soothing to drink."),
    ],
    "storybook": [
        ("What is a storybook?",
         "A storybook is a small book with pictures and a simple tale that "
         "someone can read out loud."),
    ],
    "baker": [
        ("Who is a baker?",
         "A baker is a person whose job is to make bread, scones, cookies, and "
         "other baked treats in a bakery."),
    ],
    "librarian": [
        ("Who is a librarian?",
         "A librarian is a person who looks after a library and helps people "
         "find books to read."),
    ],
    "park_ranger": [
        ("Who is a park ranger?",
         "A park ranger is a person who takes care of a park and helps visitors "
         "stay safe and welcome."),
    ],
    "shopkeeper": [
        ("Who is a shopkeeper?",
         "A shopkeeper is the person who runs a small shop and helps customers "
         "find what they need."),
    ],
    "bell": [
        ("What does a small bell do?",
         "A small bell on a door makes a soft ringing sound, *ting*, that lets "
         "the people inside know someone has come in."),
    ],
    "share": [
        ("What does it mean to share?",
         "To share means to give part of what you have to someone else so that "
         "you each have some."),
        ("Why is sharing kind?",
         "Sharing is kind because it shows you are thinking about how someone "
         "else feels, not just about yourself."),
    ],
    "surprise": [
        ("What is a surprise?",
         "A surprise is something nice that happens when you do not expect it, "
         "and it often makes you smile."),
    ],
}
KNOWLEDGE_ORDER = ["winter", "share", "surprise", "bell",
                   "scone", "cookie", "mittens", "blanket",
                   "cocoa", "hot_chocolate", "tea", "milk", "storybook",
                   "baker", "librarian", "park_ranger", "shopkeeper"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, sibling, elder = f["hero"], f["sibling"], f["elder"]
    treat, surprise, helper_def = f["treat"], f["surprise"], f["helper_def"]
    place = world.setting.place
    kw = f["activity"].keyword or treat.label
    return [
        f'Write a short winter story for a 3-to-5-year-old on the theme '
        f'"sharing, sound effects, a small surprise" that includes the word "{kw}".',
        f'Tell a heartwarming story where {hero.id} and {hero.pronoun("possessive")} '
        f'little {sibling.label_word or sibling.type} {sibling.id} visit {place} '
        f'with {elder.label_word} {elder.id}, share a {treat.label}, and '
        f'receive a sweet surprise from {helper_def.label}.',
        f'Write a simple story that uses the onomatopoeia "*ting*" and ends with '
        f'two children warm and happy after sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, sibling, elder, helper = f["hero"], f["sibling"], f["elder"], f["helper"]
    treat, surprise, helper_def = f["treat"], f["surprise"], f["helper_def"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), "thoughtful")
    sib_trait = next((t for t in sibling.traits if t != "little"), "quiet")
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who went to {place} on the snowy afternoon when the bell "
                f"ranged *ting* and the children shared a {treat.label}?"
            ),
            answer=(
                f"{hero.id}, {hero.pronoun('possessive')} little "
                f"{sibling.label_word or sibling.type} {sibling.id}, and "
                f"{hero.pronoun('possessive')} {elder.label_word} {elder.id} "
                f"went to {place}. The doorbell made a small *ting* when they "
                f"pushed inside."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} notice about {sibling.id} before "
                f"deciding to share the {treat.label} at {place}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} noticed that {sibling.id} was "
                f"shivering and that {sibling.pronoun('possessive')} hands looked "
                f"very cold. That made {hero.id} want to share the {treat.label} fairly."
            ),
        ),
        QAItem(
            question=(
                f"How did {hero.id} share the {treat.label} with {sib_trait} "
                f"{sibling.id} at {place} on the snowy afternoon?"
            ),
            answer=(
                f"{sub.capitalize()} broke the {treat.label} in two and gave the "
                f"bigger half to {sibling.id}, keeping the smaller one for "
                f"{obj}. The {treat.label} made {sibling.pronoun('object')} feel "
                f"warm all the way to {sibling.pronoun('possessive')} toes."
            ),
        ),
        QAItem(
            question=(
                f"What sound did the bell make right before the surprise at {place}?"
            ),
            answer=(
                f"The little bell on the door rang *ting ting!* a second time, "
                f"and that was the signal for the surprise from {helper_def.label}."
            ),
        ),
    ]
    if f.get("surprised"):
        qa.append(QAItem(
            question=(
                f"What kind surprise did {helper_def.label} bring for {hero.id} "
                f"and {sibling.id} after the bell rang twice at {place}?"
            ),
            answer=(
                f'{helper_def.label.capitalize()} brought out {surprise.phrase}s '
                f"for each child, on the house. It was a happy surprise, and "
                f"both children's eyes went wide with joy."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} and {sib_trait} {sibling.id} feel at "
                f"the end of the snowy afternoon at {place}?"
            ),
            answer=(
                f"They felt warm, loved, and a little shy with happiness. "
                f"{sibling.id} leaned against {hero.id}, and the {treat.label} "
                f"tasted even sweeter for being shared."
            ),
        ))
    qa.append(QAItem(
        question=(
            f"Why did {hero.id} give the bigger half to {sibling.id} when they "
            f"shared the {treat.label} at {place}?"
        ),
        answer=(
            f"Because {sibling.id} was cold and shivering, and {hero.id} cared "
            f"more about {sibling.pronoun('object')} feeling warm than about "
            f"having the bigger half for {obj}."
        ),
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = set(f["activity"].tags) | {"winter", "share", "surprise", "bell"}
    if f.get("helper_def"):
        tags.add(f["helper_def"].id)
    if f.get("treat"):
        tags.add(f["treat"].type)
    if f.get("surprise"):
        tags.add(f["surprise"].type)
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
        lines.append(f"  {e.id:10} ({e.type:11}) {' '.join(bits)}")
    bells = getattr(world, "meters_bells", 0)
    lines.append(f"  bells rung: {bells}")
    lines.append(f"  fired rule keys: {len(world.fired)}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="bakery",
        activity="scone",
        treat="scone",
        surprise="cocoa",
        helper="baker",
        name="Mira",
        gender="girl",
        sibling_name="Theo",
        sibling_kind="brother",
        sibling_gender="boy",
        elder_name="Nana",
        elder_kind="grandmother",
        helper_gender="woman",
    ),
    StoryParams(
        place="library",
        activity="cookie",
        treat="cookie",
        surprise="storybook",
        helper="librarian",
        name="Ben",
        gender="boy",
        sibling_name="Mia",
        sibling_kind="sister",
        sibling_gender="girl",
        elder_name="Poppy",
        elder_kind="grandfather",
        helper_gender="man",
    ),
    StoryParams(
        place="park",
        activity="blanket",
        treat="blanket",
        surprise="cocoa",
        helper="park_ranger",
        name="Lily",
        gender="girl",
        sibling_name="Lou",
        sibling_kind="brother",
        sibling_gender="boy",
        elder_name="Grams",
        elder_kind="grandmother",
        helper_gender="woman",
    ),
    StoryParams(
        place="shop",
        activity="mittens",
        treat="mittens",
        surprise="tea",
        helper="shopkeeper",
        name="Otis",
        gender="boy",
        sibling_name="Ada",
        sibling_kind="sister",
        sibling_gender="girl",
        elder_name="Dad",
        elder_kind="father",
        helper_gender="man",
    ),
    StoryParams(
        place="museum",
        activity="scone",
        treat="scone",
        surprise="hot_chocolate",
        helper="librarian",
        name="Zoe",
        gender="girl",
        sibling_name="Reo",
        sibling_kind="brother",
        sibling_gender="boy",
        elder_name="Mom",
        elder_kind="mother",
        helper_gender="woman",
    ),
]


def explain_rejection(reason_kind: str, *args) -> str:
    if reason_kind == "no_helper":
        place, treat_label = args
        return (f"(No story: {place} has no helper who could surprise the "
                f"children with a {treat_label}-friendly treat. Try a different "
                f"place or treat.)")
    if reason_kind == "no_pair":
        treat_label, surprise_label = args
        return (f"(No story: {surprise_label} does not naturally pair with "
                f"{treat_label}. The surprise should go with the shared treat.)")
    return "(No story: invalid combination.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(SIBLING_KINDS[gender][0] if False else
                            {k for k, _ in []}))
    return (f"(No story: gender mismatch.)") if False else ""


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (surprise_pairs_with / helper_matches / valid_combos).  Rules inline; facts
# are generated from the registries above so the two cannot drift.
# Uses the shared `asp` helper + clingo, imported lazily.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A helper can appear at a place iff the place affords that helper.
helper_at(Place, H) :- affords(Place, H).

% A surprise pairs with a treat when the surprise's goes_with set contains
% the treat's type, or vice versa.
pairs(Treat, Surprise) :- treat(Treat), surprise(Surprise),
                         ( goes_with(Surprise, Treat) ;
                           pair_with(Treat, Surprise) ).

% A story is valid when its (place, activity, treat, surprise, helper)
% tuple matches a real activity (the treat mirrors the activity) and the
% surprise/helper are both consistent with the place and treat.
valid(Place, Act, Treat, Surprise, Helper) :-
    affords(Place, Act),
    activity(Act), treat_kind(Act, Treat),
    pairs(Treat, Surprise),
    helper_at(Place, Helper).

% Gender-aware version: sibling can plausibly be a boy or girl.
valid_story(Place, Act, Treat, Surprise, Helper, Gender) :-
    valid(Place, Act, Treat, Surprise, Helper),
    sibling_gender_ok(Gender).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for h in sorted(s.affords):
            lines.append(asp.fact("affords", pid, h))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("activity_season", aid, a.season))
        # The treat mirrors the activity id (e.g. "scone" activity -> "scone" treat)
        lines.append(asp.fact("treat_kind", aid, a.id))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        if t.plural:
            lines.append(asp.fact("treat_plural", tid))
        for w in sorted(t.pair_with):
            lines.append(asp.fact("pair_with", tid, w))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        if s.plural:
            lines.append(asp.fact("surprise_plural", sid))
        for w in sorted(s.goes_with):
            lines.append(asp.fact("goes_with", sid, w))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        lines.append(asp.fact("helper_type", h.id, h.type))
    for g in ("girl", "boy"):
        lines.append(asp.fact("sibling_gender_ok", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (place, activity, treat, surprise, helper)."""
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    """(place, activity, treat, surprise, helper, gender) -- gender-aware set."""
    import asp
    model = asp.one_model(asp_program("#show valid_story/6."))
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
        description="Story world sketch: winter sharing, sound effects, a "
                    "small surprise. Unspecified choices are picked at random (seeded).")
    # A small, debuggable set of pins; any omitted choice is randomized.
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--helper", choices=[h.id for h in HELPERS])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sibling-name")
    ap.add_argument("--sibling-kind", choices=["sister", "brother"])
    ap.add_argument("--sibling-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-kind", choices=list(ELDERS.keys()))
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the *explicit* options describe an invalid story."""
    if args.treat and args.surprise:
        if not surprise_pairs_with(SURPRISES[args.surprise], TREATS[args.treat]):
            raise StoryError(explain_rejection("no_pair", args.treat, args.surprise))
    if args.place and args.helper:
        if args.helper not in SETTINGS[args.place].affords:
            raise StoryError(explain_rejection("no_helper", args.place, args.treat or ""))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.treat is None or c[2] == args.treat)
              and (args.surprise is None or c[3] == args.surprise)
              and (args.helper is None or c[4] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, treat_id, surprise_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sib_kind, sib_gender = (
        (args.sibling_kind, args.sibling_gender) if args.sibling_kind
        else rng.choice(SIBLING_KINDS[gender])
    )
    if args.sibling_gender and not args.sibling_kind:
        sib_kind = "sister" if args.sibling_gender == "girl" else "brother"
    sib_pool = SIB_GIRL_NAMES if sib_gender == "girl" else SIB_BOY_NAMES
    sibling_name = args.sibling_name or rng.choice(sib_pool)
    elder_kind = args.elder_kind or rng.choice(list(ELDERS.keys()))
    elder_default = "Grandma" if elder_kind == "grandmother" else (
        "Grandpa" if elder_kind == "grandfather" else (
        "Mom" if elder_kind == "mother" else "Dad"))
    elder_name = args.elder_name or elder_default
    helper_gender = args.helper_gender or rng.choice(sorted(
        next(h for h in HELPERS if h.id == helper_id).gender_pool))
    return StoryParams(
        place=place,
        activity=activity,
        treat=treat_id,
        surprise=surprise_id,
        helper=helper_id,
        name=name,
        gender=gender,
        sibling_name=sibling_name,
        sibling_kind=sib_kind,
        sibling_gender=sib_gender,
        elder_name=elder_name,
        elder_kind=elder_kind,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(
        SETTINGS[params.place], ACTIVITIES[params.activity],
        TREATS[params.treat], SURPRISES[params.surprise], params.helper,
        params.name, params.gender,
        params.sibling_kind, params.sibling_name,
        params.elder_kind, params.elder_name,
        params.helper_gender,
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
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, treat, surprise, "
              f"helper) combos ({len(stories)} with gender):\n")
        for place, act, treat, surprise, helper in triples:
            print(f"  {place:8} {act:8} {treat:8} {surprise:14} {helper:11}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (treat: {p.treat})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
