#!/usr/bin/env python3
"""
storyworlds/worlds/loot_bad_ending_teamwork_comedy.py
=====================================================

A standalone storyworld for a tiny comedy about loot, teamwork, and a bad
ending that still feels playful instead of grim.

Premise:
- A small team hears about a shiny piece of loot.
- They try to reach it together.
- Their teamwork keeps the plan moving, but the final prize turns out to be a
  silly disappointment: the "loot" is not treasure at all.
- The ending is bad for the goal, but comic in tone.

The world tracks physical state in meters and emotional state in memes:
- meters: proximity to the loot, carried items, obstruction, and mess
- memes: excitement, teamwork, confusion, embarrassment, and delight

The prose is state-driven: the story changes as the team coordinates, reaches
the chest, and discovers the joke hidden inside it.
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
# Typed entities and world state
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    loot: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
    outdoors: bool = True
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
class Loot:
    id: str
    label: str
    phrase: str
    weight: str
    bait: str
    joke: str
    value: int
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
class CrewRole:
    id: str
    label: str
    skill: str
    help_line: str
    reaction: str
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
        self.fired: set[tuple] = set()
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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "attic": Setting(place="the dusty attic", outdoors=False, affords={"search"}),
    "dock": Setting(place="the old dock", outdoors=True, affords={"search"}),
    "cave": Setting(place="the echoing cave", outdoors=True, affords={"search"}),
    "yard": Setting(place="the back yard", outdoors=True, affords={"search"}),
}

LOOT = {
    "crown": Loot(
        id="crown",
        label="gold crown",
        phrase="a very shiny gold crown",
        weight="heavy",
        bait="shine",
        joke="it was a plastic party crown covered in sticker stars",
        value=9,
    ),
    "chest": Loot(
        id="chest",
        label="treasure chest",
        phrase="a tiny treasure chest with a brass latch",
        weight="heavy",
        bait="mystery",
        joke="it was full of three spoons, a lemon, and a note that said 'nice try'",
        value=7,
    ),
    "coin": Loot(
        id="coin",
        label="coin pile",
        phrase="a pile of glittering coins",
        weight="medium",
        bait="clink",
        joke="the coins were chocolate tokens wrapped in crinkly foil",
        value=5,
    ),
}

CREW = [
    CrewRole(
        id="planner",
        label="planner",
        skill="map the path",
        help_line="I know a shortcut if we all carry our part.",
        reaction="grinned like the job was already done",
    ),
    CrewRole(
        id="carrier",
        label="carrier",
        skill="lift the loot",
        help_line="One of us can hold the box while the others guide it.",
        reaction="wobbled and tried not to laugh",
    ),
    CrewRole(
        id="spotter",
        label="spotter",
        skill="watch for trouble",
        help_line="I will keep an eye on the latch and the floorboards.",
        reaction="pointed dramatically at every squeak",
    ),
]

NAMES = ["Milo", "Pip", "Nina", "Bea", "Ollie", "Tara", "Juno", "Finn"]
TRAITS = ["brave", "curious", "silly", "busy", "bouncy", "cheery"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    loot: str
    hero: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def loot_is_reachable(setting: Setting, loot: Loot) -> bool:
    return "search" in setting.affords and loot.value > 0


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for loot_id in LOOT:
            if loot_is_reachable(setting, LOOT[loot_id]):
                out.append((place, loot_id))
    return out


def explain_rejection(place: str, loot_id: str) -> str:
    loot = LOOT[loot_id]
    return (
        f"(No story: {loot.label} would not make a believable loot target at {place}. "
        f"The setting must support a search, and the prize must be worth chasing.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, sidekick: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait_word', 'silly')} {hero.type} who loved a good mystery."
    )
    world.say(
        f"{sidekick.id} was {sidekick.pronoun('possessive')} best helper, always ready to stick around and make a plan."
    )


def discover_loot(world: World, loot: Entity) -> None:
    loot.meters["hidden"] = 1.0
    world.say(
        f"One day, they found a rumor about {loot.phrase} at {world.setting.place}."
    )
    world.say(
        f"It sounded like real loot, the kind that makes knees wiggle with excitement."
    )


def team_up(world: World, hero: Entity, sidekick: Entity, loot: Entity) -> None:
    hero.memes["excitement"] += 1
    sidekick.memes["excitement"] += 1
    hero.memes["teamwork"] += 1
    sidekick.memes["teamwork"] += 1
    world.say(
        f"{hero.id} said, 'We should do this together,' and {sidekick.id} nodded so hard it looked like a tiny drum solo."
    )
    world.say(
        f"They split the job so the {loot.label} could be found without anyone tripping over the joke of the day."
    )


def search(world: World, hero: Entity, sidekick: Entity, loot: Entity) -> None:
    hero.meters["distance_to_loot"] = 1.0
    sidekick.meters["distance_to_loot"] = 1.0
    world.say(
        f"They tiptoed through {world.setting.place}, checking corners, crates, and suspiciously serious shadows."
    )
    world.say(
        f"{sidekick.id} lifted a lid while {hero.id} held the lantern, and the whole team felt clever."
    )


def reveal_bad_ending(world: World, loot: Entity) -> None:
    loot.meters["revealed"] = 1.0
    world.say(
        f"At last, the loot was open."
    )
    world.say(
        f"Then everybody stared at the inside, because {loot.joke}."
    )
    world.say(
        f"The big treasure sound turned into a tiny embarrassed snort."
    )


def aftermath(world: World, hero: Entity, sidekick: Entity, loot: Entity) -> None:
    hero.memes["confusion"] += 1
    sidekick.memes["confusion"] += 1
    hero.memes["delight"] += 1
    sidekick.memes["delight"] += 1
    world.say(
        f"{hero.id} laughed first, because sometimes a bad ending is funniest when everyone is standing together."
    )
    world.say(
        f"{sidekick.id} laughed too, and they carried home the not-treasure anyway, just because it was such a ridiculous prize."
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def tell(setting: Setting, loot_cfg: Loot, hero_name: str = "Milo", sidekick_name: str = "Pip", trait: str = "silly") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="boy"))
    loot = world.add(Entity(
        id=loot_cfg.id,
        type="thing",
        label=loot_cfg.label,
        phrase=loot_cfg.phrase,
        owner=hero.id,
        carried_by=None,
    ))
    hero.memes["trait_word"] = trait
    sidekick.memes["trait_word"] = "helpful"

    introduce(world, hero, sidekick)
    world.para()
    discover_loot(world, loot)
    team_up(world, hero, sidekick, loot)
    world.para()
    search(world, hero, sidekick, loot)
    reveal_bad_ending(world, loot)
    world.para()
    aftermath(world, hero, sidekick, loot)

    world.facts.update(hero=hero, sidekick=sidekick, loot=loot, loot_cfg=loot_cfg, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    loot_cfg: Loot = _safe_fact(world, f, "loot_cfg")
    return [
        f'Write a funny short story for a child about a team searching for "{loot_cfg.label}" and finding a silly surprise instead.',
        f"Tell a comedy story set at {world.setting.place} where two friends use teamwork to chase loot, but the ending is a bad one for the treasure.",
        f"Write a small story with teamwork, loot, and a joke hidden at the end: {loot_cfg.bait} should lead to a disappointment.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    loot_cfg: Loot = _safe_fact(world, f, "loot_cfg")
    place = world.setting.place
    return [
        QAItem(
            question=f"Who searched for the loot at {place}?",
            answer=f"{hero.id} and {sidekick.id} searched together, and they used teamwork the whole time.",
        ),
        QAItem(
            question=f"What kind of loot did they think they were finding?",
            answer=f"They thought they were finding {loot_cfg.phrase}. It looked important and shiny from the outside.",
        ),
        QAItem(
            question="Was the ending a good treasure ending?",
            answer=f"No. The ending was bad for the treasure because {loot_cfg.joke}. Still, the friends laughed about it together.",
        ),
        QAItem(
            question=f"How did the friends feel about the search before the reveal?",
            answer=f"They felt excited and busy, because they were working as a team to reach the loot.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is loot?",
            answer="Loot is something valuable that people or characters want to find, carry, or keep after an adventure.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other, share jobs, and work toward the same goal together.",
        ),
        QAItem(
            question="What is a bad ending in a comedy story?",
            answer="A bad ending in a comedy story can mean the goal fails, but the result is still funny instead of sad.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_ok(P) :- setting(P).
loot_ok(L) :- loot(L).
valid(P, L) :- place_ok(P), loot_ok(L), affords(P, search).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.outdoors:
            lines.append(asp.fact("outdoors", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for loot_id, loot in LOOT.items():
        lines.append(asp.fact("loot", loot_id))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy loot storyworld with teamwork and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--loot", choices=LOOT)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    if getattr(args, "place", None) and getattr(args, "loot", None):
        if (getattr(args, "place", None), getattr(args, "loot", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "loot", None) is None or c[1] == getattr(args, "loot", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, loot_id = rng.choice(list(combos))
    hero = getattr(args, "name", None) or rng.choice(NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice([n for n in NAMES if n != hero])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, loot=loot_id, hero=hero, sidekick=sidekick, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), LOOT[params.loot], params.hero, params.sidekick, params.trait)
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
    StoryParams(place="attic", loot="chest", hero="Milo", sidekick="Pip", trait="silly"),
    StoryParams(place="dock", loot="coin", hero="Nina", sidekick="Bea", trait="curious"),
    StoryParams(place="cave", loot="crown", hero="Ollie", sidekick="Tara", trait="bouncy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        vals = asp_valid_combos()
        print(f"{len(vals)} compatible combos:\n")
        for p, l in vals:
            print(f"  {p:8} {l}")
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
            header = f"### {p.hero}: {p.loot} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
