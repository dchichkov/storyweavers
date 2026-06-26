#!/usr/bin/env python3
"""
storyworlds/worlds/beca_longitudinal_reconciliation_cautionary_inner_monologue_fairy.py
========================================================================================

A tiny fairy-tale story world about a child fairy, a long enchanted path,
a cautionary mistake, and a reconciliation that heals the hurt.

Seed idea:
- Beca is a little fairy who wants to hurry down a very long, longitudinal
  lane in the moonlit wood.
- An older fairy warns Beca that taking a shortcut through a thorn gate will
  tangle the lantern-thread and leave a friend behind.
- Beca ignores the warning, learns the hard way, thinks quietly to herself,
  and then returns to make amends.
- The ending should feel like a fairy tale: gentle, concrete, and changed.

The world simulates:
- meters: distance, tangles, dimness, drift, repair, tokens carried
- memes: worry, pride, regret, trust, warmth, reconciliation

The key narrative instruments are:
- Cautionary warning
- Inner monologue
- Reconciliation
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
# World model
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    elder: object | None = None
    friend: object | None = None
    helper_ent: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "fairy"}
        male = {"boy", "man", "father", "elf"}
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
    place: str = "the moonlit wood"
    path: str = "the longitudinal lane"
    gate: str = "the thorn gate"
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
class Choice:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    mess: str
    zone: str
    caution: str
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
class Prize:
    id: str
    label: str
    phrase: str
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
class StoryParams:
    place: str
    choice: str
    prize: str
    name: str
    helper: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


def _get_meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _add_meter(e: Entity, key: str, amount: float) -> None:
    e.meters[key] = _get_meter(e, key) + amount


def _get_meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _add_meme(e: Entity, key: str, amount: float) -> None:
    e.memes[key] = _get_meme(e, key) + amount


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "wood": Setting(place="the moonlit wood", path="the longitudinal lane", gate="the thorn gate", affords={"dash", "shortcut", "return"}),
    "glade": Setting(place="the silver glade", path="the longitudinal lane", gate="the briar arch", affords={"dash", "shortcut", "return"}),
    "brook": Setting(place="the little brook", path="the longitudinal ford", gate="the willow gate", affords={"dash", "shortcut", "return"}),
}

CHOICES = {
    "dash": Choice(
        id="dash",
        verb="hurry along",
        gerund="hurrying along",
        rush="run ahead",
        risk="straying far from the lantern-light",
        mess="drift",
        zone="path",
        caution="If you rush, you may lose the lantern-thread.",
        tags={"longitudinal", "journey"},
    ),
    "shortcut": Choice(
        id="shortcut",
        verb="take the shortcut",
        gerund="taking the shortcut",
        rush="duck through the thorn gate",
        risk="getting tangled in the briars",
        mess="tangle",
        zone="gate",
        caution="The shortcut is quick, but quick paths can prick and tear.",
        tags={"thorn", "cautionary"},
    ),
    "return": Choice(
        id="return",
        verb="go back to make things right",
        gerund="going back to make things right",
        rush="turn around in a hurry",
        risk="leaving hurt feelings behind",
        mess="rift",
        zone="hearth",
        caution="A kind return can mend a hard moment.",
        tags={"reconciliation"},
    ),
}

PRIZES = {
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="a tiny gold lantern",
        region="hand",
    ),
    "ribbon": Prize(
        id="ribbon",
        label="ribbon",
        phrase="a blue ribbon for her hair",
        region="hair",
    ),
    "cloak": Prize(
        id="cloak",
        label="cloak",
        phrase="a soft silver cloak",
        region="shoulders",
    ),
}

HELPERS = {
    "grandmother": "grandmother",
    "moth": "moth",
    "dew-sprite": "dew-sprite",
}

NAMES = ["Beca", "Lina", "Mira", "Tessa", "Nora", "Elin"]
TRAITS = ["brave", "proud", "quick", "gentle", "curious"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def valid_combo(place: str, choice: str, prize: str) -> bool:
    if place not in SETTINGS or choice not in CHOICES or prize not in PRIZES:
        return False
    c = _safe_lookup(CHOICES, choice)
    p = _safe_lookup(PRIZES, prize)
    if choice == "shortcut" and p.region not in {"hand", "hair", "shoulders"}:
        return False
    if choice == "dash" and place == "brook" and prize == "cloak":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for choice in CHOICES:
            for prize in PRIZES:
                if valid_combo(place, choice, prize):
                    out.append((place, choice, prize))
    return out


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} held {setting.path} like a pale thread."


def predict(world: World, hero: Entity, choice: Choice, prize: Entity) -> dict:
    sim = world.copy()
    do_choice(sim, sim.get(hero.id), choice, narrate=False)
    return {
        "hurt": _get_meme(sim.get("Friend"), "hurt") >= THRESHOLD,
        "repaired": _get_meme(sim.get("Friend"), "trust") >= THRESHOLD,
        "tangle": _get_meter(sim.get(prize.id), "tangle") >= THRESHOLD,
    }


def do_choice(world: World, hero: Entity, choice: Choice, narrate: bool = True) -> None:
    _add_meme(hero, "resolve", 1)
    if choice.id == "dash":
        _add_meter(hero, "distance", 1)
        _add_meme(hero, "worry", 1)
        world.say(f"{hero.id} hurried along the long lane, and the moonlight seemed to stretch farther and farther.")
    elif choice.id == "shortcut":
        _add_meter(hero, "tangle", 1)
        _add_meme(hero, "pride", 1)
        _add_meme(world.get("Friend"), "hurt", 1)
        _add_meme(world.get("Friend"), "trust", -1)
        world.say(f"{hero.id} chose the shortcut and slipped through the thorn gate.")
        world.say(f"The briars caught at {world.get('Friend').id}'s sleeve, and the little friend looked sadly after {hero.pronoun('object')}.")
    elif choice.id == "return":
        _add_meter(hero, "repair", 1)
        _add_meme(hero, "regret", 1)
        _add_meme(world.get("Friend"), "trust", 1)
        _add_meme(hero, "reconciliation", 1)
        world.say(f"{hero.id} turned back to make things right.")
        world.say(f"That slow return loosened the hurt like warm rain loosens a knot.")
    if narrate:
        world.say(choice.caution)


def tell(setting: Setting, choice: Choice, prize_cfg: Prize, hero_name: str, helper: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="fairy",
        meters={"distance": 0.0},
        memes={"worry": 0.0, "pride": 0.0, "regret": 0.0, "reconciliation": 0.0},
    ))
    friend = world.add(Entity(
        id="Friend",
        kind="character",
        type="fairy",
        meters={"hurt": 0.0},
        memes={"hurt": 0.0, "trust": 1.0},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type="fairy",
        meters={},
        memes={"care": 1.0},
    ))
    prize = world.add(Entity(
        id=prize_cfg.id,
        type="thing",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        caretaker=hero.id,
        region=prize_cfg.region,
    ))
    helper_ent = world.add(Entity(
        id=helper,
        kind="character" if helper == "grandmother" else "thing",
        type="fairy" if helper == "grandmother" else "moth",
        label=helper,
    ))

    world.say(f"{hero.id} was a little fairy who lived beside the longitudinal lane in {setting.place}.")
    world.say(f"She loved her {prize.label} because it shone like morning on water.")
    world.say(f"Her {helper_ent.label} had once told her, 'A long road is kinder than a quick one.'")

    world.para()
    world.say(setting_detail(setting))
    world.say(f"One dusk, {hero.id} and {friend.id} stood near {setting.gate}.")
    world.say(f"{hero.id} wanted to {choice.verb}, even though the path ahead felt {choice.risk}.")

    # Cautionary warning
    world.say(f'"{choice.caution}" {elder.id} said.')
    _add_meme(hero, "heard_warning", 1)

    # Inner monologue
    world.say(
        f"{hero.id} thought to herself, 'It is only a little gate. "
        f"But little gates can still scratch.'"
    )

    do_choice(world, hero, choice)

    world.para()
    if choice.id == "shortcut":
        world.say(f"{friend.id} would not smile; the hurt sat between them like a dark pebble.")
        world.say(f"{hero.id} felt the pebble in her chest and whispered, 'I was wrong.'")
        _add_meme(hero, "regret", 1)

        # Reconciliation turn
        world.say(f"Then {hero.id} went back along the longitudinal lane to find {friend.id}.")
        _add_meter(hero, "repair", 1)
        _add_meme(hero, "reconciliation", 1)
        _add_meme(friend, "trust", 1)
        _add_meme(friend, "hurt", -1)
        world.say(
            f"{hero.id} offered her {prize.label} and her apology together, "
            f"and {friend.id} took both with trembling hands."
        )
        world.say(
            f"They tied the {prize.label} with a fresh ribbon and walked home side by side, "
            f"careful, quiet, and kind."
        )
    elif choice.id == "dash":
        world.say(f"{friend.id} called after her, and {hero.id} paused before the long lane grew too lonely.")
        world.say(f"She did not turn away from the warning after all; she slowed down and waited.")
        _add_meme(hero, "reconciliation", 1)
        _add_meme(friend, "trust", 1)
        world.say(f"That made the moonlit wood feel smaller and safer.")
    else:
        world.say(f"{friend.id} watched her go back, and the hurt softened into trust.")
        world.say(f"The long lane seemed brighter once the apology had been spoken.")
        _add_meme(friend, "trust", 1)

    world.facts.update(hero=hero, friend=friend, elder=elder, prize=prize, helper=helper_ent, choice=choice, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a young child about {f["hero"].id} on a long path called the longitudinal lane.',
        f"Tell a cautionary story where {f['hero'].id} ignores a warning, then thinks quietly, and finally makes things right.",
        f"Write a gentle story about {f['hero'].id}, {f['friend'].id}, and a choice that ends in reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    choice = _safe_fact(world, f, "choice")
    prize = _safe_fact(world, f, "prize")
    setting = _safe_fact(world, f, "setting")

    out = [
        QAItem(
            question=f"Who is the story mostly about?",
            answer=f"The story is mostly about {hero.id}, a little fairy who lived in {setting.place}.",
        ),
        QAItem(
            question=f"What warning did the elder fairy give about {choice.id}?",
            answer=f"The elder warned that {choice.caution.lower()}",
        ),
        QAItem(
            question=f"What did {hero.id} think to herself after hearing the warning?",
            answer=f"{hero.id} thought that the gate looked small, but small gates can still scratch and hurt a friend.",
        ),
    ]
    if choice.id == "shortcut":
        out.append(QAItem(
            question=f"Why did {friend.id} feel hurt?",
            answer=f"{friend.id} felt hurt because {hero.id} chose the shortcut and the briars caught at {friend.id}'s sleeve.",
        ))
        out.append(QAItem(
            question=f"How did {hero.id} and {friend.id} mend the problem?",
            answer=f"{hero.id} went back, said sorry, and offered the {prize.label} and her apology together. That helped them reconcile.",
        ))
    else:
        out.append(QAItem(
            question=f"How did {hero.id} avoid the worst trouble?",
            answer=f"{hero.id} slowed down and chose the safer way, so the hurt did not grow into a bigger problem.",
        ))
    return out


WORLD_KNOWLEDGE = {
    "fairy": QAItem(
        question="What is a fairy in a story?",
        answer="A fairy is a small magical person in a story, often with wings and a gentle kind of magic.",
    ),
    "thorn": QAItem(
        question="What are thorns?",
        answer="Thorns are sharp points on some plants that can prick skin or catch on cloth.",
    ),
    "longitudinal": QAItem(
        question="What does longitudinal mean?",
        answer="Longitudinal means stretching along the length of something, like a long road or a long line.",
    ),
    "reconciliation": QAItem(
        question="What is reconciliation?",
        answer="Reconciliation is when people make peace again after a disagreement or hurt feelings.",
    ),
    "cautionary": QAItem(
        question="What is a cautionary tale?",
        answer="A cautionary tale is a story that warns about a mistake so readers can learn from it.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["choice"].tags)
    tags.add("fairy")
    tags.add("longitudinal")
    if world.facts["choice"].id == "shortcut":
        tags.add("thorn")
        tags.add("reconciliation")
        tags.add("cautionary")
    return [WORLD_KNOWLEDGE[t] for t in ["fairy", "longitudinal", "thorn", "cautionary", "reconciliation"] if t in tags]


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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_combo(P,C,R) :- place(P), choice(C), prize(R).
bad_combo(P,shortcut,cloak) :- place(P), prize(cloak).
valid_story(P,C,R) :- valid_combo(P,C,R), not bad_combo(P,C,R).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CHOICES:
        lines.append(asp.fact("choice", c))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - asp_set))
    print("only in asp:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def explain_rejection(place: str, choice: str, prize: str) -> str:
    return f"(No story: {choice} at {place} with {prize} is not a reasonable fairy-tale combination.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "choice", None) is None or c[1] == getattr(args, "choice", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, choice, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    return StoryParams(place=place, choice=choice, prize=prize, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CHOICES, params.choice), _safe_lookup(PRIZES, params.prize), params.name, params.helper)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="wood", choice="shortcut", prize="lantern", name="Beca", helper="grandmother"),
    StoryParams(place="glade", choice="dash", prize="ribbon", name="Beca", helper="moth"),
    StoryParams(place="brook", choice="return", prize="cloak", name="Beca", helper="dew-sprite"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale story world about caution and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/3."))
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.choice} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
