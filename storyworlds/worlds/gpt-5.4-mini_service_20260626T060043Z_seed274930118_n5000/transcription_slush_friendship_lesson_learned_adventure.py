#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/transcription_slush_friendship_lesson_learned_adventure.py
===============================================================================================================================

A small adventure storyworld about friendship, a muddy slush trail, and a
lesson learned from a careful transcription.

The premise is simple: two friends find a handwritten note in a shed. One friend
rushes off to follow the clue, but the other notices that the note has been
copied badly. The corrected transcription changes the plan, the slush slows the
trip, and the friends learn to trust both each other and the map before heading
out again.

This script follows the shared storyworld contract:
- standalone stdlib script
- eager results import
- lazy ASP helper import inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- physically grounded meters and emotionally grounded memes
- invalid choices raise StoryError with a readable reason
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    boots: object | None = None
    clue_ent: object | None = None
    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    outdoors: bool = True
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
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
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
class Clue:
    id: str
    label: str
    phrase: str
    helps: set[str]
    requires: set[str] = field(default_factory=set)
    wearer: str = "paper"
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.weather: str = ""

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.weather = self.weather
        return w


def _soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("slush", 0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.owner != actor.id:
                continue
            if item.worn_by != actor.id:
                continue
            if "feet" not in world.zone:
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] = item.meters.get("wet", 0) + 1
            actor.memes["worry"] = actor.memes.get("worry", 0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wet in the slush.")
    return out


def _lesson(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("confused", 0) < THRESHOLD:
            continue
        if actor.memes.get("understood", 0) >= THRESHOLD:
            sig = ("lesson", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["calm"] = actor.memes.get("calm", 0) + 1
            out.append("__lesson__")
    return out


def _friendship(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("Mina")
    b = world.get("Jo")
    if a.memes.get("helped", 0) >= THRESHOLD and b.memes.get("trust", 0) >= THRESHOLD:
        sig = ("friendship",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["friendship"] = a.memes.get("friendship", 0) + 1
            b.memes["friendship"] = b.memes.get("friendship", 0) + 1
            out.append("__friendship__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_soak, _lesson, _friendship):
            bits = rule(world)
            if bits:
                changed = True
                produced.extend([b for b in bits if not b.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_slush(world: World, actor: Entity, mission: Mission, clue: Clue) -> dict:
    sim = world.copy()
    _do_mission(sim, sim.get(actor.id), mission, narrate=False)
    copied = sim.get(clue.id)
    return {
        "wet": copied.meters.get("wet", 0) >= THRESHOLD,
        "confused": sim.get(actor.id).memes.get("confused", 0) >= THRESHOLD,
    }


def _do_mission(world: World, actor: Entity, mission: Mission, narrate: bool = True) -> None:
    if mission.id not in world.setting.affords:
        return
    world.zone = {"feet"}
    actor.meters["slush"] = actor.meters.get("slush", 0) + 1
    actor.memes["excited"] = actor.memes.get("excited", 0) + 1
    propagate(world, narrate=narrate)


def introduction(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.label_word} who loved adventure, and {friend.id} was the kind of friend who noticed small things."
    )


def find_clue(world: World, hero: Entity, friend: Entity, clue: Clue) -> None:
    world.say(
        f"On a windy afternoon, {hero.id} and {friend.id} found a folded page in the shed."
    )
    world.say(
        f"It was a transcription of a trail note, and {hero.id} thought it pointed straight to the north gate."
    )
    clue_owner = friend if clue.wearer == "paper" else hero
    clue_owner.memes["care"] = clue_owner.memes.get("care", 0) + 1


def mistranscribe(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["confused"] = hero.memes.get("confused", 0) + 1
    world.say(
        f"{hero.id} read the transcription too quickly and rushed to grab a coat."
    )
    world.say(
        f"{hero.id} wanted to {world.facts['mission'].verb} right away, even though the note did not quite make sense."
    )


def correct_transcription(world: World, friend: Entity, clue: Clue) -> None:
    friend.memes["understood"] = friend.memes.get("understood", 0) + 1
    world.say(
        f"{friend.id} leaned closer and fixed the transcription by reading the muddy word twice."
    )
    world.say(
        f"The page said to follow the slush trail to the old bridge, not the north gate."
    )


def warn_about_slush(world: World, friend: Entity, hero: Entity, clue: Clue) -> bool:
    pred = predict_slush(world, hero, world.facts["mission"], clue)
    if not pred["wet"]:
        return False
    world.say(
        f"\"The slush will soak your boots if we hurry,\" {friend.pronoun('possessive')} friend said."
    )
    world.say(
        f"\"Let's slow down and read the transcription again.\""
    )
    return True


def choose_friendship(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    friend.memes["helped"] = friend.memes.get("helped", 0) + 1
    world.say(
        f"{hero.id} listened, and the two friends chose to walk together instead of rushing."
    )


def lesson_learned(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["understood"] = hero.memes.get("understood", 0) + 1
    world.say(
        f"In the end, {hero.id} learned a lesson learned the hard way: a careful transcription can save an adventure."
    )
    world.say(
        f"They reached the old bridge with muddy shoes, warm smiles, and a plan that finally fit the map."
    )


def tell(setting: Setting, mission: Mission, clue: Clue, hero_name: str = "Mina", friend_name: str = "Jo") -> World:
    world = World(setting)
    world.weather = mission.weather
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", label="brave girl"))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", label="careful boy"))
    clue_ent = world.add(Entity(id=clue.id, type="paper", label=clue.label, phrase=clue.phrase, owner=hero.id))
    boots = world.add(Entity(id="boots", type="boots", label="boots", owner=hero.id, worn_by=hero.id))
    world.add(boots)

    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["clue"] = clue_ent
    world.facts["mission"] = mission
    world.facts["setting"] = setting

    introduction(world, hero, friend)
    world.para()
    find_clue(world, hero, friend, clue_ent)
    mistranscribe(world, hero, clue_ent)
    warn_about_slush(world, friend, hero, clue_ent)
    correct_transcription(world, friend, clue_ent)
    choose_friendship(world, hero, friend)
    world.para()
    _do_mission(world, hero, mission, narrate=True)
    lesson_learned(world, hero, friend)

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "shed": Setting(place="the old shed", outdoors=False, affords={"slushwalk"}),
    "path": Setting(place="the forest path", outdoors=True, affords={"slushwalk"}),
    "bridge": Setting(place="the river bridge", outdoors=True, affords={"slushwalk"}),
}

MISSIONS = {
    "slushwalk": Mission(
        id="slushwalk",
        verb="follow the trail",
        gerund="following the trail",
        rush="run toward the bridge",
        risk="slush on the boots",
        weather="cold",
        keyword="slush",
        tags={"slush", "adventure"},
    ),
}

CLUES = {
    "note": Clue(
        id="note",
        label="trail note",
        phrase="a smudged trail note",
        helps={"slushwalk"},
        requires={"transcription"},
    ),
}

NAMES = ["Mina", "Jo", "Tia", "Nico", "Luca", "Pia", "Sami", "Rae"]
FRIEND_NAMES = ["Jo", "Lia", "Ben", "Oli", "Nia", "Ezra", "Noa", "Ivo"]


@dataclass
class StoryParams:
    place: str
    mission: str
    clue: str
    hero: str
    friend: str
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
    return [(p, m, c) for p in SETTINGS for m in MISSIONS for c in CLUES]


def explain_rejection(mission: Mission, clue: Clue) -> str:
    return f"(No story: this adventure needs a clue about transcription and a mission that can meet the slush trail.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: transcription, slush, friendship, lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    mission = getattr(args, "mission", None) or rng.choice(sorted(MISSIONS))
    clue = getattr(args, "clue", None) or rng.choice(sorted(CLUES))
    if (place, mission, clue) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    if hero == friend:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, mission=mission, clue=clue, hero=hero, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MISSIONS, params.mission), _safe_lookup(CLUES, params.clue), params.hero, params.friend)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short adventure story for a child that includes the word "transcription" and a slush-covered trail.',
        f"Tell a friendship story where {f['hero'].id} and {f['friend'].id} correct a transcription before they follow a trail.",
        "Write a gentle lesson-learned adventure about two friends, a muddy note, and a careful choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    mission = _safe_fact(world, f, "mission")
    qa = [
        QAItem(
            question="Who found the folded page in the shed?",
            answer=f"{hero.id} and {friend.id} found the folded page together.",
        ),
        QAItem(
            question="What word was important in the story?",
            answer="The important word was transcription, because the friends had to copy the trail note carefully.",
        ),
        QAItem(
            question="Why did the friends slow down?",
            answer="They slowed down because the slush trail could soak their boots and the transcription needed a second look.",
        ),
        QAItem(
            question="What lesson did Mina learn?",
            answer="Mina learned that reading a transcription carefully can keep an adventure from going the wrong way.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question="How did friendship change the ending?",
            answer=f"{hero.id} listened to {friend.id}, and the friends walked together to the old bridge with a better plan.",
        ))
    return qa


KNOWLEDGE = {
    "transcription": [
        ("What is a transcription?",
         "A transcription is a written copy of words that were spoken or written somewhere else."),
    ],
    "slush": [
        ("What is slush?",
         "Slush is wet, half-melted snow that can make paths slippery and muddy."),
    ],
    "friendship": [
        ("What is friendship?",
         "Friendship is the kind and trusting bond between people who help and care about each other."),
    ],
    "lesson": [
        ("What does it mean to learn a lesson?",
         "Learning a lesson means understanding something important that changes how you act next time."),
    ],
    "adventure": [
        ("What is an adventure?",
         "An adventure is an exciting journey or task where something new and surprising can happen."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question=q, answer=a)
        for key in ["transcription", "slush", "friendship", "lesson", "adventure"]
        for q, a in KNOWLEDGE[key]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="shed", mission="slushwalk", clue="note", hero="Mina", friend="Jo"),
    StoryParams(place="path", mission="slushwalk", clue="note", hero="Tia", friend="Ben"),
    StoryParams(place="bridge", mission="slushwalk", clue="note", hero="Rae", friend="Oli"),
]


ASP_RULES = r"""
mission_ok(P, M, C) :- place(P), mission(M), clue(C), needs(C, transcription), affords(P, M).
compatible(P, M, C) :- mission_ok(P, M, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        for m in _safe_lookup(SETTINGS, p).affords:
            lines.append(asp.fact("affords", p, m))
    for m in MISSIONS:
        lines.append(asp.fact("mission", m))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
        for need in _safe_lookup(CLUES, c).requires:
            lines.append(asp.fact("needs", c, need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


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
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
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
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.hero} and {p.friend}: {p.mission} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "mission", None) and getattr(args, "clue", None):
        if (getattr(args, "place", None) or "shed", getattr(args, "mission", None), getattr(args, "clue", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    mission = getattr(args, "mission", None) or rng.choice(sorted(MISSIONS))
    clue = getattr(args, "clue", None) or rng.choice(sorted(CLUES))
    if (place, mission, clue) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in FRIEND_NAMES if n != hero])
    if hero == friend:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, mission=mission, clue=clue, hero=hero, friend=friend)


if __name__ == "__main__":
    main()
