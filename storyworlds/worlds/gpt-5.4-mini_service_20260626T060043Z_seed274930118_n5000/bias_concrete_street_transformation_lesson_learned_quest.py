#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bias_concrete_street_transformation_lesson_learned_quest.py
====================================================================================================

A standalone storyworld about a space-adventure-style quest on a concrete street,
where a child learns not to trust bias, and a small transformation helps finish
the mission.

Seed tale inspiration:
---
A kid on a concrete street wants to reach the old hilltop observatory before sunset.
They assume the rusty delivery bot is useless because it looks odd and clanky, but
the bot knows a shortcut, and the kid learns that first impressions can be biased.
Together, they transform a plain cart into a tiny star-rider and complete the quest.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)
    transformed: bool = False

    cart: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the concrete street"
    skyline: str = "the city lights"
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
class Quest:
    id: str
    goal: str
    prompt: str
    turn: str
    resolution: str
    clue: str
    tag: str
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
class TransformKit:
    id: str
    label: str
    phrase: str
    effect: str
    ready_line: str
    result_line: str
    tag: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
SETTINGS = {
    "street": Setting(place="the concrete street", skyline="the moonlit towers", affords={"quest", "transform"}),
}

QUESTS = {
    "star_map": Quest(
        id="star_map",
        goal="reach the hilltop observatory with the lost star map",
        prompt="find the missing star map before the sky turns dark",
        turn="a clanky helper knows a shortcut under the old rail bridge",
        resolution="the team reaches the observatory in time",
        clue="a blinking beacon hidden near the curb",
        tag="quest",
    ),
}

TRANSFORMS = {
    "star_cart": TransformKit(
        id="star_cart",
        label="a small cart",
        phrase="a plain little cart with squeaky wheels",
        effect="turn it into a shiny star-rider",
        ready_line="They taped on bright panels, clicked on a lantern, and fixed the wheels.",
        result_line="The cart now gleamed like a tiny rocket on the street.",
        tag="transform",
    ),
}

TRAITS = ["curious", "bold", "gentle", "brave", "spirited"]
NAMES = ["Maya", "Nico", "Lena", "Tobi", "Iris", "Owen", "Zara", "Milo"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    quest: str
    transform: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
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


def valid_combo(setting: Setting, quest: Quest, kit: TransformKit) -> bool:
    return quest.tag in setting.affords and kit.tag in setting.affords


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for qid, q in QUESTS.items():
            for tid, t in TRANSFORMS.items():
                if valid_combo(s, q, t):
                    out.append((sid, qid, tid))
    return out


def explain_rejection(setting: Setting, quest: Quest, kit: TransformKit) -> str:
    return (
        f"(No story: the setting {setting.place} does not support both a quest and a "
        f"transformation that can finish this space-adventure cleanly.)"
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'curious')} child who loved looking up at "
        f"{world.setting.skyline} from {world.setting.place}."
    )


def desire(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} wanted to {quest.prompt}, because the observatory above the street "
        f"could only open while the sky was still bright."
    )


def bias_turn(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["bias"] += 1
    world.say(
        f"When {helper.id} rolled up with a bent frame and a noisy wheel, {hero.id} almost "
        f"thought it was useless. That was a kind of bias, because the helper looked old "
        f"but still had a sharp map in {helper.pronoun('possessive')} head."
    )


def quest_call(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    world.say(
        f"{helper.id} pointed to {quest.clue} near the curb and said, "
        f'"{quest.turn}."'
    )
    hero.memes["curiosity"] += 1
    world.say(
        f"So {hero.id} followed the clue along the concrete street, where every cracked "
        f"line looked like a path between stars."
    )


def transform(world: World, hero: Entity, kit: TransformKit) -> None:
    cart = world.get("cart")
    cart.transformed = True
    cart.label = "star-rider"
    cart.phrase = "a shiny star-rider"
    hero.meters["work"] = hero.meters.get("work", 0.0) + 1.0
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1.0
    world.say(kit.ready_line)
    world.say(
        f"{kit.effect.capitalize()}. {kit.result_line} Now the little vehicle looked ready "
        f"for a launch instead of a sidewalk ride."
    )


def resolution(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["bias"] = 0.0
    world.say(
        f"Together they reached the hilltop observatory just in time. {quest.resolution.capitalize()}, "
        f"and {hero.id} finally understood that a smart helper can look rough on the outside."
    )
    world.say(
        f"{hero.id} smiled at {helper.id} and promised not to judge the next traveler by first glance."
    )


def tell(setting: Setting, quest: Quest, kit: TransformKit, hero_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", memes={"trait": trait}))
    helper = world.add(Entity(id="Rollo", kind="character", type="robot", label="Rollo"))
    cart = world.add(Entity(id="cart", type="cart", label="cart", phrase=kit.phrase))
    world.facts.update(hero=hero, helper=helper, cart=cart, quest=quest, kit=kit, setting=setting)

    introduce(world, hero)
    world.para()
    desire(world, hero, quest)
    bias_turn(world, hero, helper)
    quest_call(world, hero, helper, quest)
    world.para()
    transform(world, hero, kit)
    resolution(world, hero, helper, quest)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, quest, kit = f["hero"], f["quest"], f["kit"]
    return [
        f'Write a space-adventure-style story for a young child about {hero.id} on a concrete street, with a quest and a transformation.',
        f'Write a short story where a child named {hero.id} learns that bias can be wrong when a helper with a rough look shows hidden skill.',
        f'Write a gentle quest story where a plain cart becomes a star-rider before the observatory opens.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, quest, kit = f["hero"], f["helper"], f["quest"], f["kit"]
    return [
        QAItem(
            question=f"Where was {hero.id} starting the adventure?",
            answer=f"{hero.id} started on the concrete street, under the glow of the city lights.",
        ),
        QAItem(
            question=f"What was {hero.id} trying to do on the quest?",
            answer=f"{hero.id} wanted to {quest.prompt}, so the lost star map could help them reach the observatory.",
        ),
        QAItem(
            question=f"Why did {hero.id} have to change their mind about {helper.id}?",
            answer=(
                f"{hero.id} first showed bias because {helper.id} looked clanky and old, "
                f"but {helper.id} still knew the shortcut and guided the quest well."
            ),
        ),
        QAItem(
            question=f"What transformed during the story?",
            answer=(
                f"{kit.phrase.capitalize()} transformed into a shiny star-rider, which helped the team move fast."
            ),
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn by the end?",
            answer=(
                f"{hero.id} learned that first impressions can be biased and that a helpful friend "
                f"may not look heroic at first."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a concrete street?",
            answer="A concrete street is a hard road made of concrete where cars, bikes, and people can travel.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to find something important or finish a special goal.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new form or becomes very different.",
        ),
        QAItem(
            question="What does bias mean?",
            answer="Bias means judging too quickly before you really know someone or something.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting_ok(S) :- setting(S).
quest_ok(Q) :- quest(Q).
kit_ok(T) :- kit(T).

valid_story(S,Q,T) :- setting_ok(S), quest_ok(Q), kit_ok(T),
                      affords(S, quest), affords(S, transform).

bias_learned(S,Q,T) :- valid_story(S,Q,T).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for tid in TRANSFORMS:
        lines.append(asp.fact("kit", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A space-adventure quest on a concrete street.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--name", choices=NAMES)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "transform", None) is None or c[2] == getattr(args, "transform", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, quest, transform = rng.choice(list(combos))
    return StoryParams(
        setting=setting,
        quest=quest,
        transform=transform,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(QUESTS, params.quest),
        _safe_lookup(TRANSFORMS, params.transform),
        params.name,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for sid, qid, tid in valid_combos():
            params = StoryParams(setting=sid, quest=qid, transform=tid, name=_safe_lookup(NAMES, 0), trait=_safe_lookup(TRAITS, 0))
            samples.append(generate(params))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
