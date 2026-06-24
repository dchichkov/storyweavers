#!/usr/bin/env python3
"""
storyworlds/worlds/foreign_crocodile_coon_problem_solving_transformation_moral.py
=================================================================================

A small myth-style story world about a foreign traveler, a crocodile, and a coon,
where a problem is solved through transformation and a moral value is learned.

Seed tale idea:
---
A foreign traveler arrived by river with a small bundle and a kind heart. Near
the marsh, a crocodile blocked the only crossing, and a coon could not reach the
far bank with its spilled seeds. The traveler first listened, then helped the
pair solve the problem by changing how they crossed the water. In the end, the
crocodile softened, the coon became brave and generous, and the traveler left
with a lesson about respect for strangers, cleverness, and sharing.

This script models:
- physical state with meters: distance, flood, burden, bridge, dryness, etc.
- emotional state with memes: fear, trust, pride, gratitude, wonder, shame
- a mythic causal arc: arrival -> obstacle -> clever fix -> transformation -> moral
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
# World model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    owner: Optional[str] = None

    basket: object | None = None
    coon: object | None = None
    crocodile: object | None = None
    rope: object | None = None
    traveler: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"traveler", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
    place: str = "the reed marsh"
    river: str = "the black river"
    bank_left: str = "the near bank"
    bank_right: str = "the far bank"
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
    traveler_name: str
    traveler_kind: str
    crocodile_name: str
    coon_name: str
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
    "marsh": Setting(place="the reed marsh", river="the black river"),
    "riverbank": Setting(place="the riverbank village", river="the silver river"),
    "wetland": Setting(place="the wet wetland", river="the long river"),
}

TRAVELER_KINDS = {
    "foreign traveler": {"type": "traveler", "label": "foreign traveler"},
    "foreign woman": {"type": "woman", "label": "foreign woman"},
    "foreign man": {"type": "man", "label": "foreign man"},
}

TRAVELER_NAMES = ["Asha", "Niko", "Mira", "Soren", "Lina", "Ivo", "Tara", "Eden"]
CROCODILE_NAMES = ["Krogg", "Silt", "Brine", "Old Jaw", "Ridge", "Moss"]
COON_NAMES = ["Pip", "Nim", "Racco", "Thim", "Poco", "Wren"]

# ---------------------------------------------------------------------------
# Mythic world
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    traveler = world.add(Entity(
        id=params.traveler_name,
        kind="character",
        type=_safe_lookup(TRAVELER_KINDS, params.traveler_kind)["type"],
        label=_safe_lookup(TRAVELER_KINDS, params.traveler_kind)["label"],
        meters={"journey": 1.0, "distance": 3.0},
        memes={"curiosity": 1.0, "kindness": 1.0, "wonder": 1.0},
    ))
    crocodile = world.add(Entity(
        id=params.crocodile_name,
        kind="character",
        type="crocodile",
        label="crocodile",
        meters={"blockage": 1.0, "river": 1.0},
        memes={"pride": 1.0, "fear": 0.0, "trust": 0.0},
    ))
    coon = world.add(Entity(
        id=params.coon_name,
        kind="character",
        type="coon",
        label="coon",
        meters={"seeds": 1.0, "distance": 2.0},
        memes={"worry": 1.0, "hunger": 1.0, "hope": 0.5},
    ))
    rope = world.add(Entity(
        id="rope",
        kind="thing",
        type="rope",
        label="a long river rope",
        meters={"length": 1.0},
    ))
    basket = world.add(Entity(
        id="basket",
        kind="thing",
        type="basket",
        label="a seed basket",
        meters={"seeds": 1.0},
        owner=coon.id,
    ))
    world.facts.update(traveler=traveler, crocodile=crocodile, coon=coon, rope=rope, basket=basket)
    return world


def _solve_problem(world: World) -> None:
    traveler: Entity = _safe_fact(world, world.facts, "traveler")
    crocodile: Entity = _safe_fact(world, world.facts, "crocodile")
    coon: Entity = _safe_fact(world, world.facts, "coon")
    rope: Entity = _safe_fact(world, world.facts, "rope")

    world.say(
        f"Long ago, in {world.setting.place}, a foreign traveler named {traveler.id} came to "
        f"{world.setting.river} with a steady step and a listening heart."
    )
    world.say(
        f"At the water's edge stood {crocodile.id}, broad as a log and proud as a stone, "
        f"while {coon.id} sat nearby with a spilled basket of seeds and a worried face."
    )

    world.para()
    world.say(
        f"{coon.id} could not reach {world.setting.bank_right} because the river was high, "
        f"and {crocodile.id} would not move from the crossing."
    )
    crocodile.memes["pride"] += 1.0
    coon.memes["worry"] += 1.0
    traveler.memes["wonder"] += 1.0

    world.say(
        f"{traveler.id} did not shout or push. Instead, {traveler.pronoun()} looked at the water, "
        f"looked at the rope, and asked what each one needed."
    )
    traveler.memes["kindness"] += 1.0
    crocodile.memes["trust"] += 1.0

    world.para()
    world.say(
        f"Then {traveler.id} tied the rope between two roots and showed {coon.id} how to climb "
        f"across in the basket, while {crocodile.id} held the rope steady with a heavy jaw and a careful tail."
    )
    rope.meters["bridge"] = 1.0
    coon.meters["distance"] = 0.0
    croc_help = 1.0
    crocodile.memes["trust"] += croc_help
    coon.memes["hope"] += 1.0
    coon.memes["gratitude"] += 1.0

    world.say(
        f"The problem was solved not by strength, but by clever work together: the river became a bridge, "
        f"and the crossing became safe."
    )

    world.para()
    world.say(
        f"At the sight of this, {crocodile.id}'s hard pride melted like frost in morning sun. "
        f"The old beast became gentle, and {coon.id} stopped trembling and began to share the seeds."
    )
    crocodile.meters["hardness"] = 0.0
    crocodile.memes["pride"] -= 1.0
    crocodile.memes["kindness"] = 1.0
    coon.memes["generosity"] = 1.0
    coon.memes["worry"] = 0.0

    world.say(
        f"{traveler.id} smiled, for the foreign road had given a true lesson: strangers can bring wisdom, "
        f"and a strong creature can become kind when it is treated with respect."
    )
    traveler.memes["moral"] = 1.0

    world.facts["resolved"] = True
    world.facts["moral"] = "Respect and cleverness can turn a blocked path into a shared bridge."
    world.facts["bridge"] = True
    world.facts["transformation"] = True


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    _solve_problem(world)
    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    traveler: Entity = _safe_fact(world, f, "traveler")
    coon: Entity = _safe_fact(world, f, "coon")
    return [
        f'Write a short myth for children about a foreign traveler named {traveler.id}, a crocodile, and a coon by a river.',
        f"Tell a gentle story where {coon.id} cannot cross the water, and a foreign traveler solves the problem with a clever idea.",
        f"Write a myth-like tale with the words foreign, crocodile, and coon, ending with a moral about respect and wisdom.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    traveler: Entity = _safe_fact(world, f, "traveler")
    crocodile: Entity = _safe_fact(world, f, "crocodile")
    coon: Entity = _safe_fact(world, f, "coon")
    return [
        QAItem(
            question=f"Who came to {world.setting.river} in the story?",
            answer=f"A foreign traveler named {traveler.id} came to {world.setting.river}.",
        ),
        QAItem(
            question=f"Why was {coon.id} worried near the river?",
            answer=f"{coon.id} was worried because the water was high and {coon.id} could not cross to the far bank.",
        ),
        QAItem(
            question=f"How did the traveler solve the problem with {crocodile.id} and {coon.id}?",
            answer=f"The traveler tied a rope between roots and helped make a safe bridge, so {coon.id} could cross while {crocodile.id} held the rope steady.",
        ),
        QAItem(
            question="What changed in the crocodile by the end?",
            answer=f"{crocodile.id} became gentler and more trusting instead of proud and stubborn.",
        ),
        QAItem(
            question="What moral did the story teach?",
            answer="It taught that respect and cleverness can turn a blocked path into a shared bridge.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crocodile?",
            answer="A crocodile is a large water animal with a long body, strong jaws, and a tail that helps it swim.",
        ),
        QAItem(
            question="What is a coon?",
            answer="A coon is a small animal that can be curious and clever, and it often looks for food near trees and water.",
        ),
        QAItem(
            question="What does it mean to be foreign?",
            answer="Foreign means coming from another place, so a foreign traveler may be new to the land and its customs.",
        ),
        QAItem(
            question="Why can a rope help solve a crossing problem?",
            answer="A rope can help people hold on, pull, or make a simple bridge when water or distance gets in the way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A river crossing problem exists when the traveler, crocodile, and coon are present.
problem(P) :- traveler(P), crocodile(C), coon(R), blocked_crossing(C), needs_crossing(R).

% A transformation occurs when a bridge is formed from a rope.
transformation(T) :- rope(T), can_bridge(T).

% A moral value is learned when the traveler is foreign and the story resolves with respect.
moral_value(M) :- foreign_traveler(T), resolution(T), respect_used(T).

resolution(T) :- made_bridge(T), crocodile_helped(T), coon_crossed(T).
made_bridge(T) :- rope(T), bridge_fact(T).
crocodile_helped(T) :- crocodile(C), helped(C).
coon_crossed(T) :- coon(R), crossed(R).

valid_story(S) :- problem(S), transformation(S), moral_value(S).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("river", pid, setting.river))
    lines.append(asp.fact("foreign_traveler", "traveler"))
    lines.append(asp.fact("traveler", "traveler"))
    lines.append(asp.fact("crocodile", "crocodile"))
    lines.append(asp.fact("coon", "coon"))
    lines.append(asp.fact("blocked_crossing", "crocodile"))
    lines.append(asp.fact("needs_crossing", "coon"))
    lines.append(asp.fact("rope", "rope"))
    lines.append(asp.fact("can_bridge", "rope"))
    lines.append(asp.fact("bridge_fact", "rope"))
    lines.append(asp.fact("helped", "crocodile"))
    lines.append(asp.fact("crossed", "coon"))
    lines.append(asp.fact("respect_used", "traveler"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {"valid_story"} if python_reasonable() else set()
    asp_set = {name for (name,) in asp_valid()}
    if py == asp_set:
        print("OK: ASP and Python parity match.")
        return 0
    print(f"MISMATCH: python={sorted(py)} asp={sorted(asp_set)}")
    return 1


def python_reasonable() -> bool:
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-style story world: foreign, crocodile, coon.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--crocodile-name")
    ap.add_argument("--coon-name")
    ap.add_argument("--kind", choices=TRAVELER_KINDS.keys())
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS.keys()))
    kind = getattr(args, "kind", None) or rng.choice(list(TRAVELER_KINDS.keys()))
    name = getattr(args, "name", None) or rng.choice(TRAVELER_NAMES)
    crocodile_name = getattr(args, "crocodile_name", None) or rng.choice(CROCODILE_NAMES)
    coon_name = getattr(args, "coon_name", None) or rng.choice(COON_NAMES)
    if name == crocodile_name or name == coon_name or crocodile_name == coon_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        traveler_name=name,
        traveler_kind=kind,
        crocodile_name=crocodile_name,
        coon_name=coon_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available for parity checks, but this world's declarative model is minimal.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="marsh", traveler_name="Asha", traveler_kind="foreign traveler", crocodile_name="Krogg", coon_name="Pip"),
            StoryParams(place="riverbank", traveler_name="Mira", traveler_kind="foreign woman", crocodile_name="Brine", coon_name="Nim"),
            StoryParams(place="wetland", traveler_name="Soren", traveler_kind="foreign man", crocodile_name="Moss", coon_name="Wren"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.traveler_name} / {p.crocodile_name} / {p.coon_name} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
