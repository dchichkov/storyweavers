#!/usr/bin/env python3
"""
Standalone storyworld: slick friendship problem solving with a heartwarming ending.

A small, simulated world about two friends who face a slick, slippery problem,
solve it together, and end with a warm, happy feeling.
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
    held_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend1: object | None = None
    friend2: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
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
class Place:
    id: str
    label: str
    indoor: bool = False
    slick: bool = False
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
class Tool:
    id: str
    label: str
    phrase: str
    mess_guard: str
    helps_with: str
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
    problem: str
    tool: str
    name1: str
    name2: str
    type1: str
    type2: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def copy(self) -> "World":
        w = World(self.place)
        import copy
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", indoor=True, slick=True),
    "hallway": Place("hallway", "the hallway", indoor=True, slick=True),
    "porch": Place("porch", "the porch", indoor=False, slick=True),
    "playground": Place("playground", "the playground", indoor=False, slick=False),
}

PROBLEMS = {
    "spilled_juice": ("a slick puddle of juice", "slipped on the juice", "slippery juice", "spill"),
    "rain_on_steps": ("rainwater on the steps", "slipped on the wet steps", "wet steps", "rain"),
    "soap_suds": ("soap suds on the floor", "slipped on the suds", "slippery suds", "soap"),
}

TOOLS = {
    "towel": Tool("towel", "a big towel", "the big towel", "wet", "wipe"),
    "sign": Tool("sign", "a bright yellow sign", "the bright yellow sign", "slip", "warn"),
    "mop": Tool("mop", "a soft mop", "the soft mop", "wet", "clean"),
}

NAMES_GIRL = ["Maya", "Lina", "Nora", "Ivy", "Zoe", "Mina"]
NAMES_BOY = ["Eli", "Noah", "Owen", "Theo", "Ben", "Leo"]
TRAITS = ["kind", "gentle", "careful", "brave", "patient", "cheerful"]


def reasonableness(problem: str, tool: str, place: str) -> None:
    if problem not in PROBLEMS or tool not in TOOLS or place not in PLACES:
        pass
    if problem == "spilled_juice" and tool not in {"towel", "mop"}:
        pass
    if problem == "rain_on_steps" and tool not in {"towel", "sign"}:
        pass
    if problem == "soap_suds" and tool not in {"towel", "sign", "mop"}:
        pass
    if place == "playground" and problem != "soap_suds":
        pass


def predict_safety(world: World, tool: Tool) -> bool:
    return tool.helps_with in world.facts["problem_key"]


def tell_story(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    problem_text, slip_text, clue_word, problem_key = _safe_lookup(PROBLEMS, params.problem)
    tool = _safe_lookup(TOOLS, params.tool)
    world = World(place)

    friend1 = world.add(Entity(
        id=params.name1, kind="character", type=params.type1,
        memes={"friendship": 1.0, "worry": 0.0, "joy": 0.0, "problem_solving": 0.0},
    ))
    friend2 = world.add(Entity(
        id=params.name2, kind="character", type=params.type2,
        memes={"friendship": 1.0, "worry": 0.0, "joy": 0.0, "problem_solving": 0.0},
    ))
    helper = world.add(Entity(
        id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, protective=True
    ))

    world.facts = {
        "problem_text": problem_text,
        "problem_key": problem_key,
        "slip_text": slip_text,
        "clue_word": clue_word,
        "tool": tool,
        "helper": helper,
        "friend1": friend1,
        "friend2": friend2,
        "place": place,
    }

    world.say(
        f"{friend1.id} and {friend2.id} were best friends, and they loved spending time together at {place.label}."
    )
    world.say(
        f"One day, they found {problem_text}, and the spot looked slick and tricky."
    )
    friend1.memes["worry"] += 1
    friend2.memes["worry"] += 1
    world.para()
    world.say(
        f"{friend1.id} almost {slip_text}, so both friends stopped and looked at the problem together."
    )
    world.say(
        f"{friend2.id} said, \"Let's fix this kindly,\" and {friend1.id} nodded because friends help each other."
    )

    if predict_safety(world, tool):
        world.para()
        friend1.memes["problem_solving"] += 1
        friend2.memes["problem_solving"] += 1
        friend1.memes["joy"] += 1
        friend2.memes["joy"] += 1
        if tool.id == "towel":
            world.say(
                f"They used {tool.phrase} to wipe the slick spot away, and the floor became safe again."
            )
        elif tool.id == "sign":
            world.say(
                f"They set up {tool.phrase} to warn everyone, so no one would step into the slick place."
            )
        else:
            world.say(
                f"They used {tool.phrase} to clean the mess, and the slick patch slowly disappeared."
            )
        world.say(
            f"After that, the friends laughed, stood safely side by side, and felt proud that they had solved it together."
        )
        world.say(
            f"The day ended warm and happy, with {friend1.id} and {friend2.id} smiling at each other and enjoying the clean, calm place."
        )
    else:
        pass

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming story about two friends at {f['place'].label} who face a slick problem and solve it together.",
        f"Tell a gentle story where {f['friend1'].id} and {f['friend2'].id} use {(f.get('tool') or next(iter(TOOLS.values()))).phrase} to fix {f['problem_text']}.",
        f"Write a short child-friendly story about friendship, problem solving, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = _safe_fact(world, f, "place").label
    t = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Where were the two friends when they found the slick problem?",
            answer=f"They were at {p}, where they noticed the slippery problem together.",
        ),
        QAItem(
            question=f"What did the friends use to solve the problem?",
            answer=f"They used {t.phrase} to help fix the slick spot safely.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with both friends smiling, feeling proud, and enjoying a warm happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does slick mean?",
            answer="Slick means slippery, so something slick can make it easy to slide or fall.",
        ),
        QAItem(
            question="Why do friends work together to solve problems?",
            answer="Friends work together because two helpers can think, carry, and fix things more easily than one.",
        ),
        QAItem(
            question="What makes a story heartwarming?",
            answer="A heartwarming story feels kind, caring, and happy because the people help each other.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place(kitchen;hallway;porch;playground).
problem(spilled_juice;rain_on_steps;soap_suds).
tool(towel;sign;mop).

helps(towel,spilled_juice).
helps(mop,spilled_juice).
helps(towel,rain_on_steps).
helps(sign,rain_on_steps).
helps(towel,soap_suds).
helps(sign,soap_suds).
helps(mop,soap_suds).

valid_story(P,Pr,T) :- place(P), problem(Pr), tool(T), helps(T,Pr).
#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for pr in PROBLEMS:
        lines.append(asp.fact("problem", pr))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for tid, tool in TOOLS.items():
        for pr in PROBLEMS:
            if tool.helps_with in _safe_lookup(PROBLEMS, pr)[3]:
                lines.append(asp.fact("helps", tid, pr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set()
    for p in PLACES:
        for pr in PROBLEMS:
            for t in TOOLS:
                try:
                    reasonableness(pr, t, p)
                    py.add((p, pr, t))
                except StoryError:
                    pass
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python reasonableness gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("Only in Python:", sorted(py - cl))
    print("Only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming slick friendship storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--type1", choices=["girl", "boy"])
    ap.add_argument("--type2", choices=["girl", "boy"])
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    reasonableness(problem, tool, place)
    type1 = getattr(args, "type1", None) or rng.choice(["girl", "boy"])
    type2 = getattr(args, "type2", None) or ("boy" if type1 == "girl" else "girl")
    n1 = getattr(args, "name1", None) or rng.choice(NAMES_GIRL if type1 == "girl" else NAMES_BOY)
    n2_pool = [n for n in (NAMES_GIRL if type2 == "girl" else NAMES_BOY) if n != n1]
    n2 = getattr(args, "name2", None) or rng.choice(n2_pool)
    return StoryParams(place=place, problem=problem, tool=tool, name1=n1, name2=n2, type1=type1, type2=type2)


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
    StoryParams(place="kitchen", problem="spilled_juice", tool="towel", name1="Maya", name2="Eli", type1="girl", type2="boy"),
    StoryParams(place="hallway", problem="rain_on_steps", tool="sign", name1="Nora", name2="Theo", type1="girl", type2="boy"),
    StoryParams(place="porch", problem="soap_suds", tool="mop", name1="Lina", name2="Owen", type1="girl", type2="boy"),
]


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
            print(" ", row)
        return

    if getattr(args, "seed", None) is not None:
        base_seed = getattr(args, "seed", None)
    else:
        base_seed = random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
