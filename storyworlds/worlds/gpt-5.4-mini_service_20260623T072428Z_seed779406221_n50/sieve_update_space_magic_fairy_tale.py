#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T072428Z_seed779406221_n50/sieve_update_space_magic_fairy_tale.py
===============================================================================================================

A small standalone fairy-tale storyworld about a mage, a sieve, an update,
and a space-crossing wish. The domain is built from the seed words:
"sieve", "update", and "space", with magic as the key feature and a fairy-tale
tone.

The premise:
- A child-friendly magical keeper owns a sieve that can strain stardust.
- A noisy update from the sky warns that the moon garden's gate is breaking.
- A space problem can be solved only by a careful magical update: shifting the
  sieve's charm, gathering shimmering pieces, and sending them through the
  right place.

World model:
- Entities have physical meters and emotional memes.
- The sieve may gather star-dust or leak it depending on enchantment.
- The space gate can be open, cracked, or bright.
- A magical update can repair the gate if the keeper has the right tool and
  enough starlight.

The stories are intended to read like tiny fairy tales with a clear beginning,
turn, and ending image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    enchanted: bool = False
    gate_state: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    gate: object | None = None
    helper: object | None = None
    hero: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen", "witch"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "wizard"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def name_word(self) -> str:
        return self.label or self.type
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
    sky: str
    wonder: str
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
class MagicTool:
    id: str
    label: str
    phrase: str
    use: str
    effect: str
    gathers: str
    supports: set[str] = field(default_factory=set)
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
class SpaceProblem:
    id: str
    label: str
    phrase: str
    state: str
    risk: str
    clue: str
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
class Update:
    id: str
    label: str
    phrase: str
    promise: str
    fix: str
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_leak(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.type != "sieve":
            continue
        if e.meters["magic"] < THRESHOLD:
            continue
        sig = ("leak", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["stardust"] += 1
        out.append("Stardust slipped through the sieve like silver rain.")
    return out


def _r_update(world: World) -> list[str]:
    out: list[str] = []
    keeper = world.entities.get("keeper")
    sieve = world.entities.get("sieve")
    gate = world.entities.get("gate")
    if not keeper or not sieve or not gate:
        return out
    if keeper.memes["hope"] < THRESHOLD or sieve.meters["stardust"] < THRESHOLD:
        return out
    sig = ("update", gate.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gate.gate_state = "bright"
    gate.meters["broken"] = 0
    out.append("The magical update mended the moon gate and made it shine again.")
    return out


def _r_space(world: World) -> list[str]:
    out: list[str] = []
    gate = world.entities.get("gate")
    if gate and gate.gate_state == "bright":
        sig = ("space", gate.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append("A soft path opened in space, and the stars made room for a wish.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_leak, _r_update, _r_space):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(tool: MagicTool, problem: SpaceProblem, update: Update) -> bool:
    return tool.supports and problem.id in update.tags and "space" in problem.tags


def choose_combo() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for tool_id, tool in TOOLS.items():
            for prob_id, prob in PROBLEMS.items():
                if reasonableness_gate(tool, prob, UPDATES["moonfix"]):
                    combos.append((setting_id, tool_id, prob_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    tool: str
    problem: str
    update: str
    name: str
    title: str
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


def build_story(world: World, hero: Entity, helper: Entity, tool: Entity,
                problem: Entity, update: Update) -> None:
    hero.memes["wonder"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Once in {world.setting.place}, little {hero.id} kept a {tool.label} "
        f"for catching moon dust. {world.setting.wonder} drifted around the tower, "
        f"and the sky was {world.setting.sky}."
    )
    world.say(
        f"{helper.id} brought a royal {update.label}. It promised to {update.promise}, "
        f"but the gate stayed {problem.gate_state}."
    )
    world.para()
    world.say(
        f"{hero.id} lifted the {tool.label} and whispered a magic word. "
        f"The {tool.label} began to {tool.use}, and the tiny sparks gathered {tool.effect}."
    )
    tool.meters["magic"] += 1
    propagate(world)
    world.para()
    if problem.meters["broken"] >= THRESHOLD:
        world.say(
            f"At last the {problem.label} was not broken anymore. The {update.label} "
            f"had done its work, and the moon path was safe to cross."
        )
        world.say(
            f"{hero.id} smiled at the bright space above the gate, while {helper.id} "
            f"watched the stars bow like tiny lanterns."
        )


def tell(setting: Setting, tool_def: MagicTool, problem_def: SpaceProblem,
         update_def: Update, name: str = "Mira", title: str = "little wizard") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="wizard", label=title))
    helper = world.add(Entity(id="Helper", kind="character", type="queen", label="the queen"))
    tool = world.add(Entity(id="sieve", type="sieve", label=tool_def.label, phrase=tool_def.phrase))
    gate = world.add(Entity(id="gate", type="gate", label=problem_def.label, gate_state=problem_def.state))
    helper.memes["hope"] += 1
    gate.meters["broken"] = 1
    world.facts.update(hero=hero, helper=helper, tool=tool, gate=gate, problem=problem_def, update=update_def)
    build_story(world, hero, helper, tool, gate, update_def)
    return world


SETTINGS = {
    "tower": Setting(place="the silver tower", sky="clear and blue", wonder="A staircase of light"),
    "garden": Setting(place="the moon garden", sky="violet and starry", wonder="Pearls of dew"),
    "harbor": Setting(place="the starlit harbor", sky="dark and sparkling", wonder="Salt wind and lantern glow"),
}

TOOLS = {
    "sieve": MagicTool(
        id="sieve",
        label="magic sieve",
        phrase="a silver magic sieve",
        use="hum softly",
        effect="into glittering dust",
        gathers="stardust",
        supports={"space", "magic"},
        tags={"sieve", "magic"},
    ),
    "wand": MagicTool(
        id="wand",
        label="wand",
        phrase="a willow wand",
        use="sparkle",
        effect="into bright beads",
        gathers="light",
        supports={"magic"},
        tags={"magic"},
    ),
    "bowl": MagicTool(
        id="bowl",
        label="gold bowl",
        phrase="a gold bowl",
        use="ring like a bell",
        effect="into moonwater",
        gathers="moonwater",
        supports={"space", "magic"},
        tags={"space", "magic"},
    ),
}

PROBLEMS = {
    "moonfix": SpaceProblem(
        id="moonfix",
        label="moon gate",
        phrase="the moon gate",
        state="cracked",
        risk="the stars might spill away",
        clue="a thin silver crack",
        tags={"space", "gate", "moon"},
    ),
    "stairfix": SpaceProblem(
        id="stairfix",
        label="sky stair",
        phrase="the sky stair",
        state="wobbly",
        risk="the steps might fall apart",
        clue="a tilted shining step",
        tags={"space", "stairs"},
    ),
    "cloudfix": SpaceProblem(
        id="cloudfix",
        label="cloud bridge",
        phrase="the cloud bridge",
        state="frayed",
        risk="the bridge might fray into mist",
        clue="a loose ribbon of cloud",
        tags={"space", "bridge"},
    ),
}

UPDATES = {
    "moonfix": Update(id="moonfix", label="royal update", phrase="a royal update",
                      promise="repair the moon gate", fix="mend the gate",
                      tags={"moonfix", "space"}),
    "stairfix": Update(id="stairfix", label="royal update", phrase="a royal update",
                       promise="steady the sky stair", fix="steady the stair",
                       tags={"stairfix", "space"}),
    "cloudfix": Update(id="cloudfix", label="royal update", phrase="a royal update",
                       promise="stitch the cloud bridge", fix="stitch the bridge",
                       tags={"cloudfix", "space"}),
}


def valid_combos() -> list[tuple[str, str, str]]:
    return choose_combo()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale magic sieve update in space.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--update", choices=UPDATES)
    ap.add_argument("--name")
    ap.add_argument("--title")
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
              and (getattr(args, "tool", None) is None or c[1] == getattr(args, "tool", None))
              and (getattr(args, "problem", None) is None or c[2] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, tool, problem = rng.choice(list(combos))
    update = getattr(args, "update", None) or "moonfix"
    name = getattr(args, "name", None) or rng.choice(["Mira", "Nia", "Luna", "Elin"])
    title = getattr(args, "title", None) or rng.choice(["little wizard", "young mage", "tiny enchantress"])
    return StoryParams(setting=setting, tool=tool, problem=problem, update=update, name=name, title=title)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale about {f["hero"].id}, a {f["hero"].label}, a magic sieve, and a royal update in space.',
        f"Tell a gentle story where {f['hero'].id} uses a sieve to gather stardust and help the queen mend the {f['gate'].label}.",
        f'Write a child-friendly magic story that includes the words "sieve", "update", and "space".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    gate = f["gate"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a {hero.label}, and the queen who helped them in the moon garden.",
        ),
        QAItem(
            question=f"What did {hero.id} use to gather the magic dust?",
            answer=f"{hero.id} used a magic sieve to gather stardust and make the small sparks behave.",
        ),
        QAItem(
            question=f"What did the royal update do?",
            answer=f"The royal update mended the {gate.label} and made the space path bright and safe again.",
        ),
        QAItem(
            question=f"Where did the ending take place?",
            answer=f"The ending took place in space near the bright gate, where the stars opened a path for a wish.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a sieve?", answer="A sieve is a tool with tiny holes that lets small bits pass through or catch in it."),
        QAItem(question="What is a magical update?", answer="A magical update is a helpful change or repair spell that makes something work better."),
        QAItem(question="What does space mean in a fairy tale?", answer="In a fairy tale, space can mean the wide sky beyond the world where stars, moons, and paths of light live."),
    ]


ASP_RULES = r"""
valid(S, T, P) :- setting(S), tool(T), problem(P),
    has_space(T), has_magic(T), space_problem(P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
        for tag in t.supports:
            lines.append(asp.fact("has_space", t.id) if tag == "space" else asp.fact("has_magic", t.id))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
        lines.append(asp.fact("space_problem", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    return 0 if set(asp_valid_combos()) == set(valid_combos()) else 1


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="] + sample.prompts + ["", "== story qa =="]
    for q in sample.story_qa:
        lines += [f"Q: {q.question}", f"A: {q.answer}"]
    lines += ["", "== world qa =="]
    for q in sample.world_qa:
        lines += [f"Q: {q.question}", f"A: {q.answer}"]
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)} state={e.gate_state}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(TOOLS, params.tool), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(UPDATES, params.update), params.name, params.title)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="garden", tool="sieve", problem="moonfix", update="moonfix", name="Mira", title="young mage"),
    StoryParams(setting="tower", tool="sieve", problem="stairfix", update="stairfix", name="Luna", title="little wizard"),
    StoryParams(setting="harbor", tool="bowl", problem="cloudfix", update="cloudfix", name="Elin", title="tiny enchantress"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples = [generate(p) for p in CURATED] if getattr(args, "all", None) else []
    if not samples:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(p))
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
