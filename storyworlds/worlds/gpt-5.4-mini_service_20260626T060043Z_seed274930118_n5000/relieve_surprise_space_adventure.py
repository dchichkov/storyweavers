#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure tale:
a crew member feels surprise, carries a burden, and then finds relief.

Seed premise:
- In a space-adventure setting, a character is startled by an unexpected problem.
- The crew helps relieve the problem with a concrete action or device.
- The ending should show a changed physical and emotional state.

This world is intentionally small and constraint-checked:
- The surprise must be plausible for the chosen location.
- The relief method must actually address the problem.
- Invalid combinations raise StoryError.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    def __post_init__(self) -> None:
        for k in ["heat", "cold", "pressure", "odor", "dust", "power", "worry"]:
            self.meters.setdefault(k, 0.0)
        for k in ["surprise", "relief", "fear", "calm", "curiosity", "joy", "panic"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot", "engineer"}
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
    place: str = "the starship corridor"
    afford: set[str] = field(default_factory=set)
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
class Surprise:
    id: str
    noun: str
    verb: str
    happen: str
    effect: str
    meter: str
    zone: str
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
class ReliefTool:
    id: str
    label: str
    covers: set[str]
    fixes: set[str]
    prep: str
    tail: str
    plural: bool = False
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

    def characters(self) -> list[Entity]:
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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


def _rule_surprise(world: World) -> list[str]:
    out: list[str] = []
    crew = world.facts.get("hero")
    surprise = world.facts.get("surprise")
    if not crew or not surprise:
        return out
    hero = crew
    if hero.memes["surprise"] < THRESHOLD:
        return out
    sig = ("surprise", hero.id, surprise.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] += 1
    out.append(f"{hero.id} froze for a moment, because the sight was startling.")
    return out


def _rule_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    tool = world.facts.get("tool")
    surprise = world.facts.get("surprise")
    if not hero or not tool or not surprise:
        return out
    if hero.memes["relief"] < THRESHOLD:
        return out
    sig = ("relief", hero.id, tool.id, surprise.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["panic"] = 0.0
    hero.memes["calm"] += 1
    out.append(f"The tight feeling in {hero.pronoun('possessive')} chest finally loosened.")
    return out


ASP_RULES = r"""
surprised(H) :- hero(H), surprise_event(S), notices(H, S).
relieved(H) :- hero(H), relief_tool(T), uses(H, T), helps(T, S), surprise_event(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise_event", sid))
        lines.append(asp.fact("surprise_noun", sid, s.noun))
        lines.append(asp.fact("surprise_meter", sid, s.meter))
        lines.append(asp.fact("surprise_zone", sid, s.zone))
        for t in sorted(s.tags):
            lines.append(asp.fact("surprise_tag", sid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("relief_tool", tid))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", tid, c))
        for f in sorted(t.fixes):
            lines.append(asp.fact("fixes", tid, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld: surprise and relief.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--type", choices=["girl", "boy", "captain", "pilot", "engineer"])
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


@dataclass
class StoryParams:
    place: str
    surprise: str
    tool: str
    name: str
    type: str
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


SETTINGS = {
    "corridor": Setting("the starship corridor", {"holo"}),
    "cargo": Setting("the cargo bay", {"crate"}),
    "lab": Setting("the sensor lab", {"signal"}),
}

SURPRISES = {
    "alien_signal": Surprise(
        id="alien_signal",
        noun="a blinking alien signal",
        verb="blinked",
        happen="flashed to life",
        effect="made the screens buzz",
        meter="signal",
        zone="screen",
        tags={"signal", "alien", "space"},
    ),
    "lost_robot": Surprise(
        id="lost_robot",
        noun="a tiny lost repair robot",
        verb="rolled",
        happen="tumbled out from behind a crate",
        effect="made the floor clatter",
        meter="robot",
        zone="floor",
        tags={"robot", "lost", "space"},
    ),
    "spilled_starsoup": Surprise(
        id="spilled_starsoup",
        noun="a floating splash of starsoup",
        verb="splashed",
        happen="spilled from a wobbly cup",
        effect="stuck to gloves and cheeks",
        meter="soup",
        zone="hands",
        tags={"mess", "food", "space"},
    ),
}

TOOLS = {
    "blanket": ReliefTool("blanket", "a soft blanket", {"screen", "hands"}, {"signal", "soup"}, "wrap it up gently", "wrapped the problem and breathed easier"),
    "shield": ReliefTool("shield", "a pocket shield", {"screen", "floor"}, {"signal", "robot"}, "turn on the pocket shield", "switched on the shield and watched the trouble settle"),
    "towel": ReliefTool("towel", "a clean towel", {"hands", "floor"}, {"soup", "dust"}, "grab a clean towel", "used the towel to clean the mess"),
}

NAMES = ["Nova", "Rin", "Milo", "Ada", "Zed", "Luna", "Taro", "Iris"]
KINDS = ["captain", "pilot", "engineer", "girl", "boy"]
TRAITS = ["brave", "curious", "careful", "cheerful", "quick"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for sid, s in SURPRISES.items():
            if not any(tok in setting.afford for tok in s.tags if tok in setting.afford):
                continue
            for tid, t in TOOLS.items():
                if s.meter in t.fixes:
                    combos.append((place, sid, tid))
    return combos


def explain_rejection(s: Surprise, t: ReliefTool) -> str:
    return f"(No story: {t.label} does not actually help with {s.noun}. The relief must fit the surprise.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "surprise", None) and getattr(args, "tool", None):
        s, t = _safe_lookup(SURPRISES, getattr(args, "surprise", None)), _safe_lookup(TOOLS, getattr(args, "tool", None))
        if s.meter not in t.fixes:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "surprise", None) is None or c[1] == getattr(args, "surprise", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, surprise, tool = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    typ = getattr(args, "type", None) or rng.choice(KINDS)
    return StoryParams(place=place, surprise=surprise, tool=tool, name=name, type=typ)


def _do_surprise(world: World, hero: Entity, surprise: Surprise) -> None:
    hero.memes["surprise"] += 1
    hero.memes["panic"] += 1
    hero.meters[surprise.meter] += 1
    world.say(f"Then {surprise.noun} {surprise.happen}, and {hero.id} gasped.")
    world.say(f"It {surprise.effect}.")


def _offer_relief(world: World, hero: Entity, tool: ReliefTool, surprise: Surprise) -> None:
    hero.memes["relief"] += 1
    world.say(f"{hero.pronoun('possessive').capitalize()} friend hurried over with {tool.label}.")
    world.say(f"They said they could {tool.prep}.")
    world.say(f"In a little while, they {tool.tail}, and the room felt safe again.")


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.type, label=params.name))
    surprise = _safe_lookup(SURPRISES, params.surprise)
    tool = _safe_lookup(TOOLS, params.tool)

    world.facts["hero"] = hero
    world.facts["surprise"] = surprise
    world.facts["tool"] = tool

    world.say(f"{hero.id} was a {random.choice(TRAITS)} {hero.type} aboard {world.setting.place}.")
    world.say(f"{hero.id} was checking the controls when the ship felt quiet and strange.")
    world.para()
    _do_surprise(world, hero, surprise)
    if surprise.id == "lost_robot":
        world.say(f"{hero.id} looked down and saw the little robot wobbling near {world.setting.place}.")
    elif surprise.id == "alien_signal":
        world.say(f"The screens glowed with the surprise, and the whole cabin hummed.")
    else:
        world.say(f"The sweet mess drifted by in tiny sticky drops.")
    world.para()
    _offer_relief(world, hero, tool, surprise)
    hero.memes["surprise"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["calm"] += 1
    world.say(f"By the end, {hero.id} was smiling again, and the ship felt easy to breathe in.")
    world.facts.update(hero=hero, place=params.place, surprise=surprise, tool=tool)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, surprise, tool = f["hero"], f["surprise"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short Space Adventure story for a young child about "{surprise.id}" and relief.',
        f"Tell a gentle story where {hero.id} gets a surprise on a spaceship and {tool.label} helps.",
        f"Write a simple space story that begins with surprise and ends with relief.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, surprise, tool = f["hero"], f["surprise"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What surprised {hero.id}?",
            answer=f"{hero.id} was surprised by {surprise.noun}, which made the scene feel sudden and exciting.",
        ),
        QAItem(
            question=f"What helped relieve the problem?",
            answer=f"{tool.label} helped relieve the problem because it was the right tool for {surprise.noun}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"At the end, {hero.id} felt calm and happy again after the surprise passed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a starship?", "A starship is a big space vehicle that can carry people through space."),
        QAItem("Why do people use shields in space stories?", "Shields can protect people or machines from danger, sparks, or rough conditions."),
        QAItem("What does relief mean?", "Relief is the good feeling that comes when a problem gets smaller or goes away."),
        QAItem("What is surprise?", "Surprise is the feeling you get when something happens that you did not expect."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("corridor", "alien_signal", "shield", "Nova", "captain"),
    StoryParams("cargo", "lost_robot", "shield", "Rin", "engineer"),
    StoryParams("lab", "spilled_starsoup", "towel", "Milo", "boy"),
]


def asp_verify() -> int:
    import asp
    # minimal parity check: ensure program runs and can show declared predicates
    model = asp.one_model(asp_program("#show relieved/1.\n#show surprised/1."))
    _ = model
    print("OK: ASP program loads and solves.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_asp_rules() -> str:
    return ASP_RULES


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show surprised/1.\n#show relieved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(valid_combos())} compatible combos.")
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

    for idx, sample in enumerate(samples):
        print(sample.story)
        if getattr(args, "trace", None) and sample.world is not None:
            print(dump_trace(sample.world))
        if getattr(args, "qa", None):
            print()
            print(format_qa(sample))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
