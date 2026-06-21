#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/russian_foreshadowing_fable.py
=========================================================

A standalone story world for small fable-like tales about a proud little animal,
an ominous crossing, and a warning that proves true. One prize is often a little
russian doll from the market, so the required seed word appears naturally inside
the story world rather than as a glued-on token.

The stories are built from simulated state:
- physical meters: strain, wobble, wet, cracked, safe_home
- emotional memes: pride, caution, fear, relief, wisdom

Core shape:
    a childlike animal gets a market prize
    a dangerous shortcut gives an early warning
    a wiser friend notices the sign and offers a safer way
    the hero either listens, or learns too late
    the ending image proves what changed

Run it:
    python storyworlds/worlds/gpt-5.4/russian_foreshadowing_fable.py
    python storyworlds/worlds/gpt-5.4/russian_foreshadowing_fable.py --all
    python storyworlds/worlds/gpt-5.4/russian_foreshadowing_fable.py --qa --seed 7
    python storyworlds/worlds/gpt-5.4/russian_foreshadowing_fable.py --verify
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
RISK_MIN = 3
SENSE_MIN = 2
PROUD_TRAITS = {"proud", "boastful", "hasty"}
WISE_HELPERS = {"tortoise", "beaver"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Crossing:
    id: str
    label: str
    scene: str
    warning: str
    sign: str
    risk: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Bundle:
    id: str
    label: str
    phrase: str
    weight: int
    fragile: int
    joy_text: str
    ending_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    power: int
    proactive: str
    rescue: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_strain_to_danger(world: World) -> list[str]:
    out: list[str] = []
    crossing = world.get("crossing")
    hero = world.get("hero")
    helper = world.get("helper")
    if crossing.meters["strain"] >= THRESHOLD:
        sig = ("danger",)
        if sig not in world.fired:
            world.fired.add(sig)
            crossing.meters["danger"] += 1
            hero.memes["fear"] += 1
            helper.memes["urgency"] += 1
            out.append("__danger__")
    return out


def _r_drop_to_damage(world: World) -> list[str]:
    out: list[str] = []
    bundle = world.get("bundle")
    if bundle.meters["dropped"] >= THRESHOLD:
        sig = ("damage",)
        if sig not in world.fired:
            world.fired.add(sig)
            bundle.meters["wet"] += 1
            if bundle.attrs.get("fragile", 0) > 0:
                bundle.meters["cracked"] += 1
            out.append("__damage__")
    return out


CAUSAL_RULES = [
    Rule(name="strain_to_danger", tag="physical", apply=_r_strain_to_danger),
    Rule(name="drop_to_damage", tag="physical", apply=_r_drop_to_damage),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def hazard_level(crossing: Crossing, bundle: Bundle) -> int:
    return crossing.risk + bundle.weight


def hazard_at_risk(crossing: Crossing, bundle: Bundle) -> bool:
    return hazard_level(crossing, bundle) >= RISK_MIN


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def helper_authority(helper_kind: str) -> int:
    return 2 if helper_kind in WISE_HELPERS else 0


def would_heed(hero_trait: str, helper_kind: str) -> bool:
    if hero_trait not in PROUD_TRAITS:
        return True
    return helper_authority(helper_kind) >= 2


def is_contained(crossing: Crossing, bundle: Bundle, fix: Fix) -> bool:
    return fix.power >= hazard_level(crossing, bundle)


def predict_slip(world: World) -> dict:
    sim = world.copy()
    crossing = sim.get("crossing")
    bundle = sim.get("bundle")
    crossing.meters["strain"] += 1
    bundle.meters["dropped"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("crossing").meters["danger"],
        "wet": sim.get("bundle").meters["wet"],
        "cracked": sim.get("bundle").meters["cracked"],
    }


def introduce(world: World, hero: Entity, bundle_cfg: Bundle) -> None:
    world.say(
        f"In a little market town, {hero.id} the {hero.type} came hurrying home with "
        f"{bundle_cfg.phrase}. {bundle_cfg.joy_text}"
    )


def market_goal(world: World, hero: Entity, bundle_cfg: Bundle) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} wanted to reach the hillside before supper so everyone could see "
        f"the treasure at once."
    )


def approach(world: World, hero: Entity, helper: Entity, crossing_cfg: Crossing) -> None:
    world.say(
        f"The quickest way home was over {crossing_cfg.scene}. Beside it stood "
        f"{helper.id} the {helper.type}, who was listening to the water below."
    )
    world.say(
        f"{crossing_cfg.warning.capitalize()}, and {crossing_cfg.sign}."
    )


def foreshadow_warning(world: World, hero: Entity, helper: Entity, crossing_cfg: Crossing, bundle_cfg: Bundle) -> None:
    pred = predict_slip(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_wet"] = pred["wet"]
    world.facts["predicted_cracked"] = pred["cracked"]
    helper.memes["caution"] += 1
    world.say(
        f'"That crossing is telling on itself," said {helper.id}. "When wood complains '
        f"before your foot is on it, it is wiser to listen than to brag. If you rush "
        f"across with {bundle_cfg.label}, the stream will likely snatch a fright from you first."
    )


def boast(world: World, hero: Entity, crossing_cfg: Crossing) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'{hero.id} tossed {hero.pronoun("possessive")} chin. "A few creaks have never stopped me," '
        f"{hero.pronoun()} said."
    )


def accept_fix(world: World, hero: Entity, helper: Entity, fix_cfg: Fix, bundle_cfg: Bundle) -> None:
    hero.memes["relief"] += 1
    hero.memes["wisdom"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{hero.id} looked again at the trembling boards and felt smaller than {hero.pronoun("possessive")} boast. '
        f'"Very well," {hero.pronoun()} said. "Show me the wiser way."'
    )
    world.say(
        f"{helper.id} {fix_cfg.proactive}, and soon the two of them were on the far bank with "
        f"{bundle_cfg.label} safe and dry."
    )


def attempt_crossing(world: World, hero: Entity, crossing_cfg: Crossing, bundle_cfg: Bundle) -> None:
    crossing = world.get("crossing")
    bundle = world.get("bundle")
    crossing.meters["strain"] += 1
    bundle.meters["dropped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {hero.id} stepped onto {crossing_cfg.label}. At once it bowed, gave a sharp cry, "
        f"and threw a cold spray into the air. {bundle_cfg.label.capitalize()} slipped from "
        f"{hero.pronoun('possessive')} paws."
    )


def rescue_success(world: World, hero: Entity, helper: Entity, fix_cfg: Fix, bundle_cfg: Bundle) -> None:
    bundle = world.get("bundle")
    crossing = world.get("crossing")
    bundle.meters["saved"] += 1
    crossing.meters["danger"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["wisdom"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{helper.id} {fix_cfg.rescue}. In another breath, {bundle_cfg.label} was back on shore and "
        f"{hero.id} was trembling safely beside it."
    )


def rescue_fail(world: World, hero: Entity, helper: Entity, fix_cfg: Fix, bundle_cfg: Bundle) -> None:
    bundle = world.get("bundle")
    bundle.meters["lost"] += 1
    hero.memes["fear"] += 1
    hero.memes["sadness"] += 1
    hero.memes["wisdom"] += 1
    world.say(
        f"{helper.id} {fix_cfg.fail}. The stream spun once around {bundle_cfg.label} and carried it away "
        f"under the willow roots."
    )


def lesson_happy(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f'"A warning is a small kindness spoken early," said {helper.id}. '
        f'"Those who hear it need not learn the hard way."'
    )
    world.say(
        f"{hero.id} nodded. From then on, {hero.pronoun()} paid attention whenever a road, a roof, or a voice "
        f"gave a quiet sign before trouble grew loud."
    )


def lesson_sad(world: World, hero: Entity, helper: Entity, bundle_cfg: Bundle) -> None:
    world.say(
        f'{hero.id} watched the water close over the prize and whispered, "I thought the sound was only a sound."'
    )
    world.say(
        f'"So it was," said {helper.id}, "and that is how trouble often begins: not with a shout, but with a hint."'
    )
    world.say(
        f"After that day, whenever {hero.id} heard the first small warning, {hero.pronoun()} stopped to listen."
    )


def ending_image_safe(world: World, hero: Entity, helper: Entity, bundle_cfg: Bundle) -> None:
    bundle = world.get("bundle")
    bundle.meters["safe_home"] += 1
    world.say(
        f"That evening, {bundle_cfg.ending_text}, and {hero.id} shared the story of the creaking crossing more gladly "
        f"than any boast."
    )
    world.say("Moral: The ear that listens early saves the heart from late sorrow.")


def ending_image_loss(world: World, hero: Entity) -> None:
    world.say(
        f"At sunset, {hero.id} walked home with empty paws and a fuller mind."
    )
    world.say("Moral: He who laughs at the first warning may weep at the second.")
@dataclass
class StoryParams:
    crossing: str
    bundle: str
    fix: str
    hero_name: str
    hero_kind: str
    helper_name: str
    helper_kind: str
    hero_trait: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for crossing_id, crossing in CROSSINGS.items():
        for bundle_id, bundle in BUNDLES.items():
            if hazard_at_risk(crossing, bundle):
                combos.append((crossing_id, bundle_id))
    return combos


KNOWLEDGE = {
    "foreshadowing": [(
        "What is foreshadowing in a story?",
        "Foreshadowing is when a story gives a small early hint about something that will matter later. A creak, a crack, or a warning can make readers feel that trouble is coming."
    )],
    "warning": [(
        "Why can a small warning matter?",
        "A small warning can matter because little signs often come before bigger trouble. If you notice them early, you have more time to choose the safe thing."
    )],
    "bridge": [(
        "Why is a shaky bridge dangerous?",
        "A shaky bridge can bend, crack, or throw someone off balance. That is why people and animals should slow down and listen when it creaks."
    )],
    "log": [(
        "Why can an old log be slippery?",
        "An old log can be slippery because bark peels and moss grows on it. Even a careful step can slide if the top is worn smooth."
    )],
    "fragile": [(
        "What does fragile mean?",
        "Fragile means something can break easily if it is dropped or bumped. Glass jars and painted toys are often fragile."
    )],
    "raft": [(
        "What is a raft?",
        "A raft is a simple floating platform that helps carry things over water. It spreads weight and keeps a load out of the stream."
    )],
    "path": [(
        "Why is the longer safe path sometimes better?",
        "The longer safe path can be better because safety matters more than speed. A few extra steps can save you from a much bigger problem."
    )],
    "russian": [(
        "What is a russian doll?",
        "A russian doll is a painted toy doll, often made of wood. Some sets open up to show smaller dolls inside."
    )],
}
KNOWLEDGE_ORDER = ["foreshadowing", "warning", "bridge", "log", "fragile", "raft", "path", "russian"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    bundle_cfg = f["bundle_cfg"]
    crossing_cfg = f["crossing_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short fable for a 3-to-5-year-old that includes the word "{bundle_cfg.label.split()[-2] if "russian" in bundle_cfg.label else "warning"}" '
        f"and uses foreshadowing with a dangerous crossing."
    )
    if outcome == "heeded":
        return [
            base,
            f"Tell a fable where {hero.id} the {hero.type} notices a warning on {crossing_cfg.label} after {helper.id} the {helper.type} points it out, and chooses the wiser path.",
            f"Write a gentle fable in which an early hint of danger is believed in time, so the treasure reaches home safely."
        ]
    if outcome == "rescued":
        return [
            base,
            f"Tell a fable where {hero.id} the {hero.type} ignores a warning, nearly loses {bundle_cfg.label}, and is saved by {helper.id} the {helper.type}.",
            f"Write a story with foreshadowing where a small creak becomes a real problem, but a wise helper prevents a total loss."
        ]
    return [
        base,
        f"Tell a cautionary fable where {hero.id} the {hero.type} laughs at the warning on {crossing_cfg.label} and loses {bundle_cfg.label} in the stream.",
        f"Write a fable in which early signs of danger are ignored, and the ending teaches why hints should be heeded."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    crossing_cfg = f["crossing_cfg"]
    bundle_cfg = f["bundle_cfg"]
    fix_cfg = f["fix_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type}, who was carrying {bundle_cfg.label}, and {helper.id} the {helper.type}, who noticed danger first."
        ),
        (
            "What was the early warning in the story?",
            f"The early warning was that {crossing_cfg.warning}, and {crossing_cfg.sign}. Those small signs were foreshadowing because they hinted that the crossing would not hold safely."
        ),
        (
            f"Why did {helper.id} warn {hero.id}?",
            f"{helper.id} warned {hero.id} because the crossing was already showing strain before anyone stepped on it. The warning mattered because carrying {bundle_cfg.label} made the shortcut riskier."
        ),
    ]
    if outcome == "heeded":
        qa.append((
            f"How did {hero.id} solve the problem?",
            f"{hero.id} listened and let {helper.id} choose the safer way. They {fix_cfg.qa_text}, so the danger never got a chance to become a splash."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely, with {bundle_cfg.ending_text}. The ending proves that listening early changed what happened later."
        ))
    elif outcome == "rescued":
        qa.append((
            f"What happened when {hero.id} tried the shortcut?",
            f"The crossing bent and {bundle_cfg.label} slipped toward the stream. The danger that was hinted at before became real all at once."
        ))
        qa.append((
            f"How did {helper.id} help?",
            f"{helper.id} stepped in and {fix_cfg.qa_text}. That quick help turned a bad choice into a lesson instead of a loss."
        ))
        qa.append((
            f"What did {hero.id} learn?",
            f"{hero.id} learned that the first warning should have been enough. Small signs are easier to obey than big disasters are to fix."
        ))
    else:
        qa.append((
            f"What happened to {bundle_cfg.label}?",
            f"It was lost in the stream after the crossing gave way under the strain. The story lets the warning come true so the lesson feels real."
        ))
        qa.append((
            f"What did {hero.id} learn at the end?",
            f"{hero.id} learned that a hint of danger is not the same thing as an empty fear. By the end, {hero.pronoun()} understood that early warnings are meant to protect us."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"foreshadowing"}
    crossing_cfg = f["crossing_cfg"]
    bundle_cfg = f["bundle_cfg"]
    fix_cfg = f["fix_cfg"]
    tags |= set(crossing_cfg.tags) | set(bundle_cfg.tags)
    if f["outcome"] != "lost":
        tags |= set(fix_cfg.tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        crossing="reed_bridge",
        bundle="russian_doll",
        fix="beaver_raft",
        hero_name="Mila",
        hero_kind="mouse",
        helper_name="Orin",
        helper_kind="tortoise",
        hero_trait="proud",
        seed=1,
    ),
    StoryParams(
        crossing="old_log",
        bundle="berry_jar",
        fix="ford_stones",
        hero_name="Pip",
        hero_kind="rabbit",
        helper_name="Rill",
        helper_kind="otter",
        hero_trait="humble",
        seed=2,
    ),
    StoryParams(
        crossing="rope_span",
        bundle="melon_basket",
        fix="shout",
        hero_name="Bram",
        hero_kind="squirrel",
        helper_name="Vale",
        helper_kind="crow",
        hero_trait="boastful",
        seed=3,
    ),
    StoryParams(
        crossing="rope_span",
        bundle="seed_sack",
        fix="long_way",
        hero_name="Suri",
        hero_kind="hedgehog",
        helper_name="Moss",
        helper_kind="beaver",
        hero_trait="hasty",
        seed=4,
    ),
]


def explain_rejection(crossing: Crossing, bundle: Bundle) -> str:
    return (
        f"(No story: {crossing.label} with {bundle.label} is not risky enough for this fable. "
        f"The warning would not honestly foreshadow real trouble, so choose a shakier crossing or a heavier bundle.)"
    )


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.crossing not in CROSSINGS or params.bundle not in BUNDLES or params.fix not in FIXES:
        raise StoryError("(Invalid params: unknown crossing, bundle, or fix.)")
    if would_heed(params.hero_trait, params.helper_kind):
        return "heeded"
    return "rescued" if is_contained(CROSSINGS[params.crossing], BUNDLES[params.bundle], FIXES[params.fix]) else "lost"


ASP_RULES = r"""
hazard(C,B) :- crossing(C), bundle(B), crossing_risk(C,CR), bundle_weight(B,BW), CR + BW >= risk_min.
sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
valid(C,B) :- hazard(C,B).

wise_helper(H) :- helper_kind(H), authority(H,A), A >= 2.
heed :- hero_trait(T), not proud_trait(T).
heed :- hero_trait(T), proud_trait(T), chosen_helper(H), wise_helper(H).

severity(CR + BW) :- chosen_crossing(C), chosen_bundle(B), crossing_risk(C,CR), bundle_weight(B,BW).
contained :- chosen_fix(F), power(F,P), severity(S), P >= S.

outcome(heeded) :- heed.
outcome(rescued) :- not heed, contained.
outcome(lost) :- not heed, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, crossing in CROSSINGS.items():
        lines.append(asp.fact("crossing", cid))
        lines.append(asp.fact("crossing_risk", cid, crossing.risk))
    for bid, bundle in BUNDLES.items():
        lines.append(asp.fact("bundle", bid))
        lines.append(asp.fact("bundle_weight", bid, bundle.weight))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    for trait in sorted(HERO_TRAITS):
        lines.append(asp.fact("hero_trait_name", trait))
        if trait in PROUD_TRAITS:
            lines.append(asp.fact("proud_trait", trait))
    for kind in sorted(set(HELPER_KINDS)):
        lines.append(asp.fact("helper_kind", kind))
        lines.append(asp.fact("authority", kind, helper_authority(kind)))
    lines.append(asp.fact("risk_min", RISK_MIN))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(atom[0] for atom in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_crossing", params.crossing),
        asp.fact("chosen_bundle", params.bundle),
        asp.fact("chosen_fix", params.fix),
        asp.fact("hero_trait", params.hero_trait),
        asp.fact("chosen_helper", params.helper_kind),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable story world: an ominous crossing, an early warning, and the lesson of listening in time."
    )
    ap.add_argument("--crossing", choices=CROSSINGS)
    ap.add_argument("--bundle", choices=BUNDLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-kind", choices=HERO_KINDS)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-kind", choices=HELPER_KINDS)
    ap.add_argument("--hero-trait", choices=HERO_TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))
    if args.crossing and args.bundle:
        crossing = CROSSINGS[args.crossing]
        bundle = BUNDLES[args.bundle]
        if not hazard_at_risk(crossing, bundle):
            raise StoryError(explain_rejection(crossing, bundle))

    combos = [
        combo for combo in valid_combos()
        if (args.crossing is None or combo[0] == args.crossing)
        and (args.bundle is None or combo[1] == args.bundle)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    crossing_id, bundle_id = rng.choice(sorted(combos))
    fix_id = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    hero_kind = args.hero_kind or rng.choice(HERO_KINDS)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    helper_kind = args.helper_kind or rng.choice(HELPER_KINDS)
    hero_trait = args.hero_trait or rng.choice(HERO_TRAITS)

    return StoryParams(
        crossing=crossing_id,
        bundle=bundle_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_kind=hero_kind,
        helper_name=helper_name,
        helper_kind=helper_kind,
        hero_trait=hero_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.crossing not in CROSSINGS:
        raise StoryError(f"(Invalid crossing: {params.crossing})")
    if params.bundle not in BUNDLES:
        raise StoryError(f"(Invalid bundle: {params.bundle})")
    if params.fix not in FIXES:
        raise StoryError(f"(Invalid fix: {params.fix})")
    if params.hero_kind not in HERO_KINDS:
        raise StoryError(f"(Invalid hero kind: {params.hero_kind})")
    if params.helper_kind not in HELPER_KINDS:
        raise StoryError(f"(Invalid helper kind: {params.helper_kind})")
    if params.hero_trait not in HERO_TRAITS:
        raise StoryError(f"(Invalid hero trait: {params.hero_trait})")

    crossing = CROSSINGS[params.crossing]
    bundle = BUNDLES[params.bundle]
    fix = FIXES[params.fix]

    if not hazard_at_risk(crossing, bundle):
        raise StoryError(explain_rejection(crossing, bundle))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    world = tell(
        crossing_cfg=crossing,
        bundle_cfg=bundle,
        fix_cfg=fix,
        hero_name=params.hero_name,
        hero_kind=params.hero_kind,
        helper_name=params.helper_name,
        helper_kind=params.helper_kind,
        hero_trait=params.hero_trait,
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

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: valid_combos() matches ASP ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sensible = set(asp_sensible())
    python_sensible = {fix.id for fix in sensible_fixes()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible fixes match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible fixes:")
        print("  clingo:", sorted(clingo_sensible))
        print("  python:", sorted(python_sensible))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            mismatches += 1
            print(f"MISMATCH outcome for {params}: python={py_out} asp={asp_out}")
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible()
        print(f"sensible fixes: {', '.join(sensible)}\n")
        print(f"{len(combos)} valid (crossing, bundle) combos:\n")
        for crossing_id, bundle_id in combos:
            print(f"  {crossing_id:12} {bundle_id}")
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
            header = f"### {p.hero_name}: {p.bundle} over {p.crossing} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    crossing_cfg: Crossing,
    bundle_cfg: Bundle,
    fix_cfg: Fix,
    hero_name: str = "Mila",
    hero_kind: str = "mouse",
    helper_name: str = "Orin",
    helper_kind: str = "tortoise",
    hero_trait: str = "proud",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_kind,
        label=hero_name,
        role="hero",
        traits=[hero_trait],
        attrs={},
        tags={hero_kind},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_kind,
        label=helper_name,
        role="helper",
        traits=["watchful"],
        attrs={},
        tags={helper_kind},
    ))
    crossing = world.add(Entity(
        id="crossing",
        kind="thing",
        type="crossing",
        label=crossing_cfg.label,
        role="crossing",
        attrs={"risk": crossing_cfg.risk},
        tags=set(crossing_cfg.tags),
    ))
    bundle = world.add(Entity(
        id="bundle",
        kind="thing",
        type="bundle",
        label=bundle_cfg.label,
        role="bundle",
        attrs={"weight": bundle_cfg.weight, "fragile": bundle_cfg.fragile},
        tags=set(bundle_cfg.tags),
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        crossing_cfg=crossing_cfg,
        bundle_cfg=bundle_cfg,
        fix_cfg=fix_cfg,
    )

    introduce(world, hero, bundle_cfg)
    market_goal(world, hero, bundle_cfg)

    world.para()
    approach(world, hero, helper, crossing_cfg)
    foreshadow_warning(world, hero, helper, crossing_cfg, bundle_cfg)

    heed = would_heed(hero_trait, helper_kind)
    contained = True
    outcome = "heeded"

    world.para()
    if heed:
        accept_fix(world, hero, helper, fix_cfg, bundle_cfg)
        lesson_happy(world, hero, helper)
        world.para()
        ending_image_safe(world, hero, helper, bundle_cfg)
    else:
        boast(world, hero, crossing_cfg)
        attempt_crossing(world, hero, crossing_cfg, bundle_cfg)
        contained = is_contained(crossing_cfg, bundle_cfg, fix_cfg)
        world.para()
        if contained:
            outcome = "rescued"
            rescue_success(world, hero, helper, fix_cfg, bundle_cfg)
            lesson_happy(world, hero, helper)
            world.para()
            ending_image_safe(world, hero, helper, bundle_cfg)
        else:
            outcome = "lost"
            rescue_fail(world, hero, helper, fix_cfg, bundle_cfg)
            lesson_sad(world, hero, helper, bundle_cfg)
            world.para()
            ending_image_loss(world, hero)

    world.facts.update(
        heed=heed,
        outcome=outcome,
        rescued=contained if not heed else False,
        lost=outcome == "lost",
        hazard=hazard_level(crossing_cfg, bundle_cfg),
    )
    return world


CROSSINGS = {
    "reed_bridge": Crossing(
        id="reed_bridge",
        label="the reed bridge",
        scene="a narrow reed bridge over the mill stream",
        warning="the ropes twanged like thin strings in the wind",
        sign="one board in the middle sagged like a sleepy tongue",
        risk=2,
        tags={"bridge", "warning"},
    ),
    "old_log": Crossing(
        id="old_log",
        label="the old log",
        scene="an old log laid from bank to bank",
        warning="the bark flaked under the lightest touch",
        sign="a dark crack ran along the top where many feet had passed",
        risk=1,
        tags={"log", "warning"},
    ),
    "rope_span": Crossing(
        id="rope_span",
        label="the rope span",
        scene="a thin rope span hung above a pebbled brook",
        warning="the planks knocked together before anyone stepped on them",
        sign="the far knot had loosened and showed pale threads",
        risk=3,
        tags={"bridge", "warning"},
    ),
}

BUNDLES = {
    "russian_doll": Bundle(
        id="russian_doll",
        label="the little russian doll",
        phrase="a little russian doll painted with red flowers",
        weight=2,
        fragile=2,
        joy_text="Its round smile peeped through a cloth wrap, and the toy felt delicate and precious.",
        ending_text="the little russian doll stood on the supper shelf, dry and shining in the lamplight",
        tags={"russian", "toy", "fragile"},
    ),
    "berry_jar": Bundle(
        id="berry_jar",
        label="the berry jar",
        phrase="a glass jar full of blackberries",
        weight=1,
        fragile=1,
        joy_text="The berries made the whole bundle smell like summer hedges.",
        ending_text="the berry jar waited on the table, purple and unbroken",
        tags={"jar", "fragile"},
    ),
    "seed_sack": Bundle(
        id="seed_sack",
        label="the seed sack",
        phrase="a stout sack of winter seeds",
        weight=2,
        fragile=0,
        joy_text="The sack was not pretty, but it promised full bowls when snow came.",
        ending_text="the seed sack rested by the pantry door, ready for careful days ahead",
        tags={"seeds"},
    ),
    "melon_basket": Bundle(
        id="melon_basket",
        label="the melon basket",
        phrase="a basket with one striped melon inside",
        weight=3,
        fragile=1,
        joy_text="It was so heavy that every shortcut looked tempting.",
        ending_text="the melon basket sat on the bench, safe for sharing",
        tags={"basket", "fragile"},
    ),
}

FIXES = {
    "ford_stones": Fix(
        id="ford_stones",
        label="ford stones",
        sense=3,
        power=3,
        proactive="led the way down to a line of broad ford stones where the water ran shallow",
        rescue="splashed onto the ford stones, braced the bundle with both paws, and nudged it back from the current",
        fail="hurried to the ford stones and reached with both paws, but the current had already taken the prize past reach",
        qa_text="used the shallow ford stones to get across safely",
        tags={"ford", "stones"},
    ),
    "beaver_raft": Fix(
        id="beaver_raft",
        label="beaver raft",
        sense=3,
        power=5,
        proactive="untied a flat little raft that the beavers kept for heavy loads",
        rescue="pushed the beaver raft into the stream and trapped the drifting bundle against its side",
        fail="pushed the beaver raft out, but the prize had already spun beneath the bank roots",
        qa_text="used a little beaver raft to keep the load from the water",
        tags={"raft", "beaver"},
    ),
    "long_way": Fix(
        id="long_way",
        label="long way",
        sense=2,
        power=4,
        proactive="pointed to the longer willow path where the ground was firm and the crossing broad",
        rescue="ran along the willow path to the lower bank and caught the bundle where the current slowed",
        fail="ran the long path to the lower bank, but the current was faster than paws and patience",
        qa_text="took the longer safe path instead of the shaky shortcut",
        tags={"path"},
    ),
    "shout": Fix(
        id="shout",
        label="shout",
        sense=1,
        power=1,
        proactive="called from the bank and hoped courage would act like a bridge",
        rescue="shouted advice from the bank",
        fail="shouted from the bank, but words alone could not stop water",
        qa_text="only shouted from the bank",
        tags={"warning"},
    ),
}

HERO_NAMES = ["Mila", "Pip", "Tavi", "Nora", "Bram", "Lio", "Suri", "Fen"]
HELPER_NAMES = ["Orin", "Moss", "Una", "Vale", "Tara", "Brindle", "Hush", "Rill"]
HERO_KINDS = ["mouse", "rabbit", "squirrel", "hedgehog"]
HELPER_KINDS = ["tortoise", "beaver", "otter", "crow"]
HERO_TRAITS = ["proud", "boastful", "hasty", "careful", "humble", "patient"]

if __name__ == "__main__":
    main()
