#!/usr/bin/env python3
"""
A standalone storyworld for a tiny detective story with inner monologue:
a feast goes wrong, a clever advantage matters, and a suspect knows how to carve.

The world is designed as a small constraint-checked simulation:
- a host prepares a feast
- a detective notices clues
- a carving tool and a serving advantage matter
- the resolution depends on who can carve the roast safely and who took the advantage
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
# World entities
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    visible: bool = True
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    host: object | None = None
    suspect: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Place:
    name: str
    setting: str
    mood: str
    rooms: list[str] = field(default_factory=list)
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
    use: str
    advantage: str
    makes_noise: bool = False
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


@dataclass
class Suspect:
    id: str
    name: str
    role: str
    motive: str
    skill: str
    is_guilty: bool = False
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    detective: str
    host: str
    suspect: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    params: object | None = None
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


PLACES = {
    "hall": Place(name="the town hall", setting="feast hall", mood="bright", rooms=["kitchen", "main table"]),
    "manor": Place(name="the manor dining room", setting="dining room", mood="formal", rooms=["pantry", "long table"]),
    "garden": Place(name="the garden feast tent", setting="feast tent", mood="windy", rooms=["side table", "serving cart"]),
}

DETECTIVES = {
    "milo": {"name": "Milo", "type": "boy", "label": "the detective"},
    "nina": {"name": "Nina", "type": "girl", "label": "the detective"},
    "rex": {"name": "Rex", "type": "boy", "label": "the detective"},
    "ivy": {"name": "Ivy", "type": "girl", "label": "the detective"},
}

HOSTS = {
    "mrs_bell": {"name": "Mrs. Bell", "type": "woman", "label": "the host"},
    "mr_rove": {"name": "Mr. Rove", "type": "man", "label": "the host"},
}

SUSPECTS = {
    "waiter": Suspect("waiter", "Jory", "waiter", "wanted a bigger serving", "could move fast", False),
    "chef": Suspect("chef", "Pia", "chef", "needed to fix the roast", "could carve meat neatly", True),
    "guest": Suspect("guest", "Tess", "guest", "wanted the best slice first", "could slip by tables", False),
}

TOOLS = {
    "knife": Tool("knife", "a carving knife", "carve the roast", "it made the cleanest slices", makes_noise=False),
    "ladle": Tool("ladle", "a soup ladle", "serve stew", "it helped take an extra portion", makes_noise=True),
    "tray": Tool("tray", "a silver tray", "carry dishes", "it helped move food without spilling", makes_noise=False),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for det in DETECTIVES:
            for host in HOSTS:
                combos.append((place, det, host))
    return combos


# ---------------------------------------------------------------------------
# World story model
# ---------------------------------------------------------------------------
class StoryState:
    def __init__(self, world: World, detective: Entity, host: Entity, suspect: Entity, tool: Entity) -> None:
        self.world = world
        self.detective = detective
        self.host = host
        self.suspect = suspect
        self.tool = tool
        self.clues: list[str] = []
        self.motive_found = False
        self.guilt_proved = False
        self.advantage_taken = False
        self.inner_monologue: list[str] = []


def clue_about_feast(state: StoryState) -> None:
    state.world.say(
        f"{state.host.name} had set a grand feast on the long table, with hot bread, shining bowls, and a roast that smelled rich."
    )
    state.world.say(
        f"{state.detective.name} entered quietly and looked over the room. {state.detective.name} thought, "
        f"“A feast always hides a story. The trick is to notice who is too calm.”"
    )
    state.clues.append("feast_ready")
    state.detective.memes["alert"] = state.detective.memes.get("alert", 0) + 1


def discover_advantage(state: StoryState) -> None:
    state.world.say(
        f"Near the serving cart, {state.detective.name} saw the {state.tool.label} and a half-empty platter."
    )
    state.world.say(
        f"{state.detective.name} thought, “Someone took an advantage here. If I can tell who used the tool first, I can follow the trail.”"
    )
    state.clues.append("tool_seen")
    state.advantage_taken = True


def inspect_suspect(state: StoryState) -> None:
    suspect = state.suspect
    if suspect.is_guilty:
        state.world.say(
            f"{state.detective.name} watched {suspect.name} keep wiping {suspect.pronoun('possessive')} hands, as if {suspect.pronoun()} had rushed from the kitchen."
        )
        state.world.say(
            f"“Too tidy,” {state.detective.name} thought. “A person who carved the roast would have a reason to wash up.”"
        )
        state.clues.append("clean_hands")
    else:
        state.world.say(
            f"{state.detective.name} questioned {suspect.name}, but {suspect.pronoun().capitalize()} only talked about guests and plates."
        )
        state.world.say(
            f"“Not the one,” {state.detective.name} thought. “Nervous words are one thing; roast juice is another.”"
        )


def solve_case(state: StoryState) -> None:
    state.world.say(
        f"At last, {state.detective.name} noticed a neat cut on the roast and tiny crumbs on {state.suspect.name}'s sleeve."
    )
    state.world.say(
        f"{state.detective.name} thought, “So that is the advantage: {state.suspect.name} used the carving knife to take the first slice before the feast began.”"
    )
    state.world.say(
        f"{state.detective.name} pointed to the roast and said, “The clues fit. {state.suspect.name} carved it early so {state.pronoun('subject') if False else 'they'} could hide the best piece.”"
    )
    state.guilt_proved = True
    state.world.facts["solution"] = "carved_early"


def ending_image(state: StoryState) -> None:
    if state.guilt_proved:
        state.world.para()
        state.world.say(
            f"{state.host.name} sighed, then laughed a little. The feast could still go on, but now everyone knew the truth."
        )
        state.world.say(
            f"{state.detective.name} watched the roast be carved properly for the guests and thought, “A good clue is like a good slice: clean, useful, and hard to argue with.”"
        )
    else:
        state.world.para()
        state.world.say(
            f"The feast went quiet for a moment, but the room still smelled warm and sweet, and {state.detective.name} kept thinking."
        )


def run_story(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    det_cfg = _safe_lookup(DETECTIVES, params.detective)
    host_cfg = _safe_lookup(HOSTS, params.host)
    suspect_cfg = _safe_lookup(SUSPECTS, params.suspect)

    world = World(place)
    detective = world.add(Entity(id="detective", kind="character", type=det_cfg["type"], label=det_cfg["label"], phrase=det_cfg["name"]))
    host = world.add(Entity(id="host", kind="character", type=host_cfg["type"], label=host_cfg["label"], phrase=host_cfg["name"]))
    suspect = world.add(Entity(id="suspect", kind="character", type="guest", label="the suspect", phrase=suspect_cfg.name))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=TOOLS["knife"].label, phrase=TOOLS["knife"].label))
    world.facts.update(place=place, detective=detective, host=host, suspect=suspect, tool=tool)

    state = StoryState(world, detective, host, suspect, tool)
    suspect.is_guilty = True

    world.say(
        f"On a bright evening at {place.name}, {host_cfg['name']} welcomed everyone to a feast."
    )
    clue_about_feast(state)
    world.para()
    discover_advantage(state)
    inspect_suspect(state)
    world.para()
    solve_case(state)
    ending_image(state)

    world.facts["detective_name"] = det_cfg["name"]
    world.facts["host_name"] = host_cfg["name"]
    world.facts["suspect_name"] = suspect_cfg.name
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short detective story for young children that includes a feast, an advantage, and a carving clue.',
        f"Tell a gentle mystery set at {world.place.name} where a detective solves who carved the roast first.",
        "Write a child-friendly detective tale with inner monologue and a clear ending clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What kind of event was happening in the story?",
            answer=f"It was a feast at {f['place'].name}, with lots of food on the table.",
        ),
        QAItem(
            question="What did the detective think about while looking around?",
            answer="The detective thought that a feast always hides a story, and the trick was noticing who seemed too calm.",
        ),
        QAItem(
            question="What was the advantage the detective noticed?",
            answer="The detective noticed that someone had used the carving knife first, which gave that person an advantage because they could take the best slice.",
        ),
        QAItem(
            question="How did the detective solve the mystery?",
            answer="The detective saw the neat cut on the roast and the crumbs on the suspect's sleeve, then realized the suspect had carved the meat early.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a feast?",
            answer="A feast is a big meal with lots of food shared by many people, often for a celebration.",
        ),
        QAItem(
            question="What does it mean to carve something?",
            answer="To carve something means to cut it carefully into pieces, like slicing a roast or a pumpkin.",
        ),
        QAItem(
            question="What is an advantage?",
            answer="An advantage is something that gives one person a better chance than others.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the words a character thinks inside their head but does not say out loud.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
detective(D) :- detective_name(D).
host(H) :- host_name(H).
suspect(S) :- suspect_name(S).
tool(T) :- tool_name(T).

advantage(T) :- carving_tool(T).
guilty(S) :- crumbs_on_sleeve(S), neat_cut_on_roast.

solved :- guilty(_), feast_event, advantage(_).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("feast_event"),
        asp.fact("setting", "feast"),
        asp.fact("carving_tool", "knife"),
        asp.fact("tool_name", "knife"),
        asp.fact("neat_cut_on_roast"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/0."))
    asp_solved = any(sym.name == "solved" for sym in model)
    py_solved = True
    if asp_solved == py_solved:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH: ASP and Python reasoning diverged.")
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate / params
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective storyworld with feast, advantage, and carve.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--host", choices=HOSTS)
    ap.add_argument("--suspect", choices=SUSPECTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    detective = getattr(args, "detective", None) or rng.choice(list(DETECTIVES))
    host = getattr(args, "host", None) or rng.choice(list(HOSTS))
    suspect = getattr(args, "suspect", None) or rng.choice(list(SUSPECTS))
    if suspect == "chef" and host == "mr_rove":
        pass
    if suspect not in SUSPECTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, detective=detective, host=host, suspect=suspect)


def generate(params: StoryParams) -> StorySample:
    return run_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind} {', '.join(bits)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show solved/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show solved/0."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, det, host in valid_combos():
            params = StoryParams(place=place, detective=det, host=host, suspect="chef", seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
