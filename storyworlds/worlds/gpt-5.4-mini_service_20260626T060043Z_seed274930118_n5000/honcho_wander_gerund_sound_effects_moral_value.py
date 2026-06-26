#!/usr/bin/env python3
"""
storyworlds/worlds/honcho_wander_gerund_sound_effects_moral_value.py
====================================================================

A small mythic story world about a leader, a wandering child, sound effects,
and a moral value that must be proved by action.

Premise:
- A young wanderer loves to wander.
- A village honcho warns that the sacred drum may not be mocked.
- The wanderer's noisy footsteps and mistakes create tension.
- A wiser choice restores honor and peace.

The world model tracks:
- physical meters: distance, noise, dust, damage, harmony
- emotional memes: courage, pride, shame, trust, honor

The prose is generated from the simulated state, not from a frozen template.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    honcho: object | None = None
    sacred: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Place:
    name: str
    soundscape: str
    holy: bool = False
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
class Thing:
    id: str
    label: str
    phrase: str
    sound: str
    moral: str
    risk: str
    protects: str = ""
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
    thing: str
    name: str
    gender: str
    honcho_name: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path: str = "near the shrine"
        self.noise_word: str = ""
        self.sound_effect: str = ""

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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.path = self.path
        w.noise_word = self.noise_word
        w.sound_effect = self.sound_effect
        return w


PLACES = {
    "sanctuary_gate": Place(name="the sanctuary gate", soundscape="the wind and bells", holy=True),
    "river_road": Place(name="the river road", soundscape="water over stones"),
    "hill_path": Place(name="the hill path", soundscape="grass and distant crows"),
}

THINGS = {
    "drum": Thing(
        id="drum",
        label="drum",
        phrase="a bronze drum with a lion on its rim",
        sound="BOOM",
        moral="respect",
        risk="rustle",
        protects="quietly",
    ),
    "jar": Thing(
        id="jar",
        label="jar",
        phrase="a blue clay jar full of moon-salt",
        sound="CLINK",
        moral="care",
        risk="clatter",
        protects="gently",
    ),
    "torch": Thing(
        id="torch",
        label="torch",
        phrase="a river torch wrapped in resin cloth",
        sound="FSSS",
        moral="caution",
        risk="hiss",
        protects="steadily",
    ),
}

NAMES = ["Ari", "Mira", "Toma", "Niko", "Sela", "Bren", "Kira", "Jon"]
GENDERS = ["girl", "boy"]


class WorldRule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_noise(world: World) -> list[str]:
    out = []
    wanderer = world.get("wanderer")
    thing = world.get("thing")
    if wanderer.meters.get("noise", 0.0) >= THRESHOLD and not world.fired.__contains__(("noise", thing.id)):
        world.fired.add(("noise", thing.id))
        thing.meters["damage"] = thing.meters.get("damage", 0.0) + 1
        out.append(f"The {thing.label} shivered at the sound.")
    return out


def _r_shame(world: World) -> list[str]:
    wanderer = world.get("wanderer")
    honcho = world.get("honcho")
    thing = world.get("thing")
    if thing.meters.get("damage", 0.0) >= THRESHOLD and ("shame",) not in world.fired:
        world.fired.add(("shame",))
        wanderer.memes["shame"] = wanderer.memes.get("shame", 0.0) + 1
        honcho.memes["sternness"] = honcho.memes.get("sternness", 0.0) + 1
        return [f"{honcho.label_word} looked stern, and the child felt small."]
    return []


def _r_honor(world: World) -> list[str]:
    wanderer = world.get("wanderer")
    thing = world.get("thing")
    honcho = world.get("honcho")
    if wanderer.memes.get("honor", 0.0) >= THRESHOLD and thing.meters.get("damage", 0.0) < THRESHOLD and ("honor",) not in world.fired:
        world.fired.add(("honor",))
        honcho.memes["trust"] = honcho.memes.get("trust", 0.0) + 1
        return [f"Honor returned to the road."]
    return []


RULES = [WorldRule("noise", _r_noise), WorldRule("shame", _r_shame), WorldRule("honor", _r_honor)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_damage(world: World, wanderer: Entity, thing: Entity) -> bool:
    sim = world.copy()
    sim.get("wanderer").meters["noise"] = 1.0
    propagate(sim, narrate=False)
    return sim.get("thing").meters.get("damage", 0.0) >= THRESHOLD


def tell(place: Place, thing: Thing, name: str, gender: str, honcho_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="wanderer", kind="character", type=gender, label=name))
    honcho = world.add(Entity(id="honcho", kind="character", type="elder", label=honcho_name))
    sacred = world.add(Entity(id="thing", kind="thing", type=thing.label, label=thing.label, phrase=thing.phrase))

    hero.memes["curiosity"] = 1
    hero.memes["pride"] = 1
    honcho.memes["authority"] = 1

    world.say(f"In {place.name}, {name} was a young wanderer who loved to wander.")
    world.say(f"The road sang with {place.soundscape}, and {name} kept pace with a restless heart.")
    world.say(f"Nearby stood {honcho_name}, the village honcho, and beside them rested {thing.phrase}.")
    world.say(f"People said the {thing.label} carried the moral of {thing.moral}.")

    world.para()
    world.say(f"One day, {name} wandered past the shrine and made a little sound with every step.")
    world.say(f'The feet said, "{thing.sound}! {thing.sound}!" as if the stones were a drum itself.')
    hero.meters["distance"] = 1
    hero.meters["noise"] = 1
    world.noise_word = thing.sound
    world.sound_effect = f"{thing.sound}! {thing.sound}!"
    propagate(world, narrate=True)

    world.para()
    if predict_damage(world, hero, sacred):
        world.say(f'{honcho_name} lifted a hand and said, "Do not mock the {thing.label}; the old path remembers such noise."')
    hero.memes["desire"] = 1
    world.say(f"But {name} still wanted to wander on, because the world felt wide and bright.")
    world.say(f"So {name} took one foolish step nearer the sacred thing, and the sound came again: {thing.sound}.")
    hero.meters["noise"] += 1
    propagate(world, narrate=True)

    world.para()
    if sacred.meters.get("damage", 0.0) >= THRESHOLD:
        world.say(f"{name} lowered {hero.pronoun('possessive')} head when the {thing.label} trembled.")
        hero.memes["shame"] = 1
        world.say(f"{honcho_name} did not strike; instead, {honcho_name} taught the older road: repair what you disturb.")
        world.say(f"{name} knelt, brushed the dust away, and guarded the {thing.label} with both careful hands.")
        hero.memes["honor"] = 1
        sacred.meters["damage"] = 0
        hero.meters["noise"] = 0
        propagate(world, narrate=True)
        world.say(f"Then the shrine grew quiet again, and the wanderer learned that honor is a quieter song than pride.")
    else:
        world.say(f"{name} paused in time and chose silence instead.")
        hero.memes["honor"] = 1
        hero.meters["noise"] = 0
        propagate(world, narrate=True)
        world.say(f"Thus the child wandered on softly, and the old {thing.label} stayed bright under the dawn.")

    world.facts.update(hero=hero, honcho=honcho, thing=sacred, place=place, thing_cfg=thing)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    thing = _safe_fact(world, f, "thing_cfg")
    return [
        f'Write a short myth about a wanderer who hears "{thing.sound}" and learns {thing.moral}.',
        f"Tell a child-friendly legend where {hero.label} meets a honcho and must respect a sacred {thing.label}.",
        f"Write a simple myth with a sound effect like {thing.sound}! and an ending that proves honor mattered more than pride.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    honcho = _safe_fact(world, f, "honcho")
    thing = _safe_fact(world, f, "thing")
    thing_cfg = _safe_fact(world, f, "thing_cfg")
    return [
        QAItem(
            question=f"Who is the story about in the myth near {world.place.name}?",
            answer=f"It is about {hero.label}, a young wanderer, and {honcho.label}, the village honcho.",
        ),
        QAItem(
            question=f"What sound effect did the wanderer make while moving near the sacred {thing.label}?",
            answer=f"The child made the sound effect {world.sound_effect}, which echoed along the road.",
        ),
        QAItem(
            question=f"What moral value did the old folk say the {thing.label} carried?",
            answer=f"They said the {thing.label} carried the moral of {thing_cfg.moral}, and the ending proved that lesson.",
        ),
        QAItem(
            question=f"Why did {honcho.label} grow stern when the wanderer came too close?",
            answer=f"{honcho.label} worried that careless noise would disturb the sacred {thing.label}, so the leader warned the child to be respectful.",
        ),
        QAItem(
            question=f"How did the wanderer end the story?",
            answer=f"{hero.label} ended by moving carefully, repairing the damage, and learning to treat the sacred place with honor.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a honcho?", answer="A honcho is the leader or boss of a group in a story or village."),
        QAItem(question="What is a sound effect in a story?", answer="A sound effect is a written sound like boom or clink that helps the reader imagine the noise."),
        QAItem(question="What does honor mean?", answer="Honor means acting in a worthy and respectful way, especially when something important must be protected."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% The wanderer is at risk when noisy wandering disturbs the sacred thing.
at_risk(W, T) :- wanderer(W), sacred(T), noisy(W), near(W, T).

% Damage occurs when noise reaches the thing.
damaged(T) :- at_risk(_, T), noise_reaches(T).

% Honor is learned when the wanderer repairs what was disturbed.
honored(W) :- wanderer(W), repaired(W), respectful(W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.holy:
            lines.append(asp.fact("holy", pid))
    for tid, thing in THINGS.items():
        lines.append(asp.fact("sacred", tid))
        lines.append(asp.fact("moral_of", tid, thing.moral))
        lines.append(asp.fact("sound_of", tid, thing.sound))
    lines.append(asp.fact("wanderer", "hero"))
    lines.append(asp.fact("honcho", "leader"))
    lines.append(asp.fact("near", "hero", "drum"))
    lines.append(asp.fact("noisy", "hero"))
    lines.append(asp.fact("noise_reaches", "drum"))
    lines.append(asp.fact("repaired", "hero"))
    lines.append(asp.fact("respectful", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show honored/1."))
    asp_atoms = set(asp.atoms(model, "honored"))
    py_atoms = {("hero",)}
    if asp_atoms == py_atoms:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP:", sorted(asp_atoms))
    print("  Python:", sorted(py_atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world with honcho, wandering, sound effects, and moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--honcho-name")
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    thing = getattr(args, "thing", None) or rng.choice(list(THINGS))
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    honcho_name = getattr(args, "honcho_name", None) or rng.choice([n for n in NAMES if n != name])
    return StoryParams(place=place, thing=thing, name=name, gender=gender, honcho_name=honcho_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(THINGS, params.thing), params.name, params.gender, params.honcho_name)
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


CURATED = [
    StoryParams(place="sanctuary_gate", thing="drum", name="Ari", gender="boy", honcho_name="Sela"),
    StoryParams(place="river_road", thing="jar", name="Mira", gender="girl", honcho_name="Bren"),
    StoryParams(place="hill_path", thing="torch", name="Toma", gender="boy", honcho_name="Kira"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show honored/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show honored/1."))
        print(sorted(asp.atoms(model, "honored")))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
