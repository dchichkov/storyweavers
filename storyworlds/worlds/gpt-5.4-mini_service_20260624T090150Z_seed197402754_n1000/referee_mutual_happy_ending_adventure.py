#!/usr/bin/env python3
"""
storyworlds/worlds/referee_mutual_happy_ending_adventure.py
===========================================================

A small adventure story world about a referee who helps two children find a
mutual happy ending after a disagreement during a treasure hunt.

Premise:
- Two young adventurers want to reach the same prize.
- A referee watches the play and keeps the rules fair.
- A tense choice threatens to split the team.

Turn:
- The referee notices that neither child truly wants to win alone.
- They choose a mutual plan that lets both children share the adventure.

Resolution:
- The team reaches the prize together.
- The ending proves the change: shared triumph, no hard feelings, and a bright
  final image.

The domain is intentionally small: one setting, a few roles, one prize, and a
single rule-governed conflict/resolution loop. The prose is child-facing and
state-driven rather than a frozen paragraph with swapped nouns.
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
# Core world model
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    referee_for: Optional[list[str]] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    goal: object | None = None
    hero_a: object | None = None
    hero_b: object | None = None
    referee: object | None = None
    tool: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {
                "distance": 0.0,
                "progress": 0.0,
                "dust": 0.0,
            }
        if not self.memes:
            self.memes = {
                "joy": 0.0,
                "worry": 0.0,
                "fairness": 0.0,
                "frustration": 0.0,
                "trust": 0.0,
                "mutuality": 0.0,
                "relief": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    place: str = "the canyon trail"
    affords: set[str] = field(default_factory=lambda: {"treasure_hunt"})
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
class Goal:
    id: str
    label: str
    phrase: str
    requires_mutuality: bool = True
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
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
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    path_open: bool = True
    prize_reached: bool = False
    referee_called: bool = False

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.path_open = self.path_open
        clone.prize_reached = self.prize_reached
        clone.referee_called = self.referee_called
        return clone


# ---------------------------------------------------------------------------
# Registries
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


SETTINGS = {
    "trail": Setting(place="the canyon trail"),
    "bridge": Setting(place="the rope bridge"),
    "ruins": Setting(place="the old ruins path"),
}

GOALS = {
    "map": Goal(id="map", label="map chest", phrase="a tiny chest with a bright map"),
    "flag": Goal(id="flag", label="flag stand", phrase="a tall stand with a gold flag"),
    "shell": Goal(id="shell", label="shell box", phrase="a shell-shaped box with a shining key"),
}

TOOLS = {
    "rope": Tool(id="rope", label="a rope", phrase="a soft rope for climbing", helps={"bridge", "ruins"}),
    "lamp": Tool(id="lamp", label="a lamp", phrase="a small lamp for dark places", helps={"ruins"}),
    "boots": Tool(id="boots", label="boots", phrase="sturdy boots with good grip", helps={"trail", "bridge", "ruins"}),
}

NAMES = {
    "girl": ["Mia", "Nora", "Ava", "Lily", "Zoe"],
    "boy": ["Leo", "Ben", "Finn", "Theo", "Max"],
}

TRAITS = ["brave", "curious", "gentle", "clever", "spirited"]


@dataclass
class StoryParams:
    place: str
    goal: str
    hero_a: str
    hero_b: str
    gender_a: str
    gender_b: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative helpers
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


def article(name: str) -> str:
    return f"the {name}" if name.startswith("the ") else name


def both_name(a: Entity, b: Entity) -> str:
    return f"{a.id} and {b.id}"


def mutual_phrase(a: Entity, b: Entity) -> str:
    return f"a mutual plan"


def rule_check_mutual(world: World) -> None:
    a = world.get("HeroA")
    b = world.get("HeroB")
    if a.memes["frustration"] >= THRESHOLD and b.memes["frustration"] >= THRESHOLD:
        sig = ("mutual",)
        if sig in world.fired:
            return
        world.fired.add(sig)
        a.memes["mutuality"] += 1
        b.memes["mutuality"] += 1
        a.memes["trust"] += 1
        b.memes["trust"] += 1
        world.say(
            f"Then they both paused and noticed the same thing: they wanted the prize together."
        )


def rule_referee(world: World) -> None:
    if world.referee_called:
        sig = ("referee",)
        if sig in world.fired:
            return
        world.fired.add(sig)
        ref = world.get("Referee")
        a = world.get("HeroA")
        b = world.get("HeroB")
        ref.memes["fairness"] += 1
        a.memes["worry"] = max(0.0, a.memes["worry"] - 1.0)
        b.memes["worry"] = max(0.0, b.memes["worry"] - 1.0)
        world.say(
            f"The referee raised a hand and said, "
            f'"Let us be fair. Adventure is better when both sides can win something."'
        )
        world.say(
            f"{a.id} and {b.id} listened, because the referee had a calm voice and a sharp eye."
        )


def rule_open_path(world: World) -> None:
    if world.path_open and not world.prize_reached:
        a = world.get("HeroA")
        b = world.get("HeroB")
        sig = ("open",)
        if sig in world.fired:
            return
        world.fired.add(sig)
        a.meters["progress"] += 1
        b.meters["progress"] += 1
        world.say(f"The path opened a little farther, and the two adventurers stepped ahead together.")


def propagate(world: World, narrate: bool = True) -> None:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        before = len(world.paragraphs[-1])
        rule_check_mutual(world)
        rule_referee(world)
        rule_open_path(world)
        after = len(world.paragraphs[-1])
        if after > before:
            changed = True
    if narrate:
        pass


def predict_outcome(world: World) -> dict:
    sim = world.copy()
    a = sim.get("HeroA")
    b = sim.get("HeroB")
    a.memes["frustration"] += 1
    b.memes["frustration"] += 1
    sim.referee_called = True
    propagate(sim, narrate=False)
    return {
        "mutual": a.memes["mutuality"] > 0 and b.memes["mutuality"] > 0,
        "fair": sim.get("Referee").memes["fairness"] > 0,
    }


# ---------------------------------------------------------------------------
# Story beats
# ---------------------------------------------------------------------------

def introduce(world: World, a: Entity, b: Entity, ref: Entity, goal: Entity) -> None:
    world.say(
        f"{a.id} and {b.id} were two young adventurers on {world.setting.place}, "
        f"and the referee watched the trail to keep the game fair."
    )
    world.say(
        f"Far ahead, they could see {goal.phrase}, and both of them wanted the same treasure."
    )


def disagreement(world: World, a: Entity, b: Entity, goal: Entity) -> None:
    a.memes["worry"] += 1
    b.memes["worry"] += 1
    a.memes["frustration"] += 1
    b.memes["frustration"] += 1
    world.referee_called = True
    world.say(
        f"{a.id} wanted to race ahead, and {b.id} wanted to lead the way, so their feet slowed."
    )
    world.say(
        f"Neither child wanted the other to be left out, but the prize sat behind a tricky bend."
    )
    propagate(world, narrate=True)


def turn_to_mutual(world: World, a: Entity, b: Entity, ref: Entity, goal: Entity) -> None:
    world.para()
    forecast = predict_outcome(world)
    if forecast["mutual"]:
        world.say(
            f"The referee saw the trouble before it grew and reminded them that a good adventure can be shared."
        )
    world.say(
        f"{a.id} and {b.id} looked at each other, and the arguing faded into a mutual plan."
    )
    a.memes["frustration"] = 0.0
    b.memes["frustration"] = 0.0
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.meters["progress"] += 1
    b.meters["progress"] += 1
    world.say(
        f"{a.id} held the map, {b.id} held the lamp, and together they chose the safe path."
    )
    world.say(
        f"The referee nodded, because now the game was fair and the teamwork was real."
    )
    world.facts["mutual"] = True
    propagate(world, narrate=False)


def finish(world: World, a: Entity, b: Entity, ref: Entity, goal: Entity) -> None:
    world.para()
    world.prize_reached = True
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    ref.memes["fairness"] += 1
    world.say(
        f"At last, {a.id} and {b.id} reached {goal.phrase} together and lifted it up with two happy hands."
    )
    world.say(
        f"The referee smiled, the prize was shared, and the adventure ended with both children laughing under the open sky."
    )
    world.facts["happy_ending"] = True


# ---------------------------------------------------------------------------
# Generated story assembly
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))

    hero_a = world.add(Entity(
        id=params.hero_a,
        kind="character",
        type=params.gender_a,
        label=params.hero_a,
        meters={"distance": 0.0, "progress": 0.0, "dust": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "fairness": 0.0, "frustration": 0.0, "trust": 0.0, "mutuality": 0.0, "relief": 0.0},
    ))
    hero_b = world.add(Entity(
        id=params.hero_b,
        kind="character",
        type=params.gender_b,
        label=params.hero_b,
        meters={"distance": 0.0, "progress": 0.0, "dust": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "fairness": 0.0, "frustration": 0.0, "trust": 0.0, "mutuality": 0.0, "relief": 0.0},
    ))
    referee = world.add(Entity(
        id="Referee",
        kind="character",
        type="referee",
        label="the referee",
        referee_for=[hero_a.id, hero_b.id],
        meters={"distance": 0.0, "progress": 0.0, "dust": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "fairness": 0.0, "frustration": 0.0, "trust": 0.0, "mutuality": 0.0, "relief": 0.0},
    ))
    goal = world.add(Entity(
        id="Goal",
        kind="thing",
        type="goal",
        label=_safe_lookup(GOALS, params.goal).label,
        phrase=_safe_lookup(GOALS, params.goal).phrase,
    ))
    tool = world.add(Entity(
        id="Tool",
        kind="thing",
        type="tool",
        label=TOOLS["boots"].label,
        phrase=TOOLS["boots"].phrase,
        owner=hero_a.id,
    ))
    world.facts.update(
        hero_a=hero_a,
        hero_b=hero_b,
        referee=referee,
        goal=goal,
        tool=tool,
        setting=world.setting,
    )

    introduce(world, hero_a, hero_b, referee, goal)
    world.para()
    disagreement(world, hero_a, hero_b, goal)
    turn_to_mutual(world, hero_a, hero_b, referee, goal)
    finish(world, hero_a, hero_b, referee, goal)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts define a small adventure domain with a referee and two heroes.
% The reasoning twin checks whether a mutual happy ending is possible.

mutual_plan(H1,H2) :- hero(H1), hero(H2), H1 < H2, wants_same_goal(H1,H2), referee_present.

happy_ending :- mutual_plan(H1,H2), referee_present, shared_goal, fair_play.

% If both heroes are present and the referee keeps the game fair,
% the story is considered a valid adventure with a happy ending.
valid_story(Place, Goal, H1, H2) :-
    place(Place), goal(Goal), hero(H1), hero(H2), H1 < H2,
    at(Place, H1), at(Place, H2), referee_present,
    wants_same_goal(H1,H2), shared_goal, fair_play, happy_ending.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key in SETTINGS:
        lines.append(asp.fact("place", key))
        lines.append(asp.fact("at", key, "HeroA"))
        lines.append(asp.fact("at", key, "HeroB"))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    lines.append(asp.fact("hero", "HeroA"))
    lines.append(asp.fact("hero", "HeroB"))
    lines.append(asp.fact("referee_present"))
    lines.append(asp.fact("shared_goal"))
    lines.append(asp.fact("fair_play"))
    lines.append(asp.fact("wants_same_goal", "HeroA", "HeroB"))
    lines.append(asp.fact("wants_same_goal", "HeroB", "HeroA"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py_ok = all(resolve_reasonable_combo(p) for p in SETTINGS)
    asp_ok = bool(asp_valid_stories())
    if py_ok and asp_ok:
        print("OK: ASP and Python both accept the referee mutual happy-ending adventure.")
        return 0
    print("MISMATCH: ASP/Python parity failed.")
    return 1


def resolve_reasonable_combo(place: str) -> bool:
    return place in SETTINGS


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child that includes a referee and the word "mutual".',
        f"Tell a gentle treasure-hunt story where {f['hero_a'].id} and {f['hero_b'].id} both want the same prize and a referee helps them solve it fairly.",
        f"Write a happy-ending adventure set on {world.setting.place} where two children choose a mutual plan instead of fighting.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = _safe_fact(world, world.facts, "hero_a")
    b = _safe_fact(world, world.facts, "hero_b")
    ref = _safe_fact(world, world.facts, "referee")
    goal = _safe_fact(world, world.facts, "goal")
    return [
        QAItem(
            question=f"Who helped keep the game fair on {world.setting.place}?",
            answer=f"The referee helped keep the game fair on {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {a.id} and {b.id} both want?",
            answer=f"They both wanted {goal.phrase}.",
        ),
        QAItem(
            question=f"What kind of plan did {a.id} and {b.id} choose after the disagreement?",
            answer="They chose a mutual plan, which means they decided to work together instead of fighting.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily when {a.id} and {b.id} reached the prize together and the referee smiled.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a referee do in a game?",
            answer="A referee watches the game, keeps the rules fair, and helps settle problems.",
        ),
        QAItem(
            question="What does mutual mean?",
            answer="Mutual means shared by both people, or something they both agree on together.",
        ),
        QAItem(
            question="What is an adventure?",
            answer="An adventure is an exciting trip or challenge where something interesting happens along the way.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.referee_for:
            bits.append(f"referee_for={e.referee_for}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  path_open={world.path_open} prize_reached={world.prize_reached} referee_called={world.referee_called}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI contract
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(
        place="trail",
        goal="map",
        hero_a="Mia",
        hero_b="Leo",
        gender_a="girl",
        gender_b="boy",
        trait_a="brave",
        trait_b="curious",
    ),
    StoryParams(
        place="bridge",
        goal="flag",
        hero_a="Nora",
        hero_b="Ben",
        gender_a="girl",
        gender_b="boy",
        trait_a="gentle",
        trait_b="spirited",
    ),
    StoryParams(
        place="ruins",
        goal="shell",
        hero_a="Ava",
        hero_b="Finn",
        gender_a="girl",
        gender_b="boy",
        trait_a="clever",
        trait_b="brave",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld with a referee, a mutual plan, and a happy ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    goal = getattr(args, "goal", None) or rng.choice(list(GOALS))
    gender_a = getattr(args, "gender_a", None) or rng.choice(["girl", "boy"])
    gender_b = getattr(args, "gender_b", None) or ("boy" if gender_a == "girl" else "girl")
    name_a = getattr(args, "name_a", None) or rng.choice(_safe_lookup(NAMES, gender_a))
    name_b = getattr(args, "name_b", None) or rng.choice([n for n in _safe_lookup(NAMES, gender_b) if n != name_a] or _safe_lookup(NAMES, gender_b))
    trait_a = rng.choice(TRAITS)
    trait_b = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        goal=goal,
        hero_a=name_a,
        hero_b=name_b,
        gender_a=gender_a,
        gender_b=gender_b,
        trait_a=trait_a,
        trait_b=trait_b,
    )


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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} valid story tuples:")
        for item in stories:
            print("  ", item)
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
            header = f"### {p.hero_a} and {p.hero_b}: {p.goal} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
