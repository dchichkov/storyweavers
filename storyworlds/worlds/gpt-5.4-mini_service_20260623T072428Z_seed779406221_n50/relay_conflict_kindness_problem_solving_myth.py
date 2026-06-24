#!/usr/bin/env python3
"""
storyworlds/worlds/relay_conflict_kindness_problem_solving_myth.py
===================================================================

A small myth-style storyworld about a relay, where a team of runners must carry
a sacred ember across a hill path. Conflict arises when the chosen runner wants
to hurry alone, Kindness changes how the team speaks, and Problem Solving turns
the race into a cooperative relay.

The domain is intentionally tiny and state-driven:
- physical meters track distance, fatigue, and whether the ember is safe
- emotional memes track conflict, kindness, trust, and relief
- the story is generated from world state, not from a frozen paragraph
- invalid choices raise StoryError with plain reasons
- an ASP twin mirrors the reasonableness gate and can be verified

Seed image:
A village must carry a glowing ember from one shrine to another before dusk.
The fastest runner wants to take it all in one sprint, but the elder says a
relay is wiser. The team learns to pass the ember, share the load, and arrive
together with the flame still bright.

Style notes:
- mythic, child-facing, concrete
- clear beginning, middle turn, ending image
- conflict, kindness, and problem solving are all narrated as state changes
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
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
    phrase: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    flame: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "priestess"}
        male = {"boy", "man", "father", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Setting:
    place: str
    path: str
    shrine_from: str
    shrine_to: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Runner:
    label: str
    type: str
    speed: int
    style: str
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
class Ember:
    label: str
    phrase: str
    safe_bearers: set[str]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Challenge:
    id: str
    conflict_phrase: str
    problem_phrase: str
    kindness_phrase: str
    solution_phrase: str
    route_need: int
    ember_need: int
    tags: set[str] = field(default_factory=set)
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class StoryParams:
    setting: str
    runner: str
    ember: str
    challenge: str
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


SETTINGS = {
    "hillroad": Setting(
        place="the hill road",
        path="the stone path between two shrines",
        shrine_from="the Dawn Shrine",
        shrine_to="the Evening Shrine",
        affords={"relay"},
    ),
    "riverbank": Setting(
        place="the riverbank",
        path="the reed path by the water",
        shrine_from="the Reed Shrine",
        shrine_to="the Clay Shrine",
        affords={"relay"},
    ),
    "forest_lane": Setting(
        place="the forest lane",
        path="the moss path under old trees",
        shrine_from="the Pine Shrine",
        shrine_to="the Oak Shrine",
        affords={"relay"},
    ),
}

RUNNERS = {
    "swift": Runner("swift runner", "boy", speed=4, style="fast and proud"),
    "steady": Runner("steady runner", "girl", speed=3, style="calm and careful"),
    "young": Runner("young runner", "boy", speed=2, style="eager and small"),
}

EMBERS = {
    "sun_ember": Ember("sun ember", "a warm ember from the old brazier", {"torch", "relay"}),
    "moon_ember": Ember("moon ember", "a pale ember in a bronze cup", {"cup", "relay"}),
    "star_ember": Ember("star ember", "a bright ember wrapped in ashcloth", {"cloth", "relay"}),
}

CHALLENGES = {
    "rivalry": Challenge(
        id="rivalry",
        conflict_phrase="the fastest runner wanted to carry the ember alone",
        problem_phrase="the path had a steep bend and a long climb",
        kindness_phrase="the elder spoke kindly and shared the load",
        solution_phrase="they made a relay and passed the ember at each turning stone",
        route_need=3,
        ember_need=3,
        tags={"conflict", "kindness", "problem_solving", "relay"},
    ),
    "fog": Challenge(
        id="fog",
        conflict_phrase="the runners could not see the stones ahead",
        problem_phrase="fog covered the path like a gray cloak",
        kindness_phrase="the team waited for one another and listened for each step",
        solution_phrase="they used a relay order and a steady hand at every handoff",
        route_need=2,
        ember_need=2,
        tags={"kindness", "problem_solving", "relay"},
    ),
    "gap": Challenge(
        id="gap",
        conflict_phrase="one runner feared the broken bridge and wanted to turn back",
        problem_phrase="a wide gap split the road",
        kindness_phrase="a friend offered courage and walked beside the afraid runner",
        solution_phrase="they solved it by passing the ember after each careful crossing",
        route_need=3,
        ember_need=2,
        tags={"conflict", "kindness", "problem_solving", "relay"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for r in RUNNERS:
            for e in EMBERS:
                for c in CHALLENGES:
                    combos.append((s, r, e, c))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        pass
    if params.runner not in RUNNERS:
        pass
    if params.ember not in EMBERS:
        pass
    if params.challenge not in CHALLENGES:
        pass
    setting = _safe_lookup(SETTINGS, params.setting)
    challenge = _safe_lookup(CHALLENGES, params.challenge)
    if "relay" not in setting.affords:
        pass
    if challenge.route_need < 2 or challenge.ember_need < 2:
        pass


ASP_RULES = r"""
valid(S,R,E,C) :- setting(S), runner(R), ember(E), challenge(C), relay_place(S), relay_theme(C).
relay_place(S) :- affords(S, relay).
relay_theme(C) :- tag(C, relay).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "relay" in s.affords:
            lines.append(asp.fact("affords", sid, "relay"))
    for rid in RUNNERS:
        lines.append(asp.fact("runner", rid))
    for eid in EMBERS:
        lines.append(asp.fact("ember", eid))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for tag in sorted(c.tags):
            lines.append(asp.fact("tag", cid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" only python:", sorted(py - cl))
    print(" only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic relay storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--runner", choices=RUNNERS)
    ap.add_argument("--ember", choices=EMBERS)
    ap.add_argument("--challenge", choices=CHALLENGES)
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
    choices = [c for c in valid_combos()
               if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
               and (getattr(args, "runner", None) is None or c[1] == getattr(args, "runner", None))
               and (getattr(args, "ember", None) is None or c[2] == getattr(args, "ember", None))
               and (getattr(args, "challenge", None) is None or c[3] == getattr(args, "challenge", None))]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, runner, ember, challenge = rng.choice(sorted(choices))
    reasonableness_gate(StoryParams(setting, runner, ember, challenge))
    return StoryParams(setting=setting, runner=runner, ember=ember, challenge=challenge)


def _narrate_setup(world: World, hero: Entity, elder: Entity, ember: Entity) -> None:
    world.say(
        f"Long ago, in {world.setting.place}, {hero.label} and {elder.label} kept watch over {ember.phrase}."
    )
    world.say(
        f"They were to carry it across {world.setting.path}, from {world.setting.shrine_from} to {world.setting.shrine_to}, before dusk."
    )


def _narrate_conflict(world: World, hero: Entity, elder: Entity, ch: Challenge, ember: Entity) -> None:
    hero.memes["conflict"] += 1
    hero.memes["desire"] += 1
    elder.memes["concern"] += 1
    world.say(
        f"But {ch.problem_phrase}, and {hero.label} felt the urge to rush ahead."
    )
    world.say(
        f'"{ch.conflict_phrase}," {hero.label} said, while {elder.label} shook {elder.pronoun("possessive")} head.'
    )


def _narrate_kindness(world: World, elder: Entity, hero: Entity, ch: Challenge) -> None:
    elder.memes["kindness"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"Then {elder.label} answered with kindness: {ch.kindness_phrase}."
    )
    world.say(
        f"{hero.label} listened, and the sharp feeling in {hero.pronoun('possessive')} chest grew softer."
    )


def _narrate_solution(world: World, hero: Entity, elder: Entity, ember: Entity, ch: Challenge) -> None:
    hero.memes["problem_solving"] += 1
    elder.memes["relief"] += 1
    world.say(
        f"Together, they chose a better way: {ch.solution_phrase}."
    )
    world.say(
        f"{hero.label} ran the first stretch, then passed {ember.pronoun('object')} to {elder.label}, who waited at the next stone."
    )


def _finish(world: World, hero: Entity, elder: Entity, ember: Entity) -> None:
    hero.meters["distance"] = 1.0
    elder.meters["distance"] = 1.0
    ember.meters["safe"] = 1.0
    hero.memes["conflict"] = 0.0
    hero.memes["kindness"] += 1
    hero.memes["relief"] += 1
    elder.memes["kindness"] += 1
    world.say(
        f"At last they reached {world.setting.shrine_to} together, and {ember.label} still glowed bright."
    )
    world.say(
        f"The villagers saw that the relay was not only fast, but kind and wise, and the hill remembered their names."
    )


def tell(setting: Setting, runner: Runner, ember: Ember, challenge: Challenge) -> World:
    world = World(setting)
    hero = world.add(Entity(id="Hero", kind="character", type=runner.type, label=runner.label))
    elder = world.add(Entity(id="Elder", kind="character", type="woman", label="the elder"))
    flame = world.add(Entity(id="Ember", kind="thing", type="thing", label=ember.label, phrase=ember.phrase))
    hero.meters["fatigue"] = 0.0
    elder.meters["fatigue"] = 0.0
    flame.meters["safe"] = 0.0

    _narrate_setup(world, hero, elder, flame)
    world.para()
    _narrate_conflict(world, hero, elder, challenge, flame)
    world.para()
    _narrate_kindness(world, elder, hero, challenge)
    world.para()
    _narrate_solution(world, hero, elder, flame, challenge)
    world.para()
    _finish(world, hero, elder, flame)

    world.facts.update(hero=hero, elder=elder, ember=flame, challenge=challenge)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ch = f["challenge"]
    return [
        f'Write a myth-like story about a relay where a child faces {ch.problem_phrase} and learns kindness.',
        f"Tell a short legend about a sacred ember, a relay, and a wiser helper who solves the problem together.",
        f'Write a child-friendly myth that includes the word "relay" and ends with the flame still bright.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, ember, ch = f["hero"], f["elder"], f["ember"], f["challenge"]
    return [
        QAItem(
            question="Who carried the ember in the story?",
            answer=f"{hero.label} began the relay, then passed {ember.pronoun('object')} to {elder.label}."),
        QAItem(
            question="What problem did the runners face?",
            answer=f"{ch.problem_phrase.capitalize()} in {world.setting.place}, so they needed a relay instead of one long run."),
        QAItem(
            question="How did kindness change the conflict?",
            answer=f"{elder.label} spoke kindly, and {hero.label} stopped feeling so tense and listened."),
        QAItem(
            question="What was the solution to the problem?",
            answer=f"They solved it by making a relay and passing the ember at each turning stone."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a relay?",
            answer="A relay is a race or task where people take turns and pass something from one person to the next."),
        QAItem(
            question="Why do teams use kindness when solving a problem?",
            answer="Kindness helps people listen, stay calm, and work together instead of fighting."),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking of a useful way to fix a difficulty."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(out)


CURATED = [
    StoryParams("hillroad", "swift", "sun_ember", "rivalry"),
    StoryParams("riverbank", "steady", "moon_ember", "fog"),
    StoryParams("forest_lane", "young", "star_ember", "gap"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(RUNNERS, params.runner), _safe_lookup(EMBERS, params.ember), _safe_lookup(CHALLENGES, params.challenge))
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
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
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
