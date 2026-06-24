#!/usr/bin/env python3
"""
storyworlds/worlds/van_frantic_soften_suspense_moral_value_transformation.py
=============================================================================

A small fable-like storyworld about a van, a frantic scramble, and a choice
that softens into kindness. The simulated domain keeps the story grounded in
world state: a van can be loaded, a path can be blocked, a character can grow
frantic, and a helper can soften the tension by choosing a gentler action.

Seed premise:
A small van is meant to carry a fragile delivery across a short route. A child
or driver becomes frantic when the van is delayed by a stuck gate or a muddy
track. The turn comes when someone remembers a kinder, steadier method instead
of forcing the way through. The ending shows transformation: worry softens,
the van moves safely, and the lesson is stated as a moral.

The world features:
- Suspense: a delay, a blocked route, and a ticking need to arrive
- Moral Value: patience, honesty, kindness, and care over panic
- Transformation: frantic energy softens into calm action and a better ending
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    parcel: object | None = None
    van: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
        if not hasattr(self, "_tags"):
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
class Road:
    id: str
    label: str
    blocked_by: str = ""
    muddy: bool = False
    narrow: bool = False
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Cargo:
    id: str
    label: str
    fragile: bool = True
    important: bool = True
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Action:
    id: str
    verb: str
    risk: str
    softens: str
    moral: str
    transform: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.road: Road | None = None
        self.action: Action | None = None

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.road = _copy.deepcopy(self.road)
        w.action = _copy.deepcopy(self.action)
        return w


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    road = world.road
    if road is None:
        return out
    if child.memes.get("frantic", 0.0) >= THRESHOLD and road.blocked_by:
        sig = ("suspense", road.blocked_by)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["wait"] = child.meters.get("wait", 0.0) + 1
            helper.memes["care"] = helper.memes.get("care", 0.0) + 1
            out.append("The delay made the little van's work feel urgent.")
    if child.memes.get("softer", 0.0) >= THRESHOLD:
        sig = ("soften",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["frantic"] = 0.0
            child.memes["calm"] = child.memes.get("calm", 0.0) + 1
            helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
            out.append("The hard knot of worry loosened.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(action: Action, road: Road, cargo: Cargo,
         child_name: str, child_type: str, helper_name: str, helper_type: str) -> World:
    w = World()
    w.road = road
    w.action = action
    child = w.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="driver"))
    helper = w.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="guide"))
    van = w.add(Entity(id="van", kind="thing", type="van", label="little van"))
    parcel = w.add(Entity(id="cargo", kind="thing", type="cargo", label=cargo.label))

    for e in (child, helper, van, parcel):
        e.meters["state"] = 0.0
        e.memes["frantic"] = 0.0
        e.memes["softer"] = 0.0
        e.memes["patience"] = 0.0
        e.memes["kindness"] = 0.0
        e.memes["care"] = 0.0

    child.memes["frantic"] = 1.0
    van.meters["load"] = 1.0
    parcel.meters["safe"] = 1.0

    w.say(f"{child_name} had a little van and a fragile parcel to carry across {road.label}.")
    w.say(f"{helper_name} rode along, and the day already felt a little suspenseful because {road.blocked_by} blocked the way.")

    w.para()
    child.memes["frantic"] += 1.0
    w.say(f"{child_name} grew frantic when the van could not go forward. {action.risk.capitalize()} made the wait feel longer.")
    propagate(w)

    w.para()
    helper.memes["patience"] += 1.0
    helper.memes["kindness"] += 1.0
    child.memes["softer"] += 1.0
    w.say(f"Then {helper_name} spoke gently and chose a softer way. {action.softens.capitalize()}, and the tight feeling began to ease.")
    propagate(w)

    w.para()
    child.memes["moral"] = 1.0
    child.memes["transformed"] = 1.0
    w.say(f"{child_name} listened, took a slow breath, and helped clear the path with care.")
    w.say(f"At last the van rolled ahead, the parcel stayed safe, and {action.transform}.")
    w.say(f"The lesson was simple: {action.moral}")

    w.facts.update(
        child=child,
        helper=helper,
        van=van,
        cargo=parcel,
        road=road,
        action=action,
        blocked=bool(road.blocked_by),
        transformed=True,
    )
    return w


@dataclass
class StoryParams:
    road: str
    action: str
    cargo: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


ROADS = {
    "gate": Road(id="gate", label="the old gate road", blocked_by="a stuck gate", muddy=False, narrow=True),
    "mud": Road(id="mud", label="the muddy lane", blocked_by="a muddy patch", muddy=True, narrow=True),
    "bridge": Road(id="bridge", label="the little bridge road", blocked_by="a fallen crate", muddy=False, narrow=True),
}

ACTIONS = {
    "wait": Action(id="wait", verb="wait", risk="the delay made everyone frantic", softens="waiting a moment helped", moral="patience keeps trouble small", transform="the frantic feeling softened into calm"),
    "ask": Action(id="ask", verb="ask for help", risk="asking too loudly would only make the scene fussier", softens="a kind question helped", moral="kind words open better paths", transform="worry transformed into teamwork"),
    "clean": Action(id="clean", verb="clear the road", risk="forcing the mess could break the parcel", softens="careful hands softened the stubborn mess", moral="gentle effort works better than panic", transform="frantic pushing became careful helping"),
}

CARGOES = {
    "bread": Cargo(id="bread", label="fresh bread"),
    "seeds": Cargo(id="seeds", label="tiny seed packets"),
    "books": Cargo(id="books", label="library books"),
}

CHILD_NAMES = ["Milo", "Nina", "Tia", "Rowan", "Pip", "Lena", "Bram", "Iris"]
HELPER_NAMES = ["Aunt May", "Uncle Jo", "Mara", "Sol", "Oren", "Dina"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(r, a, c) for r in ROADS for a in ACTIONS for c in CARGOES]


def explain_rejection() -> str:
    return "(No story: this little fable needs a blocked road, a frantic moment, and a softening turn.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like van storyworld with suspense, moral value, and transformation.")
    ap.add_argument("--road", choices=ROADS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["woman", "man"])
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
              if (getattr(args, "road", None) is None or c[0] == getattr(args, "road", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "cargo", None) is None or c[2] == getattr(args, "cargo", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    road, action, cargo = rng.choice(list(combos))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or ("woman" if child_type == "boy" else "man")
    return StoryParams(
        road=road, action=action, cargo=cargo,
        child_name=getattr(args, "child_name", None) or rng.choice(CHILD_NAMES),
        child_type=child_type,
        helper_name=getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES),
        helper_type=helper_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable about {f['child'].label} and a little van crossing {f['road'].label}.",
        f"Tell a suspenseful story where the van cannot move because {f['road'].blocked_by}, and someone helps the worry soften.",
        f"Write a child-friendly moral story that ends with transformation from frantic to calm."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    road = f["road"]
    action = f["action"]
    return [
        QAItem(question=f"Who was the story about?", answer=f"It was about {child.label} and {helper.label}, with a little van on {road.label}."),
        QAItem(question=f"Why did the day feel suspenseful?", answer=f"It felt suspenseful because {road.blocked_by} blocked the road and the van could not move right away."),
        QAItem(question=f"What changed the frantic mood?", answer=f"{helper.label} used a softer way, which helped the frantic feeling soften into calm."),
        QAItem(question=f"What was the moral of the story?", answer=f"The moral was that {action.moral}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a van?", answer="A van is a road vehicle that can carry people or things from one place to another."),
        QAItem(question="What does frantic mean?", answer="Frantic means very worried or rushed, as if something important might go wrong."),
        QAItem(question="What does soften mean?", answer="Soften means to become gentler, calmer, or less hard."),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.road not in ROADS or params.action not in ACTIONS or params.cargo not in CARGOES:
        pass
    world = tell(_safe_lookup(ROADS, params.road), _safe_lookup(ACTIONS, params.action), _safe_lookup(CARGOES, params.cargo),
                 params.child_name, params.child_type, params.helper_name, params.helper_type)
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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  road: {world.road}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(R,A,C) :- road(R), action(A), cargo(C), blocked(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for r in ROADS:
        lines.append(asp.fact("road", r))
        lines.append(asp.fact("blocked", r))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for c in CARGOES:
        lines.append(asp.fact("cargo", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        return 0
    print("Mismatch:")
    print(" only python:", sorted(py - cl))
    print(" only asp:", sorted(cl - py))
    return 1


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
    StoryParams("gate", "wait", "bread", "Milo", "boy", "Mara", "woman"),
    StoryParams("mud", "ask", "seeds", "Nina", "girl", "Sol", "man"),
    StoryParams("bridge", "clean", "books", "Tia", "girl", "Aunt May", "woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
