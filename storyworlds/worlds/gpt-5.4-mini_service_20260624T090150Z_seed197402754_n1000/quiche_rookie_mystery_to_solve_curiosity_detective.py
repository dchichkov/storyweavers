#!/usr/bin/env python3
"""
Standalone storyworld: a rookie detective solves a quiche mystery through curiosity.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden_by: Optional[str] = None
    found_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    partner: object | None = None
    rookie: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    affordances: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    phrase: str
    hide_location: str
    hint: str
    tags: set[str] = field(default_factory=set)
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
    helps_with: set[str] = field(default_factory=set)
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    clue: str
    tool: str
    rookie_name: str
    partner_name: str
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
    "cafe": Setting(place="the cozy cafe", affordances={"search", "ask"}),
    "bakery": Setting(place="the bakery", affordances={"search", "ask"}),
    "kitchen": Setting(place="the kitchen", affordances={"search", "ask"}),
    "library": Setting(place="the library", affordances={"search", "ask"}),
}

CLUES = {
    "quiche": Clue(
        id="quiche",
        label="quiche",
        phrase="a warm quiche with a golden top",
        hide_location="under a napkin",
        hint="a buttery smell near the counter",
        tags={"food", "quiche", "crust"},
    ),
    "tray": Clue(
        id="tray",
        label="silver tray",
        phrase="a shiny silver tray",
        hide_location="behind a stack of cups",
        hint="a tiny clink from the shelf",
        tags={"metal", "counter"},
    ),
    "note": Clue(
        id="note",
        label="note",
        phrase="a folded note",
        hide_location="inside a sugar jar",
        hint="paper rustle from the pantry",
        tags={"paper", "message"},
    ),
}

TOOLS = {
    "magnifier": Tool(id="magnifier", label="magnifying glass", phrase="a round magnifying glass", helps_with={"search"}),
    "notebook": Tool(id="notebook", label="notebook", phrase="a small notebook", helps_with={"ask", "search"}),
    "lamp": Tool(id="lamp", label="desk lamp", phrase="a bright desk lamp", helps_with={"search"}),
}

ROOKIE_NAMES = ["Milo", "Nina", "Pia", "Theo", "Ruby", "Ezra", "June", "Owen"]
PARTNER_NAMES = ["Ivy", "Sam", "Mara", "Drew", "Lena", "Noah", "Tess", "Ben"]

ASP_RULES = r"""
place(P) :- setting(P).
clue(C) :- clue_item(C).
tool(T) :- tool_item(T).
helpful(T,A) :- tool_item(T), helps(T,A).
can_search(P,C) :- setting(P), clue_item(C), hidden_in(C,H), afford(P,search), helpful(_,search), H != "".
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("afford", sid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue_item", cid))
        lines.append(asp.fact("hidden_in", cid, c.hide_location))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_item", tid))
        for h in sorted(t.helps_with):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(setting: Setting, clue: Clue, tool: Tool) -> bool:
    return "search" in setting.affordances and clue.id in CLUES and tool.id in TOOLS


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for clue in CLUES:
            for tool in TOOLS:
                out.append((place, clue, tool))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld: a rookie follows curiosity to solve a quiche mystery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--partner")
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
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "clue", None):
        combos = [c for c in combos if c[1] == getattr(args, "clue", None)]
    if getattr(args, "tool", None):
        combos = [c for c in combos if c[2] == getattr(args, "tool", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue, tool = rng.choice(list(combos))
    return StoryParams(
        place=place,
        clue=clue,
        tool=tool,
        rookie_name=getattr(args, "name", None) or rng.choice(ROOKIE_NAMES),
        partner_name=getattr(args, "partner", None) or rng.choice(PARTNER_NAMES),
    )


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    clue_cfg = _safe_lookup(CLUES, params.clue)
    tool_cfg = _safe_lookup(TOOLS, params.tool)
    world = World(setting)

    rookie = world.add(Entity(id=params.rookie_name, kind="character", type="rookie", label="rookie detective"))
    partner = world.add(Entity(id=params.partner_name, kind="character", type="detective", label="partner detective"))
    clue = world.add(Entity(id="clue", type=clue_cfg.id, label=clue_cfg.label, phrase=clue_cfg.phrase, owner=partner.id))
    tool = world.add(Entity(id=tool_cfg.id, type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase, owner=rookie.id))
    clue.hidden_by = "napkin" if clue_cfg.id == "quiche" else clue_cfg.hide_location

    rookie.memes["curiosity"] = 2
    rookie.memes["hope"] = 1
    rookie.memes["confidence"] = 0
    partner.memes["calm"] = 1

    world.say(f"{rookie.id} was a rookie detective who loved every small clue.")
    world.say(f"{rookie.pronoun().capitalize()} carried {tool.phrase} and followed curiosity wherever it led.")
    world.say(f"That morning, {rookie.id} and {partner.id} arrived at {setting.place}.")
    world.say(f"They were looking for {clue_cfg.label}, but something did not feel right.")

    world.para()
    rookie.memes["curiosity"] += 1
    world.say(f"{rookie.id} noticed {clue_cfg.hint}.")
    world.say(f"{rookie.pronoun().capitalize()} crouched low and peered around with the {tool.label}.")

    if clue_cfg.id == "quiche":
        world.say(f"Under a napkin, they found the missing quiche, still warm and golden.")
        clue.meters["found"] = 1
        clue.found_by = rookie.id
        rookie.meters["mystery_solved"] = 1
        rookie.memes["joy"] += 1
    elif clue_cfg.id == "tray":
        world.say(f"Behind the cups, they found the silver tray that matched the clink.")
        clue.meters["found"] = 1
        clue.found_by = rookie.id
        rookie.meters["mystery_solved"] = 1
        rookie.memes["joy"] += 1
    else:
        world.say(f"In the sugar jar, they found the folded note that explained the hush.")
        clue.meters["found"] = 1
        clue.found_by = rookie.id
        rookie.meters["mystery_solved"] = 1
        rookie.memes["joy"] += 1

    world.para()
    world.say(f"{partner.id} smiled and said the mystery was solved.")
    world.say(f"{rookie.id} grinned, because curiosity had turned into a real answer.")
    world.say(f"At the end, the rookies' notebook held one clear clue, and the room felt bright again.")

    world.facts = {
        "rookie": rookie,
        "partner": partner,
        "clue": clue,
        "tool": tool,
        "setting": setting,
        "clue_cfg": clue_cfg,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a child about a rookie who follows curiosity to solve a mystery involving {f["clue_cfg"].label}.',
        f"Tell a gentle mystery story set in {f['setting'].place} where a rookie detective uses a {(f.get('tool') or next(iter(TOOLS.values()))).label} to find {f['clue_cfg'].phrase}.",
        "Write a tiny detective tale with a rookie, a clue, and a happy solved ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    rookie: Entity = _safe_fact(world, f, "rookie")
    partner: Entity = _safe_fact(world, f, "partner")
    clue_cfg: Clue = _safe_fact(world, f, "clue_cfg")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who was the rookie detective in the story?",
            answer=f"The rookie detective was {rookie.id}. {rookie.pronoun().capitalize()} loved curiosity and kept looking carefully.",
        ),
        QAItem(
            question=f"What mystery did {rookie.id} solve at {setting.place}?",
            answer=f"{rookie.id} solved the mystery of the missing {clue_cfg.label} at {setting.place}.",
        ),
        QAItem(
            question=f"What helped {rookie.id} search for the clue?",
            answer=f"{rookie.id} used {(f.get('tool') or next(iter(TOOLS.values()))).phrase} to search more carefully.",
        ),
        QAItem(
            question=f"Why did the answer come when {rookie.id} looked closely?",
            answer=f"Because {rookie.id} stayed curious and noticed {clue_cfg.hint}, which led straight to the clue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rookie?",
            answer="A rookie is someone who is new at a job or activity and is still learning.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn more.",
        ),
        QAItem(
            question="What is quiche?",
            answer="Quiche is a savory pie with eggs and a crust, often baked until the top is golden.",
        ),
    ]


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_by:
            bits.append(f"hidden_by={e.hidden_by}")
        if e.found_by:
            bits.append(f"found_by={e.found_by}")
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


def format_qa(sample: StorySample) -> str:
    lines = ["== story prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story questions =="]
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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


CURATED = [
    StoryParams(place="cafe", clue="quiche", tool="magnifier", rookie_name="Milo", partner_name="Ivy"),
    StoryParams(place="bakery", clue="tray", tool="notebook", rookie_name="Nina", partner_name="Sam"),
    StoryParams(place="library", clue="note", tool="lamp", rookie_name="Ruby", partner_name="Tess"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
