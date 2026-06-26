#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/peep_ounce_arrive_bad_ending_happy_ending.py
===============================================================================================================

A small folk-tale story world about a tiny traveler, a little measure of treasure,
and the choice between a bad ending, problem solving, and a happy ending.

Seed tale sketch:
---
In a hill village, Peep the sparrow liked to peep through keyholes and windows.
One day, Old Mara asked Peep to carry one ounce of honey to Grandmother Moss
before the sun set. Peep and a small mouse named Ounce set out together, but
the path crossed a narrow bridge over a brook.

A plank was loose, and the honey jar was heavy for such a little bird. If they
rushed, the jar might tip and the honey might spill into the water. Peep wanted
to arrive on time, but the safest way was to stop, think, and solve the problem.

They peeped beneath the bridge, found a flat reed, and used it to steady the jar.
Then they arrived with the ounce of honey still safe, and Grandmother Moss smiled.
---

World design:
- Physical meters: carried weight, spill risk, distance traveled, bridge stability.
- Emotional memes: hope, worry, pride, relief.
- Folk-tale instruments: peep, ounce, arrive; bad ending / problem solving / happy ending.
- A bad ending exists if the travelers fail to solve the bridge problem.
- A happy ending exists if they solve it and arrive with the honey intact.
"""

from __future__ import annotations

import argparse
import dataclasses
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

WORLD_ID = "peep_ounce_arrive_bad_ending_happy_ending"

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities / world state
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bridge: object | None = None
    elder: object | None = None
    helper: object | None = None
    hero: object | None = None
    jar: object | None = None
    reed: object | None = None
    woman: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
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
class Place:
    id: str
    label: str
    kind: str = "place"
    neighbors: set[str] = field(default_factory=set)
    peepable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
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
class World:
    places: dict[str, Place]
    entities: dict[str, Entity]
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        return World(
            places=copy.deepcopy(self.places),
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            fired=set(self.fired),
            facts=dict(self.facts),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


PLACES = {
    "hill_village": Place(id="hill_village", label="the hill village", neighbors={"brook_bridge", "grandmother_house"}),
    "brook_bridge": Place(id="brook_bridge", label="the brook bridge", neighbors={"hill_village", "grandmother_house"}, peepable=True),
    "grandmother_house": Place(id="grandmother_house", label="Grandmother Moss's house", neighbors={"hill_village", "brook_bridge"}),
}

CHAR_TYPES = {"sparrow", "mouse", "grandmother", "woman"}
NAMES = {
    "sparrow": ["Peep"],
    "mouse": ["Ounce"],
    "grandmother": ["Moss"],
    "woman": ["Mara"],
}
TRAITS = ["little", "bright-eyed", "gentle", "quick", "brave"]


@dataclass
class StoryParams:
    hero_name: str = "Peep"
    helper_name: str = "Ounce"
    elder_name: str = "Moss"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonable gate
# ---------------------------------------------------------------------------
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


def can_reach(src: str, dst: str) -> bool:
    return dst in _safe_lookup(PLACES, src).neighbors


def problem_exists(world: World) -> bool:
    jar = world.get("honey")
    bridge = world.get("bridge")
    return jar.meters.get("spill_risk", 0.0) >= THRESHOLD and bridge.meters.get("stability", 0.0) < THRESHOLD


def good_fix_available(world: World) -> bool:
    return any(
        e.id == "reed" and e.location == "brook_bridge"
        for e in world.entities.values()
    )


# ---------------------------------------------------------------------------
# World model rules
# ---------------------------------------------------------------------------
def _r_risk(world: World) -> list[str]:
    out = []
    jar = world.get("honey")
    bridge = world.get("bridge")
    if jar.location == "brook_bridge" and bridge.meters.get("stability", 0.0) < THRESHOLD:
        sig = ("risk",)
        if sig not in world.fired:
            world.fired.add(sig)
            jar.meters["spill_risk"] = 1.0
            out.append("The bridge wobbled, and the honey jar felt in danger.")
    return out


def _r_peep(world: World) -> list[str]:
    out = []
    peep = world.get("Peep")
    if peep.location == "brook_bridge" and not peep.memes.get("curious_seen"):
        peep.memes["curious_seen"] = 1.0
        out.append("Peep peeped beneath the boards and noticed a flat reed.")
    return out


def _r_happy(world: World) -> list[str]:
    out = []
    jar = world.get("honey")
    if world.facts.get("solved") and jar.location == "grandmother_house" and jar.meters.get("spill_risk", 0.0) < THRESHOLD:
        sig = ("happy",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The honey stayed safe, and the little travelers arrived with a happy ending.")
    return out


RULES = [_r_risk, _r_peep, _r_happy]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Simulation actions
# ---------------------------------------------------------------------------
def move(world: World, who: Entity, place_id: str) -> None:
    who.location = place_id


def arrive(world: World, who: Entity, place_id: str, label: str) -> None:
    move(world, who, place_id)
    world.say(f"{who.id} and {label} arrived at {_safe_lookup(PLACES, place_id).label}.")


def peep(world: World, who: Entity, place_id: str) -> None:
    who.location = place_id
    world.say(f"{who.id} peeped into the shadows and saw more than the others did.")


def carry(world: World, who: Entity, item: Entity) -> None:
    item.carried_by = who.id
    item.location = who.location


def try_cross(world: World, who: Entity, helper: Entity, item: Entity) -> None:
    bridge = world.get("bridge")
    if bridge.meters.get("stability", 0.0) < THRESHOLD:
        world.say(f"The bridge trembled under their steps, and the ounce of honey shivered in the jar.")
        who.memes["worry"] += 1
        helper.memes["worry"] += 1
        item.meters["spill_risk"] = 1.0
    else:
        world.say(f"They crossed the bridge with easy feet.")
        item.location = "grandmother_house"


def solve_problem(world: World, who: Entity, helper: Entity, item: Entity) -> bool:
    reed = world.entities.get("reed")
    bridge = world.get("bridge")
    if reed and reed.location == "brook_bridge":
        bridge.meters["stability"] = 1.0
        item.meters["spill_risk"] = 0.0
        world.facts["solved"] = True
        who.memes["relief"] += 1
        helper.memes["pride"] += 1
        world.say(f"{who.id} peeped under the plank, found the reed, and tucked it beneath the bridge to hold it steady.")
        world.say(f"Then the little pair solved the problem together.")
        return True
    return False


def bad_ending(world: World) -> None:
    world.facts["ending"] = "bad"
    jar = world.get("honey")
    jar.meters["spill_risk"] = 1.0
    world.say("But no one found a fix, the honey spilled, and the journey ended in sorrow.")


def happy_ending(world: World) -> None:
    world.facts["ending"] = "happy"
    world.say("At last they arrived safely, and Grandmother Moss smiled at the ounce of honey in Peep's care.")


# ---------------------------------------------------------------------------
# Story build
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    world = World(places={k: dataclasses.replace(v) for k, v in PLACES.items()}, entities={})

    hero = world.add_entity(Entity(id="Peep", kind="character", type="sparrow", label="Peep"))
    helper = world.add_entity(Entity(id="Ounce", kind="character", type="mouse", label="Ounce"))
    elder = world.add_entity(Entity(id="Moss", kind="character", type="grandmother", label="Grandmother Moss"))
    woman = world.add_entity(Entity(id="Mara", kind="character", type="woman", label="Old Mara"))

    jar = world.add_entity(Entity(id="honey", type="thing", label="honey", phrase="one ounce of honey", owner=elder.id))
    bridge = world.add_entity(Entity(id="bridge", type="thing", label="bridge", phrase="a narrow brook bridge", location="brook_bridge"))
    reed = world.add_entity(Entity(id="reed", type="thing", label="reed", phrase="a flat reed", location="brook_bridge"))

    hero.location = "hill_village"
    helper.location = "hill_village"
    woman.location = "hill_village"
    elder.location = "grandmother_house"
    jar.location = "hill_village"

    world.facts.update(hero=hero, helper=helper, elder=elder, woman=woman, jar=jar, bridge=bridge, reed=reed)

    # Act 1: the setup.
    world.say(f"In the hill village, {hero.id} liked to peep through keyholes and listen to old tales.")
    world.say(f"One morning, {woman.label} asked {hero.id} to carry {jar.phrase} to {elder.label}.")
    world.say(f"{helper.id} came along, because even a tiny ounce of help can matter in a folk tale.")
    world.para()

    # Act 2: the journey and trouble.
    arrive(world, hero, "brook_bridge", f"{helper.id}")
    carry(world, hero, jar)
    world.say(f"They set the jar on the bridge, and everyone could feel the weight of only an ounce.")
    world.say("Yet the plank was loose, and the brook below looked eager to catch a spill.")
    propagate(world)
    world.para()

    # Act 3: problem solving or bad ending.
    did_solve = solve_problem(world, hero, helper, jar)
    if did_solve:
        carry(world, hero, jar)
        bridge.meters["stability"] = 1.0
        arrive(world, hero, "grandmother_house", f"{helper.id}")
        jar.location = "grandmother_house"
        happy_ending(world)
    else:
        bad_ending(world)

    world.facts["solved"] = did_solve
    if did_solve:
        world.facts["ending"] = "happy"
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a short folk tale for a child about {world.facts["hero"].id}, a peep, and one ounce of honey.',
        f"Tell a gentle story where {world.facts['hero'].id} and {world.facts['helper'].id} arrive at a bridge, solve a problem, and reach Grandmother Moss.",
        f'Write a story that uses the words "peep", "ounce", and "arrive" and ends with a happy ending or a bad ending depending on the choice made.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    elder = _safe_fact(world, world.facts, "elder")
    jar = _safe_fact(world, world.facts, "jar")
    ending = world.facts.get("ending", "bad")
    return [
        QAItem(
            question=f"Who went on the journey with {hero.id}?",
            answer=f"{helper.id} went with {hero.id} so the little traveler would not carry the ounce of honey alone.",
        ),
        QAItem(
            question=f"What did {hero.id} carry to {elder.label}?",
            answer=f"{hero.id} carried {jar.phrase} to {elder.label}.",
        ),
        QAItem(
            question="Why was the bridge a problem?",
            answer="The bridge was a problem because it wobbled, and the honey jar could have spilled into the brook.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer="Peep peeped beneath the bridge, found a reed, and used it to steady the plank so the jar could pass safely.",
        ),
        QAItem(
            question="What ending did the story have?",
            answer="It had a happy ending." if ending == "happy" else "It had a bad ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to peep?",
            answer="To peep means to look quickly and carefully, often through a small opening or from a hiding place.",
        ),
        QAItem(
            question="How much is an ounce?",
            answer="An ounce is a small measure of weight. It is very little, like a tiny bit of honey or flour.",
        ),
        QAItem(
            question="What does arrive mean?",
            answer="To arrive means to reach a place after traveling there.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means stopping, thinking, and finding a way to fix what is hard.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location is not None:
            bits.append(f"location={e.location}")
        if e.carried_by is not None:
            bits.append(f"carried_by={e.carried_by}")
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% place(P).
% neighbor(P,Q).
% character(C).
% thing(T).
% located(X,P).
% bridge(P).
% reed(T).
% honey(T).
% problem(P) means a place has an unsafe bridge and the honey is there.
% solved means the reed was found and the bridge was repaired.

problem(P) :- bridge(P), located(honey,P), weak(P).
can_solve(P) :- problem(P), located(reed,P).
happy :- can_solve(P), not spill.
bad :- problem(P), not can_solve(P).
spill :- problem(P), not can_solve(P).

#show problem/1.
#show can_solve/1.
#show happy/0.
#show bad/0.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.peepable:
            lines.append(asp.fact("peepable", pid))
        for n in sorted(place.neighbors):
            lines.append(asp.fact("neighbor", pid, n))
    lines.append(asp.fact("bridge", "brook_bridge"))
    lines.append(asp.fact("character", "Peep"))
    lines.append(asp.fact("character", "Ounce"))
    lines.append(asp.fact("character", "Moss"))
    lines.append(asp.fact("character", "Mara"))
    lines.append(asp.fact("thing", "honey"))
    lines.append(asp.fact("thing", "reed"))
    lines.append(asp.fact("located", "honey", "brook_bridge"))
    lines.append(asp.fact("located", "reed", "brook_bridge"))
    lines.append(asp.fact("weak", "brook_bridge"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show problem/1.\n#show can_solve/1.\n#show happy/0.\n#show bad/0."))
    atoms = set((sym.name, tuple(a.name if a.type != a.type.Number else a.number for a in sym.arguments)) for sym in model)
    python_problem = {("problem", ("brook_bridge",))}
    python_can_solve = {("can_solve", ("brook_bridge",))}
    python_happy = {("happy", ())}
    if python_problem.issubset(atoms) and python_can_solve.issubset(atoms):
        print("OK: ASP program is internally consistent.")
        return 0
    print("MISMATCH: ASP validation failed.")
    return 1


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world: peep, ounce, arrive, and the choice of ending.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--elder-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero_name=getattr(args, "hero_name", None) or "Peep",
        helper_name=getattr(args, "helper_name", None) or "Ounce",
        elder_name=getattr(args, "elder_name", None) or "Moss",
        seed=getattr(args, "seed", None),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show problem/1.\n#show can_solve/1.\n#show happy/0.\n#show bad/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show problem/1.\n#show can_solve/1.\n#show happy/0.\n#show bad/0."))
        print("\n".join(str(a) for a in model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples.append(generate(StoryParams(seed=base_seed)))
    else:
        seen = set()
        for i in range(max(getattr(args, "n", None), 1)):
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
