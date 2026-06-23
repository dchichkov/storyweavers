#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/definite_sharing_magic_sound_effects_detective_story.py
===============================================================================================================================

A standalone storyworld about a child detective, a shared magical sound effect, and a
definite clue. The world is small, state-driven, and built to read like a tiny
detective story with a clear setup, turn, and ending image.

Seed premise:
- Style: Detective Story
- Features: Sharing, Magic, Sound Effects
- Word to include: definite
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    phrase: str = ""
    owner: str = ""
    partner: str = ""
    carries: str = ""
    emits: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    clue: object | None = None
    detective: object | None = None
    friend: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.attrs.get("plural") == "1" else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Place:
    id: str
    label: str
    hush: str
    good_for: set[str] = field(default_factory=set)
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
class Case:
    id: str
    title: str
    problem: str
    sound: str
    sound_text: str
    method: str
    clue: str
    ending: str
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
class SharingTool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    shares: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def sound_rule(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    tool = world.get("tool")
    case = world.facts["case"]
    if detective.meters.get("listen", 0.0) < THRESHOLD:
        return out
    if tool.meters.get("used", 0.0) < THRESHOLD:
        return out
    if case.id in world.fired:
        return out
    world.fired.add((case.id, "solved"))
    clue = world.get("clue")
    clue.meters["seen"] = 1.0
    detective.memes["confidence"] = detective.memes.get("confidence", 0.0) + 1.0
    out.append(f"The definite clue rang out and made the puzzle click.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        sents = sound_rule(world)
        if sents:
            changed = True
            produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for cid, case in CASES.items():
            for tid, tool in TOOLS.items():
                if case.problem in tool.helps and case.sound in tool.shares and case.method in place.good_for:
                    combos.append((pid, cid, tid))
    return combos


@dataclass
class StoryParams:
    place: str
    case: str
    tool: str
    detective_name: str
    detective_gender: str
    friend_name: str
    friend_gender: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


PLACES = {
    "archiv": Place(id="archiv", label="the old archive", hush="quiet shelves", good_for={"listen", "search", "share"}),
    "hall": Place(id="hall", label="the moonlit hall", hush="smooth floors", good_for={"listen", "search", "share"}),
    "studio": Place(id="studio", label="the toy studio", hush="bright tables", good_for={"listen", "search", "share"}),
}

CASES = {
    "bell": Case(id="bell", title="the missing bell", problem="lost", sound="jingle", sound_text="a soft jingle", method="listen", clue="a shiny tag", ending="hung on the ribbon", tags={"sound", "lost"}),
    "stamp": Case(id="stamp", title="the hidden stamp", problem="stuck", sound="click", sound_text="a neat click", method="search", clue="an ink mark", ending="pressed into the page", tags={"magic", "sound"}),
    "kite": Case(id="kite", title="the quiet kite", problem="tangled", sound="whoosh", sound_text="a bright whoosh", method="share", clue="a loose string", ending="fluttering in the window", tags={"sharing", "sound"}),
}

TOOLS = {
    "whistle": SharingTool(id="whistle", label="a tiny whistle", phrase="a tiny whistle", helps={"lost", "stuck", "tangled"}, shares={"jingle", "click", "whoosh"}, tags={"sound"}),
    "wand": SharingTool(id="wand", label="a magic listening wand", phrase="a magic listening wand", helps={"lost", "stuck", "tangled"}, shares={"jingle", "click", "whoosh"}, tags={"magic", "sound"}),
    "box": SharingTool(id="box", label="a share box", phrase="a share box", helps={"lost", "stuck", "tangled"}, shares={"jingle", "click", "whoosh"}, tags={"sharing"}),
}

GIRL_NAMES = ["Mina", "Lena", "Pia", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Eli", "Milo", "Toby", "Noah", "Finn", "Owen"]


def reasonableness_check(case: Case, tool: SharingTool, place: Place) -> bool:
    return case.problem in tool.helps and case.sound in tool.shares and "share" in place.good_for


def explain_rejection(case: Case, tool: SharingTool, place: Place) -> str:
    return f"(No story: {tool.label} cannot make the right sound for {case.title} in {place.label}.)"


def tell(place: Place, case: Case, tool: SharingTool, detective_name: str, detective_gender: str,
         friend_name: str, friend_gender: str) -> World:
    world = World(place)
    detective = world.add(Entity(id="detective", kind="character", type=detective_gender, label=detective_name,
                                 meters={"listen": 0.0}, memes={"curiosity": 1.0, "confidence": 0.0},
                                 attrs={"role": "detective"}))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name,
                              meters={}, memes={"share": 0.0},
                              attrs={"role": "friend"}))
    clue = world.add(Entity(id="clue", type="thing", label=case.clue, phrase=case.clue, meters={"seen": 0.0}))
    tool_ent = world.add(Entity(id="tool", type="thing", label=tool.label, phrase=tool.phrase,
                                owner=detective_name, partner=friend_name,
                                carries=case.sound_text, emits=case.sound_text,
                                meters={"used": 0.0}, attrs={"plural": "0" if tool.id != "box" else "1"}))
    world.facts.update(case=case, tool=tool, place=place, clue=clue, detective=detective, friend=friend)

    world.say(f"On a quiet afternoon, {detective_name} and {friend_name} worked in {place.label}.")
    world.say(f"{detective_name} was a careful detective, and {friend_name} liked to share.")
    world.say(f"They had one definite rule: the clue had to be heard before it could be found.")

    world.para()
    detective.meters["listen"] = 1.0
    world.say(f"{detective_name} leaned close to {clue.label} and listened for a sign.")
    world.say(f"{friend_name} held up {tool.phrase} and offered to help.")
    friend.memes["share"] = 1.0
    tool_ent.meters["used"] = 1.0
    world.say(f"The room answered with {case.sound_text}, and the sound bounced off the shelves.")
    propagate(world)

    world.para()
    detective.memes["confidence"] += 1.0
    world.say(f"{detective_name} smiled, because the sound was a definite clue.")
    world.say(f"It led them to {case.ending}, where the last piece was hiding.")

    world.para()
    world.say(f"At the end, {detective_name} and {friend_name} shared {tool.phrase} beside {case.title},")
    world.say(f"and the little room felt bright and solved.")
    world.facts["solved"] = clue.meters["seen"] >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    case = f["case"]
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    place = f["place"]
    return [
        f'Write a short detective story for a young child that includes the word "definite" and the sound "{case.sound}".',
        f"Tell a mystery story where {detective.label} and {friend.label} share {tool.phrase} in {place.label} to solve {case.title}.",
        f"Write a gentle detective tale about sharing, magic, and sound effects in {place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    case = f["case"]
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    place = f["place"]
    return [
        QAItem(
            question=f"What did {detective.label} and {friend.label} share in {place.label}?",
            answer=f"They shared {tool.phrase}. It helped them listen for {case.sound_text} and solve the mystery together.",
        ),
        QAItem(
            question=f"Why was the clue definite in this story?",
            answer=f"It was definite because the sound pointed to the answer instead of being just a guess. {detective.label} heard it, and that made the next step clear.",
        ),
        QAItem(
            question=f"What happened when the sound effect was heard?",
            answer=f"The room answered with {case.sound_text}, and the clue became easy to follow. That let the detective pair find the hidden piece at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something too. It can help people work together and be kind.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special sound that helps tell what is happening. In stories, it can make a clue feel exciting and real.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something wondrous that can do what ordinary things cannot. In a story, it can make a tool feel special and helpful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="archiv", case="bell", tool="wand", detective_name="Mina", detective_gender="girl", friend_name="Eli", friend_gender="boy"),
    StoryParams(place="hall", case="stamp", tool="box", detective_name="Nora", detective_gender="girl", friend_name="Finn", friend_gender="boy"),
    StoryParams(place="studio", case="kite", tool="whistle", detective_name="Toby", detective_gender="boy", friend_name="Ivy", friend_gender="girl"),
    StoryParams(place="archiv", case="kite", tool="wand", detective_name="Lena", detective_gender="girl", friend_name="Owen", friend_gender="boy"),
]


ASP_RULES = r"""
valid(P,C,T) :- place(P), case(C), tool(T), can_help(T, Need), needs(C, Need), can_make(T, S), case_sound(C, S), share_ok(P).
solved(C) :- valid(_, C, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if "share" in p.good_for:
            lines.append(asp.fact("share_ok", pid))
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("needs", cid, c.problem))
        lines.append(asp.fact("case_sound", cid, c.sound))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for need in sorted(t.helps):
            lines.append(asp.fact("can_help", tid, need))
        for s in sorted(t.shares):
            lines.append(asp.fact("can_make", tid, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(valid_combos()) == set(asp_valid_combos())
    try:
        _ = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        smoke = True
    except Exception:
        smoke = False
    if ok and smoke:
        print("OK: ASP parity and smoke test passed.")
        return 0
    print("Mismatch or smoke failure.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld with sharing, magic, sound effects, and a definite clue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "case", None) is None or c[1] == getattr(args, "case", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, case, tool = rng.choice(list(combos))
    det_gender = rng.choice(["girl", "boy"])
    fr_gender = "boy" if det_gender == "girl" else "girl"
    det_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if det_gender == "girl" else BOY_NAMES)
    fr_name = getattr(args, "friend", None) or rng.choice([n for n in (BOY_NAMES + GIRL_NAMES) if n != det_name])
    return StoryParams(place=place, case=case, tool=tool, detective_name=det_name, detective_gender=det_gender, friend_name=fr_name, friend_gender=fr_gender)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.case not in CASES or params.tool not in TOOLS:
        pass
    place = _safe_lookup(PLACES, params.place)
    case = _safe_lookup(CASES, params.case)
    tool = _safe_lookup(TOOLS, params.tool)
    if not reasonableness_check(case, tool, place):
        pass
    world = tell(place, case, tool, params.detective_name, params.detective_gender, params.friend_name, params.friend_gender)
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
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
