#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mattress_hospital_melanin_bad_ending_fairy_tale.py
=============================================================================

A standalone storyworld for a fairy-tale domain built from the seed words
"mattress", "hospital", and "melanin".

This world models a small cautionary tale: a child in a moonlit kingdom is told
a false beauty promise by a wandering seller. The seller claims that sleeping on
a strange mattress under moonlight will change the child's skin. A loving adult
and a royal healer know better: melanin is part of the child's body, not a flaw,
and the mattress is unsafe. If the child ignores the warning, the enchanted
stuffing can make the child very ill and send them to the royal hospital.

The simulation supports:
- a near-miss ending (the child listens and no harm happens),
- a contained sad ending (the child is treated in time and learns a hard lesson),
- a worse bad ending (help comes too late, and the tale ends in loss).

The world uses:
- typed entities with physical meters and emotional memes,
- a small reasonableness gate,
- an inline ASP twin for parity checking,
- generated prompts, story-grounded QA, and world-knowledge QA.

Run it
------
    python storyworlds/worlds/gpt-5.4/mattress_hospital_melanin_bad_ending_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/mattress_hospital_melanin_bad_ending_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/mattress_hospital_melanin_bad_ending_fairy_tale.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/mattress_hospital_melanin_bad_ending_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/mattress_hospital_melanin_bad_ending_fairy_tale.py --verify
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
HOPE_INIT = 5.0
WISE_TRAITS = {"careful", "steady", "kind", "thoughtful"}


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
    safe_for_skin: bool = False
    changes_melanin: bool = False
    healing_power: int = 0
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "witch", "healer"}
        male = {"boy", "father", "king", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "queen": "queen",
            "king": "king",
            "healer": "healer",
        }.get(self.type, self.label or self.type)


@dataclass
class Setting:
    id: str
    realm: str
    home: str
    moon_place: str
    hospital: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rumor:
    id: str
    seller: str
    boast: str
    promise: str
    lie_text: str
    harm_text: str
    skin_risk: int
    tags: set[str] = field(default_factory=set)


@dataclass
class MattressKind:
    id: str
    phrase: str
    filling: str
    danger_text: str
    softness: str
    safe_for_skin: bool
    changes_melanin: bool = False
    severity: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    method: str
    fail: str
    qa_text: str
    sense: int
    power: int
    hospital_text: str
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


def _r_skin_hurt(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    mattress = world.get("mattress")
    if child.meters["used_mattress"] < THRESHOLD:
        return out
    sig = ("skin_hurt",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if not mattress.safe_for_skin:
        child.meters["rash"] += 1
        child.meters["fever"] += float(mattress.attrs.get("severity", 1))
        child.memes["pain"] += 1
        child.memes["fear"] += 1
        out.append("__hurt__")
    else:
        child.memes["relief"] += 1
    return out


def _r_need_hospital(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["fever"] < THRESHOLD:
        return out
    sig = ("hospital",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hospital").meters["needed"] += 1
    world.get("caregiver").memes["worry"] += 1
    out.append("__hospital__")
    return out


CAUSAL_RULES = [
    Rule(name="skin_hurt", tag="physical", apply=_r_skin_hurt),
    Rule(name="need_hospital", tag="physical", apply=_r_need_hospital),
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


def hazardous(rumor: Rumor, mattress: MattressKind) -> bool:
    return rumor.skin_risk > 0 and not mattress.safe_for_skin


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def severity_of(rumor: Rumor, mattress: MattressKind, delay: int) -> int:
    return rumor.skin_risk + mattress.severity + delay


def can_save(helper: Helper, rumor: Rumor, mattress: MattressKind, delay: int) -> bool:
    return helper.power >= severity_of(rumor, mattress, delay)


def initial_wisdom(trait: str) -> float:
    return 5.0 if trait in WISE_TRAITS else 3.0


def would_listen(relation: str, wise_age: int, child_age: int, trait: str) -> bool:
    elder = relation == "siblings" and wise_age > child_age
    authority = initial_wisdom(trait) + (3.0 if elder else 0.0)
    return elder and authority > HOPE_INIT


def predict_harm(world: World) -> dict:
    sim = world.copy()
    try_mattress(sim, narrate=False)
    child = sim.get("child")
    return {
        "rash": child.meters["rash"] >= THRESHOLD,
        "fever": child.meters["fever"],
        "hospital": sim.get("hospital").meters["needed"] >= THRESHOLD,
    }


def introduce(world: World, setting: Setting, child: Entity, caregiver: Entity) -> None:
    world.say(
        f"In the silver kingdom of {setting.realm}, there stood {setting.home}, "
        f"where {child.id} lived with {child.pronoun('possessive')} {caregiver.label_word}."
    )
    world.say(
        f"{child.id} had skin warm as polished chestnuts, and the royal healer had once said "
        f"that melanin was part of the body's good design, helping skin keep safe in the sun."
    )


def longing(world: World, child: Entity, setting: Setting) -> None:
    child.memes["hope"] = HOPE_INIT
    world.say(
        f"All through the week, lanterns were being strung for the Moon-Feast in {setting.moon_place}, "
        f"and {child.id} wished to look as bright and admired as the moon itself."
    )


def seller_arrives(world: World, rumor: Rumor, mattress: MattressKind) -> None:
    world.say(
        f"One dusk, {rumor.seller} came down the lane with {mattress.phrase}, "
        f"stuffed with {mattress.filling}. {rumor.boast}"
    )
    world.say(f'"{rumor.promise}"')
    world.say("The promise sounded shiny and easy, which made it dangerous.")


def wise_warning(world: World, wise: Entity, child: Entity, caregiver: Entity,
                 rumor: Rumor, mattress: MattressKind) -> None:
    pred = predict_harm(world)
    world.facts["predicted_fever"] = pred["fever"]
    world.facts["predicted_hospital"] = pred["hospital"]
    wise.memes["care"] += 1
    extra = ""
    if wise.memes["wisdom"] >= 5:
        extra = " Melanin is not a stain to scrub away, and no true magic asks a child to be hurt."
    world.say(
        f'{wise.id} caught {child.id} staring at the mattress and said, '
        f'"Do not trust that boast. {rumor.lie_text} {mattress.danger_text}.{extra}"'
    )
    world.say(
        f'{caregiver.label_word.capitalize()} nodded and added, '
        f'"If anything burns or bites the skin, we go for help at once."'
    )


def refuse(world: World, child: Entity, wise: Entity, caregiver: Entity, setting: Setting) -> None:
    child.memes["shame"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{child.id} looked at {wise.id}, then at {child.pronoun('possessive')} own hands, "
        f"and the glittering wish inside {child.pronoun('object')} went quiet."
    )
    world.say(
        f'"I do not need a lying mattress," {child.pronoun()} whispered. '
        f'{caregiver.label_word.capitalize()} wrapped an arm around {child.pronoun("object")}.'
    )
    world.say(
        f"That night they walked to {setting.moon_place} under paper stars, and {child.id} felt small, "
        f"safe, and truly seen."
    )


def defy(world: World, child: Entity, wise: Entity, rumor: Rumor) -> None:
    child.memes["defiance"] += 1
    child.memes["hope"] += 1
    relation_note = ""
    if wise.attrs.get("relation") == "siblings" and wise.age > child.age:
        relation_note = f" Even though {wise.id} was older, {child.id} shook {child.pronoun('possessive')} head."
    world.say(
        f'But the false promise tugged harder than the warning. "{rumor.promise}" kept echoing in {child.id}\'s mind.{relation_note}'
    )


def midnight_choice(world: World, child: Entity, mattress: MattressKind, setting: Setting) -> None:
    world.say(
        f"When the house had gone still, {child.id} crept to the window nook in {setting.home} "
        f"and spread out {mattress.phrase}. It looked {mattress.softness}, and that made the trap worse."
    )


def try_mattress(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    child.meters["used_mattress"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(
            "The moon poured over the ticking cloth. For one breath, everything seemed calm."
        )
        if child.meters["rash"] >= THRESHOLD:
            world.say(
                "Then the child's skin began to sting as if hidden nettles were waking under the cloth, "
                "and a hot ache climbed into the night."
            )


def cry_for_help(world: World, caregiver: Entity, wise: Entity, child: Entity, setting: Setting) -> None:
    world.say(
        f'Before long, {child.id} could not hide the pain. "{caregiver.label_word.capitalize()}! {wise.id}!" '
        f'{child.pronoun().capitalize()} cried, and the quiet rooms of {setting.home} sprang awake.'
    )


def rush_to_hospital(world: World, caregiver: Entity, child: Entity, helper: Helper,
                     setting: Setting) -> None:
    child.memes["fear"] += 1
    caregiver.memes["fear"] += 1
    world.say(
        f"{caregiver.label_word.capitalize()} lifted {child.id} in a blanket and ran through the moonlit street "
        f"to {setting.hospital}. {helper.hospital_text}"
    )


def heal_in_time(world: World, helper: Helper, child: Entity, caregiver: Entity,
                 wise: Entity) -> None:
    child.meters["fever"] = 0.0
    child.meters["rash"] = max(0.0, child.meters["rash"] - 1.0)
    child.memes["pain"] = 0.0
    child.memes["relief"] += 1
    caregiver.memes["relief"] += 1
    wise.memes["relief"] += 1
    world.say(
        f"There, the {helper.label} {helper.method}. By dawn, the fever had turned back, though the lesson stayed."
    )
    world.say(
        f'{caregiver.label_word.capitalize()} kissed {child.id}\'s forehead and said, '
        f'"Your skin was never the wrong thing. The lie was."'
    )
    world.say(
        f"{child.id} wept softly and understood at last that no cruel promise had the right to bargain with {child.pronoun('possessive')} body."
    )


def fail_to_save(world: World, helper: Helper, child: Entity, caregiver: Entity,
                 wise: Entity, setting: Setting) -> None:
    child.meters["fever"] += 1
    child.meters["lost"] += 1
    world.say(
        f"But the harm had been given too much of a head start. The {helper.label} {helper.fail}."
    )
    world.say(
        f"At sunrise, the bells of {setting.realm} sounded low and slow, and {caregiver.label_word} "
        f"held {child.id}'s hand in the royal hospital with tears that would not stop."
    )
    world.say(
        f"{wise.id} never forgot that night, nor the hard truth that a lie about beauty can break more than a heart."
    )


def coda_sad(world: World, setting: Setting, child: Entity) -> None:
    world.say(
        f"Afterward, the moon still rose over {setting.moon_place}, but to everyone who remembered {child.id}, "
        f"it looked less like a prize and more like a warning."
    )


def tell(setting: Setting, rumor: Rumor, mattress_cfg: MattressKind, helper_cfg: Helper,
         child_name: str = "Nia", child_gender: str = "girl",
         wise_name: str = "Toma", wise_gender: str = "boy",
         caregiver_type: str = "mother", wise_trait: str = "careful",
         delay: int = 1, child_age: int = 6, wise_age: int = 8,
         relation: str = "siblings") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=["hopeful"],
        attrs={"relation": relation},
    ))
    wise = world.add(Entity(
        id=wise_name,
        kind="character",
        type=wise_gender,
        role="wise",
        traits=[wise_trait],
        attrs={"relation": relation},
    ))
    caregiver = world.add(Entity(
        id="caregiver",
        kind="character",
        type=caregiver_type,
        role="caregiver",
        label="the caregiver",
    ))
    hospital = world.add(Entity(
        id="hospital",
        kind="thing",
        type="hospital",
        label=setting.hospital,
    ))
    mattress = world.add(Entity(
        id="mattress",
        kind="thing",
        type="mattress",
        label="mattress",
        phrase=mattress_cfg.phrase,
        safe_for_skin=mattress_cfg.safe_for_skin,
        changes_melanin=mattress_cfg.changes_melanin,
        tags=set(mattress_cfg.tags),
        attrs={"severity": mattress_cfg.severity},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="healer",
        role="helper",
        label=helper_cfg.label,
        healing_power=helper_cfg.power,
        tags=set(helper_cfg.tags),
    ))

    child.age = child_age
    wise.age = wise_age
    wise.memes["wisdom"] = initial_wisdom(wise_trait)

    introduce(world, setting, child, caregiver)
    longing(world, child, setting)

    world.para()
    seller_arrives(world, rumor, mattress_cfg)
    wise_warning(world, wise, child, caregiver, rumor, mattress_cfg)

    listened = would_listen(relation, wise_age, child_age, wise_trait)
    if listened:
        world.para()
        refuse(world, child, wise, caregiver, setting)
        outcome = "averted"
        contained = True
    else:
        world.para()
        defy(world, child, wise, rumor)
        midnight_choice(world, child, mattress_cfg, setting)
        try_mattress(world, narrate=True)
        cry_for_help(world, caregiver, wise, child, setting)
        world.para()
        rush_to_hospital(world, caregiver, child, helper_cfg, setting)
        contained = can_save(helper_cfg, rumor, mattress_cfg, delay)
        if contained:
            heal_in_time(world, helper_cfg, child, caregiver, wise)
            outcome = "treated"
        else:
            fail_to_save(world, helper_cfg, child, caregiver, wise, setting)
            coda_sad(world, setting, child)
            outcome = "lost"

    world.facts.update(
        setting=setting,
        rumor=rumor,
        mattress_cfg=mattress_cfg,
        helper_cfg=helper_cfg,
        child=child,
        wise=wise,
        caregiver=caregiver,
        hospital=hospital,
        listened=listened,
        outcome=outcome,
        delay=delay,
        severity=severity_of(rumor, mattress_cfg, delay) if not listened else 0,
        needed_hospital=hospital.meters["needed"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "moonwell": Setting(
        id="moonwell",
        realm="Moonwell",
        home="the Blue Tower",
        moon_place="the Moon-Feast square",
        hospital="the Royal Lantern Hospital",
        tags={"moon", "hospital"},
    ),
    "starmeadow": Setting(
        id="starmeadow",
        realm="Starmeadow",
        home="the Willow House",
        moon_place="the silver bridge",
        hospital="the Starmeadow Hospital",
        tags={"moon", "hospital"},
    ),
    "glasshill": Setting(
        id="glasshill",
        realm="Glasshill",
        home="the Little East Keep",
        moon_place="the bell garden",
        hospital="the Glasshill Children's Hospital",
        tags={"moon", "hospital"},
    ),
}

RUMORS = {
    "moon_pale": Rumor(
        id="moon_pale",
        seller="a silver-tongued peddler",
        boast="He swore he sold moon-comfort finer than any royal pillow.",
        promise="Sleep here one night, and the moon will wash your skin pale and lovely.",
        lie_text="No mattress can change a person's melanin in a good or truthful way.",
        harm_text="The lie teaches children to distrust themselves.",
        skin_risk=2,
        tags={"melanin", "beauty_lie"},
    ),
    "snow_white": Rumor(
        id="snow_white",
        seller="an old market witch",
        boast="She jingled moon charms and called herself a fixer of faces.",
        promise="One night's sleep, and your skin will turn moon-white by morning.",
        lie_text="Melanin is part of your body, and trying to force it away is a dangerous lie.",
        harm_text="The lie can lead to real harm.",
        skin_risk=3,
        tags={"melanin", "beauty_lie"},
    ),
    "pearl_glow": Rumor(
        id="pearl_glow",
        seller="a wandering velvet merchant",
        boast="He smiled as if every false word had already been polished.",
        promise="Rest on this bed, and your skin will glow pale as a pearl before sunrise.",
        lie_text="A body is not improved by hurting it, and melanin is not dirt to be erased.",
        harm_text="The lie trades pain for praise.",
        skin_risk=2,
        tags={"melanin", "beauty_lie"},
    ),
}

MATTRESSES = {
    "nettles": MattressKind(
        id="nettles",
        phrase="a moon-stitched mattress",
        filling="frost-nettles and glitter dust",
        danger_text="The stuffing can sting skin and make a child terribly sick",
        softness="soft as cloud wool",
        safe_for_skin=False,
        severity=2,
        tags={"mattress", "rash"},
    ),
    "salt": MattressKind(
        id="salt",
        phrase="a pearl-colored mattress",
        filling="bitter crystal salt and silver flakes",
        danger_text="Those sharp grains can scrape skin raw and raise a burning fever",
        softness="smooth as a frozen pond",
        safe_for_skin=False,
        severity=3,
        tags={"mattress", "rash"},
    ),
    "thorns": MattressKind(
        id="thorns",
        phrase="a swan-white mattress",
        filling="moon-thorns hidden under velvet ticking",
        danger_text="The hidden thorns can bite through cloth and poison sleep with pain",
        softness="grand as a palace bed",
        safe_for_skin=False,
        severity=2,
        tags={"mattress", "rash"},
    ),
    "plain": MattressKind(
        id="plain",
        phrase="a plain straw mattress",
        filling="ordinary straw",
        danger_text="It does not carry the peddler's wicked trick",
        softness="simple and scratchy",
        safe_for_skin=True,
        severity=0,
        tags={"mattress"},
    ),
}

HELPERS = {
    "healer_salve": Helper(
        id="healer_salve",
        label="royal healer",
        method="washed the child's skin, cooled the fever, and laid healing salve over the burns",
        fail="worked through the night, but the poison-fever had gone too far",
        qa_text="washed the skin, cooled the fever, and used healing salve",
        sense=3,
        power=5,
        hospital_text="The royal lamps were lit one by one, and the doors flew open before them.",
        tags={"hospital", "healer"},
    ),
    "moon_physician": Helper(
        id="moon_physician",
        label="moon physician",
        method="called for cool cloths, medicine, and careful watching until the child's breath eased",
        fail="called for every remedy in the ward, but the fever would not turn",
        qa_text="used medicine, cool cloths, and careful watching",
        sense=3,
        power=4,
        hospital_text="Bootsteps rang over the stone floor as nurses hurried them into a bright room.",
        tags={"hospital", "healer"},
    ),
    "village_tea": Helper(
        id="village_tea",
        label="village herb-seller",
        method="poured bitter tea and muttered a guess over it",
        fail="could do little more than hope while the child worsened",
        qa_text="offered only bitter tea",
        sense=1,
        power=1,
        hospital_text="They stopped first at a little stall instead of going straight to the hospital.",
        tags={"tea"},
    ),
}

GIRL_NAMES = ["Nia", "Asha", "Mina", "Lila", "Suri", "Kemi", "Zora", "Tali"]
BOY_NAMES = ["Toma", "Ivo", "Mika", "Rafi", "Jalen", "Oren", "Sami", "Beno"]
WISE_TRAIT_OPTIONS = ["careful", "steady", "kind", "thoughtful", "curious", "dreamy"]


@dataclass
class StoryParams:
    setting: str
    rumor: str
    mattress: str
    helper: str
    child_name: str
    child_gender: str
    wise_name: str
    wise_gender: str
    caregiver: str
    wise_trait: str
    delay: int = 1
    child_age: int = 6
    wise_age: int = 8
    relation: str = "siblings"
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="moonwell",
        rumor="snow_white",
        mattress="salt",
        helper="moon_physician",
        child_name="Nia",
        child_gender="girl",
        wise_name="Toma",
        wise_gender="boy",
        caregiver="mother",
        wise_trait="careful",
        delay=2,
        child_age=6,
        wise_age=7,
        relation="friends",
    ),
    StoryParams(
        setting="starmeadow",
        rumor="moon_pale",
        mattress="nettles",
        helper="healer_salve",
        child_name="Asha",
        child_gender="girl",
        wise_name="Mika",
        wise_gender="boy",
        caregiver="father",
        wise_trait="kind",
        delay=0,
        child_age=5,
        wise_age=8,
        relation="siblings",
    ),
    StoryParams(
        setting="glasshill",
        rumor="pearl_glow",
        mattress="thorns",
        helper="healer_salve",
        child_name="Rafi",
        child_gender="boy",
        wise_name="Zora",
        wise_gender="girl",
        caregiver="mother",
        wise_trait="thoughtful",
        delay=1,
        child_age=6,
        wise_age=6,
        relation="friends",
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid in SETTINGS:
        for rid, rumor in RUMORS.items():
            for mid, mattress in MATTRESSES.items():
                for hid, helper in HELPERS.items():
                    if hazardous(rumor, mattress) and helper.sense >= SENSE_MIN:
                        combos.append((sid, rid, mid, hid))
    return combos


def explain_rejection(rumor: Rumor, mattress: MattressKind) -> str:
    if mattress.safe_for_skin:
        return (
            f"(No story: {mattress.phrase} is not dangerous enough for this cautionary tale. "
            f"If nothing harmful happens, there is no true hospital turn and no hard lesson.)"
        )
    if rumor.skin_risk <= 0:
        return (
            "(No story: this rumor carries no bodily risk, so the world has no honest danger to simulate.)"
        )
    return "(No story: this combination is not a harmful beauty lie.)"


def explain_helper(helper_id: str) -> str:
    helper = HELPERS[helper_id]
    better = ", ".join(sorted(h.id for h in sensible_helpers()))
    return (
        f"(Refusing helper '{helper_id}': it scores too low on common sense "
        f"(sense={helper.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_listen(params.relation, params.wise_age, params.child_age, params.wise_trait):
        return "averted"
    return "treated" if can_save(HELPERS[params.helper], RUMORS[params.rumor], MATTRESSES[params.mattress], params.delay) else "lost"


KNOWLEDGE = {
    "melanin": [
        (
            "What is melanin?",
            "Melanin is something your body makes that helps give skin, hair, and eyes some of their color. It is a normal and good part of the body."
        ),
        (
            "Is melanin a bad thing?",
            "No. Melanin is not dirt and not a mistake. It is a healthy part of how bodies are made."
        ),
    ],
    "mattress": [
        (
            "What is a mattress?",
            "A mattress is the soft part of a bed that people lie on to sleep. It should feel safe and comfortable, not strange or harmful."
        )
    ],
    "hospital": [
        (
            "What is a hospital?",
            "A hospital is a place where doctors and nurses help sick or hurt people. They use medicine, careful watching, and special tools to help bodies heal."
        )
    ],
    "healer": [
        (
            "What does a healer or doctor do?",
            "A healer or doctor looks after people who are hurt or sick and tries to make them better. They use knowledge and care, not tricks."
        )
    ],
    "beauty_lie": [
        (
            "Why is it wrong to hurt yourself to look different?",
            "Because your body deserves care, not pain. Anyone who asks you to suffer so you can be praised is offering a cruel lie."
        )
    ],
    "rash": [
        (
            "What is a rash?",
            "A rash is when skin gets sore, red, or itchy because something has hurt or irritated it. A grown-up or doctor should help."
        )
    ],
}
KNOWLEDGE_ORDER = ["melanin", "mattress", "hospital", "healer", "beauty_lie", "rash"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    outcome = f["outcome"]
    rumor = f["rumor"]
    if outcome == "averted":
        return [
            f'Write a fairy tale for young children that includes the words "mattress", "hospital", and "melanin", but where the child listens in time and no one is harmed.',
            f"Tell a moonlit cautionary fairy tale where {child.id} hears a cruel promise about changing {child.pronoun('possessive')} skin, then learns that melanin is not something to erase.",
            f"Write a gentle fairy tale set in {setting.realm} where a false beauty seller is refused and the ending proves that the child was already enough.",
        ]
    if outcome == "lost":
        return [
            f'Write a bad-ending fairy tale that includes the words "mattress", "hospital", and "melanin".',
            f"Tell a sorrowful fairy tale where a child believes {rumor.promise.lower()} and the lie leads to the hospital too late.",
            f"Write a cautionary fairy tale about beauty, harm, and truth, ending with a lasting loss instead of a happy rescue.",
        ]
    return [
        f'Write a sad fairy tale for young children that includes the words "mattress", "hospital", and "melanin".',
        f"Tell a fairy tale where a child believes a cruel promise about skin, is hurt by a mattress, and learns the truth in the hospital.",
        f"Write a moonlit cautionary story in which a family reaches the hospital in time, but only after a painful mistake.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    wise = f["wise"]
    caregiver = f["caregiver"]
    rumor = f["rumor"]
    mattress = f["mattress_cfg"]
    helper = f["helper_cfg"]
    setting = f["setting"]
    out = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child in {setting.realm}, the loving grown-up at home, and {wise.id}, who tried to give a wise warning."
        ),
        (
            "What lie did the seller tell?",
            f"The seller claimed that a mattress could change {child.id}'s skin and wash away melanin. That was a lie, because melanin is part of the body and not something a child should try to erase."
        ),
        (
            f"Why did {wise.id} warn {child.id}?",
            f"{wise.id} knew the promise was false and dangerous. {wise.pronoun().capitalize()} also understood that the mattress could hurt skin and make {child.id} sick enough to need the hospital."
        ),
    ]
    if out == "averted":
        qa.append(
            (
                f"What did {child.id} do after the warning?",
                f"{child.id} gave up the cruel idea and stayed away from the mattress. That choice kept {child.pronoun('possessive')} body safe and ended the danger before it began."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly and safely. {child.id} went out under the festival lights feeling truly seen, instead of trying to change what never needed fixing."
            )
        )
    elif out == "treated":
        qa.append(
            (
                f"What happened when {child.id} lay on the mattress?",
                f"{child.id}'s skin began to sting and a fever rose, so the family rushed to the hospital. The pain came from trusting a harmful lie and using an unsafe mattress."
            )
        )
        qa.append(
            (
                f"How did the {helper.label} help?",
                f"The {helper.label} {helper.qa_text}. That treatment turned the danger back before it became even worse."
            )
        )
        qa.append(
            (
                f"What lesson did {child.id} learn?",
                f"{child.id} learned that melanin was never a problem and that beauty should never cost pain. The real wrong thing in the story was the lie, not the child's skin."
            )
        )
    else:
        qa.append(
            (
                f"Could the family save {child.id} in time?",
                f"No. They reached the hospital, but the harm had already grown too great. The bad ending shows what can happen when a cruel lie is believed too late into the night."
            )
        )
        qa.append(
            (
                "Why is this a bad ending?",
                f"It is a bad ending because the child is lost, and the family is left with grief instead of relief. The final image turns the moon from a prize into a warning about false beauty promises."
            )
        )
        qa.append(
            (
                "What is the story warning children about?",
                f"It warns children not to trust anyone who says they must hurt their body to become worthy or beautiful. It also says clearly that melanin is not something bad to erase."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["rumor"].tags) | set(f["mattress_cfg"].tags)
    if f["outcome"] in {"treated", "lost"}:
        tags |= set(f["helper_cfg"].tags) | {"hospital", "healer"}
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
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if getattr(e, "age", 0):
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(R, M) :- rumor(R), mattress(M), risk(R, RR), RR > 0, unsafe(M).
sensible(H)  :- helper(H), sense(H, S), sense_min(MN), S >= MN.
valid(S, R, M, H) :- setting(S), hazard(R, M), sensible(H).

wise_now(T)  :- trait(T), wise_trait(T).
init_wisdom(5) :- trait(T), wise_now(T).
init_wisdom(3) :- trait(T), not wise_now(T).
older_sib :- relation(siblings), wise_age(WA), child_age(CA), WA > CA.
bonus(3)  :- older_sib.
bonus(0)  :- not older_sib.
authority(W + B) :- init_wisdom(W), bonus(B).
listened :- older_sib, authority(A), hope_init(H), A > H.

severity(RR + MS + D) :- chosen_rumor(R), risk(R, RR), chosen_mattress(M), mseverity(M, MS), delay(D).
contained :- chosen_helper(H), power(H, P), severity(V), P >= V.

outcome(averted) :- listened.
outcome(treated) :- not listened, contained.
outcome(lost)    :- not listened, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, rumor in RUMORS.items():
        lines.append(asp.fact("rumor", rid))
        lines.append(asp.fact("risk", rid, rumor.skin_risk))
    for mid, mattress in MATTRESSES.items():
        lines.append(asp.fact("mattress", mid))
        lines.append(asp.fact("mseverity", mid, mattress.severity))
        if not mattress.safe_for_skin:
            lines.append(asp.fact("unsafe", mid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, helper.sense))
        lines.append(asp.fact("power", hid, helper.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("hope_init", int(HOPE_INIT)))
    for trait in sorted(WISE_TRAITS):
        lines.append(asp.fact("wise_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_helpers() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(h for (h,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_rumor", params.rumor),
            asp.fact("chosen_mattress", params.mattress),
            asp.fact("chosen_helper", params.helper),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("wise_age", params.wise_age),
            asp.fact("child_age", params.child_age),
            asp.fact("trait", params.wise_trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    py_helpers = {h.id for h in sensible_helpers()}
    asp_helpers = set(asp_sensible_helpers())
    if py_helpers == asp_helpers:
        print(f"OK: sensible helpers match ({sorted(py_helpers)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible helpers: python={sorted(py_helpers)} clingo={sorted(asp_helpers)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "melanin" not in sample.story.lower() or "mattress" not in sample.story.lower():
            raise StoryError("smoke test story missing required story content")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale cautionary storyworld: a false beauty promise, a dangerous mattress, and the truth about melanin."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rumor", choices=RUMORS)
    ap.add_argument("--mattress", choices=MATTRESSES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--caregiver", choices=["mother", "father", "queen", "king"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mattress and MATTRESSES[args.mattress].safe_for_skin:
        rumor = RUMORS[args.rumor] if args.rumor else next(iter(RUMORS.values()))
        raise StoryError(explain_rejection(rumor, MATTRESSES[args.mattress]))
    if args.rumor and args.mattress:
        rumor = RUMORS[args.rumor]
        mattress = MATTRESSES[args.mattress]
        if not hazardous(rumor, mattress):
            raise StoryError(explain_rejection(rumor, mattress))
    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        raise StoryError(explain_helper(args.helper))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.rumor is None or c[1] == args.rumor)
        and (args.mattress is None or c[2] == args.mattress)
        and (args.helper is None or c[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, rumor, mattress, helper = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    wise_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    wise_name = _pick_name(rng, wise_gender, avoid=child_name)
    caregiver = args.caregiver or rng.choice(["mother", "father", "queen", "king"])
    wise_trait = rng.choice(WISE_TRAIT_OPTIONS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    child_age, wise_age = rng.sample([4, 5, 6, 7, 8], 2)
    relation = rng.choice(["siblings", "friends"])
    return StoryParams(
        setting=setting,
        rumor=rumor,
        mattress=mattress,
        helper=helper,
        child_name=child_name,
        child_gender=child_gender,
        wise_name=wise_name,
        wise_gender=wise_gender,
        caregiver=caregiver,
        wise_trait=wise_trait,
        delay=delay,
        child_age=child_age,
        wise_age=wise_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.rumor not in RUMORS:
        raise StoryError(f"Unknown rumor: {params.rumor}")
    if params.mattress not in MATTRESSES:
        raise StoryError(f"Unknown mattress: {params.mattress}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    rumor = RUMORS[params.rumor]
    mattress = MATTRESSES[params.mattress]
    helper = HELPERS[params.helper]
    if not hazardous(rumor, mattress):
        raise StoryError(explain_rejection(rumor, mattress))
    if helper.sense < SENSE_MIN:
        raise StoryError(explain_helper(params.helper))

    world = tell(
        setting=SETTINGS[params.setting],
        rumor=rumor,
        mattress_cfg=mattress,
        helper_cfg=helper,
        child_name=params.child_name,
        child_gender=params.child_gender,
        wise_name=params.wise_name,
        wise_gender=params.wise_gender,
        caregiver_type=params.caregiver,
        wise_trait=params.wise_trait,
        delay=params.delay,
        child_age=params.child_age,
        wise_age=params.wise_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        helpers = asp_sensible_helpers()
        combos = asp_valid_combos()
        print(f"sensible helpers: {', '.join(helpers)}\n")
        print(f"{len(combos)} compatible (setting, rumor, mattress, helper) combos:\n")
        for setting, rumor, mattress, helper in combos:
            print(f"  {setting:10} {rumor:11} {mattress:8} {helper}")
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
            header = (
                f"### {p.child_name}: {p.rumor} / {p.mattress} / {outcome_of(p)} "
                f"at {p.setting}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
