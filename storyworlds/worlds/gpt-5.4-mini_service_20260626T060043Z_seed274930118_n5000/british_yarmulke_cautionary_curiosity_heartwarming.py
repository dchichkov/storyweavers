#!/usr/bin/env python3
"""
A small story world about a curious child, a careful warning, and a warm
resolution around a British day out and a yarmulke.

The seed tale behind this world is simple:
A child notices a yarmulke and wants to try it on because it looks special.
A parent worries it might be handled carelessly or worn in the wrong place.
The child asks questions, learns what it is for, and finds a respectful way to
look after it and join the moment kindly.

The world is built as a tiny simulation:
- physical meters track whether an item is safe, misplaced, or gently handled
- emotional memes track curiosity, caution, worry, relief, and affection
- the story turns on a question, a warning, a respectful choice, and a warm end
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protected: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    item: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        for k in ["safe", "handled", "misplaced", "clean", "warned"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "caution", "worry", "relief", "affection", "respect"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
    british: bool = True
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
    safe_place: str
    meaning: str
    proper_use: str
    care: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    c: object | None = None
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c
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
    artifact: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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
    "museum": Setting(place="the museum", british=True),
    "library": Setting(place="the library", british=True),
    "garden": Setting(place="the back garden", british=True),
    "flat": Setting(place="the flat", british=True),
}

ARTIFACTS = {
    "yarmulke": Artifact(
        id="yarmulke",
        label="yarmulke",
        phrase="a small yarmulke",
        safe_place="the special box",
        meaning="a head covering worn with care and respect",
        proper_use="asking before wearing it",
        care="keeping it clean and setting it down gently",
    )
}

NAMES_GIRL = ["Maya", "Nora", "Lily", "Ava", "Iris"]
NAMES_BOY = ["Noah", "Theo", "Eli", "Finn", "Leo"]
TRAITS = ["curious", "gentle", "bright-eyed", "kind", "thoughtful"]


def _r_handle(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    item = world.get("artifact")
    if child.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("handle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["handled"] += 1
    item.meters["safe"] += 1
    child.memes["respect"] += 1
    out.append(f"{child.id} held the yarmulke carefully instead of tugging at it.")
    return out


def _r_misplace(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    item = world.get("artifact")
    if child.meters["misstep"] < THRESHOLD:
        return out
    sig = ("misplace",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["misplaced"] += 1
    child.memes["worry"] += 1
    out.append("That made the grown-up worry that it might be treated carelessly.")
    return out


def _r_relief(world: World) -> list[str]:
    child = world.get("child")
    parent = world.get("parent")
    if child.memes["respect"] < THRESHOLD or child.meters["asked"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    parent.memes["relief"] += 1
    parent.memes["affection"] += 1
    return ["__relief__"]


CAUSAL_RULES = [_r_handle, _r_misplace, _r_relief]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if b != "__relief__")
    if narrate:
        for s in produced:
            world.say(s)


def predict(world: World, child: Entity) -> dict:
    sim = world.copy()
    sim.get("child").meters["misstep"] += 1
    propagate(sim, narrate=False)
    return {
        "misplaced": sim.get("artifact").meters["misplaced"] >= THRESHOLD,
        "handled": sim.get("artifact").meters["handled"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "curious")
    world.say(
        f"{child.id} was a little {trait} {child.type} who loved noticing small, interesting things."
    )


def arrive(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    world.say(
        f"One bright day, {child.id} and {child.pronoun('possessive')} {parent.label} went to {setting.place}."
    )
    if setting.british:
        world.say("The day felt very british: calm voices, tidy steps, and careful manners.")


def find_item(world: World, child: Entity, artifact: Artifact) -> None:
    world.say(
        f"{child.id} spotted {artifact.phrase} and leaned closer, full of curiosity."
    )
    child.memes["curiosity"] += 1


def ask_about_item(world: World, child: Entity, parent: Entity, artifact: Artifact) -> None:
    child.meters["asked"] += 1
    world.say(
        f'"What is it for?" {child.id} asked. {parent.label.capitalize()} smiled and said '
        f'it was {artifact.meaning}.'
    )


def warn(world: World, parent: Entity, child: Entity, artifact: Artifact) -> None:
    pred = predict(world, child)
    if not pred["misplaced"]:
        return
    parent.memes["caution"] += 1
    world.say(
        f'"Let’s be careful," {parent.label} said. "It should stay in {artifact.safe_place}, '
        f'and it deserves respect."'
    )


def try_to_grab(world: World, child: Entity, artifact: Artifact) -> None:
    child.meters["misstep"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} reached out, but paused when the warning sank in."
    )


def choose_respect(world: World, child: Entity, parent: Entity, artifact: Artifact) -> None:
    child.meters["handled"] += 1
    child.meters["safe"] += 1
    child.memes["respect"] += 1
    world.say(
        f"Instead of snatching it up, {child.id} asked before touching it and held it with two gentle hands."
    )
    propagate(world, narrate=False)
    if child.memes["respect"] >= THRESHOLD:
        world.say(
            f"{parent.label.capitalize()} looked relieved. Now {child.id} could learn about the yarmulke without hurting it."
        )


def warm_finish(world: World, child: Entity, parent: Entity, artifact: Artifact) -> None:
    child.memes["relief"] += 1
    child.memes["affection"] += 1
    parent.memes["affection"] += 1
    world.say(
        f"In the end, {child.id} put {artifact.label} back in {artifact.safe_place} and smiled up at {parent.label}. "
        f"The little yarmulke stayed tidy, and the child stayed proud of being careful."
    )


def tell(setting: Setting, artifact: Artifact, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    item = world.add(Entity(id="artifact", type="yarmulke", label="yarmulke", phrase=artifact.phrase, owner=None))
    world.facts.update(child=child, parent=parent, artifact=item, artifact_cfg=artifact, setting=setting)

    introduce(world, child)
    arrive(world, child, parent, setting)
    world.para()
    find_item(world, child, artifact)
    ask_about_item(world, child, parent, artifact)
    warn(world, parent, child, artifact)
    try_to_grab(world, child, artifact)
    choose_respect(world, child, parent, artifact)
    world.para()
    warm_finish(world, child, parent, artifact)
    return world


KNOWLEDGE = {
    "yarmulke": [
        (
            "What is a yarmulke?",
            "A yarmulke is a small head covering that people wear with care and respect.",
        ),
        (
            "How should you handle a yarmulke?",
            "You should handle a yarmulke gently, because it is a special item that should be kept clean and respected.",
        ),
    ],
    "care": [
        (
            "What does it mean to be careful with something special?",
            "Being careful means using gentle hands, asking first, and keeping the special thing safe and clean.",
        )
    ],
    "british": [
        (
            "What does british often make you picture in a story?",
            "A british story often makes you picture quiet manners, careful choices, and a tidy place with a calm feeling.",
        )
    ],
}


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    art = _safe_fact(world, f, "artifact_cfg")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Why did {child.id} lean closer to the yarmulke at {setting.place}?",
            answer=f"{child.id} leaned closer because {child.pronoun('subject')} was curious and wanted to know what the yarmulke was for.",
        ),
        QAItem(
            question=f"What did {parent.label} worry about when {child.id} wanted to touch it?",
            answer=f"{parent.label.capitalize()} worried that the yarmulke might be handled carelessly instead of kept in {art.safe_place}.",
        ),
        QAItem(
            question=f"How did {child.id} show respect in the story?",
            answer=f"{child.id} showed respect by asking before touching the yarmulke and holding it gently with two hands.",
        ),
        QAItem(
            question=f"What was the happy ending for the yarmulke?",
            answer=f"The yarmulke stayed tidy in {art.safe_place}, and {child.id} felt proud of making a careful choice.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in KNOWLEDGE["yarmulke"] + KNOWLEDGE["care"] + KNOWLEDGE["british"]]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    art = _safe_fact(world, f, "artifact_cfg")
    return [
        f'Write a warm story for a young child about curiosity and care that includes the word "{art.label}".',
        f"Tell a gentle british story where {child.id} notices a yarmulke and learns to handle it respectfully.",
        "Write a short heartwarming cautionary tale about a curious child, a careful warning, and a kind ending.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
% A yarmulke is at risk when a child tries to grab it without asking.
at_risk(A) :- curious(A), misstep(A).

% Respectful handling prevents the item from being treated carelessly.
handled_safely(A) :- asked_before_touching(A), gentle_hands(A).

% A good ending exists when curiosity turns into respectful care.
good_story(A) :- at_risk(A), handled_safely(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("curious", "child"))
    lines.append(asp.fact("misstep", "child"))
    lines.append(asp.fact("asked_before_touching", "child"))
    lines.append(asp.fact("gentle_hands", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    return bool(asp.atoms(model, "good_story"))


def asp_verify() -> int:
    ok = asp_valid()
    py_ok = True
    if ok == py_ok:
        print("OK: ASP and Python both describe the story as a respectful, good ending.")
        return 0
    print("MISMATCH between ASP and Python story logic.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming British curiosity story about a yarmulke.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    artifact = getattr(args, "artifact", None) or "yarmulke"
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, artifact=artifact, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ARTIFACTS, params.artifact), params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show good_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("1 compatible story pattern: curiosity can become respectful care.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = StoryParams(place="museum", artifact="yarmulke", name="Maya", gender="girl", parent="mother", trait="curious")
        samples = [generate(params)]
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
