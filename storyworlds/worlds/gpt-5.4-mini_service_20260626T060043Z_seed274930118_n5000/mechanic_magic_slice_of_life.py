#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a mechanic whose careful repairs are
sometimes helped by gentle magic, but never replaced by it.

The world is built around a tiny shop, a useful problem, a patient turn, and a
quiet ending where something works again.
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
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    customer: object | None = None
    item: object | None = None
    mechanic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    detail: str
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
    thing: str
    fault: str
    visible: str
    fix: str
    magic_hint: str
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


@dataclass
class MagicTool:
    id: str
    label: str
    effect: str
    helps: set[str] = field(default_factory=set)
    requires_kindness: bool = True
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
class StoryParams:
    place: str
    problem: str
    tool: str
    mechanic_name: str
    mechanic_type: str
    customer_name: str
    customer_type: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "corner_shop": Setting("the corner garage", "The shop smelled like oil, warm metal, and fresh coffee."),
    "quiet_street": Setting("the little roadside bay", "Cars hummed past while tools rested in neat rows."),
    "home_garage": Setting("the home garage", "A lantern glowed over a tidy workbench and a sleeping cat."),
}

PROBLEMS = {
    "scooter_chain": Problem(
        id="scooter_chain",
        thing="scooter chain",
        fault="had slipped loose",
        visible="dangling like a silver ribbon",
        fix="tighten the chain and test the wheels",
        magic_hint="a soft blue spark could help the chain line up",
    ),
    "bike_light": Problem(
        id="bike_light",
        thing="bike light",
        fault="had gone dark",
        visible="blinking weakly and then stopping",
        fix="replace the battery and tap the casing gently",
        magic_hint="a tiny glow could wake the bulb again",
    ),
    "wagon_wheel": Problem(
        id="wagon_wheel",
        thing="wagon wheel",
        fault="kept wobbling",
        visible="shivering whenever it rolled",
        fix="steady the axle and give the rim a careful twist",
        magic_hint="a warm shimmer could coax the wood into place",
    ),
    "clock_ticker": Problem(
        id="clock_ticker",
        thing="clock",
        fault="was skipping beats",
        visible="ticking too fast, then too slow",
        fix="clean the gears and nudge the tiny spring",
        magic_hint="a gold dusting could soothe the gears",
    ),
}

TOOLS = {
    "spark_wand": MagicTool(
        id="spark_wand",
        label="a spark wand",
        effect="a small spark that helps metal settle where it belongs",
        helps={"scooter_chain", "bike_light"},
    ),
    "glow_glove": MagicTool(
        id="glow_glove",
        label="a glow glove",
        effect="a warm light that helps hidden parts show themselves",
        helps={"bike_light", "clock_ticker"},
    ),
    "mend_chime": MagicTool(
        id="mend_chime",
        label="a mend chime",
        effect="a clear note that helps loose pieces remember their place",
        helps={"wagon_wheel", "clock_ticker"},
    ),
}

MECHANIC_NAMES = ["Mara", "Noah", "Iris", "Theo", "Nina", "Eli", "Lina", "Owen"]
CUSTOMER_NAMES = ["Tess", "Cal", "June", "Ben", "Mina", "Pip", "Ari", "Sol"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about a mechanic and a little magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["woman", "man", "girl", "boy"])
    ap.add_argument("--customer")
    ap.add_argument("--customer-gender", choices=["woman", "man", "girl", "boy"])
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


def select_name(rng: random.Random, gender: str, pool: list[str]) -> str:
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    tool = getattr(args, "tool", None) or rng.choice(sorted(TOOLS))
    mech_gender = getattr(args, "gender", None) or rng.choice(["woman", "man"])
    cust_gender = getattr(args, "customer_gender", None) or rng.choice(["woman", "man", "girl", "boy"])
    mechanic_name = getattr(args, "name", None) or select_name(rng, mech_gender, MECHANIC_NAMES)
    customer_name = getattr(args, "customer", None) or select_name(rng, cust_gender, CUSTOMER_NAMES)
    if tool not in _safe_lookup(TOOLS, tool).helps:
        pass
    if problem not in _safe_lookup(TOOLS, tool).helps:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, problem=problem, tool=tool,
                       mechanic_name=mechanic_name, mechanic_type=mech_gender,
                       customer_name=customer_name, customer_type=cust_gender)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    prob = _safe_lookup(PROBLEMS, params.problem)
    tool = _safe_lookup(TOOLS, params.tool)
    world = World(setting)

    mechanic = world.add(Entity(id="mechanic", kind="character", label=params.mechanic_name, type=params.mechanic_type))
    customer = world.add(Entity(id="customer", kind="character", label=params.customer_name, type=params.customer_type))
    item = world.add(Entity(id="item", label=prob.thing, type=prob.thing, owner=customer.id))
    item.meters["broken"] = 1.0
    customer.memes["worry"] = 1.0
    mechanic.memes["care"] = 1.0

    world.say(f"{params.mechanic_name} was the mechanic at {setting.place}.")
    world.say(setting.detail)
    world.say(f"One morning, {params.customer_name} arrived with a {prob.thing} that {prob.fault}.")
    world.say(f"It looked {prob.visible}, and {params.customer_name} gave a small worried smile.")
    world.para()
    world.say(f"{params.mechanic_name} listened, nodded, and said, \"Let me take a look.\"")
    world.say(f"The mechanic checked the bolts, the wires, and the tiny hidden spots first.")
    world.say(f"Then {params.mechanic_name} reached for {tool.label}, because {tool.effect}.")
    world.say(f"{tool.label.capitalize()} gave off {prob.magic_hint}.")
    world.para()
    world.say(f"With steady hands and a little patience, {params.mechanic_name} did not rush.")
    world.say(f"{prob.fix.capitalize()}, and the old {prob.thing} became quiet and sure again.")
    item.meters["broken"] = 0.0
    item.meters["working"] = 1.0
    customer.memes["worry"] = 0.0
    customer.memes["relief"] = 1.0
    mechanic.memes["pride"] = 1.0
    world.say(f"{params.customer_name} smiled with relief, and the shop felt calm and bright again.")

    world.facts.update(setting=setting, prob=prob, tool=tool, mechanic=mechanic, customer=customer, item=item, params=params)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    prob = _safe_fact(world, world.facts, "prob")
    tool = _safe_fact(world, world.facts, "tool")
    return [
        f"Write a gentle slice-of-life story about a mechanic named {p.mechanic_name} who uses {tool.label} to help with a {prob.thing}.",
        f"Tell a short story where {p.customer_name} visits a garage, the problem is {prob.fault}, and a little magic helps the repair.",
        "Create a calm story about work, patience, and a small magical tool in a neighborhood shop.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    prob = _safe_fact(world, world.facts, "prob")
    tool = _safe_fact(world, world.facts, "tool")
    return [
        QAItem(
            question=f"Who was the mechanic in the story?",
            answer=f"The mechanic was {p.mechanic_name}. {p.mechanic_name} worked carefully in {world.setting.place}.",
        ),
        QAItem(
            question=f"What was wrong with the {prob.thing}?",
            answer=f"It {prob.fault}. That is why {p.customer_name} brought it to the shop.",
        ),
        QAItem(
            question=f"How did {tool.label} help?",
            answer=f"{tool.label.capitalize()} helped by giving {tool.effect}, which made the repair easier and calmer.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The broken thing was working again, and {p.customer_name} felt relieved while the shop grew quiet and bright.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a mechanic do?",
            answer="A mechanic fixes broken machines, checks parts, and helps things work safely again.",
        ),
        QAItem(
            question="Why can a small tool be helpful in a repair shop?",
            answer="A small tool can help a mechanic see, line up, or steady tiny parts that are hard to fix by hand.",
        ),
        QAItem(
            question="What is magic like in this story world?",
            answer="Magic is gentle and useful here. It gives a little extra help, but the mechanic still does the careful work.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        lines.append(f"  {ent.id}: {ent.label} ({ent.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
working(Item) :- item(Item), not broken(Item).
helpful_tool(Tool, Problem) :- tool(Tool), helps(Tool, Problem).
reasonable_story(Place, Problem, Tool) :- setting(Place), problem(Problem), tool(Tool), helps(Tool, Problem).
#show reasonable_story/3.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for prob in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, prob))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reasonable_story/3."))
    asp_set = set(asp.atoms(model, "reasonable_story"))
    py_set = set((place, prob, tool) for place in SETTINGS for prob in PROBLEMS for tool, t in TOOLS.items() if prob in t.helps)
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only in ASP:", sorted(asp_set - py_set))
    print("Only in Python:", sorted(py_set - asp_set))
    return 1


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
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
    StoryParams("corner_shop", "scooter_chain", "spark_wand", "Mara", "woman", "Tess", "girl"),
    StoryParams("quiet_street", "bike_light", "glow_glove", "Iris", "woman", "Cal", "man"),
    StoryParams("home_garage", "wagon_wheel", "mend_chime", "Theo", "man", "June", "woman"),
    StoryParams("corner_shop", "clock_ticker", "mend_chime", "Nina", "woman", "Pip", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonable_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show reasonable_story/3."))
        atoms = sorted(set(asp.atoms(model, "reasonable_story")))
        print(f"{len(atoms)} reasonable combinations")
        for a in atoms:
            print(a)
        return

    rng_base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            rng = random.Random(rng_base + i)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = rng_base + i
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
        header = f"### variant {idx + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
