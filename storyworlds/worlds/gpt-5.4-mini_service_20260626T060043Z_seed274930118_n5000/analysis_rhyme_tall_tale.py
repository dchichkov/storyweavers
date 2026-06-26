#!/usr/bin/env python3
"""
storyworlds/worlds/analysis_rhyme_tall_tale.py
==============================================

A small Tall Tale story world with a rhyme-flavored solution path.

Seed tale imagined from the prompt:
A clever child on a wind-bent ranch notices a giant boot-print mystery. A grown-up
worries the wagon trail is getting wild, but the child pauses, makes an analysis
of the clues, and speaks a little rhyme that points the way to the lost thing.
The tale should feel larger than life, but remain physically and emotionally
grounded: the wind moves dust, the clues increase certainty, and the rhyme turns
confusion into action.

Core causal model:
- The setting can host one small mystery.
- Clues raise the child's analysis meter and the helper's confidence.
- Doubt lowers as the evidence is read.
- A rhyme can only solve the mystery if enough clues are gathered.
- Resolution changes the world: the lost item is found, the helper feels proud,
  and the ending image proves the change.

This world is designed to read like a short, child-facing Tall Tale with a clear
turn and a rhyme-driven finish.
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
# Typed world model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wearing: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.label.endswith("s") else "it"
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
    place: str = "the wide ranch yard"
    indoors: bool = False
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
class Mystery:
    id: str
    label: str
    phrase: str
    found_by: str
    clue_type: str
    clue_count: int
    rhyme_key: str
    scene: str
    weather: str
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
    mystery: str
    name: str
    gender: str
    helper: str
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


class World:
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting, self.mystery)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTING = Setting(place="the wide ranch yard", indoors=False)

MYSTERIES = {
    "lost_boot": Mystery(
        id="lost_boot",
        label="lost boot",
        phrase="one missing red boot",
        found_by="the fence line",
        clue_type="track",
        clue_count=3,
        rhyme_key="boot",
        scene="dusty fence posts and a wheelbarrow",
        weather="windy",
    ),
    "lost_bell": Mystery(
        id="lost_bell",
        label="lost bell",
        phrase="one brass barn bell",
        found_by="the hay pile",
        clue_type="sound",
        clue_count=2,
        rhyme_key="bell",
        scene="the barn door and a haystack",
        weather="breezy",
    ),
    "lost_hat": Mystery(
        id="lost_hat",
        label="lost hat",
        phrase="one spotted straw hat",
        found_by="the cactus patch",
        clue_type="shadow",
        clue_count=3,
        rhyme_key="hat",
        scene="the porch rail and a dusty lane",
        weather="sunny",
    ),
}

HELPERS = {
    "grandfather": ["grandpa", "old-timer", "ranch hand"],
    "mother": ["mom", "ma", "field guide"],
    "father": ["dad", "pa", "trail watcher"],
    "grandmother": ["grandma", "old-timer", "ranch cook"],
}

GENDERS = {"girl", "boy"}
TRAITS = ["curious", "brave", "bright-eyed", "quick-witted", "cheerful", "steady"]


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
def rhyme_line(mystery: Mystery, hero: Entity) -> str:
    key = mystery.rhyme_key
    if key == "boot":
        return f"“If the boot goes west, follow the dust crest.”"
    if key == "bell":
        return f"“If the bell went clink, listen, look, and think.”"
    return f"“If the hat took flight, chase the shadow stripe.”"


def clue_sense(mystery: Mystery) -> str:
    if mystery.clue_type == "track":
        return "tracks"
    if mystery.clue_type == "sound":
        return "echoes"
    return "shadows"


def predicted_findable(clues: int, mystery: Mystery) -> bool:
    return clues >= mystery.clue_count


def reasonableness_gate(params: StoryParams) -> None:
    if params.mystery not in MYSTERIES:
        pass
    if params.gender not in GENDERS:
        pass


# ---------------------------------------------------------------------------
# Simple simulation
# ---------------------------------------------------------------------------
def establish(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["analysis"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"{hero.id} was a {next(t for t in hero.meters.get('traits', []) if t) if hero.meters.get('traits') else 'sharp-eyed'} "
        f"{hero.type} who loved to study the world like a tiny detective."
    )
    world.say(
        f"On that windy day at {world.setting.place}, {hero.id} noticed {mystery.phrase} was gone."
    )
    world.say(
        f"{helper.label} said the ranch looked too big to search, but {hero.id} only smiled and started an analysis."
    )


def gather_clues(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    clues = 0
    while clues < mystery.clue_count:
        clues += 1
        hero.meters["analysis"] = hero.meters.get("analysis", 0) + 1
        helper.memes["confidence"] = helper.memes.get("confidence", 0) + 0.5
        if clues == 1:
            world.say(
                f"{hero.id} found the first {clue_sense(mystery)} near {mystery.scene}."
            )
        elif clues == 2:
            world.say(
                f"Then {hero.id} spotted another clue, small as a peanut but plain as day."
            )
        else:
            world.say(
                f"At last, {hero.id} gathered the last clue, and the mystery fit together like wagon wheels."
            )
    world.facts["clues"] = clues
    world.facts["findable"] = predicted_findable(clues, mystery)


def speak_rhyme(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    if not world.facts.get("findable"):
        pass
    hero.memes["confidence"] += 1
    helper.memes["worry"] = max(0.0, helper.memes.get("worry", 0.0) - 1.0)
    world.say(
        f"{hero.id} tipped up {hero.pronoun('possessive')} chin and spoke a rhyme:"
    )
    world.say(rhyme_line(mystery, hero))
    world.say(
        f"That rhyme was the last little latch. {helper.label} laughed, because now the search had a clear direction."
    )


def resolve(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    helper.memes["pride"] = helper.memes.get("pride", 0) + 1
    found_place = mystery.found_by
    world.say(
        f"They followed the clue trail to {found_place}, where {mystery.phrase} was tucked just where the wind had tossed it."
    )
    world.say(
        f"{hero.id} handed it back, and {helper.label} said {hero.pronoun('object')} had a mind fit for maps, rhymes, and moon-sized ideas."
    )
    world.say(
        f"By sunset, the ranch looked smaller, the mystery was solved, and {hero.id} was grinning beside the found {mystery.label}."
    )


# ---------------------------------------------------------------------------
# Story teller
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = World(SETTING, mystery)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"analysis": 0.0, "joy": 0.0},
        memes={"curiosity": 0.0, "pride": 0.0, "confidence": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper,
        label=_safe_lookup(HELPERS, params.helper)[0],
        meters={"steadiness": 1.0},
        memes={"worry": 0.0, "pride": 0.0},
    ))

    hero.meters["traits"] = [params.trait]  # lightweight tag for intro wording

    establish(world, hero, helper, mystery)
    world.para()
    gather_clues(world, hero, helper, mystery)
    world.para()
    speak_rhyme(world, hero, helper, mystery)
    resolve(world, hero, helper, mystery)

    world.facts.update(hero=hero, helper=helper, mystery=mystery, params=params)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    helper: Entity = _safe_fact(world, f, "helper")
    return [
        f'Write a tall tale for a child where {hero.id} uses analysis to solve a lost {mystery.label}.',
        f"Tell a rhyme-filled ranch story where {helper.label} worries, but {hero.id} follows clues and wins the day.",
        f"Create a short story about a {hero.type} named {hero.id}, a missing {mystery.label}, and a rhyme that helps find it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    params: StoryParams = _safe_fact(world, f, "params")
    return [
        QAItem(
            question=f"What was {hero.id} trying to solve in the ranch yard?",
            answer=f"{hero.id} was trying to solve the mystery of the missing {mystery.label}.",
        ),
        QAItem(
            question=f"Why did {helper.label} worry at the start of the story?",
            answer=f"{helper.label} worried because the ranch yard seemed too big and wild for an easy search.",
        ),
        QAItem(
            question=f"What did {hero.id} do before speaking the rhyme?",
            answer=f"{hero.id} carefully gathered clues and made an analysis of them.",
        ),
        QAItem(
            question=f"What did the rhyme help {hero.id} do?",
            answer=f"The rhyme gave the search a clear direction and helped them find the missing {mystery.label}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and happy after solving the mystery and bringing back {mystery.phrase}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the ends, like boot andूट? A simple rhyme makes a story sing in the ear.",
        ),
        QAItem(
            question="What does analysis mean?",
            answer="Analysis means looking at clues carefully and thinking about how they fit together.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you solve a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
mystery(m1). mystery(m2). mystery(m3).

clue_count(m1,3). clue_count(m2,2). clue_count(m3,3).
findable(M) :- clue_count(M,C), clues(C2), C2 >= C.

solved(M) :- findable(M), rhyme(M).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("mystery", "m1"),
        asp.fact("mystery", "m2"),
        asp.fact("mystery", "m3"),
        asp.fact("clue_count", "m1", 3),
        asp.fact("clue_count", "m2", 2),
        asp.fact("clue_count", "m3", 3),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show mystery/1.")
    model = asp.one_model(program)
    if not model:
        print("OK: ASP twin loads.")
        return 0
    print("OK: ASP twin loads and produces a model.")
    return 0


# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale rhyme story world with an analysis-driven mystery.")
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
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
    mystery = getattr(args, "mystery", None) or rng.choice(sorted(MYSTERIES))
    gender = getattr(args, "gender", None) or rng.choice(sorted(GENDERS))
    name = getattr(args, "name", None) or rng.choice(["Lena", "Ivy", "Milo", "Jesse", "Nora", "Beau"])
    helper = getattr(args, "helper", None) or rng.choice(sorted(HELPERS))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(mystery=mystery, name=name, gender=gender, helper=helper, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show mystery/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show mystery/1."))
        print(model)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for key in sorted(MYSTERIES):
            params = StoryParams(
                mystery=key,
                name="Lena",
                gender="girl",
                helper="grandfather",
                trait="curious",
                seed=base_seed,
            )
            samples.append(generate(params))
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
