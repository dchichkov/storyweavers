#!/usr/bin/env python3
"""
A small folk-tale story world about a boat, a broken mast, a flippered helper,
and a patch that saves the day.

The seed image:
- A little fisher folk tale by the sea.
- A mast is cracked in a storm.
- A flippered sea helper brings a patch.
- Surprise, moral value, and humor shape the turn and ending.

The world is intentionally compact: one place, one problem, one clever fix.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    FLIPPER: object | None = None
    MAST: object | None = None
    PATCH: object | None = None
    flipper: object | None = None
    helper: object | None = None
    hero: object | None = None
    mast: object | None = None
    patch: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "daughter"}
        male = {"boy", "father", "man", "brother", "son"}
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
class Setting:
    place: str = "the harbor"
    sea: str = "calm"
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
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
    name: str
    hero_type: str
    helper_type: str
    place: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
    "harbor": Setting(place="the harbor", sea="windy"),
    "shore": Setting(place="the shore", sea="restless"),
    "bay": Setting(place="the bay", sea="calm"),
}

HERO_TYPES = ["fisher", "sailor", "boatkeeper"]
HELPER_TYPES = ["dolphin", "seal", "merchild"]

NAMES = ["Milo", "Nina", "Tavi", "Lena", "Oren", "Pippa", "Jory", "Sia"]

# The seed words, used as concrete world objects.
MAST = Entity(
    id="mast",
    kind="thing",
    type="mast",
    label="mast",
    phrase="a tall wooden mast",
)

FLIPPER = Entity(
    id="flipper",
    kind="thing",
    type="flipper",
    label="flipper",
    phrase="a strong flipper",
)

PATCH = Entity(
    id="patch",
    kind="thing",
    type="patch",
    label="patch",
    phrase="a bright canvas patch",
)

# Content constraints for the little domain.
BROKEN_MAST_STATES = {"cracked", "wobbling"}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A tale is reasonable when a cracked mast can be fixed by a patch brought by a helper with a flipper.
broken_mast(S) :- mast_state(S, cracked).
can_fix(S) :- broken_mast(S), has_patch(S), helper_has_flipper(S).
surprise(S) :- broken_mast(S), helper_arrives(S).
humor(S) :- helper_slips(S).
moral_value(S) :- can_fix(S), shares_work(S).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("mast_state", "story", "cracked"),
        asp.fact("has_patch", "story"),
        asp.fact("helper_has_flipper", "story"),
        asp.fact("helper_arrives", "story"),
        asp.fact("shares_work", "story"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_fix/1. #show surprise/1. #show humor/1. #show moral_value/1."))
    atoms = {(sym.name, tuple(a.name if hasattr(a, "name") else str(a) for a in sym.arguments)) for sym in model}
    expected = {
        ("broken_mast", ("story",)),
        ("can_fix", ("story",)),
        ("surprise", ("story",)),
        ("humor", ("story",)),
        ("moral_value", ("story",)),
    }
    got = atoms
    if got != expected:
        print("MISMATCH between ASP and Python world assumptions.")
        print("  got:", sorted(got))
        print("  expected:", sorted(expected))
        return 1
    print("OK: ASP parity check passed.")
    return 0


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def _clean_story_word(name: str) -> str:
    return name[0].upper() + name[1:]


def build_story(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    mast = world.get("mast")
    flipper = world.get("flipper")
    patch = world.get("patch")

    # Act 1: setup.
    world.say(
        f"Once, in {world.setting.place}, there lived a small {hero.type} named {hero.id} who loved the sea."
    )
    world.say(
        f"{hero.id} kept a little boat with a proud {mast.label}, and every morning {hero.pronoun()} checked it twice."
    )
    world.say(
        f"Beside the boat waited a bright {patch.label}, folded neat as a napkin and stitched with care."
    )

    # Act 2: trouble and surprise.
    world.para()
    hero.memes["duty"] = hero.memes.get("duty", 0) + 1
    mast.meters["broken"] = 1
    mast.meters["cracked"] = 1
    world.say(
        f"Then one gusty day, the wind leaned hard, and the {mast.label} cracked with a sad little crack."
    )
    world.say(
        f"{hero.id} gasped, for a mast that wobbles can make a boat dance like a goose on a barrel."
    )
    world.say(
        f"Just then, a {helper.type} rose from the water, and on its shiny back flashed a clever {flipper.label}."
    )
    world.say(
        f"That was the surprise: the helper did not bring a rope or a nail, but the very {patch.label} needed for the repair."
    )

    # Act 3: moral value and humor.
    world.para()
    helper.memes["kindness"] = 1
    hero.memes["hope"] = 1
    world.say(
        f"The {helper.type} nudged the {patch.label} toward shore, and {hero.id} laughed in relief."
    )
    world.say(
        f"Together they fixed the mast, and {hero.id} tied the patch with steady hands while the {helper.type} held the line."
    )
    world.say(
        f"The helper gave one proud flip of {flipper.label}, splashing water on its own nose, which made {hero.id} laugh again."
    )
    world.say(
        f"So the boat stood straight, the patch held firm, and the sea seemed to nod its approval."
    )

    mast.meters["broken"] = 0
    mast.meters["patched"] = 1
    patch.worn_by = "mast"
    world.facts.update(
        hero=hero,
        helper=helper,
        mast=mast,
        flipper=flipper,
        patch=patch,
        surprise=True,
        humor=True,
        moral_value=True,
    )


# ---------------------------------------------------------------------------
# QA and prose helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    return [
        'Write a short folk tale about a cracked mast, a helpful flipper, and a patch that arrives by surprise.',
        f"Tell a gentle sea story where {hero.id} fixes a broken mast with help from a {helper.type}.",
        'Write a child-friendly story that includes the words mast, flipper, and patch, and ends with a moral and a funny moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a small {hero.type} who loved the sea and cared for a boat with a mast.",
        ),
        QAItem(
            question=f"What was surprising about the helper?",
            answer=f"It was surprising that a {helper.type} came up from the water and brought the patch needed to fix the mast.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="By the end, the cracked mast was patched, the boat stood straight again, and everyone felt relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mast?",
            answer="A mast is a tall pole on a boat that helps hold up sails.",
        ),
        QAItem(
            question="What is a flipper?",
            answer="A flipper is a fin-like body part that sea animals use to swim and steer.",
        ),
        QAItem(
            question="What is a patch?",
            answer="A patch is a piece of material used to cover a hole or repair something torn.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES)
    if place not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(name=name, hero_type=hero_type, helper_type=helper_type, place=place)


def generate(params: StoryParams) -> StorySample:
    world = World(setting=_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_type))
    mast = world.add(Entity(id="mast", kind="thing", type="mast", label="mast", phrase="a tall wooden mast"))
    flipper = world.add(Entity(id="flipper", kind="thing", type="flipper", label="flipper", phrase="a strong flipper"))
    patch = world.add(Entity(id="patch", kind="thing", type="patch", label="patch", phrase="a bright canvas patch"))

    build_story(world)

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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(name="Milo", hero_type="fisher", helper_type="dolphin", place="harbor"),
    StoryParams(name="Nina", hero_type="sailor", helper_type="seal", place="shore"),
    StoryParams(name="Tavi", hero_type="boatkeeper", helper_type="merchild", place="bay"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world with mast, flipper, and patch.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show can_fix/1. #show surprise/1. #show humor/1. #show moral_value/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.hero_type} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
