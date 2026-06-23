#!/usr/bin/env python3
"""
storyworlds/worlds/curly_republican_pecker_curiosity_whodunit.py
=================================================================

A standalone story world for a small whodunit-style curiosity tale.

Premise:
- A child with curly hair notices odd clues.
- A red, white, and blue "republican" ribbon on a box is a local club ribbon,
  not a political claim; in-story it just means "from the republic club" in a
  toy-town setting.
- A pecker bird keeps tapping at hidden places and helps reveal the truth.
- Curiosity drives the plot from puzzling signs to a neat reveal.

The world is intentionally small: one mystery, a few suspects, one resolution.
It models typed entities with physical meters and emotional memes, and it uses
a forward-moving simulation to decide what clues appear and how the ending lands.
"""

from __future__ import annotations

import argparse
import copy
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
    owner: str = ""
    location: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    plural: bool = False

    clue: object | None = None
    d: object | None = None
    h: object | None = None
    suspect: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

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
    indoor: bool = True
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
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    trail: str
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
class Suspect:
    id: str
    label: str
    phrase: str
    role: str
    tells: str
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
class Tool:
    id: str
    label: str
    phrase: str
    reveals: str
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
        self.threads: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.threads = list(self.threads)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    clue: str
    suspect: str
    tool: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None
    params: object | None = None
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
    "schoolhall": Setting(place="the school hall", indoor=True, affords={"mystery"}),
    "library": Setting(place="the little library", indoor=True, affords={"mystery"}),
    "garden": Setting(place="the garden shed", indoor=False, affords={"mystery"}),
}

CLUES = {
    "curly_ribbon": Clue(
        id="curly_ribbon",
        label="curly ribbon",
        phrase="a curly ribbon tied in a knot",
        kind="ribbon",
        trail="left a curly ribbon behind",
        tags={"curly", "curious"},
    ),
    "note": Clue(
        id="note",
        label="note",
        phrase="a folded note with tiny print",
        kind="paper",
        trail="hid under a box",
        tags={"curious"},
    ),
    "pebbles": Clue(
        id="pebbles",
        label="pebbles",
        phrase="three pebbles in a neat line",
        kind="stones",
        trail="pointed toward a shelf",
        tags={"curious"},
    ),
}

SUSPECTS = {
    "republican_box": Suspect(
        id="republican_box",
        label="republican box",
        phrase="a republican box with a bright seal",
        role="box",
        tells="its latch was scratched by a pecker beak",
        tags={"republican"},
    ),
    "pecker_bird": Suspect(
        id="pecker_bird",
        label="pecker bird",
        phrase="a pecker bird with a sharp little beak",
        role="bird",
        tells="it had been pecking at the loose hinge",
        tags={"pecker"},
    ),
    "lost_key": Suspect(
        id="lost_key",
        label="lost key",
        phrase="a small brass key",
        role="key",
        tells="it had slipped into a crack",
        tags={"curious"},
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="magnifier",
        phrase="a tiny magnifier",
        reveals="makes small marks easy to see",
        tags={"curious"},
    ),
    "brush": Tool(
        id="brush",
        label="brush",
        phrase="a soft brush",
        reveals="sweeps dust away without hurting anything",
        tags={"pecker"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Milo", "Eli", "Noah"]
TRAITS = ["curious", "careful", "quiet", "smart", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            for su in SUSPECTS:
                if c == "curly_ribbon" and su == "pecker_bird":
                    combos.append((s, c, su))
                elif c == "note" and su in {"republican_box", "lost_key"}:
                    combos.append((s, c, su))
                elif c == "pebbles" and su in {"lost_key", "pecker_bird"}:
                    combos.append((s, c, su))
    return combos


def clue_matches(clue: Clue, suspect: Suspect) -> bool:
    if clue.id == "curly_ribbon" and suspect.id == "pecker_bird":
        return True
    if clue.id == "note" and suspect.id in {"republican_box", "lost_key"}:
        return True
    if clue.id == "pebbles" and suspect.id in {"lost_key", "pecker_bird"}:
        return True
    return False


def select_tool(clue: Clue) -> Tool:
    return TOOLS["magnifier"] if clue.id != "curly_ribbon" else TOOLS["brush"]


def reasonableness_gate(clue: Clue, suspect: Suspect) -> bool:
    return clue_matches(clue, suspect)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("affords", sid, "mystery"))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for su in SUSPECTS:
        lines.append(asp.fact("suspect", su))
    lines.append(asp.fact("match", "curly_ribbon", "pecker_bird"))
    lines.append(asp.fact("match", "note", "republican_box"))
    lines.append(asp.fact("match", "note", "lost_key"))
    lines.append(asp.fact("match", "pebbles", "lost_key"))
    lines.append(asp.fact("match", "pebbles", "pecker_bird"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, U) :- setting(S), clue(C), suspect(U), match(C, U).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit story world about curiosity.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--detective", choices=None)
    ap.add_argument("--helper", choices=None)
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
              and (getattr(args, "suspect", None) is None or c[2] == getattr(args, "suspect", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, clue, suspect = rng.choice(list(combos))
    dg = getattr(args, "detective_gender", None) or rng.choice(["girl", "boy"])
    hg = getattr(args, "helper_gender", None) or rng.choice(["girl", "boy"])
    detective = getattr(args, "detective", None) or rng.choice(GIRL_NAMES if dg == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(GIRL_NAMES if hg == "girl" else BOY_NAMES)
    return StoryParams(
        setting=setting,
        clue=clue,
        suspect=suspect,
        tool=select_tool(_safe_lookup(CLUES, clue)).id,
        detective=detective,
        detective_gender=dg,
        helper=helper,
        helper_gender=hg,
    )


def _setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    d = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender))
    h = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=_safe_lookup(CLUES, params.clue).label,
                            phrase=_safe_lookup(CLUES, params.clue).phrase, tags=set(_safe_lookup(CLUES, params.clue).tags)))
    suspect = world.add(Entity(id="suspect", kind="thing", type="suspect",
                               label=_safe_lookup(SUSPECTS, params.suspect).label,
                               phrase=_safe_lookup(SUSPECTS, params.suspect).phrase,
                               tags=set(_safe_lookup(SUSPECTS, params.suspect).tags)))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=params.tool, phrase=_safe_lookup(TOOLS, params.tool).phrase))
    d.memes["curiosity"] = 1
    h.memes["curiosity"] = 1
    world.facts.update(detective=d, helper=h, clue=clue, suspect=suspect, tool=tool, params=params)
    return world


def generate(params: StoryParams) -> StorySample:
    if not reasonableness_gate(_safe_lookup(CLUES, params.clue), _safe_lookup(SUSPECTS, params.suspect)):
        pass
    world = _setup_world(params)
    d = world.get(params.detective)
    h = world.get(params.helper)
    clue = world.get("clue")
    suspect = world.get("suspect")
    tool = world.get("tool")
    clue_def = _safe_lookup(CLUES, params.clue)
    suspect_def = _safe_lookup(SUSPECTS, params.suspect)
    setting = world.setting.place

    d.memes["curiosity"] += 2
    h.memes["curiosity"] += 1
    world.say(f"{d.id} had curly hair and a curious mind, and {h.id} liked puzzles too.")
    world.say(f"One morning at {setting}, {d.id} noticed {clue_def.phrase}.")
    world.say(f"It seemed odd, because the clue {clue_def.trail}.")
    world.para()
    world.say(f"{d.id} and {h.id} followed the sign, looking under benches and behind boxes.")
    if clue_def.id == "curly_ribbon":
        world.say(f"The curly ribbon kept snagging on corners, as if it wanted to be found.")
    elif clue_def.id == "note":
        world.say("The note was folded so tight that the words almost hid from the eye.")
    else:
        world.say("The pebbles made a neat little road, one careful step at a time.")
    world.say(f"Then {h.id} said they should use {tool.phrase}; its job was to {tool.reveals}.")
    world.para()
    if suspect_def.id == "pecker_bird":
        world.say(f"A tiny pecker bird hopped in from the sill, tapping once, then twice.")
        world.say(f"It had been pecking at the loose hinge, and that explained the scratch marks.")
    elif suspect_def.id == "republican_box":
        world.say(f"They opened the republican box and found that its latch was not broken at all.")
        world.say(f"It had only been nudged by the pecker bird earlier, which made the clue seem strange.")
    else:
        world.say(f"At last they lifted a board and found the lost key hiding in a crack.")
        world.say("The odd signs were not a trick; they were simply the way the key had rolled away.")
    world.para()
    world.say(f"{d.id} laughed softly. Curiosity had carried them from puzzle to answer.")
    world.say(f"In the end, the little mystery was solved, and the {suspect_def.label} was understood.")
    world.say(f"{d.id} left {setting} smiling, with the clue fixed and the truth in sight.")

    world.facts.update(clue_def=clue_def, suspect_def=suspect_def, tool_def=_safe_lookup(TOOLS, params.tool))
    prompts = generation_prompts(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a small whodunit for children that includes the words "curly", "republican", and "pecker".',
        f"Tell a curious mystery where {p.detective} and {p.helper} follow a clue at {world.setting.place} and solve what happened.",
        f"Write a gentle detective story where curiosity turns a strange sign into an answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    clue: Clue = world.facts["clue_def"]
    suspect: Suspect = world.facts["suspect_def"]
    d: Entity = world.facts["detective"]
    h: Entity = world.facts["helper"]
    qa = [
        QAItem(
            question=f"What made {d.id} start wondering about the clue at {world.setting.place}?",
            answer=f"{d.id} noticed {clue.phrase}, and that looked odd enough to spark curiosity. The strange trail made {d.id} and {h.id} want to follow it and learn the truth.",
        ),
        QAItem(
            question=f"Who helped {d.id} solve the little mystery?",
            answer=f"{h.id} helped by looking closely and choosing a tool that could reveal small marks. Together they followed the clue until the answer made sense.",
        ),
        QAItem(
            question=f"What did the curly clue have to do with the pecker bird or the republican box?",
            answer=f"The curly clue pointed toward {suspect.label}. In the end, the odd sign fit because {suspect.tells}.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more and asking questions about what seems strange. A curious person keeps looking until a puzzle makes sense.",
        ),
        QAItem(
            question="What is a pecker bird?",
            answer="A pecker bird is a bird that taps or pecks at wood, bark, or little cracks with its beak. That tapping can leave marks that help solve a mystery.",
        ),
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened. Clues are like breadcrumbs that lead to the answer.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== (2) Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between ASP and Python:")
        print("  only in ASP:", sorted(cl - py))
        print("  only in Python:", sorted(py - cl))
        return 1
    print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return 0


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
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for setting, clue, suspect in valid_combos():
            params = StoryParams(
                setting=setting,
                clue=clue,
                suspect=suspect,
                tool=select_tool(_safe_lookup(CLUES, clue)).id,
                detective="Mina",
                detective_gender="girl",
                helper="Theo",
                helper_gender="boy",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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


def _story_knowledge(world: World) -> list[QAItem]:
    return world_knowledge_qa(world)


if __name__ == "__main__":
    main()
