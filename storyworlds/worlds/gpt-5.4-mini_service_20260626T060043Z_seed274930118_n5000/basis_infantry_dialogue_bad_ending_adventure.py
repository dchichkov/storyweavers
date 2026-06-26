#!/usr/bin/env python3
"""
Standalone story world: a small adventure about a basis camp, an infantry patrol,
dialogue, and a bad ending.

The world is intentionally narrow: a courier leaves a safe basis camp, follows a
trail, speaks with an infantry guard, and may still fail if the route choice is
wrong or the warning comes too late. The prose and the QA are driven from a
simulated world state rather than a fixed template.
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
    label: str = ""
    type: str = "thing"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    goal: object | None = None
    hero: object | None = None
    scout: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Location:
    id: str
    label: str
    basis: bool = False
    danger: float = 0.0
    BASIS_LOC: object | None = None
    FOREST: object | None = None
    RIDGE: object | None = None
    RIVER: object | None = None
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
class Route:
    id: str
    label: str
    from_loc: str
    to_loc: str
    risk: float
    clue: str
    blocked_by: str = ""
    dialogue_hint: str = ""
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
class Goal:
    id: str
    label: str
    phrase: str
    destination: str
    weight: str
    fragile: bool = False
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
    route: str
    goal: str
    hero_name: str
    hero_type: str
    scout_name: str
    scout_type: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.turn: int = 0
        self.route_taken: str = ""
        self.ending: str = ""

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

        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.turn = self.turn
        w.route_taken = self.route_taken
        w.ending = self.ending
        return w


BASIS_LOC = Location(id="basis", label="the basis camp", basis=True, danger=0.0)
FOREST = Location(id="forest", label="the dark forest", danger=0.4)
RIDGE = Location(id="ridge", label="the windy ridge", danger=0.7)
RIVER = Location(id="river", label="the broken river crossing", danger=0.9)

LOCATIONS = {x.id: x for x in [BASIS_LOC, FOREST, RIDGE, RIVER]}

ROUTES = {
    "forest": Route(
        id="forest",
        label="the forest trail",
        from_loc="basis",
        to_loc="forest",
        risk=0.4,
        clue="the pines could hide a trail marker",
        blocked_by="a fallen log",
        dialogue_hint="keep your voice low and watch the roots",
    ),
    "ridge": Route(
        id="ridge",
        label="the ridge path",
        from_loc="basis",
        to_loc="ridge",
        risk=0.7,
        clue="the ridge could see the whole valley",
        blocked_by="a hard gust of wind",
        dialogue_hint="hold the rope tight and don't look down",
    ),
    "river": Route(
        id="river",
        label="the river road",
        from_loc="basis",
        to_loc="river",
        risk=0.9,
        clue="the river crossing was the fastest way",
        blocked_by="a swollen bank",
        dialogue_hint="step carefully or the current will take the crate",
    ),
}

GOALS = {
    "message": Goal(id="message", label="sealed message", phrase="a sealed message for the field captain", destination="basis", weight="light", fragile=True),
    "rations": Goal(id="rations", label="ration crate", phrase="a ration crate for the infantry line", destination="basis", weight="heavy", fragile=False),
    "map": Goal(id="map", label="route map", phrase="a route map marked with safe paths", destination="basis", weight="thin", fragile=True),
}

NAMES = ["Arin", "Mira", "Tess", "Jon", "Kara", "Pavel", "Niko", "Lena"]
TRAITS = ["brave", "careful", "quick", "steady", "stubborn", "earnest"]


def route_danger(route: Route, goal: Goal) -> bool:
    return route.risk + (0.2 if goal.fragile else 0.0) >= 0.7


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for rid, route in ROUTES.items():
        for gid, goal in GOALS.items():
            if route_danger(route, goal):
                out.append((rid, gid))
    return out


@dataclass
class Record:
    world: World
    hero: Entity
    scout: Entity
    goal: Entity
    route: Route
    location: Location
    bad_ending: bool = False
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
    ap = argparse.ArgumentParser(description="Adventure story world with dialogue and a bad ending.")
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--scout-name")
    ap.add_argument("--scout-type", choices=["woman", "man"])
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
    if getattr(args, "route", None) and getattr(args, "goal", None) and not route_danger(_safe_lookup(ROUTES, getattr(args, "route", None)), _safe_lookup(GOALS, getattr(args, "goal", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "route", None) is None or c[0] == getattr(args, "route", None))
              and (getattr(args, "goal", None) is None or c[1] == getattr(args, "goal", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    route, goal = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    scout_type = getattr(args, "scout_type", None) or rng.choice(["woman", "man"])
    hero_name = getattr(args, "name", None) or rng.choice(NAMES)
    scout_name = getattr(args, "scout_name", None) or rng.choice(NAMES)
    if scout_name == hero_name:
        scout_name = rng.choice([n for n in NAMES if n != hero_name])
    return StoryParams(route=route, goal=goal, hero_name=hero_name, hero_type=hero_type,
                       scout_name=scout_name, scout_type=scout_type)


def set_up(params: StoryParams) -> Record:
    world = World()
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, traits=["little", rng_trait()], memes={"fear": 0.0, "duty": 1.0}))
    scout = world.add(Entity(id=params.scout_name, kind="character", type=params.scout_type, label="the infantry scout", memes={"duty": 1.0, "worry": 0.0}))
    goal = world.add(Entity(id=params.goal, kind="thing", type="supply", label=_safe_lookup(GOALS, params.goal).label, owner=hero.id, meters={"weight": 1.0}))
    route = _safe_lookup(ROUTES, params.route)
    loc = _safe_lookup(LOCATIONS, route.from_loc)
    return Record(world=world, hero=hero, scout=scout, goal=goal, route=route, location=loc)


def rng_trait() -> str:
    return random.choice(TRAITS)


def tell(rec: Record) -> Record:
    w, hero, scout, goal, route, loc = rec.world, rec.hero, rec.scout, rec.goal, rec.route, rec.location
    w.say(f"At {loc.label}, {hero.id} stood beside the basis tents with {goal.label}.")
    w.say(f"{hero.id} wanted to bring {goal.phrase} to the infantry line, and {hero.pronoun().capitalize()} felt ready for the road.")
    w.para()
    w.say(f"An infantry scout checked the trail and said, \"{route.dialogue_hint.capitalize()}.\"")
    w.say(f"{hero.id} answered, \"Then I will take {route.label} and be back before dark.\"")
    if route_danger(route, _safe_lookup(GOALS, rec.goal.id)):
        hero.memes["fear"] += 1.0
        scout.memes["worry"] += 1.0
        w.say(f"But {route.blocked_by} waited ahead, and the scout frowned at the risk.")
        w.say(f"\"That way can swallow a small traveler,\" {scout.id} said. \"Choose the wrong path, and the basis may lose the only safe copy.\"")
    w.para()
    taken = route
    w.route_taken = taken.id
    hero.meters["travel"] = 1.0
    if taken.risk >= 0.9:
        w.say(f"{hero.id} ignored the warning and moved fast toward {taken.label}.")
        w.say(f"The bank broke under {hero.pronoun('object')}, and the current grabbed {goal.label}.")
        w.say(f"{hero.id} cried out, but the water carried it away before the infantry could reach the shore.")
        rec.bad_ending = True
        w.ending = "lost"
    elif taken.risk >= 0.7:
        w.say(f"{hero.id} tried to hurry past the danger, but the wind and stones forced a stumble.")
        w.say(f"{goal.label} split open on the rocks, and the route map was ruined before the basis gates could close behind {hero.pronoun('object')}.")
        w.say(f"The scout shook her head in silence; the mission had failed at the edge of the dark.")
        rec.bad_ending = True
        w.ending = "ruined"
    else:
        w.say(f"{hero.id} took the forest trail, but a hidden log blocked the way and cost too much time.")
        w.say(f"By the time {hero.id} turned back, the infantry had already marched on without the message.")
        w.say(f"The basis lanterns burned low, and the night swallowed the chance to fix it.")
        rec.bad_ending = True
        w.ending = "too_late"
    w.facts = {"hero": hero, "scout": scout, "goal": goal, "route": route, "location": loc, "ending": w.ending}
    return rec


def generate(params: StoryParams) -> StorySample:
    rec = tell(set_up(params))
    return StorySample(
        params=params,
        story=rec.world.render(),
        prompts=generation_prompts(rec),
        story_qa=story_qa(rec),
        world_qa=world_knowledge_qa(rec),
        world=rec.world,
    )


def generation_prompts(rec: Record) -> list[str]:
    return [
        f'Write a short adventure story for a child that uses the word "basis" and includes dialogue with an infantry scout.',
        f"Tell a tense adventure where {rec.hero.id} must carry {rec.goal.label} from the basis camp but a dangerous route turns the plan into a bad ending.",
        f'Write a small story with dialogue about {rec.hero.id}, the basis, and the infantry, ending in a failure that changes the final image.',
    ]


def story_qa(rec: Record) -> list[QAItem]:
    w, hero, scout, goal, route = rec.world, rec.hero, rec.scout, rec.goal, rec.route
    return [
        QAItem(
            question=f"Who was the story about at the basis camp?",
            answer=f"It was about {hero.id}, who tried to carry {goal.label} for the infantry.",
        ),
        QAItem(
            question=f"What did the infantry scout warn {hero.id} about?",
            answer=f"The scout warned {hero.id} about {route.blocked_by} on {route.label}, because the path was risky.",
        ),
        QAItem(
            question=f"Why did the adventure end badly?",
            answer=f"It ended badly because {hero.id} chose a dangerous route and the goal was lost or ruined before the mission could be finished.",
        ),
        QAItem(
            question=f"What place was the starting point of the journey?",
            answer=f"The journey started at the basis camp.",
        ),
    ]


def world_knowledge_qa(rec: Record) -> list[QAItem]:
    return [
        QAItem(question="What is an infantry?", answer="Infantry are soldiers who move on foot instead of riding in a vehicle."),
        QAItem(question="What is a basis?", answer="A basis is a main camp or starting place where a group keeps supplies and plans the next move."),
        QAItem(question="Why do scouts speak to travelers?", answer="Scouts speak to travelers so they can warn them about danger and help them choose a safer path."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"route_taken={world.route_taken}")
    lines.append(f"ending={world.ending}")
    return "\n".join(lines)


CURATED = [
    StoryParams(route="river", goal="message", hero_name="Mira", hero_type="girl", scout_name="Kara", scout_type="woman"),
    StoryParams(route="ridge", goal="map", hero_name="Jon", hero_type="boy", scout_name="Pavel", scout_type="man"),
    StoryParams(route="forest", goal="rations", hero_name="Tess", hero_type="girl", scout_name="Lena", scout_type="woman"),
]


ASP_RULES = r"""
route_risky(R) :- route(R), risk(R, X), X >= 7.
goal_fragile(G) :- goal(G), fragile(G).
bad_story(R, G) :- route_risky(R), goal_fragile(G).
bad_story(R, G) :- route(R), goal(G), risk(R, X), X >= 9.
#show bad_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("risk", rid, int(r.risk * 10)))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        if g.fragile:
            lines.append(asp.fact("fragile", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show bad_story/2.")
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "bad_story"))
    py_set = {(r, g) for r, g in valid_combos()}
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(asp_set)} bad combinations).")
        return 0
    print("MISMATCH:")
    print("only ASP:", sorted(asp_set - py_set))
    print("only Python:", sorted(py_set - asp_set))
    return 1


def asp_bad_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bad_story/2."))
    return sorted(set(asp.atoms(model, "bad_story")))


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
        print(asp_program("#show bad_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_bad_combos()
        print(f"{len(combos)} bad route/goal combinations:")
        for rid, gid in combos:
            print(f"  {rid:7} {gid}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params_list = CURATED
    else:
        params_list = []
        seen = set()
        i = 0
        while len(params_list) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            p.seed = seed
            key = (p.route, p.goal, p.hero_name, p.scout_name)
            if key in seen:
                continue
            seen.add(key)
            params_list.append(p)

    samples = [generate(p) for p in params_list]

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
            header = f"### {p.hero_name}: {p.route} / {p.goal}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
