#!/usr/bin/env python3
"""
storyworlds/worlds/confident_foreshadowing_dialogue_transformation_fairy_tale.py
==============================================================================

A small fairy-tale story world about a confident character, a foreshadowed spell,
spoken warnings and promises, and a transformation that changes the ending image.

Premise:
- A brave child or young helper carries a simple task into a magical place.
- A foreshadowed sign hints that the wrong choice will trigger an enchanted
  transformation.
- Dialogue gives a warning, a refusal, then a wiser promise.
- The resolution transforms the problem into a gentler form and leaves a clear
  final image of change.

This world keeps the vocabulary small and the cause-and-effect concrete.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    wears: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "man"}:
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
class Setting:
    place: str
    flavor: str
    affords: set[str] = field(default_factory=set)
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
class Curse:
    id: str
    trigger: str
    warning: str
    transform: str
    change_to: str
    sign: str
    weakens_with: str
    reason: str
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
    curse: str
    name: str
    gender: str
    title: str
    companion: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}
        self.observed_sign: bool = False
        self.transformed: bool = False
        self.trace_events: list[str] = []

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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "forest": Setting(place="the moonlit forest", flavor="A silver path wound between dark trees.", affords={"curse", "song"}),
    "tower": Setting(place="the high tower", flavor="A narrow stair turned around a single glowing window.", affords={"curse", "song"}),
    "lake": Setting(place="the hidden lake", flavor="Mist floated low above the water like a sleeping shawl.", affords={"curse", "song"}),
}

CURSES = {
    "stone": Curse(
        id="stone",
        trigger="touch the bright stone",
        warning="The bright stone in the moss shone like a tiny eye.",
        transform="turn to stone for a little while",
        change_to="a statue",
        sign="a cold gleam ran over the stone",
        weakens_with="a kind song",
        reason="the curse listened to hasty hands but softened when someone spoke gently and waited",
    ),
    "owl": Curse(
        id="owl",
        trigger="open the silver box",
        warning="The silver box clicked softly, as if it already knew a secret.",
        transform="change into an owl",
        change_to="a white owl",
        sign="feathers drifted from the lid",
        weakens_with="a brave apology",
        reason="the magic liked honesty better than hurry",
    ),
    "rose": Curse(
        id="rose",
        trigger="pluck the red rose",
        warning="The red rose bowed low on its stem, as if it wanted to be left alone.",
        transform="become a rosebush",
        change_to="a rosebush",
        sign="one thorn prickled before the flower opened",
        weakens_with="a careful promise",
        reason="the spell wanted respect for growing things",
    ),
}

HEROES = {
    "girl": ["Ada", "Mina", "Lina", "Nora", "Elsa", "Tessa"],
    "boy": ["Felix", "Theo", "Rowan", "Jonas", "Milo", "Soren"],
}

TRAITS = ["confident", "bright-eyed", "careful", "bold", "gentle", "curious"]

COMPANIONS = {
    "fox": "a small fox with a rust-red tail",
    "bird": "a blue bird perched on a branch",
    "grandmother": "a grandmother who knew old songs",
    "page": "a little page with ink on his fingers",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for curse_id in setting.affords:
            out.append((place, curse_id))
    return out


def story_intro(hero: Entity, companion: str, setting: Setting) -> str:
    return (
        f"{hero.id} was a {hero.traits[0]} little {hero.type} who walked "
        f"with {companion} through {setting.place}."
    )


def foreshadow(world: World, hero: Entity, curse: Curse) -> None:
    world.observed_sign = True
    world.facts["sign"] = curse.sign
    world.say(
        f"{curse.warning} {curse.sign}, and {hero.id} slowed down to look."
    )


def dialogue_warning(world: World, hero: Entity, curse: Curse) -> None:
    world.say(
        f'"Don’t {curse.trigger}," said {world.get("companion").label}. '
        f'"That magic can make someone {curse.transform}."'
    )


def dialogue_confident_reply(world: World, hero: Entity, curse: Curse) -> None:
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
    world.say(
        f'"I can handle it," {hero.id} said with a confident grin. '
        f'"I will be careful."'
    )


def maybe_trigger_transform(world: World, hero: Entity, curse: Curse) -> None:
    if world.facts.get("chosen_action") == curse.trigger:
        hero.meters["magic"] = hero.meters.get("magic", 0) + 1
        world.trace_events.append("curse_triggered")
        world.say(
            f"{hero.id} reached out anyway, and the spell woke up at once."
        )
        world.say(
            f"{curse.sign}; {hero.id} began to {curse.transform}."
        )
        world.transformed = True


def resolve_transform(world: World, hero: Entity, curse: Curse) -> None:
    if not world.transformed:
        return
    world.say(
        f"Then {world.get('companion').label} began to {curse.weakens_with}."
    )
    world.say(
        f"The magic listened. The spell loosened, and {hero.id} did not stay "
        f"{curse.change_to}."
    )
    world.transformed = False
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.meters["magic"] = 0


def ending_image(world: World, hero: Entity, curse: Curse) -> None:
    if curse.id == "stone":
        world.say(
            f"By the end, {hero.id} stood safe beneath the trees, and the bright stone "
            f"shone quietly where it had been left alone."
        )
    elif curse.id == "owl":
        world.say(
            f"By the end, {hero.id} was back beside {world.get('companion').label}, "
            f"and the silver box stayed shut with its secret tucked inside."
        )
    else:
        world.say(
            f"By the end, {hero.id} smiled beside the rose bush, and the red flowers "
            f"bloomed where no rough hand had gone."
        )


def tell(setting: Setting, curse: Curse, hero_name: str, hero_type: str,
         trait: str, companion_key: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=[trait, "confident"],
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type="helper",
        label=_safe_lookup(COMPANIONS, companion_key),
        traits=["wise"],
    ))

    world.say(story_intro(hero, companion.label, setting))
    world.say(setting.flavor)
    foreshadow(world, hero, curse)

    world.para()
    world.say(
        f"{hero.id} found {curse.reason}, but the little {hero.type} wanted to see "
        f"the secret close up."
    )
    dialogue_warning(world, hero, curse)
    dialogue_confident_reply(world, hero, curse)

    # The chosen action is the actual turn of the tale.
    if curse.id == "stone":
        action = "touch the bright stone"
    elif curse.id == "owl":
        action = "open the silver box"
    else:
        action = "pluck the red rose"
    world.facts["chosen_action"] = action
    world.say(f"At last, {hero.id} tried to {action}.")
    maybe_trigger_transform(world, hero, curse)

    world.para()
    if world.transformed:
        resolve_transform(world, hero, curse)
    else:
        world.say(
            f"Because {hero.id} stopped in time, the magic did not finish the change."
        )

    world.para()
    ending_image(world, hero, curse)

    world.facts.update(
        hero=hero,
        companion=companion,
        curse=curse,
        setting=setting,
        transformed=not world.transformed and world.facts.get("chosen_action") == action,
        safe=not world.transformed,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    curse: Curse = _safe_fact(world, f, "curse")
    return [
        'Write a short fairy tale with a confident child, a foreshadowed warning, and a magical transformation.',
        f"Tell a gentle fairy tale about {hero.id}, who is confident enough to ignore a warning about {curse.trigger}.",
        f"Write a story where a sign in the forest hints that magic may {curse.transform}, and dialogue helps solve it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    companion: Entity = _safe_fact(world, f, "companion")
    curse: Curse = _safe_fact(world, f, "curse")
    setting: Setting = _safe_fact(world, f, "setting")

    return [
        QAItem(
            question=f"Who is the story about in {setting.place}?",
            answer=f"The story is about {hero.id}, a {hero.traits[0]} little {hero.type}, and {companion.label}.",
        ),
        QAItem(
            question=f"What warning sign foreshadowed trouble for {hero.id}?",
            answer=f"The warning sign was that {curse.sign}. It hinted that the magic could {curse.transform}.",
        ),
        QAItem(
            question=f"What did {hero.id} say before the magic happened?",
            answer=f"{hero.id} said, \"I can handle it,\" and promised to be careful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    curse: Curse = _safe_fact(world, f, "curse")
    if curse.id == "stone":
        return [
            QAItem(
                question="What is a statue?",
                answer="A statue is something made to stand still and look like a person, animal, or shape.",
            ),
            QAItem(
                question="Why do people sing softly sometimes?",
                answer="People sing softly when they want to be gentle, calm a friend, or help someone feel safe.",
            ),
        ]
    if curse.id == "owl":
        return [
            QAItem(
                question="What is an owl?",
                answer="An owl is a bird that often flies at night and has big eyes for seeing in the dark.",
            ),
            QAItem(
                question="Why should a secret box stay shut?",
                answer="A secret box should stay shut if the magic inside is meant to wait until the right time.",
            ),
        ]
    return [
        QAItem(
            question="What is a rosebush?",
            answer="A rosebush is a plant that grows roses and thorny stems.",
        ),
        QAItem(
            question="Why do careful hands matter around flowers?",
            answer="Careful hands matter because flowers can be damaged if they are picked too roughly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(forest; tower; lake).
curse(stone; owl; rose).

affords(forest, curse). affords(forest, song).
affords(tower, curse).  affords(tower, song).
affords(lake, curse).   affords(lake, song).

valid(Place, Curse) :- place(Place), curse(Curse), affords(Place, curse).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
        for afforded in sorted(_safe_lookup(SETTINGS, place).affords):
            lines.append(asp.fact("affords", place, afforded))
    for curse_id in CURSES:
        lines.append(asp.fact("curse", curse_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for curse_id in setting.affords:
            combos.append((place, curse_id))
    return combos


def explain_rejection(place: str, curse: str) -> str:
    return f"(No story: {place} does not plausibly fit the {curse} curse.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale world with foreshadowing, dialogue, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--curse", choices=CURSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
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
    if getattr(args, "place", None) and getattr(args, "curse", None) and (getattr(args, "place", None), getattr(args, "curse", None)) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    curse = getattr(args, "curse", None) or rng.choice(sorted(_safe_lookup(SETTINGS, place).affords))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(HEROES, gender))
    companion = getattr(args, "companion", None) or rng.choice(list(COMPANIONS))
    trait = getattr(args, "trait", None) or "confident"
    return StoryParams(place=place, curse=curse, name=name, gender=gender, title="child", companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(CURSES, params.curse),
        params.name,
        params.gender,
        params.trait,
        params.companion,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  observed_sign={world.observed_sign}")
    lines.append(f"  transformed={world.transformed}")
    lines.append(f"  fired={world.fired}")
    lines.append(f"  trace_events={world.trace_events}")
    return "\n".join(lines)


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
    StoryParams(place="forest", curse="stone", name="Nora", gender="girl", title="child", companion="grandmother", trait="confident"),
    StoryParams(place="tower", curse="owl", name="Theo", gender="boy", title="child", companion="bird", trait="confident"),
    StoryParams(place="lake", curse="rose", name="Mina", gender="girl", title="child", companion="fox", trait="confident"),
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
        print(f"{len(combos)} valid combos:")
        for place, curse in combos:
            print(f"  {place}  {curse}")
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
            header = f"### {p.name}: {p.curse} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
