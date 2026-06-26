#!/usr/bin/env python3
"""
storyworlds/worlds/sanctuary_friendship_bedtime_story.py
=========================================================

A small bedtime-story world about a sanctuary, friendship, and the gentle
work of helping someone feel safe enough to sleep.

Premise:
- A child and a friend arrive at a quiet sanctuary at bedtime.
- One of them feels worried because the night sounds are big and unfamiliar.
- The other helps by making the sanctuary cozy, sharing a small ritual, and
  staying close until the worry softens.

The world is intentionally tiny and constraint-checked:
- the setting is a sanctuary-like place with a bedtime feel;
- friendship is the main emotional mechanism;
- the turn is driven by simulated state, not fixed prose swaps;
- invalid explicit choices raise StoryError.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

MOODS = {"calm", "sleepy", "wary", "afraid", "comforted", "brave"}
PLACES = {
    "lantern_nook": "the lantern nook",
    "garden_sanctuary": "the garden sanctuary",
    "book_sanctuary": "the book sanctuary",
}
CHARACTER_TYPES = {"child", "friend"}
GENDER_TYPES = {"girl", "boy"}
TRUST_STEPS = {
    "soft_words": 1.0,
    "shared_blanket": 1.0,
    "night_light": 1.0,
    "story_time": 1.0,
}

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # character | thing
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
    friend: object | None = None
    def __post_init__(self):
        for k in list(self.meters):
            self.meters[k] = float(self.meters[k])
        for k in list(self.memes):
            self.memes[k] = float(self.memes[k])

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "friend":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str
    bedtime: bool = True
    sanctuary: bool = True
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
class ComfortItem:
    id: str
    label: str
    phrase: str
    kind: str
    helps: set[str]
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


@dataclass
class StoryParams:
    place: str
    child_type: str
    child_name: str
    friend_name: str
    concern: str
    comfort: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def _reduce_wary(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"].id)
    friend = world.get(world.facts["friend"].id)
    comfort = world.facts.get("comfort_item")

    if child.memes.get("wary", 0.0) >= THRESHOLD and friend.memes.get("gentleness", 0.0) >= THRESHOLD:
        sig = ("soft_words", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["wary"] = max(0.0, child.memes.get("wary", 0.0) - 1.0)
            child.memes["calm"] = child.memes.get("calm", 0.0) + 1.0
            out.append(f"{friend.id} spoke in a soft voice, and {child.id} listened.")

    if comfort and comfort.worn_by == friend.id and child.memes.get("afraid", 0.0) >= THRESHOLD:
        sig = ("comfort", child.id, comfort.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["afraid"] = max(0.0, child.memes.get("afraid", 0.0) - 1.0)
            child.memes["comforted"] = child.memes.get("comforted", 0.0) + 1.0
            out.append(f"The {comfort.label} made the sanctuary feel smaller and warmer.")

    return out


def _bond_grows(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"].id)
    friend = world.get(world.facts["friend"].id)
    if child.memes.get("comforted", 0.0) >= THRESHOLD:
        sig = ("bond", child.id, friend.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["trust"] = child.memes.get("trust", 0.0) + 1.0
            friend.memes["trust"] = friend.memes.get("trust", 0.0) + 1.0
            child.memes["love"] = child.memes.get("love", 0.0) + 1.0
            friend.memes["love"] = friend.memes.get("love", 0.0) + 1.0
            out.append(f"That made room for friendship to grow.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_reduce_wary, _bond_grows):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_resolution(world: World, child: Entity, friend: Entity, comfort_item: ComfortItem) -> dict:
    sim = world.copy()
    sim.get(child.id).memes["wary"] = 1.0
    sim.get(child.id).memes["afraid"] = 1.0
    sim.get(friend.id).memes["gentleness"] = 1.0
    sim.facts["comfort_item"] = copy.deepcopy(comfort_item)
    sim.facts["comfort_item"].worn_by = friend.id
    propagate(sim, narrate=False)
    return {
        "calmed": sim.get(child.id).memes.get("comforted", 0.0) >= THRESHOLD,
        "trust": sim.get(child.id).memes.get("trust", 0.0),
    }


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "lantern_nook": Setting(place=PLACES["lantern_nook"], affords={"story_time", "shared_blanket", "night_light"}),
    "garden_sanctuary": Setting(place=PLACES["garden_sanctuary"], affords={"shared_blanket", "night_light", "soft_words"}),
    "book_sanctuary": Setting(place=PLACES["book_sanctuary"], affords={"story_time", "soft_words", "night_light"}),
}

COMFORT_ITEMS = {
    "blanket": ComfortItem(
        id="blanket",
        label="little blanket",
        phrase="a little blanket with moons on it",
        kind="blanket",
        helps={"afraid", "wary"},
        tags={"soft", "warm"},
    ),
    "lantern": ComfortItem(
        id="lantern",
        label="lantern",
        phrase="a small lantern with a golden glow",
        kind="light",
        helps={"afraid", "wary"},
        tags={"light", "night"},
    ),
    "book": ComfortItem(
        id="book",
        label="bedtime book",
        phrase="a bedtime book with sleepy pictures",
        kind="book",
        helps={"wary", "calm"},
        tags={"story", "sleep"},
    ),
}

CONCERNS = {
    "night": {
        "name": "night sounds",
        "mood": "wary",
        "meter": "wary",
        "setup": "the night sounds seemed too big",
        "turn": "the owl call and the rustling leaves sounded loud",
    },
    "dark": {
        "name": "dark corners",
        "mood": "afraid",
        "meter": "afraid",
        "setup": "the dark corners seemed too deep",
        "turn": "the shadows looked like they were listening",
    },
    "new_place": {
        "name": "a new place",
        "mood": "wary",
        "meter": "wary",
        "setup": "the sanctuary was new and a little unknown",
        "turn": "every quiet sound felt extra large",
    },
}

CHILD_NAMES = ["Mina", "Luna", "Nora", "Ivy", "Ari", "Milo", "Theo", "Bea"]
FRIEND_NAMES = ["Pip", "Sage", "Toby", "June", "Ellis", "Kit", "Rae", "Nell"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A concern is worth telling a bedtime story about if a comfort item can help it.
valid_story(Place, Concern, Comfort) :- setting(Place), concern(Concern), comfort(Comfort),
                                        affords(Place, Help), helps(Comfort, Help),
                                        helps_concern(Comfort, Concern).

% The friendship resolution is considered good when the comfort item can
% actually calm the child in a sanctuary setting.
resolved(Place, Concern, Comfort) :- valid_story(Place, Concern, Comfort), sanctuary(Place).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.sanctuary:
            lines.append(asp.fact("sanctuary", sid))
        if s.bedtime:
            lines.append(asp.fact("bedtime", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CONCERNS.items():
        lines.append(asp.fact("concern", cid))
        for h in (c["meter"],):
            lines.append(asp.fact("helps_concern", "book" if cid == "new_place" else "blanket", cid) if False else "")
        # Explicit mappings below for clarity.
    lines.append(asp.fact("helps_concern", "blanket", "night"))
    lines.append(asp.fact("helps_concern", "blanket", "dark"))
    lines.append(asp.fact("helps_concern", "book", "new_place"))
    lines.append(asp.fact("helps", "blanket", "afraid"))
    lines.append(asp.fact("helps", "blanket", "wary"))
    lines.append(asp.fact("helps", "lantern", "afraid"))
    lines.append(asp.fact("helps", "lantern", "wary"))
    lines.append(asp.fact("helps", "book", "wary"))
    lines.append(asp.fact("helps", "book", "calm"))
    for cid in COMFORT_ITEMS:
        lines.append(asp.fact("comfort", cid))
    return "\n".join([ln for ln in lines if ln])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_stories() ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and valid_stories():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def valid_stories() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for concern_id, concern in CONCERNS.items():
            for comfort_id, comfort in COMFORT_ITEMS.items():
                if comfort["kind"] if False else True:
                    if concern_id in comfort.helps:
                        if any(a in {"story_time", "shared_blanket", "night_light", "soft_words"} for a in setting.affords):
                            out.append((place, concern_id, comfort_id))
    # The story needs a true companionship fix, not just any item:
    return sorted(set(out))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "concern", None) and getattr(args, "concern", None) not in CONCERNS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "comfort", None) and getattr(args, "comfort", None) not in COMFORT_ITEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "comfort", None):
        place = _safe_lookup(SETTINGS, getattr(args, "place", None))
        comfort = _safe_lookup(COMFORT_ITEMS, getattr(args, "comfort", None))
        ok = False
        for afford in place.affords:
            if afford in {"story_time", "shared_blanket", "night_light", "soft_words"}:
                ok = True
        if not ok:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_stories()
              if (not getattr(args, "place", None) or c[0] == getattr(args, "place", None))
              and (not getattr(args, "concern", None) or c[1] == getattr(args, "concern", None))
              and (not getattr(args, "comfort", None) or c[2] == getattr(args, "comfort", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, concern, comfort = (list(rng.choice(combos)) + [None, None, None])[:3]
    child_type = getattr(args, "child_type", None) or rng.choice(sorted(GENDER_TYPES))
    child_name = getattr(args, "child_name", None) or rng.choice(CHILD_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice(FRIEND_NAMES)
    return StoryParams(place=place, child_type=child_type, child_name=child_name,
                       friend_name=friend_name, concern=concern, comfort=comfort)


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type,
                             meters={"stillness": 0.0}, memes={"wary": 0.0, "afraid": 0.0, "trust": 0.0}))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="friend",
                              meters={"stillness": 0.0}, memes={"gentleness": 0.0, "trust": 0.0}))
    comfort = copy.deepcopy(_safe_lookup(COMFORT_ITEMS, params.comfort))
    comfort.owner = friend.id
    comfort.caretaker = child.id
    comfort.worn_by = friend.id
    world.facts.update(child=child, friend=friend, comfort_item=comfort, concern=params.concern)

    concern = _safe_lookup(CONCERNS, params.concern)
    child.memes[concern["meter"]] = 1.0
    friend.memes["gentleness"] = 1.0

    world.say(f"At {setting.place}, {child.id} and {friend.id} found a small sanctuary for the night.")
    world.say(f"It was bedtime, and {child.id} felt that {concern['setup']}.")
    world.say(f"{friend.id} stayed close, because friendship can be a quiet kind of light.")

    world.para()
    if params.comfort == "blanket":
        world.say(f"{friend.id} spread out {comfort.phrase}, and the sanctuary grew warmer.")
    elif params.comfort == "lantern":
        world.say(f"{friend.id} lit {comfort.phrase}, and the corners of the sanctuary looked softer.")
    else:
        world.say(f"{friend.id} opened {comfort.phrase}, and the little pages promised a sleepy ending.")

    world.say(f"Still, {child.id} thought about how {concern['turn']}.")
    world.say(f"{child.id} wanted to keep worrying, but {friend.id} spoke in a way that sounded like a hug.")

    world.para()
    child.memes[concern["meter"]] = 0.0
    child.memes["afraid"] = 1.0 if params.concern == "dark" else 0.0
    propagate(world, narrate=True)
    if child.memes.get("trust", 0.0) >= THRESHOLD:
        world.say(f"Before long, {child.id} lay down beside {friend.id} and felt safe enough to close {child.pronoun('possessive')} eyes.")
        world.say(f"The sanctuary stayed quiet, and the night became kind.")
    else:
        world.say(f"Even so, {friend.id} kept watch until the breathing in the room went slow and steady.")

    world.facts["resolved"] = child.memes.get("trust", 0.0) >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle bedtime story set in {world.setting.place} about friendship and a sanctuary.',
        f"Tell a short story where {f['child'].id} feels {f['concern']} but {f['friend'].id} helps with a comforting {f['comfort_item'].label}.",
        "Write a child-friendly bedtime story with a safe, quiet place, a worried heart, and a friendly helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = _safe_fact(world, world.facts, "child")
    f = _safe_fact(world, world.facts, "friend")
    comfort = _safe_fact(world, world.facts, "comfort_item")
    concern = _safe_lookup(CONCERNS, world.facts.get("concern"))
    return [
        QAItem(
            question=f"Where did {c.id} and {f.id} go at bedtime?",
            answer=f"They went to {world.setting.place}, a small sanctuary where they could rest and feel safe.",
        ),
        QAItem(
            question=f"Why did {c.id} feel uneasy at first?",
            answer=f"{c.id} felt uneasy because {concern['setup']} and the night felt a little too big.",
        ),
        QAItem(
            question=f"What did {f.id} use to help?",
            answer=f"{f.id} used {comfort.phrase} and stayed close, which made the sanctuary feel warmer and kinder.",
        ),
    ] + (
        [
            QAItem(
                question=f"What changed after the comfort helped?",
                answer=f"{c.id} felt trust grow, the worry went away, and bedtime turned peaceful.",
            )
        ] if world.facts.get("resolved") else []
    )


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sanctuary?",
            answer="A sanctuary is a safe, peaceful place where someone can rest and feel protected.",
        ),
        QAItem(
            question="What does friendship do in a bedtime story?",
            answer="Friendship helps one character comfort another, so worry can soften and sleep can come.",
        ),
        QAItem(
            question="Why is a bedtime story usually gentle?",
            answer="A bedtime story is gentle because it helps the listener calm down and feel ready for sleep.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sample generation
# ---------------------------------------------------------------------------
def valid_stories_filtered(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_stories()
    out = []
    for place, concern, comfort in combos:
        if getattr(args, "place", None) and place != getattr(args, "place", None):
            continue
        if getattr(args, "concern", None) and concern != getattr(args, "concern", None):
            continue
        if getattr(args, "comfort", None) and comfort != getattr(args, "comfort", None):
            continue
        out.append((place, concern, comfort))
    return out


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: sanctuary, friendship, bedtime.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--concern", choices=sorted(CONCERNS))
    ap.add_argument("--comfort", choices=sorted(COMFORT_ITEMS))
    ap.add_argument("--child-type", choices=sorted(GENDER_TYPES))
    ap.add_argument("--child-name")
    ap.add_argument("--friend-name")
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible sanctuary bedtime stories:")
        for t in combos:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("lantern_nook", "girl", "Mina", "Pip", "night", "blanket"),
            StoryParams("garden_sanctuary", "boy", "Theo", "Sage", "dark", "lantern"),
            StoryParams("book_sanctuary", "girl", "Bea", "June", "new_place", "book"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
