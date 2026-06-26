#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/sherbet_tyrant_optimum_sound_effects_teamwork_bedtime.py
=============================================================================================================================

A small bedtime-story world about a stubborn little tyrant, a sweet sherbet
treat, and the calm teamwork that finds the optimum way to end the night.

The premise is simple:
- A child wants one more noisy, playful bedtime moment.
- A little tyrant-like stuffed king insists on a perfect, exacting routine.
- The household must cooperate to choose the optimum quiet path to sleep.

The story is generated from a simulation that tracks:
- physical state in meters: treats, light, blankets, cups, noise, bedtime readiness
- emotional state in memes: stubbornness, worry, comfort, teamwork, sleepiness

The domain is intentionally small and child-facing, with gentle bedtime prose,
sound-effect touches, and a resolution where everyone helps.
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
# Domain constants
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    blanket: object | None = None
    child: object | None = None
    lamp: object | None = None
    parent: object | None = None
    sherbet: object | None = None
    tyrant: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.kind == "character" and self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in male:
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
class Setting:
    place: str = "the nursery"
    cozy: bool = True
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
class CharacterSpec:
    name: str
    type: str
    traits: list[str] = field(default_factory=list)
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
class ItemSpec:
    id: str
    label: str
    phrase: str
    kind: str
    sounds: list[str] = field(default_factory=list)
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
    child_name: str
    child_type: str
    child_trait: str
    parent_name: str
    parent_type: str
    tyrant_name: str
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
        self.facts: dict = {}
        self.noise_level: float = 0.0

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.noise_level = self.noise_level
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "nursery": Setting(place="the nursery", cozy=True),
    "bedroom": Setting(place="the bedroom", cozy=True),
    "hall": Setting(place="the hallway", cozy=False),
}

CHILDREN = [
    CharacterSpec("Mia", "girl", ["sleepy", "gentle"]),
    CharacterSpec("Noah", "boy", ["sleepy", "curious"]),
    CharacterSpec("Luna", "girl", ["sleepy", "brave"]),
    CharacterSpec("Eli", "boy", ["sleepy", "kind"]),
]

PARENTS = [
    CharacterSpec("Mom", "mother", ["steady", "kind"]),
    CharacterSpec("Dad", "father", ["steady", "kind"]),
]

TYRANTS = [
    ItemSpec(
        id="tyrant",
        label="little tyrant",
        phrase="a tiny stuffed king with a gold felt crown",
        kind="toy",
        sounds=["hmmph", "tap-tap"],
    ),
    ItemSpec(
        id="sherbet",
        label="sherbet",
        phrase="a small bowl of sherbet",
        kind="treat",
        sounds=["slurp", "sip"],
    ),
    ItemSpec(
        id="lamp",
        label="lamp",
        phrase="a warm little lamp",
        kind="light",
        sounds=["click"],
    ),
    ItemSpec(
        id="blanket",
        label="blanket",
        phrase="a soft blue blanket",
        kind="blanket",
        sounds=["swish"],
    ),
]

SFX = {
    "shimmer": "shhh",
    "stir": "whirr-whirr",
    "sip": "sip-sip",
    "settle": "fluff",
    "sleep": "murmur",
}

TRAITS = ["patient", "curious", "gentle", "playful", "soft-spoken"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
def _mk_entity_from_spec(spec: CharacterSpec | ItemSpec, eid: str) -> Entity:
    if isinstance(spec, CharacterSpec):
        return Entity(
            id=eid,
            kind="character",
            type=spec.type,
            label=spec.name,
            phrase=spec.name,
            meters={"sleepiness": 0.0, "cooperation": 0.0, "stubbornness": 0.0, "noise": 0.0},
            memes={"comfort": 0.0, "worry": 0.0, "teamwork": 0.0},
        )
    return Entity(
        id=eid,
        kind="thing",
        type=spec.kind,
        label=spec.label,
        phrase=spec.phrase,
        meters={"sweetness": 0.0, "quiet": 0.0, "brightness": 0.0},
        memes={},
    )


def _say_sfx(world: World, key: str) -> None:
    world.say(SFX.get(key, "softly"))


def _raise_noise(world: World, amount: float) -> None:
    world.noise_level += amount
    for c in world.characters():
        c.meters["noise"] += amount


def _calm_down(world: World, amount: float) -> None:
    world.noise_level = max(0.0, world.noise_level - amount)
    for c in world.characters():
        c.meters["noise"] = max(0.0, c.meters["noise"] - amount)


def _turn_off_light(world: World, lamp: Entity) -> None:
    lamp.meters["brightness"] = 0.0
    world.say("Click. The lamp turned low, and the room grew soft and gold.")


def _make_sherbet(world: World, sherbet: Entity, child: Entity, parent: Entity) -> None:
    sherbet.meters["sweetness"] = 1.0
    sherbet.held_by = child.id
    child.meters["comfort"] += 1.0
    parent.meters["cooperation"] += 1.0
    child.memes["teamwork"] += 1.0
    parent.memes["teamwork"] += 1.0
    world.say("Whirr-whirr, the spoon stirred the sherbet until it looked like a little sunset.")
    world.say(f"{child.label} took a tiny sip. Sip-sip. The sweet chill made the bedtime worry shrink.")


def _tame_tyrant(world: World, tyrant: Entity, child: Entity, parent: Entity) -> None:
    tyrant.memes["worry"] += 1.0
    tyrant.meters["stubbornness"] = 1.0
    world.say(
        f"The little tyrant sat very straight on the pillow and said, "
        f"\"No bedtime until everything is exactly right.\""
    )
    world.say(f"{child.label} looked at {parent.label}, and they both knew the exactness had become a problem.")


def _optimum_plan(world: World, child: Entity, parent: Entity, lamp: Entity, blanket: Entity, tyrant: Entity) -> None:
    child.memes["teamwork"] += 1.0
    parent.memes["teamwork"] += 1.0
    child.meters["sleepiness"] += 1.0
    parent.meters["cooperation"] += 1.0
    tyrant.meters["stubbornness"] = 0.0
    tyrant.memes["worry"] = 0.0
    world.say(
        f"{child.label} and {parent.label} found the optimum bedtime plan: "
        f"a tiny sherbet treat, one last cuddle, and the blanket tucked just so."
    )
    world.say("Swish. Fluff. The blanket became a nest, and the room grew quieter than a whisper.")


def _bedtime_settle(world: World, child: Entity, parent: Entity, tyrant: Entity) -> None:
    child.meters["sleepiness"] += 1.0
    parent.memes["comfort"] += 1.0
    tyrant.held_by = child.id
    world.say(
        f"{child.label} yawned, the little tyrant was tucked beside the pillow, "
        f"and {parent.label} stayed nearby to keep the dark feeling small."
    )
    world.say("Murmur... murmur... and then the whole room rested.")


# ---------------------------------------------------------------------------
# Story script
# ---------------------------------------------------------------------------
def tell(setting: Setting, child_spec: CharacterSpec, parent_spec: CharacterSpec, tyrant_name: str) -> World:
    world = World(setting)

    child = world.add(Entity(
        id=child_spec.name,
        kind="character",
        type=child_spec.type,
        label=child_spec.name,
        phrase=child_spec.name,
        meters={"sleepiness": 0.0, "cooperation": 0.0, "stubbornness": 0.0, "noise": 0.0},
        memes={"comfort": 0.0, "worry": 0.0, "teamwork": 0.0},
    ))
    parent = world.add(Entity(
        id=parent_spec.name,
        kind="character",
        type=parent_spec.type,
        label=parent_spec.name,
        phrase=parent_spec.name,
        meters={"sleepiness": 0.0, "cooperation": 0.0, "stubbornness": 0.0, "noise": 0.0},
        memes={"comfort": 0.0, "worry": 0.0, "teamwork": 0.0},
    ))
    tyrant = world.add(Entity(
        id=tyrant_name,
        kind="thing",
        type="toy",
        label="little tyrant",
        phrase="a tiny stuffed king with a gold felt crown",
        meters={"stubbornness": 0.0},
        memes={"worry": 0.0},
        held_by=child.id,
    ))
    sherbet = world.add(Entity(
        id="sherbet",
        kind="thing",
        type="treat",
        label="sherbet",
        phrase="a small bowl of sherbet",
        meters={"sweetness": 0.0},
        memes={},
        held_by=child.id,
    ))
    lamp = world.add(Entity(
        id="lamp",
        kind="thing",
        type="light",
        label="lamp",
        phrase="a warm little lamp",
        meters={"brightness": 1.0},
        memes={},
    ))
    blanket = world.add(Entity(
        id="blanket",
        kind="thing",
        type="blanket",
        label="blanket",
        phrase="a soft blue blanket",
        meters={"softness": 1.0},
        memes={},
    ))

    # Act 1
    world.say(
        f"It was bedtime in {world.setting.place}, and {child.label} had one more soft wish left in {child.pronoun('possessive')} heart."
    )
    world.say(
        f"The little tyrant sat nearby like a serious king, while the warm lamp glowed and the blanket waited."
    )
    world.para()

    _tame_tyrant(world, tyrant, child, parent)
    world.say(f"{child.label} wanted just one calm sweetness before sleep, something cool and gentle like sherbet.")

    # Act 2
    world.para()
    world.say("Then the room began to feel too full of fuss, and nobody liked that at all.")
    _raise_noise(world, 1.0)
    world.say("Tap-tap. The tyrant knocked the pillow once, and the sound made the bedtime quiet wobble.")
    world.say(f"{parent.label} took a slow breath and said it was time to choose the optimum way to rest.")
    world.say(f"{child.label} listened, because teamwork works best when everyone is trying to help.")

    # Act 3
    world.para()
    _make_sherbet(world, sherbet, child, parent)
    _say_sfx(world, "settle")
    _turn_off_light(world, lamp)
    _optimum_plan(world, child, parent, lamp, blanket, tyrant)
    _calm_down(world, 1.0)
    _bedtime_settle(world, child, parent, tyrant)

    world.facts.update(
        child=child,
        parent=parent,
        tyrant=tyrant,
        sherbet=sherbet,
        lamp=lamp,
        blanket=blanket,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryChoice:
    setting: str
    child: str
    parent: str
    tyrant_name: str
    trait: str
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


def valid_choices() -> list[StoryChoice]:
    out: list[StoryChoice] = []
    for setting in SETTINGS:
        for child in CHILDREN:
            for parent in PARENTS:
                if child.type == "boy" and parent.type == "mother":
                    continue
                if child.type == "girl" and parent.type == "father":
                    continue
                out.append(StoryChoice(setting, child.name, parent.name, "Tyrant", random.choice(TRAITS)))
    return out


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts_for(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        f'Write a bedtime story for a young child named {child.label} with a tiny tyrant toy, sherbet, and a gentle optimum ending.',
        f'Tell a soothing story where {child.label} and {f["parent"].label} use teamwork to calm a stubborn little tyrant before sleep.',
        f'Write a short bedtime tale that includes sherbet, soft sound effects, and a quiet plan that helps everyone rest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, tyrant, sherbet = f["child"], f["parent"], f["tyrant"], f["sherbet"]
    return [
        QAItem(
            question=f"What did {child.label} want before bedtime?",
            answer=f"{child.label} wanted one calm little treat and a quieter moment before sleep, so {child.pronoun('possessive')} heart could settle."
        ),
        QAItem(
            question=f"Why did the little tyrant cause a problem?",
            answer="The little tyrant wanted everything to be exactly right, and that made bedtime feel fussy and too loud."
        ),
        QAItem(
            question=f"What was the optimum bedtime plan?",
            answer=f"The optimum plan was to share sherbet, turn the lamp low, tuck in the blanket, and use teamwork so the room could grow quiet."
        ),
        QAItem(
            question=f"How did {child.label} feel at the end?",
            answer=f"{child.label} felt sleepy, safe, and pleased, because the bedtime plan worked and everyone helped."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sherbet?",
            answer="Sherbet is a sweet frozen treat that is cool, fruity, and soft to eat."
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together."
        ),
        QAItem(
            question="What is an optimum choice?",
            answer="An optimum choice is the best choice for the situation."
        ),
        QAItem(
            question="Why do bedtime stories use soft sound effects?",
            answer="Soft sound effects make a bedtime story feel gentle, cozy, and sleepy."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  noise_level={world.noise_level}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child(C) :- child_name(C).
parent(P) :- parent_name(P).
setting(S) :- setting_name(S).

gentle_bedtime(C,P,S) :- child(C), parent(P), setting(S), teamwork(C,P), sherbet_present, quiet_lamp, optimum_plan.
problem(C) :- stubborn_tyrant, noise_high, child(C).
resolved(C) :- gentle_bedtime(C,P,S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_name", s))
    for c in CHILDREN:
        lines.append(asp.fact("child_name", c.name))
    for p in PARENTS:
        lines.append(asp.fact("parent_name", p.name))
    lines.append(asp.fact("sherbet_present"))
    lines.append(asp.fact("quiet_lamp"))
    lines.append(asp.fact("optimum_plan"))
    lines.append(asp.fact("stubborn_tyrant"))
    lines.append(asp.fact("noise_high"))
    lines.append(asp.fact("teamwork", "child", "parent"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show gentle_bedtime/3. #show resolved/1."))
    atoms = set((a.name, len(a.arguments)) for a in model)
    ok = ("gentle_bedtime", 3) in atoms and ("resolved", 1) in atoms
    if ok:
        print("OK: ASP twin produces the bedtime-resolution atoms.")
        return 0
    print("MISMATCH: ASP twin did not produce expected atoms.")
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world with sherbet, a tyrant toy, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child")
    ap.add_argument("--parent")
    ap.add_argument("--tyrant-name")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    child = next((c for c in CHILDREN if c.name == getattr(args, "child", None)), None)
    if getattr(args, "child", None) and child is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if child is None:
        child = rng.choice(CHILDREN)
    parent = next((p for p in PARENTS if p.name == getattr(args, "parent", None)), None)
    if getattr(args, "parent", None) and parent is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if parent is None:
        parent = _safe_lookup(PARENTS, 0) if child.type == "girl" else _safe_lookup(PARENTS, 1)
    return StoryParams(
        setting=setting,
        child_name=child.name,
        child_type=child.type,
        child_trait=rng.choice(TRAITS),
        parent_name=parent.name,
        parent_type=parent.type,
        tyrant_name=getattr(args, "tyrant_name", None) or "Tyrant",
    )


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    child = next(c for c in CHILDREN if c.name == params.child_name)
    parent = next(p for p in PARENTS if p.name == params.parent_name)
    world = tell(setting, child, parent, params.tyrant_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show gentle_bedtime/3. #show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show gentle_bedtime/3. #show resolved/1."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        choices = [
            StoryParams("nursery", "Mia", "mother", "gentle", "Mom", "mother", "Tyrant"),
            StoryParams("bedroom", "Noah", "father", "patient", "Dad", "father", "Tyrant"),
            StoryParams("hall", "Luna", "mother", "soft-spoken", "Mom", "mother", "Tyrant"),
        ]
        samples = [generate(p) for p in choices]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
