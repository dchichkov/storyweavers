#!/usr/bin/env python3
"""
storyworlds/worlds/exam_businessman_commission_rhyme_animal_story.py
====================================================================

A small standalone storyworld in an Animal Story style:
a businessman visits an animal town, commissions a rhyme helper, and worries
about an exam he must pass. The world is simulated with typed entities, physical
meters, emotional memes, a small causal model, a reasonableness gate, and an
inline ASP twin.

Seed words: exam, businessman, commission
Feature: rhyme
Style: animal-story, child-facing, concrete, upbeat
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    boss: object | None = None
    helpy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "man", "businessman"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"rabbit", "bird", "cat", "mouse"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
        if not hasattr(self, "_tags"):
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
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Task:
    id: str
    verb: str
    rhyme: str
    cost: str
    lift: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
    help_text: str
    fixes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        # tired worry -> slower, more worried
        for e in list(world.entities.values()):
            if e.memes["worry"] >= THRESHOLD and ("tired_worry", e.id) not in world.fired:
                world.fired.add(("tired_worry", e.id))
                e.meters["tired"] += 1
                out.append(f"{e.id} looked worn out from all the worrying.")
                changed = True
        # task finished -> joy
        if world.facts.get("task_done") and ("task_done",) not in world.fired:
            world.fired.add(("task_done",))
            for e in list(world.entities.values()):
                if e.role in {"businessman", "helper"}:
                    e.memes["joy"] += 1
            out.append("The little job ended well, and that brought smiles all around.")
            changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(task: Task, tool: Tool) -> bool:
    return task.keyword in tool.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for task_id, task in TASKS.items():
            for tool_id, tool in TOOLS.items():
                if reasonableness_gate(task, tool) and task_id in _safe_lookup(SETTINGS, setting).affords:
                    combos.append((setting, task_id, tool_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    task: str
    tool: str
    businessman: str
    helper: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


SETTINGS = {
    "market": Setting("the bright market", affords={"exam"}),
    "office": Setting("the little office", affords={"exam"}),
    "station": Setting("the train station", affords={"exam"}),
}

TASKS = {
    "exam": Task(
        id="exam",
        verb="study for the exam",
        rhyme="time with rhyme",
        cost="nervous and tired",
        lift="stand up proud",
        keyword="exam",
        tags={"exam"},
    ),
}

TOOLS = {
    "rhyme_book": Tool(
        id="rhyme_book",
        label="rhyme book",
        phrase="a small rhyme book",
        help_text="reads short lines that help the mind feel steady",
        fixes={"exam"},
        tags={"rhyme"},
    ),
    "cheer_card": Tool(
        id="cheer_card",
        label="cheer card",
        phrase="a bright cheer card",
        help_text="shows a friendly line and a little smile",
        fixes={"exam"},
        tags={"rhyme"},
    ),
}

ANIMALS = ["fox", "rabbit", "cat", "mouse", "bird"]
NAMES = {
    "fox": ["Finn", "Faye"],
    "rabbit": ["Ruby", "Remy"],
    "cat": ["Coco", "Milo"],
    "mouse": ["Mimi", "Moss"],
    "bird": ["Bibi", "Beau"],
}
TRAITS = ["brisk", "kind", "curious", "gentle", "lively"]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in _safe_lookup(SETTINGS, sid).affords:
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("keyword", tid, t.keyword))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for k in u.fixes:
            lines.append(asp.fact("fixes", uid, k))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,U) :- setting(S), task(T), tool(U), affords(S,T), keyword(T,K), fixes(U,K).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combos).")
        return 0
    print("MISMATCH")
    print("only in asp:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story exam and rhyme world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--businessman")
    ap.add_argument("--helper")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, task, tool = rng.choice(list(combos))
    businessman = getattr(args, "businessman", None) or rng.choice(["Benny", "Mason", "Oscar", "Hugo"])
    helper = getattr(args, "helper", None) or rng.choice(["Ria", "Nia", "Pip", "Lulu"])
    return StoryParams(setting, task, tool, businessman, helper)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    boss = world.add(Entity(id=params.businessman, kind="character", type="fox", role="businessman", traits=["polite", "busy"]))
    helpy = world.add(Entity(id=params.helper, kind="character", type="rabbit", role="helper", traits=["quick", "kind"]))
    task = _safe_lookup(TASKS, params.task)
    tool = _safe_lookup(TOOLS, params.tool)

    boss.memes["worry"] = 1.0
    helpy.memes["joy"] = 1.0

    world.say(f"In {world.setting.place}, a businessman fox named {boss.id} had a big exam to pass.")
    world.say(f"He hoped to {task.verb}, but the day felt long and gray.")
    world.say(f"A small helper rabbit named {helpy.id} offered {tool.phrase}, and {tool.help_text}.")
    world.para()
    world.say(f"{boss.id} needed a calm plan, a steady aim, and a line that could rhyme.")
    world.say(f"{helpy.id} said, '{boss.id}, take your time; a rhyme can chime and help you climb.'")

    boss.memes["worry"] += 1.0
    if reasonableness_gate(task, tool):
        world.para()
        boss.meters["steady"] += 1
        world.say(f"The rhymes made {boss.id} feel less tense, and the words fit the exam just fine.")
        world.say(f"He studied each note, each clue, each sign, until the answers lined up like a tidy line.")
        world.facts["task_done"] = True
        propagate(world)
        world.para()
        boss.memes["joy"] += 1
        helpy.memes["joy"] += 1
        world.say(f"At the exam, {boss.id} smiled and spoke in rhyme, and the little test went well.")
        world.say(f"He passed with a bow, and {helpy.id} cheered: 'That was fine! You shone like a sign!'")
    else:
        pass
    world.facts.update(boss=boss, helper=helpy, task=task, tool=tool, params=params)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    boss = f["boss"]
    helper = f["helper"]
    task = f["task"]
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(question=f"Who had the exam in the story?", answer=f"The businessman fox {boss.id} had the exam."),
        QAItem(question=f"Who helped {boss.id}?", answer=f"The helper rabbit {helper.id} helped with {tool.phrase}."),
        QAItem(question=f"What did {boss.id} need to do?", answer=f"He needed to {task.verb}."),
        QAItem(question=f"How did the helper make the day feel better?", answer=f"{helper.id} used a rhyme and a calm plan so the exam felt less scary."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an exam?", answer="An exam is a test that asks you to show what you know."),
        QAItem(question="What is a businessman?", answer="A businessman is a grown-up who works with money, plans, or trade."),
        QAItem(question="What is a commission?", answer="A commission is a special job or request that someone asks another person to do."),
        QAItem(question="What is a rhyme?", answer="A rhyme is when words sound alike at the end, like time and rhyme."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short animal-story for a child about an exam, a businessman, and a helpful rhyme.',
        f"Tell a gentle story where {f['boss'].id} the businessman fox worries about an exam, and a rabbit helper makes a rhyme to help.",
        "Create a simple story with a commission, an exam, and a cheerful rhyming ending.",
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
        lines.append(f"  {e.id:8} ({e.type:10}) meters={dict(e.meters)} memes={dict(e.memes)} role={e.role}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="market", task="exam", tool="rhyme_book", businessman="Benny", helper="Ruby"),
    StoryParams(setting="office", task="exam", tool="cheer_card", businessman="Mason", helper="Lulu"),
]


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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
