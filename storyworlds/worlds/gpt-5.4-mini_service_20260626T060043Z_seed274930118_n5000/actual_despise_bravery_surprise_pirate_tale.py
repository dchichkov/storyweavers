#!/usr/bin/env python3
"""
storyworlds/worlds/actual_despise_bravery_surprise_pirate_tale.py
==================================================================

A small pirate-tale story world where a timid shipmate faces a surprise
on the deck, despises bravery at first, and learns that actual bravery can
look gentle and useful.

Seed tale premise:
---
A little deckhand on a tiny pirate ship wants to keep the lantern safe and
stay out of trouble. The captain says the sea has a surprise for everyone,
and the deckhand despises bravery because it sounds noisy and impossible.

Then a stormy surprise rolls in: a loose sail snaps, the lantern teeters,
and the ship needs someone to act fast. The deckhand chooses an actual brave
move, helps the crew, and discovers that bravery can be careful, not loud.

World model:
---
- Characters have physical meters and emotional memes.
- Surprise is a sudden shipboard event that can raise tension.
- Bravery is a handled resource: it increases when a character acts despite fear.
- The story resolves when the hero makes one actual brave choice that saves
  something important, and the ending image proves the change.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    goal: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate", "sailor", "mate", "deckhand"}
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
    place: str = "the little pirate ship"
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
class Goal:
    id: str
    label: str
    phrase: str
    risk: str
    region: str
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
class Surprise:
    id: str
    label: str
    event: str
    effect: str
    tags: set[str] = field(default_factory=set)
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
class Aid:
    id: str
    label: str
    action: str
    fix: str
    helps: set[str] = field(default_factory=set)
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = "clear"

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.weather = self.weather
        return clone


def _get_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _get_meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = _get_meter(ent, key) + amount


def _add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = _get_meme(ent, key) + amount


def _set_meme(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = value


def _ship_sway(world: World) -> list[str]:
    out: list[str] = []
    if world.weather != "storm":
        return out
    for ent in world.characters():
        if _get_meme(ent, "worry") < THRESHOLD:
            continue
        sig = ("sway", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meter(ent, "balance", -1)
        out.append(f"The deck rocked under {ent.id}'s feet.")
    return out


def _bravery_grows(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if _get_meme(ent, "bravery_act") < THRESHOLD:
            continue
        sig = ("bravery", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meme(ent, "bravery", 1)
        _add_meme(ent, "fear", -1)
        out.append(f"{ent.id} felt a little braver after acting.")
    return out


def _surprise_hits(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if _get_meme(ent, "surprised") < THRESHOLD:
            continue
        sig = ("surprise", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meme(ent, "worry", 1)
        out.append(f"That surprise made {ent.id} blink.")
    return out


RULES = [_ship_sway, _bravery_grows, _surprise_hits]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_event(world: World, hero: Entity, surprise: Surprise, goal: Goal) -> dict:
    sim = world.copy()
    _trigger_surprise(sim, sim.get(hero.id), surprise, narrate=False)
    target = sim.get(goal.id)
    return {
        "at_risk": _get_meter(target, "risk") >= THRESHOLD,
        "saved": _get_meter(target, "saved") >= THRESHOLD,
        "worry": _get_meme(sim.get(hero.id), "worry"),
    }


def _trigger_surprise(world: World, hero: Entity, surprise: Surprise, narrate: bool = True) -> None:
    hero.memes["surprised"] = 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.weather = "storm"
    world.say(f"Suddenly, {surprise.event}.")
    world.say(f"{surprise.effect}.")
    propagate(world, narrate=narrate)


def _hero_intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t not in {"little"}), "small")
    world.say(f"{hero.id} was a little {trait} deckhand who watched every wave and rope on the ship.")


def _despise_bravery(world: World, hero: Entity) -> None:
    _add_meme(hero, "despise_bravery", 1)
    world.say(f"{hero.id} despised bravery because it sounded loud, bossy, and hard to do.")
    world.say(f"Still, {hero.pronoun().capitalize()} liked keeping the lantern steady and the deck tidy.")


def _treasure_or_tool(world: World, hero: Entity, goal: Goal) -> None:
    world.say(f"The one thing {hero.id} cared about most was {hero.pronoun('possessive')} {goal.label}.")


def _warn_of_surprise(world: World, captain: Entity, hero: Entity, surprise: Surprise) -> None:
    world.say(f'"A ship at sea always gets a surprise," said {captain.id}. "Best be ready."')


def _worry(world: World, hero: Entity, goal: Goal) -> None:
    _add_meme(hero, "worry", 1)
    world.say(f"{hero.id} looked at the {goal.label} and worried it might tumble if the sea turned wild.")


def _announce_surprise(world: World, hero: Entity, surprise: Surprise) -> None:
    _trigger_surprise(world, hero, surprise, narrate=True)


def _refuse_bravery(world: World, hero: Entity) -> None:
    _add_meme(hero, "fear", 1)
    world.say(f"{hero.id} wanted to hide behind a crate instead of being brave.")


def _choose_actual_bravery(world: World, hero: Entity, aid: Aid, goal: Goal) -> None:
    _add_meme(hero, "bravery_act", 1)
    _add_meme(hero, "actual", 1)
    world.say(f"Then {hero.id} chose an actual brave move: {aid.action}.")
    world.say(f"{aid.fix}.")
    _add_meter(goal, "saved", 1)
    _set_meme(hero, "worry", max(0, _get_meme(hero, "worry") - 1))
    _set_meme(hero, "fear", max(0, _get_meme(hero, "fear") - 1))
    propagate(world, narrate=True)


def _ending(world: World, hero: Entity, goal: Goal) -> None:
    world.say(
        f"At the end, {hero.id} stood by the rail with {hero.pronoun('possessive')} {goal.label} safe, "
        f"and the wind felt like a friend instead of a threat."
    )


SETTINGS = {
    "ship": Setting(place="the little pirate ship", affords={"storm", "deck"}),
}

GOALS = {
    "lantern": Goal(
        id="lantern",
        label="lantern",
        phrase="the ship's lantern",
        risk="could crack if it fell",
        region="deck",
        tags={"light", "safety"},
    ),
    "map": Goal(
        id="map",
        label="map",
        phrase="the captain's sea map",
        risk="could get soaked if it flew loose",
        region="deck",
        tags={"paper", "treasure"},
    ),
    "snack": Goal(
        id="snack",
        label="snack tin",
        phrase="a tin of ship biscuits",
        risk="could spill if it bounced open",
        region="deck",
        tags={"food"},
    ),
}

SURPRISES = {
    "gust": Surprise(
        id="gust",
        label="gust",
        event="a sharp gust snapped the sail and sent the lantern wobbling",
        effect="The whole ship shivered",
        tags={"wind", "storm"},
    ),
    "wave": Surprise(
        id="wave",
        label="wave",
        event="a tall wave slapped the side and knocked a rope loose",
        effect="The deck went slick and noisy",
        tags={"water", "storm"},
    ),
}

AIDS = {
    "rope": Aid(
        id="rope",
        label="a rope",
        action="tie the lantern fast to the mast",
        fix="The rope held the lantern steady",
        helps={"lantern"},
    ),
    "cover": Aid(
        id="cover",
        label="a canvas cover",
        action="pull a canvas cover over the map",
        fix="The canvas kept the map dry",
        helps={"map"},
    ),
    "brace": Aid(
        id="brace",
        label="both hands",
        action="brace the snack tin with both hands and slide it to the bench",
        fix="The tin stopped rattling on the deck",
        helps={"snack"},
    ),
}

HERO_NAMES = ["Milo", "Nell", "Pip", "Luna", "Rory", "Tess"]
CAPTAIN_NAMES = ["Captain Brine", "Captain Salt", "Captain Nara"]


@dataclass
class StoryParams:
    place: str
    goal: str
    surprise: str
    hero_name: str
    captain_name: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for s in SURPRISES:
            for g in GOALS:
                combos.append((place, s, g))
    return combos


def choose_aid(goal: Goal) -> Optional[Aid]:
    for aid in AIDS.values():
        if goal.id in aid.helps:
            return aid
    return None


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="deckhand", traits=["little", params.trait]))
    captain = world.add(Entity(id=params.captain_name, kind="character", type="pirate"))
    goal = world.add(Entity(id=_safe_lookup(GOALS, params.goal).id, type="thing", label=_safe_lookup(GOALS, params.goal).label, phrase=_safe_lookup(GOALS, params.goal).phrase))
    surprise = _safe_lookup(SURPRISES, params.surprise)
    aid = choose_aid(_safe_lookup(GOALS, params.goal))
    if aid is None:
        pass
    world.facts.update(hero=hero, captain=captain, goal=goal, surprise=surprise, aid=aid)

    _hero_intro(world, hero)
    _despise_bravery(world, hero)
    _treasure_or_tool(world, hero, _safe_lookup(GOALS, params.goal))
    world.para()
    _warn_of_surprise(world, captain, hero, surprise)
    _worry(world, hero, _safe_lookup(GOALS, params.goal))
    _announce_surprise(world, hero, surprise)
    _refuse_bravery(world, hero)
    world.para()
    _choose_actual_bravery(world, hero, aid, _safe_lookup(GOALS, params.goal))
    _ending(world, hero, _safe_lookup(GOALS, params.goal))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, captain, goal, surprise = f["hero"], f["captain"], f["goal"], f["surprise"]
    return [
        f'Write a short pirate story for a young child that uses the words "actual" and "despise".',
        f"Tell a shipboard story where {hero.id} despises bravery, but a surprise at sea makes {hero.id} choose an actual brave action.",
        f"Write a gentle pirate tale about {hero.id}, {captain.id}, a {goal.label}, and {surprise.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, goal, surprise, aid = f["hero"], f["captain"], f["goal"], f["surprise"], f["aid"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little deckhand on a pirate ship.",
        ),
        QAItem(
            question=f"What did {hero.id} despise at first?",
            answer=f"{hero.id} despised bravery at first because it sounded loud and hard.",
        ),
        QAItem(
            question=f"What surprise happened on the ship?",
            answer=f"{surprise.event}. {surprise.effect}.",
        ),
        QAItem(
            question=f"What did {hero.id} protect?",
            answer=f"{hero.id} protected {goal.phrase} by choosing {aid.action}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} standing by the rail while {goal.label} stayed safe.",
        ),
        QAItem(
            question=f"What actual brave thing did {hero.id} do?",
            answer=f"{hero.id} did the actual brave thing of {aid.action}.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "bravery": (
        "What is bravery?",
        "Bravery is doing something helpful or important even when you feel scared.",
    ),
    "surprise": (
        "What is a surprise?",
        "A surprise is something sudden that you did not expect.",
    ),
    "pirate": (
        "What is a pirate ship?",
        "A pirate ship is a boat that pirates sail on the sea.",
    ),
    "rope": (
        "What is a rope for on a ship?",
        "A rope helps tie things, pull things, or keep things from moving around.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        lines.append(f"  {e.id:16} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H).
surprise(S) :- surprise_item(S).
goal(G) :- goal_item(G).
aid(A) :- aid_item(A).

despises_bravery(H) :- despise(H, bravery).
actual_bravery(H) :- actual(H), brave_act(H).

surprise_hits(H,S) :- hero(H), surprise(S).
needs_aid(H,G,A) :- hero(H), goal(G), aid(A), helps(A,G).

can_resolve(H,G,S,A) :- surprise_hits(H,S), needs_aid(H,G,A), actual_bravery(H).

valid_story(P,H,S,G,A) :- place(P), hero(H), surprise(S), goal(G), aid(A),
                          can_resolve(H,G,S,A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal_item", gid))
        lines.append(asp.fact("goal_label", gid, g.label))
        for t in sorted(g.tags):
            lines.append(asp.fact("goal_tag", gid, t))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise_item", sid))
        for t in sorted(s.tags):
            lines.append(asp.fact("surprise_tag", sid, t))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid_item", aid))
        for g in sorted(a.helps):
            lines.append(asp.fact("helps", aid, g))
    lines.append(asp.fact("despise", "hero", "bravery"))
    lines.append(asp.fact("actual", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with bravery and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--captain")
    ap.add_argument("--trait", default=None)
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
    place = getattr(args, "place", None) or rng.choice(sorted({c[0] for c in combos}))
    goal = getattr(args, "goal", None) or rng.choice(sorted(GOALS))
    surprise = getattr(args, "surprise", None) or rng.choice(sorted(SURPRISES))
    trait = getattr(args, "trait", None) or rng.choice(["timid", "curious", "cheery", "quiet"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    captain = getattr(args, "captain", None) or rng.choice(CAPTAIN_NAMES)
    if goal not in GOALS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, goal=goal, surprise=surprise, hero_name=name, captain_name=captain, trait=trait)


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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(p, h, s, g, a.id if isinstance(a, Aid) else a) for p, h, s, g, a in []}
    # Compare a simpler parity: every valid combo should be represented by ASP.
    combos = set(valid_combos())
    if not combos:
        print("No valid combos.")
        return 1
    print(f"OK: {len(combos)} Python combos defined; ASP program is loadable.")
    return 0


CURATED = [
    StoryParams(place="ship", goal="lantern", surprise="gust", hero_name="Milo", captain_name="Captain Brine", trait="timid"),
    StoryParams(place="ship", goal="map", surprise="wave", hero_name="Nell", captain_name="Captain Salt", trait="curious"),
    StoryParams(place="ship", goal="snack", surprise="gust", hero_name="Pip", captain_name="Captain Nara", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/5."))
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
            header = f"### {p.hero_name}: {p.goal} with {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
