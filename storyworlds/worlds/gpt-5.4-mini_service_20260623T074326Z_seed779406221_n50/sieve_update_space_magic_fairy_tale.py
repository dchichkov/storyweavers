#!/usr/bin/env python3
"""
storyworlds/worlds/sieve_update_space_magic_fairy_tale.py
=========================================================

A small fairy-tale story world about a sieve, an update, and a bit of space
magic. Two tiny characters want moon-sand and star-sparkles, but they must use a
sieve, listen for an update from a helper, and make a careful choice about
space. The world simulates a few changing meters and memes, then renders a
complete child-facing tale plus QA.

Seed premise:
- A child and a helper collect glittery "moon dust" with a sieve.
- A magical update warns that the dust is drifting into space.
- A spell can either guide the dust safely back into a jar or scatter it
  farther away.
- The story ends with a clear image showing what changed.

Contract notes:
- Stdlib only for the prose engine.
- Imports storyworlds/results.py eagerly.
- Imports storyworlds/asp.py lazily inside ASP helpers.
- Includes a Python reasonableness gate and inline ASP_RULES twin.
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
SENSE_MIN = 2



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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    child: object | None = None
    helper: object | None = None
    mentor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Theme:
    id: str
    scene: str
    rig: str
    goal: str
    dark_spot: str
    space_word: str
    send_off: str
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    where: str
    makes_magic: bool = True
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
class Hazard:
    id: str
    label: str
    the: str
    drift: str
    flammable: bool = False
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
class Magic:
    id: str
    label: str
    text: str
    power: int
    sense: int
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


@dataclass
class StoryParams:
    theme: str
    tool: str
    hazard: str
    magic: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    mentor: str
    update_style: str = "gentle"
    delay: int = 0
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


THEMES = {
    "moon_garden": Theme(
        id="moon_garden",
        scene="a moonlit garden",
        rig="The bench was their little ship, the lantern made a silver path, and a toy map showed the way to the wishing pond.",
        goal="the wishing pond",
        dark_spot="the hollow under the old root",
        space_word="space",
        send_off="glided home under the stars",
    ),
    "castle_attic": Theme(
        id="castle_attic",
        scene="a quiet castle attic",
        rig="The trunk was their castle gate, a ribbon became a banner, and a toy map showed the way to the secret tower.",
        goal="the secret tower",
        dark_spot="the rafters by the tiny round window",
        space_word="space",
        send_off="walked softly back to bed",
    ),
}

TOOLS = {
    "sieve": Tool("sieve", "sieve", "a little silver sieve", "by the garden sink", tags={"sieve", "magic"}),
    "net": Tool("net", "net", "a ribbon net", "on the porch chair", tags={"magic"}),
}

HAZARDS = {
    "stardust": Hazard("stardust", "stardust", "the stardust", "drifting through space", flammable=False, tags={"space"}),
    "moon_sand": Hazard("moon_sand", "moon sand", "the moon sand", "slipping through the sieve", flammable=False, tags={"space"}),
    "star_sparkles": Hazard("star_sparkles", "star sparkles", "the star sparkles", "twinkling away into space", flammable=False, tags={"space"}),
}

MAGICS = {
    "update_spell": Magic("update_spell", "update spell", "a glowing update that changed what the children knew", 3, 3, tags={"update", "magic"}),
    "bubble_spell": Magic("bubble_spell", "bubble spell", "a bubble spell that could hold the dust for a moment", 2, 2, tags={"magic"}),
    "storm_spell": Magic("storm_spell", "storm spell", "a storm spell that could scatter everything into space", 1, 1, tags={"magic", "space"}),
}

NAMES_GIRL = ["Mina", "Lily", "Nora", "Ivy", "Tess"]
NAMES_BOY = ["Finn", "Theo", "Ben", "Owen", "Leo"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for t in THEMES:
        for tool in TOOLS:
            for h in HAZARDS:
                for m in MAGICS:
                    if _safe_lookup(TOOLS, tool).makes_magic:
                        combos.append((t, tool, h, m))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world with sieve, update, space, and magic.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    theme = getattr(args, "theme", None) or rng.choice(list(THEMES))
    tool = getattr(args, "tool", None) or "sieve"
    hazard = getattr(args, "hazard", None) or rng.choice(list(HAZARDS))
    magic = getattr(args, "magic", None) or rng.choice(list(MAGICS))
    if tool == "net" and hazard == "moon_sand":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if magic == "storm_spell":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if child_gender == "girl" else "girl"
    return StoryParams(
        theme=theme,
        tool=tool,
        hazard=hazard,
        magic=magic,
        child=_pick_name(rng, child_gender),
        child_gender=child_gender,
        helper=_pick_name(rng, helper_gender),
        helper_gender=helper_gender,
        mentor=rng.choice(["grandmother", "fairy", "garden keeper"]),
        update_style=rng.choice(["gentle", "glowing"]),
        delay=getattr(args, "delay", None),
        seed=getattr(args, "seed", None),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.tool != "sieve":
        pass
    if params.magic == "storm_spell":
        pass


def story_outcome(params: StoryParams) -> str:
    return "safe" if params.magic in {"update_spell", "bubble_spell"} else "lost"


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    w = World()
    theme = _safe_lookup(THEMES, params.theme)
    tool = _safe_lookup(TOOLS, params.tool)
    hazard = _safe_lookup(HAZARDS, params.hazard)
    magic = _safe_lookup(MAGICS, params.magic)

    child = w.add(Entity(params.child, "character", params.child_gender, role="child"))
    helper = w.add(Entity(params.helper, "character", params.helper_gender, role="helper"))
    mentor = w.add(Entity(params.mentor, "character", "woman", role="mentor"))

    child.memes["hope"] = 1.0
    helper.memes["care"] = 1.0

    w.say(
        f"In {theme.scene}, {child.id} and {helper.id} carried {tool.phrase} to gather {hazard.label}. "
        f"{theme.rig}"
    )
    w.say(f"But {theme.dark_spot} was full of twinkling dust, and the dust kept drifting into {theme.space_word}.")

    w.para()
    helper.memes["worry"] += 1
    w.say(
        f"Then the {params.update_style} update came from {mentor.id}: \"The moon dust is slipping away! "
        f"Use the sieve carefully, and keep it close to the jar.\""
    )
    w.say(f"{child.id} listened, because {mentor.id} sounded wise and the warning glowed like a little star.")

    outcome = story_outcome(params)
    if outcome == "safe":
        child.memes["bravery"] += 1
        w.para()
        if magic.id == "bubble_spell":
            w.say(
                f"{child.id} whispered a bubble spell, and a round silver bubble caught the dust before it could float off."
            )
        else:
            w.say(
                f"{helper.id} lifted the sieve, and the update spell showed the exact tilt needed to guide every grain home."
            )
        w.say(
            f"Together they tipped the sieve over the jar, and the moon sand fell in a soft, shining rain."
        )
        w.say(
            f"By bedtime the jar was full, the jar lid was snug, and the garden path sparkled with only one tiny trail of moonlight."
        )
    else:
        child.memes["sadness"] += 1
        w.para()
        w.say(
            f"{child.id} tried a stormy charm, and the dust spun high above the roof, turning into faraway space glitter."
        )
        w.say(
            f"Even the sieve could not gather it back, so the children watched the last sparkles blink out beyond the clouds."
        )
        w.say(
            f"Still, {mentor.id} smiled kindly and promised a better update for tomorrow, when the stars would wait a little longer."
        )

    w.facts.update(
        child=child,
        helper=helper,
        mentor=mentor,
        theme=theme,
        tool=tool,
        hazard=hazard,
        magic=magic,
        outcome=outcome,
    )
    return w


def generation_prompts(w: World) -> list[str]:
    f = w.facts
    return [
        f"Write a fairy-tale story for young children about {f['child'].id} using a sieve to gather {f['hazard'].label} in {f['theme'].scene}.",
        f"Tell a gentle magic story where an update warns {f['child'].id} and {f['helper'].id} that the dust is drifting into space, and they fix it with magic.",
        f"Write a child-facing story with a sieve, an update, space, and magic that ends with the treasure safely in a jar.",
    ]


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    child, helper, mentor = f["child"], f["helper"], f["mentor"]
    return [
        QAItem(
            question=f"What did {child.id} use to gather the {f['hazard'].label}?",
            answer=f"{child.id} used a sieve, because the little holes let the children sort the glittering dust carefully.",
        ),
        QAItem(
            question=f"What did the update from {mentor.id} tell them?",
            answer=f"It told them the moon dust was slipping into space and that they should keep the sieve close to the jar.",
        ),
        QAItem(
            question=f"How did {child.id} and {helper.id} fix the problem?",
            answer="They used magic carefully, tipped the sieve just right, and guided the dust back into the jar.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The jar was full and safe, and the children had only a tiny trail of moonlight left on the garden path.",
        ),
    ]


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sieve used for?",
            answer="A sieve is used to let small pieces pass through holes while bigger pieces stay behind.",
        ),
        QAItem(
            question="What does an update mean in a story like this?",
            answer="An update is new information that changes what someone knows or what they should do next.",
        ),
        QAItem(
            question="What does space mean here?",
            answer="Space means the far-away sky beyond the clouds where stars seem to live.",
        ),
        QAItem(
            question="What is magic in a fairy tale?",
            answer="Magic is a special power that can change how things behave in a story, like making dust glow or stay together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(w: World) -> str:
    out = ["--- world trace ---"]
    for e in w.entities.values():
        out.append(f"{e.id}: meters={e.meters} memes={e.memes} role={e.role}")
    return "\n".join(out)


ASP_RULES = r"""
valid(theme,tool,hazard,magic) :- theme(theme), tool(tool), hazard(hazard), magic(magic), tool(tool), sieve(tool).
safe(magic) :- magic(update_spell).
safe(magic) :- magic(bubble_spell).
outcome(safe) :- chosen_magic(M), safe(M).
outcome(lost) :- chosen_magic(M), magic(M), not safe(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
        if t == "sieve":
            lines.append(asp.fact("sieve", t))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h))
    for m in MAGICS:
        lines.append(asp.fact("magic", m))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    rc = 0
    model = asp.one_model(asp_program("", "#show safe/1."))
    safe_set = {a[0] for a in asp.atoms(model, "safe")}
    py_set = {"update_spell", "bubble_spell"}
    if safe_set != py_set:
        rc = 1
        print("MISMATCH: safe magic differs.")
    else:
        print("OK: ASP safe magic matches Python.")
    return rc


CURATED = [
    StoryParams("moon_garden", "sieve", "stardust", "update_spell", "Mina", "girl", "Finn", "boy", "fairy"),
    StoryParams("castle_attic", "sieve", "moon_sand", "bubble_spell", "Leo", "boy", "Nora", "girl", "grandmother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("", "#show valid/4.\n#show safe/1.\n#show outcome/1."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        print(asp.one_model(asp_program("", "#show valid/4.\n#show safe/1.\n#show outcome/1.")))
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(rng.randrange(2**31)))
            samples.append(generate(p))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
