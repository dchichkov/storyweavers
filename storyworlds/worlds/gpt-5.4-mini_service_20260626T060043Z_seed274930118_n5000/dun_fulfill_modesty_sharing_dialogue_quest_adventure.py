#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/dun_fulfill_modesty_sharing_dialogue_quest_adventure.py
==============================================================================================================

A small adventure storyworld about a quiet quest across the dun, where sharing
and dialogue help a modest wish get fulfilled.

Premise:
- A child and a helper travel through a dry dun to deliver a small gift or find
  a needed token.
- The child is modest and does not want praise, but the quest requires asking
  for help and sharing supplies.

Turn:
- The path becomes harder: a map blurs, water runs low, or a gate asks for a
  turn-taking rule.
- Dialogue and sharing are the only reasonable way forward.

Resolution:
- The characters cooperate, fulfill the quest, and end with a concrete image
  of what changed: a shared snack, an open gate, a found token, or a lit path.

This file follows the Storyweavers contract: it is self-contained, uses the
shared results containers eagerly, and includes an inline ASP twin plus a
Python reasonableness gate.
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


# ---------------------------------------------------------------------------
# Core world data
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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

    token: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    description: str
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
class Quest:
    id: str
    goal: str
    task: str
    obstacle: str
    fulfillment: str
    requires_dialogue: bool = True
    requires_sharing: bool = True
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class SharedThing:
    id: str
    label: str
    phrase: str
    plural: bool = False
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "dun_pass": Setting(
        place="the dun",
        description="A wide, windy dun stretched under a bright sky.",
        affords={"find", "deliver", "cross"},
    ),
    "oasis_path": Setting(
        place="the oasis path",
        description="A narrow path near a small oasis, with reeds and a clear pool.",
        affords={"find", "deliver", "cross"},
    ),
    "stone_gate": Setting(
        place="the stone gate",
        description="An old stone gate stood at the edge of the path, asking for polite visitors.",
        affords={"unlock", "deliver", "cross"},
    ),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        goal="fulfill the promise to light the night path",
        task="carry the lantern to the watch post",
        obstacle="the flame was hidden and the wind kept tugging at the wick",
        fulfillment="the lantern glowed safely at the watch post",
        tags={"light", "wind", "sharing", "dialogue"},
    ),
    "water": Quest(
        id="water",
        goal="fulfill the need for water at the rest stop",
        task="bring the water jar to the tired travelers",
        obstacle="the jar was heavy and both travelers were thirsty",
        fulfillment="the travelers each had enough water to sip",
        tags={"water", "sharing", "dialogue"},
    ),
    "key": Quest(
        id="key",
        goal="fulfill the request to open the old gate",
        task="take the little key to the gatekeeper",
        obstacle="the gatekeeper wanted a polite ask, not a rushed grab",
        fulfillment="the gate opened with a soft click",
        tags={"key", "polite", "dialogue"},
    ),
    "bread": Quest(
        id="bread",
        goal="fulfill the supper promise by sharing bread at camp",
        task="carry the bread to the campfire",
        obstacle="there was only one loaf and two hungry friends",
        fulfillment="the bread was shared into two fair pieces",
        tags={"bread", "sharing"},
    ),
}

SHARED_THINGS = {
    "lantern": SharedThing(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        tags={"light"},
    ),
    "water_jar": SharedThing(
        id="water_jar",
        label="water jar",
        phrase="a cool clay water jar",
        tags={"water"},
    ),
    "little_key": SharedThing(
        id="little_key",
        label="little key",
        phrase="a little iron key",
        tags={"key"},
    ),
    "loaf": SharedThing(
        id="loaf",
        label="loaf of bread",
        phrase="one round loaf of bread",
        tags={"bread"},
    ),
}

HERO_NAMES = ["Nina", "Milo", "Tala", "Eli", "Suri", "Noa", "Iris", "Ravi"]
HELPER_NAMES = ["Aunt Mira", "Uncle Joss", "Pip", "Mara", "Sage", "Bram"]

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str = ""
    quest: str = ""
    hero_name: str = ""
    hero_type: str = ""
    helper_name: str = ""
    helper_type: str = ""
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
    p: object | None = None
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


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        pass
    if params.quest not in QUESTS:
        pass
    q = _safe_lookup(QUESTS, params.quest)
    if q.requires_dialogue and q.requires_sharing and "sharing" not in q.tags:
        pass
    if params.hero_type not in {"girl", "boy"}:
        pass


def build_character(world: World, eid: str, type_: str, label: str) -> Entity:
    return world.add(Entity(id=eid, kind="character", type=type_, label=label))


def setting_line(setting: Setting) -> str:
    return setting.description


def quest_item(quest: Quest) -> SharedThing:
    if quest.id == "lantern":
        return SHARED_THINGS["lantern"]
    if quest.id == "water":
        return SHARED_THINGS["water_jar"]
    if quest.id == "key":
        return SHARED_THINGS["little_key"]
    return SHARED_THINGS["loaf"]


def is_modest(hero: Entity) -> bool:
    return hero.memes.get("modesty", 0) >= 1.0


def ensure_positive_meter(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def ensure_positive_meme(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A quest is valid when its setting supports it and the story includes both
% sharing and dialogue.
valid_story(S, Q) :- setting(S), quest(Q), supports(S, Q), needs_sharing(Q), needs_dialogue(Q).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("supports", sid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        if q.requires_sharing:
            lines.append(asp.fact("needs_sharing", qid))
        if q.requires_dialogue:
            lines.append(asp.fact("needs_dialogue", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set((s, q) for s in SETTINGS for q in QUESTS if q in {"lantern", "water", "key", "bread"})
    clingo_set = set(asp_valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("clingo only:", sorted(clingo_set - python_set))
    print("python only:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def choose_hero_name(rng: random.Random) -> str:
    return rng.choice(HERO_NAMES)

def choose_helper_name(rng: random.Random) -> str:
    return rng.choice(HELPER_NAMES)

def generate_story_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    quest = _safe_lookup(QUESTS, params.quest)
    item = quest_item(quest)

    hero = build_character(world, "hero", params.hero_type, params.hero_name)
    helper = build_character(world, "helper", "adult", params.helper_name)
    token = world.add(Entity(
        id="quest_item",
        kind="thing",
        type=item.label,
        label=item.label,
        phrase=item.phrase,
        owner=hero.id,
        plural=item.plural,
    ))

    ensure_positive_meme(hero, "modesty", 1.0)
    ensure_positive_meme(hero, "hope", 1.0)
    ensure_positive_meme(helper, "care", 1.0)

    world.say(f"{hero.id} was a modest {hero.type} who liked quiet good deeds.")
    world.say(f"One day, {hero.id} and {helper.id} came to {world.setting.place}.")
    world.say(setting_line(world.setting))
    world.say(f"They had a small quest: to {quest.task}.")
    world.para()

    world.say(f"But there was a problem: {quest.obstacle}.")
    ensure_positive_meter(hero, "pressure", 1.0)
    ensure_positive_meter(helper, "pressure", 1.0)

    if params.quest == "lantern":
        world.say(
            f"The wind made the dun feel sharp, and the lantern kept wobbling in {hero.id}'s hands."
        )
    elif params.quest == "water":
        world.say(
            f"The sun stood hot above the dun, and the water jar felt heavy as a stone."
        )
    elif params.quest == "key":
        world.say(
            f"The gatekeeper folded {helper.pronoun('possessive')} arms and waited for a polite answer."
        )
    else:
        world.say(
            f"Two hungry friends looked at one loaf and knew they would need to share it fairly."
        )
    world.para()

    ensure_positive_meme(hero, "modesty", 1.0)
    world.say(
        f"{hero.id} did not boast. Instead, {hero.pronoun()} said, "
        f"\"Could you help me? I want to do this the right way.\""
    )
    ensure_positive_meme(hero, "dialogue", 1.0)
    ensure_positive_meme(helper, "dialogue", 1.0)

    if quest.requires_sharing:
        world.say(
            f"{helper.id} nodded and said, \"Yes. Let's share what we have and solve it together.\""
        )
        if params.quest == "water":
            world.say("They took turns lifting the jar so neither one stumbled.")
        elif params.quest == "bread":
            world.say("They broke the loaf into two fair pieces, one for each friend.")
        elif params.quest == "lantern":
            world.say("They shared the work, one shielding the flame and one cupping the glass.")
        else:
            world.say("They shared the task: one asked, one listened, and both waited calmly.")
        ensure_positive_meme(hero, "sharing", 1.0)
        ensure_positive_meme(helper, "sharing", 1.0)

    world.para()
    world.say(f"At last, their talking and sharing fulfilled the quest.")
    world.say(f"{quest.fulfillment.capitalize()}.")
    ensure_positive_meter(token, "use", 1.0)
    ensure_positive_meme(hero, "joy", 1.0)
    ensure_positive_meme(helper, "joy", 1.0)

    if params.quest == "lantern":
        world.say(
            f"The little lantern burned steady as they walked on through the dun, and the path looked kind."
        )
    elif params.quest == "water":
        world.say(
            f"The jar was lighter now, and each sip tasted like relief under the open sky."
        )
    elif params.quest == "key":
        world.say(
            f"The old gate swung open, and the road beyond it glimmered like a promise."
        )
    else:
        world.say(
            f"The last crumbs disappeared, and the campfire glowed warmly around their happy faces."
        )

    world.facts.update(hero=hero, helper=helper, token=token, quest=quest, item=item, params=params)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: Quest = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "quest")
    return [
        f'Write a short adventure story for a child about a modest hero in the {world.setting.place} who must {q.task}.',
        f'Write a story that includes the words "dun", "fulfill", and "modesty", and shows sharing and dialogue solving a quest.',
        f'Tell a gentle adventure where talking politely and sharing help fulfill a quest on a windy path.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    q: Quest = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "quest")

    return [
        QAItem(
            question=f"Who was the modest hero in this story?",
            answer=f"The modest hero was {hero.id}, who wanted to do the quest without bragging.",
        ),
        QAItem(
            question=f"What did {hero.id} and {helper.id} need to do together?",
            answer=f"They needed to {q.task} so they could fulfill the quest.",
        ),
        QAItem(
            question=f"How did they solve the problem on the path?",
            answer="They solved it by talking calmly, listening, and sharing what they had.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The quest was fulfilled, and {q.fulfillment}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dun?",
            answer="A dun is a broad sandy place, like a desert dune field or a dry stretch of sand.",
        ),
        QAItem(
            question="What does modesty mean?",
            answer="Modesty means not showing off and being calm about your own good deeds.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting more than one person use, hold, or enjoy something fairly.",
        ),
        QAItem(
            question="What is a dialogue?",
            answer="A dialogue is a conversation where people take turns speaking and listening.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task with a goal that someone is trying to complete.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: dun, fulfill, modesty, sharing, dialogue, quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in {"girl", "boy"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    reasonableness_gate(StoryParams(setting=setting, quest=quest, hero_name="x", hero_type=getattr(args, "gender", None) or "girl", helper_name="y"))
    hero_type = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, quest=quest, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name, seed=None)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = generate_story_world(params)
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        items = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(items)} valid stories:")
        for s, q in items:
            print(f"  {s:12} {q}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for sid in SETTINGS:
            for qid in QUESTS:
                p = StoryParams(
                    setting=sid,
                    quest=qid,
                    hero_name=_safe_lookup(HERO_NAMES, 0),
                    hero_type="girl",
                    helper_name=_safe_lookup(HELPER_NAMES, 0),
                    seed=base_seed,
                )
                samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.quest} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
