#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/knickerbockers_kindergarten_quest_conflict_bedtime_story.py
===========================================================================================

A standalone story world for a small bedtime tale set in kindergarten:
a child in knickerbockers goes on a gentle quest, meets a small conflict,
asks for help, and ends the day safely and warmly.

The domain is deliberately tiny and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate with an inline ASP twin
- three QA sets grounded in world state, not rendered English
- child-facing prose with a beginning, a turn, and a closing image

This world is meant to feel like a bedtime story: soft, concrete, calm, and
resolved, while still allowing a meaningful conflict beat.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/knickerbockers_kindergarten_quest_conflict_bedtime_story.py
    python storyworlds/worlds/gpt-5.4-mini/knickerbockers_kindergarten_quest_conflict_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/knickerbockers_kindergarten_quest_conflict_bedtime_story.py -n 5 --seed 777 --qa
    python storyworlds/worlds/gpt-5.4-mini/knickerbockers_kindergarten_quest_conflict_bedtime_story.py --verify
    python storyworlds/worlds/gpt-5.4-mini/knickerbockers_kindergarten_bedtime_story.py --json
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

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    quiet: str
    bedtime_detail: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Quest:
    id: str
    noun: str
    goal: str
    clue: str
    route: str
    reward: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Conflict:
    id: str
    noun: str
    cause: str
    worry: str
    calm_fix: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class ComfortItem:
    id: str
    noun: str
    phrase: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_tired(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["tired"] < THRESHOLD:
            continue
        sig = ("tired", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["sleepy"] += 1
        out.append("__sleepy__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["frustration"] < THRESHOLD:
        return out
    sig = ("conflict", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["conflict"] += 1
    out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("tired", "physical", _r_tired), Rule("conflict", "social", _r_conflict)]


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


def quest_at_risk(quest: Quest, conflict: Conflict) -> bool:
    return quest.id in {"button", "bell", "book"} and conflict.id in {"missing_button", "stuck_door", "lost_book"}


def compromise_available(quest: Quest, conflict: Conflict) -> bool:
    return quest.id == "button" and conflict.id == "missing_button"


def bedtime_safe(quest: Quest) -> bool:
    return quest.id in {"button", "bell", "book"}


def _do_conflict(world: World, quest: Quest, conflict: Conflict) -> None:
    child = world.get("child")
    child.meters["search"] += 1
    child.memes["frustration"] += 1
    propagate(world, narrate=False)


def setup(world: World, child: Entity, parent: Entity, setting: Setting, quest: Quest) -> None:
    child.memes["hope"] += 1
    world.say(
        f"In kindergarten after the bright afternoon games, {child.id} still wore {child.pronoun('possessive')} knickerbockers, "
        f"and the room grew quiet with the soft kind of hush that comes before bedtime. "
        f"Their classroom had {setting.quiet}, {setting.bedtime_detail}."
    )
    world.say(
        f"{child.id} had a little quest: {quest.goal}. {quest.clue}"
    )


def start_conflict(world: World, child: Entity, conflict: Conflict, quest: Quest) -> None:
    child.memes["worry"] += 1
    world.say(
        f"But then the trouble began. {conflict.cause} {conflict.worry}."
    )
    world.say(
        f'{child.id} frowned and looked around. "I need to find {quest.noun}," {child.pronoun()} whispered.'
    )


def search(world: World, child: Entity, quest: Quest, conflict: Conflict) -> None:
    world.say(
        f"{child.id} searched the little classroom cubbies, then the sleepy reading rug, and then the tidy shelf by the paints. "
        f"The quest took {child.pronoun('possessive')} small feet from one quiet corner to the next."
    )
    child.memes["determination"] += 1


def ask_for_help(world: World, child: Entity, parent: Entity, conflict: Conflict) -> None:
    world.say(
        f"At last {child.id} walked to {parent.label_word}. "
        f'"I cannot finish my quest alone," {child.pronoun()} said softly.'
    )
    child.memes["trust"] += 1
    parent.memes["care"] += 1


def resolve_conflict(world: World, child: Entity, parent: Entity, quest: Quest, conflict: Conflict, comfort: ComfortItem) -> None:
    child.memes["frustration"] = 0.0
    child.memes["joy"] += 1
    parent.memes["joy"] += 1
    world.say(
        f"{parent.label_word.capitalize()} smiled and helped by {conflict.calm_fix}. "
        f"Together they found {quest.reward}, and {child.id}'s worry loosened like a ribbon untied."
    )
    world.say(
        f"Then {child.id} held {comfort.phrase} close, and the classroom felt safe again."
    )
    world.say(
        f"The quest was done, and bedtime was peaceful."
    )


def unhappy_end(world: World, child: Entity, parent: Entity, quest: Quest, conflict: Conflict) -> None:
    child.memes["frustration"] += 1
    world.say(
        f"{parent.label_word.capitalize()} helped as best {parent.pronoun()} could, but the missing piece was still not found. "
        f"{child.id} curled up, tired and sad, while the kindergarten lights glowed gently overhead."
    )
    world.say(
        f"Even so, {child.id} knew {parent.label_word} had stayed close, and that made the night feel less lonely."
    )


def tell(setting: Setting, quest: Quest, conflict: Conflict, comfort: ComfortItem,
         child_name: str = "Milo", child_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", role="parent"))
    world.add(Entity(id="room", type="room", label=setting.place))
    world.add(Entity(id="quest", type="thing", label=quest.noun))
    world.add(Entity(id="conflict", type="thing", label=conflict.noun))
    world.add(Entity(id="comfort", type="thing", label=comfort.noun))
    child.memes["tired"] = float(delay)
    world.facts["setting"] = setting
    world.facts["quest"] = quest
    world.facts["conflict"] = conflict
    world.facts["comfort"] = comfort
    world.facts["parent"] = parent
    world.facts["child"] = child

    setup(world, child, parent, setting, quest)
    world.para()
    start_conflict(world, child, conflict, quest)
    search(world, child, quest, conflict)
    ask_for_help(world, child, parent, conflict)

    world.para()
    if compromise_available(quest, conflict):
        resolve_conflict(world, child, parent, quest, conflict, comfort)
        outcome = "resolved"
    else:
        unhappy_end(world, child, parent, quest, conflict)
        outcome = "unresolved"

    world.facts["outcome"] = outcome
    world.facts["bedtime_done"] = True
    return world


SETTINGS = {
    "kindergarten": Setting(
        id="kindergarten",
        place="kindergarten",
        quiet="a tiny library nook, a row of low cubbies, and a moon-shaped lamp",
        bedtime_detail="the windows had gone dark blue",
        tags={"kindergarten", "bedtime"},
    ),
}

QUESTS = {
    "button": Quest(
        id="button",
        noun="the shiny button from the art apron",
        goal="find the shiny button before the bedtime basket was closed",
        clue="It was small and round, and it had rolled somewhere soft.",
        route="search the cubbies and the rug",
        reward="the shiny button",
        tags={"quest", "button"},
    ),
    "bell": Quest(
        id="bell",
        noun="the little silver bell",
        goal="find the little silver bell before story time ended",
        clue="It had a bright sound and liked to hide near quiet things.",
        route="listen close and follow the sound",
        reward="the little silver bell",
        tags={"quest", "bell"},
    ),
    "book": Quest(
        id="book",
        noun="the bedtime picture book",
        goal="find the bedtime picture book before the shelf lights dimmed",
        clue="Its cover showed a star and a pillow.",
        route="look by the reading rug",
        reward="the bedtime picture book",
        tags={"quest", "book"},
    ),
}

CONFLICTS = {
    "missing_button": Conflict(
        id="missing_button",
        noun="missing button",
        cause="The apron button had rolled away under the cubby bench",
        worry="and now the apron could not be finished",
        calm_fix="checking under the bench and turning the basket over carefully",
        tags={"conflict", "button"},
    ),
    "lost_book": Conflict(
        id="lost_book",
        noun="lost book",
        cause="The picture book was gone from the shelf",
        worry="and the bedtime shelf looked too empty",
        calm_fix="sliding the rug back and peeking behind the pillow pile",
        tags={"conflict", "book"},
    ),
    "stuck_door": Conflict(
        id="stuck_door",
        noun="stuck door",
        cause="The tiny reading corner door had stuck shut",
        worry="and the quiet nook would not open",
        calm_fix="pressing the latch and giving the door a gentle tug",
        tags={"conflict", "door"},
    ),
}

COMFORTS = {
    "teddy": ComfortItem(
        id="teddy",
        noun="teddy bear",
        phrase="the floppy teddy bear",
        tags={"comfort"},
    ),
    "owl": ComfortItem(
        id="owl",
        noun="plush owl",
        phrase="the soft plush owl",
        tags={"comfort"},
    ),
    "blanket": ComfortItem(
        id="blanket",
        noun="blanket",
        phrase="the little bedtime blanket",
        tags={"comfort"},
    ),
}

GIRL_NAMES = ["Maya", "Luna", "Nora", "Ivy", "Ada", "Pia"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Leo", "Eli", "Sam"]
TRAITS = ["curious", "gentle", "brave", "careful", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for quest_id, quest in QUESTS.items():
            for conflict_id, conflict in CONFLICTS.items():
                if quest_at_risk(quest, conflict) and compromise_available(quest, conflict):
                    combos.append((setting_id, quest_id, conflict_id))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    quest: str
    conflict: str
    comfort: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


KNOWLEDGE = {
    "knickerbockers": [(
        "What are knickerbockers?",
        "Knickerbockers are short, loose pants that end below the knee. They are a kind of clothes people can wear to look neat and playful."
    )],
    "kindergarten": [(
        "What is kindergarten?",
        "Kindergarten is a school place for young children where they learn, play, rest, and listen to stories."
    )],
    "quest": [(
        "What is a quest?",
        "A quest is a mission or search to find something important. It often means looking carefully and not giving up."
    )],
    "conflict": [(
        "What is a conflict in a story?",
        "A conflict is the problem or trouble that makes the character worry or try harder. It gives the story a turn before the ending."
    )],
    "bedtime": [(
        "Why do bedtime stories feel calm?",
        "Bedtime stories feel calm because they slow the day down, use gentle words, and usually end with safety and rest."
    )],
    "button": [(
        "What does a button do?",
        "A button helps hold clothes together. If a button falls off, clothes can feel unfinished until it is found or fixed."
    )],
    "bell": [(
        "What does a bell sound like?",
        "A bell usually makes a bright, ringing sound that can be heard from far away."
    )],
    "book": [(
        "What is a picture book?",
        "A picture book is a book with drawings and words. It is nice for young children because the pictures help tell the story."
    )],
    "teddy": [(
        "Why do children like teddy bears?",
        "Teddy bears feel soft and friendly. Many children like them because they are comforting to hug."
    )],
}
KNOWLEDGE_ORDER = ["kindergarten", "knickerbockers", "quest", "conflict", "bedtime", "button", "bell", "book", "teddy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    quest, conflict, setting = f["quest"], f["conflict"], f["setting"]
    return [
        f'Write a bedtime story set in {setting.place} where a child in knickerbockers goes on a small quest and meets a conflict.',
        f'Tell a gentle kindergarten story about {f["child"].id} searching for {quest.noun} while {conflict.cause.lower()}.',
        f'Write a soft story with the words "knickerbockers", "quest", and "conflict", ending in a calm bedtime image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent = f["child"], f["parent"]
    quest, conflict, comfort = f["quest"], f["conflict"], f["comfort"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, a little {child.type} in knickerbockers, and {parent.label_word}, who stayed close during the bedtime quest."
        ),
        QAItem(
            question="What was the child trying to do?",
            answer=f"{child.id} was trying to finish a quest to find {quest.noun}. The search made the story move from quiet play into a small problem and then back to calm."
        ),
        QAItem(
            question="What was the conflict?",
            answer=f"The conflict was that {conflict.cause.lower()} {conflict.worry}. That made the quest harder and gave {child.id} a reason to ask for help."
        ),
    ]
    if f["outcome"] == "resolved":
        qa.append(QAItem(
            question="How was the problem solved?",
            answer=f"{parent.label_word.capitalize()} helped by {conflict.calm_fix}, and together they found {quest.reward}. That solved the conflict and let the bedtime feeling return."
        ))
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with {child.id} holding {comfort.phrase} close and feeling safe again. The quest was finished, and bedtime was peaceful."
        ))
    else:
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with {parent.label_word} staying close even though the missing thing was still hard to find. The room was still gentle and quiet, so the ending stayed safe."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags) | set(world.facts["conflict"].tags) | set(world.facts["comfort"].tags) | {"knickerbockers", "kindergarten", "bedtime", "quest", "conflict"}
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            for q, a in KNOWLEDGE[key]:
                out.append(QAItem(q, a))
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kindergarten", "button", "missing_button", "teddy", "Milo", "boy", "mother", "gentle", 0),
    StoryParams("kindergarten", "button", "missing_button", "owl", "Maya", "girl", "father", "curious", 1),
]


def explain_rejection(quest: Quest, conflict: Conflict) -> str:
    return (
        f"(No story: {conflict.noun} does not naturally fit this quest in a way that can be solved kindly. "
        f"Pick the button quest with the missing-button conflict.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "resolved" if params.quest == "button" and params.conflict == "missing_button" else "unresolved"


ASP_RULES = r"""
quest_at_risk(Q, C) :- quest(Q), conflict(C), Q = button, C = missing_button.
compromise(Q, C) :- quest_at_risk(Q, C), Q = button, C = missing_button.
outcome(resolved) :- compromise(button, missing_button).
outcome(unresolved) :- quest(button), conflict(missing_button), not compromise(button, missing_button).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict", cid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show quest_at_risk/2."))
    return sorted(set(asp.atoms(model, "quest_at_risk")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("chosen_quest", params.quest), asp.fact("chosen_conflict", params.conflict)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = {(q, c) for _, q, c in valid_combos()}
    cl = set(asp_valid_combos())
    if cl == py:
        print(f"OK: ASP gate matches valid_combos() ({len(cl)} combos).")
    else:
        print("MISMATCH in ASP gate:")
        print("  only in asp:", sorted(cl - py))
        print("  only in python:", sorted(py - cl))
        rc = 1
    samples = [CURATED[0], CURATED[1]]
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: default generation smoke test succeeded.")
    except Exception as exc:
        print(f"FAIL: generation smoke test crashed: {exc}")
        return 1
    if any(asp_outcome(p) != outcome_of(p) for p in samples):
        print("MISMATCH in outcome model.")
        rc = 1
    else:
        print("OK: outcome model matches Python.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A kindergarten bedtime quest story world with knickerbockers and a small conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, default=0)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.conflict:
        q, c = QUESTS[args.quest], CONFLICTS[args.conflict]
        if not (quest_at_risk(q, c) and compromise_available(q, c)):
            raise StoryError(explain_rejection(q, c))
    combos = [c for c in valid_combos() if (args.setting is None or c[0] == args.setting) and (args.quest is None or c[1] == args.quest) and (args.conflict is None or c[2] == args.conflict)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, conflict = rng.choice(sorted(combos))
    comfort = args.comfort or rng.choice(sorted(COMFORTS))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, quest, conflict, comfort, name, gender, parent, trait, args.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], CONFLICTS[params.conflict], COMFORTS[params.comfort], params.child_name, params.child_gender, params.parent, params.trait, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("", "#show quest_at_risk/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible quest/conflict combos:")
        for q, c in asp_valid_combos():
            print(f"  {q} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
            header = f"### {p.child_name}: {p.quest} / {p.conflict}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
