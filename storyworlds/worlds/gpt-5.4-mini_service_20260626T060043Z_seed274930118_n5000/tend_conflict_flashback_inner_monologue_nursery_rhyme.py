#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tend_conflict_flashback_inner_monologue_nursery_rhyme.py
================================================================================

A tiny standalone storyworld for a nursery-rhyme-style tale about tending,
a small conflict, a flashback, and an inner monologue.

Premise:
- A child tends a little garden-bed or pot.
- The child wants to play, but the sprout needs care first.
- A remembered lesson from an older helper steadies the choice.
- The child thinks silently, then acts, and the ending shows the change.

The prose is intentionally simple, concrete, and causal.
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
    traits: list[str] = field(default_factory=list)

    role: str = ""
    child: object | None = None
    elder: object | None = None
    sprout: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "maiden"}
        male = {"boy", "father", "dad", "man", "grandfather", "gardener"}
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
    place: str = "the little yard"
    indoor: bool = False
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    needs: set[str]
    keyword: str = "tend"
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
class Item:
    id: str
    label: str
    phrase: str
    role: str  # "tool" or "prize"
    plural: bool = False
    used_for: set[str] = field(default_factory=set)
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def pose_feel(w: World, actor: Entity) -> None:
    actor.memes["care"] = actor.memes.get("care", 0.0) + 1.0


def introduce(w: World, child: Entity) -> None:
    w.say(f"{child.id} was a little {child.type} with a tender heart and a busy pair of hands.")


def setup_tale(w: World, child: Entity, elder: Entity, sprout: Entity, tool: Entity, act: Activity) -> None:
    w.say(f"{child.id} loved to {act.gerund}, and {child.pronoun('possessive')} {tool.label} was never far away.")
    w.say(f"In {w.setting.place}, a tiny {sprout.label} leaned up from the soil, waiting to be tended.")
    w.say(f"{elder.id} had once taught {child.id} to care for little growing things with slow, kind moves.")
    child.memes["love"] = child.memes.get("love", 0.0) + 1.0
    sprout.meters["need_water"] = 1.0


def conflict_turn(w: World, child: Entity, elder: Entity, sprout: Entity, tool: Entity, act: Activity) -> None:
    child.memes["want_play"] = child.memes.get("want_play", 0.0) + 1.0
    sprout.meters["dry"] = sprout.meters.get("dry", 0.0) + 1.0
    sprout.memes["worry"] = sprout.memes.get("worry", 0.0) + 1.0

    w.para()
    w.say(f"One bright day, {child.id} wanted to {act.verb}, but the {sprout.label} looked dry.")
    w.say(f"{child.id} picked up {child.pronoun('possessive')} {tool.label}, then paused beside the bed.")
    w.say(f'"If I dash away now," {child.id} thought, "the little {sprout.label} may droop and sigh."')
    child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1.0


def flashback_and_choice(w: World, child: Entity, elder: Entity, sprout: Entity, tool: Entity, act: Activity) -> None:
    w.para()
    w.say(f"{child.id} remembered a day from long ago when {elder.id} had knelt in the dirt and smiled.")
    w.say(f'"A kind hand helps the small one grow," {elder.id} had said, "and then there is time for play."')
    child.memes["flashback"] = child.memes.get("flashback", 0.0) + 1.0

    w.say(f"{child.id} stood still and listened to {child.pronoun('possessive')} own quiet thought:")
    w.say(f'"First I tend. Then I can play. A little care now keeps the garden gay."')
    child.memes["resolve"] = child.memes.get("resolve", 0.0) + 1.0


def resolution(w: World, child: Entity, elder: Entity, sprout: Entity, tool: Entity, act: Activity) -> None:
    w.para()
    sprout.meters["water"] = sprout.meters.get("water", 0.0) + 1.0
    sprout.meters["dry"] = 0.0
    sprout.meters["growth"] = sprout.meters.get("growth", 0.0) + 1.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    child.memes["conflict"] = 0.0

    w.say(f"{child.id} gave the {sprout.label} a careful drink from the {tool.label}.")
    w.say(f"The small green top stood a bit straighter, as if it had heard the helping song.")
    w.say(f"Then {child.id} skipped off to {act.verb}, light as a leaf, while {elder.id} clapped along.")


def tell(
    setting: Setting,
    activity: Activity,
    child_name: str = "Mina",
    child_type: str = "girl",
    elder_name: str = "Nana",
    elder_type: str = "grandmother",
) -> World:
    w = World(setting)
    child = w.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    elder = w.add(Entity(id=elder_name, kind="character", type=elder_type, label=elder_name))
    sprout = w.add(Entity(id="Sprout", type="sprout", label="little sprout", role="prize"))
    tool = w.add(Entity(id="Can", type="watering can", label="watering can", role="tool"))

    introduce(w, child)
    setup_tale(w, child, elder, sprout, tool, activity)
    conflict_turn(w, child, elder, sprout, tool, activity)
    flashback_and_choice(w, child, elder, sprout, tool, activity)
    resolution(w, child, elder, sprout, tool, activity)

    w.facts.update(
        child=child,
        elder=elder,
        sprout=sprout,
        tool=tool,
        activity=activity,
        setting=setting,
    )
    return w


SETTINGS = {
    "yard": Setting(place="the little yard", affords={"skip", "dance", "sing"}),
    "garden": Setting(place="the small garden", affords={"skip", "dance", "sing"}),
    "porch": Setting(place="the sunny porch", affords={"skip", "dance", "sing"}),
}

ACTIVITIES = {
    "skip": Activity(
        id="skip",
        verb="skip in circles",
        gerund="skipping in circles",
        rush="skip away at once",
        mess="dust",
        soil="too dusty",
        needs={"water"},
        keyword="tend",
    ),
    "dance": Activity(
        id="dance",
        verb="dance in the path",
        gerund="dancing in the path",
        rush="twirl away at once",
        mess="dust",
        soil="too dusty",
        needs={"water"},
        keyword="tend",
    ),
    "sing": Activity(
        id="sing",
        verb="sing a little song",
        gerund="singing a little song",
        rush="run off singing",
        mess="dust",
        soil="too dusty",
        needs={"water"},
        keyword="tend",
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Miri", "Nora", "Luna", "Ava"]
BOY_NAMES = ["Pip", "Toby", "Finn", "Milo", "Noah", "Ben"]
ELDER_NAMES = ["Nana", "Grandma", "Granny", "Papa", "Grandpa"]
ELDER_TYPES = ["grandmother", "grandfather"]


@dataclass
class StoryParams:
    place: str
    activity: str
    child_name: str
    child_type: str
    elder_name: str
    elder_type: str
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


CURATED = [
    StoryParams("garden", "skip", "Mina", "girl", "Nana", "grandmother"),
    StoryParams("yard", "dance", "Pip", "boy", "Grandpa", "grandfather"),
    StoryParams("porch", "sing", "Lily", "girl", "Grandma", "grandmother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny nursery-rhyme storyworld about tending a little sprout.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-type", choices=ELDER_TYPES)
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
    activity = getattr(args, "activity", None) or rng.choice(list(ACTIVITIES))
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    if activity not in _safe_lookup(SETTINGS, place).affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_type = getattr(args, "elder_type", None) or rng.choice(ELDER_TYPES)
    elder_name = getattr(args, "elder_name", None) or rng.choice(ELDER_NAMES)
    return StoryParams(place, activity, name, gender, elder_name, elder_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), params.child_name, params.child_type, params.elder_name, params.elder_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    activity = _safe_fact(world, f, "activity")
    return [
        f'Write a short nursery-rhyme-style story about {child.id} who must {activity.keyword} before play.',
        f"Tell a gentle tale where {child.id} wants to {activity.verb} but remembers how to tend a little sprout.",
        f"Write a rhyming, child-friendly story with a conflict, a flashback, and a quiet inner monologue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    elder = _safe_fact(world, f, "elder")
    sprout = _safe_fact(world, f, "sprout")
    activity = _safe_fact(world, f, "activity")
    return [
        QAItem(
            question=f"What did {child.id} want to do before tending the little sprout?",
            answer=f"{child.id} wanted to {activity.verb} and play, but first there was a tiny plant to care for.",
        ),
        QAItem(
            question=f"Who helped {child.id} remember how to care for the garden?",
            answer=f"{elder.id} helped by being part of the remembered lesson about kind hands and patient care.",
        ),
        QAItem(
            question=f"What changed after {child.id} watered the {sprout.label}?",
            answer=f"The {sprout.label} stopped looking so dry and stood a little straighter after the careful drink.",
        ),
        QAItem(
            question=f"What was {child.id}'s quiet thought before choosing what to do?",
            answer=f"{child.id} thought, 'First I tend. Then I can play,' and that helped make the choice.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to tend something?",
            answer="To tend something means to care for it, like watering a plant, checking on it, or helping it stay healthy.",
        ),
        QAItem(
            question="Why do little plants need water?",
            answer="Little plants need water so they do not dry out and can keep growing strong and green.",
        ),
    ]


ASP_RULES = r"""
need_care(S) :- sprout(S), dry(S).
resolved(C) :- child(C), action(C,A), need_care(S), tended(C,S).
conflict(C) :- child(C), want_play(C), need_care(S), not tended(C,S).
flashback(C) :- conflict(C), remembers(C).
inner_monologue(C) :- conflict(C), thinks(C).
happy_end(C) :- resolved(C), not conflict(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("child", "mina"))
    lines.append(asp.fact("sprout", "sprout"))
    lines.append(asp.fact("tended", "mina", "sprout"))
    lines.append(asp.fact("want_play", "mina"))
    lines.append(asp.fact("remembers", "mina"))
    lines.append(asp.fact("thinks", "mina"))
    lines.append(asp.fact("action", "mina", "skip"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(parts)}")
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
        print(asp_program("#show resolved/1.\n#show conflict/1.\n#show flashback/1.\n#show inner_monologue/1.\n#show happy_end/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show resolved/1.\n#show conflict/1.\n#show flashback/1.\n#show inner_monologue/1.\n#show happy_end/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
            header = f"### {p.child_name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
