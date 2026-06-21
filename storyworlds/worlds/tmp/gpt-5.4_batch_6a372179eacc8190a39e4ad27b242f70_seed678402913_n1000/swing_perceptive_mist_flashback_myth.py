#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/swing_perceptive_mist_flashback_myth.py
==================================================================

A standalone storyworld about a child, a sacred swing, and a lesson remembered
through mist. The tone stays gentle and myth-like: a misty place, a careful
turn, a flashback to an elder's wisdom, and an ending image that proves the
child learned to notice before rushing.

Run it
------
    python storyworlds/worlds/gpt-5.4/swing_perceptive_mist_flashback_myth.py
    python storyworlds/worlds/gpt-5.4/swing_perceptive_mist_flashback_myth.py --hazard frayed_rope
    python storyworlds/worlds/gpt-5.4/swing_perceptive_mist_flashback_myth.py --remedy wipe_with_sleeve
    python storyworlds/worlds/gpt-5.4/swing_perceptive_mist_flashback_myth.py --all
    python storyworlds/worlds/gpt-5.4/swing_perceptive_mist_flashback_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/swing_perceptive_mist_flashback_myth.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
FLASHBACK_BONUS = 2


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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man", "keeper", "ferryman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "keeper": "keeper",
            "ferryman": "ferryman",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    mist_phrase: str
    holy_detail: str
    ending_light: str
    mist_level: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    clue: str
    danger_text: str
    reveal_text: str
    detect_need: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    type: str
    call_name: str
    approach: str
    teaching: str
    knows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    sense: int
    fixes: set[str]
    action: str
    qa_text: str
    gift: str
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


def _r_swing_risk(world: World) -> list[str]:
    child = world.entities.get("child")
    swing = world.entities.get("swing")
    if child is None or swing is None:
        return []
    if swing.meters["attempted"] < THRESHOLD or swing.meters["unsafe"] < THRESHOLD:
        return []
    sig = ("risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    swing.meters["danger"] += 1
    if world.facts.get("noticed_before_swing"):
        return []
    child.meters["jolt"] += 1
    return ["__jolt__"]


def _r_repair(world: World) -> list[str]:
    swing = world.entities.get("swing")
    child = world.entities.get("child")
    if swing is None or child is None:
        return []
    if swing.meters["repaired"] < THRESHOLD:
        return []
    sig = ("repaired",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    swing.meters["unsafe"] = 0.0
    swing.meters["danger"] = 0.0
    swing.meters["safe"] += 1
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    return ["__safe__"]


CAUSAL_RULES = [
    Rule(name="swing_risk", tag="physical", apply=_r_swing_risk),
    Rule(name="repair", tag="physical", apply=_r_repair),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "cloud_grove": Place(
        id="cloud_grove",
        label="the Cloud Grove",
        scene="a ring of old cedars on a hill where a sacred swing hung from a moon-white beam",
        mist_phrase="silver mist drifted between the cedars and wrapped even near things in soft secret cloth",
        holy_detail="Tiny bells slept in the branches and woke when the wind moved.",
        ending_light="the bells glittered like small stars in the clearing light",
        mist_level=2,
        tags={"mist", "swing"},
    ),
    "reed_marsh": Place(
        id="reed_marsh",
        label="the Reed Marsh",
        scene="a little shrine path above still water where a swing hung from a bent willow",
        mist_phrase="pale mist rose from the water and made the marsh look as if it were dreaming",
        holy_detail="Water birds stood like carved guardians beside the reeds.",
        ending_light="the water held the sky in one quiet blue sheet",
        mist_level=2,
        tags={"mist", "swing"},
    ),
    "sun_gate": Place(
        id="sun_gate",
        label="the Sun Gate",
        scene="a stone arch above a garden path where an old festival swing waited",
        mist_phrase="thin dawn mist curled around the stones and softened the world without hiding it fully",
        holy_detail="Red ribbons from past festivals fluttered against the arch.",
        ending_light="the first sunbeam slid through the arch and painted the swing gold",
        mist_level=1,
        tags={"mist", "swing"},
    ),
}

HAZARDS = {
    "frayed_rope": Hazard(
        id="frayed_rope",
        label="frayed rope",
        clue="one of the ropes looked furry with broken fibers, as if too many damp mornings had gnawed at it",
        danger_text="the worn rope could snap if someone flew too high",
        reveal_text="the rope had been quietly weakening for many misty days",
        detect_need=4,
        tags={"rope", "swing"},
    ),
    "loose_knot": Hazard(
        id="loose_knot",
        label="loose knot",
        clue="the knot above the seat had slipped lower than it should, and the swing leaned to one side",
        danger_text="the seat could twist suddenly and throw a rider sideways",
        reveal_text="the knot had loosened while the night mist soaked and shrank the cord",
        detect_need=3,
        tags={"knot", "swing"},
    ),
    "wet_board": Hazard(
        id="wet_board",
        label="wet board",
        clue="the wooden seat shone slick as a fish, beaded all over with cold drops from the mist",
        danger_text="small hands and clothes could slide on the wet seat",
        reveal_text="the board had drunk the mist and turned slippery",
        detect_need=3,
        tags={"wood", "mist", "swing"},
    ),
}

GUIDES = {
    "grandmother": Guide(
        id="grandmother",
        type="grandmother",
        call_name="Grandmother",
        approach="came with a basket on her arm and eyes that missed very little",
        teaching="When mist blurs your eyes, little one, let your hands and ears look too.",
        knows={"replace_rope", "tighten_knot", "dry_and_sand"},
        tags={"elder", "flashback"},
    ),
    "keeper": Guide(
        id="keeper",
        type="keeper",
        call_name="the keeper",
        approach="stepped from the shrine path with a coil of cord and a patient smile",
        teaching="Sacred things stay kind only when we care for them before they complain.",
        knows={"replace_rope", "tighten_knot"},
        tags={"elder", "flashback"},
    ),
    "ferryman": Guide(
        id="ferryman",
        type="ferryman",
        call_name="the ferryman",
        approach="came up from the water stairs carrying a dry cloth over one shoulder",
        teaching="Mist loves to hide trouble in quiet places, so touch the world before you trust it.",
        knows={"tighten_knot", "dry_and_sand"},
        tags={"elder", "flashback"},
    ),
}

REMEDIES = {
    "replace_rope": Remedy(
        id="replace_rope",
        label="new rope",
        sense=3,
        fixes={"frayed_rope"},
        action="unlooped the worn rope, threaded a new strong line through the beam, and tied it firm",
        qa_text="replaced the worn rope with a new strong one",
        gift="a blue ribbon tied near the top so the child could remember to look up first",
        tags={"rope", "repair"},
    ),
    "tighten_knot": Remedy(
        id="tighten_knot",
        label="tight knot",
        sense=3,
        fixes={"loose_knot"},
        action="lifted the seat, pulled the slipping knot snug again, and tested it until the swing hung straight",
        qa_text="tightened the loose knot and tested the seat until it hung straight",
        gift="a tiny brass bell on the side so the swing would sing softly when it moved true",
        tags={"knot", "repair"},
    ),
    "dry_and_sand": Remedy(
        id="dry_and_sand",
        label="dry smooth seat",
        sense=3,
        fixes={"wet_board"},
        action="wiped the board dry, rubbed it with a smooth stone and cloth, and laid it in the new sun for a moment",
        qa_text="dried the wet seat and made it safe to hold and sit on",
        gift="a sun-mark painted on the seat to show where morning light should touch it first",
        tags={"wood", "repair"},
    ),
    "wipe_with_sleeve": Remedy(
        id="wipe_with_sleeve",
        label="quick sleeve wipe",
        sense=1,
        fixes={"wet_board"},
        action="rubbed the seat once with a sleeve",
        qa_text="gave the seat a quick wipe with a sleeve",
        gift="nothing",
        tags={"wood"},
    ),
}

TRAIT_SCORES = {
    "perceptive": 4,
    "attentive": 4,
    "careful": 3,
    "patient": 3,
    "quick": 2,
    "dreamy": 1,
}

GIRL_NAMES = ["Nila", "Mira", "Sena", "Ira", "Luma", "Tavi", "Rina", "Aya"]
BOY_NAMES = ["Arin", "Taro", "Milo", "Kian", "Sori", "Niko", "Eren", "Lio"]


def remedy_for(hazard_id: str) -> list[str]:
    return sorted(rid for rid, remedy in REMEDIES.items() if hazard_id in remedy.fixes)


def hazard_fixable(hazard_id: str, remedy_id: str) -> bool:
    remedy = REMEDIES[remedy_id]
    return hazard_id in remedy.fixes


def guide_can(guide_id: str, remedy_id: str) -> bool:
    return remedy_id in GUIDES[guide_id].knows


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for hazard_id in HAZARDS:
            for guide_id in GUIDES:
                for remedy_id, remedy in REMEDIES.items():
                    if remedy.sense < SENSE_MIN:
                        continue
                    if hazard_fixable(hazard_id, remedy_id) and guide_can(guide_id, remedy_id):
                        combos.append((place_id, hazard_id, guide_id, remedy_id))
    return combos


def perception_score(trait: str) -> int:
    return TRAIT_SCORES[trait]


def would_notice(place_id: str, hazard_id: str, trait: str) -> bool:
    place = PLACES[place_id]
    hazard = HAZARDS[hazard_id]
    return perception_score(trait) + FLASHBACK_BONUS >= hazard.detect_need + place.mist_level


def predict_notice(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    swing = sim.get("swing")
    guide = sim.get("guide")
    place = sim.facts["place_cfg"]
    hazard = sim.facts["hazard_cfg"]
    noticed = would_notice(place.id, hazard.id, child.attrs["trait"])
    if noticed:
        child.memes["caution"] += 1
    else:
        swing.meters["attempted"] += 1
        propagate(sim, narrate=False)
    return {
        "noticed": noticed,
        "jolt": child.meters["jolt"],
        "danger": swing.meters["danger"],
        "guide": guide.id,
    }


def introduce(world: World, child: Entity, place: Place) -> None:
    world.say(
        f"In {place.label}, where {place.scene}, there lived a child named {child.id}."
    )
    world.say(
        f"{place.mist_phrase} {place.holy_detail}"
    )
    world.say(
        f"{child.id} loved the old swing there and believed it could carry a quiet heart almost high enough to brush a cloud."
    )


def approach_swing(world: World, child: Entity, place: Place) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"One dawn, {child.id} came to the swing while the mist was still wandering low over the ground."
    )
    world.say(
        f"{child.pronoun().capitalize()} put one hand on the seat and listened to the clearing breathe."
    )


def clue(world: World, child: Entity, hazard: Hazard) -> None:
    world.say(
        f"Then {child.pronoun()} noticed something small: {hazard.clue}."
    )


def flashback(world: World, child: Entity, guide_cfg: Guide) -> None:
    child.memes["memory"] += 1
    world.say(
        f"At that touch, a memory opened inside {child.pronoun('possessive')} mind like a lantern behind fog."
    )
    world.say(
        f"{guide_cfg.call_name} had said once, \"{guide_cfg.teaching}\""
    )


def cautious_turn(world: World, child: Entity, hazard: Hazard) -> None:
    child.memes["caution"] += 1
    world.facts["noticed_before_swing"] = True
    world.say(
        f"Because of that remembered voice, {child.id} did not leap onto the swing at once."
    )
    world.say(
        f"{child.pronoun().capitalize()} ran careful fingers along the wood and rope and understood that {hazard.danger_text}."
    )


def startled_turn(world: World, child: Entity, swing: Entity, hazard: Hazard) -> None:
    swing.meters["attempted"] += 1
    propagate(world, narrate=False)
    world.facts["noticed_before_swing"] = False
    world.say(
        f"But the wish to fly through the mist tugged hard, and {child.id} gave the swing one eager push."
    )
    world.say(
        f"At once the swing moved wrong. It shivered under {child.pronoun('object')} in a way no good swing should."
    )
    world.say(
        f"{child.id} jumped back with a thumping heart and understood that {hazard.danger_text}."
    )


def call_for_guide(world: World, child: Entity, guide: Entity) -> None:
    child.memes["trust"] += 1
    world.say(
        f"Instead of pretending to be brave, {child.id} called for {guide.label}."
    )
    world.say(
        f"Soon {guide.label} {guide.attrs['approach']}."
    )


def reveal(world: World, guide: Entity, hazard: Hazard) -> None:
    world.say(
        f"{guide.label.capitalize()} looked once and nodded. \"Yes,\" {guide.pronoun()} said. \"{hazard.reveal_text}.\""
    )


def mend(world: World, guide: Entity, swing: Entity, remedy: Remedy) -> None:
    swing.meters["repaired"] += 1
    guide.meters["repair"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {guide.label} {remedy.action}."
    )
    world.say(
        f"{guide.pronoun().capitalize()} worked slowly, the way people do when they mean for a thing to last."
    )


def lesson(world: World, guide: Entity, child: Entity, remedy: Remedy) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"When the work was done, {guide.label} gave {child.id} {remedy.gift}."
    )
    world.say(
        f"\"A kind heart is good,\" {guide.pronoun()} said, \"but a perceptive heart is better still. It sees what needs care before joy turns into hurt.\""
    )


def ending(world: World, child: Entity, place: Place) -> None:
    child.memes["joy"] += 1
    world.say(
        f"By then the mist had begun to thin. {place.ending_light}"
    )
    world.say(
        f"{child.id} took a gentle swing, not a wild one, and the clear sound above {child.pronoun('object')} told the whole grove that haste had become wisdom."
    )


def tell(place: Place, hazard_cfg: Hazard, guide_cfg: Guide, remedy_cfg: Remedy,
         child_name: str = "Nila", child_type: str = "girl", trait: str = "perceptive") -> World:
    world = World(place)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={"trait": trait},
    ))
    guide = world.add(Entity(
        id="guide",
        kind="character",
        type=guide_cfg.type,
        label=guide_cfg.call_name,
        role="guide",
        attrs={"approach": guide_cfg.approach},
    ))
    swing = world.add(Entity(
        id="swing",
        kind="thing",
        type="swing",
        label="the swing",
        tags={"swing"},
    ))
    swing.meters["unsafe"] += 1

    world.facts.update(
        place_cfg=place,
        hazard_cfg=hazard_cfg,
        guide_cfg=guide_cfg,
        remedy_cfg=remedy_cfg,
        child_name=child_name,
        trait=trait,
    )

    introduce(world, child, place)
    world.para()
    approach_swing(world, child, place)
    clue(world, child, hazard_cfg)
    flashback(world, child, guide_cfg)

    if would_notice(place.id, hazard_cfg.id, trait):
        world.para()
        cautious_turn(world, child, hazard_cfg)
        outcome = "noticed"
    else:
        world.para()
        startled_turn(world, child, swing, hazard_cfg)
        outcome = "startled"

    world.para()
    call_for_guide(world, child, guide)
    reveal(world, guide, hazard_cfg)
    mend(world, guide, swing, remedy_cfg)
    lesson(world, guide, child, remedy_cfg)

    world.para()
    ending(world, child, place)

    world.facts.update(
        child=child,
        guide=guide,
        swing=swing,
        outcome=outcome,
        had_jolt=child.meters["jolt"] >= THRESHOLD,
        repaired=swing.meters["safe"] >= THRESHOLD,
        noticed_before_swing=world.facts.get("noticed_before_swing", False),
        flashback=True,
    )
    return world


@dataclass
class StoryParams:
    place: str
    hazard: str
    guide: str
    remedy: str
    child: str
    gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "mist": [
        (
            "What is mist?",
            "Mist is a cloud close to the ground made of tiny drops of water. It can make things look soft and harder to see clearly.",
        )
    ],
    "swing": [
        (
            "Why should you check a swing before using it?",
            "A swing needs strong ropes, a steady seat, and safe places to hold. Checking first helps you notice trouble before someone gets hurt.",
        )
    ],
    "rope": [
        (
            "What does it mean when a rope is frayed?",
            "A frayed rope has worn, broken fibers sticking out. That means it is getting weak and may not hold safely.",
        )
    ],
    "knot": [
        (
            "Why does a knot need to be tight?",
            "A tight knot keeps a thing from slipping apart. If a knot loosens, the swing can lean or twist in a dangerous way.",
        )
    ],
    "wood": [
        (
            "Why can a wet wooden seat be slippery?",
            "Water makes the top of the wood smooth and slick. Hands or clothes can slide on it more easily.",
        )
    ],
    "repair": [
        (
            "Why is fixing something better than pretending it is fine?",
            "Fixing a problem makes the thing safe again. Pretending can let a small danger grow into a bigger one.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick memory from earlier that comes back during the story. It helps a character understand what to do now.",
        )
    ],
    "elder": [
        (
            "Why do elders in myths often give advice?",
            "In myths, elders have watched the world for a long time and noticed its patterns. Their advice helps younger people act with wisdom instead of rushing.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mist", "swing", "rope", "knot", "wood", "repair", "flashback", "elder"]


CURATED = [
    StoryParams(
        place="cloud_grove",
        hazard="frayed_rope",
        guide="grandmother",
        remedy="replace_rope",
        child="Nila",
        gender="girl",
        trait="perceptive",
    ),
    StoryParams(
        place="reed_marsh",
        hazard="wet_board",
        guide="ferryman",
        remedy="dry_and_sand",
        child="Arin",
        gender="boy",
        trait="dreamy",
    ),
    StoryParams(
        place="sun_gate",
        hazard="loose_knot",
        guide="keeper",
        remedy="tighten_knot",
        child="Mira",
        gender="girl",
        trait="attentive",
    ),
    StoryParams(
        place="cloud_grove",
        hazard="wet_board",
        guide="grandmother",
        remedy="dry_and_sand",
        child="Kian",
        gender="boy",
        trait="careful",
    ),
]


def explain_rejection(hazard_id: str, guide_id: str, remedy_id: str) -> str:
    remedy = REMEDIES[remedy_id]
    if remedy.sense < SENSE_MIN:
        return (
            f"(Refusing remedy '{remedy_id}': it scores too low on common sense "
            f"(sense={remedy.sense} < {SENSE_MIN}). The fix should truly make the swing safe.)"
        )
    if not hazard_fixable(hazard_id, remedy_id):
        good = ", ".join(remedy_for(hazard_id))
        return (
            f"(No story: {remedy.label} does not solve {HAZARDS[hazard_id].label}. "
            f"Try one of: {good}.)"
        )
    if not guide_can(guide_id, remedy_id):
        able = ", ".join(sorted(GUIDES[guide_id].knows))
        return (
            f"(No story: {GUIDES[guide_id].call_name} is not the right helper for "
            f"{REMEDIES[remedy_id].label}. This guide can manage: {able}.)"
        )
    return "(No story: that combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    return "noticed" if would_notice(params.place, params.hazard, params.trait) else "startled"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place_cfg"]
    hazard = f["hazard_cfg"]
    guide = f["guide_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short myth-like story for a 3-to-5-year-old that includes the words "swing", '
        f'"perceptive", and "mist", and uses a flashback to help a child make a wise choice.'
    )
    if outcome == "noticed":
        return [
            base,
            f"Tell a gentle myth where {child.label} sees trouble on a sacred swing in {place.label}, remembers {guide.call_name}'s earlier advice in a flashback, and stops before getting hurt.",
            f"Write a story in a soft myth style where a perceptive child notices a {hazard.label} through the mist, calls for help, and ends with a safer swing and a wiser heart.",
        ]
    return [
        base,
        f"Tell a myth-like near-miss where {child.label} is tempted to swing before checking, feels something go wrong, and then remembers old advice through a flashback.",
        f"Write a child-facing story where dawn mist hides a {hazard.label}, a child gets a small scare on a swing, and an elder helps turn fear into wisdom.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    place = f["place_cfg"]
    hazard = f["hazard_cfg"]
    remedy = f["remedy_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a child who loved the sacred swing in {place.label}, and {guide.label}, the elder who helped make it safe. The misty place and the old swing shape the whole adventure.",
        ),
        (
            "What did the child notice at the swing?",
            f"{child.label} noticed that {hazard.clue}. That small clue mattered because it pointed to a danger hidden by the mist.",
        ),
        (
            "What happened in the flashback?",
            f"{child.label} remembered {guide.label}'s earlier words about noticing with hands and ears when the world is blurry. The flashback helped {child.pronoun('object')} slow down and understand what kind of danger might be there.",
        ),
    ]
    if outcome == "noticed":
        qa.append(
            (
                f"Why did {child.label} stop before swinging high?",
                f"{child.label} was perceptive enough to trust the clue and the remembered advice. Because of that, {child.pronoun()} understood that {hazard.danger_text} before the swing could give even one bad lurch.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {child.label} tried the swing?",
                f"The swing moved wrong and gave {child.pronoun('object')} a small fright, so {child.pronoun()} jumped back. That jolt showed that {hazard.danger_text}.",
            )
        )
    qa.append(
        (
            f"How did {guide.label} fix the swing?",
            f"{guide.label.capitalize()} {remedy.qa_text}. The repair changed the swing from something risky into something safe to use again.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The mist thinned, the repaired swing moved gently, and {child.label} swung with care instead of haste. The ending image shows that the child learned wisdom, not just fear.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"flashback", "elder", "mist", "swing", "repair"}
    tags |= set(f["hazard_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% reasonable combination
fixes(H, R) :- remedy(R), hazard(H), remedy_fixes(R, H).
helper_can(G, R) :- guide(G), knows(G, R).
sensible(R) :- remedy(R), sense(R, S), sense_min(M), S >= M.
valid(P, H, G, R) :- place(P), hazard(H), guide(G), remedy(R),
                     sensible(R), fixes(H, R), helper_can(G, R).

% outcome model: flashback always exists in this world, but whether the child
% notices in time depends on trait perception plus the flashback bonus versus
% mist level and clue difficulty.
noticed :- chosen_place(P), chosen_hazard(H), chosen_trait(T),
           trait_score(T, TS), flashback_bonus(FB),
           detect_need(H, DN), mist_level(P, ML),
           TS + FB >= DN + ML.

outcome(noticed) :- noticed.
outcome(startled) :- not noticed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("mist_level", place_id, place.mist_level))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("detect_need", hazard_id, hazard.detect_need))
    for guide_id in GUIDES:
        lines.append(asp.fact("guide", guide_id))
    for guide_id, guide in GUIDES.items():
        for remedy_id in sorted(guide.knows):
            lines.append(asp.fact("knows", guide_id, remedy_id))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
        for hazard_id in sorted(remedy.fixes):
            lines.append(asp.fact("remedy_fixes", remedy_id, hazard_id))
    for trait, score in TRAIT_SCORES.items():
        lines.append(asp.fact("trait_score", trait, score))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("flashback_bonus", FLASHBACK_BONUS))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth-like storyworld: a child, a swing, mist, and a flashback that teaches careful noticing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child")
    ap.add_argument("--trait", choices=sorted(TRAIT_SCORES))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_rejection(args.hazard or "wet_board", args.guide or "grandmother", args.remedy))
    if args.hazard and args.remedy and not hazard_fixable(args.hazard, args.remedy):
        guide_id = args.guide or "grandmother"
        raise StoryError(explain_rejection(args.hazard, guide_id, args.remedy))
    if args.guide and args.remedy and not guide_can(args.guide, args.remedy):
        hazard_id = args.hazard or next(iter(REMEDIES[args.remedy].fixes))
        raise StoryError(explain_rejection(hazard_id, args.guide, args.remedy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.guide is None or combo[2] == args.guide)
        and (args.remedy is None or combo[3] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, hazard_id, guide_id, remedy_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(sorted(TRAIT_SCORES))
    return StoryParams(
        place=place_id,
        hazard=hazard_id,
        guide=guide_id,
        remedy=remedy_id,
        child=child,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.guide not in GUIDES:
        raise StoryError(f"(Unknown guide: {params.guide})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.trait not in TRAIT_SCORES:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if REMEDIES[params.remedy].sense < SENSE_MIN:
        raise StoryError(explain_rejection(params.hazard, params.guide, params.remedy))
    if not hazard_fixable(params.hazard, params.remedy):
        raise StoryError(explain_rejection(params.hazard, params.guide, params.remedy))
    if not guide_can(params.guide, params.remedy):
        raise StoryError(explain_rejection(params.hazard, params.guide, params.remedy))

    world = tell(
        place=PLACES[params.place],
        hazard_cfg=HAZARDS[params.hazard],
        guide_cfg=GUIDES[params.guide],
        remedy_cfg=REMEDIES[params.remedy],
        child_name=params.child,
        child_type=params.gender,
        trait=params.trait,
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

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    python_sensible = {r.id for r in sensible_remedies()}
    clingo_sensible = set(asp_sensible())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible remedies match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (place, hazard, guide, remedy) combos:\n")
        for place_id, hazard_id, guide_id, remedy_id in combos:
            print(f"  {place_id:11} {hazard_id:12} {guide_id:11} {remedy_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.hazard} at {p.place} ({p.guide}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
