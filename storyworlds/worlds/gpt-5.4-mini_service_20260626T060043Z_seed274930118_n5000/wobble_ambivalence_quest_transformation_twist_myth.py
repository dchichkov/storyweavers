#!/usr/bin/env python3
"""
A small mythic storyworld about a quest that wobbles, meets ambivalence, and
turns through transformation and twist.

The seed image:
- A young seeker hears of a lost star-crown.
- The seeker starts a quest with confidence, then wobbles.
- A guide offers two paths, and the seeker feels ambivalence.
- The final twist reveals the treasure was never outside the seeker.
- Transformation ends the tale: the seeker becomes the kind of person who can
  carry the light.

This file is self-contained and follows the Storyweavers world contract.
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
# Domain model
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carrier: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "sister"}
        male = {"boy", "man", "father", "king", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def word(self) -> str:
        return "them" if self.plural else "it"
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
    place: str = "the whispering hill"
    detail: str = "where old stones kept the wind inside them"
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
class Relic:
    id: str
    label: str
    phrase: str
    type: str
    tags: set[str] = field(default_factory=set)
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
class Companion:
    id: str
    label: str
    type: str
    advice: str
    path_a: str
    path_b: str
    question: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "hill": Setting(place="the whispering hill", detail="where old stones kept the wind inside them"),
    "river": Setting(place="the silver river", detail="where moonlight shook like glass on the water"),
    "cave": Setting(place="the lantern cave", detail="where the dark breathed softly between the rocks"),
    "forest": Setting(place="the pine forest", detail="where the branches made a thousand listening ears"),
}

RELICS = {
    "star_crown": Relic(
        id="star_crown",
        label="star-crown",
        phrase="a crown of small bright stars",
        type="crown",
        tags={"star", "light", "quest", "transformation"},
    ),
    "bell_seed": Relic(
        id="bell_seed",
        label="bell-seed",
        phrase="a seed that could grow a singing bell-tree",
        type="seed",
        tags={"song", "quest", "transformation"},
    ),
    "mirror_pear": Relic(
        id="mirror_pear",
        label="mirror-pear",
        phrase="a pear smooth as still water",
        type="fruit",
        tags={"mirror", "twist"},
    ),
}

COMPANIONS = {
    "owl": Companion(
        id="owl",
        label="the owl",
        type="owl",
        advice="listen to both voices before choosing one",
        path_a="the bright path",
        path_b="the shaded path",
        question="Would the seeker go where the sun was loud, or where the roots were quiet?",
    ),
    "river": Companion(
        id="river_spirit",
        label="the river spirit",
        type="spirit",
        advice="hold what changes and let go of what only shines",
        path_a="the upstream road",
        path_b="the bank below",
        question="Would the seeker walk upstream, or follow the bend that looked like a sleeping snake?",
    ),
}

HERO_NAMES = ["Ari", "Mira", "Soren", "Lina", "Toma", "Nera", "Ivo", "Elia"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["young", "brave", "quiet", "restless", "earnest", "small"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    relic: str
    companion: str
    hero_name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
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


def _hero_title(hero: Entity) -> str:
    return f"{next((t for t in hero.traits if t != 'young'), 'young')} {hero.type}"


def _setup(world: World, hero: Entity, relic: Relic, companion: Companion) -> None:
    world.say(
        f"In {world.setting.place}, {world.setting.detail}, there lived {hero.id}, "
        f"a {_hero_title(hero)} who had heard of {relic.phrase}."
    )
    hero.memes["longing"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} wanted to find {relic.label} and bring it back before the night grew old."
    )
    world.say(
        f"At the edge of the path stood {companion.label}, who asked, "
        f"\"{companion.question}\""
    )
    world.facts["quest"] = True


def _wobble(world: World, hero: Entity) -> None:
    hero.memes["wobble"] += 1
    hero.memes["confidence"] = max(0.0, hero.memes.get("confidence", 1.0) - 0.6)
    world.say(
        f"{hero.id} took the first steps with a steady heart, but the ground began to wobble "
        f"under {hero.pronoun('possessive')} feet."
    )
    world.say(
        f"The stones rolled a little, and {hero.id}'s brave stride turned smaller."
    )
    world.facts["wobble"] = True


def _ambivalence(world: World, hero: Entity, companion: Companion) -> None:
    hero.memes["ambivalence"] += 1
    hero.memes["doubt"] += 1
    world.say(
        f"{hero.id} looked at {companion.path_a} and then at {companion.path_b}."
    )
    world.say(
        f"One way gleamed, the other way waited, and {hero.id} felt ambivalence tugging both hands at once."
    )
    world.say(f"{companion.label} said, \"{companion.advice}.\"")
    world.facts["ambivalence"] = True


def _twist(world: World, hero: Entity, relic: Relic) -> None:
    hero.memes["surprise"] += 1
    world.say(
        f"At the end of the road, {hero.id} found the treasure place empty."
    )
    if relic.id == "star_crown":
        world.say(
            f"Yet when {hero.id} bowed {hero.pronoun('possessive')} head in the dark, "
            f"the water below flashed, and the lost star-crown was only a reflection waiting to be worn inside."
        )
    elif relic.id == "bell_seed":
        world.say(
            f"Yet when {hero.id} opened {hero.pronoun('possessive')} palm, the bell-seed was already warm there, "
            f"as if the quest had been carrying it all along."
        )
    else:
        world.say(
            f"Yet when {hero.id} lifted the mirror-pear, it showed not a missing prize but {hero.id}'s own bright face, "
            f"ready for change."
        )
    world.facts["twist"] = True


def _transformation(world: World, hero: Entity, relic: Relic) -> None:
    hero.memes["resolve"] += 1
    hero.memes["joy"] += 1
    hero.memes["ambivalence"] = 0.0
    hero.memes["wobble"] = 0.0
    world.say(
        f"{hero.id} understood then that the quest had changed {hero.id} more than it had changed the road."
    )
    if relic.id == "star_crown":
        world.say(
            f"{hero.id} returned not with a crown in {hero.pronoun('possessive')} hands, but with a steadier head and a light that did not shake."
        )
    elif relic.id == "bell_seed":
        world.say(
            f"{hero.id} returned with the seed of song, and wherever {hero.id} stepped, the world seemed ready to bloom."
        )
    else:
        world.say(
            f"{hero.id} returned seeing plainly, as if {hero.id} had become a mirror that knew how to tell the truth."
        )
    world.facts["transformation"] = True


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------

def tell(setting: Setting, relic: Relic, companion: Companion, hero_name: str, hero_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["young", trait],
    ))
    world.facts.update(hero=hero, relic=relic, companion=companion, setting=setting)

    _setup(world, hero, relic, companion)
    world.para()
    _wobble(world, hero)
    _ambivalence(world, hero, companion)
    world.para()
    _twist(world, hero, relic)
    _transformation(world, hero, relic)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    relic: Relic = _safe_fact(world, f, "relic")
    companion: Companion = _safe_fact(world, f, "companion")
    return [
        f'Write a short myth for a child about {hero.id} and a {relic.label} on a quest that includes a wobble.',
        f"Tell a mythic story where {hero.id}, a {hero.type}, feels ambivalence before choosing between {companion.path_a} and {companion.path_b}.",
        f"Write a gentle myth with a twist in which a seeker finds that the treasure changes the seeker too.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    relic: Relic = _safe_fact(world, f, "relic")
    companion: Companion = _safe_fact(world, f, "companion")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"What was {hero.id} trying to do in {setting.place}?",
            answer=f"{hero.id} was on a quest to find {relic.label} and bring it home."
        ),
        QAItem(
            question=f"What made {hero.id} wobble during the quest?",
            answer=f"The ground wobbled under {hero.id}'s feet, and the brave stride became smaller."
        ),
        QAItem(
            question=f"Why did {hero.id} feel ambivalence?",
            answer=f"{hero.id} saw two paths, and both seemed to call at once, so {hero.id} could not choose quickly."
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The treasure was not only something outside {hero.id}; it became a change inside {hero.id} too."
        ),
        QAItem(
            question=f"How did the quest end?",
            answer=f"{hero.id} returned transformed, with a steadier heart and a new kind of light."
        ),
    ]


WORLD_KNOWLEDGE = {
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a long and important journey to find something or do something difficult."
        )
    ],
    "transformation": [
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means changing into a new form or becoming very different from before."
        )
    ],
    "twist": [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the reader thought was going to happen."
        )
    ],
    "wobble": [
        QAItem(
            question="What does wobble mean?",
            answer="To wobble means to move unsteadily, like something that is almost but not quite balanced."
        )
    ],
    "ambivalence": [
        QAItem(
            question="What is ambivalence?",
            answer="Ambivalence is when someone feels two different ways about the same choice at the same time."
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        *WORLD_KNOWLEDGE["quest"],
        *WORLD_KNOWLEDGE["wobble"],
        *WORLD_KNOWLEDGE["ambivalence"],
        *WORLD_KNOWLEDGE["transformation"],
        *WORLD_KNOWLEDGE["twist"],
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
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
quest(H) :- hero(H).
wobble(H) :- quest(H), ground_unsteady(H).
ambivalence(H) :- quest(H), two_paths(H).
twist(H) :- quest(H), treasure_within(H).
transformation(H) :- twist(H), learn(H).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        for t in sorted(relic.tags):
            lines.append(asp.fact("tagged", rid, t))
    for cid in COMPANIONS:
        lines.append(asp.fact("companion", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show quest/1.\n#show wobble/1.\n#show ambivalence/1.\n#show twist/1.\n#show transformation/1.")
    model = asp.one_model(program)
    shown = {
        "quest": set(asp.atoms(model, "quest")),
        "wobble": set(asp.atoms(model, "wobble")),
        "ambivalence": set(asp.atoms(model, "ambivalence")),
        "twist": set(asp.atoms(model, "twist")),
        "transformation": set(asp.atoms(model, "transformation")),
    }
    if any(shown.values()):
        print("OK: ASP program is syntactically solvable.")
        return 0
    print("MISMATCH: ASP program produced no shown atoms.")
    return 1


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic quest storyworld with wobble, ambivalence, twist, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    relic = getattr(args, "relic", None) or rng.choice(list(RELICS))
    companion = getattr(args, "companion", None) or rng.choice(list(COMPANIONS))
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, relic=relic, companion=companion, hero_name=name, hero_type=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(RELICS, params.relic),
        _safe_lookup(COMPANIONS, params.companion),
        params.hero_name,
        params.hero_type,
        params.trait,
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show quest/1.\n#show wobble/1.\n#show ambivalence/1.\n#show twist/1.\n#show transformation/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "seed", None) is not None:
        base_seed = getattr(args, "seed", None)
    else:
        base_seed = random.randrange(2**31)

    samples: list[StorySample] = []

    if getattr(args, "all", None):
        cur = [
            StoryParams("hill", "star_crown", "owl", "Ari", "girl", "quiet"),
            StoryParams("river", "mirror_pear", "river", "Soren", "boy", "restless"),
            StoryParams("cave", "bell_seed", "owl", "Mira", "girl", "earnest"),
        ]
        samples = [generate(p) for p in cur]
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
