#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/thicket_tidal_pool_repetition_conflict_reconciliation_heartwarming.py
==================================================================================

Storyworld: thicket / tidal pool -- heartwarming, with a thread of repetition,
a small conflict, and a gentle reconciliation.

Initial story (used to build the world model):
---
Once upon a time, in a quiet cove beside a tidal pool, there was a little
girl named Mira who loved poking through the thicket of green sea-anemones
that grew along the rocks. Every morning she would count them -- "one,
two, three" -- because counting them made her feel that the tide had not
rushed them away.

One day a boy named Theo came to the pool. He saw the same anemones and
thought they looked like soft jewels. He wanted to pick one for his mom.
But Mira's grandmother had taught her: "anemones are not for taking --
they belong to the tide." Mira shook her head and said, "Please don't
pick them. They are the pool's breath."

Theo's face went tight, and he tugged gently at a small green one anyway.
Mira tugged his sleeve and said, "Stop! You'll hurt it, and then the pool
will be quieter." Theo frowned, pulled his hand back, and the little
anemone slowly closed its petals as if it had sighed.

For a while the two children did not speak. Mira pointed at the wave
rings on the sand and said, "Look, the tide is breathing." Theo nodded
and said, "I will count them with you." They sat together at the pool's
edge and counted the anemones again -- "one, two, three" -- and this time
Theo counted too. At the end of the morning the pool was still full of
soft, breathing color, and the two children walked home side by side,
their hands full of nothing but sea air.

Causal state updates:
---
    do activity (poke / count / wave) -> actor.<engagement> += 1
                                        actor.calm += 1
    child intrudes (tries to pick)    -> actor.conflict += 1
                                        anemone.threatened += 1
    anemone.threatened & not soothed  -> pool.health -= 1
    child soothes anemone            -> anemone.threatened -> 0
                                        pool.health += 1
    one-sided care                   -> actor.shame += 1
    shared care                      -> actor.joy += 1 ; actor.conflict -> 0
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Body / region vocabulary is small: "hand", "eye", "voice".  Used for the
# gear / instrument coverage constraint below (the magnifying glass covers
# the eye, a gentle hand covers the hand, etc.).
REGIONS = {"hand", "eye", "voice"}

# Species / pool features -- the "things" that live in this domain.  Kept as a
# set so we can extend the taxonomy later without rewriting rules.
POOL_FEATURES = {"anemone", "shell", "tide_pool", "thicket", "wave", "ripple"}


# ---------------------------------------------------------------------------
# Entities: characters, instruments, and pool features share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, grandmother, magnifying_glass ...
    label: str = ""                # short reference, e.g. "the boy"
    phrase: str = ""               # full noun phrase, e.g. "a small magnifying glass"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None   # who feels responsible for this entity
    held_by: Optional[str] = None     # an instrument currently being held
    region: str = ""                  # where the actor uses this: hand | eye | voice
    protective: bool = False          # instrument that soothes rather than intrudes
    soothes: set[str] = field(default_factory=set)   # features this instrument calms
    plural: bool = False              # "waves" -> them, "anemone" -> it
    # Two numeric dimensions (meters = physical, memes = emotional), treated
    # uniformly, just like story.py's memeplex model.
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "grandmother", "mother", "mom", "woman"}
        male = {"boy", "grandfather", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad",
                "grandmother": "grandma", "grandfather": "grandpa"}.get(
            self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    """The body of water and the shore where the story happens."""
    id: str
    place: str               # e.g. "the tidal pool", "the rocky cove"
    feature: str             # the keyword for this setting (e.g. "tidal pool")
    weather: str = "calm"    # "calm" | "windy" | ""
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    """A gentle thing the hero loves to do at the pool."""
    id: str
    verb: str            # after "wanted to ..."             : "poke the anemones"
    gerund: str          # after "loved ... and ..."         : "poking the anemones"
    rush: str            # after "tried to ..."              : "reach into the pool"
    engagement: str      # meter key this activity drives    : "engagement"
    zone: set[str]       # body regions this activity uses   : {"hand", "eye"}
    keyword: str = ""    # topic word for prompts            : "anemones"
    tags: set[str] = field(default_factory=set)


@dataclass
class Feature:
    """A living feature of the pool -- e.g. an anemone thicket."""
    id: str
    label: str           # "anemones"
    phrase: str          # "a thicket of green anemones"
    type: str            # "anemone"
    region: str          # body region picking would reach: "hand"
    countable: bool = True
    plural: bool = True
    moods: set[str] = field(default_factory=set)  # which emotions a child may feel


@dataclass
class Instrument:
    """A protective instrument used in the compromise."""
    id: str
    label: str
    covers: set[str]     # body regions it shields (hand, eye, voice)
    soothes: set[str]    # pool features it calms (anemone, wave)
    prep: str            # body of the offer: "use the magnifying glass first"
    tail: str            # closing clause: "shared the magnifying glass"
    plural: bool = False


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
        self.weather: str = ""
        # Read-back by Q&A generators.
        self.facts: dict = {}

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def features(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "thing"]

    def held_by(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.held_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(i.protective and region in i.covers for i in self.held_by(actor))

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
        clone.weather = self.weather
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


def _r_soothe_intrusion(world: World) -> list[str]:
    """actor intrudes (try to pick) + uncovered hand -> anemone threatened,
    actor conflict, pool health -- unless a soothing instrument is in use."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["intrudes"] < THRESHOLD:
            continue
        for feat in world.features():
            if "anemone" not in feat.id:
                continue
            if world.covered(actor, "hand") and feat.type in _instrument_soothes(actor):
                continue
            sig = ("threat", feat.id, actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            feat.meters["threatened"] += 1
            actor.memes["conflict"] += 1
    return out


def _instrument_soothes(actor: Entity) -> set[str]:
    soothes: set[str] = set()
    for ins in actor.memes.get("_held", []) if False else []:
        pass
    # Note: we walk world.held_by explicitly below via meters bookkeeping.
    return soothes


def _r_pool_health(world: World) -> list[str]:
    """anemone threatened & not soothed -> pool health decays."""
    out: list[str] = []
    for feat in world.features():
        if "anemone" not in feat.id:
            continue
        if feat.meters["threatened"] < THRESHOLD or feat.meters["soothed"] >= THRESHOLD:
            continue
        sig = ("pool_decay", feat.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        # Find the pool feature and decay it.
        for pool in world.features():
            if pool.type == "tide_pool":
                pool.meters["health"] -= 1
    return out


def _r_one_sided_care(world: World) -> list[str]:
    """One child cared while the other intruded -> a gentle shame on intruder."""
    out: list[str] = []
    carers = [a for a in world.characters()
              if a.memes["cares"] >= THRESHOLD and a.memes["intrudes"] < THRESHOLD]
    intruders = [a for a in world.characters() if a.memes["intrudes"] >= THRESHOLD]
    if not carers or not intruders:
        return out
    for intruder in intruders:
        sig = ("shame", intruder.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        intruder.memes["shame"] += 1
    return out


def _r_shared_care(world: World) -> list[str]:
    """Two children share a counting/soothing act -> both joy, conflict cleared."""
    out: list[str] = []
    carers = [a for a in world.characters() if a.memes["cares"] >= THRESHOLD]
    if len(carers) < 2:
        return out
    for actor in carers:
        sig = ("joy", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] += 1
        actor.memes["conflict"] = 0.0
    return out


def _r_anemone_calmed(world: World) -> list[str]:
    """soothing instrument held + anemone threatened -> anemone soothed, pool +1."""
    out: list[str] = []
    for actor in world.characters():
        for ins in world.held_by(actor):
            if not ins.protective:
                continue
            for feat in world.features():
                if "anemone" not in feat.id:
                    continue
                if feat.meters["threatened"] < THRESHOLD:
                    continue
                if feat.type not in ins.soothes:
                    continue
                sig = ("calm", feat.id, ins.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                feat.meters["soothed"] += 1
                feat.meters["threatened"] = 0.0
                for pool in world.features():
                    if pool.type == "tide_pool":
                        pool.meters["health"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="intrusion_threat", tag="physical", apply=_r_soothe_intrusion),
    Rule(name="pool_decay", tag="physical", apply=_r_pool_health),
    Rule(name="one_sided_care", tag="social", apply=_r_one_sided_care),
    Rule(name="anemone_calmed", tag="physical", apply=_r_anemone_calmed),
    Rule(name="shared_care", tag="social", apply=_r_shared_care),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what makes a *reasonable* setup and a *reasonable* fix.
# ---------------------------------------------------------------------------
def feature_at_risk(activity: Activity, feature: Feature) -> bool:
    """Would this activity actually threaten this feature (right body region)?"""
    return feature.region in activity.zone


def select_instrument(activity: Activity, feature: Feature) -> Optional[Instrument]:
    """The compatible instrument: one that soothes the feature AND covers the
    at-risk region (a magnifying glass covers the eye but not the hand)."""
    for ins in INSTRUMENTS:
        if feature.type in ins.soothes and activity.zone & ins.covers:
            return ins
    return None


def select_companion_activity(setting: Setting, feature: Feature) -> Optional[str]:
    """A second activity the *companion* child can do alongside the hero --
    must also be afforded by the setting."""
    for act_id in setting.affords:
        if act_id == "count":
            return act_id
    return None


# ---------------------------------------------------------------------------
# Prediction: forward-simulate to foresee harm or healing before deciding what
# to say.
# ---------------------------------------------------------------------------
def predict_threat(world: World, actor: Entity, activity: Activity,
                   feature_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    feat = sim.entities.get(feature_id)
    pool = next((p for p in sim.features() if p.type == "tide_pool"), None)
    return {
        "threatened": bool(feat and feat.meters["threatened"] >= THRESHOLD),
        "pool_health": (pool.meters["health"] if pool else 0.0),
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def activity_detail(activity: Activity) -> str:
    return {
        "count": "each soft shape opened and closed like a small breath",
        "watch": "the colors rippled under the surface like tiny stained-glass",
        "wave": "the wave rings spread out and ran back again like a heartbeat",
    }.get(activity.id, "the pool felt alive with small, patient colors")


def setting_detail(setting: Setting) -> str:
    if setting.weather == "windy":
        return f"{setting.place.capitalize()} was bright, and the wind combed the surface."
    return f"{setting.place.capitalize()} was quiet, and the water sat in glassy pockets."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.engagement] += 1
    actor.memes["calm"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who liked to listen to small, quiet places.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["cares"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved going to {world.setting.place} and "
        f"{activity.gerund}; {activity_detail(activity)}."
    )


def arrives(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"One calm morning, {hero.id} went to {world.setting.place}."
    )
    world.say(setting_detail(world.setting))


def meets_companion(world: World, hero: Entity, other: Entity) -> None:
    world.say(
        f"There, by the edge of the water, sat {other.pronoun('object')} -- "
        f"a curious little {other.type} named {other.id}."
    )


def names_feature(world: World, hero: Entity, feature: Feature) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} showed {other_pronoun(hero)} the "
        f"{feature.label}, and said, \"{feature.phrase}.\"")


def other_pronoun(hero: Entity) -> str:
    # Used when a narrator describes the hero in the third person after
    # naming the companion.
    return "them"


def wants_to_help(world: World, other: Entity, feature: Feature) -> None:
    other.memes["cares"] += 1
    world.say(
        f"{other.id} thought the {feature.label} looked like soft jewels and "
        f"wanted to take one home."
    )


def warns(world: World, hero: Entity, feature: Feature, activity: Activity) -> bool:
    """The hero foresees the harm via the world model and warns about it."""
    pred = predict_threat(world, hero, activity, feature.id)
    if not pred["threatened"]:
        return False
    world.facts["predicted_threat"] = feature.label
    world.facts["predicted_pool"] = pred["pool_health"]
    clause = (f'"{feature.label.capitalize()} are not for taking -- they belong '
              f'to the tide," {hero.pronoun("subject")} said softly.')
    world.say(clause)
    return True


def intrudes(world: World, other: Entity, activity: Activity) -> None:
    other.memes["intrudes"] += 1
    world.say(
        f"But the wish to take one was still tugging at {other.pronoun('object')}, "
        f"and {other.pronoun('subject')} tried to reach for the {ACTIVITY_OBJ[activity.id]}."
    )


def hero_stops(world: World, hero: Entity, other: Entity, feature: Feature) -> None:
    hero.memes["conflict"] += 1
    other.memes["grabbed_by"] = other.memes.get("grabbed_by", 0.0) + 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.pronoun('subject').capitalize()} tugged {other.pronoun('possessive')} "
        f"sleeve and said, \"Please don't pick them. They are the pool's breath.\""
    )


def anemone_sighs(world: World, feature: Feature) -> None:
    world.say(
        f"The little {feature.label_word(feature) if False else feature.label[:-1] if feature.label.endswith('s') else feature.label} "
        f"closed its petals slowly, as if it had sighed."
    )


def label_word(feature: Feature) -> str:
    return feature.label if feature.plural else feature.label


# helper: ACT-3 uses instruments and reconciliation
def quiet_silence(world: World, hero: Entity, other: Entity) -> None:
    if other.memes.get("shame", 0.0) >= THRESHOLD or other.memes["conflict"] >= THRESHOLD:
        world.say(
            f"For a while neither of them spoke; the water did its small talking."
        )


def hero_invites(world: World, hero: Entity, other: Entity, activity: Activity,
                 feature: Feature, setting: Setting) -> Optional[Instrument]:
    """Offer an instrument that soothes & covers the at-risk region; only emit
    prose if the world model then predicts no harm (a compatible move)."""
    ins_def = select_instrument(activity, feature)
    if ins_def is None:
        return None
    instrument = world.add(Entity(
        id=ins_def.id, type="instrument", label=ins_def.label,
        owner=hero.id, caretaker=hero.id, protective=True,
        covers=set(ins_def.covers), soothes=set(ins_def.soothes),
        region=("eye" if "eye" in ins_def.covers else
                "hand" if "hand" in ins_def.covers else "voice"),
        plural=ins_def.plural,
    ))
    instrument.held_by = hero.id
    if predict_threat(world, hero, activity, feature.id)["threatened"]:
        instrument.held_by = None
        del world.entities[instrument.id]
        return None
    companion_act_id = select_companion_activity(setting, feature)
    companion_act = ACTIVITIES.get(companion_act_id) if companion_act_id else None
    world.say(
        f'{hero.pronoun("subject").capitalize()} held out {ins_def.label} and said, '
        f'"How about we {ins_def.prep} and {activity.verb} together?"'
    )
    return ins_def


def reconciliation(world: World, hero: Entity, other: Entity, feature: Feature,
                   activity: Activity, ins_def: Optional[Instrument],
                   setting: Setting) -> None:
    """Act 3: the children share a counting/soothing act, the pool is at peace."""
    if ins_def:
        world.say(
            f"They {ins_def.tail}, and {other.id} reached a hand toward the "
            f"{feature.label} very gently this time."
        )
    other.memes["cares"] += 1
    hero.memes["cares"] += 1
    hero.memes["conflict"] = 0.0
    other.memes["conflict"] = 0.0
    other.memes["joy"] = other.memes.get("joy", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    propagate(world, narrate=False)
    world.say(
        f"They sat together at the pool's edge and counted the "
        f"{feature.label} again -- \"one, two, three\" -- and this time "
        f"{other.id} counted too."
    )
    world.say(
        f"At the end of the morning, {world.setting.place} was still full of "
        f"soft, breathing color, and the two children walked home side by side, "
        f"their hands full of nothing but sea air."
    )


# Tiny lookup used by `intrudes` to phrase what was being reached for.
ACTIVITY_OBJ = {
    "count": "anemones",
    "watch": "anemones",
    "wave": "anemones",
}


# ---------------------------------------------------------------------------
# The screenplay: three-act shape driven by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, feature_cfg: Feature,
         hero_name: str = "Mira", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None,
         other_name: str = "Theo", other_type: str = "boy") -> World:
    world = World(setting)
    world.weather = setting.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["gentle", "watchful"]),
    ))
    other = world.add(Entity(
        id=other_name, kind="character", type=other_type,
        traits=["little", "curious", "eager"],
    ))
    feature = world.add(Entity(
        id="feature", type=feature_cfg.type, label=feature_cfg.label,
        phrase=feature_cfg.phrase, caretaker=hero.id, region=feature_cfg.region,
        plural=feature_cfg.plural,
    ))
    # Pool: a single entity representing the tidal pool's overall health.
    world.add(Entity(
        id="pool", type="tide_pool", label="tidal pool",
        caretaker=hero.id, region="",
    ))

    # Act 1 -- setup: who, what they love, what the pool looks like.
    introduce(world, hero)
    loves_activity(world, hero, activity)
    arrives(world, hero, activity)
    meets_companion(world, hero, other)
    names_feature(world, hero, feature)
    wants_to_help(world, other, feature)

    # Act 2 -- conflict: warning, intrusion, gentle stop.
    world.para()
    warns(world, hero, feature, activity)
    intrudes(world, other, activity)
    hero_stops(world, hero, other, feature)
    if feature.meters["threatened"] >= THRESHOLD:
        anemone_sighs(world, feature)
    quiet_silence(world, hero, other)

    # Act 3 -- reconciliation: an instrument + shared care clears the tension.
    world.para()
    ins_def = hero_invites(world, hero, other, activity, feature, setting)
    reconciliation(world, hero, other, feature, activity, ins_def, setting)

    # Record facts for the Q&A generators.
    world.facts.update(hero=hero, other=other, feature=feature, feature_cfg=feature_cfg,
                       activity=activity, setting=setting, instrument=ins_def,
                       conflict=(hero.memes["conflict"] >= THRESHOLD
                                 or other.memes["conflict"] >= THRESHOLD),
                       resolved=True)
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "tidal_pool": Setting(
        id="tidal_pool",
        place="the tidal pool",
        feature="tidal pool",
        weather="calm",
        affords={"count", "watch", "wave"},
    ),
    "rocky_cove": Setting(
        id="rocky_cove",
        place="the rocky cove",
        feature="cove",
        weather="calm",
        affords={"count", "watch", "wave"},
    ),
    "sea_garden": Setting(
        id="sea_garden",
        place="the sea garden",
        feature="sea garden",
        weather="windy",
        affords={"count", "watch"},
    ),
}

ACTIVITIES = {
    "count": Activity(
        id="count",
        verb="count the anemones",
        gerund="counting the anemones",
        rush="reach for an anemone",
        engagement="engagement",
        zone={"hand", "eye"},
        keyword="anemones",
        tags={"anemone", "thicket", "repetition"},
    ),
    "watch": Activity(
        id="watch",
        verb="watch the anemones",
        gerund="watching the anemones",
        rush="lean close to the water",
        engagement="engagement",
        zone={"eye"},
        keyword="anemones",
        tags={"anemone", "thicket"},
    ),
    "wave": Activity(
        id="wave",
        verb="trace the wave rings",
        gerund="tracing the wave rings",
        rush="dip a finger in the water",
        engagement="engagement",
        zone={"hand"},
        keyword="wave",
        tags={"wave", "ripple"},
    ),
}

FEATURES = {
    "anemone_thicket": Feature(
        id="anemone_thicket",
        label="anemones",
        phrase="a thicket of green anemones",
        type="anemone",
        region="hand",
        countable=True,
        plural=True,
        moods={"calm", "wonder"},
    ),
    "anemone_patch": Feature(
        id="anemone_patch",
        label="anemones",
        phrase="a small patch of pink anemones",
        type="anemone",
        region="hand",
        countable=True,
        plural=True,
        moods={"calm"},
    ),
    "tide_pool_full": Feature(
        id="tide_pool_full",
        label="shells",
        phrase="a pool full of striped shells",
        type="shell",
        region="hand",
        countable=True,
        plural=True,
        moods={"wonder"},
    ),
}

# Order matters: more specific instruments first.  Each instrument only
# protects the regions it actually covers (the core reasonableness rule).
INSTRUMENTS = [
    Instrument(
        id="magnifier",
        label="a small magnifying glass",
        covers={"eye"},
        soothes={"anemone"},
        prep="use the small magnifying glass first",
        tail="shared the small magnifying glass",
    ),
    Instrument(
        id="gentle_hand",
        label="a steady pointing finger",
        covers={"hand"},
        soothes={"anemone", "shell"},
        prep="point gently with one finger first",
        tail="agreed to point gently with one finger",
    ),
    Instrument(
        id="soft_voice",
        label="a soft counting voice",
        covers={"voice"},
        soothes={"anemone", "wave"},
        prep="count softly together first",
        tail="counted softly together",
    ),
]

GIRL_NAMES = ["Mira", "Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Nora", "Rose"]
BOY_NAMES = ["Theo", "Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli"]
TRAITS = ["gentle", "watchful", "patient", "quiet", "tender", "bright-eyed"]
OTHER_TRAITS = ["curious", "eager", "sunny", "soft-spoken", "wide-eyed"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(place, activity, feature) triples that pass the reasonableness constraint."""
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for feat_id, feat in FEATURES.items():
                if feat.region in act.zone and select_instrument(act, feat):
                    out.append((place, act_id, feat_id))
    return out


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    activity: str
    feature: str
    name: str
    gender: str
    other_name: str
    other_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "anemone": [("What is an anemone?",
                 "An anemone is a small sea animal that lives attached to rocks "
                 "in shallow water and waves its soft, colorful petals in the tide.")],
    "tide_pool": [("What is a tidal pool?",
                   "A tidal pool is a shallow pool of seawater left on the rocks "
                   "when the tide goes out, full of small sea creatures.")],
    "thicket": [("What does a thicket of anemones look like?",
                 "A thicket of anemones looks like a small garden of soft, "
                 "petalled shapes growing close together on the rocks.")],
    "wave": [("Why do waves make rings on the sand?",
              "When a small wave slides onto the sand and runs back, it leaves "
              "thin lines called wave rings that show where the water reached.")],
    "ripple": [("What is a ripple?",
                "A ripple is a small, gentle wave that spreads out across the "
                "surface of still water.")],
    "shell": [("What is a shell?",
               "A shell is the hard, sometimes colorful outer home of a sea "
               "creature like a snail or a clam.")],
    "count": [("Why is counting anemones a kind way to play?",
               "Counting anemones is a kind way to play because you watch them "
               "without touching, and the anemones stay safe in the pool.")],
    "magnifier": [("What is a magnifying glass for?",
                   "A magnifying glass is a clear lens that makes tiny things "
                   "look bigger so you can see them without touching.")],
    "soft_voice": [("Why use a soft voice near the pool?",
                   "A soft voice keeps the water calm so the small animals "
                   "stay relaxed and open.")],
}
KNOWLEDGE_ORDER = ["anemone", "thicket", "tide_pool", "wave", "ripple",
                   "shell", "count", "magnifier", "soft_voice"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, other, feat, act = f["hero"], f["other"], f["feature_cfg"], f["activity"]
    kw = act.keyword or "tidal pool"
    return [
        f'Write a short heartwarming story for a 3-to-5-year-old on the theme '
        f'"sharing a quiet place" that includes the word "{kw}".',
        f"Tell a gentle story where a little {hero.type} named {hero.id} visits "
        f"a tidal pool with a curious {other.type} named {other.id}, and together "
        f"they find a kind way to enjoy a thicket of anemones.",
        f'Write a simple story that uses the word "thicket", features repetition '
        f"and a small conflict that ends in reconciliation, set by the sea.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, other, feat, act = f["hero"], f["other"], f["feature"], f["feature_cfg"]
    pw = other.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who goes to {place} on a calm morning and meets {other.id} by the "
                f"thicket of {feat.label}?"
            ),
            answer=(
                f"A little {trait} {hero.type} named {hero.id} goes to {place} "
                f"and meets {other.id}, a curious little {other.type}, by the "
                f"thicket of {feat.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do at {place} before meeting "
                f"{other.id} by the {feat.label}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved going to {place} and "
                f"{act.gerund}. The {feat.label} were the part {sub} liked best."
            ),
        ),
        QAItem(
            question=(
                f"Why did {other.id} want to take a {feat.label_word(feat)} home from "
                f"{place} at first?"
            ),
            answer=(
                f"{other.id} thought the {feat.label} looked like soft jewels and "
                f"wanted to give one to {pw}. {sub.capitalize() if False else other.pronoun('subject').capitalize()} "
                f"did not know that the anemones belonged to the tide."
            ),
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} stop {other.id} from picking the "
                f"{feat.label} at {place}?"
            ),
            answer=(
                f"{hero.pronoun('subject').capitalize()} tugged {other.pronoun('possessive')} "
                f"sleeve and said the {feat.label} were the pool's breath, so they "
                f"should not be taken. The little {feat.label_word(feat)} closed its "
                f"petals as if it had sighed, and the children sat in silence for a while."
            ),
        ))
    if f.get("resolved"):
        ins = f["instrument"]
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} and {other.id} make up and enjoy the "
                f"{feat.label} together at {place}?"
            ),
            answer=(
                f"{hero.pronoun('subject').capitalize()} offered {ins.label} so they "
                f"could {act.verb} together. The two children sat at the pool's edge "
                f"and counted the {feat.label} again -- 'one, two, three' -- with "
                f"{other.id} counting too, and the pool stayed full of soft color."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did the children feel at the end of their morning at {place} "
                f"after counting the {feat.label} together?"
            ),
            answer=(
                f"They felt warm and calm. They walked home side by side with their "
                f"hands full of nothing but sea air, and the {feat.label} were still "
                f"breathing softly in the water behind them."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags) | {"thicket", "tide_pool"}
    if f.get("instrument"):
        tags.add(f["instrument"].id)
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
            bits.append(f"soothes={sorted(e.soothes)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="tidal_pool",
        activity="count",
        feature="anemone_thicket",
        name="Mira",
        gender="girl",
        other_name="Theo",
        other_gender="boy",
        trait="gentle",
    ),
    StoryParams(
        place="rocky_cove",
        activity="watch",
        feature="anemone_patch",
        name="Lily",
        gender="girl",
        other_name="Sam",
        other_gender="boy",
        trait="watchful",
    ),
    StoryParams(
        place="tidal_pool",
        activity="wave",
        feature="tide_pool_full",
        name="Mia",
        gender="girl",
        other_name="Ben",
        other_gender="boy",
        trait="patient",
    ),
    StoryParams(
        place="sea_garden",
        activity="count",
        feature="anemone_thicket",
        name="Ava",
        gender="girl",
        other_name="Finn",
        other_gender="boy",
        trait="tender",
    ),
]


def explain_rejection(activity: Activity, feature: Feature) -> str:
    noun = feature.label
    if not feature_at_risk(activity, feature):
        return (f"(No story: {activity.gerund} uses {sorted(activity.zone)}, "
                f"but a {noun} lives on the {feature.region} -- it would not be "
                f"at risk, so there is no honest warning. "
                f"Try a feature whose region is in {sorted(activity.zone)}.)")
    return (f"(No story: no instrument in the catalog soothes {noun} "
            f"({feature.region}) for {activity.gerund}. The compromise must "
            f"actually calm the at-risk feature, so this argument is rejected.)")


def explain_gender(feature_id: str, gender: str) -> str:
    moods = sorted(FEATURES[feature_id].moods)
    return (f"(No story: a {FEATURES[feature_id].label} isn't a typical fit "
            f"for a {gender}'s outing here; try another feature.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (feature_at_risk / select_instrument / valid_combos).  Rules are inline below;
# facts come from the registries so the two can never drift.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A feature is at risk when the activity uses a body region the feature sits on.
feature_at_risk(A, F) :- uses(A, R), on(F, R).

% An instrument is a compatible fix only when it both soothes the feature
% AND covers a region the activity uses.
protects(I, A, F) :- instrument(I), feature_at_risk(A, F),
                     kind(F, K), soothes(I, K),
                     covers(I, R), uses(A, R).
has_fix(A, F) :- protects(_, A, F).

valid(Place, A, F) :- affords(Place, A), feature_at_risk(A, F), has_fix(A, F).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("uses", aid, r))
    for fid, f in FEATURES.items():
        lines.append(asp.fact("feature", fid))
        lines.append(asp.fact("kind", fid, f.type))
        lines.append(asp.fact("on", fid, f.region))
        if f.plural:
            lines.append(asp.fact("feature_plural", fid))
    for ins in INSTRUMENTS:
        lines.append(asp.fact("instrument", ins.id))
        for k in sorted(ins.soothes):
            lines.append(asp.fact("soothes", ins.id, k))
        for r in sorted(ins.covers):
            lines.append(asp.fact("covers", ins.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
        description="Storyworld: thicket / tidal pool -- heartwarming, with "
                    "repetition, a small conflict, and a gentle reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--feature", choices=FEATURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--other-gender", choices=["girl", "boy"])
    ap.add_argument("--other-name")
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
    if args.activity and args.feature:
        act, feat = ACTIVITIES[args.activity], FEATURES[args.feature]
        if not (feature_at_risk(act, feat) and select_instrument(act, feat)):
            raise StoryError(explain_rejection(act, feat))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.feature is None or c[2] == args.feature)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, feature_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES)
    gender = args.gender or "girl"
    other_gender = args.other_gender or "boy"
    if other_gender == gender:
        pool = BOY_NAMES if other_gender == "boy" else GIRL_NAMES
        other_name = args.other_name or rng.choice([n for n in pool if n != name] or pool)
    else:
        other_name = args.other_name or rng.choice(
            BOY_NAMES if other_gender == "boy" else GIRL_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        feature=feature_id,
        name=name,
        gender=gender,
        other_name=other_name,
        other_gender=other_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 FEATURES[params.feature], params.name, params.gender,
                 [params.trait, "watchful"], params.other_name, params.other_gender)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, feature) combos:\n")
        for place, act, feat in triples:
            print(f"  {place:11} {act:8} {feat}")
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
            header = f"### {p.name} and {p.other_name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
