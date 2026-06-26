#!/usr/bin/env python3
"""
A small fable-like story world about an axe, a broken handle, and a clever fix.
The story is built from simulated state so each sample is a complete, grounded
miniature tale with a problem, a plan, and a rhyme-shaped ending.
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
# Data model
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    fix: object | None = None
    helper: object | None = None
    hero: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mole", "fox", "rabbit", "mouse", "hedgehog"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    afford: str
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
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: str
    fix_label: str
    rhyme: str
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
    tool: str
    hero: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "woods": Setting(place="the woods", afford="cut"),
    "grove": Setting(place="the grove", afford="cut"),
    "farm": Setting(place="the old farm", afford="cut"),
}

TOOLS = {
    "axe": Tool(
        id="axe",
        label="axe",
        phrase="a sharp little axe",
        helps_with="cutting wood",
        fix_label="new handle",
        rhyme="If you mend the tool with care, the work can go on fair and square.",
    ),
    "hatchet": Tool(
        id="hatchet",
        label="hatchet",
        phrase="a small hatchet",
        helps_with="splitting kindling",
        fix_label="new handle",
        rhyme="A steady plan can save the day; a broken thing need not delay.",
    ),
}

HEROES = [
    ("mole", "mole"),
    ("fox", "fox"),
    ("rabbit", "rabbit"),
    ("mouse", "mouse"),
]

HELPERS = [
    ("owl", "owl"),
    ("badger", "badger"),
    ("deer", "deer"),
    ("hare", "hare"),
]

NAMES = {
    "mole": ["Milo", "Mina", "Moss"],
    "fox": ["Fenn", "Fiona", "Fern"],
    "rabbit": ["Rory", "Ruby", "Rosie"],
    "mouse": ["Miri", "Mossy", "Minnie"],
    "owl": ["Orla", "Otis", "Olwen"],
    "badger": ["Bram", "Bea", "Bax"],
    "deer": ["Della", "Dune", "Dawn"],
    "hare": ["Hugo", "Hattie", "Hal"],
}

TRAITS = ["wise", "gentle", "patient", "careful", "steady"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def choose_name(kind: str, rng: random.Random) -> str:
    return rng.choice(_safe_lookup(NAMES, kind))


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero_kind = params.hero
    helper_kind = params.helper
    hero = world.add(Entity(
        id=choose_name(hero_kind, random.Random(params.seed or 0)),
        kind="character",
        type=hero_kind,
        label=hero_kind,
        meters={"hope": 0.0},
        memes={"worry": 0.0, "resolve": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id=choose_name(helper_kind, random.Random((params.seed or 0) + 1)),
        kind="character",
        type=helper_kind,
        label=helper_kind,
        meters={"hope": 0.0},
        memes={"worry": 0.0, "resolve": 0.0, "joy": 0.0},
    ))
    tool = world.add(Entity(
        id="tool",
        type=params.tool,
        label=_safe_lookup(TOOLS, params.tool).label,
        phrase=_safe_lookup(TOOLS, params.tool).phrase,
        owner=hero.id,
        caretaker=helper.id,
        meters={"sharp": 1.0, "broken": 1.0},
        memes={"pride": 1.0},
    ))
    fix = world.add(Entity(
        id="fix",
        type="handle",
        label=_safe_lookup(TOOLS, params.tool).fix_label,
        phrase=f"a sturdy {_safe_lookup(TOOLS, params.tool).fix_label}",
        owner=helper.id,
        meters={"ready": 0.0},
        memes={"hope": 0.0},
    ))
    world.facts.update(hero=hero, helper=helper, tool=tool, fix=fix, params=params)
    return world


def scene_open(world: World) -> None:
    h = _safe_fact(world, world.facts, "hero")
    t = _safe_fact(world, world.facts, "tool")
    world.say(
        f"{h.id} was a {random.choice(TRAITS)} little {h.type} who loved {t.helps_with}."
    )
    world.say(
        f"One bright morning, {h.pronoun('possessive')} {t.label} gleamed by the path."
    )


def scene_problem(world: World) -> None:
    h = _safe_fact(world, world.facts, "hero")
    t = _safe_fact(world, world.facts, "tool")
    world.para()
    h.memes["worry"] += 1
    world.say(
        f"But then {h.id} saw a crack in the wooden handle, and {h.pronoun()} frowned."
    )
    world.say(
        f"The {t.label} could still swing, but not safely; the work might snap in two."
    )


def scene_solve(world: World) -> None:
    h = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    fix = _safe_fact(world, world.facts, "fix")
    tool = _safe_fact(world, world.facts, "tool")
    world.para()
    helper.memes["resolve"] += 1
    fix.meters["ready"] = 1.0
    world.say(
        f"{helper.id} came along and said, 'First we think, then we fix; "
        f"a broken thing can still be quick.'"
    )
    world.say(
        f"They found a straight new {fix.label} and fitted it tight, so the {tool.label} felt strong and right."
    )
    tool.meters["broken"] = 0.0
    tool.meters["useful"] = 1.0
    h.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Now {h.id} could keep {tool.helps_with}, and the little team smiled in the light."
    )


def scene_close(world: World) -> None:
    h = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    tool = _safe_fact(world, world.facts, "tool")
    world.para()
    world.say(
        f"{_safe_lookup(TOOLS, tool.type).rhyme} {h.id} and {helper.id} carried on, and the woods grew quiet and kind."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tool: Tool = _safe_lookup(TOOLS, (f.get("tool") or next(iter(TOOLS.values()))).type)
    return [
        f"Write a short fable about {f['hero'].id} and a broken {tool.label} that needs clever problem solving.",
        f"Tell a rhyming story where a small animal finds a broken {tool.label}, worries, and then repairs it.",
        f"Create a child-friendly fable with a problem, a fix, and a gentle rhyme at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, tool = f["hero"], f["helper"], (f.get("tool") or next(iter(TOOLS.values())))
    tool_def = _safe_lookup(TOOLS, tool.type)
    return [
        QAItem(
            question=f"What problem did {hero.id} notice with the {tool.label}?",
            answer=f"{hero.id} noticed that the wooden handle was cracked, so the {tool.label} was not safe to use.",
        ),
        QAItem(
            question=f"Who helped solve the problem in the story?",
            answer=f"{helper.id} helped by finding a new {tool_def.fix_label} and fitting it to the {tool.label}.",
        ),
        QAItem(
            question=f"What changed after they fixed the {tool.label}?",
            answer=f"After the repair, the {tool.label} became strong again, and {hero.id} could keep working safely.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is an axe used for?",
        answer="An axe is a tool used for cutting wood.",
    ),
    QAItem(
        question="Why should a broken handle be fixed?",
        answer="A broken handle should be fixed so the tool stays safe and does not snap during use.",
    ),
    QAItem(
        question="What is a rhyme?",
        answer="A rhyme is when words sound alike at the end, like day and play.",
    ),
    QAItem(
        question="What is a fable?",
        answer="A fable is a short story that often teaches a simple lesson.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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
    lines.append("== (3) World knowledge questions ==")
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
        if e.kind == "character":
            bits.append("kind=character")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for tool in TOOLS:
            for hero_kind, _ in HEROES:
                combos.append((place, tool, hero_kind))
    return combos


def explain_rejection(_: str) -> str:
    return "(No story: the requested options do not make a reasonable fable.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
tool(T) :- tool_kind(T).
hero(H) :- hero_kind(H).

valid(Place, Tool, Hero) :- place(Place), tool(Tool), hero(Hero).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for t in TOOLS:
        lines.append(asp.fact("tool_kind", t))
    for h, _ in HEROES:
        lines.append(asp.fact("hero_kind", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------
def build_story(world: World) -> None:
    scene_open(world)
    scene_problem(world)
    scene_solve(world)
    scene_close(world)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    build_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="woods", tool="axe", hero="mole", helper="owl"),
    StoryParams(place="grove", tool="hatchet", hero="fox", helper="badger"),
    StoryParams(place="farm", tool="axe", hero="rabbit", helper="deer"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like story world about an axe and a clever repair.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero", choices=[h for h, _ in HEROES])
    ap.add_argument("--helper", choices=[h for h, _ in HELPERS])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    hero = getattr(args, "hero", None) or rng.choice([h for h, _ in HEROES])
    helper = getattr(args, "helper", None) or rng.choice([h for h, _ in HELPERS])
    if helper == hero:
        helper = rng.choice([h for h, _ in HELPERS if h != hero])
    return StoryParams(place=place, tool=tool, hero=hero, helper=helper)


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero} / {p.tool} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
