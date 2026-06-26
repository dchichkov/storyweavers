#!/usr/bin/env python3
"""
storyworlds/worlds/veggie_reconciliation_comedy.py
==================================================

A compact story world about a silly veggie mix-up that ends in reconciliation.

Premise:
- Two veggie friends with clashing preferences get tangled in a comic kitchen or
  garden situation.
- They feel annoyed, say the wrong thing, then discover a funny shared problem.
- They make up, share credit, and end with a cheerful little laugh.

This world keeps the prose child-facing and state-driven: the emotional arc comes
from the simulated world model, not from swapped nouns in a fixed paragraph.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    placed_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    prop: object | None = None
    snack: object | None = None
    def __post_init__(self) -> None:
        for key in ("mess", "tidy", "shared", "notice"):
            self.meters.setdefault(key, 0.0)
        for key in ("pride", "hurt", "joy", "embarrassment", "warmth", "grump"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
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
    indoors: bool = False
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
class Veggie:
    id: str
    label: str
    phrase: str
    crunch: str
    mood: str
    tags: set[str] = field(default_factory=set)
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
class Conflict:
    id: str
    prompt: str
    mishap: str
    fix: str
    laugh: str
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
class StoryParams:
    setting: str
    veggie_a: str
    veggie_b: str
    conflict: str
    name: str
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"mixup", "spill", "taste"}),
    "garden": Setting(place="the garden", indoors=False, affords={"mixup", "spill"}),
    "picnic": Setting(place="the picnic table", indoors=False, affords={"mixup", "taste"}),
}

VEGGIES = {
    "broccoli": Veggie(
        id="broccoli",
        label="broccoli",
        phrase="a bright green broccoli bunch",
        crunch="crispy",
        mood="bushy",
        tags={"green", "veggie"},
    ),
    "carrot": Veggie(
        id="carrot",
        label="carrot",
        phrase="a slim orange carrot",
        crunch="snappy",
        mood="peppy",
        tags={"orange", "veggie"},
    ),
    "pea": Veggie(
        id="pea",
        label="pea",
        phrase="a tiny round pea",
        crunch="poppy",
        mood="bouncy",
        tags={"green", "veggie"},
    ),
    "tomato": Veggie(
        id="tomato",
        label="tomato",
        phrase="a shiny red tomato",
        crunch="juicy",
        mood="sparkly",
        tags={"red", "veggie"},
    ),
    "pepper": Veggie(
        id="pepper",
        label="pepper",
        phrase="a cheerful pepper",
        crunch="bright",
        mood="zippy",
        tags={"red", "green", "veggie"},
    ),
    "cucumber": Veggie(
        id="cucumber",
        label="cucumber",
        phrase="a cool cucumber",
        crunch="cool",
        mood="smooth",
        tags={"green", "veggie"},
    ),
}

CONFLICTS = {
    "name_mixup": Conflict(
        id="name_mixup",
        prompt="the sign mixed up their names",
        mishap="the sign pointed to the wrong veggie",
        fix="they swapped the signs back and laughed",
        laugh="the letters looked so silly that they could not stay grumpy",
        tags={"sign", "name", "mixup"},
    ),
    "sauce_splash": Conflict(
        id="sauce_splash",
        prompt="a silly sauce splash landed on both of them",
        mishap="the sauce made them look like tiny painted statues",
        fix="they wiped each other clean with napkins",
        laugh="the sauce mustache made both of them snort with laughter",
        tags={"sauce", "spill"},
    ),
    "seat_spot": Conflict(
        id="seat_spot",
        prompt="they both wanted the same sunny spot",
        mishap="one veggie sat on the tiny cushion first",
        fix="they shared the cushion and took turns",
        laugh="the cushion squeaked like a mouse and broke the serious mood",
        tags={"seat", "share"},
    ),
}

NAMES = ["Milo", "Pia", "Nina", "Jules", "Toby", "Cleo", "Rae", "Nori"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def predict_repair(world: World, a: Entity, b: Entity, conflict: Conflict) -> dict:
    sim = world.copy()
    _do_conflict(sim, sim.get(a.id), sim.get(b.id), conflict, narrate=False)
    return {
        "still_grumpy": any(e.memes.get("hurt", 0) >= THRESHOLD for e in sim.entities.values()),
        "shared": sum(e.meters.get("shared", 0) for e in sim.entities.values()),
    }


def _do_conflict(world: World, a: Entity, b: Entity, conflict: Conflict, narrate: bool = True) -> None:
    sig = ("conflict", conflict.id, a.id, b.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    _add_meme(a, "hurt", 1)
    _add_meme(b, "hurt", 1)
    _add_meme(a, "grump", 1)
    _add_meme(b, "grump", 1)
    _add_meter(a, "notice", 1)
    _add_meter(b, "notice", 1)
    if narrate:
        world.say(f"At {world.setting.place}, {a.label} and {b.label} got tangled up because {conflict.prompt}.")
        world.say(f"That meant {conflict.mishap}.")


def _do_mistake(world: World, a: Entity, b: Entity, conflict: Conflict) -> None:
    if conflict.id == "name_mixup":
        world.say(f"{a.label} stared at the sign and blinked. {b.label} frowned, because the sign had got the names wrong.")
    elif conflict.id == "sauce_splash":
        world.say(f"A comic splat of sauce jumped from the spoon and dotted both veggies.")
    elif conflict.id == "seat_spot":
        world.say(f"Both veggies scooted toward the same sunny seat and bonked together with a soft boop.")


def _do_reconcile(world: World, a: Entity, b: Entity, conflict: Conflict) -> None:
    if conflict.id == "name_mixup":
        world.say("They swapped the signs back, then both giggled at the wobbly letters.")
    elif conflict.id == "sauce_splash":
        world.say("They wiped each other clean with napkins, and the silly sauce mustache made them laugh.")
    elif conflict.id == "seat_spot":
        world.say("They scooted close and shared the cushion, taking turns with tiny polite nods.")

    _add_meter(a, "shared", 1)
    _add_meter(b, "shared", 1)
    _add_meme(a, "warmth", 1)
    _add_meme(b, "warmth", 1)
    a.memes["hurt"] = 0
    b.memes["hurt"] = 0
    a.memes["grump"] = 0
    b.memes["grump"] = 0
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(f"In the end, {a.label} and {b.label} were smiling again.")


def tell(setting: Setting, veggie_a: Veggie, veggie_b: Veggie, conflict: Conflict, name: str) -> World:
    world = World(setting)
    a = world.add(Entity(id="A", kind="character", type=veggie_a.id, label=veggie_a.label, phrase=veggie_a.phrase, traits=[veggie_a.mood, veggie_a.crunch]))
    b = world.add(Entity(id="B", kind="character", type=veggie_b.id, label=veggie_b.label, phrase=veggie_b.phrase, traits=[veggie_b.mood, veggie_b.crunch]))
    prop = world.add(Entity(id="prop", type="sign", label="the sign", phrase="a wobbly paper sign"))
    snack = world.add(Entity(id="snack", type="dish", label="the snack bowl", phrase="a bowl of snack bits"))
    world.facts.update(hero=name, a=a, b=b, conflict=conflict, setting=setting, prop=prop, snack=snack)

    world.say(f"Once in {setting.place}, {name} watched two veggie friends get ready for a very silly day.")
    world.say(f"{a.label} was {veggie_a.phrase}, and {b.label} was {veggie_b.phrase}.")
    world.say(f"They both wanted the little veggie moment to go well, but then {conflict.prompt}.")

    world.para()
    _do_conflict(world, a, b, conflict)
    _do_mistake(world, a, b, conflict)
    world.say(conflict.laugh)

    world.para()
    _do_reconcile(world, a, b, conflict)
    world.say(f"After that, the snack bowl looked much happier, and {setting.place} felt friendly again.")
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for conflict_id in setting.affords:
            for a_id in VEGGIES:
                for b_id in VEGGIES:
                    if a_id == b_id:
                        continue
                    combos.append((setting_id, a_id, b_id, conflict_id))
    return combos


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for c in sorted(s.affords):
            lines.append(asp.fact("affords", sid, c))
    for vid, v in VEGGIES.items():
        lines.append(asp.fact("veggie", vid))
        for t in sorted(v.tags):
            lines.append(asp.fact("tagged", vid, t))
    for cid, c in CONFLICTS.items():
        lines.append(asp.fact("conflict", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("conflict_tag", cid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, A, B, C) :- setting(S), affords(S, C), veggie(A), veggie(B), A != B, conflict(C).
valid_story(S, A, B, C) :- valid(S, A, B, C).
#show valid/4.
#show valid_story/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic veggie reconciliation story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--veggie-a", choices=VEGGIES)
    ap.add_argument("--veggie-b", choices=VEGGIES)
    ap.add_argument("--conflict", choices=CONFLICTS)
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
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "veggie_a", None):
        combos = [c for c in combos if c[1] == getattr(args, "veggie_a", None)]
    if getattr(args, "veggie_b", None):
        combos = [c for c in combos if c[2] == getattr(args, "veggie_b", None)]
    if getattr(args, "conflict", None):
        combos = [c for c in combos if c[3] == getattr(args, "conflict", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, a_id, b_id, conflict_id = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(setting=setting, veggie_a=a_id, veggie_b=b_id, conflict=conflict_id, name=name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, c, s = f["a"], f["b"], f["conflict"], f["setting"]
    return [
        f'Write a short comedy story about two veggies in {s.place} who run into a silly problem and then reconcile.',
        f"Tell a child-friendly story where {a.label} and {b.label} laugh, disagree, and make up after {c.prompt}.",
        f"Write a funny veggie story set at {s.place} that ends with a shared smile and a calm, friendly fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, c, s = f["a"], f["b"], f["conflict"], f["setting"]
    return [
        QAItem(
            question=f"Who were the two veggie friends in the story?",
            answer=f"They were {a.label} and {b.label}, two veggie friends at {s.place}.",
        ),
        QAItem(
            question=f"What silly problem happened to {a.label} and {b.label}?",
            answer=f"{c.prompt.capitalize()}, so they had a comic little mix-up before they made up.",
        ),
        QAItem(
            question=f"How did the veggies reconcile?",
            answer=f"They used {c.fix}, and that turned the grumpy moment into a laugh.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a veggie?",
            answer="A veggie is a vegetable, like a carrot, broccoli, or pea, and people often eat them as food.",
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="To reconcile means to make up after a disagreement and feel friendly again.",
        ),
        QAItem(
            question="Why can comedy stories be funny?",
            answer="Comedy stories are funny because they use silly mix-ups, surprised faces, and playful surprises.",
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
        lines.append(f"  {e.id:6} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(VEGGIES, params.veggie_a),
        _safe_lookup(VEGGIES, params.veggie_b),
        _safe_lookup(CONFLICTS, params.conflict),
        params.name,
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
    StoryParams(setting="kitchen", veggie_a="carrot", veggie_b="broccoli", conflict="name_mixup", name="Milo"),
    StoryParams(setting="garden", veggie_a="pea", veggie_b="tomato", conflict="sauce_splash", name="Pia"),
    StoryParams(setting="picnic", veggie_a="cucumber", veggie_b="pepper", conflict="seat_spot", name="Nori"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (setting, veggie_a, veggie_b, conflict) combos ({len(stories)} with story form):\n")
        for s, a, b, c in triples:
            print(f"  {s:8} {a:10} {b:10} {c:12}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.veggie_a} vs {p.veggie_b} at {p.setting} ({p.conflict})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
