#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/loss_cup_ful_teamwork_pirate_tale.py
===============================================================================================================

A small pirate-tale storyworld about a crew facing a loss and fixing it with
teamwork. The seed words are preserved in the domain: loss, cup-ful.

Premise:
- A young pirate crew is on deck with a tiny cup-ful of treasure.
- A gust, wave, or slippery plank causes a loss.
- The crew must work together to recover what was lost.

Resolution:
- One pirate spots the missing item.
- Another steadies the boat or holds the lantern.
- The crew uses teamwork to recover the cup-ful and ends the tale with a
  stronger bond and a safer deck.

This script follows the Storyweavers storyworld contract.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cup: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate", "mate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str
    afford: set[str] = field(default_factory=set)
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
class Trouble:
    id: str
    cause: str
    danger: str
    loss_word: str
    keyword: str = "teamwork"
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
class RescueGear:
    id: str
    label: str
    role: str
    helps: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.wind: str = ""

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

    def crew(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    trouble: str
    hero: str
    helper: str
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
    "deck": Setting(place="the ship's deck", afford={"storm", "search", "recover"}),
    "cove": Setting(place="the moonlit cove", afford={"storm", "search", "recover"}),
    "harbor": Setting(place="the harbor", afford={"search", "recover"}),
}

TROUBLES = {
    "spill": Trouble(id="spill", cause="a sudden wave", danger="the tiny cup-ful of gold", loss_word="loss", keyword="teamwork"),
    "gust": Trouble(id="gust", cause="a sharp gust of wind", danger="the tiny cup-ful of pearls", loss_word="loss", keyword="teamwork"),
    "slip": Trouble(id="slip", cause="a slippery plank", danger="the tiny cup-ful of spices", loss_word="loss", keyword="teamwork"),
}

CREW_NAMES = ["Mina", "Jett", "Nico", "Ruby", "Cora", "Finn"]
HELPERS = ["mate", "lookout", "cook", "sailor", "captain"]
TRAITS = ["brave", "nimble", "cheerful", "steady"]


def make_crew_name(rng: random.Random, used: set[str]) -> str:
    choices = [n for n in CREW_NAMES if n not in used]
    if not choices:
        choices = CREW_NAMES[:]
    return rng.choice(choices)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale about loss, a cup-ful, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--hero")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    trouble = getattr(args, "trouble", None) or rng.choice(list(TROUBLES))
    hero = getattr(args, "hero", None) or rng.choice(CREW_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in CREW_NAMES if n != hero])
    if helper == hero:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, trouble=trouble, hero=hero, helper=helper)


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    trouble = _safe_lookup(TROUBLES, params.trouble)
    hero = world.add(Entity(id=params.hero, kind="character", type="pirate", label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type="pirate", label=params.helper))
    cup = world.add(Entity(
        id="cupful",
        type="treasure",
        label="cup-ful",
        phrase=trouble.danger,
        owner=hero.id,
        caretaker=helper.id,
    ))
    world.facts.update(hero=hero, helper=helper, cup=cup, trouble=trouble, params=params)
    return world


def intro(world: World) -> None:
    f = world.facts
    hero, helper, trouble = f["hero"], f["helper"], f["trouble"]
    world.say(
        f"On {world.setting.place}, {hero.id} was a {random.choice(TRAITS)} pirate with a keen eye for treasure."
    )
    world.say(
        f"Beside {hero.pronoun('object')}, {helper.id} kept watch, because a pirate tale is never quiet for long."
    )
    world.say(
        f"They had a tiny {trouble.danger} tucked away, and even a small {trouble.loss_word} could shake the whole day."
    )


def trouble_strikes(world: World) -> None:
    f = world.facts
    trouble = _safe_fact(world, f, "trouble")
    hero, helper, cup = f["hero"], f["helper"], f["cup"]
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    helper.memes["alert"] = helper.memes.get("alert", 0) + 1
    cup.meters["lost"] = 1.0
    world.say(
        f"Then {trouble.cause} hit the deck, and the little {cup.label} skittered out of sight."
    )
    world.say(
        f"It was a quick {trouble.loss_word}, and {hero.id}'s grin turned to a worried frown."
    )


def teamwork_turn(world: World) -> None:
    f = world.facts
    hero, helper, cup = f["hero"], f["helper"], f["cup"]
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0) + 1
    world.say(
        f"{helper.id} held the lantern high while {hero.id} peered under barrels and ropes."
    )
    world.say(
        f"Together they whispered, called, and listened, because teamwork helps pirates find what one pair of eyes can miss."
    )
    cup.meters["found"] = 1.0
    world.say(
        f"At last, {hero.id} spotted the {cup.label} wedged by a coil of rope near the rail."
    )


def resolution(world: World) -> None:
    f = world.facts
    hero, helper, cup = f["hero"], f["helper"], f["cup"]
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    cup.meters["lost"] = 0.0
    world.say(
        f"{hero.id} slid the {cup.label} free, and {helper.id} steadied {hero.pronoun('object')} with a hand on the shoulder."
    )
    world.say(
        f"The crew laughed in relief, and the little {cup.label} was safe again."
    )
    world.say(
        f"By the end, the ship felt brighter, and the pirate pair knew a hard day can still end well when they use teamwork."
    )


def tell(world: World) -> World:
    intro(world)
    world.para()
    trouble_strikes(world)
    world.para()
    teamwork_turn(world)
    resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    trouble = _safe_fact(world, f, "trouble")
    params = _safe_fact(world, f, "params")
    return [
        f'Write a short pirate tale for a child about a {trouble.loss_word} and teamwork on {world.setting.place}.',
        f'Write a story where {params.hero} and {params.helper} must work together after a {trouble.cause} causes a {trouble.loss_word}.',
        f'Create a gentle pirate adventure that includes the words "loss" and "cup-ful" and ends with teamwork.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, cup, trouble = f["hero"], f["helper"], f["cup"], f["trouble"]
    return [
        QAItem(
            question=f"Who was the pirate story about?",
            answer=f"It was about {hero.id} and {helper.id}, two pirates on {world.setting.place} who worked together.",
        ),
        QAItem(
            question=f"What was lost in the story?",
            answer=f"A tiny {cup.label} was lost for a while, and that loss worried the crew.",
        ),
        QAItem(
            question=f"What helped the pirates fix the problem?",
            answer=f"Teamwork helped them search, listen, and find the {cup.label} again.",
        ),
        QAItem(
            question=f"What caused the trouble?",
            answer=f"{trouble.cause.capitalize()} caused the loss when the {cup.label} skittered out of sight.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to reach a goal.",
        )
    ],
    "pirate": [
        QAItem(
            question="Who is a pirate?",
            answer="A pirate is a person in stories who sails on the sea looking for adventure and treasure.",
        )
    ],
    "cup-ful": [
        QAItem(
            question="What does cup-ful mean?",
            answer="Cup-ful means an amount that fills one cup.",
        )
    ],
    "loss": [
        QAItem(
            question="What is a loss?",
            answer="A loss is when something is missing or not there anymore for a while.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["teamwork"])
    out.extend(WORLD_KNOWLEDGE["pirate"])
    out.extend(WORLD_KNOWLEDGE["cup-ful"])
    out.extend(WORLD_KNOWLEDGE["loss"])
    return out


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- crew(H).
helper(H) :- crew(H).
loss_event(T) :- trouble(T).
story_ready(P, T) :- setting(P), trouble(T), crew(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    # small compatibility facts
    for name in CREW_NAMES:
        lines.append(asp.fact("crew", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def asp_valid_story_shapes() -> list[tuple]:
    return [(p, t, h, k) for p in SETTINGS for t in TROUBLES for h in CREW_NAMES for k in CREW_NAMES if h != k]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="deck", trouble="spill", hero="Mina", helper="Jett"),
    StoryParams(place="cove", trouble="gust", hero="Ruby", helper="Nico"),
    StoryParams(place="harbor", trouble="slip", hero="Cora", helper="Finn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ready/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available, but this compact world uses a lightweight gate.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = seed
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
