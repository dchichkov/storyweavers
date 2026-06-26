#!/usr/bin/env python3
"""
A small fable-like story world about friendship, a risky proposal, an
aggravating twist, and a cautious ending.

This world is built around a simple moral pattern:
- one friend makes a proposal,
- the proposal aggravates a problem,
- friendship is tested,
- a cautionary twist teaches restraint.

The prose is driven by a tiny world model with physical meters and emotional
memes, plus an ASP twin for the reasonableness gate.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    problem: object | None = None
    proposer: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "crow", "rabbit", "hare", "mole"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"boy", "prince"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "princess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def possessive_name(self) -> str:
        return self.label or self.id
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    name: str
    mood: str
    affords: set[str] = field(default_factory=set)
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
class Proposal:
    id: str
    idea: str
    action: str
    danger: str
    risk_meter: str
    effect: str
    twist: str
    caution: str
    keyword: str
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
    place: str
    proposal: str
    hero: str
    friend: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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


def _r_aggravate(world: World) -> list[str]:
    out: list[str] = []
    fox = world.entities.get("proposer")
    problem = world.entities.get("problem")
    if not fox or not problem:
        return out
    if fox.memes.get("scheme", 0) < THRESHOLD:
        return out
    sig = ("aggravate",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    problem.meters["trouble"] = problem.meters.get("trouble", 0) + 1
    problem.meters["risk"] = problem.meters.get("risk", 0) + 1
    out.append("The little plan aggravated the trouble instead of soothing it.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not hero or not friend:
        return out
    if hero.memes.get("worry", 0) < THRESHOLD or friend.memes.get("care", 0) < THRESHOLD:
        return out
    sig = ("friendship",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    friend.memes["trust"] = friend.memes.get("trust", 0) + 1
    out.append("The friends listened to each other with softer hearts.")
    return out


CAUSAL_RULES = [_r_aggravate, _r_friendship]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "meadow": Place("the meadow", "bright", {"proposal", "twist"}),
    "bridge": Place("the bridge", "windy", {"proposal", "twist"}),
    "orchard": Place("the orchard", "quiet", {"proposal", "twist"}),
}

PROPOSALS = {
    "shortcut": Proposal(
        id="shortcut",
        idea="take a shortcut across the reeds",
        action="cross the reeds",
        danger="the reeds will shake and spill everyone into the mud",
        risk_meter="mud",
        effect="the path becomes muddy and slippery",
        twist="the reeds bend and reveal a hidden pond",
        caution="it is wiser to test a path before trusting it",
        keyword="aggravate",
    ),
    "race": Proposal(
        id="race",
        idea="race the wind home",
        action="race home",
        danger="the hurry will tangle their feet and tire them out",
        risk_meter="tired",
        effect="their legs grow sore and slow",
        twist="the wind changes and pushes them into a ditch",
        caution="fast plans can turn sharp when nobody looks ahead",
        keyword="proposal",
    ),
    "climb": Proposal(
        id="climb",
        idea="climb the old apple tree to prove bravery",
        action="climb the old apple tree",
        danger="a high branch may wobble and drop them down",
        risk_meter="afraid",
        effect="the bark scrapes their paws and frightens them",
        twist="a nest of sparrows appears and startles the climber",
        caution="brave does not mean careless",
        keyword="Twist",
    ),
}

HEROES = {
    "fox": "fox",
    "hare": "hare",
    "crow": "crow",
}

FRIENDS = {
    "hare": "hare",
    "mouse": "mouse",
    "crow": "crow",
    "turtle": "turtle",
}


def reasonableness_gate(place: Place, prop: Proposal) -> bool:
    return "proposal" in place.affords and "twist" in place.affords and bool(prop.idea)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, prop in PROPOSALS.items():
        lines.append(asp.fact("proposal", pid))
        lines.append(asp.fact("keyword", pid, prop.keyword))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, R) :- affords(P, proposal), proposal(R).
valid_story(P, R) :- valid(P, R), affords(P, twist).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return sorted((p, r) for p in PLACES for r in PROPOSALS if reasonableness_gate(_safe_lookup(PLACES, p), _safe_lookup(PROPOSALS, r)))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about friendship, a proposal, and a cautionary twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--proposal", choices=PROPOSALS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--name")
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
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "proposal", None) is None or c[1] == getattr(args, "proposal", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prop = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(sorted(HEROES))
    friend = getattr(args, "friend", None) or rng.choice(sorted(FRIENDS))
    return StoryParams(place=place, proposal=prop, hero=hero, friend=friend)


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    prop = _safe_lookup(PROPOSALS, params.proposal)
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero, label=params.name or params.hero))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend, label=params.friend))
    problem = world.add(Entity(id="problem", type="thing", label="the trouble"))
    proposer = world.add(Entity(id="proposer", kind="character", type=params.hero, label=params.name or params.hero))

    world.say(f"Once in {place.name}, a {hero.type} and a {friend.type} were friends who liked one another well.")
    world.say(f"One day, {hero.label} made a proposal to {prop.idea}.")
    proposer.memes["scheme"] = 1
    friend.memes["care"] = 1
    hero.memes["worry"] = 1
    problem.meters["trouble"] = 1

    world.para()
    world.say(f"But the proposal would {prop.danger}.")
    world.say(f"That was the sort of idea that could aggravate a small trouble into a bigger one.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"The friendship did not break, because {friend.label} spoke gently and asked for a slower plan.")
    world.say(f"Then came the Twist: {prop.twist}.")
    world.say(f"At last they remembered the cautionary lesson: {prop.caution}.")
    world.say(f"So they chose a careful path, and the meadow grew calm again.")

    world.facts.update(hero=hero, friend=friend, proposal=prop, place=place, problem=problem)
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "proposal")
    place = _safe_fact(world, world.facts, "place")
    return [
        f"Write a short fable about friendship in {place.name} that includes the word '{p.keyword}'.",
        f"Tell a child-friendly story where a proposal to {p.idea} goes wrong and teaches a cautionary lesson.",
        f"Write a gentle fable with a Twist, Friendship, and Cautionary ending about {p.action}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    prop: Proposal = _safe_fact(world, world.facts, "proposal")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    friend: Entity = _safe_fact(world, world.facts, "friend")
    place: Place = _safe_fact(world, world.facts, "place")
    return [
        QAItem(
            question=f"What proposal did {hero.label} make in {place.name}?",
            answer=f"{hero.label} made a proposal to {prop.idea}.",
        ),
        QAItem(
            question=f"Why did the proposal aggravate the trouble?",
            answer=f"It aggravated the trouble because {prop.danger}, so the small problem could have become worse.",
        ),
        QAItem(
            question=f"How did the friendship help at the end?",
            answer=f"{friend.label} spoke gently, and the friends chose a careful plan instead of rushing ahead.",
        ),
        QAItem(
            question=f"What was the cautionary lesson?",
            answer=f"The lesson was that {prop.caution}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    prop: Proposal = _safe_fact(world, world.facts, "proposal")
    return [
        QAItem(
            question="What is a proposal?",
            answer="A proposal is a plan or suggestion that someone offers for others to consider.",
        ),
        QAItem(
            question="What does aggravate mean?",
            answer="To aggravate means to make a problem worse or more annoying.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the reader expected.",
        ),
        QAItem(
            question="What is a cautionary tale?",
            answer="A cautionary tale is a story that warns readers to be careful and make wise choices.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the kind way people or animals care for one another and help each other.",
        ),
        QAItem(
            question="Why do fables often end with a lesson?",
            answer="Fables often end with a lesson so readers can remember the good choice the story teaches.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", proposal="shortcut", hero="fox", friend="hare"),
    StoryParams(place="bridge", proposal="race", hero="crow", friend="turtle"),
    StoryParams(place="orchard", proposal="climb", hero="hare", friend="mouse"),
]


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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, proposal) combos ({len(stories)} with story predicate):\n")
        for p, r in triples:
            print(f"  {p:10} {r}")
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
            header = f"### {p.hero} / {p.proposal} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
