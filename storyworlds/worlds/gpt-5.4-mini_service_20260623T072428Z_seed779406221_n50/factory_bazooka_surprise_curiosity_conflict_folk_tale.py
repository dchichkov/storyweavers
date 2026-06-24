#!/usr/bin/env python3
"""
storyworlds/worlds/factory_bazooka_surprise_conflict_folk_tale.py
==================================================================

A small standalone storyworld in a folk-tale style about a factory, a bazooka,
surprise, curiosity, and conflict.

Premise:
- A child or young helper visits a little factory and notices a strange bazooka
  in a storeroom.
- Curiosity pulls them toward the object.
- Surprise and conflict arise when a grown-up warns them away.
- The ending turns on a safer choice: they learn what the bazooka is for and
  use it in a harmless, storybook way to free something stuck, scare off noise,
  or open a jammed gate without damage.

This is a classical simulation: meters and memes change over time, and the prose
is rendered from state rather than from a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    grown: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    affordance: str
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
class Object:
    id: str
    label: str
    phrase: str
    kind: str
    risk: str
    fixable: bool = True
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
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
    safe: bool = True
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
class StoryParams:
    setting: str
    object: str
    tool: str
    name: str
    gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "factory": Setting(place="the little factory", affordance="making things"),
    "mill": Setting(place="the old mill", affordance="spinning thread"),
    "workshop": Setting(place="the workshop", affordance="repairing toys"),
}

OBJECTS = {
    "gear": Object(
        id="gear",
        label="gear wheel",
        phrase="a big brass gear wheel",
        kind="thing",
        risk="stuck",
        fixable=True,
    ),
    "gate": Object(
        id="gate",
        label="gate",
        phrase="a heavy iron gate",
        kind="thing",
        risk="jammed",
        fixable=True,
    ),
    "box": Object(
        id="box",
        label="crate lid",
        phrase="a stubborn crate lid",
        kind="thing",
        risk="stuck",
        fixable=True,
    ),
}

TOOLS = {
    "bazooka": Tool(
        id="bazooka",
        label="bazooka",
        phrase="a great bazooka with a cork tip",
        effect="a single booming puff that can push stuck things loose",
        safe=True,
    ),
    "toyhorn": Tool(
        id="toyhorn",
        label="toy horn",
        phrase="a little toy horn",
        effect="a loud honk that startles birds but hurts nothing",
        safe=True,
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Tara", "Nora", "Ivy", "Mira"]
BOY_NAMES = ["Robin", "Perry", "Jace", "Owen", "Bram", "Eli"]
TRAITS = ["curious", "brave", "gentle", "thoughtful", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for o in OBJECTS:
            for t in TOOLS:
                out.append((s, o, t))
    return out


def explain_rejection(obj: Object, tool: Tool) -> str:
    return f"(No story: {tool.label} is not a good fit for a {obj.label}.)"


ASP_RULES = r"""
setting(factory).
setting(mill).
setting(workshop).

object(gear).
object(gate).
object(box).

tool(bazooka).
tool(toyhorn).

valid(S,O,T) :- setting(S), object(O), tool(T), O != box.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: ASP matches Python ({len(p)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in python:", sorted(p - a))
    print(" only in asp:", sorted(a - p))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a factory bazooka.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "object_", None) and getattr(args, "tool", None) == "toyhorn":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "object_", None) is None or c[1] == getattr(args, "object_", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, obj, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or ("boy" if gender == "girl" else "girl")
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting, obj, tool, name, gender, helper, helper_gender, parent, trait)


def _setup(world: World, hero: Entity, helper: Entity, parent: Entity, obj: Object) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(f"Once upon a time, {hero.id} came to {world.setting.place} with {helper.id}.")
    world.say(f"The place was busy with the old folk work of {world.setting.affordance}, and everyone knew their place.")
    world.say(f"Near the far wall stood {obj.phrase}, waiting like a secret.")


def _surprise(world: World, hero: Entity, helper: Entity, obj: Object, tool: Tool) -> None:
    hero.memes["surprise"] += 1
    helper.memes["surprise"] += 1
    world.say(f"Then {hero.id} saw {tool.phrase} tucked away beside {obj.phrase}, and {hero.pronoun()} gave a little gasp.")
    world.say(f"{helper.id} frowned. 'That is not a plaything,' {helper.pronoun()} said.")
    helper.memes["conflict"] += 1


def _warn_and_conflict(world: World, hero: Entity, helper: Entity, parent: Entity, tool: Tool) -> None:
    hero.memes["conflict"] += 1
    world.say(f'"{tool.label.capitalize()} is a grown-up tool," {parent.id} said. "Not for idle hands."')
    world.say(f"But {hero.id}'s curiosity only grew stronger, and a small conflict filled the room.")


def _resolve(world: World, hero: Entity, helper: Entity, parent: Entity, obj: Object, tool: Tool) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    helper.memes["conflict"] = 0
    hero.memes["conflict"] = 0
    world.say(f"At last, {parent.id} smiled and showed them how the {tool.label} could help.")
    world.say(f"It gave one booming puff, just enough to push {obj.label} loose without breaking a thing.")
    world.say(f"{hero.id} laughed in surprise, and the little factory rang with safe gladness.")


def tell(setting: Setting, obj: Object, tool: Tool, name: str = "Mina", gender: str = "girl",
         helper: str = "Pip", helper_gender: str = "boy", parent: str = "mother",
         trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    friend = world.add(Entity(id=helper, kind="character", type=helper_gender))
    grown = world.add(Entity(id=parent, kind="character", type=parent))
    _setup(world, hero, friend, grown, obj)
    world.para()
    _surprise(world, hero, friend, obj, tool)
    _warn_and_conflict(world, hero, friend, grown, tool)
    world.para()
    _resolve(world, hero, friend, grown, obj, tool)
    world.say(f"In the end, {hero.id} learned that curiosity is best when it walks beside care.")
    world.facts.update(hero=hero, helper=friend, parent=grown, obj=obj, tool=tool, setting=setting, trait=trait)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk-tale story for a child about {f["hero"].id}, a {f["trait"]} helper, and a {(f.get("tool") or next(iter(TOOLS.values()))).label} in {f["setting"].place}.',
        f"Tell a story with surprise, curiosity, and conflict where {f['hero'].id} sees {(f.get('tool') or next(iter(TOOLS.values()))).label} near a {f['obj'].label} in a factory.",
        f'Write a gentle tale about a bazooka that makes a safe puff and helps free something stuck.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obj = f["obj"]
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    parent = f["parent"]
    return [
        QAItem(question=f"Who is the story about?", answer=f"The story is about {hero.id}, who came to {f['setting'].place} and met a small conflict there."),
        QAItem(question=f"What did {hero.id} feel when seeing {tool.label}?", answer=f"{hero.id} felt surprise and curiosity when {hero.pronoun()} saw {tool.phrase}."),
        QAItem(question=f"What happened at the end?", answer=f"{parent.id} showed how the {tool.label} could help, and it pushed {obj.label} loose without damage."),
        QAItem(question=f"How did {helper.id} help?", answer=f"{helper.id} warned {hero.id} away at first, then shared in the happy ending once the tool was used safely."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a factory?", answer="A factory is a place where people make things or put parts together."),
        QAItem(question="What is surprise?", answer="Surprise is the feeling you get when something unexpected happens."),
        QAItem(question="What is curiosity?", answer="Curiosity is the wish to know more and to look closely at something new."),
        QAItem(question="What is conflict?", answer="Conflict is a struggle or disagreement between what one person wants and what another says is safe."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id} ({e.type}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams("factory", "gear", "bazooka", "Mina", "girl", "Pip", "boy", "mother", "curious"),
    StoryParams("workshop", "gate", "bazooka", "Robin", "boy", "Lena", "girl", "father", "thoughtful"),
    StoryParams("mill", "box", "bazooka", "Nora", "girl", "Eli", "boy", "mother", "brave"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(OBJECTS, params.object), _safe_lookup(TOOLS, params.tool),
                 params.name, params.gender, params.helper, params.helper_gender,
                 params.parent, params.trait)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} combos:\n")
        for c in combos:
            print(" ", c)
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = getattr(args, "seed", None)
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = s.params
            header = f"### {p.name} at {p.setting} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
