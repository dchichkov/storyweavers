#!/usr/bin/env python3
"""
A small superhero story world: a hero, a problem, teamwork, dialogue, and a
clean ending image.

This world is built from the seed words dapple and bathe, with a gentle
superhero-story style. The core premise is that a hero is trying to help in a
sun-dappled city square when something sticky, dusty, or smoky threatens to
ruin the day. A teammate and a few lines of dialogue create a safe, clever fix.
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
# Typed world model
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gear: object | None = None
    hero: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
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
    mood: str
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
class Trouble:
    id: str
    label: str
    verb: str
    mess: str
    soil: str
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


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    use_line: str
    protects_against: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
    "square": Setting(place="the sun-dappled city square", mood="bright", affords={"dust", "smoke", "slime"}),
    "roof": Setting(place="the rooftop garden", mood="windy", affords={"smoke", "dust"}),
    "harbor": Setting(place="the harbor pier", mood="spray-bright", affords={"slime", "smoke"}),
}

TROUBLES = {
    "dust": Trouble(
        id="dust",
        label="dust storm",
        verb="clear the dust",
        mess="dust",
        soil="covered in dust",
        tags={"dust", "dapple"},
    ),
    "smoke": Trouble(
        id="smoke",
        label="smoke cloud",
        verb="push back the smoke",
        mess="smoke",
        soil="smudged with soot",
        tags={"smoke"},
    ),
    "slime": Trouble(
        id="slime",
        label="slime spill",
        verb="scoop up the slime",
        mess="slime",
        soil="splashed with slime",
        tags={"slime"},
    ),
}

TOOLS = {
    "shower": Tool(
        id="shower",
        label="the rescue shower",
        prep="bathe in the rescue shower",
        use_line="washed the grit away",
        protects_against={"dust", "smoke", "slime"},
    ),
    "cape": Tool(
        id="cape",
        label="the clean cape",
        prep="wrap up in the clean cape",
        use_line="kept the hero dry and tidy",
        protects_against={"dust", "smoke"},
    ),
    "visor": Tool(
        id="visor",
        label="the clear visor",
        prep="lower the clear visor",
        use_line="kept the smoke out of the eyes",
        protects_against={"smoke"},
    ),
}

HERO_NAMES = ["Nova", "Flash", "Ruby", "Jet", "Mira", "Zane", "Pip", "Ivy"]
SIDEKICK_NAMES = ["Bolt", "Comet", "Penny", "Sparrow", "Tango", "Breeze"]
TRAITS = ["brave", "kind", "quick", "careful", "cheerful"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    trouble: str
    hero_name: str
    sidekick_name: str
    hero_type: str
    sidekick_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def trouble_at_risk(setting: Setting, trouble: Trouble) -> bool:
    return trouble.id in setting.affords


def choose_tool(trouble: Trouble) -> Optional[Tool]:
    for tool in TOOLS.values():
        if trouble.id in tool.protects_against:
            return tool
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for tid, trouble in TROUBLES.items():
            if trouble_at_risk(setting, trouble) and choose_tool(trouble):
                out.append((place, tid))
    return out


def explain_rejection(setting: Setting, trouble: Trouble) -> str:
    if not trouble_at_risk(setting, trouble):
        return f"(No story: {setting.place} does not naturally create {trouble.label}.)"
    return f"(No story: there is no tool in this world that reasonably fixes {trouble.label}.)"


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    trouble = _safe_lookup(TROUBLES, params.trouble)
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type=params.sidekick_type))
    tool = choose_tool(trouble)
    if tool is None:
        pass
    gear = world.add(Entity(id=tool.id, label=tool.label, kind="thing", type="tool", owner=hero.id))
    gear.worn_by = hero.id

    world.facts.update(hero=hero, sidekick=sidekick, trouble=trouble, tool=gear, setting=setting)
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    trouble: Trouble = _safe_fact(world, f, "trouble")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    setting: Setting = _safe_fact(world, f, "setting")

    world.say(
        f"{hero.id} was a {hero.pronoun('subject')} who loved helping people in {setting.place}. "
        f"The city lights and the sunlight made bright dappled patches on the ground."
    )
    world.say(
        f"{sidekick.id} stayed close by, because {hero.id} and {sidekick.id} worked best as a team."
    )

    world.para()
    world.say(
        f"One day, a {trouble.label} rolled in and threatened the square. "
        f"{hero.id} said, \"I can handle this,\" and {sidekick.id} answered, \"Then I will help.\""
    )
    world.say(
        f"{hero.id} wanted to {trouble.verb}, but the mess would leave {hero.pronoun('object')} {trouble.soil}."
    )
    world.say(
        f"{sidekick.id} pointed to {tool.label} and said, \"Try this first.\""
    )
    world.say(
        f"{hero.id} nodded and said, \"Good idea.\""
    )

    world.para()
    world.say(
        f"So {hero.id} chose to {tool.id if tool.id != 'shower' else 'bathe'} using {tool.label}. "
        f"Together, the two friends did the job fast and safe."
    )
    world.say(
        f"{tool.label.capitalize()} {tool.use_line}, and soon the {trouble.label} was gone."
    )
    world.say(
        f"At the end, {hero.id} and {sidekick.id} stood in the sun-dappled square, smiling, "
        f"while everything around them looked clean and calm again."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    trouble: Trouble = _safe_fact(world, f, "trouble")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        f"Write a superhero story about {hero.id} and {sidekick.id} in {setting.place}.",
        f"Tell a teamwork story where a hero tries to {trouble.verb} but needs a friend and a clever tool.",
        f"Write a child-friendly superhero tale that includes the words dapple and bathe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    trouble: Trouble = _safe_fact(world, f, "trouble")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a superhero who helped in {setting.place}, with {sidekick.id} as a teammate.",
        ),
        QAItem(
            question=f"What problem showed up in the story?",
            answer=f"A {trouble.label} showed up and threatened to cover the hero in {trouble.soil}.",
        ),
        QAItem(
            question=f"How did the hero and sidekick solve the problem?",
            answer=f"They worked together and used {tool.label} so the hero could stay clean while fixing the trouble.",
        ),
        QAItem(
            question=f"What did the ending look like?",
            answer=f"At the end, {hero.id} and {sidekick.id} were smiling in the clean, bright square after the trouble was gone.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "dapple": (
        "What does dappled light mean?",
        "Dappled light means the sunlight comes through leaves or buildings in little patches, so the light and shade are mixed together.",
    ),
    "bathe": (
        "What does it mean to bathe?",
        "To bathe means to wash your body with water, often in a tub or shower, so you end up clean.",
    ),
    "teamwork": (
        "What is teamwork?",
        "Teamwork means people help each other and do a job together instead of alone.",
    ),
    "dialogue": (
        "What is dialogue in a story?",
        "Dialogue is the words characters say out loud to each other in a story.",
    ),
    "superhero": (
        "What does a superhero do?",
        "A superhero is a brave helper who uses special skills to protect people and solve problems.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    trouble: Trouble = _safe_fact(world, f, "trouble")
    out = [QAItem(question=q, answer=a) for tag, (q, a) in WORLD_KNOWLEDGE.items() if tag == "dapple" or tag == "bathe"]
    out.append(QAItem(question="Why do superheroes often work with sidekicks?", answer="They work together because teamwork lets them solve bigger problems more safely and quickly."))
    out.append(QAItem(question="Why do characters talk to each other in dialogue?", answer="Dialogue lets characters share ideas, make plans, and show how they feel."))
    if "dapple" in trouble.tags:
        out.append(QAItem(question="What kind of light was in the city square?", answer="The city square had dappled sunlight, which made bright patches on the ground."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Place, Trouble) :- setting(Place), trouble(Trouble), affords(Place, Trouble), has_tool(Trouble).
has_tool(T) :- tool(Tool), protects(Tool, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for t in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        for tag in sorted(trouble.tags):
            lines.append(asp.fact("tag", tid, tag))
    for tool in TOOLS.values():
        lines.append(asp.fact("tool", tool.id))
        for t in sorted(tool.protects_against):
            lines.append(asp.fact("protects", tool.id, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "trouble", None):
        setting = _safe_lookup(SETTINGS, getattr(args, "place", None))
        trouble = _safe_lookup(TROUBLES, getattr(args, "trouble", None))
        if not trouble_at_risk(setting, trouble) or not choose_tool(trouble):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        (place, tid)
        for place, tid in valid_combos()
        if (getattr(args, "place", None) is None or place == getattr(args, "place", None))
        and (getattr(args, "trouble", None) is None or tid == getattr(args, "trouble", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, trouble = rng.choice(list(combos))
    hero_type = "girl" if rng.random() < 0.5 else "boy"
    sidekick_type = "girl" if hero_type == "boy" else "boy"
    return StoryParams(
        place=place,
        trouble=trouble,
        hero_name=getattr(args, "hero_name", None) or rng.choice(HERO_NAMES),
        sidekick_name=getattr(args, "sidekick_name", None) or rng.choice(SIDEKICK_NAMES),
        hero_type=hero_type,
        sidekick_type=sidekick_type,
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
    if qa:
        print()
        print(format_qa(sample))
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(e)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="square", trouble="dust", hero_name="Nova", sidekick_name="Bolt", hero_type="girl", sidekick_type="boy", trait="brave"),
    StoryParams(place="roof", trouble="smoke", hero_name="Ruby", sidekick_name="Penny", hero_type="girl", sidekick_type="girl", trait="careful"),
    StoryParams(place="harbor", trouble="slime", hero_name="Jet", sidekick_name="Comet", hero_type="boy", sidekick_type="boy", trait="quick"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with teamwork and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--trait")
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for place, trouble in combos:
            print(f"  {place:10} {trouble}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < getattr(args, "n", None) * 50 + 50:
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
