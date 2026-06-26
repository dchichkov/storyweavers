#!/usr/bin/env python3
"""
A small nursery-rhyme story world about a shop, a hock, a register, and an
election twist.

The seed premise:
- Twist is a little helper in a market booth.
- A shiny toy is put in hock at the shop so it can be reclaimed later.
- The shop's register keeps track of coin and promise.
- An election for "best booth helper" turns tense when the vote tally seems lost.
- The twist: the register prints the missing tally, and Twist uses it to win fair.

The prose is built from a live world model with physical meters and emotional
memes, and the story stays in a child-friendly nursery-rhyme cadence.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    badge: object | None = None
    clerk: object | None = None
    hero: object | None = None
    register: object | None = None
    toy: object | None = None
    voter1: object | None = None
    voter2: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"coin": 0.0, "lost": 0.0, "order": 0.0, "tally": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "hope": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    cozy: str
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
class Item:
    label: str
    phrase: str
    value: int
    hockable: bool = True
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    w: object | None = None
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w
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


def _r_register_prints(world: World) -> list[str]:
    out: list[str] = []
    reg = world.entities.get("register")
    if not reg or reg.meters["order"] < THRESHOLD:
        return out
    sig = ("register_prints",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if reg.meters["tally"] >= THRESHOLD:
        out.append("The register rang a bright ding-dong sound.")
        out.append("It printed a little slip with the votes in a row.")
    return out


def _r_hock_settled(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("toy")
    hero = world.entities.get("Twist")
    clerk = world.entities.get("Clerk")
    if not item or not hero or not clerk:
        return out
    if item.meters["coin"] < THRESHOLD or hero.memes["hope"] < THRESHOLD:
        return out
    sig = ("hock_settled",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["coin"] += 1
    hero.memes["joy"] += 1
    clerk.meters["order"] += 1
    out.append("The hocked toy could come home again, neat and bright.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    sents: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_register_prints, _r_hock_settled):
            out = rule(world)
            if out:
                changed = True
                sents.extend(out)
    if narrate:
        for s in sents:
            world.say(s)
    return sents


@dataclass
class StoryParams:
    place: str
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


PLACES = {
    "market": Place(name="the market", cozy="busy and bright", affords={"hock", "register", "election"}),
    "fair": Place(name="the fair", cozy="round and merry", affords={"hock", "register", "election"}),
}

NAMES = ["Twist", "Pip", "Merry", "Dot", "Nan"]


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    hero = world.add(Entity(id="Twist", kind="character", type="child", label="Twist"))
    clerk = world.add(Entity(id="Clerk", kind="character", label="the clerk", type="woman"))
    voter1 = world.add(Entity(id="Moss", kind="character", label="Moss", type="boy"))
    voter2 = world.add(Entity(id="Nia", kind="character", label="Nia", type="girl"))
    register = world.add(Entity(id="register", type="thing", label="register"))
    toy = world.add(Entity(id="toy", type="thing", label="toy", phrase="a tin-top toy", owner="Twist", caretaker="Clerk"))
    badge = world.add(Entity(id="badge", type="thing", label="badge", phrase="a bright blue badge", owner="Twist"))
    world.facts.update(hero=hero, clerk=clerk, voter1=voter1, voter2=voter2, register=register, toy=toy, badge=badge)
    return world


def tell_story(world: World) -> None:
    hero = world.get("Twist")
    clerk = world.get("Clerk")
    toy = world.get("toy")
    reg = world.get("register")
    world.say(f"Twist was a tiny child at {world.place.name}, in a place {world.place.cozy}.")
    world.say("He loved a soft little song of clicks and clinks, with numbers in a row.")
    world.say("One day he hocked his tin-top toy so it could rest behind the counter.")
    world.say(f"The {toy.label} sat safe by the shelf, and the {reg.label} kept watch like a bean.")
    world.para()
    world.say("Then came the election, round and fair, for the best booth helper there.")
    world.say("Twist wanted to win by count and cheer, but the vote slip went missing near.")
    world.say("Twist's joy turned small; his worry grew, for Moss and Nia had voted too.")
    hero.memes["worry"] += 1
    reg.meters["order"] += 1
    world.para()
    world.say("The clerk peeped down, then tapped the drawer, and shook the register once more.")
    reg.meters["tally"] += 1
    propagate(world, narrate=True)
    world.say("Out slid the slip with the tally bright, and Twist saw the truth in morning light.")
    world.say("The votes were fair, the count was clear, and Twist got a ribbon sewn with cheer.")
    hero.memes["joy"] += 2
    hero.memes["pride"] += 1
    toy.meters["coin"] += 1
    world.facts["won"] = True
    world.facts["hock_settled"] = True


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    clerk = _safe_fact(world, world.facts, "clerk")
    reg = _safe_fact(world, world.facts, "register")
    toy = _safe_fact(world, world.facts, "toy")
    return [
        QAItem(
            question="Who was the story about?",
            answer="The story was about Twist, a tiny child at the market or fair.",
        ),
        QAItem(
            question="What did Twist hock?",
            answer="Twist hocked a tin-top toy so it could rest behind the counter until it came home again.",
        ),
        QAItem(
            question="Why did Twist get worried at the election?",
            answer="Twist got worried because the vote slip went missing, so the count did not look clear at first.",
        ),
        QAItem(
            question="What helped the election turn out fair?",
            answer="The register helped by showing the tally slip, so the vote could be read in a clear and fair way.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The votes were counted, Twist won a ribbon, and the hocked toy could come home again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a register?",
            answer="A register is a machine or drawer that keeps track of coins and totals.",
        ),
        QAItem(
            question="What does it mean to hock something?",
            answer="To hock something means to leave it with a shop until you can come back for it.",
        ),
        QAItem(
            question="What is an election?",
            answer="An election is a fair choice where people cast votes to pick who should win or lead.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short nursery-rhyme story about Twist, a hocked toy, a register, and an election.',
        'Tell a gentle story where the register reveals a missing tally and the child named Twist finds a fair turn.',
        'Write a rhyme-like tale for a young child that includes the words hock, register, and election.',
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    lines.append(asp.fact("thing", "toy"))
    lines.append(asp.fact("thing", "register"))
    lines.append(asp.fact("person", "Twist"))
    lines.append(asp.fact("person", "Clerk"))
    return "\n".join(lines)


ASP_RULES = r"""
% A hock is available at places that afford it.
can_hock(P) :- affords(P, hock).

% A register can help when an election has a tally to print.
can_tally(P) :- affords(P, register), affords(P, election).

% The story is valid when both the hock premise and the election twist exist.
valid_story(P) :- can_hock(P), can_tally(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted({a[0] for a in asp.atoms(model, "valid_story")})


def asp_verify() -> int:
    py = {p for p, place in PLACES.items() if {"hock", "register", "election"} <= place.affords}
    cl = set(asp_valid_places())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


def valid_places() -> list[str]:
    return [p for p, place in PLACES.items() if {"hock", "register", "election"} <= place.affords]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about Twist, a hock, a register, and an election.")
    ap.add_argument("--place", choices=PLACES)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    if place not in valid_places():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="market"),
    StoryParams(place="fair"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_places())} compatible places: {', '.join(asp_valid_places())}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
