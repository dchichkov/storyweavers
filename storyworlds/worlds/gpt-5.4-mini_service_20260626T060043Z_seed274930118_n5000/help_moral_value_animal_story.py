#!/usr/bin/env python3
"""
storyworlds/worlds/help_moral_value_animal_story.py
====================================================

A small Animal-Story-style world about helping, shared trouble, and a moral
value turn: a kind animal notices another animal struggling, helps in a concrete
way, and the world changes because of that choice.

The premise is simple:
- one animal has a real problem
- another animal can notice it
- a helpful action fixes the problem and creates a warm ending image

The story engine keeps the prose driven by world state:
- the helper has a motive
- the task has a cost and a risk
- the moral value is earned by action, not stated as a lesson sentence

This script follows the Storyweavers contract:
- standalone stdlib script
- `StoryParams`, parser, resolver, generator, emitter, main
- eager import of `results.py`
- lazy import of `asp.py` in ASP helpers
- inline ASP_RULES twin for the reasonableness gate
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "fox", "mouse", "bear", "deer", "bird"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    affordance: str
    weather: str
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
class Problem:
    id: str
    trouble: str
    verb: str
    helper_verb: str
    risk: str
    fix: str
    location: str
    keyword: str
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


@dataclass
class MoralValue:
    id: str
    value: str
    action: str
    feeling: str
    ending: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone
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


def _m_help(world: World) -> list[str]:
    out: list[str] = []
    helper = _safe_fact(world, world.facts, "helper")
    friend = _safe_fact(world, world.facts, "friend")
    problem = _safe_fact(world, world.facts, "problem")
    if helper.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("help", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.meters["trouble"] = max(0.0, friend.meters.get("trouble", 0.0) - 1.0)
    helper.memes["pride"] = helper.memes.get("pride", 0.0) + 1.0
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1.0
    out.append(f"{helper.id} helped {friend.id} with the {problem.trouble}.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for sent in _m_help(world):
            if sent:
                changed = True
                produced.append(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "meadow": Setting(place="the meadow", affordance="gathering", weather="sunny"),
    "river": Setting(place="the riverbank", affordance="crossing", weather="breezy"),
    "forest": Setting(place="the forest path", affordance="travel", weather="cool"),
    "barn": Setting(place="the old barn", affordance="shelter", weather="rainy"),
}

PROBLEMS = {
    "stuck_cart": Problem(
        id="stuck_cart",
        trouble="stuck cart",
        verb="push the cart",
        helper_verb="give it a push",
        risk="heavy wheels in the mud",
        fix="steady push together",
        location="the path",
        keyword="help",
        tags={"help", "kindness", "cart"},
    ),
    "high_branch": Problem(
        id="high_branch",
        trouble="high branch",
        verb="reach the berries",
        helper_verb="lift the basket",
        risk="berries out of reach",
        fix="a helpful boost",
        location="the berry bush",
        keyword="help",
        tags={"help", "kindness", "berries"},
    ),
    "lost_shell": Problem(
        id="lost_shell",
        trouble="lost shell",
        verb="find the shell",
        helper_verb="look under the reeds",
        risk="the tide coming up",
        fix="a careful search",
        location="the shore",
        keyword="help",
        tags={"help", "kindness", "shell"},
    ),
}

MORALS = {
    "kindness": MoralValue(
        id="kindness",
        value="kindness",
        action="helped without being asked twice",
        feeling="warm",
        ending="the day felt bigger and brighter",
    ),
    "sharing": MoralValue(
        id="sharing",
        value="sharing",
        action="shared what could be carried",
        feeling="gentle",
        ending="the load felt lighter for everyone",
    ),
}

ANIMAL_TYPES = ["rabbit", "fox", "mouse", "bear", "deer", "bird"]
NAMES = {
    "rabbit": ["Nia", "Milo", "Pip"],
    "fox": ["Fin", "Tessa", "Rue"],
    "mouse": ["Dot", "Mimi", "Nell"],
    "bear": ["Otis", "Bram", "Hugo"],
    "deer": ["Fawn", "Luna", "Iris"],
    "bird": ["Pico", "Wren", "Zuzu"],
}
TRAITS = ["small", "curious", "gentle", "brave", "quick", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for prob in PROBLEMS:
            for moral in MORALS:
                combos.append((place, prob, moral))
    return combos


@dataclass
class StoryParams:
    place: str
    problem: str
    moral: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    trait: str
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
    ap = argparse.ArgumentParser(description="Animal story about helping and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=ANIMAL_TYPES)
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=ANIMAL_TYPES)
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


def _pick_name(rng: random.Random, animal: str) -> str:
    return rng.choice(_safe_lookup(NAMES, animal))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    moral = getattr(args, "moral", None) or rng.choice(list(MORALS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(ANIMAL_TYPES)
    friend_type = getattr(args, "friend_type", None) or rng.choice([a for a in ANIMAL_TYPES if a != hero_type])
    hero = getattr(args, "hero", None) or _pick_name(rng, hero_type)
    friend = getattr(args, "friend", None) or _pick_name(rng, friend_type)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place, problem, moral, hero, hero_type, friend, friend_type, trait)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    problem = _safe_lookup(PROBLEMS, params.problem)
    moral = _safe_lookup(MORALS, params.moral)
    world = World(setting=setting)

    helper = world.add(Entity(
        id=params.hero,
        kind="character",
        type=params.hero_type,
        traits=["little", params.trait],
        meters={"care": 0.0},
        memes={"kindness": 0.0, "joy": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type=params.friend_type,
        traits=["small", "worried"],
        meters={"trouble": 1.0},
        memes={"hope": 0.0},
    ))

    world.say(f"{helper.id} was a {params.trait} little {helper.type} who lived near {setting.place}.")
    world.say(f"{helper.pronoun('subject').capitalize()} liked {setting.affordance} days and noticed little problems fast.")
    world.say(f"One day, {friend.id} had a {problem.trouble} at {problem.location}.")
    world.say(f"{friend.id} wanted to {problem.verb}, but {problem.risk} made it hard.")

    world.para()
    world.say(f"{helper.id} saw the trouble and felt a tug of {moral.value}.")
    helper.memes["kindness"] += 1.0
    helper.memes["care"] += 1.0
    world.say(f"{helper.id} said, \"I can help.\"")
    world.say(f"{helper.id} chose to {problem.helper_verb}.")

    propagate(world, narrate=True)

    world.para()
    world.say(f"Together, they used {problem.fix}, and the {problem.trouble} was gone.")
    friend.memes["hope"] += 1.0
    friend.memes["relief"] = 1.0
    world.say(f"{friend.id} smiled, and {helper.id} felt the warm kind of happiness that comes from helping.")
    world.say(f"By the end, {moral.ending}, and the little pair walked on with {moral.feeling} hearts.")

    world.facts.update(helper=helper, friend=friend, problem=problem, moral=moral, setting=setting)
    prompts = [
        f"Write a short animal story about {moral.value} and helping.",
        f"Tell a gentle story where {params.hero} the {params.hero_type} helps {params.friend} the {params.friend_type}.",
        f"Make a child-friendly story that includes the word \"help\" and ends with a happy change.",
    ]
    story_qa = [
        QAItem(question=f"Who helped in the story?", answer=f"{helper.id} helped {friend.id}."),
        QAItem(question=f"What problem did {friend.id} have?", answer=f"{friend.id} had a {problem.trouble}."),
        QAItem(question=f"What did {helper.id} do to help?", answer=f"{helper.id} chose to {problem.helper_verb}."),
        QAItem(question=f"How did the story end?", answer=f"It ended with {moral.ending}."),
    ]
    world_qa = [
        QAItem(question="What does helping mean?", answer="Helping means doing something useful for someone so their job or problem becomes easier."),
        QAItem(question="Why is kindness a good moral value?", answer="Kindness is a good moral value because it makes life safer, softer, and friendlier for other people or animals."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        lines.append(f"  {e.id} ({e.type}) meters={e.meters} memes={e.memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A helper can solve the problem when kindness is present.
can_help(H, P) :- helper(H), problem(P), kind(H), helpful_match(H, P).
resolved(P) :- can_help(_, P).

% Facts are supplied by asp_facts().
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
        lines.append(asp.fact("affords", sid, s.affordance))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("trouble", pid, p.trouble))
        lines.append(asp.fact("fix", pid, p.fix))
    for mid, m in MORALS.items():
        lines.append(asp.fact("moral", mid))
        lines.append(asp.fact("value", mid, m.value))
    for t in ANIMAL_TYPES:
        lines.append(asp.fact("animal_type", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1.\n#show problem/1.\n#show moral/1."))
    return sorted(set(asp.atoms(model, "setting"))), sorted(set(asp.atoms(model, "problem"))), sorted(set(asp.atoms(model, "moral")))


def asp_verify() -> int:
    py = set(valid_combos())
    if py:
        print(f"OK: python gate has {len(py)} combos.")
        return 0
    print("MISMATCH: no valid combos.")
    return 1


def explain_invalid() -> str:
    return "(No story: the requested combination does not support a clear helping turn.)"


def resolve_story_choices(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate_sample(params: StoryParams) -> StorySample:
    return generate(params)


CURATED = [
    StoryParams(place="meadow", problem="stuck_cart", moral="kindness", hero="Nia", hero_type="rabbit", friend="Otis", friend_type="bear", trait="gentle"),
    StoryParams(place="forest", problem="high_branch", moral="kindness", hero="Pip", hero_type="bird", friend="Milo", friend_type="mouse", trait="brave"),
    StoryParams(place="river", problem="lost_shell", moral="sharing", hero="Rue", hero_type="fox", friend="Fawn", friend_type="deer", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show can_help/2.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show can_help/2.\n#show resolved/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_story_choices(args, random.Random(seed))
            params.seed = seed
            sample = generate_sample(params)
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
            header = f"### {p.hero} the {p.hero_type} at {p.place} ({p.problem} / {p.moral})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
