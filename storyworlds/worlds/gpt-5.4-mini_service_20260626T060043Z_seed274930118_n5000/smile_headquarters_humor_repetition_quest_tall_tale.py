#!/usr/bin/env python3
"""
A standalone storyworld: a tall tale about a quest, a headquarters, and a
smile that keeps getting bigger with every humorous try.

Seed premise:
- A crew works out of a small headquarters.
- They set out on a quest to bring back a smile that has gone missing.
- The tale uses repetition for comic lift: every plan nearly works, then a
  funnier version is tried.
- The ending proves the change by showing the headquarters full of smiles.

This file is self-contained and follows the Storyweavers storyworld contract.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    chief: object | None = None
    hero: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
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
    indoors: bool
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
    verb: str
    attempt: str
    finish: str
    kind: str
    reward: str
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
class Charm:
    id: str
    label: str
    phrase: str
    effect: str
    funny: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[tuple] = set()
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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = []
        clone.facts = dict(self.facts)
        return clone


def _hype(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"In the tall little town of Mopwick, the {hero.label} at the "
        f"headquarters loved a good {quest.label if hasattr(quest, 'label') else 'quest'}."
    )


def _introduce(world: World, hero: Entity, chief: Entity, charm: Charm, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a bright-eyed {hero.type} who ran the headquarters like a barn "
        f"cat runs a fence: quick, curious, and always looking for trouble to turn funny."
    )
    world.say(
        f"{chief.label.capitalize()} was the kind of leader who could smell a frown from "
        f"three fields away, and {hero.id} had one mighty important job: bring back a smile."
    )
    world.say(
        f"They kept a {charm.label} on the wall, because every grand quest needs a tool "
        f"that can make the day grin."
    )


def _repetition_step(world: World, hero: Entity, quest: Quest, charm: Charm, attempt: int) -> None:
    key = ("attempt", attempt)
    if key in world.fired:
        return
    world.fired.add(key)
    if attempt == 1:
        world.say(
            f"So {hero.id} marched out on the first try and whispered, "
            f'"Easy as pie, I will fetch the smile at once."'
        )
        world.say(
            f"But the first plan was as helpful as a wet boot in a fiddle case."
        )
    elif attempt == 2:
        world.say(
            f"So {hero.id} marched out on the second try and whispered, "
            f'"Easy as pie, I will fetch the smile at once."'
        )
        world.say(
            f"But the second plan was as useful as a spoon for catching fog."
        )
    else:
        world.say(
            f"So {hero.id} marched out on the third try and whispered, "
            f'"Easy as pie, I will fetch the smile at once."'
        )
        world.say(
            f"This time the trick was funny enough to work."
        )
    hero.memes["mirth"] = hero.memes.get("mirth", 0) + 1
    if attempt >= 3:
        hero.meters["success"] = hero.meters.get("success", 0) + 1
        hero.meters["smile"] = hero.meters.get("smile", 0) + 1
        charm.meters["glow"] = charm.meters.get("glow", 0) + 1


def _resolve(world: World, hero: Entity, chief: Entity, charm: Charm, quest: Quest) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    chief.memes["pride"] = chief.memes.get("pride", 0) + 2
    world.say(
        f"At last, {hero.id} came back to headquarters with the smile tucked safely under "
        f"{hero.pronoun('possessive')} arm like a pie under a bed sheet."
    )
    world.say(
        f"{charm.funny.capitalize()}, and the whole room cracked up so hard that even the "
        f"chairs looked pleased."
    )
    world.say(
        f"By supper time, the headquarters had a smile in every window, and {hero.id} "
        f"was already planning the next big, goofy, glorious quest."
    )


def tell(setting: Setting, quest: Quest, charm: Charm, hero_name: str, hero_type: str, chief_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label="quest runner"))
    chief = world.add(Entity(id="Chief", kind="character", type=chief_type, label="chief"))
    relic = world.add(Entity(id="Smile", kind="thing", type="smile", label="smile", phrase="a runaway smile"))

    world.facts["hero"] = hero
    world.facts["chief"] = chief
    world.facts["relic"] = relic
    world.facts["quest"] = quest
    world.facts["charm"] = charm

    _hype(world, hero, quest)
    _introduce(world, hero, chief, charm, quest)

    world.para()
    world.say(
        f"The headquarters sat on a hill like a cookie tin with a flag on top, and the town "
        f"kept asking whether a smile could really be found after it went missing."
    )
    world.say(
        f"{chief.label.capitalize()} pointed at the map and said the same thing three times for luck: "
        f'"Find the smile, find the smile, find the smile."'
    )
    world.say(
        f"{hero.id} answered three times too: 'I can do that, I can do that, I can do that.'"
    )

    world.para()
    _repetition_step(world, hero, quest, charm, 1)
    _repetition_step(world, hero, quest, charm, 2)
    _repetition_step(world, hero, quest, charm, 3)

    world.para()
    _resolve(world, hero, chief, charm, quest)

    world.facts["ended_happy"] = True
    world.facts["attempts"] = 3
    return world


SETTINGS = {
    "hill": Setting(place="the hilltop headquarters", indoors=False, affords={"quest"}),
    "barn": Setting(place="the old red barn headquarters", indoors=True, affords={"quest"}),
    "station": Setting(place="the tiny station headquarters", indoors=True, affords={"quest"}),
}

QUESTS = {
    "smile_search": Quest(
        id="smile_search",
        verb="go looking for the missing smile",
        attempt="fetch the smile",
        finish="bring the smile home",
        kind="quest",
        reward="a room full of grins",
        tags={"smile", "quest", "humor", "repetition"},
    ),
    "guffaw_hunt": Quest(
        id="guffaw_hunt",
        verb="hunt for the lost guffaw",
        attempt="catch the laugh",
        finish="carry the laugh back",
        kind="quest",
        reward="a burst of laughter",
        tags={"smile", "quest", "humor", "repetition"},
    ),
}

CHARMS = {
    "funny_hat": Charm(
        id="funny_hat",
        label="funny hat",
        phrase="a lopsided funny hat",
        effect="silly sparkle",
        funny="the hat leaned left and winked right",
    ),
    "giggle_bell": Charm(
        id="giggle_bell",
        label="giggle bell",
        phrase="a brass giggle bell",
        effect="ringing cheer",
        funny="the bell went ding-ding and then hiccuped like a goose",
    ),
}

GIRL_NAMES = ["Mabel", "Tilly", "Nora", "Poppy", "Winnie", "Daisy"]
BOY_NAMES = ["Otis", "Benny", "Milo", "Jasper", "Hank", "Rufus"]
TRAITS = ["brave", "cheery", "earnest", "bouncy"]


@dataclass
class StoryParams:
    place: str
    quest: str
    charm: str
    name: str
    gender: str
    chief: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for quest in QUESTS.values():
            if "quest" not in setting.affords:
                continue
            for charm in CHARMS.values():
                combos.append((place, quest.id, charm.id))
    return combos


def explain_rejection(place: str, quest: str, charm: str) -> str:
    return f"(No story: the requested mix of {place}, {quest}, and {charm} cannot make a coherent headquarters quest.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale storyworld about a headquarters quest for a smile.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--chief", choices=["captain", "boss"])
    ap.add_argument("--name")
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
    if getattr(args, "place", None) and getattr(args, "quest", None) and getattr(args, "charm", None):
        if (getattr(args, "place", None), getattr(args, "quest", None), getattr(args, "charm", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "charm", None) is None or c[2] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest_id, charm_id = rng.choice(list(combos))
    quest = _safe_lookup(QUESTS, quest_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    chief = getattr(args, "chief", None) or rng.choice(["captain", "boss"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest_id, charm=charm_id, name=name, gender=gender, chief=chief, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a young child about a headquarters and a missing smile.',
        f"Tell a humorous quest where {f['hero'].id} works from the {world.setting.place} to bring back a smile.",
        f'Write a repeated, funny adventure that ends with the headquarters full of smiles.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    chief: Entity = _safe_fact(world, f, "chief")
    quest: Quest = _safe_fact(world, f, "quest")
    charm: Charm = _safe_fact(world, f, "charm")
    return [
        QAItem(
            question=f"Where did {hero.id} work from during the quest?",
            answer=f"{hero.id} worked from {world.setting.place}, which served as the headquarters for the whole tall tale."
        ),
        QAItem(
            question=f"What was {hero.id} trying to do on the quest?",
            answer=f"{hero.id} was trying to {quest.verb}, because the town needed a smile back."
        ),
        QAItem(
            question=f"Why was the story funny and repeated?",
            answer=f"The story repeated the same promise three times on purpose, and each try got sillier until the {charm.label} trick worked."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the headquarters full of smiles, after {hero.id} brought the smile home and everybody laughed."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a headquarters?",
            answer="A headquarters is the main place where a group works, plans, and keeps important things."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a long search or mission to find something important or solve a problem."
        ),
        QAItem(
            question="Why can repetition be funny in a story?",
            answer="Repetition can be funny because saying or trying the same thing again and again makes the change at the end feel bigger and sillier."
        ),
        QAItem(
            question="What makes a tall tale feel grand?",
            answer="A tall tale feels grand when ordinary things are described in a huge, playful way, like a tiny headquarters that seems big enough to hold a whole town's hopes."
        ),
    ]


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill", quest="smile_search", charm="funny_hat", name="Mabel", gender="girl", chief="captain", trait="bouncy"),
    StoryParams(place="barn", quest="guffaw_hunt", charm="giggle_bell", name="Otis", gender="boy", chief="boss", trait="earnest"),
]


ASP_RULES = r"""
setting(hill).
setting(barn).
setting(station).

affords(hill,quest).
affords(barn,quest).
affords(station,quest).

quest(smile_search).
quest(guffaw_hunt).

charm(funny_hat).
charm(giggle_bell).

valid(Place,Quest,Charm) :- setting(Place), affords(Place,quest), quest(Quest), charm(Charm).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if s.indoors:
            lines.append(asp.fact("indoors", place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", place, a))
    for q in QUESTS.values():
        lines.append(asp.fact("quest", q.id))
    for c in CHARMS.values():
        lines.append(asp.fact("charm", c.id))
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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(CHARMS, params.charm), params.name, params.gender, params.chief)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, quest, charm in combos:
            print(f"  {place:8} {quest:14} {charm}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
