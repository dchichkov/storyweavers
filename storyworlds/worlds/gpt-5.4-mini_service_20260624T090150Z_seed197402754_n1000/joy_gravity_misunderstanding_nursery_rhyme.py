#!/usr/bin/env python3
"""
joy_gravity_misunderstanding_nursery_rhyme.py
============================================

A tiny storyworld in a nursery-rhyme style: a child, a curious question,
and a misunderstanding about gravity that turns into a gentle lesson.

Premise:
- A little child loves a shiny kite or feather or ball.
- They hear "gravity" and misunderstand it as a grumpy thing.
- The child worries that gravity will "take" the joy away.
- A kind helper shows that gravity is just why things come down, which makes
  the rhyme-world feel safe and steady again.

This world models:
- physical meters: height, weight, bounce, fall, sway
- emotional memes: joy, worry, wonder, relief, misunderstanding

The story is driven by world state:
- the child starts joyful and curious
- a misunderstanding raises worry
- a small experiment with a dropped object demonstrates gravity
- the ending image proves the child learned the truth and feels joy again
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper_ent: object | None = None
    toy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the little nursery"
    indoors: bool = True
    window: bool = True
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class Toy:
    id: str
    label: str
    phrase: str
    type: str
    drop_line: str
    land_line: str
    sounds: str
    weight: str
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
class StoryParams:
    toy: str
    name: str
    gender: str
    helper: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace_notes: list[str] = []

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting(place="the little nursery", indoors=True, window=True, affords={"drop", "toss", "bounce"})

TOYS = {
    "ball": Toy(
        id="ball",
        label="ball",
        phrase="a round red ball",
        type="ball",
        drop_line="boing",
        land_line="bop",
        sounds="boing-boing",
        weight="light",
        tags={"gravity", "bounce", "joy"},
    ),
    "feather": Toy(
        id="feather",
        label="feather",
        phrase="a soft white feather",
        type="feather",
        drop_line="swish",
        land_line="floaty",
        sounds="swish-swish",
        weight="very light",
        tags={"gravity", "float", "joy"},
    ),
    "apple": Toy(
        id="apple",
        label="apple",
        phrase="a shiny green apple",
        type="apple",
        drop_line="plunk",
        land_line="thud",
        sounds="plink-plunk",
        weight="small and firm",
        tags={"gravity", "fruit"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "June", "Elsie"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Owen", "Sam", "Ira"]
TRAITS = ["curious", "cheerful", "gentle", "sprightly", "bright"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
toy_has_tag(T, Tag) :- toy(T), tag(T, Tag).
child_toy(T) :- loves_toy(T).

gravity_misunderstanding(T) :- toy_has_tag(T, gravity), hears_about(gravity), not knows_gravity.
need_explain(T) :- gravity_misunderstanding(T).

drop_happens(T) :- toy(T), afford(drop).
falling(T) :- drop_happens(T), toy_has_tag(T, gravity).
resolves(T) :- falling(T), learns(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "nursery"))
    if SETTING.indoors:
        lines.append(asp.fact("indoors", "nursery"))
    if SETTING.window:
        lines.append(asp.fact("window", "nursery"))
    for t in TOYS.values():
        lines.append(asp.fact("toy", t.id))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", t.id, tag))
    lines.append(asp.fact("afford", "drop"))
    lines.append(asp.fact("afford", "toss"))
    lines.append(asp.fact("afford", "bounce"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show toy_has_tag/2.\n#show gravity_misunderstanding/1.\n#show falling/1.\n#show resolves/1."))
    # Simple parity gate: ensure gravity-tagged toys exist and at least one can fall.
    tags = set(asp.atoms(model, "toy_has_tag"))
    if ("ball", "gravity") not in tags or ("feather", "gravity") not in tags:
        print("ASP mismatch: expected gravity-tagged toys.")
        return 1
    if not asp.atoms(model, "gravity_misunderstanding"):
        print("ASP mismatch: expected a gravity misunderstanding.")
        return 1
    print("OK: ASP twin is internally consistent.")
    return 0


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _drop(world: World, child: Entity, toy: Entity, narrate: bool = True) -> None:
    if "drop" not in world.setting.affords:
        pass
    child.meters["reach"] = 0.5
    toy.meters["height"] = 0.0
    child.memes["misunderstanding"] += 1
    child.memes["worry"] += 1
    world.facts["gravity_heard"] = True
    world.facts["toy_falling"] = True
    if narrate:
        world.say(f"{child.id} let {toy.it()} go, and {toy.drop_line}—down it came.")


def _explain(world: World, helper: Entity, child: Entity, toy: Entity) -> None:
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    child.memes["wonder"] += 1
    child.memes["understanding"] += 1
    child.memes["misunderstanding"] = 0.0
    world.facts["understood"] = True
    world.say(
        f"{helper.id} smiled and said, “Gravity is not a grumpy thing; it is the gentle pull that helps {toy.label} come down.”"
    )
    world.say(
        f"{child.id} nodded, and the little room felt bright again."
    )


def _bounce(world: World, child: Entity, toy: Entity) -> None:
    child.memes["joy"] += 1
    toy.meters["bounce"] = toy.meters.get("bounce", 0.0) + 1.0
    toy.meters["height"] = 0.3
    world.say(f"{toy.label} gave a tiny bounce, and {toy.sounds} went the rhyme of the play.")


def tell(name: str, gender: str, helper: str, trait: str, toy_cfg: Toy) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id=name, kind="character", type=gender, label=name,
        meters={"height": 1.0},
        memes={"joy": 2.0, "worry": 0.0, "wonder": 0.0, "misunderstanding": 0.0, "understanding": 0.0},
    ))
    helper_ent = world.add(Entity(
        id=helper, kind="character", type="mother" if helper == "Mom" else "father", label=helper,
        memes={"calm": 1.0},
    ))
    toy = world.add(Entity(
        id=toy_cfg.id, kind="thing", type=toy_cfg.type, label=toy_cfg.label, phrase=toy_cfg.phrase,
        owner=child.id, meters={"height": 1.0, "bounce": 0.0}, memes={"held": 1.0},
    ))

    world.say(f"In the little nursery lived {child.id}, a {trait} little {gender}.")
    world.say(f"{child.id} loved {toy.phrase}, because it felt like a tiny song in {child.pronoun('possessive')} hands.")
    world.para()
    world.say(f"One day, {child.id} heard the word gravity and frowned a little.")
    world.say(f"{child.id} thought gravity might grab {toy.it()} away, which made {child.pronoun('possessive')} heart wobble.")
    world.para()
    _drop(world, child, toy)
    world.say(f"It was only a soft fall, and nothing was lost.")
    world.say(f"{helper_ent.id} came near, with a smile as warm as tea.")
    _explain(world, helper_ent, child, toy)
    _bounce(world, child, toy)
    world.para()
    world.say(
        f"Then {child.id} tossed {toy.it()} once more, and knew the truth: gravity helps the world stay near the floor, while joy can still leap and play."
    )
    world.say(f"And so {child.id} laughed, and the little nursery sang its quiet, cozy tune.")
    world.facts.update(child=child, helper=helper_ent, toy=toy, trait=trait)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story for a child named {f["child"].id} about joy, gravity, and a misunderstanding.',
        f"Tell a gentle rhyme where {f['child'].id} worries that gravity is mean, but {f['helper'].id} explains it kindly.",
        f"Write a child-facing story about {f['child'].id}, {f['toy'].label}, and learning what gravity really does.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = _safe_fact(world, world.facts, "child")
    h = _safe_fact(world, world.facts, "helper")
    t = _safe_fact(world, world.facts, "toy")
    return [
        QAItem(
            question=f"What did {c.id} misunderstand about gravity?",
            answer=f"{c.id} thought gravity might snatch {t.it()} away, but gravity was only the pull that made {t.label} come down gently.",
        ),
        QAItem(
            question=f"How did {h.id} help {c.id} feel better?",
            answer=f"{h.id} explained gravity in a soft voice and showed that {t.label} could fall safely, so {c.id}'s worry turned into wonder and joy.",
        ),
        QAItem(
            question=f"What happened after {c.id} learned the truth?",
            answer=f"{c.id} felt happy again, tossed {t.it()} once more, and laughed when {t.label} gave a tiny bounce.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gravity?",
            answer="Gravity is the pull that makes things fall down toward the ground.",
        ),
        QAItem(
            question="Why do things fall when you let go of them?",
            answer="They fall because gravity pulls them down instead of letting them float away.",
        ),
        QAItem(
            question="What is joy?",
            answer="Joy is a bright, happy feeling that makes playtime feel light and warm.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class _Params:
    toy: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None
    p: object | None = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about joy, gravity, and misunderstanding.")
    ap.add_argument("--toy", choices=sorted(TOYS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["Mom", "Dad"])
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> _Params:
    toy = getattr(args, "toy", None) or rng.choice(sorted(TOYS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["Mom", "Dad"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return _Params(toy=toy, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: _Params) -> StorySample:
    world = tell(params.name, params.gender, params.helper, params.trait, _safe_lookup(TOYS, params.toy))
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
        print(asp_program("#show toy_has_tag/2.\n#show gravity_misunderstanding/1.\n#show falling/1.\n#show resolves/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for toy in sorted(TOYS):
            p = _Params(
                toy=toy,
                name=_safe_lookup(GIRL_NAMES, 0) if toy != "apple" else _safe_lookup(BOY_NAMES, 0),
                gender="girl" if toy != "apple" else "boy",
                helper="Mom",
                trait="curious",
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
