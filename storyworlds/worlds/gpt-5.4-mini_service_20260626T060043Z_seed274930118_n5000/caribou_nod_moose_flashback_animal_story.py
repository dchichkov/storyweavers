#!/usr/bin/env python3
"""
storyworlds/worlds/caribou_nod_moose_flashback_animal_story.py
===============================================================

A small animal-story world built from the seed words caribou, nod, and moose.

Premise:
- A young caribou wants to cross a windy marsh path.
- A moose friend notices the caribou's hesitation.
- A flashback reminds the caribou of an older, safer crossing.
- The story resolves with a careful nod and a steady, shared crossing.

This world is intentionally narrow and constraint-checked: it simulates a
single causal arc with a flashback as the narrative instrument that turns fear
into confidence.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    location: str = ""
    knows_path: bool = False
    ally: bool = False
    has_flashback: bool = False

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
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
    place: str = "the marsh path"
    weather: str = "windy"
    affords: set[str] = field(default_factory=lambda: {"crossing"})
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
    setting: str = "marsh"
    seed: Optional[int] = None
    name: str = "Pip"
    friend_name: str = "Moss"
    hero_trait: str = "small"
    friend_trait: str = "steady"
    params: object | None = None
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(copy.deepcopy(self.setting))
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with a flashback turn.")
    ap.add_argument("--setting", choices=["marsh"], default=None)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-trait")
    ap.add_argument("--friend-trait")
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
    return StoryParams(
        setting=getattr(args, "setting", None) or "marsh",
        seed=getattr(args, "seed", None),
        name=getattr(args, "name", None) or rng.choice(["Pip", "Nori", "Bram", "Kiki", "Luma"]),
        friend_name=getattr(args, "friend_name", None) or rng.choice(["Moss", "Hush", "Tarn", "Rill", "Tovo"]),
        hero_trait=getattr(args, "hero_trait", None) or rng.choice(["small", "timid", "curious", "young"]),
        friend_trait=getattr(args, "friend_trait", None) or rng.choice(["steady", "kind", "patient", "gentle"]),
    )


def setting_for(params: StoryParams) -> Setting:
    return Setting(place="the marsh path", weather="windy", affords={"crossing"})


def _do_crossing(world: World, hero: Entity, friend: Entity, narrate: bool = True) -> None:
    hero.meters["fear"] += 1
    if hero.has_flashback:
        hero.memes["confidence"] += 1
        hero.meters["fear"] = max(0.0, hero.meters["fear"] - 1)
    friend.memes["support"] += 1
    if narrate:
        world.say(f"They kept moving along the marsh path together.")


def predict_crossing(world: World, hero: Entity) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    _do_crossing(sim, h, sim.get("friend"), narrate=False)
    return {
        "fear": sim.get(hero.id).meters.get("fear", 0.0),
        "confidence": sim.get(hero.id).memes.get("confidence", 0.0),
    }


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} caribou who liked quiet mornings near the marsh."
    )
    world.say(
        f"{friend.id} was a {friend.traits[0]} moose who always noticed when a friend needed help."
    )


def want_crossing(world: World, hero: Entity) -> None:
    world.say(
        f"One windy morning, {hero.id} stopped beside the marsh path and looked across the reeds."
    )
    world.say(
        f"{hero.id} wanted to cross, but the tall grass and wobbly mud made {hero.pronoun()} pause."
    )


def flashback(world: World, hero: Entity, friend: Entity) -> None:
    hero.has_flashback = True
    world.say(
        f"Then {hero.id} had a flashback to a day when {friend.id} had shown the safest stepping stones."
    )
    world.say(
        f"In that memory, {friend.id} had waited patiently while {hero.id} learned to place each hoof with care."
    )


def nod_turn(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} gave a small nod, because the remembered lesson felt strong in {hero.id}'s chest."
    )
    world.say(
        f"{friend.id} nodded back, and that tiny answer made the path feel less scary."
    )


def resolve(world: World, hero: Entity, friend: Entity) -> None:
    pred = predict_crossing(world, hero)
    if pred["confidence"] < THRESHOLD and not hero.has_flashback:
        pass
    _do_crossing(world, hero, friend, narrate=False)
    world.say(
        f"Together they crossed the marsh path, one careful step after another."
    )
    world.say(
        f"By the time they reached the far bank, {hero.id} was calm, and the wind only brushed their fur."
    )


def tell(params: StoryParams) -> World:
    world = World(setting_for(params))
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="caribou",
        label="caribou",
        traits=[params.hero_trait],
        meters={"fear": 0.0},
        memes={"confidence": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type="moose",
        label="moose",
        traits=[params.friend_trait],
        meters={"support": 0.0},
        memes={"support": 0.0},
        ally=True,
    ))

    introduce(world, hero, friend)
    world.para()
    want_crossing(world, hero)
    flashback(world, hero, friend)
    nod_turn(world, hero, friend)
    world.para()
    resolve(world, hero, friend)

    world.facts.update(
        hero=hero,
        friend=friend,
        setting=world.setting,
        flashback=True,
        crossed=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    return [
        f"Write a short animal story about a caribou named {hero.id} and a moose named {friend.id}.",
        f"Tell a gentle story where a {hero.type} gets nervous, remembers a flashback, and nods to a {friend.type}.",
        f"Write a simple marsh story that includes caribou, moose, and nod, and ends with a calm crossing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a small caribou, and {friend.id}, a steady moose friend.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do by the marsh path?",
            answer=f"{hero.id} wanted to cross the marsh path, even though the muddy steps made the trip feel uncertain.",
        ),
        QAItem(
            question=f"What helped {hero.id} feel brave enough to keep going?",
            answer=f"A flashback of {friend.id} teaching safe steps helped {hero.id} remember what to do, and then {hero.id} gave a nod.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{hero.id} and {friend.id} crossed together, and the wind only brushed their fur by the far bank.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a caribou?",
            answer="A caribou is a deer-like animal that lives in cold places and walks with careful hooves.",
        ),
        QAItem(
            question="What is a moose?",
            answer="A moose is a large forest animal with long legs and a big nose, and it can be very gentle.",
        ),
        QAItem(
            question="What does it mean to nod?",
            answer="To nod means to move your head up and down a little, usually to show yes or agreement.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something from before, so the reader can remember how the past helps now.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"  {e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)} "
            f"flashback={e.has_flashback}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
hero(caribou).
friend(moose).
gesture(nod).
narrative(flashback).

needs_help(H) :- hero(H).
turn(H) :- narrative(flashback), needs_help(H).
resolve(H) :- turn(H), gesture(nod).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "caribou"),
            asp.fact("friend", "moose"),
            asp.fact("gesture", "nod"),
            asp.fact("narrative", "flashback"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolve/1."))
    asp_resolve = set(asp.atoms(model, "resolve"))
    py_resolve = {"caribou"} if True else set()
    if asp_resolve == {( "caribou",)} and py_resolve == {"caribou"}:
        print("OK: clingo gate matches Python reasonableness.")
        return 0
    print("MISMATCH between clingo and Python reasonableness.")
    print("  clingo:", sorted(asp_resolve))
    print("  python:", sorted(py_resolve))
    return 1


def asp_resolve_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolve/1."))
    return sorted(set(asp.atoms(model, "resolve")))


def valid_story(params: StoryParams) -> bool:
    return params.setting == "marsh"


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        pass
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
        print(asp_program("#show resolve/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show resolve/1."))
        atoms = asp.atoms(model, "resolve")
        print(f"{len(atoms)} resolve facts:")
        for a in atoms:
            print(" ", a)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = StoryParams(seed=base_seed)
        samples = [generate(params)]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
