#!/usr/bin/env python3
"""
A small storyworld: a child in a subway station, a route, a lullabye, and a
surprising shift from mix-up to reconciliation with a little humor.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Route:
    name: str
    destination: str
    stop: str
    rhyme: str
    surprise: str
    humor: str
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
class Lullabye:
    title: str
    words: str
    effect: str
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
class StoryParams:
    route: str
    lullabye: str
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None
    p: object | None = None
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


class World:
    def __init__(self, route: Route, lullabye: Lullabye) -> None:
        self.route = route
        self.lullabye = lullabye
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ROUTES = {
    "blue_line": Route(
        name="blue line",
        destination="the north side",
        stop="subway station",
        rhyme="through the blue-line tune",
        surprise="a toy train in a paper moon",
        humor="the conductor winked and tipped his hat so soon",
    ),
    "green_loop": Route(
        name="green loop",
        destination="the park gate",
        stop="subway station",
        rhyme="round the green-loop beam",
        surprise="a sleepy kitten on a beanbag dream",
        humor="the ticket machine beeped with a squeaky scream",
    ),
    "circle_route": Route(
        name="circle route",
        destination="the library steps",
        stop="subway station",
        rhyme="along the circle song",
        surprise="a busker's spoon that sang along",
        humor="a mop bucket scooted like it had found a wrong",
    ),
}

LULLABYES = {
    "moon_hush": Lullabye(
        title="Moon Hush",
        words="Hush, hush, little rush, / let the rails go by; / sip the night, hold tight, / and blink your sleepy eye.",
        effect="softened the noise and slowed the feet",
    ),
    "tiny_tide": Lullabye(
        title="Tiny Tide",
        words="Tip and tap, clip-clap, / as the silver wheels sing; / breathe and sway, drift away, / like a feather on a string.",
        effect="made the station feel gentle and warm",
    ),
    "pillow_ping": Lullabye(
        title="Pillow Ping",
        words="Peek-a-peep, sleep-sweep, / in a tunnel of humming light; / rest your chin, grin within, / till the morning turns bright.",
        effect="turned the echo into a playful hum",
    ),
}

NAMES = {
    "girl": ["Mia", "Nora", "Lily", "Ava", "Zoe", "Maya"],
    "boy": ["Leo", "Ben", "Theo", "Noah", "Finn", "Sam"],
}
TRAITS = ["curious", "gentle", "silly", "brave", "cheerful", "sleepy"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [(r, l) for r in ROUTES for l in LULLABYES]


def make_title(route: Route, lullabye: Lullabye) -> str:
    return f"{route.name} / {lullabye.title}"


def _introduce(world: World, child: Entity, companion: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "curious")
    world.say(
        f"{child.id} was a little {trait} {child.type} who loved the subway station "
        f"because every train went somewhere new."
    )
    world.say(
        f"{child.pronoun().capitalize()} liked to hum the {world.lullabye.title} "
        f"with {companion.pronoun('possessive')} {companion.label} beside {child.pronoun('object')}."
    )


def _setup_route(world: World, child: Entity, companion: Entity) -> None:
    route = world.route
    world.say(
        f"One evening, they chose the {route.name}, a route that ran {route.rhyme}."
    )
    world.say(
        f"The old station lights blinked, and the tracks made a cozy clink-clink song."
    )


def _surprise(world: World, child: Entity, companion: Entity) -> None:
    route = world.route
    world.say(
        f"Just then, a surprise appeared: {route.surprise} waiting by the bench."
    )
    world.say(
        f"{child.id} blinked, then giggled, because even the station seemed to be wearing a joke."
    )
    child.memes["surprise"] = child.memes.get("surprise", 0.0) + 1.0
    companion.memes["humor"] = companion.memes.get("humor", 0.0) + 1.0


def _mixup(world: World, child: Entity, companion: Entity) -> None:
    route = world.route
    lull = world.lullabye
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{child.id} thought the funny surprise meant the ride was ruined, "
        f"but {companion.id} said, 'Nope, this is only a bump in the tune.'"
    )
    world.say(
        f"Then {companion.id} sang the {lull.title}, and the echo answered back like a tiny balloon."
    )
    world.facts["mixup"] = True
    world.facts["route"] = route.name


def _reconcile(world: World, child: Entity, companion: Entity) -> None:
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1.0
    child.memes["worry"] = 0.0
    companion.memes["love"] = companion.memes.get("love", 0.0) + 1.0
    world.say(
        f"{child.id} leaned close and listened, and the station's hard hum turned soft and slow."
    )
    world.say(
        f"{companion.id} smiled, and together they laughed at the silly surprise as it rolled down the row."
    )
    world.say(
        f"After that, they took the route again, and the night felt peaceful and bright."
    )
    world.say(
        f"The {world.lullabye.title} kept them steady, and the train carried them home in a gentle glow."
    )
    world.facts["resolved"] = True


def tell(route_key: str, lullabye_key: str, name: str, gender: str, companion_type: str) -> World:
    if route_key not in ROUTES:
        pass
    if lullabye_key not in LULLABYES:
        pass
    if gender not in NAMES:
        pass
    route = _safe_lookup(ROUTES, route_key)
    lullabye = _safe_lookup(LULLABYES, lullabye_key)
    world = World(route, lullabye)

    child = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            traits=["little", random.choice(TRAITS)],
        )
    )
    companion = world.add(
        Entity(
            id="Companion",
            kind="character",
            type=companion_type,
            label="grown-up",
            traits=["kind"],
        )
    )
    world.facts.update(child=child, companion=companion, route=route, lullabye=lullabye)

    _introduce(world, child, companion)
    world.para()
    _setup_route(world, child, companion)
    _surprise(world, child, companion)
    _mixup(world, child, companion)
    world.para()
    _reconcile(world, child, companion)
    return world


# ---------------------------------------------------------------------------
# QA and prose
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a rhyming story set in a subway station that includes the words "{world.route.name}" and "{world.lullabye.title}".',
        f"Tell a short child's story about a surprise on the {world.route.name} that ends in reconciliation and humor.",
        f"Write a gentle subway-station tale where a lullabye helps a child laugh, calm down, and ride home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    companion = _safe_fact(world, world.facts, "companion")
    route = _safe_fact(world, world.facts, "route")
    lull = _safe_fact(world, world.facts, "lullabye")
    return [
        QAItem(
            question=f"Where does {child.id} go in the story?",
            answer=f"{child.id} goes to the subway station and takes the {route.name} with {companion.label}.",
        ),
        QAItem(
            question=f"What surprise shows up during the ride?",
            answer=f"A surprise appears by the bench: {route.surprise}. It makes the scene funny instead of frightening.",
        ),
        QAItem(
            question=f"How does the {lull.title} help?",
            answer=f"The {lull.title} softens the noise, helps everyone breathe, and makes the station feel gentle again.",
        ),
        QAItem(
            question=f"How do the child and companion feel at the end?",
            answer="They feel calm, happy, and reconciled, and they laugh together before the train carries them home.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a subway station?",
            answer="A subway station is a place where people wait for underground trains to stop and pick them up.",
        ),
        QAItem(
            question="What is a lullabye?",
            answer="A lullabye is a soft, sleepy song that helps a child relax and get ready for rest.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop feeling upset and come back together kindly after a problem.",
        ),
        QAItem(
            question="Why can humor help during a surprise?",
            answer="Humor can make a surprise feel less scary because laughing helps people stay calm and kind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    out = ["--- world model ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: type={e.type}, kind={e.kind}, meters={e.meters}, memes={e.memes}")
    out.append(f"facts={world.facts}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
route_ok(R,L) :- route(R), lullabye(L).
#show route_ok/2.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines = []
    for r in ROUTES:
        lines.append(asp.fact("route", r))
    for l in LULLABYES:
        lines.append(asp.fact("lullabye", l))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show route_ok/2."))
    asp_set = set(asp.atoms(model, "route_ok"))
    asp_pairs = {(r, l) for r, l in asp_set}
    if asp_pairs == py:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate")
    print("only in ASP:", sorted(asp_pairs - py))
    print("only in Python:", sorted(py - asp_pairs))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: subway station, route, lullabye, surprise, reconciliation, humor.")
    ap.add_argument("--route", choices=sorted(ROUTES))
    ap.add_argument("--lullabye", choices=sorted(LULLABYES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=sorted(NAMES))
    ap.add_argument("--companion", choices=["mother", "father"])
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
    combos = valid_combos()
    if getattr(args, "route", None):
        combos = [c for c in combos if c[0] == getattr(args, "route", None)]
    if getattr(args, "lullabye", None):
        combos = [c for c in combos if c[1] == getattr(args, "lullabye", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    route, lull = rng.choice(combos)
    gender = getattr(args, "gender", None) or rng.choice(list(NAMES))
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    companion = getattr(args, "companion", None) or rng.choice(["mother", "father"])
    return StoryParams(route=route, lullabye=lull, name=name, gender=gender, companion=companion)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.route, params.lullabye, params.name, params.gender, params.companion)
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
        print(asp_program("#show route_ok/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp  # lazy
        model = asp.one_model(asp_program("#show route_ok/2."))
        pairs = sorted(set(asp.atoms(model, "route_ok")))
        print(f"{len(pairs)} compatible route/lullabye combinations:\n")
        for r, l in pairs:
            print(f"  {r[0]:12} {l[0]}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for r in sorted(ROUTES):
            for l in sorted(LULLABYES):
                p = StoryParams(route=r, lullabye=l, name="Mia", gender="girl", companion="mother")
                samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
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
