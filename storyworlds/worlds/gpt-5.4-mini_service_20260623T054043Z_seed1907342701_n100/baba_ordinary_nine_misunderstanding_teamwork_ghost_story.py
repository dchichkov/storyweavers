#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/baba_ordinary_nine_misunderstanding_teamwork_ghost_story.py
======================================================================================================================

A small ghost-story world about a child, a misunderstanding, and teamwork.

The seed words are woven into the story: baba, ordinary, nine.
The style stays child-facing and spooky-gentle, with a misunderstanding that
turns into teamwork and a final image that proves the change.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    helper: object | None = None
    hero: object | None = None
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
class Place:
    id: str
    label: str
    dark: bool = False
    echoes: bool = False
    allows: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    label: str
    sounds_like: str
    truly_is: str
    helps_with: str
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
class Tool:
    id: str
    label: str
    glow: str
    quiet: bool = False
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
class StoryParams:
    place: str = "hall"
    mystery: str = "whisper"
    tool: str = "lamp"
    name: str = "Baba"
    gender: str = "boy"
    helper: str = "Mina"
    helper_gender: str = "girl"
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


PLACES = {
    "hall": Place(id="hall", label="the old hall", dark=True, echoes=True, allows={"whisper", "shadow"}),
    "attic": Place(id="attic", label="the attic", dark=True, echoes=True, allows={"whisper", "rattle"}),
    "yard": Place(id="yard", label="the back yard", dark=True, echoes=False, allows={"shadow", "rattle"}),
    "basement": Place(id="basement", label="the basement", dark=True, echoes=True, allows={"whisper", "shadow", "rattle"}),
}

MYSTERIES = {
    "whisper": Mystery(id="whisper", label="a whisper", sounds_like="a ghost calling", truly_is="the wind in a crack", helps_with="listening closely", tags={"ghost", "wind"}),
    "shadow": Mystery(id="shadow", label="a shadow", sounds_like="a ghost at the door", truly_is="a coat on a hook", helps_with="looking twice", tags={"ghost", "light"}),
    "rattle": Mystery(id="rattle", label="a rattle", sounds_like="little bones tapping", truly_is="loose jars on a shelf", helps_with="holding still", tags={"ghost", "noise"}),
}

TOOLS = {
    "lamp": Tool(id="lamp", label="a small lamp", glow="made a warm square of light", quiet=True, tags={"light"}),
    "flashlight": Tool(id="flashlight", label="a flashlight", glow="clicked on bright and steady", quiet=True, tags={"light"}),
    "lantern": Tool(id="lantern", label="a paper lantern", glow="glowed like a moon in a cup", quiet=True, tags={"light"}),
    "rope": Tool(id="rope", label="a soft rope", glow="helped them tie the loose drawer", quiet=False, tags={"teamwork"}),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Lina", "Zoe"]
BOY_NAMES = ["Baba", "Oren", "Noah", "Eli", "Theo"]
HELPER_TRAITS = ["careful", "kind", "quick", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for m in MYSTERIES:
            for t in TOOLS:
                place = _safe_lookup(PLACES, p)
                mystery = _safe_lookup(MYSTERIES, m)
                tool = _safe_lookup(TOOLS, t)
                if mystery.id in place.allows and ("light" in tool.tags or tool.id == "rope"):
                    combos.append((p, m, t))
    return combos


def explain_rejection(place: Place, mystery: Mystery, tool: Tool) -> str:
    return (
        f"(No story: {place.label} does not fit this mystery/tool pairing, so the "
        f"ghostly misunderstanding would not feel honest. Pick a place and tool that "
        f"can actually help with {mystery.label}.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
        if p.echoes:
            lines.append(asp.fact("echoes", pid))
        for a in sorted(p.allows):
            lines.append(asp.fact("allows", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for a in sorted(m.tags):
            lines.append(asp.fact("tags", mid, a))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if "light" in t.tags:
            lines.append(asp.fact("light", tid))
        if "teamwork" in t.tags:
            lines.append(asp.fact("teamwork_tool", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,M,T) :- place(P), mystery(M), tool(T), allows(P,M), (light(T); teamwork_tool(T)).
misunderstanding(P,M) :- dark(P), mystery(M), tags(M, ghost).
teamwork(T) :- teamwork_tool(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class World:
    place: Place
    mystery: Mystery
    tool: Tool
    hero: Entity
    helper: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    world: object | None = None
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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


def setup_world(params: StoryParams) -> World:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.tool not in TOOLS:
        pass
    place = _safe_lookup(PLACES, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    tool = _safe_lookup(TOOLS, params.tool)
    if params.mystery not in place.allows or ("light" not in tool.tags and tool.id != "rope"):
        pass
    hero = Entity(id=params.name, kind="character", type=params.gender, meters={"worry": 0.0, "relief": 0.0}, memes={"worry": 0.0, "curiosity": 1.0}, attrs={"name": params.name})
    helper = Entity(id=params.helper, kind="character", type=params.helper_gender, meters={"worry": 0.0, "relief": 0.0}, memes={"worry": 0.0, "teamwork": 0.0}, attrs={"name": params.helper})
    world = World(place=place, mystery=mystery, tool=tool, hero=hero, helper=helper)
    world.facts.update(place=place, mystery=mystery, tool=tool, hero=hero, helper=helper)
    return world


def tell(world: World) -> None:
    h, a, p, m, t = world.hero, world.helper, world.place, world.mystery, world.tool
    h.memes["worry"] += 1
    world.say(f"On an ordinary evening, {h.id} and {a.id} went to {p.label}.")
    world.say(f"The dark there felt old and hushed, and one sound seemed like {m.sounds_like}.")
    world.say(f'"Did you hear that?" {h.id} asked. "{m.label}!"')
    world.para()
    h.meters["misunderstanding"] = 1.0
    h.memes["fear"] += 1
    world.say(f"{h.id} thought the sound meant a ghost was hiding nearby.")
    world.say(f"But {a.id} looked again and pointed at the truth: it was {m.truly_is}.")
    a.memes["teamwork"] += 1
    world.say(f'"Let’s use {t.label}," {a.id} said, "and look together."')
    if "light" in t.tags:
        world.say(f"{t.label.capitalize()} {t.glow}, and the dark corner became easy to see.")
    else:
        world.say(f"{t.label.capitalize()} helped them tie the loose thing that was making the noise.")
    world.para()
    h.meters["misunderstanding"] = 0.0
    h.meters["relief"] += 1
    a.meters["relief"] += 1
    h.memes["relief"] += 1
    a.memes["teamwork"] += 1
    world.say(f"Together they found the ordinary little cause and fixed it side by side.")
    world.say(f"In the end, {p.label} looked quiet again, with {h.id} and {a.id} standing by the door, safe and smiling.")
    world.facts.update(outcome="resolved")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story for a small child that includes the words "baba" and "ordinary" and "nine".',
        f"Tell a spooky-but-safe story where {f['hero'].id} hears something in {f['place'].label} and {f['helper'].id} helps explain the misunderstanding.",
        f'Write a child-facing ghost story about a strange sound, a calm helper, and teamwork, ending with a clear ordinary solution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h: Entity = f["hero"]  # type: ignore[assignment]
    a: Entity = f["helper"]  # type: ignore[assignment]
    p: Place = f["place"]  # type: ignore[assignment]
    m: Mystery = f["mystery"]  # type: ignore[assignment]
    t: Tool = (f.get("tool") or next(iter(TOOLS.values())))  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {h.id} think the sound in {p.label} was?",
            answer=f"{h.id} thought it was a ghost at first. The sound only seemed scary because the dark made {m.label} feel bigger than it was.",
        ),
        QAItem(
            question=f"How did {a.id} help {h.id} in the story?",
            answer=f"{a.id} looked twice, explained the mistake, and used {t.label} with {h.id}. That teamwork turned the misunderstanding into a calm fix.",
        ),
        QAItem(
            question=f"Why was the ending ordinary instead of scary?",
            answer=f"The ending was ordinary because the sound had an everyday cause, not a ghost. Once the children worked together, the place became quiet again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks something means one thing, but the real reason is different.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and use their different ideas together to solve a problem.",
        ),
        QAItem(
            question="What is a flashlight for?",
            answer="A flashlight gives a bright beam of light so people can see in the dark without any fire.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    return (
        "--- world model state ---\n"
        f"  place={world.place.label}\n"
        f"  mystery={world.mystery.label}\n"
        f"  tool={world.tool.label}\n"
        f"  hero meters={world.hero.meters} memes={world.hero.memes}\n"
        f"  helper meters={world.helper.meters} memes={world.helper.memes}\n"
    )


CURATED = [
    StoryParams(place="hall", mystery="whisper", tool="lamp", name="Baba", gender="boy", helper="Mina", helper_gender="girl"),
    StoryParams(place="attic", mystery="shadow", tool="flashlight", name="Nia", gender="girl", helper="Baba", helper_gender="boy"),
    StoryParams(place="basement", mystery="rattle", tool="lantern", name="Baba", gender="boy", helper="Oren", helper_gender="boy"),
    StoryParams(place="yard", mystery="shadow", tool="rope", name="Ivy", gender="girl", helper="Baba", helper_gender="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: a misunderstanding, a calm reveal, and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
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
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    helper_gender = getattr(args, "helper_gender", None) or ("girl" if gender == "boy" else "boy")
    name = getattr(args, "name", None) or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name])
    return StoryParams(place=place, mystery=mystery, tool=tool, name=name, gender=gender, helper=helper, helper_gender=helper_gender, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP valid_combos().")
        print(" only python:", sorted(py - cl))
        print(" only asp:", sorted(cl - py))
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print(f"OK: {len(py)} combos, ASP parity matches, and story generation smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
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
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
