#!/usr/bin/env python3
"""
storyworlds/worlds/morphodite_sharing_magic_space_adventure.py
=============================================================

A standalone *story world* sketch for "The Morphodite's Sharing Magic"
tale and close, constraint-checked variations of it -- a tiny
Space-Adventure-style domain for 3-to-5-year-olds.

Initial story (used to build a world model):
---
Far across the twinkly dark, on a little green moon called Zin, lived a
small morphodite named Mox. A morphodite is a kind, sparkly creature that
can take the shape of whatever it meets, and Mox was the friendliest one
on Zin. Mox lived with Grin, the wise old morphodite who watched over the
whole moon.

Mox loved one thing most of all: sharing. Mox carried a soft, glowing
pouch called a sharing-pouch, and inside it was a pinch of sharing magic --
the kind of magic that turns one thing into enough for everyone. Sharing
magic was Mox's favorite thing to find, and Mox was always on the lookout
for a new way to share it.

One starry night, Mox and Grin flew their tiny rocket to a small grey
asteroid called Plo, where a sad little meteor named Klee was sitting all
alone. Klee had no glow at all, and the dark felt very long. Mox wanted
to share a sparkle of sharing magic with Klee right away, but Grin held
up a gentle wing and said, "If we share without thinking, the magic will
spread too thin, and none of us will glow."

Mox pouted a tiny pout and tried to fly straight to Klee, but Grin
grabbed Mox's tail and said, "You can want to help, and we can still
choose the safe way." Mox crossed small arms and said, "But I really
want to share!"

Grin smiled and said, "How about we use the sharing-pouch? It holds
just enough magic for one, and we can split the glow fairly." Mox's
face lit up. "Yay, let's share it!" they said, and together they went
to get the sharing-pouch from the rocket.

Soon Mox was splitting a single sparkle of sharing magic, Klee was
glowing for the very first time, and Grin was laughing beside them.
That night, three friends glowed brighter than one ever could.

Causal state updates:
---
    do kind act             -> hero.<glow> += 1 ; hero.joy += 1
    hero glow + spent item  -> item.<glow>--   (only if the item is a magic carrier
                                                and the hero is sharing, not hoarding)
    spent item empty        -> hero.<tired> += 1 ; caregiver.workload += 1
    caregiver warns         -> hero.defiance += 1
    grab a defiant child    -> hero.conflict += 1
    compromise accepted     -> hero.joy/love += 1 ; hero.conflict -> 0

Scripted social/emotional beats:
---
    warning ignored         -> hero.defiance += 1
    parent grabs a defiant  -> hero.conflict += 1                 (child tension)
    compromise accepted     -> hero.joy/love += 1 ; hero.conflict -> 0
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
# (``python storyworlds/worlds/morphodite_sharing_magic_space_adventure.py``):
# add the package dir (storyworlds/) to the path so ``results`` resolves
# regardless of the current directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Physical meter keys that count as a "glow" the kind act drains from carriers.
GLOW_KINDS = {"sparkle", "hum", "twinkle"}

# Body slots, used for the carrier-coverage constraint on a morphodite.
SLOTS = {"pouch", "tail-tuft", "wings", "core"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # morphodite, meteor, friend, pouch, lantern ...
    label: str = ""                # short reference, e.g. "sharing-pouch"
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None    # who tends this object (often a parent/mentor)
    held_by: Optional[str] = None      # who is currently carrying it
    slot: str = ""                     # where the carrier sits: pouch | tail-tuft | wings | core
    protective: bool = False           # gear that doesn't get drained
    guards: set[str] = field(default_factory=set)   # glow kinds this carrier conserves
    plural: bool = False               # "wings" -> them, "pouch" -> it
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        # Most morphodite heroes are they/them, but we keep gendered pronouns
        # for non-morphodite characters (e.g. mom/dad) so the prose can vary.
        if self.type in {"mother", "mom", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "dad", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the moon Zin"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)   # which kind acts this place supports


@dataclass
class KindAct:
    """A generous thing the hero loves to do."""
    id: str
    verb: str            # after "wanted to ..."             : "share a sparkle of magic"
    gerund: str          # after "loved ... and ..."        : "sharing a sparkle of magic"
    rush: str            # after "tried to ..."             : "fly straight to the lonely meteor"
    glow: str            # glow kind key, one of GLOW_KINDS : "sparkle"
    drain: str           # how the carrier gets weakened    : "drained of sparkle"
    zone: set[str]       # carrier slots the act drains     : {"pouch"}
    weather: str         # "starry" | "comet-bright" | ""
    keyword: str = ""    # topic word for generation prompts : "sharing"
    tags: set[str] = field(default_factory=set)   # world-knowledge topics it touches


@dataclass
class Carrier:
    """A magic-carrying item the hero wears or holds, that the kind act would drain."""
    label: str
    phrase: str
    type: str
    slot: str            # pouch | tail-tuft | wings | core
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"morphodite"})  # who holds it


@dataclass
class Helper:
    """A protective tool offered as the compromise -- conserves one glow kind."""
    id: str
    label: str
    guards: set[str]     # glow kinds it conserves
    covers: set[str]     # carrier slots it shields from drain
    prep: str            # body of the offer: "use the sharing-pouch first"
    tail: str            # closing clause: "went back to the rocket to get the sharing-pouch"
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
        self.zone: set[str] = set()          # drain zone of the kind act in play
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

    def held_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.held_by == actor.id]

    def conserved(self, actor: Entity, slot: str) -> bool:
        """Is `slot` shielded by some protective helper the actor is using?"""
        return any(h.protective and slot in h.covers for h in self.held_items(actor))

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


def _r_drain(world: World) -> list[str]:
    """actor glow + held carrier in the drain zone & uncovered -> drain."""
    out: list[str] = []
    for actor in world.characters():
        for glow in GLOW_KINDS:
            if actor.meters[glow] < THRESHOLD:
                continue
            for item in world.held_items(actor):
                if item.protective or item.slot not in world.zone:
                    continue
                if world.conserved(actor, item.slot):
                    continue
                sig = ("drain", item.id, glow)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[glow] -= 1
                item.meters["drained"] += 1
                out.append(
                    f"Their {item.label} got {glow}-less and faded."
                )
    return out


def _r_tired(world: World) -> list[str]:
    """held carrier drained -> its caretaker is more tired."""
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["drained"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("tired", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["tired"] += 1
        out.append(f"That would mean more work for {carer.label_word}.")
    return out


def _r_grab_conflict(world: World) -> list[str]:
    """Parent grabbed the hero while the hero is defiant -> hero conflict."""
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
    Rule(name="drain", tag="physical", apply=_r_drain),
    Rule(name="tired", tag="physical", apply=_r_tired),
    Rule(name="grab_conflict", tag="social", apply=_r_grab_conflict),
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
def carrier_at_risk(kind_act: KindAct, carrier: Carrier) -> bool:
    """Would this kind act actually drain this carrier (right slot)?"""
    return carrier.slot in kind_act.zone


def select_helper(kind_act: KindAct, carrier: Carrier) -> Optional[Helper]:
    """The compatible compromise: a helper that conserves the glow AND covers
    the at-risk slot.  Returns None when no reasonable helper exists."""
    for helper in HELPERS:
        if kind_act.glow in helper.guards and carrier.slot in helper.covers:
            return helper
    return None


# ---------------------------------------------------------------------------
# Prediction: the mentor runs the world model forward on a copy to foresee the
# drain before deciding what to say.
# ---------------------------------------------------------------------------
def predict_drain(world: World, actor: Entity, kind_act: KindAct, carrier_id: str) -> dict:
    """Simulate the kind act silently and report whether the carrier is drained."""
    sim = world.copy()
    _do_kind_act(sim, sim.get(actor.id), kind_act, narrate=False)
    carrier = sim.entities.get(carrier_id)
    return {
        "drained": bool(carrier and carrier.meters["drained"] >= THRESHOLD),
        "tired": sum(e.meters["tired"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def kind_act_detail(kind_act: KindAct) -> str:
    return {
        "sparkle": "the soft hum made every star feel a little closer",
        "hum": "the warm hum made the rocks feel like they were humming back",
        "twinkle": "the tiny twinkles made the dark feel friendly",
    }.get(kind_act.glow, "it made the night feel full of friends")


def setting_detail(setting: Setting, kind_act: KindAct) -> str:
    if setting.indoor:
        return f"Inside the {setting.place.removeprefix('the ')}, the air was still and the lights waited nearby."
    if kind_act.weather == "starry":
        return f"The stars blinked slow, and {setting.place} glowed like a tiny lantern."
    if kind_act.weather == "comet-bright":
        return "A comet had just streaked by, and the dust it left behind made the path look silver."
    if setting.place == "the moon Zin":
        return "Zin was small and green, and the dark felt soft and friendly."
    return f"{setting.place.capitalize()} looked quiet and ready for a kind visit."


def carrier_was_glowing(hero: Entity, carrier: Entity) -> str:
    return f"{hero.pronoun('possessive')} {carrier.label} stayed glowing"


def _do_kind_act(world: World, actor: Entity, kind_act: KindAct, narrate: bool = True) -> None:
    if kind_act.id not in world.setting.affords:
        return                                  # this place can't host the kind act
    world.zone = set(kind_act.zone)
    actor.meters[kind_act.glow] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who noticed every friend who needed help.")


def loves_kind_act(world: World, hero: Entity, kind_act: KindAct) -> None:
    hero.memes["love_sharing"] += 1
    where = "at home" if world.setting.indoor else "out among the stars"
    world.say(
        f"{hero.pronoun().capitalize()} loved {kind_act.gerund} {where}; "
        f"{kind_act_detail(kind_act)}."
    )


def buys(world: World, mentor: Entity, hero: Entity, carrier: Entity) -> None:
    world.say(
        f"One day, {hero.id}'s {mentor.label_word} gave "
        f"{hero.pronoun('object')} {carrier.phrase}."
    )


def loves_carrier(world: World, hero: Entity, carrier: Entity) -> None:
    hero.memes["love"] += 1
    carrier.held_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {carrier.label} and "
        f"held {carrier.it()} close, as if the day had been made specially for "
        f"{hero.pronoun('object')}."
    )


def arrive(world: World, hero: Entity, mentor: Entity, kind_act: KindAct) -> None:
    day = {"starry": "One starry night, ", "comet-bright": "One comet-bright night, "}.get(
        world.weather, "One quiet evening, "
    )
    go = "were in" if world.setting.indoor else "flew their tiny rocket to"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} "
        f"{mentor.label_word} {go} {world.setting.place}."
    )
    world.say(setting_detail(world.setting, kind_act))


def wants(world: World, hero: Entity, mentor: Entity, kind_act: KindAct) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {kind_act.verb} right away, but "
        f"{hero.pronoun('possessive')} {mentor.label_word} held up a gentle wing."
    )


def warn(world: World, mentor: Entity, hero: Entity, kind_act: KindAct,
         carrier: Entity) -> bool:
    """The mentor foresees the drain via the world model and warns about it."""
    pred = predict_drain(world, hero, kind_act, carrier.id)
    if not pred["drained"]:
        return False
    world.facts["predicted_drain"] = kind_act.drain
    world.facts["predicted_tired"] = pred["tired"]
    clause = f"Your {carrier.label} will get {kind_act.drain}"
    if pred["tired"] >= THRESHOLD:
        clause += f", and then I'll have to recharge {carrier.it()}"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {mentor.label_word} said. "Let\'s think first."')
    return True


def defies(world: World, hero: Entity, kind_act: KindAct) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the wish to help was still tugging hard.")
    world.say(f"{hero.pronoun().capitalize()} tried to {kind_act.rush},")


def grab_hand(world: World, mentor: Entity, hero: Entity, kind_act: KindAct) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)             # fires the grab->conflict rule
    world.say(
        f"but {hero.pronoun('possessive')} {mentor.label_word} grabbed "
        f"{hero.pronoun('possessive')} tail and said, "
        f'"You can want to {kind_act.verb}, and we can still choose the safe way."'
    )


def pout(world: World, hero: Entity, kind_act: KindAct) -> None:
    if hero.memes["conflict"] >= THRESHOLD:     # only narrate embedded conflict
        world.say(
            f'{hero.id} pouted and crossed {hero.pronoun("possessive")} arms. '
            f'"But I really want to {kind_act.verb}!" {hero.pronoun()} said.'
        )


def compromise(world: World, mentor: Entity, hero: Entity, kind_act: KindAct,
               carrier: Entity) -> Optional[Helper]:
    """Offer a helper -- but only the helper that actually covers the at-risk
    slot, and only if the world model then predicts no drain."""
    helper_def = select_helper(kind_act, carrier)
    if helper_def is None:
        return None
    helper = world.add(Entity(
        id=helper_def.id, type="helper", label=helper_def.label,
        owner=hero.id, caretaker=mentor.id, protective=True,
        guards=set(helper_def.guards), covers=set(helper_def.covers),
        plural=helper_def.plural,
    ))
    helper.held_by = hero.id
    if predict_drain(world, hero, kind_act, carrier.id)["drained"]:   # helper didn't help
        helper.held_by = None
        del world.entities[helper.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {mentor.label_word} looked at the '
        f'{carrier.label}, then back at {hero.id}, and smiled. '
        f'"How about we {helper_def.prep} and {kind_act.verb} together?"'
    )
    return helper_def


def accept(world: World, mentor: Entity, hero: Entity, kind_act: KindAct,
           carrier: Entity, helper_def: Helper) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0                # resolution clears the tension
    world.say(
        f"{hero.id}'s face lit up and {hero.pronoun()} hugged "
        f"{hero.pronoun('possessive')} {mentor.label_word}. "
        f'"Yay, let\'s share it!" {hero.pronoun()} said.'
    )
    world.say(
        f"They {helper_def.tail}. Soon {hero.id} was {kind_act.gerund}, "
        f"{carrier_was_glowing(hero, carrier)}, and {mentor.label_word} was laughing beside "
        f"{hero.pronoun('object')}."
    )


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, kind_act: KindAct, carrier_cfg: Carrier,
         hero_name: str = "Mox", hero_type: str = "morphodite",
         hero_traits: Optional[list[str]] = None,
         mentor_type: str = "morphodite") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else kind_act.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["playful", "stubborn"]),
    ))
    mentor = world.add(Entity(id="Mentor", kind="character", type=mentor_type,
                              label="the mentor"))
    carrier = world.add(Entity(
        id="carrier", type=carrier_cfg.type, label=carrier_cfg.label,
        phrase=carrier_cfg.phrase, owner=hero.id, caretaker=mentor.id,
        slot=carrier_cfg.slot, plural=carrier_cfg.plural,
    ))

    # Act 1 -- setup: who, what they love, the carrier they hold.
    introduce(world, hero)
    loves_kind_act(world, hero, kind_act)
    buys(world, mentor, hero, carrier)
    loves_carrier(world, hero, carrier)

    # Act 2 -- conflict: desire vs. the predicted drain, ending in a grabbed tail.
    world.para()
    arrive(world, hero, mentor, kind_act)
    wants(world, hero, mentor, kind_act)
    warn(world, mentor, hero, kind_act, carrier)
    defies(world, hero, kind_act)
    grab_hand(world, mentor, hero, kind_act)

    # Act 3 -- resolution: a compatible move (conserving helper) clears the conflict.
    world.para()
    pout(world, hero, kind_act)
    helper_def = compromise(world, mentor, hero, kind_act, carrier)
    if helper_def:
        accept(world, mentor, hero, kind_act, carrier, helper_def)

    # Record facts for the Q&A generators (grounded in the simulated world).
    world.facts.update(hero=hero, mentor=mentor, carrier=carrier,
                       carrier_cfg=carrier_cfg, kind_act=kind_act,
                       setting=setting, helper=helper_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=helper_def is not None)
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "moon_zin": Setting(place="the moon Zin", indoor=False,
                        affords={"sparkle", "hum", "twinkle"}),
    "asteroid_plo": Setting(place="the asteroid Plo", indoor=False,
                            affords={"sparkle", "twinkle"}),
    "comet_field": Setting(place="the comet field", indoor=False,
                           affords={"hum", "twinkle"}),
    "star_garden": Setting(place="the star garden", indoor=False,
                           affords={"sparkle", "hum"}),
    "tin_hangar": Setting(place="the tin hangar", indoor=True,
                          affords={"hum", "twinkle"}),
}

KIND_ACTS = {
    # Sharing a sparkle drains the pouch only -- NOT the wings or core.
    "sparkle": KindAct(
        id="sparkle",
        verb="share a sparkle of sharing magic",
        gerund="sharing a sparkle of magic",
        rush="fly straight to the lonely meteor",
        glow="sparkle",
        drain="drained of sparkle",
        zone={"pouch"},
        weather="starry",
        keyword="sharing",
        tags={"sharing", "sparkle"},
    ),
    # Humming reaches the tail-tuft as well as the pouch -- broader carrier risk.
    "hum": KindAct(
        id="hum",
        verb="hum a kind hum",
        gerund="humming a kind hum",
        rush="zip toward the quiet rock",
        glow="hum",
        drain="hushed and quiet",
        zone={"pouch", "tail-tuft"},
        weather="starry",
        keyword="hum",
        tags={"hum", "kind"},
    ),
    # Twinkling reaches the core too -- a high-cost generous act.
    "twinkle": KindAct(
        id="twinkle",
        verb="twinkle for the lonely comet",
        gerund="twinkling for the lonely comet",
        rush="spin toward the lonely comet",
        glow="twinkle",
        drain="dim and pale",
        zone={"pouch", "core"},
        weather="comet-bright",
        keyword="twinkle",
        tags={"twinkle", "kind"},
    ),
}

# Order matters: more specific helpers first, broader fallback last.  Each
# helper only conserves the slots it actually covers (the core rule).
HELPERS = [
    Helper(
        id="sharing_pouch",
        label="a sharing-pouch",
        guards={"sparkle"},
        covers={"pouch"},
        prep="use the sharing-pouch first",
        tail="went back to the rocket to get the sharing-pouch",
    ),
    Helper(
        id="calm_cloak",
        label="a calm cloak",
        guards={"hum"},
        covers={"pouch", "tail-tuft"},
        prep="wrap up in the calm cloak first",
        tail="flew back to fetch the calm cloak",
    ),
    Helper(
        id="kind_lantern",
        label="a kind lantern",
        guards={"twinkle"},
        covers={"pouch", "core"},
        prep="light the kind lantern first",
        tail="went to get the kind lantern",
    ),
    Helper(
        id="gentle_wings",
        label="old gentle wings",
        guards={"sparkle", "hum", "twinkle"},
        covers={"pouch", "tail-tuft", "core"},
        prep="put on the old gentle wings first",
        tail="went to get the old gentle wings",
        plural=True,
    ),
]

CARRIERS = {
    "pouch": Carrier(
        label="pouch",
        phrase="a soft, glowing sharing-pouch",
        type="pouch",
        slot="pouch",
    ),
    "tail_tuft": Carrier(
        label="tail-tuft",
        phrase="a fuzzy little tail-tuft charm",
        type="tail-tuft",
        slot="tail-tuft",
    ),
    "lantern": Carrier(
        label="lantern",
        phrase="a tiny star-shaped lantern",
        type="lantern",
        slot="core",
    ),
    "wings": Carrier(
        label="wings",
        phrase="a pair of soft, sparkly wings",
        type="wings",
        slot="wings",
        plural=True,
    ),
}

HERO_NAMES = ["Mox", "Lilo", "Bibi", "Tavi", "Nori", "Pim", "Koko", "Vee", "Lumi", "Eki"]
TRAITS = ["playful", "curious", "stubborn", "cheerful", "spirited", "lively"]


def valid_combos() -> list[tuple[str, str]]:
    """(place, kind_act, carrier) triples that pass the reasonableness constraint."""
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = KIND_ACTS[act_id]
            for carrier_id, carrier in CARRIERS.items():
                if carrier_at_risk(act, carrier) and select_helper(act, carrier):
                    combos.append((place, act_id, carrier_id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    kind_act: str
    carrier: str
    name: str
    trait: str
    mentor: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.  These are answerable WITHOUT
# the story; they explain the *elements* the world is built from.
KNOWLEDGE = {
    "morphodite": [
        ("What is a morphodite?",
         "A morphodite is a kind, sparkly creature from a tiny moon. "
         "Morphodites can take the shape of whoever they meet, and they love "
         "making new friends."),
    ],
    "sharing": [
        ("Why is sharing nice?",
         "Sharing is nice because when you share, everyone gets a little bit "
         "of the good thing, and no one is left out."),
    ],
    "magic": [
        ("What is sharing magic?",
         "Sharing magic is a tiny pinch of sparkle that turns one kind thing "
         "into enough for everyone."),
    ],
    "sparkle": [
        ("What is a sparkle of magic?",
         "A sparkle of magic is a tiny glowing bit of kindness. When you share "
         "it, the sparkle grows instead of shrinking."),
    ],
    "hum": [
        ("Why does humming feel kind?",
         "Humming is a soft, steady sound. When someone hums for you, it can "
         "feel like the night is being kind on purpose."),
    ],
    "twinkle": [
        ("What is a twinkle?",
         "A twinkle is a tiny quick flash of light, like a star winking hello. "
         "Many twinkles together make the dark feel friendly."),
    ],
    "moon": [
        ("What is a moon?",
         "A moon is a round piece of rock that goes around a planet. Some "
         "moons are small and green, and some are grey and dusty."),
    ],
    "asteroid": [
        ("What is an asteroid?",
         "An asteroid is a small rocky object that floats in space. It is "
         "much smaller than a planet and is often shaped like a potato."),
    ],
    "rocket": [
        ("What does a tiny rocket do?",
         "A tiny rocket is a little ship that takes morphodites on short "
         "trips between moons and asteroids."),
    ],
    "sharing_pouch": [
        ("What is a sharing-pouch?",
         "A sharing-pouch is a soft, glowing bag that holds just enough "
         "sharing magic for one kind act at a time."),
    ],
    "calm_cloak": [
        ("What does a calm cloak do?",
         "A calm cloak is a soft wrap that keeps the kind hum from "
         "spreading too thin, so the carrier stays glowing."),
    ],
    "kind_lantern": [
        ("What is a kind lantern?",
         "A kind lantern is a small star-shaped light that helps a morphodite "
         "twinkle for others without dimming their own core."),
    ],
    "gentle_wings": [
        ("What are gentle wings?",
         "Gentle wings are old, soft wings that a morphodite can wear so "
         "any kind of magic stays safely inside them."),
    ],
}
KNOWLEDGE_ORDER = ["morphodite", "sharing", "magic", "sparkle", "hum", "twinkle",
                   "moon", "asteroid", "rocket",
                   "sharing_pouch", "calm_cloak", "kind_lantern", "gentle_wings"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, mentor, act, carrier = (f["hero"], f["mentor"], f["kind_act"], f["carrier_cfg"])
    kw = act.keyword or act.glow
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "sharing, '
        f'magic, and a tiny space adventure" that includes the word "{kw}".',
        f"Tell a gentle space story where a {hero.type} named {hero.id} wants "
        f"to {act.verb} but {hero.pronoun('possessive')} {mentor.label_word} worries "
        f"about {carrier.phrase}, and they find a happy compromise.",
        f'Write a simple story that uses the noun "{kw}" and ends with a mentor '
        f"and child pausing to choose a safer, kinder way to share.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, mentor, carrier, act = (f["hero"], f["mentor"], f["carrier"], f["kind_act"])
    mw = mentor.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    where = "at home" if world.setting.indoor else "out among the stars"
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    night = {"starry": "starry night", "comet-bright": "comet-bright night"}.get(
        world.weather, "quiet evening"
    )
    # Keep story QA heavily parametrized by sampled story state. These should
    # vary with names, roles, setting, kind_act, carrier, conflict, and outcome
    # as much as possible so the training set does not learn invariant QA shells.
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} visits {place} to "
                f"{act.verb} with {pos} {carrier.label}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pos} {mw}. They go to {place} on a {night}, and {hero.id} is "
                f"holding {pos} {carrier.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do {where} in {place} before "
                f"{mw} worried about {pos} {carrier.label}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved {act.gerund} {where}. "
                f"That wish became tricky because {pos} {carrier.label} could "
                f"get drained."
            ),
        ),
        QAItem(
            question=(
                f"What new {carrier.label} did {hero.id}'s {mw} give the "
                f"{trait} {hero.type} before "
                f"the {act.keyword or act.glow} kindness at {place}?"
            ),
            answer=(
                f"{pos.capitalize()} {mw} gave {obj} {carrier.phrase}. "
                f"{hero.id} loved {carrier.it()} and held {carrier.it()} for the outing."
            ),
        ),
    ]
    # The featured question: how/why the mentor was worried -- grounded in the
    # predicted drain (the world model run forward) and the grabbed-tail conflict.
    if f.get("conflict"):
        drain = f.get("predicted_drain", "drained")
        work = f.get("predicted_tired", 0)
        why = (f"{pos.capitalize()} {mw} was worried because if {hero.id} went to "
               f"{act.verb}, {pos} {carrier.label} would get {drain}")
        why += (f", and then {mw} would have to recharge {carrier.it()}. "
                if work >= THRESHOLD else ". ")
        why += (f"When {hero.id} tried to {act.rush.rstrip(', ')}, {pos} {mw} "
                f"held {pos} tail and reminded {obj} they could still want to "
                f"{act.verb} while choosing a safer way.")
        qa.append(QAItem(
            question=(
                f"Why did {hero.id}'s {mw} worry about {pos} {carrier.label} "
                f"when {trait} {hero.id} wanted to {act.verb} at {place}?"
            ),
            answer=why,
        ))
    if f.get("resolved"):
        helper = f["helper"]
        helper_plan = helper.label
        if helper_plan.startswith(("a ", "an ")):
            helper_plan = helper_plan.split(" ", 1)[1]
        qa.append(QAItem(
            question=(
                f"How did {helper.label} help {trait} {hero.id} {act.verb} at {place} "
                f"without draining {pos} {carrier.label}?"
            ),
            answer=(
                f"They agreed to use {helper.label} first, so {hero.id} could "
                f"{act.verb} at {place} without draining {pos} {carrier.label}. "
                f"The plan let {obj} share while {pos} {carrier.label} stayed glowing."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel after {mw} agreed to the {helper_plan} "
                f"plan for {act.keyword or act.glow} at {place}?"
            ),
            answer=(
                f"{hero.id} felt happy and hugged {pos} {mw} once they agreed "
                f"on the plan for {pos} {carrier.label}. At the end, {sub} was "
                f"{act.gerund} with {mw} laughing nearby."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = set(f["kind_act"].tags)
    if f.get("helper"):
        tags.add(f["helper"].id)
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
        elif e.slot:
            bits.append(f"slot={e.slot}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="moon_zin",
        kind_act="sparkle",
        carrier="pouch",
        name="Mox",
        trait="playful",
        mentor="morphodite",
    ),
    StoryParams(
        place="asteroid_plo",
        kind_act="twinkle",
        carrier="lantern",
        name="Lilo",
        trait="curious",
        mentor="morphodite",
    ),
    StoryParams(
        place="comet_field",
        kind_act="hum",
        carrier="tail_tuft",
        name="Bibi",
        trait="lively",
        mentor="morphodite",
    ),
    StoryParams(
        place="star_garden",
        kind_act="sparkle",
        carrier="wings",
        name="Tavi",
        trait="spirited",
        mentor="morphodite",
    ),
    StoryParams(
        place="tin_hangar",
        kind_act="hum",
        carrier="pouch",
        name="Nori",
        trait="cheerful",
        mentor="morphodite",
    ),
]


def explain_rejection(kind_act: KindAct, carrier: Carrier) -> str:
    noun = carrier.label if carrier.plural else f"a {carrier.label}"
    verb = "sit" if carrier.plural else "sits"
    if not carrier_at_risk(kind_act, carrier):
        return (f"(No story: {kind_act.gerund} drains {sorted(kind_act.zone)}, "
                f"but {noun} {verb} on the {carrier.slot} -- it wouldn't get "
                f"{kind_act.glow}-less, so the mentor has no honest warning. "
                f"Try a carrier held in {sorted(kind_act.zone)}.)")
    return (f"(No story: nothing in the helper catalog conserves {noun} "
            f"({carrier.slot}) during {kind_act.gerund}. The compromise must "
            f"actually cover the at-risk carrier, so this argument is rejected.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (carrier_at_risk / select_helper / valid_combos).  The rules are inline
# below; the facts are generated from the registries above so the two can
# never drift.  Uses the shared `asp` helper + clingo, imported lazily so
# the prose engine runs without them.  See --verify.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A carrier is at risk when the kind act drains the slot it is held in.
carrier_at_risk(A, C) :- drains(A, S), held_in(C, S).

% A helper is a compatible fix only when it both conserves the glow kind AND
% covers the at-risk slot (sharing-pouch guards sparkle but covers only pouch).
protects(H, A, C) :- helper(H), carrier_at_risk(A, C),
                     glow_of(A, G), conserves(H, G),
                     covers(H, S), held_in(C, S).
has_fix(A, C) :- protects(_, A, C).

valid(Place, A, C) :- affords(Place, A), carrier_at_risk(A, C), has_fix(A, C).
valid_story(Place, A, C) :- valid(Place, A, C).
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
    for aid, a in KIND_ACTS.items():
        lines.append(asp.fact("kind_act", aid))
        lines.append(asp.fact("glow_of", aid, a.glow))
        for s in sorted(a.zone):
            lines.append(asp.fact("drains", aid, s))
    for cid, c in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("held_in", cid, c.slot))
        if c.plural:
            lines.append(asp.fact("carrier_plural", cid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for g in sorted(h.guards):
            lines.append(asp.fact("conserves", h.id, g))
        for s in sorted(h.covers):
            lines.append(asp.fact("covers", h.id, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (place, kind_act, carrier) triples."""
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    """(place, kind_act, carrier) -- the gate is gender-agnostic here."""
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
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
        description="Story world sketch: a morphodite, sharing magic, a tiny "
                    "space adventure. Unspecified choices are picked at random "
                    "(seeded).")
    # A small, debuggable set of pins; any omitted choice is randomized.
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--kind-act", dest="kind_act", choices=KIND_ACTS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--mentor", choices=["morphodite"])
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
    if args.kind_act and args.carrier:
        act, car = KIND_ACTS[args.kind_act], CARRIERS[args.carrier]
        if not (carrier_at_risk(act, car) and select_helper(act, car)):
            raise StoryError(explain_rejection(act, car))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.kind_act is None or c[1] == args.kind_act)
              and (args.carrier is None or c[2] == args.carrier)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, kind_act, carrier_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    mentor = args.mentor or "morphodite"
    return StoryParams(
        place=place,
        kind_act=kind_act,
        carrier=carrier_id,
        name=name,
        trait=trait,
        mentor=mentor,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(SETTINGS[params.place], KIND_ACTS[params.kind_act],
                 CARRIERS[params.carrier], params.name, "morphodite",
                 [params.trait, "stubborn"], params.mentor)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, kind_act, carrier) combos "
              f"({len(stories)} in clingo):\n")
        for place, act, carrier in triples:
            print(f"  {place:14} {act:9} {carrier:10}")
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
            header = f"### {p.name}: {p.kind_act} at {p.place} (carrier: {p.carrier})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
