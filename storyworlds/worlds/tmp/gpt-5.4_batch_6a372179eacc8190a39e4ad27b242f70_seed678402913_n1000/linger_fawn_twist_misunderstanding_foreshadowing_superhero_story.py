#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/linger_fawn_twist_misunderstanding_foreshadowing_superhero_story.py
================================================================================================

A standalone story world for a tiny superhero-style misunderstanding tale.

Premise
-------
A child in a pretend superhero mood notices a strange shape near dusk and jumps
to the wrong conclusion. Small clues quietly foreshadow the truth: a frightened
fawn is nearby. The child first mistakes a shadowy grown-up helper for a thief
or villain, then discovers the grown-up is trying to rescue the animal. The
child joins in, learns to look closely before accusing, and ends with a gentler
idea of what being heroic means.

This world models:
- physical state: stuck / scared / calm / open gate / lowered crate / etc.
- emotional state: alarm, embarrassment, relief, pride, trust
- foreshadowing facts recorded in the world state, not inferred from the prose
- a misunderstanding beat that can resolve only when the rescue facts line up
- a twist reveal: the feared "villain" was helping a fawn all along

Run it
------
python storyworlds/worlds/gpt-5.4/linger_fawn_twist_misunderstanding_foreshadowing_superhero_story.py
python storyworlds/worlds/gpt-5.4/linger_fawn_twist_misunderstanding_foreshadowing_superhero_story.py --place garden --snag ribbon --helper gardener
python storyworlds/worlds/gpt-5.4/linger_fawn_twist_misunderstanding_foreshadowing_superhero_story.py --snag drain_cover
python storyworlds/worlds/gpt-5.4/linger_fawn_twist_misunderstanding_foreshadowing_superhero_story.py --all
python storyworlds/worlds/gpt-5.4/linger_fawn_twist_misunderstanding_foreshadowing_superhero_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/linger_fawn_twist_misunderstanding_foreshadowing_superhero_story.py --verify
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
THIS = os.path.abspath(__file__)
STORYWORLDS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(THIS)))
sys.path.insert(0, STORYWORLDS_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "gardener_f", "neighbor_f"}
        male = {"boy", "father", "man", "gardener_m", "neighbor_m", "janitor_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {"mother": "mom", "father": "dad"}
        return mapping.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    shadow_spot: str
    ending_image: str
    affordances: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Snag:
    id: str
    label: str
    foreshadow: str
    danger_text: str
    reveal_text: str
    fix_method: str
    aftermath: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    title: str
    type: str
    silhouette: str
    kind_action: str
    gear: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Alarm:
    id: str
    suspect_name: str
    boast: str
    mistake_line: str
    correction_line: str
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


def _r_stuck_fawn_scared(world: World) -> list[str]:
    out: list[str] = []
    fawn = world.entities.get("fawn")
    if not fawn:
        return out
    if fawn.meters["stuck"] >= THRESHOLD and ("scared", "fawn") not in world.fired:
        world.fired.add(("scared", "fawn"))
        fawn.memes["fear"] += 1
        out.append("__fawn_scared__")
    return out


def _r_calm_after_help(world: World) -> list[str]:
    out: list[str] = []
    fawn = world.entities.get("fawn")
    child = world.entities.get("hero")
    if not fawn or not child:
        return out
    if (
        fawn.meters["freed"] >= THRESHOLD
        and fawn.memes["fear"] >= THRESHOLD
        and ("calm", "fawn") not in world.fired
    ):
        world.fired.add(("calm", "fawn"))
        fawn.memes["fear"] = 0.0
        fawn.memes["calm"] += 1
        child.memes["relief"] += 1
        out.append("__fawn_calm__")
    return out


def _r_truth_softens_child(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not child or not helper:
        return out
    if (
        child.meters["misunderstanding"] >= THRESHOLD
        and helper.meters["helping"] >= THRESHOLD
        and ("soften", child.id) not in world.fired
    ):
        world.fired.add(("soften", child.id))
        child.memes["embarrassment"] += 1
        child.memes["trust"] += 1
        out.append("__truth__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="stuck_fawn_scared", tag="physical", apply=_r_stuck_fawn_scared),
    Rule(name="calm_after_help", tag="emotional", apply=_r_calm_after_help),
    Rule(name="truth_softens_child", tag="social", apply=_r_truth_softens_child),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "garden": Place(
        id="garden",
        label="the community garden",
        opening="Behind the library, the community garden glowed green in the late light.",
        shadow_spot="behind the bean trellis",
        ending_image="the rows of beans stood still again, and the moon made silver stripes on the leaves",
        affordances={"ribbon", "crate"},
        tags={"garden"},
    ),
    "schoolyard": Place(
        id="schoolyard",
        label="the schoolyard",
        opening="After school, the playground had gone quiet except for a few leaves skittering by the fence.",
        shadow_spot="near the bike rack and the tall hedge",
        ending_image="the empty swings barely moved, and the last pink light rested on the blacktop",
        affordances={"ribbon", "gate"},
        tags={"school"},
    ),
    "park_edge": Place(
        id="park_edge",
        label="the edge of the park",
        opening="At the edge of the park, the path curled beside bushes that looked dark and secret in the evening.",
        shadow_spot="beside the berry bushes",
        ending_image="the path turned quiet, and the lantern glow from the park gate looked warm instead of spooky",
        affordances={"gate", "crate"},
        tags={"park"},
    ),
}

SNAGS = {
    "ribbon": Snag(
        id="ribbon",
        label="a shiny ribbon tangled around one slim leg",
        foreshadow="Something pale seemed to linger on a low branch, fluttering whenever the wind breathed through it.",
        danger_text="The ribbon held the little animal in one place, and every tug only tightened it more.",
        reveal_text="A tiny fawn stood there, trembling, with a birthday ribbon tangled around one slim leg.",
        fix_method="worked the ribbon loose with slow fingers while the child kept still and quiet",
        aftermath="When the knot slipped free, the fawn tested one hoof and then another.",
        needs={"gentle_hands"},
        tags={"ribbon", "gentle"},
    ),
    "gate": Snag(
        id="gate",
        label="one front hoof caught between the bars of a narrow side gate",
        foreshadow="Along the dirt were small pointed prints, too neat to be a dog and too light to be a person.",
        danger_text="The fawn could not pull backward without scraping its leg, and it could not step forward until the gate moved.",
        reveal_text="A small fawn had pushed too far into the side gate, and one front hoof was caught between the bars.",
        fix_method="lifted the latch and swung the gate wide while the child talked in a soft voice",
        aftermath="As the gate opened, the fawn pulled free in one quick, shaky hop.",
        needs={"open_gate"},
        tags={"gate", "gentle"},
    ),
    "crate": Snag(
        id="crate",
        label="a tipped wooden berry crate resting over its shoulders",
        foreshadow="Near the bushes lay nibbled leaves and one little brown hair caught on a splintered crate.",
        danger_text="The crate was light enough to move but awkward enough to keep the fawn from turning around.",
        reveal_text="Under the shadow was a frightened fawn with a wooden berry crate tipped over its shoulders.",
        fix_method="raised the crate carefully while the child drew the cape away so nothing brushed the fawn's eyes",
        aftermath="Once the crate lifted clear, the fawn blinked and stood very still for a beat.",
        needs={"lift_light"},
        tags={"crate", "gentle"},
    ),
}

HELPERS = {
    "gardener": Helper(
        id="gardener",
        title="gardener",
        type="gardener_f",
        silhouette="a bent figure in a wide straw hat",
        kind_action="was reaching slowly because quick motions would scare the animal more",
        gear={"gentle_hands", "lift_light"},
        tags={"gardener"},
    ),
    "janitor": Helper(
        id="janitor",
        title="janitor",
        type="janitor_m",
        silhouette="a broad shape with a ring of keys that clicked softly",
        kind_action="was crouching there to see what was trapped without making the poor thing panic",
        gear={"open_gate", "lift_light"},
        tags={"janitor"},
    ),
    "neighbor": Helper(
        id="neighbor",
        title="neighbor",
        type="neighbor_m",
        silhouette="a coat-shaped shadow with a small flashlight pointed at the ground",
        kind_action="kept the light low and gentle so the frightened animal would not bolt",
        gear={"gentle_hands", "open_gate"},
        tags={"neighbor"},
    ),
}

ALARMS = {
    "thief": Alarm(
        id="thief",
        suspect_name="the Shade Snatcher",
        boast="Tonight I stop the Shade Snatcher!",
        mistake_line="The child was sure the shadowy grown-up must be sneaking around for trouble.",
        correction_line="The twist stung at first: the shadowy grown-up was not stealing anything at all.",
        tags={"misunderstanding"},
    ),
    "monster": Alarm(
        id="monster",
        suspect_name="the Bush Monster",
        boast="Stand back! I can handle the Bush Monster!",
        mistake_line="With the cape flapping behind, the child decided the shape in the dusk had to be a monster from the bushes.",
        correction_line="Then the truth came clear: there had never been a monster there.",
        tags={"misunderstanding"},
    ),
    "villain": Alarm(
        id="villain",
        suspect_name="Doctor Gloom",
        boast="No one scares this town while I am on watch!",
        mistake_line="The dim shape, the hush, and the bent back all looked villainish to the child for one hot second.",
        correction_line="But the supposed villain had only been trying to help.",
        tags={"misunderstanding"},
    ),
}

GIRL_NAMES = ["Maya", "Zoe", "Lily", "Ava", "Nora", "Ella", "Ruby", "Mina"]
BOY_NAMES = ["Leo", "Finn", "Max", "Sam", "Eli", "Noah", "Theo", "Jack"]
TRAITS = ["brave", "eager", "watchful", "dramatic", "kind", "quick"]
POWER_NAMES = ["Comet Kid", "Moon Mask", "Captain Bright", "Whirlwind", "Star Cape"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for snag_id in sorted(place.affordances):
            snag = SNAGS[snag_id]
            for helper_id, helper in HELPERS.items():
                if snag.needs.issubset(helper.gear):
                    combos.append((place_id, snag_id, helper_id))
    return sorted(combos)


def combo_reasonable(place_id: str, snag_id: str, helper_id: str) -> bool:
    if place_id not in PLACES or snag_id not in SNAGS or helper_id not in HELPERS:
        return False
    place = PLACES[place_id]
    snag = SNAGS[snag_id]
    helper = HELPERS[helper_id]
    return snag_id in place.affordances and snag.needs.issubset(helper.gear)


def explain_rejection(place: Place, snag: Snag, helper: Helper) -> str:
    if snag.id not in place.affordances:
        return (
            f"(No story: {place.label} is not a plausible place for the {snag.id} rescue setup. "
            f"Pick a snag that fits the location.)"
        )
    if not snag.needs.issubset(helper.gear):
        need = ", ".join(sorted(snag.needs))
        have = ", ".join(sorted(helper.gear))
        return (
            f"(No story: a {helper.title} here lacks the rescue ability needed for this snag. "
            f"The snag needs {{{need}}}, but this helper offers {{{have}}}.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_truth(world: World) -> dict:
    sim = world.copy()
    helper = sim.get("helper")
    child = sim.get("hero")
    fawn = sim.get("fawn")
    child.meters["misunderstanding"] += 1
    helper.meters["helping"] += 1
    propagate(sim, narrate=False)
    return {
        "helper_helping": helper.meters["helping"] >= THRESHOLD,
        "fawn_scared": fawn.memes["fear"] >= THRESHOLD,
        "child_softens": child.memes["trust"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, place: Place) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{place.opening} {child.id} hurried along in a red towel-cape, feeling exactly like {child.attrs['hero_name']}."
    )
    world.say(
        f"{child.pronoun().capitalize()} liked to patrol slowly enough for little mysteries to linger in the corners of the day."
    )


def foreshadow(world: World, child: Entity, place: Place, snag: Snag) -> None:
    world.say(
        f"Near {place.shadow_spot}, {snag.foreshadow}"
    )
    world.say(
        f"{child.id} heard a small rustle after that, not loud enough to understand, only sad enough to make {child.pronoun('object')} stop."
    )
    world.facts["foreshadow_seen"] = True


def mistake_shadow(world: World, child: Entity, helper: Entity, alarm: Alarm) -> None:
    child.meters["misunderstanding"] += 1
    child.memes["alarm"] += 1
    world.say(
        f"There in the dimness moved {helper.attrs['silhouette']}. {alarm.mistake_line}"
    )
    world.say(f'"{alarm.boast}"')
    propagate(world, narrate=False)


def approach(world: World, child: Entity, helper: Entity) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} marched closer, but the closer {child.pronoun()} came, the stranger the scene looked."
    )
    world.say(
        f"The shadowy grown-up was not grabbing treasure or hiding loot. {helper.pronoun().capitalize()} {helper.attrs['kind_action']}."
    )


def reveal_twist(world: World, child: Entity, helper: Entity, fawn: Entity, snag: Snag, alarm: Alarm) -> None:
    helper.meters["helping"] += 1
    fawn.meters["stuck"] += 1
    propagate(world, narrate=False)
    pred = predict_truth(world)
    world.facts["pred_child_softens"] = pred["child_softens"]
    world.say(
        f"Then the real trouble showed itself. {snag.reveal_text}"
    )
    world.say(
        f"{alarm.correction_line} The hidden shape in the dusk was a fawn, not a foe."
    )
    world.say(
        f'"Easy there," the {helper.label} whispered. "{snag.danger_text}"'
    )


def child_apology(world: World, child: Entity, helper: Entity) -> None:
    child.memes["embarrassment"] += 1
    world.say(
        f'{child.id} felt hot in the cheeks. "I thought you were the bad guy," {child.pronoun()} admitted.'
    )
    world.say(
        f'The {helper.label} gave a small smile. "Looking first is part of being brave," {helper.pronoun()} said.'
    )


def rescue(world: World, child: Entity, helper: Entity, fawn: Entity, snag: Snag) -> None:
    world.say(
        f"So {child.id} took one slow breath and did the hardest superhero thing of all: {child.pronoun()} listened."
    )
    world.say(
        f"Together they {snag.fix_method}."
    )
    fawn.meters["stuck"] = 0.0
    fawn.meters["freed"] += 1
    child.memes["care"] += 1
    helper.meters["helping"] += 1
    propagate(world, narrate=False)
    world.say(snag.aftermath)


def release(world: World, child: Entity, fawn: Entity, place: Place) -> None:
    world.say(
        f"For one heartbeat the fawn did not run. It seemed to linger beside the bushes, ears tipped forward as if listening to the kind voices."
    )
    world.say(
        f"Then it gave one light spring into the shadows and was gone."
    )
    child.memes["wonder"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{place.ending_image}. {child.id} held still and felt more superheroish than before, only softer now."
    )


def ending_lesson(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f'"Next time," {child.id} said, tugging the cape straight, "I will look twice before I shout at the shadows."'
    )
    world.say(
        f'"That," said the {helper.label}, "is how real heroes help."'
    )


def tell(
    place: Place,
    snag: Snag,
    helper_cfg: Helper,
    alarm: Alarm,
    *,
    child_name: str = "Leo",
    child_type: str = "boy",
    parent_type: str = "mother",
    trait: str = "brave",
    hero_name: str = "Comet Kid",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id="hero",
            kind="character",
            type=child_type,
            label=child_name,
            phrase=child_name,
            role="hero",
            traits=[trait],
            attrs={"hero_name": hero_name},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.title,
            role="helper",
            attrs={"silhouette": helper_cfg.silhouette, "kind_action": helper_cfg.kind_action},
            tags=set(helper_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    fawn = world.add(
        Entity(
            id="fawn",
            kind="thing",
            type="fawn",
            label="fawn",
            phrase="the little fawn",
            role="animal",
            tags={"fawn"},
        )
    )

    world.facts.update(
        place=place,
        snag=snag,
        helper_cfg=helper_cfg,
        alarm=alarm,
        child=child,
        helper=helper,
        fawn=fawn,
    )

    introduce(world, child, place)
    foreshadow(world, child, place, snag)

    world.para()
    mistake_shadow(world, child, helper, alarm)
    approach(world, child, helper)
    reveal_twist(world, child, helper, fawn, snag, alarm)

    world.para()
    child_apology(world, child, helper)
    rescue(world, child, helper, fawn, snag)

    world.para()
    ending_lesson(world, child, helper)
    release(world, child, fawn, place)

    world.facts.update(
        misunderstanding=child.meters["misunderstanding"] >= THRESHOLD,
        twist_revealed=helper.meters["helping"] >= THRESHOLD and fawn.meters["freed"] >= THRESHOLD,
        freed=fawn.meters["freed"] >= THRESHOLD,
        child_learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    snag: str
    helper: str
    alarm: str
    name: str
    gender: str
    parent: str
    trait: str
    hero_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="garden",
        snag="ribbon",
        helper="gardener",
        alarm="villain",
        name="Maya",
        gender="girl",
        parent="mother",
        trait="watchful",
        hero_name="Captain Bright",
    ),
    StoryParams(
        place="schoolyard",
        snag="gate",
        helper="janitor",
        alarm="monster",
        name="Leo",
        gender="boy",
        parent="father",
        trait="dramatic",
        hero_name="Moon Mask",
    ),
    StoryParams(
        place="park_edge",
        snag="crate",
        helper="gardener",
        alarm="thief",
        name="Nora",
        gender="girl",
        parent="mother",
        trait="kind",
        hero_name="Star Cape",
    ),
    StoryParams(
        place="schoolyard",
        snag="ribbon",
        helper="neighbor",
        alarm="thief",
        name="Finn",
        gender="boy",
        parent="father",
        trait="eager",
        hero_name="Comet Kid",
    ),
    StoryParams(
        place="park_edge",
        snag="gate",
        helper="neighbor",
        alarm="villain",
        name="Ruby",
        gender="girl",
        parent="mother",
        trait="brave",
        hero_name="Whirlwind",
    ),
]


KNOWLEDGE = {
    "fawn": [
        (
            "What is a fawn?",
            "A fawn is a baby deer. It has thin legs, quick ears, and often freezes when it is frightened."
        )
    ],
    "gentle": [
        (
            "Why should people move gently around a scared wild animal?",
            "A scared animal may kick, run, or hurt itself trying to escape. Slow, quiet movements help it feel safer."
        )
    ],
    "gate": [
        (
            "Why can a narrow gate be dangerous for an animal?",
            "An animal can put a leg or hoof into a gap that is easy to enter but hard to pull back out of. Then the animal may get stuck and panic."
        )
    ],
    "ribbon": [
        (
            "Why can ribbon be a problem outside?",
            "Ribbon can twist around a leg or branch and tighten when something pulls on it. Even pretty things can become dangerous litter."
        )
    ],
    "crate": [
        (
            "What is a wooden crate?",
            "A wooden crate is a light box used to carry fruit or other things. If it tips over, a small animal can get trapped under it."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks they know what is going on, but they are wrong. Looking carefully and listening can fix it."
        )
    ],
    "hero": [
        (
            "What can make someone a real hero?",
            "A real hero does not just rush in loudly. A real hero notices what is true and helps in the kindest useful way."
        )
    ],
}
KNOWLEDGE_ORDER = ["fawn", "gentle", "gate", "ribbon", "crate", "misunderstanding", "hero"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    snag = f["snag"]
    alarm = f["alarm"]
    return [
        (
            f'Write a short superhero-style story for a 3-to-5-year-old that includes the words '
            f'"linger" and "fawn", uses foreshadowing and a misunderstanding, and ends with a twist in {place.label}.'
        ),
        (
            f"Tell a gentle superhero story where {child.label} mistakes a shadow for {alarm.suspect_name}, "
            f"but the real problem is {snag.label}."
        ),
        (
            "Write a child-facing story about a pretend hero learning that looking closely can be braver than making a loud guess."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    snag = f["snag"]
    alarm = f["alarm"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a child pretending to be {child.attrs['hero_name']}, and a {helper.label} trying to help a frightened fawn in {place.label}."
        ),
        (
            f"Why did {child.label} think something bad was happening?",
            f"{child.label} saw a strange shadow in the dusk and heard a sad rustle without understanding it yet. Because the scene looked spooky, {child.pronoun()} mistakenly imagined {alarm.suspect_name} instead of the truth."
        ),
        (
            "What clues foreshadowed the real problem?",
            f"Before the truth was shown, there were small clues near {place.shadow_spot}: {snag.foreshadow.lower()} Those details quietly pointed toward an animal problem before anyone said the word fawn."
        ),
        (
            "What was the twist?",
            f"The twist was that the shadowy grown-up was not a villain at all. The real trouble was a fawn that was stuck because {snag.label}."
        ),
        (
            f"How did {child.label} help in the end?",
            f"{child.label} stopped charging in and listened to the helper first. Then the two of them {snag.fix_method}, which freed the fawn without scaring it more."
        ),
        (
            f"What did {child.label} learn?",
            f"{child.label} learned that being heroic means looking carefully before accusing someone. The story ends with courage and kindness working together instead of loud guessing."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"fawn", "misunderstanding", "hero"}
    tags |= set(f["snag"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Reasonableness: a combo works when the place supports the snag and the helper
% has every capability the snag needs.
valid(P, S, H) :- place(P), snag(S), helper(H), affords(P, S), helper_has_all(H, S).
missing_need(H, S, N) :- needs(S, N), not helper_has(H, N), helper(H).
helper_has_all(H, S) :- helper(H), snag(S), not missing_need(H, S, _).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for snag_id in sorted(place.affordances):
            lines.append(asp.fact("affords", pid, snag_id))
    for sid, snag in SNAGS.items():
        lines.append(asp.fact("snag", sid))
        for need in sorted(snag.needs):
            lines.append(asp.fact("needs", sid, need))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for gear in sorted(helper.gear):
            lines.append(asp.fact("helper_has", hid, gear))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero misunderstanding that turns into a gentle animal rescue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--alarm", choices=ALARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero-name", choices=POWER_NAMES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.snag and args.helper:
        if not combo_reasonable(args.place, args.snag, args.helper):
            raise StoryError(explain_rejection(PLACES[args.place], SNAGS[args.snag], HELPERS[args.helper]))

    candidates = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.snag is None or combo[1] == args.snag)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not candidates:
        raise StoryError("(No valid combination matches the given options.)")

    place, snag, helper = rng.choice(candidates)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    hero_name = args.hero_name or rng.choice(POWER_NAMES)
    alarm = args.alarm or rng.choice(sorted(ALARMS))
    return StoryParams(
        place=place,
        snag=snag,
        helper=helper,
        alarm=alarm,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        hero_name=hero_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.snag not in SNAGS:
        raise StoryError(f"(Unknown snag: {params.snag})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.alarm not in ALARMS:
        raise StoryError(f"(Unknown alarm: {params.alarm})")
    if not combo_reasonable(params.place, params.snag, params.helper):
        raise StoryError(explain_rejection(PLACES[params.place], SNAGS[params.snag], HELPERS[params.helper]))

    world = tell(
        place=PLACES[params.place],
        snag=SNAGS[params.snag],
        helper_cfg=HELPERS[params.helper],
        alarm=ALARMS[params.alarm],
        child_name=params.name,
        child_type=params.gender,
        parent_type=params.parent,
        trait=params.trait,
        hero_name=params.hero_name,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if asp_set - py:
            print("  only in ASP:", sorted(asp_set - py))
        if py - asp_set:
            print("  only in Python:", sorted(py - asp_set))

    smoke_cases = list(CURATED)
    try:
        sample = generate(smoke_cases[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:  # pragma: no cover - defensive for batch verification
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Random smoke test failed: empty story)")
        print("OK: random generation succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"RANDOM GENERATION FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, snag, helper) combos:\n")
        for place, snag, helper in combos:
            print(f"  {place:10} {snag:8} {helper}")
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
            header = f"### {p.name}: {p.place}, {p.snag}, {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
