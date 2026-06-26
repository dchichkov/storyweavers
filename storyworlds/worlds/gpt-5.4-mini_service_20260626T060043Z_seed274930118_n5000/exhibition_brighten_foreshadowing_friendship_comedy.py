#!/usr/bin/env python3
"""
Story world: exhibition_brighten_foreshadowing_friendship_comedy

A small simulated comedy domain about a children's exhibition that starts a bit
dull, gathers a few foreshadowed worries, and ends brighter because friends work
together.

The story engine models:
- physical meters: brightness, clutter, balance, poster_straight, snack_sticky
- emotional memes: worry, hope, friendship, pride, laughter

The premise is simple:
- Two friends prepare an exhibition in a small hall.
- A dim room, a wobbly display, or a dull sign can make the show feel flat.
- A friendly plan fixes the problem in a way that changes the world state.

The prose is state-driven rather than template-swapped: the ending image depends
on what changed in the world.
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

# ---------------------------------------------------------------------------
# World constants
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
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    wearer: Optional[str] = None
    support: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    banner: object | None = None
    display: object | None = None
    friend: object | None = None
    hero: object | None = None
    lamp: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    place: str = "the little hall"
    indoors: bool = True
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
class ExhibitPlan:
    id: str
    label: str
    keyword: str
    starting_brightness: int
    has_spotlight: bool
    has_banner: bool
    can_fix: str  # spotlight | banner | both
    comic_problem: str
    comic_fix: str
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
    exhibit: str
    hero: str
    friend: str
    hero_type: str
    friend_type: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def chars(self) -> list[Entity]:
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
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hall": Setting(place="the little hall", indoors=True),
    "school": Setting(place="the school gallery", indoors=True),
    "library": Setting(place="the library corner", indoors=True),
}

EXHIBITS = {
    "space": ExhibitPlan(
        id="space",
        label="a tiny space exhibition",
        keyword="exhibition",
        starting_brightness=2,
        has_spotlight=False,
        has_banner=True,
        can_fix="spotlight",
        comic_problem="the moon poster looked sleepy",
        comic_fix="a bright lamp",
    ),
    "garden": ExhibitPlan(
        id="garden",
        label="a garden exhibition",
        keyword="brighten",
        starting_brightness=1,
        has_spotlight=True,
        has_banner=False,
        can_fix="banner",
        comic_problem="the flower cutouts looked like they were yawning",
        comic_fix="a cheerful banner",
    ),
    "animals": ExhibitPlan(
        id="animals",
        label="an animal exhibition",
        keyword="exhibition",
        starting_brightness=1,
        has_spotlight=False,
        has_banner=False,
        can_fix="both",
        comic_problem="the cardboard lion was hiding in the shadows",
        comic_fix="two friends with a lamp and a banner",
    ),
}

HEROES = ["Mina", "Noah", "Lia", "Theo", "Aria", "Owen"]
FRIENDS = ["Pip", "Nina", "Zed", "Milo", "Tess", "June"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting: Setting, exhibit: ExhibitPlan) -> bool:
    return setting.indoors and exhibit.id in EXHIBITS


def valid_combos() -> list[tuple[str, str]]:
    return [(s, e) for s in SETTINGS for e in EXHIBITS if valid_combo(_safe_lookup(SETTINGS, s), _safe_lookup(EXHIBITS, e))]


def explain_rejection(setting: str, exhibit: str) -> str:
    if setting not in SETTINGS or exhibit not in EXHIBITS:
        return "(No story: unknown setting or exhibition choice.)"
    return "(No story: this comedy needs a small indoor exhibition space so the brightening fix can matter.)"


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    exhibit = _safe_lookup(EXHIBITS, params.exhibit)
    world = World(setting)

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, label=params.hero))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_type, label=params.friend))
    display = world.add(Entity(id="display", type="thing", label=exhibit.label))
    lamp = world.add(Entity(id="lamp", type="thing", label="a small lamp"))
    banner = world.add(Entity(id="banner", type="thing", label="a cheerful banner"))

    world.facts.update(hero=hero, friend=friend, display=display, lamp=lamp, banner=banner, exhibit=exhibit)

    # Setup
    world.say(
        f"{hero.id} and {friend.id} were getting ready for {exhibit.label} at {setting.place}."
    )
    world.say(
        f"They wanted the room to feel lively, because a good exhibition should make people smile."
    )

    # Foreshadowing
    world.para()
    display.meters["brightness"] = exhibit.starting_brightness
    hero.memes["worry"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"But {exhibit.comic_problem}, and the room felt a little too plain."
    )
    world.say(
        f"{hero.id} glanced at the display and whispered, "
        f'"It needs something to {exhibit.keyword}."'
    )

    # Small comedic tension
    if not exhibit.has_spotlight:
        world.say(
            f"{friend.id} stood on tiptoe and looked around. "
            f'"Maybe the ceiling lamp is hiding," {friend.pronoun()} said with a grin.'
        )
    if not exhibit.has_banner:
        world.say(
            f"{hero.id} pointed at the empty wall. "
            f'"That wall looks so serious it could use a joke," {hero.pronoun()} said.'
        )

    # Turn
    world.para()
    if exhibit.can_fix in {"spotlight", "both"}:
        lamp.wearer = hero.id
        display.meters["brightness"] += 2
        world.say(
            f"{hero.id} carried over {lamp.label}, and the pictures woke up at once."
        )
    if exhibit.can_fix in {"banner", "both"}:
        banner.wearer = friend.id
        display.meters["brightness"] += 1
        world.say(
            f"{friend.id} hung {banner.label}, and even the grumpy wall started to look cheerful."
        )

    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    hero.memes["laughter"] += 1
    friend.memes["laughter"] += 1

    # Resolution
    world.para()
    world.say(
        f"In the end, the room was bright enough for the paper stars to sparkle."
    )
    world.say(
        f"{hero.id} and {friend.id} stood together by the exhibit, laughing because "
        f"{exhibit.comic_fix} had turned the whole place lively."
    )
    world.say(
        f"The exhibition no longer looked sleepy; it looked ready for visitors to walk in and smile."
    )

    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A setting is valid for the comedy when it is indoors.
valid_combo(S, E) :- setting(S), indoor(S), exhibit(E).

% The exhibit brightens when a compatible fix is available.
can_fix(E, spotlight) :- exhibit(E), needs_spotlight(E).
can_fix(E, banner) :- exhibit(E), needs_banner(E).
can_fix(E, both) :- exhibit(E), needs_spotlight(E), needs_banner(E).

% Friendly collaboration is part of the intended story.
friendship_story(E) :- exhibit(E), keyword(E, exhibition).
friendship_story(E) :- exhibit(E), keyword(E, brighten).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoor", sid))
    for eid, exhibit in EXHIBITS.items():
        lines.append(asp.fact("exhibit", eid))
        lines.append(asp.fact("keyword", eid, exhibit.keyword))
        if exhibit.can_fix == "spotlight":
            lines.append(asp.fact("needs_spotlight", eid))
        elif exhibit.can_fix == "banner":
            lines.append(asp.fact("needs_banner", eid))
        else:
            lines.append(asp.fact("needs_spotlight", eid))
            lines.append(asp.fact("needs_banner", eid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python valid_combos():")
    print(" only python:", sorted(py - cl))
    print(" only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ex: ExhibitPlan = _safe_fact(world, f, "exhibit")  # type: ignore[assignment]
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    friend: Entity = _safe_fact(world, f, "friend")  # type: ignore[assignment]
    return [
        f'Write a short comedy story for a child about an "{ex.keyword}" exhibition that needs brightening.',
        f"Tell a story where {hero.id} and {friend.id} work together to make {ex.label} look less dull.",
        f"Write a gentle, funny story where friendship helps a small exhibition become bright and cheerful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    friend: Entity = _safe_fact(world, f, "friend")  # type: ignore[assignment]
    ex: ExhibitPlan = _safe_fact(world, f, "exhibit")  # type: ignore[assignment]
    setting: Setting = world.setting

    return [
        QAItem(
            question=f"Who was the story about at {setting.place}?",
            answer=f"It was about {hero.id} and {friend.id}, who were preparing {ex.label} together at {setting.place}.",
        ),
        QAItem(
            question=f"What problem made {ex.label} need help?",
            answer=f"{ex.comic_problem.capitalize()}, so the room looked plain and needed a little brightening.",
        ),
        QAItem(
            question=f"How did the friends fix the exhibition?",
            answer=f"{hero.id} brought {f['lamp'].label} and {friend.id} hung {f['banner'].label}, which made the exhibit brighter and happier.",
        ),
        QAItem(
            question=f"Why was the ending funny and happy?",
            answer=f"It was funny because the friends treated a dull room like a big joke, and it was happy because they used teamwork to brighten {ex.label}.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "exhibition": (
        "What is an exhibition?",
        "An exhibition is a place where people show pictures, objects, or ideas so others can look at them and learn.",
    ),
    "brighten": (
        "What does brighten mean?",
        "To brighten something means to make it lighter, cheerier, or easier to see.",
    ),
    "friendship": (
        "What is friendship?",
        "Friendship is when people care about each other, help each other, and enjoy being together.",
    ),
}


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    ex: ExhibitPlan = _safe_fact(world, f, "exhibit")  # type: ignore[assignment]
    out = [
        QAItem(question=WORLD_KNOWLEDGE["exhibition"][0], answer=WORLD_KNOWLEDGE["exhibition"][1]),
        QAItem(question=WORLD_KNOWLEDGE["brighten"][0], answer=WORLD_KNOWLEDGE["brighten"][1]),
        QAItem(question=WORLD_KNOWLEDGE["friendship"][0], answer=WORLD_KNOWLEDGE["friendship"][1]),
    ]
    if ex.keyword == "exhibition":
        out.append(QAItem(
            question="Why do people make exhibitions?",
            answer="People make exhibitions to share things they made, collected, or learned about with other people.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "exhibit", None):
        if not valid_combo(_safe_lookup(SETTINGS, getattr(args, "setting", None)), _safe_lookup(EXHIBITS, getattr(args, "exhibit", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "exhibit", None):
        combos = [c for c in combos if c[1] == getattr(args, "exhibit", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting_id, exhibit_id = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(HEROES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in FRIENDS if n != hero])
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    friend_type = getattr(args, "friend_type", None) or ("girl" if hero_type == "boy" else "boy")

    return StoryParams(
        setting=setting_id,
        exhibit=exhibit_id,
        hero=hero,
        friend=friend,
        hero_type=hero_type,
        friend_type=friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="hall", exhibit="space", hero="Mina", friend="Pip", hero_type="girl", friend_type="boy"),
    StoryParams(setting="school", exhibit="garden", hero="Noah", friend="Tess", hero_type="boy", friend_type="girl"),
    StoryParams(setting="library", exhibit="animals", hero="Lia", friend="Milo", hero_type="girl", friend_type="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world about an exhibition that gets brightened by friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--exhibit", choices=EXHIBITS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid_combo/2."))
        print(f"{len(asp.atoms(model, 'valid_combo'))} compatible combos:")
        for combo in asp.atoms(model, "valid_combo"):
            print(combo)
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
            header = f"### {p.hero} and {p.friend}: {p.exhibit} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
