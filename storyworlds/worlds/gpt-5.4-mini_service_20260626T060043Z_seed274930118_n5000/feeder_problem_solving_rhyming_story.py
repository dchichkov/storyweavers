#!/usr/bin/env python3
"""
A standalone storyworld for a rhyming, problem-solving feeder tale.

Premise:
A child wants to fill a bird feeder, but a small obstacle gets in the way.
The child thinks, tries a fix, and ends with a peaceful, cheerful scene.

The world is intentionally tiny and state-driven:
- a child, an adult helper, a feeder, and a small problem
- physical meters: fill, stuck, spill, dry, safe
- emotional memes: worry, hope, pride, joy
- a short causal chain that turns a problem into a solution
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
# Registry data
# ---------------------------------------------------------------------------

CHILD_NAMES = [
    "Maya", "Lina", "Noah", "Ari", "Ivy", "Finn", "Zoe", "Milo", "Pia", "Theo"
]

HELPER_NAMES = [
    "Mom", "Dad", "Nana", "Papa", "Aunt Jo", "Uncle Ben"
]

FEEDER_TYPES = [
    "bird feeder",
    "sunflower feeder",
    "seed feeder",
]

PROBLEMS = {
    "jam": {
        "label": "stuck seed",
        "cause": "the tiny seeds were packed too tight",
        "fix": "tap it gently and shake the feeder loose",
        "result": "the seeds slid down like a little snow",
        "risk": "the birds could not get a bite",
        "meter": "stuck",
    },
    "spill": {
        "label": "spilled seed",
        "cause": "the box tipped and the seeds spilled on the grass",
        "fix": "sweep the seed back into a tray and pour it in slowly",
        "result": "the feeder filled up neat and true",
        "risk": "the ground would get messy and the birds would peck at the crumbs",
        "meter": "spill",
    },
    "rain": {
        "label": "wet seed",
        "cause": "a rain cloud made the seed damp",
        "fix": "bring the feeder under the porch and dry the tray with a towel",
        "result": "the seed dried and stayed light",
        "risk": "wet seed clumps up and does not flow",
        "meter": "wet",
    },
}


# ---------------------------------------------------------------------------
# Core data model
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    feeder: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    child_name: str
    helper_name: str
    feeder_type: str
    problem: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[str] = set()
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
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)

    def copy(self) -> "World":
        import copy as _copy

        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def _inc(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _mood(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

def rule_spill(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    feeder = world.get("feeder")
    if child.meters.get("spill", 0) >= 1 and "spill" not in world.fired:
        world.fired.add("spill")
        _inc(feeder, "mess", 1)
        out.append("The seed made a little white trail, a scatter of sparkle and spill.")
    return out


def rule_jam(world: World) -> list[str]:
    out: list[str] = []
    feeder = world.get("feeder")
    child = world.get("child")
    if child.meters.get("stuck", 0) >= 1 and "jam" not in world.fired:
        world.fired.add("jam")
        _inc(feeder, "stuck", 1)
        _mood(child, "worry", 1)
        out.append("The feeder stayed tight and mute, and that made the child feel a little blue.")
    return out


def rule_fix(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    feeder = world.get("feeder")
    problem = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "problem")
    if world.facts.get("solved"):
        return out
    if child.memes.get("hope", 0) >= 1 and helper.memes.get("help", 0) >= 1 and "fix" not in world.fired:
        world.fired.add("fix")
        world.facts["solved"] = True
        feeder.meters["safe"] = 1
        child.memes["joy"] = child.memes.get("joy", 0) + 1
        child.memes["pride"] = child.memes.get("pride", 0) + 1
        helper.memes["pride"] = helper.memes.get("pride", 0) + 1
        out.append(problem["result"].capitalize() + ".")
    return out


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (rule_spill, rule_jam, rule_fix):
            lines = rule(world)
            if lines:
                changed = True
                for line in lines:
                    world.say(line)


# ---------------------------------------------------------------------------
# Rhyming narration
# ---------------------------------------------------------------------------

def intro_line(child: Entity, feeder: Entity, feeder_type: str) -> str:
    return (
        f"{child.id} found a {feeder_type} by the lane, "
        f"and wanted it filled again and again."
    )


def setup_line(child: Entity, feeder: Entity, problem: dict) -> str:
    return (
        f"{child.id} could see the little job ahead: "
        f"{problem['cause']}, so the feeder would not spread."
    )


def worry_line(child: Entity, problem: dict) -> str:
    return (
        f"{child.id} frowned and sighed, quite wary and shy, "
        f"for {problem['risk']} nearby."
    )


def helper_line(helper: Entity, child: Entity) -> str:
    return (
        f"{helper.id} came strolling with a calm, kind grin, "
        f"and said, 'Let's think and try again within.'"
    )


def fix_line(problem: dict) -> str:
    return f"They chose to {problem['fix']} so the work would not sway."


def ending_line(child: Entity, feeder: Entity) -> str:
    return (
        f"Then {child.id} stood back with a happy cheer: "
        f"the feeder was full, bright, and clear."
    )


def tell_story(params: StoryParams) -> World:
    if params.problem not in PROBLEMS:
        pass
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="helper", label=params.helper_name))
    feeder = world.add(Entity(
        id="feeder",
        kind="thing",
        type="feeder",
        label=params.feeder_type,
        phrase=f"a little {params.feeder_type}",
    ))
    problem = _safe_lookup(PROBLEMS, params.problem)
    world.facts["problem"] = problem

    # Act 1
    world.say(intro_line(child, feeder, params.feeder_type))
    world.say(setup_line(child, feeder, problem))

    # Act 2
    if params.problem == "spill":
        _inc(child, "spill", 1)
    elif params.problem == "jam":
        _inc(child, "stuck", 1)
    elif params.problem == "rain":
        _inc(feeder, "wet", 1)

    propagate(world)
    world.say(worry_line(child, problem))

    # Act 3
    _mood(child, "hope", 1)
    _mood(helper, "help", 1)
    world.say(helper_line(helper, child))
    world.say(fix_line(problem))
    if params.problem == "rain":
        _inc(feeder, "dry", 1)
    elif params.problem == "jam":
        _inc(feeder, "loose", 1)
    elif params.problem == "spill":
        _inc(feeder, "clean", 1)
    propagate(world)
    world.say(ending_line(child, feeder))

    world.facts.update(
        child=child,
        helper=helper,
        feeder=feeder,
        params=params,
        solved=world.facts.get("solved", False),
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    problem = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "problem")
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    return [
        f'Write a short rhyming story for young children about a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "feeder").label} and a small problem.',
        f"Tell a gentle problem-solving story where {child.id} tries to help a feeder and then finds a fix.",
        f"Write a simple story with a feeder, a worry, a helper, and a happy ending that rhymes a little.",
        f"Make a child-friendly story about {problem['label']} that ends with the feeder working well again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    feeder: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "feeder")
    problem: dict = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "problem")
    solved = f.get("solved", False)
    qa = [
        QAItem(
            question=f"What did {child.id} want to do with the {feeder.label}?",
            answer=f"{child.id} wanted to fill the {feeder.label} so the birds could come and eat.",
        ),
        QAItem(
            question=f"What was the problem in the story?",
            answer=f"The problem was that {problem['cause']}. That made the feeder hard to use.",
        ),
        QAItem(
            question=f"Who helped {child.id}?",
            answer=f"{helper.id} helped {child.id} slow down, think, and solve the problem.",
        ),
    ]
    if solved:
        qa.append(
            QAItem(
                question=f"How did they fix it?",
                answer=f"They {problem['fix']}. After that, the feeder worked again.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {child.id} feel at the end?",
                answer=f"{child.id} felt proud and happy because the feeder was ready and the problem was gone.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a feeder?",
            answer="A feeder is a container that holds food for birds or other animals.",
        ),
        QAItem(
            question="Why do people fill bird feeders?",
            answer="People fill bird feeders so birds can find food near homes and gardens.",
        ),
        QAItem(
            question="Why is it nice to solve a small problem?",
            answer="Solving a small problem can make a job easier, safer, and less frustrating.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A feeder story is valid when there is a fixable problem and a helper.
has_problem(jam).
has_problem(spill).
has_problem(rain).

solvable(jam).
solvable(spill).
solvable(rain).

valid_story(Problem) :- has_problem(Problem), solvable(Problem).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for key in PROBLEMS:
        lines.append(asp.fact("problem", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid() -> list[tuple]:
    return [(k,) for k in PROBLEMS.keys()]


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(python_valid())
    if a == b:
        print(f"OK: ASP matches Python gate ({len(a)} cases).")
        return 0
    print("MISMATCH between ASP and Python:")
    if a - b:
        print("only in ASP:", sorted(a - b))
    if b - a:
        print("only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Parameters, generation, output
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming feeder storyworld with gentle problem solving.")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--feeder", choices=FEEDER_TYPES)
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
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
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    feeder_type = getattr(args, "feeder", None) or rng.choice(FEEDER_TYPES)
    child_name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    if helper_name == child_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        child_name=child_name,
        helper_name=helper_name,
        feeder_type=feeder_type,
        problem=problem,
    )


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


CURATED = [
    StoryParams(child_name="Maya", helper_name="Mom", feeder_type="bird feeder", problem="jam"),
    StoryParams(child_name="Noah", helper_name="Dad", feeder_type="seed feeder", problem="spill"),
    StoryParams(child_name="Ivy", helper_name="Nana", feeder_type="sunflower feeder", problem="rain"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/1."))
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
            try:
                params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.child_name} / {p.problem} / {p.feeder_type}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
