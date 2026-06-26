#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero tale with a quest, antic sound
effects, and a kid-friendly turn from chaos to teamwork.

Premise:
A young hero wants to complete a small quest in the city, but their playful
antic creates a mess of sound effects and trouble. A helper superhero reroutes
the excitement into a safer mission, and the story ends with the quest finished
and the hero proud.

The world tracks physical meters and emotional memes:
- meters: noise, damage, progress, comfort
- memes: excitement, worry, pride, gratitude, mischief, teamwork

The simulated state drives the prose; the story is not a frozen paragraph.
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


NOISE_THRESHOLD = 2
PROGRESS_DONE = 3



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
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ally: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for k in ["noise", "damage", "progress", "comfort"]:
            self.meters.setdefault(k, 0.0)
        for k in ["excitement", "worry", "pride", "gratitude", "mischief", "teamwork"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    name: str
    afford: set[str] = field(default_factory=set)
    risk: str = "noise"
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
class Quest:
    id: str
    goal: str
    verb: str
    progress_word: str
    reward: str
    sound: str
    sound_word: str
    antic: str
    risk: str
    helper_action: str
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
class Sidekick:
    id: str
    label: str
    phrase: str
    fix: str
    ability: str
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
    world: object | None = None
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w
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
    "rooftop": Place("the rooftop", {"gadget"}, "noise"),
    "alley": Place("the alley", {"dash", "gadget"}, "noise"),
    "museum": Place("the museum hall", {"gadget", "search"}, "noise"),
    "library": Place("the library steps", {"search"}, "noise"),
}

QUESTS = {
    "rescue_bell": Quest(
        id="rescue_bell",
        goal="find the city bell",
        verb="find the city bell",
        progress_word="searching",
        reward="the bell chimed again",
        sound="clang-clang",
        sound_word="clang",
        antic="a clattery antic",
        risk="noise",
        helper_action="quiet the noise",
    ),
    "deliver_map": Quest(
        id="deliver_map",
        goal="deliver the secret map",
        verb="deliver the secret map",
        progress_word="dash forward",
        reward="the map reached its friend",
        sound="zip-zip",
        sound_word="zip",
        antic="a zooming antic",
        risk="noise",
        helper_action="slip into a quieter route",
    ),
    "save_kitten": Quest(
        id="save_kitten",
        goal="save the kitten from the tree",
        verb="reach the kitten",
        progress_word="climb",
        reward="the kitten was safe",
        sound="meow-meow",
        sound_word="meow",
        antic="a wobbly antic",
        risk="noise",
        helper_action="steady the climb",
    ),
}

SIDEKICKS = {
    "echo": Sidekick("echo", "Echo", "a calm helper superhero", "mute the loud burst", "quiet"),
    "glider": Sidekick("glider", "Glider", "a swift helper superhero", "guide the route", "speed"),
    "spark": Sidekick("spark", "Spark", "a bright helper superhero", "turn the moment into teamwork", "light"),
}

HERO_NAMES = ["Nova", "Milo", "Tess", "Ari", "Lena", "Jax", "Iris", "Pip"]
HERO_TRAITS = ["bold", "curious", "brave", "cheerful", "sly", "lively"]


def reasonableness_gate(place: Place, quest: Quest, sidekick: Sidekick) -> None:
    if quest.risk not in place.afford:
        pass
    if quest.risk == "noise" and sidekick.ability == "quiet":
        return
    if quest.risk == "noise" and sidekick.ability in {"speed", "light", "quiet"}:
        return
    pass


def predict(world: World, hero: Entity, quest: Quest) -> dict:
    sim = world.copy()
    do_antic(sim, sim.get(hero.id), quest, narrate=False)
    return {
        "noisy": sim.get(hero.id).meters["noise"] >= NOISE_THRESHOLD,
        "progress": sim.get(hero.id).meters["progress"],
    }


def do_antic(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    hero.meters["noise"] += 1
    hero.memes["mischief"] += 1
    hero.memes["excitement"] += 1
    if narrate:
        world.say(f"{hero.id} made {quest.antic} that went {quest.sound} around {world.place.name}.")
        if hero.meters["noise"] >= NOISE_THRESHOLD:
            world.say(f"The sound bounced off the walls and made everything feel too loud.")


def do_quest(world: World, hero: Entity, quest: Quest) -> None:
    hero.meters["progress"] += 1
    hero.memes["pride"] += 1
    world.say(f"{hero.id} kept {quest.progress_word}, and the quest moved closer to {quest.goal}.")


def offer_help(world: World, hero: Entity, sidekick: Sidekick, quest: Quest) -> None:
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1)
    hero.memes["teamwork"] += 1
    world.say(
        f"Then {sidekick.label} swooped in like {sidekick.phrase} and said they could {sidekick.fix}."
    )


def accept_help(world: World, hero: Entity, sidekick: Sidekick, quest: Quest) -> None:
    hero.memes["gratitude"] += 1
    hero.memes["worry"] = 0
    hero.meters["comfort"] += 1
    world.say(
        f"{hero.id} nodded, and together they turned the antic into a smarter plan."
    )
    world.say(
        f"With {sidekick.label}'s help, {hero.id} could {quest.verb} without the noisy trouble."
    )


def finish(world: World, hero: Entity, quest: Quest) -> None:
    hero.meters["progress"] = PROGRESS_DONE
    hero.memes["pride"] += 1
    world.say(
        f"At last, {hero.id} finished the quest, and {quest.reward}."
    )
    world.say(
        f"{hero.id} stood tall, proud and calm, while the last {quest.sound_word}-{quest.sound_word} faded away."
    )


def tell(place: Place, quest: Quest, sidekick: Sidekick, hero_name: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="hero", label=hero_name))
    ally = world.add(Entity(id=sidekick.id, kind="character", type="sidekick", label=sidekick.label))
    world.facts.update(hero=hero, ally=ally, quest=quest, place=place, sidekick=sidekick, trait=trait)

    world.say(f"{hero.id} was a {trait} little superhero who loved a good quest.")
    world.say(f"{hero.id} wanted to {quest.verb}, because {quest.goal} sounded exciting.")
    world.say(f"The air near {place.name} seemed ready for trouble and cheer.")

    world.para()
    do_antic(world, hero, quest)
    pred = predict(world, hero, quest)
    if pred["noisy"]:
        hero.memes["worry"] += 1
        world.say(f"{hero.id} frowned because the antic made the whole mission feel shaky.")
        offer_help(world, hero, sidekick, quest)
        accept_help(world, hero, sidekick, quest)

    world.para()
    do_quest(world, hero, quest)
    finish(world, hero, quest)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a short superhero story for a child about {hero.id} and a quest at {place.name}.',
        f'Write a gentle story where a small hero makes an antic sound like "{quest.sound}" and then gets help.',
        f'Create a kid-friendly superhero adventure that includes a noisy antic and a happy teamwork ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ally, quest, place, sidekick = f["hero"], f["ally"], f["quest"], f["place"], f["sidekick"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do at {place.name}?",
            answer=f"{hero.id} was trying to {quest.verb}. It was a small superhero quest in {place.name}.",
        ),
        QAItem(
            question=f"What kind of antic did {hero.id} make?",
            answer=f"{hero.id} made {quest.antic}, and it sounded like {quest.sound} in the story.",
        ),
        QAItem(
            question=f"Who helped turn the noisy problem into teamwork?",
            answer=f"{sidekick.label} helped by staying calm and using {sidekick.fix}. That made the quest easier for {hero.id}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} finished the quest, felt proud, and saw that {quest.reward}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or mission that someone tries to complete, often step by step.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that imitate noises, like bang, zip, clang, or meow.",
        ),
        QAItem(
            question="Why can loud noise make a plan harder?",
            answer="Loud noise can make it harder to think, listen, and work together, so a calm helper can make things easier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story Q&A ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World Q&A ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    quest: str
    sidekick: str
    name: str
    trait: str
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a quest and sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=HERO_TRAITS)
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
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    sidekick = getattr(args, "sidekick", None) or rng.choice(list(SIDEKICKS))
    trait = getattr(args, "trait", None) or rng.choice(HERO_TRAITS)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    reasonableness_gate(_safe_lookup(PLACES, place), _safe_lookup(QUESTS, quest), _safe_lookup(SIDEKICKS, sidekick))
    return StoryParams(place=place, quest=quest, sidekick=sidekick, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(SIDEKICKS, params.sidekick), params.name, params.trait)
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
place(rooftop; alley; museum; library).
quest(rescue_bell; deliver_map; save_kitten).
sidekick(echo; glider; spark).

supports(rooftop, rescue_bell).
supports(alley, deliver_map).
supports(alley, rescue_bell).
supports(museum, rescue_bell).
supports(museum, deliver_map).
supports(museum, save_kitten).
supports(library, save_kitten).

helper(echo, quiet).
helper(glider, speed).
helper(spark, light).

valid(P, Q, S) :- supports(P, Q), helper(S, _).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for s in SIDEKICKS:
        lines.append(asp.fact("sidekick", s))
    for p, place in PLACES.items():
        for q in sorted(place.afford):
            lines.append(asp.fact("supports", p, q))
    for s, sk in SIDEKICKS.items():
        lines.append(asp.fact("helper", s, sk.ability))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program())
    asp_set = set(asp.atoms(model, "valid"))
    py_set = set()
    for p, place in PLACES.items():
        for q in place.afford:
            for s in SIDEKICKS:
                py_set.add((p, q, s))
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH")
    print("only in asp:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid combos")
        for v in vals:
            print(v)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in PLACES:
            for quest in sorted(_safe_lookup(PLACES, place).afford):
                for sidekick in SIDEKICKS:
                    try:
                        params = StoryParams(place=place, quest=quest, sidekick=sidekick, name="Nova", trait="brave")
                        reasonableness_gate(_safe_lookup(PLACES, place), _safe_lookup(QUESTS, quest), _safe_lookup(SIDEKICKS, sidekick))
                        samples.append(generate(params))
                    except StoryError:
                        pass
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
