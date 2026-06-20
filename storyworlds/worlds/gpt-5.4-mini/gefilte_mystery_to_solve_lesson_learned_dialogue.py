#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gefilte_mystery_to_solve_lesson_learned_dialogue.py
===================================================================================

A small standalone story world about animals solving a little mystery around a
missing bowl of gefilte, learning a lesson, and talking it through together.

The domain is intentionally tiny:
- a few animal characters
- one shared treat: gefilte
- one mystery: where did it go?
- one lesson: ask first and share fairly
- dialogue throughout, with the state of the world driving the ending

The story shape is:
1. A cozy animal scene with a shared snack.
2. A mystery: the gefilte is missing.
3. A careful search and a conversation that reveals the truth.
4. A lesson learned and a gentle ending image.

The script supports:
- default random story generation
- -n / --all / --seed / --trace / --qa / --json
- --asp / --verify / --show-asp

It is stdlib-only and imports storyworlds/results.py eagerly, with storyworlds/asp.py
imported lazily inside ASP helpers.
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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        gender = self.type
        if gender in {"cat", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in {"dog", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



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
    mood: str
    hiding_spots: list[str]
    table: str

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
class Treat:
    id: str
    label: str
    smell: str
    texture: str
    favorite: bool = True

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
class Mystery:
    id: str
    clue: str
    suspicious_spot: str
    missing_words: str
    ask_sentence: str

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
class Lesson:
    id: str
    moral: str
    closing: str

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
class DialogueBeat:
    speaker: str
    line: str

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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class Rule:
    name: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.get("gefilte_bowl").meters["missing"] >= THRESHOLD:
        for ch in world.characters():
            if ch.role == "sleuth" and ch.memes["curious"] >= THRESHOLD:
                if ("worry", ch.id) not in world.fired:
                    world.fired.add(("worry", ch.id))
                    ch.memes["worry"] += 1
                    out.append(f"{ch.id} frowned and looked around the room.")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.get("gefilte_bowl")
    if bowl.meters["missing"] >= THRESHOLD and bowl.attrs.get("clue_found") and ("clue", bowl.id) not in world.fired:
        world.fired.add(("clue", bowl.id))
        world.get("table").meters["searched"] += 1
        out.append("__clue__")
    return out


RULES = [Rule("worry", _r_worry), Rule("clue", _r_clue)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sniff_out(world: World, sleuth: Entity, clue_spot: str) -> bool:
    bowl = world.get("gefilte_bowl")
    if bowl.attrs.get("hidden_in") == clue_spot:
        bowl.attrs["clue_found"] = True
        sleuth.memes["curious"] += 1
        return True
    return False


def missing_bowl(world: World, bowl: Entity) -> None:
    bowl.meters["missing"] += 1
    bowl.memes["absence"] += 1
    propagate(world, narrate=False)


def introduce(world: World, setting: Setting, sleuth: Entity, friend: Entity, elder: Entity, treat: Treat) -> None:
    world.say(
        f"In {setting.place}, {sleuth.id} the {sleuth.type}, {friend.id} the {friend.type}, "
        f"and {elder.id} the {elder.type} sat near {setting.table}. "
        f"The room felt {setting.mood}, and the air smelled like {treat.smell}."
    )


def snack_time(world: World, sleuth: Entity, friend: Entity, treat: Treat) -> None:
    sleuth.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f'"We saved the {treat.label} for snack time," {sleuth.id} said. '
        f'"It is soft and {treat.texture}."'
    )


def discover_mystery(world: World, sleuth: Entity, mystery: Mystery) -> None:
    bowl = world.get("gefilte_bowl")
    if bowl.meters["missing"] < THRESHOLD:
        return
    sleuth.memes["curious"] += 1
    world.say(
        f'But when {sleuth.id} looked at {mystery.suspicious_spot}, {mystery.ask_sentence} '
        f'"Where did the gefilte go?"'
    )
    world.say(f'"That is odd," {sleuth.id} whispered. "{mystery.clue}"')
    world.say(f'"Maybe we should solve the mystery together," {sleuth.id} said.')


def search_spot(world: World, sleuth: Entity, spot: str) -> bool:
    found = sniff_out(world, sleuth, spot)
    if found:
        world.say(f'{sleuth.id} peeked under {spot} and gasped. "I found it!"')
    else:
        world.say(f'{sleuth.id} checked {spot}, but there was only dust and a crumb.')
    return found


def talk_it_out(world: World, sleuth: Entity, friend: Entity, elder: Entity, treat: Treat) -> None:
    bowl = world.get("gefilte_bowl")
    opener = DialogueBeat(speaker=sleuth.id, line=f'"I thought someone took the {treat.label}."')
    answer = DialogueBeat(speaker=friend.id, line='"I moved it so nobody would bump it."')
    lesson = DialogueBeat(speaker=elder.id, line='"Next time, tell the group first."')
    world.say(f"{opener.speaker} said, {opener.line}")
    world.say(f"{answer.speaker} said, {answer.line}")
    world.say(f"{lesson.speaker} said, {lesson.line}")
    bowl.meters["missing"] = 0.0
    bowl.attrs["hidden_in"] = ""
    bowl.meters["served"] += 1
    sleuth.memes["relief"] += 1
    friend.memes["relief"] += 1
    elder.memes["pride"] += 1


def lesson_learned(world: World, elder: Entity, sleuth: Entity, friend: Entity, lesson: Lesson, treat: Treat) -> None:
    sleuth.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f'Then {elder.id} smiled. "{lesson.moral}" {elder.pronoun()} said. '
        f'"{lesson.closing}"'
    )
    world.say(
        f'{sleuth.id} nodded. "I will ask first next time," {sleuth.id} said, '
        f'and {friend.id} promised to do the same.'
    )
    world.say(
        f"At last, the bowl of {treat.label} was set back on the table, and the little animals "
        f"sat down to eat it together."
    )


def tell(setting: Setting, treat: Treat, mystery: Mystery, lesson: Lesson,
         sleuth_name: str = "Milo", sleuth_type: str = "cat",
         friend_name: str = "Bea", friend_type: str = "rabbit",
         elder_name: str = "Auntie", elder_type: str = "owl") -> World:
    world = World()
    sleuth = world.add(Entity(sleuth_name, kind="character", type=sleuth_type, role="sleuth"))
    friend = world.add(Entity(friend_name, kind="character", type=friend_type, role="friend"))
    elder = world.add(Entity(elder_name, kind="character", type=elder_type, role="elder"))
    bowl = world.add(Entity("gefilte_bowl", type="thing", label="gefilte", attrs={"hidden_in": setting.hiding_spots[0]}))
    world.add(Entity("table", kind="place", type="place", label=setting.table))

    introduce(world, setting, sleuth, friend, elder, treat)
    snack_time(world, sleuth, friend, treat)

    world.para()
    missing_bowl(world, bowl)
    discover_mystery(world, sleuth, mystery)
    found = False
    for spot in setting.hiding_spots:
        if search_spot(world, sleuth, spot):
            found = True
            break

    world.para()
    if found:
        talk_it_out(world, sleuth, friend, elder, treat)
        lesson_learned(world, elder, sleuth, friend, lesson, treat)
    else:
        world.say(f'"We still cannot find it," {sleuth.id} said. "Let us ask {elder.id} again."')
        world.say(f"{elder.id} gently helped them check every hiding spot.")
        bowl.meters["found_later"] += 1
        bowl.meters["missing"] = 0.0
        lesson_learned(world, elder, sleuth, friend, lesson, treat)

    world.facts.update(
        setting=setting,
        treat=treat,
        mystery=mystery,
        lesson=lesson,
        sleuth=sleuth,
        friend=friend,
        elder=elder,
        bowl=bowl,
        found=found,
    )
    return world


SETTINGS = {
    "kitchen": Setting("the kitchen", "cozy", ["under the table", "behind the chair", "near the window"], "the round table"),
    "sunroom": Setting("the sunroom", "bright", ["behind the plant", "under the bench", "beside the rug"], "the low table"),
    "porch": Setting("the porch", "quiet", ["behind the basket", "under the stool", "near the steps"], "the small table"),
}

TREATS = {
    "classic": Treat("classic", "gefilte", "fishy and sweet", "soft"),
    "spiced": Treat("spiced", "gefilte", "warm and a little peppery", "tender"),
}

MYSTERIES = {
    "missing": Mystery("missing", "a mystery was waiting under the table", "the table", "something was missing", "The bowl was not where it should have been."),
}

LESSONS = {
    "ask_first": Lesson("ask_first", "If something moves, ask before you worry", "Little mysteries are easier when everyone talks kindly."),
    "share_kindly": Lesson("share_kindly", "When you share, say so out loud", "That way nobody gets confused and everybody stays calm."),
}

ANIMALS = [
    ("Milo", "cat"),
    ("Bea", "rabbit"),
    ("Toby", "dog"),
    ("Nina", "mouse"),
    ("Ollie", "fox"),
    ("Pip", "bear"),
]



@dataclass
class StoryParams:
    setting: str
    treat: str
    mystery: str
    lesson: str
    sleuth_name: str
    sleuth_type: str
    friend_name: str
    friend_type: str
    elder_name: str
    elder_type: str
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

CURATED = [
    StoryParams("kitchen", "classic", "missing", "ask_first", "Milo", "cat", "Bea", "rabbit", "Auntie", "owl"),
    StoryParams("sunroom", "spiced", "missing", "share_kindly", "Toby", "dog", "Nina", "mouse", "Grandpa", "turtle"),
    StoryParams("porch", "classic", "missing", "ask_first", "Ollie", "fox", "Pip", "bear", "Auntie", "owl"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, m) for s in SETTINGS for t in TREATS for m in MYSTERIES]


KNOWLEDGE = {
    "gefilte": [("What is gefilte?", "Gefilte is a kind of fish dish. People can serve it at a meal, and it is meant to be eaten, not hidden away.")],
    "mystery": [("What is a mystery?", "A mystery is something that seems confusing at first. People solve it by noticing clues and asking careful questions.")],
    "ask": [("Why should you ask before moving something?", "Asking first keeps people from getting confused. It also helps everyone know where things are.")],
    "share": [("Why is sharing helpful?", "Sharing helps everyone know what is happening. It can keep small problems from becoming big ones.")],
    "dialogue": [("What is dialogue?", "Dialogue is when characters talk to each other in a story. It helps the reader hear their thoughts and feelings.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a young child that includes the word "gefilte" and has a small mystery to solve.',
        f"Tell a cozy story where {f['sleuth'].id} and friends wonder where the gefilte went, then solve the mystery by talking kindly.",
        f'Write a gentle animal story with dialogue, a lesson learned, and the word "gefilte" appearing at the snack table.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sleuth, friend, elder, bowl = f["sleuth"], f["friend"], f["elder"], f["bowl"]
    qa = [
        ("Who is the story about?",
         f"It is about {sleuth.id}, {friend.id}, and {elder.id}, a small group of animals sharing a snack and solving a mystery together."),
        ("What was the mystery?",
         f"They could not find the gefilte bowl at first, so they had to ask questions and look for clues. That is what made the story a mystery to solve."),
        ("What did the animals do when they were confused?",
         f"They talked to each other instead of staying upset. The dialogue helped them learn where the gefilte had gone."),
        ("What lesson did they learn?",
         f"They learned to ask before moving something and to say where they put shared food. That kept everyone calm and helped the mystery get solved."),
    ]
    if f["found"]:
        qa.append(("How was the mystery solved?",
                   f"{friend.id} had moved the bowl to keep it safe, and then {sleuth.id} found the hiding spot by searching carefully. After that, everyone talked it out and put the gefilte back on the table."))
    qa.append(("How did the story end?",
                f"It ended with the gefilte back on the table and the animals eating together. The missing bowl was no longer a mystery, and the lesson stayed with them."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    tags = {"gefilte", "mystery", "ask", "share", "dialogue"}
    for tag in tags:
        out.extend(KNOWLEDGE.get(tag, []))
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
missing_bowl :- bowl_missing.
curious_now(C) :- character(C), curious(C, N), N >= 1.
worry(C) :- curious_now(C), missing_bowl.
found_clue :- hidden_in(gefilte_bowl, Spot), clue_spot(Spot).
lesson_learned :- found_clue.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    clingo = sorted(set(asp.atoms(model, "setting")))
    python = sorted((sid,) for sid in SETTINGS)
    if clingo != python:
        print("MISMATCH in settings facts")
        return 1
    sample = generate(CURATED[0])
    print("OK: ASP facts parsed and story generation works.")
    print(sample.story[:120] + "...")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal mystery story world with gefilte, dialogue, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--lesson", choices=LESSONS)
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
    choices = valid_combos()
    if not choices:
        raise StoryError("No valid story combinations.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    treat = args.treat or rng.choice(sorted(TREATS))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    lesson = args.lesson or rng.choice(sorted(LESSONS))
    return StoryParams(
        setting=setting,
        treat=treat,
        mystery=mystery,
        lesson=lesson,
        sleuth_name=rng.choice([n for n, _ in ANIMALS]),
        sleuth_type=rng.choice([t for _, t in ANIMALS]),
        friend_name=rng.choice([n for n, _ in ANIMALS]),
        friend_type=rng.choice([t for _, t in ANIMALS]),
        elder_name=rng.choice(["Auntie", "Grandpa", "Uncle", "Nana"]),
        elder_type=rng.choice(["owl", "turtle", "bear", "cat"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], TREATS[params.treat], MYSTERIES[params.mystery], LESSONS[params.lesson],
        params.sleuth_name, params.sleuth_type, params.friend_name, params.friend_type, params.elder_name, params.elder_type
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def tell(setting: Setting, treat: Treat, mystery: Mystery, lesson: Lesson,
         sleuth_name: str, sleuth_type: str, friend_name: str, friend_type: str,
         elder_name: str, elder_type: str) -> World:
    return tell_world(setting, treat, mystery, lesson, sleuth_name, sleuth_type, friend_name, friend_type, elder_name, elder_type)


def tell_world(setting: Setting, treat: Treat, mystery: Mystery, lesson: Lesson,
               sleuth_name: str, sleuth_type: str, friend_name: str, friend_type: str,
               elder_name: str, elder_type: str) -> World:
    world = World()
    sleuth = world.add(Entity(sleuth_name, kind="character", type=sleuth_type, role="sleuth", traits=["curious"]))
    friend = world.add(Entity(friend_name, kind="character", type=friend_type, role="friend", traits=["kind"]))
    elder = world.add(Entity(elder_name, kind="character", type=elder_type, role="elder", traits=["wise"]))
    bowl = world.add(Entity("gefilte_bowl", kind="thing", type="thing", label="gefilte", attrs={"hidden_in": setting.hiding_spots[1]}))
    world.add(Entity("table", kind="place", type="place", label=setting.table))

    introduce(world, setting, sleuth, friend, elder, treat)
    snack_time(world, sleuth, friend, treat)
    world.para()
    missing_bowl(world, bowl)
    discover_mystery(world, sleuth, mystery)
    search_spot(world, sleuth, setting.hiding_spots[0])
    if bowl.attrs.get("hidden_in") == setting.hiding_spots[1]:
        bowl.attrs["clue_found"] = True
        search_spot(world, sleuth, setting.hiding_spots[1])
    world.para()
    talk_it_out(world, sleuth, friend, elder, treat)
    lesson_learned(world, elder, sleuth, friend, lesson, treat)
    world.facts.update(sleuth=sleuth, friend=friend, elder=elder, bowl=bowl, setting=setting, found=True)
    return world


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(sorted(SETTINGS)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
