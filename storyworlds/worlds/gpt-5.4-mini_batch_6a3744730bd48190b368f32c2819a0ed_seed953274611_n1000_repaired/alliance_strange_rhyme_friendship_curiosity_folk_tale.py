#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/alliance_strange_rhyme_friendship_curiosity_folk_tale.py
========================================================================================

A tiny folk-tale storyworld about curiosity, a strange rhyme, and a friendship
that turns into an alliance.

Premise
-------
A curious child hears a strange rhyme from the old bridge, meets a shy helper,
and decides whether to trust the clue. If the child follows the clue, the pair
work together to recover something the village needs, and the ending shows a
new alliance in action.

The world is built to produce complete, child-facing stories with:
- a folk-tale voice
- a state-driven turn
- an ending image proving change
- three Q&A sets grounded in simulated state
- a Python reasonableness gate with an inline ASP twin

Words from the seed are woven into the narrative:
- alliance
- strange
- rhyme
- friendship
- curiosity
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
CURIOUS_INIT = 6.0
TRUST_INIT = 4.0


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
class StoryParams:
    setting: str
    child: str
    child_gender: str
    helper: str
    helper_kind: str
    helper_gender: str
    object: str
    obstacle: str
    rhyme: str
    action: str
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


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    mood: str
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
class HelperType:
    id: str
    kind: str
    label: str
    pronoun_type: str
    what_it_knows: str
    what_it_can_do: str
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
class Treasure:
    id: str
    label: str
    phrase: str
    needs: str
    risk: str
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
class Obstacle:
    id: str
    label: str
    phrase: str
    blocks: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_bond(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["curiosity"] >= THRESHOLD and helper.memes["trust"] >= THRESHOLD:
        sig = ("bond",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["friendship"] += 1
            helper.memes["friendship"] += 1
            out.append("__bond__")
    return out


def _r_alliance(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["friendship"] >= THRESHOLD and helper.memes["friendship"] >= THRESHOLD:
        sig = ("alliance",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["alliance"] += 1
            helper.memes["alliance"] += 1
            out.append("__alliance__")
    return out


CAUSAL_RULES = [Rule("bond", _r_bond), Rule("alliance", _r_alliance)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            for sent in rule.apply(world):
                changed = True
                if not sent.startswith("__"):
                    produced.append(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for hid in HELPERS:
            for tid in TREASURES:
                for oid in OBSTACLES:
                    if is_reasonable(HELPERS[hid], TREASURES[tid], OBSTACLES[oid]):
                        combos.append((sid, hid, tid))
    return combos


def is_reasonable(helper: HelperType, treasure: Treasure, obstacle: Obstacle) -> bool:
    return treasure.needs in helper.what_it_can_do and obstacle.blocks == treasure.risk


def outcome_of(params: StoryParams) -> str:
    return "joined" if params.action in {"help", "follow"} else "missed"


def explain_rejection(helper: HelperType, treasure: Treasure, obstacle: Obstacle) -> str:
    return (
        f"(No story: {helper.label} cannot reasonably solve {treasure.label} against "
        f"{obstacle.label}. The alliance would not have a believable turn.)"
    )


def build_world(setting: Setting, helper_type: HelperType) -> World:
    w = World(setting)
    child = w.add(Entity(id="child", kind="character", type="girl", role="curious-one"))
    helper = w.add(Entity(id="helper", kind="character", type=helper_type.pronoun_type, role="friend"))
    elder = w.add(Entity(id="elder", kind="character", type="woman", role="elder", label="the old woman"))
    field = w.add(Entity(id="field", type="place", label="the village green"))
    w.facts["elder"] = elder
    w.facts["field"] = field
    child.memes["curiosity"] = CURIOUS_INIT
    helper.memes["trust"] = TRUST_INIT
    return w


def tell(setting: Setting, helper_type: HelperType, treasure: Treasure, obstacle: Obstacle,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str,
         rhyme: str, action: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="curious-one"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="friend"))
    elder = world.add(Entity(id="elder", kind="character", type="woman", role="elder", label="the old woman"))
    child.memes["curiosity"] = CURIOUS_INIT
    helper.memes["trust"] = TRUST_INIT

    world.say(
        f"Once in {setting.place}, where {setting.mood}, {child.id} walked with {child.pronoun('possessive')} eyes open for wonders."
    )
    world.say(
        f"At the old bridge, {child.id} heard a strange rhyme: “{rhyme}.” "
        f"The words sounded like a door that wanted to open."
    )
    world.para()
    world.say(
        f"{child.id} followed the rhyme and found {helper.id}, a shy little {helper.label}, "
        f"standing near {obstacle.phrase}."
    )
    child.memes["curiosity"] += 1
    helper.memes["trust"] += 1
    world.say(
        f'"{helper.what_it_knows}," said {helper.id}, "and {treasure.risk} keeps the {treasure.label} from the village."'
    )
    world.say(
        f"{child.id} did not laugh at the strange tale. {child.id} listened, and a friendship began to warm.'
    )
    propagate(world, narrate=False)
    world.para()
    if child.memes["alliance"] >= THRESHOLD:
        world.say(
            f"Together they made an alliance. {child.id} climbed the low stones while {helper.id} did "
            f"{helper.what_it_can_do}, and the obstacle at last gave way."
        )
        child.meters["distance"] += 1
        helper.meters["effort"] += 1
        treasure.meters["recovered"] = 1
        world.say(
            f"When the {treasure.label} came free, the old woman carried it back to the green, "
            f"and the village bell rang clear again."
        )
        world.say(
            f"That night, {child.id} and {helper.id} shared a crust of bread by the fire, "
            f"their alliance shining brighter than the moon."
        )
    else:
        world.say(
            f"The words were strange, but not yet understood. {child.id} waved goodbye, "
            f"and the bridge kept its secret for another day."
        )
    world.facts.update(
        child=child,
        helper=helper,
        elder=elder,
        setting=setting,
        helper_type=helper_type,
        treasure=treasure,
        obstacle=obstacle,
        rhyme=rhyme,
        action=action,
        outcome="joined" if child.memes["alliance"] >= THRESHOLD else "unjoined",
    )
    return world


SETTINGS = {
    "river": Setting(id="river", place="the willow river", opening="by a silver river", mood="the reeds whispered and the water sang"),
    "hill": Setting(id="hill", place="the wind hill", opening="on a mossy hill", mood="the grass bowed to every breeze"),
}

HELPERS = {
    "fox": HelperType(id="fox", kind="animal", label="fox", pronoun_type="thing", what_it_knows="I know where the hidden path bends", what_it_can_do="slip through the brambles", tags={"fox"}),
    "heron": HelperType(id="heron", kind="animal", label="heron", pronoun_type="thing", what_it_knows="I know how the water opens a way", what_it_can_do="reach the snagged branch", tags={"heron"}),
    "mouse": HelperType(id="mouse", kind="animal", label="mouse", pronoun_type="thing", what_it_knows="I know which root-latch turns", what_it_can_do="fit into the tiny gap", tags={"mouse"}),
}

TREASURES = {
    "bell": Treasure(id="bell", label="brass bell", phrase="the village bell", needs="reach", risk="stuck", tags={"bell"}),
    "bread": Treasure(id="bread", label="seed bread", phrase="the baker's bread", needs="carry", risk="stolen", tags={"bread"}),
    "songbook": Treasure(id="songbook", label="songbook", phrase="the festival songbook", needs="open", risk="shut", tags={"songbook"}),
}

OBSTACLES = {
    "bramble": Obstacle(id="bramble", label="bramble", phrase="a thorny bramble", blocks="stuck", tags={"bramble"}),
    "lock": Obstacle(id="lock", label="lock", phrase="an old iron lock", blocks="shut", tags={"lock"}),
    "wind": Obstacle(id="wind", label="wind", phrase="a greedy gust of wind", blocks="stolen", tags={"wind"}),
}

NAMES = ["Mara", "Nina", "Ivo", "Pip", "Tomas", "Lea"]
RHYMES = [
    "Follow the dusk, follow the dew, and the shy old road will open for you",
    "When the moon is thin and the reeds are high, kindness can answer a hidden cry",
    "Step by step and breath by breath, the little friend may beat the test",
]


@dataclass
class StoryParams:
    setting: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    object: str
    obstacle: str
    rhyme: str
    action: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about curiosity, friendship, and alliance.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--object", choices=TREASURES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--action", choices=["help", "follow", "wait"])
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["woman", "man", "thing"], default="thing")
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
    if args.helper and args.object and args.obstacle:
        if not is_reasonable(HELPERS[args.helper], TREASURES[args.object], OBSTACLES[args.obstacle]):
            raise StoryError(explain_rejection(HELPERS[args.helper], TREASURES[args.object], OBSTACLES[args.obstacle]))
    choices = [
        (sid, hid, oid, bid)
        for sid in SETTINGS
        for hid in HELPERS
        for oid in TREASURES
        for bid in OBSTACLES
        if is_reasonable(HELPERS[hid], TREASURES[oid], OBSTACLES[bid])
        and (args.setting is None or sid == args.setting)
        and (args.helper is None or hid == args.helper)
        and (args.object is None or oid == args.object)
        and (args.obstacle is None or bid == args.obstacle)
    ]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    sid, hid, oid, bid = rng.choice(sorted(choices))
    child = args.child or rng.choice(NAMES)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or "thing"
    action = args.action or rng.choice(["help", "follow"])
    rhyme = rng.choice(RHYMES)
    return StoryParams(
        setting=sid,
        child=child,
        child_gender=child_gender,
        helper=hid,
        helper_gender=helper_gender,
        object=oid,
        obstacle=bid,
        rhyme=rhyme,
        action=action,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a young child that includes the words "alliance" and "strange".',
        f"Tell a story where {f['child'].id} hears a strange rhyme, makes a friendship with {f['helper'].id}, and the two form an alliance.",
        f"Write a gentle tale with curiosity, rhyme, and a helper who solves {f['obstacle'].label} so the village can recover {f['treasure'].label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, treasure, obstacle = f["child"], f["helper"], f["treasure"], f["obstacle"]
    qa = [
        ("What kind of story is this?",
         "It is a folk tale with a curious child, a strange rhyme, and a friendship that grows into an alliance."),
        (f"Why did {child.id} go to the bridge?",
         f"{child.id} went because curiosity pulled {child.pronoun('object')} toward the strange rhyme. The rhyme sounded like a clue, so {child.id} followed it to see where it led."),
        (f"What did {child.id} and {helper.id} do together?",
         f"They joined in an alliance and worked together to clear {obstacle.phrase}. That teamwork let them recover {treasure.phrase} for the village."),
    ]
    if f["outcome"] == "joined":
        qa.append((
            "How did the story end?",
            f"It ended with the village bell sounding again and {child.id} sharing bread with {helper.id}. "
            f"The ending proves the friendship had become a real alliance."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended quietly, with the bridge still keeping its secret. "
            f"{child.id} was curious, but the alliance never formed."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set()
    tags.add("curiosity")
    tags.add("friendship")
    tags.add("rhyme")
    if world.facts["outcome"] == "joined":
        tags.add("alliance")
    out = []
    if "curiosity" in tags:
        out.append(("What is curiosity?",
                     "Curiosity is the feeling that makes you want to know more. It helps a child ask questions and follow a clue carefully."))
    if "friendship" in tags:
        out.append(("What is friendship?",
                     "Friendship is a kind bond between friends. Friends listen to one another and help each other when something is hard."))
    if "rhyme" in tags:
        out.append(("What is a rhyme?",
                     "A rhyme is a pair of words or lines that sound alike at the end. Folk tales often use rhymes like tiny songs or clues."))
    if "alliance" in tags:
        out.append(("What is an alliance?",
                     "An alliance is a promise to work together for the same goal. In a story, it means the helpers choose the same side and act as one team."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    if params.object not in TREASURES:
        raise StoryError(f"Unknown object: {params.object}")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"Unknown obstacle: {params.obstacle}")
    if params.action not in {"help", "follow", "wait"}:
        raise StoryError(f"Unknown action: {params.action}")
    if not is_reasonable(HELPERS[params.helper], TREASURES[params.object], OBSTACLES[params.obstacle]):
        raise StoryError(explain_rejection(HELPERS[params.helper], TREASURES[params.object], OBSTACLES[params.obstacle]))

    world = tell(
        SETTINGS[params.setting],
        HELPERS[params.helper],
        TREASURES[params.object],
        OBSTACLES[params.obstacle],
        params.child,
        params.child_gender,
        params.helper,
        params.helper_gender,
        params.rhyme,
        params.action,
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


ASP_RULES = r"""
reasonable(S,H,T,O) :- setting(S), helper(H), treasure(T), obstacle(O),
    need(T, N), can_do(H, N), blocks(O, B), risk(T, B).
joined :- curious(C), trust(H), friendship(C), friendship(H).
outcome(joined) :- reasonable(S,H,T,O), joined.
outcome(unjoined) :- reasonable(S,H,T,O), not joined.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("can_do", hid, h.what_it_can_do.split()[0]))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("need", tid, t.needs))
        lines.append(asp.fact("risk", tid, t.risk))
    for oid, o in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("blocks", oid, o.blocks))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/4."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    rc = 0
    pset = set(valid_combos())
    aset = set((s, h, t) for s, h, t, _ in asp_valid_combos())
    if pset == aset:
        print(f"OK: ASP gate matches valid_combos() ({len(pset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about alliance, strange rhyme, friendship, and curiosity.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--object", choices=TREASURES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--action", choices=["help", "follow", "wait"])
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["woman", "man", "thing"], default="thing")
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
    if args.setting and args.helper and args.object and args.obstacle:
        if not is_reasonable(HELPERS[args.helper], TREASURES[args.object], OBSTACLES[args.obstacle]):
            raise StoryError(explain_rejection(HELPERS[args.helper], TREASURES[args.object], OBSTACLES[args.obstacle]))
    combos = [
        (s, h, o, b)
        for s in SETTINGS
        for h in HELPERS
        for o in TREASURES
        for b in OBSTACLES
        if is_reasonable(HELPERS[h], TREASURES[o], OBSTACLES[b])
        and (args.setting is None or s == args.setting)
        and (args.helper is None or h == args.helper)
        and (args.object is None or o == args.object)
        and (args.obstacle is None or b == args.obstacle)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, h, o, b = rng.choice(sorted(combos))
    return StoryParams(
        setting=s,
        child=args.child or rng.choice(NAMES),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        helper=h,
        helper_gender=args.helper_gender,
        object=o,
        obstacle=b,
        rhyme=rng.choice(RHYMES),
        action=args.action or rng.choice(["help", "follow"]),
    )


CURATED = [
    StoryParams(setting="river", child="Mara", child_gender="girl", helper="fox", helper_gender="thing", object="bell", obstacle="bramble", rhyme="Follow the dusk, follow the dew, and the shy old road will open for you", action="help"),
    StoryParams(setting="hill", child="Pip", child_gender="boy", helper="mouse", helper_gender="thing", object="songbook", obstacle="lock", rhyme="When the moon is thin and the reeds are high, kindness can answer a hidden cry", action="follow"),
    StoryParams(setting="river", child="Lea", child_gender="girl", helper="heron", helper_gender="thing", object="bread", obstacle="wind", rhyme="Step by step and breath by breath, the little friend may beat the test", action="help"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show reasonable/4.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show reasonable/4."))
        print(f"{len(asp.atoms(model, 'reasonable'))} reasonable combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            except StoryError as e:
                print(e)
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
            header = f"### {p.child} with {p.helper} in {p.setting} ({p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
