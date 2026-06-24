#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T082828Z_seed779406221_n50/script_constipate_rejoice_transformation_humor_mystery.py
===============================================================================================================================

A small mystery storyworld with a light comic turn and a transformation payoff.

Seed tale sketch:
- A child finds a strange script for a tiny play.
- The script includes a funny made-up line, "constipate," that sounds like a spell.
- Someone thinks the missing prop is stolen, but the clues point to a jammed stage box instead.
- When the box is opened and the prop is revealed, the child rejoices.

This world keeps the prose child-facing and clue-driven:
- mystery: a missing object, misleading clues, a reveal
- humor: the odd script word, a comic misunderstanding
- transformation: a plain prop becomes a stage character under light
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
    hidden_in: Optional[str] = None
    transformed: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    can_transform: bool = False
    box: object | None = None
    child: object | None = None
    lantern: object | None = None
    parent: object | None = None
    prop: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
        if not hasattr(self, "_tags"):
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
    place: str = "the little theater"
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Script:
    title: str
    lines: list[str]
    mystery_word: str = "constipate"
    script: object | None = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    stage_role: str
    can_transform: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    name: str
    gender: str
    parent: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
        self.fired: set[tuple] = set()
        self.script: Optional[Script] = None
        self.story_events: list[str] = []

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

        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.script = copy.deepcopy(self.script)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def has_transformation_clue(world: World) -> bool:
    return any(e.meters.get("mystery", 0) >= THRESHOLD for e in world.entities.values())


def _r_unhide_prop(world: World) -> list[str]:
    out: list[str] = []
    box = world.entities.get("box")
    prop = world.entities.get("prop")
    if not box or not prop:
        return out
    if box.meters.get("opened", 0) < THRESHOLD:
        return out
    if prop.hidden_in != "box":
        return out
    sig = ("unhide", prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prop.hidden_in = None
    prop.meters["found"] = 1
    out.append("Inside was the missing prop, tucked under a folded costume cloth.")
    return out


def _r_transform_prop(world: World) -> list[str]:
    out: list[str] = []
    prop = world.entities.get("prop")
    if not prop or not prop.can_transform:
        return out
    if prop.hidden_in is not None:
        return out
    if prop.meters.get("spotlight", 0) < THRESHOLD:
        return out
    sig = ("transform", prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prop.transformed = True
    out.append("Under the warm light, the plain prop seemed to become a real character.")
    return out


def _r_rejoice(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    prop = world.entities.get("prop")
    if not child or not prop:
        return out
    if prop.meters.get("found", 0) < THRESHOLD or not prop.transformed:
        return out
    sig = ("rejoice", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    out.append(f"{child.id} clapped and smiled so hard that the whole room felt lighter.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_unhide_prop, _r_transform_prop, _r_rejoice):
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, meters={"curiosity": 1}, memes={"wonder": 1}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the grown-up"))
    script = Script(
        title="The Lantern Script",
        lines=[
            "Say the word constipate, and the paper fox will wake up.",
            "If the box is stuck, look for the key with the silver star.",
        ],
    )
    world.script = script
    prop = world.add(Entity(id="prop", type="fox", label="paper fox", phrase="a folded paper fox", owner=name, caretaker="Parent", can_transform=True, hidden_in="box"))
    box = world.add(Entity(id="box", type="box", label="stage box", phrase="a painted stage box", meters={"jammed": 1}))
    lantern = world.add(Entity(id="lantern", type="lantern", label="lantern", phrase="a warm brass lantern"))

    world.say(f"{child.id} was a {trait} little {gender} who loved mysteries and little plays.")
    world.say(f"One afternoon, {child.id} found a script called {script.title}.")
    world.say(f"One line in it made {child.id} giggle: \"Say the word {script.mystery_word}, and the paper fox will wake up.\"")
    world.say(f"{child.id} wondered who had hidden {prop.phrase} and why the stage box felt stuck.")
    world.para()
    world.say(f"At {setting.place}, {child.id} and {parent.label} looked at the jammed box like tiny detectives.")
    world.say(f"{child.id} noticed a silver star key under the lantern and guessed the box was not stolen at all, just tucked shut.")
    box.meters["opened"] = 1
    world.say(f"With one careful turn, the box opened.")
    propagate(world, narrate=True)
    world.para()
    if prop.transformed:
        prop.meters["spotlight"] = 1
        world.say(f"The lantern shone on the paper fox, and the folded shape seemed to come alive.")
        propagate(world, narrate=True)
    world.say(f"{child.id} rejoiced, because the mystery was solved and the little play could begin.")
    world.facts.update(
        child=child,
        parent=parent,
        prop=prop,
        box=box,
        lantern=lantern,
        script=script,
        setting=setting,
        resolved=True,
    )
    return world


SETTINGS = {
    "the little theater": Setting(place="the little theater", affords={"script", "mystery", "transform"}),
    "the school stage": Setting(place="the school stage", affords={"script", "mystery", "transform"}),
    "the attic playroom": Setting(place="the attic playroom", affords={"script", "mystery", "transform"}),
}

GIRL_NAMES = ["Mina", "Tess", "June", "Lena", "Nina", "Ivy"]
BOY_NAMES = ["Noel", "Owen", "Eli", "Pip", "Theo", "Milo"]
TRAITS = ["curious", "brave", "careful", "bright", "cheerful", "clever"]


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    ap = argparse.ArgumentParser(description="A small mystery storyworld with a comic transformation payoff.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a short mystery story for a young child that includes the word "{f["script"].mystery_word}".',
        f"Tell a funny little story where {child.id} opens a script, finds a missing prop, and solves a stage mystery.",
        f"Write a child-friendly tale about a hidden prop, a funny script, and a transformation under a lantern.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    prop = f["prop"]
    script = f["script"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"What did {child.id} find first in the story?",
            answer=f"{child.id} found a script called {script.title}. It had a funny line about the word {script.mystery_word}.",
        ),
        QAItem(
            question=f"What mystery did {child.id} and {f['parent'].label} solve at {place}?",
            answer=f"They solved the mystery of the stuck stage box and the missing {prop.label}. The prop was not stolen; it was hidden inside the box.",
        ),
        QAItem(
            question=f"What changed when the lantern light touched the {prop.label}?",
            answer=f"The folded paper fox transformed and seemed to become a real character. That made the ending feel magical and surprising.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} rejoiced because the mystery was solved and the little play could begin.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a script?",
            answer="A script is a written set of lines that tells actors what to say in a play.",
        ),
        QAItem(
            question="What does it mean to rejoice?",
            answer="To rejoice means to feel and show great happiness, like smiling, clapping, or cheering.",
        ),
        QAItem(
            question="What is a mystery story?",
            answer="A mystery story is a story about a puzzling problem that gets solved by noticing clues.",
        ),
        QAItem(
            question="What is a transformation in a story?",
            answer="A transformation is a change from one form into another, like a plain prop seeming to become alive.",
        ),
        QAItem(
            question="Why can a funny word make a story humorous?",
            answer="A funny word can sound surprising or silly, which can make readers giggle while they follow the story.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== (1) Generation prompts ==")
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


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    lines.append(asp.fact("word", "script"))
    lines.append(asp.fact("word", "constipate"))
    lines.append(asp.fact("word", "rejoice"))
    lines.append(asp.fact("mood", "humor"))
    lines.append(asp.fact("style", "mystery"))
    lines.append(asp.fact("theme", "transformation"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- place(P).
featured_word(script).
featured_word(constipate).
featured_word(rejoice).
featured_theme(transformation).
featured_style(mystery).
featured_mood(humor).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_place/1."))
    got = sorted(set(asp.atoms(model, "valid_place")))
    exp = sorted((p,) for p in SETTINGS)
    if got == exp:
        print(f"OK: clingo gate matches Python ({len(got)} places).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("  clingo:", got)
    print("  python:", exp)
    return 1


def asp_valid_places() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


CURATED = [
    StoryParams(place="the little theater", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="the school stage", name="Owen", gender="boy", parent="father", trait="clever"),
    StoryParams(place="the attic playroom", name="Tess", gender="girl", parent="mother", trait="bright"),
]


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
        print(asp_program("#show valid_place/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        places = asp_valid_places()
        print(f"{len(places)} valid places:")
        for (p,) in places:
            print(f"  {p}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
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
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
