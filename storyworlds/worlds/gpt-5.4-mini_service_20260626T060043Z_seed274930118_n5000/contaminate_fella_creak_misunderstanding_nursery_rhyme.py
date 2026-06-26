#!/usr/bin/env python3
"""
A tiny nursery-rhyme story world about a fella, a creaky place, and a
misunderstanding that leads to a mess unless someone notices in time.
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
    type: str = "thing"
    name: str = ""
    role: str = ""
    phrase: str = ""
    wears: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    label: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fella", "boy", "dad", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
class Place:
    id: str
    name: str
    creaky: bool = False
    setting: str = ""
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
    id: str
    name: str
    phrase: str
    kind: str
    cover: str
    guard: str
    clean_again: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    item: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
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
    "nursery": Place(
        id="nursery",
        name="the nursery",
        creaky=True,
        setting="a soft little room with a rocking chair and a toy shelf",
        affords={"play", "tiptoe", "reach"},
    ),
    "porch": Place(
        id="porch",
        name="the porch",
        creaky=True,
        setting="a wooden porch with one board that always gave a creak",
        affords={"walk", "carry", "peek"},
    ),
    "kitchen": Place(
        id="kitchen",
        name="the kitchen",
        creaky=False,
        setting="a warm kitchen with a bright table and a sunny window",
        affords={"stir", "carry", "share"},
    ),
}

ITEMS = {
    "jam": Item(
        id="jam",
        name="jam jar",
        phrase="a shiny jam jar",
        kind="jam",
        cover="lips",
        guard="cloth",
        clean_again="wiped the red jam away",
    ),
    "paint": Item(
        id="paint",
        name="paint pot",
        phrase="a little paint pot",
        kind="paint",
        cover="hands",
        guard="apron",
        clean_again="washed the blue paint away",
    ),
    "crumbs": Item(
        id="crumbs",
        name="crumb bowl",
        phrase="a bowl of sweet crumbs",
        kind="crumbs",
        cover="table",
        guard="tray",
        clean_again="swept the crumbs away",
    ),
}

NAMES = ["Milo", "Toby", "Pip", "Nora", "Lina", "Bea", "Otis", "Finn"]
HELPER_NAMES = ["Mum", "Dad", "Auntie", "Uncle", "Gran"]
TRAITS = ["little", "cheerful", "curious", "bouncy", "gentle"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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


def rhyme_line(a: str, b: str) -> str:
    return f"{a}, {b}."


def do_action(world: World, actor: Entity, item: Entity, narrate: bool = True) -> None:
    actor.meters["busy"] = actor.meters.get("busy", 0) + 1
    if world.place.creaky and "creak" in world.place.setting.lower():
        actor.memes["curious"] = actor.memes.get("curious", 0) + 1
    if narrate:
        world.say(f"{actor.name} tried to {world.facts['action']} with {item.name} at {world.place.name}.")


def predict_contaminate(world: World, item: Item) -> bool:
    return bool(world.place.creaky and world.facts["misunderstanding"] and item.kind in {"jam", "paint"})


def build_story(world: World, hero: Entity, helper: Entity, item: Item) -> None:
    place = world.place
    world.say(f"{hero.name} was a {hero.role} fella in {place.name}.")
    world.say(f"{place.setting} made a merry little scene, and one board would {('creak' if place.creaky else 'not creak')} when stepped on.")
    world.say(f"{hero.name} loved to carry {item.phrase} and sing a nursery tune.")
    world.para()

    world.say(f"One day {hero.name} heard a small { 'creak' if place.creaky else 'tap' } and frowned.")
    world.say(f"{hero.name} thought the sound meant {helper.name} was calling for help.")
    world.say(f"But {helper.name} only meant to say, 'Please do not {world.facts['action']} yet!'")
    world.say(f"That was the misunderstanding, and it made {hero.name} hurry the wrong way.")
    world.para()

    if predict_contaminate(world, item):
        hero.meters["messy"] = hero.meters.get("messy", 0) + 1
        item.meters["dirty"] = item.meters.get("dirty", 0) + 1
        world.say(f"The hurry caused the {item.name} to tip and contaminate the cloth below.")
        world.say(f"{helper.name} gasped, then smiled kindly and said it was only a mix-up.")
        world.say(f"They used a clean cloth and {item.clean_again}, and soon the room was neat once more.")
    else:
        world.say(f"{hero.name} stopped short and listened again.")
        world.say(f"Then the fella saw the true meaning of the note, laughed softly, and set the {item.name} down safely.")
        world.say(f"{helper.name} nodded, and the creaky place stayed tidy and calm.")

    world.para()
    world.say(f"By bedtime, {hero.name} was humming, {helper.name} was smiling, and the little creak had become a funny story.")


def resolve_story(params: StoryParams) -> tuple[World, Entity, Entity, Item]:
    if params.place not in PLACES:
        pass
    if params.item not in ITEMS:
        pass

    place = _safe_lookup(PLACES, params.place)
    item = _safe_lookup(ITEMS, params.item)
    world = World(place)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, name=params.hero_name, role="little"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, name=params.helper_name, role="kind"))

    world.facts["action"] = {"nursery": "tiptoe", "porch": "reach", "kitchen": "stir"}[params.place]
    world.facts["misunderstanding"] = True
    world.facts["item"] = item
    world.facts["place"] = place

    build_story(world, hero, helper, item)
    return world, hero, helper, item


def generation_prompts(world: World) -> list[str]:
    item: Item = _safe_fact(world, world.facts, "item")  # type: ignore[assignment]
    place: Place = _safe_fact(world, world.facts, "place")  # type: ignore[assignment]
    return [
        f"Write a short nursery-rhyme story about a fella in {place.name} and a {item.name}.",
        f"Tell a child-friendly tale where a creak causes a misunderstanding and someone nearly contaminates {item.phrase}.",
        f"Make a gentle rhyme about listening closely, fixing a mix-up, and keeping {place.name} tidy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.get("hero")
    helper: Entity = world.get("helper")
    item: Item = _safe_fact(world, world.facts, "item")  # type: ignore[assignment]
    place: Place = _safe_fact(world, world.facts, "place")  # type: ignore[assignment]
    contaminated = any(e.meters.get("dirty", 0) > 0 for e in world.entities.values()) or "contaminate" in world.render()
    return [
        QAItem(
            question=f"Who was the story about in {place.name}?",
            answer=f"It was about {hero.name}, a little fella, and {helper.name}, who helped keep things kind and calm.",
        ),
        QAItem(
            question=f"What made the mix-up happen near the {item.name}?",
            answer=f"A little creak made {hero.name} misunderstand what {helper.name} meant, so {hero.name} hurried the wrong way.",
        ),
        QAItem(
            question="Did anything get contaminated?",
            answer=(
                f"Yes, the hurry nearly contaminated the cloth under the {item.name}. "
                if contaminated else
                f"No, {hero.name} stopped in time, so nothing got contaminated."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    place: Place = _safe_fact(world, world.facts, "place")  # type: ignore[assignment]
    item: Item = _safe_fact(world, world.facts, "item")  # type: ignore[assignment]
    return [
        QAItem(
            question="What does a creak usually sound like?",
            answer="A creak is a squeaky, wooden sound, like a board or a door moving slowly.",
        ),
        QAItem(
            question=f"What is a {item.name} for?",
            answer=f"A {item.name} is for holding {item.kind} so it can be carried or used without spilling.",
        ),
        QAItem(
            question=f"What kind of place is {place.name} in this story?",
            answer=f"It is a small, cozy place where a child can play, listen, and learn carefully.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place: {world.place.name}")
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: type={e.type} name={e.name} meters={meters} memes={memes}")
    lines.append(f"fired: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.creaky:
            lines.append(asp.fact("creaky", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("kind", iid, item.kind))
        lines.append(asp.fact("contaminates", iid, item.kind))
    return "\n".join(lines)


ASP_RULES = r"""
% A place invites misunderstanding if it is creaky.
misunderstanding(P) :- creaky(P).

% A contaminating incident is possible in a creaky place with jam or paint.
can_contaminate(P, I) :- misunderstanding(P), item(I), contaminates(I, jam).
can_contaminate(P, I) :- misunderstanding(P), item(I), contaminates(I, paint).

#show misunderstanding/1.
#show can_contaminate/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show misunderstanding/1.\n#show can_contaminate/2."))
    got_mis = set(asp.atoms(model, "misunderstanding"))
    got_can = set(asp.atoms(model, "can_contaminate"))
    py_mis = {(pid,) for pid, p in PLACES.items() if p.creaky}
    py_can = {(pid, iid) for pid, p in PLACES.items() for iid in ITEMS if p.creaky and _safe_lookup(ITEMS, iid).kind in {"jam", "paint"}}
    if got_mis == py_mis and got_can == py_can:
        print(f"OK: ASP parity matches ({len(py_mis)} misunderstanding places, {len(py_can)} contamination pairs).")
        return 0
    print("MISMATCH:")
    print(" ASP misunderstanding:", sorted(got_mis))
    print(" PY  misunderstanding:", sorted(py_mis))
    print(" ASP can_contaminate:", sorted(got_can))
    print(" PY  can_contaminate:", sorted(py_can))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about a fella, a creak, and a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["fella", "boy", "girl"], default="fella")
    ap.add_argument("--helper-type", choices=["mother", "father", "auntie", "uncle"], default="mother")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    hero_name = getattr(args, "name", None) or rng.choice(NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    if getattr(args, "hero_type", None) == "girl" and hero_name in {"Toby", "Pip", "Otis", "Finn"}:
        hero_name = rng.choice([n for n in NAMES if n not in {"Toby", "Pip", "Otis", "Finn"}])
    if getattr(args, "helper_type", None) == "auntie" and helper_name in {"Dad", "Uncle"}:
        helper_name = "Auntie"
    return StoryParams(
        place=place,
        item=item,
        hero_name=hero_name,
        hero_type=getattr(args, "hero_type", None),
        helper_name=helper_name,
        helper_type=getattr(args, "helper_type", None),
    )


def generate(params: StoryParams) -> StorySample:
    world, hero, helper, item = resolve_story(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(place="nursery", item="jam", hero_name="Milo", hero_type="fella", helper_name="Mum", helper_type="mother"),
    StoryParams(place="porch", item="paint", hero_name="Pip", hero_type="fella", helper_name="Dad", helper_type="father"),
    StoryParams(place="kitchen", item="crumbs", hero_name="Toby", hero_type="fella", helper_name="Gran", helper_type="auntie"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show misunderstanding/1.\n#show can_contaminate/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show misunderstanding/1.\n#show can_contaminate/2."))
        print("misunderstanding:", sorted(asp.atoms(model, "misunderstanding")))
        print("can_contaminate:", sorted(asp.atoms(model, "can_contaminate")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
