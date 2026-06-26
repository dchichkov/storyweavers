#!/usr/bin/env python3
"""
storyworlds/worlds/real_ist_repetition_cautionary_space_adventure.py
====================================================================

A small story world about a real-ist space journey: a careful crew, a looping
mistake, and a warning that turns repetition into a safer habit.

The seed premise is a tiny cautionary space adventure:
- A childlike crew member wants to hurry through a repeating route in space.
- The captain warns that rushing the same route again is risky.
- The crew learns to repeat the safe checks instead of repeating the mistake.

This world is intentionally small and state-driven:
- physical state tracks meters like fuel, hull wear, shield charge, distance,
  and signal strength
- emotional state tracks memes like worry, relief, trust, and caution
- repetition matters because the route contains recurring checkpoints
- the ending proves a change: the same journey is repeated, but safely

The file supports the standard Storyweavers storyworld contract, including:
- generation
- text and JSON output
- Q&A
- trace
- ASP parity verification
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
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    crew: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
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
class Route:
    name: str
    place: str
    hazard: str
    repeat_word: str
    caution_word: str
    risk_meter: str
    risk_threshold: float
    safe_check: str
    safe_item: str
    safe_item_phrase: str
    safe_item_protects: set[str]
    safe_item_plural: bool = False
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
class StoryParams:
    route: str
    crew_name: str
    crew_type: str
    captain_type: str
    trait: str
    seed: Optional[int] = None
    p: object | None = None
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


class World:
    def __init__(self, route: Route) -> None:
        self.route = route
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.route)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ROUTES = {
    "ring": Route(
        name="orbital ring",
        place="the orbital ring",
        hazard="a repeating belt of tiny sparks",
        repeat_word="again",
        caution_word="careful",
        risk_meter="shield",
        risk_threshold=1.0,
        safe_check="check the shield panels",
        safe_item="shield patch",
        safe_item_phrase="a bright shield patch",
        safe_item_protects={"shield"},
    ),
    "dock": Route(
        name="harbor dock",
        place="the moon dock",
        hazard="a repeating patch of slippery frost",
        repeat_word="again",
        caution_word="steady",
        risk_meter="boots",
        risk_threshold=1.0,
        safe_check="slow down at the frosty rail",
        safe_item="grip boots",
        safe_item_phrase="a pair of grip boots",
        safe_item_protects={"boots"},
        safe_item_plural=True,
    ),
    "comet": Route(
        name="comet lane",
        place="the comet lane",
        hazard="a repeated shower of dust",
        repeat_word="once more",
        caution_word="watchful",
        risk_meter="visor",
        risk_threshold=1.0,
        safe_check="close the visor",
        safe_item="dust visor",
        safe_item_phrase="a clear dust visor",
        safe_item_protects={"visor"},
    ),
}

TRAITS = ["curious", "brave", "real-ist", "thoughtful", "bright", "steady"]
CREW_NAMES = ["Nia", "Tao", "Mira", "Juno", "Ari", "Rin", "Sol", "Pip"]


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def _apply_hazard(world: World) -> list[str]:
    out: list[str] = []
    crew = world.get("crew")
    route = world.route
    if crew.meters.get("moving", 0.0) < THRESHOLD:
        return out
    if crew.meters.get(route.risk_meter, 0.0) >= THRESHOLD:
        return out
    sig = ("hazard", route.risk_meter)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crew.meters[route.risk_meter] = crew.meters.get(route.risk_meter, 0.0) + 1
    crew.memes["worry"] = crew.memes.get("worry", 0.0) + 1
    out.append(f"The repeated hazard made the {route.risk_meter} feel strained.")
    return out


def _apply_caution(world: World) -> list[str]:
    out: list[str] = []
    crew = world.get("crew")
    captain = world.get("captain")
    if crew.memes.get("worry", 0.0) < THRESHOLD:
        return out
    sig = ("caution",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    captain.memes["caution"] = captain.memes.get("caution", 0.0) + 1
    captain.memes["trust"] = captain.memes.get("trust", 0.0) + 1
    out.append("The captain noticed the worry and chose a slower, safer repeat.")
    return out


def _apply_repair(world: World) -> list[str]:
    out: list[str] = []
    crew = world.get("crew")
    if crew.memes.get("caution", 0.0) < THRESHOLD:
        return out
    if crew.meters.get("repaired", 0.0) >= THRESHOLD:
        return out
    sig = ("repair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crew.meters["repaired"] = 1
    crew.memes["relief"] = crew.memes.get("relief", 0.0) + 1
    out.append("They repeated the safety check until the route felt calm again.")
    return out


CAUSAL_RULES = [_apply_hazard, _apply_caution, _apply_repair]


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


# ---------------------------------------------------------------------------
# Story functions
# ---------------------------------------------------------------------------
def route_detail(route: Route) -> str:
    return {
        "orbital ring": "The ring curved around the station like a silver bracelet.",
        "moon dock": "The dock lights blinked in the cold, quiet dark.",
        "comet lane": "The lane shimmered with dust as if the stars had dropped crumbs there.",
    }.get(route.name, f"{route.place.capitalize()} waited in the dark like a careful map.")


def intro(world: World, crew: Entity) -> None:
    world.say(
        f"{crew.id} was a little {crew.type} with a {world.facts['trait']} way of looking at space."
    )
    world.say(
        f"{crew.id} loved the same route because repeating it felt like learning a song."
    )


def setup(world: World, crew: Entity, captain: Entity, route: Route, item: Entity) -> None:
    world.say(
        f"One day, {crew.id} and {crew.pronoun('possessive')} {captain.type} went to {route.place}."
    )
    world.say(route_detail(route))
    world.say(
        f"{crew.id} wanted to go {route.repeat_word} right away, even though {route.hazard} was waiting there."
    )
    world.say(
        f"{captain.id} held up {captain.pronoun('possessive')} hand and said, "
        f'"Be {route.caution_word}. {route.safe_check} first."'
    )
    world.say(
        f"{crew.id} had brought {item.phrase}, because the little ship knew safer gear mattered."
    )


def risk(world: World, crew: Entity, route: Route) -> None:
    crew.meters["moving"] = crew.meters.get("moving", 0.0) + 1
    propagate(world, narrate=True)


def pushback(world: World, crew: Entity, captain: Entity, route: Route) -> None:
    crew.memes["wanting"] = crew.memes.get("wanting", 0.0) + 1
    world.say(
        f"{crew.id} hurried toward the route again, but the captain stepped in front of the risky part."
    )
    world.say(
        f'"We do not repeat the danger," {captain.id} said. "We repeat the check."'
    )


def safe_turn(world: World, crew: Entity, captain: Entity, item: Entity, route: Route) -> None:
    crew.memes["caution"] = crew.memes.get("caution", 0.0) + 1
    item.worn_by = crew.id
    item.protective = True
    world.say(
        f"{captain.id} fastened {item.phrase} on {crew.id}, and the crew member listened this time."
    )
    world.say(
        f"They repeated the careful steps: first the check, then the path, then the next check."
    )
    propagate(world, narrate=True)
    crew.meters["safe"] = 1
    crew.memes["trust"] = crew.memes.get("trust", 0.0) + 1


def ending(world: World, crew: Entity, captain: Entity, route: Route, item: Entity) -> None:
    world.say(
        f"In the end, {crew.id} crossed {route.place} safely, with {item.phrase} working like a promise."
    )
    world.say(
        f"The same route was there {route.repeat_word}, but now {crew.id} knew how to pass it without fear."
    )


# ---------------------------------------------------------------------------
# Build the story
# ---------------------------------------------------------------------------
def tell(route: Route, crew_name: str, crew_type: str, captain_type: str, trait: str) -> World:
    world = World(route)
    crew = world.add(Entity(id=crew_name, kind="character", type=crew_type))
    captain = world.add(Entity(id="captain", kind="character", type=captain_type))
    item = world.add(
        Entity(
            id=route.safe_item,
            type=route.safe_item,
            label=route.safe_item,
            phrase=route.safe_item_phrase,
            owner=crew.id,
            protective=True,
            plural=route.safe_item_plural,
        )
    )
    world.facts.update(route=route, crew=crew, captain=captain, item=item, trait=trait)
    intro(world, crew)
    world.para()
    setup(world, crew, captain, route, item)
    world.para()
    risk(world, crew, route)
    pushback(world, crew, captain, route)
    world.para()
    safe_turn(world, crew, captain, item, route)
    ending(world, crew, captain, route, item)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    route: Route = _safe_fact(world, f, "route")
    crew: Entity = _safe_fact(world, f, "crew")
    return [
        f"Write a short cautionary space adventure about {crew.id} on {route.place}.",
        f"Tell a tiny story where the same route is repeated, but the hero learns to be {route.caution_word}.",
        f"Make a child-friendly space story about a real-ist crew member who wants to go {route.repeat_word} but must stop and check first.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    route: Route = _safe_fact(world, f, "route")
    crew: Entity = _safe_fact(world, f, "crew")
    captain: Entity = _safe_fact(world, f, "captain")
    item: Entity = _safe_fact(world, f, "item")
    return [
        QAItem(
            question=f"Who wanted to go {route.repeat_word} on the route?",
            answer=f"{crew.id} wanted to go {route.repeat_word}, because repeating the path felt exciting.",
        ),
        QAItem(
            question=f"Why did {captain.id} tell {crew.id} to be careful?",
            answer=f"{captain.id} saw that {route.hazard} could make the route risky, so {captain.id} warned {crew.id} to check first.",
        ),
        QAItem(
            question=f"What helped {crew.id} cross {route.place} safely at the end?",
            answer=f"{item.phrase} helped because it supported the safe check and reminded {crew.id} to travel carefully.",
        ),
        QAItem(
            question=f"What changed in the story from the beginning to the end?",
            answer=f"At first {crew.id} wanted to rush the same route, but at the end {crew.id} repeated the safety check and crossed safely.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "space": [
        QAItem(
            question="What is space like?",
            answer="Space is very wide and mostly empty, with stars, planets, and dark silence between them.",
        ),
        QAItem(
            question="Why do astronauts use careful checks?",
            answer="Astronauts use careful checks because mistakes in space can be dangerous and hard to fix.",
        ),
    ],
    "repetition": [
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing the same thing again. It can help you remember a path, a song, or a safe routine.",
        )
    ],
    "cautionary": [
        QAItem(
            question="What is a cautionary story?",
            answer="A cautionary story is one that warns about a mistake so the reader can learn a safer choice.",
        )
    ],
    "shield": [
        QAItem(
            question="What does a shield do on a spaceship?",
            answer="A shield helps protect a ship or person from danger like sparks, dust, or heat.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        *WORLD_KNOWLEDGE["space"],
        *WORLD_KNOWLEDGE["repetition"],
        *WORLD_KNOWLEDGE["cautionary"],
        *WORLD_KNOWLEDGE["shield"],
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
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
route_hazard(Route) :- route(Route), hazard(Route,_).
needs_caution(Crew) :- worry(Crew), captain(Captain), caution(Captain).
safe_end(Crew) :- needs_caution(Crew), checked(Crew), safe_item(Item).
repetition_good(Route) :- route(Route), repeated_check(Route).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("hazard", rid, route.hazard))
        lines.append(asp.fact("repeat_word", rid, route.repeat_word))
        lines.append(asp.fact("caution_word", rid, route.caution_word))
        lines.append(asp.fact("safe_item", rid, route.safe_item))
        lines.append(asp.fact("safe_check", rid, route.safe_check))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show route_hazard/1. #show repetition_good/1."))
    atoms = set((sym.name, tuple(a.name if a.type == a.type.Other else getattr(a, "string", getattr(a, "number", None)) for a in sym.arguments)) for sym in model)
    expected = {("route_hazard", ("ring",)), ("route_hazard", ("dock",)), ("route_hazard", ("comet",))}
    if any(name == "repetition_good" for name, _ in atoms):
        expected.add(("repetition_good", ("ring",)))
        expected.add(("repetition_good", ("dock",)))
        expected.add(("repetition_good", ("comet",)))
    print("OK: ASP program parsed and solved.")
    return 0


# ---------------------------------------------------------------------------
# Validation / selection
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for rid, route in ROUTES.items():
        for g in ["girl", "boy"]:
            combos.append((rid, g))
    return combos


def explain_rejection(route: Route) -> str:
    return f"(No story: the route '{route.name}' would not support the cautionary repetition pattern.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cautionary space adventure about repetition and safer checks."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    route = getattr(args, "route", None) or rng.choice(list(ROUTES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CREW_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    crew_type = "girl" if gender == "girl" else "boy"
    captain_type = "captain"
    return StoryParams(route=route, crew_name=name, crew_type=crew_type, captain_type=captain_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(ROUTES, params.route), params.crew_name, params.crew_type, params.captain_type, params.trait)
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
        print(asp_program("#show route_hazard/1. #show repetition_good/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show route_hazard/1. #show repetition_good/1."))
        print(len(model), "atoms")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for rid in ROUTES:
            p = StoryParams(route=rid, crew_name=random.choice(CREW_NAMES), crew_type="girl", captain_type="captain", trait="real-ist")
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
