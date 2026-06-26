#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mumble_spear_sound_effects_transformation_ghost_story.py
===============================================================================================================================

A small ghost-story world about a child, a haunted sound, and a careful turn
from fear to understanding.

Seed image:
- A quiet night
- A ghostly mumble in the walls
- A spear-shaped object used as a pointer, not a weapon
- Sound effects that reveal the haunting
- A transformation from spooky to gentle

The story engine models:
- a child with fear and curiosity
- a local ghost with an old, stuck form
- a spear-like brass pointer from a costume box
- sound effects that can be heard, followed, and transformed into meaning

The intended beat:
- setup: the child hears a mumble in the dark house
- tension: the spooky sound seems like a ghost warning
- turn: the child discovers the sound is trapped in the house's old pipes and uses the spear pointer to trace it
- resolution: the ghost transforms into a soft, friendly guide once its sound is answered and understood
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    ghost: object | None = None
    haunt: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
        if "_tags" not in self.__dict__:
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
    place: str = "the old house"
    moonlight: str = "thin moonlight"
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Haunt:
    id: str
    sound: str
    echo: str
    source: str
    fear: str
    reveal: str
    transform_to: str
    keyword: str = "mumble"
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
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
    tip: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_hear(world: World) -> list[str]:
    out: list[str] = []
    child = _safe_fact(world, world.facts, "child")
    haunt = _safe_fact(world, world.facts, "haunt")
    if child.memes.get("listening", 0.0) >= THRESHOLD and haunt.meters.get("sound", 0.0) >= THRESHOLD:
        sig = ("hear", haunt.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] = child.memes.get("fear", 0.0) + 1
            out.append(f"A soft {haunt.sound} leaked through the hall.")
    return out


def _r_trace(world: World) -> list[str]:
    out: list[str] = []
    child = _safe_fact(world, world.facts, "child")
    haunt = _safe_fact(world, world.facts, "haunt")
    tool = _safe_fact(world, world.facts, "tool")
    if child.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if tool.meters.get("pointing", 0.0) < THRESHOLD:
        return out
    sig = ("trace", haunt.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] = max(0.0, child.memes.get("fear", 0.0) - 0.5)
    child.memes["understanding"] = child.memes.get("understanding", 0.0) + 1
    out.append("The brass tip traced the sound to the wall beside the stairs.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    child = _safe_fact(world, world.facts, "child")
    haunt = _safe_fact(world, world.facts, "haunt")
    if child.memes.get("understanding", 0.0) < THRESHOLD:
        return out
    if haunt.meters.get("trapped", 0.0) < THRESHOLD:
        return out
    sig = ("transform", haunt.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    haunt.meters["trapped"] = 0.0
    haunt.meters["gentle"] = 1.0
    haunt.meters["sound"] = 0.0
    haunt.meters["glow"] = 1.0
    out.append("The old mumble softened into a warm little hum.")
    return out


CAUSAL_RULES = [_r_hear, _r_trace, _r_transform]


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule(world)
            if got:
                changed = True
                out.extend(got)
    for line in out:
        world.say(line)
    return out


@dataclass
class StoryParams:
    name: str
    gender: str
    setting: str
    haunt: str
    tool: str
    seed: Optional[int] = None
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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


SETTINGS = {
    "old_house": Setting(place="the old house", moonlight="thin moonlight", affords={"listen", "trace", "transform"}),
}

HAUNTS = {
    "mumble": Haunt(
        id="mumble",
        sound="mumble",
        echo="mumbly echo",
        source="the wall beside the stairs",
        fear="spooky",
        reveal="an old stuck message",
        transform_to="a gentle guide",
        keyword="mumble",
        tags={"mumble", "ghost", "sound"},
    ),
}

TOOLS = {
    "spear": Tool(
        id="spear",
        label="a costume spear",
        phrase="a brass costume spear with a rounded tip",
        tip="rounded tip",
        safe=True,
        tags={"spear", "tool"},
    ),
}

GIRL_NAMES = ["Maya", "Lena", "Nora", "Ivy", "Rose"]
BOY_NAMES = ["Theo", "Eli", "Finn", "Noah", "Ben"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with mumble, spear, sound effects, and transformation.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--haunt", choices=sorted(HAUNTS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
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
    setting = getattr(args, "setting", None) or "old_house"
    haunt = getattr(args, "haunt", None) or "mumble"
    tool = getattr(args, "tool", None) or "spear"
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(name=name, gender=gender, setting=setting, haunt=haunt, tool=tool)


def _make_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost"))
    tool = world.add(Entity(id=params.tool, type="tool", label="costume spear", phrase=_safe_lookup(TOOLS, params.tool).phrase))
    haunt = world.add(Entity(id=params.haunt, type="haunt", label="mumble", phrase="a mumbling sound"))
    child.memes["curiosity"] = 1.0
    child.memes["listening"] = 1.0
    ghost.meters["trapped"] = 1.0
    ghost.meters["sound"] = 1.0
    tool.meters["pointing"] = 0.0
    world.facts.update(child=child, ghost=ghost, tool=tool, haunt=ghost)
    return world


def _narrate(world: World) -> None:
    child = _safe_fact(world, world.facts, "child")
    ghost = _safe_fact(world, world.facts, "ghost")
    tool = _safe_fact(world, world.facts, "tool")
    world.say(f"{child.id} lived in {world.setting.place}, where {world.setting.moonlight} rested on the stairs.")
    world.say(f"At night, {child.id} heard a {ghost.label} in the dark: a little {ghost.id} of sound that went, \"mumble, mumble.\"")
    world.para()
    world.say(f"{child.id} held {tool.phrase} like a lantern pointer and followed the spooky noise.")
    tool.meters["pointing"] = 1.0
    propagate(world)
    world.say(f"The sound felt scary at first, because it sounded like a ghost warning from the walls.")
    world.para()
    world.say(f"{child.id} stayed still and listened harder, then tapped the wall with the spear's rounded tip.")
    propagate(world)
    world.say(f"That was when the old {ghost.id} changed shape.")
    propagate(world)
    if ghost.meters.get("gentle", 0.0) >= THRESHOLD:
        world.say(f"The ghost turned into a gentle guide with a soft glow, and the little house felt safe again.")
    else:
        world.say(f"The house stayed quiet, but the quiet was less lonely than before.")
    world.facts["resolved"] = ghost.meters.get("gentle", 0.0) >= THRESHOLD


def _story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    ghost = _safe_fact(world, world.facts, "ghost")
    tool = _safe_fact(world, world.facts, "tool")
    return [
        QAItem(
            question=f"What did {child.id} hear in the old house at night?",
            answer=f"{child.id} heard a spooky little {ghost.id}: a mumbling sound in the walls.",
        ),
        QAItem(
            question=f"What did {child.id} use to trace the sound?",
            answer=f"{child.id} used {tool.phrase} and pointed it toward the stairs and wall.",
        ),
        QAItem(
            question="What changed after the child understood the sound?",
            answer=f"The trapped ghost transformed from a scary mumble into a gentle, glowing guide.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mumble?",
            answer="A mumble is a soft, unclear sound that can be hard to understand.",
        ),
        QAItem(
            question="Why can a spear be safe in a costume box?",
            answer="A costume spear can be safe when it has a rounded tip and is used for pointing, not for hurting.",
        ),
        QAItem(
            question="What does transformation mean in a story?",
            answer="Transformation means something changes into a new form or becomes different in an important way.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    _narrate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a child-friendly ghost story about a mumble in an old house and a spear used to trace the sound.",
            "Tell a gentle spooky story where a ghostly noise transforms after a child follows it with a costume spear.",
            "Write a short ghost story with sound effects, a careful search, and a friendly transformation.",
        ],
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Maya", gender="girl", setting="old_house", haunt="mumble", tool="spear"),
    StoryParams(name="Theo", gender="boy", setting="old_house", haunt="mumble", tool="spear"),
]


ASP_RULES = r"""
#show valid/3.
valid(P,H,T) :- setting(P), haunt(H), tool(T), compatible(H,T), safe_setting(P).
compatible(mumble,spear).
safe_setting(old_house).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for hid in HAUNTS:
        lines.append(asp.fact("haunt", hid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.append(asp.fact("compatible", "mumble", "spear"))
    lines.append(asp.fact("safe_setting", "old_house"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {("old_house", "mumble", "spear")}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combo).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


def resolve_reasonable(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
        return samples
    seen: set[str] = set()
    i = 0
    while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
        params = resolve_reasonable(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story not in seen:
            seen.add(sample.story)
            samples.append(sample)
        i += 1
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} compatible stories:")
        for item in vals:
            print(" ", item)
        return

    samples = build_samples(args)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
