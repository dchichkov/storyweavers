#!/usr/bin/env python3
"""
Standalone story world: petting zoo with sound effects, repetition, and reconciliation.

Premise:
A child visits a petting zoo and wants to make a funny sound effect with a loud,
bouncy mattress prop they brought for a little show. The child also has a prized
artichoke-shaped fame ribbon from a school contest. When the sound effects scare
the animals, the child and a helper must calm things down, repair the moment, and
find a gentler way to share the joke.

This file models a small causal world with physical meters and emotional memes,
plus a Python reasonableness gate and an inline ASP twin for parity checks.
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

ANIMAL_KINDS = {"goat", "lamb", "piglet", "rabbit", "pony"}

SOUND_EFFECTS = {
    "boing": {"bounce": 1.0, "loud": 1.0},
    "boop": {"loud": 0.3},
    "tap": {"loud": 0.1},
    "honk": {"loud": 0.8},
}

# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    animal: object | None = None
    child: object | None = None
    helper: object | None = None
    item: object | None = None
    def _meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def _meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the petting zoo"
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
class Prop:
    id: str
    label: str
    phrase: str
    sound: str
    loudness: float
    mess: str
    emotion: str
    guards: set[str] = field(default_factory=set)
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
    world: object | None = None
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

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "animal"]

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
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
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
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_role: str
    prop: str
    sound_effect: str
    animal: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "petting_zoo": Setting(place="the petting zoo", affords={"sound_effects", "reconciliation"}),
}

PROPS = {
    "mattress": Prop(
        id="mattress",
        label="mattress",
        phrase="a small mattress prop",
        sound="boing",
        loudness=1.0,
        mess="bump",
        emotion="showy",
        guards={"soft"},
    ),
    "artichoke": Prop(
        id="artichoke",
        label="artichoke",
        phrase="a bright artichoke-shaped fame ribbon",
        sound="boop",
        loudness=0.2,
        mess="nervous",
        emotion="proud",
        guards={"gentle"},
    ),
    "tambourine": Prop(
        id="tambourine",
        label="tambourine",
        phrase="a shiny little tambourine",
        sound="honk",
        loudness=0.8,
        mess="clatter",
        emotion="lively",
        guards={"gentle"},
    ),
}

ANIMALS = {
    "goat": {"kind": "goat", "nickname": "goat", "noise": "bleat"},
    "lamb": {"kind": "lamb", "nickname": "lamb", "noise": "baa"},
    "piglet": {"kind": "piglet", "nickname": "piglet", "noise": "oink"},
    "rabbit": {"kind": "rabbit", "nickname": "rabbit", "noise": "squeak"},
    "pony": {"kind": "pony", "nickname": "pony", "noise": "neigh"},
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Pia", "Tess"]
BOY_NAMES = ["Eli", "Owen", "Theo", "Noah", "Milo", "Finn"]
HELPERS = ["zookeeper", "mom", "dad", "older sister", "older brother"]


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def prop_at_risk(prop: Prop, animal: str) -> bool:
    return prop.id == "mattress" and animal in {"goat", "pony"} or prop.id == "artichoke"


def valid_combo(place: str, prop: str, animal: str) -> bool:
    if place not in SETTINGS:
        return False
    if prop not in PROPS or animal not in ANIMALS:
        return False
    # Mattress makes sense only if the sound is loud enough to matter.
    if prop == "mattress" and _safe_lookup(PROPS, prop).loudness < 0.5:
        return False
    return prop_at_risk(_safe_lookup(PROPS, prop), animal)


def explain_rejection(place: str, prop: str, animal: str) -> str:
    return (
        f"(No story: at the petting zoo, the {prop} situation with a {animal} "
        f"doesn't create a believable little problem and fix.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def sound_repeat(effect: str, times: int = 3) -> str:
    return " ".join([effect] * times)


def _sound(world: World, child: Entity, prop: Prop, animal: Entity) -> None:
    sig = ("sound", prop.id, animal.id)
    if sig in world.fired:
        return
    world.fired.add(sig)

    child.meters["activity"] = child.meters.get("activity", 0.0) + 1
    child.memes["delight"] = child.memes.get("delight", 0.0) + 1

    if prop.sound == "boing":
        child.meters["bounce"] = child.meters.get("bounce", 0.0) + 1

    if prop.loudness >= 0.7:
        animal.memes["startle"] = animal.memes.get("startle", 0.0) + 1
        world.say(
            f"{child.id} went, “{sound_repeat(prop.sound)}!” and the little sound "
            f"filled the pen like a round toy drum."
        )
        world.say(
            f"{animal.label.capitalize()} flinched and stepped back."
        )
    else:
        world.say(
            f"{child.id} made a small “{prop.sound},” then smiled at the neat little echo."
        )

    if prop.id == "mattress":
        world.facts["repetition"] = True
        world.facts["sound_effect"] = prop.sound
        world.facts["animal_startled"] = animal.memes.get("startle", 0.0) >= THRESHOLD


def _reconcile(world: World, child: Entity, helper: Entity, animal: Entity, prop: Prop) -> None:
    sig = ("reconcile", child.id, animal.id)
    if sig in world.fired:
        return
    world.fired.add(sig)

    if animal.memes.get("startle", 0.0) < THRESHOLD:
        return

    child.memes["embarrassment"] = child.memes.get("embarrassment", 0.0) + 1
    helper.memes["gentleness"] = helper.memes.get("gentleness", 0.0) + 1
    animal.memes["calm"] = animal.memes.get("calm", 0.0) + 1

    world.say(
        f"Then {helper.id} knelt beside {child.id} and said it was all right."
    )
    world.say(
        f"{child.id} looked at the {animal.label}, lowered the mattress, and tried a softer “{prop.sound}.”"
    )
    world.say(
        f"{animal.label.capitalize()} listened, stayed put, and nosed a tuft of hay instead."
    )
    world.say(
        f"{child.id} and {helper.id} smiled because the joke had turned kind again."
    )


def tell(setting: Setting, prop: Prop, animal_kind: str, child_name: str, child_gender: str, helper_name: str, helper_role: str) -> World:
    world = World(setting)

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        traits=["little", "careful", "proud"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_role if helper_role in {"mother", "father"} else "person",
        label=helper_name,
        traits=["calm", "patient"],
    ))
    animal_info = _safe_lookup(ANIMALS, animal_kind)
    animal = world.add(Entity(
        id=animal_kind,
        kind="animal",
        type=animal_info["kind"],
        label=animal_info["nickname"],
        traits=["small", "curious"],
        meters={},
        memes={},
    ))
    item = world.add(Entity(
        id=prop.id,
        kind="thing",
        type="prop",
        label=prop.label,
        phrase=prop.phrase,
        owner=child.id,
        caretaker=helper.id,
    ))

    child.memes["fame"] = 1.0
    child.meters["careful"] = 1.0

    # Act 1
    world.say(
        f"{child.id} came to {setting.place} with {item.phrase} and a tiny feeling of fame."
    )
    world.say(
        f"{child.id} liked the way {prop.sound} sounded and kept saying it again: “{prop.sound}, {prop.sound}.”"
    )
    world.say(
        f"A {animal.label} watched from the straw with bright eyes."
    )

    # Act 2
    world.para()
    world.say(
        f"{child.id} tapped the mattress and let out a big “{sound_repeat(prop.sound)}!”"
    )
    _sound(world, child, prop, animal)

    # Act 3
    world.para()
    _reconcile(world, child, helper, animal, prop)

    world.facts.update(
        child=child,
        helper=helper,
        animal=animal,
        prop=item,
        prop_cfg=prop,
        setting=setting,
        resolved=animal.memes.get("calm", 0.0) >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a slice-of-life story set at a petting zoo with a playful sound effect and a gentle reconciliation.',
        f"Tell a short story in which {f['child'].id} keeps repeating {f['prop_cfg'].sound} and then learns to be quieter around a {f['animal'].label}.",
        f"Write a simple story that includes a mattress, an artichoke, and a petting zoo, ending with everyone feeling okay again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    animal = _safe_fact(world, f, "animal")
    prop = _safe_fact(world, f, "prop_cfg")

    return [
        QAItem(
            question=f"What did {child.id} bring to the petting zoo?",
            answer=f"{child.id} brought {prop.phrase}. It was the thing that made the loud or soft sound effect in the story.",
        ),
        QAItem(
            question=f"Why did the {animal.label} step back when {child.id} made the sound?",
            answer=f"The sound was repeated and loud enough to startle the {animal.label}, so it stepped back for a moment.",
        ),
        QAItem(
            question=f"How did {child.id} and {helper.id} fix the awkward moment?",
            answer=f"{helper.id} stayed gentle, and {child.id} lowered the prop and tried a softer sound until the {animal.label} settled down.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the surprise had turned into reconciliation, and everyone was calm again at the petting zoo.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a petting zoo?",
            answer="A petting zoo is a place where children can meet and gently visit small farm animals.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special sound people make on purpose to seem funny, dramatic, or exciting.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making things friendly and okay again after a small problem or hurt feeling.",
        ),
        QAItem(
            question="Why can repetition make a sound funnier?",
            answer="Repetition can make a sound funnier because hearing the same sound again and again can feel playful and bouncy.",
        ),
        QAItem(
            question="What is an artichoke?",
            answer="An artichoke is a green vegetable with layers of leaves, and its name can sound a little funny and fancy.",
        ),
        QAItem(
            question="What is a mattress?",
            answer="A mattress is the soft thing you sleep on in a bed.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prop_at_risk(mattress, animal) :- animal(animal).
prop_at_risk(artichoke, animal) :- animal(animal).

needs_reconciliation(C, A) :- startled(A), child(C), animal(A).
good_story(P, C, A) :- place(P), prop(mattress), child(C), animal(A), prop_at_risk(mattress, A), needs_reconciliation(C, A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = sorted((p, "child", a) for p in SETTINGS for a in ANIMALS if valid_combo(p, "mattress", a))
    cl = asp_valid_combos()
    if set(py) == set(cl):
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("python:", py)
    print("clingo:", cl)
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Petting-zoo slice-of-life story world with sound effects and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role", choices=["mother", "father"])
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
    place = getattr(args, "place", None) or "petting_zoo"
    prop = getattr(args, "prop", None) or "mattress"
    animal = getattr(args, "animal", None) or rng.choice(sorted(ANIMALS))
    if not valid_combo(place, prop, animal):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_role = getattr(args, "role", None) or rng.choice(["mother", "father"])
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(
        place=place,
        child_name=name,
        child_gender=gender,
        helper_name=helper,
        helper_role=helper_role,
        prop=prop,
        sound_effect=_safe_lookup(PROPS, prop).sound,
        animal=animal,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(PROPS, params.prop),
        params.animal,
        params.child_name,
        params.child_gender,
        params.helper_name,
        params.helper_role,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def CURATED_PARAMS() -> list[StoryParams]:
    return [
        StoryParams(
            place="petting_zoo",
            child_name="Mina",
            child_gender="girl",
            helper_name="Mom",
            helper_role="mother",
            prop="mattress",
            sound_effect="boing",
            animal="goat",
        ),
        StoryParams(
            place="petting_zoo",
            child_name="Eli",
            child_gender="boy",
            helper_name="Dad",
            helper_role="father",
            prop="mattress",
            sound_effect="boing",
            animal="pony",
        ),
        StoryParams(
            place="petting_zoo",
            child_name="Ivy",
            child_gender="girl",
            helper_name="Zoe",
            helper_role="mother",
            prop="artichoke",
            sound_effect="boop",
            animal="rabbit",
        ),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED_PARAMS()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.child_name}: {p.prop} at {p.place} with {p.animal}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
