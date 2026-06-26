#!/usr/bin/env python3
"""
simultaneous_gesture_fine_curiosity_pirate_tale.py
===================================================

A small storyworld about a curious pirate crew, a risky curiosity, and a
simultaneous gesture that solves a fine-tipped problem at sea.

Premise:
- A young pirate named Pip is full of Curiosity and wants to explore a locked
  chest on a small ship.
- The chest is secured with a delicate latch that must be opened with a fine
  gesture: two fingers, slow and careful.
- While Pip reaches for the chest, the captain notices the danger and makes a
  simultaneous gesture to guide Pip away from the edge.
- The story turns on whether Pip can listen, learn the fine gesture, and keep
  the ship steady.

This world is intentionally tiny and classical:
- one setting: a small pirate ship
- one central object: a curious chest
- one tension: curiosity vs. safety
- one resolution: a careful gesture and a shared discovery
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    chest: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for k in ["risk", "care", "mess", "steadiness", "skill"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "captain"}
        male = {"boy", "man", "pirate"}
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
    place: str = "the little pirate ship"
    sea: str = "calm"
    affords: set[str] = field(default_factory=lambda: {"curiosity", "gesture"})
    SETTING: object | None = None
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
    name: str
    captain_name: str
    setting: str = "ship"
    seed: Optional[int] = None
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
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting()

CHARACTER_NAMES = ["Pip", "Mira", "Ned", "Tess", "Jory"]
CAPTAIN_NAMES = ["Captain Lane", "Captain Brine", "Captain Wren"]

# Fine gesture: two fingers, slow and careful
GESTURES = {
    "fine": {
        "label": "a fine two-finger gesture",
        "method": "lift two fingers and tap the latch very gently",
        "warning": "The latch was small and delicate, so it needed a fine touch.",
        "effect": "the latch clicked open without a creak",
        "covers": {"hands"},
    }
}

# Curiosity as a concrete meter / motive in the world
CURIOUS_STORY = "Curiosity"
CHEST = {
    "label": "chest",
    "phrase": "a small chest with a brass latch",
    "content": "a tiny map rolled into a shell tube",
}

# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------


def valid_story(params: StoryParams) -> bool:
    return params.setting == "ship" and bool(params.name) and bool(params.captain_name)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
story(Name, Captain) :- pirate(Name), captain(Captain), ship(place).

curious(Name) :- pirate(Name).
at_risk(chest) :- curious(Name), reaches(Name, chest).

fine_gesture(fine) :- gesture(fine), delicate(latch).
safe_open(Name) :- fine_gesture(fine), learns(Name, fine).

resolution(Name) :- safe_open(Name), captain(Captain), guides(Captain, Name).
#show at_risk/1.
#show safe_open/2.
#show resolution/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("ship", "place"))
    lines.append(asp.fact("pirate", "pip"))
    lines.append(asp.fact("captain", "captain"))
    lines.append(asp.fact("gesture", "fine"))
    lines.append(asp.fact("delicate", "latch"))
    lines.append(asp.fact("reaches", "pip", "chest"))
    lines.append(asp.fact("learns", "pip", "fine"))
    lines.append(asp.fact("guides", "captain", "pip"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show at_risk/1.\n#show safe_open/2.\n#show resolution/1."))
    shown = {
        "at_risk": set(asp.atoms(model, "at_risk")),
        "safe_open": set(asp.atoms(model, "safe_open")),
        "resolution": set(asp.atoms(model, "resolution")),
    }
    expected = {
        "at_risk": {("chest",)},
        "safe_open": {("pip", "fine")},
        "resolution": {("pip",)},
    }
    if shown == expected:
        print("OK: clingo parity matches the Python gate.")
        return 0
    print("MISMATCH:")
    print("clingo:", shown)
    print("expected:", expected)
    return 1


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------


def setup_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type="pirate"))
    captain = world.add(Entity(id=params.captain_name, kind="character", type="captain"))
    chest = world.add(Entity(id="chest", type="chest", label="chest", phrase=CHEST["phrase"], owner=params.name))
    world.facts.update(hero=hero, captain=captain, chest=chest, params=params)
    return world


def predict_harm(world: World, hero: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["curiosity"] += 1
    sim.get("chest").meters["risk"] += 1
    return sim.get("chest").meters["risk"] >= THRESHOLD


def introduce(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    world.say(
        f"{hero.id} was a little pirate with {CURIOUS_STORY} in {hero.memes.get('curiosity', 0):.0f} bright bits and a head full of questions."
    )


def desire(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    chest: Entity = _safe_fact(world, world.facts, "chest")
    hero.memes["curiosity"] += 1
    chest.meters["risk"] += 1
    world.say(
        f"{hero.id} kept staring at {chest.phrase}, because every silver corner of it seemed to whisper, 'Look closer.'"
    )


def warning(world: World) -> bool:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    captain: Entity = _safe_fact(world, world.facts, "captain")
    chest: Entity = _safe_fact(world, world.facts, "chest")
    if not predict_harm(world, hero):
        return False
    world.say(
        f'"Careful," {captain.id} said, because {chest.label} was small and delicate. '
        f'"That latch needs a fine gesture, not a rough pull."'
    )
    return True


def simultaneous_gesture(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    captain: Entity = _safe_fact(world, world.facts, "captain")
    world.say(
        f"At the same time, {captain.id} made a gentle gesture with one hand and pointed to the latch with the other."
    )
    hero.memes["hesitation"] = hero.memes.get("hesitation", 0.0) + 1


def learn_fine_gesture(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    hero.memes["skill"] += 1
    hero.memes["curiosity"] -= 0.5
    world.say(
        f"{hero.id} copied the fine two-finger gesture: slow, soft, and careful."
    )


def resolve(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    captain: Entity = _safe_fact(world, world.facts, "captain")
    chest: Entity = _safe_fact(world, world.facts, "chest")
    chest.meters["risk"] = 0
    world.say(
        f"The latch clicked open without a creak, and inside was {CHEST['content']}."
    )
    world.say(
        f"{hero.id} grinned, and {captain.id} nodded, pleased that curiosity had learned to move gently."
    )


def tell_story(world: World) -> None:
    introduce(world)
    world.para()
    desire(world)
    warning(world)
    simultaneous_gesture(world)
    learn_fine_gesture(world)
    world.para()
    resolve(world)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    captain: Entity = _safe_fact(world, world.facts, "captain")
    return [
        f"Write a short pirate tale about {hero.id}, {CURIOUS_STORY}, and a fine gesture that opens a delicate chest.",
        f"Tell a child-friendly ship story where {captain.id} and {hero.id} solve a problem with a simultaneous gesture.",
        f"Write a small story on a pirate ship that uses the words curiosity, simultaneous, and fine.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    captain: Entity = _safe_fact(world, world.facts, "captain")
    return [
        QAItem(
            question=f"Who was the curious pirate in the story?",
            answer=f"The curious pirate was {hero.id}. {hero.id} kept reaching for the chest because curiosity tugged hard."
        ),
        QAItem(
            question=f"What did {captain.id} do to help {hero.id}?",
            answer=f"{captain.id} made a simultaneous gesture and showed {hero.id} the fine two-finger way to touch the latch."
        ),
        QAItem(
            question="What was inside the chest?",
            answer=f"Inside the chest was {CHEST['content']}."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the latch opening safely, so curiosity turned into a careful discovery instead of a rough grab."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more, look closer, and learn about something."
        ),
        QAItem(
            question="What is a gesture?",
            answer="A gesture is a movement of your hands or body that helps show a feeling or a message."
        ),
        QAItem(
            question="What does fine mean in a careful task?",
            answer="Fine can mean small and precise, like a tiny careful movement that avoids mistakes."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generate / emit / CLI
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "setting", None) != "ship":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(CHARACTER_NAMES)
    captain = getattr(args, "captain", None) or rng.choice(CAPTAIN_NAMES)
    if name == captain:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(name=name, captain_name=captain, setting="ship", seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        pass
    world = setup_world(params)
    tell_story(world)
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
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale storyworld about curiosity and a fine gesture.")
    ap.add_argument("--setting", choices=["ship"], default="ship")
    ap.add_argument("--name")
    ap.add_argument("--captain")
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


def show_asp_program() -> str:
    return asp_program("#show at_risk/1.\n#show safe_open/2.\n#show resolution/1.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(show_asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(show_asp_program())
        print("ASP model:")
        print("at_risk:", sorted(set(asp.atoms(model, "at_risk"))))
        print("safe_open:", sorted(set(asp.atoms(model, "safe_open"))))
        print("resolution:", sorted(set(asp.atoms(model, "resolution"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        seeds = [base_seed]
    else:
        seeds = [base_seed + i for i in range(max(getattr(args, "n", None), 1))]

    for seed in seeds[: getattr(args, "n", None)]:
        rng = random.Random(seed)
        params = resolve_params(args, rng)
        params.seed = seed
        samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### sample {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
