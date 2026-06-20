#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fat_discuss_cliff_lookout_problem_solving_detective.py
=================================================================================

A standalone story world for a tiny detective-style tale at a cliff lookout.

Premise
-------
Two children visit a cliff lookout with a grown-up. A small problem appears:
something is missing or out of place. Instead of guessing wildly, the children
pause, look for clues, and discuss what each clue means. Their calm detective
work leads them to the right cause and a sensible fix.

This world keeps its coverage narrow on purpose. Every generated sample has:

* a cliff lookout setting,
* the words "fat" and "discuss" in the story,
* a clear detective-style mystery,
* a problem-solving middle built from world state,
* a concrete ending image proving the problem was solved.

Reasonableness constraint
-------------------------
Not every culprit can cause every problem, and not every recovery method makes
sense for every culprit. The world refuses impossible or flimsy combinations.

Run it
------
    python storyworlds/worlds/gpt-5.4/fat_discuss_cliff_lookout_problem_solving_detective.py
    python storyworlds/worlds/gpt-5.4/fat_discuss_cliff_lookout_problem_solving_detective.py --problem sandwich --culprit gull
    python storyworlds/worlds/gpt-5.4/fat_discuss_cliff_lookout_problem_solving_detective.py --problem notebook --culprit gull
    python storyworlds/worlds/gpt-5.4/fat_discuss_cliff_lookout_problem_solving_detective.py --all --qa
    python storyworlds/worlds/gpt-5.4/fat_discuss_cliff_lookout_problem_solving_detective.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    edible: bool = False
    can_blow: bool = False
    can_snatch: bool = False
    can_nibble: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "ranger_woman"}
        male = {"boy", "father", "man", "ranger_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "ranger_woman": "ranger",
            "ranger_man": "ranger",
        }.get(self.type, self.type)


@dataclass
class Problem:
    id: str
    missing_label: str
    phrase: str
    place_line: str
    portable: bool = True
    edible: bool = False
    windy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    article: str
    clue: str
    trail: str
    move_text: str
    can_take_food: bool = False
    can_take_light_object: bool = False
    can_take_shiny_object: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    works_for: set[str]
    find_text: str
    solve_text: str
    qa_text: str
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
        new = World()
        new.entities = copy.deepcopy(self.entities)
        new.fired = set(self.fired)
        new.paragraphs = [[]]
        new.facts = copy.deepcopy(self.facts)
        return new


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_stirs_worry(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return out
    for eid in ("detective1", "detective2"):
        kid = world.get(eid)
        sig = ("worry", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["worry"] += 1
    return out


def _r_discuss_cools_panic(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("discussed") and ("discuss",) not in world.fired:
        world.fired.add(("discuss",))
        for eid in ("detective1", "detective2"):
            kid = world.get(eid)
            if kid.memes["worry"] >= THRESHOLD:
                kid.memes["worry"] = max(0.0, kid.memes["worry"] - 1.0)
            kid.memes["focus"] += 1
        out.append("__discussion__")
    return out


def _r_found_brings_relief(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("detective1", "detective2"):
        kid = world.get(eid)
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
        kid.memes["worry"] = 0.0
    out.append("__solved__")
    return out


CAUSAL_RULES = [
    Rule("missing_stirs_worry", "emotional", _r_missing_stirs_worry),
    Rule("discuss_cools_panic", "social", _r_discuss_cools_panic),
    Rule("found_brings_relief", "emotional", _r_found_brings_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def culprit_can_cause(problem: Problem, culprit: Culprit) -> bool:
    if problem.edible:
        return culprit.can_take_food
    if problem.id == "scarf":
        return culprit.can_take_light_object
    if problem.id == "notebook":
        return culprit.can_take_shiny_object or culprit.can_take_light_object
    return False


def sensible_methods(problem: Problem, culprit: Culprit) -> list[Method]:
    return [
        m for m in METHODS.values()
        if m.sense >= SENSE_MIN and culprit.id in m.works_for and method_matches_problem(m, problem, culprit)
    ]


def method_matches_problem(method: Method, problem: Problem, culprit: Culprit) -> bool:
    if culprit.id == "wind":
        return method.id == "follow_flap"
    if culprit.id == "gull":
        return method.id in {"watch_bench", "ask_ranger"}
    if culprit.id == "goat":
        return method.id in {"follow_tracks", "ask_ranger"}
    return False


def best_method(problem: Problem, culprit: Culprit) -> Method:
    return max(sensible_methods(problem, culprit), key=lambda m: m.sense)


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for pid, p in PROBLEMS.items():
        for cid, c in CULPRITS.items():
            if culprit_can_cause(p, c) and sensible_methods(p, c):
                out.append((pid, cid))
    return out


def predict_solution(problem: Problem, culprit: Culprit, method: Method) -> dict:
    return {
        "possible": culprit_can_cause(problem, culprit),
        "method_ok": method in sensible_methods(problem, culprit),
        "clue": culprit.clue,
    }


def introduce(world: World, a: Entity, b: Entity, guide: Entity) -> None:
    world.say(
        f"{a.id} and {b.id} climbed the path to the cliff lookout with {guide.label_word}. "
        "The sea shone far below, and the rail at the edge made the place feel like a real lookout post."
    )
    world.say(
        f"{a.id} liked mysteries, and {b.id} liked careful noticing, so together they always felt like a pair of young detectives."
    )


def set_problem(world: World, a: Entity, b: Entity, problem: Problem) -> None:
    item = world.get("item")
    item.meters["missing"] += 1
    world.facts["problem_started"] = True
    propagate(world, narrate=False)
    world.say(problem.place_line)
    world.say(
        f'"My {problem.missing_label} is gone," {b.id} said. Right away the happy trip turned into a small cliff-top mystery.'
    )


def worry_beat(world: World, a: Entity, b: Entity) -> None:
    if a.memes["worry"] >= THRESHOLD or b.memes["worry"] >= THRESHOLD:
        world.say(
            f"{a.id} glanced over the stones, and {b.id} looked under the bench, but the missing thing was nowhere nearby."
        )


def discuss_clues(world: World, a: Entity, b: Entity, culprit: Culprit, problem: Problem) -> None:
    world.facts["discussed"] = True
    propagate(world, narrate=False)
    a.memes["logic"] += 1
    b.memes["logic"] += 1
    world.say(
        f'"Before we guess, let\'s discuss the clues," {a.id} whispered, using the most detective voice {a.pronoun()} could manage.'
    )
    world.say(
        f"Near the bench they found {culprit.clue}. That clue did not match every idea, so the children slowed down and thought carefully."
    )
    if culprit.id == "gull":
        world.say(
            f'{b.id} pointed to the sky. "A fat gull was hopping near us before," {b.pronoun()} said. '
            f'"A bird could grab food faster than the wind could."'
        )
    elif culprit.id == "wind":
        world.say(
            f'{b.id} held up a hand to the breeze. "The wind is still tugging at everything," {b.pronoun()} said. '
            f'"If the thing was light, the gust could have carried it."'
        )
    else:
        world.say(
            f'{b.id} knelt by the ground. "These marks look like little hoofprints," {b.pronoun()} said. '
            f'"A cliff goat could have trotted off with a snack."'
        )


def choose_method(world: World, a: Entity, b: Entity, guide: Entity, problem: Problem,
                  culprit: Culprit, method: Method) -> None:
    pred = predict_solution(problem, culprit, method)
    world.facts["predicted_possible"] = pred["possible"]
    world.facts["predicted_method_ok"] = pred["method_ok"]
    world.say(
        f'{guide.label_word.capitalize()} listened and nodded. "Good detectives use clues before they act," {guide.pronoun()} said.'
    )
    if method.id == "watch_bench":
        world.say(
            f'"Then let\'s stay still and watch," said {a.id}. "If the thief wants another bite, it may come back."'
        )
    elif method.id == "follow_flap":
        world.say(
            f'"Then we should follow what is fluttering, not run everywhere," said {a.id}. "The breeze will show us the path."'
        )
    elif method.id == "follow_tracks":
        world.say(
            f'"Then we should follow the tracks slowly," said {a.id}. "We can solve this without scaring anything."'
        )
    else:
        world.say(
            f'"Then let\'s ask the ranger what usually happens here," said {a.id}. "A local detective knows local tricks."'
        )


def solve(world: World, a: Entity, b: Entity, guide: Entity, problem: Problem,
          culprit: Culprit, method: Method) -> None:
    item = world.get("item")
    culprit_ent = world.get("culprit")
    culprit_ent.meters["revealed"] += 1
    item.meters["found"] += 1
    world.facts["solved"] = True
    if culprit.id == "gull":
        culprit_ent.meters["perched"] += 1
    elif culprit.id == "wind":
        culprit_ent.meters["gusting"] += 1
    else:
        culprit_ent.meters["nibbling"] += 1
    propagate(world, narrate=False)
    world.say(method.find_text.format(problem=problem.missing_label, culprit=culprit.label))
    world.say(method.solve_text.format(problem=problem.missing_label, culprit=culprit.label))
    if culprit.id == "gull":
        world.say(
            f'The children laughed softly when they saw the thief at last: {culprit.article} {culprit.label} with crumbs on its beak, looking much too pleased with itself.'
        )
    elif culprit.id == "wind":
        world.say(
            "Nothing had been stolen at all. The gusts had only pushed the missing thing farther along the rail than anyone first guessed."
        )
    else:
        world.say(
            f"Beyond a patch of grass, they spotted {culprit.article} {culprit.label} chewing busily beside the path."
        )


def resolution(world: World, a: Entity, b: Entity, guide: Entity, problem: Problem,
               culprit: Culprit) -> None:
    for eid in ("detective1", "detective2"):
        world.get(eid).memes["joy"] += 1
    world.say(
        f'"Case closed," said {b.id}, hugging the recovered {problem.missing_label} to {b.pronoun("object")}self.'
    )
    if culprit.id == "gull":
        world.say(
            f'{guide.label_word.capitalize()} moved the food box farther from the edge and said, "Next time we keep our snacks shut tight when seabirds are near."'
        )
    elif culprit.id == "wind":
        world.say(
            f'{guide.label_word.capitalize()} tucked loose things into a bag and said, "At a cliff lookout, the wind is part of every plan."'
        )
    else:
        world.say(
            f'{guide.label_word.capitalize()} smiled and said, "If goats are around, we eat first and leave no tasty things on the bench."'
        )
    world.say(
        "Soon the lookout did not feel like a place of worry anymore. It felt like a bright detective office above the sea."
    )


def tell(problem: Problem, culprit: Culprit, method: Method,
         name1: str = "Mina", gender1: str = "girl",
         name2: str = "Leo", gender2: str = "boy",
         guide_type: str = "ranger_woman",
         trait1: str = "bold", trait2: str = "careful") -> World:
    world = World()
    a = world.add(Entity(id=name1, kind="character", type=gender1, role="detective1", traits=[trait1]))
    b = world.add(Entity(id=name2, kind="character", type=gender2, role="detective2", traits=[trait2]))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, role="guide", label="the ranger"))
    item = world.add(Entity(
        id="item", type="thing", label=problem.missing_label,
        portable=problem.portable, edible=problem.edible
    ))
    culprit_ent = world.add(Entity(
        id="culprit", type="animal" if culprit.id != "wind" else "weather",
        label=culprit.label,
        can_blow=(culprit.id == "wind"),
        can_snatch=(culprit.id == "gull"),
        can_nibble=(culprit.id == "goat"),
    ))

    introduce(world, a, b, guide)
    set_problem(world, a, b, problem)
    worry_beat(world, a, b)

    world.para()
    discuss_clues(world, a, b, culprit, problem)
    choose_method(world, a, b, guide, problem, culprit, method)

    world.para()
    solve(world, a, b, guide, problem, culprit, method)
    resolution(world, a, b, guide, problem, culprit)

    world.facts.update(
        detective1=a,
        detective2=b,
        guide=guide,
        item=item,
        problem=problem,
        culprit_cfg=culprit,
        culprit=culprit_ent,
        method=method,
        recovered=item.meters["found"] >= THRESHOLD,
        clue=culprit.clue,
    )
    return world


PROBLEMS = {
    "sandwich": Problem(
        "sandwich", "sandwich", "a warm cheese sandwich",
        "They set down their things on a lookout bench for just a moment while the waves boomed below.",
        portable=True, edible=True, tags={"food", "sandwich"},
    ),
    "scarf": Problem(
        "scarf", "scarf", "a soft red scarf",
        "A scarf had been folded on the bench while they looked out across the water.",
        portable=True, windy=True, tags={"wind", "clothes"},
    ),
    "notebook": Problem(
        "notebook", "notebook", "a little shiny detective notebook",
        "Their detective notebook had been lying beside the map of the path and a pencil stub.",
        portable=True, windy=True, tags={"notebook", "clue"},
    ),
}

CULPRITS = {
    "gull": Culprit(
        "gull", "gull", "a", "a white feather and greasy crumbs",
        "toward a high rail post", "snatched it and hopped away",
        can_take_food=True, can_take_light_object=False, can_take_shiny_object=False,
        tags={"gull", "bird"},
    ),
    "wind": Culprit(
        "wind", "wind", "the", "scraped marks and a fluttering edge of fabric",
        "along the rail toward a thorn bush", "blew it farther down the path",
        can_take_food=False, can_take_light_object=True, can_take_shiny_object=True,
        tags={"wind", "weather"},
    ),
    "goat": Culprit(
        "goat", "cliff goat", "a", "small hoofprints and a torn bit of wrapper",
        "toward a grassy patch by the rocks", "carried it off to nibble",
        can_take_food=True, can_take_light_object=False, can_take_shiny_object=False,
        tags={"goat", "animal"},
    ),
}

METHODS = {
    "watch_bench": Method(
        "watch_bench", "wait and watch", 3, {"gull"},
        "The children crouched behind the bench. In less than a minute they saw the {culprit} swoop back toward the crumbs.",
        "Guide walked slowly around the post, shooed the bird away, and picked up the {problem} where it had been dropped behind the rail.",
        "They waited quietly for the gull to return, then recovered the missing thing from behind the rail.",
        tags={"patience", "gull"},
    ),
    "follow_flap": Method(
        "follow_flap", "follow the flutter", 3, {"wind"},
        "Instead of searching everywhere, they watched what fluttered. A corner of the missing {problem} twitched from a thorn bush beside the path.",
        "Guide held the bush still while the children gently pulled the {problem} free.",
        "They followed the way the wind tugged at loose things and found it caught in a thorn bush.",
        tags={"wind", "careful"},
    ),
    "follow_tracks": Method(
        "follow_tracks", "follow the tracks", 3, {"goat"},
        "They followed the tiny hoofprints to a grassy patch near the rocks, where the smell of lunch still hung in the air.",
        "There they found the missing {problem}, a little squashed but still clearly the thing they had lost, and the goat trotted off when the ranger clapped once.",
        "They followed hoofprints to a grassy patch and found the missing thing there.",
        tags={"tracks", "animal"},
    ),
    "ask_ranger": Method(
        "ask_ranger", "ask the ranger", 2, {"gull", "goat"},
        "The ranger listened to the clues and led them to the spot where that kind of trouble usually ended.",
        "Because the children had noticed the right clues first, the ranger took them straight to the missing {problem}.",
        "They asked the ranger after gathering clues, and the ranger guided them to the right place.",
        tags={"ranger", "help"},
    ),
    "run_randomly": Method(
        "run_randomly", "run in circles", 1, {"gull", "wind", "goat"},
        "They raced around without a plan.",
        "That only made them tired, and it would not make a good detective story.",
        "They ran around without using clues.",
        tags={"bad_idea"},
    ),
}


GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Zoe", "Ivy", "Tess", "Ruby"]
BOY_NAMES = ["Leo", "Ben", "Owen", "Sam", "Max", "Theo", "Eli", "Finn"]
TRAITS = ["bold", "careful", "curious", "steady", "patient", "sharp-eyed"]


@dataclass
class StoryParams:
    problem: str
    culprit: str
    method: str
    name1: str
    gender1: str
    name2: str
    gender2: str
    guide: str
    trait1: str
    trait2: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "gull": [("Why do gulls steal food?",
              "Gulls are quick seabirds, and they learn that people sometimes leave food where they can grab it. They are especially bold near places overlooking the sea.")],
    "wind": [("Why is wind stronger at a cliff lookout?",
              "A cliff lookout is high and open, so the air can rush across it with very little in the way. That can make light things flap or blow away.")],
    "goat": [("Why might a goat take a snack?",
              "Goats explore with their mouths and noses, so they may nibble food if they find it. That is why people should keep snacks packed away.")],
    "tracks": [("What can tracks tell a detective?",
                "Tracks can show where someone or something went. They help a detective follow movement instead of guessing.")],
    "ranger": [("What does a ranger do at a lookout?",
                "A ranger watches over the place, helps visitors stay safe, and often knows the animals and weather there very well.")],
    "sandwich": [("Why would a sandwich attract animals?",
                  "A sandwich smells strong and is easy to carry in bites, so hungry animals may try to snatch it. Food should be kept packed away near wild animals.")],
    "notebook": [("Why can a notebook blow away?",
                  "A small notebook is light and has pages that catch the air. A strong gust can push it along or lift a corner until it flies.")],
    "wind_safe": [("What should you do with loose things on a windy cliff?",
                   "Keep them tucked in a bag or hold them tightly. Open, windy places can carry light objects away very fast.")],
}
KNOWLEDGE_ORDER = ["gull", "wind", "goat", "tracks", "ranger", "sandwich", "notebook", "wind_safe"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["problem"]
    c = f["culprit_cfg"]
    a = f["detective1"]
    b = f["detective2"]
    return [
        'Write a short detective story for a 3-to-5-year-old set at a cliff lookout that includes the words "fat" and "discuss".',
        f"Tell a gentle mystery where {a.id} and {b.id} stop to discuss clues after a {p.missing_label} goes missing at a cliff lookout.",
        f"Write a small problem-solving detective tale where the real cause is {c.label} and the ending shows the children solving the case calmly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["detective1"]
    b = f["detective2"]
    guide = f["guide"]
    problem = f["problem"]
    culprit = f["culprit_cfg"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        ("Who are the detectives in the story?",
         f"The young detectives are {a.id} and {b.id}. They are at the cliff lookout with the ranger when the mystery begins."),
        (f"What was the problem at the cliff lookout?",
         f"The problem was that the {problem.missing_label} went missing. That turned an ordinary lookout visit into a small detective case."),
        ("Why did they stop to discuss the clues?",
         f"They did not want to guess wildly and blame the wrong cause. Discussing the clue helped them choose a plan that fit what they had actually seen."),
        ("What clue helped solve the mystery?",
         f"The key clue was {culprit.clue}. That clue matched {culprit.label} better than the other ideas, so it pointed the children in the right direction."),
        ("How did they solve the case?",
         f"They used {method.label} instead of panicking. {method.qa_text}"),
    ]
    if f.get("recovered"):
        qa.append((
            f"How did the story end?",
            f"The children recovered the {problem.missing_label} and felt proud and relieved. The lookout ended up feeling bright and safe again because they solved the problem carefully."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["culprit_cfg"].tags) | set(f["problem"].tags) | set(f["method"].tags)
    if f["culprit_cfg"].id == "wind":
        tags.add("wind_safe")
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
        flags = [
            n for n, on in (
                ("portable", e.portable),
                ("edible", e.edible),
                ("can_blow", e.can_blow),
                ("can_snatch", e.can_snatch),
                ("can_nibble", e.can_nibble),
            ) if on
        ]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("sandwich", "gull", "watch_bench", "Mina", "girl", "Leo", "boy", "ranger_woman", "bold", "careful"),
    StoryParams("scarf", "wind", "follow_flap", "Ruby", "girl", "Finn", "boy", "ranger_man", "curious", "steady"),
    StoryParams("sandwich", "goat", "follow_tracks", "Ava", "girl", "Max", "boy", "ranger_woman", "patient", "sharp-eyed"),
    StoryParams("sandwich", "gull", "ask_ranger", "Nora", "girl", "Theo", "boy", "ranger_man", "steady", "curious"),
    StoryParams("notebook", "wind", "follow_flap", "Ivy", "girl", "Ben", "boy", "ranger_woman", "bold", "careful"),
]


def explain_rejection(problem: Problem, culprit: Culprit) -> str:
    if not culprit_can_cause(problem, culprit):
        if problem.edible:
            return (
                f"(No story: {culprit.label} is not a good cause for a missing {problem.missing_label}. "
                "This world only allows food-snatching culprits for missing food.)"
            )
        return (
            f"(No story: {culprit.label} is not a good cause for a missing {problem.missing_label}. "
            "Pick a culprit that could really move that object at a cliff lookout.)"
        )
    return "(No story: that combination does not fit this world.)"


def explain_method(problem: Problem, culprit: Culprit, method_id: str) -> str:
    m = METHODS[method_id]
    better = ", ".join(sorted(mm.id for mm in sensible_methods(problem, culprit)))
    return (
        f"(Refusing method '{method_id}': it is not a sensible way to solve a "
        f"{problem.missing_label} case caused by {culprit.label}. Try: {better}.)"
    )


ASP_RULES = r"""
can_cause(P, gull) :- edible(P).
can_cause(P, goat) :- edible(P).
can_cause(P, wind) :- windy(P).

sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
method_ok(P, C, M) :- can_cause(P, C), works_for(M, C), sensible(M), method_match(C, M).

valid(P, C) :- problem(P), culprit(C), can_cause(P, C), method_ok(P, C, _).

chosen_valid :- chosen_problem(P), chosen_culprit(C), valid(P, C).
chosen_method_ok :- chosen_problem(P), chosen_culprit(C), chosen_method(M), method_ok(P, C, M).

outcome(solved) :- chosen_valid, chosen_method_ok.
outcome(invalid) :- not chosen_valid.
outcome(bad_method) :- chosen_valid, not chosen_method_ok.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.edible:
            lines.append(asp.fact("edible", pid))
        if p.windy:
            lines.append(asp.fact("windy", pid))
    for cid in CULPRITS:
        lines.append(asp.fact("culprit", cid))
    for mid, m in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, m.sense))
        for c in sorted(m.works_for):
            lines.append(asp.fact("works_for", mid, c))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.extend([
        asp.fact("method_match", "gull", "watch_bench"),
        asp.fact("method_match", "gull", "ask_ranger"),
        asp.fact("method_match", "wind", "follow_flap"),
        asp.fact("method_match", "goat", "follow_tracks"),
        asp.fact("method_match", "goat", "ask_ranger"),
    ])
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_culprit", params.culprit),
        asp.fact("chosen_method", params.method),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if (params.problem, params.culprit) not in set(valid_combos()):
        return "invalid"
    if METHODS[params.method] not in sensible_methods(PROBLEMS[params.problem], CULPRITS[params.culprit]):
        return "bad_method"
    return "solved"


def asp_verify() -> int:
    rc = 0
    py, cl = set(valid_combos()), set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective story world: a cliff lookout mystery solved by discussing clues."
    )
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--guide", choices=["ranger_woman", "ranger_man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (problem, culprit) pairs from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.culprit:
        p = PROBLEMS[args.problem]
        c = CULPRITS[args.culprit]
        if not culprit_can_cause(p, c):
            raise StoryError(explain_rejection(p, c))
    chosen_pairs = [
        combo for combo in valid_combos()
        if (args.problem is None or combo[0] == args.problem)
        and (args.culprit is None or combo[1] == args.culprit)
    ]
    if not chosen_pairs:
        raise StoryError("(No valid combination matches the given options.)")

    problem_id, culprit_id = rng.choice(sorted(chosen_pairs))
    problem = PROBLEMS[problem_id]
    culprit = CULPRITS[culprit_id]

    allowed_methods = sensible_methods(problem, culprit)
    if args.method:
        if METHODS[args.method] not in allowed_methods:
            raise StoryError(explain_method(problem, culprit, args.method))
        method_id = args.method
    else:
        method_id = rng.choice(sorted(m.id for m in allowed_methods))

    gender1 = rng.choice(["girl", "boy"])
    gender2 = rng.choice(["girl", "boy"])
    name1 = pick_name(rng, gender1)
    name2 = pick_name(rng, gender2, avoid=name1)
    guide = args.guide or rng.choice(["ranger_woman", "ranger_man"])
    trait1 = rng.choice(TRAITS)
    trait2 = rng.choice([t for t in TRAITS if t != trait1] or TRAITS)

    return StoryParams(problem_id, culprit_id, method_id, name1, gender1, name2, gender2, guide, trait1, trait2)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PROBLEMS[params.problem],
        CULPRITS[params.culprit],
        METHODS[params.method],
        params.name1, params.gender1,
        params.name2, params.gender2,
        params.guide,
        params.trait1, params.trait2,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (problem, culprit) combos:\n")
        for p, c in combos:
            methods = ", ".join(sorted(m.id for m in sensible_methods(PROBLEMS[p], CULPRITS[c])))
            print(f"  {p:10} {c:6} [{methods}]")
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
            header = f"### {p.problem} / {p.culprit} / {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
