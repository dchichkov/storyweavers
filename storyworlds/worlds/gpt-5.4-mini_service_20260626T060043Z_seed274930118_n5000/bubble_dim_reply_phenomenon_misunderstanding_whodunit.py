#!/usr/bin/env python3
"""
A compact storyworld for a child-friendly whodunit about a misunderstanding.

Premise:
- A small cast is gathered in one place.
- A strange phenomenon makes a clue seem to vanish or change.
- Someone gives the wrong reply, causing a misunderstanding.
- The detective-like helper follows the evidence and clears it up.

The seed words are embedded as world vocabulary:
- bubble-dim
- reply
- phenomenon

The simulated state tracks both physical meters and emotional memes so the
narration is driven by world changes rather than by a frozen template.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    helper: object | None = None
    hero: object | None = None
    suspect: object | None = None
    witness: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
    place: str = "the library"
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
class Mystery:
    id: str
    phenomenon: str
    oddity: str
    cause: str
    clue: str
    reveal: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    mystery: Optional[Mystery] = None

    clone: object | None = None
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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.mystery = copy.deepcopy(self.mystery)
        return clone
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


def mood_line(world: World, helper: Entity) -> str:
    if helper.memes.get("curiosity", 0) >= THRESHOLD:
        return f"{helper.id} kept looking at the clue with bright, curious eyes."
    return f"{helper.id} looked at the clue carefully and stayed very still."


def explain_phenomenon(mystery: Mystery) -> str:
    return (
        f"The strange {mystery.phenomenon} was only a {mystery.oddity}; "
        f"the real cause was {mystery.cause}."
    )


def build_scene(world: World, hero: Entity, helper: Entity, witness: Entity, clue: Entity, mystery: Mystery) -> None:
    world.say(
        f"At {world.setting.place}, {hero.id} noticed something odd: "
        f"{mystery.phenomenon}."
    )
    world.say(
        f"Near the clue, {helper.id} leaned in and said, "
        f"'{mystery.clue}'"
    )
    world.say(mood_line(world, helper))
    witness.memes["unease"] += 1
    clue.meters["seen"] += 1


def suspect_reply(world: World, suspect: Entity, helper: Entity, mystery: Mystery) -> None:
    helper.memes["misunderstanding"] += 1
    suspect.memes["worry"] += 1
    world.say(
        f"{suspect.id} gave a quick reply that sounded wrong. "
        f"'{mystery.reveal}'"
    )
    world.say(
        f"That reply made {helper.id} think the clue meant something else."
    )


def detective_turn(world: World, helper: Entity, clue: Entity, mystery: Mystery) -> None:
    helper.memes["curiosity"] += 1
    clue.meters["checked"] += 1
    world.say(
        f"{helper.id} did not rush. Instead, {helper.pronoun()} checked the clue again."
    )
    world.say(
        f"The clue was still there, and the odd {mystery.phenomenon} began to make sense."
    )


def reveal_and_fix(world: World, hero: Entity, helper: Entity, suspect: Entity, mystery: Mystery) -> None:
    helper.memes["misunderstanding"] = 0.0
    suspect.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    world.say(
        f"At last, {helper.id} pointed to the real pattern: {explain_phenomenon(mystery)}"
    )
    world.say(
        f"{suspect.id} let out a small sigh and gave the honest reply at once."
    )
    world.say(
        f"{hero.id} smiled, because the puzzle was solved and nobody had meant any harm."
    )


def tell(world: World, mystery: Mystery, hero_name: str = "Mina", hero_type: str = "girl") -> World:
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Detective", kind="character", type="boy"))
    witness = world.add(Entity(id="Pip", kind="character", type="girl"))
    suspect = world.add(Entity(id="Rafi", kind="character", type="boy"))
    clue = world.add(Entity(id="clue", label="the clue", kind="thing", type="thing"))
    world.mystery = mystery

    hero.memes["curiosity"] = 1
    helper.memes["curiosity"] = 1
    witness.memes["unease"] = 0
    suspect.memes["worry"] = 0

    world.say(
        f"{hero.id} was in {world.setting.place}, where everyone was talking about a small mystery."
    )
    world.say(
        f"They had heard of a {mystery.phenomenon}, but nobody knew why it happened."
    )
    world.say(
        f"{hero.id} liked mysteries, especially when a clue was hiding in plain sight."
    )

    world.para()
    build_scene(world, hero, helper, witness, clue, mystery)
    suspect_reply(world, suspect, helper, mystery)

    world.para()
    detective_turn(world, helper, clue, mystery)
    reveal_and_fix(world, hero, helper, suspect, mystery)

    world.facts.update(
        hero=hero,
        helper=helper,
        witness=witness,
        suspect=suspect,
        clue=clue,
        mystery=mystery,
    )
    return world


SETTINGS = {
    "library": Setting(place="the library", affords={"investigate"}),
    "museum": Setting(place="the museum", affords={"investigate"}),
    "greenhouse": Setting(place="the greenhouse", affords={"investigate"}),
    "attic": Setting(place="the attic", affords={"investigate"}),
}

MYSTERIES = {
    "bubble-dim": Mystery(
        id="bubble-dim",
        phenomenon="bubble-dim",
        oddity="the bubble light seemed to dim and vanish",
        cause="a mirror in the window bouncing the light away",
        clue="The bubbles did not disappear; they only looked dim in the glass.",
        reveal="I thought you said the bubbles were gone!",
        tags={"bubble", "light", "misunderstanding"},
    ),
    "reply": Mystery(
        id="reply",
        phenomenon="reply",
        oddity="a reply came from the next room and sounded like a secret",
        cause="the echo in the hallway",
        clue="The reply was only bouncing back from the wall.",
        reveal="I was answering you, not hiding anything.",
        tags={"echo", "voice", "misunderstanding"},
    ),
    "phenomenon": Mystery(
        id="phenomenon",
        phenomenon="phenomenon",
        oddity="a curious phenomenon made the room seem too quiet",
        cause="everyone had stopped to listen at the same time",
        clue="The quiet came from all the listening, not from a missing sound.",
        reveal="It looked strange, but nothing was wrong.",
        tags={"quiet", "listening", "misunderstanding"},
    ),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Tess", "Ruby", "Ivy", "Ada"]
BOY_NAMES = ["Owen", "Theo", "Jules", "Milo", "Ezra", "Noah", "Finn"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mystery_id) for place in SETTINGS for mystery_id in MYSTERIES]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a short whodunit for a small child that includes the word "{mystery.id}".',
        f"Tell a gentle mystery story about {hero.id} in {world.setting.place} when a strange {mystery.phenomenon} causes a misunderstanding.",
        f'Write a simple detective story where a wrong reply leads to a clue being misunderstood, and end with the truth explained.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    suspect = _safe_fact(world, f, "suspect")
    mystery = _safe_fact(world, f, "mystery")
    place = world.setting.place
    return [
        QAItem(
            question=f"Where did {hero.id} notice the mystery?",
            answer=f"{hero.id} noticed the mystery at {place}, where the strange {mystery.phenomenon} first seemed confusing.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look at the clue again?",
            answer=f"{helper.id} helped by checking the clue carefully instead of believing the first wrong idea.",
        ),
        QAItem(
            question=f"Why did {suspect.id}'s reply cause trouble?",
            answer=f"{suspect.id}'s reply caused trouble because it made the clue sound like one thing when it really meant another, so everyone misunderstood it for a moment.",
        ),
        QAItem(
            question=f"What solved the misunderstanding in the end?",
            answer=f"The misunderstanding was solved when {helper.id} checked the clue again and explained that the strange {mystery.phenomenon} had an ordinary cause.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    mystery = _safe_fact(world, world.facts, "mystery")
    out = [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or sees something the wrong way and thinks it means something else.",
        )
    ]
    if "bubble" in mystery.tags:
        out.append(QAItem(
            question="What is a bubble?",
            answer="A bubble is a little ball of air inside water or soap foam.",
        ))
    if "echo" in mystery.tags:
        out.append(QAItem(
            question="What is an echo?",
            answer="An echo is a sound that bounces off a wall or cliff and comes back to your ears.",
        ))
    if "quiet" in mystery.tags:
        out.append(QAItem(
            question="Why can a room seem quiet when people are listening?",
            answer="A room can seem quiet when people are listening because nobody is speaking, even though everyone is paying attention.",
        ))
    return out


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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    if world.mystery:
        lines.append(f"  mystery: {world.mystery.id}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is interesting when the phenomenon is present.
interesting(M) :- mystery(M).

% A misunderstanding happens if a reply is heard but interpreted wrongly.
misunderstanding(M) :- reply(M), wrong_interpretation(M).

% The whodunit is resolved when the helper checks the clue and the cause is found.
resolved(M) :- checked(M), cause_found(M).

% A story is valid when it has a place, a mystery, and a possible resolution.
valid_story(P, M) :- place(P), mystery(M), interesting(M), resolved(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("phenomenon", mid, m.phenomenon))
        for tag in sorted(m.tags):
            lines.append(asp.fact("tag", mid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child-friendly whodunit about a misunderstanding."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = tell(world, mystery, params.name, params.gender)
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
    StoryParams(place="library", mystery="bubble-dim", name="Mina", gender="girl"),
    StoryParams(place="museum", mystery="reply", name="Owen", gender="boy"),
    StoryParams(place="attic", mystery="phenomenon", name="Lia", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
        for combo in combos:
            print("  ", combo)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
