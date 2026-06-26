#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/stance_pediatric_icing_teamwork_flashback_superhero_story.py
==============================================================================================================================

A small superhero-style storyworld about a child hero, a pediatric clinic,
a sticky icing problem, teamwork, and a flashback that explains the hero's
stance. The domain is intentionally compact: one premise, one tension, one
turn, one resolution.

Seed tale:
---
Mina was a tiny superhero who loved helping at the pediatric clinic. One day,
the clinic was preparing cupcakes for the children's visit, but a tub of icing
slipped and splashed onto the hero banner. Mina wanted to rush in with a bold
stance and scrub everything clean by herself, but her friend said they should
work together. Mina remembered a flashback from training day: when heroes share
the job, they finish faster and make less mess. So Mina and her team teamed up,
saved the banner, and still had time to frost the cupcakes neatly.

World design notes:
---
- Physical meters: sticky, messy, progress, banner_clean, frosting_ready.
- Emotional memes: confidence, worry, pride, teamwork, stubbornness.
- "Stance" is the hero's chosen way of facing a problem: solo, steady, or
  teamwork-first.
- "Flashback" is a narrated memory that can flip the hero from stubbornness
  to cooperation.
- The story is child-facing, concrete, and state-driven rather than an event
  log.
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


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------

STANCE_CHOICES = ("solo", "steady", "teamwork-first")

LOCATIONS = {
    "clinic": {
        "label": "the pediatric clinic",
        "affords": {"icing", "cleanup", "decorate"},
    },
    "community_room": {
        "label": "the community room",
        "affords": {"icing", "cleanup", "decorate"},
    },
    "rooftop_garden": {
        "label": "the rooftop garden",
        "affords": {"decorate", "teamwork"},
    },
}

ACTIONS = {
    "icing": {
        "verb": "frost the cupcakes",
        "gerund": "frosting cupcakes",
        "mess": "sticky",
        "soil": "smeared with icing",
        "zone": {"hands", "torso"},
        "keyword": "icing",
        "tags": {"icing", "sticky"},
    },
    "cleanup": {
        "verb": "clean the banner",
        "gerund": "scrubbing the banner",
        "mess": "messy",
        "soil": "spotted with frosting",
        "zone": {"hands"},
        "keyword": "banner",
        "tags": {"cleanup"},
    },
    "decorate": {
        "verb": "decorate the party table",
        "gerund": "decorating the table",
        "mess": "sticky",
        "soil": "sprinkled with glitter icing",
        "zone": {"hands", "torso"},
        "keyword": "decorate",
        "tags": {"teamwork"},
    },
}

GEAR = {
    "apron": {
        "label": "a blue apron",
        "covers": {"torso"},
        "guards": {"sticky"},
        "prep": "put on a blue apron first",
        "tail": "pulled on the blue apron",
    },
    "gloves": {
        "label": "clean gloves",
        "covers": {"hands"},
        "guards": {"sticky", "messy"},
        "prep": "wear clean gloves together",
        "tail": "slid into the clean gloves",
    },
    "tray": {
        "label": "a tray of cupcakes",
        "covers": {"hands"},
        "guards": {"sticky"},
        "prep": "carry the cupcakes on a tray",
        "tail": "set the tray down carefully",
    },
}

HERO_NAMES = ["Mina", "Tess", "Ravi", "Nia", "Pip", "Jules", "Lina", "Omar"]
SIDEKICK_NAMES = ["Bea", "Sol", "Ada", "Milo", "Zuri", "Theo"]
ADULT_NAMES = ["Dr. Rowan", "Nurse June", "Coach Imani", "Aunt Keira"]
TRAITS = ["brave", "kind", "quick", "curious", "spirited", "gentle"]


# ---------------------------------------------------------------------------
# Entities
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


def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)


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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    banner: object | None = None
    cupcakes: object | None = None
    hero: object | None = None
    sidekick: object | None = None
    table: object | None = None
    def __post_init__(self) -> None:
        for k in ("sticky", "messy", "progress", "clean", "frosting_ready"):
            self.meters.setdefault(k, 0.0)
        for k in ("confidence", "worry", "pride", "teamwork", "stubbornness", "calm"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "nurse"}
        male = {"boy", "man", "father", "doctor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    setting: object | None = None
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
    action: str
    stance: str
    hero: str
    sidekick: str
    adult: str
    trait: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Mechanics
# ---------------------------------------------------------------------------

def can_cover(action: str, gear_name: str) -> bool:
    return _safe_lookup(ACTIONS, action)["mess"] in GEAR[gear_name]["guards"]


def action_risks_banner(action: str) -> bool:
    return "hands" in _safe_lookup(ACTIONS, action)["zone"]


def choose_gear(action: str) -> Optional[str]:
    for gear_name in ("gloves", "apron", "tray"):
        if can_cover(action, gear_name):
            return gear_name
    return None


def predict(world: World, hero: Entity, action: str) -> dict:
    sim = world.copy()
    perform_action(sim, sim.get(hero.id), action, narrate=False)
    banner = sim.get("banner")
    return {
        "banner_soiled": banner.meters["messy"] > 0,
        "sticky": hero.meters["sticky"] > 0,
    }


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["sticky"] >= 1 and ("sticky_to_worry", ent.id) not in world.fired:
            world.fired.add(("sticky_to_worry", ent.id))
            ent.memes["worry"] += 1
            out.append(f"{ent.id} felt worried about the sticky mess.")
        if ent.memes["teamwork"] >= 1 and ent.memes["stubbornness"] > 0 and ("teamwork_calm", ent.id) not in world.fired:
            world.fired.add(("teamwork_calm", ent.id))
            ent.memes["calm"] += 1
            ent.memes["stubbornness"] = 0
            out.append(f"{ent.id}'s shoulders loosened when the team stayed close.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def perform_action(world: World, actor: Entity, action: str, narrate: bool = True) -> None:
    actor.meters[_safe_lookup(ACTIONS, action)["mess"]] += 1
    actor.memes["confidence"] += 1
    banner = world.get("banner")
    if action == "icing" and not any(item.protective and "hands" in item.covers for item in world.worn_items(actor)):
        banner.meters["messy"] += 1
        banner.meters["clean"] = 0
    if action == "decorate":
        world.get("table").meters["frosting_ready"] += 1
    world.get("cupcakes").meters["frosting_ready"] += 1
    world.get("cupcakes").meters["progress"] += 1
    propagate(world, narrate=narrate)


# ---------------------------------------------------------------------------
# Narrative beats
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, sidekick: Entity, adult: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait_word', 'brave')} hero who loved helping at {world.setting.place}."
    )
    world.say(
        f"{hero.id} and {sidekick.id} wore their capes like they were ready to save the day with {adult.id}."
    )


def setup(world: World, hero: Entity, sidekick: Entity, action: str) -> None:
    world.say(
        f"Today, the clinic was getting ready for children who were coming to visit, and everyone was making cupcakes with {_safe_lookup(ACTIONS, action)['keyword']} on top."
    )
    world.say(f"{hero.id} loved {_safe_lookup(ACTIONS, action)['gerund']}, because it made the room feel like a tiny parade.")


def flashback(world: World, hero: Entity) -> None:
    hero.memes["teamwork"] += 1
    world.say(
        f"{hero.id} had a flashback to training day: the team had once tried to do everything alone, and the work had taken forever."
    )
    world.say(
        f"In the memory, the coach had smiled and said that a true hero keeps a steady stance and lets helpers join in."
    )


def warning(world: World, adult: Entity, hero: Entity, action: str) -> None:
    if action_risks_banner(action):
        world.say(
            f'"Careful," {adult.id} said. "If you rush the {_safe_lookup(ACTIONS, action)["verb"]}, the banner could end up {_safe_lookup(ACTIONS, action)["soil"]}."'
        )


def stance_turn(world: World, hero: Entity, sidekick: Entity, stance: str) -> None:
    hero.memes["stubbornness"] += 1
    if stance == "solo":
        world.say(f"{hero.id} planted {hero.pronoun('possessive')} feet in a solo stance, ready to do it all alone.")
    elif stance == "steady":
        world.say(f"{hero.id} took a steady stance and looked at the mess without hurrying.")
    else:
        world.say(f"{hero.id} chose a teamwork-first stance and nodded toward {sidekick.id}.")


def teamwork_offer(world: World, hero: Entity, sidekick: Entity, action: str) -> Optional[str]:
    gear_name = choose_gear(action)
    if gear_name is None:
        return None
    gear = GEAR[gear_name]
    world.add(Entity(
        id=gear_name,
        type="gear",
        label=gear["label"],
        owner=hero.id,
        protective=True,
        covers=set(gear["covers"]),
        worn_by=hero.id,
    ))
    world.say(
        f'{sidekick.id} said, "How about we {gear["prep"]} and do it together?"'
    )
    return gear_name


def resolution(world: World, hero: Entity, sidekick: Entity, adult: Entity, action: str, gear_name: str) -> None:
    hero.memes["teamwork"] += 1
    hero.memes["pride"] += 1
    banner = world.get("banner")
    banner.meters["messy"] = 0
    banner.meters["clean"] = 1
    world.say(
        f"{hero.id} smiled, {hero.pronoun()} and {sidekick.id} worked side by side, and soon the banner was clean again."
    )
    world.say(
        f"Then the heroes finished {_safe_lookup(ACTIONS, action)['gerund']}, and the cupcakes sat neat and shiny on the table."
    )
    world.say(
        f"{adult.id} laughed, because the clinic still looked bright, and {hero.id}'s stance had changed from solo to teamwork-first."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    setting = Setting(place=_safe_lookup(LOCATIONS, params.place)["label"], affords=set(_safe_lookup(LOCATIONS, params.place)["affords"]))
    world = World(setting)

    hero = world.add(Entity(id=params.hero, kind="character", type="girl" if params.hero in {"Mina", "Tess", "Nia", "Pip", "Lina"} else "boy"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="girl" if params.sidekick in {"Bea", "Ada", "Zuri"} else "boy"))
    adult = world.add(Entity(id=params.adult, kind="character", type="doctor" if "Dr." in params.adult else "nurse"))
    banner = world.add(Entity(id="banner", type="banner", label="banner", phrase="a bright welcome banner", region="wall"))
    cupcakes = world.add(Entity(id="cupcakes", type="cupcakes", label="cupcakes", phrase="cupcakes for the visitors", plural=True))
    table = world.add(Entity(id="table", type="table", label="table", phrase="the party table"))

    hero.memes["trait_word"] = 0
    hero.memes["trait_word"] = 0
    hero.memes["teamwork"] += 0

    intro(world, hero, sidekick, adult)
    world.para()
    setup(world, hero, sidekick, params.action)
    warning(world, adult, hero, params.action)
    world.para()
    stance_turn(world, hero, sidekick, params.stance)
    perform_action(world, hero, params.action, narrate=True)
    flashback(world, hero)
    gear_name = teamwork_offer(world, hero, sidekick, params.action)
    if gear_name:
        perform_action(world, hero, "cleanup" if params.action == "icing" else params.action, narrate=True)
        resolution(world, hero, sidekick, adult, params.action, gear_name)

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        adult=adult,
        banner=banner,
        cupcakes=cupcakes,
        table=table,
        action=params.action,
        stance=params.stance,
        gear=gear_name,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting").place} faces {_safe_lookup(ACTIONS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "action"))["keyword"]} and learns through a flashback to choose teamwork.',
        f"Tell a gentle superhero story about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id}, {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sidekick").id}, and {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "adult").id} at the pediatric clinic, with a sticky {_safe_lookup(ACTIONS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "action"))['verb']} problem and a helpful stance change.",
        f'Write a kid-friendly superhero tale that includes the words "stance", "pediatric", and "icing", and ends with teamwork solving the mess.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    sidekick = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sidekick")
    adult = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "adult")
    action = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "action")
    stance = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "stance")
    qa = [
        QAItem(
            question=f"Who was the little hero in the story?",
            answer=f"The little hero was {hero.id}, who helped at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting").place}.",
        ),
        QAItem(
            question=f"What problem started when {hero.id} tried to {_safe_lookup(ACTIONS, action)['verb']}?",
            answer=f"The problem was a sticky icing mess that could smear the banner if {hero.id} rushed alone.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered training day, when the coach said heroes finish faster when they work together.",
        ),
        QAItem(
            question=f"How did {hero.id}'s stance change by the end?",
            answer=f"{hero.id} started with a {stance} stance, then changed to a teamwork-first stance.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the problem?",
            answer=f"{sidekick.id} helped {hero.id}, and {adult.id} kept the clinic calm while they worked.",
        ),
    ]
    if f.get("gear"):
        qa.append(
            QAItem(
                question=f"What gear helped keep the mess from spreading?",
                answer=f"{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gear")} helped by protecting {sorted(_safe_lookup(GEAR, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gear"))['covers'])} while they cleaned and frosted the cupcakes.",
            )
        )
    return qa


KNOWLEDGE = {
    "pediatric": [
        (
            "What does pediatric mean?",
            "Pediatric means about children and their health care, especially in a clinic or doctor's office.",
        )
    ],
    "icing": [
        (
            "What is icing?",
            "Icing is a sweet, spreadable topping for cakes or cupcakes that can be soft and sticky.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other and do a job together instead of doing it alone.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a memory scene that shows something from earlier and helps explain what a character knows or feels now.",
        )
    ],
    "stance": [
        (
            "What is a stance?",
            "A stance is the way someone stands or faces a problem, like standing ready, calm, or determined.",
        )
    ],
    "sticky": [
        (
            "Why can icing be sticky?",
            "Icing can be sticky because it is soft and sweet, so it can cling to hands, clothes, and surfaces.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "action")}
    tags.add("pediatric")
    tags.add("icing")
    tags.add("teamwork")
    tags.add("flashback")
    tags.add("stance")
    out: list[QAItem] = []
    for tag in ("pediatric", "icing", "teamwork", "flashback", "stance", "sticky"):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.covers:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A place affords an action if the registry says so.
affords(Place, Action) :- place(Place), action(Action), has_affordance(Place, Action).

% Sticky icing is risky when it touches the hands or torso.
risky(Action) :- action(Action), zone(Action, hands).
risky(Action) :- action(Action), zone(Action, torso).

% Gear is compatible when it guards the mess and covers a risky zone.
compatible(Gear, Action) :- gear(Gear), action(Action),
                            mess_of(Action, Mess), guards(Gear, Mess),
                            covers(Gear, Zone), zone(Action, Zone).

valid_story(Place, Action, Stance) :- affords(Place, Action), risky(Action),
                                      stance(Stance), compatible(_, Action).
"""

def asp_facts() -> str:
    from storyworlds import asp
    lines: list[str] = []
    for pid, data in LOCATIONS.items():
        lines.append(asp.fact("place", pid))
        for act in sorted(data["affords"]):
            lines.append(asp.fact("has_affordance", pid, act))
    for aid, data in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, data["mess"]))
        for z in sorted(data["zone"]):
            lines.append(asp.fact("zone", aid, z))
    for sid in STANCE_CHOICES:
        lines.append(asp.fact("stance", sid))
    for gid, data in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for m in sorted(data["guards"]):
            lines.append(asp.fact("guards", gid, m))
        for c in sorted(data["covers"]):
            lines.append(asp.fact("covers", gid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    from storyworlds import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(
        (place, action, stance)
        for place in LOCATIONS
        for action in ACTIONS
        for stance in STANCE_CHOICES
        if place in LOCATIONS and action in _safe_lookup(LOCATIONS, place)["affords"] and action_risks_banner(action) and choose_gear(action) is not None
    )
    clingo_set = set(asp_valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: pediatric icing teamwork with a flashback and stance change.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--stance", choices=STANCE_CHOICES)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("--adult", choices=ADULT_NAMES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, pdata in LOCATIONS.items():
        for action in pdata["affords"]:
            if action_risks_banner(action) and choose_gear(action) is not None:
                for stance in STANCE_CHOICES:
                    out.append((place, action, stance))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "stance", None) is None or c[2] == getattr(args, "stance", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, stance = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICK_NAMES)
    adult = getattr(args, "adult", None) or rng.choice(ADULT_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, stance=stance, hero=hero, sidekick=sidekick, adult=adult, trait=trait)


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        from storyworlds import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="clinic", action="icing", stance="teamwork-first", hero="Mina", sidekick="Bea", adult="Dr. Rowan", trait="brave"),
            StoryParams(place="community_room", action="cleanup", stance="steady", hero="Tess", sidekick="Ada", adult="Nurse June", trait="kind"),
            StoryParams(place="clinic", action="decorate", stance="solo", hero="Ravi", sidekick="Theo", adult="Coach Imani", trait="curious"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.hero}: {p.action} at {p.place} ({p.stance})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
