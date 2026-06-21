#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vaseline_meddle_think_surprise_folk_tale.py
======================================================================

A standalone story world for a small folk-tale domain: a child in a village
wants to meddle with a festival lantern, thinks a dab of vaseline will help,
and learns to think first before touching a delicate thing.

The world model is concrete and state-driven:
- a lantern has parts and a fault,
- the wrong meddling adds grease and makes the trouble worse in a specific way,
- an elder applies the fitting fix,
- the ending depends on whether the child waited and whether the elder finished
  in time for the evening surprise.

Run it
------
    python storyworlds/worlds/gpt-5.4/vaseline_meddle_think_surprise_folk_tale.py
    python storyworlds/worlds/gpt-5.4/vaseline_meddle_think_surprise_folk_tale.py --lantern crane --problem dust_cuts
    python storyworlds/worlds/gpt-5.4/vaseline_meddle_think_surprise_folk_tale.py --problem rusty_hinge --lantern crane
    python storyworlds/worlds/gpt-5.4/vaseline_meddle_think_surprise_folk_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/vaseline_meddle_think_surprise_folk_tale.py --verify
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
THINKING_TRAITS = {"patient", "careful", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "mother"}
        male = {"boy", "man", "grandfather", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def elder_word(self) -> str:
        return {"grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Lantern:
    id: str
    label: str
    phrase: str
    features: set[str] = field(default_factory=set)
    image: str = ""
    surprise_line: str = ""
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
class Problem:
    id: str
    label: str
    need: str = ""
    clue: str = ""
    correct_fix: str = ""
    grease_bad: str = ""
    severity: int = 1
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
class Fix:
    id: str
    label: str
    power: int = 2
    action: str = ""
    qa_text: str = ""
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


def _r_grease_effect(world: World) -> list[str]:
    out: list[str] = []
    lantern = world.get("lantern")
    if lantern.meters["greased"] < THRESHOLD:
        return out
    effect = lantern.attrs.get("grease_bad", "")
    sig = ("grease_effect", effect)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["worry"] += 1
    if effect == "smudge":
        lantern.meters["smudged"] += 1
        lantern.meters["dim"] += 1
        out.append("__smudge__")
    elif effect == "smoke":
        lantern.meters["smoky"] += 1
        lantern.meters["dim"] += 1
        out.append("__smoke__")
    elif effect == "grit":
        lantern.meters["stuck"] += 1
        out.append("__grit__")
    return out


def _r_ready_to_shine(world: World) -> list[str]:
    lantern = world.get("lantern")
    if lantern.meters["fixed"] < THRESHOLD:
        return []
    if lantern.meters["smudged"] >= THRESHOLD or lantern.meters["smoky"] >= THRESHOLD:
        return []
    if lantern.attrs.get("problem") == "rusty_hinge" and lantern.meters["stuck"] >= THRESHOLD:
        return []
    sig = ("shining", lantern.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lantern.meters["working"] += 1
    child = world.get("child")
    elder = world.get("elder")
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    elder.memes["pride"] += 1
    return ["__working__"]


CAUSAL_RULES = [
    Rule(name="grease_effect", tag="physical", apply=_r_grease_effect),
    Rule(name="ready_to_shine", tag="physical", apply=_r_ready_to_shine),
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
        for sent in produced:
            world.say(sent)
    return produced


def problem_fits(lantern: Lantern, problem: Problem) -> bool:
    return problem.need in lantern.features


def valid_fix(problem: Problem, fix_id: str) -> bool:
    return problem.correct_fix == fix_id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for lantern_id, lantern in LANTERNS.items():
        for problem_id, problem in PROBLEMS.items():
            if problem_fits(lantern, problem):
                combos.append((lantern_id, problem_id, problem.correct_fix))
    return combos


def meddle_damage(problem: Problem, delay: int) -> int:
    return problem.severity + delay


def finished_in_time(problem: Problem, fix: Fix, delay: int) -> bool:
    return fix.power >= meddle_damage(problem, delay)


def would_wait(trait: str, delay: int) -> bool:
    return trait in THINKING_TRAITS and delay == 0


def explain_problem_mismatch(lantern: Lantern, problem: Problem) -> str:
    return (
        f"(No story: {lantern.label} has {sorted(lantern.features)}, but {problem.label} "
        f"needs a lantern with {problem.need}. The fault does not honestly fit the object.)"
    )


def explain_fix_mismatch(problem: Problem, fix: Fix) -> str:
    right = FIXES[problem.correct_fix].label
    return (
        f"(No story: {fix.label} is not the right village remedy for {problem.label}. "
        f"This world only accepts {right} for that trouble.)"
    )


def predict_meddling(world: World, problem: Problem) -> dict:
    sim = world.copy()
    lantern = sim.get("lantern")
    lantern.meters["greased"] += 1
    propagate(sim, narrate=False)
    return {
        "smudged": lantern.meters["smudged"] >= THRESHOLD,
        "smoky": lantern.meters["smoky"] >= THRESHOLD,
        "stuck": lantern.meters["stuck"] >= THRESHOLD,
    }


def village_opening(world: World, child: Entity, elder: Entity, lantern: Lantern) -> None:
    world.say(
        f"In a village folded between a river and a low blue hill, {child.id} lived with "
        f"{child.pronoun('possessive')} {elder.elder_word}, who kept {lantern.phrase} on the highest shelf."
    )
    world.say(
        f"Each year, when dusk came to the Feast of First Lights, that lantern was lifted down "
        f"so its shining picture could dance across the square."
    )


def introduce_desire(world: World, child: Entity, lantern: Lantern) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} had watched it since baby days and always thought the lantern looked like a little secret with handles."
    )
    world.say(
        f"This year {child.pronoun()} was old enough to carry it with two careful hands, and that made {child.pronoun('object')} proud."
    )


def discover_trouble(world: World, child: Entity, elder: Entity, lantern: Lantern, problem: Problem) -> None:
    lantern.meters["troubled"] += 1
    world.say(
        f"But when {elder.elder_word} set the lantern on the table, {problem.clue}."
    )
    world.say(
        f'"Wait," said {elder.elder_word}. "Before small hands meddle with an old treasure, they must think."'
    )


def tempt_vaseline(world: World, child: Entity, problem: Problem) -> None:
    child.memes["impulse"] += 1
    pred = predict_meddling(world, problem)
    world.facts["predicted_smudged"] = pred["smudged"]
    world.facts["predicted_smoky"] = pred["smoky"]
    world.facts["predicted_stuck"] = pred["stuck"]
    extra = ""
    if pred["smoky"]:
        extra = " It would only make smoke."
    elif pred["smudged"]:
        extra = " It would leave greasy smears where clear light should go."
    elif pred["stuck"]:
        extra = " Dust would cling to the grease, and the little door would stick harder."
    world.say(
        f"On the corner of the table stood a small tin of vaseline. "
        f'{child.id} looked at it and thought, "Something slippery helps many things. '
        f'''Perhaps it will help this too."{extra}'''
    )


def wait_and_ask(world: World, child: Entity, elder: Entity) -> None:
    child.memes["patience"] += 1
    child.memes["trust"] += 1
    world.say(
        f"{child.id} curled {child.pronoun('possessive')} fingers back into {child.pronoun('possessive')} palm and did not touch the tin."
    )
    world.say(
        f'"I will think first," {child.pronoun()} said. "Show me the right way, {elder.elder_word}."'
    )


def meddle(world: World, child: Entity, lantern_ent: Entity, problem: Problem) -> None:
    child.memes["shame"] += 1
    lantern_ent.meters["greased"] += 1
    propagate(world, narrate=False)
    if problem.grease_bad == "smudge":
        world.say(
            f"Yet the room was quiet and the feast drum was already muttering outside, so {child.id} dabbed on a little vaseline anyway."
        )
        world.say(
            f"At once the thin cut-paper windows turned shiny and blurred, as if a thumbprint had walked across the moon."
        )
    elif problem.grease_bad == "smoke":
        world.say(
            f"Yet the room was quiet and the feast drum was already muttering outside, so {child.id} touched the tin and rubbed a little vaseline where {child.pronoun()} should not."
        )
        world.say(
            "When the lamp was tried, a weak gray smoke coiled up like a disappointed snake."
        )
    else:
        world.say(
            f"Yet the room was quiet and the feast drum was already muttering outside, so {child.id} spread a little vaseline along the tiny door and pin."
        )
        world.say(
            "For one breath the metal gleamed. Then grit clung to the grease, and the little door stuck more stubbornly than before."
        )


def elder_returns(world: World, elder: Entity, child: Entity) -> None:
    elder.memes["concern"] += 1
    world.say(
        f"{elder.elder_word.capitalize()} came back with the lamp spoon, saw {child.id}'s shining fingertips, and understood the whole matter at a glance."
    )
    world.say(
        f'"Ah, little one," {elder.pronoun()} said, not in anger but in sorrow, "quick hands often run ahead of wise thoughts."'
    )


def clean_mess(world: World, lantern_ent: Entity, problem: Problem) -> None:
    if problem.grease_bad == "smudge":
        lantern_ent.meters["smudged"] = 0.0
        lantern_ent.meters["greased"] = 0.0
        world.say(
            "First the elder wiped the greasy shine away with a soft cloth until the paper windows could breathe again."
        )
    elif problem.grease_bad == "smoke":
        lantern_ent.meters["smoky"] = 0.0
        lantern_ent.meters["greased"] = 0.0
        world.say(
            "First the elder cleaned away the grease and opened the room so the sour little smoke could wander out."
        )
    else:
        lantern_ent.meters["stuck"] = 0.0
        lantern_ent.meters["greased"] = 0.0
        world.say(
            "First the elder washed the sticky dust from the pin and hinge until the brass no longer dragged."
        )


def apply_fix(world: World, elder: Entity, lantern_ent: Entity, fix: Fix) -> None:
    lantern_ent.meters["fixed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {elder.elder_word} {fix.action}."
    )


def in_time_ending(
    world: World,
    child: Entity,
    elder: Entity,
    lantern: Lantern,
    fix: Fix,
    waited: bool,
) -> None:
    child.memes["lesson"] += 1
    world.say(
        f'Soon the lantern shone true. {lantern.surprise_line}'
    )
    if waited:
        world.say(
            f'"Now you know why we think before we meddle," said {elder.elder_word}. "{fix.label.capitalize()} for the right trouble, and patience for the hand."'
        )
    else:
        world.say(
            f'{child.id} bowed {child.pronoun("possessive")} head. "I thought any slippery thing would help," {child.pronoun()} said.'
        )
        world.say(
            f'"And now you know better," said {elder.elder_word}. "We think before we meddle, and we name the trouble before we choose the cure."'
        )
    world.say(
        f"That night, when the villagers saw {lantern.image}, they clapped, and {child.id} smiled because wisdom had mended what hurry had tangled."
    )


def late_surprise_ending(world: World, child: Entity, elder: Entity, lantern: Lantern, fix: Fix) -> None:
    child.memes["lesson"] += 1
    child.memes["wonder"] += 1
    world.say(
        "But the feast song began before the work was done, and the square waited in a hush under the first star."
    )
    world.say(
        "Then, from the reeds by the river, a swarm of fireflies drifted up and circled the square. "
        "They hung in the dusk like little borrowed lanterns, and the villagers laughed in surprise."
    )
    world.say(
        f"By the time the last note faded, {fix.label} had done its work. {lantern.surprise_line}"
    )
    world.say(
        f'"Do you see?" said {elder.elder_word}. "Even when we are late, the world may send a surprise. But it is still better to think before we meddle."'
    )
    world.say(
        f"{child.id} never forgot the fireflies, nor the lesson that came walking beside them."
    )
@dataclass
class StoryParams:
    lantern: str = ""
    problem: str = ""
    fix: str = ""
    child: str = ""
    gender: str = ""
    elder: str = "grandmother"
    trait: str = "patient"
    delay: int = 0
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


KNOWLEDGE = {
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light carried inside a frame, often with glass or paper around the flame. It helps people carry light safely through the dark.",
        )
    ],
    "paper": [
        (
            "Why should paper be handled gently?",
            "Paper tears and smears easily, especially when it is thin. Gentle hands keep the light shining through it clearly.",
        )
    ],
    "glass": [
        (
            "Why is glass useful in a lantern?",
            "Glass lets light shine through while sheltering the flame from wind. That helps the lantern glow steadily.",
        )
    ],
    "metal": [
        (
            "Why do metal hinges sometimes stick?",
            "Metal parts can gather rust or grit, so they scrape instead of moving smoothly. A tiny proper drop of oil can help them move again.",
        )
    ],
    "dust": [
        (
            "Why does dust make things look dim?",
            "Dust sits on the surface and blocks or softens the light. When the dust is brushed away, the light shows more clearly.",
        )
    ],
    "wick": [
        (
            "What does a wick do?",
            "A wick drinks up lamp oil and feeds the flame. If it is too long or ragged, the flame can smoke instead of burning cleanly.",
        )
    ],
    "smoke": [
        (
            "Why is smoke a sign that something is wrong with a lamp?",
            "Smoke means the flame is not burning cleanly. The wick may be wrong, or something greasy may be where it should not be.",
        )
    ],
    "brush": [
        (
            "What is a soft brush good for?",
            "A soft brush lifts dust without scratching or tearing delicate things. That is why people use it on paper and carvings.",
        )
    ],
    "trim": [
        (
            "Why would someone trim a wick?",
            "Trimming a wick makes the flame steadier and cleaner. A neat wick gives more light and less smoke.",
        )
    ],
    "oil": [
        (
            "Why is a tiny drop of oil better than a big greasy smear on a hinge?",
            "A small proper drop goes exactly where the moving part needs help. A big greasy smear collects dirt and can make a delicate part worse.",
        )
    ],
    "care": [
        (
            "Why is it wise to think before you meddle with an old object?",
            "Old things often have one particular trouble and one fitting cure. Thinking first helps you choose the right help instead of making new trouble.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "lantern",
    "paper",
    "glass",
    "metal",
    "dust",
    "wick",
    "smoke",
    "brush",
    "trim",
    "oil",
    "care",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    lantern = f["lantern_cfg"]
    problem = f["problem_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short folk tale for a 3-to-5-year-old that includes the words '
        f'"vaseline", "meddle", and "think", and centers on a village child and a festival lantern.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle folk tale where {child.id} wants to meddle with a {lantern.label}, but pauses to think and asks an elder for help.",
            f"Write a story where {problem.label} troubles an old lantern, yet the child waits, learns the right remedy, and the ending brings a soft surprise in the village square.",
        ]
    if outcome == "late":
        return [
            base,
            f"Tell a folk tale where {child.id} uses vaseline on a {lantern.label}, learns that quick meddling can make {problem.label} worse, and a late magical surprise saves the feast mood.",
            f"Write a village tale with a small mistake, a wise elder, and a surprise ending with fireflies before the lantern finally shines.",
        ]
    return [
        base,
        f"Tell a folk tale where {child.id} thinks vaseline will help a {lantern.label}, meddles, and then learns the right cure from an elder.",
        f"Write a simple story with a folk-tale voice: an old lantern, {problem.label}, a child who must think before meddling, and a bright ending image in the square.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    lantern = f["lantern_cfg"]
    problem = f["problem_cfg"]
    fix = f["fix_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child in a village, and {child.pronoun('possessive')} {elder.elder_word}, who keeps {lantern.phrase}. The story turns on whether {child.id} will think before trying to help.",
        ),
        (
            "What was wrong with the lantern?",
            f"The trouble was {problem.label}. That mattered because it kept the lantern from giving the festival its clear shining picture.",
        ),
        (
            f"Why did {child.id} want to use vaseline?",
            f"{child.id} thought a slippery thing might help the lantern move or shine better. That was a quick guess, not a careful look at what the real trouble was.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What did {child.id} do when told to think before meddling?",
                f"{child.id} stopped, pulled {child.pronoun('possessive')} hand back, and asked {elder.elder_word} for the right help. Because {child.pronoun()} waited, the lantern was mended before any new trouble was made.",
            )
        )
        qa.append(
            (
                f"How did {elder.elder_word} fix the lantern?",
                f"{elder.elder_word.capitalize()} {fix.qa_text}. That matched the real problem instead of covering it with grease.",
            )
        )
    elif outcome == "restored":
        qa.append(
            (
                f"What happened after {child.id} meddled with the lantern?",
                f"The vaseline made the trouble worse in its own way before the elder could set it right. The mistake showed that guessing at a cure can add a second problem to the first one.",
            )
        )
        qa.append(
            (
                f"How was the lantern saved in time?",
                f"First {elder.elder_word} cleaned away the extra mess, and then {elder.pronoun()} {fix.qa_text}. Because the elder worked quickly and used the right remedy, the lantern still shone for the feast.",
            )
        )
    else:
        qa.append(
            (
                "Why was the lantern late to the feast?",
                f"It was late because the child's vaseline meddling made the trouble bigger, and the elder had to clean that away before fixing the true fault. The delay let the feast song begin before the lantern was ready.",
            )
        )
        qa.append(
            (
                "What was the surprise in the ending?",
                "A cloud of fireflies drifted over the square before the lantern was ready, so the villagers were given a different little light to enjoy. Then the lantern shone too, which made the ending feel like a gift instead of only a scolding.",
            )
        )
    qa.append(
        (
            "What lesson did the child learn?",
            "The child learned to think before meddling with a delicate thing. The story shows that naming the real problem comes before choosing the cure.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"lantern", "care"}
    lantern = world.facts["lantern_cfg"]
    problem = world.facts["problem_cfg"]
    fix = world.facts["fix_cfg"]
    tags |= lantern.tags
    tags |= problem.tags
    tags |= fix.tags
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None, [], {})}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        lantern="crane",
        problem="dust_cuts",
        fix="brush",
        child="Nila",
        gender="girl",
        elder="grandmother",
        trait="patient",
        delay=0,
    ),
    StoryParams(
        lantern="carp",
        problem="long_wick",
        fix="trim",
        child="Kavi",
        gender="boy",
        elder="grandfather",
        trait="curious",
        delay=0,
    ),
    StoryParams(
        lantern="tortoise",
        problem="rusty_hinge",
        fix="oil",
        child="Mira",
        gender="girl",
        elder="grandmother",
        trait="restless",
        delay=1,
    ),
    StoryParams(
        lantern="carp",
        problem="long_wick",
        fix="trim",
        child="Hari",
        gender="boy",
        elder="grandfather",
        trait="hasty",
        delay=2,
    ),
]


ASP_RULES = r"""
feature_match(L,P) :- lantern(L), problem(P), needs(P,F), has_feature(L,F).
required_fix(P,R) :- problem(P), correct_fix(P,R).
valid(L,P,R) :- feature_match(L,P), required_fix(P,R).

waits :- chosen_trait(T), thinking_trait(T), delay(0).

damage(S + D) :- chosen_problem(P), severity(P,S), delay(D).
in_time :- chosen_fix(F), power(F,PP), damage(V), PP >= V.

outcome(averted) :- waits.
outcome(restored) :- not waits, in_time.
outcome(late) :- not waits, not in_time.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for lantern_id, lantern in LANTERNS.items():
        lines.append(asp.fact("lantern", lantern_id))
        for feat in sorted(lantern.features):
            lines.append(asp.fact("has_feature", lantern_id, feat))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("needs", problem_id, problem.need))
        lines.append(asp.fact("correct_fix", problem_id, problem.correct_fix))
        lines.append(asp.fact("severity", problem_id, problem.severity))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("power", fix_id, fix.power))
    for trait in sorted(THINKING_TRAITS):
        lines.append(asp.fact("thinking_trait", trait))
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
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_fix", params.fix),
            asp.fact("chosen_trait", params.trait),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if would_wait(params.trait, params.delay):
        return "averted"
    return "restored" if finished_in_time(PROBLEMS[params.problem], FIXES[params.fix], params.delay) else "late"


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
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generate/emit passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a lantern, a wrong guess with vaseline, and a folk-tale surprise."
    )
    ap.add_argument("--lantern", choices=sorted(LANTERNS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible lantern/problem/fix triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke generation test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.lantern and args.problem:
        lantern = LANTERNS[args.lantern]
        problem = PROBLEMS[args.problem]
        if not problem_fits(lantern, problem):
            raise StoryError(explain_problem_mismatch(lantern, problem))
    if args.problem and args.fix:
        problem = PROBLEMS[args.problem]
        fix = FIXES[args.fix]
        if not valid_fix(problem, args.fix):
            raise StoryError(explain_fix_mismatch(problem, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.lantern is None or combo[0] == args.lantern)
        and (args.problem is None or combo[1] == args.problem)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    lantern_id, problem_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or pick_name(rng, gender)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        lantern=lantern_id,
        problem=problem_id,
        fix=fix_id,
        child=child,
        gender=gender,
        elder=elder,
        trait=trait,
        delay=delay,
    )


def validate_params(params: StoryParams) -> None:
    if params.lantern not in LANTERNS:
        raise StoryError(f"(Unknown lantern: {params.lantern})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    lantern = LANTERNS[params.lantern]
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    if not problem_fits(lantern, problem):
        raise StoryError(explain_problem_mismatch(lantern, problem))
    if not valid_fix(problem, params.fix):
        raise StoryError(explain_fix_mismatch(problem, fix))
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.elder not in {"grandmother", "grandfather"}:
        raise StoryError(f"(Unknown elder: {params.elder})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.delay not in {0, 1, 2}:
        raise StoryError("(Delay must be 0, 1, or 2.)")


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(
        lantern=LANTERNS[params.lantern],
        problem=PROBLEMS[params.problem],
        fix=FIXES[params.fix],
        child_name=params.child,
        child_gender=params.gender,
        elder_type=params.elder,
        trait=params.trait,
        delay=params.delay,
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
        print(f"{len(combos)} compatible (lantern, problem, fix) combos:\n")
        for lantern, problem, fix in combos:
            print(f"  {lantern:10} {problem:12} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
            header = f"### {p.child}: {p.lantern} / {p.problem} / {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    lantern: Lantern,
    problem: Problem,
    fix: Fix,
    child_name: str = "Nila",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "patient",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
            attrs={},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
            attrs={},
        )
    )
    lantern_ent = world.add(
        Entity(
            id="lantern",
            kind="thing",
            type="lantern",
            label=lantern.label,
            attrs={
                "lantern_id": lantern.id,
                "problem": problem.id,
                "grease_bad": problem.grease_bad,
                "need": problem.need,
            },
        )
    )

    child.memes["wonder"] = 0.0
    child.memes["impulse"] = 0.0
    child.memes["patience"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["lesson"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["shame"] = 0.0
    child.memes["relief"] = 0.0
    elder.memes["concern"] = 0.0
    elder.memes["pride"] = 0.0
    lantern_ent.meters["troubled"] = 0.0
    lantern_ent.meters["greased"] = 0.0
    lantern_ent.meters["smudged"] = 0.0
    lantern_ent.meters["smoky"] = 0.0
    lantern_ent.meters["stuck"] = 0.0
    lantern_ent.meters["fixed"] = 0.0
    lantern_ent.meters["working"] = 0.0
    lantern_ent.meters["dim"] = 0.0

    world.facts.update(
        lantern_cfg=lantern,
        problem_cfg=problem,
        fix_cfg=fix,
        child=child,
        elder=elder,
        delay=delay,
        waited=False,
        outcome="?",
        image=lantern.image,
    )

    village_opening(world, child, elder, lantern)
    introduce_desire(world, child, lantern)

    world.para()
    discover_trouble(world, child, elder, lantern, problem)
    tempt_vaseline(world, child, problem)

    waited = would_wait(trait, delay)
    world.facts["waited"] = waited

    world.para()
    if waited:
        wait_and_ask(world, child, elder)
        apply_fix(world, elder, lantern_ent, fix)
        world.para()
        in_time_ending(world, child, elder, lantern, fix, waited=True)
        outcome = "averted"
    else:
        meddle(world, child, lantern_ent, problem)
        elder_returns(world, elder, child)
        clean_mess(world, lantern_ent, problem)
        apply_fix(world, elder, lantern_ent, fix)
        world.para()
        if finished_in_time(problem, fix, delay):
            in_time_ending(world, child, elder, lantern, fix, waited=False)
            outcome = "restored"
        else:
            late_surprise_ending(world, child, elder, lantern, fix)
            outcome = "late"

    world.facts.update(
        waited=waited,
        outcome=outcome,
        lantern=lantern_ent,
        damage=meddle_damage(problem, delay) if not waited else 0,
        in_time=finished_in_time(problem, fix, delay) if not waited else True,
        smoke=lantern_ent.meters["smoky"] >= THRESHOLD,
        smudge=lantern_ent.meters["smudged"] >= THRESHOLD,
        stuck=lantern_ent.meters["stuck"] >= THRESHOLD,
        working=lantern_ent.meters["working"] >= THRESHOLD,
    )
    return world


LANTERNS = {
    "crane": Lantern(
        id="crane",
        label="crane lantern",
        phrase="a paper crane lantern painted with reeds and moon-water",
        features={"shutters", "wick"},
        image="the pale shape of a crane opened its wings across the meeting-house wall",
        surprise_line="A white crane seemed to spread its wings over the meeting-house wall, so gently that even the noisy boys fell quiet.",
        tags={"lantern", "paper", "shadow"},
    ),
    "carp": Lantern(
        id="carp",
        label="carp lantern",
        phrase="a river-carp lantern with a round glass belly",
        features={"wick", "glass"},
        image="a silver carp seemed to swim along the stones of the well",
        surprise_line="A silver carp swam across the well stones, wavering as if the river itself had climbed up to watch the feast.",
        tags={"lantern", "glass", "shadow"},
    ),
    "tortoise": Lantern(
        id="tortoise",
        label="tortoise lantern",
        phrase="a brass tortoise lantern with a tiny hinged door",
        features={"hinge", "wick"},
        image="a golden tortoise crawled over the courtyard gate",
        surprise_line="A golden tortoise crept over the courtyard gate, and all the old women nodded as if a very small king had arrived.",
        tags={"lantern", "metal", "shadow"},
    ),
}

PROBLEMS = {
    "dust_cuts": Problem(
        id="dust_cuts",
        label="dust in the cut-paper windows",
        need="shutters",
        clue="the lantern's paper cuts looked dull with dust, and the moon-shape inside would not show clearly",
        correct_fix="brush",
        grease_bad="smudge",
        severity=2,
        tags={"dust", "paper"},
    ),
    "long_wick": Problem(
        id="long_wick",
        label="a wick grown too long",
        need="wick",
        clue="the wick had grown shaggy, and instead of a clean flame it only sulked and coughed",
        correct_fix="trim",
        grease_bad="smoke",
        severity=3,
        tags={"wick", "smoke"},
    ),
    "rusty_hinge": Problem(
        id="rusty_hinge",
        label="a rusty little hinge",
        need="hinge",
        clue="the tiny brass door would not open without a scrape and a frown",
        correct_fix="oil",
        grease_bad="grit",
        severity=1,
        tags={"hinge", "metal"},
    ),
}

FIXES = {
    "brush": Fix(
        id="brush",
        label="a soft brush",
        power=3,
        action="took a soft brush of goat hair and whisked the dust from every paper edge",
        qa_text="used a soft brush to whisk the dust away",
        tags={"brush", "care"},
    ),
    "trim": Fix(
        id="trim",
        label="a wick trimmer",
        power=3,
        action="snipped the ragged wick with the tiny trimmer until the flame could stand straight and clear",
        qa_text="trimmed the wick so the flame could burn clearly",
        tags={"trim", "wick"},
    ),
    "oil": Fix(
        id="oil",
        label="a drop of lamp oil",
        power=2,
        action="placed one careful drop of lamp oil on the hinge pin and worked the brass door until it moved like a polite guest",
        qa_text="used one careful drop of lamp oil on the hinge",
        tags={"oil", "metal"},
    ),
}

GIRL_NAMES = ["Nila", "Mira", "Sita", "Lila", "Tara", "Asha", "Pema", "Rina"]
BOY_NAMES = ["Kavi", "Hari", "Milan", "Dev", "Raju", "Toma", "Biren", "Niko"]
TRAITS = ["patient", "careful", "thoughtful", "curious", "hasty", "restless"]

if __name__ == "__main__":
    main()
