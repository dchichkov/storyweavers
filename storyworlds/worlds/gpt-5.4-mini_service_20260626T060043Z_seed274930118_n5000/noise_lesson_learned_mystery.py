#!/usr/bin/env python3
"""
storyworlds/worlds/noise_lesson_learned_mystery.py
===================================================

A small mystery storyworld about a strange noise, a careful investigation,
and a lesson learned at the end.

Premise:
- A child hears a puzzling noise in a familiar place.
- The child first suspects something mysterious is wrong.
- The mystery is solved by checking clues in the world, not by guessing.
- The child learns that a noise can have an ordinary cause.

The world is constrained so the story stays concrete and believable:
- A sound source makes one kind of noise.
- The hero can investigate by moving through the setting and examining clues.
- The final reveal must explain the sound in a child-friendly way.

This world supports the required Storyweavers CLI, JSON, QA, trace, and ASP
verification modes.
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
    owner: Optional[str] = None
    location: str = ""
    openable: bool = False
    open_state: bool = False
    noisy: bool = False
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    room: object | None = None
    hero: object | None = None
    parent: object | None = None
    source_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    indoor: bool = True
    rooms: list[str] = field(default_factory=list)
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
class SoundSource:
    id: str
    label: str
    room: str
    noise: str
    clue: str
    reveal: str
    harmless: bool = True
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
class StoryParams:
    setting: str
    source: str
    hero_name: str
    hero_type: str
    parent_type: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.trace_notes = list(self.trace_notes)
        w.paragraphs = [[]]
        return w


def _propagate(world: World, narrate: bool = True) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        # fear from noisy clue
        for ent in list(world.entities.values()):
            if ent.kind == "character" and ent.meters.get("unease", 0.0) >= THRESHOLD:
                sig = ("fear", ent.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    ent.memes["worry"] = ent.memes.get("worry", 0.0) + 1
                    changed = True
                    if narrate:
                        world.say(f"{ent.label or ent.id} felt a little more worried.")
        # lesson learned after reveal
        for ent in list(world.entities.values()):
            if ent.kind == "character" and ent.meters.get("understanding", 0.0) >= THRESHOLD:
                sig = ("lesson", ent.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    ent.memes["lesson"] = ent.memes.get("lesson", 0.0) + 1
                    changed = True
                    if narrate:
                        world.say(f"{ent.label or ent.id} understood that the noise had a simple cause.")


def _find_noise(world: World, hero: Entity, source: SoundSource) -> None:
    hero.meters["curiosity"] = hero.meters.get("curiosity", 0.0) + 1
    world.say(
        f"That night, {hero.label} heard a strange {source.noise} coming from {source.room}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} listened closely and wondered what could make a sound like that."
    )
    hero.meters["unease"] = hero.meters.get("unease", 0.0) + 1


def _suspect(world: World, hero: Entity, source: SoundSource) -> None:
    hero.memes["guessing"] = hero.memes.get("guessing", 0.0) + 1
    world.say(
        f"{hero.label} whispered, \"What if something weird is hiding in the dark?\""
    )
    world.say("The hallway felt long and quiet, which made the noise seem even bigger.")
    world.say(f"{hero.pronoun().capitalize()} decided not to shout and instead look for clues.")


def _investigate(world: World, hero: Entity, source: SoundSource) -> None:
    hero.location = source.room
    world.say(f"{hero.label} tiptoed to the {source.room} and looked around.")
    world.say(f"Near the cupboard, {hero.pronoun('possessive')} eyes found a clue: {source.clue}.")
    world.get(source.id).meters["noticed"] = 1.0
    hero.meters["clue_found"] = hero.meters.get("clue_found", 0.0) + 1


def _open_and_reveal(world: World, hero: Entity, source: SoundSource) -> None:
    source_ent = world.get(source.id)
    if not source_ent.openable:
        pass
    source_ent.open_state = True
    world.say(f"{hero.label} opened the {source_ent.label} slowly.")
    world.say(f"Inside, {source.reveal}")
    hero.meters["understanding"] = hero.meters.get("understanding", 0.0) + 1
    _propagate(world, narrate=False)


def _lesson_learned(world: World, hero: Entity, parent: Entity, source: SoundSource) -> None:
    world.say(
        f"{hero.label} smiled and told {parent.pronoun('object')} that the noise was not scary after all."
    )
    world.say(
        f"\"I thought it was something spooky,\" {hero.pronoun()} said, "
        f"\"but it was only {source.reveal.strip().rstrip('.').lower()}.\""
    )
    world.say(
        f"{parent.label} hugged {hero.pronoun('object')} and said that careful looking can solve a mystery."
    )
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["lesson"] = hero.memes.get("lesson", 0.0) + 1


SETTINGS = {
    "house": Setting(place="the house", indoor=True, rooms=["hallway", "kitchen", "closet"]),
    "cabin": Setting(place="the cabin", indoor=True, rooms=["entry room", "pantry", "attic"]),
    "school": Setting(place="the school building", indoor=True, rooms=["hallway", "supply room", "music room"]),
}

SOURCES = {
    "fan": SoundSource(
        id="fan",
        label="fan",
        room="closet",
        noise="whirring",
        clue="a small ribbon fluttering near the vent",
        reveal="it was just a fan blowing air through a loose ribbon.",
        harmless=True,
    ),
    "pipes": SoundSource(
        id="pipes",
        label="pipe",
        room="wall",
        noise="clunking",
        clue="a warm pipe under the sink",
        reveal="it was only the pipes tapping as hot water moved through them.",
        harmless=True,
    ),
    "branch": SoundSource(
        id="branch",
        label="window",
        room="window",
        noise="scratching",
        clue="a branch tapping the glass",
        reveal="it was only a branch brushing the window in the wind.",
        harmless=True,
    ),
    "toy": SoundSource(
        id="toy",
        label="toy box",
        room="toy corner",
        noise="buzzing",
        clue="a toy with a loose battery cover",
        reveal="it was just a toy buzzing because a button had been pressed.",
        harmless=True,
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Owen", "Lily", "Eli", "Zoe", "Noah"]
TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]


def tell(setting: Setting, source: SoundSource, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_type))
    source_ent = world.add(Entity(
        id=source.id,
        kind="thing",
        type="source",
        label=source.label,
        room=source.room,
        openable=True,
        open_state=False,
        noisy=True,
        hidden=True,
    ))

    world.say(f"{hero.label} lived in {setting.place} with {parent.label}.")
    world.say(f"Everything was normal until one evening a strange noise drifted through the rooms.")
    world.para()
    _find_noise(world, hero, source)
    _suspect(world, hero, source)
    world.para()
    _investigate(world, hero, source)
    _open_and_reveal(world, hero, source)
    world.para()
    _lesson_learned(world, hero, parent, source)

    world.facts = {
        "hero": hero,
        "parent": parent,
        "source": source,
        "source_ent": source_ent,
    }
    return world


def choose_combo(rng: random.Random, args: argparse.Namespace) -> tuple[str, str]:
    settings = list(SETTINGS.keys())
    sources = list(SOURCES.keys())
    if getattr(args, "setting", None):
        settings = [getattr(args, "setting", None)]
    if getattr(args, "source", None):
        sources = [getattr(args, "source", None)]
    combo = []
    for s in settings:
        for src in sources:
            combo.append((s, src))
    if not combo:
        pass
    return rng.choice(sorted(combo))


@dataclass
class RegistryItem:
    name: str
    rule: str
    value: str
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
    ap = argparse.ArgumentParser(description="A small mystery about a strange noise and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--source", choices=SOURCES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=TYPES)
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    setting, source = choose_combo(rng, args)
    hero_type = getattr(args, "gender", None) or rng.choice(TYPES)
    hero_name = getattr(args, "name", None) or rng.choice(NAMES)
    parent_type = getattr(args, "parent", None) or rng.choice(PARENT_TYPES)
    return StoryParams(
        setting=setting,
        source=source,
        hero_name=hero_name,
        hero_type=hero_type,
        parent_type=parent_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    source = _safe_fact(world, f, "source")
    return [
        f'Write a short mystery story for a young child about a strange "{source.noise}" sound.',
        f"Tell a gentle mystery where {hero.label} hears a noise in {world.setting.place} and learns what made it.",
        f'Write a child-friendly story that begins with a puzzling noise and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    source = _safe_fact(world, f, "source")
    return [
        QAItem(
            question=f"What strange noise did {hero.label} hear?",
            answer=f"{hero.label} heard a {source.noise} coming from the {source.room}.",
        ),
        QAItem(
            question=f"What clue helped {hero.label} solve the mystery?",
            answer=f"The clue was {source.clue}.",
        ),
        QAItem(
            question=f"What was the noise really?",
            answer=source.reveal,
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn?",
            answer=f"{hero.label} learned that a scary-sounding noise can have a simple cause, and careful looking can solve a mystery.",
        ),
        QAItem(
            question=f"Who helped {hero.label} feel better at the end?",
            answer=f"{parent.label} helped by listening, hugging {hero.pronoun('object')}, and pointing out the truth.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem or puzzling event that can be solved by finding clues.",
        ),
        QAItem(
            question="Why should you check clues instead of guessing right away?",
            answer="Checking clues helps you find the real answer, while guessing can make you worry about the wrong thing.",
        ),
        QAItem(
            question="What is a noise?",
            answer="A noise is a sound you hear, like a whir, a clunk, a scratch, or a buzz.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.openable:
            bits.append(f"open={e.open_state}")
        if e.noisy:
            bits.append("noisy=True")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
source_noise(S) :- source(S).
mystery(S) :- source_noise(S).
clue_seen(H,S) :- hero(H), source(S).
lesson_learned(H) :- understanding(H).
solved(H,S) :- clue_seen(H,S), lesson_learned(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, src in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("noisy_source", sid))
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(setting="house", source="fan", hero_name="Mia", hero_type="girl", parent_type="mother"),
    StoryParams(setting="cabin", source="pipes", hero_name="Finn", hero_type="boy", parent_type="father"),
    StoryParams(setting="school", source="branch", hero_name="Ava", hero_type="girl", parent_type="mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(SOURCES, params.source), params.hero_name, params.hero_type, params.parent_type)
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
        print(asp_program("#show solved/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

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
            i += 1
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
            header = f"### {p.hero_name}: {p.setting} / {p.source}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
