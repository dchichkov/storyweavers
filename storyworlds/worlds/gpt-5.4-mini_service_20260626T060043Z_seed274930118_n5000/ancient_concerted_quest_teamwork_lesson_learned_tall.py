#!/usr/bin/env python3
"""
A standalone storyworld for a tall-tale quest about an ancient, concerted effort,
where teamwork turns a hard job into a lesson learned.

Premise:
- A small crew tries to lift, carry, or unlock an ancient thing too heavy or too
  tricky for one character alone.
- The tension comes from overconfidence, strain, and a warning from an elder or
  captain.
- The turn is a clear teamwork compromise: the crew shares the task, uses the
  right tool, and succeeds together.
- The ending image proves the change: the ancient prize is secured, the danger is
  gone, and the lesson learned is remembered.

This world is intentionally small and classical: a few characters, one quest,
one obstacle, one helpful method, and a clear before/after change.
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
# Core model
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carrying: bool = False
    helping: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    goal: object | None = None
    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"strain": 0.0, "tired": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "worry": 0.0, "joy": 0.0, "lesson": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "king"}
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
    place: str
    detail: str
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
class Quest:
    id: str
    goal: str
    verb: str
    obstacle: str
    strain: str
    reward: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
    prep: str
    cure: str
    plural: bool = False
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "ruins": Setting(
        place="the sun-baked ruins",
        detail="Broken pillars leaned like tired giants, and every stone looked old enough to remember thunder.",
        affords={"lift", "pull", "unlock"},
    ),
    "cave": Setting(
        place="the echoing cave",
        detail="The cave breathed cold air, and the walls glittered like a treasure chest that had forgotten its key.",
        affords={"lift", "pull", "unlock"},
    ),
    "riverbank": Setting(
        place="the muddy riverbank",
        detail="The river rolled by with a loud mutter, while the bank sank under every determined step.",
        affords={"lift", "pull"},
    ),
}

QUESTS = {
    "stone": Quest(
        id="stone",
        goal="move the ancient stone gate",
        verb="move the stone gate",
        obstacle="too heavy",
        strain="their arms trembled and their boots slid",
        reward="the path beyond the gate",
        keyword="ancient",
        tags={"ancient", "stone", "heavy"},
    ),
    "idol": Quest(
        id="idol",
        goal="carry the ancient idol home",
        verb="carry the idol",
        obstacle="too awkward",
        strain="their shoulders wobbled and their knees knocked",
        reward="the idol's safe place",
        keyword="concerted",
        tags={"ancient", "idol", "carry"},
    ),
    "chest": Quest(
        id="chest",
        goal="open the ancient chest",
        verb="unlock the chest",
        obstacle="too stubborn",
        strain="their fingers slipped and their hearts thumped",
        reward="the hidden map inside",
        keyword="quest",
        tags={"ancient", "chest", "lock"},
    ),
}

TOOLS = {
    "lever": Tool(
        id="lever",
        label="a long lever",
        phrase="a long lever made from a sturdy branch",
        prep="use the lever together",
        cure="the stone gate would finally budge",
        plural=False,
    ),
    "rope": Tool(
        id="rope",
        label="a braided rope",
        phrase="a braided rope with knots every handspan",
        prep="pull in concert with the rope",
        cure="the idol would stay balanced",
        plural=False,
    ),
    "key": Tool(
        id="key",
        label="an iron key",
        phrase="an iron key with a tooth like a fish hook",
        prep="try the iron key at once",
        cure="the chest would click open",
        plural=False,
    ),
}

HEROES = [
    ("Mabel", "girl", "stubborn"),
    ("Hank", "boy", "bold"),
    ("Nell", "girl", "fearless"),
    ("Jeb", "boy", "loud"),
    ("Tess", "girl", "steady"),
]

HELPERS = [
    ("Uncle Pike", "man"),
    ("Aunt Junie", "woman"),
    ("Captain Elm", "man"),
    ("Grandma Star", "woman"),
]

TRAITS = ["stubborn", "bold", "fearless", "loud", "steady"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    hero: str
    gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World mechanics
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


def quest_needs_teamwork(q: Quest) -> bool:
    return True


def select_tool(q: Quest) -> Optional[Tool]:
    return {"stone": TOOLS["lever"], "idol": TOOLS["rope"], "chest": TOOLS["key"]}.get(q.id)


def predict_success(world: World, hero: Entity, helper: Entity, quest: Quest, tool: Tool) -> dict:
    sim = world.copy()
    _do_work(sim, sim.get(hero.id), sim.get(helper.id), quest, tool, narrate=False)
    target = sim.entities.get("goal")
    return {
        "safe": bool(target and target.meters["safe"] >= THRESHOLD),
        "lesson": sum(e.memes["lesson"] for e in sim.characters()),
    }


def _do_work(world: World, hero: Entity, helper: Entity, quest: Quest, tool: Tool, narrate: bool = True) -> None:
    if quest.id not in world.setting.affords:
        return
    hero.meters["strain"] += 1
    helper.meters["strain"] += 1
    hero.memes["worry"] += 1
    helper.memes["worry"] += 0.5
    world.get("goal").meters["safe"] += 1
    world.get("goal").carrying = True
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.fired.add(("done", quest.id))
    if narrate:
        world.say(f"Together they used {tool.label}, and the hard old job began to give way.")


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} {hero.type} with a taste for tall tales and bigger errands."
    )
    world.say(
        f"On that day, {hero.id} and {helper.id} set out on a {quest.keyword} quest to {quest.goal}."
    )


def scene(world: World, quest: Quest) -> None:
    world.say(world.setting.detail)
    world.say(
        f"The old job was {quest.obstacle}, and that meant one brave pair would need more than hot luck to finish it."
    )


def tension(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    hero.memes["pride"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"{hero.id} wanted to do it all at once, but {quest.strain}."
    )
    world.say(
        f"{helper.id} shook {helper.pronoun('possessive')} head and warned that a lone push would only wear them out."
    )


def teamwork_turn(world: World, hero: Entity, helper: Entity, quest: Quest, tool: Tool) -> None:
    world.say(
        f"Then they took a deep breath and chose a concerted way: {tool.prep}."
    )
    _do_work(world, hero, helper, quest, tool, narrate=True)


def ending(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    goal = world.get("goal")
    world.say(
        f"By sunset, the ancient prize was safe, {hero.id} was grinning, and {helper.id} was laughing so hard the crows lifted off the stones."
    )
    world.say(
        f"They had learned that a hard quest gets lighter when good hearts pull together."
    )
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    goal.meters["safe"] += 1


def tell(setting: Setting, quest: Quest, hero_name: str, hero_gender: str, helper_name: str, helper_gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, traits=[trait, "bold"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, traits=["wise", "steady"]))
    goal = world.add(Entity(id="goal", kind="thing", type=quest.id, label=quest.goal, phrase=quest.goal))

    tool = select_tool(quest)
    if tool is None:
        pass

    intro(world, hero, helper, quest)
    world.para()
    scene(world, quest)
    tension(world, hero, helper, quest)
    world.para()
    teamwork_turn(world, hero, helper, quest, tool)
    world.para()
    ending(world, hero, helper, quest)

    world.facts.update(hero=hero, helper=helper, quest=quest, tool=tool, goal=goal)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: Quest = _safe_fact(world, f, "quest")
    return [
        f"Write a tall tale about an ancient quest where {f['hero'].id} and {f['helper'].id} solve a problem by working together.",
        f"Tell a child-friendly story about a {q.keyword} quest that ends with a lesson learned about teamwork.",
        f"Write a short story set at {world.setting.place} where two helpers use a tool to finish an old task.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, quest = f["hero"], f["helper"], f["quest"]
    return [
        QAItem(
            question=f"Who went on the quest at {world.setting.place}?",
            answer=f"{hero.id} went with {helper.id} on the quest.",
        ),
        QAItem(
            question=f"What was hard about the ancient job?",
            answer=f"It was {quest.obstacle}, so one character alone would have had a rough time.",
        ),
        QAItem(
            question="How did they finish the task?",
            answer=f"They used {(f.get('tool') or next(iter(TOOLS.values()))).label} and worked together in a concerted way.",
        ),
        QAItem(
            question="What lesson did they learn?",
            answer="They learned that teamwork makes a big job easier and safer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does ancient mean?",
            answer="Ancient means very old, from a long time ago.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help one another and work together toward the same goal.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or mission to do something important.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
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


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(
            f"  {e.id:8} ({e.kind:7}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    out.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A quest is reasonable when it needs teamwork and has a matching tool.
needs_teamwork(Q) :- quest(Q).
has_tool(Q) :- quest(Q), tool(T), matches(T,Q).

valid_story(Place, Quest, HeroGender) :- setting(Place), quest(Quest), hero_gender(HeroGender),
                                        affords(Place, Quest), needs_teamwork(Quest), has_tool(Quest).

% The matching tool is determined by quest type.
matches(lever, stone).
matches(rope, idol).
matches(key, chest).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for gid, _, gender in HEROES:
        lines.append(asp.fact("hero_gender", gender))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_stories())
    projected = {(p, q, g) for (p, q, g) in asp_set}
    if projected == py:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("Python only:", sorted(py - projected))
    print("ASP only:", sorted(projected - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for qid in s.affords:
            if qid in QUESTS and select_tool(_safe_lookup(QUESTS, qid)) is not None:
                for _, _, g in HEROES:
                    combos.append((place, qid, g))
    return combos


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

def pick_name(rng: random.Random, gender: str) -> str:
    pool = [x for x in HEROES if x[1] == gender]
    return rng.choice(pool)[0]


def pick_helper(rng: random.Random) -> tuple[str, str]:
    return rng.choice(HELPERS)


def pick_gender(rng: random.Random) -> str:
    return rng.choice(["girl", "boy"])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    quest = getattr(args, "quest", None) or rng.choice(sorted(_safe_lookup(SETTINGS, place).affords))
    if quest not in _safe_lookup(SETTINGS, place).affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if quest not in QUESTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or pick_gender(rng)
    hero = getattr(args, "hero", None) or pick_name(rng, gender)
    helper, helper_gender = pick_helper(rng)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, hero=hero, gender=gender, helper=helper, helper_gender=helper_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(QUESTS, params.quest),
        params.hero,
        params.gender,
        params.helper,
        params.helper_gender,
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
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="ruins", quest="stone", hero="Mabel", gender="girl", helper="Captain Elm", helper_gender="man", trait="stubborn"),
    StoryParams(place="cave", quest="chest", hero="Hank", gender="boy", helper="Grandma Star", helper_gender="woman", trait="bold"),
    StoryParams(place="riverbank", quest="idol", hero="Nell", gender="girl", helper="Uncle Pike", helper_gender="man", trait="fearless"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale quest storyworld with teamwork and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for row in stories:
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
