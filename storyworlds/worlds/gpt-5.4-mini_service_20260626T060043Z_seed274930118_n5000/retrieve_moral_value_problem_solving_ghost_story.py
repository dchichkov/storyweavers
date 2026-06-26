#!/usr/bin/env python3
"""
Storyworld: retrieve_moral_value_problem_solving_ghost_story.py

A small ghost-story world about a child who must retrieve something important
from a haunted place by using patience, honesty, and kindness.
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
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    name: str
    eerie: str
    hiding_spots: list[str] = field(default_factory=list)
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
class LostThing:
    label: str
    phrase: str
    hidden_spot: str
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
    lost: str
    name: str
    gender: str
    helper: str
    trait: str
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
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
        other = World(self.place)
        import copy as _copy

        other.entities = _copy.deepcopy(self.entities)
        other.facts = dict(self.facts)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        return other


LOCALES = {
    "attic": Place(name="the attic", eerie="dusty", hiding_spots=["old trunk", "crawlspace", "behind boxes"]),
    "churchyard": Place(name="the churchyard", eerie="quiet", hiding_spots=["stone arch", "mossy wall", "grave marker"]),
    "cottage": Place(name="the cottage hallway", eerie="shadowy", hiding_spots=["umbrella stand", "coat hook", "floorboard crack"]),
    "library": Place(name="the old library", eerie="hushed", hiding_spots=["ladder", "reading nook", "back shelf"]),
}

LOST_THINGS = {
    "lantern": LostThing(label="lantern", phrase="a little brass lantern", hidden_spot="old trunk"),
    "key": LostThing(label="key", phrase="a small silver key", hidden_spot="mossy wall"),
    "toy": LostThing(label="toy", phrase="a tiny toy train", hidden_spot="back shelf"),
    "photo": LostThing(label="photo", phrase="a faded family photo", hidden_spot="floorboard crack"),
}

GHOSTS = [
    ("Moth", "gentle"),
    ("Pale Nora", "shy"),
    ("Mr. Drift", "lonely"),
    ("Ivy Shade", "soft"),
]

TRAITS = ["brave", "careful", "patient", "kind", "quiet", "steady"]

GENDER_NAMES = {
    "girl": ["Mia", "Lina", "Eva", "Nora", "June", "Iris"],
    "boy": ["Finn", "Owen", "Leo", "Theo", "Milo", "Ben"],
}


def setup_story(world: World, hero: Entity, helper: Entity, item: Entity, lost: LostThing) -> None:
    hero.memes["worry"] += 1
    helper.memes["mystery"] += 1
    world.say(f"{hero.id} had lost {hero.pronoun('possessive')} {item.label}.")
    world.say(f"At {world.place.name}, the air felt {world.place.eerie}, and even the floorboards seemed to listen.")
    world.say(f"Then {helper.id}, a {helper.type} ghost, floated near and whispered, \"I know where it is, but you must be gentle.\"")


def problem(world: World, hero: Entity, helper: Entity, item: Entity, lost: LostThing) -> None:
    hero.memes["fear"] += 1
    world.say(f"{hero.id} wanted to retrieve {hero.pronoun('possessive')} {item.label}, but the wrong choice could scare the ghost away.")
    world.say(f"The {world.place.eerie} place hid clues in {lost.hidden_spot}, and the answer would take careful thinking.")


def solve(world: World, hero: Entity, helper: Entity, item: Entity, lost: LostThing) -> None:
    hero.memes["kindness"] += 1
    hero.memes["problem_solving"] += 1
    helper.memes["trust"] += 1
    item.hidden_in = lost.hidden_spot
    world.say(f"{hero.id} took a slow breath, said thank you, and asked what the ghost needed.")
    world.say(f"The ghost pointed with a pale finger, and {hero.id} followed the clue to {lost.hidden_spot}.")
    world.say(f"There {hero.id} found {item.phrase} and gently retrieved it instead of grabbing or shouting.")
    item.carried_by = hero.id


def ending(world: World, hero: Entity, helper: Entity, item: Entity, lost: LostThing) -> None:
    hero.memes["relief"] += 1
    helper.memes["peace"] += 1
    world.say(f"{hero.id} smiled and held {hero.pronoun('possessive')} {item.label} close.")
    world.say(f"The ghost looked brighter, because kindness had solved the problem, and the haunted room felt calm at last.")


def tell(place: Place, lost: LostThing, hero_name: str, hero_gender: str, helper_name: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="ghost", label=helper_name))
    item = world.add(Entity(id=lost.label, type=lost.label, label=lost.label, phrase=lost.phrase))
    setup_story(world, hero, helper, item, lost)
    world.para()
    problem(world, hero, helper, item, lost)
    world.para()
    solve(world, hero, helper, item, lost)
    ending(world, hero, helper, item, lost)
    world.facts.update(hero=hero, helper=helper, item=item, lost=lost, place=place, trait=trait)
    return world


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(_safe_lookup(GENDER_NAMES, gender))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for children about a {f["trait"]} child who must retrieve a lost {f["lost"].label} from {f["place"].name}.',
        f'Tell a gentle story where {f["hero"].id} meets a ghost and uses kindness and problem solving to retrieve a missing object.',
        f'Write a spooky-but-kind story in which a child in {f["place"].name} listens carefully to a ghost clue and retrieves {f["lost"].phrase}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    item: Entity = _safe_fact(world, f, "item")
    lost: LostThing = _safe_fact(world, f, "lost")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What did {hero.id} need to retrieve in {place.name}?",
            answer=f"{hero.id} needed to retrieve {hero.pronoun('possessive')} {item.label}, which was {lost.phrase}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} in the spooky place?",
            answer=f"A gentle ghost named {helper.id} helped by giving a clue and not hiding the answer forever.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} stayed calm, listened to the ghost, followed the clue, and retrieved the lost thing with kindness.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The missing {item.label} was found, the ghost felt peaceful, and the scary place became calm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story like this?",
            answer="In a gentle ghost story, a ghost is a spooky character who can also be lonely, helpful, or kind.",
        ),
        QAItem(
            question="What does it mean to retrieve something?",
            answer="To retrieve something means to go get it back after it was lost or put away somewhere else.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully, finding clues, and choosing a good way to fix a problem.",
        ),
        QAItem(
            question="Why is kindness important in a ghost story?",
            answer="Kindness can help build trust, calm fear, and make it easier to solve the problem without hurting anyone's feelings.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return [(place, lost) for place in LOCALES for lost in LOST_THINGS]


@dataclass
class _AspGate:
    place: str
    lost: str
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


ASP_RULES = r"""
place(P) :- loc(P).
lost(L) :- thing(L).
can_story(P,L) :- loc(P), thing(L).
#show can_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in LOCALES:
        lines.append(asp.fact("loc", p))
    for l in LOST_THINGS:
        lines.append(asp.fact("thing", l))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_story/2."))
    return sorted(set(asp.atoms(model, "can_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story about retrieving a lost thing through kindness and problem solving.")
    ap.add_argument("--place", choices=LOCALES)
    ap.add_argument("--lost", choices=LOST_THINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = getattr(args, "place", None) or rng.choice(list(LOCALES))
    lost = getattr(args, "lost", None) or rng.choice(list(LOST_THINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(GENDER_NAMES, gender))
    helper = getattr(args, "helper", None) or rng.choice([n for n, _ in GHOSTS])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, lost=lost, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(LOCALES, params.place), _safe_lookup(LOST_THINGS, params.lost), params.name, params.gender, params.helper, params.trait)
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
    StoryParams(place="attic", lost="lantern", name="Mia", gender="girl", helper="Moth", trait="patient"),
    StoryParams(place="churchyard", lost="key", name="Finn", gender="boy", helper="Pale Nora", trait="kind"),
    StoryParams(place="library", lost="toy", name="Lina", gender="girl", helper="Mr. Drift", trait="careful"),
    StoryParams(place="cottage", lost="photo", name="Theo", gender="boy", helper="Ivy Shade", trait="steady"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show can_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
        for place, lost in triples:
            print(f"  {place:12} {lost}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: retrieve {p.lost} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
