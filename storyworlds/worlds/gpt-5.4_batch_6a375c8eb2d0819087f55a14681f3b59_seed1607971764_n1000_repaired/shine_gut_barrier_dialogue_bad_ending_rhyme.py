#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shine_gut_barrier_dialogue_bad_ending_rhyme.py
=========================================================================

A standalone story world for a rhyming cautionary tale about a tempting shiny
snack behind a garden barrier. The child-facing lesson is simple: some food is
not ready or clean enough to eat yet, and a grown-up's warning matters.

The seed asked for:
- the words: shine, gut, barrier
- dialogue
- a bad ending
- a rhyming-story feel

This world models a lantern-night garden with tempting glowing fruit behind a
barrier. A child wants a quick bite. A cautious companion may stop them, but if
not, the child eats unsafe fruit, gets a stomachache, and misses the lantern
walk. The world uses explicit state for dirt, ripeness, pain, regret, trust,
fear, and comfort, then renders prose from that state.

Run it
------
    python storyworlds/worlds/gpt-5.4/shine_gut_barrier_dialogue_bad_ending_rhyme.py
    python storyworlds/worlds/gpt-5.4/shine_gut_barrier_dialogue_bad_ending_rhyme.py --fruit shineberries --patch compost_patch
    python storyworlds/worlds/gpt-5.4/shine_gut_barrier_dialogue_bad_ending_rhyme.py --patch washed_bowl
    python storyworlds/worlds/gpt-5.4/shine_gut_barrier_dialogue_bad_ending_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/shine_gut_barrier_dialogue_bad_ending_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/shine_gut_barrier_dialogue_bad_ending_rhyme.py --verify
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
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "steady"}
IMPULSE_INIT = 6.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    edible: bool = False
    washed: bool = False
    behind_barrier: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    glow: str
    path: str
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
class Fruit:
    id: str
    label: str
    phrase: str
    shine_word: str
    rhyme_line: str
    needs_wash: bool
    ripe_need: int
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
class Patch:
    id: str
    label: str
    barrier: str
    warning_sign: str
    dirt: int
    ripeness: int
    washed: bool
    behind_barrier: bool
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
class Comfort:
    id: str
    label: str
    phrase: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"eater", "warn_friend"}]

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


def _r_bad_bite(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    fruit = world.get("fruit")
    if child.meters["ate_bite"] < THRESHOLD:
        return out
    risk = fruit.meters["risk"]
    if risk < THRESHOLD:
        return out
    sig = ("bad_bite", int(risk))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["belly_pain"] += risk
    child.meters["rest_need"] += 1
    child.memes["fear"] += 1
    child.memes["regret"] += 1
    out.append("__belly__")
    return out


def _r_gut_barrier(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    fruit = world.get("fruit")
    if child.meters["belly_pain"] < THRESHOLD:
        return out
    sig = ("gut_barrier",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["gut_barrier_hurt"] += 1
    fruit.meters["trouble"] += 1
    out.append("__gut__")
    return out


def _r_missed_walk(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["belly_pain"] < THRESHOLD:
        return out
    sig = ("missed_walk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["missed_lantern_walk"] += 1
    child.memes["sadness"] += 1
    out.append("__missed__")
    return out


CAUSAL_RULES = [
    Rule(name="bad_bite", tag="physical", apply=_r_bad_bite),
    Rule(name="gut_barrier", tag="physical", apply=_r_gut_barrier),
    Rule(name="missed_walk", tag="social", apply=_r_missed_walk),
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


def fruit_risk(fruit: Fruit, patch: Patch) -> int:
    risk = 0
    if fruit.needs_wash and not patch.washed:
        risk += max(1, patch.dirt)
    if patch.ripeness < fruit.ripe_need:
        risk += fruit.ripe_need - patch.ripeness
    if patch.behind_barrier:
        risk += 1
    return risk


def hazard_at_risk(fruit: Fruit, patch: Patch) -> bool:
    return patch.behind_barrier and fruit_risk(fruit, patch) > 0


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, eater_age: int, friend_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and friend_age > eater_age
    authority = initial_caution(trait) + 1.0 + (4.0 if older_sibling else 0.0)
    return older_sibling and authority > IMPULSE_INIT


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["ate_bite"] += 1
    propagate(sim, narrate=False)
    return {
        "belly_pain": sim.get("child").meters["belly_pain"],
        "missed_walk": sim.get("child").meters["missed_lantern_walk"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, friend: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"At {setting.place}, lanterns learned to shine, and every little leaf looked fine. "
        f"{setting.glow}"
    )
    world.say(
        f'{child.id} skipped with {friend.id} down {setting.path}. '
        f'"What a twinkly, tinkly night," said {child.id}. "Everything glows soft and bright."'
    )


def see_treat(world: World, child: Entity, fruit: Fruit, patch: Patch) -> None:
    child.memes["desire"] += 1
    world.say(
        f"Then {child.id} saw {fruit.phrase} beyond {patch.barrier}. "
        f"{fruit.rhyme_line}"
    )
    world.say(
        f'"Oh, look!" cried {child.id}. "They shine, they gleam, they taste as sweet as any dream."'
    )


def warn(world: World, friend: Entity, child: Entity, fruit: Fruit, patch: Patch, grownup: Entity) -> None:
    pred = predict_trouble(world)
    friend.memes["caution"] += 1
    world.facts["predicted_belly_pain"] = pred["belly_pain"]
    world.facts["predicted_missed_walk"] = pred["missed_walk"]
    extra = ""
    if pred["missed_walk"]:
        extra = " If you nibble now, the lantern walk may pass you by."
    world.say(
        f'{friend.id} tugged {child.pronoun("possessive")} sleeve. '
        f'"Please wait," said {friend.id}. "{patch.warning_sign}. '
        f'{grownup.label_word.capitalize()} said not to pick from behind the barrier.{extra}"'
    )
    world.say(
        f'"Your gut has a little barrier too," {friend.pronoun()} added. '
        f'"When food is dirty or not ready, that barrier can feel sad and sore."'
    )


def defy(world: World, child: Entity, friend: Entity) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"Just one bite will be all right," said {child.id}. '
        f'"One quick chew, and then I\'m through."'
    )
    if child.attrs.get("relation") == "siblings" and child.age > friend.age:
        world.say(
            f"{friend.id} did not like it, but {child.id} was the older one, and the moment moved too fast to stop."
        )


def back_down(world: World, child: Entity, friend: Entity, grownup: Entity, comfort: Comfort) -> None:
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    child.memes["impulse"] = 0.0
    world.say(
        f'{child.id} looked at the fruit, then at {friend.id}, then gave a tiny sigh. '
        f'"All right," said {child.pronoun()}. "I will not try."'
    )
    world.say(
        f"{grownup.label_word.capitalize()} soon came by with {comfort.phrase}. "
        f"They shared it on a bench and watched the lanterns drift and fly."
    )


def bite(world: World, child: Entity, fruit_ent: Entity, fruit: Fruit, patch: Patch) -> None:
    child.meters["ate_bite"] += 1
    fruit_ent.meters["risk"] = float(fruit_risk(fruit, patch))
    fruit_ent.meters["dirt"] = float(patch.dirt)
    fruit_ent.meters["unripe"] = float(max(0, fruit.ripe_need - patch.ripeness))
    propagate(world, narrate=False)
    world.say(
        f"Before another word could land, {child.id} slipped a small one into {child.pronoun('possessive')} hand. "
        f"Crunch went the bite in the silver light, quick as a wink in the night."
    )


def ache(world: World, child: Entity) -> None:
    if child.meters["belly_pain"] >= THRESHOLD:
        world.say(
            f"At first {child.id} tried to grin, but soon a twist began within. "
            f'"My tummy feels wrong," {child.pronoun()} said. "A pinch, a plink, a heavy dread."'
        )
        world.say(
            f"{child.pronoun('Possessive') if False else child.pronoun('possessive').capitalize()} belly gave a grumble and a muttering sigh, "
            f"and all the music seemed too loud nearby."
        )


def help_and_explain(world: World, grownup: Entity, child: Entity, friend: Entity, comfort: Comfort) -> None:
    child.memes["fear"] += 1
    friend.memes["fear"] += 1
    child.memes["love"] += 1
    world.say(
        f'{grownup.label_word.capitalize()} hurried over. "{child.id}, come sit with me," {grownup.pronoun()} said softly. '
        f'{grownup.pronoun().capitalize()} wrapped {comfort.label} around {child.pronoun("object")} and rubbed {child.pronoun("possessive")} back.'
    )
    world.say(
        f'"The garden barrier was there for a reason," said {grownup.label_word}. '
        f'"Some fruit needs washing, some needs time, and a rushed bite can upset the gut barrier inside."'
    )


def bad_ending(world: World, child: Entity, friend: Entity, setting: Setting) -> None:
    child.memes["sadness"] += 1
    friend.memes["sadness"] += 1
    world.say(
        f"Outside, the lantern children sang in rhyme, and down {setting.path} went the shining line. "
        f"But {child.id} stayed on the bench instead, pale in the cheeks and heavy in the head."
    )
    world.say(
        f'{friend.id} squeezed {child.pronoun("possessive")} hand. '
        f'''"Next time we wait," said {friend.pronoun()}. "Then the night can end up bright."'.replace("Then the night can end up bright.", "Then the night can end up bright.")'''
    )
    world.say(
        f"So the lanterns went by with their gold little gleam, while {child.id} watched from afar and could only dream."
    )
@dataclass
class StoryParams:
    setting: str
    fruit: str
    patch: str
    comfort: str
    eater_name: str
    eater_gender: str
    friend_name: str
    friend_gender: str
    grownup: str
    trait: str
    eater_age: int = 5
    friend_age: int = 7
    relation: str = "siblings"
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for fruit_id, fruit in FRUITS.items():
            for patch_id, patch in PATCHES.items():
                if hazard_at_risk(fruit, patch):
                    combos.append((setting_id, fruit_id, patch_id))
    return combos


KNOWLEDGE = {
    "barrier": [
        (
            "What is a barrier?",
            "A barrier is something that tells you to stop or stay back, like a rope, ribbon, or fence. It helps keep people safe and protects things that are not ready yet.",
        )
    ],
    "gut": [
        (
            "What does your gut do?",
            "Your gut helps break food down so your body can use it. When food is dirty or not ready to eat, your gut can hurt and make your tummy ache.",
        )
    ],
    "berries": [
        (
            "Why should berries be washed before you eat them?",
            "Berries can have dirt or tiny germs on their skins. Washing them helps make them safer to eat.",
        )
    ],
    "plums": [
        (
            "What happens if fruit is not ripe yet?",
            "Fruit that is not ripe can taste sour or hard, and it can upset your stomach. Waiting gives it time to become softer and sweeter.",
        )
    ],
    "pears": [
        (
            "Why do people wait for pears to be ready?",
            "Pears get softer and sweeter as they ripen. If you pick them too soon, they may not taste good and may bother your tummy.",
        )
    ],
    "shine": [
        (
            "Why do shiny things look tempting at night?",
            "A little shine catches your eyes quickly in the dark. Bright things can feel special, even when they are not the right choice.",
        )
    ],
    "tea": [
        (
            "Why do grown-ups sometimes give warm tea or water for a tummy ache?",
            "A small sip can feel gentle and comforting when your tummy hurts. It does not fix every problem, but it can help you rest while a grown-up watches you.",
        )
    ],
}
KNOWLEDGE_ORDER = ["barrier", "gut", "shine", "berries", "plums", "pears", "tea"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    fruit = f["fruit_cfg"]
    patch = f["patch_cfg"]
    if f["outcome"] == "averted":
        return [
            f'Write a short rhyming story for a 3-to-5-year-old that uses the words "shine", "gut", and "barrier", where a child wants to eat {fruit.label} behind {patch.barrier} but listens to a warning in time.',
            f"Tell a dialogue-rich bedtime rhyme where {child.id} is tempted by shiny fruit, but {friend.id} explains why waiting is wise and nobody gets sick.",
            f"Write a gentle rhyming story about lanterns, a barrier, and a child who chooses patience over a risky bite.",
        ]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that uses the words "shine", "gut", and "barrier", and ends badly after a child ignores a warning.',
        f"Tell a dialogue-rich cautionary rhyme where {child.id} grabs {fruit.label} from behind {patch.barrier}, gets a stomachache, and misses the lantern walk.",
        f"Write a simple rhyming story with a sad ending that teaches children not to eat food from behind a barrier before a grown-up says it is ready.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    grown = f["grownup"]
    fruit = f["fruit_cfg"]
    patch = f["patch_cfg"]
    comfort = f["comfort"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who wanted a quick bite of {fruit.label}, and {friend.id}, who tried to stop {child.pronoun('object')}. A grown-up came to help when the choice went wrong.",
        ),
        (
            "What did the child see?",
            f"{child.id} saw {fruit.phrase} behind {patch.barrier}. The fruit looked beautiful in the lantern light, which is why it felt so tempting.",
        ),
        (
            f"Why did {friend.id} warn {child.id} not to eat the fruit?",
            f"{friend.id} warned that the fruit was behind a barrier and was not ready to eat yet. In this story, that meant it could be dirty or not ripe enough, so it could hurt {child.id}'s tummy.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.extend(
            [
                (
                    f"What did {child.id} do after the warning?",
                    f"{child.id} stopped and listened instead of taking a bite. That choice kept the tempting fruit outside the story's trouble and let the night stay calm.",
                ),
                (
                    "How did the story end?",
                    f"It ended safely, with the children sharing {comfort.phrase}. They watched the lanterns together because {child.id} chose patience over a risky snack.",
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"What happened after {child.id} ate the fruit?",
                    f"{child.id} got a stomachache very quickly and had to sit with the grown-up. The bite caused trouble because the fruit was not safe to eat yet.",
                ),
                (
                    "What did the grown-up explain about the gut barrier?",
                    f"The grown-up said the garden barrier was there for a reason, and the gut barrier inside the body can hurt when food is dirty or not ready. That explanation tied the warning to what happened in {child.id}'s own body.",
                ),
                (
                    "What was the bad ending?",
                    f"{child.id} missed the lantern walk and had to watch from a bench instead. The ending feels sad because the unsafe choice stole the bright part of the night.",
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"barrier", "gut", "shine"}
    fruit = world.facts["fruit_cfg"]
    patch = world.facts["patch_cfg"]
    comfort = world.facts["comfort"]
    if "berries" in fruit.tags:
        tags.add("berries")
    if "plums" in fruit.tags:
        tags.add("plums")
    if "pears" in fruit.tags:
        tags.add("pears")
    if {"tea", "water"} & comfort.tags:
        tags.add("tea")
    if patch.behind_barrier:
        tags.add("barrier")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.behind_barrier:
            bits.append("behind_barrier=True")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moon_garden",
        fruit="shineberries",
        patch="compost_patch",
        comfort="blanket",
        eater_name="Nia",
        eater_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        grownup="mother",
        trait="careful",
        eater_age=5,
        friend_age=7,
        relation="siblings",
    ),
    StoryParams(
        setting="river_fair",
        fruit="moonplums",
        patch="dew_patch",
        comfort="shawl",
        eater_name="Finn",
        eater_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        grownup="father",
        trait="sensible",
        eater_age=6,
        friend_age=5,
        relation="friends",
    ),
    StoryParams(
        setting="lantern_orchard",
        fruit="glass_pears",
        patch="picker_rows",
        comfort="pillow",
        eater_name="Ada",
        eater_gender="girl",
        friend_name="Milo",
        friend_gender="boy",
        grownup="aunt",
        trait="steady",
        eater_age=5,
        friend_age=8,
        relation="siblings",
    ),
]


def explain_rejection(fruit: Fruit, patch: Patch) -> str:
    if not patch.behind_barrier:
        return (
            f"(No story: {patch.label} is not behind a barrier, so the warning beat disappears. "
            f"Pick a patch with a real barrier and some reason to wait.)"
        )
    if fruit_risk(fruit, patch) <= 0:
        return (
            f"(No story: {fruit.label} from {patch.label} are already safe here, so there is no honest tummy-risk and no cautionary turn.)"
        )
    return "(No story: this combination does not create a plausible unsafe bite.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.eater_age, params.friend_age, params.trait):
        return "averted"
    return "sick"


ASP_RULES = r"""
hazard(F, P) :- fruit(F), patch(P), behind_barrier(P), risk(F, P, R), R > 0.
valid(S, F, P) :- setting(S), hazard(F, P).

older_sibling :- relation(siblings), eater_age(EA), friend_age(FA), FA > EA.
init_caution(5) :- trait(T), cautious_trait(T).
init_caution(3) :- trait(T), not cautious_trait(T).
bonus(4) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), impulse_init(I), A > I.
outcome(averted) :- averted.
outcome(sick) :- not averted.

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for fruit_id, fruit in FRUITS.items():
        lines.append(asp.fact("fruit", fruit_id))
        lines.append(asp.fact("needs_wash", fruit_id, int(fruit.needs_wash)))
        lines.append(asp.fact("ripe_need", fruit_id, fruit.ripe_need))
    for patch_id, patch in PATCHES.items():
        lines.append(asp.fact("patch", patch_id))
        if patch.behind_barrier:
            lines.append(asp.fact("behind_barrier", patch_id))
        lines.append(asp.fact("dirt", patch_id, patch.dirt))
        lines.append(asp.fact("ripeness", patch_id, patch.ripeness))
        if patch.washed:
            lines.append(asp.fact("washed", patch_id))
    for fruit_id, fruit in FRUITS.items():
        for patch_id, patch in PATCHES.items():
            lines.append(asp.fact("risk", fruit_id, patch_id, fruit_risk(fruit, patch)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
    lines.append(asp.fact("impulse_init", int(IMPULSE_INIT)))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("eater_age", params.eater_age),
            asp.fact("friend_age", params.friend_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming cautionary storyworld: a shiny fruit behind a barrier, a warning, and a sad lesson."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--patch", choices=PATCHES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--grownup", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.patch and args.fruit:
        fruit = FRUITS[args.fruit]
        patch = PATCHES[args.patch]
        if not hazard_at_risk(fruit, patch):
            raise StoryError(explain_rejection(fruit, patch))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.fruit is None or combo[1] == args.fruit)
        and (args.patch is None or combo[2] == args.patch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, fruit_id, patch_id = rng.choice(sorted(combos))
    comfort_id = args.comfort or rng.choice(sorted(COMFORTS))
    eater_name, eater_gender = _pick_kid(rng)
    friend_name, friend_gender = _pick_kid(rng, avoid=eater_name)
    relation = rng.choice(["siblings", "friends"])
    eater_age, friend_age = rng.sample([4, 5, 6, 7, 8], 2)
    trait = rng.choice(TRAITS)
    grownup = args.grownup or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(
        setting=setting_id,
        fruit=fruit_id,
        patch=patch_id,
        comfort=comfort_id,
        eater_name=eater_name,
        eater_gender=eater_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        grownup=grownup,
        trait=trait,
        eater_age=eater_age,
        friend_age=friend_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.fruit not in FRUITS:
        raise StoryError(f"(Unknown fruit: {params.fruit})")
    if params.patch not in PATCHES:
        raise StoryError(f"(Unknown patch: {params.patch})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Unknown comfort item: {params.comfort})")
    if params.grownup not in {"mother", "father", "aunt", "uncle"}:
        raise StoryError(f"(Unknown grown-up type: {params.grownup})")

    fruit = FRUITS[params.fruit]
    patch = PATCHES[params.patch]
    if not hazard_at_risk(fruit, patch):
        raise StoryError(explain_rejection(fruit, patch))

    world = tell(
        setting=SETTINGS[params.setting],
        fruit=fruit,
        patch=patch,
        comfort=COMFORTS[params.comfort],
        eater_name=params.eater_name,
        eater_gender=params.eater_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        trait=params.trait,
        grownup_type=params.grownup,
        eater_age=params.eater_age,
        friend_age=params.friend_age,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, fruit, patch) combos:\n")
        for setting_id, fruit_id, patch_id in combos:
            print(f"  {setting_id:16} {fruit_id:12} {patch_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.eater_name} and {p.friend_name}: {p.fruit} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    setting: Setting,
    fruit: Fruit,
    patch: Patch,
    comfort: Comfort,
    eater_name: str = "Nia",
    eater_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    trait: str = "careful",
    grownup_type: str = "mother",
    eater_age: int = 5,
    friend_age: int = 7,
    relation: str = "siblings",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=eater_name,
            kind="character",
            type=eater_gender,
            role="eater",
            age=eater_age,
            attrs={"relation": relation},
            traits=["eager"],
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="warn_friend",
            age=friend_age,
            attrs={"relation": relation},
            traits=[trait],
        )
    )
    grownup = world.add(
        Entity(
            id="Grownup",
            kind="character",
            type=grownup_type,
            role="grownup",
            label="the grown-up",
        )
    )
    fruit_ent = world.add(
        Entity(
            id="fruit",
            kind="thing",
            type="fruit",
            label=fruit.label,
            edible=True,
            washed=patch.washed,
            behind_barrier=patch.behind_barrier,
        )
    )
    world.add(
        Entity(
            id="barrier",
            kind="thing",
            type="barrier",
            label=patch.barrier,
        )
    )

    child.memes["impulse"] = IMPULSE_INIT
    friend.memes["caution"] = initial_caution(trait)
    fruit_ent.meters["risk"] = float(fruit_risk(fruit, patch))

    introduce(world, child, friend, setting)
    world.para()
    see_treat(world, child, fruit, patch)
    warn(world, friend, child, fruit, patch, grownup)

    averted = would_avert(relation, eater_age, friend_age, trait)
    if averted:
        world.para()
        back_down(world, child, friend, grownup, comfort)
        outcome = "averted"
    else:
        defy(world, child, friend)
        world.para()
        bite(world, child, fruit_ent, fruit, patch)
        ache(world, child)
        world.para()
        help_and_explain(world, grownup, child, friend, comfort)
        bad_ending(world, child, friend, setting)
        outcome = "sick"

    world.facts.update(
        setting=setting,
        fruit_cfg=fruit,
        patch_cfg=patch,
        comfort=comfort,
        child=child,
        friend=friend,
        grownup=grownup,
        fruit=fruit_ent,
        outcome=outcome,
        relation=relation,
        averted=averted,
        missed_walk=child.meters["missed_lantern_walk"] >= THRESHOLD,
        belly_pain=child.meters["belly_pain"],
        risk=fruit_ent.meters["risk"],
    )
    return world


SETTINGS = {
    "moon_garden": Setting(
        id="moon_garden",
        place="the moon garden",
        glow="Blue lanterns bobbed like sleepy fish, and the pond held every starry wish.",
        path="the pebble path",
        tags={"garden", "lanterns"},
    ),
    "lantern_orchard": Setting(
        id="lantern_orchard",
        place="the lantern orchard",
        glow="Paper lights swung in the trees, and the apples hummed with the evening breeze.",
        path="the orchard lane",
        tags={"orchard", "lanterns"},
    ),
    "river_fair": Setting(
        id="river_fair",
        place="the river fair",
        glow="Strings of light kissed the rail, and little boats blinked along the trail.",
        path="the river walk",
        tags={"fair", "lanterns"},
    ),
}

FRUITS = {
    "shineberries": Fruit(
        id="shineberries",
        label="shine berries",
        phrase="a spray of shine berries",
        shine_word="shine",
        rhyme_line="They glimmered like beads in a storybook scene, too bright to ignore and too pretty to glean.",
        needs_wash=True,
        ripe_need=2,
        tags={"berries", "shine", "food"},
    ),
    "moonplums": Fruit(
        id="moonplums",
        label="moon plums",
        phrase="three moon plums",
        shine_word="shine",
        rhyme_line="Their skins had a shimmer, a soft silver bloom, like tiny round lamps in the hush of the gloom.",
        needs_wash=True,
        ripe_need=3,
        tags={"plums", "shine", "food"},
    ),
    "glass_pears": Fruit(
        id="glass_pears",
        label="glass pears",
        phrase="two glass pears",
        shine_word="shine",
        rhyme_line="They flashed with a shine like a bell or a tear, all dewy and dreamy and terribly near.",
        needs_wash=True,
        ripe_need=2,
        tags={"pears", "shine", "food"},
    ),
}

PATCHES = {
    "compost_patch": Patch(
        id="compost_patch",
        label="the compost patch",
        barrier="a twine barrier",
        warning_sign="Not washed yet",
        dirt=2,
        ripeness=1,
        washed=False,
        behind_barrier=True,
        tags={"dirty", "barrier", "compost"},
    ),
    "dew_patch": Patch(
        id="dew_patch",
        label="the dew patch",
        barrier="a reed barrier",
        warning_sign="Wait till dawn",
        dirt=1,
        ripeness=1,
        washed=False,
        behind_barrier=True,
        tags={"dew", "barrier", "unripe"},
    ),
    "picker_rows": Patch(
        id="picker_rows",
        label="the picker rows",
        barrier="a ribbon barrier",
        warning_sign="For tomorrow's picking",
        dirt=1,
        ripeness=2,
        washed=False,
        behind_barrier=True,
        tags={"rows", "barrier"},
    ),
    "washed_bowl": Patch(
        id="washed_bowl",
        label="the washed bowl",
        barrier="no barrier",
        warning_sign="Ready to share",
        dirt=0,
        ripeness=3,
        washed=True,
        behind_barrier=False,
        tags={"safe_food"},
    ),
}

COMFORTS = {
    "blanket": Comfort(
        id="blanket",
        label="a soft blanket",
        phrase="a soft blanket and a cup of mint tea",
        tags={"blanket", "tea"},
    ),
    "shawl": Comfort(
        id="shawl",
        label="a warm shawl",
        phrase="a warm shawl and a little sip of water",
        tags={"shawl", "water"},
    ),
    "pillow": Comfort(
        id="pillow",
        label="a moon-patterned pillow",
        phrase="a moon-patterned pillow and some cool water",
        tags={"pillow", "water"},
    ),
}

GIRL_NAMES = ["Nia", "Lila", "Mina", "Tess", "Ruby", "Ada", "Ivy", "Mara"]
BOY_NAMES = ["Ben", "Owen", "Finn", "Kai", "Milo", "Theo", "Jude", "Noah"]
TRAITS = ["careful", "cautious", "sensible", "steady", "thoughtful", "gentle"]

if __name__ == "__main__":
    main()
