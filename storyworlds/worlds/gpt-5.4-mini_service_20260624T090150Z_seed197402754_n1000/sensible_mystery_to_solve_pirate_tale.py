#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld about a sensible mystery to solve.

Premise:
- A careful pirate crew spots a strange problem on their ship or island.
- The captain uses clues, tools, and a sensible plan to solve it.
- The story changes with the modeled state: clue count, suspicion, and repair.

The domain stays small and classical:
- typed entities with physical meters and emotional memes
- a mystery that becomes solvable only when enough clues are gathered
- a resolution image proving what changed
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    mate: object | None = None
    ship: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain-girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "captain-boy"}:
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
    weather: str = "calm"
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
class Mystery:
    id: str
    clue_key: str
    culprit: str
    symptom: str
    fix: str
    location: str
    severity: str
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
class Tool:
    id: str
    label: str
    helps_with: set[str]
    use: str
    result: str
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


SETTINGS = {
    "ship": Setting(place="the ship", weather="breezy", affords={"search", "sail", "repair"}),
    "dock": Setting(place="the dock", weather="salt-spray", affords={"search", "repair"}),
    "island": Setting(place="the island cove", weather="sunny", affords={"search", "dig"}),
}

MYSTERIES = {
    "missing_map": Mystery(
        id="missing_map",
        clue_key="map",
        culprit="the wind",
        symptom="the treasure map was gone",
        fix="a map pinned under a heavy brass compass",
        location="the captain's cabin",
        severity="odd",
    ),
    "stolen_biscuit": Mystery(
        id="stolen_biscuit",
        clue_key="crumbs",
        culprit="a parrot",
        symptom="the biscuit tin was open",
        fix="a trail of crumbs leading to the mast",
        location="the galley",
        severity="curious",
    ),
    "leaky_boat": Mystery(
        id="leaky_boat",
        clue_key="water",
        culprit="a loose plank",
        symptom="water kept sneaking into the hull",
        fix="a cracked plank with fresh tar over it",
        location="below deck",
        severity="serious",
    ),
}

TOOLS = {
    "lantern": Tool(id="lantern", label="a lantern", helps_with={"search"}, use="lit it up", result="the corners shone clearly"),
    "magnifier": Tool(id="magnifier", label="a small magnifying glass", helps_with={"search"}, use="looked close", result="tiny marks stood out"),
    "hammer": Tool(id="hammer", label="a little hammer", helps_with={"repair"}, use="tapped the boards", result="the loose piece settled"),
    "rope": Tool(id="rope", label="a coil of rope", helps_with={"repair", "search"}, use="tied things steady", result="nothing drifted away"),
}

CREW_NAMES = ["Mira", "Ned", "Pip", "Jory", "Lila", "Tess", "Finn", "Bea"]
CAPTAIN_NAMES = ["Captain Mira", "Captain Ned", "Captain Pip"]
TRAITS = ["sensible", "brave", "curious", "steady"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    captain: str
    first_mate: str
    trait: str
    tool: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale about a sensible mystery to solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--captain")
    ap.add_argument("--first-mate")
    ap.add_argument("--trait", choices=TRAITS)
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


def reveal_hint(world: World, mystery: Mystery) -> str:
    if mystery.id == "missing_map":
        return "A brass compass had dent marks where something had rested."
    if mystery.id == "stolen_biscuit":
        return "Tiny crumbs dotted the floor near the mast."
    return "A wet trail on the boards led toward the repair kit."


def solve_mystery(world: World, mystery: Mystery, tool: Tool) -> None:
    captain = world.get("captain")
    mate = world.get("mate")
    captain.memes["focus"] = captain.memes.get("focus", 0.0) + 1
    mate.memes["trust"] = mate.memes.get("trust", 0.0) + 1
    world.say(f"{captain.id} used {tool.label}; {tool.result}.")
    world.say(f"{reveal_hint(world, mystery)}")
    world.say(f"That was a sensible clue. It pointed right at {mystery.culprit}.")
    captain.meters["clues"] = captain.meters.get("clues", 0.0) + 1
    if captain.meters["clues"] >= THRESHOLD:
        captain.memes["certainty"] = captain.memes.get("certainty", 0.0) + 1


def _repair(world: World, mystery: Mystery, tool: Tool) -> None:
    ship = world.get("ship")
    ship.meters["fixed"] = ship.meters.get("fixed", 0.0) + 1
    ship.meters["mess"] = 0.0
    world.say(f"Then they followed the clue and found {mystery.fix}.")
    world.say(f"With {tool.label} and a calm plan, they fixed the problem before sunset.")


def tell(setting: Setting, mystery: Mystery, captain_name: str, mate_name: str, trait: str, tool: Tool) -> World:
    world = World(setting)
    captain = world.add(Entity(id=captain_name, kind="character", type="boy" if "Captain" in captain_name else "girl"))
    mate = world.add(Entity(id=mate_name, kind="character", type="boy" if mate_name in {"Ned", "Pip", "Jory", "Finn"} else "girl"))
    ship = world.add(Entity(id="ship", type="ship", label="the ship"))

    ship.meters["mess"] = 1.0
    ship.meters["fixed"] = 0.0
    captain.meters["clues"] = 0.0
    captain.memes["worry"] = 1.0
    mate.memes["worry"] = 1.0

    world.say(f"On {setting.place}, {captain.id} was a {trait} pirate who liked things done the sensible way.")
    world.say(f"{mate.id} stayed close, because {mystery.symptom} had made the crew uneasy.")
    world.para()
    world.say(f"{captain.id} looked around and said, '{mystery.symptom.capitalize()}. We will find out why.'")
    world.say(f"First they searched with {tool.label}, because a sensible pirate starts with clues, not guesses.")
    solve_mystery(world, mystery, tool)
    world.para()
    _repair(world, mystery, tool)
    captain.memes["joy"] = captain.memes.get("joy", 0.0) + 1
    mate.memes["joy"] = mate.memes.get("joy", 0.0) + 1
    world.say(f"At last, the ship felt steady again, and {captain.id} smiled at {mate.id}.")
    world.say(f"The mystery was solved, and the crew sailed on with the problem behind them.")

    world.facts.update(
        captain=captain,
        mate=mate,
        ship=ship,
        mystery=mystery,
        tool=tool,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale for a young child about a sensible captain who solves a mystery on {world.setting.place}.',
        f"Tell a simple story where {f['captain'].id} notices that {f['mystery'].symptom} and uses {(f.get('tool') or next(iter(TOOLS.values()))).label} to investigate.",
        f'Write a child-friendly pirate story that includes the word "sensible" and ends with the crew feeling safe again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain = _safe_fact(world, f, "captain")
    mate = _safe_fact(world, f, "mate")
    mystery = _safe_fact(world, f, "mystery")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who was the sensible pirate in the story?",
            answer=f"{captain.id} was the sensible pirate who chose a careful way to solve the mystery.",
        ),
        QAItem(
            question=f"What problem made the crew uneasy at {world.setting.place}?",
            answer=f"The crew was uneasy because {mystery.symptom}. That was the mystery they needed to solve.",
        ),
        QAItem(
            question=f"What did {captain.id} use to look for clues?",
            answer=f"{captain.id} used {tool.label} to search carefully instead of making wild guesses.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"The mystery ended when they found {mystery.fix} and fixed the problem before sunset.",
        ),
        QAItem(
            question=f"Who stayed close to {captain.id} during the search?",
            answer=f"{mate.id} stayed close and helped keep the search calm and sensible.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sensible mean?",
            answer="Sensible means using good judgment and choosing a careful, reasonable way to do something.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you figure out a mystery.",
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives light so people can see in dark places.",
        ),
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat that pirates sail on the sea.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(out)


ASP_RULES = r"""
setting(ship).
setting(dock).
setting(island).

mystery(missing_map).
mystery(stolen_biscuit).
mystery(leaky_boat).

tool(lantern).
tool(magnifier).
tool(hammer).
tool(rope).

sensible_story(S, M, T) :- setting(S), mystery(M), tool(T).
#show sensible_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, m, t) for s in SETTINGS for m in MYSTERIES for t in TOOLS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show sensible_story/3."))
    return sorted(set(asp.atoms(model, "sensible_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    if clingo_set - python_set:
        print("only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("only in python:", sorted(python_set - clingo_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    captain = getattr(args, "captain", None) or rng.choice(CAPTAIN_NAMES)
    first_mate = getattr(args, "first_mate", None) or rng.choice(CREW_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if first_mate == captain:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, mystery=mystery, captain=captain, first_mate=first_mate, trait=trait, tool=tool)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(MYSTERIES, params.mystery), params.captain, params.first_mate, params.trait, _safe_lookup(TOOLS, params.tool))
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


CURATED = [
    StoryParams(setting="ship", mystery="missing_map", captain="Captain Mira", first_mate="Pip", trait="sensible", tool="magnifier"),
    StoryParams(setting="dock", mystery="stolen_biscuit", captain="Captain Ned", first_mate="Bea", trait="steady", tool="lantern"),
    StoryParams(setting="island", mystery="leaky_boat", captain="Captain Pip", first_mate="Lila", trait="curious", tool="hammer"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show sensible_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} sensible story combinations:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
        header = f"### {sample.params.captain} at {sample.params.setting}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
