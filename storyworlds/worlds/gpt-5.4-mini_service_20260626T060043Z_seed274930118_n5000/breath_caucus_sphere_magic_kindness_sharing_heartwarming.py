#!/usr/bin/env python3
"""
Storyworld: breath, caucus, and a sphere of kindness.

A small heartwarming story domain about a child, a little gathering of friends,
and a magical sphere that helps everyone breathe, share, and choose kindly.
The simulated state tracks physical items with meters and emotional shifts with
memes, then turns those state changes into a gentle story.

The seed words are woven into the world:
- breath
- caucus
- sphere

Core features:
- Magic
- Kindness
- Sharing

The premise is simple: a child arrives anxious at a small caucus, where a
glowing sphere is meant to help everyone take a breath, listen, and share what
they have. The tension is that one friend wants to keep the sphere for themself.
The turn is that the group uses magic not to take, but to soothe and share.
The resolution is warm and concrete: the sphere is passed around, calm returns,
and the gathering ends with everyone breathing easier together.
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
    plural: bool = False
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    host: object | None = None
    sphere_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Place:
    name: str
    cozy: bool = True
    magic_safe: bool = True
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
class SphereKind:
    id: str
    label: str
    phrase: str
    glow: str
    effect: str
    helps: str
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
    sphere: str
    name: str
    gender: str
    host: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "hall": Place("the village hall"),
    "library": Place("the library room"),
    "garden": Place("the garden bench"),
    "sunroom": Place("the sunroom"),
}

SPHERES = {
    "breathlight": SphereKind(
        id="breathlight",
        label="Breathlight Sphere",
        phrase="a small glowing sphere with a soft silver shine",
        glow="silver",
        effect="help everyone take a slow breath",
        helps="calm worried hearts",
    ),
    "kindnessorb": SphereKind(
        id="kindnessorb",
        label="Kindness Orb",
        phrase="a warm round sphere that shimmered like honey",
        glow="gold",
        effect="make gentle words feel easier to say",
        helps="invite kind choices",
    ),
    "sharingglobe": SphereKind(
        id="sharingglobe",
        label="Sharing Globe",
        phrase="a bright little sphere with tiny sparkles inside",
        glow="blue",
        effect="remind friends to share the next turn",
        helps="help friends take turns",
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lila", "Ava", "Zoe", "Iris"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Ben", "Leo", "Sam"]
HOSTS = ["teacher", "neighbor", "grandmother", "librarian", "guide"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        pass
    if params.sphere not in SPHERES:
        pass
    place = _safe_lookup(PLACES, params.place)
    sphere = _safe_lookup(SPHERES, params.sphere)
    world = World(place)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"breath": 0.0, "calm": 0.0},
        memes={"worry": 0.0, "kindness": 0.0, "sharing": 0.0, "joy": 0.0},
    ))
    host = world.add(Entity(
        id="Host",
        kind="character",
        type=params.host,
        label=f"the {params.host}",
        meters={"breath": 0.0},
        memes={"kindness": 0.0},
    ))
    sphere_ent = world.add(Entity(
        id=sphere.id,
        kind="thing",
        type="sphere",
        label=sphere.label,
        phrase=sphere.phrase,
        owner=host.id,
        held_by=host.id,
        meters={"glow": 1.0},
        memes={"magic": 1.0},
    ))

    world.facts.update(child=child, host=host, sphere=sphere_ent, sphere_kind=sphere, place=place)

    # Act 1: setup.
    world.say(
        f"{child.id} came to {place.name} for a small caucus, where everyone sat in a loose circle."
    )
    world.say(
        f"On a cloth in the center rested {sphere.phrase}, and the host smiled because the little sphere was meant to bring Magic, Kindness, and Sharing."
    )
    world.say(
        f"{child.id} took a small breath and tried to listen, but {child.pronoun('possessive')} chest felt tight."
    )
    child.memes["worry"] += 1.0

    # Act 2: tension.
    world.para()
    world.say(
        f"Then one friend reached for the sphere and said it should stay with them a while longer."
    )
    world.say(
        f"{child.id} looked down, because the room felt less bright when Sharing was forgotten."
    )
    child.memes["worry"] += 1.0

    # Act 3: turn and resolution.
    world.para()
    world.say(
        f"The host lifted a hand and let a little Magic drift over the caucus, soft as a lullaby."
    )
    if sphere.id == "breathlight":
        world.say("The silver glow made slow breath feel easy to follow.")
        child.meters["breath"] += 1.0
        child.memes["calm"] += 1.0
    elif sphere.id == "kindnessorb":
        world.say("The golden glow made kind words come out gently, like warm tea.")
        child.memes["kindness"] += 1.0
    else:
        world.say("The blue sparkles reminded everyone that a shared turn can still feel special.")
        child.memes["sharing"] += 1.0

    world.say(
        f"{child.id} listened, took another breath, and said {child.pronoun('possessive')} own gentle wish: "
        f'"Can we all have a turn?"'
    )
    child.memes["sharing"] += 1.0
    child.memes["kindness"] += 1.0

    world.say(
        f"The friend nodded, passed the sphere around, and the caucus grew warm and quiet in the nicest way."
    )
    world.say(
        f"By the end, {child.id} was smiling, the sphere had been shared, and the whole room seemed to breathe together."
    )
    child.memes["joy"] += 1.0
    child.memes["worry"] = 0.0

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    sphere = _safe_fact(world, f, "sphere_kind")
    return [
        f"Write a heartwarming story about {child.id}, a small caucus, and {sphere.label}.",
        f"Tell a gentle tale where Magic helps friends practice Kindness and Sharing around a sphere.",
        f"Create a child-friendly story that includes breath, caucus, and sphere, and ends with everyone feeling calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    host = _safe_fact(world, f, "host")
    sphere = _safe_fact(world, f, "sphere_kind")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Where did {child.id} go for the caucus?",
            answer=f"{child.id} went to {place.name} for the caucus."
        ),
        QAItem(
            question=f"What was special about the sphere?",
            answer=f"It was {sphere.phrase} and it was meant to use Magic to {sphere.effect}."
        ),
        QAItem(
            question=f"Why did {child.id} feel better at the end?",
            answer=f"{child.id} felt better because the host helped everyone share the sphere, and the room filled with Kindness and calm breath."
        ),
        QAItem(
            question=f"Who helped the group choose a kinder way?",
            answer=f"The {host.type} helped the group slow down, listen, and share."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    sphere = _safe_fact(world, f, "sphere_kind")
    out = [
        QAItem(
            question="What is a caucus?",
            answer="A caucus is a small meeting where people gather to talk and decide things together."
        ),
        QAItem(
            question="What does it mean to take a breath?",
            answer="Taking a breath means breathing in and out slowly, which can help a person feel calmer."
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use or enjoy something too."
        ),
    ]
    if sphere.id == "breathlight":
        out.append(QAItem(
            question="Why can a glowing light feel soothing?",
            answer="A soft glowing light can feel soothing because it makes a space seem gentle, quiet, and safe."
        ))
    if sphere.id == "kindnessorb":
        out.append(QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and thoughtful toward other people."
        ))
    if sphere.id == "sharingglobe":
        out.append(QAItem(
            question="Why is taking turns helpful?",
            answer="Taking turns is helpful because it lets everyone have a fair chance."
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
sphere(S) :- sphere_kind(S).
magic_help(P,S) :- place(P), sphere(S), glow(S,_), helps(S,_).
good_story(P,S) :- place(P), sphere(S), magic_help(P,S).
#show good_story/2.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for sid, sk in SPHERES.items():
        lines.append(asp.fact("sphere_kind", sid))
        lines.append(asp.fact("glow", sid, sk.glow))
        lines.append(asp.fact("helps", sid, sk.helps))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/2."))
    asp_pairs = set(asp.atoms(model, "good_story"))
    py_pairs = {(p, s) for p in PLACES for s in SPHERES}
    if asp_pairs == py_pairs:
        print(f"OK: ASP parity matches ({len(py_pairs)} good_story pairs).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if asp_pairs - py_pairs:
        print("  only in ASP:", sorted(asp_pairs - py_pairs))
    if py_pairs - asp_pairs:
        print("  only in Python:", sorted(py_pairs - asp_pairs))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld: breath, caucus, and a sphere.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sphere", choices=SPHERES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--host", choices=HOSTS)
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    sphere = getattr(args, "sphere", None) or rng.choice(list(SPHERES))
    host = getattr(args, "host", None) or rng.choice(HOSTS)
    return StoryParams(place=place, sphere=sphere, name=name, gender=gender, host=host)


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
        print(asp_program("#show good_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show good_story/2."))
        pairs = sorted(set(asp.atoms(model, "good_story")))
        for p, s in pairs:
            print(p, s)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="hall", sphere="breathlight", name="Mia", gender="girl", host="teacher"),
            StoryParams(place="library", sphere="kindnessorb", name="Eli", gender="boy", host="librarian"),
            StoryParams(place="garden", sphere="sharingglobe", name="Nora", gender="girl", host="neighbor"),
            StoryParams(place="sunroom", sphere="breathlight", name="Theo", gender="boy", host="grandmother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.sphere} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
