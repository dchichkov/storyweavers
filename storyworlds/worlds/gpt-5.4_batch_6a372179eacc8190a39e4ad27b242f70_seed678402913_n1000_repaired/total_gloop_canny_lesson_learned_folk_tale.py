#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/total_gloop_canny_lesson_learned_folk_tale.py
========================================================================

A standalone storyworld for a small folk-tale domain: a village child must carry
a gift across a troublesome path. A canny elder predicts what the path will do
to the gift, offers the right way to carry it, and the child either listens at
once or learns after one sticky mistake.

The seed words "total", "gloop", and "canny" are worked into the prose. The
feature is a clear Lesson Learned ending, and the style stays close to a gentle
folk tale.

Run it
------
    python storyworlds/worlds/gpt-5.4/total_gloop_canny_lesson_learned_folk_tale.py
    python storyworlds/worlds/gpt-5.4/total_gloop_canny_lesson_learned_folk_tale.py --hazard marsh --cargo cakes
    python storyworlds/worlds/gpt-5.4/total_gloop_canny_lesson_learned_folk_tale.py --hazard thorn_lane --cargo milk
    python storyworlds/worlds/gpt-5.4/total_gloop_canny_lesson_learned_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/total_gloop_canny_lesson_learned_folk_tale.py --qa
    python storyworlds/worlds/gpt-5.4/total_gloop_canny_lesson_learned_folk_tale.py --verify
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
LISTENING_TRAITS = {"careful", "patient", "humble", "canny"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    protects: set[str] = field(default_factory=set)
    supports: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def elder_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "aunt": "aunt",
            "uncle": "uncle",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)


@dataclass
class Hazard:
    id: str
    place: str
    path_name: str
    scene: str
    sound: str
    risks: set[str] = field(default_factory=set)
    spoil_text: str = ""
    safe_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    profiles: set[str] = field(default_factory=set)
    ruined_text: str = ""
    safe_text: str = ""
    recipient: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Carrier:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    supports: set[str] = field(default_factory=set)
    prep: str = ""
    carry_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.current_risks: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone.current_risks = set(self.current_risks)
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def carrier_for(self, actor: Entity) -> Optional[Entity]:
        for ent in self.entities.values():
            if ent.type == "carrier" and ent.carried_by == actor.id:
                return ent
        return None


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_ruin_cargo(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    cargo = world.entities.get("cargo")
    if hero is None or cargo is None:
        return out
    if hero.meters["crossed"] < THRESHOLD:
        return out
    carrier = world.carrier_for(hero)
    unguarded = set(world.current_risks)
    if carrier is not None:
        unguarded -= set(carrier.protects)
    harmful = unguarded & set(cargo.attrs.get("profiles", set()))
    if not harmful:
        return out
    sig = ("ruin", tuple(sorted(harmful)))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["ruined"] += 1
    hero.memes["worry"] += 1
    hero.memes["shame"] += 1
    out.append("__ruined__")
    return out


def _r_notice_lesson(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    cargo = world.entities.get("cargo")
    elder = world.entities.get("elder")
    if hero is None or cargo is None or elder is None:
        return out
    if cargo.meters["ruined"] < THRESHOLD:
        return out
    sig = ("lesson", cargo.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    elder.memes["patience"] += 1
    hero.memes["lesson"] += 1
    out.append("__lesson__")
    return out


CAUSAL_RULES = [
    Rule(name="ruin_cargo", tag="physical", apply=_r_ruin_cargo),
    Rule(name="notice_lesson", tag="social", apply=_r_notice_lesson),
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
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def cargo_at_risk(hazard: Hazard, cargo: Cargo) -> bool:
    return bool(set(hazard.risks) & set(cargo.profiles))


def select_carrier(hazard: Hazard, cargo: Cargo) -> Optional[Carrier]:
    for carrier in CARRIERS.values():
        if set(hazard.risks) <= set(carrier.protects) and set(cargo.profiles) <= set(carrier.supports):
            return carrier
    return None


def would_listen(trait: str) -> bool:
    return trait in LISTENING_TRAITS


def outcome_of(params: "StoryParams") -> str:
    return "safe_first" if would_listen(params.trait) else "learned_after_mess"


def _do_cross(world: World, hero: Entity, hazard: Hazard, narrate: bool = True) -> None:
    hero.meters["crossed"] += 1
    hero.meters["mud"] += 1 if "splash" in hazard.risks else 0
    hero.meters["wet"] += 1 if "water" in hazard.risks else 0
    hero.meters["scratched"] += 1 if "snag" in hazard.risks else 0
    world.current_risks = set(hazard.risks)
    propagate(world, narrate=narrate)


def predict_crossing(world: World, hero: Entity, hazard: Hazard) -> dict:
    sim = world.copy()
    _do_cross(sim, sim.get(hero.id), hazard, narrate=False)
    cargo = sim.get("cargo")
    return {
        "ruined": cargo.meters["ruined"] >= THRESHOLD,
        "risk_count": len(sim.current_risks),
    }


def introduce(world: World, hero: Entity, elder: Entity, cargo: Cargo, hazard: Hazard) -> None:
    world.say(
        f"Once, on the edge of {hazard.place}, there lived a little {hero.type} named {hero.id}."
    )
    world.say(
        f"{hero.id} was quick on the feet and fond of errands, especially when {elder.elder_word} trusted "
        f"{hero.pronoun('object')} with something important."
    )
    world.say(
        f"One morning, {elder.elder_word} set out {cargo.phrase} and said it must go to {cargo.recipient} "
        f"before the sun climbed high."
    )


def need_path(world: World, hero: Entity, hazard: Hazard) -> None:
    world.say(
        f"Between the cottage and the far door ran {hazard.path_name}, {hazard.scene}."
    )
    world.say(
        f"It was the shortest way, and to a child in a hurry the short way always looked like the best way."
    )


def elder_warning(world: World, elder: Entity, hero: Entity, hazard: Hazard, cargo: Cargo) -> None:
    pred = predict_crossing(world, hero, hazard)
    world.facts["predicted_ruin"] = pred["ruined"]
    world.facts["predicted_risk_count"] = pred["risk_count"]
    world.say(
        f'But {elder.elder_word} was a canny elder and had watched that path in all seasons. '
        f'"If you carry {cargo.label} across {hazard.path_name} just so," {elder.pronoun()} said, '
        f'"{hazard.spoil_text}."'
    )


def offer_carrier(world: World, elder: Entity, carrier: Carrier) -> None:
    world.say(
        f'{elder.pronoun().capitalize()} brought out {carrier.phrase} and added, '
        f'"{carrier.prep}."'
    )


def ignore_warning(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.memes["hurry"] += 1
    hero.memes["defiance"] += 1
    world.say(
        f"But hurry buzzed in {hero.id}'s ears. {hero.pronoun().capitalize()} thanked {world.get('elder').elder_word}, "
        f"yet thought, just this once, that quick feet would be enough."
    )
    world.say(
        f"So off {hero.pronoun()} went onto {hazard.path_name}, where the ground answered {hazard.sound}, {hazard.sound} underfoot."
    )


def first_mess(world: World, hero: Entity, cargo: Entity, hazard: Hazard, cargo_cfg: Cargo) -> None:
    _do_cross(world, hero, hazard, narrate=False)
    world.say(
        f"In the middle of the path came a slip, a wobble, and then a total gloop of trouble."
    )
    if cargo.meters["ruined"] >= THRESHOLD:
        world.say(
            f"{cargo_cfg.ruined_text} {hazard.spoil_text.capitalize()}."
        )
    else:
        world.say(hazard.spoil_text.capitalize() + ".")
    world.say(
        f"{hero.id} looked at the poor errand and knew that quickness without thought had made the work twice as long."
    )


def return_and_repair(world: World, elder: Entity, hero: Entity, cargo: Entity, cargo_cfg: Cargo, carrier: Carrier) -> None:
    hero.meters["crossed"] = 0.0
    world.current_risks = set()
    world.say(
        f"Back to the cottage {hero.pronoun()} came, slow now, with the spoiled gift in {hero.pronoun('possessive')} hands."
    )
    world.say(
        f"{elder.elder_word.capitalize()} did not scold. {elder.pronoun().capitalize()} set the ruined things aside, prepared {cargo_cfg.phrase} anew, "
        f"and laid {carrier.phrase} beside it."
    )
    world.say(
        f'"A short road is not the same as an easy road," {elder.pronoun()} said. '
        f'"Take the wise way, and the road will do less mischief."'
    )


def equip(world: World, hero: Entity, carrier_ent: Entity, carrier: Carrier) -> None:
    carrier_ent.carried_by = hero.id
    world.say(
        f"{hero.id} lifted {carrier.phrase}. {carrier.carry_text}."
    )


def safe_cross(world: World, hero: Entity, hazard: Hazard, cargo: Cargo, first_try: bool) -> None:
    _do_cross(world, hero, hazard, narrate=False)
    opener = "This time" if not first_try else "So"
    world.say(
        f"{opener}, when {hero.id} stepped onto {hazard.path_name}, the path still muttered {hazard.sound}, "
        f"but it could not reach the gift."
    )
    world.say(hazard.safe_text)
    world.say(cargo.safe_text)


def arrival(world: World, hero: Entity, cargo: Cargo) -> None:
    hero.memes["pride"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"When {hero.id} reached {cargo.recipient}, the gift was fit to offer and the errand was done before noon."
    )


def moral(world: World, hero: Entity, elder: Entity, first_try: bool) -> None:
    if first_try:
        world.say(
            f"That evening {hero.id} told the tale by the hearth and said that a canny word, heard in time, can save a journey entire."
        )
    else:
        world.say(
            f"That evening {hero.id} told the tale by the hearth and said that a lesson learned in mud is still worth keeping."
        )
    world.say(
        f"From then on, whenever a road looked easy only because it was short, {hero.id} remembered {elder.elder_word}'s wisdom and chose with more care."
    )


def tell(
    hazard: Hazard,
    cargo_cfg: Cargo,
    carrier: Carrier,
    hero_name: str = "Mira",
    hero_type: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "careful",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero", traits=[trait]))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label="the elder", role="elder", traits=["canny", "patient"]))
    cargo = world.add(
        Entity(
            id="cargo",
            type="cargo",
            label=cargo_cfg.label,
            phrase=cargo_cfg.phrase,
            attrs={"profiles": set(cargo_cfg.profiles)},
            tags=set(cargo_cfg.tags),
            carried_by=hero.id,
        )
    )
    carrier_ent = world.add(
        Entity(
            id="carrier",
            type="carrier",
            label=carrier.label,
            phrase=carrier.phrase,
            protects=set(carrier.protects),
            supports=set(carrier.supports),
        )
    )

    world.facts.update(
        hero=hero,
        elder=elder,
        cargo=cargo,
        cargo_cfg=cargo_cfg,
        hazard=hazard,
        carrier=carrier,
        trait=trait,
    )

    introduce(world, hero, elder, cargo_cfg, hazard)
    need_path(world, hero, hazard)

    world.para()
    elder_warning(world, elder, hero, hazard, cargo_cfg)
    offer_carrier(world, elder, carrier)

    first_try_safe = would_listen(trait)
    if first_try_safe:
        equip(world, hero, carrier_ent, carrier)
        world.para()
        safe_cross(world, hero, hazard, cargo_cfg, first_try=True)
        arrival(world, hero, cargo_cfg)
        world.para()
        moral(world, hero, elder, first_try=True)
        outcome = "safe_first"
    else:
        ignore_warning(world, hero, hazard)
        world.para()
        first_mess(world, hero, cargo, hazard, cargo_cfg)
        return_and_repair(world, elder, hero, cargo, cargo_cfg, carrier)
        equip(world, hero, carrier_ent, carrier)
        cargo.meters["ruined"] = 0.0
        world.para()
        safe_cross(world, hero, hazard, cargo_cfg, first_try=False)
        arrival(world, hero, cargo_cfg)
        world.para()
        moral(world, hero, elder, first_try=False)
        outcome = "learned_after_mess"

    world.facts.update(
        outcome=outcome,
        listened=first_try_safe,
        ruined_first=cargo.meters["ruined"] >= THRESHOLD if not first_try_safe else False,
    )
    return world


HAZARDS = {
    "marsh": Hazard(
        id="marsh",
        place="the Willow Marsh",
        path_name="the reed path",
        scene="a narrow strip of earth through soft black mud",
        sound="gloop",
        risks={"splash"},
        spoil_text="the mud will leap up and spatter the gift",
        safe_text="The mud stayed below, grumbling to itself among the reeds.",
        tags={"mud", "path"},
    ),
    "stream": Hazard(
        id="stream",
        place="the Alder Stream",
        path_name="the stepping-stone ford",
        scene="a line of stones through bright, hurrying water",
        sound="splish",
        risks={"water", "spill"},
        spoil_text="the stream will wet it or tip it into a sloshy mess",
        safe_text="The water flashed on both sides, but not a drop touched the gift.",
        tags={"water", "path"},
    ),
    "thorn_lane": Hazard(
        id="thorn_lane",
        place="the Briar Lane",
        path_name="the thorn lane",
        scene="a crooked track where hedge-thorns leaned in like hooked fingers",
        sound="snick",
        risks={"snag"},
        spoil_text="the thorns will catch and tear at it",
        safe_text="The hedge scraped at empty air while the gift passed safely by.",
        tags={"briar", "path"},
    ),
}

CARGOS = {
    "cakes": Cargo(
        id="cakes",
        label="the honey cakes",
        phrase="a round tray of honey cakes",
        profiles={"splash"},
        ruined_text="The honey cakes wore brown spots where none should be",
        safe_text="The honey cakes came through golden and neat",
        recipient="the miller at the far door",
        tags={"cakes"},
    ),
    "milk": Cargo(
        id="milk",
        label="the milk bowl",
        phrase="a brimful bowl of morning milk",
        profiles={"water", "spill"},
        ruined_text="Half the milk was gone, and what remained was thin and untidy",
        safe_text="The milk still shone white and calm in its bowl",
        recipient="the baker by the warm oven",
        tags={"milk"},
    ),
    "linen": Cargo(
        id="linen",
        label="the folded linen",
        phrase="a bundle of fresh folded linen",
        profiles={"snag"},
        ruined_text="The clean linen showed ugly pulls and little tears",
        safe_text="The linen stayed folded smooth as moonlight",
        recipient="the seamstress near the market square",
        tags={"linen"},
    ),
}

CARRIERS = {
    "lidded_basket": Carrier(
        id="lidded_basket",
        label="lidded basket",
        phrase="a willow basket with a tight lid",
        protects={"splash"},
        supports={"splash"},
        prep="Set it in this basket, and carry it above the mud's jumping reach",
        carry_text="It sat light but steady in the crook of the arm",
        tags={"basket"},
    ),
    "handled_pail": Carrier(
        id="handled_pail",
        label="handled pail",
        phrase="a little pail with a snug cover",
        protects={"water", "spill"},
        supports={"water", "spill"},
        prep="Set it in this pail, and let the cover keep the road from meddling",
        carry_text="The handle swung neatly, and the cover held fast",
        tags={"pail"},
    ),
    "wrapped_hamper": Carrier(
        id="wrapped_hamper",
        label="wrapped hamper",
        phrase="a stout hamper wrapped in smooth cloth",
        protects={"snag"},
        supports={"snag"},
        prep="Lay it in this hamper, and the thorns will have nothing to catch",
        carry_text="The cloth slipped past bramble and twig without a hitch",
        tags={"hamper"},
    ),
}


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for hazard_id, hazard in HAZARDS.items():
        for cargo_id, cargo in CARGOS.items():
            if cargo_at_risk(hazard, cargo) and select_carrier(hazard, cargo) is not None:
                combos.append((hazard_id, cargo_id))
    return combos


@dataclass
class StoryParams:
    hazard: str
    cargo: str
    carrier: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        hazard="marsh",
        cargo="cakes",
        carrier="lidded_basket",
        name="Mira",
        gender="girl",
        elder="grandmother",
        trait="careful",
    ),
    StoryParams(
        hazard="stream",
        cargo="milk",
        carrier="handled_pail",
        name="Tobin",
        gender="boy",
        elder="grandfather",
        trait="hasty",
    ),
    StoryParams(
        hazard="thorn_lane",
        cargo="linen",
        carrier="wrapped_hamper",
        name="Elsa",
        gender="girl",
        elder="aunt",
        trait="patient",
    ),
    StoryParams(
        hazard="marsh",
        cargo="cakes",
        carrier="lidded_basket",
        name="Rowan",
        gender="boy",
        elder="uncle",
        trait="stubborn",
    ),
]


KNOWLEDGE = {
    "mud": [
        (
            "What is mud?",
            "Mud is wet earth. It sticks, splashes, and can make clean things dirty very quickly.",
        )
    ],
    "water": [
        (
            "Why can carrying something over a stream be hard?",
            "A stream moves and splashes, so a bowl or tray can wobble or get wet. That is why people use steady hands and the right container.",
        )
    ],
    "briar": [
        (
            "What do thorns do?",
            "Thorns are sharp, stiff points on some plants. They can catch cloth and scratch skin if you brush past them.",
        )
    ],
    "basket": [
        (
            "What does a basket lid do?",
            "A lid covers what is inside the basket. It helps keep splashes and dirt away from the food.",
        )
    ],
    "pail": [
        (
            "Why is a covered pail useful?",
            "A covered pail keeps liquid from sloshing out so easily. The cover also helps road dust and splashes stay out.",
        )
    ],
    "hamper": [
        (
            "Why wrap a hamper in cloth?",
            "Smooth cloth can slide past rough branches better than loose linen can. Wrapping protects the things inside from snagging.",
        )
    ],
    "path": [
        (
            "Why is the shortest road not always the best road?",
            "A short road may still be muddy, rough, or tricky. A wise traveler thinks about what the road can do, not only how long it is.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mud", "water", "briar", "basket", "pail", "hamper", "path"]

GIRL_NAMES = ["Mira", "Elsa", "Nell", "Anya", "Tilda", "Lina", "Rosa", "Wren"]
BOY_NAMES = ["Tobin", "Rowan", "Milo", "Perrin", "Elias", "Bram", "Ivo", "Soren"]
TRAITS = ["careful", "patient", "humble", "canny", "hasty", "stubborn", "proud"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    hazard = f["hazard"]
    cargo = f["cargo_cfg"]
    outcome = f["outcome"]
    if outcome == "safe_first":
        return [
            f'Write a gentle folk tale for a young child that includes the words "total", "gloop", and "canny".',
            f"Tell a lesson-learned story where {hero.label} must carry {cargo.label} across {hazard.path_name}, listens to a canny elder, and finishes the errand wisely.",
            f"Write a village folk tale in which a child chooses the right way before trouble starts and learns that the shortest road is not always the best road.",
        ]
    return [
        f'Write a gentle folk tale for a young child that includes the words "total", "gloop", and "canny".',
        f"Tell a lesson-learned story where {hero.label} hurries across {hazard.path_name}, makes a sticky mistake, and then learns from a canny elder how to finish the errand properly.",
        f"Write a folk-tale style story in which a child ignores good advice once, spoils the gift, and then returns to do the work the wise way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    hazard = f["hazard"]
    cargo = f["cargo_cfg"]
    carrier = f["carrier"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child trusted with an errand, and a canny {elder.elder_word} who gave wise advice. The whole tale turns on whether {hero.label} listens before crossing {hazard.path_name}.",
        ),
        (
            f"What was {hero.label} carrying, and where did it need to go?",
            f"{hero.label} was carrying {cargo.phrase}. It had to go to {cargo.recipient} before the day grew late.",
        ),
        (
            f"Why did the elder warn {hero.label} about {hazard.path_name}?",
            f"The elder knew what that path could do and foresaw that the gift would be spoiled if it was carried the wrong way. The warning came from understanding the road, not from trying to stop the errand.",
        ),
    ]
    if outcome == "safe_first":
        qa.extend(
            [
                (
                    f"How did {hero.label} keep the gift safe?",
                    f"{hero.label} used {carrier.phrase} just as the elder suggested. That carrier matched the trouble on the road, so the path could not spoil the gift.",
                ),
                (
                    "What lesson did the story teach?",
                    f"It taught that wise advice can save work before trouble begins. {hero.label} learned that a short road is only good when you are ready for it.",
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"What happened when {hero.label} hurried across the path the first time?",
                    f"{hero.label} slipped into a total gloop of trouble, and the gift was spoiled on the road. That mistake showed why the elder's warning had been true.",
                ),
                (
                    f"How was the problem finally solved?",
                    f"{hero.label} went back, the elder prepared the gift again, and then {hero.label} carried it in {carrier.phrase}. The second trip worked because the wise method fit the danger on the path.",
                ),
                (
                    "What lesson did the story teach?",
                    f"It taught that even after a mistake, a child can stop, listen, and do the work properly. {hero.label} learned that quickness without thought only makes the journey longer.",
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["hazard"].tags) | set(f["carrier"].tags) | {"path"}
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.protects:
            bits.append(f"protects={sorted(ent.protects)}")
        if ent.supports:
            bits.append(f"supports={sorted(ent.supports)}")
        if ent.carried_by:
            bits.append(f"carried_by={ent.carried_by}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  current_risks: {sorted(world.current_risks)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(hazard: Hazard, cargo: Cargo) -> str:
    if not cargo_at_risk(hazard, cargo):
        return (
            f"(No story: {hazard.path_name} threatens {sorted(hazard.risks)}, but {cargo.label} is not vulnerable to that kind of trouble. "
            f"The elder would have no honest warning to give.)"
        )
    return (
        f"(No story: there is no carrier in this world that protects {cargo.label} from {hazard.path_name}. "
        f"A lesson-learned folk tale needs a sensible wise fix, not only a warning.)"
    )


ASP_RULES = r"""
cargo_at_risk(H, C) :- hazard(H), cargo(C), risk(H, R), profile(C, R).
carrier_works(H, C, K) :- carrier(K),
                          cargo_at_risk(H, C),
                          risk(H, R), protects(K, R),
                          profile(C, P), supports(K, P).
valid(H, C) :- cargo_at_risk(H, C), carrier_works(H, C, _).

listens :- trait(T), listening_trait(T).
outcome(safe_first) :- listens.
outcome(learned_after_mess) :- not listens.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        for risk in sorted(hazard.risks):
            lines.append(asp.fact("risk", hazard_id, risk))
    for cargo_id, cargo in CARGOS.items():
        lines.append(asp.fact("cargo", cargo_id))
        for profile in sorted(cargo.profiles):
            lines.append(asp.fact("profile", cargo_id, profile))
    for carrier_id, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", carrier_id))
        for risk in sorted(carrier.protects):
            lines.append(asp.fact("protects", carrier_id, risk))
        for support in sorted(carrier.supports):
            lines.append(asp.fact("supports", carrier_id, support))
    for trait in sorted(LISTENING_TRAITS):
        lines.append(asp.fact("listening_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("trait", params.trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a folk-tale errand, a troublesome path, and a lesson learned."
    )
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "aunt", "uncle", "mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (hazard, cargo) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and args.cargo:
        hazard = HAZARDS[args.hazard]
        cargo = CARGOS[args.cargo]
        if not cargo_at_risk(hazard, cargo) or select_carrier(hazard, cargo) is None:
            raise StoryError(explain_rejection(hazard, cargo))

    combos = [
        combo
        for combo in valid_combos()
        if (args.hazard is None or combo[0] == args.hazard)
        and (args.cargo is None or combo[1] == args.cargo)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hazard_id, cargo_id = rng.choice(sorted(combos))
    carrier = select_carrier(HAZARDS[hazard_id], CARGOS[cargo_id])
    if carrier is None:
        raise StoryError(explain_rejection(HAZARDS[hazard_id], CARGOS[cargo_id]))
    if args.carrier and args.carrier != carrier.id:
        raise StoryError(
            f"(No story: {args.carrier} is not the sensible carrier for {cargo_id} on {hazard_id}. "
            f"Try --carrier {carrier.id}.)"
        )

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        hazard=hazard_id,
        cargo=cargo_id,
        carrier=carrier.id,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Invalid hazard: {params.hazard})")
    if params.cargo not in CARGOS:
        raise StoryError(f"(Invalid cargo: {params.cargo})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Invalid carrier: {params.carrier})")

    chosen = select_carrier(HAZARDS[params.hazard], CARGOS[params.cargo])
    if chosen is None:
        raise StoryError(explain_rejection(HAZARDS[params.hazard], CARGOS[params.cargo]))
    if chosen.id != params.carrier:
        raise StoryError(
            f"(Invalid carrier for this story: {params.carrier} does not fit {params.hazard} + {params.cargo}; expected {chosen.id}.)"
        )

    world = tell(
        hazard=HAZARDS[params.hazard],
        cargo_cfg=CARGOS[params.cargo],
        carrier=CARRIERS[params.carrier],
        hero_name=params.name,
        hero_type=params.gender,
        elder_type=params.elder,
        trait=params.trait,
    )

    return StorySample(
        params=params,
        story=world.render().replace("hero", params.name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    text = sample.story.replace(" hero ", f" {sample.params.name} ")
    print(text)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hazard, cargo) pairs:\n")
        for hazard, cargo in combos:
            carrier = select_carrier(HAZARDS[hazard], CARGOS[cargo])
            show_carrier = carrier.id if carrier is not None else "?"
            print(f"  {hazard:10} {cargo:8} -> {show_carrier}")
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
            header = f"### {p.name}: {p.cargo} over {p.hazard} ({outcome_of(p)})"
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
