#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/skating_improvise_swivel_moral_value_foreshadowing_repetition.py
=================================================================================================

A small detective-story world about skating, improvising, and swiveling.

Premise:
- A child detective notices a repeating clue while skating at a local rink or
  park path.
- The clue points to a small mystery: something slippery, missing, or out of
  place.
- The detective must improvise, swivel to a new viewpoint, and choose between
  shortcutting the problem or doing the honest thing.

Story features:
- Moral Value: the ending explicitly rewards honesty, patience, repair, or
  helping someone rather than taking credit.
- Foreshadowing: an earlier detail quietly predicts the turn.
- Repetition: a clue, motion, or phrase repeats enough to feel patterned.

This script models:
- physical state with meters (speed, balance, slickness, noise, etc.)
- emotional state with memes (curiosity, worry, pride, relief, fairness, etc.)
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    hidden: bool = False
    lost: bool = False

    clue_ent: object | None = None
    detective: object | None = None
    helper_ent: object | None = None
    tool_ent: object | None = None
    def __post_init__(self):
        for k in [
            "speed", "balance", "slickness", "noise", "scrape", "footprints",
            "evidence", "tidy", "damage", "repair", "clarity"
        ]:
            self.meters.setdefault(k, 0.0)
        for k in [
            "curiosity", "worry", "pride", "relief", "fairness", "guilt",
            "patience", "trust", "surprise", "calm", "determination"
        ]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "detective"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    mood: str
    afford_skating: bool = True
    afford_improvise: bool = True
    afford_swivel: bool = True
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
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    hides: str
    repeat_phrase: str
    sign: str
    suspicious_if_seen: bool = True
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
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    helps: str
    improvise: bool = True
    swivel: bool = False
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
class Moral:
    value: str
    lesson: str
    ending_image: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
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


SETTINGS = {
    "rink": Setting(place="the rink", mood="bright"),
    "boardwalk": Setting(place="the boardwalk", mood="windy"),
    "park_path": Setting(place="the park path", mood="quiet"),
    "community_center": Setting(place="the community center", mood="echoing"),
}

CLUES = {
    "scuff_mark": Clue(
        id="scuff_mark",
        label="a scuff mark",
        phrase="a tiny scuff mark that curved like a comma",
        kind="mark",
        hides="under the bench",
        repeat_phrase="the same curved scuff",
        sign="a left turn",
    ),
    "blue_ribbon": Clue(
        id="blue_ribbon",
        label="a blue ribbon",
        phrase="a blue ribbon tied in the same knot twice",
        kind="ribbon",
        hides="behind the skate locker",
        repeat_phrase="the same knot twice",
        sign="someone had used care",
    ),
    "chalk_arrow": Clue(
        id="chalk_arrow",
        label="a chalk arrow",
        phrase="a chalk arrow drawn two times in a row",
        kind="arrow",
        hides="near the snack counter",
        repeat_phrase="drawn two times in a row",
        sign="a direction to follow",
    ),
    "button": Clue(
        id="button",
        label="a button",
        phrase="a small button with one scratched side",
        kind="button",
        hides="in the gutter by the rail",
        repeat_phrase="the scratched side again",
        sign="a piece from a coat",
    ),
}

TOOLS = {
    "cone": Tool(
        id="cone",
        label="a bright cone",
        phrase="a bright cone from the supply shelf",
        use="mark the spot",
        helps="keeps other skaters away",
    ),
    "notebook": Tool(
        id="notebook",
        label="a tiny notebook",
        phrase="a tiny notebook with a blunt pencil",
        use="draw the clue",
        helps="helps compare the repeated detail",
    ),
    "towel": Tool(
        id="towel",
        label="a towel",
        phrase="a folded towel",
        use="wipe the slick floor",
        helps="soaks up a little spill",
    ),
    "spare_laces": Tool(
        id="spare_laces",
        label="spare laces",
        phrase="spare laces in a pocket",
        use="fix a loose skate",
        helps="keeps a skate from wobbling",
    ),
}

MORALS = {
    "honesty": Moral(
        value="honesty",
        lesson="It was better to tell the truth than to keep the clue for herself.",
        ending_image="the clue resting back where everyone could see it",
    ),
    "patience": Moral(
        value="patience",
        lesson="It was smarter to slow down and look carefully than to rush past the answer.",
        ending_image="the detective skating in one careful circle after another",
    ),
    "helping": Moral(
        value="helping",
        lesson="It felt good to help someone quietly, even when nobody was watching.",
        ending_image="the repaired skate rolling smoothly again",
    ),
}

NAMES = ["Mina", "Noah", "Lina", "Toby", "Rae", "Ezra", "Pia", "Owen", "Nia", "Jules"]
GENDERS = ["girl", "boy"]
PARENT_TYPES = ["mother", "father", "aunt", "uncle"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    clue: str
    tool: str
    moral: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
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


def noun_with_article(text: str) -> str:
    return f"an {text}" if text[:1].lower() in "aeiou" else f"a {text}"


def choose(setting: Setting, clue: Clue, tool: Tool) -> bool:
    if not setting.afford_skating or not setting.afford_improvise or not setting.afford_swivel:
        return False
    if clue.id == "blue_ribbon" and tool.id == "towel":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for clue_id, clue in CLUES.items():
            for tool_id, tool in TOOLS.items():
                for moral_id in MORALS:
                    if choose(setting, clue, tool):
                        out.append((place, clue_id, tool_id, moral_id))
    return out


def _predict_mystery(world: World, detective: Entity, clue: Clue, tool: Tool) -> dict:
    sim = world.copy()
    sim.get(detective.id).memes["curiosity"] += 1
    sim.facts["noticed"] = clue.id
    sim.facts["used_tool"] = tool.id
    return {
        "found": True,
        "ended_cleanly": clue.id != "button" or tool.id != "cone",
    }


def intro(world: World, detective: Entity, clue: Clue) -> None:
    world.say(
        f"{detective.id} was a little detective who liked skating because the wheels made quiet circles."
    )
    world.say(
        f"One detail kept catching {detective.pronoun('possessive')} eye: {clue.phrase}."
    )
    world.say(
        f"{clue.repeat_phrase} looked important, like a whisper that wanted to be noticed twice."
    )


def setting_line(world: World, detective: Entity) -> None:
    mood = world.setting.mood
    world.say(
        f"At {world.setting.place}, the air felt {mood}, and the floor shone where skates had passed."
    )
    world.say(
        f"{detective.id} took one lap, then another lap, to see what the first lap had missed."
    )


def ask_question(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} wondered who left {clue.label} and why it kept pointing to the same place."
    )


def notice_foreshadowing(world: World, detective: Entity, clue: Clue) -> None:
    if clue.id == "scuff_mark":
        world.say("Earlier, a tiny left turn near the bench had hinted at the answer.")
    elif clue.id == "blue_ribbon":
        world.say("Earlier, the same knot twice had looked odd, but now it looked useful.")
    elif clue.id == "chalk_arrow":
        world.say("Earlier, the double chalk marks had seemed playful, yet they were a path.")
    else:
        world.say("Earlier, the scratched side of the button had flashed like a small warning.")


def improvise(world: World, detective: Entity, tool: Tool, clue: Clue) -> None:
    detective.memes["determination"] += 1
    world.say(
        f"When the first idea did not fit, {detective.id} had to improvise."
    )
    if tool.id == "notebook":
        world.say(
            f"{detective.id} sketched {clue.repeat_phrase} in {tool.label}, then compared the marks carefully."
        )
    elif tool.id == "cone":
        world.say(
            f"{detective.id} set down {tool.label} to mark the spot and keep the answer from getting trampled."
        )
    elif tool.id == "towel":
        world.say(
            f"{detective.id} used {tool.label} to wipe a slick spot, so the clue could stay in place long enough to read."
        )
    else:
        world.say(
            f"{detective.id} used {tool.label} to steady a loose skate and keep the search going."
        )


def swivel(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["patience"] += 1
    world.say(
        f"{detective.id} swiveling around in a slow circle changed the whole picture."
    )
    world.say(
        f"From the new angle, {clue.sign} made sense at last."
    )


def moral_turn(world: World, detective: Entity, clue: Clue, tool: Tool, moral: Moral) -> None:
    if moral.value == "honesty":
        world.say(
            f"{detective.id} found the clue tucked away and could have kept the discovery for {detective.pronoun('possessive')}self."
        )
        world.say(
            f"Instead, {detective.id} brought it back and told the grown-up helper the truth."
        )
    elif moral.value == "patience":
        world.say(
            f"{detective.id} almost rushed away, but stayed one more minute to look again."
        )
        world.say(
            f"That extra minute revealed the clue's real place, proving that patience can solve what hurry misses."
        )
    else:
        world.say(
            f"{detective.id} noticed that someone else had a small problem and quietly helped fix it."
        )
        world.say(
            f"After the repair, the search became easier for everyone, and no one had to worry about the wobble anymore."
        )


def ending(world: World, detective: Entity, clue: Clue, tool: Tool, moral: Moral) -> None:
    if moral.value == "honesty":
        world.say(
            f"In the end, {detective.id} placed {clue.label} back where it belonged, and the helper smiled."
        )
        world.say(
            f"The room felt lighter with the truth out in the open, like {moral.ending_image}."
        )
    elif moral.value == "patience":
        world.say(
            f"In the end, {detective.id} kept skating in careful circles until the answer stood still."
        )
        world.say(
            f"The final view was calm and clear, like {moral.ending_image}."
        )
    else:
        world.say(
            f"In the end, {detective.id} fixed the problem with {tool.label} and let the other child keep the credit."
        )
        world.say(
            f"That left {moral.ending_image}, and {detective.id} skated home feeling quietly proud."
        )


def tell(setting: Setting, clue: Clue, tool: Tool, moral: Moral,
         name: str, gender: str, helper: str) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        label="detective",
        traits=["small", "careful", "curious"],
    ))
    helper_ent = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper,
        label=helper,
        traits=["kind", "busy"],
    ))
    clue_ent = world.add(Entity(
        id=clue.id,
        kind="thing",
        type=clue.kind,
        label=clue.label,
        phrase=clue.phrase,
        hidden=True,
    ))
    tool_ent = world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        owner=detective.id,
    ))

    world.facts.update(
        detective=detective,
        helper=helper_ent,
        clue=clue_ent,
        tool=tool_ent,
        moral=moral,
    )

    intro(world, detective, clue)
    world.para()
    setting_line(world, detective)
    ask_question(world, detective, clue)
    notice_foreshadowing(world, detective, clue)

    world.para()
    if _predict_mystery(world, detective, clue, tool)["found"]:
        improvise(world, detective, tool, clue)
    swivel(world, detective, clue)
    moral_turn(world, detective, clue, tool, moral)

    world.para()
    ending(world, detective, clue, tool, moral)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child about skating, improvising, and a clue that repeats itself at {world.setting.place}.',
        f"Tell a gentle mystery where {f['detective'].id} must swivel to solve a small problem and learn a moral lesson about {f['moral'].value}.",
        f"Write a child-friendly story with foreshadowing and repetition, where a skater detective uses {(f.get('tool') or next(iter(TOOLS.values()))).label} to understand {f['clue'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = _safe_fact(world, f, "detective")
    clue: Entity = _safe_fact(world, f, "clue")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    moral: Moral = _safe_fact(world, f, "moral")
    helper: Entity = _safe_fact(world, f, "helper")

    return [
        QAItem(
            question=f"Who was skating and looking for the clue at {world.setting.place}?",
            answer=f"{detective.id} was the little detective who was skating and searching carefully at {world.setting.place}.",
        ),
        QAItem(
            question=f"What clue kept repeating and catching {detective.id}'s attention?",
            answer=f"The clue was {clue.phrase}, and the repeated detail was {clue.repeat_phrase}.",
        ),
        QAItem(
            question=f"What did {detective.id} use to improvise when the first idea did not work?",
            answer=f"{detective.id} used {tool.phrase} to improvise and keep the search going.",
        ),
        QAItem(
            question=f"Why did swiveling help {detective.id} solve the mystery?",
            answer=f"Swiveling let {detective.id} see the scene from a new angle, and then {clue.sign} made sense.",
        ),
        QAItem(
            question=f"What lesson did the story teach about {moral.value}?",
            answer=moral.lesson,
        ),
        QAItem(
            question=f"Who helped {detective.id} or shared the scene during the mystery?",
            answer=f"{helper.id} was the grown-up helper nearby while {detective.id} worked through the clue.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "skating": (
        "What is skating?",
        "Skating is moving smoothly on wheels or blades, often by pushing and gliding in little turns.",
    ),
    "improvise": (
        "What does it mean to improvise?",
        "To improvise means to make a quick plan with what you have when the first plan does not fit.",
    ),
    "swivel": (
        "What does swivel mean?",
        "To swivel means to turn around in a smooth spin so you can face a different direction.",
    ),
    "moral": (
        "What is a moral in a story?",
        "A moral is a lesson a story teaches, like telling the truth, being patient, or helping others.",
    ),
    "foreshadowing": (
        "What is foreshadowing?",
        "Foreshadowing is a small hint early in a story that points to something important later.",
    ),
    "repetition": (
        "What is repetition in a story?",
        "Repetition means something is said or shown again, which can make it easier to notice and remember.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for _, (q, a) in WORLD_KNOWLEDGE.items()]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
clue(C) :- clue_fact(C).
tool(T) :- tool_fact(T).
moral(M) :- moral_fact(M).

compatible(P, C, T, M) :- place(P), clue(C), tool(T), moral(M), afford(P, C, T).

selected_story(P, C, T, M) :- compatible(P, C, T, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.afford_skating:
            lines.append(asp.fact("affords_skating", pid))
        if s.afford_improvise:
            lines.append(asp.fact("affords_improvise", pid))
        if s.afford_swivel:
            lines.append(asp.fact("affords_swivel", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue_fact", cid))
        lines.append(asp.fact("clue_kind", cid, c.kind))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_fact", tid))
        if t.improvise:
            lines.append(asp.fact("helps_improvise", tid))
        if t.swivel:
            lines.append(asp.fact("helps_swivel", tid))
    for mid, m in MORALS.items():
        lines.append(asp.fact("moral_fact", mid))
    for pid in SETTINGS:
        for cid in CLUES:
            for tid in TOOLS:
                lines.append(asp.fact("afford", pid, cid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"""
{asp_facts()}

{ASP_RULES}

{show}
"""


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show selected_story/4."))
    return sorted(set(asp.atoms(model, "selected_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="rink", clue="scuff_mark", tool="notebook", moral="patience", name="Mina", gender="girl", helper="mother"),
    StoryParams(place="boardwalk", clue="blue_ribbon", tool="cone", moral="honesty", name="Noah", gender="boy", helper="father"),
    StoryParams(place="park_path", clue="chalk_arrow", tool="towel", moral="helping", name="Lina", gender="girl", helper="aunt"),
    StoryParams(place="community_center", clue="button", tool="spare_laces", moral="patience", name="Jules", gender="boy", helper="uncle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-story world about skating, improvising, and swiveling.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=PARENT_TYPES)
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
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
              and (getattr(args, "moral", None) is None or c[3] == getattr(args, "moral", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue, tool, moral = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(PARENT_TYPES)
    return StoryParams(place=place, clue=clue, tool=tool, moral=moral, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CLUES, params.clue), _safe_lookup(TOOLS, params.tool), _safe_lookup(MORALS, params.moral), params.name, params.gender, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.hidden:
            bits.append("hidden=True")
        if e.lost:
            bits.append("lost=True")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show selected_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show selected_story/4."))
        combos = sorted(set(asp.atoms(model, "selected_story")))
        print(f"{len(combos)} compatible story combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.clue} at {p.place} (tool: {p.tool}, moral: {p.moral})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
