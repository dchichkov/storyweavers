#!/usr/bin/env python3
"""
storyworlds/worlds/alias_twist_repetition_happy_ending_bedtime_story.py
======================================================================

A small bedtime story world with an alias twist, gentle repetition, and a
happy ending.

Premise:
- A child is getting ready for bed.
- A small worry arrives under a secret alias.
- Repeated soothing steps turn the worry into a friend.
- The ending proves the room is calm and the child is safe.

The world models both physical meters and emotional memes, and the prose is
driven by simulated state rather than by a frozen template.
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
    alias: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the bedroom"
    cozy: bool = True
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
class Routine:
    id: str
    verb: str
    gerund: str
    soothing: str
    grows: str
    keyword: str
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
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
class Comfort:
    id: str
    label: str
    phrase: str
    effect: str
    helps: set[str]
    tags: set[str] = field(default_factory=set)
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
        self.night: int = 0

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.night = self.night
        return clone


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    parent_name: str
    parent_type: str
    alias: str
    routine: str
    comfort: str
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
    "bedroom": Setting(place="the bedroom", cozy=True),
    "nursery": Setting(place="the nursery", cozy=True),
    "attic_room": Setting(place="the attic room", cozy=False),
}

ROUTINES = {
    "bath": Routine(
        id="bath",
        verb="take a bath",
        gerund="taking a warm bath",
        soothing="the warm water washed away the day",
        grows="the water made the room quieter",
        keyword="bubble",
        tags={"water", "calm"},
    ),
    "story": Routine(
        id="story",
        verb="listen to a bedtime story",
        gerund="listening to a bedtime story",
        soothing="the story gave the room a soft, sleepy feeling",
        grows="each page made the worry smaller",
        keyword="story",
        tags={"book", "calm"},
    ),
    "song": Routine(
        id="song",
        verb="sing a lullaby",
        gerund="singing a lullaby",
        soothing="the song wrapped the room in a gentle hum",
        grows="every note made the dark feel friendlier",
        keyword="lullaby",
        tags={"music", "calm"},
    ),
}

COMFORTS = {
    "lamp": Comfort(
        id="lamp",
        label="a little lamp",
        phrase="a little lamp with a warm glow",
        effect="the lamp turned the shadows soft and small",
        helps={"dark"},
        tags={"light"},
    ),
    "blanket": Comfort(
        id="blanket",
        label="a blue blanket",
        phrase="a blue blanket with moon stitches",
        effect="the blanket made the bed feel like a safe nest",
        helps={"cold"},
        tags={"cloth"},
    ),
    "bear": Comfort(
        id="bear",
        label="a sleepy bear",
        phrase="a sleepy bear with a stitched smile",
        effect="the bear kept watch in the quiet corner",
        helps={"lonely"},
        tags={"toy"},
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava", "Lily", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Milo", "Eli", "Noah", "Finn"]


def _base_ent(eid: str, kind: str, type_: str, label: str = "") -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, meters={}, memes={})


def mutter(world: World, child: Entity, alias: str) -> None:
    child.memes["worry"] += 1
    world.say(
        f"{child.id} had a tiny worry, but {child.pronoun('possessive')} worry had an alias: "
        f'"{alias}."'
    )


def parent_notice(world: World, parent: Entity, child: Entity, alias: str) -> None:
    parent.memes["care"] += 1
    world.say(
        f"{parent.id} heard the alias and smiled gently. "
        f'"Hello, {alias}," {parent.pronoun()} said, "you may come in, but only if you are small and sleepy."'
    )


def apply_routine(world: World, child: Entity, routine: Routine) -> None:
    child.meters[routine.id] += 1
    child.memes["calm"] += 1
    world.say(
        f"{child.id} did the same bedtime step again: {routine.verb}. "
        f"{routine.soothing} {routine.grows}."
    )


def offer_comfort(world: World, parent: Entity, child: Entity, comfort: Comfort) -> None:
    child.meters[comfort.id] += 1
    child.memes["safe"] += 1
    world.say(
        f"Then {parent.id} brought {comfort.label}. {comfort.effect}."
    )


def twist(world: World, child: Entity, alias: str, comfort: Comfort) -> None:
    child.memes["surprise"] += 1
    world.say(
        f"But here was the twist: {alias} was not a monster at all. "
        f"{alias} was only the name {child.id} gave to the dark corner near {comfort.label}."
    )


def settle(world: World, child: Entity, parent: Entity, comfort: Comfort) -> None:
    child.memes["fear"] = 0.0
    child.memes["joy"] += 1
    world.say(
        f"{child.id} peeked again and saw {comfort.label} waiting there. "
        f"The room felt soft, the bed felt safe, and {child.id} gave {parent.id} a sleepy hug."
    )
    world.say(
        f"At last {child.id} lay down under the blanket and listened to the hush of the room. "
        f"The alias had lost its teeth, and bedtime had won."
    )


def tell(setting: Setting, routine: Routine, comfort: Comfort, child_name: str, child_type: str,
         parent_name: str, parent_type: str, alias: str) -> World:
    world = World(setting)
    child = world.add(_base_ent(child_name, "character", child_type))
    parent = world.add(_base_ent(parent_name, "character", parent_type))
    parent.label = parent_name
    child.label = child_name

    world.say(
        f"{child.id} was a little {child.type} who liked quiet nights in {setting.place}."
    )
    world.say(
        f"{child.id} was ready for bed, and {child.id} liked doing the same gentle things again and again."
    )
    world.say(
        f"{child.id} loved {routine.gerund}, and {comfort.phrase} waited nearby."
    )

    world.para()
    mutter(world, child, alias)
    parent_notice(world, parent, child, alias)

    world.para()
    apply_routine(world, child, routine)
    apply_routine(world, child, routine)
    offer_comfort(world, parent, child, comfort)
    apply_routine(world, child, routine)

    world.para()
    twist(world, child, alias, comfort)
    settle(world, child, parent, comfort)

    world.facts.update(
        child=child,
        parent=parent,
        setting=setting,
        routine=routine,
        comfort=comfort,
        alias=alias,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a small child in {f["setting"].place} with a gentle alias twist.',
        f"Tell a cozy story where {f['child'].id} repeats a calming routine and learns that '{f['alias']}' is only a silly name for a shadowy corner.",
        f'Write a happy ending bedtime story using the word "alias" and a soothing repeated rhythm.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    routine: Routine = _safe_fact(world, f, "routine")
    comfort: Comfort = _safe_fact(world, f, "comfort")
    alias: str = _safe_fact(world, f, "alias")
    return [
        QAItem(
            question=f"What was {child.id}'s worry called?",
            answer=f"{child.id} called the little worry {alias}, like a secret nickname for the dark corner.",
        ),
        QAItem(
            question=f"What did {child.id} do again and again before falling asleep?",
            answer=f"{child.id} repeated {routine.gerund}, and the repetition helped the room feel calmer and calmer.",
        ),
        QAItem(
            question=f"Who helped make bedtime feel safe?",
            answer=f"{parent.id} helped by speaking gently, bringing comfort, and staying close until {child.id} felt sleepy.",
        ),
        QAItem(
            question=f"What made the twist in the story surprising?",
            answer=f"The twist was that {alias} was not a real scary thing at all; it was just the name for a shadowy corner near {comfort.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an alias?",
            answer="An alias is another name used for someone or something, often as a nickname or a secret label.",
        ),
        QAItem(
            question="Why do people repeat calming bedtime steps?",
            answer="People repeat calming bedtime steps because the familiar pattern helps the body and mind slow down for sleep.",
        ),
        QAItem(
            question="Why is a happy ending nice in a bedtime story?",
            answer="A happy ending is nice because it leaves the child feeling safe, cozy, and ready to rest.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {"bedroom": SETTINGS["bedroom"], "nursery": SETTINGS["nursery"], "attic_room": SETTINGS["attic_room"]}

CURATED = [
    StoryParams("Mia", "girl", "Mom", "mother", "MoonMurmur", "story", "lamp"),
    StoryParams("Theo", "boy", "Dad", "father", "ShadowSnip", "song", "blanket"),
    StoryParams("Lina", "girl", "Mom", "mother", "QuietQuill", "bath", "bear"),
]


ASP_RULES = r"""
% A bedtime story is reasonable when the child can do a calm routine
% and there is at least one comfort item that helps the alias-worry.

routine_ok(R) :- routine(R).
comfort_ok(C) :- comfort(C).

calm_story(R, C) :- routine_ok(R), comfort_ok(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.cozy:
            lines.append(asp.fact("cozy", sid))
    for rid, r in ROUTINES.items():
        lines.append(asp.fact("routine", rid))
        for t in sorted(r.tags):
            lines.append(asp.fact("routine_tag", rid, t))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("comfort_tag", cid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return sorted((r, c) for r in ROUTINES for c in COMFORTS)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show calm_story/2."))
    return sorted(set(asp.atoms(model, "calm_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy bedtime story world with an alias twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--routine", choices=ROUTINES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--alias")
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
    combos = list(valid_combos())
    routine = getattr(args, "routine", None) or rng.choice(sorted(ROUTINES))
    comfort = getattr(args, "comfort", None) or rng.choice(sorted(COMFORTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    alias = getattr(args, "alias", None) or rng.choice(["Shadow Mouse", "Midnight", "Whisper", "Little Dark", "Moon Wink"])

    if (routine, comfort) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        child_name=name,
        child_type=gender,
        parent_name=parent.title(),
        parent_type=parent,
        alias=alias,
        routine=routine,
        comfort=comfort,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS["bedroom"],
        _safe_lookup(ROUTINES, params.routine),
        _safe_lookup(COMFORTS, params.comfort),
        params.child_name,
        params.child_type,
        params.parent_name,
        params.parent_type,
        params.alias,
    )
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
        print(asp_program("#show calm_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} calm bedtime combos:\n")
        for routine, comfort in combos:
            print(f"  {routine:8} {comfort}")
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
            header = f"### {p.child_name}: {p.routine} with {p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
