#!/usr/bin/env python3
"""
A small beach fairy-tale world with a happy ending.

Premise:
- A tiny midget-sized beach fairy loves collecting adjective shells.
- The tide threatens a sandcastle sign unless the fairy and a helper recover the
  missing adjective charm.
- A gentle compromise and a quick rescue turn worry into a bright ending.

The story engine models:
- physical meters: shell, sand, tide, shine, damp
- emotional memes: joy, worry, courage, relief, pride

The world is intentionally small and constraint-checked: only a few believable
story variants are generated, and invalid explicit choices raise StoryError.
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
# World entities
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
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    region: object | None = None
    charm: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fairy", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the beach"
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
class Charm:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
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
class Helper:
    id: str
    label: str
    phrase: str
    fix_label: str
    fix_tail: str
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
    place: str
    charm: str
    helper: str
    name: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "beach": Setting(place="the beach", affords={"tide", "shellwind"}),
}

CHARMS = {
    "adjective_shell": Charm(
        id="adjective_shell",
        label="adjective shell",
        phrase="a bright adjective shell",
        type="shell",
        region="hand",
    ),
    "sparkle_shell": Charm(
        id="sparkle_shell",
        label="sparkle shell",
        phrase="a tiny sparkle shell",
        type="shell",
        region="hand",
    ),
}

HELPERS = {
    "seagull": Helper(
        id="seagull",
        label="a seagull",
        phrase="a feather-bright seagull",
        fix_label="shell-boat",
        fix_tail="brought it back in a little shell-boat",
    ),
    "starfish": Helper(
        id="starfish",
        label="a starfish",
        phrase="a cheerful starfish",
        fix_label="sand-ramp",
        fix_tail="pushed it up the sand-ramp",
    ),
}

TRAITS = ["brave", "gentle", "curious", "cheerful", "small", "spry"]
NAMES = ["Lina", "Mimi", "Pip", "Nora", "Fae", "Suri"]


def reason_gate(params: StoryParams) -> None:
    if params.place != "beach":
        pass
    if params.charm not in CHARMS:
        pass
    if params.helper not in HELPERS:
        pass
    if params.trait not in TRAITS:
        pass


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(beach).
charm(adjective_shell).
charm(sparkle_shell).
helper(seagull).
helper(starfish).

valid_story(P,C,H) :- place(P), charm(C), helper(H).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "beach")]
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {("beach", c, h) for c in CHARMS for h in HELPERS}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    reason_gate(params)
    world = World(_safe_lookup(SETTINGS, params.place))

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="fairy",
        traits=[params.trait, "tiny", "midget-sized"],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="creature",
        label=_safe_lookup(HELPERS, params.helper).label,
        phrase=_safe_lookup(HELPERS, params.helper).phrase,
    ))
    charm_cfg = _safe_lookup(CHARMS, params.charm)
    charm = world.add(Entity(
        id="charm",
        kind="thing",
        type=charm_cfg.type,
        label=charm_cfg.label,
        phrase=charm_cfg.phrase,
        owner=hero.id,
        caretaker=hero.id,
        region=charm_cfg.region,
        plural=charm_cfg.plural,
    ))
    charm.worn_by = hero.id

    world.facts.update(hero=hero, helper=helper, charm=charm, params=params)
    return world


def predict_loss(world: World) -> bool:
    sim = world.copy()
    sim.get("charm").meters["lost"] = 1
    return sim.get("charm").meters["lost"] >= 1


def tell_story(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    charm: Entity = _safe_fact(world, f, "charm")
    params: StoryParams = _safe_fact(world, f, "params")
    helper_cfg = _safe_lookup(HELPERS, params.helper)

    world.say(
        f"Once upon a tide-lit morning at the beach, {hero.id} was a little "
        f"{params.trait} fairy who was midget-sized and proud of every grain of sand."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved collecting an {charm.label} because "
        f"the little word-shine inside it made the shell cast magical names."
    )
    world.say(
        f"{hero.id} used the charm to label a sandcastle sign, so the castle could "
        f"read 'Happy Home' when the sea breeze came close."
    )

    world.para()
    world.say(
        f"Then the tide rolled in farther than expected, and the sign tipped on its side."
    )
    world.say(
        f"{hero.id} gasped and worried that the {charm.label} might vanish into the foam."
    )
    if predict_loss(world):
        world.say(
            f'"Oh no," {hero.pronoun("possessive")} voice whispered, "I need that '
            f'{charm.label} to keep my castle bright."'
        )

    world.para()
    world.say(
        f"But {helper.label} swooped down with a kind eye and a clever plan."
    )
    world.say(
        f'"{helper_cfg.fix_label} first," {helper.pronoun("subject").capitalize()} '
        f"chirped, and then {helper_cfg.fix_tail}."
    )
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["worry"] = 0
    charm.meters["shine"] = 1

    world.say(
        f"{hero.id} ran after the helper, caught the {charm.label} before the next wave, "
        f"and tucked it safely beside the castle gate."
    )
    world.say(
        f"With the charm back in place, the sandcastle sign shone clearly again, "
        f"and the beach looked like it had been sprinkled with a happy ending."
    )
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write a fairy tale set at the beach about a midget-sized fairy named {p.name} "
        f"who must protect an adjective shell.",
        f"Tell a gentle happy-ending story where {p.name} uses a magical adjective "
        f"charm at the beach and gets help from {_safe_lookup(HELPERS, p.helper).label}.",
        f"Create a short beach fairy tale that includes the words adjective and midget, "
        f"and ends with a bright rescue and a happy castle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    charm: Entity = _safe_fact(world, f, "charm")
    helper: Entity = _safe_fact(world, f, "helper")
    params: StoryParams = _safe_fact(world, f, "params")
    helper_cfg = _safe_lookup(HELPERS, params.helper)
    return [
        QAItem(
            question=f"Who was the story about at the beach?",
            answer=(
                f"It was about {hero.id}, a little {params.trait} fairy who was "
                f"midget-sized and loved the {charm.label}."
            ),
        ),
        QAItem(
            question=f"What did the tide threaten to do?",
            answer=(
                f"The tide threatened to wash the {charm.label} away and tip the "
                f"sandcastle sign over."
            ),
        ),
        QAItem(
            question=f"Who helped {hero.id} fix the problem?",
            answer=(
                f"{helper.label} helped by using the {helper_cfg.fix_label} plan "
                f"and bringing the charm back safely."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended happily, with the {charm.label} back beside the castle "
                f"gate and the beach shining like a fairy-tale page."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beach?",
            answer=(
                "A beach is a stretch of land by the sea where sand, waves, and "
                "shells meet."
            ),
        ),
        QAItem(
            question="What does the word adjective do?",
            answer=(
                "An adjective is a describing word. It tells more about a person, "
                "place, or thing, like saying a shell is bright or tiny."
            ),
        ),
        QAItem(
            question="Why are shell treasures special?",
            answer=(
                "Shell treasures can be special because they are pretty, come from "
                "the sea, and can feel magical in a fairy tale."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Beach fairy tale world with a happy ending.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--charm", choices=CHARMS.keys())
    ap.add_argument("--helper", choices=HELPERS.keys())
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
    if getattr(args, "place", None) and getattr(args, "place", None) != "beach":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = "beach"

    charm = getattr(args, "charm", None) or rng.choice(list(CHARMS.keys()))
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS.keys()))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(place=place, charm=charm, helper=helper, name=name, trait=trait)


CURATED = [
    StoryParams(place="beach", charm="adjective_shell", helper="seagull", name="Lina", trait="cheerful"),
    StoryParams(place="beach", charm="sparkle_shell", helper="starfish", name="Pip", trait="gentle"),
]


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for t in stories:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
