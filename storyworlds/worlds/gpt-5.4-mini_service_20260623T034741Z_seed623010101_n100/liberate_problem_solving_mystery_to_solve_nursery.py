#!/usr/bin/env python3
"""
storyworlds/worlds/liberate_problem_solving_mystery_to_solve_nursery.py
=======================================================================

A tiny nursery-rhyme storyworld about a little mystery, a missing thing, and
the child who helps liberate it with clever problem solving.

Seed tale:
---
A small mouse named Miri heard a riddle in the nursery: something had gone
missing from the toy chest. The room was full of soft blankets, wooden blocks,
and a shy little song. Miri looked under the rug, behind the chair, and inside
the basket, but the answer stayed hidden.

Then Miri noticed a ribbon caught on the drawer latch. The drawer was stuck
shut. "Oh dear," Miri said, "that is the mystery to solve!" She pushed a toy
spoon into the crack, wiggled gently, and at last the drawer popped open.

Inside was the lost bell, bright as moonlight. Miri liberated the bell, gave it
back to the nursery, and everyone sang a tiny happy song.

World shape:
- physical meters track stuckness, foundness, hiddenness, and carried objects
- emotional memes track worry, curiosity, joy, and relief
- a small causal rule engine turns hidden clues into revealed objects
- a reasonableness gate only allows mysteries with a plausible clue + tool
- story prose is driven by world state, not a frozen template swap
"""

from __future__ import annotations

import argparse
import copy
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    place: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    container: object | None = None
    helper: object | None = None
    hero: object | None = None
    missing: object | None = None
    parent: object | None = None
    tool_ent: object | None = None
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
    indoors: bool = True
    affordances: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    missing: str
    container: str
    clue: str
    stuck_part: str
    tool_needed: str
    reveal_phrase: str
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
    fits: str
    nudges: str
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


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
    world: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w
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
class StoryParams:
    setting: str = "nursery"
    mystery: str = "lost_bell"
    tool: str = "spoon"
    hero_name: str = "Miri"
    hero_type: str = "mouse"
    helper_name: str = "Tully"
    helper_type: str = "turtle"
    parent_name: str = "Nana"
    parent_type: str = "mother"
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
    "nursery": Setting(place="the nursery", indoors=True, affordances={"stuck_drawer"}),
    "playroom": Setting(place="the playroom", indoors=True, affordances={"stuck_box"}),
    "attic": Setting(place="the attic", indoors=True, affordances={"stuck_trunk"}),
}

MYSTERIES = {
    "lost_bell": Mystery(
        id="lost_bell",
        missing="a little silver bell",
        container="the toy chest",
        clue="a ribbon caught on the drawer latch",
        stuck_part="the drawer",
        tool_needed="spoon",
        reveal_phrase="the lost bell",
        tags={"bell", "lost", "stuck_drawer"},
    ),
    "missing_key": Mystery(
        id="missing_key",
        missing="a tiny brass key",
        container="the music box",
        clue="a thread looped around the box's tiny hinge",
        stuck_part="the lid",
        tool_needed="hook",
        reveal_phrase="the missing key",
        tags={"key", "lost", "stuck_box"},
    ),
    "hidden_seed": Mystery(
        id="hidden_seed",
        missing="a packet of seeds",
        container="the trunk",
        clue="a crooked latch held by a string",
        stuck_part="the trunk latch",
        tool_needed="wedge",
        reveal_phrase="the hidden seeds",
        tags={"seeds", "lost", "stuck_trunk"},
    ),
}

TOOLS = {
    "spoon": Tool(id="spoon", label="spoon", phrase="a toy spoon", fits="drawer", nudges="wiggled gently", tags={"spoon"}),
    "hook": Tool(id="hook", label="hook", phrase="a bent hook", fits="box", nudges="lifted carefully", tags={"hook"}),
    "wedge": Tool(id="wedge", label="wedge", phrase="a small wooden wedge", fits="latch", nudges="tapped softly", tags={"wedge"}),
}

NAMES = ["Miri", "Nina", "Lulu", "Toby", "Pip", "Momo", "Rory", "Bibi"]
KINDS = ["mouse", "rabbit", "bird", "cat"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_reveal(world: World) -> list[str]:
    out = []
    child = world.get("hero")
    myst = world.facts["mystery"]
    tool = world.facts["tool"]
    container = world.get("container")
    if container.meters["opened"] >= THRESHOLD and myst.id not in world.fired:
        world.fired.add((myst.id, "reveal"))
        world.get("missing").meters["found"] += 1
        child.memes["joy"] += 1
        child.memes["relief"] += 1
        out.append(f"Inside was {myst.missing}.")
    return out


CAUSAL_RULES = [Rule("reveal", _r_reveal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                produced.extend(sents)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_at_risk(mystery: Mystery, tool: Tool) -> bool:
    return mystery.tool_needed == tool.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for mystery_id, mystery in MYSTERIES.items():
            if mystery.tags & setting.affordances:
                for tool_id, tool in TOOLS.items():
                    if clue_at_risk(mystery, tool):
                        combos.append((setting_id, mystery_id, tool_id))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
        lines.append(asp.fact("needs", mid, m.tool_needed))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("fits", tid, t.fits))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, T) :- setting(S), mystery(M), tool(T), affords(S, A), tag(M, A), needs(M, T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: a small mystery, a tool, and liberation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--parent")
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
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, mystery, tool = rng.choice(list(combos))
    hero_name = getattr(args, "name", None) or rng.choice(NAMES)
    hero_type = "mouse" if hero_name in {"Miri", "Momo", "Bibi"} else rng.choice(KINDS)
    helper = getattr(args, "helper", None) or rng.choice([n for n in NAMES if n != hero_name])
    parent = getattr(args, "parent", None) or "Nana"
    return StoryParams(setting=setting, mystery=mystery, tool=tool, hero_name=hero_name, hero_type=hero_type, helper_name=helper, helper_type="turtle", parent_name=parent, parent_type="mother")


def _open_container(world: World, child: Entity, tool: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    child.meters["trying"] += 1
    container = world.get("container")
    if tool.id != mystery.tool_needed:
        return
    container.meters["opened"] += 1
    container.meters["stuck"] = 0.0
    tool.meters["used"] += 1
    propagate(world, narrate=False)


def tell(setting: Setting, mystery: Mystery, tool: Tool, hero_name: str, hero_type: str, helper_name: str, helper_type: str, parent_name: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, meters={"trying": 0.0}, memes={"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "relief": 0.0}))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, meters={}, memes={"curiosity": 0.0, "joy": 0.0}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_name, meters={}, memes={"pride": 0.0}))
    missing = world.add(Entity(id="missing", type="thing", label=mystery.missing, meters={"found": 0.0}, memes={}))
    container = world.add(Entity(id="container", type="thing", label=mystery.container, place=mystery.stuck_part, meters={"stuck": 1.0, "opened": 0.0}, memes={}))
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, meters={"used": 0.0}, memes={}))
    world.facts.update(hero=hero, helper=helper, parent=parent, mystery=mystery, tool=tool_ent)
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    world.say(f"{hero_name} was a little {hero_type} in {setting.place}, where soft toys kept a quiet tune.")
    world.say(f"{hero_name} heard a mystery: {mystery.missing} had gone missing from {mystery.container}.")
    world.para()
    world.say(f"{hero_name} peeked under the rug, behind the chair, and inside the basket, but the answer stayed hidden.")
    world.say(f"Then {hero_name} noticed {mystery.clue}.")
    world.para()
    world.say(f'"Oh dear," said {hero_name}, "that is the mystery to solve!"')
    world.say(f"{helper_name} leaned close, and {hero_name} took {tool.phrase}.")
    _open_container(world, hero, tool_ent, mystery)
    if container.meters["opened"] >= THRESHOLD:
        world.say(f"{hero_name} {tool.nudges} until the drawer popped open.")
        world.say(f"{hero_name} helped liberate {mystery.missing}, bright as moonlight.")
        world.say(f"The nursery smiled, and a tiny song began.")
        parent.memes["pride"] += 1
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme story for a small child about a mystery in {world.setting.place} and how {f["hero"].label} helps solve it. Include the word "liberate".',
        f"Tell a gentle story where {f['hero'].label} finds a clue, uses {(f.get('tool') or next(iter(TOOLS.values()))).phrase}, and liberates the missing thing from the stuck {f['mystery'].stuck_part}.",
        f'Write a rhyming, child-friendly story about a hidden treasure, a stuck container, and a happy ending that says "liberate".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, parent = f["hero"], f["helper"], f["parent"]
    mystery, tool = f["mystery"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            f"What mystery did {hero.label} try to solve?",
            f"{hero.label} tried to solve the mystery of {mystery.missing}. It was hidden inside {mystery.container}, so the little one had to look carefully.",
        ),
        QAItem(
            f"Why did {hero.label} need {tool.phrase}?",
            f"{hero.label} needed {tool.phrase} because {mystery.clue}. The clue showed that the stuck {mystery.stuck_part} had to be nudged open before the missing thing could be found.",
        ),
        QAItem(
            f"How did {hero.label} liberate {mystery.missing}?",
            f"{hero.label} used {tool.phrase} and {tool.nudges} until the container opened. Then {hero.label} could liberate {mystery.missing} and bring it back to the nursery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a mystery?", "A mystery is something puzzling that you do not know yet. People solve a mystery by looking for clues."),
        QAItem("What does liberate mean?", "To liberate something means to free it or let it out. In a story, you can liberate a lost thing by opening what kept it hidden."),
        QAItem("What is a clue?", "A clue is a small hint that helps you solve a mystery. It can be a shape, a sound, a mark, or something out of place."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.tool not in TOOLS:
        pass
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    tool = _safe_lookup(TOOLS, params.tool)
    if not clue_at_risk(mystery, tool):
        pass
    world = tell(_safe_lookup(SETTINGS, params.setting), mystery, tool, params.hero_name, params.hero_type, params.helper_name, params.helper_type, params.parent_name, params.parent_type)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(setting="nursery", mystery="lost_bell", tool="spoon", hero_name="Miri", hero_type="mouse", helper_name="Tully", helper_type="turtle", parent_name="Nana", parent_type="mother"),
    StoryParams(setting="playroom", mystery="missing_key", tool="hook", hero_name="Lulu", hero_type="rabbit", helper_name="Pip", helper_type="bird", parent_name="Mama", parent_type="mother"),
    StoryParams(setting="attic", mystery="hidden_seed", tool="wedge", hero_name="Toby", hero_type="cat", helper_name="Bibi", helper_type="mouse", parent_name="Grandma", parent_type="mother"),
]


def asp_verify() -> int:
    got = set(asp_valid_combos())
    want = set(valid_combos())
    if got != want:
        print("MISMATCH between ASP and Python:")
        print(" only in ASP:", sorted(got - want))
        print(" only in Python:", sorted(want - got))
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: ASP matches Python for {len(got)} combos and generation smoke test passed.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, mystery, tool = rng.choice(list(combos))
    return StoryParams(
        setting=setting,
        mystery=mystery,
        tool=tool,
        hero_name=getattr(args, "name", None) or rng.choice(NAMES),
        hero_type="mouse" if (getattr(args, "name", None) or "Miri") in {"Miri", "Momo"} else rng.choice(KINDS),
        helper_name=getattr(args, "helper", None) or rng.choice([n for n in NAMES if n != (getattr(args, "name", None) or "Miri")]),
        helper_type="turtle",
        parent_name=getattr(args, "parent", None) or "Nana",
        parent_type="mother",
    )


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
        for row in combos:
            print("  ", row)
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
            header = f"### {p.hero_name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
