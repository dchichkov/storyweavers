#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tang_moral_value_superhero_story.py
===============================================================================================================

A small superhero story world focused on Moral Value.

Premise:
A young hero named Tang wants to help people in a bright city, but a tempting
shortcut could make the rescue feel easy at first and wrong by the end. The
world tracks courage, honesty, and fairness as physical action and emotional
state, and the story resolves when Tang chooses the harder but better path.

This script follows the Storyweavers contract:
- self-contained stdlib storyworld
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- inline ASP twin plus Python reasonableness gate
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
    kind: str = "thing"  # hero | civilian | villain | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prize: object | None = None
    side: object | None = None
    vil: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Scene:
    place: str
    vibe: str
    risk: str
    moral_choice: str
    shortcut: str
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
class Power:
    id: str
    label: str
    method: str
    helps: set[str]
    rule: str
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
class Prize:
    label: str
    phrase: str
    risk: str
    value: str
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


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.lines = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    scene: str
    hero_name: str
    hero_type: str
    sidekick: str
    villain: str
    prize: str
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


SCENES = {
    "downtown": Scene(
        place="downtown",
        vibe="The skyscrapers flashed like silver mirrors above the street.",
        risk="a bus full of people could be delayed",
        moral_choice="tell the truth about the broken bridge instead of hiding it",
        shortcut="pretend the problem was already fixed",
    ),
    "harbor": Scene(
        place="the harbor",
        vibe="Waves tapped against the docks, and gulls cried over the water.",
        risk="boats could crash into the blocked channel",
        moral_choice="warn the harbor guard before anyone got hurt",
        shortcut="ignore the warning and let the crowd guess",
    ),
    "museum": Scene(
        place="the museum",
        vibe="Golden lights glowed over glass cases and polished floors.",
        risk="a shattered display could frighten the visitors",
        moral_choice="return the lost key to the curator right away",
        shortcut="keep it for a quick reward",
    ),
}

POWERS = {
    "tang-sense": Power(
        id="tang-sense",
        label="Tang Sense",
        method="notice hidden problems before they spread",
        helps={"truth", "warning", "care"},
        rule="A true hero uses a power to protect people, not to show off.",
    ),
    "wind-shield": Power(
        id="wind-shield",
        label="Wind Shield",
        method="push danger away with a clean gust",
        helps={"rescue", "fairness"},
        rule="A shield should keep others safe, even when nobody is watching.",
    ),
    "bright-step": Power(
        id="bright-step",
        label="Bright Step",
        method="jump quickly to the right place",
        helps={"rescue", "warning"},
        rule="Fast feet are best when they carry help, not bragging.",
    ),
}

PRIZES = {
    "key": Prize(label="key", phrase="a small brass key", risk="locked doors stayed closed", value="trust"),
    "badge": Prize(label="badge", phrase="a shiny captain badge", risk="people would follow the wrong leader", value="honor"),
    "map": Prize(label="map", phrase="a folded city map", risk="helpers could get lost", value="guidance"),
}

NAMES = ["Tang", "Mina", "Jasper", "Rosa", "Leo", "Ivy", "Nico", "Zara"]
SIDEKICKS = ["pigeon", "robot pup", "helper drone", "street cat"]
VILLAINS = ["the Whisperer", "Captain Clatter", "Lady Loop", "Mr. Mask"]
TYPE_BY_NAME = {"Tang": "boy"}
TRAITS = ["brave", "thoughtful", "quick", "kind", "steady"]


def moral_gate(scene: Scene, prize: Prize, power: Power) -> bool:
    return prize.value in power.helps


def explain_rejection(scene: Scene, prize: Prize, power: Power) -> str:
    return (
        f"(No story: {power.label} is not a good moral fit for {prize.label}. "
        f"The story needs a power that supports honesty, fairness, or rescue in a way that matches the choice.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for scene_id, scene in SCENES.items():
        for power_id, power in POWERS.items():
            for prize_id, prize in PRIZES.items():
                if moral_gate(scene, prize, power):
                    out.append((scene_id, power_id, prize_id))
    return out


class TraceRule:
    def __init__(self, name, fn):
        self.name = name
        self.fn = fn


def _r_moral_choice(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["honesty"] >= THRESHOLD and hero.memes["courage"] >= THRESHOLD:
        sig = ("choice",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        return ["__choice__"]
    return []


CAUSAL_RULES = [TraceRule("moral_choice", _r_moral_choice)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.fn(world)
            if produced:
                changed = True
                lines.extend([p for p in produced if p != "__choice__"])
    if narrate:
        for s in lines:
            world.say(s)
    return lines


def build_scene_story(world: World, hero: Entity, sidekick: Entity, villain: Entity, prize: Entity, power: Power) -> None:
    scene = world.scene
    world.say(f"{hero.id} was a young hero who loved helping people in {scene.place}.")
    world.say(scene.vibe)
    world.say(f"{hero.id} had {power.label}, and {power.method}.")
    world.say(f"{hero.id} and {sidekick.label} were watching over the city when {villain.label} caused trouble.")

    world.para()
    world.say(f"{villain.label} wanted the crowd to panic, but the real problem was that {prize.phrase} had gone missing.")
    world.say(f"If nobody acted soon, {scene.risk}.")
    hero.memes["courage"] += 1
    hero.memes["honesty"] += 1
    hero.memes["fairness"] += 1
    world.facts["risk"] = scene.risk
    world.facts["shortcut"] = scene.shortcut
    world.facts["choice"] = scene.moral_choice

    world.say(f"{hero.id} noticed the shortcut would be easy: {scene.shortcut}.")
    world.say(f"But {hero.id} knew the better choice was to {scene.moral_choice}.")
    world.say(f"{hero.id} took a deep breath and chose the honest path.")
    propagate(world, narrate=False)

    world.para()
    world.say(f"Using {power.label}, {hero.id} went to the right place and fixed the danger without showing off.")
    world.say(f"{hero.id} returned {prize.phrase} to the right hands, and the city felt safe again.")
    world.say(f"{sidekick.label.capitalize()} bumped against {hero.id}'s shoulder as the lights came back on.")
    world.say(f"In the end, {hero.id} was proud not because {hero.pronoun('subject')} was famous, but because {hero.pronoun('subject')} had done what was right.")


def tell(scene_id: str, hero_name: str, hero_type: str, sidekick: str, villain: str, prize_id: str) -> World:
    scene = _safe_lookup(SCENES, scene_id)
    power = next(iter(POWERS.values()))
    for p in POWERS.values():
        if moral_gate(scene, _safe_lookup(PRIZES, prize_id), p):
            power = p
            break

    world = World(scene)
    hero = world.add(Entity(id=hero_name, kind="hero", type=hero_type, label=hero_name))
    side = world.add(Entity(id="sidekick", kind="thing", type="thing", label=sidekick))
    vil = world.add(Entity(id="villain", kind="villain", type="thing", label=villain))
    prize = world.add(Entity(id="prize", kind="thing", type="thing", label=_safe_lookup(PRIZES, prize_id).label, phrase=_safe_lookup(PRIZES, prize_id).phrase, owner=hero.id))

    world.facts.update(scene=scene_id, hero=hero, sidekick=side, villain=vil, prize=prize, power=power)
    build_scene_story(world, hero, side, vil, prize, power)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child about "{f["hero"].id}" using the word "tang" in a brave rescue.',
        f"Tell a short moral-value superhero story where {f['hero'].id} chooses honesty over an easy shortcut in {f['scene']}.",
        f"Write a gentle action story about a hero, a missing prize, and the right choice to help people.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    power = _safe_fact(world, f, "power")
    scene = _safe_fact(world, f, "scene")
    return [
        QAItem(
            question=f"Who is the story about, and where does {hero.id} help people?",
            answer=f"The story is about {hero.id}, a young hero who helps people in {scene}.",
        ),
        QAItem(
            question=f"What moral choice did {hero.id} make instead of taking the shortcut?",
            answer=f"{hero.id} chose to do what was right: {world.scene.moral_choice}.",
        ),
        QAItem(
            question=f"What missing thing did {hero.id} return in the end?",
            answer=f"{hero.id} returned {prize.phrase} to the right hands.",
        ),
        QAItem(
            question=f"How did {power.label} help {hero.id}?",
            answer=f"{power.label} helped {hero.id} notice and fix the problem in a careful, heroic way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character who uses special abilities and courage to protect other people and do good.",
        ),
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth and not hiding what is important.",
        ),
        QAItem(
            question="What does fairness mean?",
            answer="Fairness means treating people in a kind and equal way so nobody is cheated.",
        ),
        QAItem(
            question="What is a shortcut?",
            answer="A shortcut is a quicker way to do something, but it is not always the best or most honest way.",
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
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
moral_fit(S,P,W) :- scene(S), prize(P), power(W), helps(W,V), prize_value(P,V).
valid(S,P,W) :- moral_fit(S,P,W).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_value", pid, prize.value))
    for wid, power in POWERS.items():
        lines.append(asp.fact("power", wid))
        for v in sorted(power.helps):
            lines.append(asp.fact("helps", wid, v))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero moral-value story world with Tang.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--villain", choices=VILLAINS)
    ap.add_argument("--prize", choices=PRIZES)
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
    combos = valid_combos()
    if getattr(args, "scene", None):
        combos = [c for c in combos if c[0] == getattr(args, "scene", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    scene, _, prize = rng.choice(list(combos))
    hero_name = getattr(args, "hero_name", None) or "Tang"
    hero_type = getattr(args, "hero_type", None) or TYPE_BY_NAME.get(hero_name, rng.choice(["boy", "girl"]))
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    villain = getattr(args, "villain", None) or rng.choice(VILLAINS)
    return StoryParams(scene=scene, hero_name=hero_name, hero_type=hero_type, sidekick=sidekick, villain=villain, prize=prize)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.scene, params.hero_name, params.hero_type, params.sidekick, params.villain, params.prize)
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
    StoryParams(scene="downtown", hero_name="Tang", hero_type="boy", sidekick="robot pup", villain="Captain Clatter", prize="map"),
    StoryParams(scene="harbor", hero_name="Ivy", hero_type="girl", sidekick="helper drone", villain="Lady Loop", prize="key"),
    StoryParams(scene="museum", hero_name="Leo", hero_type="boy", sidekick="street cat", villain="the Whisperer", prize="badge"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (scene, prize, power) combos:")
        for t in triples:
            print(" ", t)
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
