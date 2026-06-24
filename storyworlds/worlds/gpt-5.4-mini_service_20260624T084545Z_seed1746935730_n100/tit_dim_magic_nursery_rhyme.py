#!/usr/bin/env python3
"""
storyworlds/worlds/tit_dim_magic_nursery_rhyme.py
==================================================

A tiny, self-contained storyworld for a nursery-rhyme style tale about a
tit-dim little bird, a bit of magic, and a small problem that turns into a
gentle fix.

The domain is classical and simulation-driven:
- a little bird wants something bright and cheerful,
- a magic object or charm is involved,
- the wrong choice makes the bird feel dim or gloomy,
- a small helper action changes the state and the ending image.

The story is meant to read like a short nursery rhyme with concrete beats,
simple repetition, and a clear turn.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    held_by: Optional[str] = None
    glowing: bool = False
    magical: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm_ent: object | None = None
    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the moonlit garden"
    indoors: bool = False
    has_wind: bool = True
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
class Charm:
    id: str
    label: str
    phrase: str
    glow: str
    lift: str
    slip: str
    fix: str
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
class Prize:
    label: str
    phrase: str
    type: str
    place: str
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
    charm: str
    prize: str
    name: str
    gender: str
    helper: str
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
        self.facts: dict[str, object] = {}
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
        import copy

        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


def _rule_dim(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("dim", 0.0) >= THRESHOLD and not e.glowing:
            sig = ("dim", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["sad"] = e.memes.get("sad", 0.0) + 1
            out.append(f"The little light on {e.label or e.id} went soft and low.")
    return out


def _rule_glow(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("glow", 0.0) >= THRESHOLD and e.glowing:
            sig = ("glow", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["joy"] = e.memes.get("joy", 0.0) + 1
            out.append(f"A bright little gleam danced around {e.label or e.id}.")
    return out


def _rule_fix(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("fixed", 0.0) < THRESHOLD:
            continue
        sig = ("fixed", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["relief"] = e.memes.get("relief", 0.0) + 1
        out.append(f"That made everything feel right and tidy again.")
    return out


RULES = [_rule_dim, _rule_glow, _rule_fix]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def rhyme(line: str) -> str:
    return line


def nursery_opening(hero: Entity, charm: Charm) -> str:
    return (
        f"Little {hero.label}, a tit-dim sprite so small, "
        f"loved {charm.phrase} most of all."
    )


def clue_line(hero: Entity, charm: Charm, prize: Entity) -> str:
    return (
        f"{hero.pronoun().capitalize()} wanted {prize.phrase} to shine and sing, "
        f"but {charm.label} made a curious thing."
    )


def predict(world: World, charm: Charm, prize: Prize) -> bool:
    sim = world.copy()
    hero = sim.get("hero")
    if charm.id == "moonbell":
        hero.meters["dim"] += 1
    elif charm.id == "glimmer_leaf":
        hero.meters["dim"] += 1
    elif charm.id == "lantern_crumb":
        hero.meters["dim"] += 1
    return bool(sim.get("prize").meters.get("dim", 0.0) >= THRESHOLD)


def resolve_fix(world: World, hero: Entity, helper: Entity, charm: Charm, prize: Entity) -> None:
    helper.memes["kind"] = helper.memes.get("kind", 0.0) + 1
    hero.meters["fixed"] += 1
    hero.meters["dim"] = max(0.0, hero.meters.get("dim", 0.0) - 1)
    hero.meters["glow"] += 1
    hero.glowing = True
    prize.glowing = True
    propagate(world, narrate=True)
    world.say(
        f"Then {helper.label} gave {hero.pronoun('object')} a gentle wink, "
        f"and {hero.label} twinkled bright."
    )
    world.say(
        f"{hero.label} hummed a tune so soft and light; "
        f"{prize.label} shone clear in the nursery night."
    )


def tell(setting: Setting, charm: Charm, prize_cfg: Prize, name: str, gender: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero", kind="character", type=gender, label=name, phrase=f"little {name}",
        glowing=False, magical=True
    ))
    helper = world.add(Entity(
        id="helper", kind="character", type=helper_type, label=helper_type,
        phrase=f"kind {helper_type}"
    ))
    prize = world.add(Entity(
        id="prize", kind="thing", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, glowing=False
    ))
    charm_ent = world.add(Entity(
        id="charm", kind="thing", type=charm.id, label=charm.label,
        phrase=charm.phrase, magical=True
    ))

    world.facts.update(hero=hero, helper=helper, prize=prize, charm=charm, setting=setting)

    world.say(nursery_opening(hero, charm))
    world.say(clue_line(hero, charm, prize))
    world.para()
    world.say(f"In the {setting.place}, the grass was hush and green.")
    world.say(f"{hero.label} said, 'Oh dear me, I want a scene!'")
    world.say(f"{hero.label} reached for {prize.label} and held {prize.it()} near.")
    if charm.id == "moonbell":
        hero.meters["dim"] += 1
        world.say(f"But the moonbell chimed, and the little light grew queer.")
    elif charm.id == "glimmer_leaf":
        hero.meters["dim"] += 1
        world.say(f"The glimmer leaf flashed once, then made the colors dim.")
    elif charm.id == "lantern_crumb":
        hero.meters["dim"] += 1
        world.say(f"The lantern crumb gave one small spark, then hid within a whim.")
    propagate(world, narrate=True)
    world.para()
    world.say(f"{helper.label} saw the hush and came with a smile.")
    world.say(f"'Try this kind magic,' {helper.label} said, 'and wait a little while.'")
    resolve_fix(world, hero, helper, charm, prize)
    world.para()
    world.say(
        f"So {hero.label} kept {prize.label} bright and fine, "
        f"and every star sang, 'This day is thine.'"
    )
    return world


SETTINGS = {
    "garden": Setting(place="the moonlit garden"),
    "lawn": Setting(place="the dew-bright lawn"),
    "porch": Setting(place="the painted porch", indoors=False, has_wind=True),
}

CHARMS = {
    "moonbell": Charm(
        id="moonbell",
        label="the moonbell",
        phrase="the moonbell",
        glow="moon-glow",
        lift="lift",
        slip="dim",
        fix="ring it soft and slow",
    ),
    "glimmer_leaf": Charm(
        id="glimmer_leaf",
        label="the glimmer leaf",
        phrase="the glimmer leaf",
        glow="leaf-glow",
        lift="flutter",
        slip="dim",
        fix="hold it to the light",
    ),
    "lantern_crumb": Charm(
        id="lantern_crumb",
        label="the lantern crumb",
        phrase="the lantern crumb",
        glow="crumb-glow",
        lift="spark",
        slip="dim",
        fix="warm it in a hand",
    ),
}

PRIZES = {
    "ribbon": Prize(label="ribbon", phrase="a red ribbon", type="ribbon", place="neck"),
    "cup": Prize(label="cup", phrase="a tiny tea cup", type="cup", place="table"),
    "lantern": Prize(label="lantern", phrase="a little paper lantern", type="lantern", place="hook"),
}

GIRL_NAMES = ["Mimi", "Lulu", "Daisy", "Nina", "Poppy", "Tilly"]
BOY_NAMES = ["Benny", "Toby", "Rory", "Jasper", "Milo", "Tommy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CHARMS:
            for p in PRIZES:
                combos.append((s, c, p))
    return combos


def explain_rejection() -> str:
    return "(No story: that choice does not make a gentle rhyme-like magic problem.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tit-dim magic nursery-rhyme storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "rabbit", "cat"])
    ap.add_argument("--name")
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
    if getattr(args, "place", None) and getattr(args, "charm", None) and getattr(args, "prize", None):
        if (getattr(args, "place", None), getattr(args, "charm", None), getattr(args, "prize", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        charm=getattr(args, "charm", None) or rng.choice(list(CHARMS)),
        prize=getattr(args, "prize", None) or rng.choice(list(PRIZES)),
        name=name,
        gender=gender,
        helper=getattr(args, "helper", None) or rng.choice(["mother", "father", "rabbit", "cat"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    charm: Charm = _safe_fact(world, f, "charm")  # type: ignore[assignment]
    prize: Prize = _safe_fact(world, f, "prize")  # type: ignore[assignment]
    return [
        f'Write a short nursery-rhyme story about a tit-dim little {hero.type} and {charm.label}.',
        f"Tell a gentle magic tale where {hero.label} wants {prize.phrase} to shine.",
        f'Write a rhyme-like story that includes the word "tit-dim" and ends with a bright, happy fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, f, "helper")  # type: ignore[assignment]
    prize: Entity = _safe_fact(world, f, "prize")  # type: ignore[assignment]
    charm: Charm = _safe_fact(world, f, "charm")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who is the little tit-dim story about?",
            answer=f"It is about {hero.label}, a tiny {hero.type} in a magic nursery-rhyme world.",
        ),
        QAItem(
            question=f"What did {hero.label} want to make shine?",
            answer=f"{hero.label} wanted {prize.phrase} to shine and look bright again.",
        ),
        QAItem(
            question=f"Who helped {hero.label} with the magic?",
            answer=f"{helper.label} helped {hero.label} with {charm.label}, and that led to the happy fix.",
        ),
        QAItem(
            question=f"Why did the story feel dim at first?",
            answer=(
                f"The magic made {hero.label} feel dim for a little while, so the story had a gentle problem "
                f"before it turned bright again."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright, like a soft little light in the evening.",
        ),
        QAItem(
            question="What is a charm in a magic story?",
            answer="A charm is a small magical thing that can help, glow, or change how something feels.",
        ),
        QAItem(
            question="What is a nursery rhyme?",
            answer="A nursery rhyme is a short, song-like story with simple words and a gentle beat.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.glowing:
            bits.append("glowing=True")
        if e.magical:
            bits.append("magical=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(P) :- prize(P).
dim_story(P) :- prize_at_risk(P).
fix_story(P) :- prize_at_risk(P).
valid_story(S,C,P) :- setting(S), charm(C), prize(P), dim_story(P), fix_story(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CHARMS:
        lines.append(asp.fact("charm", c))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set((s, c, p) for s, c, p in valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.charm == "moonbell" and "garden" or "garden"),
        _safe_lookup(CHARMS, params.charm),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.gender,
        params.helper,
    )
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
    StoryParams(charm="moonbell", prize="lantern", name="Mimi", gender="girl", helper="mother"),
    StoryParams(charm="glimmer_leaf", prize="ribbon", name="Toby", gender="boy", helper="rabbit"),
    StoryParams(charm="lantern_crumb", prize="cup", name="Poppy", gender="girl", helper="cat"),
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
        for s, c, p in combos:
            print(f"  {s:10} {c:14} {p}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
