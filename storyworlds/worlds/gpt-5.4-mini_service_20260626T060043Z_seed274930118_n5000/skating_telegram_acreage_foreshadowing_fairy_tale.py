#!/usr/bin/env python3
"""
storyworlds/worlds/skating_telegram_acreage_foreshadowing_fairy_tale.py
=======================================================================

A tiny fairy-tale story world about skating, a telegram, and an acreage.

Premise:
A young skater loves to glide on a frozen pond near a little acreage. A telegram
arrives with a warning that something about the land is not quite safe. The
story uses foreshadowing: small signs appear early, then the warning proves
useful, and the ending shows what changed.

World model:
- physical meters: ice_thin, cold, distance, damage, safety, dryness
- emotional memes: delight, worry, patience, trust, relief, pride

The narrative is intentionally small and constraint-driven:
the hero skates, the telegram foreshadows trouble, and the fix is a careful
choice that protects the acreage and the skates.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    protective: bool = False
    acreage: object | None = None
    cloak: object | None = None
    hero: object | None = None
    messenger: object | None = None
    skates: object | None = None
    telegram: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "man"}:
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
    setting_word: str
    frozen: bool = True
    acres: int = 3
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
class ObjectDef:
    id: str
    label: str
    phrase: str
    protects: bool = False
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
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
    hero_name: str
    hero_type: str
    messenger: str
    acreage: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]


PLACES = {
    "pond": Place(name="the pond", setting_word="pond", frozen=True, acres=2),
    "meadow": Place(name="the meadow", setting_word="meadow", frozen=True, acres=4),
    "castle_lake": Place(name="the castle lake", setting_word="lake", frozen=True, acres=5),
}

HERO_TYPES = ["girl", "boy", "princess", "prince"]
MESSENGERS = ["herald", "page", "rider"]
ACREAGE_WORDS = ["little acreage", "small acreage", "wide acreage", "old acreage"]

OBJECTS = {
    "skates": ObjectDef(id="skates", label="skates", phrase="a pair of silver skates", plural=True),
    "cloak": ObjectDef(id="cloak", label="cloak", phrase="a warm blue cloak", protects=True, guards={"cold"}, covers={"torso"}),
    "lantern": ObjectDef(id="lantern", label="lantern", phrase="a bright lantern"),
    "sled": ObjectDef(id="sled", label="sled", phrase="a small red sled"),
}

TRAITS = ["gentle", "brave", "curious", "patient", "cheerful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, h) for p in PLACES for h in HERO_TYPES]


@dataclass
class RidePlan:
    want: str
    foreshadow: str
    risk: str
    fix: str
    RIDE: object | None = None
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


RIDE = RidePlan(
    want="skate across the frozen pond",
    foreshadow="a telegram about thin ice at the edge of the acreage",
    risk="the ice near the reeds might crack",
    fix="skate only where the ice is strong and keep a lookout",
)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world: skating, a telegram, and acreage.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--messenger", choices=MESSENGERS)
    ap.add_argument("--acreage", choices=ACREAGE_WORDS)
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
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    messenger = getattr(args, "messenger", None) or rng.choice(MESSENGERS)
    acreage = getattr(args, "acreage", None) or rng.choice(ACREAGE_WORDS)
    hero_name = getattr(args, "hero_name", None) or rng.choice(["Elsa", "Mira", "Anya", "Ivo", "Nora", "Soren"])
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, messenger=messenger, acreage=acreage)


def foreshadow(world: World, hero: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"At {world.place.name}, {hero.id} noticed a silver crack line near the reeds, "
        f"like a whisper that had not yet learned to speak."
    )


def predict_risk(world: World) -> bool:
    return world.place.frozen and world.place.acres >= 2


def tell_story(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"delight": 1.0, "safety": 0.0, "distance": 0.0},
        memes={"trust": 0.0, "worry": 0.0, "relief": 0.0},
    ))
    messenger = world.add(Entity(
        id="Messenger",
        kind="character",
        type=params.messenger,
        label=f"the {params.messenger}",
        meters={"distance": 0.0},
        memes={"urgency": 0.0},
    ))
    skates = world.add(Entity(
        id="Skates",
        type="skates",
        label="skates",
        phrase="a pair of silver skates",
        owner=hero.id,
        worn_by=hero.id,
        plural=True,
        meters={"shine": 1.0},
    ))
    cloak = world.add(Entity(
        id="Cloak",
        type="cloak",
        label="cloak",
        phrase="a warm blue cloak",
        owner=hero.id,
        worn_by=hero.id,
        protective=True,
        plural=False,
        meters={"warmth": 1.0},
    ))
    telegram = world.add(Entity(
        id="Telegram",
        type="telegram",
        label="telegram",
        phrase="a folded telegram sealed with red wax",
        meters={"arrival": 1.0},
        memes={"warning": 1.0},
    ))
    acreage = world.add(Entity(
        id="Acreage",
        type="acreage",
        label=params.acreage,
        phrase=f"a {params.acreage}",
        meters={"size": float(place.acres), "risk": 0.0},
        memes={"memory": 0.0},
    ))

    world.facts.update(hero=hero, messenger=messenger, skates=skates, cloak=cloak, telegram=telegram, acreage=acreage)

    world.say(
        f"Once upon a winter's morning, {hero.id} loved to {RIDE.want} on {world.place.name}, "
        f"where the {params.acreage} lay white and quiet."
    )
    world.say(
        f"{hero.id} wore {skates.it()} and {cloak.it()} and laughed, for the cold made the world shine."
    )

    world.para()
    foreshadow(world, hero)
    if predict_risk(world):
        world.say(
            f"Before long, the {params.messenger} arrived with a telegram and bowed low, "
            f"for the message had come from beyond the {params.acreage}."
        )
        world.say(
            f"The telegram warned that {RIDE.risk}, and the warning felt like a lantern lit inside the story."
        )
        messenger.memes["urgency"] += 1
        world.facts["warned"] = True

    world.para()
    if world.facts.get("warned"):
        hero.memes["worry"] += 1
        world.say(
            f"{hero.id} looked at the snow, then at the reeds, and remembered the telegram."
        )
        world.say(
            f"Instead of racing ahead, {hero.id} chose {RIDE.fix}, holding the cloak close and gliding with care."
        )
        hero.meters["safety"] += 1
        hero.memes["trust"] += 1
        acreage.meters["risk"] = 0.0
        world.say(
            f"So {hero.id} skated only on the strong ice, and the {params.acreage} stayed safe behind {hero.pronoun('possessive')} careful path."
        )
        hero.memes["relief"] += 1
    else:
        pass

    world.para()
    world.say(
        f"By sunset, {hero.id} was still skating, but now the pond shone like a promise kept."
    )
    world.say(
        f"The telegram lay folded and quiet in the cloak pocket, and the {params.acreage} rested without a crack."
    )

    world.facts["resolved"] = True
    world.facts["place"] = place
    return world


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    acreage = _safe_fact(world, world.facts, "acreage").phrase
    return [
        f"Write a fairy tale about {hero.id} who loves skating and receives a telegram about {acreage}.",
        "Tell a short story with foreshadowing, a skating pond, and a warning carried by a telegram.",
        "Write a child-friendly fairy tale where a little hero notices a sign of danger on the acreage before skating.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    messenger = _safe_fact(world, world.facts, "messenger")
    acreage = _safe_fact(world, world.facts, "acreage")
    place = _safe_fact(world, world.facts, "place")
    return [
        QAItem(
            question=f"What did {hero.id} love to do at {place.name}?",
            answer=f"{hero.id} loved to skate on {place.name} and watch the winter world shine.",
        ),
        QAItem(
            question=f"What did the {params_word(messenger.type)} bring to {hero.id}?",
            answer=f"The {params_word(messenger.type)} brought a telegram with a warning about the {acreage.label}.",
        ),
        QAItem(
            question="How did the telegram matter in the story?",
            answer="It foreshadowed danger near the reeds, so the hero slowed down and chose a careful path.",
        ),
    ]


def params_word(word: str) -> str:
    return word.replace("_", " ")


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a telegram?",
            answer="A telegram is a short message that is sent quickly to tell news or a warning.",
        ),
        QAItem(
            question="What is acreage?",
            answer="Acreage means a piece of land measured by acres; it tells how much ground there is.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a little hint that something important may happen later.",
        ),
        QAItem(
            question="What does skating mean?",
            answer="Skating means moving smoothly on ice with skates on your feet.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.protective:
            bits.append("protective=True")
        out.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    out.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
place(P) :- setting(P).
hero_type(T) :- type(T).
warned(S) :- telegram(T), foreshadows(T,S).
careful_path(S) :- warned(S).
valid_story(P,T) :- place(P), hero_type(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
    for t in HERO_TYPES:
        lines.append(asp.fact("type", t))
    lines.append(asp.fact("telegram", "telegram"))
    lines.append(asp.fact("foreshadows", "telegram", "danger"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP matches Python valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP only:", sorted(asp_set - py_set))
    print("PY only:", sorted(py_set - asp_set))
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(asp.atoms(model, "valid_story")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="pond", hero_name="Mira", hero_type="girl", messenger="herald", acreage="little acreage"),
            StoryParams(place="meadow", hero_name="Soren", hero_type="boy", messenger="page", acreage="small acreage"),
            StoryParams(place="castle_lake", hero_name="Anya", hero_type="princess", messenger="rider", acreage="wide acreage"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(max(1, getattr(args, "n", None))):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
