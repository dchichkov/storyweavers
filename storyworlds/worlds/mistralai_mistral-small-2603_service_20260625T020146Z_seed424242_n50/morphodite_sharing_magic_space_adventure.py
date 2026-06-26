#!/usr/bin/env python3
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
from results import QAItem, StoryError, StorySample
from asp import fact, term, solve, one_model, atoms

THRESHOLD = 0.8

METER_KINDS = {
    "magic_reserve",
    "harmony",
    "conflict",
    "curiosity",
    "trust_increase",
    "shared_count",
}

MEME_KINDS = {
    "trust",
    "connection",
    "fear",
    "joy",
    "curiosity",
    "understanding",
}

CREW_ROLES = {"astrogator", "engineer", "botanist", "commander", "medic"}

@dataclass
class Entity:
    id: str
    kind: str = "being"
    type: str = ""
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
        female = {"botanist", "medic"}
        male = {"astrogator", "engineer", "commander"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

@dataclass
class Place:
    id: str
    phrase: str
    description: str
    magic_friendly: bool = False

@dataclass
class Activity:
    id: str
    verb: str = ""
    gerund: str = ""
    demand: str = ""
    mess: str = ""
    ritual: str = ""
    zone: set[str] = field(default_factory=set)
    power_cost: float = 0.0
    tag: str = ""

@dataclass
class Magic:
    id: str
    label: str
    phrase: str
    installs: set[str] = field(default_factory=set)
    lifecycle: str = "one_use"
    charges: int = 1
    verbal_form: str = ""
    hem: str = ""

class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.active_magic: Optional[str] = None
        self.shared_subject: Optional[str] = None
        self.magic_cost_paid: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.type]

    def crew(self) -> list[Entity]:
        return [e for e in self.characters() if e.type in CREW_ROLES]

    def stam(self) -> list[str]:
        return [e for e in self.characters() if e.type == "morphodite"]

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.active_magic = self.active_magic
        clone.shared_subject = self.shared_subject
        clone.magic_cost_paid = self.magic_cost_paid
        clone.paragraphs = [[]]
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_conflict_drop(world: World) -> list[str]:
    outs: list[str] = []
    for morph in world.stam():
        for crew in world.crew():
            if morph.memes["trust"] >= THRESHOLD and crew.memes["fear"] >= THRESHOLD:
                key = (morph.id, crew.id)
                if key in world.fired:
                    continue
                world.fired.add(key)
                morph.memes["trust_increase"] += 0.2
                crew.memes["fear"] -= 0.3
                phrase = (
                    f"{morph.pronoun().capitalize()} felt safe and {morph.pronoun()} "
                    f"lowered {morph.pronoun('possessive')} barriers."
                )
                outs.append(phrase)
    return outs

def _r_trust_accum(world: World) -> list[str]:
    for morph in world.stam():
        if morph.memes["trust"] >= THRESHOLD:
            pair = (
                morph.pronoun().capitalize() + " felt more connected every time "
                f"{morph.pronoun()} shared, and {morph.pronoun()} was no longer isolated. "
                f"The crew drew nearer as {morph.pronoun('object')} shifted from light to shadow."
            )
            return [pair]
    return []

def _r_magic_depletion(world: World) -> list[str]:
    if not world.active_magic or world.magic_cost_paid:
        return []
    item = world.get(world.active_magic)
    if item.meters["magic_reserve"] >= (THRESHOLD + 0.2):
        return []
    world.magic_cost_paid = True
    return [
        f"The {item.label} flickered with dim blue arcs and hummed softly, "
        f"{item.pronoun('object')} drained of surplus power."
    ]

CAUSAL_RULES: list[Rule] = [
    Rule(name="harmony", tag="social", apply=_r_trust_accum),
    Rule(name="lower_conflict", tag="social", apply=_r_conflict_drop),
    Rule(name="depletion", tag="magic", apply=_r_magic_depletion),
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
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def select_active_magic(world: World) -> Optional[Magic]:
    item = world.get(world.active_magic) if world.active_magic else None
    return item

def predict_memory_share(world: World, morph: Entity, target: str) -> dict:
    sim = world.copy()
    astra = sim.get(morph.id)
    if astra:
        astra.memes["connection"] += 0.5
        astra.memes["trust"] += 0.3
        astra.memes["fear"] -= 0.4
        item = select_active_magic(sim)
        if item:
            item.meters["magic_reserve"] = max(0.0, item.meters["magic_reserve"] - 0.7)
    target_entity = sim.entities.get(target)
    if target_entity:
        target_entity.memes["curiosity"] += 0.6
        target_entity.memes["fear"] -= 0.3
    return {
        "harmony": sum(e.memes["trust"] for e in sim.characters()),
        "magic_down": bool(item and item.meters["magic_reserve"] < THRESHOLD),
        "crew_fear_removed": any(e.memes["fear"] < THRESHOLD for e in sim.crew()),
    }

def stationed(world: World, morph: Entity, place: Place) -> None:
    kind = "morphodite" if morph.type == "morphodite" else "crew"
    world.say(
        f"Deep in {place.phrase}, {morph.id} — a {kind} of few words — "
        f"checked {place.description}."
    )

def reveals(world: World, morph: Entity, magic: Magic) -> None:
    world.active_magic = magic.id
    magic_item = world.get(magic.id)
    magic_item.worn_by = morph.id
    world.shared_subject = "a fundamental memory"
    world.say(
        f"{morph.pronoun().capitalize()} held the {magic.label} aloft and "
        f"the facets glowed {magic.hem}. “This is the Dream Sphere,” {morph.id} "
        f"whispered. “It lets us share visions... of worlds unseen.”"
    )
    magic_item.meters["magic_reserve"] = magic.charges

def wonders_if_share(world: World, morph: Entity, crew: Entity, topic: str) -> None:
    morph.memes["curiosity"] += 0.7
    mood = (
        "careful" if crew.memes["fear"] >= THRESHOLD else
        "hopeful" if crew.memes["trust"] >= THRESHOLD else
        "quiet"
    )
    world.say(
        f"{morph.pronoun().capitalize()} turned to {crew.id} with a {mood} look. "
        f"“May I show {morph.pronoun()} something?” {morph.pronoun().capitalize()} "
        f"asked, fingers hovering over the {world.active_magic}. “It’s {topic} — "
        f"our shared past, in color and light.”"
    )

def warns_of_danger(world: World, crew: Entity, morph: Entity, magic: Magic) -> None:
    sig = ("warn", crew.id, morph.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    crew.memes["fear"] += 0.5
    world.say(
        f'"No,’ {crew.pronoun()} said, scowling. “You mustn\'t tap into '
        f"that power without safeguards. Such magic rips spacetime like stale fabric. "
        f'If you force the Sphere, you may unweave our shared thread!"'
    )

def expresses_fear(world: World, morph: Entity, crew: Entity, topic: str) -> None:
    morph.memes["fear"] += 0.6
    world.say(
        f'{morph.pronoun().capitalize()} curled {morph.pronoun("possessive")} '
        f"limbs close. “But it’s the only path to {topic},” {morph.pronoun()} "
        f"mumbled, eyes flickering with ambivalence."
    )

def hesitates(world: World, morph: Entity, crew: Entity) -> None:
    morph.memes["fear"] -= 0.2
    crew.memes["fear"] += 0.3
    side = (
        "left" if crew.id in {"Talis", "Rook"} else
        "right" if crew.id in {"Syl", "Kai"} else "center"
    )
    world.say(
        f"{morph.id} took a step {side}, tail-like limbs folding, "
        f"hesitating between urge and caution."
    )

def commands_halt(world: World, crew: Entity, magic: Magic, topic: str) -> None:
    crew.memes["fear"] += 0.4
    world.say(
        f'"Halt!” {crew.pronoun().capitalize()} said. “The {magic.label} is too '
        f"fragile for {topic}. You will overdraw {magic.pronoun()} before "
        f"you reach safe harbor.”"
    )

def reviews_shared_goal(world: World, morph: Entity) -> None:
    morph.memes["connection"] += 0.3
    world.say(
        f"{morph.pronoun().capitalize()} stared at the glimmering facets. "
        f"It pulsed with visions of stars they had charted together, "
        f"of nebulae they had named side by side. A future unspooled "
        f"before {morph.pronoun('object')}: {morph.id} could share joy."
    )

def compromises_with_small(world: World, morph: Entity, crew: Entity, new_topic: str) -> None:
    morph.memes["trust"] += 0.5
    crew.memes["fear"] -= 0.4
    world.shared_subject = new_topic
    magic = world.get(world.active_magic)
    magic.charges = max(0, magic.charges - 1)
    world.say(
        f"{morph.pronoun().capitalize()} exhaled, facets dimming. “Then I will "
        f"offer something brighter.” With delicate hands, {morph.id} "
        f"shifted {magic.pronoun()} focus to {new_topic}."
    )
    propagate(world)

def shares_memory_first(world: World, morph: Entity) -> None:
    morph.memes["trust"] += 0.6
    morph.memes["fear"] = 0.0
    world.magic_cost_paid = True
    world.say(
        f"{morph.pronoun().capitalize()} activated the Sphere for a joyous "
        f"vision — the stellar garden where first roots sprouted on comet soil. "
        f"The crew turned, breathless; {morph.pronoun()} saw {morph.it()} "
        f"finally let others inside {morph.pronoun('possessive')} mind."
    )
    propagate(world)

def shimmers_healed(world: World, morph: Entity, crew: Entity) -> None:
    world.say(
        f'Blue light rippled through {morph.pronoun("possessive")} form and '
        f"{crew.id}'s posture unfurled. Hesitation shifted to wonder as "
        f"thoughts interwove like threads."
    )
    morph.memes["connection"] += 0.7
    crew.memes["trust"] += 0.5
    crew.memes["fear"] = 0.0
    propagate(world)

def concludes_cycle(world: World, morph: Entity, crew: Entity) -> None:
    world.say(
        f"At journey’s end, {morph.id} rested — {morph.pronoun()} had "
        f"shared a piece of {morph.pronoun('possessive')} soul, and "
        f"{crew.pronoun('object')} had grown a piece nearer."
    )
    morph.memes["joy"] += 0.4
    crew.memes["happiness"] += 0.3

PLACE_REGISTRY = {
    "bridge": Place(
        id="bridge",
        phrase="the bridge overlooking the void",
        description="the observation window on the bridge",
        magic_friendly=True,
    ),
    "engine": Place(
        id="engine",
        phrase="the engine core",
        description="the humming heart of the ship",
        magic_friendly=False,
    ),
    "observation": Place(
        id="observation",
        phrase="the observation deck",
        description="the crystalline dome where stars streamed by",
        magic_friendly=True,
    ),
    "cargo": Place(
        id="cargo",
        phrase="the cargo bay",
        description="the glowing crèche filled with star-sprouted flora",
        magic_friendly=False,
    ),
}

ACTIVITY_REGISTRY = {
    "sharedream": Activity(
        id="sharedream",
        verb="share the streaming memory",
        gerund="sharing visions",
        demand="tap into this magic",
        mess="memory overload",
        ritual="speak the coordinates aloud",
        zone={"mind"},
        power_cost=0.6,
        tag="sharing",
    ),
    "harmonize": Activity(
        id="harmonize",
        verb="harmonize the resonance field",
        gerund="harmonizing the resonance",
        demand="rebalance the quantum lattice",
        mess="quantum strain",
        ritual="hum the stellar hymn",
        zone={"mind"},
        power_cost=0.4,
        tag="magic",
    ),
    "channel": Activity(
        id="channel",
        verb="channel the morph stream",
        gerund="channeling collective dreams",
        demand="enter the shared dreamstream",
        mess="identity drift",
        ritual="breathe in unison with the crew",
        zone={"mind"},
        power_cost=0.9,
        tag="sharing",
    ),
}

MAGIC_REGISTRY = {
    "dreamsphere": Magic(
        id="dreamsphere",
        label="Dream Sphere",
        phrase="the ancient Dream Sphere",
        installs={"memory_path", "image_sharing"},
        lifecycle="rechargeable",
        charges=2,
        verbal_form="speak stream coordinates aloud",
        hem="#00afff",
    ),
    "empathorb": Magic(
        id="empathorb",
        label="Empath Orb",
        phrase="the glimmering Empath Orb",
        installs={"empath_direct"},
        lifecycle="permanent",
        charges=1,
        verbal_form="request the bond",
        hem="#a0f0ff",
    ),
    "quantaflux": Magic(
        id="quantaflux",
        label="Quanta-Flux Rod",
        phrase="the crackling Quanta-Flux Rod",
        installs={"resonance_tuning"},
        lifecycle="one_use",
        charges=1,
        verbal_form="invoke the quantum hymn",
        hem="#ff5a00",
    ),
}

CREW_REGISTRY = {
    "Talis": Entity(
        id="Talis",
        type="astrogator",
        label="Talis",
        phrase="the sharp-eyed astrogator",
        traits=["skeptical", "logical"],
    ),
    "Rook": Entity(
        id="Rook",
        type="engineer",
        phrase="the burly engineer with oil-streaked hands",
        traits=["practical", "cautious"],
    ),
    "Syl": Entity(
        id="Syl",
        type="botanist",
        phrase="the gentle botanist whose vines curled constantly",
        traits=["empathic", "whimsical"],
    ),
    "Kai": Entity(
        id="Kai",
        type="commander",
        phrase="the stern but fair commander Kai",
        traits=["authoritative", "disciplined"],
    ),
    "Ora": Entity(
        id="Ora",
        type="medic",
        phrase="the empathic medic Ora",
        traits=["compassionate", "diplomatic"],
    ),
}

MORPH_NAMES = [
    "Astra", "Lumen", "Void", "Neb", "Echo", "Quant", "Stell", "Vey", "Kai-" + random.choice(["7", "9", "11"]),
]

TOPICS_POSITIVE = ["the birth of our solar plexus", "the stellar garden where flora first sprouted", "the day star’s first kiss", "the comet lullaby"]
TOPICS_NEGATIVE = ["the gravity well collapse", "the solar winds that scorched half the nebula", "the three who were lost to the void", "the event horizon that erased the chronicle"]

def valid_trio() -> list[tuple[str, str, str, str]]:
    trios: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACE_REGISTRY.items():
        if not place.magic_friendly:
            continue
        for act_id, act in ACTIVITY_REGISTRY.items():
            for mid, magic in MAGIC_REGISTRY.items():
                if act.power_cost > magic.charges * 0.5:
                    continue
                valid_staff = [
                    cid for cid in CREW_REGISTRY
                    if CREW_REGISTRY[cid].traits and "empath" in CREW_REGISTRY[cid].traits
                ]
                if not valid_staff:
                    continue
                for cid in valid_staff:
                    trios.append((place_id, act_id, mid, cid))
    return sorted(set(trios))

@dataclass
class StoryParams:
    place: str
    activity: str
    magic: str
    crew: str
    morph_name: str
    topic_positive: str
    topic_negative: str
    seed: Optional[int] = None

KNOWLEDGE_BASE = {
    "morphodite": [
        ("What is a morphodite?",
         "A morphodite is a being without fixed gender who adjusts form and mind to unify diverse perspectives."),
    ],
    "dreamsphere": [
        ("What does the Dream Sphere do?",
         "The Dream Sphere lets creatures share vision-streams: sights, sounds, and feelings. "
         "It must be aimed carefully to avoid memory overload."),
    ],
    "empathorb": [
        ("What is an Empath Orb?",
         "The Empath Orb creates direct bonds between minds so they feel each other’s emotions as colors."),
    ],
    "quantaflux": [
        ("What is a Quanta-Flux Rod?",
         "The Quanta-Flux Rod tunes quantum resonance fields allowing shared dreams, "
         "but each use weakens it irreversibly."),
    ],
    "sharing": [
        ("Why is sharing memories important?",
         "Sharing memories deepens bonds and spreads knowledge among the crew. "
         "Astra’s kind does this every cycle to weave tighter crew unity."),
    ],
    "magicspace": [
        ("How does magic work in space?",
         "On long voyages, the crew relies on ancient devices to share joys and warnings "
         "across the vessel. These artifacts draw on stellar energy."),
    ],
}
ROSTER = list(KNOWLEDGE_BASE.keys())

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    morph = f.get("morph")
    crew = f.get("crew")
    topic_pos = f.get("topic_positive")
    topic_neg = f.get("topic_negative")
    place = world.place
    act = f.get("activity")
    magic = f.get("magic")
    verb = act.verb if act else ""
    return [
        f'Write a very short children’s fable about a morphodite aboard a spaceship who '
        f'shares precious memories with the crew using a glowing artifact. Include the words '
        f'"Dream Sphere".',
        f'Compose a gentle 4–6 paragraph space adventure tale for ages 5–8 about '
        f'"{morph} shared something important from {morph}\'s past with the crew, '
        f'using a magical device the crew fears at first but eventually accepts.',
        f'Write a TinyStories-style vignette where a being from the void shares '
        f'a joyous memory through a glowing Sphere, healing old rifts with the crew '
        f'on the {place.description}. Use the phrase "stellar garden".',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    morph = f.get("morph")
    crew = f.get("crew")
    topic_pos = f.get("topic_positive")
    magic = f.get("magic_art")
    place_id = world.place.id
    place_word = {
        "bridge": "the bridge overlooking the cosmic ocean",
        "observation": "the observation dome with its walls of living crystal",
        "cargo": "the glowing nursery of star-sprouts",
        "engine": "the warm core where the ship’s heartbeat thrums",
    }.get(place_id, place_id)
    mc = (
        f"The {magic.label}" if magic else
        "the Dream Sphere" if world.active_magic else "the artifact"
    )
    sub = morph.pronoun()
    obj = morph.pronoun("object")
    pos = morph.pronoun("possessive")
    crew_type = "astrogator" if crew.id == "Talis" else \
                "engineer" if crew.id == "Rook" else \
                "botanist" if crew.id == "Syl" else \
                "commander" if crew.id == "Kai" else \
                "medic"
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Where on the ship is {morph} who can shift between light and shadow — "
                f"the {crew_type} {obj} — trying to share a memory?"
            ),
            answer=(
                f"{morph} is on {place_word}. {morph.pronoun().capitalize()} "
                f"holds {pos} glowing Dream Sphere forth and asks "
                f"{obj} to witness {topic_pos}."
            ),
        ),
        QAItem(
            question=(
                f"What worries the sharp-eyed {crew_type} {crew.id} about {mc} "
                f"whenever {morph} tries to share?"
            ),
            answer=(
                f"{crew.id} fears the power could tear spacetime itself. "
                f'They say, "You will unweave our shared thread!"'
            ),
        ),
        QAItem(
            question=(
                f"How does the Dream Sphere help {morph} share memories without "
                f"frightening the crew?"
            ),
            answer=(
                f"{morph} begins with {topic_pos} instead of the "
                f"painful {topic_negative} that scared the crew first. "
                f"When {morph.it()} changes the topic, the Sphere’s light "
                f"fades somewhat but bonds strengthen."
            ),
        ),
    ]
    if world.facts.get("healed"):
        qa.append(QAItem(
            question=(
                f"After {morph} shared the bright memory of the stellar garden, "
                f"how did the crew’s fear shift?"
            ),
            answer=(
                f" {crew.id}’s fear drained away as blue light rippled through "
                f"{morph} and {obj} felt thoughts joining like interwoven threads. "
                f"The crew drew nearer without hesitation."
            ),
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"morphodite", "sharing", "magicspace"}
    magic = getattr(world.facts.get("magic_art"), "id", "")
    if magic:
        tags.add(magic)
    out: list[QAItem] = []
    for tag in ["morphodite", "sharing", "magic", "magicspace", "dreamsphere", "empathorb"]:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE_BASE.get(tag, []))
    return out

def tell_story(
    place: Place,
    activity: Activity,
    magic: Magic,
    crew_name: str,
    morph_name: str,
    topic_positive: str,
) -> World:
    world = World(place)
    morph = world.add(Entity(
        id=morph_name, type="morphodite",
        label=morph_name, phrase=f"the morphodite {morph_name}",
        traits=["empathetic", "resilient"],
    ))
    crew = world.add(copy.deepcopy(CREW_REGISTRY[crew_name]))
    item = world.add(Entity(
        id=magic.id, type="magical artifact", label=magic.label,
        phrase=magic.phrase, owner=morph.id,
        meters={"magic_reserve": magic.charges},
    ))
    item.caretaker = crew.id

    world.say(
        f"Deep in {place.phrase} aboard the Hollow Star, "
        f"{morph.id} hovered — not grown, not machine, but a bundle of "
        f"light and shadow tuned to the stars."
    )
    stationary_in_place(world, morph, place)
    reveals(world, morph, magic)
    stationary_in_place(world, morph, place)
    wonders_if_share(world, morph, crew, topic_positive)
    warns_of_danger(world, crew, morph, magic)
    expresses_fear(world, morph, crew, topic_positive)
    hesitates(world, morph, crew)
    commands_halt(world, crew, magic, topic_positive)
    reviews_shared_goal(world, morph)
    compromises_with_small(world, morph, crew, topic_positive)
    shares_memory_first(world, morph)
    shimmers_healed(world, morph, crew)
    concludes_cycle(world, morph, crew)

    world.facts.update(
        morph=morph, crew=crew, activity=activity,
        magic_art=magic, place=place,
        topic_positive=topic_positive, topic_negative=TOPICS_NEGATIVE[0],
        healed=crew.memes["fear"] < THRESHOLD,
    )
    return world

def stationary_in_place(world: World, morph: Entity, place: Place) -> None:
    world.para()
    stationed(world, morph, place)

ASP_RULES = r"""
% A place supports an activity if it is magic-friendly.
place_supports_sharing(P) :- magic_place(P).

% A magic item must have sufficient reserves to power the activity.
sufficient_magic(M, A) :- magic_item(M, Chg),
                            magic_charge(Chg),
                            power_cost(A, Cost),
                            Chg >= Cost.
magic_item(M, Chg) :- magic(M), charge_of(M, Chg).
charge_of("dreamsphere", 2).
charge_of("empathorb", 5).
charge_of("quantaflux", 1).
power_cost("sharedream", 0.6).
power_cost("harmonize", 0.4).
power_cost("channel", 0.9).

% Crew must be empathic to be valid.
valid_crew(C) :- crew(C), empath(C).
empath(C) :- crew(C), trait_in(C, "empathic").

% Valid story requires place, activity, magic, and empathic crew.
valid_story(Pl, Ac, Mg, Cr) :-
    place_supports_sharing(Pl),
    activity_tag(Ac, "sharing"),
    magic_item(Mg, _),
    valid_crew(Cr),
    holds(Mg, Pl, Ac).
holds(Mg, Pl, Ac) :- magic(Mg), place(Pl), activity(Ac), lifecycle(Mg,"one_use").
holds(Mg, Pl, Ac) :- magic(Mg), place(Pl), activity(Ac), lifecycle(Mg,"rechargeable").
"""

def asp_facts() -> str:
    lines: list[str] = []
    for pid, p in PLACE_REGISTRY.items():
        lines.append(fact("magic_place" if p.magic_friendly else "place", pid))
    for aid, a in ACTIVITY_REGISTRY.items():
        lines.append(fact("activity", aid))
        lines.append(fact("power_cost", aid, a.power_cost))
        for t in a.tag.split():
            lines.append(fact("activity_tag", aid, t))
        lines.append(fact("zone", aid, "mind"))
    for mid, m in MAGIC_REGISTRY.items():
        lines.append(fact("magic", mid))
        lines.append(fact("lifecycle", mid, m.lifecycle))
        lines.append(fact("charge_of", mid, m.charges))
    for cid in CREW_REGISTRY:
        lines.append(fact("crew", cid))
        for tr in CREW_REGISTRY[cid].traits:
            lines.append(fact("trait_in", cid, tr))
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_trios() -> list[tuple]:
    model = one_model(asp_program("#show valid_story/4."))
    return sorted(atoms(model, "valid_story"))

def asp_verify() -> int:
    clingo_set = set(asp_valid_trios())
    python_set = set(valid_trio())
    if clingo_set == python_set:
        print(f"OK: parity (clingo={len(clingo_set)} vs python={len(python_set)}).")
        return 0
    print("MISMATCH between ASP gate and valid_trio():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1

CURATED_PAIRS = [
    ("observation", "sharedream", "dreamsphere", "Syl"),
    ("bridge", "sharedream", "empathorb", "Ora"),
    ("observation", "harmonize", "quantaflux", "Ora"),
    ("cargo", "channel", "empathorb", "Syl"),
]

def explain_rejection(
    place: Place, activity: Activity, magic: Magic, topic: str
) -> str:
    return (
        f"(No story: {activity.ritual} in {place.phrase} would overload "
        f"the {magic.label} and cause {topic.split()[0]} scatter. "
        f"A smaller sharing is required first.)"
    )

def explain_staff(place_id: str) -> str:
    has_em = any("empath" in CREW_REGISTRY[c].traits for c in CREW_REGISTRY)
    return (
        f"(No story: the {place_id} needs at least one empathic crew member; "
        f"present: {'yes' if has_em else 'no'}.)"
    )

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="morphodite_sharing_magic_space adventure — "
                    "a tiny tales world of light, memory, and shipboard life."
    )
    ap.add_argument("--place", choices=list(PLACE_REGISTRY))
    ap.add_argument("--activity", choices=list(ACTIVITY_REGISTRY))
    ap.add_argument("--magic", choices=list(MAGIC_REGISTRY))
    ap.add_argument("--crew", choices=list(CREW_REGISTRY))
    ap.add_argument("--morph-name")
    ap.add_argument("--topic-positive", choices=TOPICS_POSITIVE)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.magic:
        act = ACTIVITY_REGISTRY[args.activity]
        mag = MAGIC_REGISTRY[args.magic]
        if act.power_cost > mag.charges * 0.5:
            raise StoryError(explain_rejection(
                PLACE_REGISTRY[args.place] if args.place else None,
                act, mag, TOPICS_NEGATIVE[0],
            ))
    if args.place and not PLACE_REGISTRY[args.place].magic_friendly:
        raise StoryError(explain_staff(args.place))
    trio = [c for c in valid_trio()
            if (args.place is None or c[0] == args.place)
            and (args.activity is None or c[1] == args.activity)
            and (args.magic is None or c[2] == args.magic)
            and (args.crew is None or c[3] == args.crew)]
    if not trio:
        raise StoryError("(No valid trio matches options.)")
    place_id, act_id, magic_id, crew_id = rng.choice(sorted(trio))
    magic = MAGIC_REGISTRY[magic_id]
    topic_positive = args.topic_positive or rng.choice(TOPICS_POSITIVE)
    morph_name = args.morph_name or rng.choice(MORPH_NAMES)
    return StoryParams(
        place=place_id,
        activity=act_id,
        magic=magic_id,
        crew=crew_id,
        morph_name=morph_name,
        topic_positive=topic_positive,
        topic_negative=rng.choice(TOPICS_NEGATIVE),
        seed=None,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell_story(
        PLACE_REGISTRY[params.place],
        ACTIVITY_REGISTRY[params.activity],
        MAGIC_REGISTRY[params.magic],
        params.crew,
        params.morph_name,
        params.topic_positive,
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
    if trace and sample.world:
        lines = ["--- world model state ---"]
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v >= THRESHOLD}
            memes = {k: v for k, v in e.memes.items() if v >= THRESHOLD}
            bits = []
            if e.type == "morphodite":
                bits.append("morphodite")
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            lines.append(f"  {e.id:10} {bits}")
        print("\n".join(lines))
    if qa:
        print()
        print("== Story Q&A ==")
        for i, q in enumerate(sample.story_qa, 1):
            print(f"Q{i}: {q.question}")
            print(f"A{i}: {q.answer}")
        print()
        print("== World Q&A ==")
        for i, w in enumerate(sample.world_qa, 1):
            print(f"Q{i}: {w.question}")
            print(f"A{i}: {w.answer}")

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        trios = asp_valid_trios()
        print(f"{len(trios)} clingo-valid story trios:\n")
        for pl, ac, mg, cr in trios:
            print(f"  {pl:11} {ac:10} {mg:12} — {cr}")
        return

    base_seed = args.seed or random.randrange(2 ** 31)
    samples: list[StorySample] = []
    seen = set()

    if args.all:
        samples = [generate(
            StoryParams(
                place=p, activity=a, magic=m, crew=c,
                morph_name=morph,
                topic_positive=(
                    "the stellar garden where flora first sprouted on comet soil."
                ),
                topic_negative="the gravity well collapse",
            )
        ) for p, a, m, c in CURATED_PAIRS for morph in MORPH_NAMES[:5]]
        )
    else:
        for i in range(args.n):
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as se:
                print(se)
                return
            params.seed = seed
            story = generate(params)
            if story.story not in seen:
                seen.add(story.story)
                samples.append(story)
            if len(samples) >= args.n:
                break

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        h = ""
        if args.all:
            h = f"### {s.params.morph_name} sharing on {s.params.place} with {s.params.crew}"
        elif len(samples) > 1:
            h = f"### variant {i+1}"
        emit(s, trace=args.trace, qa=args.qa, header=h)
        if i < len(samples) - 1:
            print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
