#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/tick_cautionary_sound_effects_mystery_to_solve.py
=====================================================================================================================

Story world sketch: "The Tick of the Hollow Gate" -- a small cautionary myth
in which a young village listener is sent on a quest to a strange and quiet
gate, and the only clue they are given is the ticking sound that no one else
can name.

Initial story (the seed this world was built from):
---
Once upon a time, in a small village that listened to the wind, there lived a
young listener named Wren. The elders of the village spoke in careful tones
about a Hollow Gate that stood at the edge of the orchards, and they warned
every child to never, ever try to find out what made the sound that came from
it. "It tick, tick, ticks at night," the eldest of the elders would say,
"and what it counts is a thing no child should know."

One dusk, when the wind was thin and the orchard smelled of warm bark, Wren
slipped past the bread oven, past the yawning dogs, and walked alone to the
Hollow Gate. The gate was just a gate -- two old posts and a beam of wood --
but on the beam, in the dust, there was a small brass key, and beside the
key, a single line scratched into the wood: "tick is the way, the way is the
turn."

Wren listened. There it was: tick, tick, tick. The sound was small but very
honest, the way a fingernail taps on a kettle lid. From the open air on one
side of the gate came a soft wind, a cricket, a sleepy owl, and the smell of
wet grass. From the quiet side came nothing at all -- nothing but the tick.
Wren held the key up to the lock. The lock did not open. The lock did not
close. The lock did something else. The lock swallowed the key, the way a
throat swallows a song, and the tick went plip into a new shape: tock.

"Took, took, took," said the quiet side of the gate.

"I think the tick was the lock counting how many people walked through," said
Wren, very slowly, because Wren had not been sure of the words until the
words were already out. "And I think the key is the thing that lets you count
back."

Wren walked back to the village with one hand on the key-less beam and one
hand on the gate, and the elders met the young listener at the bread oven with
their careful tones and said, "What did you hear?" Wren said, "I heard a tick
that was a count of crossings. I have brought the count back with me." And the
eldest of the elders said, "Then you are the one we have been waiting for."

From that night, the village no longer feared the gate. They listened to it
together, and when the wind was thin, they walked out to it and counted back.

Causal updates and the screenplay the world runs through:
---
    do the sound check            -> ear.meters["tick"]   += 1
                                     ear.meters["tock"]   += 1
                                     ear.memes["courage"] += 1
    do the key trial              -> key.meters["used"]  += 1
                                     key.meters["swallowed"] += 1
                                     key.worn_by = None
    do the return                 -> village.memes["trust"]   += 1
                                     village.memes["fear"]    -> 0
    do the elders' verdict        -> wren.memes["station"]    += 1
                                     wren.memes["listener"]   += 1

Sound-effect beats (the small acoustic gestures that give the world its style):
    on the open side     : "the wind", "a sleepy owl", "a cricket"
    on the quiet side    : "nothing but the tick"
    at the verdict       : "the bread oven ticked, the way it always does"

Mystery beats (what the listener must piece together):
    the sound was a *count of crossings*, not a warning.
    the key is the way to *count back*.
    the gate is not a door; it is a *ledger*.
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
# (``python storyworlds/worlds/<this file>.py``): add the package dir
# (storyworlds/) to the path so ``results`` resolves regardless of cwd.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# A meter or meme has to be at least this large to be considered "embedded
# enough" to be narrated (a single boot is not yet a soaked foot, a single
# single tick is not yet a pattern).
THRESHOLD = 1.0

# Acoustic kinds the world recognises.  ``tick`` is the canonical mystery beat;
# the other kinds are the open-side ambience the listener uses to confirm
# that the quiet side is, in fact, quiet.
ACOUSTIC_KINDS = {"tick", "tock", "wind", "owl", "cricket", "oven"}

# The two acoustic zones of the Hollow Gate.  The contrast between them is the
# whole reason this is a mystery at all.
ZONE_OPEN = "open"
ZONE_QUIET = "quiet"

# The two passages a child can choose: obey the elders and never go, or slip
# past the bread oven and find out.  The screenplay only ever runs the second.
WAYS = {"obey", "investigate"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # listener, elder, gate, key, oven, dog, ...
    label: str = ""                # short reference, e.g. "the gate", "the key"
    phrase: str = ""               # full noun phrase, e.g. "a small brass key"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    # A worn/sound-emitting item's "region" here is its acoustic zone (open or
    # quiet), so the world model can check whether a sound was *meant* to
    # carry from that side of the gate.
    region: str = ""
    # Two numeric dimensions, treated uniformly:
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical / sonic
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional / mythic
    plural: bool = False
    # The list of sound effects this entity emits.  Used by the rule engine to
    # generate the *sound-effects* beats the style requires.
    sounds: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"listener-girl", "girl", "mother", "elder-woman"}
        male = {"listener-boy", "boy", "father", "elder-man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom", "father": "dad",
            "elder-woman": "eldest", "elder-man": "eldest",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Setting + props: this world is small and almost static.  The story is what
# happens when a child steps *outside* the village into a quiet acoustic zone.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    village: str
    place: str
    gate: str
    bread: str
    orchard: str
    weather: str                  # "thin-wind" | "still-air" | "rain-near"
    acoustic_open: set[str]       # sound effects on the open side of the gate
    acoustic_quiet: set[str]      # sound effects on the quiet side (always subset: {"tick"})


@dataclass
class Key:
    id: str
    label: str
    phrase: str
    material: str
    effect: str                   # what the key *does* when it touches the lock
    swallowed_clause: str         # the narrative clause for the key being swallowed


@dataclass
class Verdict:
    """What the elders say to Wren when Wren comes back with the count."""
    id: str
    line: str                     # the elders' line, in careful tones


# ---------------------------------------------------------------------------
# World: entity store + acoustic zone + screenplay history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting, key: Key, verdict: Verdict) -> None:
        self.setting = setting
        self.key_def = key
        self.verdict = verdict
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()        # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.way: str = "investigate"          # only meaningful way; the others refused upstream
        # Tracks which acoustic side the listener is currently standing on.
        self.ear_zone: str = ZONE_OPEN
        # The accumulated counts of "ticks heard" and "tocks returned".
        self.counts: dict[str, int] = {"crossings": 0, "returns": 0}
        # World-knowledge facts recorded during the screenplay, used by Q&A.
        self.facts: dict = {}

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def ear(self) -> Entity:
        return self.entities["Ear"]

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
        """Throwaway clone used for forward-simulation (the prediction rule)."""
        clone = World(self.setting, self.key_def, self.verdict)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.ear_zone = self.ear_zone
        clone.counts = dict(self.counts)
        clone.paragraphs = [[]]                # predictions are silent
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_tick_isolated(world: World) -> list[str]:
    """Standing on the open side and hearing the quiet side -> the open side
    confirms its own sounds; the quiet side remains nothing but the tick.

    Two consequences:
      - the open side gains a soft wind / owl / cricket reading
      - the quiet side resolves as a pure tick (no ambient noise bleeds across)
    """
    out: list[str] = []
    if world.ear_zone != ZONE_OPEN:
        return out
    open_kinds = sorted(world.setting.acoustic_open & ACOUSTIC_KINDS)
    for kind in open_kinds:
        sig = ("open_sound", kind)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.ear().meters[kind] += 1
    sig = ("quiet_isolation",)
    if sig not in world.fired and "tick" in world.setting.acoustic_quiet:
        world.fired.add(sig)
        world.ear().meters["tick"] += 1           # the only sound on that side
    return out


def _r_key_trial(world: World) -> list[str]:
    """The listener tries the key in the lock -> the key is swallowed, the
    tick is converted to a tock, and the count of crossings goes up by one.

    The key's *owner* is cleared (the key is now part of the gate, not Wren's
    pocket), which is the way the world shows possession has changed.
    """
    out: list[str] = []
    if "key_trial" not in world.fired_as_set():
        return out
    key = world.entities.get("Key")
    if not key or key.meters["used"] >= THRESHOLD:
        return out
    sig = ("key_trial_fire",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    key.meters["used"] += 1
    key.meters["swallowed"] += 1
    key.owner = world.setting.id                 # key now belongs to the gate
    world.ear().meters["tock"] += 1
    world.counts["crossings"] += 1
    out.append("__key_trial__")                  # marker; narrated by the beat
    return out


def _r_return_brings_count(world: World) -> list[str]:
    """Wren walks back -> the village's fear clears and trust rises; the
    listener earns the new station of 'the one we have been waiting for'.
    """
    out: list[str] = []
    if "return_walk" not in world.fired_as_set():
        return out
    sig = ("return_fire",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.counts["returns"] += 1
    village = world.entities.get("Village")
    if village is not None:
        village.memes["fear"] = 0.0
        village.memes["trust"] += 1
    wren = world.entities.get("Wren")
    if wren is not None:
        wren.memes["station"] += 1
        wren.memes["listener"] += 1
    return out


def _r_verdict_recognition(world: World) -> list[str]:
    """The eldest of the elders recognises the listener after the return."""
    out: list[str] = []
    if "elders_speak" not in world.fired_as_set():
        return out
    sig = ("verdict_fire",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    eldest = world.entities.get("Eldest")
    if eldest is not None:
        eldest.memes["recognition"] += 1
    return out


# `fired` is a set of tuples, but we want to ask "is the *name* of a beat
# already on the list".  We add beat names there directly in the verbs.
def _fired_beats(world: World) -> set[str]:
    return {n for (n, *_) in world.fired if isinstance(n, str)}


# Patch the rules so they can read which *beats* have already been logged.
def _patch(world: World) -> None:
    world.fired_as_set = lambda: _fired_beats(world)  # type: ignore[attr-defined]


CAUSAL_RULES: list[Rule] = [
    Rule(name="tick_isolated", tag="acoustic", apply=_r_tick_isolated),
    Rule(name="key_trial", tag="physical", apply=_r_key_trial),
    Rule(name="return_count", tag="social", apply=_r_return_brings_count),
    Rule(name="verdict_recognition", tag="social", apply=_r_verdict_recognition),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (forward chaining to fixpoint)."""
    _patch(world)
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
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def _beat(world: World, name: str) -> None:
    """Record that a screenplay beat fired, so the rules can subscribe to it."""
    world.fired.add((name,))


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "young"), "")
    desc = f"young {trait} {hero.type.replace('listener-', '')}".strip()
    world.say(
        f"{hero.id} was a {desc} of the listening kind, and the village said so "
        f"as often as the village said anything at all."
    )


def village_setup(world: World, hero: Entity, village_ents: list[Entity]) -> None:
    """Describe the village in the cautionary-myth register."""
    oven, dog, elder = village_ents[0], village_ents[1], village_ents[2]
    world.say(
        f"The village was small, and the bread {oven.label_word} at the centre of "
        f"it went {oven.sounds.pop() if oven.sounds else 'tick'} in the way that "
        f"old ovens do."
    )
    world.say(
        f"At the edge of the {world.setting.orchard} there stood "
        f"{world.setting.gate}, and the {elder.label_word} of the elders spoke of "
        f"it in careful tones: \"It {world.setting.acoustic_quiet.copy().pop()}, "
        f"and what it counts is a thing no child should know.\""
    )


def dusk_walk(world: World, hero: Entity) -> None:
    """Hero slips past the bread oven to reach the Hollow Gate at dusk."""
    _beat(world, "dusk_walk")
    world.say(
        f"One dusk, when the {world.setting.weather.replace('-', ' ')} was thin "
        f"and the {world.setting.orchard} smelled of warm bark, {hero.id} slipped "
        f"past the bread oven, past the yawning dogs, and walked alone to "
        f"{world.setting.gate}."
    )


def arrive_at_gate(world: World, hero: Entity) -> None:
    """Describe the gate and the key on the beam."""
    _beat(world, "arrive_at_gate")
    world.say(
        f"{world.setting.gate.capitalize()} was just a gate -- two old posts and "
        f"a beam of wood -- but on the beam, in the dust, there was "
        f"{world.key_def.phrase}, and beside the key a single line scratched "
        f'into the wood: "tick is the way, the way is the turn."'
    )


def do_sound_check(world: World, hero: Entity) -> None:
    """The listener stands on the open side, then on the quiet side, and
    compares what is heard.  This is the *mystery-to-solve* core beat."""
    _beat(world, "sound_check")
    # The open side: a recognisable soundscape.
    open_kinds = sorted(world.setting.acoustic_open & ACOUSTIC_KINDS)
    open_list = []
    if "wind" in open_kinds:
        open_list.append("a soft wind")
    if "owl" in open_kinds:
        open_list.append("a sleepy owl")
    if "cricket" in open_kinds:
        open_list.append("a cricket")
    if not open_list:
        open_list.append("a small wind")
    world.say(
        f"{hero.id} listened. From the open air on one side of the gate came "
        f"{', '.join(open_list[:-1] + ['and ' + open_list[-1]] if len(open_list) > 1 else open_list)}, "
        f"and the smell of wet grass."
    )
    # Step to the quiet side: only the tick.
    world.ear_zone = ZONE_QUIET
    world.say(
        f"From the quiet side of the gate came nothing at all -- nothing but "
        f"the tick, tick, tick of the lock, the way a fingernail taps on a "
        f"kettle lid."
    )
    propagate(world, narrate=True)


def do_key_trial(world: World, hero: Entity) -> None:
    """The listener holds the key to the lock; the lock swallows the key and
    converts the tick to a tock -- the count of crossings has just gone up by
    one.  This is the *turn* of the story."""
    _beat(world, "key_trial")
    world.say(
        f"{hero.id} held {world.key_def.phrase} up to the lock. The lock did not "
        f"open. The lock did not close. The lock did something else."
    )
    world.say(
        f"The lock swallowed the key, the way a throat swallows a song, and the "
        f"tick went plip into a new shape: tock."
    )
    world.say('"Took, took, took," said the quiet side of the gate.')
    propagate(world, narrate=True)


def do_return(world: World, hero: Entity) -> None:
    """Wren walks back to the village with the count of crossings in hand."""
    _beat(world, "return_walk")
    world.say(
        f"{hero.id} walked back to the village with one hand on the key-less beam "
        f"and one hand on the gate, and the elders met the young listener at the "
        f"bread oven with their careful tones."
    )
    propagate(world, narrate=True)


def elders_verdict(world: World, hero: Entity, eldest: Entity) -> None:
    """The eldest of the elders says: 'then you are the one we have been
    waiting for.'  This is the *cautionary* moral beat -- a *return to the
    village* that proves the warning was a riddle, not a prohibition."""
    _beat(world, "elders_speak")
    world.say(f'"{world.verdict.line}," the {eldest.label_word} of the elders said.')
    world.say(
        f"The bread oven ticked, the way it always does, and the village did not "
        f"shiver."
    )
    propagate(world, narrate=True)


def new_era(world: World, hero: Entity) -> None:
    """The after-image: the village no longer fears the gate; they count back
    together.  This is the *sound-effects* closer -- the tick becomes a
    *shared* sound rather than a warning."""
    world.say(
        f"From that night, the village no longer feared {world.setting.gate}. "
        f"They listened to it together, and when the {world.setting.weather.replace('-', ' ')} "
        f"was thin, they walked out to it and counted back."
    )


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* myth to tell in this world.
# ---------------------------------------------------------------------------
def listener_sound_check_ok(hero: Entity, key: Key) -> bool:
    """A listener has to be the kind of person who *listens* (i.e. carries
    the 'listener' trait), and the key has to be the kind of object that
    actually changes the lock (i.e. material == 'brass' or material == 'iron')."""
    return "listener" in hero.traits and key.material in {"brass", "iron", "bone"}


def gate_is_real(gate_id: str) -> bool:
    """The gate has to be a *hollow* gate, not a closed one.  'closed' gates
    do not produce a tick and the mystery dissolves."""
    return "closed" not in gate_id


# ---------------------------------------------------------------------------
# Prediction: forward-simulate the world on a clone to check the *caution*
# holds: would the listener, going to the gate, find a tick AND a key?
# ---------------------------------------------------------------------------
def predict_investigation(world: World, hero: Entity) -> dict:
    sim = world.copy()
    dusk_walk(sim, hero)
    arrive_at_gate(sim, hero)
    do_sound_check(sim, hero)
    return {
        "tick_heard": sim.ear().meters["tick"] >= THRESHOLD,
        "open_sounds": sim.ear().meters.get("wind", 0)
                       + sim.ear().meters.get("owl", 0)
                       + sim.ear().meters.get("cricket", 0),
        "key_intact": sim.entities.get("Key") and sim.entities["Key"].meters["used"] < THRESHOLD,
    }


# ---------------------------------------------------------------------------
# The screenplay: a coarse three-act myth shape, driven by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, key: Key, verdict: Verdict,
         hero_name: str, hero_type: str, hero_traits: list[str]) -> World:
    world = World(setting, key, verdict)

    # Set up the listener and the village.
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["young", "listener"] + hero_traits,
    ))
    world.add(Entity(id="Ear", kind="thing", type="ear",
                     label="the ear", sounds={"tick", "tock"}))
    world.add(Entity(id="Village", kind="thing", type="village",
                     label="the village"))
    oven = world.add(Entity(
        id="Oven", kind="thing", type="oven", label="the bread oven",
        sounds={"oven"},
    ))
    world.add(Entity(id="Dog", kind="thing", type="dog", label="the dogs",
                     plural=True))
    eldest = world.add(Entity(
        id="Eldest", kind="character", type="elder-woman",
        label="the eldest", traits=["careful", "old"],
    ))
    world.add(Entity(
        id="Key", kind="thing", type="key", label=key.label,
        phrase=key.phrase, owner=hero.id, sounds={"tick"},
    ))

    # Act 1 -- the cautionary setup: who Wren is, and what the elders warned.
    introduce(world, hero)
    world.para()
    village_setup(world, hero, [oven, world.entities["Dog"], eldest])

    # Act 2 -- the investigation: the slip, the gate, the sound check, the
    # key trial.  The world model forward-chains here.
    world.para()
    dusk_walk(world, hero)
    arrive_at_gate(world, hero)
    do_sound_check(world, hero)
    do_key_trial(world, hero)

    # Act 3 -- the return and the verdict: the village's fear clears; Wren
    # is recognised.  Closing image: the oven ticks, the village does not
    # shiver.
    world.para()
    do_return(world, hero)
    elders_verdict(world, hero, eldest)
    new_era(world, hero)

    # World-knowledge facts recorded for the Q&A generators.
    world.facts.update(
        hero=hero, eldest=eldest, oven=oven, setting=setting,
        key=key, verdict=verdict,
        tick_heard=world.ear().meters["tick"] >= THRESHOLD,
        tock_heard=world.ear().meters["tock"] >= THRESHOLD,
        crossings=world.counts["crossings"],
        returns=world.counts["returns"],
        recognised=world.entities["Wren"].memes["station"] >= THRESHOLD,
        investigated=world.way == "investigate",
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "orchard-edge": Setting(
        id="orchard-edge",
        village="the listening village",
        place="the orchard edge",
        gate="the Hollow Gate",
        bread="the bread oven",
        orchard="orchard",
        weather="thin-wind",
        acoustic_open={"wind", "owl", "cricket"},
        acoustic_quiet={"tick"},
    ),
    "orchard-edge-still": Setting(
        id="orchard-edge-still",
        village="the listening village",
        place="the orchard edge",
        gate="the Hollow Gate",
        bread="the bread oven",
        orchard="orchard",
        weather="still-air",
        acoustic_open={"wind", "cricket"},
        acoustic_quiet={"tick"},
    ),
    "orchard-edge-rain": Setting(
        id="orchard-edge-rain",
        village="the listening village",
        place="the orchard edge",
        gate="the Hollow Gate",
        bread="the bread oven",
        orchard="orchard",
        weather="rain-near",
        acoustic_open={"owl"},
        acoustic_quiet={"tick"},
    ),
}

KEYS = {
    "brass": Key(
        id="brass",
        label="brass key",
        phrase="a small brass key",
        material="brass",
        effect="counts back",
        swallowed_clause="the lock swallowed the key",
    ),
    "iron": Key(
        id="iron",
        label="iron key",
        phrase="a small iron key",
        material="iron",
        effect="counts back",
        swallowed_clause="the lock swallowed the key",
    ),
    "bone": Key(
        id="bone",
        label="bone key",
        phrase="a pale bone key",
        material="bone",
        effect="counts back",
        swallowed_clause="the lock swallowed the key",
    ),
}

VERDICTS = {
    "station": Verdict(
        id="station",
        line="Then you are the one we have been waiting for",
    ),
    "listener": Verdict(
        id="listener",
        line="Then the village has a listener again",
    ),
    "caretaker": Verdict(
        id="caretaker",
        line="Then you are the one who will keep the count",
    ),
}

GIRL_NAMES = ["Wren", "Ivy", "Sage", "Lark", "Hazel", "June", "Fern", "Cora"]
BOY_NAMES = ["Theo", "Asa", "Roe", "Fenn", "Pip", "Owen", "Cael", "Milo"]
TRAITS = ["quiet", "patient", "wary", "soft-voiced", "wide-eyed", "stubborn"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(setting, key, verdict) triples that pass the reasonableness constraint."""
    out: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for kid in KEYS:
            for vid in VERDICTS:
                if gate_is_real(SETTINGS[sid].gate) and KEYS[kid].material != "wood":
                    out.append((sid, kid, vid))
    return out


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    setting: str
    key: str
    verdict: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.  These are answerable WITHOUT
# the story; they explain the *elements* the world is built from.
KNOWLEDGE = {
    "tick": [
        ("What is a tick?",
         "A tick is a small, steady sound -- the kind of sound a clock makes "
         "when the second hand moves one step."),
    ],
    "tock": [
        ("What is a tock?",
         "A tock is the second beat of a tick-tock pair. It is the answer a "
         "tick gives when the lock has counted something."),
    ],
    "lock": [
        ("What is a lock?",
         "A lock is the small metal part of a gate or a door that needs a key "
         "to open it."),
    ],
    "key": [
        ("What is a key?",
         "A key is a small piece of shaped metal that fits into a lock and "
         "turns it open, or in this story, turns it back."),
    ],
    "elders": [
        ("Who are the elders?",
         "The elders are the oldest people of a village, and they are the ones "
         "who remember the warnings and the riddles the village has been told."),
    ],
    "oven": [
        ("Why does a bread oven tick?",
         "A bread oven ticks as it cools, because the warm stones inside shrink "
         "very slowly and make small clicking sounds as they settle."),
    ],
    "gate": [
        ("What is a Hollow Gate?",
         "A Hollow Gate is a gate that is mostly empty inside, so the wind and "
         "the ticks of its lock carry through it like a throat."),
    ],
    "cautionary": [
        ("What is a cautionary tale?",
         "A cautionary tale is a story that warns you about something by "
         "showing what happens when a person tries it anyway."),
    ],
    "mystery": [
        ("What is a mystery?",
         "A mystery is a small puzzle: something is making a sound or a sign, "
         "and you have to find out what it means."),
    ],
}
KNOWLEDGE_ORDER = ["tick", "tock", "lock", "key", "gate", "elders", "oven",
                   "mystery", "cautionary"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, setting, key, verdict = f["hero"], f["setting"], f["key"], f["verdict"]
    return [
        f'Write a short cautionary myth for a 5-to-7-year-old on the theme '
        f'"a child, a gate, a tick that means something" that uses the word '
        f'"tick" as a sound effect.',
        f"Tell a quiet story in a myth register about a young listener named "
        f"{hero.id} who slips past the bread oven to a Hollow Gate at the edge "
        f"of the orchard and has to find out what the tick is counting.",
        f'Write a story that ends with the line "{verdict.line}" and that uses '
        f"the sound effects tick, tock, and the wind, owl, and cricket as "
        f"accompanying beats.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, eldest, setting, key = f["hero"], f["eldest"], f["setting"], f["key"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    trait = next((t for t in hero.traits if t not in {"young", "listener"}), hero.type)
    return [
        QAItem(
            question=(
                f"Who is the listener in the cautionary story about "
                f"{setting.gate} at the edge of {setting.orchard}?"
            ),
            answer=(
                f"It is a {trait} young {hero.type.replace('listener-', '')} named "
                f"{hero.id}, the kind of child the village calls a listener. "
                f"{sub.capitalize()} slips out at dusk past the bread oven and "
                f"the yawning dogs."
            ),
        ),
        QAItem(
            question=(
                f"What sound did {hero.id} hear when {sub} stepped to the quiet "
                f"side of {setting.gate}?"
            ),
            answer=(
                f"{sub.capitalize()} heard nothing but the tick of the lock, the "
                f"way a fingernail taps on a kettle lid. The wind, the sleepy "
                f"owl, and the cricket all stayed on the open side."
            ),
        ),
        QAItem(
            question=(
                f"What did the {key.label} do when {hero.id} held it to the "
                f"lock at {setting.gate}?"
            ),
            answer=(
                f"The lock did not open and did not close. The lock swallowed "
                f"the key, the way a throat swallows a song, and the tick went "
                f"plip into a new shape: tock. The count of crossings went up "
                f"by one."
            ),
        ),
        QAItem(
            question=(
                f"What did the {eldest.label_word} of the elders say to "
                f"{hero.id} when {sub} came back to {setting.village} with the "
                f"count of crossings?"
            ),
            answer=(
                f'The {eldest.label_word} said, "{f["verdict"].line}." '
                f"From that night, the village no longer feared the gate and "
                f"walked out to count back together."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = {"tick", "tock", "lock", "key", "gate", "elders", "oven",
            "mystery", "cautionary"}
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
        if e.sounds:
            bits.append(f"sounds={sorted(e.sounds)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:14}) {' '.join(bits)}")
    lines.append(f"  ear_zone     : {world.ear_zone}")
    lines.append(f"  counts       : {world.counts}")
    lines.append(f"  fired beats  : {sorted({n for (n, *_) in world.fired if isinstance(n, str)})}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        setting="orchard-edge",
        key="brass",
        verdict="station",
        name="Wren",
        gender="girl",
        trait="patient",
    ),
    StoryParams(
        setting="orchard-edge-still",
        key="iron",
        verdict="listener",
        name="Ivy",
        gender="girl",
        trait="soft-voiced",
    ),
    StoryParams(
        setting="orchard-edge-rain",
        key="bone",
        verdict="caretaker",
        name="Theo",
        gender="boy",
        trait="wary",
    ),
]


def explain_rejection(setting: Setting, key: Key) -> str:
    if not gate_is_real(setting.gate):
        return (f"(No story: {setting.gate} is a closed gate and the lock has no "
                f"tick for {key.label} to be counted by. Pick a Hollow Gate.)")
    if key.material == "wood":
        return (f"(No story: a wooden key would not turn the lock at "
                f"{setting.gate}. Pick a brass, iron, or bone key.)")
    return "(No story: the listener's qualities do not match the gate's riddle.)"


def explain_gender(name: str, gender: str) -> str:
    return (f"(No story: {name!r} is not a {gender}'s name in this village; "
            f"try a different name or --gender boy/girl.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (listener_sound_check_ok / gate_is_real / valid_combos).  The rules are
# inline below; the facts are generated from the registries above so the two
# cannot drift.  Uses the shared `asp` helper + clingo, imported lazily so the
# prose engine runs without them.  See `python <this file>.py --verify`.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% The listener is a "real" listener iff the listener trait is present.
is_listener(L) :- listener_trait(L, listener).

% The gate produces a tick iff it is hollow (not "closed").
gate_has_tick(G) :- gate_kind(G, hollow).
gate_has_tick(G) :- gate_kind(G, hollow_open).
gate_has_tick(G) :- gate_kind(G, hollow_rain).

% A key can turn the lock iff its material is one we accept.
key_turns(K) :- key_material(K, brass).
key_turns(K) :- key_material(K, iron).
key_turns(K) :- key_material(K, bone).

% A story is valid iff the listener is a real listener, the gate has a tick,
% and the key can turn the lock.
valid_story(S, G, K, V) :-
    setting(S), gate_of(S, G), key_of(S, K), verdict_of(S, V),
    gate_has_tick(G), key_turns(K), listener_for(S, listener).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        # Translate the placeholder gate to a *kind* the rules can reason over.
        kind = "hollow"
        if s.id.endswith("-rain"):
            kind = "hollow_rain"
        elif s.id.endswith("-still"):
            kind = "hollow_open"
        lines.append(asp.fact("gate_of", sid, s.gate))
        lines.append(asp.fact("gate_kind", s.gate, kind))
        lines.append(asp.fact("key_of", sid, list(KEYS.keys())[0]))    # default key per setting
        lines.append(asp.fact("verdict_of", sid, list(VERDICTS.keys())[0]))
        lines.append(asp.fact("listener_for", sid, "listener"))
        for k in s.acoustic_open:
            lines.append(asp.fact("acoustic_open", sid, k))
        for k in s.acoustic_quiet:
            lines.append(asp.fact("acoustic_quiet", sid, k))
    for kid, k in KEYS.items():
        lines.append(asp.fact("key", kid))
        lines.append(asp.fact("key_material", kid, k.material))
    for vid in VERDICTS:
        lines.append(asp.fact("verdict", vid))
    # The (single) listener trait recognised by the rule.
    lines.append(asp.fact("listener_trait", "listener", "listener"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    """(setting, gate, key, verdict) -- the ASP-twin valid set."""
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
    import asp
    # The Python valid_combos is keyed (setting, key, verdict); the ASP twin
    # returns (setting, gate, key, verdict).  We compare on (setting, key, verdict).
    python_set = set(valid_combos())
    clingo_set = {(s, k, v) for (s, _g, k, v) in asp_valid_stories()}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
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
        description="Story world sketch: the tick of the Hollow Gate. "
                    "Unspecified choices are picked at random (seeded).")
    # A small, debuggable set of pins; any omitted choice is randomized.
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--key", choices=KEYS)
    ap.add_argument("--verdict", choices=VERDICTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.setting and args.key:
        setting, key = SETTINGS[args.setting], KEYS[args.key]
        if not (gate_is_real(setting.gate) and key.material != "wood"):
            raise StoryError(explain_rejection(setting, key))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.key is None or c[1] == args.key)
              and (args.verdict is None or c[2] == args.verdict)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, key_id, verdict_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        key=key_id,
        verdict=verdict_id,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    hero_type = "listener-girl" if params.gender == "girl" else "listener-boy"
    world = tell(SETTINGS[params.setting], KEYS[params.key], VERDICTS[params.verdict],
                 params.name, hero_type, [params.trait])
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
        stories = asp_valid_stories()
        print(f"{len(stories)} valid (setting, gate, key, verdict) combos:\n")
        for s, g, k, v in stories:
            print(f"  setting={s:22}  gate={g:14}  key={k:5}  verdict={v}")
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
            header = f"### {p.name}: tick at {p.setting} (key: {p.key})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
