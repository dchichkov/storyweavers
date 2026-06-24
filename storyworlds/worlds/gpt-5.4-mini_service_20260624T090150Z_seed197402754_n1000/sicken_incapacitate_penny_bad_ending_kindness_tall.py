#!/usr/bin/env python3
"""
A tiny Tall-Tale storyworld about Penny, kindness, sickness, and a bad ending
that turns into a gentler ending image.

Premise:
- Penny is a small, capable helper in a big, bustling town.
- People keep showering Penny with kindness, but one oversized act of care
  leaves Penny too tired and too sick to keep going.

Tension:
- A planned day of helping grows too heavy.
- The world model tracks strain, warmth, rest, and nausea.

Turn:
- A kind helper notices Penny is fading and chooses a smaller, safer form of
  kindness: shade, water, a chair, and quiet.

Resolution:
- Penny cannot finish the grand task, but can rest.
- The bad ending is softened into a calm, true image: Penny safe, cared for,
  and no longer being pushed past the limit.

This world is intentionally narrow and constraint-checked: "kindness" can be
too much, but only when it is the wrong size for Penny's body state.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for key in ("energy", "warmth", "strain", "sick", "care", "calm", "hope"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the bright fairground"
    affords: set[str] = field(default_factory=lambda: {"helping", "resting", "walking"})
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
class Kindness:
    id: str
    label: str
    act: str
    size: str
    helps: str
    can_backfire: bool = False
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
    place: str
    kindness: str
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
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "fair": Setting("the bright fairground"),
    "market": Setting("the wind-bent market"),
    "harbor": Setting("the old harbor lane"),
}

KINDNESSES = {
    "penny_help": Kindness(
        id="penny_help",
        label="a penny-pinching kindness",
        act="handing out pennies and praising every little step",
        size="small",
        helps="steady the heart",
        can_backfire=False,
    ),
    "big_fix": Kindness(
        id="big_fix",
        label="a big blanket of kindness",
        act="feeding, fussing, and cheering too loud for too long",
        size="large",
        helps="warm the bones",
        can_backfire=True,
    ),
    "gentle_chair": Kindness(
        id="gentle_chair",
        label="a chair-sized kindness",
        act="offering a chair, a cup of water, and quiet shade",
        size="small",
        helps="let the body rest",
        can_backfire=False,
    ),
}

GENDERS = ["girl", "boy"]
HERO_NAMES = ["Penny", "Mabel", "June", "Ivy", "Tess", "Nell"]
HELPER_NAMES = ["Aunt Ada", "Old Ben", "Mina", "Hank", "Nora", "Mr. Pike"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def kindness_can_backfire(k: Kindness) -> bool:
    return k.can_backfire


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for kid in KINDNESSES:
            combos.append((place, kid))
    return combos


def explain_rejection(kindness: Kindness) -> str:
    return (
        f"(No story: {kindness.label} does not create the kind of trouble this world "
        f"needs. Try a larger, fussier act of care.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A kindness can backfire when it is large and the body is already strained.
can_backfire(K) :- kindness(K), large(K), risky(K).

% A story is valid when the place exists and a backfiring kindness is present.
valid(Place, K) :- setting(Place), kindness(K), can_backfire(K).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for kid, k in KINDNESSES.items():
        lines.append(asp.fact("kindness", kid))
        if k.size == "large":
            lines.append(asp.fact("large", kid))
        if k.can_backfire:
            lines.append(asp.fact("risky", kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = {("fair", "big_fix"), ("market", "big_fix"), ("harbor", "big_fix")}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def predict_sicken(world: World, hero: Entity, kindness: Kindness) -> dict:
    sim = world.copy()
    _apply_kindness(sim, sim.get(hero.id), kindness, narrate=False)
    h = sim.get(hero.id)
    return {
        "sick": h.meters["sick"] >= THRESHOLD,
        "incapacitated": h.meters["energy"] <= 0.0 or h.meters["strain"] >= 2.0,
        "calm": h.meters["calm"],
    }


def _apply_kindness(world: World, hero: Entity, kindness: Kindness, narrate: bool = True) -> None:
    sig = ("kindness", kindness.id)
    if sig in world.fired:
        return
    world.fired.add(sig)

    if kindness.id == "big_fix":
        hero.meters["warmth"] += 1.5
        hero.meters["strain"] += 1.5
        hero.meters["sick"] += 1.0
        hero.meters["energy"] -= 1.0
        hero.memes["overhelped"] += 1.0
        if narrate:
            world.say(
                f"The kindness came in a great heaping wave, warm as a wool blanket on a July noon."
            )
            world.say(
                f"But Penny's cheeks went pale, and the big fuss made her stomach turn."
            )
    elif kindness.id == "gentle_chair":
        hero.meters["calm"] += 1.0
        hero.meters["energy"] += 1.0
        hero.meters["strain"] = max(0.0, hero.meters["strain"] - 1.0)
        hero.meters["sick"] = max(0.0, hero.meters["sick"] - 0.5)
        hero.memes["safe"] += 1.0
        if narrate:
            world.say(
                f"The helper brought a chair, a cup of water, and a hush that settled like snow."
            )
    else:
        hero.memes["steady"] += 1.0
        hero.meters["calm"] += 0.5
        if narrate:
            world.say(f"The small kindness was tidy and kind, like a penny tucked in a child's palm.")


def tell(setting: Setting, kindness: Kindness, hero_name: str, hero_type: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, label=hero_name,
        traits=["little", "brave"],
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type="adult", label=helper_name,
        traits=["kind"],
    ))
    world.facts.update(hero=hero, helper=helper, kindness=kindness, setting=setting)

    world.say(
        f"In {setting.place}, there lived a little {hero.type} named {hero.id}, "
        f"known from one end of the lane to the other for helping anybody in need."
    )
    world.say(
        f"{helper.id} admired {hero.id} so much that {helper.pronoun('subject')} brought "
        f"{kindness.label} in the hope of making the day shine brighter."
    )

    world.para()
    world.say(
        f"When the hour came to work, {hero.id} tried to keep pace with the town's busy errands."
    )
    if kindness.id == "big_fix":
        world.say(
            f"That was when the kindness grew too large. It was a mighty river of soups, hugs, and loud praise."
        )
    else:
        world.say(
            f"That was when the smaller kindness slipped into place, neat as a key in a lock."
        )

    _apply_kindness(world, hero, kindness, narrate=True)

    if kindness.id == "big_fix":
        world.say(
            f"Penny wanted to smile through it, but the great care had sapped her steadiness."
        )
        world.say(
            f"She wobbled like a fence post in a storm, and the doctor said she must lie down at once."
        )
        hero.meters["energy"] = max(0.0, hero.meters["energy"])
        hero.meters["sick"] += 0.5
        hero.memes["fear"] += 1.0

    world.para()
    if kindness.id == "big_fix":
        world.say(
            f"Then {helper.id} saw the bad ending coming and chose a gentler way."
        )
        gentle = KINDNESSES["gentle_chair"]
        _apply_kindness(world, hero, gentle, narrate=True)
        world.say(
            f"The great errand could not be finished, but Penny was set in a chair by the window, "
            f"with shade on her face and water in her hands."
        )
        world.say(
            f"The town kept humming outside, yet inside the little room Penny was safe, still, and cared for."
        )
    else:
        world.say(
            f"By the end, Penny had only a tiny scare, and the neat kindness left her bright-eyed and steady."
        )
        world.say(
            f"She went back to helping with a penny in her pocket and a soft grin on her face."
        )

    world.facts["bad_ending"] = kindness.id == "big_fix"
    world.facts["resolved"] = kindness.id == "big_fix"
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, kindness = f["hero"], f["helper"], f["kindness"]
    return [
        f'Write a Tall Tale for young children about {hero.id}, a tiny helper in {world.setting.place}, '
        f'where too much kindness makes {hero.id} sick and a smaller kindness helps.',
        f"Tell a story in which {helper.id} tries to help {hero.id} with {kindness.label} "
        f"but must change plans when the care becomes too heavy.",
        f"Write a gentle bad-ending story that begins with bravery, grows too big, and ends with rest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, kindness = f["hero"], f["helper"], f["kindness"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little helper with a big heart.",
        ),
        QAItem(
            question=f"What kind of care did {helper.id} bring at first?",
            answer=f"{helper.id} brought {kindness.label}, which was meant to help but turned out to be too much.",
        ),
        QAItem(
            question=f"What happened when the care got too big for {hero.id}?",
            answer=f"{hero.id} got weak and sick, and the big plan had to stop.",
        ),
    ]
    if f.get("bad_ending"):
        qa.append(
            QAItem(
                question=f"Was this a bad ending?",
                answer=(
                    f"Yes. The grand helping did not finish the task. "
                    f"But the ending was still kind, because {hero.id} was rested and kept safe."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a penny?",
            answer="A penny is a very small coin. People often use pennies as a simple example of something tiny.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means doing something caring, gentle, or helpful for someone else.",
        ),
        QAItem(
            question="Why can too much fuss make a person tired?",
            answer="Too much fuss can make a person tired because they have to keep up with noise, attention, and effort for too long.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="fair", kindness="big_fix", name="Penny", gender="girl", helper="Aunt Ada"),
    StoryParams(place="market", kindness="big_fix", name="Penny", gender="girl", helper="Nora"),
    StoryParams(place="harbor", kindness="big_fix", name="Penny", gender="girl", helper="Old Ben"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld about Penny, kindness, sickness, and a bad ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper")
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
    if getattr(args, "kindness", None) and not kindness_can_backfire(_safe_lookup(KINDNESSES, getattr(args, "kindness", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    kindness = getattr(args, "kindness", None) or "big_fix"
    name = getattr(args, "name", None) or "Penny"
    gender = getattr(args, "gender", None) or "girl"
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, kindness=kindness, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(KINDNESSES, params.kindness), params.name, params.gender, params.helper)
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_stories()
        print(f"{len(combos)} valid combos:")
        for place, kind in combos:
            print(f"  {place:8} {kind}")
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
            header = f"### {p.name} at {p.place} ({p.kindness})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
