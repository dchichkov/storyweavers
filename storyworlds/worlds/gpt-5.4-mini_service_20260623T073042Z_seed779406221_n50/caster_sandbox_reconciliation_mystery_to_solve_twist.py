#!/usr/bin/env python3
"""
storyworlds/worlds/caster_sandbox_reconciliation_mystery_to_solve_twist.py
==========================================================================

A small slice-of-life storyworld set in a sandbox, built around a caster
tool, a little mystery to solve, a twist, and a reconciliation ending.

Premise:
- A child is playing in a sandbox and wants to make a tiny sand castle.
- The sand keeps collapsing, and the child suspects the caster is broken.
- The twist is that the caster is not broken at all; it is clogged with damp
  sand, and a simple cleanup fixes it.
- The ending is reconciliation: the child and helper work together, the sand
  settles into a sturdy shape, and everyone feels better.

The world uses typed entities with physical meters and emotional memes,
forward-chaining rules, and an inline ASP twin for validity checks.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    afford: set[str] = field(default_factory=set)
    world: object | None = None
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
class Caster:
    id: str
    label: str
    phrase: str
    clog_kind: str
    fix: str
    tool_kind: str = "caster"
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
class SandScene:
    id: str
    goal: str
    collapse: str
    clue: str
    ending_image: str
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
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        if world.facts.get("cast_attempt") and ("clog",) not in world.fired:
            world.fired.add(("clog",))
            caster = world.get("caster")
            if caster.meters["clogged"] >= THRESHOLD:
                caster.memes["frustration"] += 1
                out.append("The caster still moved, but only a little, as if something inside it was packed tight.")
                changed = True
        if world.facts.get("cleaned") and ("fix",) not in world.fired:
            world.fired.add(("fix",))
            caster = world.get("caster")
            caster.meters["clogged"] = 0
            caster.memes["relief"] += 1
            out.append("Once the clog was brushed away, the caster worked again.")
            changed = True
        if world.facts.get("reconciled") and ("reconcile",) not in world.fired:
            world.fired.add(("reconcile",))
            for eid in ("child", "helper"):
                world.get(eid).memes["warmth"] += 1
                world.get(eid).memes["trust"] += 1
            out.append("After that, they felt like a team again.")
            changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_clog(world: World) -> bool:
    sim = world.copy()
    return sim.get("caster").meters["clogged"] >= THRESHOLD


def tell(scene: SandScene, caster: Caster, child_name: str, helper_name: str, seed: Optional[int] = None) -> World:
    world = World(Setting(place="the sandbox", afford={"build", "sift", "clean"}))
    child = world.add(Entity(id="child", kind="character", type="boy" if child_name in BOY_NAMES else "girl", label=child_name))
    helper = world.add(Entity(id="helper", kind="character", type="girl" if helper_name in GIRL_NAMES else "boy", label=helper_name, role="helper"))
    tool = world.add(Entity(id="caster", type="tool", label=caster.label))
    tool.meters["clogged"] = 0.0
    tool.memes["helpfulness"] = 1.0
    child.meters["sand"] = 0.0
    helper.meters["sand"] = 0.0
    child.memes["curiosity"] = 1.0
    helper.memes["patience"] = 1.0

    world.say(f"{child.label_word} and {helper.label_word} were playing in {world.setting.place}.")
    world.say(f"They wanted to use {caster.phrase} to make a little sand castle.")
    world.para()
    world.say(f"But the sand kept doing the same annoying thing: {scene.collapse}.")
    world.say(f"{child.label_word.capitalize()} peered at the {caster.label} and frowned. {scene.clue}")

    world.facts["cast_attempt"] = True
    tool.meters["clogged"] = 1.0
    child.memes["mystery"] += 1
    propagate(world)

    world.para()
    if predict_clog(world):
        world.say(f"{helper.label_word.capitalize()} looked closer and found the twist: the {caster.label} was not broken.")
        world.say(f"It was just clogged with damp sand, so they sat down together and cleaned it.")
        world.facts["cleaned"] = True
        propagate(world)
        world.facts["reconciled"] = True
        propagate(world)
        world.say(f"Then the {caster.label} poured out smooth sand, and the castle finally stayed up.")
        world.say(f"{scene.ending_image.capitalize()}")
    else:
        world.say(f"That would not make sense here, so the day would need a different story.")
    world.facts.update(child=child, helper=helper, caster=tool, scene=scene, caster_cfg=caster)
    return world


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    h = world.facts["helper"]
    caster = world.facts["caster_cfg"]
    scene = world.facts["scene"]
    return [
        QAItem(
            question=f"What were {c.label_word} and {h.label_word} trying to do in the sandbox?",
            answer=f"They were trying to use {caster.phrase} to build a little sand castle in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {c.label_word} think there was a mystery?",
            answer=f"The sand kept collapsing, so {c.label_word} thought the {caster.label} might be broken.",
        ),
        QAItem(
            question=f"What was the twist about the {caster.label}?",
            answer=f"The twist was that it was not broken at all; it was clogged with damp sand.",
        ),
        QAItem(
            question=f"How did the story end after they solved the mystery?",
            answer=f"They cleaned the {caster.label}, worked together again, and the castle stayed up at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sandbox?",
            answer="A sandbox is a place filled with sand where children can scoop, pour, and build things.",
        ),
        QAItem(
            question="What does it mean when something is clogged?",
            answer="If something is clogged, it is blocked by packed-up stuff and cannot work as smoothly as it should.",
        ),
        QAItem(
            question="Why can damp sand be tricky?",
            answer="Damp sand can stick together and block small tools, which makes building feel frustrating.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    h = world.facts["helper"]
    caster = world.facts["caster_cfg"]
    scene = world.facts["scene"]
    return [
        f"Write a slice-of-life sandbox story where {c.label_word} and {h.label_word} try to use {caster.phrase} to build {scene.goal}.",
        f"Tell a gentle mystery-to-solve story in {world.setting.place} where the {caster.label} seems broken but turns out to have a simple problem.",
        f"Write a child-facing story with a twist and reconciliation ending about a clogged {caster.label} and a sand castle that finally stands.",
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


SETTINGS = {
    "sandbox": Setting(place="the sandbox", afford={"build", "sift", "clean"}),
}

CASTERS = {
    "cup_caster": Caster(id="cup_caster", label="plastic caster cup", phrase="a little plastic caster cup", clog_kind="sand", fix="shake out the sand"),
    "tube_caster": Caster(id="tube_caster", label="narrow caster tube", phrase="a narrow caster tube", clog_kind="sand", fix="tap it clear"),
}

SCENES = {
    "castle": SandScene(id="castle", goal="a sand castle", collapse="the walls slid down again", clue="Maybe the caster was packed with wet sand.", ending_image="The little castle stood in a neat, sunny lump of sand"),
    "tower": SandScene(id="tower", goal="a tall tower", collapse="the tower slumped every time", clue="Maybe the opening was blocked with sticky sand.", ending_image="The tower rose straight and tidy beside a smooth bucket line"),
}

GIRL_NAMES = ["Mia", "Lena", "Nora", "Ava", "June"]
BOY_NAMES = ["Ben", "Leo", "Owen", "Finn", "Theo"]

def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, sc) for s in SETTINGS for c in CASTERS for sc in SCENES]

@dataclass
class StoryParams:
    setting: str
    caster: str
    scene: str
    child_name: str
    helper_name: str
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


ASP_RULES = r"""
setting(sandbox).
caster(cup_caster). caster(tube_caster).
scene(castle). scene(tower).
valid(S,C,SC) :- setting(S), caster(C), scene(SC).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "sandbox")]
    for cid in CASTERS:
        lines.append(asp.fact("caster", cid))
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Sandbox slice-of-life storyworld with a caster mystery, twist, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--caster", choices=CASTERS)
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--name")
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
              and (getattr(args, "caster", None) is None or c[1] == getattr(args, "caster", None))
              and (getattr(args, "scene", None) is None or c[2] == getattr(args, "scene", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, caster, scene = rng.choice(list(combos))
    child_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child_name])
    return StoryParams(setting=setting, caster=caster, scene=scene, child_name=child_name, helper_name=helper_name)

def generate(params: StoryParams) -> StorySample:
    scene = _safe_lookup(SCENES, params.scene)
    caster = _safe_lookup(CASTERS, params.caster)
    world = World(_safe_lookup(SETTINGS, params.setting))
    child = world.add(Entity(id="child", kind="character", type="girl" if params.child_name in GIRL_NAMES else "boy", label=params.child_name))
    helper = world.add(Entity(id="helper", kind="character", type="girl" if params.helper_name in GIRL_NAMES else "boy", label=params.helper_name, role="helper"))
    world.add(Entity(id="caster", type="tool", label=caster.label))
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["caster_cfg"] = caster
    world.facts["scene"] = scene
    world.say(f"{child.label_word} and {helper.label_word} were in {world.setting.place} on an ordinary day.")
    world.say(f"They wanted to use {caster.phrase} to make {scene.goal}.")
    world.para()
    world.say(f"But {scene.collapse}.")
    world.say(f"{scene.clue}")
    world.facts["mystery"] = True
    world.get("caster").meters["clogged"] = 1.0
    propagate(world)
    world.para()
    world.say(f"The twist was simple: the {caster.label} was clogged, not broken.")
    world.say(f"They cleaned it together, and the problem became a small shared job instead of a fight.")
    world.facts["reconciled"] = True
    propagate(world)
    world.para()
    world.say(f"At the end, {scene.ending_image}.")
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

def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(c)
        return
    base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for s in [StoryParams(s, c, sc, "Mia", "Ben") for s, c, sc in valid_combos()]:
            samples.append(generate(s))
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(base + i))
            p.seed = base + i
            samples.append(generate(p))
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i+1}")
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
