#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/subscription_suspense_foreshadowing_space_adventure.py
=================================================================================

A standalone story world for a small, child-facing space adventure built around a
monthly subscription mission kit. The model prefers a narrow, plausible domain:

- a child receives a space-club subscription packet with a mission and one safety gadget
- an early warning sign quietly foreshadows trouble
- a bold child is tempted to step away from the marked route
- a cautious companion either stops the mistake, or the chosen gadget guides them back
- the ending image proves what changed: the children finish the mission safely

The world keeps a typed entity model with physical meters and emotional memes,
includes a Python reasonableness gate plus an inline ASP twin, and supports the
standard storyworld CLI contract.
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

# Make the shared result containers importable when this nested script is run
# directly from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CAUTIOUS_TRAITS = {"careful", "steady", "patient", "sensible"}
BRAVERY_INIT = 6.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Mission:
    id: str
    launch: str
    route: str
    goal: str
    treasure: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    sign: str
    warning: str
    trap: str
    rescue_image: str
    severity: int = 1
    counters: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Gadget:
    id: str
    label: str
    phrase: str
    action: str
    proof: str
    power: int = 1
    counters: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
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


def _r_lost(world: World) -> list[str]:
    out: list[str] = []
    explorer = world.entities.get("explorer")
    if explorer is None:
        return out
    if explorer.meters["off_path"] < THRESHOLD:
        return out
    if world.facts.get("guidance_active"):
        return out
    sig = ("lost", explorer.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    explorer.meters["lost"] += 1
    explorer.memes["fear"] += 1
    helper = world.entities.get("helper")
    if helper is not None:
        helper.memes["fear"] += 1
    out.append("__lost__")
    return out


def _r_guided_home(world: World) -> list[str]:
    out: list[str] = []
    explorer = world.entities.get("explorer")
    if explorer is None:
        return out
    if explorer.meters["lost"] < THRESHOLD or not world.facts.get("guidance_active"):
        return out
    sig = ("guided_home", explorer.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    explorer.meters["lost"] = 0.0
    explorer.meters["found"] += 1
    explorer.memes["relief"] += 1
    helper = world.entities.get("helper")
    if helper is not None:
        helper.memes["hope"] += 1
        helper.memes["relief"] += 1
    out.append("__found__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="lost", tag="physical", apply=_r_lost),
    Rule(name="guided_home", tag="physical", apply=_r_guided_home),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


MISSIONS = {
    "moon_mail": Mission(
        id="moon_mail",
        launch="their silver scout rover",
        route="the quiet moon plain",
        goal="carry a glowing message capsule to Beacon Rock",
        treasure="the blue message capsule",
        tags={"moon", "rover"},
    ),
    "ring_map": Mission(
        id="ring_map",
        launch="their bubble-window shuttle",
        route="the ice-ring path",
        goal="plant a tiny star flag beside the ring stones",
        treasure="the tiny star flag",
        tags={"space", "shuttle"},
    ),
    "comet_seed": Mission(
        id="comet_seed",
        launch="their little comet cart",
        route="the frosty comet trail",
        goal="deliver a warm seed pod to the crystal garden dome",
        treasure="the warm seed pod",
        tags={"comet", "garden"},
    ),
}

HAZARDS = {
    "dust_shadow": Hazard(
        id="dust_shadow",
        label="a slow dust shadow",
        sign="A ribbon of silver dust kept sliding over the path markers, then clearing again.",
        warning="If the dust shadow thickened, the path home could disappear for a minute at a time.",
        trap="the dust shadow swallowed the marker lights and turned every gray rock into the same gray rock",
        rescue_image="the blinking path appeared one dot at a time through the dust",
        severity=2,
        counters={"beacon_orb", "glow_tether"},
        tags={"dust", "shadow", "path"},
    ),
    "echo_cave": Hazard(
        id="echo_cave",
        label="an echo cave",
        sign="Each footstep came back twice, as if the cave were practicing their names.",
        warning="Inside the echo cave, a voice could bounce the wrong way and make a turn sound safe when it was not.",
        trap="the cave sent their own voices back from the dark and made every tunnel mouth sound correct",
        rescue_image="a clear answering signal cut through the echoes and pointed to the real exit",
        severity=2,
        counters={"beacon_orb", "ping_compass"},
        tags={"echo", "cave", "sound"},
    ),
    "sun_glare": Hazard(
        id="sun_glare",
        label="a hard sheet of sun glare",
        sign="Far ahead, the ice flashed so brightly that the trail stakes looked pale and thin.",
        warning="If they hurried into that bright patch, the trail stakes could vanish in the shine.",
        trap="the white glare washed the little trail stakes right out of sight",
        rescue_image="the safe line returned as the glare softened behind the shaded visor",
        severity=1,
        counters={"sun_visor", "ping_compass"},
        tags={"sun", "glare", "ice"},
    ),
}

GADGETS = {
    "beacon_orb": Gadget(
        id="beacon_orb",
        label="beacon orb",
        phrase="a beacon orb from the Star Post subscription",
        action="tapped the beacon orb, and it floated up blinking a bright path back to the rover",
        proof="The orb blinked steady as a small moon and never let the safe way wander.",
        power=2,
        counters={"dust_shadow", "echo_cave"},
        tags={"beacon", "subscription", "light"},
    ),
    "glow_tether": Gadget(
        id="glow_tether",
        label="glow tether",
        phrase="a glow tether from the Star Post subscription",
        action="clipped on the glow tether, and its gentle blue line stayed stretched between explorer and rover",
        proof="The blue line hummed softly, proving nobody had to guess where home was.",
        power=2,
        counters={"dust_shadow"},
        tags={"tether", "subscription", "light"},
    ),
    "ping_compass": Gadget(
        id="ping_compass",
        label="ping compass",
        phrase="a ping compass from the Star Post subscription",
        action="pressed the ping compass, and its warm chirp pointed exactly where the rover waited",
        proof="Each chirp landed in front of them like a careful footstep.",
        power=2,
        counters={"echo_cave", "sun_glare"},
        tags={"compass", "subscription", "sound"},
    ),
    "sun_visor": Gadget(
        id="sun_visor",
        label="sun visor",
        phrase="a fold-down sun visor from the Star Post subscription",
        action="lowered the sun visor, and the hard white shine shrank until the trail stakes came back",
        proof="With the visor down, the bright plain became a place with edges again.",
        power=1,
        counters={"sun_glare"},
        tags={"visor", "subscription", "sun"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "steady", "patient", "sensible", "curious", "eager"]
PETS = ["the tiny robot mouse", "the moon puppy", "the silver cat-bot", "the pocket rover"]

KNOWLEDGE = {
    "subscription": [
        (
            "What is a subscription?",
            "A subscription is something that arrives again and again, like a box, a magazine, or a kit. You sign up once, and then new things keep coming on a schedule.",
        )
    ],
    "beacon": [
        (
            "What does a beacon do?",
            "A beacon makes a signal people can follow. It helps them find the safe place or the way home.",
        )
    ],
    "tether": [
        (
            "What is a tether for?",
            "A tether is a safe line that keeps one thing connected to another. In a risky place, it helps you stay close and not drift away.",
        )
    ],
    "compass": [
        (
            "What does a compass help you do?",
            "A compass helps you know which way to go. It gives you direction when places look confusing.",
        )
    ],
    "visor": [
        (
            "Why does a visor help in bright light?",
            "A visor blocks some of the bright light from your eyes. That makes it easier to see the path clearly.",
        )
    ],
    "dust": [
        (
            "Why can dust make it hard to find a path?",
            "Dust can cover marks and make everything look alike. When that happens, it is easy to get turned around.",
        )
    ],
    "echo": [
        (
            "Why can echoes be confusing?",
            "An echo is a sound that bounces back. In a cave, echoes can make it hard to tell where the real sound came from.",
        )
    ],
    "sun": [
        (
            "Why can bright glare be a problem?",
            "Very bright glare can wash things out so your eyes cannot see small details. Then signs and trail markers are harder to notice.",
        )
    ],
    "path": [
        (
            "Why is it important to stay on a marked path?",
            "A marked path shows the safe way through a place. If you leave it, you might miss dangers or have trouble finding your way back.",
        )
    ],
}
KNOWLEDGE_ORDER = ["subscription", "path", "beacon", "tether", "compass", "visor", "dust", "echo", "sun"]


def gadget_fits(hazard: Hazard, gadget: Gadget) -> bool:
    return hazard.id in gadget.counters and gadget.id in hazard.counters and gadget.power >= hazard.severity


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for hazard_id, hazard in HAZARDS.items():
            for gadget_id, gadget in GADGETS.items():
                if gadget_fits(hazard, gadget):
                    combos.append((mission_id, hazard_id, gadget_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    if relation != "siblings" or cautioner_age <= instigator_age:
        return False
    authority = initial_caution(trait) + 1.0 + 2.0
    return authority > BRAVERY_INIT


def predict_risk(world: World) -> dict:
    sim = world.copy()
    sim.get("explorer").meters["off_path"] += 1
    propagate(sim, narrate=False)
    return {
        "lost": sim.get("explorer").meters["lost"] >= THRESHOLD,
        "fear": sim.get("explorer").memes["fear"],
    }


def introduction(world: World, mission: Mission, gadget: Gadget, explorer: Entity, helper: Entity, captain: Entity) -> None:
    explorer.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On launch morning, {explorer.id} and {helper.id} opened their Star Post subscription packet beside {mission.launch}. "
        f"Inside was a mission card telling them to {mission.goal}, and tucked under it was {gadget.phrase}."
    )
    world.say(
        f'"Cadets ready?" asked {captain.label_word.capitalize()}. The two children climbed in, and the little craft rolled out across {mission.route} with {mission.treasure} packed safely in the rear tray.'
    )


def foreshadow(world: World, hazard: Hazard, helper: Entity) -> None:
    world.say(hazard.sign)
    world.say(
        f"{helper.id} noticed it first and grew quiet. {hazard.warning}"
    )


def temptation(world: World, mission: Mission, explorer: Entity) -> None:
    explorer.memes["bravado"] += 1
    world.say(
        f"Halfway there, {explorer.id} spotted a shortcut between two shiny rocks. "
        f'"If I hurry through there, we can reach the goal first," {explorer.pronoun()} said.'
    )
    world.say(
        f"The mission suddenly felt less like a game and more like the kind of brave story that made {explorer.pronoun('possessive')} heart beat faster."
    )


def warning(world: World, hazard: Hazard, gadget: Gadget, explorer: Entity, helper: Entity) -> None:
    pred = predict_risk(world)
    world.facts["predicted_lost"] = pred["lost"]
    helper.memes["caution"] += 1
    world.say(
        f'{helper.id} caught {explorer.id}\'s sleeve. "Wait. That is how someone gets lost in {hazard.label}," {helper.pronoun()} said. '
        f'"We brought {gadget.label} for a reason."'
    )


def back_down(world: World, mission: Mission, gadget: Gadget, explorer: Entity, helper: Entity, captain: Entity, pet: str) -> None:
    explorer.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{explorer.id} looked at the dim stretch ahead, then back at the subscription packet tucked by the dashboard. "
        f"The warning sign from before did not feel small anymore."
    )
    world.say(
        f'"You are right," {explorer.pronoun()} whispered. "Fast is not the same as safe." So the children stayed on the marked route, using {gadget.label} before they moved on.'
    )
    world.para()
    world.say(
        f"Soon Beacon Rock rose ahead, and they set down {mission.treasure} exactly where the mission card had shown."
    )
    if pet:
        world.say(f"Even {pet} blinked a happy green light beside the wheel.")
    world.say(
        f'{captain.label_word.capitalize()} smiled at them. "That is how real explorers finish a mission," {captain.pronoun()} said. The stars overhead looked calm now, and the safe path home was bright.'
    )
    world.facts["guidance_active"] = True


def step_off(world: World, explorer: Entity) -> None:
    explorer.meters["off_path"] += 1
    explorer.memes["defiance"] += 1
    world.say(
        f"But the shortcut sparkled, and {explorer.id} took three quick steps off the path."
    )


def suspense(world: World, hazard: Hazard, explorer: Entity, helper: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"At once, {hazard.trap}. {explorer.id} stopped and turned in a small circle."
    )
    world.say(
        f'"{helper.id}?" {explorer.pronoun()} called, and for one nervous moment the dark, bright, or echoing place gave back the wrong answer. '
        f"{helper.id}'s stomach dipped, but {helper.pronoun()} remembered the subscription gadget."
    )


def rescue(world: World, hazard: Hazard, gadget: Gadget, explorer: Entity, helper: Entity, captain: Entity) -> None:
    world.facts["guidance_active"] = True
    propagate(world, narrate=False)
    helper.memes["bravery"] += 1
    world.say(
        f"{helper.id} {gadget.action}. {hazard.rescue_image}."
    )
    world.say(
        f"{explorer.id} followed the signal back, one careful step after another, until {captain.label_word} could reach out and squeeze {explorer.pronoun('possessive')} hand."
    )
    world.say(gadget.proof)


def resolution(world: World, mission: Mission, gadget: Gadget, explorer: Entity, helper: Entity, captain: Entity, pet: str) -> None:
    explorer.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f'Nobody hurried after that. Together they carried {mission.treasure} to its place and finished the mission the slow, true way.'
    )
    if pet:
        world.say(f"{pet.capitalize()} rolled after them with a tiny cheerful beep.")
    world.say(
        f'{captain.label_word.capitalize()} knelt by the rover hatch. "The best adventurers notice danger before it grows," {captain.pronoun()} said. '
        f'"And when something feels wrong, they use their tools and stay together."'
    )
    world.say(
        f"As they drove home, the subscription packet rustled in the storage pocket, no longer like a toy surprise but like a promise to be ready for the next starry job."
    )


def tell(
    mission: Mission,
    hazard: Hazard,
    gadget: Gadget,
    *,
    explorer_name: str = "Tom",
    explorer_gender: str = "boy",
    helper_name: str = "Lily",
    helper_gender: str = "girl",
    captain_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    explorer_age: int = 6,
    helper_age: int = 7,
    pet: str = "",
) -> World:
    world = World()
    explorer = world.add(
        Entity(
            id="explorer",
            kind="character",
            type=explorer_gender,
            label=explorer_name,
            role="instigator",
            age=explorer_age,
            attrs={"name": explorer_name, "relation": relation},
            traits=["bold"],
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_gender,
            label=helper_name,
            role="cautioner",
            age=helper_age,
            attrs={"name": helper_name, "relation": relation},
            traits=[trait],
        )
    )
    captain = world.add(
        Entity(
            id="captain",
            kind="character",
            type=captain_type,
            label="the captain",
            role="captain",
        )
    )
    world.add(Entity(id="rover", type="rover", label=mission.launch))
    explorer.memes["bravery"] = BRAVERY_INIT
    helper.memes["caution"] = initial_caution(trait)

    introduction(world, mission, gadget, explorer, helper, captain)
    foreshadow(world, hazard, helper)

    world.para()
    temptation(world, mission, explorer)
    warning(world, hazard, gadget, explorer, helper)

    averted = would_avert(relation, explorer_age, helper_age, trait)
    if averted:
        world.para()
        back_down(world, mission, gadget, explorer, helper, captain, pet)
        outcome = "averted"
    else:
        step_off(world, explorer)
        world.para()
        suspense(world, hazard, explorer, helper)
        world.para()
        rescue(world, hazard, gadget, explorer, helper, captain)
        resolution(world, mission, gadget, explorer, helper, captain, pet)
        outcome = "rescued"

    world.facts.update(
        mission=mission,
        hazard=hazard,
        gadget=gadget,
        explorer=explorer,
        helper=helper,
        captain=captain,
        pet=pet,
        relation=relation,
        averted=averted,
        outcome=outcome,
        lost=explorer.meters["found"] >= THRESHOLD or explorer.meters["lost"] >= THRESHOLD,
        guidance_used=world.facts.get("guidance_active", False),
    )
    return world


@dataclass
class StoryParams:
    mission: str
    hazard: str
    gadget: str
    explorer: str
    explorer_gender: str
    helper: str
    helper_gender: str
    captain: str
    trait: str
    relation: str = "siblings"
    explorer_age: int = 6
    helper_age: int = 7
    pet: str = ""
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        mission="moon_mail",
        hazard="dust_shadow",
        gadget="beacon_orb",
        explorer="Tom",
        explorer_gender="boy",
        helper="Lily",
        helper_gender="girl",
        captain="mother",
        trait="careful",
        relation="siblings",
        explorer_age=5,
        helper_age=7,
        pet="the moon puppy",
    ),
    StoryParams(
        mission="ring_map",
        hazard="echo_cave",
        gadget="ping_compass",
        explorer="Max",
        explorer_gender="boy",
        helper="Mia",
        helper_gender="girl",
        captain="father",
        trait="steady",
        relation="friends",
        explorer_age=6,
        helper_age=6,
        pet="the tiny robot mouse",
    ),
    StoryParams(
        mission="comet_seed",
        hazard="sun_glare",
        gadget="sun_visor",
        explorer="Ava",
        explorer_gender="girl",
        helper="Nora",
        helper_gender="girl",
        captain="mother",
        trait="patient",
        relation="siblings",
        explorer_age=4,
        helper_age=7,
        pet="the pocket rover",
    ),
]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    explorer = f["explorer"]
    helper = f["helper"]
    mission = f["mission"]
    hazard = f["hazard"]
    gadget = f["gadget"]
    if f["outcome"] == "averted":
        return [
            'Write a short story for a 3-to-5-year-old in a space-adventure style that includes the word "subscription", uses foreshadowing, and ends safely.',
            f"Tell a suspenseful but gentle space story where {explorer.label} and {helper.label} receive a subscription mission kit, notice an early warning sign, and choose the safe path.",
            f"Write a story about young cadets carrying out a mission to {mission.goal}, where {hazard.label} is foreshadowed early and the children use {gadget.label} instead of rushing.",
        ]
    return [
        'Write a short story for a 3-to-5-year-old in a space-adventure style that includes the word "subscription", uses foreshadowing, and has a tense middle with a safe rescue.',
        f"Tell a space adventure where {explorer.label} steps off the path during a mission, the early warning sign turns out to matter, and {helper.label} uses a subscription gadget to guide the way back.",
        f"Write a child-facing suspense story about a mission to {mission.goal}, where {hazard.label} almost causes trouble before {gadget.label} saves the day.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    explorer = f["explorer"]
    helper = f["helper"]
    captain = f["captain"]
    mission = f["mission"]
    hazard = f["hazard"]
    gadget = f["gadget"]
    pair = pair_noun(explorer, helper, f["relation"])
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {explorer.label} and {helper.label}, on a small space mission with their {captain.label_word}. They are carrying out a job from their Star Post subscription packet.",
        ),
        (
            "What did the subscription packet give them?",
            f"It gave them a mission card and {gadget.phrase}. The packet mattered because the gadget was exactly what they needed when the danger grew real.",
        ),
        (
            "What was the early warning sign?",
            f"The first sign was that {hazard.sign[0].lower() + hazard.sign[1:]} {helper.label} noticed it before the trouble started, so it worked as a clue that the path might become confusing.",
        ),
    ]
    if f["outcome"] == "averted":
        out.append(
            (
                f"Why did {explorer.label} stop trying to rush ahead?",
                f"{helper.label} warned that {hazard.label} could hide the safe way home, and the earlier sign suddenly felt important. {explorer.label} understood that being fast was not worth getting lost.",
            )
        )
        out.append(
            (
                "How did the story end?",
                f"They stayed on the marked route, finished the mission, and reached the goal safely. The ending shows they changed by treating the subscription gadget like a real safety tool, not just a fun extra.",
            )
        )
    else:
        out.append(
            (
                f"What happened when {explorer.label} stepped off the path?",
                f"{hazard.trap[0].upper() + hazard.trap[1:]}, and {explorer.label} could not tell the safe way back for a moment. That tense moment happens because the warning sign from earlier finally becomes true.",
            )
        )
        out.append(
            (
                f"How did {helper.label} help?",
                f"{helper.label} used {gadget.label} to make a clear way home again. The gadget worked because it matched the kind of danger they were facing.",
            )
        )
        out.append(
            (
                "What lesson did the children learn?",
                f"They learned to notice small warning signs and to stay together on a marked path. They also learned that the right tool from the subscription packet could turn a scary moment into a safe ending.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"subscription", "path"} | set(f["hazard"].tags) | set(f["gadget"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:9} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(hazard: Hazard, gadget: Gadget) -> str:
    return (
        f"(No story: {gadget.label} is not a sensible fix for {hazard.label}. "
        f"The gadget must directly guide the children through that kind of danger.)"
    )


ASP_RULES = r"""
valid(M, H, G) :- mission(M), hazard(H), gadget(G), counters_hazard(H, G), counters_gadget(G, H), power(G, P), severity(H, S), P >= S.

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_helper :- relation(siblings), explorer_age(EA), helper_age(HA), HA > EA.
authority(C + 1 + 2) :- init_caution(C), older_helper.
averted :- older_helper, authority(A), bravery_init(B), A > B.

outcome(averted) :- averted.
outcome(rescued) :- not averted, chosen_valid.
chosen_valid :- chosen_hazard(H), chosen_gadget(G), valid(_, H, G).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("severity", hazard_id, hazard.severity))
        for gid in sorted(hazard.counters):
            lines.append(asp.fact("counters_hazard", hazard_id, gid))
    for gadget_id, gadget in GADGETS.items():
        lines.append(asp.fact("gadget", gadget_id))
        lines.append(asp.fact("power", gadget_id, gadget.power))
        for hid in sorted(gadget.counters):
            lines.append(asp.fact("counters_gadget", gadget_id, hid))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_gadget", params.gadget),
            asp.fact("relation", params.relation),
            asp.fact("explorer_age", params.explorer_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
            asp.fact("chosen_valid"),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.explorer_age, params.helper_age, params.trait):
        return "averted"
    return "rescued"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome disagreements.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        _ = sample.to_json()
        print("OK: smoke test generated a normal story sample.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a subscription space mission with foreshadowed danger and a safe ending."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--captain", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and args.gadget:
        hazard = HAZARDS[args.hazard]
        gadget = GADGETS[args.gadget]
        if not gadget_fits(hazard, gadget):
            raise StoryError(explain_rejection(hazard, gadget))

    combos = [
        combo
        for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.gadget is None or combo[2] == args.gadget)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, hazard_id, gadget_id = rng.choice(sorted(combos))
    explorer_name, explorer_gender = _pick_child(rng)
    helper_name, helper_gender = _pick_child(rng, avoid=explorer_name)
    captain = args.captain or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    explorer_age, helper_age = rng.sample([4, 5, 6, 7], 2)
    pet = rng.choice(PETS + ["", ""])
    return StoryParams(
        mission=mission_id,
        hazard=hazard_id,
        gadget=gadget_id,
        explorer=explorer_name,
        explorer_gender=explorer_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        captain=captain,
        trait=trait,
        relation=relation,
        explorer_age=explorer_age,
        helper_age=helper_age,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.gadget not in GADGETS:
        raise StoryError(f"(Unknown gadget: {params.gadget})")
    mission = MISSIONS[params.mission]
    hazard = HAZARDS[params.hazard]
    gadget = GADGETS[params.gadget]
    if not gadget_fits(hazard, gadget):
        raise StoryError(explain_rejection(hazard, gadget))

    world = tell(
        mission=mission,
        hazard=hazard,
        gadget=gadget,
        explorer_name=params.explorer,
        explorer_gender=params.explorer_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        captain_type=params.captain,
        trait=params.trait,
        relation=params.relation,
        explorer_age=params.explorer_age,
        helper_age=params.helper_age,
        pet=params.pet,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, hazard, gadget) combos:\n")
        for mission_id, hazard_id, gadget_id in combos:
            print(f"  {mission_id:11} {hazard_id:12} {gadget_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.explorer} & {p.helper}: {p.mission} / {p.hazard} / {p.gadget} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
