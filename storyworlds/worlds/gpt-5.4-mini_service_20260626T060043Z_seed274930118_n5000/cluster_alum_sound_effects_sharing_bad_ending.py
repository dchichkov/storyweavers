#!/usr/bin/env python3
"""
storyworlds/worlds/cluster_alum_sound_effects_sharing_bad_ending.py
====================================================================

A small nursery-rhyme-style story world about a little cluster of friends,
bouncy sound effects, a shared treat, and a bad ending when the plan goes wrong.

The seed image is a tiny rhyme-like scene: a cluster of bright things, a jar of
alum on the shelf, a child who loves sound effects, and a sharing moment that
turns sour. The simulation keeps track of physical state (meters) and feelings
(memes), and the prose follows what the world state actually does.

Core premise:
- A child plays with a cluster of noisy little objects.
- They want to share a treat with friends.
- A jar of alum sits nearby and must not spill.
- If the noisy play and sharing go poorly, the story ends in a bad ending.

The tone stays child-facing and singsong, but the ending is genuinely sour.
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
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0
SOFT = 0.5

SFX = {
    "plink",
    "plonk",
    "clink",
    "tink",
    "patter",
    "tap-tap",
    "thump",
    "whoosh",
}

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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    fragile: bool = False
    def __post_init__(self):
        if not self.meters:
            self.meters = {"mess": 0.0, "spill": 0.0, "noise": 0.0, "sour": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "want": 0.0, "share": 0.0, "sad": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    place: str = "the kitchen"
    indoor: bool = True
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
class ClusterThing:
    id: str
    label: str
    phrase: str
    sfx: str
    fragile: bool = False
    shareable: bool = False
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
    name: str
    gender: str
    parent: str
    trait: str
    cluster: str
    share_item: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
    "kitchen": Setting(place="the kitchen", indoor=True),
    "porch": Setting(place="the porch", indoor=False),
    "playroom": Setting(place="the playroom", indoor=True),
}

CLUSTERS = {
    "bells": ClusterThing(
        id="bells",
        label="cluster of bells",
        phrase="a cluster of bright bells",
        sfx="clink",
        fragile=False,
        shareable=True,
    ),
    "spoons": ClusterThing(
        id="spoons",
        label="cluster of spoons",
        phrase="a cluster of shiny spoons",
        sfx="plink",
        fragile=False,
        shareable=True,
    ),
    "buttons": ClusterThing(
        id="buttons",
        label="cluster of buttons",
        phrase="a cluster of tiny buttons",
        sfx="tap-tap",
        fragile=True,
        shareable=True,
    ),
}

SHARE_ITEMS = {
    "cake": ClusterThing(
        id="cake",
        label="cake",
        phrase="a little honey cake",
        sfx="",
        fragile=True,
        shareable=True,
    ),
    "berries": ClusterThing(
        id="berries",
        label="berries",
        phrase="a bowl of red berries",
        sfx="",
        fragile=False,
        shareable=True,
    ),
}

TRAITS = ["bright-eyed", "cheerful", "bouncy", "curious", "jolly"]
GIRL_NAMES = ["Mina", "Lily", "Nora", "Poppy", "Ruby"]
BOY_NAMES = ["Ben", "Theo", "Milo", "Finn", "Jack"]
PARTNERS = ["mother", "father", "grandma", "grandpa"]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def is_reasonable(place: str, cluster: str, share_item: str) -> bool:
    return place in SETTINGS and cluster in CLUSTERS and share_item in SHARE_ITEMS


def invalid_reason(place: str, cluster: str, share_item: str) -> str:
    return f"(No story: {cluster} and {share_item} do not fit this tiny rhyme world.)"


def sfx_line(sfx: str) -> str:
    return {
        "plink": "Plink, plink, went the little things.",
        "clink": "Clink, clink, sang the bright little bells.",
        "tap-tap": "Tap-tap, went the tiny buttons.",
        "patter": "Patter, patter, went the soft little steps.",
    }.get(sfx, "It made a small sound.")


def child_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            label=params.name,
            traits=[params.trait, "little"],
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=params.parent,
            label=params.parent,
        )
    )
    cluster = _safe_lookup(CLUSTERS, params.cluster)
    share_item = _safe_lookup(SHARE_ITEMS, params.share_item)

    cluster_ent = world.add(
        Entity(
            id=cluster.id,
            type="thing",
            label=cluster.label,
            phrase=cluster.phrase,
            plural=True,
            owner=hero.id,
            location=setting.place,
        )
    )
    item_ent = world.add(
        Entity(
            id=share_item.id,
            type="thing",
            label=share_item.label,
            phrase=share_item.phrase,
            owner=hero.id,
            caretaker=parent.id,
            location=setting.place,
        )
    )
    alum = world.add(
        Entity(
            id="alum",
            type="thing",
            label="alum",
            phrase="a little jar of alum",
            owner=parent.id,
            location=setting.place,
            fragile=True,
        )
    )

    # Act 1: setup
    world.say(f"{params.name} was a {params.trait} little {params.gender} in {setting.place}.")
    world.say(
        f"{params.name} loved the {cluster.label}, and {sfx_line(cluster.sfx)} "
        f"the room went."
    )
    world.say(
        f"On the shelf sat {alum.phrase}, all neat and trim, "
        f"and {params.name} was told, 'Leave the alum there, sweet child, leave it be.'"
    )
    world.para()

    # Act 2: desire and sharing
    hero.memes["want"] += 1
    hero.memes["joy"] += 1
    cluster_ent.meters["noise"] += 1
    world.say(
        f"But {params.name} wanted to share {item_ent.phrase} with everyone at hand."
    )
    world.say(
        f"{params.name} set the {cluster.label} to bouncing and chiming, "
        f"and the whole table heard {sfx_line(cluster.sfx).lower()}"
    )
    if cluster_ent.type == "thing":
        cluster_ent.meters["noise"] += 1
    world.say(
        f"Then the small folks reached for the share dish, and little hands came quick."
    )
    hero.memes["share"] += 1

    # Bad turn: the noisy cluster bumps the shelf, alum spills, and the share goes wrong.
    if cluster_ent.meters["noise"] >= THRESHOLD:
        hero.meters["mess"] += 1
        alum.meters["spill"] += 1
        alum.meters["mess"] += 1
        item_ent.meters["spill"] += 1
        item_ent.meters["mess"] += 1
        hero.memes["worry"] += 1
        parent.memes["worry"] += 1
        world.say(
            f"But tumble-tap, the {cluster.label} knocked the shelf with a slip and a shimmy."
        )
        world.say(
            f"The jar of alum tipped, and out it spilled with a pale little puff."
        )
        world.say(
            f"Alum dust drifted over the shared {share_item.label}, and no one liked the taste."
        )

    # Ending: bad ending, no fix.
    hero.memes["joy"] = max(0.0, hero.memes["joy"] - 1)
    hero.memes["sad"] += 1
    parent.memes["sad"] += 1
    world.para()
    world.say(
        f"{params.name} looked down and felt the fun go flat. The sharing was over, "
        f"the cake was spoiled, and the bright song had turned to a sigh."
    )
    world.say(
        f"At the end, the little {params.name} sat by the sticky dish, "
        f"and the alum jar stayed shut while the room went quiet."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        cluster=cluster,
        cluster_ent=cluster_ent,
        share_item=share_item,
        item_ent=item_ent,
        alum=alum,
        setting=setting,
        bad_ending=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    cluster = _safe_fact(world, f, "cluster")
    share_item = _safe_fact(world, f, "share_item")
    return [
        f'Write a short nursery-rhyme-style story about a little {hero.type} named {hero.id} '
        f"who makes sound effects with a {cluster.label} and tries to share {share_item.phrase}.",
        f"Tell a gentle but sad story where {hero.id} hears {cluster.sfx} sounds, "
        f"shares a treat, and the alum spills so the ending is bad.",
        f'Write a tiny rhyme that uses the words "cluster" and "alum" and ends with a sour little mishap.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    cluster: ClusterThing = _safe_fact(world, f, "cluster")
    share_item: ClusterThing = _safe_fact(world, f, "share_item")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about little {hero.id}, a {hero.traits[0]} {hero.type} who lives in {f['setting'].place}.",
        ),
        QAItem(
            question=f"What did {hero.id} love to play with?",
            answer=f"{hero.id} loved the {cluster.label}, and it went {cluster.sfx} while {hero.id} played.",
        ),
        QAItem(
            question=f"What did {hero.id} want to share?",
            answer=f"{hero.id} wanted to share {share_item.phrase} with everyone nearby.",
        ),
        QAItem(
            question=f"Why did the ending turn bad?",
            answer=(
                f"The ending turned bad because the noisy {cluster.label} knocked the shelf, "
                f"the alum jar spilled, and the shared {share_item.label} got ruined."
            ),
        ),
        QAItem(
            question=f"What was left at the end?",
            answer=(
                f"At the end, {hero.id} sat by the spoiled dish while the alum jar stayed shut "
                f"and the room went quiet."
            ),
        ),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "alum": [
        (
            "What is alum?",
            "Alum is a small crystal-like substance that can be kept in a jar. People sometimes use it for cleaning or crafting, but it is not food.",
        )
    ],
    "share": [
        (
            "What does it mean to share?",
            "To share means to give some of what you have to other people so everyone can enjoy it.",
        )
    ],
    "sound": [
        (
            "What are sound effects?",
            "Sound effects are little sounds like clink, tap-tap, or plink that help a story feel lively.",
        )
    ],
    "cluster": [
        (
            "What is a cluster?",
            "A cluster is a small group of things that are close together, like bells on a string or berries on a stem.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question=q, answer=a)
        for key in ["cluster", "sound", "share", "alum"]
        for q, a in WORLD_KNOWLEDGE[key]
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is compatible when the chosen place exists, the cluster can make sound
% effects, and the shared item can be spoiled by the bad ending.
compatible(P, C, S) :- place(P), cluster(C), share_item(S),
                       noisy(C), shareable(S).

% A bad ending is expected when a noisy cluster and a fragile shared item meet.
bad_end(C, S) :- noisy(C), shareable(S), fragile(S).

#show compatible/3.
#show bad_end/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for cid, c in CLUSTERS.items():
        lines.append(asp.fact("cluster", cid))
        lines.append(asp.fact("noisy", cid))
        if c.fragile:
            lines.append(asp.fact("fragile", cid))
    for sid, s in SHARE_ITEMS.items():
        lines.append(asp.fact("share_item", sid))
        lines.append(asp.fact("shareable", sid))
        if s.fragile:
            lines.append(asp.fact("fragile", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Parameter logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for cluster in CLUSTERS:
            for share_item in SHARE_ITEMS:
                if is_reasonable(place, cluster, share_item):
                    combos.append((place, cluster, share_item))
    return combos


def explain_rejection(place: str, cluster: str, share_item: str) -> str:
    return invalid_reason(place, cluster, share_item)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: cluster, alum, sound effects, sharing, bad ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--cluster", choices=CLUSTERS)
    ap.add_argument("--share-item", choices=SHARE_ITEMS, dest="share_item")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARTNERS)
    ap.add_argument("--name")
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "cluster", None) is None or c[1] == getattr(args, "cluster", None))
        and (getattr(args, "share_item", None) is None or c[2] == getattr(args, "share_item", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, cluster, share_item = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or child_name(gender, rng)
    parent = getattr(args, "parent", None) or rng.choice(PARTNERS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)

    return StoryParams(
        place=place,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        cluster=cluster,
        share_item=share_item,
    )


# ---------------------------------------------------------------------------
# Generation / emit
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="kitchen", name="Mina", gender="girl", parent="mother", trait="bouncy", cluster="bells", share_item="cake"),
    StoryParams(place="porch", name="Milo", gender="boy", parent="father", trait="curious", cluster="spoons", share_item="berries"),
    StoryParams(place="playroom", name="Nora", gender="girl", parent="grandma", trait="jolly", cluster="buttons", share_item="cake"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3.\n#show bad_end/2."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.cluster} / {p.share_item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
