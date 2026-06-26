#!/usr/bin/env python3
"""
storyworlds/worlds/repeat_cautionary_dialogue_inner_monologue_pirate_tale.py
============================================================================

A small pirate-tale story world about a child pirate, a tempting repeat action,
a cautionary warning, dialogue, and a brief inner monologue.

Premise:
- A young pirate finds something shiny or exciting on the deck or shore.
- A captain or mate warns that repeating a risky action will cause trouble.
- The child argues, thinks to themselves, then chooses a safer, cleverer way.
- The ending proves what changed: the deck stays safe, the treasure stays put,
  and the child learns a useful pirate lesson.

The domain is intentionally compact:
- physical state is tracked with meters
- emotional state is tracked with memes
- dialogue and inner monologue are driven by state, not swapped-in nouns
- a cautionary warning can be repeated, and repetition can escalate concern

This script supports:
default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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

ASP_RULES = r"""
% A risky repeat action is valid only if the setting supports it and the caution
% has a believable fix.
risky(A) :- action(A), danger(A, D), D > 0.
repeatable(A) :- risky(A), can_repeat(A).
safe_choice(A) :- risky(A), repeatable(A), has_fix(A).

valid_story(Place, Action, Treasure, Crew) :-
    setting(Place), action(Action), treasure(Treasure), crew_role(Crew),
    affords(Place, Action), endangered_by(Action, Treasure), has_fix(Action).
"""

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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    captain: object | None = None
    hero: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "captain", "woman"}
        male = {"boy", "pirate", "man", "mate", "first mate", "sailor"}
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
    affords: set[str] = field(default_factory=set)
    salt_air: bool = False
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
class Action:
    id: str
    verb: str
    gerund: str
    caution: str
    repeat_line: str
    risk: str
    repeat_risk: str
    meter: str
    effect: str
    keyword: str
    can_repeat: bool = True
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
class Treasure:
    id: str
    label: str
    phrase: str
    region: str
    guard: str
    fragile: bool = True
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
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str]
    blocks: set[str]
    plural: bool = False
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.repeat_count: dict[str, int] = {}

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.repeat_count = dict(self.repeat_count)
        return clone


def _apply_risk(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for act_id, count in world.repeat_count.items():
            if count < 1:
                continue
            if actor.meters.get(act_id, 0.0) < THRESHOLD:
                continue
            action = _safe_lookup(ACTIONS, act_id)
            if actor.meters.get(action.meter, 0.0) < THRESHOLD:
                continue
            sig = ("risk", actor.id, act_id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["trouble"] = actor.memes.get("trouble", 0.0) + 1
            out.append(f"The second time made the trouble feel closer.")
    return out


def _apply_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for act_id, count in world.repeat_count.items():
            if count < 1:
                continue
            action = _safe_lookup(ACTIONS, act_id)
            if actor.meters.get(action.meter, 0.0) < THRESHOLD:
                continue
            for thing in list(world.entities.values()):
                if thing.worn_by != actor.id:
                    continue
                if thing.id == "gear":
                    continue
                sig = ("soil", actor.id, thing.id, act_id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                thing.meters["mess"] = thing.meters.get("mess", 0.0) + 1
                out.append(f"{thing.label.capitalize()} would not like a second round of that.")
    return out


CAUSAL_RULES = [_apply_risk, _apply_soil]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule(world)
            if res:
                changed = True
                produced.extend(res)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_repeat(world: World, actor: Entity, action: Action, treasure_id: str) -> dict[str, object]:
    sim = world.copy()
    do_action(sim, sim.get(actor.id), action, narrate=False)
    do_action(sim, sim.get(actor.id), action, narrate=False)
    treasure = sim.get(treasure_id)
    return {
        "mess": treasure.meters.get("mess", 0.0),
        "trouble": actor.memes.get("trouble", 0.0),
    }


def choose_fix(action: Action, treasure: Treasure) -> Optional[Fix]:
    for fix in FIXES:
        if action.id in fix.blocks and treasure.region in fix.protects:
            return fix
    return None


def deck_detail(setting: Setting) -> str:
    if setting.salt_air:
        return f"The salty air rolled over {setting.place}, and the ropes creaked softly."
    return f"{setting.place.capitalize()} was close and quiet, with planks underfoot."


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a young pirate with bright eyes and a brave hat, always listening for a good secret."
    )


def loves(world: World, hero: Entity, action: Action) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved to {action.verb}, because {action.keyword} felt exciting on a windy deck."
    )


def treasure_intro(world: World, hero: Entity, treasure: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    treasure.worn_by = hero.id
    world.say(
        f"One day, {hero.id} found {hero.pronoun('possessive')} {treasure.label} and tucked {treasure.it()} close."
    )


def arrive(world: World) -> None:
    world.say(deck_detail(world.setting))


def caution(world: World, captain: Entity, hero: Entity, action: Action, treasure: Entity) -> bool:
    pred = predict_repeat(world, hero, action, treasure.id)
    if pred["mess"] < THRESHOLD:
        return False
    world.facts["predicted_mess"] = action.effect
    world.say(
        f'"{action.caution}," said {captain.id}. "Repeat it again and {treasure.label} could get {action.effect}."'
    )
    return True


def dialogue_pushback(world: World, hero: Entity, action: Action) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(f'"But I only did it once," said {hero.id}. "One more time will be fine."')


def inner_monologue(world: World, hero: Entity, action: Action, treasure: Entity) -> None:
    fear = world.facts.get("predicted_mess", action.effect)
    world.say(
        f"{hero.id} looked down at {treasure.label} and thought, maybe the captain was right; "
        f"the second try could leave {treasure.it()} {fear}."
    )


def do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    actor.meters[action.id] = actor.meters.get(action.id, 0.0) + 1
    actor.meters[action.meter] = actor.meters.get(action.meter, 0.0) + 1
    world.repeat_count[action.id] = world.repeat_count.get(action.id, 0) + 1
    propagate(world, narrate=narrate)


def follow_fix(world: World, hero: Entity, action: Action, treasure: Entity, fix: Fix) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f'"A better way then," said {hero.id}, and {hero.pronoun()} chose to {fix.prep} instead of repeating the risky bit.'
    )
    world.say(
        f"{hero.id} {fix.tail}. After that, {hero.pronoun()} could {action.verb} once more, and {treasure.label} stayed safe."
    )


def tell(setting: Setting, action: Action, treasure_cfg: Treasure,
         hero_name: str = "Mara", hero_type: str = "girl",
         captain_name: str = "Captain Reed", captain_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_type))
    treasure = world.add(Entity(
        id="treasure",
        type=treasure_cfg.id,
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        owner=hero.id,
        region=treasure_cfg.region,
    ))

    introduce(world, hero)
    loves(world, hero, action)
    treasure_intro(world, hero, treasure)

    world.para()
    arrive(world)
    caution(world, captain, hero, action, treasure)
    dialogue_pushback(world, hero, action)
    do_action(world, hero, action, narrate=True)
    inner_monologue(world, hero, action, treasure)

    world.para()
    do_action(world, hero, action, narrate=True)
    fix = choose_fix(action, treasure)
    if fix:
        follow_fix(world, hero, action, treasure, fix)

    world.facts.update(
        hero=hero,
        captain=captain,
        treasure=treasure,
        action=action,
        setting=setting,
        fix=fix,
        repeated=world.repeat_count.get(action.id, 0) >= 2,
        warned=True,
    )
    return world


SETTINGS = {
    "deck": Setting(place="the deck", affords={"peek", "hide", "sing"}, salt_air=True),
    "harbor": Setting(place="the harbor", affords={"peek", "hide", "sing"}, salt_air=True),
    "cove": Setting(place="the cove", affords={"peek", "hide", "sing"}, salt_air=True),
}

ACTIONS = {
    "peek": Action(
        id="peek",
        verb="peek at the map",
        gerund="peeking at the map",
        caution="Don't keep peeking at the map in the wind",
        repeat_line="peeked at it again",
        risk="the map could fly away",
        repeat_risk="the map could tear or blow overboard",
        meter="squint",
        effect="blown overboard",
        keyword="map",
        can_repeat=True,
    ),
    "hide": Action(
        id="hide",
        verb="hide the key",
        gerund="hiding the key",
        caution="Don't keep hiding the key in the same loose place",
        repeat_line="hid it again",
        risk="the key could slip into a crack",
        repeat_risk="the key could vanish under a plank",
        meter="nest",
        effect="lost under the boards",
        keyword="key",
        can_repeat=True,
    ),
    "sing": Action(
        id="sing",
        verb="sing a sea shanty",
        gerund="singing a sea shanty",
        caution="Don't keep singing so loud that you scare the gulls",
        repeat_line="sang it again",
        risk="the gulls could crowd the rail",
        repeat_risk="the gulls could swoop down and make a mess",
        meter="volume",
        effect="stirred up by the gulls",
        keyword="shanty",
        can_repeat=True,
    ),
}

TREASURES = {
    "map": Treasure(
        id="map",
        label="map",
        phrase="a curled paper map with a red X",
        region="hand",
        guard="kept dry",
    ),
    "key": Treasure(
        id="key",
        label="key",
        phrase="a small brass key",
        region="pocket",
        guard="kept hidden",
    ),
    "feather": Treasure(
        id="feather",
        label="parrot feather",
        phrase="a bright parrot feather",
        region="hat",
        guard="kept still",
    ),
}

FIXES = [
    Fix(
        id="glass",
        label="a glass jar",
        prep="hold the map under a glass jar",
        tail="placed the map under a glass jar",
        protects={"hand"},
        blocks={"peek"},
    ),
    Fix(
        id="pouch",
        label="a tied pouch",
        prep="tie the key into a pouch",
        tail="tied the key into a pouch",
        protects={"pocket"},
        blocks={"hide"},
    ),
    Fix(
        id="whistle",
        label="a quiet whistle",
        prep="use a quiet whistle for a signal",
        tail="used a quiet whistle instead of another loud song",
        protects={"hat"},
        blocks={"sing"},
    ),
]

GIRL_NAMES = ["Mara", "Lena", "Tia", "Nia", "Ivy", "Rosa"]
BOY_NAMES = ["Finn", "Jory", "Pip", "Tom", "Rey", "Ollie"]


@dataclass
class StoryParams:
    place: str
    action: str
    treasure: str
    name: str
    gender: str
    captain: str
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
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIONS, act_id)
            for tr_id, tr in TREASURES.items():
                if choose_fix(act, tr) is not None:
                    combos.append((place, act_id, tr_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with repeat cautionary dialogue and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--captain", default="Captain Reed")
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
    if getattr(args, "action", None) and getattr(args, "treasure", None):
        if choose_fix(_safe_lookup(ACTIONS, getattr(args, "action", None)), _safe_lookup(TREASURES, getattr(args, "treasure", None))) is None:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, treasure = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, action=action, treasure=treasure, name=name, gender=gender, captain=getattr(args, "captain", None))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, action, treasure = f["hero"], f["action"], f["treasure"]
    return [
        f'Write a short pirate tale for a small child that includes the word "{action.keyword}" and a warning about repeating a risky action.',
        f"Tell a story where {hero.id} wants to {action.verb} again, but {f['captain'].id} worries about {treasure.label}.",
        f"Write a gentle pirate story with dialogue, an inner thought, and a safer way to handle {action.keyword}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, treasure, action = f["hero"], f["captain"], f["treasure"], f["action"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do again on the pirate deck?",
            answer=f"{hero.id} wanted to {action.verb} again, because {action.keyword} felt exciting.",
        ),
        QAItem(
            question=f"Who warned {hero.id} about repeating the risky action?",
            answer=f"{captain.id} warned {hero.id} with a careful pirate caution about {treasure.label}.",
        ),
        QAItem(
            question=f"What was the shiny thing {hero.id} cared about during the story?",
            answer=f"It was {treasure.phrase}, which {hero.id} kept close at first.",
        ),
    ]
    if f.get("fix"):
        fix = _safe_fact(world, f, "fix")
        qa.append(QAItem(
            question=f"How did the safer plan help {hero.id} in the end?",
            answer=f"{hero.id} used {fix.label} and could keep going without ruining {treasure.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a captain on a ship?",
            answer="A captain is the leader of the ship, the person who helps keep the crew safe and gives the big directions.",
        ),
        QAItem(
            question="What is a map for?",
            answer="A map shows where places are and helps sailors find the way across the sea.",
        ),
        QAItem(
            question="What does it mean to be cautious?",
            answer="Being cautious means being careful before acting, especially when something might go wrong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"repeat_count={world.repeat_count}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="deck", action="peek", treasure="map", name="Mara", gender="girl", captain="Captain Reed"),
    StoryParams(place="harbor", action="hide", treasure="key", name="Finn", gender="boy", captain="Captain Reed"),
    StoryParams(place="cove", action="sing", treasure="feather", name="Tia", gender="girl", captain="Captain Reed"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("danger", aid, 1))
        if a.can_repeat:
            lines.append(asp.fact("can_repeat", aid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("endangered_by", "peek", tid) if tid == "map" else "")
        lines.append(asp.fact("endangered_by", "hide", tid) if tid == "key" else "")
        lines.append(asp.fact("endangered_by", "sing", tid) if tid == "feather" else "")
        lines.append(asp.fact("worn_on", tid, t.region))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for p in sorted(fx.protects):
            lines.append(asp.fact("protects_region", fx.id, p))
    lines.append(asp.fact("crew_role", "captain"))
    lines.append(asp.fact("crew_role", "mate"))
    return "\n".join(l for l in lines if l)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
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
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(TREASURES, params.treasure),
                 params.name, params.gender, params.captain)
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
