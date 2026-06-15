#!/usr/bin/env python3
"""
storyworlds/worlds/puddles.py
=============================

A standalone *story world* sketch for the "Lily / puddles / new jacket" tale
(``data00:36242``) and close, *constraint-checked* variations of it.  

Reference story (can be poor quality, or good quality, needs a world model):
--------------------------------------------------
Once upon a time, there was a little cheerful boy named Leo. He loved playing outside 
and dancing in the rain. One day, Leo's mom bought him a clean white shirt. 
Leo loved his new shirt and wore it everywhere he went.

One rainy day, Leo and his mom went to the backyard. Leo wanted to play in the rain,
but his mom said no. "You'll get your shirt soaking wet, and then I'll have to clean it,"
his mom said. Leo didn't want to listen and tried to run out into the rain, 
but his mom grabbed his hand and said, "You have to resist the urge to play in the rain today."
    
Leo pouted and crossed his arms. "But I want to play in the rain!" he said. His mom smiled 
and said, "How about we put on your rain boots first and play in the rain together?" 
Leo's face lit up and he hugged his mom. "Yay, let's do it!" he said as they went to get the rain boots.

Why the coverage constraint exists
----------------------------------
The original logic ("a new *shirt* will get wet -> let's put on
*rain boots*") is weak: rain boots protect feet, not a jacket.  ("new white
*shirt* -> rain jacket" is fine.)  So this sketch refuses to generate the
unreasonable argument.  Every wearable occupies a body **region**; an activity
splashes a set of regions; protective gear **covers** a set of regions.  A
compromise is only a compatible move when the chosen gear (a) guards the mess
kind *and* (b) covers the region of the at-risk prize.  The world model itself
enforces this: a shirt (torso) is not covered by the splash zone of puddle-jumping
(feet/legs), so the parent has no honest warning to give, and no story is made.

Causal rules (forward-chained to a fixpoint), one engine for both axes:

    do activity                  -> actor.<mess> += 1
    actor messy + worn item      -> item.<mess>++, item.dirty++       only if the item's
                                    region is in the splash zone and not covered by gear
    worn item dirty              -> item.caretaker.workload += 1       (more work for the parent)

    loves play + does it         -> actor.joy += 1
    forbidden + wants it         -> actor.defiance += 1
    parent grabs the hand        -> conflict += 1 on both
    compromise accepted          -> joy/love += 1 ; conflict -> 0

Run it
------
    python storyworlds/worlds/puddles.py                       # random reasonable story (seeded)
    python storyworlds/worlds/puddles.py --place garden --activity mud --prize socks
    python storyworlds/worlds/puddles.py --prize jacket --activity puddles   # rejected: explains why
    python storyworlds/worlds/puddles.py --all                 # curated, constraint-valid variety set
    python storyworlds/worlds/puddles.py -n 5 --seed 7         # random, only constraint-valid combos
    python storyworlds/worlds/puddles.py --trace               # dump the world-model state
    python storyworlds/worlds/puddles.py --qa --json           # serialize story + 3 Q&A sets to JSON
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
# (``python storyworlds/worlds/puddles.py``): add the package dir (storyworlds/)
# to the path so ``results`` resolves regardless of the current directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Physical meter keys that count as a "mess" the activity spreads onto worn items.
MESS_KINDS = {"wet", "muddy", "painted", "sandy"}

# Body regions, used for the gear-coverage constraint.
REGIONS = {"feet", "legs", "torso"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, mother, father, jacket, shoes, gear ...
    label: str = ""                # short reference, e.g. "jacket", "rain boots"
    phrase: str = ""               # full noun phrase, e.g. "a new jacket with a tough zipper"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None   # who has to clean up after this object
    worn_by: Optional[str] = None
    region: str = ""                  # where a worn item sits: feet | legs | torso
    protective: bool = False          # gear that doesn't get ruined
    covers: set[str] = field(default_factory=set)   # regions the gear shields
    plural: bool = False              # "shoes" -> them, "jacket" -> it
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
    place: str = "the park"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)   # which activities this place supports


@dataclass
class Activity:
    """A messy thing the hero loves to do."""
    id: str
    verb: str            # after "wanted to ..."             : "jump in the puddles"
    gerund: str          # after "loved playing ... and ..." : "jumping in puddles"
    rush: str            # after "tried to ..."              : "run towards the puddles"
    mess: str            # mess kind key, one of MESS_KINDS  : "wet"
    soil: str            # how the prize gets ruined         : "wet and dirty"
    zone: set[str]       # body regions the activity splashes: {"feet", "legs"}
    weather: str         # "rainy" | "sunny" | ""
    keyword: str = ""    # topic word for generation prompts : "puddles"
    tags: set[str] = field(default_factory=set)   # world-knowledge topics it touches


@dataclass
class Prize:
    """The thing the hero loves and wears, that the messy activity would ruin."""
    label: str
    phrase: str
    type: str
    region: str          # feet | legs | torso  -- where it sits on the body
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})  # who plausibly wears it


@dataclass
class Gear:
    """Protective clothing offered as the compromise."""
    id: str
    label: str
    covers: set[str]     # regions it shields
    guards: set[str]     # mess kinds it neutralizes
    prep: str            # body of the offer: "go home and put on our rain boots"
    tail: str            # closing clause: "walked back home to get their rain boots"
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
        self.zone: set[str] = set()          # splash zone of the activity in play
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


def _r_soak(world: World) -> list[str]:
    """actor messy + worn item in the splash zone & uncovered -> mess + dirty."""
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
    """worn item dirty -> its caretaker has more work."""
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
    """parent grabbed the hand while the child is defiant -> conflict on both."""
    for actor in world.characters():
        if actor.memes["grabbed_by"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]          # marker; narrated by the screenplay beat
    return []


CAUSAL_RULES: list[Rule] = [
    Rule("soak", "physical", _r_soak),
    Rule("workload", "physical", _r_workload),
    Rule("grab_conflict", "social", _r_grab_conflict),
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
                produced.extend(s for s in sents if s != "__conflict__")
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
    """The compatible compromise: gear that guards the mess AND covers the
    at-risk region.  Returns None when no reasonable gear exists (e.g. rain
    boots for a jacket), which is exactly the case we refuse to generate."""
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
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
def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return                                  # this place can't host the activity
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"Once upon a time, there was a {desc} named {hero.id}.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    where = "inside" if world.setting.indoor else "outside"
    world.say(f"{hero.pronoun().capitalize()} loved playing {where} and {activity.gerund}.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One day, {hero.id}'s {parent.label_word} bought "
        f"{hero.pronoun('object')} {prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} new {prize.label} and "
        f"wore {prize.it()} everywhere {hero.pronoun()} went."
    )


def arrive(world: World, hero: Entity, parent: Entity) -> None:
    day = {"rainy": "One rainy day, ", "sunny": "One sunny day, "}.get(world.weather, "One day, ")
    go = "were in" if world.setting.indoor else "went to"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} {go} {world.setting.place}."
    )


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, but "
        f"{hero.pronoun('possessive')} {parent.label_word} said no."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    """The parent foresees the mess via the world model and warns about it."""
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"You'll get your {prize.label} {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I'll have to clean {prize.it()}"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said.')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} didn't want to listen and tried to {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)             # fires the grab->conflict rule
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} grabbed "
        f"{hero.pronoun('possessive')} hand and said, "
        f'"You have to resist the urge to {activity.verb} today."'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:     # only narrate embedded conflict
        world.say(
            f'{hero.id} pouted and crossed {hero.pronoun("possessive")} arms. '
            f'"But I want to {activity.verb}!" {hero.pronoun()} said.'
        )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    """Offer gear -- but only the gear that actually covers the at-risk prize,
    and only if the world model then predicts no mess (a compatible move)."""
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:   # gear didn't actually help
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled and '
        f'said, "How about we {gear_def.prep} and {activity.verb} together?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0                # resolution clears the tension
    world.say(
        f"{hero.id}'s face lit up and {hero.pronoun()} hugged "
        f"{hero.pronoun('possessive')} {parent.label_word}. "
        f'"Yay, let\'s do it!" {hero.pronoun()} said as they {gear_def.tail}.'
    )


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Lily", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
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
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1 -- setup: who, what they love, the prize they wear.
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2 -- conflict: desire vs. the predicted mess, ending in a grabbed hand.
    world.para()
    arrive(world, hero, parent)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    # Act 3 -- resolution: a compatible move (covering gear) clears the conflict.
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, gear_def)

    # Record facts for the Q&A generators (grounded in the simulated world).
    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "park": Setting("the park", indoor=False, affords={"puddles", "rain"}),
    "garden": Setting("the garden", indoor=False, affords={"puddles", "mud", "rain"}),
    "backyard": Setting("the backyard", indoor=False, affords={"mud", "puddles", "rain"}),
    "beach": Setting("the beach", indoor=False, affords={"sand"}),
    "playroom": Setting("the playroom", indoor=True, affords={"paint"}),
}

ACTIVITIES = {
    # puddle-jumping splashes feet/legs only -- NOT the torso (so a jacket is
    # not at risk here, which is why jacket+puddles is rejected, cf. the README).
    "puddles": Activity("puddles", "jump in the puddles", "jumping in puddles",
                        "run towards the puddles", "wet", "wet and dirty",
                        {"feet", "legs"}, "rainy",
                        keyword="puddles", tags={"puddle", "wet"}),
    # rain falls on everything, so it *does* reach the torso -- jacket+rain is the
    # reasonable counterpart that a raincoat genuinely fixes.
    "rain": Activity("rain", "play in the rain", "dancing in the rain",
                     "run out into the rain", "wet", "soaking wet",
                     {"feet", "legs", "torso"}, "rainy",
                     keyword="rain", tags={"rain", "wet"}),
    "mud": Activity("mud", "play in the mud", "splashing in the mud",
                    "run to the mud", "muddy", "all muddy",
                    {"feet", "legs"}, "rainy",
                    keyword="mud", tags={"mud", "dirty"}),
    "paint": Activity("paint", "paint a picture", "painting pictures",
                      "grab the paints", "painted", "covered in paint",
                      {"torso"}, "",
                      keyword="paint", tags={"paint", "dirty"}),
    "sand": Activity("sand", "dig in the sand", "digging in the sand",
                     "sit down in the sand", "sandy", "covered in sand",
                     {"legs"}, "sunny",
                     keyword="sand", tags={"sand"}),
}

# Order matters: more specific gear first, full-body fallback last.  Each gear
# only protects the regions it actually covers (the core reasonableness rule).
GEAR = [
    Gear("boots", "rain boots", {"feet"}, {"wet", "muddy"},
         "go home and put on our rain boots",
         "walked back home to get their rain boots", plural=True),
    Gear("smock", "an old smock", {"torso"}, {"painted"},
         "put on an old smock first", "went to get the old smock"),
    Gear("raincoat", "a raincoat", {"torso"}, {"wet"},
         "put on your raincoat first", "went to get the raincoat"),
    Gear("playclothes", "old play clothes", {"legs", "torso"},
         {"wet", "muddy", "sandy", "painted"},
         "go home and put on your old play clothes",
         "walked back home to get the old play clothes", plural=True),
]

PRIZES = {
    "shoes": Prize("shoes", "pretty white shoes", "shoes", "feet", plural=True),
    "socks": Prize("socks", "new white socks", "socks", "feet", plural=True),
    "dress": Prize("dress", "a pretty new dress", "dress", "legs", genders={"girl"}),
    "jacket": Prize("jacket", "a new jacket with a tough zipper", "jacket", "torso"),
    "shirt": Prize("shirt", "a clean white shirt", "shirt", "torso"),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
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
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.  These are answerable WITHOUT
# the story; they explain the *elements* the world is built from.
KNOWLEDGE = {
    "puddle": [("What is a puddle?",
                "A puddle is a small pool of water on the ground, usually left "
                "behind after it rains.")],
    "wet": [("Why does it feel cold when your feet get wet?",
             "Wet feet feel cold because the water carries the warmth away from "
             "your skin as it dries, so your feet lose heat and feel chilly.")],
    "rain": [("Where does rain come from?",
              "Rain is water that falls from clouds in the sky when the clouds "
              "get too full of tiny water drops.")],
    "mud": [("What is mud?",
             "Mud is soft, wet dirt. It sticks to shoes and clothes and makes "
             "them dirty.")],
    "paint": [("Why can paint be messy?",
               "Paint is a colored liquid, so it can drip and smear onto clothes "
               "and hands, and it is hard to wash out.")],
    "sand": [("What is sand?",
              "Sand is made of tiny bits of rock and shell, and you find lots of "
              "it at the beach.")],
    "dirty": [("Why do dirty clothes need to be washed?",
               "Dirty clothes are washed to get the mud and stains out so they "
               "are clean and fresh to wear again.")],
    "boots": [("What are rain boots for?",
               "Rain boots are tall, waterproof boots that keep your feet dry "
               "when you splash in water or mud.")],
    "raincoat": [("What does a raincoat do?",
                  "A raincoat is a waterproof coat that keeps the rest of you dry "
                  "when you play in the rain.")],
    "smock": [("What is a smock for?",
               "A smock is a loose cover you wear over your clothes so paint "
               "does not get on them.")],
    "playclothes": [("What are old play clothes?",
                     "Old play clothes are clothes you do not mind getting dirty, "
                     "so it is fine if they get muddy or messy.")],
}
KNOWLEDGE_ORDER = ["puddle", "rain", "mud", "paint", "sand", "wet", "dirty",
                   "boots", "raincoat", "smock", "playclothes"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a child, a '
        f'mess, a compromise" that includes the word "{kw}".',
        f"Tell a gentle story where a {hero.type} named {hero.id} wants to "
        f"{act.verb} but {hero.pronoun('possessive')} {parent.label_word} worries "
        f"about {prize.phrase}, and they find a happy compromise.",
        f'Write a simple story that uses the verb "resist", the noun "{kw}", and '
        f"ends with a parent and child agreeing on a compromise.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    where = "inside" if world.setting.indoor else "outside"
    qa: list[tuple[str, str]] = [
        (f"Who is the story about?",
         f"It is about a little {hero.type} named {hero.id} and "
         f"{pos} {pw}."),
        (f"What did {hero.id} love to do?",
         f"{hero.id} loved playing {where} and {act.gerund}."),
        (f"What did {hero.id}'s {pw} buy {obj}?",
         f"{pos.capitalize()} {pw} bought {obj} {prize.phrase}."),
    ]
    # The featured question: how/why the parent was upset -- grounded in the
    # predicted mess (the world model run forward) and the grabbed-hand conflict.
    if f.get("conflict"):
        soil = f.get("predicted_soil", "messy")
        work = f.get("predicted_workload", 0)
        why = (f"{pos.capitalize()} {pw} was upset because if {hero.id} went to "
               f"{act.verb}, {pos} {prize.label} would get {soil}")
        why += (f", and then {pw} would have to clean {prize.it()}. "
                if work >= THRESHOLD else ". ")
        why += (f"When {hero.id} tried to {act.rush.rstrip(', ')}, {pos} {pw} "
                f"grabbed {pos} hand and asked {obj} to resist the urge to "
                f"{act.verb}.")
        qa.append((f"Using the story above, explain how {hero.id}'s {pw} was "
                   f"upset and why.", why))
    if f.get("resolved"):
        gear = f["gear"]
        prep = gear.prep.replace("your ", "their ").replace("our ", "their ")
        qa.append(("How did they solve the problem?",
                   f"They agreed to {prep}, so {hero.id} could {act.verb} "
                   f"without ruining {pos} {prize.label}."))
        qa.append((f"How did {hero.id} feel at the end?",
                   f"{hero.id} felt happy and hugged {pos} {pw} once they agreed "
                   f"on the plan."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    """(3) Generic, child-level questions about the world's elements."""
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
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams("park", "puddles", "shoes", "Lily", "girl", "mother", "playful"),
    StoryParams("garden", "mud", "socks", "Tim", "boy", "father", "curious"),
    StoryParams("park", "rain", "jacket", "Ben", "boy", "father", "lively"),  # jacket+rain -> raincoat
    StoryParams("playroom", "paint", "shirt", "Mia", "girl", "mother", "spirited"),
    StoryParams("beach", "sand", "dress", "Zoe", "girl", "mother", "cheerful"),
]


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
# runs without them.  See `python puddles.py --verify`.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk when the activity splashes the region it is worn on.
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

% Gear is a compatible fix only when it both neutralises the mess kind AND
% covers the at-risk region (rain boots guard wet but cover only feet).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
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
        description="Story world sketch: a child, a mess, a compromise. "
                    "Unspecified choices are picked at random (seeded).")
    # A small, debuggable set of pins; any omitted choice is randomized.
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, activity, prize_id, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "stubborn"], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
