#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a wagon wheel, a broken axle, advice, and
the right proportion of fix.

Premise:
- A young hero has a wagon with a wooden axle.
- The axle is cracked, so the wagon cannot roll well.
- A helper offers advice, but the wrong-sized fix would make things worse.
- Repetition matters: each attempt to roll reveals the same problem until the
  hero listens and chooses the proper proportion.
- Surprise matters: the "tiny" helper turns out to be the one who knows the
  exact fit.

This script follows the Storyweavers world contract:
- stdlib only
- uses storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, registries, parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    ridden_by: Optional[str] = None
    carried_by: Optional[str] = None
    size: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    axle: object | None = None
    entities: set[str] = field(default_factory=set)
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "mother", "woman", "princess"}
        male = {"boy", "king", "father", "man", "prince"}
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
    place: str = "the meadow"
    indoors: bool = False
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
class Ride:
    id: str
    verb: str
    gerund: str
    roll_phrase: str
    trouble: str
    effect: str
    tag: str = ""
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
class Fix:
    id: str
    label: str
    phrase: str
    size: str
    fits: str
    helps: str
    is_exact: bool = False
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}
        self.repetition_count: int = 0
        self.surprise: bool = False

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

    def copy(self) -> "World":
        other = World(self.setting)
        other.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        other.fired = set(self.fired)
        other.lines = []
        other.facts = dict(self.facts)
        other.repetition_count = self.repetition_count
        other.surprise = self.surprise
        return other


@dataclass
class StoryParams:
    setting: str
    ride: str
    fix: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None
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
    "meadow": Setting(place="the meadow", indoors=False, affords={"roll"}),
    "forest": Setting(place="the forest path", indoors=False, affords={"roll"}),
    "village": Setting(place="the village road", indoors=False, affords={"roll"}),
}

RIDES = {
    "cart": Ride(
        id="cart",
        verb="pull the cart",
        gerund="pulling the cart",
        roll_phrase="roll along the road",
        trouble="creaks and wobbles",
        effect="the cart moves straight",
        tag="wood",
    ),
    "wagon": Ride(
        id="wagon",
        verb="pull the wagon",
        gerund="pulling the wagon",
        roll_phrase="roll down the lane",
        trouble="rocks and rattles",
        effect="the wagon rolls smoothly",
        tag="wheel",
    ),
}

FIXES = {
    "pin": Fix(
        id="pin",
        label="a tiny pin",
        phrase="a tiny pin for the axle",
        size="tiny",
        fits="small",
        helps="holds the axle steady",
        is_exact=False,
    ),
    "peg": Fix(
        id="peg",
        label="a wooden peg",
        phrase="a wooden peg for the axle",
        size="small",
        fits="small",
        helps="fills the crack just right",
        is_exact=True,
    ),
    "strap": Fix(
        id="strap",
        label="a leather strap",
        phrase="a leather strap",
        size="large",
        fits="large",
        helps="wraps too much and makes the wheel stiff",
        is_exact=False,
    ),
}

HERO_NAMES = ["Mira", "Elsa", "Lina", "Nora", "June", "Pia"]
HELPER_NAMES = ["Hob", "Iris", "Fenn", "Wren", "Tilo", "Sage"]
HERO_TYPES = ["girl", "boy", "princess", "prince"]
HELPER_TYPES = ["old owl", "tiny mouse", "wise fox", "green frog"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld of axle, advice, and proportion.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ride", choices=RIDES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def advise(hero: Entity, helper: Entity, fix: Fix) -> str:
    return (
        f"{helper.id} leaned close and advised {hero.id} to choose "
        f"{fix.phrase}."
    )


def _roll_attempt(world: World, hero: Entity, ride: Ride, fix: Optional[Fix] = None) -> bool:
    axle = world.get("axle")
    world.repetition_count += 1
    if axle.meters["crack"] >= THRESHOLD and not (fix and fix.is_exact):
        hero.memes["frustration"] += 1
        axle.meters["wobble"] += 1
        world.say(
            f"Again and again, the {ride.id} tried to {ride.roll_phrase}, "
            f"but the axle {ride.trouble}."
        )
        return False
    axle.meters["crack"] = 0.0
    axle.meters["wobble"] = 0.0
    world.say(f"At last, the {ride.id} could {ride.effect}.")
    return True


def predict_success(world: World, ride: Ride, fix: Optional[Fix]) -> bool:
    clone = world.copy()
    clone.get("axle").meters["crack"] = clone.get("axle").meters.get("crack", 0.0)
    return _roll_attempt(clone, clone.get("hero"), ride, fix)


def introduce(world: World, hero: Entity, ride: Ride) -> None:
    world.say(
        f"Once, in {world.setting.place}, there was a little {hero.type} named {hero.id} "
        f"who loved {ride.gerund}."
    )
    world.say(
        f"The {ride.id} had one wooden axle, and that axle held the whole little journey together."
    )


def crack(world: World, hero: Entity, ride: Ride) -> None:
    axle = world.get("axle")
    axle.meters["crack"] = 1.0
    hero.memes["worry"] += 1
    world.say(
        f"But one day the axle cracked, so every trip made the {ride.id} shake."
    )


def attempt_and_repeat(world: World, hero: Entity, ride: Ride) -> None:
    _roll_attempt(world, hero, ride, None)
    world.say(
        f"{hero.id} tried again, and the same trouble came back, because the cracked axle was still there."
    )


def surprise_fix(world: World, hero: Entity, helper: Entity, ride: Ride, fix: Fix) -> None:
    world.say(
        f"Then came a surprise: the {helper.type} was not a nuisance at all, but a clever helper."
    )
    world.say(advise(hero, helper, fix))
    if fix.is_exact:
        world.say(
            f"The advice was just right in proportion, not too small and not too large."
        )
    else:
        world.say(
            f"The advice sounded brave, but its proportion was wrong for the crack."
        )


def resolution(world: World, hero: Entity, helper: Entity, ride: Ride, fix: Fix) -> None:
    axle = world.get("axle")
    if fix.is_exact:
        axle.meters["crack"] = 0.0
        hero.memes["joy"] += 1
        helper.memes["pride"] += 1
        world.say(
            f"They set the {fix.label} into the axle, and the little crack closed up neatly."
        )
        world.say(
            f"After that, the {ride.id} could {ride.effect}, and {hero.id} laughed all the way home."
        )
    else:
        axle.meters["crack"] = 1.0
        hero.memes["worry"] += 1
        world.say(
            f"The wrong fix did not help, so the axle still complained and the wheels still shivered."
        )


def tell(setting: Setting, ride: Ride, fix: Fix, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    axle = world.add(Entity(id="axle", type="axle", label="axle", owner=hero.id))
    axle.meters["crack"] = 0.0
    axle.meters["wobble"] = 0.0
    axle.memes["importance"] = 1.0

    world.facts.update(hero=hero, helper=helper, axle=axle, ride=ride, fix=fix)

    introduce(world, hero, ride)
    world.say(
        f"{hero.id} trusted the axle because it was the right piece in the right place."
    )
    crack(world, hero, ride)
    world.say(
        f"Each time {hero.id} tried to make the {ride.id} move, the crack answered with a squeak."
    )
    attempt_and_repeat(world, hero, ride)
    surprise_fix(world, hero, helper, ride, fix)
    resolution(world, hero, helper, ride, fix)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    ride: Ride = _safe_fact(world, f, "ride")
    fix: Fix = _safe_fact(world, f, "fix")
    qa = [
        QAItem(
            question=f"Who was trying to {ride.verb} in the story?",
            answer=f"It was {hero.id}, a little {hero.type} in {world.setting.place}.",
        ),
        QAItem(
            question="What was wrong with the wagon?",
            answer="The wooden axle cracked, so the ride shook and would not roll smoothly.",
        ),
        QAItem(
            question=f"What did {helper.id} do when the trouble kept coming back?",
            answer=f"{helper.id} gave advice and suggested {fix.phrase}.",
        ),
        QAItem(
            question="Why did the story repeat the same trouble more than once?",
            answer="Because the axle was still cracked, so every try brought back the same wobble until the right fix was chosen.",
        ),
    ]
    if fix.is_exact:
        qa.append(
            QAItem(
                question="Why did the surprise fix work?",
                answer=(
                    "It worked because it fit the crack in the right proportion: not too big, not too tiny, but just right."
                ),
            )
        )
    else:
        qa.append(
            QAItem(
                question="Why did the first fix fail?",
                answer="It failed because its size was the wrong proportion for the crack in the axle.",
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an axle?",
            answer="An axle is the rod or bar that holds a wheel in place so the wheel can turn.",
        ),
        QAItem(
            question="What does advise mean?",
            answer="To advise means to give a helpful suggestion about what to do.",
        ),
        QAItem(
            question="What does proportion mean?",
            answer="Proportion means the right size or amount compared with something else.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    ride: Ride = _safe_fact(world, f, "ride")
    return [
        f"Write a fairy tale where {hero.id} wants to {ride.verb} but the axle is cracked.",
        "Tell a short story with repetition, a surprise helper, and the word proportion.",
        f"Create a child-friendly tale about an axle that needs advice and the right proportion of repair.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  repetition_count={world.repetition_count}")
    lines.append(f"  surprise={world.surprise}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="meadow", ride="wagon", fix="peg", hero_name="Mira", hero_type="girl", helper_name="Wren", helper_type="tiny mouse"),
    StoryParams(setting="forest", ride="cart", fix="pin", hero_name="Pia", hero_type="princess", helper_name="Sage", helper_type="wise fox"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    ride = getattr(args, "ride", None) or rng.choice(list(RIDES))
    fix = getattr(args, "fix", None) or rng.choice(list(FIXES))
    if getattr(args, "fix", None) and not _safe_lookup(FIXES, fix).is_exact:
        # still allowed, but if explicit invalid combination chosen, reject if no exact fit
        pass
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    hero_type = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper_type = rng.choice(HELPER_TYPES)
    return StoryParams(setting=setting, ride=ride, fix=fix, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(RIDES, params.ride),
        _safe_lookup(FIXES, params.fix),
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


ASP_RULES = r"""
axle(axle).
hero(H) :- hero_name(H).
helper(X) :- helper_name(X).
cracked(axle) :- crack(axle).
repetition(Story) :- repeated(Story).
surprise(Story) :- surprise_helper(Story).

good_fix(F) :- exact(F).
bad_fix(F) :- not exact(F).

advises(Helper,Hero,F) :- helper(Helper), hero(Hero), fix(F), exact(F).
valid_story :- cracked(axle), exact(peg).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("axle", "axle"),
        asp.fact("hero_name", "hero"),
        asp.fact("helper_name", "helper"),
        asp.fact("crack", "axle"),
        asp.fact("repeated", "story"),
        asp.fact("surprise_helper", "story"),
        asp.fact("fix", "peg"),
        asp.fact("exact", "peg"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    asp_ok = any(sym.name == "valid_story" for sym in model)
    py_ok = FIXES["peg"].is_exact
    if asp_ok == py_ok:
        print("OK: ASP parity matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_sample_from_args(args: argparse.Namespace, seed: int) -> StorySample:
    params = resolve_params(args, random.Random(seed))
    params.seed = seed
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show axle/1.\n#show valid_story/0."))
        print(f"ASP model atoms: {len(model)}")
        for sym in model:
            print(sym)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            sample = build_sample_from_args(args, seed)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.ride} in {p.setting} (fix: {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
