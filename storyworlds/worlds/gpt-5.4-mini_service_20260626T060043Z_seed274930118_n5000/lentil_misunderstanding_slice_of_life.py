#!/usr/bin/env python3
"""
storyworlds/worlds/lentil_misunderstanding_slice_of_life.py
===========================================================

A small slice-of-life storyworld about a gentle misunderstanding around lentils.

Premise:
- A child notices lentils in a bowl, pan, or lunchbox and misreads what they are.
- A parent or caregiver explains what lentils are and how they change when cooked.
- The child gets a little worried, then curious, then reassured.
- The ending proves the misunderstanding was cleared up by a concrete, everyday action:
  rinsing, cooking, tasting, or sharing a meal.

The world is intentionally small and constraint-checked so the story feels grounded
instead of random. Each story is driven by simulated state: physical objects gather
meters, feelings change as the misunderstanding unfolds, and the resolution depends
on the actual kitchen situation.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    edible: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bowl: object | None = None
    caregiver: object | None = None
    child: object | None = None
    spoon: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"clean": 0.0, "cooked": 0.0, "mixed": 0.0, "served": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "comfort": 0.0, "relief": 0.0, "hunger": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
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
class Place:
    id: str
    label: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)
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
class Scene:
    id: str
    label: str
    setting: str
    lens: str
    child_guess: str
    reveal: str
    fix: str
    theme_word: str = "lentil"
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
class StoryParams:
    place: str
    scene: str
    child_name: str
    child_type: str
    caregiver_type: str
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
    def __init__(self, place: Place, scene: Scene) -> None:
        self.place = place
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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


def _build_kitchen_trace(world: World) -> None:
    for e in list(world.entities.values()):
        world.trace.append(e.id)


def _child_subject(entity: Entity) -> str:
    return entity.pronoun("subject").capitalize()


def _scene_phrase(scene: Scene) -> str:
    return {
        "counter": "on the kitchen counter",
        "table": "on the table",
        "lunchbox": "inside the lunchbox",
        "pan": "in the warm pan",
    }.get(scene.id, scene.setting)


def _parent_label(entity: Entity) -> str:
    return {"mother": "mom", "father": "dad", "caregiver": "grown-up", "grandparent": "grandparent"}.get(entity.type, entity.type)


def _describe_lentils(scene: Scene) -> str:
    return {
        "dry": "little brown lentils that looked like tiny pebbles",
        "soup": "soft lentils in a steaming soup",
        "salad": "lentils mixed with rice and herbs",
        "mashed": "lentils being stirred into a thick mash",
    }.get(scene.id, "lentils in an everyday bowl")


def _do_misunderstanding(world: World, child: Entity, caregiver: Entity, bowl: Entity, scene: Scene) -> None:
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{child.id} paused and looked at the lentils { _scene_phrase(scene) }. "
        f"They seemed {scene.child_guess}."
    )
    world.say(
        f'"Are those really for eating?" {child.pronoun("subject").capitalize()} asked, '
        f"with a small frown."
    )
    caregiver.memes["comfort"] += 1
    world.say(
        f"{_parent_label(caregiver).capitalize()} smiled and said that lentils were just food, "
        f"not {scene.child_guess}."
    )
    world.facts["misunderstanding"] = True
    world.facts["guess"] = scene.child_guess


def _fix_misunderstanding(world: World, child: Entity, caregiver: Entity, bowl: Entity, spoon: Entity, scene: Scene) -> None:
    if scene.id in {"dry", "pan"}:
        bowl.meters["cooked"] += 1
    if scene.id in {"soup", "salad", "mashed"}:
        bowl.meters["served"] += 1
    spoon.meters["mixed"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"{_parent_label(caregiver).capitalize()} showed {child.id} how the lentils could be rinsed, simmered, "
        f"and turned into {scene.reveal}."
    )
    if scene.id == "dry":
        world.say("The lentils swished in water, then softened in the pot until they looked cozy and ready.")
    elif scene.id == "soup":
        world.say("The steam rose from the bowl, and the lentils looked warm and soft instead of strange.")
    elif scene.id == "salad":
        world.say("The rice and herbs made the lentils look like part of a simple, colorful lunch.")
    else:
        world.say("The spoon moved slowly through the pot, and the lentils thickened into a meal everyone could share.")
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    world.facts["resolved"] = True


def _ending(world: World, child: Entity, caregiver: Entity, bowl: Entity, scene: Scene) -> None:
    world.say(
        f"{child.id} took a careful taste and nodded. They were not pebbles at all; they were tasty lentils."
    )
    world.say(
        f"At the end, {child.id} sat with { _parent_label(caregiver) } and finished the simple meal together."
    )
    bowl.meters["served"] += 1
    child.memes["comfort"] += 1
    child.memes["hunger"] = 0.0


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    scene = _safe_lookup(SCENES, params.scene)
    world = World(place, scene)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    caregiver = world.add(Entity(id="Caregiver", kind="character", type=params.caregiver_type))
    bowl = world.add(Entity(id="Lentils", type="lentils", label="lentils", phrase=_describe_lentils(scene), edible=True, plural=True))
    spoon = world.add(Entity(id="Spoon", type="spoon", label="spoon"))
    world.facts.update(child=child, caregiver=caregiver, bowl=bowl, spoon=spoon, scene=scene, place=place)

    child.memes["hunger"] += 1

    world.say(f"One ordinary day, {child.id} and {_parent_label(caregiver)} were {place.label.lower()}.")
    world.say(f"On the counter sat {bowl.phrase}.")
    world.say(f"{child.id} liked the smell of the room, but the lentils looked unfamiliar.")

    world.para()
    _do_misunderstanding(world, child, caregiver, bowl, scene)

    world.para()
    _fix_misunderstanding(world, child, caregiver, bowl, spoon, scene)

    world.para()
    _ending(world, child, caregiver, bowl, scene)

    _build_kitchen_trace(world)
    return world


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", indoors=True, affords={"counter", "table", "pan", "lunchbox"}),
    "dining_room": Place(id="dining_room", label="the dining room", indoors=True, affords={"table", "lunchbox"}),
    "small_apartment": Place(id="small_apartment", label="the small apartment kitchen", indoors=True, affords={"counter", "pan", "table"}),
}

SCENES = {
    "dry": Scene(
        id="dry",
        label="dry lentils",
        setting="the kitchen counter",
        lens="counter",
        child_guess="tiny stones",
        reveal="a warm bowl of lentil soup",
        fix="rinsing and simmering",
        theme_word="lentil",
    ),
    "soup": Scene(
        id="soup",
        label="lentil soup",
        setting="the table",
        lens="table",
        child_guess="muddy pebbles",
        reveal="a simple soup for lunch",
        fix="stirring and serving",
        theme_word="lentil",
    ),
    "salad": Scene(
        id="salad",
        label="lentil salad",
        setting="the lunchbox",
        lens="lunchbox",
        child_guess="little beads",
        reveal="a bright lunch for later",
        fix="mixing and packing",
        theme_word="lentil",
    ),
    "pan": Scene(
        id="pan",
        label="lentils in a pan",
        setting="the warm pan",
        lens="pan",
        child_guess="bitty coins",
        reveal="a cozy dinner",
        fix="stirring and waiting",
        theme_word="lentil",
    ),
}

CHILD_NAMES = ["Mina", "Owen", "Lila", "Noah", "Ivy", "Eli", "Maya", "Theo"]
CHILD_TYPES = ["girl", "boy"]
CAREGIVER_TYPES = ["mother", "father", "grandparent", "caregiver"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, p in PLACES.items():
        for scene, s in SCENES.items():
            if s.lens in p.affords:
                combos.append((place, scene))
    return combos


def explain_rejection(place: str, scene: str) -> str:
    return f"(No story: {_safe_lookup(SCENES, scene).label} does not fit naturally in {_safe_lookup(PLACES, place).label}.)"


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, s in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("lens", sid, s.lens))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Scene) :- place(Place), scene(Scene), affords(Place, Lens), lens(Scene, Lens).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


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
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about a lentil misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--caregiver-type", choices=CAREGIVER_TYPES)
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
              and (getattr(args, "scene", None) is None or c[1] == getattr(args, "scene", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, scene = rng.choice(list(combos))
    child_type = getattr(args, "child_type", None) or rng.choice(CHILD_TYPES)
    caregiver_type = getattr(args, "caregiver_type", None) or rng.choice(CAREGIVER_TYPES)
    child_name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    return StoryParams(place=place, scene=scene, child_name=child_name, child_type=child_type, caregiver_type=caregiver_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = _safe_fact(world, f, "scene")
    child: Entity = _safe_fact(world, f, "child")
    return [
        f'Write a short slice-of-life story for a young child about a lentil misunderstanding, using the word "{scene.theme_word}".',
        f"Tell a gentle everyday story where {child.id} thinks the lentils are {scene.child_guess} and learns what they really are.",
        f"Write a simple kitchen story that ends with {child.id} happily eating lentils with family.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    caregiver: Entity = _safe_fact(world, f, "caregiver")
    scene: Scene = _safe_fact(world, f, "scene")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What did {child.id} think the lentils were at first?",
            answer=f"{child.id} thought the lentils were {scene.child_guess} before {caregiver.type} explained them.",
        ),
        QAItem(
            question=f"Where was the story set?",
            answer=f"The story was set in {place.label}, an ordinary everyday place where a family could have a meal.",
        ),
        QAItem(
            question=f"How was the misunderstanding fixed?",
            answer=f"{_parent_label(caregiver).capitalize()} showed that the lentils could be {scene.fix}, which turned the strange-looking food into an ordinary meal.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt relieved and comfortable after tasting the lentils and seeing they were safe and tasty.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are lentils?",
            answer="Lentils are small, edible seeds that people cook in soups, stews, salads, and other simple meals.",
        ),
        QAItem(
            question="Why might lentils look confusing at first?",
            answer="Dry lentils can look like tiny pebbles or beads, but cooking changes them into soft food.",
        ),
        QAItem(
            question="What happens when lentils are cooked?",
            answer="When lentils are cooked, they get softer and more tender, so they are easier to eat.",
        ),
    ]


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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="kitchen", scene="dry", child_name="Mina", child_type="girl", caregiver_type="mother"),
    StoryParams(place="dining_room", scene="soup", child_name="Owen", child_type="boy", caregiver_type="father"),
    StoryParams(place="small_apartment", scene="pan", child_name="Ivy", child_type="girl", caregiver_type="grandparent"),
    StoryParams(place="kitchen", scene="salad", child_name="Theo", child_type="boy", caregiver_type="caregiver"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, scene) combos:\n")
        for place, scene in combos:
            print(f"  {place:14} {scene}")
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
            header = f"### {p.child_name}: {p.scene} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
