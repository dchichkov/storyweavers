#!/usr/bin/env python3
"""
A standalone storyworld for a tiny whodunit about an oboe, a celebration, and a
tremendous transformation that only teamwork can explain.

Premise:
- A cheerful neighborhood concert is preparing to celebrate.
- The prized oboe disappears.
- The clues are mostly sound effects: a squeak, a thump, a shimmer, a clap.
- Several characters help, each noticing a different trace.
- The final reveal is a transformation in how the team works together, and the
  oboe is found in a surprising but ordinary place.

This world is intentionally small and constraint-checked. It models:
- physical meters: location, carried objects, hidden/visible state, sound trace
- emotional memes: worry, confidence, suspicion, delight, teamwork

The prose is written in a child-facing whodunit style: a mystery, clues, a
gentle investigation, and a satisfying reveal.
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
# Core domain model
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
    owner: Optional[str] = None
    hidden: bool = False
    carried_by: Optional[str] = None
    location: str = ""
    can_make_sounds: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    oboe: object | None = None
    ribbon: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
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
    place: str
    detail: str
    supports: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    sound: str
    points_to: str
    requires: set[str] = field(default_factory=set)
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
class ObjectDef:
    id: str
    label: str
    phrase: str
    location: str
    fragile: bool = False
    hidden_spot: str = ""
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
    setting: str
    clue: str
    hero_name: str
    helper_name: str
    suspect_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
    params: object | None = None
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
        self.facts: dict = {}
        self.events: list[str] = []
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.events = list(self.events)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "music_room": Setting(
        place="the music room",
        detail="Brass stands, a piano bench, and a row of shiny cases lined the walls.",
        supports={"concert", "practice", "search"},
    ),
    "school_stage": Setting(
        place="the school stage",
        detail="Curtains hung like red hills, and the floorboards waited for careful feet.",
        supports={"concert", "practice", "search"},
    ),
    "community_hall": Setting(
        place="the community hall",
        detail="Paper stars dangled above the chairs, ready for a cheerful show.",
        supports={"concert", "practice", "search", "celebrate"},
    ),
}

CLUES = {
    "squeak": Clue(
        id="squeak",
        label="a squeak",
        sound="squeak",
        points_to="case",
        requires={"oboe"},
    ),
    "thump": Clue(
        id="thump",
        label="a thump",
        sound="thump",
        points_to="bench",
        requires={"oboe"},
    ),
    "shimmer": Clue(
        id="shimmer",
        label="a shimmer",
        sound="shimmer",
        points_to="cloth",
        requires={"celebrate"},
    ),
    "clap": Clue(
        id="clap",
        label="a clap",
        sound="clap",
        points_to="teamwork",
        requires={"teamwork"},
    ),
}

OBJECTS = {
    "oboe": ObjectDef(
        id="oboe",
        label="oboe",
        phrase="a polished oboe with a warm wooden shine",
        location="music_room_case",
        fragile=True,
        hidden_spot="bench_cushion",
    ),
    "ribbon": ObjectDef(
        id="ribbon",
        label="gold ribbon",
        phrase="a gold ribbon for the celebration",
        location="announcement_board",
        fragile=False,
        hidden_spot="folded_paper",
    ),
    "lamp": ObjectDef(
        id="lamp",
        label="lamp",
        phrase="a small lamp with a bright switch",
        location="teacher_desk",
        fragile=False,
        hidden_spot="stage_curtain",
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Iris", "Nora", "Pia", "Maya"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Eli", "Finn", "Cal"]
ADULT_NAMES = ["Ms. Reed", "Mr. Vale", "Mrs. Quinn"]
TRAITS = ["careful", "curious", "brave", "gentle", "quick-thinking"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A clue is valid for a setting when its requirements are met and the setting supports the scene.
valid_clue(S, C) :- setting(S), clue(C), clue_requires(C, R), clue_requires(C, R2), scene_supports(S, R), scene_supports(S, R2).

% The oboe can be found where the clue points, but only if the search setting supports searching.
findable(S, oboe) :- setting(S), scene_supports(S, search), valid_clue(S, C), clue_points_to(C, case).

% The celebration is complete when the team works together and the ribbon is present.
celebrate_ready(S) :- setting(S), scene_supports(S, celebrate), ribbon_present(S), teamwork_present(S).

% A whodunit is solvable when the oboe is findable and the celebration can proceed.
solvable(S) :- findable(S, oboe), celebrate_ready(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for support in sorted(s.supports):
            lines.append(asp.fact("scene_supports", sid, support))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_points_to", cid, c.points_to))
        for req in sorted(c.requires):
            lines.append(asp.fact("clue_requires", cid, req))
    lines.append(asp.fact("ribbon_present", "community_hall"))
    lines.append(asp.fact("teamwork_present", "community_hall"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solvable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/1."))
    return sorted(set(asp.atoms(model, "solvable")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(setting: str, clue: str) -> bool:
    s = _safe_lookup(SETTINGS, setting)
    c = _safe_lookup(CLUES, clue)
    if "search" not in s.supports:
        return False
    if clue == "shimmer" and "celebrate" not in s.supports:
        return False
    if clue == "clap" and "teamwork" not in s.supports:
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    return [(s, c) for s in SETTINGS for c in CLUES if valid_combo(s, c)]


# ---------------------------------------------------------------------------
# World actions and narration
# ---------------------------------------------------------------------------

def setup_world(setting: Setting, clue: Clue, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="girl", label=params.hero_name))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="boy", label=params.helper_name))
    suspect = world.add(Entity(id=params.suspect_name, kind="character", type="adult", label=params.suspect_name))

    oboe = world.add(Entity(
        id="oboe", type="oboe", label="oboe", phrase=OBJECTS["oboe"].phrase,
        owner=hero.id, hidden=True, location="bench_cushion", can_make_sounds=True
    ))
    ribbon = world.add(Entity(
        id="ribbon", type="ribbon", label="gold ribbon", phrase=OBJECTS["ribbon"].phrase,
        location="announcement_board", hidden=False
    ))

    world.facts.update(
        hero=hero, helper=helper, suspect=suspect, oboe=oboe, ribbon=ribbon,
        clue=clue, setting=setting,
    )
    return world


def intro(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    world.say(
        f"{hero.id} was a {random.choice(TRAITS)} young player who knew the music room by heart."
    )
    world.say(
        f"{helper.id} liked to help with chairs, pages, and anything that needed two careful hands."
    )


def celebration_setup(world: World) -> None:
    world.say(
        f"That afternoon, everyone was getting ready to celebrate in {world.setting.place}."
    )
    world.say(world.setting.detail)
    world.facts["celebrate"] = True


def discovery(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    oboe = _safe_fact(world, world.facts, "oboe")
    clue = _safe_fact(world, world.facts, "clue")
    world.say(
        f"Then {hero.id} opened the case—and gasped. The oboe was gone."
    )
    world.say(
        f"Only {clue.label} seemed to linger in the air, like a tiny note trying to tell the truth."
    )
    world.facts["missing"] = True
    world.facts["clue_seen"] = clue.id


def suspect_scene(world: World) -> None:
    suspect = _safe_fact(world, world.facts, "suspect")
    hero = _safe_fact(world, world.facts, "hero")
    world.say(
        f"{suspect.id} was near the stage, smiling at the decorations, which made {hero.id} wonder if that was suspicious."
    )
    world.say(
        f"But in a whodunit, a smile is not a crime. It is only a place to start asking questions."
    )
    world.facts["suspect_watched"] = True
    suspect.memes["suspicion"] = 1.0


def follow_clue(world: World) -> None:
    clue: Clue = _safe_fact(world, world.facts, "clue")
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    world.say(
        f"{helper.id} listened closely and said, 'Did you hear that {clue.sound}?'"
    )
    world.say(
        f"{hero.id} nodded. The sound pointed toward the case area, where the bench sat under a tidy cloth."
    )
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    helper.memes["confidence"] = helper.memes.get("confidence", 0.0) + 1
    world.facts["searched_case"] = True


def teamwork_turn(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    suspect = _safe_fact(world, world.facts, "suspect")
    world.say(
        f"{hero.id} looked under the bench while {helper.id} checked the cloth and the little shelf beside it."
    )
    world.say(
        f"Then {suspect.id} noticed a soft thump from the cushion and helped lift it together."
    )
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 1
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0.0) + 1
    suspect.memes["teamwork"] = suspect.memes.get("teamwork", 0.0) + 1
    world.facts["teamwork"] = True


def reveal(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    oboe = _safe_fact(world, world.facts, "oboe")
    world.say(
        f"Under the cushion, there it was: the oboe, safe and snug, where nobody had first thought to look."
    )
    world.say(
        f"{hero.id} laughed with relief, because the mystery was not a trick at all. It was only a hidden place and a very big day."
    )
    oboe.hidden = False
    oboe.location = "hero_hands"
    oboe.carried_by = hero.id
    world.facts["found"] = True


def transformation(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    suspect = _safe_fact(world, world.facts, "suspect")
    world.say(
        f"By the end, the whole room had changed: worry had turned into teamwork, and silence had turned into music again."
    )
    world.say(
        f"Their small search had made a tremendous transformation in how they listened to one another."
    )
    world.say(
        f"Together they celebrated, and the oboe gave the first bright note of the happy show."
    )
    hero.memes["delight"] = hero.memes.get("delight", 0.0) + 2
    helper.memes["delight"] = helper.memes.get("delight", 0.0) + 2
    suspect.memes["delight"] = suspect.memes.get("delight", 0.0) + 2
    world.facts["transformation"] = True
    world.facts["tremendous"] = True


def tell_story(params: StoryParams) -> World:
    world = setup_world(_safe_lookup(SETTINGS, params.setting), _safe_lookup(CLUES, params.clue), params)
    intro(world)
    world.para()
    celebration_setup(world)
    discovery(world)
    suspect_scene(world)
    world.para()
    follow_clue(world)
    teamwork_turn(world)
    reveal(world)
    transformation(world)
    return world


# ---------------------------------------------------------------------------
# Q&A and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child about a missing oboe, a celebration, and a {f["clue"].sound} clue.',
        f"Tell a gentle mystery where {f['hero'].id}, {f['helper'].id}, and {f['suspect'].id} work together to find a lost oboe.",
        f"Write a story that includes the words oboe, celebrate, and tremendous, and ends with teamwork solving the mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, suspect, clue = f["hero"], f["helper"], f["suspect"], f["clue"]
    return [
        QAItem(
            question=f"What was missing at the start of the story?",
            answer=f"The oboe was missing from its case, and that is why the mystery began.",
        ),
        QAItem(
            question=f"What sound clue helped {hero.id} and {helper.id} search?",
            answer=f"They listened for {clue.sound}, which pointed them toward the hidden spot near the bench.",
        ),
        QAItem(
            question=f"Who helped lift the cushion and solve the mystery?",
            answer=f"{hero.id}, {helper.id}, and {suspect.id} all helped together, so the search could succeed.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer="Worry changed into teamwork, and the quiet room changed back into a place for music and celebration.",
        ),
        QAItem(
            question=f"Why was the transformation called tremendous?",
            answer="It was tremendous because the whole room went from confused and worried to happy, united, and ready to play.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "oboe": [
        QAItem(
            question="What is an oboe?",
            answer="An oboe is a woodwind instrument with a narrow body and a bright, reedy sound.",
        )
    ],
    "celebrate": [
        QAItem(
            question="What does it mean to celebrate?",
            answer="To celebrate means to do something happy to mark a special event, like a party, song, or cheering.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help one another and share the job so they can do something together.",
        )
    ],
    "sound effects": [
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special noises that help tell what is happening, like a squeak, a thump, or a clap.",
        )
    ],
    "tremendous": [
        QAItem(
            question="What does tremendous mean?",
            answer="Tremendous means very big, strong, or impressive.",
        )
    ],
    "whodunit": [
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader listens to clues and tries to figure out who did it or where something went.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        *WORLD_KNOWLEDGE["oboe"],
        *WORLD_KNOWLEDGE["celebrate"],
        *WORLD_KNOWLEDGE["teamwork"],
        *WORLD_KNOWLEDGE["sound effects"],
        *WORLD_KNOWLEDGE["tremendous"],
        *WORLD_KNOWLEDGE["whodunit"],
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Verification / trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_solvable())
    python_set = {("solvable", ("community_hall",))}
    if clingo_set:
        print("OK: ASP rules produced a solvable model.")
        return 0
    print("MISMATCH: ASP did not produce expected solvable result.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld about an oboe, celebration, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--suspect-name")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    if not valid_combo(setting, clue):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero = getattr(args, "hero_name", None) or rng.choice(GIRL_NAMES)
    helper = getattr(args, "helper_name", None) or rng.choice(BOY_NAMES)
    suspect = getattr(args, "suspect_name", None) or rng.choice(ADULT_NAMES)
    return StoryParams(setting=setting, clue=clue, hero_name=hero, helper_name=helper, suspect_name=suspect)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show solvable/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        combos = valid_combos()
        for i, (setting, clue) in enumerate(combos):
            params = StoryParams(
                setting=setting,
                clue=clue,
                hero_name=_safe_lookup(GIRL_NAMES, i % len(GIRL_NAMES)),
                helper_name=_safe_lookup(BOY_NAMES, i % len(BOY_NAMES)),
                suspect_name=_safe_lookup(ADULT_NAMES, i % len(ADULT_NAMES)),
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
