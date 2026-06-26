#!/usr/bin/env python3
"""
tuvwx_lend_surround_problem_solving_myth.py
===========================================

A small myth-like storyworld about a stubborn problem, a helpful lending act,
and a circle of allies who surround danger until a clever fix can be made.

The seed words are woven into the world in an in-story way:
- tuvwx: the old shrine-name of a five-stone pattern used for guidance
- lend: a sacred act of temporary giving
- surround: the encircling move that keeps trouble from escaping
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ally: object | None = None
    hero: object | None = None
    problem: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "queen", "priestess"}
        masculine = {"boy", "man", "father", "king", "priest"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
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
    sky: str
    provides: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    fits: set[str]
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
class Problem:
    id: str
    label: str
    verb: str
    peril: str
    zone: set[str]
    needs: str
    tags: set[str] = field(default_factory=set)
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.state: dict[str, float] = {"harm": 0.0, "calm": 0.0, "wonder": 0.0}

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

    def items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.state = dict(self.state)
        return clone


def _narrate_problem(world: World, actor: Entity, problem: Problem) -> None:
    actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
    world.state["harm"] += 1
    world.say(
        f"{actor.id} saw that {problem.label} was stirring again near {world.setting.place}."
    )
    world.say(
        f"The trouble had a way of pressing against everything it touched, as if it wanted to grow."
    )


def _apply_surround(world: World, actor: Entity, problem: Problem, allies: list[Entity]) -> None:
    if ("surround", problem.id) in world.fired:
        return
    world.fired.add(("surround", problem.id))
    world.state["calm"] += 1
    actor.memes["resolve"] = actor.memes.get("resolve", 0.0) + 1
    for ally in allies:
        ally.memes["bond"] = ally.memes.get("bond", 0.0) + 1
    names = ", ".join(a.id for a in allies)
    world.say(
        f"Then {actor.id} called {names} to surround the danger, so it could not race away."
    )


def _apply_lend(world: World, lender: Entity, receiver: Entity, tool: Entity, problem: Problem) -> None:
    if ("lend", tool.id) in world.fired:
        return
    world.fired.add(("lend", tool.id))
    receiver.memes["hope"] = receiver.memes.get("hope", 0.0) + 1
    tool.owner = receiver.id
    tool.worn_by = receiver.id
    world.state["wonder"] += 1
    world.say(
        f"{lender.id} chose to lend {receiver.pronoun('object')} {tool.phrase}, and the gift was only for the needed hour."
    )
    world.say(
        f"With {tool.label} in hand, {receiver.id} could answer {problem.label} without wasting strength."
    )


def _apply_fix(world: World, actor: Entity, tool: Entity, problem: Problem) -> None:
    if ("fix", problem.id) in world.fired:
        return
    world.fired.add(("fix", problem.id))
    if tool.label == problem.needs:
        world.state["harm"] = 0.0
        world.state["calm"] += 2
        actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
        world.say(
            f"At last {actor.id} used the {tool.label} to mend the problem, and the hard knot gave way."
        )
        world.say(
            f"The land breathed easier, because the right tool had met the right need."
        )


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        harm_before = world.state["harm"]
        for hero in world.characters():
            if hero.memes.get("worry", 0.0) >= THRESHOLD and world.state["harm"] >= THRESHOLD:
                changed = True
                world.state["wonder"] += 0.5
        if world.state["harm"] != harm_before:
            changed = True


SETTINGS = {
    "grove": Setting(place="the moonlit grove", sky="silver", provides={"rope", "baskets"}),
    "river": Setting(place="the river bend", sky="blue", provides={"boats", "nets"}),
    "mountain": Setting(place="the high mountain shrine", sky="gold", provides={"stones", "bells"}),
}

PROBLEMS = {
    "floodgate": Problem(
        id="floodgate",
        label="the floodgate",
        verb="bursting",
        peril="water was spilling into the path",
        zone={"river"},
        needs="rope",
        tags={"water", "gate", "surround"},
    ),
    "thornwall": Problem(
        id="thornwall",
        label="the thornwall",
        verb="spreading",
        peril="brambles were closing the trail",
        zone={"grove"},
        needs="basket",
        tags={"thorn", "trail", "surround"},
    ),
    "bellstorm": Problem(
        id="bellstorm",
        label="the bellstorm",
        verb="clanging",
        peril="the shrine bells were striking too hard",
        zone={"mountain"},
        needs="stone",
        tags={"sound", "shrine", "tuvwx"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a strong rope",
        helps="tie the wild parts together",
        fits={"floodgate"},
    ),
    "basket": Tool(
        id="basket",
        label="basket",
        phrase="a wide basket",
        helps="carry away thorns",
        fits={"thornwall"},
    ),
    "stone": Tool(
        id="stone",
        label="stone",
        phrase="a smooth stone",
        helps="steady the shrine song",
        fits={"bellstorm"},
    ),
}

HEROES = {
    "girl": ["Asha", "Mira", "Nia", "Tala", "Rina"],
    "boy": ["Bram", "Kian", "Orin", "Soren", "Eli"],
}

ALLIES = ["old fox", "river-heron", "lamp-bearer", "silent sister", "village child"]


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    gender: str
    ally: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth-like problem-solving storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--ally")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for prob_id, prob in PROBLEMS.items():
            if place not in prob.zone:
                continue
            for tool_id, tool in TOOLS.items():
                if prob_id in tool.fits:
                    combos.append((place, prob_id, tool_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "problem", None) and getattr(args, "tool", None):
        if getattr(args, "problem", None) not in _safe_lookup(TOOLS, getattr(args, "tool", None)).fits:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(HEROES, gender))
    ally = getattr(args, "ally", None) or rng.choice(ALLIES)
    return StoryParams(place=place, problem=problem, tool=tool, name=name, gender=gender, ally=ally)


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    prob = _safe_lookup(PROBLEMS, params.problem)
    tool_cfg = _safe_lookup(TOOLS, params.tool)
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    ally = world.add(Entity(id=params.ally.replace(" ", "_"), kind="character", type="thing", label=params.ally))
    tool = world.add(Entity(id=tool_cfg.id, type=tool_cfg.label, label=tool_cfg.label, phrase=tool_cfg.phrase, owner=hero.id, worn_by=hero.id))
    problem = world.add(Entity(id=prob.id, type="problem", label=prob.label))

    world.say(
        f"Long ago, in {setting.place}, {hero.id} listened for the old word tuvwx, "
        f"which the elders used when a hard task needed a clear mind."
    )
    world.say(
        f"{hero.id} loved to lend a hand, because in that country a gift given for a single need was still a kind of treasure."
    )
    world.para()
    _narrate_problem(world, hero, prob)
    world.say(
        f"The trouble was {prob.peril}, and only {tool.label} could answer it."
    )
    world.say(
        f"So {hero.id} went to {setting.place} and asked {ally.label if ally.label else params.ally} to help surround the danger."
    )
    _apply_surround(world, hero, problem, [ally])
    world.para()
    lender = ally
    _apply_lend(world, lender, hero, tool, problem)
    _apply_fix(world, hero, tool, problem)
    world.say(
        f"By dawn the place was calm again, and the people said the circle of help had become a little myth of its own."
    )
    world.facts.update(hero=hero, ally=ally, tool=tool, problem_cfg=prob, setting=setting)
    return world


ASP_RULES = r"""
reachable(Place, Problem, Tool) :- place(Place), problem(Problem), tool(Tool),
                                  solves(Tool, Problem), occurs_in(Problem, Place).
compatible(Place, Problem, Tool) :- reachable(Place, Problem, Tool).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for p in sorted(s.provides):
            lines.append(asp.fact("provides", pid, p))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("occurs_in", pid, next(iter(p.zone))))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(t.fits):
            lines.append(asp.fact("solves", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    clingo_set = set(asp.atoms(model, "compatible"))
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for children that includes the word "tuvwx" and shows a problem being solved by surrounding it first.',
        f"Tell a gentle legend where {f['hero'].id} must lend {f['hero'].pronoun('object')} strength to {f['problem_cfg'].label} at {f['setting'].place}.",
        f"Write a small story about help, patience, and a tool that is borrowed for one careful task.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ally = _safe_fact(world, f, "ally")
    prob = _safe_fact(world, f, "problem_cfg")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Who is the story about in {place}?",
            answer=f"It is about {hero.id}, who faced {prob.label} and learned to solve the trouble with help.",
        ),
        QAItem(
            question=f"What did {hero.id} ask {ally.label if ally.label else 'the ally'} to do?",
            answer=f"{hero.id} asked for help to surround {prob.label} so the trouble could not spread.",
        ),
        QAItem(
            question=f"Which thing was lent so the problem could be solved?",
            answer=f"{tool.phrase} was lent for the task, and it was the right thing for {prob.label}.",
        ),
        QAItem(
            question=f"Why was lending important in the story?",
            answer="Lending was important because the needed tool did not need to stay forever; it only had to help for the one hard moment.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to lend something?",
            answer="To lend something means to give it to someone for a while, with the plan that it will come back later.",
        ),
        QAItem(
            question="What does surround mean?",
            answer="To surround something means to stand or place things all around it.",
        ),
        QAItem(
            question="What is a problem in a story?",
            answer="A problem is the hard thing that makes the characters stop, think, and find a better way.",
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  state={world.state}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="grove", problem="thornwall", tool="basket", name="Asha", gender="girl", ally="old fox"),
    StoryParams(place="river", problem="floodgate", tool="rope", name="Bram", gender="boy", ally="river-heron"),
    StoryParams(place="mountain", problem="bellstorm", tool="stone", name="Mira", gender="girl", ally="lamp-bearer"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible/3."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
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
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
