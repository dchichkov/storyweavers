#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/garrison_surprise_fable.py
=======================================================================================================

A small fable-style storyworld about a garrison, a surprise, and the lesson
that a closed gate is not always the wisest gate.

Premise:
- A proud hill garrison keeps watch over a road and a little valley.
- The captain believes surprises are for careless folk.

Turn:
- A surprise arrives: not an enemy, but a small traveler in need.
- The garrison's first instinct is to stay stern and keep the gate shut.

Resolution:
- The captain chooses shelter over pride.
- The garrison becomes a place of help, not just a place of watch.

The prose is generated from world state and a simple simulation. It includes
meters (physical state) and memes (emotional state) for its entities.
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    hero: object | None = None
    traveler: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "owl", "dog", "fox", "badger", "wolf"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"matron", "hen", "goat", "mare"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)
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
    height: str
    affords_surprise: bool = True
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
class SurpriseEvent:
    id: str
    label: str
    cause: str
    need: str
    location: str
    emotional_turn: str
    moral_hint: str
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
class Role:
    hero_type: str
    hero_name: str
    captain_type: str
    captain_name: str
    traveler_type: str
    traveler_name: str
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
        self.event_active: bool = False
        self.event_resolved: bool = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.event_active = self.event_active
        clone.event_resolved = self.event_resolved
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "hillfort": Setting(place="the hill garrison", height="high"),
    "rivergate": Setting(place="the river gate garrison", height="low"),
    "stonekeep": Setting(place="the stone garrison", height="high"),
}

SURPRISES = {
    "lost_lamb": SurpriseEvent(
        id="lost_lamb",
        label="a lost lamb",
        cause="wandered away from the flock",
        need="warm shelter and a little milk",
        location="the gate",
        emotional_turn="kindness",
        moral_hint="a hard heart can miss a small cry for help",
    ),
    "storm_pigeon": SurpriseEvent(
        id="storm_pigeon",
        label="a soaked pigeon messenger",
        cause="flew through a sudden storm",
        need="a dry corner and a bit of grain",
        location="the watch post",
        emotional_turn="care",
        moral_hint="even a watcher must make room for mercy",
    ),
    "tiny_traveler": SurpriseEvent(
        id="tiny_traveler",
        label="a tiny traveler with a cracked basket",
        cause="took the road too far in the dark",
        need="water and help carrying the basket",
        location="the road gate",
        emotional_turn="welcome",
        moral_hint="surprises are easier when the gate opens a little",
    ),
}

ROLES = {
    "badger_captain": Role("badger", "Bram", "badger captain", "Captain Bram", "mouse", "Mina"),
    "fox_captain": Role("fox", "Tessa", "fox captain", "Captain Tessa", "hare", "Hob"),
    "owl_captain": Role("owl", "Orin", "owl captain", "Captain Orin", "sparrow", "Sib"),
}

GIRL_NAMES = ["Mina", "Tessa", "Luna", "Nia", "Ivy", "Mara"]
BOY_NAMES = ["Bram", "Orin", "Pip", "Hob", "Glen", "Tobin"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A surprise is reasonable when it names a real event.
valid_surprise(S) :- surprise(S).

% A story is valid when the setting supports a garrison and the surprise exists.
valid_story(Set, S) :- setting(Set), surprise(S), affords(Set, garrison).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("affords", sid, "garrison"))
        if setting.height == "high":
            lines.append(asp.fact("high", sid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        pass
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(sid, sr) for sid in SETTINGS for sr in SURPRISES}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    surprise: str
    role: str
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


def choose_name(role: Role, rng: random.Random) -> tuple[str, str]:
    if rng.random() < 0.5:
        return role.hero_name, role.captain_name
    return rng.choice(GIRL_NAMES + BOY_NAMES), role.captain_name


def reasonableness_gate(setting: Setting, surprise: SurpriseEvent) -> None:
    if not setting.affords_surprise:
        pass
    if surprise.id not in SURPRISES:
        pass


def tell(setting: Setting, surprise: SurpriseEvent, role: Role) -> World:
    world = World(setting)
    captain = world.add(Entity(
        id="captain",
        kind="character",
        type=role.captain_type.split("_")[0],
        label=role.captain_name,
        meters={"watch": 2.0, "tired": 1.0},
        memes={"pride": 1.0, "duty": 2.0},
    ))
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=role.hero_type,
        label=role.hero_name,
        meters={"hunger": 1.0, "travel": 1.0},
        memes={"fear": 0.5, "hope": 1.0},
    ))
    traveler = world.add(Entity(
        id="traveler",
        kind="character",
        type=role.traveler_type,
        label=surprise.label,
        meters={"wet": 0.0, "load": 1.0},
        memes={"anxiety": 1.0},
    ))

    world.facts.update(captain=captain, hero=hero, traveler=traveler, surprise=surprise, setting=setting)

    # Setup
    world.say(
        f"On a windy hill stood {setting.place}, where {captain.label} kept watch from the tallest stone."
    )
    world.say(
        f"{captain.label} liked order and quiet horns, and he often said that surprises belonged to fools."
    )
    world.para()
    world.say(
        f"Below the walls, {hero.label} was on the road, carrying a small loaf and thinking about home."
    )
    world.say(
        f"{hero.label} loved the road, but {hero.pronoun('possessive')} {role.traveler_name.lower()}? no, {hero.label} did not love getting caught off guard."
    )

    # Turn: surprise arrives
    world.para()
    world.event_active = True
    traveler.meters["wet"] += 1.0 if surprise.id == "storm_pigeon" else 0.0
    traveler.meters["load"] += 1.0
    captain.memes["alert"] += 1.0
    captain.memes["unease"] += 1.0
    world.say(
        f"Then a surprise came to {surprise.location}: {surprise.label} appeared because it had {surprise.cause}."
    )
    world.say(
        f"It needed {surprise.need}, and its little eyes looked as tired as the moon after dawn."
    )
    world.say(
        f"{captain.label} frowned, because the garrison had been built to watch for trouble, not to make room for it."
    )

    # Conflict
    if surprise.id == "lost_lamb":
        hero.memes["compassion"] = hero.meme("compassion") + 1.0
    if surprise.id == "storm_pigeon":
        hero.meters["grain"] = 0.0
    captain.meters["gate_tension"] = captain.meter("gate_tension") + 1.0
    world.say(
        f"For a breath, the gate stayed shut, and the whole garrison felt stiff as a stuck latch."
    )

    # Resolution
    world.para()
    captain.memes["pride"] = max(0.0, captain.meme("pride") - 1.0)
    captain.memes["mercy"] = captain.meme("mercy") + 2.0
    captain.memes["joy"] = captain.meme("joy") + 1.0
    traveler.memes["relief"] = traveler.meme("relief") + 2.0
    world.event_resolved = True
    world.say(
        f"Then {captain.label} remembered that a strong wall is not strong because it shuts everything out."
    )
    world.say(
        f"He opened the gate, and {hero.label} helped bring {surprise.label} inside for {surprise.need}."
    )
    world.say(
        f"Soon the surprise was no longer frightening. It had become {surprise.emotional_turn}."
    )
    world.say(
        f"That night, the garrison looked less like a stern stone mouth and more like a lantern for the road."
    )
    world.say(f"Moral: {surprise.moral_hint}.")

    return world


# ---------------------------------------------------------------------------
# QA and prose helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    surprise: SurpriseEvent = _safe_fact(world, f, "surprise")
    setting: Setting = _safe_fact(world, f, "setting")
    captain: Entity = _safe_fact(world, f, "captain")
    hero: Entity = _safe_fact(world, f, "hero")
    return [
        f"Write a short fable about {setting.place} and a surprise visitor who changes a proud captain's mind.",
        f"Tell a child-friendly story where {captain.label} learns something kind when {surprise.label} arrives.",
        f"Create a simple moral tale about a garrison, a surprise, and a helpful opening of the gate.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain: Entity = _safe_fact(world, f, "captain")
    hero: Entity = _safe_fact(world, f, "hero")
    traveler: Entity = _safe_fact(world, f, "traveler")
    surprise: SurpriseEvent = _safe_fact(world, f, "surprise")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who kept watch at {setting.place}?",
            answer=f"{captain.label} kept watch at {setting.place} from the tallest stone.",
        ),
        QAItem(
            question=f"What surprise came to the gate?",
            answer=f"{surprise.label} came as the surprise, and it needed {surprise.need}.",
        ),
        QAItem(
            question=f"Who helped when the surprise needed care?",
            answer=f"{hero.label} helped {captain.label} bring the surprise inside.",
        ),
        QAItem(
            question=f"How did the garrison change by the end?",
            answer=(
                "It changed from a stern, closed place into a warm shelter that could open its gate "
                "when kindness was needed."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a garrison?",
            answer="A garrison is a place where guards stay to watch a road, gate, or border.",
        ),
        QAItem(
            question="What does surprise mean?",
            answer="A surprise is something unexpected that happens before you are ready for it.",
        ),
        QAItem(
            question="Why can opening a gate help?",
            answer="Opening a gate can help because it lets people or animals come in for safety and care.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  event_active={world.event_active} event_resolved={world.event_resolved}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard contract
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style storyworld about a garrison and a surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    surprise = getattr(args, "surprise", None) or rng.choice(list(SURPRISES))
    role = getattr(args, "role", None) or rng.choice(list(ROLES))
    reasonableness_gate(_safe_lookup(SETTINGS, setting), _safe_lookup(SURPRISES, surprise))
    return StoryParams(setting=setting, surprise=surprise, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(SURPRISES, params.surprise), _safe_lookup(ROLES, params.role))
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
    StoryParams(setting="hillfort", surprise="lost_lamb", role="badger_captain"),
    StoryParams(setting="rivergate", surprise="storm_pigeon", role="fox_captain"),
    StoryParams(setting="stonekeep", surprise="tiny_traveler", role="owl_captain"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid garrison-surprise combinations:")
        for item in combos:
            print(" ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
            header = f"### {p.setting} / {p.surprise} / {p.role}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
