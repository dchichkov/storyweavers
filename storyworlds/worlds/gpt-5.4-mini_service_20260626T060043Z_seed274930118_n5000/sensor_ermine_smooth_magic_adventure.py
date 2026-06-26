#!/usr/bin/env python3
"""
Storyworld: Sensor, Ermine, and the Smooth Path
===============================================

A small Adventure-style world where a child explorer carries a magic sensor,
meets an ermine guide, and must choose a smooth path through a tricky place.

The story premise:
- A curious child wants to follow a hidden trail.
- A magic sensor helps detect danger or openings.
- An ermine can slip through narrow places and lead the way.
- The turn comes when rough ground blocks the path.
- The resolution comes when the child follows the smooth way the sensor found.

This world is built to produce short, complete, child-facing adventure stories
with a clear beginning, a state-driven middle, and an ending image proving
what changed.
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
    companion_of: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    magical: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    artifact: object | None = None
    companion: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    shadowy: bool
    smooth_places: set[str] = field(default_factory=set)
    rough_places: set[str] = field(default_factory=set)
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
    function: str
    clue: str
    magical: bool = False
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
    artifact: str
    name: str
    gender: str
    companion: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "cavern": Setting(place="the moonlit cavern", shadowy=True, smooth_places={"glass floor", "stone slide"}, rough_places={"rubble slope", "bramble shelf"}),
    "forest": Setting(place="the deep forest", shadowy=False, smooth_places={"mossy trail", "river stone path"}, rough_places={"roots", "thorn patch"}),
    "ruins": Setting(place="the old ruins", shadowy=True, smooth_places={"polished hall", "secret ramp"}, rough_places={"broken steps", "loose stones"}),
}

ARTIFACTS = {
    "sensor": Artifact(
        id="sensor",
        label="magic sensor",
        phrase="a small magic sensor with a blue glow",
        function="sense the smooth way",
        clue="It could hum when a safe path was near.",
        magical=True,
    ),
    "lantern": Artifact(
        id="lantern",
        label="magic lantern",
        phrase="a tiny magic lantern",
        function="light the way",
        clue="It shone when the path was calm and clear.",
        magical=True,
    ),
    "map": Artifact(
        id="map",
        label="magic map",
        phrase="a folded magic map",
        function="show the hidden path",
        clue="It warmed when a true route was nearby.",
        magical=True,
    ),
}

COMPANIONS = {
    "ermine": {
        "type": "ermine",
        "label": "ermine",
        "phrase": "a quick white ermine",
        "hint": "It slipped through tight places and never feared narrow ledges.",
    },
    "fox": {
        "type": "fox",
        "label": "fox",
        "phrase": "a clever little fox",
        "hint": "It watched carefully and noticed tiny clues.",
    },
    "owl": {
        "type": "owl",
        "label": "owl",
        "phrase": "a wise night owl",
        "hint": "It could see shapes even in dim places.",
    },
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Ada", "Zoe"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Leo", "Max", "Ben"]
TRAITS = ["curious", "brave", "gentle", "bold", "lively"]


ASP_RULES = r"""
setting(S).
artifact(A).
companion(C).

smooth(S, P) :- smooth_place(S, P).
rough(S, P) :- rough_place(S, P).

goal(A, smooth_path) :- artifact(A), magic(A).
safe_way(S, P) :- smooth(S, P), not rough(S, P).

ready_to_go(S, A, C) :- setting(S), artifact(A), companion(C), magic(A), sight(C).
has_resolution(S, A, C) :- ready_to_go(S, A, C), safe_way(S, P), senses(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.shadowy:
            lines.append(asp.fact("shadowy", sid))
        for p in sorted(s.smooth_places):
            lines.append(asp.fact("smooth_place", sid, p))
        for p in sorted(s.rough_places):
            lines.append(asp.fact("rough_place", sid, p))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("magic", aid))
    for cid in COMPANIONS:
        lines.append(asp.fact("companion", cid))
        if cid == "owl":
            lines.append(asp.fact("sight", cid))
        else:
            lines.append(asp.fact("sight", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show goal/2.\n#show safe_way/2.\n"))
    atoms = set(asp.atoms(model, "goal")) | set(asp.atoms(model, "safe_way"))
    if atoms:
        print("OK: ASP rules loaded and produced a model.")
        return 0
    print("MISMATCH: ASP model was empty.")
    return 1


def story_intro(world: World, hero: Entity, artifact: Entity, companion: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', hero.type)} {hero.type} who loved adventure."
    )
    world.say(
        f"One day, {hero.id} packed {artifact.phrase} and met {companion.phrase} at the edge of {world.setting.place}."
    )
    world.say(
        f"{artifact.label.capitalize()} promised to {artifact.function}, and the {companion.label} promised to help."
    )


def story_turn(world: World, hero: Entity, artifact: Entity, companion: Entity) -> None:
    rough = sorted(world.setting.rough_places)[0]
    smooth = sorted(world.setting.smooth_places)[0]
    artifact.meters["glow"] = 1.0
    companion.memes["alert"] = 1.0
    world.say(
        f"Deep inside, the trail split near {rough}, and the ground looked too hard to cross."
    )
    world.say(
        f"{artifact.label.capitalize()} gave a soft hum, and {hero.id} held it up until its glow pointed toward {smooth}."
    )
    world.say(
        f"The {companion.label} darted ahead first, proving the {smooth} way was safe."
    )
    world.facts["rough"] = rough
    world.facts["smooth"] = smooth


def story_resolution(world: World, hero: Entity, artifact: Entity, companion: Entity) -> None:
    smooth = _safe_fact(world, world.facts, "smooth")
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    world.say(
        f"{hero.id} followed the smooth path, and the tricky maze opened into a bright hidden chamber."
    )
    world.say(
        f"There, {hero.id}, the {companion.label}, and the glowing {artifact.label} found the treasure together."
    )
    world.say(
        f"At the end, the rough path was behind them, and the magic sensor had turned a scary search into a safe adventure."
    )


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    artifact_cfg = _safe_lookup(ARTIFACTS, params.artifact)
    comp_cfg = _safe_lookup(COMPANIONS, params.companion)
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        memes={"trait": params.trait},
    ))
    artifact = world.add(Entity(
        id="artifact",
        type="artifact",
        label=artifact_cfg.label,
        phrase=artifact_cfg.phrase,
        magical=artifact_cfg.magical,
        owner=hero.id,
        carried_by=hero.id,
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type=comp_cfg["type"],
        label=comp_cfg["label"],
        phrase=comp_cfg["phrase"],
        companion_of=hero.id,
    ))

    story_intro(world, hero, artifact, companion)
    world.say("")
    story_turn(world, hero, artifact, companion)
    world.say("")
    story_resolution(world, hero, artifact, companion)

    world.facts.update(hero=hero, artifact=artifact, companion=companion, params=params)
    return world


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "artifact", None) and getattr(args, "artifact", None) not in ARTIFACTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "companion", None) and getattr(args, "companion", None) not in COMPANIONS:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    artifact = getattr(args, "artifact", None) or rng.choice(list(ARTIFACTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = getattr(args, "companion", None) or "ermine"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)

    return StoryParams(place=place, artifact=artifact, name=name, gender=gender, companion=companion, trait=trait)


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short Adventure-style story for children about {p.name} carrying a magic sensor through {world.setting.place}.',
        f"Tell a story where a {p.gender} named {p.name} and an ermine search for a smooth path.",
        f"Create a gentle adventure with a glowing sensor, a small companion, and a hidden safe route.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    artifact: Entity = _safe_fact(world, world.facts, "artifact")
    companion: Entity = _safe_fact(world, world.facts, "companion")
    smooth = _safe_fact(world, world.facts, "smooth")
    rough = _safe_fact(world, world.facts, "rough")
    return [
        QAItem(
            question=f"What did {hero.id} carry on the adventure?",
            answer=f"{hero.id} carried {artifact.phrase}. It helped point out the safe path.",
        ),
        QAItem(
            question=f"Who helped {hero.id} find the way forward?",
            answer=f"The {companion.label} helped by darting ahead and leading toward the smooth way.",
        ),
        QAItem(
            question=f"What kind of path did the sensor find?",
            answer=f"It found the smooth path, not the rough place near {rough}.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The scary search became a safe adventure, and {hero.id} reached the hidden chamber.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sensor?",
            answer="A sensor is a tool that notices things, like movement, light, heat, or a safe way forward.",
        ),
        QAItem(
            question="What is an ermine?",
            answer="An ermine is a small, quick animal with white fur that can slip through narrow places.",
        ),
        QAItem(
            question="What does smooth mean?",
            answer="Smooth means flat and even, without many bumps or rough spots.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something special and impossible in real life, like a glowing tool that helps in a surprising way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"setting: {world.setting.place}")
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.magical:
            bits.append("magical=True")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        lines.append(f"{e.id}: {', '.join(bits)}")
    lines.append(f"facts: {world.facts.keys()}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with a magic sensor and an ermine guide.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--artifact", choices=sorted(ARTIFACTS))
    ap.add_argument("--companion", choices=sorted(COMPANIONS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=sorted(TRAITS))
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


CURATED = [
    StoryParams(place="cavern", artifact="sensor", name="Mina", gender="girl", companion="ermine", trait="curious"),
    StoryParams(place="forest", artifact="sensor", name="Theo", gender="boy", companion="ermine", trait="brave"),
    StoryParams(place="ruins", artifact="sensor", name="Ivy", gender="girl", companion="ermine", trait="lively"),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show goal/2.\n#show safe_way/2.\n"))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
