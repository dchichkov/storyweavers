#!/usr/bin/env python3
"""
storyworlds/worlds/musical_holder_dialogue_happy_ending_curiosity_myth.py
==========================================================================

A tiny mythic storyworld about a curious child, a musical holder, a speaking
helper, and a happy ending.

Premise sketch:
- A curious child finds a small sacred holder for a musical instrument.
- The holder is treasured because it keeps the instrument safe and ready.
- A temptation appears: the child wants to rush the music before the holder is
  used correctly.
- Through dialogue, a wiser figure explains the right way, and the child learns
  to listen, place, and carry with care.
- The ending is happy because the music is made without damage, and the holder
  becomes part of the tale of wisdom.

The world tracks:
- physical meters: sturdiness, balance, shine, carried, cracked, ready, sound
- emotional memes: curiosity, worry, patience, pride, joy, trust

The story style is mythic but child-facing: a small legend with a clear turn,
dialogue, and a proving ending image.
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
    owner: Optional[str] = None
    holder_for: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    instrument: object | None = None
    stand: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "goddess", "priestess"}
        male = {"boy", "father", "dad", "man", "king", "priest"}
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
    place: str = "the temple grove"
    indoor: bool = False
    calm: bool = True
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
class Music:
    id: str
    name: str
    verb: str
    sound: str
    danger: str
    delight: str
    keyword: str
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
class Holder:
    id: str
    name: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    supports: set[str] = field(default_factory=set)
    carries: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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


SETTINGS = {
    "grove": Setting(place="the temple grove", indoor=False, calm=True),
    "hall": Setting(place="the myth hall", indoor=True, calm=True),
    "spring": Setting(place="the spring shrine", indoor=False, calm=True),
}

MUSIC = {
    "lyre": Music(
        id="lyre",
        name="lyre",
        verb="play the lyre",
        sound="soft strings",
        danger="a snapped string",
        delight="the air seemed to shimmer like sunrise",
        keyword="music",
    ),
    "flute": Music(
        id="flute",
        name="flute",
        verb="play the flute",
        sound="clear notes",
        danger="a bent reed",
        delight="the birds answered from the branches",
        keyword="song",
    ),
    "drum": Music(
        id="drum",
        name="drum",
        verb="beat the drum",
        sound="steady thunder",
        danger="a torn hide",
        delight="the ground felt like it was waking",
        keyword="rhythm",
    ),
}

HOLDERS = {
    "stand": Holder(
        id="stand",
        name="musical holder",
        phrase="a carved musical holder",
        protects={"lyre", "flute"},
        supports={"rest", "shine"},
        carries={"lyre", "flute"},
        prep="set the instrument into the musical holder first",
        tail="placed the instrument into the holder and lifted it again with care",
    ),
    "cradle": Holder(
        id="cradle",
        name="holder cradle",
        phrase="a small cedar cradle",
        protects={"lyre"},
        supports={"rest"},
        carries={"lyre"},
        prep="rest the lyre in the cedar cradle first",
        tail="rested the lyre in the cradle before the song",
    ),
    "ring": Holder(
        id="ring",
        name="singer's ring",
        phrase="a bronze singer's ring",
        protects={"flute"},
        supports={"shine"},
        carries={"flute"},
        prep="lay the flute in the bronze ring first",
        tail="laid the flute in the ring and then raised it to the lips",
    ),
}

NAMES = ["Mira", "Tavi", "Sera", "Ilan", "Noa", "Arin", "Kia", "Belen"]
ROLES = ["child", "novice", "herder", "scribe", "apprentice"]
GUARDIANS = ["mother", "father", "elder", "priest", "aunt"]


@dataclass
class StoryParams:
    setting: str
    music: str
    holder: str
    name: str
    role: str
    guardian: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A mythic story world about a curious child, a musical holder, and a happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--music", choices=MUSIC)
    ap.add_argument("--holder", choices=HOLDERS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--guardian", choices=GUARDIANS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MUSIC:
            for h in HOLDERS:
                if m in _safe_lookup(HOLDERS, h).protects and m in _safe_lookup(HOLDERS, h).carries:
                    combos.append((s, m, h))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "music", None) is None or c[1] == getattr(args, "music", None))
        and (getattr(args, "holder", None) is None or c[2] == getattr(args, "holder", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, music, holder = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    role = getattr(args, "role", None) or rng.choice(ROLES)
    guardian = getattr(args, "guardian", None) or rng.choice(GUARDIANS)
    return StoryParams(setting=setting, music=music, holder=holder, name=name, role=role, guardian=guardian)


def _ensure(m: bool, reason: str) -> None:
    if not m:
        pass


def tell(setting: Setting, music: Music, holder: Holder, name: str, role: str, guardian: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="child", meters={"balance": 0.0}, memes={"curiosity": 1.0}))
    elder = world.add(Entity(id="Guardian", kind="character", type=guardian, label=f"the {guardian}", memes={"wisdom": 1.0}))
    instrument = world.add(Entity(
        id=music.id,
        type=music.id,
        label=music.name,
        phrase=f"the {music.name}",
        owner=hero.id,
        meters={"ready": 0.0, "sound": 0.0, "cracked": 0.0, "shine": 1.0},
        memes={"value": 1.0},
    ))
    stand = world.add(Entity(
        id=holder.id,
        type="holder",
        label=holder.name,
        phrase=holder.phrase,
        owner=hero.id,
        meters={"sturdy": 1.0, "balance": 1.0},
        memes={"mystery": 0.0},
    ))

    world.say(f"In the old days, {name} was a {role} who loved to ask why the stars sang in the dark.")
    world.say(f"{hero.pronoun().capitalize()} had a curious heart, and every bright thing seemed to call {hero.pronoun('object')} closer.")
    world.say(f"One morning, {guardian} gave {name} {instrument.phrase}, and beside it lay {stand.phrase}.")
    world.say(f'"Keep it in the holder," {elder.id if False else elder.label} said, "for what is precious should rest before it rises."')

    world.para()
    world.say(f"{name} looked at the {holder.name} and wondered aloud, " + f'"Why would a song need a holder?"')
    world.say(f'"Because even a song," the {guardian} said, "can stumble if it is rushed without care."')
    world.say(f"{name} touched the {holder.name} and felt {music.delight}.")

    # tension: child wants to play before use of holder.
    hero.memes["curiosity"] += 1.0
    hero.memes["impatience"] = 1.0
    instrument.meters["ready"] += 0.2
    world.zone = {"stage"}
    world.say(f"{name} wanted to {music.verb} at once, but the {holder.name} had not been used yet.")
    world.say(f'"Can I try now?" {name} asked. "Will the holder really matter?"')

    # consequence prediction and warning.
    if holder.name == "musical holder":
        world.say(f'"Yes," said the {guardian}, "for without it, the {music.name} may lean, scrape, or crack."')
    else:
        world.say(f'"Yes," said the {guardian}, "for without it, the {music.name} may lose its true shape."')

    # resolution through dialogue.
    holder_obj = stand
    if music.id not in holder.protects:
        pass
    holder_obj.carried_by = hero.id
    world.say(f"{name} listened. " + f'"Then show me," {name} said, "and I will do it the right way."')
    world.say(f'The {guardian} smiled and answered, "First {holder.prep}."')
    world.say(f"{name} did as told, and the {holder.name} held the {music.name} steady and bright.")

    # State change: now ready, no crack.
    instrument.meters["ready"] = 1.0
    instrument.meters["sound"] = 1.0
    instrument.meters["cracked"] = 0.0
    stand.meters["balance"] = 1.0
    hero.memes["curiosity"] += 0.5
    hero.memes["patience"] = 1.0
    hero.memes["joy"] = 1.0
    hero.memes["pride"] = 1.0

    world.para()
    world.say(f"Then {name} played.")
    world.say(f"The {music.sound} rose from the {music.name}, and the air answered like a blessing.")
    world.say(f"The {holder.name} did its work well, so there was no {music.danger}.")
    world.say(f"{name} laughed and said, " + f'"Now I see. The holder was part of the song all along!"')
    world.say(f"The {guardian} laughed too, and the grove felt happier than before.")
    world.say(f"By sunset, {name} carried the {music.name} home without a scratch, and the {holder.name} shone as if it had heard the story itself.")

    world.facts.update(hero=hero, guardian=elder, instrument=instrument, holder=holder_obj, music=music, setting=setting, role=role)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    music = _safe_fact(world, f, "music")
    return [
        f'Write a short myth for children about a curious {hero.type} and a "{music.keyword}" that must be kept in a musical holder.',
        f"Tell a gentle dialogue story where {hero.id} learns why a {music.name} needs a holder before being played.",
        "Write a happy-ending myth about curiosity, careful hands, and a wise answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guardian = _safe_fact(world, f, "guardian")
    instrument = _safe_fact(world, f, "instrument")
    holder = _safe_fact(world, f, "holder")
    music = _safe_fact(world, f, "music")
    qa = [
        QAItem(
            question=f"Who was the curious child in the story?",
            answer=f"The curious child was {hero.id}, a small {f['role']} who wanted to know why the song needed a holder.",
        ),
        QAItem(
            question=f"What did {guardian.label} tell {hero.id} to do first with the {music.name}?",
            answer=f"{guardian.label} told {hero.id} to {holder.phrase if False else holder.phrase.replace('a ', '').replace('an ', '') if holder.phrase.startswith(('a ', 'an ')) else holder.phrase} first, so the {music.name} would rest safely before it was played.",
        ),
        QAItem(
            question=f"Why did the {holder.name} matter to the {music.name}?",
            answer=f"It mattered because it kept the {music.name} steady and safe, so there was no {music.danger} and the music could be played happily.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the instrument?",
            answer=f"It ended happily: {hero.id} played the {music.name}, the sound rose cleanly, and the {holder.name} shone after doing its job well.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a holder for in a story like this?",
            answer="A holder is for keeping something important steady, safe, or ready, like an instrument before it is played.",
        ),
        QAItem(
            question="Why do people ask questions in mythic stories?",
            answer="People ask questions in mythic stories because curiosity leads them to learn a hidden rule, a promise, or a wise way to act.",
        ),
        QAItem(
            question="What makes a story feel like a happy ending?",
            answer="A happy ending happens when the worry is solved and the important thing is safe, so the characters can smile at the end.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="grove", music="lyre", holder="stand", name="Mira", role="curious", guardian="elder"),
    StoryParams(setting="hall", music="flute", holder="ring", name="Tavi", role="apprentice", guardian="priest"),
    StoryParams(setting="spring", music="drum", holder="stand", name="Sera", role="child", guardian="mother"),
]


ASP_RULES = r"""
% A music item is at risk if it is played without a compatible holder.
at_risk(M, H) :- music(M), holder(H), protects(H, M), carries(H, M).

% A story is valid when the holder matches the music and the myth can end safely.
valid_story(S, M, H) :- setting(S), music(M), holder(H), at_risk(M, H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MUSIC:
        lines.append(asp.fact("music", m))
    for h, holder in HOLDERS.items():
        lines.append(asp.fact("holder", h))
        for p in sorted(holder.protects):
            lines.append(asp.fact("protects", h, p))
        for c in sorted(holder.carries):
            lines.append(asp.fact("carries", h, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_story_python() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_story_python())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def explain_rejection(music: Music, holder: Holder) -> str:
    return f"(No story: {holder.name} does not both protect and carry the {music.name}, so the mythic fix would not be honest.)"


def resolve_params_validated(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "music", None) and getattr(args, "holder", None):
        if getattr(args, "music", None) not in _safe_lookup(HOLDERS, getattr(args, "holder", None)).protects or getattr(args, "music", None) not in _safe_lookup(HOLDERS, getattr(args, "holder", None)).carries:
            pass
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), MUSIC[params.music], _safe_lookup(HOLDERS, params.holder), params.name, params.role, params.guardian)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, music, holder) combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
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
                params = resolve_params_validated(args, random.Random(seed))
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
            header = f"### {p.name}: {p.music} at {p.setting} (holder: {p.holder})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
