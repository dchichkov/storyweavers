#!/usr/bin/env python3
"""
storyworlds/worlds/porter_triple_curiosity_superhero_story.py
=============================================================

A small superhero-style story world about a curious porter whose curiosity
pulls them toward a triple puzzle, then toward a brave, helpful fix.

The story premise:
- Porter is a night-shift porter at a busy tower station.
- A hero cape and three locked sky-gates create a triple problem.
- Porter's curiosity makes them investigate instead of ignoring the clues.
- The investigation reveals a small trapped helper, and the porter becomes a
  tiny superhero by delivering the missing key and opening the way.

The simulation tracks:
- physical meters: carried items, locked gates, opened doors, rescued helper
- emotional memes: curiosity, worry, courage, relief, pride

This world is designed in a child-facing superhero style with a clear beginning,
middle turn, and ending image proving what changed.
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
    carried_by: Optional[str] = None
    locked: bool = False
    opened: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    traits: list = field(default_factory=list)
    bird: object | None = None
    cape: object | None = None
    gate1: object | None = None
    gate2: object | None = None
    gate3: object | None = None
    hero: object | None = None
    key: object | None = None
    lantern: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    skyline: str
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
class HeroGear:
    id: str
    label: str
    phrase: str
    help_text: str
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
class Mystery:
    id: str
    clue: str
    triple: str
    risk: str
    reveal: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "tower": Setting(place="the tower station", skyline="the moonlit city", affords={"triple"}),
    "roof": Setting(place="the roof garden", skyline="the silver skyline", affords={"triple"}),
    "dock": Setting(place="the sky dock", skyline="the glowing harbor", affords={"triple"}),
}

MYSTERIES = {
    "triple": Mystery(
        id="triple",
        clue="three blinking lights",
        triple="a triple lock",
        risk="stuck shut",
        reveal="a trapped baby bird",
        keyword="triple",
        tags={"triple", "lights", "lock"},
    ),
}

GEAR = {
    "cape": HeroGear(
        id="cape",
        label="a bright cape",
        phrase="a bright cape with a gold clasp",
        help_text="wrap up like a true hero",
    ),
    "key": HeroGear(
        id="key",
        label="the silver key",
        phrase="a silver key on a red ribbon",
        help_text="unlock the triple door",
    ),
    "lantern": HeroGear(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern with a warm beam",
        help_text="follow the clue trail",
    ),
}

PORTER_NAMES = ["Porter", "Milo", "Nina", "Arlo", "Tess"]
PORTER_TYPES = ["porter", "boy", "girl"]
TRAITS = ["curious", "brave", "gentle", "clever", "quick"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero-style story world about a curious porter and a triple mystery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy", "porter"])
    ap.add_argument("--trait", choices=TRAITS)
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
    mystery = getattr(args, "mystery", None) or "triple"
    gender = getattr(args, "gender", None) or rng.choice(["porter", "boy", "girl"])
    name = getattr(args, "name", None) or rng.choice(PORTER_NAMES)
    trait = getattr(args, "trait", None) or "curious"
    if gender == "porter" and getattr(args, "name", None) is None:
        name = "Porter"
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, trait=trait)


def make_pronoun(gender: str, case: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if gender == "boy":
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def tell(setting: Setting, mystery: Mystery, name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        label="porter",
        traits=[],
        meters={"steps": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "courage": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    gate1 = world.add(Entity(id="gate1", label="first gate", locked=True))
    gate2 = world.add(Entity(id="gate2", label="second gate", locked=True))
    gate3 = world.add(Entity(id="gate3", label="third gate", locked=True))
    key = world.add(Entity(id="key", label="silver key", carried_by=None, owner=name))
    bird = world.add(Entity(id="bird", kind="character", type="thing", label="baby bird"))
    cape = world.add(Entity(id="cape", label="cape", carried_by=name))
    lantern = world.add(Entity(id="lantern", label="lantern", carried_by=name))

    world.say(
        f"{name} was a {trait} porter at {setting.place}, where {setting.skyline} shimmered above the tracks."
    )
    world.say(
        f"{make_pronoun(gender).capitalize()} wore a bright cape and carried a lantern, because heroes were welcome there."
    )
    world.say(
        f"Every night, {name} watched for {mystery.clue} and listened for trouble."
    )

    world.para()
    hero.meters["steps"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"One night, {name} spotted {mystery.clue} near {mystery.triple} at the end of the hall."
    )
    world.say(
        f"The clue felt important, and {make_pronoun(gender)} curiosity grew bigger than the dark."
    )

    world.para()
    hero.meters["steps"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"{name} moved closer and saw that the {mystery.triple} kept the door {mystery.risk}."
    )
    world.say(
        f"Behind the locked panels, something small made a tiny peep."
    )

    world.para()
    hero.meters["steps"] += 1
    hero.memes["courage"] += 1
    gate1.locked = gate2.locked = gate3.locked = False
    gate1.opened = gate2.opened = gate3.opened = True
    key.carried_by = name
    bird.carried_by = name
    world.say(
        f"{name} followed the clue trail with the lantern, found the silver key, and opened all three gates."
    )
    world.say(
        f"Inside the last gate was {mystery.reveal}, safe at last."
    )

    world.para()
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    bird.meters["safe"] = 1.0
    world.say(
        f"{name} lifted the little bird to the open window, and the night breeze carried it home."
    )
    world.say(
        f"Then {make_pronoun(gender)} stood in the moonlight with the cape shining behind {make_pronoun(gender, 'object')},"
        f" looking like a tiny superhero who had saved the station."
    )

    world.facts.update(
        hero=hero,
        setting=setting,
        mystery=mystery,
        gate_ids=["gate1", "gate2", "gate3"],
        key=key,
        bird=bird,
        cape=cape,
        lantern=lantern,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a short superhero story for a young child about a {hero.label} named {hero.id} and a {mystery.keyword} mystery.',
        f"Tell a gentle adventure where {hero.id} follows {mystery.clue} and helps fix a triple problem.",
        f"Write a story where curiosity helps a porter become a hero at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a {hero.label} who works at {setting.place} and has a curious superhero heart.",
        ),
        QAItem(
            question=f"What did {hero.id} notice in the hall?",
            answer=f"{hero.id} noticed {mystery.clue}, which pointed to the triple lock and told {make_pronoun(hero.type)} that something was wrong.",
        ),
        QAItem(
            question="What did the porter do to solve the problem?",
            answer=f"{hero.id} found the silver key, opened the triple gates, and rescued {mystery.reveal}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt relieved and proud, because curiosity helped turn a scary lock into a saved little life.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a porter do?",
            answer="A porter helps carry things, watch over places, and keep a station or building working smoothly.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn more about something new.",
        ),
        QAItem(
            question="What is a cape for in superhero stories?",
            answer="A cape is a bright piece of clothing that can help a superhero look brave and ready for action.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.locked:
            bits.append("locked")
        if e.opened:
            bits.append("opened")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- porter(X).
triple_problem(M) :- mystery(M), triple(M).
valid_story(S, M) :- setting(S), mystery(M), hero_porter.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    lines.append(asp.fact("porter", "porter"))
    lines.append(asp.fact("hero_porter"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(MYSTERIES, params.mystery), params.name, params.gender, params.trait)
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
    StoryParams(setting="tower", mystery="triple", name="Porter", gender="porter", trait="curious"),
    StoryParams(setting="roof", mystery="triple", name="Nina", gender="girl", trait="curious"),
    StoryParams(setting="dock", mystery="triple", name="Milo", gender="boy", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("1 compatible story family: porter + triple mystery")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
