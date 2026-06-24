#!/usr/bin/env python3
"""
A small storyworld about a river path, a boastful challenge, and a tall-tale
conflict that ends with a clever turn.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prize: object | None = None
    relative: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
    place: str = "the river path"
    world: object | None = None
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
class Challenge:
    id: str
    verb: str
    noun: str
    obstacle: str
    result: str
    hazard: str
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
class Prize:
    label: str
    phrase: str
    type: str
    owner_kind: str
    value: str
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
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
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
    def __init__(self, setting: Setting):
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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


HEROES = [
    ("Milo", "boy"), ("Nina", "girl"), ("Jasper", "boy"), ("Tessa", "girl"),
    ("Pip", "girl"), ("Otto", "boy")
]
KINDS = ["boy", "girl"]
RELATIVES = {"boy": ["father", "uncle"], "girl": ["mother", "aunt"]}
TRAITS = ["bold", "curious", "spirited", "lively", "stubborn", "cheerful"]

CHALLENGES = {
    "logjam": Challenge(
        id="logjam",
        verb="cross the logjam",
        noun="logjam",
        obstacle="a packed tangle of floating logs",
        result="one log rolled like a thunder drum",
        hazard="splash",
        tag="water",
    ),
    "bridge": Challenge(
        id="bridge",
        verb="cross the wobbly bridge",
        noun="bridge",
        obstacle="a narrow bridge that bounced like a pony's back",
        result="the boards sang with every step",
        hazard="shake",
        tag="wood",
    ),
    "ferry": Challenge(
        id="ferry",
        verb="ride the ferry",
        noun="ferry",
        obstacle="a little ferry that rocked in the current",
        result="the rope hummed in the wind",
        hazard="rock",
        tag="water",
    ),
}

PRIZES = {
    "hat": Prize("hat", "a bright river hat", "hat", "child", "sparkle"),
    "boots": Prize("boots", "tall rubber boots", "boots", "child", "dry feet"),
    "kite": Prize("kite", "a red kite with a long tail", "kite", "child", "fly high"),
}

TOOLS = [
    Tool("pole", "a long pole", "plant a long pole and test the ground", "planted the pole and walked safely", {"water", "wood"}),
    Tool("rope", "a sturdy rope", "tie on a sturdy rope and take turns", "held the rope and crossed together", {"wood", "water"}),
    Tool("raft", "a little raft", "ride a little raft instead", "floated the raft along the path-side bank", {"water"}),
]

ASP_RULES = r"""
challenge(C). prize(P). tool(T).
needs_fix(C,P) :- hazard(C, water), prize_on_child(P).
needs_fix(C,P) :- hazard(C, wood), prize_on_child(P).
has_fix(C,P) :- needs_fix(C,P), tool(T), helps(T, water).
has_fix(C,P) :- needs_fix(C,P), tool(T), helps(T, wood).
valid(C,P) :- challenge(C), prize(P), has_fix(C,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_on_child", pid))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, h))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("hazard", cid, "water" if c.tag == "water" else "wood"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for cid in CHALLENGES:
        for pid in PRIZES:
            if select_tool(_safe_lookup(CHALLENGES, cid), _safe_lookup(PRIZES, pid)) is not None:
                out.append((cid, pid))
    return out


def asp_verify() -> int:
    a, b = set(asp_valid()), set(valid_combos())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combos).")
        return 0
    print("MISMATCH")
    print("only in asp:", sorted(a - b))
    print("only in py:", sorted(b - a))
    return 1


def select_tool(challenge: Challenge, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if challenge.tag in tool.helps:
            return tool
    return None


def predict_conflict(world: World, hero: Entity, challenge: Challenge, prize: Entity) -> bool:
    sim = world.copy()
    do_challenge(sim, sim.get(hero.id), challenge, narrate=False)
    return bool(sim.get(prize.id).meters.get("shaken", 0) >= 1)


def do_challenge(world: World, hero: Entity, challenge: Challenge, narrate: bool = True) -> None:
    hero.meters["effort"] = hero.meters.get("effort", 0) + 1
    hero.meters["danger"] = hero.meters.get("danger", 0) + 1
    hero.memes["excitement"] = hero.memes.get("excitement", 0) + 1
    if narrate:
        world.say(f"{hero.id} tried to {challenge.verb}, and {challenge.obstacle} was waiting there.")


def introduce(world: World, hero: Entity, relative: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a big grin and a bigger story in {hero.pronoun('possessive')} head."
    )
    world.say(
        f"That day, {hero.id}'s {relative.type} had given {hero.pronoun('object')} {prize.phrase}."
    )


def conflict(world: World, hero: Entity, relative: Entity, challenge: Challenge, prize: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.para()
    world.say(
        f"At the river path, the wind whistled thin as a flute, and {hero.id} wanted to {challenge.verb} at once."
    )
    if predict_conflict(world, hero, challenge, prize):
        world.say(
            f"“No, no,” said {relative.id}, because if {hero.id} went headlong, {prize.label} would get spoiled by the rush and shake of it."
        )
        hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
        world.say(
            f"{hero.id} puffed up like a little cloud. “I can do it myself!” {hero.pronoun().capitalize()} said, and {hero.id} started toward the danger."
        )


def resolve(world: World, hero: Entity, relative: Entity, challenge: Challenge, prize: Entity) -> None:
    tool = select_tool(challenge, prize)
    if tool is None:
        pass
    world.para()
    world.say(
        f"Then {relative.id} pointed to {tool.label} and smiled. “How about we {tool.prep}?”"
    )
    world.say(
        f"{hero.id}'s eyes went wide, because that was a cleverer plan than trying to out-bluster the river."
    )
    hero.memes["conflict"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"So they {tool.tail}, and {hero.id} got to {challenge.verb} without ruining {hero.pronoun('possessive')} {prize.label}."
    )
    world.say(
        f"By the end, the river path looked small and tame, and {hero.id} looked proud enough to shake hands with thunder."
    )
    world.facts.update(hero=hero, relative=relative, challenge=challenge, prize=prize, tool=tool, resolved=True)


def tell(hero_name: str, hero_kind: str, relative_kind: str, challenge_id: str, prize_id: str, trait: str) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_kind))
    relative_name = _safe_lookup(RELATIVES, hero_kind)[0].capitalize()
    relative = world.add(Entity(id=relative_name, kind="character", type=relative_kind))
    prize = world.add(Entity(id=prize_id, kind="thing", type=prize_id, label=prize_id, phrase=_safe_lookup(PRIZES, prize_id).phrase, owner=hero.id))
    challenge = _safe_lookup(CHALLENGES, challenge_id)

    world.say(
        f"Once, on the river path, {hero.id} was a {trait} little {hero_kind} with a head full of tall tales."
    )
    introduce(world, hero, relative, prize)
    conflict(world, hero, relative, challenge, prize)
    resolve(world, hero, relative, challenge, prize)
    return world


@dataclass
class StoryParams:
    challenge: str
    prize: str
    name: str
    kind: str
    relative_kind: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale style story about a child on a river path who wants to {f["challenge"].verb}.',
        f'Write a child-friendly story with the word "chapter" where {f["hero"].id} faces a conflict near the river path and finds a clever fix.',
        f'Write a short story where a {f["hero"].type} named {f["hero"].id} argues with a relative, then uses a tool to cross safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    rel = _safe_fact(world, f, "relative")
    challenge = _safe_fact(world, f, "challenge")
    prize = _safe_fact(world, f, "prize")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What was the conflict in the story about {hero.id} on the river path?",
            answer=f"{hero.id} wanted to {challenge.verb}, but {rel.id} worried about {prize.label} getting messed up."
        ),
        QAItem(
            question=f"How did {hero.id} and {rel.id} solve the problem?",
            answer=f"They used {tool.label} and crossed in a safer way, so {hero.id} could still {challenge.verb}."
        ),
        QAItem(
            question=f"What happened to {prize.label} by the end?",
            answer=f"{prize.label.capitalize()} stayed safe while {hero.id} finished the river-path adventure."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a river path?",
            answer="A river path is a path that runs beside a river, where people can walk and watch the water move."
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or disagreement that makes the characters have to choose, talk, or try a new plan."
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a story told in a big, exaggerated way, like the world is a little larger and sillier than usual."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld set on a river path with a conflict and a clever fix.")
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--relative-kind", choices=KINDS)
    ap.add_argument("--trait", choices=TRAITS)
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
    challenge = getattr(args, "challenge", None) or rng.choice(list(CHALLENGES))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    kind = getattr(args, "kind", None) or rng.choice(KINDS)
    relative_kind = getattr(args, "relative_kind", None) or rng.choice(_safe_lookup(RELATIVES, kind))
    name = getattr(args, "name", None) or rng.choice([n for n, k in HEROES if k == kind])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(challenge=challenge, prize=prize, name=name, kind=kind, relative_kind=relative_kind, trait=trait)


def valid_params(params: StoryParams) -> None:
    if params.challenge not in CHALLENGES:
        pass
    if params.prize not in PRIZES:
        pass
    if params.kind not in KINDS:
        pass
    if params.relative_kind not in KINDS:
        pass


def generate(params: StoryParams) -> StorySample:
    valid_params(params)
    world = tell(params.name, params.kind, params.relative_kind, params.challenge, params.prize, params.trait)
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(sorted(asp_valid()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("logjam", "boots", "Milo", "boy", "father", "bold"),
            StoryParams("bridge", "hat", "Nina", "girl", "mother", "curious"),
            StoryParams("ferry", "kite", "Jasper", "boy", "uncle", "spirited"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

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
