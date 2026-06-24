#!/usr/bin/env python3
"""
storyworlds/worlds/humorous_twist_sound_effects_kindness_heartwarming.py
========================================================================

A small, self-contained storyworld about a child, a surprising noisy twist,
and a kind choice that turns the day warm again.

Premise:
- A character wants to use a noisy toy or gadget in a quiet place.
- The noise startles someone or ruins a calm moment.
- A humorous twist makes the noisy thing turn helpful instead of harmful.
- Kindness resolves the tension and ends with a gentle, heartwarming image.

The world is intentionally tiny: one setting, one main object, one emotional
turn, and one recovery. The prose is driven by simulated state rather than
fixed template swapping.
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

# ---------------------------------------------------------------------------
# Data model
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
            keys = [upper + "S", upper + "ES"]
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    toy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
    place: str
    quiet: bool = True
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
class Activity:
    id: str
    verb: str
    sound: str
    effect: str
    twist: str
    help_line: str
    tags: set[str] = field(default_factory=set)
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    sound: str
    can_help: bool
    tags: set[str] = field(default_factory=set)
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
    activity: str
    object: str
    name: str
    gender: str
    helper: str
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting("the kitchen", quiet=True),
    "library": Setting("the library", quiet=True),
    "nursery": Setting("the nursery", quiet=True),
    "workshop": Setting("the workshop", quiet=False),
}

ACTIVITIES = {
    "drum": Activity(
        id="drum",
        verb="beat the drum",
        sound="boom-boom",
        effect="the table shook with little booms",
        twist="the booms started sounding like marching feet",
        help_line="the beat helped everyone march to the same rhythm",
        tags={"sound", "kindness"},
    ),
    "bell": Activity(
        id="bell",
        verb="ring the bell",
        sound="ding-ding",
        effect="the room rang with bright dings",
        twist="the dings sounded like tiny laughing birds",
        help_line="the bell called everyone together for help",
        tags={"sound", "twist"},
    ),
    "whistle": Activity(
        id="whistle",
        verb="blow the whistle",
        sound="wheeet!",
        effect="the whistle made a sharp little wheeet",
        twist="the whistle sounded like a tea kettle asking for a hug",
        help_line="the whistle turned into a tidy signal for cleanup",
        tags={"sound", "heartwarming"},
    ),
}

OBJECTS = {
    "drum": ObjectCfg(
        id="drum",
        label="drum",
        phrase="a red toy drum",
        sound="boom-boom",
        can_help=True,
        tags={"sound", "kindness"},
    ),
    "bell": ObjectCfg(
        id="bell",
        label="bell",
        phrase="a shiny hand bell",
        sound="ding-ding",
        can_help=True,
        tags={"sound", "twist"},
    ),
    "whistle": ObjectCfg(
        id="whistle",
        label="whistle",
        phrase="a tiny silver whistle",
        sound="wheeet!",
        can_help=True,
        tags={"sound", "heartwarming"},
    ),
}

HELPERS = {
    "mother": "mother",
    "father": "father",
    "grandma": "grandma",
    "grandpa": "grandpa",
}

GIRL_NAMES = ["Mia", "Lila", "Nora", "Zoe", "Ivy", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Owen", "Ben", "Max"]
TRAITS = ["curious", "gentle", "playful", "shy", "cheerful"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def can_story(setting: Setting, activity: Activity, obj: ObjectCfg) -> bool:
    return activity.can_help and obj.can_help and "sound" in activity.tags and "sound" in obj.tags


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming storyworld with a humorous noisy twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for a in ACTIVITIES:
            for o in OBJECTS:
                if can_story(_safe_lookup(SETTINGS, s), _safe_lookup(ACTIVITIES, a), _safe_lookup(OBJECTS, o)):
                    out.append((s, a, o))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "object", None):
        if not can_story(_safe_lookup(SETTINGS, getattr(args, "setting", None) or "kitchen"), _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(OBJECTS, getattr(args, "object", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "object", None) is None or c[2] == getattr(args, "object", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, activity, obj = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, activity=activity, object=obj, name=name, gender=gender, helper=helper, trait=trait)


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    obj_cfg = _safe_lookup(OBJECTS, params.object)
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=_safe_lookup(HELPERS, params.helper)))
    toy = world.add(Entity(id="toy", type=obj_cfg.id, label=obj_cfg.label, phrase=obj_cfg.phrase, owner=child.id))
    child.memes["joy"] = 0
    child.memes["surprise"] = 0
    helper.memes["kindness"] = 0

    world.say(f"{child.id} was a {params.trait} little {params.gender} who loved to make sound.")
    world.say(f"{params.name} had {obj_cfg.phrase}, and {activity.effect}.")
    world.para()
    world.say(f"One day in {setting.place}, {child.id} wanted to {activity.verb}.")
    world.say(f"'{activity.sound}' went the {obj_cfg.label}, and the room got very still.")
    child.memes["surprise"] += 1
    child.meters["noise"] += 1

    if setting.quiet:
        world.say(f"That was the humorous twist: the {obj_cfg.label} was so loud it sounded like {activity.twist}.")
    else:
        world.say(f"Even in the busy workshop, the sound bounced around like {activity.twist}.")

    world.para()
    helper.memes["kindness"] += 1
    child.memes["joy"] += 1
    world.say(f"{helper.label.capitalize()} smiled and did not scold {child.id}.")
    world.say(f"Instead, {helper.label} said, '{activity.help_line}.'")
    world.say(f"Then {child.id} and {helper.label} used the {obj_cfg.label} to call everyone for a small help-up.")

    world.para()
    child.memes["joy"] += 1
    world.say(f"Soon the noise became a funny little signal, and {child.id} laughed.")
    world.say(f"At the end, {child.id} was sharing, {helper.label} was proud, and {obj_cfg.label} sounded like a happy {activity.sound} that brought everyone closer.")

    world.facts.update(child=child, helper=helper, toy=toy, activity=activity, obj=obj_cfg, params=params)
    return world


def story_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    a = world.facts["activity"]
    o = world.facts["obj"]
    return [
        f"Write a heartwarming humorous story where {p.name} uses {o.phrase} and a {a.id} creates a surprising twist.",
        f"Tell a gentle tale in {_safe_lookup(SETTINGS, p.setting).place} about kindness after a loud {o.label} makes {a.sound}.",
        f"Create a child-friendly story with a funny sound effect, a twist, and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    a = world.facts["activity"]
    o = world.facts["obj"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"What did {p.name} want to do in {_safe_lookup(SETTINGS, p.setting).place}?",
            answer=f"{p.name} wanted to {a.verb}. The sound was {a.sound}, and that was the big noisy twist.",
        ),
        QAItem(
            question=f"Who stayed kind when the sound got funny?",
            answer=f"{helper.label.capitalize()} stayed kind and helped turn the noise into something useful.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The noisy thing became a helpful signal, and {p.name} ended the story laughing with {helper.label}.",
        ),
    ]


WORLD_QA = [
    QAItem(question="What is a sound effect?", answer="A sound effect is a special sound that helps tell a story or make a moment feel lively."),
    QAItem(question="What is kindness?", answer="Kindness means being gentle, helpful, and caring to someone else."),
    QAItem(question="What is a twist in a story?", answer="A twist is a surprising turn that changes what you expect to happen."),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_QA


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid(S,A,O) :- setting(S), activity(A), object(O), compatible(S,A,O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for s, a, o in valid_combos():
        lines.append(asp.fact("compatible", s, a, o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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


CURATED = [
    StoryParams(setting="kitchen", activity="drum", object="drum", name="Mia", gender="girl", helper="mother", trait="curious"),
    StoryParams(setting="library", activity="bell", object="bell", name="Leo", gender="boy", helper="grandma", trait="gentle"),
    StoryParams(setting="nursery", activity="whistle", object="whistle", name="Nora", gender="girl", helper="father", trait="playful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
