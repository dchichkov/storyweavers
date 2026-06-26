#!/usr/bin/env python3
"""
Space Adventure storyworld: thing-dim, suey, graze, and inner monologue.

A tiny classical simulation about a crewmate on a starship who must decide
whether to use a risky thing-dim ray to solve a problem before a close call
becomes a real graze on the hull. The story is driven by state changes:
pressure, size, worry, and a final successful repair.

The style is kept close to a child-facing space adventure: concrete ship parts,
clear tension, and an ending image proving what changed.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    danger: object | None = None
    device: object | None = None
    hero: object | None = None
    mate: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "pilot"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "engineer"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
    star: str
    ship: str
    zone: str = "corridor"
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
    phrase: str
    effect: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Hazard:
    id: str
    label: str
    verb: str
    injury: str
    risk: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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


@dataclass
class StoryParams:
    setting: str
    hero: str
    crewmate: str
    tool: str
    hazard: str
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


SETTINGS = {
    "moonbase": Setting(place="Moon Base Nine", star="the bright sun", ship="the silver shuttle"),
    "asteroid": Setting(place="the asteroid station", star="a red dwarf", ship="the shuttle"),
    "orbit": Setting(place="the orbiting lab", star="the blue star", ship="the small ship"),
}

TOOLS = {
    "thing-dim": Tool(
        id="thing-dim",
        label="thing-dim ray",
        phrase="a small thing-dim ray",
        effect="make bulky things tiny",
    ),
    "patch": Tool(
        id="patch",
        label="hull patch",
        phrase="a sticky hull patch kit",
        effect="seal tiny leaks",
    ),
    "tug": Tool(
        id="tug",
        label="cargo tug",
        phrase="a little cargo tug",
        effect="pull heavy crates",
    ),
}

HAZARDS = {
    "suey": Hazard(
        id="suey",
        label="suey drone",
        verb="zip by too close",
        injury="a loud bonk",
        risk="scratched panels",
    ),
    "graze": Hazard(
        id="graze",
        label="graze on the hull",
        verb="scrape along the hull",
        injury="a thin scrape",
        risk="a scuffed hull panel",
    ),
}

CREW_NAMES = ["Mira", "Jax", "Nia", "Toby", "Zuri", "Finn", "Rae", "Pax"]
CREW_TYPES = ["pilot", "engineer", "navigator", "scout"]
TRAITS = ["brave", "curious", "quick", "careful", "spirited"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--crewmate")
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hazard", choices=HAZARDS)
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "tool", None) is None or c[1] == getattr(args, "tool", None))
        and (getattr(args, "hazard", None) is None or c[2] == getattr(args, "hazard", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, tool, hazard = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(CREW_NAMES)
    crewmate = getattr(args, "crewmate", None) or rng.choice([n for n in CREW_NAMES if n != hero])
    return StoryParams(setting=setting, hero=hero, crewmate=crewmate, tool=tool, hazard=hazard)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TOOLS:
            for h in HAZARDS:
                if t == "thing-dim" and h in {"suey", "graze"}:
                    combos.append((s, t, h))
    return combos


def explain_rejection(tool: Tool, hazard: Hazard) -> str:
    return (
        f"(No story: {tool.label} does not make sense for this hazard. "
        f"This world only tells stories where thing-dim can prevent a close-call "
        f"from becoming a real graze or suey scrape.)"
    )


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    lines.append(asp.fact("compatible", "thing-dim", "suey"))
    lines.append(asp.fact("compatible", "thing-dim", "graze"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,H) :- setting(S), tool(T), hazard(H), compatible(T,H).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    tool = _safe_lookup(TOOLS, params.tool)
    hazard = _safe_lookup(HAZARDS, params.hazard)
    world = World(setting)

    hero = world.add(Entity(id=params.hero, kind="character", type="engineer", meters={"size": 1.0}, memes={"worry": 0.0}))
    mate = world.add(Entity(id=params.crewmate, kind="character", type="pilot", meters={"size": 1.0}, memes={"calm": 1.0}))
    device = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, owner=hero.id))
    danger = world.add(Entity(id=hazard.id, type="hazard", label=hazard.label, phrase=hazard.label))

    world.say(f"On {setting.place}, {hero.id} checked the panel lights while the ship hummed softly.")
    world.say(f"{hero.id} had brought {tool.phrase}, because {tool.effect} could save the day.")
    world.say(f"{params.crewmate} floated beside {hero.id}, watching the dark window and the far-off stars.")
    world.para()

    world.say(f"Then {danger.label} started to {hazard.verb}.")
    hero.memes["worry"] += 1.0
    world.say(
        f"In {hero.id}'s head, one small thought repeated: {tool.label} had to work now, "
        f"before the mistake became {hazard.risk}."
    )
    world.say(
        f"{hero.id} whispered to {hero.pronoun('possessive')}self, "
        f"'If I can make this thing-dim, we can stop the graze.'"
    )
    world.say(f"{params.crewmate} reached for the controls, but {hero.id} was already aiming the ray.")
    world.para()

    if tool.id == "thing-dim" and hazard.id == "suey":
        hero.meters["focus"] += 1.0
        world.say(f"The thing-dim ray blinked blue. The suey drone shrank to the size of a walnut.")
        world.say(
            f"{hero.id} thought, 'Good. Small is safe.' {params.crewmate} laughed, and the little drone "
            f"bounced harmlessly off a magnet tray instead of the hatch."
        )
    elif tool.id == "thing-dim" and hazard.id == "graze":
        hero.meters["focus"] += 1.0
        world.say(f"The thing-dim ray blinked blue. The big scrape on the hull became a tiny nick.")
        world.say(
            f"{hero.id} thought, 'That tiny mark I can fix.' Then the patch kit sealed it before the air "
            f"could hiss out."
        )

    hero.memes["worry"] = 0.0
    mate.memes["relief"] = 1.0
    world.say(
        f"After that, the ship was quiet again. {hero.id} could see the stars in the window, "
        f"and the metal wall gleamed smooth and safe."
    )

    world.facts.update(
        hero=hero,
        mate=mate,
        tool=device,
        hazard=danger,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure story for a child that includes the words "thing-dim", "suey", and "graze".',
        f"Tell a gentle starship story about {f['hero'].id} using a thing-dim ray to stop {f['hazard'].label}.",
        f"Write a child-friendly space story with an inner monologue and a safe ending on {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mate = _safe_fact(world, f, "mate")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    hazard = _safe_fact(world, f, "hazard")
    return [
        QAItem(
            question=f"Who used the thing-dim ray in the story?",
            answer=f"{hero.id} used the thing-dim ray to help keep the ship safe.",
        ),
        QAItem(
            question=f"What did {hero.id} worry about when {hazard.label} showed up?",
            answer=f"{hero.id} worried that the close call would turn into {hazard.risk} or a real graze on the ship.",
        ),
        QAItem(
            question=f"How did {mate.id} help with the problem?",
            answer=f"{mate.id} stayed beside {hero.id}, and after the ray worked, {mate.id} laughed with relief.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The danger became small or harmless, and the ship ended quiet with the wall smooth and safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a thing-dim ray for?",
            answer="A thing-dim ray is a made-up space tool that makes a big thing tiny so it is easier to move or keep safe.",
        ),
        QAItem(
            question="What is a graze?",
            answer="A graze is a light scrape that brushes across a surface instead of smashing into it hard.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the little voice a character hears in their own head while thinking.",
        ),
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="moonbase", hero="Mira", crewmate="Jax", tool="thing-dim", hazard="suey"),
    StoryParams(setting="asteroid", hero="Nia", crewmate="Pax", tool="thing-dim", hazard="graze"),
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
            header = f"### {p.hero}: {p.tool} vs {p.hazard} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
