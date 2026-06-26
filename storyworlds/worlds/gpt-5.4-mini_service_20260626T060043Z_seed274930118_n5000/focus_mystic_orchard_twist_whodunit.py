#!/usr/bin/env python3
"""
focus_mystic_orchard_twist_whodunit.py
======================================

A small whodunit-style storyworld set in a mystic orchard.

Premise:
- A child or helper notices something is wrong in the orchard.
- Everyone has a clear reason to be there.
- A careful focus on clues reveals the twist: the "missing" thing was not stolen,
  it was hidden by a practical mistake or misunderstood by one character.
- The ending proves the change in state with a concrete image.

This script is self-contained and uses the shared Storyweavers result containers.
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
    keeper: Optional[str] = None
    hidden: bool = False
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Setting:
    place: str = "the orchard"
    features: set[str] = field(default_factory=lambda: {"orchard", "mystic"})
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
class Clue:
    id: str
    label: str
    detail: str
    location: str
    reveals: str
    false_alarm: bool = False
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
class Suspect:
    id: str
    type: str
    label: str
    reason: str
    alibi_detail: str
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
class StoryParams:
    clue: str
    suspect: str
    place: str = "orchard"
    name: str = "Mina"
    gender: str = "girl"
    helper: str = "grandmother"
    seed: Optional[int] = None
    trait: str = ""
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
        self.facts: dict = {}
        self.fired: set[str] = set()

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


SETTING = Setting()

CLUES = {
    "ladder": Clue(
        id="ladder",
        label="a small ladder",
        detail="leaning near the plum tree",
        location="by the plum tree",
        reveals="someone had only used it to reach a high branch",
    ),
    "basket": Clue(
        id="basket",
        label="a berry basket",
        detail="under the pear leaves",
        location="under the pear leaves",
        reveals="the basket had been tucked there to keep it out of the dew",
    ),
    "ribbon": Clue(
        id="ribbon",
        label="a blue ribbon",
        detail="caught on a low twig",
        location="caught on a low twig",
        reveals="it had snagged during a hurried walk and was not taken at all",
    ),
    "key": Clue(
        id="key",
        label="a brass key",
        detail="glinting in the moss",
        location="in the moss",
        reveals="it had slipped from a pocket and landed in the grass",
    ),
}

SUSPECTS = {
    "gardener": Suspect(
        id="gardener",
        type="man",
        label="the gardener",
        reason="he had come early to check the trees",
        alibi_detail="he was pruning the east branch when the clue went missing",
    ),
    "aunt": Suspect(
        id="aunt",
        type="woman",
        label="the aunt",
        reason="she carried jars for jam and always knew the orchard paths",
        alibi_detail="she was stamping labels on jelly jars at the table",
    ),
    "boy": Suspect(
        id="boy",
        type="boy",
        label="the boy",
        reason="he liked climbing trees and scouting the best apples",
        alibi_detail="he was feeding cider scraps to the hens near the gate",
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Tess", "Ivy"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Owen"]
HELPERS = ["grandmother", "grandfather", "aunt", "uncle"]
TRAITS = ["careful", "curious", "focused", "brave", "quiet"]


def valid_combos() -> list[tuple[str, str]]:
    return [(c, s) for c in CLUES for s in SUSPECTS]


ASP_RULES = r"""
% A clue is suspicious if it is in the orchard and someone looks involved.
suspicious(C) :- clue(C), in_orchard(C).

% A twist happens when careful focus shows the clue is innocent and the suspect
% has a mundane alibi.
twist(C,S) :- suspicious(C), suspect(S), innocent(C), alibi(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "orchard"))
    lines.append(asp.fact("feature", "mystic"))
    lines.append(asp.fact("feature", "orchard"))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("in_orchard", cid))
        lines.append(asp.fact("reveals", cid, clue.reveals))
    for sid, sus in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("role", sid, sus.label))
        lines.append(asp.fact("alibi", sid))
    lines.append(asp.fact("innocent", "basket"))
    lines.append(asp.fact("innocent", "ladder"))
    lines.append(asp.fact("innocent", "ribbon"))
    lines.append(asp.fact("innocent", "key"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show twist/2."))
    got = sorted(set(asp.atoms(model, "twist")))
    want = sorted(set((c, s) for c, s in valid_combos()))
    if got == want:
        print(f"OK: clingo gate matches valid_combos() ({len(got)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  clingo:", got)
    print("  python:", want)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Whodunit-style orchard storyworld with a mystic twist."
    )
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--place", default="orchard")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    clue = getattr(args, "clue", None) or rng.choice(sorted(CLUES))
    suspect = getattr(args, "suspect", None) or rng.choice(sorted(SUSPECTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(clue=clue, suspect=suspect, place=getattr(args, "place", None), name=name, gender=gender, helper=helper, trait=trait)


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    suspect = _safe_lookup(SUSPECTS, params.suspect)
    clue = _safe_lookup(CLUES, params.clue)

    world.facts.update(hero=hero, helper=helper, suspect=suspect, clue=clue, params=params)

    world.say(
        f"{params.name} was {params.trait} and liked to keep a sharp focus on little details in the mystic orchard."
    )
    world.say(
        f"One evening, {params.name} and {helper.label} found that {clue.label} was gone from {clue.location}."
    )

    world.para()
    world.say(
        f"The orchard looked quiet, but it did not feel simple. Pale moonlight silvered the apple leaves, and every path seemed to hide a clue."
    )
    world.say(
        f"{params.name} asked who might have taken it, and {helper.label} named a suspect: {suspect.label}, because {suspect.reason}."
    )
    world.say(
        f"{suspect.label.capitalize()} did look suspicious at first, especially with {suspect.alibi_detail}."
    )

    world.para()
    world.say(
        f"{params.name} did not guess. {hero.pronoun().capitalize()} walked slowly, looked closely, and followed the tiny signs."
    )
    world.say(
        f"At last, {hero.pronoun('subject')} spotted {clue.detail}; that was the twist."
    )
    world.say(
        f"{clue.reveals.capitalize()}, so nobody had stolen it at all."
    )

    world.para()
    world.say(
        f"{params.name} smiled and pointed out the truth. {helper.label.capitalize()} laughed softly, and {suspect.label} turned out to be innocent."
    )
    world.say(
        f"In the end, the orchard felt calm again, with {clue.label} back in plain sight and the mystic trees glowing over the solved mystery."
    )

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = _safe_fact(world, f, "params")
    clue: Clue = _safe_fact(world, f, "clue")
    suspect: Suspect = _safe_fact(world, f, "suspect")
    return [
        f'Write a short whodunit for a child set in a mystic orchard featuring the word "focus" and the clue "{clue.label}".',
        f"Tell a gentle mystery where {params.name} uses careful focus in the orchard to learn why {suspect.label} seemed suspicious.",
        f'Write a story with a twist in an orchard mystery that ends by explaining why "{clue.label}" was not stolen.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = _safe_fact(world, f, "params")
    clue: Clue = _safe_fact(world, f, "clue")
    suspect: Suspect = _safe_fact(world, f, "suspect")
    return [
        QAItem(
            question=f"Where did {params.name} look for clues?",
            answer="They looked in the mystic orchard, where the apple trees and paths made the mystery feel quiet and strange.",
        ),
        QAItem(
            question=f"What clue made everyone wonder what happened?",
            answer=f"The clue was {clue.label}, and it seemed important because it was missing from {clue.location}.",
        ),
        QAItem(
            question=f"Who seemed suspicious at first?",
            answer=f"{suspect.label.capitalize()} seemed suspicious at first, but that was only because of the clue and the alibi detail.",
        ),
        QAItem(
            question=f"What did {params.name} use to solve the mystery?",
            answer=f"{params.name} used careful focus and looked closely at the orchard instead of guessing too soon.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {clue.label} had not been stolen; it had simply been left in a hidden place by mistake.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an orchard?",
            answer="An orchard is a place where fruit trees grow, like apple trees or pear trees.",
        ),
        QAItem(
            question="What does it mean to focus?",
            answer="To focus means to pay close attention to one thing and notice small details.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story or situation where someone must find out what really happened.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the listener thought was true.",
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
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.keeper:
            bits.append(f"keeper={e.keeper}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(clue="ladder", suspect="gardener", name="Mina", gender="girl", helper="grandmother", trait="focused"),
    StoryParams(clue="basket", suspect="aunt", name="Nora", gender="girl", helper="aunt", trait="curious"),
    StoryParams(clue="ribbon", suspect="boy", name="Eli", gender="boy", helper="grandfather", trait="careful"),
    StoryParams(clue="key", suspect="gardener", name="Tess", gender="girl", helper="uncle", trait="quiet"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show twist/2."))
    return sorted(set(asp.atoms(model, "twist")))


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
        print(asp_program("#show twist/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible twist combos:\n")
        for c, s in combos:
            print(f"  clue={c:8} suspect={s}")
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
            header = f"### {p.name}: {p.clue} / {p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
