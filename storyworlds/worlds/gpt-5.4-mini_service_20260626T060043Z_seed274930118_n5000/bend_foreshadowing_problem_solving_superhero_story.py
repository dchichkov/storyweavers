#!/usr/bin/env python3
"""
storyworlds/worlds/bend_foreshadowing_problem_solving_superhero_story.py
========================================================================

A small superhero story world about a bend in a city river, where
foreshadowing hints at trouble and problem solving turns the day around.

Premise:
- A child hero, a sidekick, and a mentor patrol a city.
- The city has a bend in a river, and that bend is important.
- A looming problem is foreshadowed by clues in the setting.

Tension:
- Something threatens the bridge, street, or park near the bend.
- The hero notices clues before the trouble grows.
- A direct attack is not enough; they must think carefully.

Resolution:
- The hero uses tools, teamwork, and a clever plan.
- The problem is solved without breaking the city.
- The ending image shows the bend safe and the heroes proud.

The world uses physical meters and emotional memes, with state changes
driving the prose rather than a frozen template swap.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    mentor: object | None = None
    sidekick: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "climb": 0.0, "wind": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "fear": 0.0, "focus": 0.0, "teamwork": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
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


@dataclass
class Setting:
    place: str = "the river bend"
    detail: str = "a quiet city bend where the water turns under a bridge"
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
    label: str
    threat: str
    clue: str
    danger: str
    fix: str
    method: str
    tags: set[str] = field(default_factory=set)
    needed: set[str] = field(default_factory=set)
    place_only: Optional[str] = None
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
    helps: set[str]
    covers: set[str] = field(default_factory=set)
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue_seen")
    if clue and not world.facts.get("foreshadowed"):
        world.facts["foreshadowed"] = True
        out.append(clue)
    return out


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    prob: Problem = _safe_fact(world, world.facts, "problem")
    for hero in world.characters():
        if hero.meters["climb"] < THRESHOLD:
            continue
        if world.setting.place != prob.place_only and prob.place_only is not None:
            continue
        if hero.memes["focus"] < THRESHOLD:
            continue
        sig = ("damage", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["damage"] += 1
        hero.memes["fear"] += 1
        out.append(f"The trouble got worse near the bend.")
    return out


CAUSAL_RULES = [
    ("foreshadow", _r_foreshadow),
    ("damage", _r_damage),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_scene(world: World, hero: Entity, sidekick: Entity, mentor: Entity,
                problem: Problem, tool: Tool) -> None:
    world.say(
        f"{hero.id} was a little superhero who watched the city from the bend in the river."
    )
    world.say(
        f"{hero.id} loved helping people, and {hero.pronoun('possessive')} {sidekick.label} stayed close."
    )
    world.say(
        f"Each day, {mentor.id} pointed out clues and reminded {hero.id} to look before leaping."
    )
    world.para()
    world.say(world.setting.detail.capitalize() + ".")
    world.say(
        f"One day, {hero.id} noticed {problem.clue}."
    )
    world.say(
        f"It made {hero.pronoun('object')} think the bend was hiding {problem.danger}."
    )
    world.facts["clue_seen"] = (
        f"That little clue was a warning: something near the bend could break if nobody solved it in time."
    )
    propagate(world)
    world.para()
    world.say(
        f"{hero.id} wanted to rush in, but {mentor.id} said, "
        f"\"First we find the real problem.\""
    )
    hero.memes["fear"] += 1
    hero.memes["focus"] += 1
    sidekick.memes["hope"] += 1
    world.say(
        f"{sidekick.id} looked around and found {tool.phrase}."
    )
    world.say(
        f"Together they used it to {problem.method}."
    )
    hero.meters["climb"] += 1
    hero.memes["teamwork"] += 1
    propagate(world)
    world.para()
    hero.memes["hope"] += 2
    hero.memes["fear"] = 0
    world.say(
        f"At last, {problem.fix}."
    )
    world.say(
        f"The bend was safe again, and {hero.id} stood with {sidekick.id} and {mentor.id}, smiling at the calm water."
    )
    world.facts.update(hero=hero, sidekick=sidekick, mentor=mentor, problem=problem, tool=tool)


SETTINGS = {
    "river_bend": Setting(
        place="the river bend",
        detail="the river bend curved under a narrow bridge, where loose stones could hide trouble",
        affords={"bridge"},
    ),
    "city_park": Setting(
        place="the city park",
        detail="the city park reached all the way to the river bend, with paths, benches, and tall grass",
        affords={"bridge"},
    ),
}

PROBLEMS = {
    "flood_gate": Problem(
        id="flood_gate",
        label="a flood gate",
        threat="a jammed flood gate",
        clue="water sloshing too high against the metal gate",
        danger="a spill of water onto the bridge",
        fix="they cleared the gate and guided the water away",
        method="lift the stuck latch and nudge the gate open",
        tags={"water", "bend", "problem_solving", "foreshadowing"},
        needed={"hook"},
        place_only="the river bend",
    ),
    "fallen_tree": Problem(
        id="fallen_tree",
        label="a fallen tree",
        threat="a fallen tree across the river path",
        clue="cracked branches leaning over the bend like a warning sign",
        danger="a blocked path and a shaky bridge",
        fix="they cut the branches into safe pieces and opened the path",
        method="tie a rope and pull the branches away together",
        tags={"tree", "bend", "problem_solving", "foreshadowing"},
        needed={"rope"},
    ),
    "storm_drone": Problem(
        id="storm_drone",
        label="a storm drone",
        threat="a buzzing storm drone low over the bridge",
        clue="a blinking light hidden in the clouds above the bend",
        danger="a broken sign and scared birds",
        fix="they tricked the drone into landing and switched it off",
        method="shine a mirror so it followed the light away from the bridge",
        tags={"drone", "sky", "problem_solving", "foreshadowing"},
        needed={"mirror"},
    ),
}

TOOLS = {
    "hook": Tool(
        id="hook",
        label="a rescue hook",
        phrase="a rescue hook hanging on the wall",
        helps={"flood_gate"},
    ),
    "rope": Tool(
        id="rope",
        label="a long rope",
        phrase="a long rope coiled beside the bench",
        helps={"fallen_tree"},
    ),
    "mirror": Tool(
        id="mirror",
        label="a bright mirror",
        phrase="a bright mirror in the hero kit",
        helps={"storm_drone"},
    ),
}

HEROES = ["Nova", "Piper", "Zane", "Mila", "Aria", "Jett", "Kai", "Ruby"]
SIDEKICKS = ["Spark", "Comet", "Dash", "Orbit"]
MENTORS = ["Captain Lantern", "Professor Halo", "Aunt Vector"]


@dataclass
class StoryParams:
    place: str
    problem: str
    hero: str
    sidekick: str
    mentor: str
    seed: Optional[int] = None
    p: object | None = None
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


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for pid, prob in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if pid in tool.helps and (prob.place_only is None or prob.place_only == setting.place):
                    out.append((place, pid))
                    break
    return sorted(set(out))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world at a river bend with foreshadowing and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--mentor", choices=MENTORS)
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
    if getattr(args, "place", None) or getattr(args, "problem", None):
        combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem = rng.choice(combos)
    return StoryParams(
        place=place,
        problem=problem,
        hero=getattr(args, "hero", None) or rng.choice(HEROES),
        sidekick=getattr(args, "sidekick", None) or rng.choice(SIDEKICKS),
        mentor=getattr(args, "mentor", None) or rng.choice(MENTORS),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero, kind="character", type="hero", label="hero"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="hero", label="sidekick"))
    mentor = world.add(Entity(id=params.mentor, kind="character", type="hero", label="mentor"))
    problem = _safe_lookup(PROBLEMS, params.problem)
    tool = next(t for t in TOOLS.values() if problem.id in t.helps)
    build_scene(world, hero, sidekick, mentor, problem, tool)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "problem")
    h = _safe_fact(world, world.facts, "hero")
    return [
        f"Write a short superhero story for a child about {h.id} solving {p.label} near a river bend.",
        f"Tell a gentle foreshadowing story where a hero notices a clue at the bend and solves the problem by thinking first.",
        "Write a superhero story with a careful clue, a real problem, and a smart fix that keeps the city safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = _safe_fact(world, world.facts, "hero")
    s = _safe_fact(world, world.facts, "sidekick")
    m = _safe_fact(world, world.facts, "mentor")
    p: Problem = _safe_fact(world, world.facts, "problem")
    return [
        QAItem(
            question=f"What clue helped {h.id} notice that something was wrong near the bend?",
            answer=f"{p.clue.capitalize()}. It hinted that trouble was hiding near the river bend before the bigger problem showed up.",
        ),
        QAItem(
            question=f"How did {h.id}, {s.id}, and {m.id} solve the problem?",
            answer=f"They used teamwork and a clever tool to {p.method}. That let them fix the danger without hurting the city.",
        ),
        QAItem(
            question=f"What did the ending show after the problem was solved?",
            answer=f"The ending showed the bend calm and safe again, with {h.id} smiling beside {s.id} and {m.id}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    p: Problem = _safe_fact(world, world.facts, "problem")
    return [
        QAItem(question="What is foreshadowing?", answer="Foreshadowing is when a story gives a small clue early that hints something important will happen later."),
        QAItem(question="What is problem solving?", answer="Problem solving means figuring out a smart way to fix a problem instead of just rushing at it."),
        QAItem(question="What is a river bend?", answer="A river bend is a place where a river turns and curves instead of flowing straight."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}")
    lines.append(f"facts={sorted(world.facts)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem_place(P, Place) :- problem(P), place(Place).
tool_for(P, T) :- problem(P), tool(T), helps(T, P).
valid_story(Place, P) :- problem_place(P, Place), tool_for(P, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
        if _safe_lookup(PROBLEMS, pid).place_only:
            lines.append(asp.fact("problem_at", pid, _safe_lookup(PROBLEMS, pid).place_only))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo matches python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        print(asp_program("#show valid_story/2."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, problem in valid_combos():
            p = StoryParams(place=place, problem=problem, hero=_safe_lookup(HEROES, 0), sidekick=_safe_lookup(SIDEKICKS, 0), mentor=_safe_lookup(MENTORS, 0))
            samples.append(generate(p))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
