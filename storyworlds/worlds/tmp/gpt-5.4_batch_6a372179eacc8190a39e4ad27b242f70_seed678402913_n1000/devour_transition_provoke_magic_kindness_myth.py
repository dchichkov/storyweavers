#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/devour_transition_provoke_magic_kindness_myth.py
============================================================================

A small myth-shaped storyworld about a child guarding a magical creature during
a sacred transition. A hungry myth-beast may be provoked into trying to devour
the fragile being, and the child must answer with kindness and the right magic.

The world prefers a narrow set of plausible variants over broad weak coverage:
a place must actually fit the creature, the threat must be one that could truly
hunt it there, the chosen magic must steady the creature's transition, and the
chosen kindness must be the sort of thing that could calm that threat.

Run it
------
    python storyworlds/worlds/gpt-5.4/devour_transition_provoke_magic_kindness_myth.py
    python storyworlds/worlds/gpt-5.4/devour_transition_provoke_magic_kindness_myth.py --all
    python storyworlds/worlds/gpt-5.4/devour_transition_provoke_magic_kindness_myth.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/devour_transition_provoke_magic_kindness_myth.py --qa
    python storyworlds/worlds/gpt-5.4/devour_transition_provoke_magic_kindness_myth.py --trace --seed 22
    python storyworlds/worlds/gpt-5.4/devour_transition_provoke_magic_kindness_myth.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "goddess"}
        male = {"boy", "father", "man", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    image: str
    wards: set[str] = field(default_factory=set)
    threats: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Ward:
    id: str
    label: str
    phrase: str
    stage_before: str
    stage_after: str
    transition_word: str
    vulnerable_to: set[str] = field(default_factory=set)
    magic_ok: set[str] = field(default_factory=set)
    opening: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Threat:
    id: str
    label: str
    phrase: str
    appetite: int
    prowls: set[str] = field(default_factory=set)
    kindness_ok: set[str] = field(default_factory=set)
    approach_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicAid:
    id: str
    label: str
    phrase: str
    steady: int
    wards: set[str] = field(default_factory=set)
    text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class KindnessAct:
    id: str
    label: str
    phrase: str
    power: int
    threats: set[str] = field(default_factory=set)
    text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ProvokeAct:
    id: str
    label: str
    phrase: str
    strength: int
    places: set[str] = field(default_factory=set)
    text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_provoked(world: World) -> list[str]:
    threat = world.get("threat")
    ward = world.get("ward")
    if threat.memes["provoked"] < THRESHOLD:
        return []
    sig = ("provoked",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    threat.memes["anger"] += 1
    ward.meters["danger"] += 1
    world.get("child").memes["fear"] += 1
    return ["__danger__"]


def _r_calm(world: World) -> list[str]:
    threat = world.get("threat")
    if threat.memes["soothed"] < THRESHOLD or threat.memes["anger"] <= 0:
        return []
    sig = ("calmed",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    threat.memes["anger"] = max(0.0, threat.memes["anger"] - 1.0)
    threat.meters["hunger"] = max(0.0, threat.meters["hunger"] - 1.0)
    world.get("child").memes["hope"] += 1
    return []


def _r_transition(world: World) -> list[str]:
    ward = world.get("ward")
    if ward.meters["steady"] < THRESHOLD or ward.meters["danger"] >= THRESHOLD or ward.meters["devoured"] >= THRESHOLD:
        return []
    sig = ("transition",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ward.meters["transformed"] += 1
    world.get("child").memes["wonder"] += 1
    return ["__transition__"]


CAUSAL_RULES = [
    Rule(name="provoked", tag="social", apply=_r_provoked),
    Rule(name="calm", tag="social", apply=_r_calm),
    Rule(name="transition", tag="magic", apply=_r_transition),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "moon_orchard": Place(
        id="moon_orchard",
        label="the Moon Orchard",
        image="silver fig trees stood in rows, and pale fruit shone like little moons",
        wards={"moon_moth", "dawn_fawn"},
        threats={"bat_king", "shadow_fox"},
        tags={"moon", "orchard"},
    ),
    "reed_delta": Place(
        id="reed_delta",
        label="the Reed Delta",
        image="the water curled between tall reeds, and the evening wind made them whisper together",
        wards={"river_dragon"},
        threats={"white_heron"},
        tags={"river", "reeds"},
    ),
    "laurel_hill": Place(
        id="laurel_hill",
        label="the Laurel Hill",
        image="laurel leaves trembled around an old stone altar where dawn always came first",
        wards={"dawn_fawn", "moon_moth"},
        threats={"shadow_fox", "bat_king"},
        tags={"hill", "laurel"},
    ),
}

WARDS = {
    "moon_moth": Ward(
        id="moon_moth",
        label="moon cocoon",
        phrase="a silver moon cocoon",
        stage_before="cocoon",
        stage_after="moon moth",
        transition_word="unfurl",
        vulnerable_to={"bat_king"},
        magic_ok={"moon_chime", "temple_lamp"},
        opening="It hung from a bent fig branch like a lantern no bigger than a plum.",
        ending_image="At last the moon moth rose from the branch and wrote a white curve through the dark.",
        tags={"moth", "moon", "transition"},
    ),
    "river_dragon": Ward(
        id="river_dragon",
        label="pearl fry",
        phrase="a pearl fry with clear fins",
        stage_before="fry",
        stage_after="river dragon",
        transition_word="lengthen",
        vulnerable_to={"white_heron"},
        magic_ok={"shell_flute", "temple_lamp"},
        opening="It circled in the pool with a bright bead of light in its throat.",
        ending_image="Then the little river dragon slipped through the reeds, trailing blue light on the water.",
        tags={"river", "dragon", "transition"},
    ),
    "dawn_fawn": Ward(
        id="dawn_fawn",
        label="ember fawn",
        phrase="an ember fawn with a star on its brow",
        stage_before="fawn",
        stage_after="sun stag",
        transition_word="brighten",
        vulnerable_to={"shadow_fox"},
        magic_ok={"sun_thread", "temple_lamp"},
        opening="It slept in the grass, and every breath sent a warm gold spark into the air.",
        ending_image="When the light changed, the young sun stag stepped up the hill and the grass shone after it.",
        tags={"fawn", "sun", "transition"},
    ),
}

THREATS = {
    "bat_king": Threat(
        id="bat_king",
        label="Bat King",
        phrase="the Bat King with velvet wings",
        appetite=2,
        prowls={"moon_orchard", "laurel_hill"},
        kindness_ok={"fig_offering", "reed_song"},
        approach_line="From the branches above came the hush of leather wings.",
        tags={"bat", "night"},
    ),
    "white_heron": Threat(
        id="white_heron",
        label="White Heron",
        phrase="the White Heron with a spear-bright beak",
        appetite=2,
        prowls={"reed_delta"},
        kindness_ok={"reed_song", "milk_bowl"},
        approach_line="A white shape stepped through the reeds, slow and tall as a dream.",
        tags={"heron", "river"},
    ),
    "shadow_fox": Threat(
        id="shadow_fox",
        label="Shadow Fox",
        phrase="the Shadow Fox with dusk in its fur",
        appetite=2,
        prowls={"moon_orchard", "laurel_hill"},
        kindness_ok={"fig_offering", "milk_bowl"},
        approach_line="Between the roots glimmered two clever eyes.",
        tags={"fox", "night"},
    ),
}

MAGIC = {
    "moon_chime": MagicAid(
        id="moon_chime",
        label="moon chime",
        phrase="a moon chime of shell and silver thread",
        steady=2,
        wards={"moon_moth"},
        text="rang the moon chime once, and the soft silver note wrapped the cocoon like a calm ribbon",
        qa_text="rang the moon chime to steady the cocoon",
        tags={"magic", "chime"},
    ),
    "shell_flute": MagicAid(
        id="shell_flute",
        label="shell flute",
        phrase="a shell flute carved with waves",
        steady=2,
        wards={"river_dragon"},
        text="blew one low note on the shell flute, and the pool answered with a circle of blue light",
        qa_text="played the shell flute so the pool itself guarded the fry",
        tags={"magic", "flute"},
    ),
    "sun_thread": MagicAid(
        id="sun_thread",
        label="sun thread",
        phrase="a spool of sun thread from the temple loom",
        steady=2,
        wards={"dawn_fawn"},
        text="laid a loop of sun thread around the sleeping fawn, and the thread shone warm instead of tight",
        qa_text="laid sun thread around the fawn as a warm ward",
        tags={"magic", "sun"},
    ),
    "temple_lamp": MagicAid(
        id="temple_lamp",
        label="temple lamp",
        phrase="a small temple lamp with star oil",
        steady=1,
        wards={"moon_moth", "river_dragon", "dawn_fawn"},
        text="lifted the temple lamp, and its steady glow reminded the sacred creature what shape to become",
        qa_text="raised the temple lamp to guide the sacred change",
        tags={"magic", "lamp"},
    ),
}

KINDNESS = {
    "fig_offering": KindnessAct(
        id="fig_offering",
        label="fig offering",
        phrase="a split moon fig on both palms",
        power=2,
        threats={"bat_king", "shadow_fox"},
        text="held out a moon fig in open hands instead of a fist",
        qa_text="offered food with open hands",
        tags={"kindness", "fig"},
    ),
    "reed_song": KindnessAct(
        id="reed_song",
        label="reed song",
        phrase="a soft reed song",
        power=2,
        threats={"bat_king", "white_heron"},
        text="sang a quiet reed song that carried no challenge at all",
        qa_text="sang softly so the hunter would not feel challenged",
        tags={"kindness", "song"},
    ),
    "milk_bowl": KindnessAct(
        id="milk_bowl",
        label="milk bowl",
        phrase="a small clay bowl of sweet milk",
        power=2,
        threats={"white_heron", "shadow_fox"},
        text="set down a clay bowl of sweet milk and stepped back to show trust",
        qa_text="set down a bowl of sweet milk and stepped back",
        tags={"kindness", "milk"},
    ),
}

PROVOKES = {
    "taunt": ProvokeAct(
        id="taunt",
        label="taunt",
        phrase="a sharp taunt",
        strength=2,
        places={"moon_orchard", "reed_delta", "laurel_hill"},
        text='For one frightened heartbeat, the child almost chose to provoke the hunter with a bold insult.',
        tags={"provoke"},
    ),
    "clap": ProvokeAct(
        id="clap",
        label="clap",
        phrase="a hard clap of the hands",
        strength=1,
        places={"moon_orchard", "reed_delta", "laurel_hill"},
        text="Fear made the child's hands clap once, too loud for a holy place.",
        tags={"provoke"},
    ),
    "pebble": ProvokeAct(
        id="pebble",
        label="pebble toss",
        phrase="a pebble tossed in anger",
        strength=2,
        places={"moon_orchard", "laurel_hill"},
        text="A pebble skittered over stone, a foolish little challenge that could only provoke a hungry beast.",
        tags={"provoke"},
    ),
    "bow_head": ProvokeAct(
        id="bow_head",
        label="bowed head",
        phrase="a bowed head and still hands",
        strength=0,
        places={"moon_orchard", "reed_delta", "laurel_hill"},
        text="The child remembered not to provoke what was already hungry, and kept still.",
        tags={"provoke"},
    ),
}

GIRL_NAMES = ["Ione", "Thaleia", "Mira", "Daphne", "Selene", "Lysa", "Calla", "Rhea"]
BOY_NAMES = ["Nikos", "Theron", "Ari", "Leander", "Orin", "Phaon", "Damon", "Helios"]
TRAITS = ["gentle", "brave", "patient", "kind", "quiet", "steady"]


def place_hosts(place_id: str, ward_id: str, threat_id: str) -> bool:
    place = PLACES[place_id]
    return ward_id in place.wards and threat_id in place.threats


def hazard_at_risk(ward_id: str, threat_id: str) -> bool:
    return threat_id in WARDS[ward_id].vulnerable_to


def magic_fits(ward_id: str, magic_id: str) -> bool:
    return magic_id in WARDS[ward_id].magic_ok and ward_id in MAGIC[magic_id].wards


def kindness_fits(threat_id: str, kindness_id: str) -> bool:
    return kindness_id in THREATS[threat_id].kindness_ok and threat_id in KINDNESS[kindness_id].threats


def provoke_fits(place_id: str, provoke_id: str) -> bool:
    return place_id in PROVOKES[provoke_id].places


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for ward_id in WARDS:
            for threat_id in THREATS:
                if place_hosts(place_id, ward_id, threat_id) and hazard_at_risk(ward_id, threat_id):
                    combos.append((place_id, ward_id, threat_id))
    return sorted(combos)


def sensible_magic_for(ward_id: str) -> list[str]:
    return sorted(mid for mid in MAGIC if magic_fits(ward_id, mid) and MAGIC[mid].steady >= 1)


def sensible_kindness_for(threat_id: str) -> list[str]:
    return sorted(kid for kid in KINDNESS if kindness_fits(threat_id, kid) and KINDNESS[kid].power >= SENSE_MIN)


def risk_value(threat_id: str, provoke_id: str, delay: int) -> int:
    return THREATS[threat_id].appetite + PROVOKES[provoke_id].strength + delay


def safety_value(ward_id: str, threat_id: str, magic_id: str, kindness_id: str) -> int:
    if not (magic_fits(ward_id, magic_id) and kindness_fits(threat_id, kindness_id)):
        return -999
    return MAGIC[magic_id].steady + KINDNESS[kindness_id].power


def outcome_of(params: "StoryParams") -> str:
    if PROVOKES[params.provoke].strength == 0:
        return "peaceful"
    return "saved" if safety_value(params.ward, params.threat, params.magic, params.kindness) >= risk_value(params.threat, params.provoke, params.delay) else "devoured"


def predict_danger(place_id: str, ward_id: str, threat_id: str, provoke_id: str, delay: int) -> dict:
    return {
        "can_devour": hazard_at_risk(ward_id, threat_id),
        "risk": risk_value(threat_id, provoke_id, delay),
        "place": PLACES[place_id].label,
    }


def introduce(world: World, child: Entity, elder: Entity, ward_cfg: Ward) -> None:
    world.say(
        f"In the age when streams still listened, {child.id} climbed to {world.place.label}. "
        f"There, {world.place.image}."
    )
    world.say(
        f"{elder.id}, the old keeper, had asked {child.pronoun('object')} to watch over {ward_cfg.phrase}. "
        f"{ward_cfg.opening}"
    )


def explain_transition(world: World, child: Entity, elder: Entity, ward_cfg: Ward, threat_cfg: Threat) -> None:
    world.say(
        f'"Tonight is its transition," {elder.id} said. "Before dawn, the little {ward_cfg.stage_before} '
        f'will {ward_cfg.transition_word} into a {ward_cfg.stage_after}."'
    )
    world.say(
        f'"Be kind, and do not provoke {threat_cfg.phrase}," {elder.pronoun()} warned. '
        f'"If hunger and anger wake together, {threat_cfg.pronoun()} may devour the holy one before the change is done."'
    )


def approach_threat(world: World, child: Entity, threat_cfg: Threat, provoke_cfg: ProvokeAct) -> None:
    threat = world.get("threat")
    world.say(threat_cfg.approach_line)
    world.say(f"Soon {threat_cfg.phrase} came near, nose or beak lifted toward the sacred scent.")
    world.say(provoke_cfg.text)
    if provoke_cfg.strength > 0:
        threat.memes["provoked"] += 1
        propagate(world, narrate=False)
        world.say(
            f"The sound did provoke {threat_cfg.pronoun('object')}. A hungry gleam sharpened in {threat_cfg.pronoun('possessive')} eyes."
        )
    else:
        threat.memes["stillness_seen"] += 1
        world.say(
            f"Because {child.id} stayed gentle, the hunter paused instead of lunging."
        )


def use_kindness(world: World, child: Entity, kindness_cfg: KindnessAct, threat_cfg: Threat) -> None:
    threat = world.get("threat")
    child.memes["kindness"] += 1
    threat.memes["soothed"] += 1
    world.say(
        f"Then {child.id} {kindness_cfg.text}. Even in fear, {child.pronoun()} chose kindness first."
    )
    propagate(world, narrate=False)


def use_magic(world: World, child: Entity, magic_cfg: MagicAid, ward_cfg: Ward) -> None:
    ward = world.get("ward")
    child.memes["faith"] += 1
    ward.meters["steady"] += 1
    ward.meters["steady"] += float(magic_cfg.steady - 1)
    world.say(
        f"After that, {child.id} {magic_cfg.text}."
    )
    propagate(world, narrate=False)


def devour_attempt(world: World, child: Entity, threat_cfg: Threat, ward_cfg: Ward) -> None:
    ward = world.get("ward")
    threat = world.get("threat")
    ward.meters["danger"] += 1
    threat.meters["hunger"] += 1
    child.memes["fear"] += 1
    world.say(
        f"{threat_cfg.label} gathered itself to spring. For a breath it looked as if {threat_cfg.pronoun()} would devour the little {ward_cfg.stage_before} whole."
    )


def rescue(world: World, child: Entity, ward_cfg: Ward, threat_cfg: Threat) -> None:
    ward = world.get("ward")
    threat = world.get("threat")
    ward.meters["danger"] = 0.0
    threat.meters["hunger"] = 0.0
    threat.memes["anger"] = 0.0
    ward.meters["steady"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The fierce moment passed. {threat_cfg.label} lowered {threat_cfg.pronoun('possessive')} head, took the offered peace, and turned aside from the holy creature."
    )
    world.say(
        f"Safe again, the sacred body began its true change."
    )


def peaceful_transition(world: World, child: Entity, ward_cfg: Ward, threat_cfg: Threat) -> None:
    ward = world.get("ward")
    threat = world.get("threat")
    threat.meters["hunger"] = 0.0
    ward.meters["steady"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{threat_cfg.label} stayed at the edge of the clearing, no longer a danger. Quiet kindness left room for the miracle."
    )


def finish_blessed(world: World, child: Entity, elder: Entity, ward_cfg: Ward) -> None:
    child.memes["joy"] += 1
    child.memes["wonder"] += 1
    world.say(
        ward_cfg.ending_image
    )
    world.say(
        f'{elder.id} smiled. "Magic obeys a steady heart," {elder.pronoun()} said. '
        f'"You kept watch with kindness, and so the world kept its promise."'
    )


def loss(world: World, child: Entity, elder: Entity, threat_cfg: Threat, ward_cfg: Ward) -> None:
    ward = world.get("ward")
    threat = world.get("threat")
    ward.meters["devoured"] += 1
    ward.meters["danger"] = 0.0
    threat.meters["hunger"] += 1
    child.memes["grief"] += 1
    world.say(
        f"But hunger was quicker than song or spell. {threat_cfg.label} leapt, and the holy {ward_cfg.stage_before} was gone."
    )
    world.say(
        f"When {elder.id} returned, {child.id} was weeping beside the empty place where the transition should have happened."
    )
    world.say(
        f'"Remember this," {elder.pronoun()} said softly. "Power that tries to answer fear with more fear only feeds the dark. Kindness must come before the bite, not after."'
    )
    world.say(
        f"At sunrise, {child.id} set a little bowl of figs and flowers on the stone, so the hill would remember mercy even after sorrow."
    )


def tell(
    place_cfg: Place,
    ward_cfg: Ward,
    threat_cfg: Threat,
    magic_cfg: MagicAid,
    kindness_cfg: KindnessAct,
    provoke_cfg: ProvokeAct,
    child_name: str = "Ione",
    child_gender: str = "girl",
    elder_type: str = "woman",
    trait: str = "gentle",
    delay: int = 0,
) -> World:
    world = World(place_cfg)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", label=child_name))
    elder = world.add(Entity(id="Thea", kind="character", type=elder_type, role="elder", label="the keeper"))
    ward = world.add(Entity(id="ward", type="ward", label=ward_cfg.label, phrase=ward_cfg.phrase, tags=set(ward_cfg.tags)))
    threat = world.add(Entity(id="threat", type="beast", label=threat_cfg.label, phrase=threat_cfg.phrase, tags=set(threat_cfg.tags)))
    shrine = world.add(Entity(id="place", type="place", label=place_cfg.label, phrase=place_cfg.label, tags=set(place_cfg.tags)))

    child.attrs["trait"] = trait
    child.memes["kindness"] = 1.0 if trait in {"gentle", "kind", "patient"} else 0.0
    threat.meters["hunger"] = float(threat_cfg.appetite)

    introduce(world, child, elder, ward_cfg)
    explain_transition(world, child, elder, ward_cfg, threat_cfg)

    pred = predict_danger(place_cfg.id, ward_cfg.id, threat_cfg.id, provoke_cfg.id, delay)
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["can_devour"] = pred["can_devour"]

    world.para()
    approach_threat(world, child, threat_cfg, provoke_cfg)

    if delay > 0:
        world.say(
            f"For {delay} long heartbeat{'s' if delay != 1 else ''}, fear made everything feel slower."
        )

    world.para()
    use_kindness(world, child, kindness_cfg, threat_cfg)
    use_magic(world, child, magic_cfg, ward_cfg)

    outcome = outcome_of(
        StoryParams(
            place=place_cfg.id,
            ward=ward_cfg.id,
            threat=threat_cfg.id,
            magic=magic_cfg.id,
            kindness=kindness_cfg.id,
            provoke=provoke_cfg.id,
            name=child_name,
            gender=child_gender,
            elder=elder_type,
            trait=trait,
            delay=delay,
            seed=None,
        )
    )

    world.para()
    if outcome == "peaceful":
        peaceful_transition(world, child, ward_cfg, threat_cfg)
        finish_blessed(world, child, elder, ward_cfg)
    elif outcome == "saved":
        devour_attempt(world, child, threat_cfg, ward_cfg)
        rescue(world, child, ward_cfg, threat_cfg)
        finish_blessed(world, child, elder, ward_cfg)
    else:
        devour_attempt(world, child, threat_cfg, ward_cfg)
        loss(world, child, elder, threat_cfg, ward_cfg)

    world.facts.update(
        child=child,
        elder=elder,
        ward=ward,
        threat=threat,
        shrine=shrine,
        place_cfg=place_cfg,
        ward_cfg=ward_cfg,
        threat_cfg=threat_cfg,
        magic_cfg=magic_cfg,
        kindness_cfg=kindness_cfg,
        provoke_cfg=provoke_cfg,
        delay=delay,
        outcome=outcome,
        transformed=ward.meters["transformed"] >= THRESHOLD,
        devoured=ward.meters["devoured"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    ward: str
    threat: str
    magic: str
    kindness: str
    provoke: str
    name: str
    gender: str
    elder: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "transition": [(
        "What does transition mean in a story like this?",
        "Transition means changing from one state into another. In myths, that change can be magical, like a cocoon becoming a moth or a small creature becoming a greater one."
    )],
    "magic": [(
        "What is magic in a myth?",
        "Magic in a myth is a special power that helps the world do more than ordinary things. It often works best when it is used with wisdom instead of pride."
    )],
    "kindness": [(
        "Why can kindness be powerful?",
        "Kindness can calm fear and anger before they grow worse. Sometimes a gentle choice changes what happens more than a hard one does."
    )],
    "devour": [(
        "What does devour mean?",
        "Devour means to eat something up very quickly and greedily. In myths, the word often makes danger feel large and frightening."
    )],
    "provoke": [(
        "What does provoke mean?",
        "Provoke means to poke at someone's anger and make them more likely to lash out. It is the opposite of calming things down."
    )],
    "moth": [(
        "What comes out of a cocoon?",
        "A moth or butterfly can come out of a cocoon. It changes shape during its time inside."
    )],
    "river": [(
        "Why are reeds often near rivers?",
        "Reeds are tall plants that like wet ground. They grow well where water stays close to the surface."
    )],
    "fox": [(
        "Why are foxes called clever in stories?",
        "Foxes are often shown as clever because they move quietly and notice chances quickly. Storytellers use them to stand for sly thinking."
    )],
    "bat": [(
        "How do bats find things in the dark?",
        "Bats can use tiny sounds and echoes to sense where things are. That helps them move and hunt at night."
    )],
    "heron": [(
        "What does a heron do by the water?",
        "A heron stands very still and watches for fish. Then it strikes quickly with its long beak."
    )],
    "chime": [(
        "What is a chime?",
        "A chime is something that rings with a clear note. In stories, that note can sound calm and magical."
    )],
    "flute": [(
        "What is a flute?",
        "A flute is a musical instrument you blow into to make a note. A soft flute sound can feel gentle and far away."
    )],
    "lamp": [(
        "What does a lamp do?",
        "A lamp gives a steady light. In stories, steady light often stands for guidance and safety."
    )],
}

KNOWLEDGE_ORDER = [
    "transition", "magic", "kindness", "devour", "provoke",
    "moth", "river", "fox", "bat", "heron", "chime", "flute", "lamp",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    ward_cfg = f["ward_cfg"]
    threat_cfg = f["threat_cfg"]
    place_cfg = f["place_cfg"]
    outcome = f["outcome"]
    magic_cfg = f["magic_cfg"]
    kindness_cfg = f["kindness_cfg"]
    base = (
        f'Write a child-facing myth that includes the words "devour", "transition", and "provoke". '
        f'The story should happen at {place_cfg.label} and center on {child.id} guarding {ward_cfg.phrase}.'
    )
    if outcome == "devoured":
        return [
            base,
            f"Tell a sorrowful myth where {child.id} is warned not to provoke {threat_cfg.phrase}, but fear slows the gentle answer and the sacred change is lost.",
            f"Write a myth in which kindness is learned through grief after a hungry hunter devours the holy creature before its transition can finish.",
        ]
    if outcome == "peaceful":
        return [
            base,
            f"Tell a calm myth where {child.id} refuses to provoke {threat_cfg.phrase}, answers with {kindness_cfg.label}, and uses {magic_cfg.label} to guide a holy transition.",
            f"Write a gentle magical myth where stillness and kindness make room for a miracle.",
        ]
    return [
        base,
        f"Tell a myth where {child.id} almost provokes {threat_cfg.phrase}, then chooses {kindness_cfg.label} and {magic_cfg.label} in time to save the sacred creature.",
        f"Write a magical kindness story where danger rises for a moment, but a calm child keeps the holy transition safe.",
    ]


def pair_answer_lines(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    ward_cfg = f["ward_cfg"]
    threat_cfg = f["threat_cfg"]
    magic_cfg = f["magic_cfg"]
    kindness_cfg = f["kindness_cfg"]
    provoke_cfg = f["provoke_cfg"]
    place_cfg = f["place_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child standing watch at {place_cfg.label}, and {elder.id}, the old keeper. They are trying to protect {ward_cfg.phrase} through a sacred change."
        ),
        (
            "What was the sacred creature waiting to do?",
            f"It was waiting to make a transition from a {ward_cfg.stage_before} into a {ward_cfg.stage_after}. That change could only finish safely if the little creature stayed calm and unharmed."
        ),
        (
            f"Why did {elder.id} warn {child.id} not to provoke the hunter?",
            f"{elder.id} knew the hungry beast might try to devour the holy creature if anger was stirred up. The warning mattered because the sacred creature was weak while its transition was not finished."
        ),
    ]
    if provoke_cfg.strength > 0:
        qa.append((
            f"What did {child.id} do that could provoke the hunter?",
            f"{child.id} let fear make a noisy or sharp move: {provoke_cfg.phrase}. That could feel like a challenge to a hungry beast and make the danger worse."
        ))
    else:
        qa.append((
            f"Did {child.id} provoke the hunter?",
            f"No. {child.id} remembered the warning and kept still instead of provoking it. That gentle beginning helped keep the holy place calm."
        ))
    if f["outcome"] == "peaceful":
        qa.append((
            f"How did {child.id} keep the creature safe?",
            f"{child.pronoun().capitalize()} used {kindness_cfg.label} and {magic_cfg.label} without letting fear rule the moment. Because the hunter was not stirred into anger, the transition could unfold peacefully."
        ))
    elif f["outcome"] == "saved":
        qa.append((
            f"How did {child.id} save the sacred creature?",
            f"{child.pronoun().capitalize()} answered danger with {kindness_cfg.qa_text} and then {magic_cfg.qa_text}. Those two choices calmed the hunter and steadied the holy body before it could be devoured."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended sadly: {threat_cfg.label} devoured the holy {ward_cfg.stage_before}, and the sacred transition never finished. The child still learned that kindness must come before anger grows too large."
        ))
    if f["outcome"] != "devoured":
        qa.append((
            "What changed at the end?",
            f"The fragile creature became what it was meant to be: a {ward_cfg.stage_after}. The ending image proves the danger has passed because the holy change finally shines in the open."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"transition", "magic", "kindness", "devour", "provoke"}
    tags |= set(f["ward_cfg"].tags)
    tags |= set(f["threat_cfg"].tags)
    tags |= set(f["magic_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moon_orchard",
        ward="moon_moth",
        threat="bat_king",
        magic="moon_chime",
        kindness="reed_song",
        provoke="bow_head",
        name="Ione",
        gender="girl",
        elder="woman",
        trait="gentle",
        delay=0,
        seed=None,
    ),
    StoryParams(
        place="reed_delta",
        ward="river_dragon",
        threat="white_heron",
        magic="shell_flute",
        kindness="reed_song",
        provoke="clap",
        name="Ari",
        gender="boy",
        elder="man",
        trait="steady",
        delay=0,
        seed=None,
    ),
    StoryParams(
        place="laurel_hill",
        ward="dawn_fawn",
        threat="shadow_fox",
        magic="temple_lamp",
        kindness="milk_bowl",
        provoke="taunt",
        name="Mira",
        gender="girl",
        elder="woman",
        trait="brave",
        delay=2,
        seed=None,
    ),
    StoryParams(
        place="moon_orchard",
        ward="dawn_fawn",
        threat="shadow_fox",
        magic="sun_thread",
        kindness="fig_offering",
        provoke="pebble",
        name="Theron",
        gender="boy",
        elder="man",
        trait="patient",
        delay=0,
        seed=None,
    ),
]


def explain_combo(place_id: str, ward_id: str, threat_id: str) -> str:
    place = PLACES[place_id]
    ward = WARDS[ward_id]
    threat = THREATS[threat_id]
    if ward_id not in place.wards:
        return f"(No story: {ward.phrase} does not belong at {place.label}.)"
    if threat_id not in place.threats:
        return f"(No story: {threat.label} does not prowl {place.label}.)"
    return f"(No story: {threat.label} would not truly hunt {ward.phrase}, so there is no honest devour-risk.)"


def explain_magic(ward_id: str, magic_id: str) -> str:
    return f"(No story: {MAGIC[magic_id].label} does not guide the transition of {WARDS[ward_id].phrase}.)"


def explain_kindness(threat_id: str, kindness_id: str) -> str:
    return f"(No story: {KINDNESS[kindness_id].label} is not the kind of kindness that calms {THREATS[threat_id].label} here.)"


def explain_provoke(place_id: str, provoke_id: str) -> str:
    return f"(No story: {PROVOKES[provoke_id].label} is not a fitting action at {PLACES[place_id].label}.)"


ASP_RULES = r"""
% --- basic fit --------------------------------------------------------------
hazard(W, T) :- vulnerable(W, T).
valid(P, W, T) :- place(P), ward(W), threat(T), hosts_ward(P, W), hosts_threat(P, T), hazard(W, T).

good_magic(W, M) :- ward_magic(W, M), magic_for(M, W), magic_steady(M, S), S >= 1.
good_kindness(T, K) :- threat_kindness(T, K), kindness_for(K, T), kindness_power(K, S), sense_min(M), S >= M.
good_provoke(P, Pr) :- provoke(Pr), provoke_place(Pr, P).

% --- outcome model ----------------------------------------------------------
risk(R) :- chosen_threat(T), chosen_provoke(Pr), chosen_delay(D),
           threat_appetite(T, A), provoke_strength(Pr, P), R = A + P + D.
safety(S) :- chosen_ward(W), chosen_magic(M), chosen_kindness(K),
             good_magic(W, M), good_kindness(chosen_t(T), K),
             magic_steady(M, MS), kindness_power(K, KS), S = MS + KS.
chosen_t(T) :- chosen_threat(T).

outcome(peaceful) :- chosen_provoke(Pr), provoke_strength(Pr, 0).
outcome(saved) :- not outcome(peaceful), risk(R), safety(S), S >= R.
outcome(devoured) :- not outcome(peaceful), risk(R), safety(S), S < R.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for wid in sorted(place.wards):
            lines.append(asp.fact("hosts_ward", pid, wid))
        for tid in sorted(place.threats):
            lines.append(asp.fact("hosts_threat", pid, tid))
    for wid, ward in WARDS.items():
        lines.append(asp.fact("ward", wid))
        for tid in sorted(ward.vulnerable_to):
            lines.append(asp.fact("vulnerable", wid, tid))
        for mid in sorted(ward.magic_ok):
            lines.append(asp.fact("ward_magic", wid, mid))
    for tid, threat in THREATS.items():
        lines.append(asp.fact("threat", tid))
        lines.append(asp.fact("threat_appetite", tid, threat.appetite))
        for kid in sorted(threat.kindness_ok):
            lines.append(asp.fact("threat_kindness", tid, kid))
    for mid, magic in MAGIC.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("magic_steady", mid, magic.steady))
        for wid in sorted(magic.wards):
            lines.append(asp.fact("magic_for", mid, wid))
    for kid, kindness in KINDNESS.items():
        lines.append(asp.fact("kindness", kid))
        lines.append(asp.fact("kindness_power", kid, kindness.power))
        for tid in sorted(kindness.threats):
            lines.append(asp.fact("kindness_for", kid, tid))
    for prid, provoke in PROVOKES.items():
        lines.append(asp.fact("provoke", prid))
        lines.append(asp.fact("provoke_strength", prid, provoke.strength))
        for pid in sorted(provoke.places):
            lines.append(asp.fact("provoke_place", prid, pid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_magic_for(ward_id: str) -> list[str]:
    import asp

    extra = asp.fact("chosen_ward", ward_id)
    model = asp.one_model(asp_program(extra, "#show good_magic/2."))
    return sorted(m for w, m in asp.atoms(model, "good_magic") if w == ward_id)


def asp_kindness_for(threat_id: str) -> list[str]:
    import asp

    extra = asp.fact("chosen_threat", threat_id)
    model = asp.one_model(asp_program(extra, "#show good_kindness/2."))
    return sorted(k for t, k in asp.atoms(model, "good_kindness") if t == threat_id)


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_ward", params.ward),
        asp.fact("chosen_threat", params.threat),
        asp.fact("chosen_magic", params.magic),
        asp.fact("chosen_kindness", params.kindness),
        asp.fact("chosen_provoke", params.provoke),
        asp.fact("chosen_delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    for wid in WARDS:
        py = set(sensible_magic_for(wid))
        cl = set(asp_magic_for(wid))
        if py != cl:
            rc = 1
            print(f"MISMATCH in magic choices for {wid}: python={sorted(py)} clingo={sorted(cl)}")
    if rc == 0:
        print("OK: sensible magic choices match.")

    for tid in THREATS:
        py = set(sensible_kindness_for(tid))
        cl = set(asp_kindness_for(tid))
        if py != cl:
            rc = 1
            print(f"MISMATCH in kindness choices for {tid}: python={sorted(py)} clingo={sorted(cl)}")
    if rc == 0:
        print("OK: sensible kindness choices match.")

    cases = list(CURATED)
    for seed in range(80):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        resolve = resolve_params(build_parser().parse_args([]), random.Random(123))
        resolve.seed = 123
        smoke2 = generate(resolve)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke2, trace=False, qa=False)
        if not smoke.story or not smoke2.story:
            raise StoryError("smoke generation produced empty story text")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic storyworld: a child guards a magical transition from a hungry creature and answers danger with kindness."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ward", choices=WARDS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--kindness", choices=KINDNESS)
    ap.add_argument("--provoke", choices=PROVOKES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["woman", "man"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how many heartbeats fear delays the child's answer")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story cores derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.ward and args.threat:
        if not (place_hosts(args.place, args.ward, args.threat) and hazard_at_risk(args.ward, args.threat)):
            raise StoryError(explain_combo(args.place, args.ward, args.threat))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.ward is None or combo[1] == args.ward)
        and (args.threat is None or combo[2] == args.threat)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, ward_id, threat_id = rng.choice(combos)

    if args.magic is not None and not magic_fits(ward_id, args.magic):
        raise StoryError(explain_magic(ward_id, args.magic))
    magic_choices = sensible_magic_for(ward_id)
    if not magic_choices:
        raise StoryError(f"(No story: there is no fitting magic for {WARDS[ward_id].phrase}.)")
    magic_id = args.magic or rng.choice(magic_choices)

    if args.kindness is not None and not kindness_fits(threat_id, args.kindness):
        raise StoryError(explain_kindness(threat_id, args.kindness))
    kindness_choices = sensible_kindness_for(threat_id)
    if not kindness_choices:
        raise StoryError(f"(No story: there is no fitting kindness for {THREATS[threat_id].label}.)")
    kindness_id = args.kindness or rng.choice(kindness_choices)

    provoke_pool = [pid for pid in PROVOKES if provoke_fits(place_id, pid)]
    if args.provoke is not None and not provoke_fits(place_id, args.provoke):
        raise StoryError(explain_provoke(place_id, args.provoke))
    provoke_id = args.provoke or rng.choice(sorted(provoke_pool))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    elder = args.elder or rng.choice(["woman", "man"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place_id,
        ward=ward_id,
        threat=threat_id,
        magic=magic_id,
        kindness=kindness_id,
        provoke=provoke_id,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
        delay=delay,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.ward not in WARDS or params.threat not in THREATS:
        raise StoryError("(Invalid story parameters: unknown place, ward, or threat.)")
    if params.magic not in MAGIC or params.kindness not in KINDNESS or params.provoke not in PROVOKES:
        raise StoryError("(Invalid story parameters: unknown magic, kindness, or provoke choice.)")
    if not (place_hosts(params.place, params.ward, params.threat) and hazard_at_risk(params.ward, params.threat)):
        raise StoryError(explain_combo(params.place, params.ward, params.threat))
    if not magic_fits(params.ward, params.magic):
        raise StoryError(explain_magic(params.ward, params.magic))
    if not kindness_fits(params.threat, params.kindness):
        raise StoryError(explain_kindness(params.threat, params.kindness))
    if not provoke_fits(params.place, params.provoke):
        raise StoryError(explain_provoke(params.place, params.provoke))

    world = tell(
        place_cfg=PLACES[params.place],
        ward_cfg=WARDS[params.ward],
        threat_cfg=THREATS[params.threat],
        magic_cfg=MAGIC[params.magic],
        kindness_cfg=KINDNESS[params.kindness],
        provoke_cfg=PROVOKES[params.provoke],
        child_name=params.name,
        child_gender=params.gender,
        elder_type=params.elder,
        trait=params.trait,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in pair_answer_lines(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("", "#show valid/3.\n#show good_magic/2.\n#show good_kindness/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, ward, threat) combos:\n")
        for place_id, ward_id, threat_id in combos:
            print(
                f"  {place_id:12} {ward_id:12} {threat_id:12}  "
                f"[magic: {', '.join(asp_magic_for(ward_id))}; kindness: {', '.join(asp_kindness_for(threat_id))}]"
            )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.ward} at {p.place} ({p.threat}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
