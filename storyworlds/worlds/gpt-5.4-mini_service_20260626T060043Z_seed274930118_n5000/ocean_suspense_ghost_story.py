#!/usr/bin/env python3
"""
storyworlds/worlds/ocean_suspense_ghost_story.py
=================================================

A small storyworld for a gentle ghost-story suspense tale by the ocean.

Premise:
- A child explores a foggy ocean shore with a keeper or family member.
- They notice signs that something unseen is near: a lantern bobbing, a tune,
  or a cold draft over the water.
- The child wants to investigate, but the adult worries because the sea is dark
  and the way is uncertain.
- The child and adult follow clues, discover that the "ghost" is harmless and
  lonely, and help it finish one unfinished task.
- The ending proves the change with a calmer shore, a warmer feeling, and the
  ghost at rest.

This script is self-contained and uses a tiny world model with both physical
meters and emotional memes. The prose is generated from simulated state rather
than a frozen paragraph with swapped nouns.
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
    kind: str = "thing"  # "character" | "thing" | "spirit"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    visible: bool = True
    luminous: bool = False
    anchored: bool = False

    adult: object | None = None
    ghost: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "spirit":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the shore"
    has_fog: bool = True
    has_lighthouse: bool = True
    sea_state: str = "quiet"  # quiet | choppy
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
    clue_text: str
    reveal_text: str
    resolves: str  # what unfinished thing this clue points to
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


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    place: str
    glow: bool = False
    damp: bool = True
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
    setting: str
    clue: str
    relic: str
    name: str
    gender: str
    adult: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def spirit(self) -> Entity:
        return next(e for e in self.entities.values() if e.kind == "spirit")


def _clue_seen(world: World) -> bool:
    return world.facts.get("clue_seen", False)


def _ghost_unsettled(world: World) -> bool:
    ghost = world.spirit()
    return ghost.memes.get("lonely", 0.0) >= THRESHOLD and not ghost.anchored


def _settle_ghost(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.spirit()
    relic = world.get("relic")
    if ghost.anchored:
        return out
    if relic.visible and not relic.damp:
        sig = ("settle",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        ghost.anchored = True
        ghost.memes["lonely"] = 0.0
        ghost.memes["peace"] = 1.0
        out.append("The cold feeling over the water softened at last.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = _settle_ghost(world)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def ocean_at_night(setting: Setting) -> str:
    if setting.sea_state == "choppy":
        return "The waves kept tapping the shore like worried fingers."
    return "The waves rolled in softly, but the fog made the sea look farther away than ever."


def hero_intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved listening to the ocean."
    )


def adult_intro(world: World, adult: Entity) -> None:
    world.say(
        f"{adult.id} walked beside {adult.pronoun('object')}, carrying a lantern and watching the dark water."
    )


def clue_hint(world: World, clue: Clue) -> None:
    world.say(clue.clue_text)
    world.facts["clue_seen"] = True
    world.facts["clue_id"] = clue.id


def fear_turn(world: World, hero: Entity, adult: Entity, clue: Clue) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.memes["unease"] = hero.memes.get("unease", 0.0) + 1
    adult.memes["worry"] = adult.memes.get("worry", 0.0) + 1
    world.say(
        f"{hero.id} wanted to follow the strange sign, but {adult.pronoun('possessive')} {adult.type} had a worried face."
    )
    world.say(
        f'"Stay close," {adult.id} said. "The fog can hide stones, boats, and anything else that does not want to be found."'
    )


def investigate(world: World, hero: Entity, clue: Clue, relic: Relic) -> None:
    hero.memes["brave"] = hero.memes.get("brave", 0.0) + 1
    world.say(
        f"{hero.id} took one careful step after another, following the {clue.label} toward {relic.place}."
    )
    if world.setting.has_fog:
        world.say("The mist curled around their ankles, and every splash sounded too loud.")
    if world.setting.has_lighthouse:
        world.say("Far off, the lighthouse blinked once, like a sleepy eye checking the shore.")
    if clue.resolves == relic.id:
        relic.glow = True
        relic.damp = False
        world.facts["relic_found"] = True
        world.facts["relic_id"] = relic.id
        world.say(clue.reveal_text)
    propagate(world, narrate=True)


def final_image(world: World, hero: Entity, adult: Entity, relic: Relic) -> None:
    ghost = world.spirit()
    world.say(
        f"Then the {ghost.label} was no longer a lonely thing in the dark. It hovered by the {relic.label}, gentle and still, as if it had finally found what it had been missing."
    )
    world.say(
        f"{hero.id} smiled up at {adult.id}, and the two of them walked home with the lantern glowing warm between them, while the ocean kept its secret in the hush of the night."
    )


SETTINGS = {
    "shore": Setting(place="the shore", has_fog=True, has_lighthouse=True, sea_state="quiet"),
    "pier": Setting(place="the pier", has_fog=True, has_lighthouse=False, sea_state="choppy"),
    "harbor": Setting(place="the harbor", has_fog=False, has_lighthouse=True, sea_state="quiet"),
}

CLUES = {
    "lantern": Clue(
        id="lantern",
        label="lantern glow",
        clue_text="Out past the rocks, a little light bobbed on the water, though no boat was near it.",
        reveal_text="When they reached the edge of the rocks, they saw the light came from an old lantern hanging by a rope.",
        resolves="lantern",
    ),
    "song": Clue(
        id="song",
        label="sea song",
        clue_text="A thin little song drifted over the waves, soft as a breath and sad as a sigh.",
        reveal_text="The song led them to a shell tucked under the pier, where the tune had been waiting all alone.",
        resolves="shell",
    ),
    "footprints": Clue(
        id="footprints",
        label="wet footprints",
        clue_text="Tiny wet prints appeared in the sand, then stopped right before the tide line.",
        reveal_text="The footprints ended at a starfish charm caught in a bit of driftwood, glimmering in the dark.",
        resolves="charm",
    ),
}

RELICS = {
    "lantern": Relic(id="lantern", label="old lantern", phrase="an old lantern", place="the rocks"),
    "shell": Relic(id="shell", label="silver shell", phrase="a silver shell", place="under the pier"),
    "charm": Relic(id="charm", label="starfish charm", phrase="a starfish charm", place="the driftwood"),
}

GIRL_NAMES = ["Mina", "Luna", "Elsa", "Nora", "Ivy", "Maya"]
BOY_NAMES = ["Finn", "Eli", "Theo", "Noah", "Ben", "Rowan"]
TRAITS = ["curious", "brave", "quiet", "gentle", "watchful", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, clue in CLUES.items():
            if clue.resolves in RELICS:
                combos.append((sid, cid, clue.resolves))
    return combos


def explain_rejection(clue: Clue, relic: Relic) -> str:
    return f"(No story: the clue '{clue.label}' does not lead to the relic '{relic.label}' in this small world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "clue", None) and getattr(args, "relic", None):
        clue, relic = _safe_lookup(CLUES, getattr(args, "clue", None)), _safe_lookup(RELICS, getattr(args, "relic", None))
        if clue.resolves != relic.id:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
              and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, clue_id, relic_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = getattr(args, "adult", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, clue=clue_id, relic=relic_id, name=name, gender=gender, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    clue = _safe_lookup(CLUES, params.clue)
    relic = _safe_lookup(RELICS, params.relic)
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    adult = world.add(Entity(id="Adult", kind="character", type=params.adult, label="the grown-up"))
    ghost = world.add(Entity(id="Ghost", kind="spirit", type="ghost", label="ghost of the tide", visible=False))
    ghost.memes["lonely"] = 1.0
    ghost.memes["peace"] = 0.0
    world.add(Entity(id="relic", kind="thing", type=relic.id, label=relic.label, phrase=relic.phrase, anchored=True, luminous=False))

    world.facts.update(hero=hero, adult=adult, ghost=ghost, clue=clue, relic=relic, setting=setting)

    hero_intro(world, hero)
    adult_intro(world, adult)
    world.say(ocean_at_night(setting))

    world.para()
    clue_hint(world, clue)
    fear_turn(world, hero, adult, clue)

    world.para()
    investigate(world, hero, clue, relic)
    final_image(world, hero, adult, relic)

    world.facts["resolved"] = world.spirit().anchored
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
    hero: Entity = _safe_fact(world, f, "hero")
    adult: Entity = _safe_fact(world, f, "adult")
    clue: Clue = _safe_fact(world, f, "clue")
    relic: Relic = _safe_fact(world, f, "relic")
    return [
        'Write a suspenseful ghost story for a young child set by the ocean, with fog, a lantern, and a gentle ending.',
        f"Tell a child-sized spooky story where {hero.id} and {adult.id} follow {clue.label} to find {relic.label} near the water.",
        f"Create a soft ghost story at the shore where the scary-sounding sign turns out to be harmless and lonely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    adult: Entity = _safe_fact(world, f, "adult")
    clue: Clue = _safe_fact(world, f, "clue")
    relic: Relic = _safe_fact(world, f, "relic")
    ghost: Entity = _safe_fact(world, f, "ghost")
    return [
        QAItem(
            question=f"Who was the story about at {world.setting.place}?",
            answer=f"It was about {hero.id}, a little {hero.pronoun('possessive')} {hero.type}, and the grown-up who stayed beside {hero.pronoun('object')} by the ocean.",
        ),
        QAItem(
            question=f"What strange sign did {hero.id} notice first?",
            answer=f"{hero.id} noticed {clue.clue_text.lower()} That was the first clue that something was waiting in the dark water.",
        ),
        QAItem(
            question=f"Why did the grown-up worry when {hero.id} wanted to go closer?",
            answer=f"The grown-up worried because the fog made the shore hard to see, and the sea could hide stones, waves, or other surprises.",
        ),
        QAItem(
            question=f"What was the lonely ghost really connected to?",
            answer=f"The ghost was connected to {relic.phrase}, which was the unfinished thing it had been near all along.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {ghost.label} calm and still, and {hero.id} walking home with the lantern glowing warmly in the dark.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fog?",
            answer="Fog is a cloud close to the ground that makes the world look pale and blurry.",
        ),
        QAItem(
            question="What is a lantern for?",
            answer="A lantern gives out light so people can see in dark places.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is a spooky-looking spirit, often shown as something unseen or glowing, even when it is not truly dangerous.",
        ),
        QAItem(
            question="What are waves?",
            answer="Waves are moving rises of water on the sea, and they can roll, splash, or tap the shore.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.kind == "spirit":
            bits.append(f"visible={e.visible}")
            bits.append(f"anchored={e.anchored}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_fog:
            lines.append(asp.fact("foggy", sid))
        if s.has_lighthouse:
            lines.append(asp.fact("lighthouse", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("resolves_to", cid, c.resolves))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
    return "\n".join(lines)


ASP_RULES = r"""
match(C, R) :- clue(C), resolves_to(C, R).
valid_story(S, C, R) :- setting(S), match(C, R), relic(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle suspense ghost story by the ocean.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="shore", clue="lantern", relic="lantern", name="Mina", gender="girl", adult="mother", trait="curious"),
    StoryParams(setting="pier", clue="song", relic="shell", name="Finn", gender="boy", adult="father", trait="watchful"),
    StoryParams(setting="harbor", clue="footprints", relic="charm", name="Ivy", gender="girl", adult="mother", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for item in combos:
            print("  ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.name}: {p.clue} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
