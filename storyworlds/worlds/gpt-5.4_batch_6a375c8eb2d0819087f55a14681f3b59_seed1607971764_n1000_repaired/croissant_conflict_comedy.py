#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/croissant_conflict_comedy.py
=======================================================

A small story world about a silly breakfast conflict over the last croissant.

The world models one flaky pastry, two hungry children, and a grown-up or shop
helper who turns a tug-of-war into a funny, kinder ending. The prose comes from
simulated state: hunger raises conflict, tugging can squash the croissant,
different settings allow different fixes, and the ending image shows what
changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/croissant_conflict_comedy.py
    python storyworlds/worlds/gpt-5.4/croissant_conflict_comedy.py --place bakery --fix bake_more
    python storyworlds/worlds/gpt-5.4/croissant_conflict_comedy.py --size mini --fix cut_share
    python storyworlds/worlds/gpt-5.4/croissant_conflict_comedy.py --all
    python storyworlds/worlds/gpt-5.4/croissant_conflict_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/croissant_conflict_comedy.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/croissant_conflict_comedy.py --asp
    python storyworlds/worlds/gpt-5.4/croissant_conflict_comedy.py --verify
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
FAIR_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman", "baker_woman"}
        male = {"boy", "father", "uncle", "man", "baker_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
            "baker_woman": "baker",
            "baker_man": "baker",
        }.get(self.type, self.type)
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
class Place:
    id: str
    scene: str
    line: str
    affords: set[str] = field(default_factory=set)
    helper_type: str = "mother"
    helper_label: str = "the grown-up"
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
class CroissantCfg:
    id: str
    label: str
    smell: str
    size: str
    cuttable: bool
    messy: bool
    crumbs: int
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
    fairness: int
    needs: set[str]
    works_if_squished: bool
    text: str
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "rival"}]

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


def _r_conflict(world: World) -> list[str]:
    hero = world.get("hero")
    rival = world.get("rival")
    if hero.memes["claim"] < THRESHOLD or rival.memes["claim"] < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["annoyance"] += 1
    rival.memes["annoyance"] += 1
    hero.meters["tugging"] += 1
    rival.meters["tugging"] += 1
    return ["__conflict__"]


def _r_squish(world: World) -> list[str]:
    croissant = world.get("croissant")
    hero = world.get("hero")
    rival = world.get("rival")
    if hero.meters["tugging"] < THRESHOLD or rival.meters["tugging"] < THRESHOLD:
        return []
    if croissant.meters["squished"] >= THRESHOLD:
        return []
    sig = ("squish",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    croissant.meters["squished"] += 1
    croissant.meters["intact"] = 0.0
    croissant.meters["crumbs"] += croissant.attrs["crumbs"]
    for child in world.children():
        child.memes["surprise"] += 1
        child.memes["embarrassment"] += 1
    return ["__squish__"]


CAUSAL_RULES = [
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="squish", tag="physical", apply=_r_squish),
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


def can_use_fix(place: Place, croissant: CroissantCfg, fix: Fix) -> bool:
    if not fix.needs.issubset(place.affords):
        return False
    if fix.id == "cut_share" and not croissant.cuttable:
        return False
    return True


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.fairness >= FAIR_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for size_id, croissant in CROISSANTS.items():
            for fix_id, fix in FIXES.items():
                if can_use_fix(place, croissant, fix) and fix.fairness >= FAIR_MIN:
                    combos.append((place_id, size_id, fix_id))
    return combos


def predict_tug(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").memes["claim"] += 1
    sim.get("rival").memes["claim"] += 1
    propagate(sim, narrate=False)
    return {
        "conflict": sim.get("hero").memes["annoyance"] >= THRESHOLD,
        "squished": sim.get("croissant").meters["squished"] >= THRESHOLD,
        "crumbs": int(sim.get("croissant").meters["crumbs"]),
    }


def introduce(world: World, hero: Entity, rival: Entity, place: Place, croissant: CroissantCfg) -> None:
    for child in (hero, rival):
        child.memes["joy"] += 1
        child.memes["hunger"] += 1
    world.say(
        f"One cheerful morning, {hero.id} and {rival.id} were at {place.scene}. "
        f"{place.line}"
    )
    world.say(
        f"On the plate sat one last {croissant.label}. It smelled {croissant.smell}, "
        f"as if the whole room had put on a buttery hat."
    )


def desire(world: World, hero: Entity, rival: Entity, croissant: Entity) -> None:
    hero.memes["claim"] += 1
    rival.memes["claim"] += 1
    world.say(f'"That croissant is mine," said {hero.id}.')
    world.say(f'"No, it was smiling at me," said {rival.id}.')
    croissant.memes["importance"] += 1


def warning(world: World, helper: Entity) -> None:
    pred = predict_tug(world)
    world.facts["predicted_squished"] = pred["squished"]
    world.facts["predicted_crumbs"] = pred["crumbs"]
    if pred["squished"]:
        world.say(
            f'{helper.label_word.capitalize()} looked at their hands creeping toward the plate. '
            f'"Careful," {helper.pronoun()} said. "If two people pull one pastry at once, '
            f"the croissant will not become two croissants. It will become one sad accordion."
        )


def grab_and_tug(world: World, hero: Entity, rival: Entity, croissant: Entity) -> None:
    croissant.meters["held"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Of course, both children reached at the same time. Two small hands caught "
        f"the same flaky moon, and a tug-of-war began right over the plate."
    )
    if croissant.meters["squished"] >= THRESHOLD:
        world.say(
            f"The croissant gave a tiny fwump. Buttery layers folded in the middle, "
            f"and {int(croissant.meters['crumbs'])} brave crumbs flew out like confetti."
        )
    else:
        world.say("For one wiggly second, the croissant somehow survived.")


def react(world: World, hero: Entity, rival: Entity) -> None:
    if world.get("croissant").meters["squished"] >= THRESHOLD:
        world.say(
            f"{hero.id} and {rival.id} both froze. Nobody looked heroic. "
            f"They looked like two squirrels who had accidentally hugged a pillow."
        )


def solve(world: World, helper: Entity, fix: Fix, croissant_cfg: CroissantCfg) -> str:
    croissant = world.get("croissant")
    squished = croissant.meters["squished"] >= THRESHOLD
    if squished and not fix.works_if_squished:
        raise StoryError(
            f"(No story: {fix.id} only works if the croissant stays intact, but the tug squished it.)"
        )

    if fix.id == "cut_share":
        croissant.meters["shared"] += 1
        world.say(
            f'{helper.label_word.capitalize()} took a small knife, trimmed the squashed middle neat, '
            f"and cut the croissant into two fair halves."
        )
        world.say(
            f"Each half was a little crooked, but that only made it funnier. "
            f"They looked like two sleepy crescent moons trying to wave."
        )
        outcome = "shared"
    elif fix.id == "bake_more":
        croissant.meters["saved_for_plate"] += 1
        world.say(
            f'{helper.label_word.capitalize()} lifted one floury finger. "Nobody panic," '
            f'{helper.pronoun()} said. "The oven still believes in second chances."'
        )
        world.say(
            f"Soon a whole tray of warm croissants came out puffed and proud, "
            f"and the squished one was declared the official funny sample."
        )
        outcome = "more"
    elif fix.id == "jam_hat":
        croissant.meters["shared"] += 1
        croissant.meters["jammed"] += 1
        world.say(
            f'{helper.label_word.capitalize()} spread a bright spoonful of jam over the squashed spot '
            f'and said, "There. Now it is wearing a jam hat."'
        )
        world.say(
            f"Then {helper.pronoun()} cut the croissant in two and slid the stickiest, reddest part "
            f"right down the middle so both children got an equal bite."
        )
        outcome = "shared_jam"
    else:
        raise StoryError(f"(No story: unknown fix '{fix.id}'.)")

    for child in world.children():
        child.memes["relief"] += 1
        child.memes["joy"] += 1
        child.memes["generosity"] += 1
        child.memes["annoyance"] = 0.0
        child.memes["hunger"] = 0.0
    helper.memes["calm"] += 1
    world.facts["outcome"] = outcome
    return outcome


def lesson(world: World, hero: Entity, rival: Entity, helper: Entity) -> None:
    world.say(
        f'"Next time," said {helper.label_word}, "use words before hands."'
    )
    world.say(
        f'{hero.id} nodded. {rival.id} nodded too. It is hard to argue with good advice '
        f"when a pastry has already made the joke for you."
    )


def ending(world: World, hero: Entity, rival: Entity, croissant_cfg: CroissantCfg, outcome: str) -> None:
    if outcome == "more":
        world.say(
            f"By the end, {hero.id} and {rival.id} were laughing with full cheeks while the tray steamed "
            f"between them. The last lonely croissant was no longer the boss of breakfast."
        )
    elif outcome == "shared_jam":
        world.say(
            f"By the end, both children sat with pink jam on their noses and matching half-croissants "
            f"in their hands. The silly little disaster had turned into the funniest snack of the morning."
        )
    else:
        world.say(
            f"By the end, {hero.id} and {rival.id} were nibbling neat little halves and comparing whose "
            f"piece looked more like a moon. The croissant was smaller, but the quarrel was gone."
        )
@dataclass
class StoryParams:
    place: str
    size: str
    fix: str
    hero_name: str
    hero_type: str
    rival_name: str
    rival_type: str
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
    "croissant": [
        (
            "What is a croissant?",
            "A croissant is a flaky, buttery pastry shaped a little like a crescent moon. When you bite it, little crisp layers can break into crumbs."
        )
    ],
    "sharing": [
        (
            "Why is sharing helpful when two people want the same snack?",
            "Sharing can turn one problem into a fair plan. It helps both people feel included, so the argument usually gets smaller."
        )
    ],
    "jam": [
        (
            "What is jam?",
            "Jam is fruit cooked with sugar until it turns soft and spreadable. People put it on bread or pastries for a sweet taste."
        )
    ],
    "bakery": [
        (
            "What does a baker do?",
            "A baker makes bread and pastries like rolls, buns, and croissants. Bakers use ovens to turn dough into warm food."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    fix = f["fix"]
    croissant_cfg = f["croissant_cfg"]
    hero = f["hero"]
    rival = f["rival"]
    return [
        f'Write a funny story for a 3-to-5-year-old about two children arguing over one {croissant_cfg.label} at {place.scene}. Include the word "croissant".',
        f"Tell a comedy where {hero.attrs['name']} and {rival.attrs['name']} both want the same pastry, a silly conflict squishes it, and {place.helper_label} solves the breakfast problem.",
        f'Write a gentle conflict story where a croissant almost becomes the boss of the room, but the ending uses {fix.id.replace("_", " ")} to make everyone laugh instead.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    rival = f["rival"]
    helper = f["helper"]
    place = f["place"]
    croissant_cfg = f["croissant_cfg"]
    fix = f["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.attrs['name']} and {rival.attrs['name']}, two hungry children, and {helper.label_word} at {place.scene}."
        ),
        (
            "What caused the conflict?",
            f"The conflict began because there was only one last {croissant_cfg.label}, and both children wanted it. Each one claimed the pastry before they stopped to make a fair plan."
        ),
        (
            "What happened when they both grabbed the croissant?",
            f"They started a tug-of-war over the same pastry, and the croissant got squished. That silly accident sent crumbs flying and made them both feel embarrassed."
        ),
    ]
    if f["outcome"] == "more":
        qa.append(
            (
                "How was the problem solved?",
                f"{helper.label_word.capitalize()} solved it by {fix.qa_text}. That changed the problem from one scarce snack into plenty, so the quarrel no longer had anything to hold onto."
            )
        )
        qa.append(
            (
                "Why was the ending funny instead of angry?",
                f"The grown-up treated the squashed pastry like a joke instead of a disaster. Once everyone laughed, the children could let go of the argument and enjoy breakfast."
            )
        )
    elif f["outcome"] == "shared_jam":
        qa.append(
            (
                "How did the helper fix the squished croissant?",
                f"{helper.label_word.capitalize()} put jam over the squashed middle and then split the croissant fairly. The jam turned the accident into something playful, so both children could still share."
            )
        )
        qa.append(
            (
                "What showed that the quarrel was over at the end?",
                f"Both children were eating matching halves and laughing with jam on their noses. That final image shows they had stopped fighting and started sharing."
            )
        )
    else:
        qa.append(
            (
                "How did the helper make things fair?",
                f"{helper.label_word.capitalize()} {fix.qa_text}. Because each child got a piece, neither one had to win by taking everything."
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned to use words before grabbing. The squished croissant showed them that fighting over one snack can leave everyone with crumbs and a silly face."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"croissant", "sharing"}
    fix = world.facts["fix"]
    place = world.facts["place"]
    if "jam" in fix.tags:
        tags.add("jam")
    if "bakery" in place.tags or "bakery" in fix.tags:
        tags.add("bakery")
    out: list[tuple[str, str]] = []
    for tag in ["croissant", "sharing", "jam", "bakery"]:
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, croissant: CroissantCfg, fix: Fix) -> str:
    if fix.fairness < FAIR_MIN:
        return (
            f"(No story: the fix '{fix.id}' is too unfair for this world. A comedy conflict should end with a kinder plan, not a winner-takes-all answer.)"
        )
    if not fix.needs.issubset(place.affords):
        missing = sorted(fix.needs - place.affords)
        return (
            f"(No story: {place.scene} does not have what '{fix.id}' needs: {missing}. Pick a setting where that fix is possible.)"
        )
    if fix.id == "cut_share" and not croissant.cuttable:
        return (
            f"(No story: a {croissant.label} is too small to cut into fair pieces here. Pick a bigger croissant or another fix.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    if params.fix == "bake_more":
        return "more"
    if params.fix == "jam_hat":
        return "shared_jam"
    return "shared"


ASP_RULES = r"""
usable_fix(P, S, F) :- place(P), size(S), fix(F),
                       fairness(F, N), fair_min(M), N >= M,
                       needs_met(P, F),
                       not blocked_cut(P, S, F).

needs_met(P, F) :- not needs_any(F).
needs_met(P, F) :- need(F, X), affords(P, X), not missing_need(P, F).
missing_need(P, F) :- need(F, X), not affords(P, X).

blocked_cut(_, S, cut_share) :- not cuttable(S).
blocked_cut(_, _, F) :- fix(F), F != cut_share, false_block(F).
false_block(F) :- fix(F), not fake_ok(F).
fake_ok(F) :- fix(F).

valid(P, S, F) :- usable_fix(P, S, F).

outcome(shared) :- chosen_fix(cut_share).
outcome(more) :- chosen_fix(bake_more).
outcome(shared_jam) :- chosen_fix(jam_hat).
"""

# The blocked_cut/fake_ok lines keep the program fully grounded and explicit
# while staying deterministic with the shared helper API.


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for affordance in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, affordance))
    for size_id, croissant in CROISSANTS.items():
        lines.append(asp.fact("size", size_id))
        if croissant.cuttable:
            lines.append(asp.fact("cuttable", size_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("fairness", fix_id, fix.fairness))
        if not fix.needs:
            lines.append(asp.fact("needs_any", fix_id))
        for need in sorted(fix.needs):
            lines.append(asp.fact("need", fix_id, need))
        lines.append(asp.fact("fake_ok", fix_id))
    lines.append(asp.fact("fair_min", FAIR_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("chosen_fix", params.fix)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outcomes = asp.atoms(model, "outcome")
    return outcomes[0][0] if outcomes else "?"


CURATED = [
    StoryParams(
        place="kitchen",
        size="big",
        fix="cut_share",
        hero_name="Mia",
        hero_type="girl",
        rival_name="Ben",
        rival_type="boy",
    ),
    StoryParams(
        place="bakery",
        size="chocolate",
        fix="bake_more",
        hero_name="Ava",
        hero_type="girl",
        rival_name="Max",
        rival_type="boy",
    ),
    StoryParams(
        place="picnic",
        size="big",
        fix="jam_hat",
        hero_name="Nora",
        hero_type="girl",
        rival_name="Leo",
        rival_type="boy",
    ),
    StoryParams(
        place="bakery",
        size="mini",
        fix="jam_hat",
        hero_name="Ella",
        hero_type="girl",
        rival_name="Theo",
        rival_type="boy",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a funny conflict over the last croissant."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--size", choices=CROISSANTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.size and args.fix:
        place = PLACES[args.place]
        croissant = CROISSANTS[args.size]
        fix = FIXES[args.fix]
        if not can_use_fix(place, croissant, fix) or fix.fairness < FAIR_MIN:
            raise StoryError(explain_rejection(place, croissant, fix))
    if args.fix and FIXES[args.fix].fairness < FAIR_MIN:
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        croissant = CROISSANTS[args.size] if args.size else next(iter(CROISSANTS.values()))
        raise StoryError(explain_rejection(place, croissant, FIXES[args.fix]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.size is None or combo[1] == args.size)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, size_id, fix_id = rng.choice(sorted(combos))
    hero_type = rng.choice(["girl", "boy"])
    rival_type = "boy" if hero_type == "girl" else "girl"
    hero_name = _pick_name(rng, hero_type)
    rival_name = _pick_name(rng, rival_type, avoid=hero_name)
    return StoryParams(
        place=place_id,
        size=size_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_type=hero_type,
        rival_name=rival_name,
        rival_type=rival_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.size not in CROISSANTS:
        raise StoryError(f"(No story: unknown size '{params.size}'.)")
    if params.fix not in FIXES:
        raise StoryError(f"(No story: unknown fix '{params.fix}'.)")

    place = PLACES[params.place]
    croissant = CROISSANTS[params.size]
    fix = FIXES[params.fix]
    if not can_use_fix(place, croissant, fix) or fix.fairness < FAIR_MIN:
        raise StoryError(explain_rejection(place, croissant, fix))

    world = tell(
        place=place,
        croissant_cfg=croissant,
        fix=fix,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        rival_name=params.rival_name,
        rival_type=params.rival_type,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(20):
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
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: normal story generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, size, fix) combos:\n")
        for place, size, fix in combos:
            print(f"  {place:8} {size:10} {fix}")
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
            header = f"### {p.hero_name} & {p.rival_name}: {p.size} croissant at {p.place} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    place: Place,
    croissant_cfg: CroissantCfg,
    fix: Fix,
    hero_name: str = "Mia",
    hero_type: str = "girl",
    rival_name: str = "Ben",
    rival_type: str = "boy",
) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    rival = world.add(Entity(id="rival", kind="character", type=rival_type, label=rival_name, role="rival"))
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=place.helper_type,
            label=place.helper_label,
            role="helper",
        )
    )
    croissant = world.add(
        Entity(
            id="croissant",
            kind="thing",
            type="pastry",
            label=croissant_cfg.label,
            role="prize",
            attrs={"crumbs": croissant_cfg.crumbs},
        )
    )
    croissant.meters["intact"] = 1.0
    croissant.meters["squished"] = 0.0
    croissant.meters["crumbs"] = 0.0
    hero.attrs["name"] = hero_name
    rival.attrs["name"] = rival_name
    helper.attrs["name"] = place.helper_label

    introduce(world, hero, rival, place, croissant_cfg)
    world.para()
    desire(world, hero, rival, croissant)
    warning(world, helper)
    grab_and_tug(world, hero, rival, croissant)
    react(world, hero, rival)
    world.para()
    outcome = solve(world, helper, fix, croissant_cfg)
    lesson(world, hero, rival, helper)
    world.para()
    ending(world, hero, rival, croissant_cfg, outcome)

    world.facts.update(
        hero=hero,
        rival=rival,
        helper=helper,
        place=place,
        croissant_cfg=croissant_cfg,
        croissant=croissant,
        fix=fix,
        squished=croissant.meters["squished"] >= THRESHOLD,
        crumbs=int(croissant.meters["crumbs"]),
        outcome=outcome,
    )
    return world


PLACES = {
    "kitchen": Place(
        id="kitchen",
        scene="the family kitchen",
        line="A teapot puffed on the table, and a sunny plate waited by the window.",
        affords={"knife", "jam"},
        helper_type="mother",
        helper_label="the grown-up",
        tags={"kitchen"},
    ),
    "bakery": Place(
        id="bakery",
        scene="the little corner bakery",
        line="The bell over the door kept jingling as if it could not stop laughing.",
        affords={"knife", "oven", "jam"},
        helper_type="baker_woman",
        helper_label="the baker",
        tags={"bakery"},
    ),
    "picnic": Place(
        id="picnic",
        scene="a park picnic table",
        line="A paper napkin kept trying to fly away, and the juice cups wobbled every time someone giggled.",
        affords={"jam"},
        helper_type="aunt",
        helper_label="their aunt",
        tags={"park"},
    ),
}

CROISSANTS = {
    "big": CroissantCfg(
        id="big",
        label="croissant",
        smell="warm and buttery",
        size="big",
        cuttable=True,
        messy=False,
        crumbs=7,
        tags={"croissant"},
    ),
    "mini": CroissantCfg(
        id="mini",
        label="mini croissant",
        smell="sweet and toasty",
        size="mini",
        cuttable=False,
        messy=False,
        crumbs=5,
        tags={"croissant"},
    ),
    "chocolate": CroissantCfg(
        id="chocolate",
        label="chocolate croissant",
        smell="warm, buttery, and a little like a secret dessert",
        size="big",
        cuttable=True,
        messy=True,
        crumbs=8,
        tags={"croissant", "chocolate"},
    ),
}

FIXES = {
    "cut_share": Fix(
        id="cut_share",
        fairness=2,
        needs={"knife"},
        works_if_squished=True,
        text="cut it into two fair pieces",
        qa_text="cut the croissant into two fair halves so both children could have some",
        tags={"sharing"},
    ),
    "bake_more": Fix(
        id="bake_more",
        fairness=3,
        needs={"oven"},
        works_if_squished=True,
        text="bake more croissants for everyone",
        qa_text="bake more croissants so there was no need to fight over one pastry",
        tags={"bakery", "sharing"},
    ),
    "jam_hat": Fix(
        id="jam_hat",
        fairness=2,
        needs={"jam"},
        works_if_squished=True,
        text="turn the squashed middle into a funny jam hat and then share it",
        qa_text="cover the squashed middle with jam and split the croissant fairly",
        tags={"jam", "sharing"},
    ),
    "winner_keeps": Fix(
        id="winner_keeps",
        fairness=1,
        needs=set(),
        works_if_squished=False,
        text="let one child keep the whole pastry",
        qa_text="let one child keep the whole croissant",
        tags={"unfair"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Finn", "Theo"]

if __name__ == "__main__":
    main()
