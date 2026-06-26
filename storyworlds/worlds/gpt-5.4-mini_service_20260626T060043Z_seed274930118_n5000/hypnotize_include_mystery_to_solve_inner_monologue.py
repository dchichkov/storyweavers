#!/usr/bin/env python3
"""
Standalone storyworld: an adventure mystery with hypnotize, include, mystery to solve,
and inner monologue beats.

Premise seed:
- A small adventure tale where a curious child and a helper must solve a mystery.
- A strange hypnotize cue makes someone want to leave another out, and the turn is
  learning to include the missing person or clue.
- The story should read like an authored adventure, not a log.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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


@dataclass
class Setting:
    place: str
    mood: str
    affordances: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    clue: str
    hidden: str
    solved_by: str
    reveal: str
    wrong_suspicion: str
    lead_in: str
    keyword: str = "mystery"
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
    risk: str
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
class StoryParams:
    setting: str
    mystery: str
    item: str
    name: str
    gender: str
    sidekick: str
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
        self.trace_bits: list[str] = []

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


SETTINGS = {
    "harbor": Setting("the harbor path", "salt-bright", {"walk", "search"}),
    "cave": Setting("the cave mouth", "echoing", {"search", "follow"}),
    "forest": Setting("the forest trail", "leafy", {"walk", "search"}),
    "ruins": Setting("the old ruins", "dusty", {"search", "follow"}),
}

MYSTERIES = {
    "lost_map": Mystery(
        id="lost_map",
        clue="a torn map corner",
        hidden="the map was tucked inside the lantern case",
        solved_by="looking where the light had been stored",
        reveal="the lantern case held the missing map",
        wrong_suspicion="the wind had blown it away",
        lead_in="They noticed one clue and began to wonder where the rest had gone",
    ),
    "whisper_box": Mystery(
        id="whisper_box",
        clue="soft whispers from a wooden box",
        hidden="a small speaker behind the latch",
        solved_by="listening closely and opening the box together",
        reveal="the whispers came from a tiny speaker",
        wrong_suspicion="someone magical was trapped inside",
        lead_in="A strange sound made everyone stop and listen",
    ),
    "silver_key": Mystery(
        id="silver_key",
        clue="silver dust on the floor",
        hidden="the key was taped under a stepped stone",
        solved_by="checking the places nobody thought to look",
        reveal="the key was hidden beneath the stone",
        wrong_suspicion="a thief had already stolen it",
        lead_in="The trail of dust promised a secret to solve",
    ),
}

ITEMS = {
    "cloak": Item("cloak", "cloak", "a bright explorer's cloak", "muddy", "back", False),
    "boots": Item("boots", "boots", "sturdy boots", "wet", "feet", True),
    "satchel": Item("satchel", "satchel", "a small satchel", "scratched", "side", False),
    "hat": Item("hat", "hat", "a wide adventure hat", "dusty", "head", False),
}

NAMES = {
    "girl": ["Mina", "Luna", "Ivy", "Nora", "Zoe"],
    "boy": ["Finn", "Leo", "Owen", "Max", "Theo"],
}
SIDEKICKS = ["fox", "sparrow", "dog", "cat", "robot"]
TRAITS = ["curious", "brave", "quiet", "spirited", "clever"]


def _do_action(world: World, hero: Entity, item: Entity, mystery: Mystery) -> None:
    hero.meters["search"] = hero.meters.get("search", 0.0) + 1
    item.meters[item.label] = item.meters.get(item.label, 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.trace_bits.append("searched")


def solve_mystery(world: World, hero: Entity, mystery: Mystery, sidekick: str) -> None:
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
    world.say(
        f"{hero.id} stared at the clue and took a careful breath. "
        f'In {hero.pronoun("possessive")} inner monologue, {hero.pronoun("subject")} thought, '
        f'"If I follow the clue and stay calm, I can solve this."'
    )
    world.say(
        f"{hero.id} and the {sidekick} went {mystery.solved_by}. "
        f"That was the right adventure move, because {mystery.reveal}."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["mystery_solved"] = 1.0


def tell(setting: Setting, mystery: Mystery, item_cfg: Item,
         hero_name: str, hero_type: str, sidekick: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    companion = world.add(Entity(id="Companion", kind="character", type=sidekick))
    item = world.add(Entity(
        id=item_cfg.id,
        type=item_cfg.label,
        label=item_cfg.label,
        plural=item_cfg.plural,
        owner=hero.id,
    ))

    world.say(
        f"On {setting.place}, {hero.id} was a little {hero_type} who loved adventure. "
        f"{hero.id} wore {item_cfg.phrase} and kept looking for one more surprise."
    )
    world.say(
        f"{mystery.lead_in}, and soon the {mystery.clue} made the whole path feel like a puzzle."
    )
    world.say(
        f"The {sidekick} stayed close, and {hero.id} wondered if {mystery.wrong_suspicion}."
    )

    world.para()
    hero.memes["curiosity"] = 1.0
    world.say(
        f"Then a funny whisper seemed to hypnotize {companion.id} into wanting to keep the clue secret."
    )
    world.say(
        f"{hero.id}'s chest tightened. In {hero.pronoun('possessive')} inner monologue, "
        f'{hero.pronoun("subject")} thought, "If I let that happen, I might leave someone out."'
    )
    world.say(
        f"So {hero.id} spoke up and said, 'We should include everyone who can help.'"
    )
    hero.memes["include"] = hero.memes.get("include", 0.0) + 1
    companion.memes["startled"] = 1.0

    world.para()
    _do_action(world, hero, item, mystery)
    solve_mystery(world, hero, mystery, sidekick)
    world.say(
        f"In the end, the group found that {mystery.hidden}. "
        f"{hero.id} smiled, because the adventure had become bigger when everyone was included."
    )
    hero.memes["relief"] = 1.0

    world.facts.update(
        hero=hero,
        item=item,
        mystery=mystery,
        sidekick=sidekick,
        setting=setting,
        item_cfg=item_cfg,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    item: Entity = _safe_fact(world, f, "item")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a short adventure story for a child about "{mystery.keyword}" and a clue that must be solved.',
        f"Tell a story where {hero.id} wears {item.label} and learns to include everyone instead of letting a strange hypnotize moment leave others out.",
        f"Write a mystery-to-solve tale with inner monologue where {hero.id} follows a clue at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    item: Entity = _safe_fact(world, f, "item")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    sidekick = _safe_fact(world, f, "sidekick")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who is the adventure story about?",
            answer=f"It is about {hero.id}, who goes to {setting.place} to solve a mystery with a {sidekick}.",
        ),
        QAItem(
            question=f"What helped {hero.id} notice the mystery?",
            answer=f"A clue, {mystery.clue}, helped {hero.id} notice that something needed to be solved.",
        ),
        QAItem(
            question=f"What did {hero.id} decide when the hypnotize moment tried to leave someone out?",
            answer=f"{hero.id} decided to include everyone who could help, instead of keeping the clue secret.",
        ),
        QAItem(
            question=f"What was the mystery solved by?",
            answer=f"It was solved by {mystery.solved_by}.",
        ),
        QAItem(
            question=f"What item did {hero.id} wear during the adventure?",
            answer=f"{hero.id} wore {item.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.id}'s inner monologue say about the problem?",
            answer=f"{hero.id} thought that staying calm and following the clue would help solve the mystery.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or secret that people try to solve by looking for clues.",
        )
    ],
    "include": [
        QAItem(
            question="What does it mean to include someone?",
            answer="To include someone means to make sure they are part of the group or activity.",
        )
    ],
    "hypnotize": [
        QAItem(
            question="What does hypnotize mean?",
            answer="To hypnotize someone means to make them focus so hard that they may stop noticing other things for a while.",
        )
    ],
    "inner_monologue": [
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the quiet voice of a character's own thoughts inside their head.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["mystery"])
    out.extend(WORLD_KNOWLEDGE["include"])
    out.extend(WORLD_KNOWLEDGE["hypnotize"])
    out.extend(WORLD_KNOWLEDGE["inner_monologue"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery(M) :- clue(M,_).
solved(M) :- mystery(M), solved_by(M,_).
included(H) :- include(H,_).
twist(H) :- hypnotize(H,_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("solved_by", mid, m.solved_by))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("risk", iid, it.risk))
        lines.append(asp.fact("region", iid, it.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with hypnotize and include.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    return StoryParams(setting=setting, mystery=mystery, item=item, name=name, gender=gender, sidekick=sidekick)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(MYSTERIES, params.mystery),
        _safe_lookup(ITEMS, params.item),
        params.name,
        params.gender,
        params.sidekick,
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


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery/1.\n#show solved/1.\n#show included/1.\n#show twist/1."))
    return sorted(set((sym.name, tuple(a.name if hasattr(a, "name") else getattr(a, "string", None) for a in sym.arguments)) for sym in model))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery/1."))
    if model is None:
        print("ASP produced no model.")
        return 1
    print("OK: ASP program loads and solves.")
    return 0


CURATED = [
    StoryParams(setting="forest", mystery="lost_map", item="cloak", name="Mina", gender="girl", sidekick="fox"),
    StoryParams(setting="cave", mystery="whisper_box", item="boots", name="Leo", gender="boy", sidekick="dog"),
    StoryParams(setting="ruins", mystery="silver_key", item="satchel", name="Ivy", gender="girl", sidekick="sparrow"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery/1.\n#show solved/1.\n#show included/1.\n#show twist/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

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

    if getattr(args, "asp", None):
        print(asp_program("#show mystery/1.\n#show solved/1.\n#show included/1.\n#show twist/1."))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
