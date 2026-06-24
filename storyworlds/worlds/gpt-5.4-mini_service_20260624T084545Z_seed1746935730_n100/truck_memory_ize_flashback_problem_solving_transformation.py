#!/usr/bin/env python3
"""
A small superhero-style story world about a child hero, a trusty truck, and a
memory-ize power that turns a forgotten problem into a solved one.

The seed tale behind this world:
A little hero loved a red truck that could carry big blocks. One day the truck
got stuck in a messy yard, and the hero felt worried because the truck held an
important memory token for a family surprise. The hero flashed back to how the
truck had helped before, remembered the right trick, and used the memory-ize
power to steady the wheels, lift the blocks, and transform the stuck moment
into a proud rescue.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    artifact: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
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
    place: str
    detail: str
    weather: str = ""
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
class Artifact:
    id: str
    label: str
    phrase: str
    risk: str
    region: str
    memory_role: str = ""
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
class Power:
    id: str
    label: str
    prep: str
    turn: str
    transforms: str
    helps: set[str] = field(default_factory=set)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story: list[list[str]] = [[]]
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
            self.story[-1].append(text)

    def para(self) -> None:
        if self.story[-1]:
            self.story.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.story if p)

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.story = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    sidekick: str
    artifact: str
    power: str
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


SETTINGS = {
    "garage": Setting(place="the garage", detail="The garage smelled like dust and sunshine."),
    "yard": Setting(place="the yard", detail="The yard was bright, but one muddy patch waited near the gate."),
    "workshop": Setting(place="the workshop", detail="The workshop hummed softly beside a table full of blocks."),
}

ARTIFACTS = {
    "memory_token": Artifact(
        id="memory_token",
        label="memory token",
        phrase="a silver memory token",
        risk="lost",
        region="bed",
        memory_role="flashback",
    ),
    "block_stack": Artifact(
        id="block_stack",
        label="block stack",
        phrase="a tall stack of bright blocks",
        risk="toppling",
        region="hands",
        memory_role="problem",
    ),
    "truck": Artifact(
        id="truck",
        label="truck",
        phrase="a red truck with strong wheels",
        risk="stuck",
        region="ground",
        memory_role="transform",
    ),
}

POWERS = {
    "memory_ize": Power(
        id="memory_ize",
        label="memory-ize",
        prep="closed their eyes and said the memory-ize word",
        turn="a clear flashback returned to them",
        transforms="the stuck moment turned useful",
        helps={"flashback", "problem", "transform"},
    ),
    "lift_burst": Power(
        id="lift_burst",
        label="lift-burst",
        prep="stomped one boot and called for a lift-burst",
        turn="a strong burst of bravery lifted the load",
        transforms="the heavy load shifted safely",
        helps={"problem", "transform"},
    ),
}

HERO_NAMES = ["Nova", "Rio", "Luna", "Milo", "Zuri", "Tara", "Jace", "Ivy"]
SIDEKICKS = ["small dog", "little robot", "bright bird", "tiny helper"]
HERO_TYPES = ["girl", "boy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world about a truck, memory-ize, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--power", choices=POWERS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for artifact in ARTIFACTS:
            for power in POWERS:
                if artifact == "truck" and power == "memory_ize":
                    combos.append((place, artifact, power))
                elif artifact == "memory_token" and power == "memory_ize":
                    combos.append((place, artifact, power))
                elif artifact == "block_stack" and power in {"memory_ize", "lift_burst"}:
                    combos.append((place, artifact, power))
    return combos


def explain_rejection(artifact: Artifact, power: Power) -> str:
    return f"(No story: {power.label} cannot reasonably solve {artifact.label} in this tiny superhero world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "artifact", None) and getattr(args, "power", None):
        if (getattr(args, "place", None) or "garage", getattr(args, "artifact", None), getattr(args, "power", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "artifact", None) is None or c[1] == getattr(args, "artifact", None))
              and (getattr(args, "power", None) is None or c[2] == getattr(args, "power", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, artifact, power = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, sidekick=sidekick, artifact=artifact, power=power)


def flashback_hint(world: World, hero: Entity, artifact: Entity) -> str:
    return f"{hero.id} remembered how {artifact.label} had helped before, when the day had gone wrong and then right again."


def solve_problem(world: World, hero: Entity, artifact: Entity, power: Power) -> str:
    hero.memes["worry"] = max(hero.memes.get("worry", 0), 1)
    hero.memes["focus"] = hero.memes.get("focus", 0) + 1
    artifact.meters["stuck"] = 1
    return f"{hero.id} noticed the problem at once: {artifact.phrase} was stuck, and the {artifact.label} could not move."


def transform_scene(world: World, hero: Entity, artifact: Entity, power: Power) -> str:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    artifact.meters["stuck"] = 0
    artifact.meters["ready"] = 1
    return f"Then {hero.id} used the {power.label} power, and {power.transforms}."


def tell(setting: Setting, artifact_cfg: Artifact, power_cfg: Power, hero_name: str, hero_type: str, sidekick: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type="thing", label=sidekick))
    artifact = world.add(Entity(id=artifact_cfg.id, type=artifact_cfg.id, label=artifact_cfg.label, phrase=artifact_cfg.phrase))
    hero.meters["bravery"] = 1
    hero.memes["protect"] = 1

    world.say(f"{hero.id} was a little {hero_type} hero who wore a bright cape and listened for trouble.")
    world.say(f"Beside {hero.id} was a {helper.label}, always ready to help.")
    world.say(f"In {setting.place}, the most important thing was {artifact_cfg.phrase}.")
    world.para()
    world.say(setting.detail)
    world.say(f"One afternoon, {hero.id} found the {artifact_cfg.label} in a hard spot.")
    world.say(solve_problem(world, hero, artifact, power_cfg))
    world.say(f"{helper.label.capitalize()} tugged at the wheel, but the truck still would not budge.")
    world.para()
    world.say(f"That was when {hero.id} had a flashback.")
    world.say(flashback_hint(world, hero, artifact))
    world.say(f"With a deep breath, {hero.id} {power_cfg.prep}.")
    world.say(f"At once, {power_cfg.turn}.")
    world.say(transform_scene(world, hero, artifact, power_cfg))
    world.say(f"The {artifact.label} rolled free, and {hero.id} smiled because the rescue was complete.")
    world.facts.update(hero=hero, helper=helper, artifact=artifact, power=power_cfg, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    art = _safe_fact(world, f, "artifact")
    power = _safe_fact(world, f, "power")
    return [
        f'Write a short superhero story for a child about {hero.id}, a {art.label}, and the power to "{power.label}".',
        f"Tell a brave story where a hero uses a flashback to solve a problem with a {art.label}.",
        f"Write a gentle rescue story that ends with transformation and a rolling truck.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    art = _safe_fact(world, f, "artifact")
    power = _safe_fact(world, f, "power")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"What did {hero.id} use the {power.label} power for?",
            answer=f"{hero.id} used the {power.label} power to help the {art.label} after it got stuck. That turned the hard moment into a rescue.",
        ),
        QAItem(
            question=f"Who helped {hero.id} beside the {art.label}?",
            answer=f"The {helper.label} helped by tugging and cheering, but {hero.id} had to solve the problem with the power.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, the stuck {art.label} rolled free, and the problem transformed into a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a truck for?", answer="A truck is a vehicle that can carry things from one place to another."),
        QAItem(question="What is a flashback?", answer="A flashback is a memory that brings an earlier moment back into your mind."),
        QAItem(question="What does it mean to solve a problem?", answer="To solve a problem means to find a way to make trouble go away."),
        QAItem(question="What is transformation?", answer="Transformation means something changes into a new form or a new state."),
    ]


ASP_RULES = r"""
artifact_ok(A) :- artifact(A).
power_ok(P) :- power(P).
compatible(grocery_truck, memory_ize).
compatible(memory_token, memory_ize).
compatible(block_stack, memory_ize).
compatible(block_stack, lift_burst).
valid_story(Place, Artifact, Power) :- setting(Place), compatible(Artifact, Power).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ARTIFACTS:
        lines.append(asp.fact("artifact", a))
    for p in POWERS:
        lines.append(asp.fact("power", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p[0], p[1], p[2]) for p in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ARTIFACTS, params.artifact), _safe_lookup(POWERS, params.power), params.hero_name, params.hero_type, params.sidekick)
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
    StoryParams(place="garage", hero_name="Nova", hero_type="girl", sidekick="tiny robot", artifact="truck", power="memory_ize"),
    StoryParams(place="yard", hero_name="Milo", hero_type="boy", sidekick="small dog", artifact="memory_token", power="memory_ize"),
    StoryParams(place="workshop", hero_name="Ivy", hero_type="girl", sidekick="bright bird", artifact="block_stack", power="lift_burst"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(asp.atoms(model, "valid_story"))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "artifact", None) is None or c[1] == getattr(args, "artifact", None))
              and (getattr(args, "power", None) is None or c[2] == getattr(args, "power", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, artifact, power = rng.choice(list(combos))
    return StoryParams(
        place=place,
        hero_name=getattr(args, "hero_name", None) or rng.choice(HERO_NAMES),
        hero_type=getattr(args, "hero_type", None) or rng.choice(HERO_TYPES),
        sidekick=getattr(args, "sidekick", None) or rng.choice(SIDEKICKS),
        artifact=artifact,
        power=power,
    )


if __name__ == "__main__":
    main()
