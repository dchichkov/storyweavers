#!/usr/bin/env python3
"""
A small animal-story world about a beach day, a wave emergency, and a
reconciliation with sound effects.

The seed idea:
- An animal is having a happy seaside day.
- A big wave creates an emergency and causes a messy accident.
- A helper animal and the main animal fall into a brief disagreement.
- They reconcile, clean up, and end on a calmer, happier image.

This world models:
- physical meters: splash, mess, distance, clean, damage, wetness
- emotional memes: fear, worry, anger, kindness, relief, friendship

The child-facing story stays concrete and state-driven, with sound effects
used as narrative instruments.
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
# Shared world constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

ANIMAL_KINDS = {
    "fox": {"pronoun": "he", "possessive": "his"},
    "rabbit": {"pronoun": "she", "possessive": "her"},
    "bear": {"pronoun": "he", "possessive": "his"},
    "cat": {"pronoun": "she", "possessive": "her"},
    "dog": {"pronoun": "he", "possessive": "his"},
    "otter": {"pronoun": "they", "possessive": "their"},
}

PLACES = {
    "beach": {
        "label": "the beach",
        "sound": "whish",
        "affords": {"wave", "sandcastle", "shells"},
    },
    "riverbank": {
        "label": "the riverbank",
        "sound": "splash",
        "affords": {"wave", "stone-throwing", "mud"},
    },
}

ACTIONS = {
    "wave": {
        "verb": "watch the wave",
        "gerund": "watching the waves",
        "rush": "run toward the water",
        "risk": "wet and messy",
        "mess": "wet",
        "zone": {"feet", "fur"},
        "sound": "whoooosh",
        "problem": "a big wave rushed high onto the sand",
        "keyword": "wave",
        "tags": {"wave", "wet", "emergency"},
    },
    "mud": {
        "verb": "splash in the mud",
        "gerund": "splashing in the mud",
        "rush": "run toward the muddy bank",
        "risk": "muddy",
        "mess": "muddy",
        "zone": {"feet", "fur"},
        "sound": "splat",
        "problem": "a muddy splash flew everywhere",
        "keyword": "mud",
        "tags": {"mud"},
    },
    "shells": {
        "verb": "sort the shells",
        "gerund": "sorting shells",
        "rush": "scamper for the bright shells",
        "risk": "scattered",
        "mess": "scattered",
        "zone": {"paws"},
        "sound": "click-clack",
        "problem": "the shells skittered all over the sand",
        "keyword": "shells",
        "tags": {"shells"},
    },
}

SUPPORT_TOOLS = {
    "bucket": {
        "label": "a little bucket",
        "helps": {"wet", "muddy"},
        "prep": "grab a little bucket and help scoop water away",
        "tail": "carried the bucket back and forth until the sand was safe",
    },
    "towel": {
        "label": "a big towel",
        "helps": {"wet", "muddy"},
        "prep": "wrap the child in a big towel and dry their fur",
        "tail": "patted the sand dry with the big towel",
    },
    "shell_net": {
        "label": "a shell net",
        "helps": {"scattered"},
        "prep": "use a shell net to gather the shells",
        "tail": "gathered every shell back into one happy pile",
    },
}

HERO_NAMES = ["Milo", "Tilly", "Pip", "Nori", "Bram", "Mimi", "Penny", "Ollie"]
HELPER_NAMES = ["Pip", "Luna", "Moss", "Toby", "June", "Bea", "Clover", "Sage"]


# ---------------------------------------------------------------------------
# Dataclasses
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
class StoryParams:
    place: str
    action: str
    hero_name: str
    hero_kind: str
    helper_name: str
    helper_kind: str
    seed: Optional[int] = None
    params: object | None = None
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    owner: Optional[str] = None
    carries: Optional[str] = None

    helper: object | None = None
    hero: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type == "otter":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        data = ANIMAL_KINDS.get(self.type, {"pronoun": "it", "possessive": "its"})
        if data["pronoun"] == "they":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {
            "subject": data["pronoun"],
            "object": "him" if data["pronoun"] == "he" else "her",
            "possessive": data["possessive"],
        }[case]
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


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        cur: list[str] = []
        for line in self.lines:
            if line == "":
                if cur:
                    out.append(" ".join(cur))
                    cur = []
            else:
                cur.append(line)
        if cur:
            out.append(" ".join(cur))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sound_effect(label: str) -> str:
    return {
        "wave": "WHOOOOSH!",
        "mud": "SPLAT!",
        "shells": "click-clack!",
        "emergency": "Help! Help!",
        "reconcile": "softly, softly...",
    }.get(label, "pop!")


def place_label(place: str) -> str:
    return _safe_lookup(PLACES, place)["label"]


def animal_phrase(kind: str, name: str) -> str:
    return f"{name} the {kind}"


def is_reasonable(place: str, action: str) -> bool:
    return action in _safe_lookup(PLACES, place)["affords"]


def compatible_tool(action: str) -> Optional[str]:
    for tool_id, tool in SUPPORT_TOOLS.items():
        if _safe_lookup(ACTIONS, action)["mess"] in tool["helps"]:
            return tool_id
    return None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Place supports action.
valid(Place, Action) :- affords(Place, Action).

% A tool is compatible if it helps with the action's mess.
compatible(Tool, Action) :- helps(Tool, Mess), mess_of(Action, Mess).

% A story is workable when the place supports the action and some tool helps.
workable(Place, Action) :- valid(Place, Action), compatible(_, Action).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for act in sorted(place["affords"]):
            lines.append(asp.fact("affords", place_id, act))
    for action_id, action in ACTIONS.items():
        lines.append(asp.fact("action", action_id))
        lines.append(asp.fact("mess_of", action_id, action["mess"]))
    for tool_id, tool in SUPPORT_TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for mess in sorted(tool["helps"]):
            lines.append(asp.fact("helps", tool_id, mess))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_workable() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show workable/2."))
    return sorted(set(asp.atoms(model, "workable")))


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for action in ACTIONS:
            if is_reasonable(place, action) and compatible_tool(action):
                combos.append((place, action))
    return combos


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_workable())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} workable combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def run_emergency(world: World, hero: Entity, helper: Entity, action_id: str) -> None:
    action = _safe_lookup(ACTIONS, action_id)
    hero.meters[action["mess"]] = hero.meters.get(action["mess"], 0.0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"{sound_effect('emergency')} A big emergency wave came rushing in, "
        f"and {animal_phrase(hero.type, hero.id)} got {action['problem']}."
    )
    world.say(
        f"{hero.id} went still for a moment, because {hero.pronoun('possessive')} "
        f"paws were wet and the sand was not safe anymore."
    )
    helper.memes["worry"] = helper.memes.get("worry", 0.0) + 1


def conflict(world: World, hero: Entity, helper: Entity, action_id: str) -> None:
    action = _safe_lookup(ACTIONS, action_id)
    hero.memes["anger"] = hero.memes.get("anger", 0.0) + 1
    world.say(
        f"{hero.id} wanted to keep playing, but {helper.id} said, "
        f'"No more, not until the emergency is under control."'
    )
    world.say(
        f"{hero.id} scuffed the sand and tried to {action['rush']}, "
        f"but {helper.id} gently stepped in front."
    )
    world.say(
        f"The beach sounded loud with {action['sound']} and the crash of water."
    )


def reconcile(world: World, hero: Entity, helper: Entity, action_id: str) -> Optional[Entity]:
    tool_id = compatible_tool(action_id)
    if tool_id is None:
        return None
    tool_def = _safe_lookup(SUPPORT_TOOLS, tool_id)
    action = _safe_lookup(ACTIONS, action_id)

    tool = world.add(Entity(
        id=tool_id,
        kind="tool",
        type="tool",
        label=tool_def["label"],
        owner=helper.id,
    ))
    helper.carries = tool.id

    hero.memes["anger"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    helper.memes["friendship"] = helper.memes.get("friendship", 0.0) + 1

    world.say(
        f"Then {helper.id} took a breath and said, "
        f'"{tool_def["prep"].capitalize()}."'
    )
    world.say(
        f"{sound_effect('reconcile')} {hero.id} looked at {helper.id}, and the tight feeling "
        f"in {hero.pronoun('possessive')} chest got smaller."
    )
    world.say(
        f"{hero.id} nodded. {helper.id} nodded back. Together they used the {tool.label} "
        f"until the danger was gone."
    )

    hero.meters["clean"] = hero.meters.get("clean", 0.0) + 1
    hero.meters[action["mess"]] = 0.0
    world.say(
        f"In the end, {helper.id} {tool_def['tail']}, and {hero.id} was dry enough to smile again."
    )
    return tool


def tell_story(params: StoryParams) -> World:
    world = World(params.place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_kind))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_kind))
    world.facts.update(params=params, hero=hero, helper=helper, action=params.action, place=params.place)

    action = _safe_lookup(ACTIONS, params.action)
    world.say(
        f"One bright day at {place_label(params.place)}, {animal_phrase(hero.type, hero.id)} "
        f"and {animal_phrase(helper.type, helper.id)} were close friends."
    )
    world.say(
        f"{hero.id} loved {action['gerund']}, and the little beach felt happy and busy."
    )
    world.say(
        f"Everything changed when {sound_effect('wave')} a tall wave rolled in."
    )

    world.para()
    run_emergency(world, hero, helper, params.action)
    conflict(world, hero, helper, params.action)

    world.para()
    tool = reconcile(world, hero, helper, params.action)
    world.facts["tool"] = tool
    world.facts["resolved"] = tool is not None
    world.facts["action_def"] = action
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    action = _safe_lookup(ACTIONS, p.action)
    return [
        f"Write an animal story about a {p.hero_kind} and a wave emergency at {place_label(p.place)}.",
        f"Tell a gentle story where {p.hero_name} the {p.hero_kind} gets caught in a {action['keyword']} emergency and then reconciles with {p.helper_name}.",
        f"Write a short story with sound effects like 'WHOOOOSH' and 'SPLAT' about friends solving a beach problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    action = _safe_lookup(ACTIONS, p.action)
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    tool = _safe_fact(world, world.facts, "tool")
    qa = [
        QAItem(
            question=f"Where did {p.hero_name} and {p.helper_name} spend the day?",
            answer=f"They spent the day at {place_label(p.place)}.",
        ),
        QAItem(
            question=f"What emergency happened while {p.hero_name} was playing?",
            answer=f"A big wave rushed in and made an emergency on the sand.",
        ),
        QAItem(
            question=f"What sound told readers that the wave was coming?",
            answer="The story used the sound effect WHOOOOSH to show the wave.",
        ),
        QAItem(
            question=f"How did {p.helper_name} help after the mess?",
            answer=f"{p.helper_name} used {tool.label if tool else 'a helpful tool'} to clean up and calm the situation.",
        ),
        QAItem(
            question=f"How did the friends feel at the end?",
            answer=f"They felt calm again, and their friendship was stronger after they reconciled.",
        ),
    ]
    if hero.memes.get("fear", 0.0) >= THRESHOLD:
        qa.append(QAItem(
            question=f"Why was {p.hero_name} upset at first?",
            answer=f"{p.hero_name} was upset because the wave emergency made the beach messy and unsafe.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    action = _safe_lookup(ACTIONS, p.action)
    out = [
        QAItem(
            question="What is a wave?",
            answer="A wave is moving water that rises and rolls across the sea or shore.",
        ),
        QAItem(
            question="What does an emergency mean?",
            answer="An emergency is a sudden problem that needs quick help.",
        ),
        QAItem(
            question="Why do sound effects help stories?",
            answer="Sound effects help a story feel lively by showing what something sounds like.",
        ),
    ]
    if "wave" in action["tags"]:
        out.append(QAItem(
            question="Why do waves sometimes make a beach messy?",
            answer="Big waves can splash water and sand far away, which makes a beach wet and messy.",
        ))
    if world.facts.get("tool"):
        out.append(QAItem(
            question="Why can a towel help after a splash?",
            answer="A towel can dry wet fur and make a helper feel cared for.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.carries:
            bits.append(f"carries={e.carries}")
        lines.append(f"{e.id} ({e.type}): " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------

@dataclass
class _Registry:
    pass
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with a wave emergency and reconciliation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--action", choices=sorted(ACTIONS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-kind", choices=sorted(ANIMAL_KINDS))
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-kind", choices=sorted(ANIMAL_KINDS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    action = getattr(args, "action", None) or rng.choice(list(ACTIONS))
    if not is_reasonable(place, action):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if compatible_tool(action) is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_kind = getattr(args, "hero_kind", None) or rng.choice(list(ANIMAL_KINDS))
    helper_kind = getattr(args, "helper_kind", None) or rng.choice(list(ANIMAL_KINDS))
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        action=action,
        hero_name=hero_name,
        hero_kind=hero_kind,
        helper_name=helper_name,
        helper_kind=helper_kind,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show workable/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_workable()
        print(f"{len(combos)} workable combos:")
        for place, action in combos:
            print(f"  {place:12} {action}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = []
        for place in PLACES:
            for action in ACTIONS:
                if is_reasonable(place, action) and compatible_tool(action):
                    curated.append((place, action))
        for i, (place, action) in enumerate(curated):
            params = StoryParams(
                place=place,
                action=action,
                hero_name=_safe_lookup(HERO_NAMES, i % len(HERO_NAMES)),
                hero_kind=list(ANIMAL_KINDS)[i % len(ANIMAL_KINDS)],
                helper_name=_safe_lookup(HELPER_NAMES, i % len(HELPER_NAMES)),
                helper_kind=list(ANIMAL_KINDS)[(i + 3) % len(ANIMAL_KINDS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
