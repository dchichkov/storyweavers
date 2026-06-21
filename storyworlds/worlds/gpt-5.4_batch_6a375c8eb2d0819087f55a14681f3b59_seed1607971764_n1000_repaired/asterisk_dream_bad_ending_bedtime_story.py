#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/asterisk_dream_bad_ending_bedtime_story.py
=====================================================================

A standalone story world for a small bedtime domain: a child wants a special
dream after seeing an asterisk in a bedtime book, hides a "dream charm" under a
pillow, and either sleeps well after a calm fix or sleeps badly and misses the
dream.

The world is deliberately narrow and state-driven:

- A charm under the pillow can be hard, noisy, or crumbly.
- Those physical properties create a bump, jingle, or crumbs.
- Discomfort at lights-out causes tossing, poor rest, and a missed dream.
- A sensible grown-up fix removes the charm from the pillow while keeping the
  wish nearby in a gentle bedtime way.

The inline ASP twin mirrors both the reasonableness gate and the simple outcome
model.

Run it
------
    python storyworlds/worlds/gpt-5.4/asterisk_dream_bad_ending_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/asterisk_dream_bad_ending_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/asterisk_dream_bad_ending_bedtime_story.py --qa --seed 7
    python storyworlds/worlds/gpt-5.4/asterisk_dream_bad_ending_bedtime_story.py --trace
    python storyworlds/worlds/gpt-5.4/asterisk_dream_bad_ending_bedtime_story.py --asp
    python storyworlds/worlds/gpt-5.4/asterisk_dream_bad_ending_bedtime_story.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    hard: bool = False
    noisy: bool = False
    crumbly: bool = False
    soft: bool = False
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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class DreamGoal:
    id: str
    wish: str
    image: str
    ending: str
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
class Charm:
    id: str
    label: str
    phrase: str
    tuck_text: str
    bump_text: str
    morning_text: str
    hard: bool = False
    noisy: bool = False
    crumbly: bool = False
    soft: bool = False
    severity: int = 1
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
class Remedy:
    id: str
    label: str
    phrase: str
    place_text: str
    keep_nearby_text: str
    qa_text: str
    sense: int = 2
    keeps_nearby: bool = True
    uses_asterisk: bool = False
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


def _r_bump(world: World) -> list[str]:
    charm = world.get("charm")
    pillow = world.get("pillow")
    if charm.attrs.get("under_pillow") and charm.hard:
        sig = ("bump", charm.id)
        if sig not in world.fired:
            world.fired.add(sig)
            pillow.meters["lumpy"] += 1
    return []


def _r_jingle(world: World) -> list[str]:
    charm = world.get("charm")
    room = world.get("room")
    if charm.attrs.get("under_pillow") and charm.noisy:
        sig = ("jingle", charm.id)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["noise"] += 1
    return []


def _r_crumbs(world: World) -> list[str]:
    charm = world.get("charm")
    pillow = world.get("pillow")
    if charm.attrs.get("under_pillow") and charm.crumbly:
        sig = ("crumbs", charm.id)
        if sig not in world.fired:
            world.fired.add(sig)
            pillow.meters["crumbs"] += 1
    return []


def _r_tossing(world: World) -> list[str]:
    child = world.get("child")
    pillow = world.get("pillow")
    room = world.get("room")
    if room.meters["lights_out"] < THRESHOLD:
        return []
    trouble = pillow.meters["lumpy"] + pillow.meters["crumbs"] + room.meters["noise"]
    if trouble < THRESHOLD:
        return []
    sig = ("tossing", int(trouble))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["tossing"] += 1
    child.meters["rest"] = 0.0
    child.meters["sleep_loss"] += 1
    child.memes["frustration"] += 1
    child.memes["hope"] = 0.0
    return []


def _r_dream(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    if room.meters["lights_out"] < THRESHOLD:
        return []
    if child.meters["sleep_loss"] >= THRESHOLD:
        return []
    sig = ("dream", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["rest"] += 1
    child.meters["dreamed"] += 1
    child.memes["peace"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="bump", tag="physical", apply=_r_bump),
    Rule(name="jingle", tag="physical", apply=_r_jingle),
    Rule(name="crumbs", tag="physical", apply=_r_crumbs),
    Rule(name="tossing", tag="physical", apply=_r_tossing),
    Rule(name="dream", tag="physical", apply=_r_dream),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        snapshot = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        if len(world.fired) != snapshot:
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def risky_charm(charm: Charm) -> bool:
    return charm.hard or charm.noisy or charm.crumbly


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN and r.keeps_nearby]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for goal_id in GOALS:
        for charm_id, charm in CHARMS.items():
            for remedy_id, remedy in REMEDIES.items():
                if risky_charm(charm) and remedy.sense >= SENSE_MIN and remedy.keeps_nearby:
                    combos.append((goal_id, charm_id, remedy_id))
    return combos


def is_peaceful(delay: int) -> bool:
    return delay == 0


def predict_sleep(world: World, charm_id: str, delay: int) -> dict:
    sim = world.copy()
    child = sim.get("child")
    charm = sim.get(charm_id)
    charm.attrs["under_pillow"] = True
    if delay > 0:
        sim.get("room").meters["lights_out"] += 1
    propagate(sim, narrate=False)
    return {
        "sleep_loss": child.meters["sleep_loss"],
        "rest": child.meters["rest"],
        "lumpy": sim.get("pillow").meters["lumpy"],
        "crumbs": sim.get("pillow").meters["crumbs"],
        "noise": sim.get("room").meters["noise"],
    }


def bedtime_setup(world: World, child: Entity, parent: Entity, goal: DreamGoal, pet: str) -> None:
    child.memes["hope"] += 1
    world.say(
        f"At bedtime, {child.id}'s {parent.label_word} read one last story in the soft lamp light."
    )
    world.say(
        f"On one page there was a tiny asterisk by the words about {goal.wish}, and {child.id} decided that meant a very special dream."
    )
    if pet:
        world.say(f"{pet.capitalize()} curled at the foot of the bed and listened to the pages turn.")


def wish_for_dream(world: World, child: Entity, goal: DreamGoal) -> None:
    world.say(
        f'"I want to dream about {goal.wish} tonight," {child.id} whispered.'
    )
    world.say(
        f"The wish felt so bright that it seemed to float over the pillow like a little silver thought."
    )


def hide_charm(world: World, child: Entity, charm: Entity, charm_cfg: Charm) -> None:
    child.memes["secrecy"] += 1
    charm.attrs["under_pillow"] = True
    world.say(
        f"When the room grew quieter, {child.id} slipped {charm_cfg.phrase} under the pillow. {charm_cfg.tuck_text}"
    )


def early_warning(world: World, parent: Entity, child: Entity, charm_cfg: Charm) -> None:
    pred = predict_sleep(world, "charm", delay=1)
    world.facts["predicted_trouble"] = pred
    child.memes["worry"] += 1
    details: list[str] = []
    if pred["lumpy"] >= THRESHOLD:
        details.append("a hard lump")
    if pred["crumbs"] >= THRESHOLD:
        details.append("scratchy crumbs")
    if pred["noise"] >= THRESHOLD:
        details.append("a tiny jingle")
    joined = ", ".join(details[:-1]) + (" and " if len(details) > 1 else "") + details[-1]
    world.say(
        f"{parent.label_word.capitalize()} smoothed the blanket, felt the hidden shape, and paused. "
        f'"Dreams do not come from secrets under pillows," {parent.pronoun()} said softly. '
        f'"That would make {joined}, and you would keep waking instead of sleeping."'
    )


def apply_remedy(world: World, parent: Entity, child: Entity, charm: Entity,
                 remedy: Remedy, goal: DreamGoal) -> None:
    charm.attrs["under_pillow"] = False
    charm.attrs["nearby"] = True
    child.memes["hope"] += 1
    child.memes["peace"] += 1
    world.say(
        f"{parent.label_word.capitalize()} lifted the pillow, took out the {charm.label}, and {remedy.place_text}."
    )
    if remedy.uses_asterisk:
        world.say(
            f"Then {parent.pronoun()} drew a neat little asterisk on a scrap of paper and set it beside the bed. "
            f'"There," {parent.pronoun()} smiled. "Now your wish can wait nearby while your body rests."'
        )
    else:
        world.say(
            f'{remedy.keep_nearby_text} "Your dream can stay close without sleeping on top of it," {parent.pronoun()} said.'
        )
    world.facts["remedy_used"] = remedy.id
    world.facts["goal_image"] = goal.image


def lights_out(world: World) -> None:
    world.get("room").meters["lights_out"] += 1
    propagate(world, narrate=False)


def peaceful_sleep(world: World, child: Entity, goal: DreamGoal) -> None:
    world.say(
        f"The room grew still. This time the pillow was soft, the blanket was smooth, and {child.id}'s breathing turned slow and even."
    )
    if child.meters["dreamed"] >= THRESHOLD:
        world.say(
            f"Soon the dream came at last: {goal.image}. {goal.ending}"
        )


def bad_night(world: World, child: Entity, charm_cfg: Charm) -> None:
    pillow = world.get("pillow")
    room = world.get("room")
    parts: list[str] = []
    if pillow.meters["lumpy"] >= THRESHOLD:
        parts.append(charm_cfg.bump_text)
    if pillow.meters["crumbs"] >= THRESHOLD:
        parts.append("little crumbs kept scratching the warm side of the pillow")
    if room.meters["noise"] >= THRESHOLD:
        parts.append("a faint jingle kept peeping out whenever the pillow moved")
    joined = "; ".join(parts)
    world.say(
        f"But sleep did not settle. {joined}, so {child.id} kept turning the pillow and opening tired eyes in the dark."
    )
    world.say(
        f"The special dream never came. Night slowly thinned into gray morning instead."
    )


def morning_discovery(world: World, parent: Entity, child: Entity, charm_cfg: Charm) -> None:
    child.memes["sadness"] += 1
    child.meters["yawn"] += 1
    world.say(
        f"In the morning, {parent.label_word} found {charm_cfg.morning_text}."
    )
    world.say(
        f'"Oh, sweetheart," {parent.pronoun()} said, "the {charm_cfg.label} did not bring a dream. It only stole your rest."'
    )
    world.say(
        f"{child.id} gave a long yawn and looked at the rumpled bed. The room was full of daylight, but {child.pronoun('possessive')} wish felt far away now."
    )


def late_comfort(world: World, parent: Entity, child: Entity, remedy: Remedy) -> None:
    world.say(
        f"{parent.label_word.capitalize()} moved the charm {remedy.place_text}."
    )
    if remedy.uses_asterisk:
        world.say(
            f"{parent.pronoun().capitalize()} added a paper asterisk beside it for the next night, but this night had already been used up."
        )
    else:
        world.say(
            f"{parent.pronoun().capitalize()} kept it nearby for another night, but this one could not be mended."
        )
    world.say(
        f"They promised to try the gentle way tomorrow, yet that morning began with heavy eyes instead of a dream."
    )
@dataclass
class StoryParams:
    goal: str
    charm: str
    remedy: str
    name: str
    gender: str
    parent: str
    trait: str
    delay: int = 1
    pet: str = ""
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "dream": [
        (
            "What is a dream?",
            "A dream is a story or picture your mind can make while you are asleep. Dreams come during sleep, not from staying awake and worrying."
        )
    ],
    "sleep": [
        (
            "Why do pillows need to feel soft and smooth at bedtime?",
            "A soft, smooth pillow helps your body stay comfortable and still. When something pokes, scratches, or jingles, it is harder to rest."
        )
    ],
    "asterisk": [
        (
            "What is an asterisk?",
            "An asterisk is a little star-shaped mark used in books and notes. It can show that something is special or that there is more to notice."
        )
    ],
    "pebble": [
        (
            "Why would a pebble under a pillow feel bad?",
            "A pebble is hard, so it makes a lump under your head. Hard lumps can wake you up instead of helping you sleep."
        )
    ],
    "bell": [
        (
            "Why can a bell make bedtime harder?",
            "A bell can make little sounds when it moves. Even a tiny jingle can keep a room from feeling calm and sleepy."
        )
    ],
    "biscuit": [
        (
            "Why are crumbs bad in a bed?",
            "Crumbs feel scratchy and messy against sheets and pillows. That can make it hard to settle down and sleep."
        )
    ],
    "key": [
        (
            "Why is a key not a good bedtime object under a pillow?",
            "A key is hard and poky, so it can press into the pillow. Bedtime goes better when the bed feels soft and safe."
        )
    ],
    "bedside": [
        (
            "Why is a bedside table better than under a pillow for a keepsake?",
            "A bedside table keeps something close without putting it under your head. That way you can keep the wish nearby and still sleep comfortably."
        )
    ],
    "moonlight": [
        (
            "What is moonlight?",
            "Moonlight is sunlight reflected off the moon. At night it can make a room look soft and silver."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "dream",
    "sleep",
    "asterisk",
    "pebble",
    "bell",
    "biscuit",
    "key",
    "bedside",
    "moonlight",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    goal = f["goal"]
    charm = f["charm_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "asterisk" and "dream". '
        f"The child wants to dream about {goal.wish} and hides {charm.phrase} under a pillow."
    )
    if outcome == "missed_dream":
        return [
            base,
            f"Tell a gentle bad-ending bedtime story where {child.id} tries to make a special dream happen with {charm.phrase}, but the plan ruins the night's sleep.",
            "Write a soft, child-facing cautionary story where a bedtime secret under the pillow leads to a tired morning instead of a dream.",
        ]
    return [
        base,
        f"Tell a soothing bedtime story where {child.id}'s parent notices the hidden charm, explains why it will disturb sleep, and offers a better bedtime ritual.",
        "Write a gentle story where a child learns that dreams come from resting, not from tucking objects under a pillow.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    goal = f["goal"]
    charm = f["charm_cfg"]
    remedy = f["remedy"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who wanted a special dream at bedtime, and {child.pronoun('possessive')} {pw}. The whole story turns on what {child.id} hid under the pillow."
        ),
        (
            f"What did {child.id} want that night?",
            f"{child.id} wanted to dream about {goal.wish}. The little asterisk in the bedtime book made the wish feel extra special."
        ),
        (
            f"What did {child.id} hide under the pillow?",
            f"{child.pronoun().capitalize()} hid {charm.phrase} under the pillow. {charm.tuck_text}"
        ),
    ]
    if f["outcome"] == "peaceful":
        pred = f.get("predicted_trouble", {})
        reasons: list[str] = []
        if pred.get("lumpy", 0) >= THRESHOLD:
            reasons.append("a hard lump")
        if pred.get("crumbs", 0) >= THRESHOLD:
            reasons.append("scratchy crumbs")
        if pred.get("noise", 0) >= THRESHOLD:
            reasons.append("a tiny jingle")
        joined = ", ".join(reasons[:-1]) + (" and " if len(reasons) > 1 else "") + reasons[-1]
        qa.append(
            (
                f"Why did {child.id}'s {pw} take the {charm.label} out from under the pillow?",
                f"{pw.capitalize()} knew it would make {joined}, which would keep {child.id} from resting. The fix worked because dreams come from sleep, not from sleeping on top of a charm."
            )
        )
        qa.append(
            (
                f"How did {child.id}'s {pw} help without throwing the wish away?",
                f"{pw.capitalize()} {remedy.qa_text}. That kept the wish nearby in a gentle way while making the bed soft again."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly and happily: {child.id} slept well and finally dreamed of {goal.wish}. The last image proves the change, because the dream came only after the pillow was made comfortable."
            )
        )
    else:
        causes: list[str] = []
        if f["lumpy"]:
            causes.append("a hard lump under the pillow")
        if f["crumbs"]:
            causes.append("scratchy crumbs in the pillow")
        if f["noisy"]:
            causes.append("a little jingle in the dark")
        joined = ", ".join(causes[:-1]) + (" and " if len(causes) > 1 else "") + causes[-1]
        qa.append(
            (
                f"Why did {child.id} miss the dream?",
                f"{child.id} missed the dream because {joined} kept the bed from feeling calm. Instead of sinking into sleep, {child.pronoun()} kept waking and turning over."
            )
        )
        qa.append(
            (
                f"What did {child.id}'s {pw} find in the morning?",
                f"{pw.capitalize()} found {charm.morning_text}. By then the night was already over, so the kind fix came too late to save that dream."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a tired morning, not with the wished-for dream. {child.id} learned that a secret under the pillow can steal rest instead of bringing magic."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"dream", "sleep", "asterisk"}
    charm_id = f["charm_cfg"].id
    if charm_id in KNOWLEDGE:
        tags.add(charm_id)
    remedy = f["remedy"]
    if remedy.id in {"dream_card", "moon_bowl"}:
        tags.add("bedside")
    if remedy.id == "window_shelf":
        tags.add("moonlight")
        tags.add("bedside")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("hard", ent.hard), ("noisy", ent.noisy),
                                       ("crumbly", ent.crumbly), ("soft", ent.soft)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        shown_attrs = {k: v for k, v in ent.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        goal="boats",
        charm="bell",
        remedy="dream_card",
        name="Nora",
        gender="girl",
        parent="mother",
        trait="dreamy",
        delay=1,
        pet="the cat",
    ),
    StoryParams(
        goal="rabbits",
        charm="pebble",
        remedy="moon_bowl",
        name="Theo",
        gender="boy",
        parent="father",
        trait="hopeful",
        delay=0,
        pet="",
    ),
    StoryParams(
        goal="whales",
        charm="biscuit",
        remedy="window_shelf",
        name="Maya",
        gender="girl",
        parent="mother",
        trait="quiet",
        delay=1,
        pet="the kitten",
    ),
    StoryParams(
        goal="boats",
        charm="key",
        remedy="dream_card",
        name="Finn",
        gender="boy",
        parent="father",
        trait="curious",
        delay=0,
        pet="the puppy",
    ),
]


def explain_rejection(charm: Charm) -> str:
    return (
        f"(No story: {charm.phrase} would not meaningfully disturb sleep under a pillow, "
        f"so there is no honest bedtime problem to solve. Pick a hard, noisy, or crumbly charm instead.)"
    )


def explain_remedy(remedy_id: str) -> str:
    remedy = REMEDIES[remedy_id]
    return (
        f"(Refusing remedy '{remedy_id}': it scores too low on common sense "
        f"(sense={remedy.sense} < {SENSE_MIN}). A bedtime fix should keep the wish nearby without leaving the bed uncomfortable.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "peaceful" if is_peaceful(params.delay) else "missed_dream"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
risky(C) :- charm(C), hard(C).
risky(C) :- charm(C), noisy(C).
risky(C) :- charm(C), crumbly(C).

sensible(R) :- remedy(R), sense(R,S), sense_min(M), S >= M, keeps_nearby(R).
valid(G,C,R) :- goal(G), risky(C), sensible(R).

% --- outcome model ---------------------------------------------------------
peaceful :- delay(0).
missed_dream :- delay(D), D > 0.

outcome(peaceful) :- peaceful.
outcome(missed_dream) :- missed_dream.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
    for charm_id, charm in CHARMS.items():
        lines.append(asp.fact("charm", charm_id))
        if charm.hard:
            lines.append(asp.fact("hard", charm_id))
        if charm.noisy:
            lines.append(asp.fact("noisy", charm_id))
        if charm.crumbly:
            lines.append(asp.fact("crumbly", charm_id))
        if charm.soft:
            lines.append(asp.fact("soft", charm_id))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
        if remedy.keeps_nearby:
            lines.append(asp.fact("keeps_nearby", remedy_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_remedies()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible remedies match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible remedies:")
        print("  clingo:", sorted(clingo_sensible))
        print("  python:", sorted(python_sensible))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child wants a special dream and learns what bedtime really needs."
    )
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = parent notices before sleep; 1 = too late, tired morning")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.charm and not risky_charm(CHARMS[args.charm]):
        raise StoryError(explain_rejection(CHARMS[args.charm]))
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_remedy(args.remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.goal is None or combo[0] == args.goal)
        and (args.charm is None or combo[1] == args.charm)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    goal, charm, remedy = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 1])

    return StoryParams(
        goal=goal,
        charm=charm,
        remedy=remedy,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        delay=delay,
        pet=rng.choice(PETS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")
    if params.charm not in CHARMS:
        raise StoryError(f"(Unknown charm: {params.charm})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent: {params.parent})")
    if params.delay not in {0, 1}:
        raise StoryError(f"(Invalid delay: {params.delay})")

    charm = CHARMS[params.charm]
    remedy = REMEDIES[params.remedy]
    if not risky_charm(charm):
        raise StoryError(explain_rejection(charm))
    if remedy.sense < SENSE_MIN or not remedy.keeps_nearby:
        raise StoryError(explain_remedy(params.remedy))

    world = tell(
        goal=GOALS[params.goal],
        charm_cfg=charm,
        remedy=remedy,
        child_name=params.name,
        child_type=params.gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible()
        combos = asp_valid_combos()
        print(f"sensible remedies: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (goal, charm, remedy) combos:\n")
        for goal, charm, remedy in combos:
            print(f"  {goal:8} {charm:10} {remedy}")
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
            header = f"### {p.name}: {p.goal}, {p.charm}, {p.remedy} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(goal: DreamGoal, charm_cfg: Charm, remedy: Remedy,
         child_name: str = "Nora", child_type: str = "girl",
         parent_type: str = "mother", trait: str = "sleepy",
         delay: int = 1, pet: str = "") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        traits=[trait],
        attrs={"pet": pet},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
        attrs={},
    ))
    world.add(Entity(id="room", type="room", label="bedroom", attrs={}))
    world.add(Entity(id="pillow", type="pillow", label="pillow", attrs={}))
    charm = world.add(Entity(
        id="charm",
        type="charm",
        label=charm_cfg.label,
        attrs={"under_pillow": False, "nearby": False},
        hard=charm_cfg.hard,
        noisy=charm_cfg.noisy,
        crumbly=charm_cfg.crumbly,
        soft=charm_cfg.soft,
    ))

    world.facts.update(
        goal=goal,
        charm_cfg=charm_cfg,
        remedy=remedy,
        child=child,
        parent=parent,
        delay=delay,
        pet=pet,
    )

    bedtime_setup(world, child, parent, goal, pet)
    wish_for_dream(world, child, goal)

    world.para()
    hide_charm(world, child, charm, charm_cfg)

    if delay == 0:
        early_warning(world, parent, child, charm_cfg)
        world.para()
        apply_remedy(world, parent, child, charm, remedy, goal)
        lights_out(world)
        peaceful_sleep(world, child, goal)
        outcome = "peaceful"
    else:
        world.para()
        lights_out(world)
        bad_night(world, child, charm_cfg)
        world.para()
        morning_discovery(world, parent, child, charm_cfg)
        late_comfort(world, parent, child, remedy)
        outcome = "missed_dream"

    world.facts.update(
        outcome=outcome,
        dreamed=child.meters["dreamed"] >= THRESHOLD,
        sleep_loss=child.meters["sleep_loss"] >= THRESHOLD,
        lumpy=world.get("pillow").meters["lumpy"] >= THRESHOLD,
        crumbs=world.get("pillow").meters["crumbs"] >= THRESHOLD,
        noisy=world.get("room").meters["noise"] >= THRESHOLD,
    )
    return world


GOALS = {
    "whales": DreamGoal(
        id="whales",
        wish="whales swimming under the moon",
        image="blue whales sailed through the sky as if the stars were a deep, quiet sea",
        ending="Even in sleep, everything moved slowly and kindly.",
        tags={"dream", "ocean"},
    ),
    "rabbits": DreamGoal(
        id="rabbits",
        wish="rabbits in silver slippers",
        image="small rabbits bounced across a moonlit meadow with dew on their ears",
        ending="The meadow felt hushed, as if the whole night were tiptoeing.",
        tags={"dream", "animals"},
    ),
    "boats": DreamGoal(
        id="boats",
        wish="a boat floating through clouds",
        image="a little boat drifted between soft white clouds and sleepy stars",
        ending="Nothing hurried; the whole sky rocked like a cradle.",
        tags={"dream", "clouds"},
    ),
}

CHARMS = {
    "pebble": Charm(
        id="pebble",
        label="pebble",
        phrase="a smooth gray pebble",
        tuck_text="It seemed solid and important, like the sort of thing that ought to hold a wish in place.",
        bump_text="the pebble made a stubborn little lump",
        morning_text="the gray pebble tucked under the pillowcase",
        hard=True,
        severity=2,
        tags={"pebble", "hard"},
    ),
    "bell": Charm(
        id="bell",
        label="bell",
        phrase="a tiny brass bell",
        tuck_text="It looked bright in the lamplight, and the child thought a bright thing might call a dream closer.",
        bump_text="the bell pressed into the pillow",
        morning_text="the brass bell hidden under the pillow",
        hard=True,
        noisy=True,
        severity=3,
        tags={"bell", "sound"},
    ),
    "biscuit": Charm(
        id="biscuit",
        label="biscuit",
        phrase="half a butter biscuit",
        tuck_text="The child had heard grown-ups say sweet things make sweet dreams, and mixed that up in a sleepy mind.",
        bump_text="the biscuit broke into rough little pieces under the weight of a turning head",
        morning_text="crumbs and a squashed bit of biscuit under the pillow",
        crumbly=True,
        severity=2,
        tags={"biscuit", "crumbs"},
    ),
    "key": Charm(
        id="key",
        label="key",
        phrase="an old toy key",
        tuck_text="It felt like the right shape to unlock a dream.",
        bump_text="the key poked through the pillow like a stiff little elbow",
        morning_text="the toy key hidden in the pillow fold",
        hard=True,
        severity=2,
        tags={"key", "hard"},
    ),
    "felt_star": Charm(
        id="felt_star",
        label="felt star",
        phrase="a soft felt star",
        tuck_text="It was so light that it hardly changed the pillow at all.",
        bump_text="the star barely made a bump",
        morning_text="the soft felt star still tucked neatly under the pillow",
        soft=True,
        severity=0,
        tags={"soft", "star"},
    ),
}

REMEDIES = {
    "dream_card": Remedy(
        id="dream_card",
        label="dream card",
        phrase="a little dream card",
        place_text="set it on the bedside table beside a little dream card",
        keep_nearby_text='The wish was still close enough to keep company with the room.',
        qa_text="moved the charm to the bedside table and added a paper asterisk",
        sense=3,
        keeps_nearby=True,
        uses_asterisk=True,
        tags={"paper", "asterisk"},
    ),
    "moon_bowl": Remedy(
        id="moon_bowl",
        label="moon bowl",
        phrase="a moon bowl",
        place_text="placed it in a small moon-painted bowl on the nightstand",
        keep_nearby_text='The bowl shone softly in the lamplight, so the wish still felt close.',
        qa_text="placed the charm in a small bowl on the nightstand",
        sense=2,
        keeps_nearby=True,
        uses_asterisk=False,
        tags={"bowl", "bedside"},
    ),
    "window_shelf": Remedy(
        id="window_shelf",
        label="window shelf",
        phrase="the window shelf",
        place_text="stood it on the window shelf where the moonlight could touch it",
        keep_nearby_text='Moonlight reached it there, and that was near enough for wishing.',
        qa_text="set the charm on the window shelf in the moonlight",
        sense=2,
        keeps_nearby=True,
        uses_asterisk=False,
        tags={"window", "moonlight"},
    ),
    "pocket": Remedy(
        id="pocket",
        label="pajama pocket",
        phrase="a pajama pocket",
        place_text="slipped it into the pajama pocket hanging from the bedpost",
        keep_nearby_text= """It stayed close, but not under the child's head.""",
        qa_text="slipped the charm into a hanging pocket by the bed",
        sense=1,
        keeps_nearby=True,
        uses_asterisk=False,
        tags={"pocket"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Maya", "Ella", "Rose", "Anna", "Lucy", "Ivy"]
BOY_NAMES = ["Theo", "Ben", "Noah", "Eli", "Finn", "Sam", "Leo", "Jack"]
TRAITS = ["sleepy", "hopeful", "gentle", "curious", "quiet", "dreamy"]
PETS = ["the cat", "the puppy", "the little dog", "the kitten", ""]

if __name__ == "__main__":
    main()
