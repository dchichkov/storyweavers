#!/usr/bin/env python3
"""
A standalone story world for a small ghost-story domain with magic, sound effects,
and teamwork.

Premise:
- A child-friendly ghost story in a cozy spooky place.
- A ghostly problem makes eerie sounds and needs a team effort.
- Magic is used carefully, with an ending that proves something stayed intact.

This world keeps the story grounded in state changes:
- the haunted object can become rattly, dim, or quiet
- teamwork raises courage and lowers fear
- magic can restore an intact state
- sound effects are part of the world and the prose

The seed story inspiration is a gentle ghost tale where a small group works
together to help a shy ghost and fix a spooky noise without breaking anything.
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
            keys = [upper, upper + "S", upper + "ES"]
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    ghost: object | None = None
    helper: object | None = None
    object_: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "aunt"}
        masculine = {"boy", "man", "father", "uncle"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
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
class Place:
    name: str
    spooky: bool = True
    magic_friendly: bool = True
    sound_source: str = "the attic"
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
    sound: str
    makes_intact: bool = False
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
class StoryParams:
    place: str
    ghost_kind: str
    tool: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = [[]]
        clone.facts = dict(self.facts)
        return clone


def noun_for_ghost(kind: str) -> str:
    return {
        "shy": "shy ghost",
        "tiny": "tiny ghost",
        "glowing": "glowing ghost",
        "sleepy": "sleepy ghost",
    }.get(kind, "ghost")


def tool_for_magic(tool: Tool) -> str:
    return {
        "bell": "a silver bell",
        "lantern": "a lantern of blue light",
        "whisper": "a whisper spell",
        "ribbon": "a ribbon charm",
    }[tool.id]


def world_detail(place: Place) -> str:
    if place.name == "attic":
        return "Dust motes drifted through the attic beams, and the floorboards gave little squeaks."
    if place.name == "garden":
        return "The garden was dark and soft, with moonlight on the leaves and a fence that creaked."
    if place.name == "hall":
        return "The old hall was long and quiet, with echoing corners and a staircase that sighed."
    return "The room felt cozy and spooky at the same time, like a story waiting to be told."


def make_sound(tool: Tool) -> str:
    return tool.sound


def _r_magic_restore(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters.get("rattly", 0.0) < THRESHOLD:
            continue
        if ent.meters.get("magic", 0.0) < THRESHOLD:
            continue
        sig = ("restore", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["rattly"] = 0.0
        ent.meters["intact"] = 1.0
        out.append(f"The magic settled the rattling and kept {ent.label} intact.")
    return out


def _r_teamwork_calm(world: World) -> list[str]:
    out: list[str] = []
    team = [e for e in world.entities.values() if e.kind == "character"]
    if not team:
        return out
    if sum(e.memes.get("teamwork", 0.0) for e in team) < THRESHOLD * 2:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in team:
        e.memes["fear"] = max(0.0, e.memes.get("fear", 0.0) - 0.5)
        e.memes["courage"] = e.memes.get("courage", 0.0) + 0.5
    out.append("Working together made everyone feel braver.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_magic_restore, _r_teamwork_calm):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACE_REGISTRY = {
    "attic": Place(name="attic", spooky=True, magic_friendly=True, sound_source="the attic"),
    "hall": Place(name="hall", spooky=True, magic_friendly=True, sound_source="the hallway"),
    "garden": Place(name="garden", spooky=True, magic_friendly=True, sound_source="the old garden shed"),
}

TOOLS = {
    "bell": Tool(id="bell", label="silver bell", phrase="a silver bell", effect="magic", sound="ding-ding", makes_intact=True),
    "lantern": Tool(id="lantern", label="blue lantern", phrase="a lantern with blue light", effect="magic", sound="whoooom", makes_intact=True),
    "whisper": Tool(id="whisper", label="whisper spell", phrase="a whisper spell", effect="magic", sound="hush-hush", makes_intact=True),
    "ribbon": Tool(id="ribbon", label="glow ribbon", phrase="a glowing ribbon charm", effect="magic", sound="fwap-fwap", makes_intact=True),
}

GHOST_KINDS = ["shy", "tiny", "glowing", "sleepy"]
CHILD_NAMES = ["Mina", "Leo", "Nora", "Theo", "Iris", "Finn", "Ava", "Sam"]
HELPER_NAMES = ["Aunt June", "Uncle Pip", "Mara", "Toby", "Mr. Bell", "Mrs. Vale"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACE_REGISTRY:
        for ghost_kind in GHOST_KINDS:
            for tool in TOOLS:
                combos.append((place, ghost_kind, tool))
    return combos


def explain_rejection(place: str, ghost_kind: str, tool: str) -> str:
    return f"(No story: the ghost story world accepts only known place, ghost, and magic tool choices; got {place}, {ghost_kind}, {tool}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world with magic, sound effects, and teamwork.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--ghost-kind", choices=GHOST_KINDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["woman", "man"])
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
    if getattr(args, "place", None) and getattr(args, "ghost_kind", None) and getattr(args, "tool", None):
        if (getattr(args, "place", None), getattr(args, "ghost_kind", None), getattr(args, "tool", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(PLACE_REGISTRY))
    ghost_kind = getattr(args, "ghost_kind", None) or rng.choice(GHOST_KINDS)
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "child_name", None) or rng.choice(CHILD_NAMES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(["woman", "man"])
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    return StoryParams(
        place=place,
        ghost_kind=ghost_kind,
        tool=tool,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def tell(params: StoryParams) -> World:
    place = PLACE_REGISTRY[params.place]
    tool = _safe_lookup(TOOLS, params.tool)
    world = World(place)

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, meters={"fear": 0.0}, memes={"teamwork": 0.0, "courage": 0.0}))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, meters={"fear": 0.0}, memes={"teamwork": 0.0, "courage": 0.0}))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=f"a {noun_for_ghost(params.ghost_kind)}", meters={"rattly": 0.0, "magic": 0.0, "intact": 0.0}, memes={"lonely": 0.0, "hope": 0.0}))
    object_ = world.add(Entity(id="lantern", type="thing", label="lantern", phrase="an old lantern", meters={"rattly": 1.0, "intact": 0.0}))

    world.say(f"{child.id} and {helper.id} came to the {place.name} after supper.")
    world.say(f"Inside, {world_detail(place)}")
    world.say(f"They heard {make_sound(tool)} from {place.sound_source}, and then they saw {ghost.label} by the lantern.")
    world.say(f"The little ghost looked lonely, not mean, just lost in the dark.")

    world.para()
    child.memes["teamwork"] += 1.0
    helper.memes["teamwork"] += 1.0
    child.memes["fear"] += 0.5
    helper.memes["fear"] += 0.5
    ghost.meters["rattly"] += 1.0
    world.say(f"{child.id} held up {tool_for_magic(tool)}, and {helper.id} said they could help together.")
    world.say(f"{make_sound(tool).capitalize()} went the tool, and the spooky room answered with a soft echo.")

    ghost.meters["magic"] += 1.0
    if tool.makes_intact:
        object_.meters["magic"] += 1.0
    propagate(world, narrate=True)

    world.para()
    child.memes["teamwork"] += 1.0
    helper.memes["teamwork"] += 1.0
    world.say(f"Then the three of them worked as a team.")
    if ghost.meters.get("intact", 0.0) >= THRESHOLD:
        world.say(f"The lantern stayed intact, the rattling stopped, and the ghost gave a bright little grin.")
    else:
        world.say(f"The lantern stopped wobbling, and the ghost became calm and clear in the glow.")
    world.say(f"At the end, the {place.name} was still spooky, but it felt friendly now, like it was keeping a secret.")

    world.facts.update(
        child=child,
        helper=helper,
        ghost=ghost,
        object=object_,
        place=place,
        tool=tool,
        ghost_kind=params.ghost_kind,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story for a young child that includes the sound "{(f.get("tool") or next(iter(TOOLS.values()))).sound}".',
        f"Tell a spooky-but-kind story where {f['child'].id} and {f['helper'].id} use magic teamwork to help {f['ghost'].label}.",
        f"Write a short ghost story set in the {f['place'].name} that ends with something staying intact.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    ghost = _safe_fact(world, f, "ghost")
    place = _safe_fact(world, f, "place")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who went to the {place.name} to help the ghost?",
            answer=f"{child.id} and {helper.id} went there together, and they stayed calm enough to help the ghost.",
        ),
        QAItem(
            question=f"What sound did the magic tool make in the spooky room?",
            answer=f"The tool made a {tool.sound} sound, which fit the ghost story's echoing room.",
        ),
        QAItem(
            question=f"What did the children use to help {ghost.label}?",
            answer=f"They used {tool.phrase} and worked as a team, so the ghost could feel safe and the room could settle down.",
        ),
        QAItem(
            question=f"What stayed intact at the end?",
            answer="The lantern stayed intact, so the story ended with the spooky place calm and nothing broken.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work together to do something that is hard to do alone.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special power in a story that can do surprising things, like glow, whisper, or restore something safely.",
        ),
        QAItem(
            question="Why do sound effects matter in a ghost story?",
            answer="Sound effects help the story feel spooky or exciting, like a creaky floor, a hush, or a dinging bell.",
        ),
    ]


ASP_RULES = r"""
place(attic). place(hall). place(garden).
ghost_kind(shy). ghost_kind(tiny). ghost_kind(glowing). ghost_kind(sleepy).
tool(bell). tool(lantern). tool(whisper). tool(ribbon).

can_story(P,G,T) :- place(P), ghost_kind(G), tool(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACE_REGISTRY:
        lines.append(asp.fact("place", p))
    for g in GHOST_KINDS:
        lines.append(asp.fact("ghost_kind", g))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_story/3."))
    return sorted(set(asp.atoms(model, "can_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in ASP:", sorted(cl - py))
    return 1


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(place="attic", ghost_kind="shy", tool="bell", child_name="Mina", child_type="girl", helper_name="Aunt June", helper_type="woman"),
    StoryParams(place="hall", ghost_kind="tiny", tool="whisper", child_name="Leo", child_type="boy", helper_name="Uncle Pip", helper_type="man"),
    StoryParams(place="garden", ghost_kind="glowing", tool="lantern", child_name="Nora", child_type="girl", helper_name="Mara", helper_type="woman"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show can_story/3."))
        return
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name} and {p.helper_name} in the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
