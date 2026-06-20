#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/difficulty_cautionary_twist_conflict_adventure.py
============================================================================

A standalone story world for a small cautionary adventure tale about two children
on a pretend quest who meet a real difficulty on the trail. One wants to take an
unsafe shortcut, the other warns against it, and a guide helps them learn that
the safe route was the true way forward all along.

This world models:

- a bright adventure setup
- a concrete trail difficulty
- a conflict between boldness and caution
- a cautionary unsafe attempt or an averted near-miss
- a twist: the treasure marker waits by the safe route, not beyond the shortcut

Run it
------
    python storyworlds/worlds/gpt-5.4/difficulty_cautionary_twist_conflict_adventure.py
    python storyworlds/worlds/gpt-5.4/difficulty_cautionary_twist_conflict_adventure.py --obstacle creek --shortcut stones
    python storyworlds/worlds/gpt-5.4/difficulty_cautionary_twist_conflict_adventure.py --obstacle creek --shortcut scramble
    python storyworlds/worlds/gpt-5.4/difficulty_cautionary_twist_conflict_adventure.py --all
    python storyworlds/worlds/gpt-5.4/difficulty_cautionary_twist_conflict_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/difficulty_cautionary_twist_conflict_adventure.py --verify
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
BOLDNESS_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "sensible", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "ranger_woman"}
        male = {"boy", "father", "grandfather", "man", "ranger_man"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "ranger_woman": "ranger",
            "ranger_man": "ranger",
        }.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    opener: str
    goal: str
    reward: str
    reward_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    article: str
    difficulty: str
    danger: str
    safe_route: str
    safe_route_short: str
    setback: str
    rescue: str
    consequence: str
    risk: int
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.article[0].upper() + self.article[1:]


@dataclass
class Shortcut:
    id: str
    label: str
    verb: str
    boast: str
    warning: str
    works_on: str
    risk_push: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    type: str
    arrival: str
    lesson: str
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
        return [e for e in self.entities.values() if e.role in ("instigator", "cautioner")]

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


def _r_setback(world: World) -> list[str]:
    out: list[str] = []
    obstacle: Obstacle = world.facts["obstacle_cfg"]
    threshold = obstacle.risk + 1
    for kid in world.kids():
        if kid.role != "instigator":
            continue
        if kid.meters["risk"] < threshold:
            continue
        sig = ("setback", kid.id, obstacle.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.meters[obstacle.consequence] += 1
        kid.meters["stuck"] += 1
        world.get("trail").meters["danger"] += 1
        for other in world.kids():
            if other.id != kid.id:
                other.memes["fear"] += 1
        out.append("__setback__")
    return out


CAUSAL_RULES = [
    Rule("setback", "physical", _r_setback),
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


THEMES = {
    "treasure": Theme(
        "treasure",
        "a treasure trail",
        "A hand-drawn map and a tin compass turned the afternoon into a treasure trail.",
        "the brass bell at the lookout",
        "brass bell",
        "the little brass bell tied beside the safe trail sign",
        tags={"map", "trail", "treasure"},
    ),
    "dragon": Theme(
        "dragon",
        "a dragon quest",
        "A rolled paper map and a cardboard shield turned the afternoon into a dragon quest.",
        "the dragon badge at the lookout",
        "dragon badge",
        "the shiny dragon badge clipped beside the safe trail sign",
        tags={"map", "trail", "badge"},
    ),
    "rescue": Theme(
        "rescue",
        "a rescue mission",
        "A red string map and a toy whistle turned the afternoon into a rescue mission.",
        "the rescue flag at the lookout",
        "rescue flag",
        "the bright rescue flag fluttering beside the safe trail sign",
        tags={"map", "trail", "flag"},
    ),
}

OBSTACLES = {
    "creek": Obstacle(
        "creek",
        "creek",
        "the creek",
        "a splashing difficulty",
        "the stones were slick and the water below them moved fast",
        "a little wooden footbridge",
        "the footbridge",
        "one shoe slid, and cold water splashed up to the child's knees",
        "used a long branch to steady the child and guided the child back to shore",
        "wet",
        3,
        tags={"creek", "water", "bridge"},
    ),
    "thorns": Obstacle(
        "thorns",
        "thorn patch",
        "the thorn patch",
        "a prickly difficulty",
        "the narrow gap was full of hooks and scratchy stems",
        "a winding path around the bushes",
        "the winding path",
        "the child pushed in too far and the thorns caught at sleeves and socks",
        "lifted the branches aside with gloved hands and led the child out",
        "scratched",
        2,
        tags={"thorns", "path"},
    ),
    "hill": Obstacle(
        "hill",
        "steep hill",
        "the steep hill",
        "a tall difficulty",
        "the dirt was loose and pebbles rolled under small shoes",
        "a zigzag set of wooden steps",
        "the zigzag steps",
        "the child scrambled twice, then slid back to a sitting bump in the dirt",
        "held out a strong hand and helped the child down before trying the steps",
        "bumped",
        3,
        tags={"hill", "steps", "climb"},
    ),
}

SHORTCUTS = {
    "stones": Shortcut(
        "stones",
        "wet stones",
        "hop across the wet stones",
        "The stones look faster.",
        "Those stones are slippery.",
        "creek",
        2,
        tags={"stones", "water"},
    ),
    "gap": Shortcut(
        "gap",
        "thorny gap",
        "squeeze through the thorny gap",
        "The gap is shorter.",
        "Those thorns grab clothes and skin.",
        "thorns",
        2,
        tags={"thorns", "shortcut"},
    ),
    "scramble": Shortcut(
        "scramble",
        "loose dirt",
        "scramble straight up the loose dirt",
        "Straight up is quicker.",
        "Loose dirt can slide under your feet.",
        "hill",
        2,
        tags={"hill", "shortcut"},
    ),
}

GUIDES = {
    "mother": Guide(
        "mother",
        "mother",
        "Mom came up the trail as soon as she heard them call.",
        "Shortcuts are not brave when they hide danger. The true brave choice is the safe one.",
        tags={"adult", "help"},
    ),
    "father": Guide(
        "father",
        "father",
        "Dad came along the trail the moment he heard the shout.",
        "Rushing past a danger is not real courage. Real courage listens and chooses the safe way.",
        tags={"adult", "help"},
    ),
    "grandpa": Guide(
        "grandpa",
        "grandfather",
        "Grandpa hurried over with calm steps and a steady voice.",
        "Adventure still needs good sense. A safe path can be part of the adventure too.",
        tags={"adult", "help"},
    ),
    "ranger": Guide(
        "ranger",
        "ranger_man",
        "The ranger heard the cry and came quickly from the next bend in the trail.",
        "A trail gives warnings for a reason. The safe route is there to help explorers succeed.",
        tags={"adult", "help", "ranger"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "steady", "sensible", "patient", "thoughtful", "curious"]
RELATIONS = ["siblings", "friends"]


def hazard_match(obstacle: Obstacle, shortcut: Shortcut) -> bool:
    return obstacle.id == shortcut.works_on


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for obstacle_id, obstacle in OBSTACLES.items():
            for shortcut_id, shortcut in SHORTCUTS.items():
                if hazard_match(obstacle, shortcut):
                    combos.append((theme, obstacle_id, shortcut_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older_sibling else 0.0)
    return older_sibling and authority > BOLDNESS_INIT


def predict_setback(world: World) -> bool:
    sim = world.copy()
    instigator = sim.facts["instigator"]
    shortcut: Shortcut = sim.facts["shortcut_cfg"]
    instigator_ent = sim.get(instigator.id)
    instigator_ent.meters["risk"] += shortcut.risk_push + sim.facts["obstacle_cfg"].risk
    propagate(sim, narrate=False)
    return instigator_ent.meters["stuck"] >= THRESHOLD


def setup(world: World, a: Entity, b: Entity, theme: Theme, guide: Entity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"{a.id} and {b.id} were walking with {guide.label_word} on a wooded trail. "
        f"{theme.opener}"
    )
    world.say(
        f'Today they were searching for {theme.goal}, and every turn in the path '
        f'made them feel like real explorers.'
    )


def reach_difficulty(world: World, a: Entity, b: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"Then they reached {obstacle.article}, the first real difficulty of the trail. "
        f"It was {obstacle.difficulty}, because {obstacle.danger}."
    )
    world.say(f"{b.id} slowed down and looked hard at the ground ahead.")


def tempt(world: World, a: Entity, shortcut: Shortcut) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'{a.id} pointed at {shortcut.label}. "{shortcut.boast} I can just '
        f'{shortcut.verb}."'
    )


def warn(world: World, b: Entity, a: Entity, obstacle: Obstacle, shortcut: Shortcut) -> None:
    setback = predict_setback(world)
    b.memes["caution"] += 1
    world.facts["predicted_setback"] = setback
    extra = ""
    if setback:
        extra = f" {b.pronoun().capitalize()} could almost picture {a.id} slipping and needing help."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{shortcut.warning} '
        f'Let\'s use {obstacle.safe_route_short} instead."{extra}'
    )


def defy(world: World, a: Entity, b: Entity, shortcut: Shortcut) -> None:
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"We will lose time if we go the long way," {a.id} argued. '
            f"Because {a.pronoun()} was the older one, {b.id} could not stop "
            f"{a.pronoun('object')}."
        )
    else:
        world.say(
            f'"We will lose time if we go the long way," {a.id} argued, and before '
            f"{b.id} could answer, {a.pronoun()} tried to {shortcut.verb}."
        )


def back_down(world: World, a: Entity, b: Entity, obstacle: Obstacle) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} stared at {obstacle.article} for one more second, then blew out a breath."
    )
    world.say(
        f'"All right," {a.pronoun()} said. "The shortcut can wait." Together they '
        f"turned toward {obstacle.safe_route_short}."
    )


def attempt(world: World, a: Entity, obstacle: Obstacle, shortcut: Shortcut) -> None:
    a.meters["risk"] += obstacle.risk + shortcut.risk_push
    propagate(world, narrate=False)
    if a.meters["stuck"] >= THRESHOLD:
        a.memes["fear"] += 1
        world.say(
            f"But {obstacle.setback} At once the adventure stopped feeling playful."
        )


def alarm(world: World, b: Entity, guide: Entity, a: Entity) -> None:
    world.say(f'"{guide.label_word.capitalize()}! {a.id} needs help!" {b.id} shouted.')


def rescue(world: World, guide: Entity, a: Entity, obstacle: Obstacle) -> None:
    a.meters["stuck"] = 0.0
    world.get("trail").meters["danger"] = 0.0
    a.memes["relief"] += 1
    world.say(guide.attrs["arrival"])
    world.say(
        f"{guide.pronoun().capitalize()} {obstacle.rescue}. Soon {a.id} was safe "
        f"again, with a thumping heart and quiet cheeks."
    )


def lesson(world: World, guide: Entity, a: Entity, b: Entity, obstacle: Obstacle) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{guide.label_word.capitalize()} knelt beside them. "{guide.attrs["lesson"]}"'
    )
    if a.meters[obstacle.consequence] >= THRESHOLD:
        world.say(
            f"{a.id} looked at {a.pronoun('possessive')} {obstacle.consequence} clothes "
            f"and nodded. {b.id} nodded too."
        )
    else:
        world.say(f"{a.id} and {b.id} listened closely and nodded.")


def twist_and_reward(world: World, a: Entity, b: Entity, theme: Theme, obstacle: Obstacle) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    world.say(
        f"They followed {obstacle.safe_route_short}, and around the next bend came the twist:"
    )
    world.say(
        f"{theme.reward_phrase} was waiting right there. The trail had never asked "
        f"them to beat the danger; it had asked them to read it well."
    )
    world.say(
        f"{a.id} rang the {theme.reward} while {b.id} laughed, and the adventure felt "
        f"bigger now that they understood how to be brave and careful together."
    )


def tell(
    theme: Theme,
    obstacle: Obstacle,
    shortcut: Shortcut,
    guide_cfg: Guide,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    trait: str = "careful",
    relation: str = "siblings",
    instigator_age: int = 6,
    cautioner_age: int = 4,
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            traits=["bold"],
            age=instigator_age,
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            traits=[trait],
            age=cautioner_age,
            attrs={"relation": relation},
        )
    )
    guide = world.add(
        Entity(
            id="Guide",
            kind="character",
            type=guide_cfg.type,
            role="guide",
            label="the guide",
            attrs={"arrival": guide_cfg.arrival, "lesson": guide_cfg.lesson},
        )
    )
    trail = world.add(Entity(id="trail", type="trail", label="the trail"))
    world.facts.update(
        theme=theme,
        obstacle_cfg=obstacle,
        shortcut_cfg=shortcut,
        guide_cfg=guide_cfg,
        instigator=a,
        cautioner=b,
        guide=guide,
        trail=trail,
    )

    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["caution"] = initial_caution(trait)

    setup(world, a, b, theme, guide)
    reach_difficulty(world, a, b, obstacle)

    world.para()
    tempt(world, a, shortcut)
    warn(world, b, a, obstacle, shortcut)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, obstacle)
        world.para()
        lesson(world, guide, a, b, obstacle)
        twist_and_reward(world, a, b, theme, obstacle)
        outcome = "averted"
    else:
        defy(world, a, b, shortcut)
        world.para()
        attempt(world, a, obstacle, shortcut)
        alarm(world, b, guide, a)
        world.para()
        rescue(world, guide, a, obstacle)
        lesson(world, guide, a, b, obstacle)
        world.para()
        twist_and_reward(world, a, b, theme, obstacle)
        outcome = "rescued"

    world.facts.update(
        relation=relation,
        outcome=outcome,
        difficulty=obstacle.difficulty,
        consequence=obstacle.consequence,
        setback_happened=a.meters[obstacle.consequence] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    theme: str
    obstacle: str
    shortcut: str
    guide: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 4
    seed: Optional[int] = None


KNOWLEDGE = {
    "trail": [(
        "What does a trail sign do?",
        "A trail sign shows people where to go. It helps explorers choose the safer path."
    )],
    "bridge": [(
        "Why is a bridge safer than hopping on wet stones?",
        "A bridge gives you a steady place to walk. Wet stones can be slippery and make you fall."
    )],
    "water": [(
        "Why can wet stones be dangerous?",
        "Wet stones can be slick, so your feet may slide off them. That can make you fall into cold water."
    )],
    "thorns": [(
        "Why are thorns a problem on a trail?",
        "Thorns can scratch skin and catch clothes. That is why people go around them instead of pushing through."
    )],
    "path": [(
        "Why is a winding path useful?",
        "A winding path goes around a danger instead of through it. Sometimes the longer way is the safer way."
    )],
    "hill": [(
        "Why can a steep hill be hard to climb?",
        "A steep hill can make your feet slide, especially if the dirt is loose. Climbing carefully helps you stay safe."
    )],
    "steps": [(
        "Why are steps safer than climbing straight up loose dirt?",
        "Steps give your feet a firmer place to land. Loose dirt can slip and make you slide backward."
    )],
    "adult": [(
        "What should a child do when a trail feels unsafe?",
        "Stop and call for a grown-up right away. Asking for help is a smart part of being brave."
    )],
    "map": [(
        "What is a map for?",
        "A map helps you see where to go. It can show a safer route when a place looks tricky."
    )],
    "badge": [(
        "What is a trail badge?",
        "A trail badge is a small prize or marker explorers find at the end of a route. It shows they finished the trail."
    )],
    "flag": [(
        "Why do explorers use flags?",
        "Flags are bright and easy to spot from far away. They can mark a safe place or the end of a route."
    )],
}
KNOWLEDGE_ORDER = ["map", "trail", "water", "bridge", "thorns", "path", "hill", "steps", "adult", "badge", "flag"]


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
    a = f["instigator"]
    b = f["cautioner"]
    theme: Theme = f["theme"]
    obstacle: Obstacle = f["obstacle_cfg"]
    shortcut: Shortcut = f["shortcut_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short adventure story for a 3-to-5-year-old that includes the word "difficulty" and a safe twist ending.',
            f"Tell a cautionary trail story where {a.id} wants to {shortcut.verb}, but {b.id} talks {a.pronoun('object')} out of it and they discover the prize by the safe route.",
            f'Write a story with conflict between two young explorers, a warning about danger, and a happy twist that shows the longer path was the right one.'
        ]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the word "difficulty", an unsafe shortcut, and a calm rescue.',
        f"Tell a cautionary story where {a.id} argues for a shortcut at {obstacle.article}, needs help, and then learns the safe route held the prize all along.",
        f'Write a child-facing adventure with conflict, a small dangerous mistake, and a twist ending where being careful turns out to be the real way to win.'
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a: Entity = f["instigator"]
    b: Entity = f["cautioner"]
    guide: Entity = f["guide"]
    theme: Theme = f["theme"]
    obstacle: Obstacle = f["obstacle_cfg"]
    shortcut: Shortcut = f["shortcut_cfg"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, on an adventure trail with {guide.label_word}. They were searching for {theme.goal}."
        ),
        (
            "What was the first difficulty on the trail?",
            f"The first difficulty was {obstacle.article}. It was hard because {obstacle.danger}."
        ),
        (
            f"What did {a.id} want to do, and why did {b.id} disagree?",
            f"{a.id} wanted to {shortcut.verb} because it looked faster. {b.id} disagreed because {shortcut.warning.lower()} and the safe route was steadier."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"How was the conflict solved?",
            f"The conflict was solved when {a.id} listened and gave up the shortcut. That let them choose {obstacle.safe_route_short} before anyone got hurt."
        ))
    else:
        qa.append((
            f"What happened when {a.id} tried the shortcut?",
            f"{obstacle.setback[0].upper()}{obstacle.setback[1:]}. The danger became real, so {b.id} called {guide.label_word} for help."
        ))
        qa.append((
            f"How did {guide.label_word} help?",
            f"{guide.label_word.capitalize()} came quickly and {obstacle.rescue}. That made the trail safe again and gave the children time to listen to the warning."
        ))
    qa.append((
        "What was the twist at the end?",
        f"The twist was that {theme.reward_phrase} was beside {obstacle.safe_route_short}, not beyond the shortcut. The trail was teaching them to notice the safe way, not race past danger."
    ))
    qa.append((
        "What did the children learn?",
        f"They learned that a shortcut is not a good choice when it hides danger. In this adventure, being careful was part of being brave."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    theme: Theme = f["theme"]
    obstacle: Obstacle = f["obstacle_cfg"]
    tags = set(theme.tags) | set(obstacle.tags) | {"adult"}
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        "treasure", "creek", "stones", "mother",
        "Tom", "boy", "Lily", "girl", "careful",
        relation="siblings", instigator_age=6, cautioner_age=4,
    ),
    StoryParams(
        "dragon", "thorns", "gap", "grandpa",
        "Mia", "girl", "Ben", "boy", "steady",
        relation="friends", instigator_age=5, cautioner_age=5,
    ),
    StoryParams(
        "rescue", "hill", "scramble", "ranger",
        "Sam", "boy", "Zoe", "girl", "patient",
        relation="siblings", instigator_age=5, cautioner_age=7,
    ),
]


def explain_rejection(obstacle: Obstacle, shortcut: Shortcut) -> str:
    return (
        f"(No story: {shortcut.label} does not fit {obstacle.article}. "
        f"This world only allows shortcuts that match the real trail difficulty, "
        f"so the danger and the warning stay honest.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "rescued"


ASP_RULES = r"""
% valid combinations: the shortcut must fit the obstacle
valid(T, O, S) :- theme(T), obstacle(O), shortcut(S), works_on(S, O).

% averted outcome: older sibling with enough caution to overrule boldness
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
outcome(averted) :- older_sibling, authority(A), boldness_init(B), A > B.
outcome(rescued) :- not outcome(averted).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("risk", oid, obstacle.risk))
    for sid, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", sid))
        lines.append(asp.fact("works_on", sid, shortcut.works_on))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    for s in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if mismatches:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")
    else:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story during smoke test")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an adventure trail, a risky shortcut, and a safe twist ending."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.shortcut:
        obstacle = OBSTACLES[args.obstacle]
        shortcut = SHORTCUTS[args.shortcut]
        if not hazard_match(obstacle, shortcut):
            raise StoryError(explain_rejection(obstacle, shortcut))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.obstacle is None or c[1] == args.obstacle)
        and (args.shortcut is None or c[2] == args.shortcut)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, obstacle, shortcut = rng.choice(sorted(combos))
    guide = args.guide or rng.choice(sorted(GUIDES))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    trait = rng.choice(TRAITS)
    relation = rng.choice(RELATIONS)
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        theme, obstacle, shortcut, guide,
        instigator, ig, cautioner, cg, trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        THEMES[params.theme],
        OBSTACLES[params.obstacle],
        SHORTCUTS[params.shortcut],
        GUIDES[params.guide],
        params.instigator,
        params.instigator_gender,
        params.cautioner,
        params.cautioner_gender,
        params.trait,
        params.relation,
        params.instigator_age,
        params.cautioner_age,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
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
        print(f"{len(combos)} compatible (theme, obstacle, shortcut) combos:\n")
        for theme, obstacle, shortcut in combos:
            print(f"  {theme:9} {obstacle:8} {shortcut}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.obstacle} via {p.shortcut} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
