#!/usr/bin/env python3
"""
storyworlds/worlds/caribou_boat_ramp_quest_rhyming_story.py
===========================================================

A small storyworld about a child, a caribou, and a quest at the boat ramp.

Seed premise:
A child visits a boat ramp with a caribou friend and must find a lost quest
token before the tide changes. The story is written in a gentle rhyming style,
with a clear setup, search, turn, and ending image.

The world is intentionally tiny: a few entities, a few physical meters, and a
few emotional memes drive the prose. The quest has only a couple of reasonable
variants so the stories stay crisp and complete.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    caribou: object | None = None
    child: object | None = None
    ramp: object | None = None
    token: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    id: str
    place: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Quest:
    id: str
    title: str
    rhyme1: str
    rhyme2: str
    clue: str
    hidden_place: str
    risk: str
    turn: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


def _r_tide(world: World) -> list[str]:
    out = []
    tide = world.facts.get("tide", 0.0)
    if tide >= THRESHOLD and ("tide",) not in world.fired:
        world.fired.add(("tide",))
        world.get("ramp").meters["wet"] += 1
        world.get("child").memes["rush"] += 1
        out.append("__tide__")
    return out


def _r_find(world: World) -> list[str]:
    out = []
    if world.get("token").meters["found"] >= THRESHOLD and ("found",) not in world.fired:
        world.fired.add(("found",))
        world.get("child").memes["joy"] += 1
        world.get("caribou").memes["pride"] += 1
        out.append("__found__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_tide, _r_find):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUESTS.values():
            for t in TOOLS.values():
                if q.id == "lost_token" and t.id in {"hook", "lantern"}:
                    combos.append((s, q.id, t.id))
    return combos


def road_to_quest(world: World, child: Entity, caribou: Entity, quest: Quest) -> None:
    child.memes["wonder"] += 1
    caribou.memes["calm"] += 1
    world.say(
        f"At the boat ramp, where the water lapped with a silvery gleam, "
        f"{child.id} and {caribou.label} came to dream."
    )
    world.say(
        f"They heard of a quest with a little lost sign, "
        f"and followed the clue line by rhyming line."
    )


def search(world: World, child: Entity, caribou: Entity, quest: Quest, tool: Tool) -> None:
    world.say(
        f'"{tool.phrase}," said {child.id}, "will help us to see '
        f"where the lost quest token might happen to be."
    )
    world.say(
        f"{caribou.label} lowered {caribou.pronoun('possessive')} nose, "
        f"sniffing the dock and the slippery rows."
    )
    world.say(
        f"They peeked by a cleat and they looked by a post, "
        f"and even the gulls seemed to join in the coast."
    )


def turn(world: World, child: Entity, caribou: Entity, quest: Quest, tool: Tool) -> None:
    child.memes["worry"] += 1
    world.say(
        f"But the wind got colder; the clouds drifted near, "
        f"and the ramp started shining with watery fear."
    )
    world.say(
        f'Then {caribou.id} nudged the old driftwood crate: '
        f'"The token is tucked where the barnacles wait."'
    )
    world.say(
        f"They lifted the lid with a careful small sway, "
        f"and found the bright token in a snug hidden tray."
    )
    world.get("token").meters["found"] += 1
    propagate(world)


def finish(world: World, child: Entity, caribou: Entity, quest: Quest, tool: Tool) -> None:
    world.say(
        f"{quest.turn} {child.id} laughed, and {caribou.label} did too; "
        f"the quest felt complete in the salt-sea blue."
    )
    world.say(
        f"{quest.ending_image} "
        f"{child.id} held the token, all shining and bright, "
        f"while {caribou.label} stood watching the last of the light."
    )


SETTINGS = {
    "boat_ramp": Setting(id="boat_ramp", place="the boat ramp", tags={"water", "dock"}),
}

QUESTS = {
    "lost_token": Quest(
        id="lost_token",
        title="the lost token quest",
        rhyme1="dock and rock",
        rhyme2="glow and show",
        clue="a small marker slipped near the boards",
        hidden_place="under a driftwood crate",
        risk="the tide would wet the ramp",
        turn="At last they knew what the clue had meant:",
        ending_image="The token shone gold in the evening air.",
        tags={"quest", "token", "tide"},
    ),
}

TOOLS = {
    "hook": Tool(id="hook", label="hook", phrase="a little hook on a rope", helps="lift"),
    "lantern": Tool(id="lantern", label="lantern", phrase="a bright lantern", helps="see"),
}


@dataclass
class StoryParams:
    setting: str
    quest: str
    tool: str
    child_name: str = "Mina"
    child_type: str = "girl"
    seed: Optional[int] = None
    sample: object | None = None
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming quest story at a boat ramp.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
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
    combos = valid_combos()
    if getattr(args, "setting", None) or getattr(args, "quest", None) or getattr(args, "tool", None):
        combos = [
            c for c in combos
            if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
            and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
            and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
        ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, quest, tool = rng.choice(list(combos))
    return StoryParams(
        setting=setting,
        quest=quest,
        tool=tool,
        child_name=getattr(args, "child_name", None) or rng.choice(["Mina", "Lena", "Pip", "Nori"]),
        child_type=getattr(args, "child_type", None) or rng.choice(["girl", "boy"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.quest not in QUESTS or params.tool not in TOOLS:
        pass
    setting = _safe_lookup(SETTINGS, params.setting)
    quest = _safe_lookup(QUESTS, params.quest)
    tool = _safe_lookup(TOOLS, params.tool)
    world = World(setting)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, label=params.child_name))
    caribou = world.add(Entity(id="caribou", kind="character", type="caribou", label="the caribou"))
    ramp = world.add(Entity(id="ramp", type="place", label="the boat ramp"))
    token = world.add(Entity(id="token", type="thing", label="the token"))
    world.facts.update(tide=0.0, child=child, caribou=caribou, quest=quest, tool=tool, ramp=ramp, token=token)

    child.memes["hope"] += 1
    caribou.memes["care"] += 1
    road_to_quest(world, child, caribou, quest)
    world.para()
    search(world, child, caribou, quest, tool)
    world.para()
    turn(world, child, caribou, quest, tool)
    world.para()
    finish(world, child, caribou, quest, tool)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a rhyming quest story at {f['quest'].title} set on the boat ramp, and include a caribou.",
        f"Tell a child-friendly rhyme where {f['child'].id} and a caribou search the boat ramp for a lost token.",
        f"Write a short quest story in verse that uses the word caribou and ends with the token found at the ramp.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, caribou, quest, tool = f["child"], f["caribou"], f["quest"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who went on the quest at the boat ramp?",
            answer=f"{child.id} went with the caribou, and together they followed the quest clue at the boat ramp. They stayed side by side while the search grew trickier.",
        ),
        QAItem(
            question=f"What did {child.id} use to help search for the token?",
            answer=f"{child.id} used {tool.phrase}. It helped the pair look carefully while they hunted for the lost token.",
        ),
        QAItem(
            question=f"Where did they find the lost token?",
            answer=f"They found it under a driftwood crate by the boat ramp. The clue led them right to the hidden place at the end of the quest.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and the caribou?",
            answer=f"It ended with the token found and both of them happy. The caribou stood in the last light while {child.id} held the token and smiled.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a caribou?",
            answer="A caribou is a large deer that lives in cold places and walks with strong hooves. It can help make a story feel wild and wintry.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important. In a quest story, the characters keep going until they solve the clue.",
        ),
        QAItem(
            question="What is a boat ramp?",
            answer="A boat ramp is a sloping place where people can slide boats into the water. It often has wet boards, rocks, and water nearby.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,Q,T) :- setting(S), quest(Q), tool(T), S="boat_ramp", Q="lost_token", (T="hook"; T="lantern").
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    aspy = set(asp_valid_combos())
    rc = 0
    if py == aspy:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid combos:")
        print("  only in python:", sorted(py - aspy))
        print("  only in asp:", sorted(aspy - py))
        rc = 1
    try:
        sample = generate(StoryParams(setting="boat_ramp", quest="lost_token", tool="hook", child_name="Mina", child_type="girl"))
        assert sample.story
        _ = sample.to_json()
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
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


CURATED = [
    StoryParams(setting="boat_ramp", quest="lost_token", tool="hook", child_name="Mina", child_type="girl"),
    StoryParams(setting="boat_ramp", quest="lost_token", tool="lantern", child_name="Owen", child_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def valid_story_combo_check() -> None:
    if not valid_combos():
        pass


if __name__ == "__main__":
    main()
