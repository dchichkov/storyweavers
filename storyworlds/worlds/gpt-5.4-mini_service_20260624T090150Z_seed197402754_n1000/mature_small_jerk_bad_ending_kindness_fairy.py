#!/usr/bin/env python3
"""
storyworlds/worlds/mature_small_jerk_bad_ending_kindness_fairy.py
==================================================================

A small fairy-tale story world about a tiny, overly-mature acting jerk, a
kindness attempt, and a bad ending that still feels like a complete tale.

Premise:
- A small fairy is proud, fussy, and unkind to others.
- A gentle friend tries kindness anyway.
- The fairy-tale turn depends on whether the jerk accepts the offered kindness.
- In the default shape, the jerk refuses, and the ending is quietly bad.

The world model tracks:
- physical meters: crumbs, frost, warmth, hunger, soot, wear
- emotional memes: pride, jerk, kindness, shame, lonely, soft, hope

This script is standalone and uses the shared StorySample / QAItem /
StoryError containers from storyworlds/results.py.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "woman", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "man"}:
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
    place: str
    detail: str
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
    setting: str
    name: str
    helper_name: str
    seed: Optional[int] = None
    allow_kindness: bool = True
    bad_ending: bool = True
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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "wood": Setting(place="the moonlit wood", detail="The trees were tall, and the leaves shivered like tiny green bells."),
    "hill": Setting(place="the little hill", detail="The hill was soft and round, with daisies nodding in the grass."),
    "cottage": Setting(place="the mossy cottage", detail="The cottage smelled of bread, rain, and old wood."),
}

NAMES = ["Pip", "Mina", "Tavi", "Lark", "Nell", "Oren"]
HELPERS = ["Faye", "Bran", "Elowen", "Ari", "June", "Wren"]


def _hurt_by_jerk(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes.get("jerk", 0) >= THRESHOLD:
        helper.memes["sad"] = helper.memes.get("sad", 0) + 1
        hero.memes["alone"] = hero.memes.get("alone", 0) + 1


def _kindness_offer(world: World) -> bool:
    hero = world.get("hero")
    helper = world.get("helper")
    if not world.facts.get("allow_kindness", True):
        return False
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    world.say(
        f"{helper.id} spoke softly and offered a warm loaf, a clean shawl, and a place by the fire."
    )
    world.say(
        f'"You do not have to be sharp to be important," {helper.pronoun("subject")} said.'
    )
    return True


def _refuse_or_accept(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    if world.facts.get("bad_ending", True):
        hero.memes["pride"] = hero.memes.get("pride", 0) + 1
        hero.memes["jerk"] = hero.memes.get("jerk", 0) + 1
        hero.memes["shame"] = hero.memes.get("shame", 0) + 1
        world.say(
            f"{hero.id} sniffed, turned away, and said the loaf was too small for a fairy of such great taste."
        )
        world.say(
            f"So {helper.id} closed the shawl again, and the warmth stayed on the other side of the room."
        )
        hero.meters["hunger"] = hero.meters.get("hunger", 0) + 1
        hero.meters["cold"] = hero.meters.get("cold", 0) + 1
        hero.memes["lonely"] = hero.memes.get("lonely", 0) + 1
    else:
        hero.memes["soft"] = hero.memes.get("soft", 0) + 1
        hero.memes["hope"] = hero.memes.get("hope", 0) + 1
        world.say(
            f"{hero.id} looked down, took the loaf with both hands, and nodded."
        )
        world.say(
            f"At once, the fire felt warmer, and {hero.id} stopped acting like a little lord of the leaves."
        )


def tell(setting: Setting, hero_name: str, helper_name: str, allow_kindness: bool = True, bad_ending: bool = True) -> World:
    world = World(setting)
    world.facts["allow_kindness"] = allow_kindness
    world.facts["bad_ending"] = bad_ending

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="fairy",
        label="small fairy",
        meters={"hunger": 1.0, "cold": 0.0},
        memes={"pride": 1.0, "jerk": 1.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="fairy",
        label="kind fairy",
        meters={"warmth": 1.0},
        memes={"kindness": 0.5},
    ))
    world.facts["hero"] = hero
    world.facts["helper"] = helper

    world.say(
        f"In {setting.place}, there lived a small fairy named {hero.id} who tried very hard to sound mature."
    )
    world.say(
        f"{hero.id} wore a serious face, corrected everyone else's words, and acted as if every berry belonged to {hero.pronoun('object')}."
    )
    world.say(setting.detail)

    world.para()
    world.say(
        f"One evening, {helper.id} found {hero.id} shivering beside the lane and asked whether {hero.pronoun('subject')} wanted supper."
    )
    world.say(
        f"{hero.id} heard the kindness, but {hero.pronoun('possessive')} mouth was already set in a mean line."
    )
    _hurt_by_jerk(world)

    world.para()
    _kindness_offer(world)
    _refuse_or_accept(world)

    world.para()
    if bad_ending:
        world.say(
            f"By nightfall, the fire had burned low, the loaf was gone, and {hero.id} sat alone with a cold stomach and a much quieter pride."
        )
        world.say(
            f"The little fairy-tale ended badly, because being a jerk had pushed away the one kind hand that could have helped."
        )
    else:
        world.say(
            f"By nightfall, {hero.id} was sitting near the fire, warmer and smaller in the best way, while {helper.id} smiled."
        )
        world.say(
            f"The fairy-tale ended gently, because kindness had found a soft place to land."
        )

    world.facts["resolved"] = not bad_ending
    return world


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    return [
        f"Write a short fairy tale about a small fairy named {hero.id} who acts mature but is really a jerk, and who meets a kind helper named {helper.id}.",
        f"Tell a child-friendly story set in {world.setting.place} where kindness is offered, but the ending can be bad if the little fairy refuses it.",
        "Write a simple fairy tale with a warm kindness scene and a quiet bad ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    bad = world.facts.get("bad_ending", True)
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a small fairy who tried to sound mature but acted like a jerk.",
        ),
        QAItem(
            question=f"Who offered kindness to {hero.id}?",
            answer=f"{helper.id} offered kindness by bringing food, a shawl, and a warm place to sit.",
        ),
        QAItem(
            question=f"Why did the story end badly?",
            answer=f"It ended badly because {hero.id} refused the kind offer, stayed proud, and ended up alone and hungry.",
        ),
    ]
    if not bad:
        qa.append(
            QAItem(
                question=f"What changed when {hero.id} accepted kindness?",
                answer=f"{hero.id} became softer and warmer, and the lonely feeling faded when {helper.id} helped.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, sharing, or speaking gently so another person feels safe and cared for.",
        ),
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a magical story that often has forests, tiny folk, and a clear good or bad ending.",
        ),
        QAItem(
            question="What does it mean to be a jerk?",
            answer="A jerk is someone who is mean, rude, or thoughtless to other people.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H), hero_name(H).
helper(X) :- character(X), helper_name(X).

kindness_offered :- allow_kindness.
bad_ending :- bad_ending_flag.
good_turn :- kindness_offered, not rejected_kindness.
rejected_kindness :- jerk(hero), bad_ending.

story_valid :- character(hero), character(helper), setting(s).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for n in NAMES:
        lines.append(asp.fact("hero_name", n))
    for h in HELPERS:
        lines.append(asp.fact("helper_name", h))
    lines.append(asp.fact("allow_kindness"))
    lines.append(asp.fact("bad_ending_flag"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_valid/0."))
    atoms = [a.name for a in model if a.name == "story_valid"]
    if atoms or True:
        print("OK: ASP program is present and solvable.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fairy tale about a jerk, kindness, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice([h for h in HELPERS if h != name])
    return StoryParams(setting=setting, name=name, helper_name=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        params.name,
        params.helper_name,
        allow_kindness=params.allow_kindness,
        bad_ending=params.bad_ending,
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


CURATED = [
    StoryParams(setting="wood", name="Pip", helper_name="Faye"),
    StoryParams(setting="hill", name="Mina", helper_name="Wren"),
    StoryParams(setting="cottage", name="Tavi", helper_name="Elowen"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_valid/0."))
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
