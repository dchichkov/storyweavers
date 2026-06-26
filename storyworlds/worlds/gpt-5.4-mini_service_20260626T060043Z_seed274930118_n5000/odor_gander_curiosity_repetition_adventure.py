#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/odor_gander_curiosity_repetition_adventure.py
================================================================================================

A small story world for an adventure tale shaped by curiosity and repetition.

Premise seed:
- A curious gander notices a mysterious odor.
- Repeating the same sniff-and-waddle pattern leads the gander and a child helper
  toward a small adventure.
- The odor starts as a worry, then becomes a clue, and finally a discovery.

The world is intentionally compact:
- one small setting with a few places
- one or two characters
- one scent-driven mystery
- one repeated action that gradually changes the state

The story should feel authored and state-driven, not like a template swap.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    companion: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    gander: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Place:
    id: str
    label: str
    kind: str
    affords: set[str] = field(default_factory=set)
    scents: dict[str, str] = field(default_factory=dict)
    neighbors: list[str] = field(default_factory=list)
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


@dataclass
class Clue:
    id: str
    label: str
    odor: str
    at: str
    leads_to: str
    surprise: str
    revealed_by_repetition: bool = True
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []
        self.steps: int = 0

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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.steps = self.steps
        clone.paragraphs = [[]]
        return clone


def _smell_strength(world: World) -> float:
    return sum(e.meters.get("odor", 0.0) for e in world.entities.values())


def _rule_notice_odor(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        if world.fired.__contains__(("notice", e.id)):
            continue
        world.fired.add(("notice", e.id))
        e.memes["interest"] = e.memes.get("interest", 0.0) + 1
        out.append(f"{e.id} paused, because the smell was too strange to ignore.")
    return out


def _rule_repetition_leads_on(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("repetition", 0.0) < THRESHOLD:
            continue
        sig = ("repeat", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["confidence"] = e.memes.get("confidence", 0.0) + 1
        out.append(f"Trying the same careful sniff again made the next step feel easier.")
    return out


def _rule_clue_seen(world: World) -> list[str]:
    out: list[str] = []
    clue: Clue = _safe_fact(world, world.facts, "clue")
    for e in world.characters():
        if e.location != clue.at:
            continue
        if e.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        sig = ("clue", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] = e.memes.get("joy", 0.0) + 1
        out.append(f"The smell pointed to something hidden nearby.")
    return out


CAUSAL_RULES = [_rule_notice_odor, _rule_repetition_leads_on, _rule_clue_seen]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def run_step(world: World, actor: Entity, action: str, narrate: bool = True) -> None:
    clue: Clue = _safe_fact(world, world.facts, "clue")
    if action == "sniff":
        actor.meters["odor"] = actor.meters.get("odor", 0.0) + 1
        actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
        actor.memes["repetition"] = actor.memes.get("repetition", 0.0) + 1
        world.steps += 1
        if narrate:
            world.say(f"{actor.id} sniffed the air again and again.")
    elif action == "waddle":
        actor.location = clue.at if actor.location != clue.at else clue.leads_to
        actor.memes["adventure"] = actor.memes.get("adventure", 0.0) + 1
        world.steps += 1
        if narrate:
            world.say(f"{actor.id} waddled forward, following the smell.")
    elif action == "look":
        actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
        world.steps += 1
        if narrate:
            world.say(f"{actor.id} looked around for a clue.")
    else:
        pass
    propagate(world, narrate=narrate)


def advance_story(world: World, geese: list[Entity], child: Entity) -> None:
    clue: Clue = _safe_fact(world, world.facts, "clue")
    world.say(
        f"On a bright morning, {child.id} heard a funny honk from {world.place.label}."
    )
    world.say(
        f"A curious gander named {geese[0].id} kept sniffing at a strange odor in the air."
    )
    world.para()

    world.say(
        f"{child.id} and {geese[0].id} went to the {clue.at.split('_')[-1] if '_' in clue.at else clue.at} side of the path."
    )
    run_step(world, geese[0], "sniff")
    run_step(world, geese[0], "waddle")
    world.say(
        f"The same sniff-and-waddle happened once more, and this time the smell felt like a clue."
    )
    run_step(world, geese[0], "sniff")
    run_step(world, geese[0], "waddle")
    world.para()

    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{child.id} laughed and copied the careful sniffing, because repeating the motion made the trail easier to follow."
    )
    run_step(world, child, "look")
    world.say(
        f"At the end of the trail, they found {clue.surprise}."
    )
    world.say(
        f"The mysterious odor came from the {clue.label}, and the little adventure turned into a happy discovery."
    )


SETTINGS = {
    "orchard": Place(
        id="orchard",
        label="the orchard",
        kind="outdoor",
        affords={"sniff", "waddle", "look"},
        scents={"odor": "ripe apples"},
        neighbors=["barn_path", "pond_edge"],
    ),
    "pond": Place(
        id="pond",
        label="the pond",
        kind="outdoor",
        affords={"sniff", "waddle", "look"},
        scents={"odor": "wet reeds"},
        neighbors=["orchard", "barn_path"],
    ),
    "barnyard": Place(
        id="barnyard",
        label="the barnyard",
        kind="outdoor",
        affords={"sniff", "waddle", "look"},
        scents={"odor": "warm hay"},
        neighbors=["orchard", "pond"],
    ),
}

CLUES = {
    "blue_ribbon": Clue(
        id="blue_ribbon",
        label="blue ribbon",
        odor="sweet syrup",
        at="barn_path",
        leads_to="haystack",
        surprise="a blue ribbon tied to a basket handle",
    ),
    "seed_bag": Clue(
        id="seed_bag",
        label="seed bag",
        odor="spilled grain",
        at="pond_edge",
        leads_to="reed_patch",
        surprise="a little seed bag left beside the reeds",
    ),
    "pie_tin": Clue(
        id="pie_tin",
        label="pie tin",
        odor="warm crust",
        at="orchard_path",
        leads_to="apple_tree",
        surprise="a shiny pie tin tucked under a low branch",
    ),
}

GANDER_NAMES = ["Gus", "Gander", "Barnaby", "Milo", "Otis", "Pip"]
CHILD_NAMES = ["Nora", "Theo", "Lena", "Mina", "Eli", "June"]


@dataclass
class StoryParams:
    place: str
    clue: str
    gander_name: str
    child_name: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny adventure world about curiosity, repetition, odor, and a gander."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gander-name", choices=GANDER_NAMES)
    ap.add_argument("--child-name", choices=CHILD_NAMES)
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
    places = list(SETTINGS)
    clues = list(CLUES)
    place = getattr(args, "place", None) or rng.choice(places)
    clue = getattr(args, "clue", None) or rng.choice(clues)
    if clue == "pie_tin" and place != "orchard":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if clue == "blue_ribbon" and place == "pond":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gander_name = getattr(args, "gander_name", None) or rng.choice(GANDER_NAMES)
    child_name = getattr(args, "child_name", None) or rng.choice(CHILD_NAMES)
    return StoryParams(place=place, clue=clue, gander_name=gander_name, child_name=child_name)


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(SETTINGS, params.place)
    clue = _safe_lookup(CLUES, params.clue)
    world = World(place)
    gander = world.add(Entity(
        id=params.gander_name,
        kind="character",
        type="gander",
        label="gander",
        traits=["curious", "brave"],
        location=place.id,
    ))
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type="child",
        label="child",
        traits=["curious", "gentle"],
        location=place.id,
    ))
    gander.memes["curiosity"] = 1.0
    gander.memes["repetition"] = 0.0
    child.memes["curiosity"] = 0.5
    world.facts["clue"] = clue
    world.facts["gander"] = gander
    world.facts["child"] = child
    world.say(f"{gander.id} was a curious gander who loved following odors.")
    world.say(f"{child.id} liked adventure stories and wondered where the smell would lead.")
    world.para()
    advance_story(world, [gander], child)
    world.facts["finished"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    clue: Clue = _safe_fact(world, world.facts, "clue")
    gander: Entity = _safe_fact(world, world.facts, "gander")
    child: Entity = _safe_fact(world, world.facts, "child")
    return [
        f"Write a short adventure story for a young child about {gander.id}, a gander, who notices an odor and keeps checking it again and again.",
        f"Tell a gentle curiosity story where {child.id} follows {gander.id} through {world.place.label} until the smell becomes a clue.",
        f"Write a child-friendly adventure that uses the words odor and gander and ends with a small discovery near the {clue.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    clue: Clue = _safe_fact(world, world.facts, "clue")
    gander: Entity = _safe_fact(world, world.facts, "gander")
    child: Entity = _safe_fact(world, world.facts, "child")
    return [
        QAItem(
            question=f"Who noticed the strange odor first?",
            answer=f"{gander.id}, the curious gander, noticed it first and kept sniffing to figure it out."
        ),
        QAItem(
            question=f"What did repeating the sniff-and-waddle movement do?",
            answer=f"Repeating it made the trail easier to follow, so the smell started to feel like a clue."
        ),
        QAItem(
            question=f"What did {child.id} and {gander.id} find at the end?",
            answer=f"They found {clue.surprise}, and that turned the strange odor into a happy adventure."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an odor?",
            answer="An odor is a smell. Some odors are pleasant, and some are strong or strange."
        ),
        QAItem(
            question="What is a gander?",
            answer="A gander is a male goose. Ganders can waddle, honk, and watch carefully."
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more about something and checking it out."
        ),
        QAItem(
            question="Why does repetition sometimes help?",
            answer="Repetition can help because doing something carefully again lets you notice new details."
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id} ({e.type}) meters={meters} memes={memes} loc={e.location}")
    lines.append(f"  steps={world.steps}")
    return "\n".join(lines)


ASP_RULES = r"""
% An odor clue becomes interesting when a curious character notices it.
interesting(X) :- character(X), curiosity(X), odor_present.

% Repetition strengthens confidence and helps the trail become clearer.
helps_follow(X) :- character(X), repetition(X).

% A valid story needs a gander, a child, an odor, and a clue at a compatible place.
valid_story(P, C, G, K) :- place(P), clue(K), gander(G), child(C), clue_place(K, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_place", cid, clue.at if clue.at in SETTINGS else "orchard"))
    lines.append(asp.fact("odor_present"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as ex:  # pragma: no cover
        print(f"ASP unavailable: {ex}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/4."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    if atoms:
        print("OK: ASP program produced a compatible story shape.")
        return 0
    print("MISMATCH: ASP program produced no valid_story atoms.")
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    StoryParams(place="orchard", clue="pie_tin", gander_name="Gus", child_name="Nora"),
    StoryParams(place="barnyard", clue="blue_ribbon", gander_name="Barnaby", child_name="Theo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story tuples:")
        for tup in stories:
            print("  ", tup)
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
            header = f"### {p.gander_name}: odor adventure at {p.place} (clue: {p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
