#!/usr/bin/env python3
"""
A small folk-tale storyworld about a child, a shiny aluminum thing, a nix, a twist,
and a reconciliation, with sound effects threaded through the action.

The premise:
- A child wants to use a bright aluminum object for a pleasant folk-style task.
- A nix-like trickster spirit worries that the shiny thing will be claimed by the wrong party.
- A mistaken twist breaks the plan.
- A reconciliation restores the object to the right hands, with a simple, satisfying ending.

The world is intentionally narrow: only a few combinations are reasonable.
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
# World state
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    place: str = ""
    child_name: str = ""
    child_type: str = ""
    caretaker_type: str = ""
    object_id: str = ""
    helper_id: str = ""
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


@dataclass
class Setting:
    place: str
    affordance: str
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
class Prop:
    id: str
    label: str
    phrase: str
    type: str
    sound: str
    twist_sound: str
    reconciliation_sound: str
    friendly_use: str
    risk: str
    ending_image: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "millpond": Setting(place="the millpond", affordance="float a small offering"),
    "orchard": Setting(place="the orchard", affordance="carry a gift to the fair"),
    "hearth": Setting(place="the hearth", affordance="stir the supper pot"),
}

PROPS = {
    "lantern": Prop(
        id="lantern",
        label="lantern",
        phrase="a bright aluminum lantern",
        type="lantern",
        sound="clink",
        twist_sound="clang",
        reconciliation_sound="hum",
        friendly_use="light the path",
        risk="go missing in the wrong hands",
        ending_image="the lantern shining softly over the water",
    ),
    "cup": Prop(
        id="cup",
        label="cup",
        phrase="a small aluminum cup",
        type="cup",
        sound="tink",
        twist_sound="plink",
        reconciliation_sound="ring",
        friendly_use="carry spring water",
        risk="get carried off by the wind",
        ending_image="the cup resting beside the bread",
    ),
    "spoon": Prop(
        id="spoon",
        label="spoon",
        phrase="a little aluminum spoon",
        type="spoon",
        sound="ting",
        twist_sound="clink",
        reconciliation_sound="soft ring",
        friendly_use="stir the porridge",
        risk="be mistaken for a silver charm",
        ending_image="the spoon tucked beside the bowl",
    ),
}

CHILD_NAMES = ["Mira", "Eli", "Nora", "Finn", "Lena", "Oren"]
CARETAKERS = {"mother": "mother", "father": "father", "grandmother": "grandmother", "grandfather": "grandfather"}
CHILD_TYPES = {"girl": "girl", "boy": "boy"}


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def build_story(world: World, params: StoryParams) -> None:
    prop = _safe_lookup(PROPS, params.object_id)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        label=params.child_name,
        memes={"hope": 1.0, "worry": 0.0, "relief": 0.0, "joy": 0.0},
    ))
    caretaker = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=params.caretaker_type,
        label=params.caretaker_type,
        memes={"care": 1.0, "worry": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="Nix",
        kind="character",
        type="nix",
        label="the nix",
        memes={"mischief": 1.0, "regret": 0.0, "warmth": 0.0},
    ))
    obj = world.add(Entity(
        id=prop.id,
        kind="thing",
        type=prop.type,
        label=prop.label,
        phrase=prop.phrase,
        owner=child.id,
        caretaker=caretaker.id,
        carried_by=child.id,
        location=world.setting.place,
    ))

    # Act 1: setup
    world.say(
        f"Once, in {world.setting.place}, there lived a little {child.type} named {child.id}."
    )
    world.say(
        f"{child.id} loved the look of {obj.phrase}, because it gleamed like moonlight on a bowl."
    )
    world.say(
        f"Whenever {child.id} touched it, it went {prop.sound}, and that tiny sound made the day feel cheerful."
    )

    # Act 2: tension
    world.para()
    world.say(
        f"One evening, {child.id} wanted to {prop.friendly_use} with it at {world.setting.place}."
    )
    world.say(
        f"But the nix peered from the reeds and said, '{prop.label} will {prop.risk}.'"
    )
    caretaker.memes["worry"] += 1.0
    child.memes["worry"] += 1.0
    world.say(
        f"{child.id} frowned. The water answered with a soft {prop.twist_sound}, as if the pond itself had a secret."
    )

    # Twist
    world.para()
    world.say(
        f"Then the wind gave a sly twist, and the {prop.label} slipped from {child.id}'s hands."
    )
    obj.carried_by = "Nix"
    obj.location = "reeds"
    helper.memes["mischief"] += 0.5
    world.say(
        f"It landed near the nix with a bright {prop.twist_sound}, and everyone gasped."
    )
    world.say(
        f"For a moment, it seemed the shiny thing might be lost to the wrong story."
    )

    # Reconciliation
    world.para()
    helper.memes["regret"] += 1.0
    helper.memes["warmth"] += 1.0
    caretaker.memes["relief"] += 1.0
    child.memes["joy"] += 1.0
    child.memes["worry"] = 0.0
    caretaker.memes["worry"] = 0.0
    obj.carried_by = child.id
    obj.location = "hands"
    world.say(
        f"At last, the nix lowered its head and said it had meant no harm."
    )
    world.say(
        f"{child.id}'s {params.caretaker_type} smiled, and together they made a gentle bargain: "
        f"the {prop.label} would be used wisely, not snatched."
    )
    world.say(
        f"The little object gave a calm {prop.reconciliation_sound}, and peace came back to {world.setting.place}."
    )
    world.say(
        f"In the end, {prop.ending_image}, while {child.id} and the nix stood side by side like old friends."
    )

    world.facts = {
        "child": child,
        "caretaker": caretaker,
        "helper": helper,
        "object": obj,
        "prop": prop,
        "setting": world.setting,
    }


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for prop_id in PROPS:
            out.append((place, prop_id))
    return out


ASP_RULES = r"""
valid(P, O) :- setting(P), prop(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prop")
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    return [
        f'Write a short folk tale for a small child about a nix, an aluminum {p.label}, and a kind ending.',
        f'Tell a gentle story where {child.id} hears a {p.sound}, then a twist, then a reconciliation.',
        f'Write a tiny story set at {world.setting.place} with an aluminum {p.label} that ends in peace.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, caretaker, helper, prop = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "caretaker"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prop")
    return [
        QAItem(
            question=f"What shiny thing did {child.id} love?",
            answer=f"{child.id} loved {prop.phrase}. It gleamed in the folk-tale light and made a cheerful {prop.sound}.",
        ),
        QAItem(
            question=f"Who worried when the {prop.label} might be lost?",
            answer=f"{caretaker.label.capitalize()} worried, and even the nix noticed the trouble. The worry came before the twist was mended.",
        ),
        QAItem(
            question="What happened after the twist?",
            answer=f"The nix gave back the {prop.label}, said sorry in its own way, and the story ended in reconciliation.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"{child.id} was happy at the end, because the {prop.label} was safe again and the whole place grew calm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nix in folk tales?",
            answer="A nix is a water spirit or trickster from old folk tales. It may hide by the water, make trouble, or later choose to help.",
        ),
        QAItem(
            question="Why does aluminum make a nice story object?",
            answer="Aluminum is light and shiny, so it can catch the light and make a small object seem bright and special.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means people who were upset make peace again. They listen, apologize, and agree to move forward kindly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld with a nix and a bright aluminum object.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--object", dest="object_id", choices=PROPS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=list(CARETAKERS.keys()))
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "object_id", None):
        combos = [c for c in combos if c[1] == getattr(args, "object_id", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, object_id = rng.choice(combos)
    prop = _safe_lookup(PROPS, object_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(list(CARETAKERS.keys()))
    if getattr(args, "gender", None) and getattr(args, "name", None) is None:
        # name selection already okay, no further constraint
        pass
    return StoryParams(
        place=place,
        child_name=name,
        child_type=gender,
        caretaker_type=parent,
        object_id=object_id,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    build_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid_stories() -> list[tuple]:
    return asp_valid_combos()


def asp_verify_gate() -> int:
    return asp_verify()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="millpond", child_name="Mira", child_type="girl", caretaker_type="mother", object_id="lantern"),
    StoryParams(place="orchard", child_name="Finn", child_type="boy", caretaker_type="father", object_id="cup"),
    StoryParams(place="hearth", child_name="Nora", child_type="girl", caretaker_type="grandmother", object_id="spoon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_gate())
    if getattr(args, "asp", None):
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible combos:")
        for place, obj in combos:
            print(f"  {place:10} {obj}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
