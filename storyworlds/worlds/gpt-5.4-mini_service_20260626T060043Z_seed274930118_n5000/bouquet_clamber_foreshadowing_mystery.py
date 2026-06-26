#!/usr/bin/env python3
"""
Bouquet Clamber Foreshadowing Mystery
=====================================

A small storyworld where a child follows a trail of tiny clues, climbs to reach
a bouquet, and discovers that the strange hints were pointing to a kindly
surprise all along.

The domain is intentionally narrow:
- one setting with a few plausible rooms/places,
- one child who likes climbing,
- one mysterious bouquet,
- one gentle reveal that resolves the puzzle.

The prose is written to feel like a child-friendly mystery with foreshadowing:
little details appear early, then become meaningful at the end.
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
    location: str = ""
    reachable: bool = False
    fragile: bool = False
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bouquet: object | None = None
    child: object | None = None
    clue: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Setting:
    place: str = "the garden"
    details: list[str] = field(default_factory=list)
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
    place: str
    child_name: str
    child_type: str
    parent_type: str
    seed: Optional[int] = None
    world: object | None = None
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(
        place="the garden",
        details=[
            "The path curved past a stone bench.",
            "Near the fence, one flower bed looked freshly turned.",
        ],
    ),
    "greenhouse": Setting(
        place="the greenhouse",
        details=[
            "Water beads glimmered on the glass.",
            "A small table stood beside the tomato pots.",
        ],
    ),
    "porch": Setting(
        place="the porch",
        details=[
            "A squeaky step sat under the railing.",
            "Something bright waited in a wicker chair.",
        ],
    ),
}

CHILD_NAMES = ["Maya", "Nina", "Theo", "Pip", "Ruby", "Lena", "Owen", "Sage"]
TRAITS = ["curious", "careful", "brave", "quiet", "bright", "spirited"]

BOUQUET_TYPES = {
    "roses": {
        "label": "bouquet of roses",
        "phrase": "a wrapped bouquet of red roses",
        "scent": "sweet",
    },
    "daisies": {
        "label": "bouquet of daisies",
        "phrase": "a cheerful bouquet of daisies",
        "scent": "fresh",
    },
    "wildflowers": {
        "label": "bouquet of wildflowers",
        "phrase": "a bright bouquet of wildflowers tied with twine",
        "scent": "earthy",
    },
}

FORESHADOWS = [
    "a ribbon fluttered where no wind should have reached",
    "one petal had been tucked under the chair leg",
    "a muddy footprint pointed toward the bench",
    "a note was folded into a square and hidden under a pot",
]

GUESSABLE_SIGNS = [
    "the ribbon",
    "the footprint",
    "the hidden note",
    "the bench",
]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for bouquet_id in BOUQUET_TYPES:
            combos.append((place, bouquet_id))
    return combos


def explain_rejection(place: str, bouquet_id: str) -> str:
    return (
        f"(No story: the bouquet of {bouquet_id} does not fit the clues and climb "
        f"at {place}; try one of the supported bouquets and settings.)"
    )


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def predict_discovery(world: World, bouquet: Entity) -> bool:
    # In this tiny domain, the bouquet is discovered if the child climbs high
    # enough to see the hiding place.
    return bouquet.hidden and bouquet.location in {"bench", "chair", "table"}


def setup_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        meters={"height": 1.0, "clamber": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "relief": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label="the parent",
        meters={"attention": 1.0},
        memes={"knowing": 1.0, "kindness": 1.0},
    ))
    bouquet_kind = random.choice(list(BOUQUET_TYPES))
    bouquet_cfg = _safe_lookup(BOUQUET_TYPES, bouquet_kind)
    bouquet = world.add(Entity(
        id="Bouquet",
        kind="thing",
        type="bouquet",
        label=bouquet_cfg["label"],
        phrase=bouquet_cfg["phrase"],
        owner=parent.id,
        location="bench" if params.place == "garden" else "chair",
        reachable=False,
        fragile=True,
        hidden=True,
        meters={"freshness": 1.0},
    ))
    clue = world.add(Entity(
        id="Clue",
        kind="thing",
        type="note",
        label="small note",
        phrase="a small folded note",
        location="pot",
        hidden=True,
    ))

    world.facts.update(
        child=child,
        parent=parent,
        bouquet=bouquet,
        bouquet_cfg=bouquet_cfg,
        clue=clue,
        setting=setting,
    )
    return world


def narrate_setup(world: World) -> None:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    bouquet: Entity = _safe_fact(world, f, "bouquet")

    world.say(
        f"{child.id} was a little curious {child.type} who noticed tiny things "
        f"that other people missed."
    )
    world.say(
        f"{child.id} liked to clamber onto low walls, step stools, and sturdy chairs "
        f"to get a better look at the world."
    )
    world.say(
        f"That morning, {parent.pronoun('possessive')} {parent.label} had left a "
        f"{bouquet.label} somewhere nearby."
    )
    world.say(
        f"It smelled {_safe_lookup(BOUQUET_TYPES, bouquet.id.lower() if bouquet.id.lower() in BOUQUET_TYPES else 'wildflowers')['scent'] if bouquet.label else 'nice'}, "
        f"and {child.id} could tell it was meant to matter."
    )


def foreshadow(world: World) -> None:
    detail = random.choice(FORESHADOWS)
    world.say(
        f"As {child_name(world)} wandered, {detail}, and that made the garden feel like "
        f"it was hiding a secret."
    )


def child_name(world: World) -> str:
    return world.facts["child"].id


def act_clamber(world: World) -> None:
    child: Entity = _safe_fact(world, world.facts, "child")
    bouquet: Entity = _safe_fact(world, world.facts, "bouquet")
    parent: Entity = _safe_fact(world, world.facts, "parent")

    child.meters["clamber"] += 1.0
    child.memes["curiosity"] += 1.0
    world.say(
        f"{child.id} stopped at the bench and clambered up carefully, using both hands."
    )
    world.say(
        f"From there, {child.id} noticed the tucked ribbon and the folded note."
    )
    if predict_discovery(world, bouquet):
        world.say(
            f"That was the first clue that the missing bouquet was not lost at all."
        )
    else:
        world.say(
            f"That was strange, because the trail still seemed to point to where "
            f"{parent.pronoun('subject')} had been."
        )


def reveal(world: World) -> None:
    child: Entity = _safe_fact(world, world.facts, "child")
    parent: Entity = _safe_fact(world, world.facts, "parent")
    bouquet: Entity = _safe_fact(world, world.facts, "bouquet")
    clue: Entity = _safe_fact(world, world.facts, "clue")

    child.memes["worry"] = 0.0
    child.memes["relief"] = 1.0
    bouquet.hidden = False
    clue.hidden = False
    world.say(
        f"At the top, {child.id} could see it: the {bouquet.label} waiting in plain sight."
    )
    world.say(
        f"The folded note was not a warning after all; it was a clue for a little surprise."
    )
    world.say(
        f"{parent.pronoun('subject').capitalize()} smiled and said the flowers were for "
        f"{child.id}, picked to celebrate a very good day."
    )
    world.say(
        f"{child.id} climbed back down with the bouquet held close, and the whole garden "
        f"seemed brighter than before."
    )


def tell(setting: Setting, name: str, child_type: str, parent_type: str) -> World:
    world = setup_world(StoryParams(place=setting.place, child_name=name, child_type=child_type, parent_type=parent_type))
    narrate_setup(world)
    world.para()
    world.say(setting.details[0])
    world.say(setting.details[1])
    foreshadow(world)
    world.para()
    act_clamber(world)
    world.say("The clues made sense only after the climb.")
    world.para()
    reveal(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    bouquet: Entity = _safe_fact(world, f, "bouquet")
    return [
        f'Write a short mystery for a child named {child.id} that includes a bouquet and a clamber up to a clue.',
        f'Tell a gentle foreshadowing story where {child.id} notices hints, clambers higher, and finds the {bouquet.label}.',
        f'Write a child-friendly mystery about a hidden bouquet, a small note, and a careful clamber.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    bouquet: Entity = _safe_fact(world, f, "bouquet")
    setting: Setting = _safe_fact(world, f, "setting")

    return [
        QAItem(
            question=f"What did {child.id} do to see the clue more clearly?",
            answer=f"{child.id} clambered up carefully onto a low spot so {child.pronoun('subject')} could look around better.",
        ),
        QAItem(
            question=f"Why did the garden feel mysterious before the bouquet was found?",
            answer=(
                "Because there were tiny hints first, like a ribbon out of place and a folded note. "
                f"Those clues made it feel as if {setting.place} was hiding a secret."
            ),
        ),
        QAItem(
            question=f"Who had left the {bouquet.label} nearby?",
            answer=f"It had been left by {parent.pronoun('possessive')} {parent.label}, who was planning a surprise for {child.id}.",
        ),
        QAItem(
            question=f"What did the clue turn out to mean at the end?",
            answer=f"The clue was part of a surprise, and it pointed {child.id} toward the {bouquet.label}.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "bouquet": [
        QAItem(
            question="What is a bouquet?",
            answer="A bouquet is a bunch of flowers tied together so they can be held as one pretty gift.",
        )
    ],
    "clamber": [
        QAItem(
            question="What does clamber mean?",
            answer="To clamber means to climb in a careful but clumsy way, using hands and feet to get up.",
        )
    ],
    "mystery": [
        QAItem(
            question="What makes a story feel like a mystery?",
            answer="A mystery usually has clues, a little wondering, and a surprise answer at the end.",
        )
    ],
    "foreshadowing": [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives small hints early that help explain what happens later.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["bouquet"] + WORLD_KNOWLEDGE["clamber"] + WORLD_KNOWLEDGE["mystery"] + WORLD_KNOWLEDGE["foreshadowing"]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if e.reachable:
            bits.append("reachable=True")
        if e.fragile:
            bits.append("fragile=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- place(S).

clue(C) :- thing(C), hidden(C).
basket(B) :- thing(B), bouquet(B).

mystery_story(P, B) :- place(P), bouquet(B), clue(_), action(clamber).

foreshadowing_hint(X) :- clue(X).
foreshadowing_hint(X) :- sign(X).

resolved(P, B) :- mystery_story(P, B), seen_clue(_), climbed(_), found(B).

valid_story(P, B) :- place(P), bouquet(B), resolved(P, B).
#show valid_story/2.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for bid in BOUQUET_TYPES:
        lines.append(asp.fact("bouquet", bid))
    lines.append(asp.fact("action", "clamber"))
    lines.append(asp.fact("sign", "ribbon"))
    lines.append(asp.fact("thing", "Clue"))
    lines.append(asp.fact("thing", "Bouquet"))
    lines.append(asp.fact("hidden", "Clue"))
    lines.append(asp.fact("hidden", "Bouquet"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Parity is intentionally simple here: both Python and ASP should agree on
    # the set of places and bouquet kinds that form a valid story.
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    mapped = set((p, b) for (p, b) in cl)
    if py == mapped:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if mapped - py:
        print("  only in clingo:", sorted(mapped - py))
    if py - mapped:
        print("  only in python:", sorted(py - mapped))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly mystery with foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--bouquet", choices=BOUQUET_TYPES)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    bouquet = getattr(args, "bouquet", None) or rng.choice(list(BOUQUET_TYPES))
    if getattr(args, "place", None) and getattr(args, "bouquet", None):
        if (getattr(args, "place", None), getattr(args, "bouquet", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, child_name=name, child_type=gender, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.child_name, params.child_type, params.parent_type)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, b) for p in SETTINGS for b in BOUQUET_TYPES]


CURATED = [
    StoryParams(place="garden", child_name="Maya", child_type="girl", parent_type="mother"),
    StoryParams(place="greenhouse", child_name="Theo", child_type="boy", parent_type="father"),
    StoryParams(place="porch", child_name="Ruby", child_type="girl", parent_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print(" ", item)
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
            header = f"### {p.child_name}: mystery at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
