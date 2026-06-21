#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jacks_novel_fool_ish_humor_cautionary_teamwork.py
==================================================================================

A small, standalone storyworld for a child-facing animal story with humor,
caution, and teamwork.

Premise
-------
A few animals are playing with jacks in a little library. They spot a novel on a
high shelf and one of them has a fool-ish idea about using the jacks to reach it.
A cautious friend warns them, and the group finds a safer, funnier way to get the
book down together.

This script follows the shared Storyweavers contract:
- typed entities with meters and memes
- state-driven narration
- grounded QA sets
- Python reasonableness gate plus inline ASP twin
- --verify smoke tests normal generation

The required seed words appear naturally in the story:
- jacks
- novel
- fool-ish
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
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "cautious", "thoughtful", "gentle", "wise"}


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    shelf: str
    mood: str
    sounds: str
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


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    safe_reach: bool
    stackable: bool = False
    makes_noise: bool = False
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
class Tool:
    id: str
    label: str
    phrase: str
    helps_reach: bool
    safe: bool = True
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
class Response:
    id: str
    sense: int
    power: int
    text: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
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


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["risk"] < THRESHOLD:
            continue
        sig = ("tension", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append("")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)


CAUSAL_RULES = [Rule("tension", _r_tension)]


def hazard_on_jacks(item: Item, tool: Tool) -> bool:
    return item.safe_reach and tool.safe


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for iid, item in ITEMS.items():
            for tid, tool in TOOLS.items():
                for rid, resp in RESPONSES.items():
                    if resp.sense < SENSE_MIN:
                        continue
                    if item.safe_reach and tool.helps_reach:
                        combos.append((sid, iid, tid, rid))
    return combos


def scene_intro(world: World, leader: Entity, friend: Entity) -> None:
    leader.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a quiet afternoon, {leader.id} and {friend.id} played in {world.setting.place}. "
        f"The room smelled of paper, and the shelves stood tall and tidy."
    )
    world.say(
        f"They giggled over a little game of jacks, with tiny clacks and skitters across the floor."
    )
    world.say(
        f"Up high, a shiny novel sat on {world.setting.shelf}, looking lonely and just a bit mysterious."
    )


def want_book(world: World, leader: Entity, item: Item) -> None:
    leader.memes["want"] += 1
    world.say(
        f'{leader.id} pointed up. "I want that {item.label}," {leader.pronoun()} said. '
        f'"It looks novel and important."'
    )


def fool_ish_idea(world: World, leader: Entity, item: Item, tool: Tool) -> None:
    leader.memes["risk"] += 1
    world.say(
        f"{leader.id}'s eyes sparkled with a fool-ish plan. "
        f'"I can stack these {tool.label} and reach it!" {leader.pronoun()} said.'
    )
    world.say(
        f"For one silly second, it seemed funny to try."
    )


def caution(world: World, friend: Entity, leader: Entity, item: Item, tool: Tool) -> None:
    friend.memes["caution"] += 1
    world.say(
        f'{friend.id} blinked. "That is a fool-ish idea," {friend.pronoun()} said. '
        f'"The {tool.label} are for play, not ladders, and the shelf is too high."'
    )
    world.say(
        f"{friend.id} also knew the book could slip and thump the floor."
    )


def reject_if_unreasonable(item: Item, tool: Tool) -> bool:
    return item.safe_reach and tool.safe


def safe_teamwork(world: World, leader: Entity, friend: Entity, item: Item, tool: Tool, resp: Response) -> None:
    leader.memes["joy"] += 1
    friend.memes["joy"] += 1
    leader.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"Then {leader.id} and {friend.id} looked around together."
    )
    world.say(
        f'{friend.id} found a little stool, and {leader.id} carried the {tool.label} away from the shelf.'
    )
    world.say(
        f'They used the stool and a long book hook, and soon the {item.label} came down with a soft plop.'
    )
    world.say(
        f'{resp.text.replace("{target}", item.label)}'
    )
    world.say(
        f"They sat on the rug, shared the {item.label}, and laughed at how the jacks had nearly turned into a tower of trouble."
    )


def fail_branch(world: World, leader: Entity, friend: Entity, item: Item, tool: Tool, resp: Response) -> None:
    leader.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"{leader.id} tried the plan anyway, but the stack wobbled at once."
    )
    world.say(
        f'{resp.fail.replace("{target}", item.label)}'
    )
    world.say(
        f"{friend.id} hurried over, and together they set the {tool.label} aside before anything else could topple."
    )


def ending(world: World, leader: Entity, friend: Entity, item: Item) -> None:
    world.say(
        f"In the end, the little library was tidy again, the {item.label} was open, and the jacks were back in their box."
    )
    world.say(
        f"{leader.id} and {friend.id} smiled at the same page, proud that they had chosen teamwork over a fool-ish tumble."
    )


def tell(setting: Setting, item: Item, tool: Tool, response: Response,
         leader_name: str = "Mina", leader_gender: str = "girl",
         friend_name: str = "Pip", friend_gender: str = "boy",
         parent_name: str = "Aunt Owl", parent_gender: str = "woman") -> World:
    world = World(setting)
    leader = world.add(Entity(id=leader_name, kind="character", type=leader_gender, role="leader"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    book = world.add(Entity(id="novel", type=item.type, label=item.label))
    world.facts["parent"] = parent
    world.facts["item"] = item
    world.facts["tool"] = tool
    world.facts["response"] = response
    scene_intro(world, leader, friend)
    world.para()
    want_book(world, leader, item)
    fool_ish_idea(world, leader, item, tool)
    caution(world, friend, leader, item, tool)
    if reject_if_unreasonable(item, tool):
        safe_teamwork(world, leader, friend, item, tool, response)
    else:
        fail_branch(world, leader, friend, item, tool, response)
    world.para()
    ending(world, leader, friend, item)
    world.facts.update(leader=leader, friend=friend, book=book, outcome="safe")
    return world


SETTINGS = {
    "library": Setting(id="library", place="a little library", shelf="a high shelf", mood="quiet", sounds="soft page flutters"),
    "reading_room": Setting(id="reading_room", place="a cozy reading room", shelf="a tall shelf", mood="calm", sounds="tiny whispers"),
}

ITEMS = {
    "novel": Item(id="novel", label="novel", phrase="a colorful novel", type="book", safe_reach=True, stackable=False, tags={"novel"}),
}

TOOLS = {
    "jacks": Tool(id="jacks", label="jacks", phrase="a tin box of jacks", helps_reach=False, safe=True, tags={"jacks"}),
    "stool": Tool(id="stool", label="stool", phrase="a little stool", helps_reach=True, safe=True, tags={"teamwork"}),
}

RESPONSES = {
    "book_hook": Response(
        id="book_hook",
        sense=3,
        power=3,
        text="The little book hook did the job, and the novel slipped gently into their hands",
        fail="The little book hook was too short, and the novel slid back up",
        qa_text="used the little book hook to get the novel down",
        tags={"teamwork"},
    ),
    "stool_and_hook": Response(
        id="stool_and_hook",
        sense=4,
        power=4,
        text="The stool and the book hook worked perfectly, and the novel came down safely",
        fail="The stool and the hook wobbled, but the novel stayed put",
        qa_text="used a stool and book hook to get the novel down safely",
        tags={"teamwork"},
    ),
    "pity": Response(
        id="pity",
        sense=1,
        power=1,
        text="They tried a silly trick, but it hardly helped at all",
        fail="They tried a silly trick, but it hardly helped at all",
        qa_text="did not solve the problem",
        tags={"fool-ish"},
    ),
}

SENSE_MIN = 2
GIRL_NAMES = ["Mina", "Luna", "Poppy", "Tara"]
BOY_NAMES = ["Pip", "Otto", "Milo", "Finn"]
TRAITS = ["careful", "cautious", "thoughtful", "gentle", "wise"]
@dataclass
class StoryParams:
    setting: str
    item: str
    tool: str
    response: str
    leader: str = "Mina"
    leader_gender: str = "girl"
    friend: str = "Pip"
    friend_gender: str = "boy"
    parent: str = "Aunt Owl"
    parent_gender: str = "woman"
    trait: str = "careful"
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


CURATED = [
    StoryParams(setting="library", item="novel", tool="jacks", response="stool_and_hook", leader="Mina", leader_gender="girl", friend="Pip", friend_gender="boy", parent="Aunt Owl", parent_gender="woman", trait="careful"),
    StoryParams(setting="reading_room", item="novel", tool="jacks", response="book_hook", leader="Luna", leader_gender="girl", friend="Otto", friend_gender="boy", parent="Aunt Owl", parent_gender="woman", trait="thoughtful"),
]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write an animal story for a young child that includes the words "jacks", "novel", and "fool-ish".',
        'Tell a cautionary teamwork story about animals in a library, with a funny fool-ish idea that gets replaced by a safer plan.',
        'Write a short story where two animal friends nearly use jacks in a fool-ish way, but work together to reach a novel safely.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader, friend, item = f["leader"], f["friend"], f["item"]
    qa = [
        ("Who is the story about?",
         f"It is about {leader.id} and {friend.id}, two animal friends who are playing in a little library."),
        ("What silly idea did the leader have?",
         f"{leader.id} had the fool-ish idea of stacking the jacks to reach the novel on the high shelf."),
        ("What did the cautious friend say?",
         f"{friend.id} warned that the plan was fool-ish because the jacks were for play, not for climbing."),
        ("How did they solve the problem?",
         f"They used teamwork, found a stool, and brought the novel down safely instead of making a wobbling tower."),
        ("How did the story end?",
         f"It ended with both friends reading the novel together and the jacks safely back in their box."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What are jacks?",
         "Jacks are a small game with little pieces that bounce and clack on the floor. They are fun to play with, but not for climbing."),
        ("What is a novel?",
         "A novel is a book with a story inside it. People read novels to enjoy adventures and ideas."),
        ("What does fool-ish mean?",
         "Fool-ish means not very smart or not careful. It is the kind of choice that can cause trouble."),
        ("What is teamwork?",
         "Teamwork means people help each other and do a task together. It often makes hard jobs safer and easier."),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(item: Item, tool: Tool) -> str:
    return f"(No story: {tool.label} cannot safely help reach the {item.label}; the plan is too fool-ish.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: jacks, novel, fool-ish, humor, cautionary teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--leader")
    ap.add_argument("--friend")
    ap.add_argument("--parent")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.tool == "jacks" and args.response == "pity":
        raise StoryError(explain_rejection(ITEMS["novel"], TOOLS["jacks"]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.tool is None or c[2] == args.tool)
              and (args.response is None or c[3] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, tool, response = rng.choice(sorted(combos))
    leader = args.leader or rng.choice(GIRL_NAMES)
    friend = args.friend or rng.choice(BOY_NAMES)
    parent = args.parent or "Aunt Owl"
    return StoryParams(setting=setting, item=item, tool=tool, response=response,
                       leader=leader, leader_gender="girl", friend=friend, friend_gender="boy",
                       parent=parent, parent_gender="woman", trait=rng.choice(TRAITS))


def generate(params: StoryParams) -> StorySample:
    for key in (params.setting, params.item, params.tool, params.response):
        if key not in {"library", "reading_room", "novel", "jacks", "stool", "book_hook", "stool_and_hook", "pity"}:
            raise StoryError("Invalid params.")
    world = tell(SETTINGS[params.setting], ITEMS[params.item], TOOLS[params.tool], RESPONSES[params.response],
                 params.leader, params.leader_gender, params.friend, params.friend_gender, params.parent, params.parent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
item_safe(novel).
tool_safe(stool).
response_good(book_hook).
response_good(stool_and_hook).
valid(S,I,T,R) :- setting(S), item(I), tool(T), response(R), item_safe(I), tool_safe(T), response_good(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combinations.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test story generated.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
