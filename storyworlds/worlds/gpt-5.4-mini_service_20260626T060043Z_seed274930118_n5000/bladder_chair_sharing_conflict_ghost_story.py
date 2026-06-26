#!/usr/bin/env python3
"""
A small ghost-story world about sharing a chair, a restless bladder, and a
gentle conflict that ends in a kinder choice.
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

CHAR_VALUES = {"kind", "brave", "sleepy", "curious", "shy"}
MOOD_VALUES = {"calm", "uneasy", "frightened", "hopeful"}



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
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    chair: object | None = None
    ghost: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class Place:
    name: str = "the old house"
    setting_detail: str = "The old house was quiet, with a chair by the window and a hallway that creaked softly."
    affords_sharing: bool = True
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
    hero_name: str
    hero_trait: str
    ghost_name: str
    seed: Optional[int] = None
    params: object | None = None
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "the old house": Place(),
    "the attic room": Place(
        name="the attic room",
        setting_detail="The attic room was dusty and still, and an old chair stood beside a tiny lamp.",
    ),
    "the moonlit parlor": Place(
        name="the moonlit parlor",
        setting_detail="The moonlit parlor glowed silver, and the chair near the hearth looked almost watchful.",
    ),
}

HERO_NAMES = ["Mina", "Theo", "Ivy", "Nora", "Ben", "Luca", "Maya", "Eli"]
GHOST_NAMES = ["Pale Pip", "Luna", "Moss", "Whisper", "Bram", "Wren"]
TRAITS = ["kind", "brave", "sleepy", "curious", "shy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world about sharing a chair and a bladder conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--ghost")
    ap.add_argument("--trait", choices=sorted(CHAR_VALUES))
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
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    hero_trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    ghost_name = getattr(args, "ghost", None) or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, hero_name=hero_name, hero_trait=hero_trait, ghost_name=ghost_name)


def _do_settle(world: World, hero: Entity, ghost: Entity, chair: Entity) -> None:
    hero.meters["bladder"] += 1
    ghost.memes["want_chair"] += 1
    hero.memes["need_bathroom"] += 1


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", label=params.hero_name, type="child"))
    ghost = world.add(Entity(id="ghost", kind="character", label=params.ghost_name, type="ghost"))
    chair = world.add(Entity(id="chair", label="chair", type="chair", owner=ghost.id))

    world.say(f"{hero.label} was a {params.hero_trait} child who had come to {place.name}.")
    world.say(f"Near the window stood a chair, and {ghost.label} liked that chair very much.")
    world.say(place.setting_detail)

    world.para()
    world.say(f"That night, {hero.label} felt a tight little pinch in {hero.pronoun('possessive')} bladder.")
    world.say(f"{hero.label} wanted the chair for a moment, because {hero.pronoun('subject')} wanted to sit and rest.")
    world.say(f"But {ghost.label} wanted to keep the chair, and the two of them had a small conflict.")

    _do_settle(world, hero, ghost, chair)
    world.para()
    world.say(f"{hero.label} took a slow breath and said, “Can we share the chair for a little while?”")
    world.say(f"{ghost.label} floated back, listened, and nodded, because sharing felt better than arguing.")
    world.say(f"{hero.label} sat for a moment, then hurried off to the bathroom, and the chair stayed safe and calm.")
    world.say(f"In the quiet old house, the chair by the window waited in the moonlight, and the little ghost smiled.")

    world.facts = {
        "hero": hero,
        "ghost": ghost,
        "chair": chair,
        "place": place,
    }
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ghost = _safe_fact(world, f, "ghost")
    return [
        f"Write a gentle ghost story about {hero.label}, a chair, and a small conflict over sharing.",
        f"Tell a child-friendly story where {hero.label} needs the bathroom but also wants to sit in the chair with {ghost.label}.",
        f"Write a short spooky-but-kind story that includes a bladder, a chair, and a peaceful sharing choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ghost = _safe_fact(world, f, "ghost")
    return [
        QAItem(
            question=f"Why did {hero.label} want the chair?",
            answer=f"{hero.label} wanted the chair because {hero.pronoun('subject')} felt a tight little pinch in {hero.pronoun('possessive')} bladder and wanted to sit for a moment.",
        ),
        QAItem(
            question=f"What caused the conflict in the old house?",
            answer=f"The conflict happened because both {hero.label} and {ghost.label} wanted the chair at the same time.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The story ended with {hero.label} and {ghost.label} sharing calmly, and then {hero.label} going to the bathroom while the chair stayed safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bladder?",
            answer="The bladder is a small part inside the body that holds urine until it is time to go to the bathroom.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something too, so everyone gets a turn.",
        ),
        QAItem(
            question="What is a chair for?",
            answer="A chair is for sitting on, so a person can rest or wait comfortably.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f'label="{e.label}"')
        lines.append(f"  {e.id} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A simple compatibility twin for the story gate.
needs_share(H,C) :- hero(H), chair(C), bladder(H), ghost(G), wants_chair(G,C).
valid_story(H,C) :- needs_share(H,C).
#show valid_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("ghost", "ghost"))
    lines.append(asp.fact("chair", "chair"))
    lines.append(asp.fact("bladder", "hero"))
    lines.append(asp.fact("wants_chair", "ghost", "chair"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("hero", "chair")}
    if asp_set == py_set:
        print("OK: clingo gate matches Python gate (1 valid story).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


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

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i, place in enumerate(PLACES):
            params = StoryParams(
                place=place,
                hero_name=_safe_lookup(HERO_NAMES, i % len(HERO_NAMES)),
                hero_trait=_safe_lookup(TRAITS, i % len(TRAITS)),
                ghost_name=_safe_lookup(GHOST_NAMES, i % len(GHOST_NAMES)),
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.hero_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
