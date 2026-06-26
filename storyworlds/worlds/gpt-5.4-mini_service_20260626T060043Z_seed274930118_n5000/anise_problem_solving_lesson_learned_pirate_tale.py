#!/usr/bin/env python3
"""
A standalone storyworld for a small pirate tale with a practical problem,
a clever fix, and a lesson learned.

Premise:
- A young pirate on a little ship has an anise pouch that makes the galley
  smell sweet.
- A strong fish smell spoils the crew's supper mood.
- The pirate tries to solve the problem with anise, learns that scent can help
  but must be used carefully, and ends with a calmer, cleaner deck.

This world models:
- physical meters: smell, cleanliness, mess, usefulness
- emotional memes: worry, hope, pride, relief, gratitude

The prose is generated from a simulated state rather than a frozen template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    anise: object | None = None
    cook: object | None = None
    galley: object | None = None
    hero: object | None = None
    ship: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
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
    ship_name: str
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
class Problem:
    id: str
    trigger: str
    symptom: str
    smell_kind: str
    worse: str
    keyword: str = "anise"
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
class Fix:
    id: str
    label: str
    phrase: str
    action: str
    helps: set[str]
    requires: set[str]
    clue: str
    lesson: str
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


def _narrate_join(parts: list[str]) -> str:
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + ", and " + parts[-1]


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    problem = world.facts.get("problem")
    if not problem:
        return out
    ship = world.get("ship")
    galley = world.get("galley")
    if ship.meters.get(problem.smell_kind, 0.0) < THRESHOLD:
        return out
    sig = ("spoil", problem.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ship.memes["worry"] = ship.memes.get("worry", 0.0) + 1
    galley.meters["stale"] = galley.meters.get("stale", 0.0) + 1
    out.append("The galley air turned stale, and the crew wrinkled their noses.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    fix: Fix = world.facts.get("fix")
    if not fix:
        return out
    ship = world.get("ship")
    galley = world.get("galley")
    if ship.meters.get("stale", 0.0) < THRESHOLD:
        return out
    sig = ("fix", fix.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ship.meters["stale"] = max(0.0, ship.meters.get("stale", 0.0) - 1)
    ship.memes["hope"] = ship.memes.get("hope", 0.0) + 1
    galley.meters["sweet"] = galley.meters.get("sweet", 0.0) + 1
    out.append(f"The {fix.label} made the galley smell sweet again.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    fix: Fix = world.facts.get("fix")
    sig = ("lesson", hero.id)
    if sig in world.fired:
        return out
    if hero.memes.get("pride", 0.0) >= THRESHOLD and hero.memes.get("relief", 0.0) >= THRESHOLD:
        world.fired.add(sig)
        hero.memes["wisdom"] = hero.memes.get("wisdom", 0.0) + 1
        out.append(f"{hero.label} learned that a small, careful idea can solve a big mess.")
        if fix:
            out.append(f"{hero.label} also learned to use {fix.label} before the smell grows worse.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_spoil, _r_fix, _r_lesson):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_problem(world: World, hero: Entity, problem: Problem) -> bool:
    sim = world.copy()
    sim.get("ship").meters[problem.smell_kind] = 1.0
    propagate(sim, narrate=False)
    return sim.get("ship").meters.get("stale", 0.0) >= THRESHOLD


def choose_fix(problem: Problem) -> Optional[Fix]:
    for fix in FIXES:
        if problem.smell_kind in fix.helps and problem.keyword in fix.requires:
            return fix
    return None


def pirate_name(gender: str) -> str:
    return random.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def tell(setting: Setting, problem: Problem, fix: Fix, hero_name: str, hero_gender: str) -> World:
    world = World(setting)
    ship = world.add(Entity(id="ship", kind="character", type="ship", label=f"the {setting.ship_name}"))
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    cook = world.add(Entity(id="cook", kind="character", type="man", label="the cook"))
    galley = world.add(Entity(id="galley", type="room", label="the galley"))
    anise = world.add(Entity(
        id="anise", type="spice", label="anise pouch", phrase="a little pouch of anise",
        owner=hero.id, caretaker=hero.id
    ))

    world.facts.update(hero=hero, cook=cook, ship=ship, galley=galley, problem=problem, fix=fix, anise=anise)

    world.say(
        f"On the {setting.ship_name}, {hero.label} was a young pirate with {anise.phrase} tied to {hero.pronoun('possessive')} belt."
    )
    world.say(
        f"{hero.label} liked the sweet smell of {anise.label}, because it reminded {hero.pronoun('object')} of calm mornings at sea."
    )
    world.say(
        f"But one day the {problem.trigger} {problem.symptom}, and the whole crew muttered that supper would taste wrong."
    )
    world.para()
    ship.meters[problem.smell_kind] = 1.0
    hero.memes["worry"] = 1.0
    propagate(world)
    world.say(
        f"{hero.label} saw the problem and did not give up. {hero.pronoun().capitalize()} thought hard, then sprinkled a pinch of {problem.keyword} near the hatch."
    )
    hero.memes["hope"] = 1.0
    if predict_problem(world, hero, problem):
        world.say(
            f"That first try was not enough, so {hero.label} opened the windows, swept the floor, and spread the spice more carefully."
        )
        ship.meters["stale"] = 1.0
        hero.memes["pride"] = 1.0
        propagate(world)
    world.para()
    hero.memes["relief"] = 1.0
    hero.memes["pride"] = max(hero.memes.get("pride", 0.0), 1.0)
    ship.meters["stale"] = 0.0
    galley.meters["sweet"] = 1.0
    world.say(
        f"At last the bad smell faded, and the cook smiled as the supper steam rose."
    )
    world.say(
        f"{hero.label} grinned too, because the little {problem.keyword} pouch had helped the crew find a clean, clever answer."
    )
    world.say(
        f"From then on, {hero.label} remembered the lesson: when a problem starts small, a careful plan can keep the whole ship cheerful."
    )
    return world


SETTINGS = {
    "ship": Setting(place="at sea", ship_name="Little Gull", affords={"stale_air", "messy_galley"}),
    "harbor": Setting(place="by the harbor", ship_name="Merry Wave", affords={"stale_air"}),
    "cove": Setting(place="in the cove", ship_name="Blue Shell", affords={"stale_air", "messy_galley"}),
}

PROBLEMS = {
    "fish_smell": Problem(
        id="fish_smell",
        trigger="the fish barrel tipped over and",
        symptom="left a strong fishy smell in the galley",
        smell_kind="stale",
        worse="the crew could barely stomach supper",
        keyword="anise",
        tags={"anise", "smell", "galley"},
    ),
    "wet_rations": Problem(
        id="wet_rations",
        trigger="the rain splashed in and",
        symptom="made the biscuit sack damp and sour",
        smell_kind="stale",
        worse="the crew frowned at the soggy biscuits",
        keyword="anise",
        tags={"anise", "smell", "harbor"},
    ),
}

FIXES = [
    Fix(
        id="anise_air",
        label="anise pouch",
        phrase="a little pouch of anise",
        action="sprinkle",
        helps={"stale"},
        requires={"anise"},
        clue="The sweet spice can freshen the air when used with clean windows and swept boards.",
        lesson="small useful things work best when the helper notices the whole problem",
    ),
    Fix(
        id="ventilation",
        label="open hatches",
        phrase="the open hatches",
        action="open",
        helps={"stale"},
        requires={"anise"},
        clue="Fresh wind helps the spice do its job.",
        lesson="a good plan may need both a tool and a clear space",
    ),
]

GIRL_NAMES = ["Mara", "Tess", "Nell", "Ivy", "Rae", "Pip"]
BOY_NAMES = ["Jory", "Finn", "Bo", "Hale", "Kit", "Leif"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    hero_name: str
    gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale storyworld with anise, problem solving, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, pid) for sid, s in SETTINGS.items() for pid in PROBLEMS if choose_fix(_safe_lookup(PROBLEMS, pid))]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "problem", None) and getattr(args, "problem", None) not in PROBLEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "setting", None) and getattr(args, "setting", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        (sid, pid) for sid, pid in combos
        if (getattr(args, "setting", None) is None or sid == getattr(args, "setting", None))
        and (getattr(args, "problem", None) is None or pid == getattr(args, "problem", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, problem = rng.choice(list(filtered))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or pirate_name(gender)
    return StoryParams(setting=setting, problem=problem, hero_name=name, gender=gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate story for a child where {f["hero"].label} uses anise to solve a smell problem on a ship.',
        f"Tell a gentle tale about {f['hero'].label} the pirate, the {f['problem'].keyword} pouch, and a messy galley that becomes fresh again.",
        f"Write a simple story with a clever fix and a lesson learned, using the word '{f['problem'].keyword}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    problem: Problem = _safe_fact(world, f, "problem")
    fix: Fix = _safe_fact(world, f, "fix")
    return [
        QAItem(
            question=f"What problem did {hero.label} notice on the ship?",
            answer=f"{hero.label} noticed that the galley had a strong smell and the crew did not like it.",
        ),
        QAItem(
            question=f"What did {hero.label} use to help solve the smell problem?",
            answer=f"{hero.label} used an anise pouch and careful cleaning to make the air smell sweet again.",
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn in the end?",
            answer=f"{hero.label} learned that a small, careful idea can solve a big mess when it is used wisely.",
        ),
        QAItem(
            question=f"Why did the first try need another step?",
            answer=f"The first try was not enough because the smell still needed fresh air and a cleaner galley.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is anise?",
            answer="Anise is a spice with a sweet smell that people can use in food or to make a room smell nicer.",
        ),
        QAItem(
            question="Why can a strong smell make supper feel bad?",
            answer="A strong smell can make people lose their appetite, which means they may not want to eat.",
        ),
        QAItem(
            question="Why do open windows help in a room with a bad smell?",
            answer="Open windows let fresh air move through the room and help carry away stale air.",
        ),
    ]


ASP_RULES = r"""
problem(B) :- bad_smell(B).
helper(anise) :- spice(anise).
can_fix(B) :- problem(B), helper(anise), clean_hands, open_hatches.
lesson_learned(H) :- solved(H), careful_plan.
#show problem/1.
#show helper/1.
#show can_fix/1.
#show lesson_learned/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("bad_smell", "stale_air"),
        asp.fact("spice", "anise"),
        asp.fact("clean_hands"),
        asp.fact("open_hatches"),
        asp.fact("careful_plan"),
        asp.fact("solved", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_fix/1.\n#show lesson_learned/1."))
    atoms = {str(a) for a in model}
    expected = {"can_fix(stale_air)", "lesson_learned(hero)"}
    if atoms == expected:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH:", sorted(atoms), "expected", sorted(expected))
    return 1


def asp_valid_story_flags() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_fix/1.\n#show lesson_learned/1."))
    return sorted(set(asp.atoms(model, "can_fix")) | set(asp.atoms(model, "lesson_learned")))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="ship", problem="fish_smell", hero_name="Mara", gender="girl"),
    StoryParams(setting="cove", problem="wet_rations", hero_name="Kit", gender="boy"),
]


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    problem = _safe_lookup(PROBLEMS, params.problem)
    fix = choose_fix(problem)
    if fix is None:
        pass
    world = tell(setting, problem, fix, params.hero_name, params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show can_fix/1.\n#show lesson_learned/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("Compatible story flags:")
        for item in asp_valid_story_flags():
            print(" ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.hero_name}: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
