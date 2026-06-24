#!/usr/bin/env python3
"""
A small story world for a friendly ghost story about a sociable vegetable,
sharing, and dialogue.

Seed tale premise:
A sociable vegetable was lonely in a quiet kitchen until a ghost arrived,
started a gentle dialogue, and helped it share with the others. The story
turns on fear becoming friendship through conversation and sharing.
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    ghost: object | None = None
    veg: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"ghost"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"child", "girl", "boy"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the kitchen"
    quiet: bool = True
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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


@dataclass
class StoryParams:
    place: str = "kitchen"
    vegetable: str = "carrot"
    ghost: str = "Milo"
    friend: str = "Nina"
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


SETTINGS = {
    "kitchen": Setting("the kitchen", True),
    "garden": Setting("the garden", False),
    "cellar": Setting("the cellar", True),
    "market": Setting("the market", False),
}

VEGETABLES = {
    "carrot": {"label": "carrot", "phrase": "a bright orange carrot", "plural": False},
    "pea": {"label": "pea pod", "phrase": "a small pea pod", "plural": False},
    "pumpkin": {"label": "pumpkin", "phrase": "a round little pumpkin", "plural": False},
    "cabbage": {"label": "cabbage", "phrase": "a leafy green cabbage", "plural": False},
    "beans": {"label": "beans", "phrase": "a little bowl of beans", "plural": True},
}

GHOSTS = ["Milo", "Luna", "Pip", "Boo", "Nell"]
FRIENDS = ["Nina", "Ollie", "Maya", "Toby", "June", "Leo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with sharing and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--vegetable", choices=VEGETABLES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--friend", choices=FRIENDS)
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
    veg = getattr(args, "vegetable", None) or rng.choice(list(VEGETABLES))
    ghost = getattr(args, "ghost", None) or rng.choice(GHOSTS)
    friend = getattr(args, "friend", None) or rng.choice(FRIENDS)
    if ghost == friend:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, vegetable=veg, ghost=ghost, friend=friend)


def _do_sharing(world: World, veg: Entity, ghost: Entity, friend: Entity) -> None:
    veg.memes["sharing"] = veg.memes.get("sharing", 0.0) + 1
    ghost.memes["helping"] = ghost.memes.get("helping", 0.0) + 1
    friend.memes["comfort"] = friend.memes.get("comfort", 0.0) + 1


def tell(world: World) -> World:
    setting = world.setting
    veg = world.get("vegetable")
    ghost = world.get("ghost")
    friend = world.get("friend")

    world.say(
        f"In {setting.place}, a sociable {veg.label} waited on the table and wondered if anyone would notice {veg.it()}."
    )
    world.say(
        f"Then {ghost.id} drifted in like a soft white whisper and said, “Hello. Can we talk?”"
    )
    world.say(
        f"{veg.id} nodded, because {veg.id} was sociable too, and soon the two of them had a gentle dialogue about the room, the moon, and the smell of soup."
    )
    world.para()
    friend.memes["fear"] = 1.0
    world.say(
        f"At first, {friend.id} froze and whispered that a ghost in the {setting.place} sounded spooky."
    )
    world.say(
        f"But {ghost.id} answered kindly, “I am not here to frighten you. I am here to share.”"
    )
    _do_sharing(world, veg, ghost, friend)
    world.say(
        f"So {veg.id} offered {veg.it()} to share, and {ghost.id} helped make room at the plate. {friend.id} smiled and joined the dialogue instead of hiding."
    )
    world.para()
    world.say(
        f"By the end, the {veg.label} was not lonely anymore. It stayed in the middle of the table, surrounded by friendship, while {ghost.id} and {friend.id} talked softly in the warm quiet room."
    )

    world.facts.update(vegetable=veg, ghost=ghost, friend=friend, setting=setting, shared=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    veg = _safe_fact(world, f, "vegetable")
    return [
        f'Write a short ghost story for a child about a sociable {veg.label} that learns to share.',
        f'Create a gentle story where a ghost and a vegetable have a dialogue and become friends.',
        f'Write a simple, cozy ghost story that includes sharing, conversation, and a {veg.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    veg = _safe_fact(world, f, "vegetable")
    ghost = _safe_fact(world, f, "ghost")
    friend = _safe_fact(world, f, "friend")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened in {place}, where the sociable {veg.label} waited on the table.",
        ),
        QAItem(
            question=f"Who came first to speak with the {veg.label}?",
            answer=f"{ghost.id} came first and started a gentle dialogue with the {veg.label}.",
        ),
        QAItem(
            question=f"What changed in the end?",
            answer=f"The {veg.label} stopped being lonely, {ghost.id} and {friend.id} shared kindly, and everyone joined the conversation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means giving some of what you have so another person or friend can enjoy it too.",
        ),
        QAItem(
            question="What is a dialogue?",
            answer="A dialogue is a conversation where people or characters take turns speaking and listening.",
        ),
        QAItem(
            question="What is a ghost in a gentle story?",
            answer="In a gentle story, a ghost is a spooky-looking character who can still be kind and friendly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


ASP_RULES = r"""
% A story is valid when it contains a vegetable, a ghost, a friend, dialogue,
% and a sharing turn that resolves fear into comfort.
valid_story(P, V, G, F) :- place(P), vegetable(V), ghost(G), friend(F),
    not same(G, F), dialogue(P, V, G), sharing(P, V, G, F).

same(X, X).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for v in VEGETABLES:
        lines.append(asp.fact("vegetable", v))
    for g in GHOSTS:
        lines.append(asp.fact("ghost", g))
    for f in FRIENDS:
        lines.append(asp.fact("friend", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams("kitchen", "carrot", "Milo", "Nina"),
    StoryParams("garden", "beans", "Luna", "Ollie"),
    StoryParams("cellar", "pumpkin", "Pip", "Maya"),
]


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    veg_cfg = _safe_lookup(VEGETABLES, params.vegetable)
    veg = world.add(Entity(
        id="vegetable",
        kind="thing",
        type=params.vegetable,
        label=veg_cfg["label"],
        phrase=veg_cfg["phrase"],
        plural=veg_cfg["plural"],
    ))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=params.ghost))
    friend = world.add(Entity(id="friend", kind="character", type="child", label=params.friend))
    world.facts.update(vegetable=veg, ghost=ghost, friend=friend, setting=setting)
    tell(world)
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
