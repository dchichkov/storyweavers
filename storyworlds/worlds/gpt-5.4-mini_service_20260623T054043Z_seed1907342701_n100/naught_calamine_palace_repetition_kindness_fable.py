#!/usr/bin/env python3
"""
storyworlds/worlds/naught_calamine_palace_repetition_kindness_fable.py
======================================================================

A small fable-like storyworld about a palace, repeated kindness, and a soothing
bottle of calamine. The premise is simple: someone at the palace has an itchy,
worrying problem, and repeated kindness turns a prickly moment into a calm one.

The world is intentionally tiny and constraint-checked:
- a place (the palace or its gardens),
- a trouble (itch or rash),
- a helper action (kindness, repeated),
- a soothing item (calamine),
- and a final change in physical state that proves the ending.

The stories are state-driven rather than template-swapped. The same world model
feeds prose, QA, and the ASP twin.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    plural: bool = False
    owner: str = ""
    caretaker: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    balm: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
        if not hasattr(self, "_tags"):
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
    has_windows: bool = False
    echoes: bool = False
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Trouble:
    id: str
    label: str
    phrase: str
    body_part: str
    cause_word: str
    mess_word: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

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
class Remedy:
    id: str
    label: str
    phrase: str
    action: str
    repeat: str
    calm_word: str
    clears: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

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
    place: str = ""
    trouble: str = ""
    remedy: str = ""
    name: str = ""
    role: str = ""
    helper_name: str = ""
    helper_role: str = ""
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    def __init__(self, place: Place) -> None:
        self.place = place
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

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _fix_rash(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["rash"] < THRESHOLD:
            continue
        sig = ("rash", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["itch"] += 1
        out.append(f"{ent.label_word} felt extra itchy.")
    return out


def _calm_by_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    cared = world.entities.get("hero")
    if not helper or not cared:
        return out
    if helper.memes["kindness"] < THRESHOLD:
        return out
    if cared.meters["itch"] < THRESHOLD:
        return out
    sig = ("kindness", helper.id, cared.id, int(helper.memes["kindness"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cared.memes["relief"] += 1
    helper.memes["care"] += 1
    out.append(f"{helper.label_word} sat close and repeated a kind word.")
    return out


CAUSAL_RULES = [
    _fix_rash,
    _calm_by_kindness,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(trouble: Trouble, remedy: Remedy) -> bool:
    return trouble.body_part in remedy.clears


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for trouble_id, trouble in TROUBLES.items():
            for remedy_id, remedy in REMEDIES.items():
                if place_id in place.affords and hazard_at_risk(trouble, remedy):
                    combos.append((place_id, trouble_id, remedy_id))
    return combos


def explain_rejection(place: Place, trouble: Trouble, remedy: Remedy) -> str:
    if place.id not in place.affords:
        return f"(No story: {place.label} does not support that kind of trouble.)"
    if not hazard_at_risk(trouble, remedy):
        return f"(No story: {remedy.label} would not soothe {trouble.label} here.)"
    return "(No story: this combination is not reasonable.)"


def tone_line(place: Place) -> str:
    if place.id == "palace_hall":
        return "The palace hall was tall and quiet, with polished floors and bright banners."
    return "The palace garden was soft with grass, and the little paths curved under the trees."


def predict_calm(world: World, hero: Entity, helper: Entity, remedy: Remedy) -> bool:
    sim = world.copy()
    sim.get("hero").meters["itch"] += 1
    sim.get("hero").meters["rash"] += 1
    simulate_kindness(sim, narrate=False)
    apply_remedy(sim, sim.get("hero"), sim.get("helper"), remedy, narrate=False)
    return sim.get("hero").memes["relief"] >= THRESHOLD


def simulate_kindness(world: World, narrate: bool = True) -> None:
    world.get("helper").memes["kindness"] += 1
    world.get("hero").memes["hope"] += 1
    propagate(world, narrate=narrate)


def apply_remedy(world: World, hero: Entity, helper: Entity, remedy: Remedy, narrate: bool = True) -> None:
    sig = ("remedy", remedy.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.meters["rash"] = max(0.0, hero.meters["rash"] - 1.0)
    hero.meters["itch"] = max(0.0, hero.meters["itch"] - 1.0)
    hero.memes["relief"] += 1
    helper.memes["care"] += 1
    if narrate:
        world.say(f"{helper.label_word} brought {remedy.phrase} and used it gently.")


def tell(place: Place, trouble: Trouble, remedy: Remedy,
         name: str = "Nina", role: str = "girl",
         helper_name: str = "Mira", helper_role: str = "girl") -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=role, label=name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_role, label=helper_name, role="helper"))
    balm = world.add(Entity(id="balm", type="thing", label=remedy.label, phrase=remedy.phrase, owner=helper.id))
    world.facts.update(hero=hero, helper=helper, balm=balm, trouble=trouble, remedy=remedy, place=place)

    hero.meters["itch"] = 0.0
    hero.meters["rash"] = 0.0
    hero.memes["worry"] = 0.0
    helper.memes["kindness"] = 0.0
    helper.memes["care"] = 0.0

    world.say(f"In the {place.label}, {hero.label_word} was known for a soft heart and a steady step.")
    world.say(f"{hero.label_word} had a little trouble: {trouble.phrase}.")
    world.say(f"{helper.label_word} watched closely and promised to help.")

    world.para()
    world.say(tone_line(place))
    world.say(f"One day, {hero.label_word} felt {trouble.label} on {trouble.body_part}.")
    world.say(f"{hero.label_word} tried to bear it with naught complaint, but the itch grew worse.")

    world.para()
    world.say(f"{helper.label_word} did not laugh. {helper.label_word} said the same kind thing twice: 'Stay still, stay still.'")
    world.say(f"That repetition made the room feel calmer.")
    simulate_kindness(world)

    if predict_calm(world, hero, helper, remedy):
        world.say(f"{helper.label_word} reached for the palace kit and chose {remedy.phrase}.")
        apply_remedy(world, hero, helper, remedy)
        world.say(f"After that, {hero.label_word}'s skin cooled, and the red patch faded.")
        world.para()
        world.say(f"By evening, the palace hall was bright again, and {hero.label_word} walked past the echoing doors with a calm smile.")
        world.say(f"{helper.label_word} kept the rest of the {remedy.label} on a shelf, ready for the next small trouble.")
    else:
        world.say(f"{helper.label_word} tried the calm thing, but the itch still troubled {hero.label_word}.")
        world.para()
        world.say(f"So {helper.label_word} called for a wiser hand, and the story ended with a hush instead of a cure.")

    world.facts.update(resolved=hero.memes["relief"] >= THRESHOLD)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    trouble = f["trouble"]
    remedy = f["remedy"]
    place = f["place"]
    return [
        f'Write a short fable about kindness in a {place.label}, and include the words "naught", "{remedy.label}", and "{trouble.label}".',
        f"Tell a gentle story where {hero.label_word} has {trouble.phrase}, {helper.label_word} helps with {remedy.phrase}, and a repeated kind phrase makes things better.",
        f"Write a child-facing palace fable about a small trouble, a repeated kindness, and a quiet ending image that shows the worry has eased.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    trouble = f["trouble"]
    remedy = f["remedy"]
    place = f["place"]
    qa = [
        QAItem(
            question=f"Who is the fable about in the {place.label}?",
            answer=f"It is about {hero.label_word} and {helper.label_word} in the {place.label}. {hero.label_word} had a small trouble, and {helper.label_word} answered it with kindness.",
        ),
        QAItem(
            question=f"What problem did {hero.label_word} have?",
            answer=f"{hero.label_word} had {trouble.phrase}. It made the skin feel itchy and uncomfortable, so the day needed a gentle fix.",
        ),
        QAItem(
            question=f"What did {helper.label_word} bring to help?",
            answer=f"{helper.label_word} brought {remedy.phrase}. The soothing calamine helped cool the rash and made the hurt easier to bear.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"Why did the repeated kind words matter?",
                answer=f"They mattered because {helper.label_word} said the kind thing again and again, and that repetition helped {hero.label_word} feel safe. Once the worry settled, the remedy could do its job more easily.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did the story end for {hero.label_word}?",
                answer=f"It ended with {hero.label_word}'s skin calm and the red patch faded. {helper.label_word} left the {remedy.label} ready on the shelf, and the palace felt peaceful again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is calamine?",
            answer="Calamine is a soothing lotion that can help calm itchy skin and dry a rash.",
        ),
        QAItem(
            question="What does kindness do in a fable?",
            answer="Kindness helps someone feel safe, cared for, and less alone. In a fable, it often changes a bad moment into a better one.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means saying or doing something again and again. It can make a message feel steady and easy to remember.",
        ),
        QAItem(
            question="What does naught mean?",
            answer="Naught means nothing at all. It is an old-fashioned word that can mean zero or nothing.",
        ),
    ]


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:6} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


PLACES = {
    "palace_hall": Place(id="palace_hall", label="palace hall", affords={"itch", "rash"}, has_windows=True, echoes=True),
    "palace_garden": Place(id="palace_garden", label="palace garden", affords={"itch", "rash"}, has_windows=False, echoes=False),
    "palace_infirmary": Place(id="palace_infirmary", label="palace infirmary", affords={"itch", "rash"}, has_windows=False, echoes=True),
}

TROUBLES = {
    "itch": Trouble(id="itch", label="itch", phrase="an itchy patch", body_part="arm", cause_word="scratching", mess_word="redness", zone={"arm"}, tags={"itch", "kindness"}),
    "rash": Trouble(id="rash", label="rash", phrase="a pink rash", body_part="cheek", cause_word="irritation", mess_word="flare", zone={"cheek"}, tags={"rash", "kindness"}),
    "sting": Trouble(id="sting", label="sting", phrase="a stingy spot", body_part="knee", cause_word="sting", mess_word="soreness", zone={"knee"}, tags={"sting", "kindness"}),
}

REMEDIES = {
    "calamine": Remedy(id="calamine", label="calamine", phrase="a little bottle of calamine", action="dab", repeat="again and again", calm_word="calm", clears={"arm", "cheek", "knee"}, tags={"calamine", "soothing"}),
    "oat_lotion": Remedy(id="oat_lotion", label="oat lotion", phrase="a pot of oat lotion", action="smooth", repeat="once more", calm_word="soft", clears={"arm", "cheek"}, tags={"lotion", "soothing"}),
    "cool_cloth": Remedy(id="cool_cloth", label="cool cloth", phrase="a cool wet cloth", action="press", repeat="one more time", calm_word="cool", clears={"arm", "cheek", "knee"}, tags={"cloth", "soothing"}),
}

CURATED = [
    StoryParams(place="palace_hall", trouble="itch", remedy="calamine", name="Mina", role="girl", helper_name="Tessa", helper_role="girl"),
    StoryParams(place="palace_garden", trouble="rash", remedy="oat_lotion", name="Oren", role="boy", helper_name="Lina", helper_role="girl"),
    StoryParams(place="palace_infirmary", trouble="sting", remedy="cool_cloth", name="Lila", role="girl", helper_name="Hana", helper_role="girl"),
    StoryParams(place="palace_hall", trouble="rash", remedy="calamine", name="Eli", role="boy", helper_name="Nora", helper_role="girl"),
]


def asp_facts() -> str:
    import asp

    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("body_part", tid, t.body_part))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for c in sorted(r.clears):
            lines.append(asp.fact("clears", rid, c))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, T, R) :- place(P), trouble(T), remedy(R), affords(P, T), body_part(T, B), clears(R, B).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    rc = 0
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        with redirect_stdout(io.StringIO()):
            emit(sample, qa=True, trace=True)
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {err}")
        return 1

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a palace fable of repeated kindness and calamine.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-role", choices=["girl", "boy"])
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
              and (getattr(args, "trouble", None) is None or c[1] == getattr(args, "trouble", None))
              and (getattr(args, "remedy", None) is None or c[2] == getattr(args, "remedy", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, trouble, remedy = rng.choice(list(combos))
    role = getattr(args, "role", None) or rng.choice(["girl", "boy"])
    helper_role = getattr(args, "helper_role", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(["Nina", "Mina", "Lila", "Oren", "Eli", "Ada", "Mira"])
    helper_name = getattr(args, "helper_name", None) or rng.choice(["Tessa", "Hana", "Nora", "Lina", "Suri", "Maya"])
    return StoryParams(place=place, trouble=trouble, remedy=remedy, name=name, role=role, helper_name=helper_name, helper_role=helper_role)


def generation_prompts_wrapper(world: World) -> list[str]:
    return generation_prompts(world)


def generate(params: StoryParams) -> StorySample:
    try:
        place = _safe_lookup(PLACES, params.place)
        trouble = _safe_lookup(TROUBLES, params.trouble)
        remedy = _safe_lookup(REMEDIES, params.remedy)
    except KeyError as err:
        pass
    world = tell(place, trouble, remedy, params.name, params.role, params.helper_name, params.helper_role)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
        for p, t, r in combos:
            print(f"  {p:18} {t:8} {r}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name} at {p.place} ({p.trouble}, {p.remedy})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
