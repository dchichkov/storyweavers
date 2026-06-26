#!/usr/bin/env python3
"""
A small storyworld for a cautionary fairy tale set in a bedroom.

Premise:
A child in a bedtime bedroom wants to keep playing after the lantern is lit.
A warning is given about a troublesome anti-sleep charm that makes the room
noisier and lonelier if bedtime is delayed too long. The child resists, but a
kind guardian offers a gentler ritual: put away the trick toy, hush the room,
and climb into bed. The ending proves the change by showing the bedroom calm
and the child finally asleep.

This world supports dialogue and a cautionary turn, with a fairy-tale tone.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    guardian: object | None = None
    toy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "princess"}
        male = {"boy", "father", "dad", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Bedroom:
    place: str = "the bedroom"
    dark: bool = False
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
class Temptation:
    id: str
    verb: str
    gerund: str
    rush: str
    noise: str
    caution: str
    risk: str
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
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    quiets: set[str] = field(default_factory=set)
    protects: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, room: Bedroom) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("restless", 0.0) < THRESHOLD:
            continue
        sig = ("noise", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["noise"] = actor.meters.get("noise", 0.0) + 1
        out.append("The room grew noisier.")
    return out


def _r_dark_worry(world: World) -> list[str]:
    out: list[str] = []
    if not world.room.dark:
        return out
    for actor in world.characters():
        if actor.meters.get("fear", 0.0) < THRESHOLD:
            continue
        sig = ("worry", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append("The shadows felt a little larger.")
    return out


CAUSAL_RULES = [_r_noise, _r_dark_worry]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def story_setup_delight() -> str:
    return "The bedroom was soft with quilted shadows, and a moonbeam rested on the sill."


def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "small")
    world.say(
        f"There once was a little {trait} {child.type} named {child.id} "
        f"who loved every toy within {child.pronoun('possessive')} bedroom."
    )


def want_play(world: World, child: Entity, temptation: Temptation) -> None:
    child.memes["desire"] = child.memes.get("desire", 0.0) + 1
    world.say(
        f"{child.id} loved to {temptation.verb} after the lantern was lit, "
        f"because {temptation.gerund} felt like one more tiny adventure."
    )


def warn(world: World, guardian: Entity, child: Entity, temptation: Temptation, toy: Entity) -> bool:
    if child.meters.get("restless", 0.0) < THRESHOLD:
        return False
    world.facts["risk"] = temptation.risk
    world.facts["caution"] = temptation.caution
    world.say(
        f'"If you keep trying to {temptation.verb}," said {guardian.id}, '
        f'"that {toy.label} will turn into an {temptation.keyword} trick and make '
        f'the bedroom {temptation.noise}."'
    )
    return True


def defy(world: World, child: Entity, temptation: Temptation) -> None:
    child.memes["defiance"] = child.memes.get("defiance", 0.0) + 1
    child.meters["restless"] = child.meters.get("restless", 0.0) + 1
    world.say(
        f'"But I am not sleepy yet," said {child.id}. '
        f'{child.id} tried to {temptation.rush}, and the sheets rustled.'
    )
    propagate(world, narrate=True)


def offer_remedy(world: World, guardian: Entity, child: Entity, remedy: Remedy, temptation: Temptation) -> None:
    world.say(
        f'Then {guardian.id} pointed to the pillow and said, '
        f'"Let us {remedy.prep} instead, and we can still keep the tale gentle."'
    )
    world.say(
        f'That was the old fairy-tale way: not a scolding, but a safer path.'
    )
    child.memes["hope"] = child.memes.get("hope", 0.0) + 1
    child.memes["defiance"] = 0.0


def accept(world: World, child: Entity, guardian: Entity, remedy: Remedy, toy: Entity) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    child.meters["restless"] = 0.0
    world.say(
        f'{child.id} nodded, tucked the {toy.label} away, and went to the bed. '
        f'{guardian.id} smiled, and together they {remedy.tail}.'
    )
    world.say(
        f'At last the bedroom was quiet again, and {child.id} was asleep under the blanket.'
    )


def tell(room: Bedroom, temptation: Temptation, remedy: Remedy, child_name: str,
         child_type: str = "girl", guardian_type: str = "mother") -> World:
    world = World(room)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        traits=["little", "curious", "stubborn"],
    ))
    guardian = world.add(Entity(
        id="Mara",
        kind="character",
        type=guardian_type,
        label="the guardian",
    ))
    toy = world.add(Entity(
        id="toy",
        type="thing",
        label="music box",
        phrase="a tiny music box with a silver key",
        caretaker=guardian.id,
    ))

    world.say(story_setup_delight())
    introduce(world, child)
    world.say(f"{child.id} adored {toy.phrase}, especially when its tune twinkled like a star.")
    world.para()
    world.say(f"One night, {child.id} and {guardian.id} were in {world.room.place}.")
    want_play(world, child, temptation)
    child.meters["restless"] = 1.0
    warn(world, guardian, child, temptation, toy)
    defy(world, child, temptation)
    world.para()
    offer_remedy(world, guardian, child, remedy, temptation)
    accept(world, child, guardian, remedy, toy)

    world.facts.update(
        child=child,
        guardian=guardian,
        toy=toy,
        temptation=temptation,
        remedy=remedy,
        room=room,
    )
    return world


SETTINGS = {
    "bedroom": Bedroom(place="the bedroom", dark=False, affords={"play", "rest"}),
}

TEMPTATIONS = {
    "tapping": Temptation(
        id="tapping",
        verb="tap the walls",
        gerund="tapping in time",
        rush="tap the headboard harder and harder",
        noise="loud",
        caution="A little tapping can wake a sleepy room",
        risk="the lantern glow will turn into a restless night",
        keyword="anti",
        tags={"anti", "noise"},
    ),
    "whispering": Temptation(
        id="whispering",
        verb="whisper to the dolls",
        gerund="whispering stories",
        rush="whisper louder and louder",
        noise="full of whispers",
        caution="Too many whispers can keep dreams away",
        risk="the quilt will not feel cozy enough for sleep",
        keyword="anti",
        tags={"anti", "quiet"},
    ),
}

REMEDIES = {
    "book": Remedy(
        id="book",
        label="bedtime book",
        prep="open the bedtime book and read one calm page",
        tail="read one calm page and turned out the lamp",
        quiets={"noise"},
        protects={"rest"},
    ),
    "song": Remedy(
        id="song",
        label="soft song",
        prep="sing a soft song and smooth the blanket",
        tail="sang a soft song and tucked the blanket higher",
        quiets={"noise"},
        protects={"rest"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Elsa", "Ivy", "Tessa"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Milo", "Hugo", "Eli"]
TRAITS = ["brave", "curious", "stubborn", "gentle", "bright", "dreamy"]


@dataclass
class StoryParams:
    place: str
    temptation: str
    remedy: str
    name: str
    gender: str
    guardian: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, room in SETTINGS.items():
        for temp_id in room.affords:
            for remedy_id in REMEDIES:
                combos.append((place, temp_id, remedy_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedroom fairy tale with dialogue and caution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "temptation", None) is None or c[1] == getattr(args, "temptation", None))
              and (getattr(args, "remedy", None) is None or c[2] == getattr(args, "remedy", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, temptation, remedy = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = getattr(args, "guardian", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, temptation, remedy, name, gender, guardian, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    temp = _safe_fact(world, f, "temptation")
    return [
        f'Write a fairy tale in a bedroom where the word "{temp.keyword}" appears and a child must choose sleep over play.',
        f"Tell a cautionary story about {child.id} in {world.room.place} who wants to {temp.verb}, but learns a gentler bedtime path.",
        f"Write a short dialogue-heavy tale for a young child that begins with a restless bedroom and ends with calm blankets.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    guardian: Entity = _safe_fact(world, f, "guardian")
    toy: Entity = _safe_fact(world, f, "toy")
    temp: Temptation = _safe_fact(world, f, "temptation")
    remedy: Remedy = _safe_fact(world, f, "remedy")
    return [
        QAItem(
            question=f"Who was the story about in the bedroom?",
            answer=f"It was about {child.id}, a little {next(t for t in child.traits if t != 'little')} {child.type}, and {guardian.id}, who helped with bedtime.",
        ),
        QAItem(
            question=f"What did {child.id} want to do instead of settling down?",
            answer=f"{child.id} wanted to {temp.verb}, because {temp.gerund} felt like a game.",
        ),
        QAItem(
            question=f"Why did {guardian.id} warn {child.id} about the {toy.label}?",
            answer=f"{guardian.id} warned {child.id} because the {toy.label} had become part of an {temp.keyword} trick, and it could make the bedroom {temp.noise}.",
        ),
        QAItem(
            question=f"What helped {child.id} choose a safer bedtime?",
            answer=f"The gentle answer was {remedy.label}: {remedy.prep}. That helped {child.id} calm down and go to bed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bedroom for?",
            answer="A bedroom is a room where people sleep, rest, and keep comforting things near the bed.",
        ),
        QAItem(
            question="Why is bedtime meant to be quiet?",
            answer="Bedtime is meant to be quiet so the mind can slow down, the room can settle, and sleep can come easily.",
        ),
        QAItem(
            question="What does caution mean in a fairy tale?",
            answer="Caution means a character notices a danger and chooses a safer path before anything goes wrong.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(TEMPTATIONS, params.temptation),
        _safe_lookup(REMEDIES, params.remedy),
        params.name,
        params.gender,
        params.guardian,
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


ASP_RULES = r"""
in_bedroom(P) :- setting(P).
restless(C) :- child(C).
noisy(C) :- restless(C).
caution_needed(C) :- restless(C), temptation(T), risk(T, _).
safe(C) :- remedy(R), not noisy(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for tid, t in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", tid))
        lines.append(asp.fact("risk", tid, t.risk))
    for rid in REMEDIES:
        lines.append(asp.fact("remedy", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show in_bedroom/1.")
    model = asp.one_model(program)
    asp_rooms = set(asp.atoms(model, "in_bedroom"))
    py_rooms = {(k,) for k in SETTINGS}
    if asp_rooms == py_rooms:
        print(f"OK: clingo gate matches valid bedroom facts ({len(py_rooms)} rooms).")
        return 0
    print("MISMATCH between clingo and Python:")
    if asp_rooms - py_rooms:
        print("  only in clingo:", sorted(asp_rooms - py_rooms))
    if py_rooms - asp_rooms:
        print("  only in python:", sorted(py_rooms - asp_rooms))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show in_bedroom/1."))
    return sorted(set(asp.atoms(model, "in_bedroom")))


def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show in_bedroom/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show in_bedroom/1."))
        print(f"{len(asp.atoms(model, 'in_bedroom'))} bedroom facts.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("bedroom", "tapping", "book", "Mira", "girl", "mother", "curious"),
            StoryParams("bedroom", "whispering", "song", "Owen", "boy", "father", "stubborn"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = build_story_params_from_args(args, random.Random(seed))
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
