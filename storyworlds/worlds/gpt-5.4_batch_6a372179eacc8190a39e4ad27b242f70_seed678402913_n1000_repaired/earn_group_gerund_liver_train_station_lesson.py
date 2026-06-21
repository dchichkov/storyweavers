#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/earn_group_gerund_liver_train_station_lesson.py
===========================================================================

A small story world set in a train station.

This world rebuilds a simple slice-of-life pattern:

- a child waits at a train station with a grown-up
- the child notices a small problem in the bustle
- the child has an inner monologue about whether to help
- the child chooses a sensible kind of help
- the child earns trust and a tiny token of praise
- the ending image shows the lesson learned

Seed words are included naturally in the domain:
- "earn" appears in the child's goal and the ending
- "group-gerund" appears as the funny notebook game the child is doing while waiting
- "liver" appears in one lunch option from the child's bag

The world enforces one common-sense rule:
different station problems need different kinds of help. Some are safe for a child
to do directly; others should be handled by asking a station worker or grown-up.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "lady", "clerk_f"}
        male = {"boy", "father", "grandfather", "man", "porter", "clerk_m"}
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
        }.get(self.type, self.type)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    intro: str
    owner_phrase: str
    owner_type: str
    location: str
    direct_ok: bool = False
    adult_ok: bool = False
    edge_risk: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    label: str
    sense: int
    mode: str
    text: str
    qa_text: str
    fail_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Reward:
    id: str
    label: str
    give_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    phrase: str
    hand_busy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class WordGame:
    id: str
    label: str
    intro: str
    sample: str
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


def _r_problem_worry(world: World) -> list[str]:
    out: list[str] = []
    owner = world.entities.get("owner")
    item = world.entities.get("item")
    if owner is None or item is None:
        return out
    if item.meters["lost"] < THRESHOLD:
        return out
    sig = ("worry", owner.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    owner.memes["worry"] += 1
    world.get("child").memes["concern"] += 1
    world.get("station").meters["bustle"] += 1
    out.append("__worry__")
    return out


def _r_help_resolves(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    owner = world.entities.get("owner")
    item = world.entities.get("item")
    if child is None or owner is None or item is None:
        return out
    if child.meters["helped"] < THRESHOLD:
        return out
    sig = ("resolve", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["lost"] = 0.0
    item.meters["found"] += 1
    owner.memes["relief"] += 1
    owner.memes["gratitude"] += 1
    child.memes["pride"] += 1
    child.memes["worry"] = 0.0
    out.append("__resolved__")
    return out


CAUSAL_RULES = [
    Rule(name="problem_worry", tag="social", apply=_r_problem_worry),
    Rule(name="help_resolves", tag="social", apply=_r_help_resolves),
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


def action_fits(problem: Problem, action: Action) -> bool:
    if action.sense < SENSE_MIN:
        return False
    if action.mode == "direct":
        return problem.direct_ok and not problem.edge_risk
    if action.mode == "adult":
        return problem.adult_ok
    return False


def sensible_actions() -> list[Action]:
    return [action for action in ACTIONS.values() if action.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for pid, problem in PROBLEMS.items():
        for aid, action in ACTIONS.items():
            if action_fits(problem, action):
                combos.append((pid, aid))
    return combos


def explain_rejection(problem: Problem, action: Action) -> str:
    if action.sense < SENSE_MIN:
        return (
            f"(No story: '{action.label}' is known to the world but refused because it "
            f"is not sensible enough for a child at a train station. Try a safer help.)"
        )
    if problem.edge_risk and action.mode == "direct":
        return (
            f"(No story: {problem.phrase} is too close to the platform edge for a child "
            f"to fix directly. In this world, the safe help is to call a grown-up or "
            f"station worker.)"
        )
    return (
        f"(No story: '{action.label}' does not honestly solve '{problem.label}'. "
        f"Pick a kind of help that matches the station problem.)"
    )


def predict_outcome(problem: Problem, action: Action) -> str:
    if not action_fits(problem, action):
        return "stuck"
    if action.mode == "adult":
        return "asked_adult"
    return "direct_help"


def predict_on_copy(world: World, problem: Problem, action: Action) -> dict:
    sim = world.copy()
    outcome = predict_outcome(problem, action)
    if outcome in {"asked_adult", "direct_help"}:
        sim.get("child").meters["helped"] += 1
        propagate(sim, narrate=False)
    return {
        "outcome": outcome,
        "resolved": sim.get("item").meters["found"] >= THRESHOLD,
        "owner_relief": sim.get("owner").memes["relief"],
    }


def introduce(world: World, child: Entity, companion: Entity, wordgame: WordGame, snack: Snack) -> None:
    world.say(
        f"{child.id} waited with {child.pronoun('possessive')} {companion.label_word} in the train station, "
        f"where shoes tapped, wheels hummed, and the big board kept flipping letters."
    )
    world.say(
        f"To pass the time, {child.pronoun()} played {wordgame.intro}. On the page, "
        f"{child.pronoun()} had written {wordgame.sample}."
    )
    world.say(
        f"In {child.pronoun('possessive')} bag was {snack.phrase}, saved for the ride."
    )


def want_to_earn(world: World, child: Entity, reward: Reward) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} hoped to earn {reward.label} before the train came. It was only a small thing, "
        f"but it made {child.pronoun('object')} stand a little taller to imagine it."
    )


def notice_problem(world: World, child: Entity, problem: Problem) -> None:
    owner = world.get("owner")
    item = world.get("item")
    item.meters["lost"] += 1
    propagate(world, narrate=False)
    world.say(problem.intro)
    world.say(
        f"{owner.label} looked around for {problem.phrase}, and {child.id} felt the worry in the air."
    )


def inner_monologue(world: World, child: Entity, problem: Problem, action: Action, snack: Snack) -> None:
    child.memes["hesitation"] += 1
    extra = ""
    if snack.hand_busy:
        extra = f" {child.pronoun().capitalize()} tightened {child.pronoun('possessive')} fingers around the bag for a moment."
    world.say(
        f'{child.id} thought, "I want to help. If I am careful, maybe I can earn that {world.facts["reward"].label} '
        f'for being useful, not just for being quiet."{extra}'
    )
    if problem.edge_risk:
        world.say(
            f'Then another thought came: "{problem.phrase.capitalize()} is too close to the edge. I should not dash after it by myself."'
        )
    elif action.mode == "adult":
        world.say(
            f'Then {child.pronoun()} reminded {child.pronoun("object")}self, "Good helping can mean asking the right grown-up."'
        )
    else:
        world.say(
            f'Then {child.pronoun()} reminded {child.pronoun("object")}self, "Small hands can still do a kind thing when it is safe."'
        )


def do_help(world: World, child: Entity, companion: Entity, problem: Problem, action: Action) -> None:
    owner = world.get("owner")
    item = world.get("item")
    outcome = predict_outcome(problem, action)
    world.facts["outcome"] = outcome
    child.meters["helped"] += 1
    if action.mode == "adult":
        world.say(
            f"{child.id} touched {companion.label_word}'s sleeve and then pointed to {item.label}. "
            f"{action.text}"
        )
    else:
        world.say(
            f"{child.id} took one careful step, then another. {action.text}"
        )
    propagate(world, narrate=False)
    if outcome == "asked_adult":
        world.say(
            f"A station worker moved quickly, staying behind the yellow line, and soon {owner.label} had {item.label} back."
        )
    else:
        world.say(
            f"In another second, {owner.label} had {item.label} back in {owner.pronoun('possessive')} hands."
        )


def thanks_and_reward(world: World, child: Entity, companion: Entity, reward: Reward) -> None:
    owner = world.get("owner")
    child.memes["lesson"] += 1
    child.memes["warmth"] += 1
    world.say(
        f'"Thank you," {owner.label} said, with a face that had gone soft again. '
        f'"You noticed before I did what to do next."'
    )
    world.say(
        f"{companion.label_word.capitalize()} smiled and {reward.give_text} "
        f"{child.id} had earned it."
    )


def closing(world: World, child: Entity, companion: Entity, reward: Reward, snack: Snack) -> None:
    lesson = LESSONS[world.facts["lesson"]]
    child.attrs["lesson_text"] = lesson
    world.say(
        f"{child.id} sat down on the bench again, this time with {reward.label} tucked close and {snack.phrase} finally opened."
    )
    world.say(
        f"{child.pronoun().capitalize()} watched people hurrying and waiting together and understood something new: {lesson}"
    )
    world.say(
        f"When the train rolled in at last, the station still sounded busy, but it no longer felt so big. "
        f"{child.id} climbed aboard carrying a smaller fear and a steadier heart."
    )


def tell(
    problem: Problem,
    action: Action,
    reward: Reward,
    snack: Snack,
    wordgame: WordGame,
    child_name: str = "Mina",
    child_type: str = "girl",
    companion_type: str = "grandfather",
    lesson_key: str = "notice",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", label=child_name))
    companion = world.add(Entity(id="Companion", kind="character", type=companion_type, role="companion", label="the companion"))
    station = world.add(Entity(id="station", kind="thing", type="station", label="the station"))
    owner = world.add(
        Entity(
            id="owner",
            kind="character",
            type=problem.owner_type,
            role="owner",
            label=problem.owner_phrase,
            phrase=problem.owner_phrase,
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="lost_item",
            label=problem.phrase,
            phrase=problem.phrase,
            tags=set(problem.tags),
        )
    )

    world.facts.update(
        child=child,
        companion=companion,
        station=station,
        owner=owner,
        item=item,
        problem=problem,
        action=action,
        reward=reward,
        snack=snack,
        wordgame=wordgame,
        lesson=lesson_key,
    )

    introduce(world, child, companion, wordgame, snack)
    want_to_earn(world, child, reward)

    world.para()
    notice_problem(world, child, problem)
    inner_monologue(world, child, problem, action, snack)

    world.para()
    do_help(world, child, companion, problem, action)
    thanks_and_reward(world, child, companion, reward)

    world.para()
    closing(world, child, companion, reward, snack)
    return world


PROBLEMS = {
    "ticket": Problem(
        id="ticket",
        label="dropped ticket",
        phrase="a paper ticket",
        intro="Near the bench, a paper ticket slipped from an old man's coat pocket and skated across the floor.",
        owner_phrase="the old man",
        owner_type="man",
        location="near the bench",
        direct_ok=True,
        adult_ok=True,
        edge_risk=False,
        tags={"ticket", "train_station"},
    ),
    "scarf": Problem(
        id="scarf",
        label="blown scarf",
        phrase="a red scarf",
        intro="A gust from an arriving train tugged a red scarf out of a woman's hand and sent it fluttering toward the yellow line.",
        owner_phrase="the woman",
        owner_type="woman",
        location="near the yellow line",
        direct_ok=False,
        adult_ok=True,
        edge_risk=True,
        tags={"scarf", "safety", "train_station"},
    ),
    "map": Problem(
        id="map",
        label="folded map spill",
        phrase="a folded station map",
        intro="At the timetable board, a folded station map slid from a traveler's bag and landed by a puddle of melted rainwater.",
        owner_phrase="the traveler",
        owner_type="woman",
        location="by the timetable board",
        direct_ok=True,
        adult_ok=True,
        edge_risk=False,
        tags={"map", "train_station"},
    ),
}

ACTIONS = {
    "hand_back": Action(
        id="hand_back",
        label="pick it up and hand it back",
        sense=3,
        mode="direct",
        text="She picked it up and hurried it back before anyone's shoes could step on it.",
        qa_text="picked it up and handed it back",
        tags={"kindness", "help"},
    ),
    "call_worker": Action(
        id="call_worker",
        label="call a station worker",
        sense=3,
        mode="adult",
        text="She called, clear and quick, for the station worker standing nearby.",
        qa_text="called a station worker for help",
        tags={"safety", "help"},
    ),
    "point_and_hold": Action(
        id="point_and keep the place clear",
        sense=2,
        mode="adult",
        text="She pointed right away and told the nearest grown-up where to look.",
        qa_text="pointed it out to a nearby grown-up",
        tags={"kindness", "help"},
    ),
    "dash_alone": Action(
        id="dash_alone",
        label="dash after it alone",
        sense=1,
        mode="direct",
        text="She dashed after it without thinking.",
        qa_text="dashed after it alone",
        fail_text="That would be too risky.",
        tags={"unsafe"},
    ),
}

REWARDS = {
    "stamp": Reward(
        id="stamp",
        label="a little blue helper stamp",
        give_text="pressed a little blue helper stamp onto the back of her hand and told her",
        tags={"reward"},
    ),
    "sticker": Reward(
        id="sticker",
        label="a silver train sticker",
        give_text="peeled a silver train sticker from a sheet in the bag and whispered that",
        tags={"reward"},
    ),
    "window_seat": Reward(
        id="window_seat",
        label="the window seat",
        give_text="promised her the window seat and said",
        tags={"reward"},
    ),
}

SNACKS = {
    "liver_sandwich": Snack(
        id="liver_sandwich",
        phrase="a liver sandwich cut into neat squares",
        hand_busy=True,
        tags={"liver", "snack"},
    ),
    "pear": Snack(
        id="pear",
        phrase="a small pear wrapped in a napkin",
        hand_busy=False,
        tags={"snack"},
    ),
    "bun": Snack(
        id="bun",
        phrase="a soft raisin bun from the station bakery",
        hand_busy=False,
        tags={"snack"},
    ),
}

WORDGAMES = {
    "group_gerund": WordGame(
        id="group_gerund",
        label="group-gerund",
        intro="a silly notebook game called group-gerund",
        sample='"waiting, listening, wondering" in a neat row',
        tags={"group-gerund", "words"},
    ),
    "platform_list": WordGame(
        id="platform_list",
        label="platform list",
        intro="a page of travel words",
        sample='"rolling, ringing, rushing" under the station clock',
        tags={"words"},
    ),
    "quiet_count": WordGame(
        id="quiet_count",
        label="quiet count",
        intro="a quiet counting game with words instead of numbers",
        sample='"standing, blinking, breathing" beside a tiny doodled train',
        tags={"words"},
    ),
}

LESSONS = {
    "notice": "kindness often begins with noticing",
    "ask": "being careful is part of being brave",
    "small": "small help can still matter very much",
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Owen", "Noah", "Eli", "Sam", "Ben", "Theo"]


@dataclass
class StoryParams:
    problem: str
    action: str
    reward: str
    snack: str
    wordgame: str
    child_name: str
    child_type: str
    companion_type: str
    lesson: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ticket": [
        (
            "What is a train ticket for?",
            "A train ticket shows that you are allowed to ride the train. People keep it safe so they can show it when they need to."
        )
    ],
    "map": [
        (
            "What is a station map?",
            "A station map shows where platforms, doors, and signs are. It helps travelers find the right way."
        )
    ],
    "safety": [
        (
            "Why should children stay behind the yellow line at a train station?",
            "The yellow line marks a safer place to stand back from the tracks. Trains are big and fast, so children should let grown-ups and workers handle anything near the edge."
        )
    ],
    "kindness": [
        (
            "How can a child help safely in a busy place?",
            "A child can notice a problem, speak clearly, and choose a safe kind of help. Sometimes helping means using your own hands, and sometimes it means getting the right grown-up."
        )
    ],
    "group-gerund": [
        (
            "What is a gerund?",
            "A gerund is a word ending in -ing that acts like a thing or idea, such as waiting or listening. In a game, a child might gather several together as a funny little group-gerund list."
        )
    ],
    "liver": [
        (
            "What is liver in food?",
            "Liver is a kind of food some families eat in sandwiches or spreads. Different families like different train snacks."
        )
    ],
    "train_station": [
        (
            "What happens in a train station?",
            "People wait, listen for announcements, and find the right platform for their train. It can feel busy, so calm eyes and careful choices matter."
        )
    ],
}
KNOWLEDGE_ORDER = ["train_station", "ticket", "map", "safety", "kindness", "group-gerund", "liver"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    problem = world.facts["problem"]
    reward = world.facts["reward"]
    snack = world.facts["snack"]
    wordgame = world.facts["wordgame"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old set in a train station that includes the words "earn", "{wordgame.label}", and "liver".',
        f"Tell a gentle story where {child.id} notices {problem.phrase} in a busy station, has an inner monologue about helping, and earns {reward.label}.",
        f"Write a simple waiting-for-the-train story with a small problem, a careful choice, a clear lesson learned, and a snack like {snack.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    companion = world.facts["companion"]
    problem = world.facts["problem"]
    action = world.facts["action"]
    reward = world.facts["reward"]
    snack = world.facts["snack"]
    owner = world.facts["owner"]
    lesson = child.attrs.get("lesson_text", LESSONS[world.facts["lesson"]])
    outcome = world.facts.get("outcome", predict_outcome(problem, action))
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child waiting in a train station with {child.pronoun('possessive')} {companion.label_word}. While they waited, {child.pronoun()} noticed another traveler needed help."
        ),
        (
            "What was the child doing at the start?",
            f"{child.id} was waiting for the train, playing a word game, and thinking about earning {reward.label}. {child.pronoun().capitalize()} also had {snack.phrase} in the bag for the ride."
        ),
        (
            "What problem did the child notice?",
            f"{child.id} saw that {owner.label} had lost {problem.phrase}. That changed the station from a place of waiting into a moment when someone needed help."
        ),
        (
            "What was the child's inner monologue about?",
            f"{child.id} told {child.pronoun('object')}self that helping should be careful, not showy. The thought mattered because {child.pronoun()} wanted to do something kind in the right way."
        ),
    ]
    if outcome == "asked_adult":
        qa.append(
            (
                "How did the child help safely?",
                f"{child.id} did not rush in alone. {child.pronoun().capitalize()} {action.qa_text}, because the problem was safer for a grown-up or station worker to handle."
            )
        )
    else:
        qa.append(
            (
                "How did the child solve the problem?",
                f"{child.id} {action.qa_text}. It worked because the lost thing was in a safe place to reach, so a small direct action was enough."
            )
        )
    qa.append(
        (
            "What did the child earn, and why?",
            f"{child.id} earned {reward.label} after helping. The reward came because {child.pronoun()} noticed another person's trouble and chose a sensible kind of help."
        )
    )
    qa.append(
        (
            "What lesson did the child learn?",
            f"{child.id} learned that {lesson}. By the end, helping did not mean doing the biggest thing; it meant doing the right thing."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"kindness"}
    problem = world.facts["problem"]
    action = world.facts["action"]
    snack = world.facts["snack"]
    wordgame = world.facts["wordgame"]
    tags |= set(problem.tags)
    tags |= set(action.tags)
    tags |= set(snack.tags)
    tags |= set(wordgame.tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        problem="ticket",
        action="hand_back",
        reward="stamp",
        snack="liver_sandwich",
        wordgame="group_gerund",
        child_name="Mina",
        child_type="girl",
        companion_type="grandfather",
        lesson="small",
    ),
    StoryParams(
        problem="scarf",
        action="call_worker",
        reward="window_seat",
        snack="pear",
        wordgame="platform_list",
        child_name="Owen",
        child_type="boy",
        companion_type="mother",
        lesson="ask",
    ),
    StoryParams(
        problem="map",
        action="hand_back",
        reward="sticker",
        snack="bun",
        wordgame="quiet_count",
        child_name="Lila",
        child_type="girl",
        companion_type="father",
        lesson="notice",
    ),
]


ASP_RULES = r"""
direct_possible(ticket).
direct_possible(map).

adult_possible(ticket).
adult_possible(map).
adult_possible(scarf).

edge_risk(scarf).

sensible(A) :- action(A), sense(A,S), sense_min(M), S >= M.

fits(P,A) :- problem(P), action_mode(A,direct), direct_possible(P), not edge_risk(P), sensible(A).
fits(P,A) :- problem(P), action_mode(A,adult), adult_possible(P), sensible(A).

outcome(P,A,direct_help) :- fits(P,A), action_mode(A,direct).
outcome(P,A,asked_adult) :- fits(P,A), action_mode(A,adult).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, action.sense))
        lines.append(asp.fact("action_mode", aid, action.mode))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show fits/2."))
    return sorted(set(asp.atoms(model, "fits")))


def asp_outcome(problem_id: str, action_id: str) -> str:
    import asp

    extra = "\n".join([asp.fact("chosen_problem", problem_id), asp.fact("chosen_action", action_id)])
    program = asp_program(
        extra + "\nchosen_outcome(O) :- outcome(" + problem_id + "," + action_id + ",O).",
        "#show chosen_outcome/1.",
    )
    model = asp.one_model(program)
    atoms = asp.atoms(model, "chosen_outcome")
    return atoms[0][0] if atoms else "stuck"


def outcome_of(params: StoryParams) -> str:
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem '{params.problem}'.)")
    if params.action not in ACTIONS:
        raise StoryError(f"(Unknown action '{params.action}'.)")
    return predict_outcome(PROBLEMS[params.problem], ACTIONS[params.action])


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        py = outcome_of(params)
        asp_val = asp_outcome(params.problem, params.action)
        if py != asp_val:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: ASP outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child at a train station notices a small problem and helps in a sensible way."
    )
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--action", choices=sorted(ACTIONS))
    ap.add_argument("--reward", choices=sorted(REWARDS))
    ap.add_argument("--snack", choices=sorted(SNACKS))
    ap.add_argument("--wordgame", choices=sorted(WORDGAMES))
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--lesson", choices=sorted(LESSONS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (problem, action) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.action:
        problem = PROBLEMS[args.problem]
        action = ACTIONS[args.action]
        if not action_fits(problem, action):
            raise StoryError(explain_rejection(problem, action))
    if args.action and ACTIONS[args.action].sense < SENSE_MIN:
        problem = PROBLEMS[args.problem] if args.problem else next(iter(PROBLEMS.values()))
        raise StoryError(explain_rejection(problem, ACTIONS[args.action]))

    combos = [
        combo for combo in valid_combos()
        if (args.problem is None or combo[0] == args.problem)
        and (args.action is None or combo[1] == args.action)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    problem_id, action_id = rng.choice(sorted(combos))
    reward_id = args.reward or rng.choice(sorted(REWARDS))
    snack_id = args.snack or rng.choice(sorted(SNACKS))
    wordgame_id = args.wordgame or rng.choice(sorted(WORDGAMES))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    companion_type = args.companion or rng.choice(["mother", "father", "grandmother", "grandfather"])
    lesson_key = args.lesson or rng.choice(sorted(LESSONS))
    child_name = rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)

    return StoryParams(
        problem=problem_id,
        action=action_id,
        reward=reward_id,
        snack=snack_id,
        wordgame=wordgame_id,
        child_name=child_name,
        child_type=child_type,
        companion_type=companion_type,
        lesson=lesson_key,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        problem = PROBLEMS[params.problem]
        action = ACTIONS[params.action]
        reward = REWARDS[params.reward]
        snack = SNACKS[params.snack]
        wordgame = WORDGAMES[params.wordgame]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err})") from None

    if not action_fits(problem, action):
        raise StoryError(explain_rejection(problem, action))
    if params.lesson not in LESSONS:
        raise StoryError(f"(Unknown lesson '{params.lesson}'.)")
    if params.child_type not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child type '{params.child_type}'.)")
    if params.companion_type not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError(f"(Unknown companion type '{params.companion_type}'.)")

    world = tell(
        problem=problem,
        action=action,
        reward=reward,
        snack=snack,
        wordgame=wordgame,
        child_name=params.child_name,
        child_type=params.child_type,
        companion_type=params.companion_type,
        lesson_key=params.lesson,
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
        print(asp_program("", "#show fits/2.\n#show outcome/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (problem, action) pairs:\n")
        for problem_id, action_id in combos:
            print(f"  {problem_id:8} {action_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.problem} with {p.action} ({p.reward})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
