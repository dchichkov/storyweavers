#!/usr/bin/env python3
"""
storyworlds/worlds/puppet_coincide_magic_rhyme_repetition_detective_story.py
=============================================================================

A small detective-style storyworld about a puppet, a coincidence, and a case
that can be solved with magic, rhyme, and repetition.

The seed tale imagined for this world:
---
A little puppet named Pip lived in a quiet theater. One evening, the silver
star prop went missing, and everyone said it was a strange coincidence that the
same night a magic lantern began to glow. Pip liked rhymes and repeated clues
out loud like a detective. By following the glow, the rhyme, and the repeated
footprints, Pip found the star hidden behind the curtain and the whole theater
cheered.

World model:
- Physical meters track location, glow, hiddenness, and tidy/messy stage state.
- Emotional memes track curiosity, confidence, worry, surprise, and relief.
- The story is built from causal state changes: missing prop -> investigation ->
  magical clue -> rhyme/repetition -> discovery -> resolution.

The story stays close to a detective story tone while remaining child-facing.
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
    plural: bool = False
    hidden: bool = False
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prop: object | None = None
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
    indoors: bool = True
    details: str = "a velvet curtain, a dusty stage, and a lamp stand"
    affords: set[str] = field(default_factory=lambda: {"search", "glow", "rhyme"})
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
class Mystery:
    id: str
    clue: str
    culprit: str
    hiding_place: str
    magical: bool = True
    rhyme_word: str = "shine"
    repetition_word: str = "again"
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


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    helper: str
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
        self.facts: dict[str, object] = {}
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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "the little theater": Setting(),
    "the puppet house": Setting(place="the puppet house", details="a tiny box stage, red ropes, and bright curtains"),
    "the old stage": Setting(place="the old stage", details="wooden boards, brass lights, and a painted moon"),
}

MYSTERIES = {
    "silver_star": Mystery(
        id="silver_star",
        clue="a silver star prop",
        culprit="the wind from the open window",
        hiding_place="behind the curtain",
        magical=True,
        rhyme_word="shine",
        repetition_word="again",
    ),
    "blue_key": Mystery(
        id="blue_key",
        clue="a blue key prop",
        culprit="a loose costume pocket",
        hiding_place="under the drum",
        magical=True,
        rhyme_word="glow",
        repetition_word="slow",
    ),
    "gold_ring": Mystery(
        id="gold_ring",
        clue="a golden ring prop",
        culprit="a spinning trick string",
        hiding_place="inside the hat box",
        magical=True,
        rhyme_word="ring",
        repetition_word="thing",
    ),
}

NAMES = {
    "girl": ["Mina", "Lena", "Pia", "Ivy", "Nora"],
    "boy": ["Pip", "Theo", "Milo", "Arlo", "Ben"],
}
HELPERS = ["the stage mouse", "the lantern", "the old mirror"]


@dataclass
class ASPConfig:
    setting: str
    mystery: str
    magical: bool
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


ASP_RULES = r"""
setting(S) :- setting_fact(S).
mystery(M) :- mystery_fact(M).
magical_case(M) :- mystery_fact(M), magical_fact(M).
good_case(S,M) :- setting(S), mystery(M), clue_fit(S,M), magical_case(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery_fact", mid))
        if m.magical:
            lines.append(asp.fact("magical_fact", mid))
        lines.append(asp.fact("rhyme_word", mid, m.rhyme_word))
        lines.append(asp.fact("repetition_word", mid, m.repetition_word))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show magical_case/1."))
    return sorted(set(asp.atoms(model, "magical_case")))


def asp_verify() -> int:
    python_set = {mid for mid, m in MYSTERIES.items() if m.magical}
    asp_set = {m[0] for m in asp_valid_cases()}
    if python_set == asp_set:
        print(f"OK: clingo gate matches magical mysteries ({len(asp_set)}).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in python:", sorted(python_set - asp_set))
    print("only in asp:", sorted(asp_set - python_set))
    return 1


def reasonableness_gate(setting: Setting, mystery: Mystery) -> bool:
    return setting.indoors and mystery.magical


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with a puppet, coincidence, magic, rhyme, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    if not reasonableness_gate(_safe_lookup(SETTINGS, setting), _safe_lookup(MYSTERIES, mystery)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, helper=helper)


def _say_intro(world: World, hero: Entity, mystery: Mystery, helper: str) -> None:
    world.say(
        f"{hero.id} was a little puppet detective who lived in {world.setting.place}. "
        f"{hero.pronoun().capitalize()} liked quiet clues, neat steps, and solving problems with a brave heart."
    )
    world.say(
        f"One evening, {hero.pronoun('possessive')} friends noticed that {mystery.clue} had gone missing, and {helper} said it was a strange coincidence."
    )
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    world.facts["coincidence"] = True


def _say_investigation(world: World, hero: Entity, mystery: Mystery) -> None:
    world.para()
    hero.memes["focus"] += 1
    world.say(
        f"{hero.id} looked at the stage floor, then at the curtain, and then at the lamp. "
        f"{hero.pronoun().capitalize()} whispered, 'I will follow the clue, and I will follow it again.'"
    )
    hero.memes["repetition"] += 1
    if mystery.magical:
        world.say(
            f"The lantern gave off a gentle magic glow, and the glow made a rhyme in {hero.pronoun('possessive')} mind: "
            f"'{mystery.rhyme_word}, {mystery.rhyme_word}, let the secret show and shine.'"
        )
        hero.meters["glow"] = 1.0
        hero.memes["hope"] += 1


def _say_search(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} repeated the rhyme out loud, step by step, because repetition helped the clues stay clear."
    )
    world.say(
        f"That led {hero.pronoun('object')} to the curtain, where a tiny mark on the floor matched the missing prop."
    )
    hero.memes["confidence"] += 1
    world.facts["tracked"] = True


def _say_resolution(world: World, hero: Entity, mystery: Mystery) -> None:
    world.para()
    hero.memes["relief"] += 1
    hidden = world.get(mystery.id)
    hidden.hidden = False
    hidden.location = "the stage"
    world.say(
        f"Behind the curtain, {hero.id} found {mystery.clue}. It had not vanished at all; the wind had tucked it into {mystery.hiding_place}."
    )
    world.say(
        f"That coincidence made sense now, and {hero.id} smiled as the puppet stage shone like new. "
        f"The case was solved by magic, rhyme, and repetition, and the whole theater clapped."
    )


def tell(setting: Setting, mystery: Mystery, name: str, gender: str, helper: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label="puppet detective", location=setting.place))
    prop = world.add(Entity(id=mystery.id, type="prop", label=mystery.clue, hidden=True, location=mystery.hiding_place))
    world.facts.update(hero=hero, prop=prop, mystery=mystery, helper=helper)
    _say_intro(world, hero, mystery, helper)
    _say_investigation(world, hero, mystery)
    _say_search(world, hero, mystery)
    _say_resolution(world, hero, mystery)
    return world


def story_prompts(world: World) -> list[str]:
    m = world.facts["mystery"]
    hero = world.facts["hero"]
    return [
        "Write a short detective story for a young child about a puppet solving a mystery with magic.",
        f"Tell a story where {hero.id} follows a rhyme and a repeated clue to find {m.clue}.",
        "Write a gentle puppet detective tale where a coincidence turns into a clear answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    m = world.facts["mystery"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little puppet detective.",
        ),
        QAItem(
            question=f"What went missing in the theater?",
            answer=f"{m.clue} went missing from the theater stage.",
        ),
        QAItem(
            question=f"What helped {hero.id} solve the case?",
            answer="Magic, rhyme, and repetition all helped the puppet detective solve the case.",
        ),
        QAItem(
            question=f"Why did the missing prop seem like a coincidence?",
            answer=f"It seemed like a coincidence because the same night the magic lantern began to glow, and that glow helped point to the hidden clue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a detective?", answer="A detective is someone who looks for clues and tries to solve a mystery."),
        QAItem(question="What is a puppet?", answer="A puppet is a toy or figure that can be moved and made to act like a character."),
        QAItem(question="What is rhyme?", answer="Rhyme happens when words sound alike at the end, like shine and line."),
        QAItem(question="What is repetition?", answer="Repetition means doing or saying something again and again."),
        QAItem(question="What is magic?", answer="Magic is a special kind of pretend power in stories that can make surprising things happen."),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(MYSTERIES, params.mystery), params.name, params.gender, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="the little theater", mystery="silver_star", name="Pip", gender="boy", helper="the lantern"),
    StoryParams(setting="the puppet house", mystery="blue_key", name="Mina", gender="girl", helper="the stage mouse"),
    StoryParams(setting="the old stage", mystery="gold_ring", name="Theo", gender="boy", helper="the old mirror"),
]


def asp_valid_mysteries() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show magical_case/1."))
    return sorted(set(asp.atoms(model, "magical_case")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    py = {mid for mid, m in MYSTERIES.items() if m.magical}
    cl = {m[0] for m in asp_valid_mysteries()}
    if py == cl:
        print(f"OK: ASP and Python agree on magical mysteries ({len(py)}).")
        return 0
    print("MISMATCH:", sorted(py ^ cl))
    return 1


def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    if not reasonableness_gate(_safe_lookup(SETTINGS, setting), _safe_lookup(MYSTERIES, mystery)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, helper=helper)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show magical_case/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show magical_case/1."))
        print(sorted(set(asp.atoms(model, "magical_case"))))
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
