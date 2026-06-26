#!/usr/bin/env python3
"""
storyworlds/worlds/love_ocean_sharing_curiosity_rhyming_story.py
=================================================================

A small story world about love, the ocean, sharing, and curiosity,
told in a gentle rhyming-story style.

Premise:
- A child loves a special ocean day and treasures a found shell.
- Curiosity makes the child want to keep exploring the tide pools.
- Sharing tension appears when a friend or sibling wants a turn.

Turn:
- A parent or helper notices the child fears losing the treasure.
- A fair sharing plan lets everyone look, hold, and explore.

Resolution:
- The children share the ocean finds and end with a happy seaside image.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
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
    place: str
    detail: str
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
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
class Treasure:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
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
class SharingTool:
    id: str
    label: str
    prep: str
    tail: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []
        self.zone: set[str] = set()

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


def normalize(s: str) -> str:
    return " ".join(s.strip().split())


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def possessive_name(name: str) -> str:
    return name + "'" if name.endswith("s") else name + "'s"


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def activity_rhyme(activity: Activity) -> str:
    return {
        "tidepools": "The waves went swish, the shells went gleam, the shore felt like a dream.",
        "driftwood": "The driftwood bobbed, the foam danced near, and laughter sparkled clear.",
        "seaglass": "The sea-glass shone like candy light, so bright, so smooth, so right.",
        "sandcastle": "The castle rose with a sandy grace, then smiled at the sea's soft face.",
    }.get(activity.id, "The ocean sang a silver song, and all day long felt strong.")


def setting_detail(setting: Setting) -> str:
    return setting.detail


def _r_salt(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("ocean_play", 0.0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.held_by == actor.id and item.region in world.zone and not item.plural:
                sig = ("salt", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["sparkle"] = item.meters.get("sparkle", 0.0) + 1.0
                out.append(f"The ocean breeze gave {item.label} a brighter gleam.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("sharing", 0.0) < THRESHOLD:
            continue
        for friend in world.characters():
            if friend.id == actor.id:
                continue
            sig = ("share", actor.id, friend.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1.0
            out.append(f"{actor.id} let {friend.id} have a turn, and the moment felt bright.")
    return out


def _r_curious(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        sig = ("curious", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["wonder"] = actor.memes.get("wonder", 0.0) + 1.0
        out.append(f"{actor.id} peered closer, because curious eyes love to roam.")
    return out


CAUSAL_RULES = [_r_curious, _r_salt, _r_share]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, treasure: Treasure) -> bool:
    return treasure.region in activity.zone


def valid_combo(activity: Activity, treasure: Treasure) -> bool:
    return prize_at_risk(activity, treasure)


def choose_sharing_tool(activity: Activity, treasure: Treasure) -> Optional[SharingTool]:
    if not valid_combo(activity, treasure):
        return None
    if activity.id in {"tidepools", "seaglass", "driftwood"}:
        return SharingTool(
            id="basket",
            label="a little beach basket",
            prep="put the treasures in a little beach basket and take turns",
            tail="shared the basket and looked together",
        )
    return SharingTool(
        id="blanket",
        label="a striped beach blanket",
        prep="spread out a striped beach blanket and take turns",
        tail="sat on the blanket and shared what they found",
    )


def tell(
    setting: Setting,
    activity: Activity,
    treasure_cfg: Treasure,
    hero_name: str = "Mia",
    hero_type: str = "girl",
    friend_name: str = "Noah",
    friend_type: str = "boy",
    parent_name: str = "Mama",
) -> World:
    world = World(setting)

    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            traits=["little", "curious", "loving"],
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_type,
            traits=["little", "bright", "patient"],
        )
    )
    parent = world.add(
        Entity(
            id=parent_name,
            kind="character",
            type="mother",
            label=parent_name,
            traits=["gentle", "wise"],
        )
    )
    treasure = world.add(
        Entity(
            id="treasure",
            type=treasure_cfg.type,
            label=treasure_cfg.label,
            phrase=treasure_cfg.phrase,
            owner=hero.id,
            caretaker=parent.id,
            region=treasure_cfg.region,
            plural=treasure_cfg.plural,
        )
    )

    hero.memes["love"] = 1.0
    hero.memes["curiosity"] = 1.0
    hero.memes["sharing"] = 0.0

    world.say(
        f"{hero.id} loved the ocean shore, where foamy waves went by."
    )
    world.say(
        f"{hero.id} found {article(treasure.phrase)} {treasure.phrase} by the tide, and {hero.pronoun('possessive')} heart felt high."
    )
    world.say(activity_rhyme(activity))

    world.para()
    world.say(
        f"One bright day, {hero.id} and {friend.id} came down where the seagulls cry."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, because {hero.pronoun('subject')} was curious to see what hid nearby."
    )
    world.say(
        f"But {friend.id} wanted a turn with the {treasure.label}, and {hero.id} held it close with a sigh."
    )

    hero.memes["wanting"] = 1.0
    friend.memes["wanting"] = 1.0
    if prize_at_risk(activity, treasure):
        hero.memes["worry"] = 1.0
        world.say(
            f"{hero.id} worried that sharing would mean losing {treasure.phrase} in the spray of the sky."
        )

    world.para()
    world.say(
        f"{parent.id} smiled and said, \"A treasure can twinkle, and still be shared with care.\""
    )
    tool = choose_sharing_tool(activity, treasure)
    if tool is None:
        pass

    hero.memes["sharing"] = 1.0
    friend.memes["sharing"] = 1.0
    treasure.held_by = hero.id
    world.zone = set(activity.zone)
    propagate(world, narrate=True)
    world.say(
        f"{hero.id} and {friend.id} used {tool.label}, {tool.prep}, and each got a fair share."
    )
    world.say(
        f"Then {hero.id} let {friend.id} hold the {treasure.label}, and {friend.id} let {hero.id} hold it with a stare."
    )
    world.say(
        f"At the end, they {tool.tail}, while the ocean made a glittering ribbon in the air."
    )

    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1.0
    parent.memes["joy"] = 1.0

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        treasure=treasure,
        treasure_cfg=treasure_cfg,
        activity=activity,
        setting=setting,
        tool=tool,
        shared=True,
    )
    return world


SETTINGS = {
    "shore": Setting(
        place="the shore",
        detail="The shore was bright, with shells in the sand and foam in the breeze.",
        affords={"tidepools", "driftwood", "seaglass", "sandcastle"},
    ),
    "beach": Setting(
        place="the beach",
        detail="The beach was wide and warm, with gulls circling overhead.",
        affords={"tidepools", "driftwood", "seaglass", "sandcastle"},
    ),
    "pier": Setting(
        place="the pier",
        detail="The pier stretched over the water, creaking softly in the salt air.",
        affords={"driftwood", "seaglass"},
    ),
}

ACTIVITIES = {
    "tidepools": Activity(
        id="tidepools",
        verb="peek into the tide pools",
        gerund="peeking into tide pools",
        rush="dash to the tide pools",
        mess="wet",
        soil="splash-wet",
        zone={"hands", "feet"},
        keyword="curiosity",
        tags={"ocean", "curiosity", "sharing"},
    ),
    "driftwood": Activity(
        id="driftwood",
        verb="stack driftwood boats",
        gerund="stacking driftwood boats",
        rush="hurry to the driftwood",
        mess="scratched",
        soil="a little scratched",
        zone={"hands"},
        keyword="sharing",
        tags={"ocean", "sharing"},
    ),
    "seaglass": Activity(
        id="seaglass",
        verb="search for sea glass",
        gerund="searching for sea glass",
        rush="kneel by the shining stones",
        mess="sandy",
        soil="sandy",
        zone={"hands", "feet"},
        keyword="curiosity",
        tags={"ocean", "curiosity"},
    ),
    "sandcastle": Activity(
        id="sandcastle",
        verb="build a sandcastle",
        gerund="building a sandcastle",
        rush="pat the sand into walls",
        mess="sandy",
        soil="sandy",
        zone={"hands", "feet"},
        keyword="sharing",
        tags={"ocean", "sharing", "curiosity"},
    ),
}

TREASURES = {
    "shell": Treasure(
        label="shell",
        phrase="a pearly shell",
        type="shell",
        region="hands",
    ),
    "bucket": Treasure(
        label="bucket",
        phrase="a red beach bucket",
        type="bucket",
        region="hands",
        plural=False,
    ),
    "net": Treasure(
        label="net",
        phrase="a small blue net",
        type="net",
        region="hands",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Ava", "Nia", "Zoe"]
BOY_NAMES = ["Noah", "Finn", "Leo", "Eli", "Theo"]


@dataclass
class StoryParams:
    place: str
    activity: str
    treasure: str
    name: str
    gender: str
    friend: str
    friend_gender: str
    parent: str
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


KNOWLEDGE = {
    "ocean": [
        QAItem(
            question="What is the ocean?",
            answer="The ocean is a huge body of salty water that covers much of Earth.",
        ),
    ],
    "sharing": [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else use, hold, or enjoy something too.",
        ),
    ],
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more, peek closer, and learn what something is like.",
        ),
    ],
    "shell": [
        QAItem(
            question="What is a shell?",
            answer="A shell is the hard outside home of some sea animals, and people often find empty shells on the beach.",
        ),
    ],
    "seaglass": [
        QAItem(
            question="What is sea glass?",
            answer="Sea glass is smooth glass that waves and sand have worn down until it feels soft and looks shiny.",
        ),
    ],
    "tidepools": [
        QAItem(
            question="What is a tide pool?",
            answer="A tide pool is a little pool of seawater left in rocks when the ocean tide goes out.",
        ),
    ],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for tre_id, tre in TREASURES.items():
                if prize_at_risk(act, tre):
                    combos.append((place, act_id, tre_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, act, treasure = f["hero"], f["friend"], f["activity"], f["treasure_cfg"]
    return [
        f'Write a rhyming story for a little child about love, the ocean, {act.keyword}, and sharing.',
        f"Tell a gentle seaside tale where {hero.id} and {friend.id} both want the {treasure.phrase} and must share.",
        f'Write a short ocean story using the word "{act.keyword}" that ends with a happy sharing plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, parent = f["hero"], f["friend"], f["parent"]
    act, treasure = f["activity"], f["treasure_cfg"]
    place = _safe_fact(world, f, "setting").place
    qa = [
        QAItem(
            question=f"Where did {hero.id} find {treasure.phrase}?",
            answer=f"{hero.id} found {treasure.phrase} by the ocean at {place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {place}?",
            answer=f"{hero.id} wanted to {act.verb} because {hero.pronoun('subject')} was curious.",
        ),
        QAItem(
            question=f"Why did {hero.id} hold the treasure close at first?",
            answer=f"{hero.id} held it close because {friend.id} wanted a turn and {hero.id} worried about losing it.",
        ),
        QAItem(
            question=f"Who helped the children make a fair plan?",
            answer=f"{parent.id} helped them make a fair plan for sharing the treasure.",
        ),
        QAItem(
            question=f"What did the children do at the end?",
            answer=f"They shared the treasure and enjoyed the ocean together.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("ocean")
    tags.add("sharing")
    tags.add("curiosity")
    tags.add(world.facts["treasure_cfg"].type)
    out: list[QAItem] = []
    for key in ["ocean", "sharing", "curiosity", "shell", "seaglass", "tidepools"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
    return out


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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="shore",
        activity="tidepools",
        treasure="shell",
        name="Mia",
        gender="girl",
        friend="Noah",
        friend_gender="boy",
        parent="Mama",
    ),
    StoryParams(
        place="beach",
        activity="seaglass",
        treasure="shell",
        name="Ava",
        gender="girl",
        friend="Finn",
        friend_gender="boy",
        parent="Mom",
    ),
    StoryParams(
        place="pier",
        activity="driftwood",
        treasure="net",
        name="Leo",
        gender="boy",
        friend="Mia",
        friend_gender="girl",
        parent="Dad",
    ),
]


def explain_rejection(activity: Activity, treasure: Treasure) -> str:
    return (
        f"(No story: {activity.gerund} does not reach the {treasure.label} in a way "
        f"that creates a real sharing choice.)"
    )


ASP_RULES = r"""
prize_at_risk(A, T) :- splashes(A, R), worn_on(T, R).
valid(Place, A, T) :- affords(Place, A), prize_at_risk(A, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("worn_on", tid, t.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming ocean story world about love and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--parent")
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
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if getattr(args, "treasure", None):
        combos = [c for c in combos if c[2] == getattr(args, "treasure", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, treasure = rng.choice(list(combos))
    hero_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    friend_gender = getattr(args, "friend_gender", None) or ("boy" if hero_gender == "girl" else "girl")
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_name = getattr(args, "friend", None) or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero_name])
    parent = getattr(args, "parent", None) or rng.choice(["Mama", "Mom", "Dad"])
    return StoryParams(
        place=place,
        activity=activity,
        treasure=treasure,
        name=hero_name,
        gender=hero_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(TREASURES, params.treasure),
        params.name,
        params.gender,
        params.friend,
        params.friend_gender,
        params.parent,
    )
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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for row in vals:
            print(" ", row)
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.activity} at {p.place} (treasure: {p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
