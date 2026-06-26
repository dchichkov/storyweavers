#!/usr/bin/env python3
"""
storyworlds/worlds/rhinoceros_vodka_aromatic_reconciliation_conflict_repetition_superhero.py
=============================================================================================

A small superhero storyworld about a stubborn rhinoceros, a sharp aromatic spill,
and a reconciliation that comes after repeated conflict.

Seed premise:
---
A tiny city superhero patrols the fragrant market district. One day, a rhinoceros
janitor accidentally knocks over a bottle of vodka used by the scent-maker for
cleaning and preserving aromatic herbs. The strong smell makes the hero think
something dangerous has happened, and the rhinoceros thinks the hero is blaming
him. They argue more than once until they learn the bottle was just a cleanup
tool, apologize, and work together to save the market.

The world tracks:
---
- Physical meters: spill, breakage, smell, mess, distance, damage
- Emotional memes: fear, anger, guilt, courage, trust, reconciliation, relief

Narrative instruments:
---
- Conflict: the hero and rhinoceros misunderstand the spill
- Repetition: the misunderstanding happens in a repeated loop of "warn / deny / accuse"
- Reconciliation: they repair the mistake, apologize, and cooperate
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bottle: object | None = None
    hero: object | None = None
    rhino: object | None = None
    def __post_init__(self) -> None:
        for k in ["spill", "breakage", "smell", "mess", "distance", "damage"]:
            self.meters.setdefault(k, 0.0)
        for k in ["fear", "anger", "guilt", "courage", "trust", "reconciliation", "relief"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero", "rhinoceros"}
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
    place: str = "the fragrant market"
    smell_level: str = "aromatic"
    world: object | None = None
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
class HeroConfig:
    name: str
    title: str
    suit_color: str
    power: str
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
class StoryParams:
    place: str
    hero_name: str
    rhino_name: str
    bottle_name: str
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
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.loop_count: int = 0

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.loop_count = self.loop_count
        return w


def _punc(text: str) -> str:
    return text[0].lower() + text[1:] if text else text


def _hero_line(hero: Entity) -> str:
    return f"{hero.id}, the city hero in a shining suit"


def _rhino_line(rhino: Entity) -> str:
    return f"{rhino.id}, a rhinoceros with a careful heart"


def _bottle_line(bottle: Entity) -> str:
    return f"{bottle.phrase}"


def _run_conflict(world: World, hero: Entity, rhino: Entity, bottle: Entity) -> None:
    if hero.memes["fear"] >= THRESHOLD and rhino.memes["guilt"] >= THRESHOLD:
        sig = ("conflict", world.loop_count)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["anger"] += 1
            rhino.memes["anger"] += 1
            world.say(
                f"{hero.id} pointed at {_bottle_line(bottle)} and warned that the strong "
                f"{world.setting.smell_level} smell meant trouble."
            )
            world.say(
                f"{rhino.id} snorted, worried that {hero.id} was blaming him for the whole mess."
            )


def _run_repetition(world: World, hero: Entity, rhino: Entity, bottle: Entity) -> None:
    if hero.memes["anger"] >= THRESHOLD and rhino.memes["anger"] >= THRESHOLD:
        sig = ("repetition", world.loop_count)
        if sig not in world.fired:
            world.fired.add(sig)
            world.loop_count += 1
            hero.memes["fear"] += 0.5
            rhino.memes["guilt"] += 0.5
            world.say(
                f"They had the same argument again: {hero.id} warned, {rhino.id} defended, "
                f"and the aromatic spill seemed to grow louder in both of their minds."
            )


def _run_reconciliation(world: World, hero: Entity, rhino: Entity, bottle: Entity) -> None:
    if bottle.meters["spill"] >= THRESHOLD and hero.memes["courage"] >= THRESHOLD and rhino.memes["guilt"] >= THRESHOLD:
        sig = ("reconciliation",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["trust"] += 1
            rhino.memes["trust"] += 1
            hero.memes["reconciliation"] += 1
            rhino.memes["reconciliation"] += 1
            hero.memes["anger"] = 0
            rhino.memes["anger"] = 0
            world.say(
                f"Then {hero.id} took a slow breath and saw the bottle was only for cleaning aromatic herbs."
            )
            world.say(
                f"{rhino.id} apologized for knocking it over, and {hero.id} apologized for shouting too fast."
            )
            world.say(
                f"Together they soaked up the vodka spill, and the market smelled clean again."
            )


def propagate(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    rhino = world.get("rhino")
    bottle = world.get("bottle")
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        before = (hero.memes.copy(), rhino.memes.copy(), bottle.meters.copy())
        _run_conflict(world, hero, rhino, bottle)
        _run_repetition(world, hero, rhino, bottle)
        _run_reconciliation(world, hero, rhino, bottle)
        after = (hero.memes.copy(), rhino.memes.copy(), bottle.meters.copy())
        if before != after:
            changed = True
    if not narrate:
        return


def setup_world(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="hero",
        label="hero",
        phrase="a small superhero with bright gloves",
    ))
    rhino = world.add(Entity(
        id=params.rhino_name,
        kind="character",
        type="rhinoceros",
        label="rhinoceros",
        phrase="a big rhinoceros wearing a work vest",
    ))
    bottle = world.add(Entity(
        id="bottle",
        kind="thing",
        type="bottle",
        label="bottle",
        phrase=f"a glass bottle of vodka used to clean aromatic herbs",
        caretaker=params.hero_name,
    ))
    world.facts.update(hero=hero, rhino=rhino, bottle=bottle)
    return world


def tell(world: World) -> None:
    hero = world.get("hero")
    rhino = world.get("rhino")
    bottle = world.get("bottle")

    hero.memes["courage"] += 1
    rhino.memes["guilt"] += 1

    world.say(f"{_hero_line(hero)} patrolled {world.setting.place}, listening for trouble.")
    world.say(f"{_rhino_line(rhino)} was sweeping near the spice stalls.")
    world.say(
        f"On the stone path lay {_bottle_line(bottle)}, a bottle of vodka the market keeper used for aromatic cleaning."
    )
    bottle.meters["breakage"] += 1
    bottle.meters["spill"] += 1
    bottle.meters["smell"] += 1
    hero.memes["fear"] += 1
    rhino.memes["guilt"] += 1
    world.say(
        f"The lid popped off, and a sharp, aromatic smell floated into the air."
    )
    world.say(
        f"{hero.id} thought the smell meant danger, and {rhino.id} thought the hero thought he had done something awful."
    )

    propagate(world, narrate=True)

    if hero.memes["reconciliation"] >= THRESHOLD:
        world.say(
            f"After that, {hero.id} and {rhino.id} stood shoulder to shoulder, "
            f"proud of the quiet, clean market."
        )
    else:
        world.say(
            f"They still had more to learn, but the city stayed safe under {hero.id}'s watch."
        )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    rhino = _safe_fact(world, f, "rhino")
    return [
        f"Write a short superhero story for children about {hero.id} and a rhinoceros named {rhino.id}.",
        f"Tell a story where an aromatic spill causes conflict, repetition, and then reconciliation.",
        f"Write a gentle city adventure featuring a vodka bottle used for aromatic cleaning, misunderstanding, and apology.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    rhino = world.get("rhino")
    bottle = world.get("bottle")
    qa = [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.id}, who patrolled the market and tried to keep everyone safe.",
        ),
        QAItem(
            question=f"What caused the conflict between {hero.id} and {rhino.id}?",
            answer=f"The conflict started when a bottle of vodka used for aromatic cleaning spilled and made a sharp smell.",
        ),
        QAItem(
            question=f"Why did {rhino.id} feel bad at first?",
            answer=f"{rhino.id} felt guilty because he knocked over the bottle and thought he had caused a big problem.",
        ),
    ]
    if world.facts["hero"].memes["reconciliation"] >= THRESHOLD:
        qa.append(QAItem(
            question="How did the story end?",
            answer="It ended with an apology, a calm explanation, and both of them cleaning the spill together.",
        ))
        qa.append(QAItem(
            question="What changed after the repeated argument?",
            answer="After the same argument happened again, they stopped, understood the bottle was for cleaning, and became friends again.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does aromatic mean?",
            answer="Aromatic means having a strong smell, often a pleasant one like herbs or spices.",
        ),
        QAItem(
            question="What is a rhinoceros?",
            answer="A rhinoceros is a very large animal with a horn on its nose.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop fighting, apologize, and make peace again.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


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


SETTINGS = {
    "market": Setting(place="the fragrant market"),
    "rooftop": Setting(place="the windy rooftop garden"),
    "alley": Setting(place="the lantern-lit alley"),
}

HEROES = ["Nova", "Spark", "Comet", "Valor", "Mira"]
RHINOS = ["Bongo", "Rumble", "Tusk", "Rafi", "Nuru"]
BOTTLES = [
    "a glass bottle of vodka used to clean aromatic herbs",
    "a tall bottle of vodka for aromatic polishing",
    "a small bottle of vodka kept beside the fragrant counter",
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, h, r) for p in SETTINGS for h in HEROES for r in RHINOS]


@dataclass
class ASPConfig:
    place: str
    hero: str
    rhino: str
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


ASP_RULES = r"""
place(P) :- setting(P).
hero(H) :- hero_name(H).
rhinoceros(R) :- rhino_name(R).

compatible(P,H,R) :- place(P), hero(H), rhinoceros(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for h in HEROES:
        lines.append(asp.fact("hero_name", h))
    for r in RHINOS:
        lines.append(asp.fact("rhino_name", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


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
    ap = argparse.ArgumentParser(description="A superhero storyworld with a rhinoceros, vodka, and aromatic reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--rhino")
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
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, hero, rhino = (list(rng.choice(combos)) + [None, None, None])[:3]
    if getattr(args, "hero", None):
        hero = getattr(args, "hero", None)
    if getattr(args, "rhino", None):
        rhino = getattr(args, "rhino", None)
    return StoryParams(place=place, hero_name=hero, rhino_name=rhino, bottle_name=rng.choice(BOTTLES))


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
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


CURATED = [
    StoryParams(place="market", hero_name="Nova", rhino_name="Bongo", bottle_name=_safe_lookup(BOTTLES, 0)),
    StoryParams(place="rooftop", hero_name="Spark", rhino_name="Rumble", bottle_name=_safe_lookup(BOTTLES, 1)),
    StoryParams(place="alley", hero_name="Valor", rhino_name="Nuru", bottle_name=_safe_lookup(BOTTLES, 2)),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, hero, rhino) combos:\n")
        for c in combos:
            print("  ", c)
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
