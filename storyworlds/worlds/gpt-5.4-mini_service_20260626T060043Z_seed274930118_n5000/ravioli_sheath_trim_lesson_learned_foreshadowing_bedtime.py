#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ravioli_sheath_trim_lesson_learned_foreshadowing_bedtime.py
==============================================================================================================================

A small bedtime-story world about a child, a kitchen, and a careful lesson:
ravioli dough, a small cutting sheath, and the urge to trim just a little too fast.

Premise:
- A child loves helping make ravioli before bed.
- The child wants to trim the dough into neat squares.
- A sharp little cutter lives in a sheath, and the sheath matters.

Tension:
- The child wants to hurry and trim without listening.
- The parent foresees that rushing with the cutter could nick a finger or make a mess.
- The child is tempted to ignore the warning.

Turn:
- The child notices the sheath, slows down, and learns the safer way.
- The parent lets the child help with the dough in a gentle, guided way.

Resolution:
- The ravioli are finished, the cutter goes back in its sheath, and the child goes to bed with a new lesson learned.

This world is intentionally small, concrete, and state-driven. It includes:
- physical meters (mess, sharpness, clean, warmth, fullness)
- emotional memes (joy, worry, patience, pride, trust, defiance)
- a Python reasonableness gate and an inline ASP twin for parity checks.
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
    in_sheath: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the warm kitchen"
    SETTING: object | None = None
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
    noun: str
    mess: str
    danger: str
    needs_sheath: bool = True
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
class Lesson:
    title: str
    text: str
    lesson: object | None = None
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def is_reasonable(tool: Tool, action: str) -> bool:
    if action == "trim" and tool.needs_sheath:
        return True
    return action != "trim"


def valid_combo(tool: Tool) -> bool:
    return tool.id in TOOLS and tool.mess == "flour"


@dataclass
class StoryParams:
    tool: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None
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


SETTING = Setting(place="the warm kitchen")

TOOLS = {
    "knife": Tool(
        id="knife",
        label="little ravioli knife",
        noun="knife",
        mess="flour",
        danger="sharp",
        needs_sheath=True,
    ),
    "cutter": Tool(
        id="cutter",
        label="pasta cutter",
        noun="cutter",
        mess="flour",
        danger="sharp",
        needs_sheath=True,
    ),
}

NAMES = {
    "girl": ["Mina", "Lily", "Nora", "Ivy"],
    "boy": ["Theo", "Milo", "Ezra", "Finn"],
}
PARENTS = ["mother", "father"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about ravioli, sheath, and trim.")
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    if tool not in TOOLS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    return StoryParams(tool=tool, name=name, gender=gender, parent=parent)


def _start(world: World, child: Entity, parent: Entity, tool: Entity) -> None:
    world.say(
        f"At bedtime in {world.setting.place}, {child.id} wanted to make ravioli "
        f"with {tool.label}."
    )
    world.say(
        f"The dough was soft, the room was quiet, and the moonlight made the bowl "
        f"look silver."
    )


def _foreshadow(world: World, child: Entity, tool: Entity) -> None:
    world.say(
        f"{child.pronoun('possessive').capitalize()} parent noticed the small {tool.noun} "
        f"had a sheath resting beside it."
    )
    world.say(
        f'"Keep the sheath on when you are not trimming," {child.pronoun("possessive")} '
        f"parent said, with a careful voice."
    )
    world.facts["foreshadowed"] = True


def _temptation(world: World, child: Entity, tool: Entity) -> None:
    child.memes["want"] += 1
    child.memes["impatience"] += 1
    world.say(
        f"{child.id} reached for the {tool.noun} and wanted to trim faster and faster."
    )
    world.say(
        f"For a tiny moment, {child.id} forgot how sharp it could be."
    )


def _risk(world: World, child: Entity, tool: Entity) -> None:
    child.memes["worry"] += 1
    world.say(
        f"The parent gently held up a hand and reminded {child.id} that one quick slip "
        f"could nick a finger or tear the dough."
    )


def _turn(world: World, child: Entity, tool: Entity) -> None:
    child.memes["patience"] += 1
    child.memes["defiance"] = 0
    tool.in_sheath = False
    world.say(
        f"{child.id} looked at the sheath and nodded."
    )
    world.say(
        f"{child.id} trimmed the ravioli the slow way, one neat square at a time."
    )
    world.say(
        f"The dough stayed tidy, and the little pieces looked like pillows for supper."
    )


def _finish(world: World, child: Entity, parent: Entity, tool: Entity, lesson: Lesson) -> None:
    child.memes["joy"] += 1
    child.memes["trust"] += 1
    child.memes["pride"] += 1
    tool.in_sheath = True
    world.say(
        f"When the tray was full, the {tool.noun} went back into its sheath."
    )
    world.say(
        f"{child.id} carried the tray to the counter, washed {child.pronoun('possessive')} "
        f"hands, and smiled at the neat ravioli."
    )
    world.say(
        f"That was the lesson learned: a careful pause can make bedtime work go better."
    )
    world.say(
        f"Then {child.id} climbed into bed while {parent.id} tucked the kitchen quiet for the night."
    )
    world.facts["lesson"] = lesson.title
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="parent"))
    tool_def = _safe_lookup(TOOLS, params.tool)
    tool = world.add(Entity(
        id=tool_def.id,
        type="tool",
        label=tool_def.label,
        owner=child.id,
        caretaker=parent.id,
        in_sheath=True,
        meters={"sharp": 1.0},
    ))
    lesson = Lesson(
        title="Be careful with sharp tools",
        text="Using a sheath and trimming slowly keeps hands safe and dough neat.",
    )
    child.memes["joy"] += 1
    _start(world, child, parent, tool)
    world.para()
    _foreshadow(world, child, tool)
    _temptation(world, child, tool)
    _risk(world, child, tool)
    world.para()
    _turn(world, child, tool)
    world.para()
    _finish(world, child, parent, tool, lesson)
    world.facts.update(child=child, parent=parent, tool=tool, lesson=lesson)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f"Write a gentle bedtime story about {child.id}, {tool.label}, and a lesson learned about safety.",
        f"Tell a foreshadowing bedtime story where a child wants to trim ravioli but must remember the sheath.",
        f"Write a short story for a sleepy child that ends with ravioli ready and a careful lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What did {child.id} want to make before bed?",
            answer=f"{child.id} wanted to make ravioli in the warm kitchen before bedtime.",
        ),
        QAItem(
            question=f"What did the parent warn {child.id} about?",
            answer=f"The parent warned {child.id} to keep the {tool.noun} in its sheath when not trimming, because it was sharp.",
        ),
        QAItem(
            question=f"What lesson was learned by the end?",
            answer="The lesson learned was to use a sheath and trim slowly so the food stayed neat and the hands stayed safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ravioli?",
            answer="Ravioli are little pasta pillows that are often filled and then sealed before cooking.",
        ),
        QAItem(
            question="What is a sheath?",
            answer="A sheath is a cover that holds a sharp tool safely when it is not being used.",
        ),
        QAItem(
            question="Why should someone trim carefully with a sharp tool?",
            answer="Careful trimming helps keep fingers safe and makes the edges neat instead of messy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.in_sheath:
            parts.append("in_sheath=True")
        lines.append(f"  {e.id}: {' '.join(parts)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_wants_trim(C) :- child(C).
sharp_tool(T) :- tool(T).
has_sheath(T) :- tool(T), sheath_on(T).
safe_trim(C, T) :- child_wants_trim(C), sharp_tool(T), has_sheath(T).
lesson_learned(C) :- safe_trim(C, T).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("child", "child")]
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sheath_on", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp
    model = asp.one_model(asp_program("#show lesson_learned/1."))
    return bool(asp.atoms(model, "lesson_learned"))


def python_valid() -> bool:
    return any(valid_combo(t) for t in TOOLS.values())


def asp_verify() -> int:
    a = asp_valid()
    b = python_valid()
    if a == b:
        print("OK: ASP and Python gates agree.")
        return 0
    print(f"MISMATCH: ASP={a} Python={b}")
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
    StoryParams(tool="knife", name="Mina", gender="girl", parent="mother"),
    StoryParams(tool="cutter", name="Theo", gender="boy", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show lesson_learned/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is minimal in this world; the parity check is the intended use.")
        print(asp_program("#show lesson_learned/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
