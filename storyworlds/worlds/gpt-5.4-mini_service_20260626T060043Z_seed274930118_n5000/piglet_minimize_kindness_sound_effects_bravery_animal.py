#!/usr/bin/env python3
"""
A small standalone storyworld for an Animal Story about a piglet who learns to
minimize noisy sound effects, show kindness, and be brave.

Seed premise:
- A piglet is curious about a noisy path of sound effects in the barnyard.
- The piglet's actions can either make the noise bigger or smaller.
- A gentle helper encourages kindness and bravery, leading to a calmer ending.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    heard: list[str] = field(default_factory=list)

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"piglet", "pig", "animal"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"fox", "boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"rabbit", "girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the barnyard"
    affords: set[str] = field(default_factory=lambda: {"squeak", "stomp", "shh"})
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
class Sound:
    id: str
    label: str
    verb: str
    effect: str
    quiet_alt: str
    loudness: int
    keyword: str
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
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
    helped_by: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_log: list[str] = []

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
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.events = set(self.events)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def loudness_total(world: World) -> int:
    return int(sum(e.meters.get("noise", 0) for e in world.entities.values()))


def quiet_total(world: World) -> int:
    return int(sum(e.meters.get("quiet", 0) for e in world.entities.values()))


def make_sound(world: World, actor: Entity, sound: Sound, narrate: bool = True) -> None:
    if sound.id not in world.setting.affords:
        pass
    sig = ("sound", actor.id, sound.id)
    if sig in world.events:
        return
    world.events.add(sig)
    actor.meters["noise"] = actor.meters.get("noise", 0) + sound.loudness
    actor.heard.append(sound.label)
    if narrate:
        world.say(f"{actor.id} {sound.verb}, and the {sound.label} went {sound.effect}.")


def quiet_action(world: World, actor: Entity, tool: Tool, narrate: bool = True) -> None:
    sig = ("quiet", actor.id, tool.id)
    if sig in world.events:
        return
    world.events.add(sig)
    actor.meters["quiet"] = actor.meters.get("quiet", 0) + 1
    actor.meters["noise"] = max(0, actor.meters.get("noise", 0) - 1)
    actor.memes["kindness"] = actor.memes.get("kindness", 0) + 1
    if narrate:
        world.say(
            f"{actor.id} tried {tool.phrase}, and the noise turned {tool.effect}."
        )


def bravery_turn(world: World, actor: Entity, helper: Entity) -> None:
    actor.memes["bravery"] = actor.memes.get("bravery", 0) + 1
    actor.memes["kindness"] = actor.memes.get("kindness", 0) + 1
    helper.memes["pride"] = helper.memes.get("pride", 0) + 1
    world.say(
        f"{actor.id} took a brave breath and listened to {helper.id}. "
        f"{actor.pronoun().capitalize()} chose the kinder, quieter way."
    )


def predict_noise(world: World, actor: Entity, sound: Sound, tool: Tool) -> dict:
    sim = world.copy()
    make_sound(sim, sim.get(actor.id), sound, narrate=False)
    quiet_action(sim, sim.get(actor.id), tool, narrate=False)
    return {
        "noise": loudness_total(sim),
        "quiet": quiet_total(sim),
    }


def tell(world: World, hero: Entity, helper: Entity, sound: Sound, tool: Tool) -> World:
    world.say(
        f"{hero.id} was a little piglet who loved gentle things and bright new sounds."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked kindness, because kind sounds made the barnyard feel safe."
    )
    world.para()
    world.say(
        f"One morning at {world.setting.place}, {hero.id} heard a {sound.label} and felt very curious."
    )
    world.say(
        f"{hero.id} wanted to {sound.verb}, but {helper.id} noticed the noise and frowned a little."
    )
    predicted = predict_noise(world, hero, sound, tool)
    world.facts["predicted_noise"] = predicted["noise"]
    world.facts["predicted_quiet"] = predicted["quiet"]
    if predicted["noise"] > 0:
        world.say(
            f'"If you do that, the sound may stay too big," {helper.id} said. '
            f'"Let\'s {tool.helped_by} instead."'
        )
    world.para()
    make_sound(world, hero, sound)
    if hero.meters.get("noise", 0) >= THRESHOLD:
        world.say(
            f"The loudness made {hero.id} pause. {hero.pronoun().capitalize()} did not want to bother anyone."
        )
    quiet_action(world, hero, tool)
    bravery_turn(world, hero, helper)
    world.say(
        f"In the end, {hero.id} still enjoyed the sound, but {hero.pronoun('possessive')} voice stayed small and soft."
    )
    world.say(
        f"The barnyard felt calmer, and {hero.id} looked proud of being both kind and brave."
    )
    world.facts.update(hero=hero, helper=helper, sound=sound, tool=tool)
    return world


SETTINGS = {
    "barnyard": Setting(place="the barnyard", affords={"squeak", "stomp", "shh"}),
    "orchard": Setting(place="the orchard", affords={"squeak", "rustle", "shh"}),
    "pond": Setting(place="the pond", affords={"splash", "squeak", "shh"}),
}

SOUNDS = {
    "squeak": Sound(
        id="squeak",
        label="squeak",
        verb="squeaks very loudly",
        effect="squeeeeak",
        quiet_alt="tiny squeak",
        loudness=2,
        keyword="squeak",
        tags={"sound", "animal"},
    ),
    "stomp": Sound(
        id="stomp",
        label="stomp",
        verb="stomps hard",
        effect="thump-thump",
        quiet_alt="soft step",
        loudness=2,
        keyword="stomp",
        tags={"sound", "animal"},
    ),
    "rustle": Sound(
        id="rustle",
        label="rustle",
        verb="rustles the leaves",
        effect="shhhh-rustle",
        quiet_alt="gentle rustle",
        loudness=1,
        keyword="rustle",
        tags={"sound", "nature"},
    ),
    "splash": Sound(
        id="splash",
        label="splash",
        verb="splashes at the water",
        effect="plip-plop",
        quiet_alt="small plip",
        loudness=1,
        keyword="splash",
        tags={"sound", "water"},
    ),
}

TOOLS = {
    "whisper": Tool(
        id="whisper",
        label="whispering",
        phrase="whispering into the straw",
        effect="smaller and kinder",
        helped_by="whisper softly",
        tags={"quiet", "kindness"},
    ),
    "breath": Tool(
        id="breath",
        label="slow breaths",
        phrase="taking slow brave breaths",
        effect="softer and steadier",
        helped_by="take slow brave breaths",
        tags={"bravery", "quiet"},
    ),
    "hoof_tap": Tool(
        id="hoof_tap",
        label="tiny hoof taps",
        phrase="tapping tiny hoof beats",
        effect="small and neat",
        helped_by="tap tiny hoof beats",
        tags={"quiet", "animal"},
    ),
}

HERO_NAMES = ["Pip", "Milo", "Mabel", "Rosie", "Nell", "Ollie", "Sunny"]
HELPER_NAMES = ["Mina", "Toby", "Hazel", "Fern", "June"]

CURATED = [
    ("barnyard", "squeak", "whisper", "Pip", "Mina"),
    ("orchard", "rustle", "breath", "Milo", "Hazel"),
    ("pond", "splash", "hoof_tap", "Rosie", "Toby"),
]


@dataclass
class StoryParams:
    place: str
    sound: str
    tool: str
    name: str
    helper_name: str
    seed: Optional[int] = None
    params: object | None = None
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
    out = []
    for place, setting in SETTINGS.items():
        for s in setting.affords:
            for t in TOOLS:
                out.append((place, s, t))
    return out


def explain_invalid(sound: Sound, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not reasonably help a piglet minimize {sound.label} in this setting.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: a piglet learns to minimize noisy sound effects with kindness and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    if getattr(args, "sound", None) and getattr(args, "tool", None):
        if getattr(args, "sound", None) == "stomp" and getattr(args, "tool", None) == "hoof_tap":
            pass
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "sound", None) is None or c[1] == getattr(args, "sound", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, sound, tool = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, sound=sound, tool=tool, name=name, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="piglet"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="rabbit"))
    sound = _safe_lookup(SOUNDS, params.sound)
    tool = _safe_lookup(TOOLS, params.tool)
    tell(world, hero, helper, sound, tool)
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
    hero = _safe_fact(world, f, "hero")
    sound = _safe_fact(world, f, "sound")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short Animal Story about a piglet named {hero.id} who hears a {sound.label} and learns to minimize the noise.',
        f"Tell a gentle story where {hero.id} is brave enough to try quieter sound effects and be kind to a friend.",
        f'Write a child-friendly story about {hero.id}, {sound.keyword}, kindness, and bravery at {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    sound = _safe_fact(world, f, "sound")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What kind of animal was {hero.id} in the story?",
            answer=f"{hero.id} was a little piglet.",
        ),
        QAItem(
            question=f"What noisy thing did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {sound.verb}.",
        ),
        QAItem(
            question=f"How did {hero.id} try to make the sound smaller?",
            answer=f"{hero.id} used {tool.phrase} to make the sound {tool.effect}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} be kinder and braver?",
            answer=f"{helper.id} helped {hero.id} be kinder and braver.",
        ),
        QAItem(
            question=f"Why did the helper worry about the sound?",
            answer=(
                f"The helper worried because a {sound.label} could get too big and bother others, so {hero.id} needed to minimize it."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be kind?",
            answer="Being kind means being gentle, helpful, and considerate of others' feelings.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary even when you feel nervous.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a noise that helps show what is happening, like a squeak or a thump.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
sound_valid(P, S, T) :- place(P), sound(S), tool(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for sid in SOUNDS:
        lines.append(asp.fact("sound", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show sound_valid/3."))
    return sorted(set(asp.atoms(model, "sound_valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    mapped = set(a)
    if mapped == b:
        print(f"OK: clingo gate matches valid_combos() ({len(b)} combos).")
        return 0
    print("MISMATCH")
    print("only in asp:", sorted(mapped - b))
    print("only in python:", sorted(b - mapped))
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
        print(asp_program("#show sound_valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, sound, tool in CURATED:
            params = StoryParams(place=place, sound=sound, tool=tool, name=random.choice(HERO_NAMES), helper_name=random.choice(HELPER_NAMES), seed=base_seed)
            samples.append(generate(params))
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
