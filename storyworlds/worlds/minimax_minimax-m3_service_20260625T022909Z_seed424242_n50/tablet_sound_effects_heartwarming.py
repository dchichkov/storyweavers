#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/tablet_sound_effects_heartwarming.py
============================================================================================================

A standalone *story world* sketch for "The Tablet and the Sound Effects" tale and
close, *constraint-checked* variations of it.  Heartwarming style: every beat
has to land softly, with a child-safe ending image.

Initial story (used to build a world model):
---
Once upon a time, there was a little girl named Maya who loved watching her
tablet. The tablet could play all kinds of sounds. When Maya tapped a picture
of rain, the tablet made a soft pitter-patter sound. When she tapped a picture
of a fire, it made a warm crackle. When she tapped a picture of the wind, it
made a gentle whoosh.

One rainy afternoon, Maya's big brother Theo came to sit beside her. "Can I
make a sound too?" he asked. Maya nodded and shared the tablet.

Maya wanted to play a loud thunder sound, but the tablet said, "Too loud for
inside." So Maya picked the rain sound instead. The soft pitter-patter filled
the room. Theo's shoulders relaxed and he smiled.

Then their mom came in with a blanket. "I love this sound," she said. She sat
between the children, wrapped the blanket around them, and the three of them
listened together while the rain outside kept the tablet company.

Causal state updates:
---
    do tap-sound effect          -> child.delight += 1
                                    sibling.connection += 1
    picked-too-loud sound       -> child.shame += 1, tablet.guardian_care -= 1
    tablet rejects too-loud tap  -> child.calm += 1, child.coping += 1
    parent wraps blanket         -> child.warmth += 1, sibling.warmth += 1
                                    child.attachment += 1

Scripted social/emotional beats:
---
    shared tablet               -> sibling.bond += 1
    sibling nervous about sound  -> sibling.settled += 1 once the soft sound plays
    parent joins softly         -> home.coziness += 1
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

SOUND_KINDS = {"soft", "loud"}

SOUND_REGIONS = {"ears", "room"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, tablet, mom, brother ...
    label: str = ""                # short reference, e.g. "tablet", "the blanket"
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    plays_for: Optional[str] = None   # whose experience this object supports
    loud: bool = False               # sound effect loudness flag (true = too loud)
    cozy: bool = False               # the blanket, anything that wraps
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    # Two numeric dimensions, treated uniformly.
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def them(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the living room"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Sound:
    """A single sound effect available on the tablet."""
    id: str
    name: str          # "soft rain", "warm fire", "loud thunder"
    onomatopoeia: str  # "pitter-patter", "crackle", "boom"
    kind: str          # "soft" | "loud"
    mood: str          # "cozy" | "big" | "calm"
    line: str          # one-line description of what the tablet shows
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    """A relative or sibling who shares the tablet moment."""
    id: str
    label: str
    type: str          # "brother" | "sister" | "mother" | "father"
    line: str          # how they ask to join


@dataclass
class Wrap:
    """A cozy wrap offered as the resolution -- a blanket or a hug shape."""
    id: str
    label: str
    covers: set[str]    # who it warms
    prep: str           # body of the offer
    tail: str           # closing clause
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
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def owned_by(self, owner_id: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == owner_id]

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


def _r_relax(world: World) -> list[str]:
    """A soft sound effect played for a nervous sibling -> sibling settles."""
    out: list[str] = []
    for sibling in world.characters():
        if sibling.id == world.facts.get("hero_id"):
            continue
        if sibling.memes["nervous"] < THRESHOLD:
            continue
        soft_active = any(
            s.meters["played"] >= THRESHOLD and not s.loud
            for s in world.owned_by(world.facts.get("hero_id", ""))
            if s.kind == "sound"
        )
        if not soft_active:
            continue
        sig = ("relax", sibling.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        sibling.memes["settled"] += 1
        out.append(f"{sibling.label}'s shoulders relaxed and {sibling.pronoun()} smiled.")
    return out


def _r_attach(world: World) -> list[str]:
    """When caregiver wraps the blanket -> child + sibling warmth + child.attachment."""
    out: list[str] = []
    blanket = next((e for e in world.entities.values()
                    if e.kind == "thing" and e.cozy), None)
    if not blanket or blanket.meters["shared"] < THRESHOLD:
        return out
    caregiver = world.get(blanket.caregiver) if blanket.caregiver else None
    if caregiver is None:
        return out
    for actor in world.characters():
        if actor.id == caregiver.id:
            continue
        sig = ("warmth", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["warmth"] += 1
        actor.memes["attachment"] += 1
        out.append(
            f"{actor.id} felt warm all the way down to {actor.pronoun('possessive')} toes."
        )
    return out


def _r_sibling_bond(world: World) -> list[str]:
    """Sibling asks to make a sound and the child shares -> bond up."""
    out: list[str] = []
    sibling = world.facts.get("sibling")
    if not sibling:
        return out
    hero = world.facts.get("hero")
    if not hero:
        return out
    if sibling.memes["asked"] < THRESHOLD or hero.memes["shared"] < THRESHOLD:
        return out
    sig = ("bond", sibling.id)
    if sig in world.fired:
        continue_str = ""  # placeholder for type-checker
        _ = continue_str
        return out
    world.fired.add(sig)
    sibling.memes["bond"] += 1
    return out


def _r_attach_fix():
    return _r_attach


def _r_relax_fix():
    return _r_relax


# rewrite _r_sibling_bond without the dead `continue_str` placeholder
def _r_sibling_bond(world: World) -> list[str]:
    out: list[str] = []
    sibling = world.facts.get("sibling")
    if not sibling:
        return out
    hero = world.facts.get("hero")
    if not hero:
        return out
    if sibling.memes["asked"] < THRESHOLD or hero.memes["shared"] < THRESHOLD:
        return out
    sig = ("bond", sibling.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sibling.memes["bond"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="relax", tag="social", apply=_r_relax),
    Rule(name="attach", tag="social", apply=_r_attach_fix()),
    Rule(name="sibling_bond", tag="social", apply=_r_sibling_bond),
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
# Constraints: a soft sound is always available; a loud sound must be refused.
# ---------------------------------------------------------------------------
def has_soft_match(sounds: list[Sound]) -> Optional[Sound]:
    """The first soft sound in the catalog -- always present, by construction."""
    for s in sounds:
        if s.kind == "soft":
            return s
    return None


def is_loud(sound: Sound) -> bool:
    return sound.kind == "loud"


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def sound_line(sound: Sound) -> str:
    return f"the tablet showed {sound.line} and made a soft {sound.onomatopoeia} sound"


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who noticed every good sound.")


def tablet_intro(world: World, hero: Entity, tablet: Entity) -> None:
    world.say(
        f"{hero.id} had a small {tablet.label} that could play all kinds of sounds."
    )


def loves_tablet(world: World, hero: Entity, tablet: Entity) -> None:
    hero.memes["love_tablet"] += 1
    tablet.plays_for = hero.id
    world.say(
        f"{hero.pronoun().capitalize()} loved watching {hero.pronoun('possessive')} "
        f"{tablet.label} and listening to what each picture could do."
    )


def explore_sounds(world: World, hero: Entity, tablet: Entity,
                   catalog: list[Sound]) -> None:
    """Show 1-2 soft sounds as the catalog the child already loves."""
    samples = [s for s in catalog if s.kind == "soft"][:2]
    if not samples:
        return
    bits = [sound_line(s) for s in samples]
    if len(bits) == 1:
        detail = bits[0]
    else:
        detail = bits[0] + ", and when " + hero.pronoun("subject") + " tapped another picture, " + bits[1]
    world.say(f"When {hero.pronoun('subject')} tapped a picture, {detail}.")


def companion_arrives(world: World, hero: Entity, sibling: Entity,
                      companion_def: Companion) -> None:
    sibling.kind = "character"
    sibling.type = companion_def.type
    sibling.label = companion_def.label
    sibling.memes["nervous"] += 1
    sibling.memes["asked"] += 1
    world.say(
        f"One {world.weather or 'quiet'} afternoon, {sibling.label} came to sit beside "
        f"{hero.id}. \"{companion_def.line}\" {sibling.pronoun('subject')} asked."
    )


def share_tablet(world: World, hero: Entity, sibling: Entity) -> None:
    hero.memes["shared"] += 1
    sibling.memes["welcomed"] += 1
    world.say(f"{hero.id} nodded and tilted the tablet so {sibling.id} could see.")


def pick_loud(world: World, hero: Entity, tablet: Entity, sound: Sound) -> None:
    """The child tries a loud sound -- the tablet gently says no."""
    sound.loud = True
    sound.meters["attempted"] += 1
    hero.memes["shame"] += 1
    tablet.meters["guardian_care"] = max(0.0, tablet.meters["guardian_care"] - 1)
    world.say(
        f"{hero.id} tapped the picture of {sound.line}, but the {tablet.label} "
        f"shook its little picture softly. \"{sound.name} is too loud for inside,\" "
        f"it said."
    )


def pick_soft(world: World, hero: Entity, tablet: Entity, sound: Sound) -> None:
    sound.meters["played"] += 1
    hero.memes["calm"] += 1
    hero.memes["coping"] += 1
    tablet.meters["guardian_care"] += 1
    world.say(
        f"So {hero.pronoun('subject')} tapped the picture of {sound.line} instead, "
        f"and a soft {sound.onomatopoeia} filled the room."
    )


def caregiver_wraps(world: World, hero: Entity, sibling: Entity,
                    tablet: Entity, caregiver: Entity, wrap_def: Wrap) -> Entity:
    caregiver.kind = "character"
    caregiver.label = caregiver.label or "the parent"
    blanket = world.add(Entity(
        id=wrap_def.id, kind="thing", type="blanket",
        label=wrap_def.label, owner=hero.id,
        caregiver=caregiver.id, cozy=True,
        covers=set(wrap_def.covers), plural=wrap_def.plural,
    ))
    blanket.meters["shared"] += 1
    caregiver.memes["coziness"] += 1
    world.facts["wrap"] = wrap_def
    world.say(
        f"Then {caregiver.id} came in with {wrap_def.label}. "
        f"\"I love this sound,\" {caregiver.pronoun('subject')} said."
    )
    world.say(
        f"{caregiver.pronoun('subject').capitalize()} sat between the children, "
        f"{wrap_def.prep}, and the three of them listened together."
    )
    return blanket


def settle_together(world: World, hero: Entity, sibling: Entity,
                    tablet: Entity, sound: Sound, caregiver: Entity) -> None:
    world.say(
        f"The soft {sound.onomatopoeia} kept going, and so did the rain outside, "
        f"and nobody had to shout to be heard."
    )


# ---------------------------------------------------------------------------
# The screenplay: three-act shape, driven by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, catalog: list[Sound], wrap_def: Wrap,
         sibling_def: Companion, hero_name: str = "Maya",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         sibling_name: str = "Theo",
         caregiver_name: str = "Mom",
         caregiver_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "rainy"

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["thoughtful", "gentle"]),
    ))
    tablet = world.add(Entity(
        id="tablet", kind="thing", type="tablet", label="tablet",
        owner=hero.id,
    ))
    sibling = world.add(Entity(id=sibling_name, kind="character", type=sibling_def.type,
                               label=sibling_name))
    caregiver = world.add(Entity(id=caregiver_name, kind="character",
                                 type=caregiver_type, label=caregiver_name))

    # Wrap the soft sounds as objects on the tablet so causal rules can see them.
    for s in catalog:
        world.add(Entity(
            id=f"snd_{s.id}", kind="thing", type="sound", label=s.name,
            owner=hero.id, loud=(s.kind == "loud"),
        ))

    # Act 1 -- the child, the tablet, the sounds it knows.
    introduce(world, hero)
    tablet_intro(world, hero, tablet)
    loves_tablet(world, hero, tablet)
    explore_sounds(world, hero, tablet, catalog)

    # Act 2 -- sibling arrives, child tries a loud sound, tablet refuses, picks soft.
    world.para()
    companion_arrives(world, hero, sibling, sibling_def)
    share_tablet(world, hero, sibling)
    loud = next((s for s in catalog if s.kind == "loud"), None)
    soft = has_soft_match(catalog)
    if loud is None or soft is None:
        raise StoryError("Catalog must contain at least one loud and one soft sound.")
    pick_loud(world, hero, tablet, loud)
    pick_soft(world, hero, tablet, soft)
    # Let the relax rule fire so the sibling visibly settles.
    propagate(world, narrate=False)
    propagate(world, narrate=True)

    # Act 3 -- caregiver wraps them and they settle.
    world.para()
    blanket = caregiver_wraps(world, hero, sibling, tablet, caregiver, wrap_def)
    settle_together(world, hero, sibling, tablet, soft, caregiver)
    propagate(world, narrate=False)
    propagate(world, narrate=True)

    world.facts.update(
        hero=hero, tablet=tablet, sibling=sibling, caregiver=caregiver,
        catalog=catalog, wrap=wrap_def, wrap_obj=blanket,
        loud=loud, soft=soft,
        sibling_def=sibling_def,
        conflict=sibling.memes["nervous"] >= THRESHOLD,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "living_room": Setting(place="the living room", indoor=True, affords={"tablet"}),
    "bedroom": Setting(place="the bedroom", indoor=True, affords={"tablet"}),
    "kitchen": Setting(place="the kitchen nook", indoor=True, affords={"tablet"}),
}

SOUNDS = {
    "rain": Sound(
        id="rain", name="soft rain", onomatopoeia="pitter-patter",
        kind="soft", mood="cozy",
        line="rain falling on a window",
        keyword="rain",
        tags={"rain", "cozy", "soft"},
    ),
    "fire": Sound(
        id="fire", name="warm fire", onomatopoeia="crackle",
        kind="soft", mood="cozy",
        line="a fire in a small fireplace",
        keyword="fire",
        tags={"fire", "cozy", "soft"},
    ),
    "wind": Sound(
        id="wind", name="gentle wind", onomatopoeia="whoosh",
        kind="soft", mood="calm",
        line="wind through tall grass",
        keyword="wind",
        tags={"wind", "calm", "soft"},
    ),
    "ocean": Sound(
        id="ocean", name="soft waves", onomatopoeia="shhh-shhh",
        kind="soft", mood="calm",
        line="small waves on a sandy shore",
        keyword="waves",
        tags={"ocean", "calm", "soft"},
    ),
    "thunder": Sound(
        id="thunder", name="loud thunder", onomatopoeia="BOOM",
        kind="loud", mood="big",
        line="a great thunder cloud",
        keyword="thunder",
        tags={"thunder", "big", "loud"},
    ),
    "horn": Sound(
        id="horn", name="loud horn", onomatopoeia="BWAH",
        kind="loud", mood="big",
        line="a big parade horn",
        keyword="horn",
        tags={"horn", "big", "loud"},
    ),
}

COMPANIONS = {
    "brother": Companion(
        id="brother", label="the big brother", type="brother",
        line="Can I make a sound too?",
    ),
    "sister": Companion(
        id="sister", label="the big sister", type="sister",
        line="Will you share the sound with me?",
    ),
    "mother": Companion(
        id="mother", label="Mom", type="mother",
        line="What does the tablet say today?",
    ),
    "father": Companion(
        id="father", label="Dad", type="father",
        line="Can I listen with you for a minute?",
    ),
}

WRAPS = [
    Wrap(
        id="blanket", label="a soft blanket",
        covers={"child", "sibling"},
        prep="wrapped it around both children",
        tail="the blanket tucked them in",
    ),
    Wrap(
        id="quilt", label="a warm quilt",
        covers={"child", "sibling"},
        prep="spread the quilt across their laps",
        tail="the quilt warmed their laps",
    ),
]

GIRL_NAMES = ["Maya", "Lily", "Zoe", "Ava", "Ella", "Nora", "Mia", "Anna", "Rose", "Lucy"]
BOY_NAMES = ["Theo", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Owen"]
SIBLING_NAMES_BOY = ["Theo", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah"]
SIBLING_NAMES_GIRL = ["Lily", "Zoe", "Ava", "Ella", "Nora", "Mia", "Anna"]
TRAITS = ["gentle", "thoughtful", "patient", "kind", "soft-spoken", "loving"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(soft_sound, companion, wrap) triples that pass the constraints."""
    combos = []
    for soft_id, s in SOUNDS.items():
        if s.kind != "soft":
            continue
        for comp_id in COMPANIONS:
            for wrap in WRAPS:
                combos.append((soft_id, comp_id, wrap.id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    soft_sound: str
    loud_sound: str
    companion: str
    wrap: str
    name: str
    gender: str
    sibling: str
    caregiver: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "rain": [("What does rain sound like?",
             "Rain sounds like a soft pitter-patter, like tiny fingertips "
             "tapping on a window.")],
    "fire": [("What does a small fire sound like?",
              "A small fire makes a warm crackle, like kindling whispering.")],
    "wind": [("What does a gentle wind sound like?",
              "A gentle wind makes a soft whoosh, like breath slipping past leaves.")],
    "ocean": [("What do small waves sound like?",
               "Small waves make a soft shhh-shhh, like a quiet song on the sand.")],
    "thunder": [("Why is thunder so loud?",
                 "Thunder is a big sound made by warm air and cold air bumping "
                 "together high up in the sky.")],
    "horn": [("What is a parade horn for?",
              "A parade horn is a big noisy instrument played to call people "
              "to come and watch.")],
    "tablet": [("What is a tablet?",
                "A tablet is a small flat screen you can tap with your finger "
                "to watch pictures, hear sounds, and play gentle games.")],
    "soft": [("Why are soft sounds nice to listen to?",
              "Soft sounds are gentle on your ears and help a room feel calm "
              "and warm.")],
    "loud": [("Why can loud sounds feel too much?",
              "Loud sounds can hurt tender ears, and they can make a small "
              "room feel too busy.")],
    "blanket": [("Why does a blanket feel warm?",
                 "A blanket holds the heat from your body close to your skin, "
                 "so the chill of the room can't reach you.")],
    "quilt": [("What is a quilt?",
               "A quilt is a blanket made by stitching soft pieces of cloth "
               "together, often in pretty patterns.")],
}
KNOWLEDGE_ORDER = ["rain", "fire", "wind", "ocean", "thunder", "horn",
                   "tablet", "soft", "loud", "blanket", "quilt"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, tablet, sibling = f["hero"], f["tablet"], f["sibling"]
    soft = f["soft"]
    kw = soft.keyword
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a small sound, '
        f'a shared moment" that includes the word "{kw}".',
        f"Tell a gentle story where {hero.id} loves the sounds on "
        f"{hero.pronoun('possessive')} {tablet.label}, shares them with "
        f"{sibling.label}, and ends with a caregiver wrapping them up warm.",
        f'Write a simple story that uses the noun "{kw}" and ends with a child, '
        f"a sibling, and a parent listening to the same soft sound together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, tablet, sibling, caregiver = (
        f["hero"], f["tablet"], f["sibling"], f["caregiver"]
    )
    soft, loud, wrap_def = f["soft"], f["loud"], f["wrap"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    place = world.setting.place

    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} shares the {tablet.label} "
                f"at {place}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} who "
                f"loved listening to the {tablet.label}. {sibling.label} came to "
                f"sit beside {obj}, and {caregiver.id} joined them softly at the end."
            ),
        ),
        QAItem(
            question=(
                f"What sounds did the {tablet.label} play for {trait} {hero.id} "
                f"before {sibling.label} sat down at {place}?"
            ),
            answer=(
                f"The {tablet.label} could play a {SOUNDS['rain'].name} sound "
                f"and a {SOUNDS['fire'].name} sound. {hero.id} loved tapping each "
                f"picture to hear what it would do."
            ),
        ),
        QAItem(
            question=(
                f"Which picture did {hero.id} tap first that the {tablet.label} "
                f"would not play inside the {place}?"
            ),
            answer=(
                f"{hero.id} tapped the picture of {loud.line}, but the "
                f"{tablet.label} shook its little picture softly and said "
                f"\"{loud.name} is too loud for inside.\""
            ),
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=(
                f"Which soft sound did {trait} {hero.id} pick after the "
                f"{tablet.label} said the {loud.name} was too loud?"
            ),
            answer=(
                f"{sub.capitalize()} picked the picture of {soft.line} instead, "
                f"and a soft {soft.onomatopoeia} filled the {place}. "
                f"{sibling.label}'s shoulders relaxed and {sibling.pronoun()} smiled."
            ),
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"How did {wrap_def.label} help {trait} {hero.id} and "
                f"{sibling.label} feel cozy while the {soft.onomatopoeia} "
                f"played at {place}?"
            ),
            answer=(
                f"{caregiver.id} came in with {wrap_def.label} and "
                f"{wrap_def.prep}. The three of them listened to the soft "
                f"{soft.onomatopoeia} together, and nobody had to shout to be heard."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel at the end of the afternoon "
                f"with the {tablet.label} and the {wrap_def.label}?"
            ),
            answer=(
                f"{hero.id} felt warm, calm, and close to {caregiver.id} and "
                f"{sibling.label}. The soft {soft.onomatopoeia} kept going, and so "
                f"did the rain outside, and the room felt like a small hug."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["soft"].tags) | set(f["loud"].tags) | {"tablet"}
    if f.get("wrap"):
        tags.add(f["wrap"].id)
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
        if e.cozy:
            bits.append(f"cozy covers={sorted(e.covers)}")
        if e.loud:
            bits.append("loud=true")
        lines.append(f"  {e.id:14} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="living_room",
        soft_sound="rain",
        loud_sound="thunder",
        companion="brother",
        wrap="blanket",
        name="Maya",
        gender="girl",
        sibling="Theo",
        caregiver="Mom",
        trait="gentle",
    ),
    StoryParams(
        place="bedroom",
        soft_sound="fire",
        loud_sound="horn",
        companion="sister",
        wrap="quilt",
        name="Lily",
        gender="girl",
        sibling="Zoe",
        caregiver="Mom",
        trait="thoughtful",
    ),
    StoryParams(
        place="kitchen",
        soft_sound="wind",
        loud_sound="thunder",
        companion="father",
        wrap="blanket",
        name="Ben",
        gender="boy",
        sibling="Dad",
        caregiver="Mom",
        trait="patient",
    ),
    StoryParams(
        place="living_room",
        soft_sound="ocean",
        loud_sound="horn",
        companion="mother",
        wrap="quilt",
        name="Ava",
        gender="girl",
        sibling="Mom",
        caregiver="Dad",
        trait="soft-spoken",
    ),
    StoryParams(
        place="bedroom",
        soft_sound="rain",
        loud_sound="horn",
        companion="brother",
        wrap="blanket",
        name="Theo",
        gender="boy",
        sibling="Ben",
        caregiver="Mom",
        trait="kind",
    ),
]


def explain_rejection(soft_id: str, loud_id: str) -> str:
    s = SOUNDS.get(soft_id)
    l = SOUNDS.get(loud_id)
    if s is None or s.kind != "soft":
        return (f"(No story: a heartwarming tablet moment needs a soft sound to "
                f"settle on, but {soft_id} is not in the soft catalog. Try one "
                f"of: {', '.join(k for k, v in SOUNDS.items() if v.kind == 'soft')}.)")
    if l is None or l.kind != "loud":
        return (f"(No story: the gentle refusal beat only works when the child "
                f"first asks for a loud sound. {loud_id} is not loud; try one "
                f"of: {', '.join(k for k, v in SOUNDS.items() if v.kind == 'loud')}.)")
    return "(No story: the chosen catalog does not satisfy the soft/loud pairing.)"


def explain_companion(comp_id: str) -> str:
    if comp_id not in COMPANIONS:
        return (f"(No story: companion {comp_id!r} is unknown; try one of: "
                f"{', '.join(COMPANIONS)}.)")
    return ""


def explain_wrap(wrap_id: str) -> str:
    if not any(w.id == wrap_id for w in WRAPS):
        return (f"(No story: wrap {wrap_id!r} is unknown; try one of: "
                f"{', '.join(w.id for w in WRAPS)}.)")
    return ""


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- declarative twin of the soft+loud catalog rule.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A heartwarming tablet story needs at least one soft sound AND one loud sound.
has_soft(S) :- sound(S), kind(S, soft).
has_loud(S) :- sound(S), kind(S, loud).

% The chosen soft sound and the chosen loud sound must both exist in the catalog.
valid_soft(Soft) :- has_soft(Soft).
valid_loud(Loud) :- has_loud(Loud).

% The wrap must be a known wrap that covers both child and sibling.
valid_wrap(W) :- wrap(W), covers(W, child), covers(W, sibling).

% Companions can be any of the registered kinds.
valid_companion(C) :- companion(C).

% A complete story needs all four pieces, and they must be compatible.
valid(Soft, Loud, W, C) :- valid_soft(Soft), valid_loud(Loud),
                            valid_wrap(W), valid_companion(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for snid, s in SOUNDS.items():
        lines.append(asp.fact("sound", snid))
        lines.append(asp.fact("kind", snid, s.kind))
        lines.append(asp.fact("mood", snid, s.mood))
    for cid in COMPANIONS:
        lines.append(asp.fact("companion", cid))
    for w in WRAPS:
        lines.append(asp.fact("wrap", w.id))
        for r in sorted(w.covers):
            lines.append(asp.fact("covers", w.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos() shape."""
    import asp
    clingo_set = set(asp_valid_stories())
    # Python valid_combos yields (soft_sound, companion, wrap); ASP yields
    # (soft, loud, wrap, companion).  Compare after projecting to the same shape.
    python_set = set(valid_combos())
    clingo_projected = {(soft, comp, wrap)
                       for (soft, _loud, wrap, comp) in clingo_set}
    if clingo_projected == python_set:
        print(f"OK: clingo gate matches valid_combos() "
              f"({len(clingo_projected)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_projected - python_set:
        print("  only in clingo:", sorted(clingo_projected - python_set))
    if python_set - clingo_projected:
        print("  only in python:", sorted(python_set - clingo_projected))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tablet, soft sounds, a shared blanket. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--soft-sound", choices=SOUNDS,
                    help="the soft sound the child ends up playing")
    ap.add_argument("--loud-sound", choices=SOUNDS,
                    help="the loud sound the tablet gently refuses")
    ap.add_argument("--companion", choices=COMPANIONS,
                    help="who comes to sit beside the child")
    ap.add_argument("--wrap", choices=[w.id for w in WRAPS],
                    help="the cozy wrap that ends the story")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    """Fill in any unspecified choices at random, keeping the combo reasonable."""
    soft = SOUNDS.get(args.soft_sound) if args.soft_sound else None
    loud = SOUNDS.get(args.loud_sound) if args.loud_sound else None
    if args.soft_sound and (soft is None or soft.kind != "soft"):
        raise StoryError(explain_rejection(args.soft_sound, args.loud_sound or ""))
    if args.loud_sound and (loud is None or loud.kind != "loud"):
        raise StoryError(explain_rejection(args.soft_sound or "", args.loud_sound))
    if args.companion and args.companion not in COMPANIONS:
        raise StoryError(explain_companion(args.companion))
    if args.wrap:
        msg = explain_wrap(args.wrap)
        if msg:
            raise StoryError(msg)

    soft_id = args.soft_sound or rng.choice([k for k, v in SOUNDS.items() if v.kind == "soft"])
    loud_id = args.loud_sound or rng.choice([k for k, v in SOUNDS.items() if v.kind == "loud"])
    if SOUNDS[soft_id].kind != "soft" or SOUNDS[loud_id].kind != "loud":
        raise StoryError(explain_rejection(soft_id, loud_id))

    comp_id = args.companion or rng.choice(list(COMPANIONS))
    wrap_def = next(w for w in WRAPS if w.id == (args.wrap or rng.choice([w.id for w in WRAPS])))

    gender = args.gender or rng.choice(["girl", "boy"])
    if gender == "girl":
        name = args.name or rng.choice(GIRL_NAMES)
        sibling = rng.choice(SIBLING_NAMES_BOY)
    else:
        name = args.name or rng.choice(BOY_NAMES)
        sibling = rng.choice(SIBLING_NAMES_GIRL)
    if comp_id in ("mother", "father"):
        caregiver_type = comp_id
        sibling = ""
    else:
        caregiver_type = rng.choice(["mother", "father"])
    caregiver = "Mom" if caregiver_type == "mother" else "Dad"
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        soft_sound=soft_id,
        loud_sound=loud_id,
        companion=comp_id,
        wrap=wrap_def.id,
        name=name,
        gender=gender,
        sibling=sibling,
        caregiver=caregiver,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(
        SETTINGS[params.place],
        [SOUNDS[params.soft_sound], SOUNDS[params.loud_sound]],
        next(w for w in WRAPS if w.id == params.wrap),
        COMPANIONS[params.companion],
        hero_name=params.name,
        hero_type=params.gender,
        hero_traits=[params.trait, "patient"],
        sibling_name=params.sibling or "Theo",
        caregiver_name=params.caregiver,
        caregiver_type="mother" if params.caregiver == "Mom" else "father",
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (soft, loud, wrap, companion) stories:\n")
        for soft, loud, wrap, comp in stories:
            print(f"  soft={soft:6} loud={loud:7} wrap={wrap:8} companion={comp}")
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
            header = (f"### {p.name}: {p.soft_sound} vs {p.loud_sound} "
                      f"at {p.place} (companion: {p.companion}, wrap: {p.wrap})")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
