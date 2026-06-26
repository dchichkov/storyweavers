#!/usr/bin/env python3
"""
A small storyworld in pirate-tale style: an apartment housewife contributes to a
rhyme-making problem and gets a surprise at the end.

The seed tale imagined for this world:
---
A housewife named Mara lived in an apt above the dock. She loved neat rooms,
but her heart also loved pirate songs. One morning, the ship's cook asked her to
help make a rhyme for the captain's birthday. The first rhyme was clumsy, and
the cook worried it would spoil the surprise. Mara kept at it, sorted the words,
and found a better rhyme. When the captain arrived, the whole crew shouted the
finished rhyme and surprised her with lanterns and cake.

World model:
---
- People can carry hope, worry, pride, and joy as memes.
- Poetry work can fail if the rhyme is stiff or off-beat.
- Careful problem solving increases the rhyme quality.
- A surprise ending resolves worry into delight.
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

# Narrative thresholds.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    cook: object | None = None
    mara: object | None = None
    spark: object | None = None
    task: object | None = None
    def __post_init__(self) -> None:
        for k in ("mess", "rhyme", "help", "surprise", "pride", "worry", "joy"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "wife", "housewife", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "father", "captain"}:
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
    place: str = "the apt near the docks"
    affords: set[str] = field(default_factory=lambda: {"rhyme", "problem_solving", "surprise"})
    setting: object | None = None
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
class Task:
    id: str
    name: str
    problem: str
    method: str
    result: str
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
class Spark:
    id: str
    label: str
    reveal: str
    tags: set[str] = field(default_factory=set)
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


def _r_rhyme(world: World) -> list[str]:
    out: list[str] = []
    poet = world.entities.get("Mara")
    task = world.facts.get("task")
    if not poet or not task:
        return out
    if poet.meters["rhyme"] < THRESHOLD:
        return out
    sig = ("rhyme", task.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    poet.memes["pride"] += 1
    poet.memes["joy"] += 0.5
    out.append("The new rhyme clicked into place.")
    return out


def _r_problem_solving(world: World) -> list[str]:
    out: list[str] = []
    poet = world.entities.get("Mara")
    task = world.facts.get("task")
    if not poet or not task:
        return out
    if poet.memes["help"] < THRESHOLD or poet.memes["worry"] < THRESHOLD:
        return out
    sig = ("solve", task.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    poet.meters["rhyme"] += 1
    poet.memes["worry"] = max(0.0, poet.memes["worry"] - 1)
    poet.memes["pride"] += 1
    out.append("Careful word-hunting made the lines sound better.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    poet = world.entities.get("Mara")
    spark = world.facts.get("spark")
    if not poet or not spark:
        return out
    if poet.memes["surprised"] < THRESHOLD:
        return out
    sig = ("surprise", spark.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    poet.memes["surprise"] += 1
    poet.memes["joy"] += 1
    out.append("The whole room burst into a cheerful surprise.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_problem_solving, _r_rhyme, _r_surprise):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_rhyme(world: World, actor: Entity, task: Task) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["rhyme"] += 1
    sim.get(actor.id).memes["help"] += 1
    propagate(sim, narrate=False)
    return {
        "good": sim.get(actor.id).meters["rhyme"] >= THRESHOLD,
        "worry": sim.get(actor.id).memes["worry"],
    }


def tell() -> World:
    setting = Setting()
    world = World(setting)

    mara = world.add(Entity(
        id="Mara",
        kind="character",
        type="housewife",
        label="Mara",
        phrase="a housewife in the apt",
        traits=["tidy", "brave", "kind"],
    ))
    cook = world.add(Entity(
        id="Cook",
        kind="character",
        type="man",
        label="the cook",
        phrase="the ship's cook",
        traits=["busy"],
    ))
    captain = world.add(Entity(
        id="Captain",
        kind="character",
        type="captain",
        label="the captain",
        phrase="the captain of the ship",
        traits=["grand"],
    ))
    task = world.add(Entity(
        id="RhymeTask",
        type="task",
        label="the rhyme task",
        phrase="a tricky birthday rhyme",
    ))
    spark = world.add(Entity(
        id="LanternSpark",
        type="spark",
        label="the lantern surprise",
        phrase="lanterns and cake",
    ))

    world.facts["task"] = task
    world.facts["spark"] = spark

    # Act 1: setup.
    world.say("Mara was a housewife in an apt by the docks, and she liked her shelves neat.")
    world.say("But she also liked pirate songs, and she could hum a tune while folding cloth.")
    world.say("One bright morning, the cook came knocking with a request for a birthday rhyme.")

    # Act 2: problem.
    world.para()
    world.say("He said the first rhyme was clumsy and might spoil the surprise for the captain.")
    mara.memes["worry"] += 1
    if predict_rhyme(world, mara, task)["good"]:
        mara.memes["help"] += 1
    world.say("Mara thought for a moment, then she started sorting words by sound and beat.")
    mara.memes["help"] += 1
    mara.meters["rhyme"] += 1
    propagate(world)

    # Act 3: surprise ending.
    world.para()
    world.say("She found a better line, one that felt steady and bright like a ship's bell.")
    mara.memes["surprised"] += 1
    propagate(world)
    world.say("Then the captain stepped in, and the crew sang the finished rhyme together.")
    world.say("Lanterns flashed, cake appeared, and Mara laughed as the surprise washed over her.")
    mara.memes["surprise"] += 1
    mara.memes["joy"] += 1

    world.facts.update(
        mara=mara,
        cook=cook,
        captain=captain,
        task=task,
        spark=spark,
        resolved=True,
    )
    return world


SETTINGS = {
    "apt": Setting(place="the apt near the docks"),
}

TASKS = {
    "rhyme": Task(
        id="rhyme",
        name="rhyme",
        problem="the first rhyme is clumsy",
        method="sort words by sound and beat",
        result="the line sounds lively and smooth",
        keyword="rhyme",
        tags={"rhyme", "problem_solving"},
    ),
    "problem_solving": Task(
        id="problem_solving",
        name="problem solving",
        problem="the surprise might be spoiled",
        method="think carefully and try again",
        result="the crew finds a better line",
        keyword="solve",
        tags={"problem_solving"},
    ),
    "surprise": Task(
        id="surprise",
        name="surprise",
        problem="the captain must not know yet",
        method="keep the celebration hidden",
        result="the room bursts into cheers",
        keyword="surprise",
        tags={"surprise"},
    ),
}

SPARKS = {
    "surprise": Spark(
        id="surprise",
        label="lanterns and cake",
        reveal="the crew's birthday surprise",
        tags={"surprise"},
    )
}

CURATED = [
    ("apt", "rhyme", "surprise"),
]


@dataclass
class StoryParams:
    place: str
    task: str
    spark: str
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale storyworld: apt, contribute, housewife, rhyme, problem solving, surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--spark", choices=SPARKS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("apt", "rhyme", "surprise"), ("apt", "problem_solving", "surprise")]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "spark", None) is None or c[2] == getattr(args, "spark", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, spark = (list(rng.choice(combos)) + [None, None, None])[:3]
    return StoryParams(place=place, task=task, spark=spark)


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short pirate-tale story about a housewife in an apt who helps with a rhyme and gets a surprise.',
        'Tell a child-friendly pirate story where Mara contributes to a rhyme, solves a problem, and ends with a surprise.',
        'Write a simple story with the words apt, contribute, and housewife, and make it feel like a pirate tale.',
    ]


def story_qa(world: World) -> list[QAItem]:
    mara = _safe_fact(world, world.facts, "mara")
    cook = _safe_fact(world, world.facts, "cook")
    return [
        QAItem(
            question="Who lived in the apt by the docks?",
            answer="Mara lived in the apt by the docks. She was the housewife in the story.",
        ),
        QAItem(
            question="What did Mara contribute to the crew?",
            answer="Mara contributed a better rhyme by sorting words and fixing the beat.",
        ),
        QAItem(
            question="Why was the cook worried at first?",
            answer="The cook was worried because the first rhyme was clumsy and might spoil the surprise.",
        ),
        QAItem(
            question="What happened at the end?",
            answer="The crew sang the finished rhyme, and Mara got a cheerful surprise with lanterns and cake.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair or group of words that sound alike at the end, which makes them fun to say together.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means thinking carefully about a trouble and trying different ways until one works.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something good that happens without warning, so it feels exciting and new.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell()
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
valid_combo(apt,rhyme,surprise).
valid_combo(apt,problem_solving,surprise).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "apt"),
        asp.fact("task", "rhyme"),
        asp.fact("task", "problem_solving"),
        asp.fact("task", "surprise"),
        asp.fact("spark", "surprise"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
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

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place, task, spark in CURATED:
            params = StoryParams(place=place, task=task, spark=spark, seed=base_seed)
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
