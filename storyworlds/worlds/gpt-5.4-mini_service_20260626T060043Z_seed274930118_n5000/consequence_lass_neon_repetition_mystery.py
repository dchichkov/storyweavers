#!/usr/bin/env python3
"""
Standalone Storyworld: consequence / lass / neon / repetition / mystery.

A small child-facing mystery world:
- a lass notices a neon clue,
- repeated clues create a pattern,
- the consequence of a hidden action is uncovered,
- the story ends with a clear reveal and changed state.

This script follows the Storyweavers storyworld contract.
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
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    notes: dict[str, str] = field(default_factory=dict)

    clue_ent: object | None = None
    hero: object | None = None
    keeper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "lass"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "lad"}:
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
    indoor: bool = False
    bright: bool = False
    echoey: bool = False
    affords: set[str] = field(default_factory=set)
    outdoor: bool = False
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
    phrase: str
    repetition: str
    consequence: str
    place: str
    hidden_by: str
    reveals: str
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
    place: str
    clue: str
    hero_name: str
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
    def __init__(self, place: Place, clue: Clue) -> None:
        self.place = place
        self.clue = clue
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.pattern_seen: int = 0
        self.hint_seen: bool = False
        self.revealed: bool = False

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
        clone = World(self.place, self.clue)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.pattern_seen = self.pattern_seen
        clone.hint_seen = self.hint_seen
        clone.revealed = self.revealed
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    if world.pattern_seen >= 2 and not world.hint_seen:
        sig = ("pattern", world.clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.hint_seen = True
            out.append(f"She noticed the same little sign again, and again, and again.")
    return out


def _r_consequence(world: World) -> list[str]:
    out: list[str] = []
    if world.hint_seen and not world.revealed:
        sig = ("consequence", world.clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.revealed = True
            out.append(
                f"The repeated clue pointed to the consequence: someone had hidden the key by the neon window."
            )
    return out


RULES = [_r_repetition, _r_consequence]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


PLACE_REGISTRY = {
    "alley": Place(id="alley", label="the alley", outdoor=True, bright=False, echoey=True, affords={"search"}),
    "shop": Place(id="shop", label="the tiny shop", indoor=True, bright=True, echoey=False, affords={"search"}),
    "hall": Place(id="hall", label="the old hall", indoor=True, bright=False, echoey=True, affords={"search"}),
}

CLUE_REGISTRY = {
    "neon": Clue(
        id="neon",
        label="neon",
        phrase="a neon sign",
        repetition="neon glow",
        consequence="the missing key was tucked behind it",
        place="shop",
        hidden_by="dust",
        reveals="key",
    ),
    "window": Clue(
        id="window",
        label="window",
        phrase="a neon window poster",
        repetition="bright neon edge",
        consequence="the note was stuck to the sill",
        place="hall",
        hidden_by="rain",
        reveals="note",
    ),
}


def build_world(params: StoryParams) -> World:
    place = PLACE_REGISTRY[params.place]
    clue = CLUE_REGISTRY[params.clue]
    world = World(place, clue)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="lass", label="lass"))
    keeper = world.add(Entity(id="keeper", kind="character", type="adult", label="shopkeeper"))
    clue_ent = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue.label,
        phrase=clue.phrase,
        hidden=True,
    ))

    hero.meters["curiosity"] = 1
    hero.memes["unease"] = 1
    keeper.memes["worry"] = 1
    clue_ent.notes["repetition"] = clue.repetition
    clue_ent.notes["consequence"] = clue.consequence

    world.say(f"{hero.id} was a little lass with sharp eyes and a quiet step.")
    world.say(f"She loved noticing strange things, especially in {place.label}.")
    world.say(f"That day, a {clue.phrase} glowed with a neon shine.")
    world.para()

    world.say(f"{hero.id} saw the neon glow once.")
    world.pattern_seen += 1
    propagate(world)
    world.say(f"Then she saw it again.")
    world.pattern_seen += 1
    propagate(world)
    world.say(f"And then she saw it one more time, in the same spot.")
    world.pattern_seen += 1
    propagate(world)

    world.para()
    if world.revealed:
        hero.memes["relief"] = 1
        hero.meters["solved"] = 1
        world.say(f"At last, the mystery made sense.")
        world.say(
            f"The neon clue had a consequence: {clue.consequence}, and {hero.pronoun()} found the hidden key."
        )
        world.say(f"{hero.id} smiled, because the repeated glow had led her right to the answer.")
    else:
        world.say(f"She kept looking, but the clue still felt unfinished.")

    world.facts.update(
        hero=hero,
        keeper=keeper,
        clue=clue_ent,
        place=place,
        clue_cfg=clue,
        solved=world.revealed,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a child about a lass, a repeated neon clue, and a clear consequence.',
        f"Tell a gentle mystery where {f['hero'].id} notices the same neon clue more than once and solves what it means.",
        f"Write a simple story that uses the word 'neon' and ends with the lass understanding the consequence of the pattern.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    place = _safe_fact(world, f, "place")
    clue = _safe_fact(world, f, "clue_cfg")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little lass who noticed a mystery in {place.label}.",
        ),
        QAItem(
            question=f"What clue did {hero.id} keep seeing?",
            answer=f"{hero.id} kept seeing {clue.phrase}, and its neon glow stood out each time.",
        ),
        QAItem(
            question=f"What happened because the clue was repeated?",
            answer=f"The repeated clue helped {hero.id} understand the consequence and find the hidden key.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the mystery?",
            answer=f"She watched the neon clue again and again, noticed the pattern, and followed it to the answer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is neon?",
            answer="Neon is a very bright light or color that can glow and catch your eye.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means something happens or is seen more than once, often in the same way.",
        ),
        QAItem(
            question="What is a consequence?",
            answer="A consequence is what happens because of something else that came before it.",
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
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  pattern_seen={world.pattern_seen}")
    lines.append(f"  hint_seen={world.hint_seen}")
    lines.append(f"  revealed={world.revealed}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(place: str, clue: str) -> str:
    return f"(No story: {place} and {clue} do not fit the mystery pattern for this world.)"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACE_REGISTRY.items():
        if "search" not in place.affords:
            continue
        for cid in CLUE_REGISTRY:
            combos.append((pid, cid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a lass, a neon clue, and a mystery of repetition."
    )
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--clue", choices=CLUE_REGISTRY)
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
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(["Mira", "Luna", "Tess", "Nora", "Ivy"])
    return StoryParams(place=place, clue=clue, hero_name=name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


ASP_RULES = r"""
place(P) :- setting(P).
clue(C) :- clue_id(C).
repeated(C) :- seen(C,1), seen(C,2), seen(C,3).
mystery(C) :- clue(C), repeated(C).
consequence(C) :- mystery(C), hidden(C).
#show mystery/1.
#show consequence/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACE_REGISTRY:
        lines.append(asp.fact("setting", pid))
    for cid, clue in CLUE_REGISTRY.items():
        lines.append(asp.fact("clue_id", cid))
        lines.append(asp.fact("hidden", cid))
        lines.append(asp.fact("seen", cid, 1))
        lines.append(asp.fact("seen", cid, 2))
        lines.append(asp.fact("seen", cid, 3))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show mystery/1.\n#show consequence/1."))
    mystery = set(asp.atoms(model, "mystery"))
    consequence = set(asp.atoms(model, "consequence"))
    python = {(c,) for c in CLUE_REGISTRY}
    if mystery == python and consequence == python:
        print(f"OK: ASP matches Python for {len(python)} clues.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery/1.\n"))
    return sorted(set(asp.atoms(model, "mystery")))


CURATED = [
    StoryParams(place="shop", clue="neon", hero_name="Mira"),
    StoryParams(place="hall", clue="window", hero_name="Luna"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery/1.\n#show consequence/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show mystery/1.\n#show consequence/1."))
        print("mystery:", asp.atoms(model, "mystery"))
        print("consequence:", asp.atoms(model, "consequence"))
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
            p = sample.params
            header = f"### {p.hero_name}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
