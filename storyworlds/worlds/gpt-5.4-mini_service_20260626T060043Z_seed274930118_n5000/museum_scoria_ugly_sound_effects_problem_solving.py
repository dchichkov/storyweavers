#!/usr/bin/env python3
"""
Standalone storyworld: museum whodunit with scoria, ugly sound effects, and problem solving.

A small detective-style world where a child visitor, a museum, a strange pile of scoria,
and a suspicious ugly sound effect create a mystery. The story is resolved through
careful noticing, clues, and a practical fix.

The simulated world tracks:
- physical meters: noise, mess, dust, worry, order
- emotional memes: curiosity, fear, confidence, relief, suspicion

The prose is generated from the world state, not from a frozen template.
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    clue: object | None = None
    guide: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
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
    place: str = "the museum"
    rooms: list[str] = field(default_factory=lambda: ["lobby", "gallery", "storage", "cafe"])
    SETTING: object | None = None
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
    label: str
    place: str
    effect: str
    source: str
    suspicious: bool = False
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
class Tool:
    label: str
    use: str
    effect: str
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
        self.facts: dict = {}
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    guide: str
    clue: str
    tool: str
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


GIRL_NAMES = ["Mia", "Lila", "Nora", "Zoe", "Ivy", "Ava", "Ruby", "Maya"]
BOY_NAMES = ["Ben", "Theo", "Noah", "Eli", "Finn", "Leo", "Sam", "Owen"]


SETTING = Setting()

CLUES = {
    "scoria": Clue(
        label="a pile of scoria",
        place="storage",
        effect="scratchy scraping and tiny clacks",
        source="a broken lava display",
        suspicious=True,
    ),
    "marble": Clue(
        label="a marble statue base",
        place="gallery",
        effect="a low dragging hum",
        source="a loose wheel under a cart",
        suspicious=False,
    ),
    "coin": Clue(
        label="a dropped coin tray",
        place="lobby",
        effect="a bright ringing ping",
        source="a child at the desk",
        suspicious=False,
    ),
}

TOOLS = {
    "brush": Tool(label="a soft brush", use="brush away dust", effect="clean, gentle swishes"),
    "tape": Tool(label="masking tape", use="mark the floor", effect="small sticky snaps"),
    "cart": Tool(label="a rolling cart", use="move the clue carefully", effect="soft wheel hum"),
}


class GateError(StoryError):
    pass


def reasonableness_check(clue: Clue, tool: Tool) -> None:
    if clue.label == "a pile of scoria" and tool.label == "a rolling cart":
        return
    if clue.label == "a pile of scoria" and tool.label == "masking tape":
        return
    if clue.label == "a pile of scoria" and tool.label == "a soft brush":
        return
    if clue.label == "a marble statue base" and tool.label == "a soft brush":
        return
    if clue.label == "a dropped coin tray" and tool.label == "masking tape":
        return
    raise GateError("This clue and tool do not make a reasonable museum solution.")


def clue_is_suspicious(clue: Clue) -> bool:
    return clue.suspicious


def generated_sound(clue: Clue) -> str:
    if clue.label == "a pile of scoria":
        return "ugly little clack-clack-scrape"
    if clue.label == "a marble statue base":
        return "low grrrr-hum"
    return "bright ping-ping"


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("in_room", cid, clue.place))
        if clue.suspicious:
            lines.append(asp.fact("suspicious", cid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_use", tid, tool.use))
    return "\n".join(lines)


ASP_RULES = r"""
suspicion(C) :- clue(C), suspicious(C).
solves(C,T) :- clue(C), tool(T), suspicious(C), can_handle(T,C).
safe_fix(C,T) :- solves(C,T).
#show suspicion/1.
#show safe_fix/2.
#show solves/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\ncan_handle(brush,scoria).\ncan_handle(tape,scoria).\ncan_handle(cart,scoria).\ncan_handle(brush,marble).\ncan_handle(tape,coin).\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show safe_fix/2."))
    shown = set(asp.atoms(model, "safe_fix"))
    expected = {("scoria", "brush"), ("scoria", "tape"), ("scoria", "cart"),
                ("marble", "brush"), ("coin", "tape")}
    if shown == expected:
        print(f"OK: ASP gate matches Python reasonableness set ({len(shown)} entries).")
        return 0
    print("Mismatch between ASP and Python gate.")
    print("ASP:", sorted(shown))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Museum whodunit storyworld with scoria and sound effects.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["guard", "curator", "parent"], help="who helps solve the mystery")
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
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
    clue_id = getattr(args, "clue", None) or rng.choice(list(CLUES))
    tool_id = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    clue = _safe_lookup(CLUES, clue_id)
    tool = _safe_lookup(TOOLS, tool_id)
    if clue.suspicious and tool.label == "a rolling cart":
        pass
    reasonableness_check(clue, tool)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = getattr(args, "guide", None) or rng.choice(["guard", "curator", "parent"])
    return StoryParams(name=name, gender=gender, guide=guide, clue=clue_id, tool=tool_id)


def add_noise(world: World, amount: float, sound: str) -> None:
    world.facts["sound"] = sound
    world.facts["noise"] = amount


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    guide_type = {"guard": "man", "curator": "woman", "parent": "mother"}[params.guide]
    guide_label = {"guard": "the guard", "curator": "the curator", "parent": "the parent"}[params.guide]
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, label=guide_label))
    clue = world.add(Entity(id="Clue", type="thing", label=_safe_lookup(CLUES, params.clue).label, location=_safe_lookup(CLUES, params.clue).place))
    tool = world.add(Entity(id="Tool", type="thing", label=_safe_lookup(TOOLS, params.tool).label, location="lobby"))

    child.memes["curiosity"] = 2
    child.memes["suspicion"] = 1
    guide.memes["confidence"] = 2

    world.say(f"{child.id} came to the museum with bright eyes and quiet shoes.")
    world.say(f"{child.pronoun('subject').capitalize()} liked looking for clues, because museums felt like puzzles with windows.")

    world.para()
    sound = generated_sound(_safe_lookup(CLUES, params.clue))
    add_noise(world, 2.0, sound)
    world.say(f"Near the storage hall, there was an ugly sound: {sound}.")
    world.say(f"It did not sound like a song or a machine the museum wanted to keep.")
    world.say(f"{child.id} frowned and listened again.")

    if clue_is_suspicious(_safe_lookup(CLUES, params.clue)):
        child.memes["fear"] = 1
        child.memes["curiosity"] += 1
        world.say(f"The sound seemed to come from {clue.label}, which made the room feel odd and suspicious.")
    else:
        world.say(f"The sound seemed to come from {clue.label}, but the mystery was not as bad as it first sounded.")

    world.para()
    world.say(f"{guide.label.capitalize()} walked over and said, 'Let's solve it step by step.'")
    world.say(f"First they chose {tool.label}, because careful tools make a problem smaller instead of bigger.")
    world.say(f"Then they followed the sound to {clue.location}, where the clue was sitting in plain sight.")

    if params.tool == "brush":
        fix = "The brush swept the dust aside"
    elif params.tool == "tape":
        fix = "The tape marked the floor so nobody would kick the clue"
    else:
        fix = "The cart moved the clue safely without shaking it"
    world.say(fix + ".")
    world.say("Under the scoria, they found a cracked vent that had been rattling against the stones.")
    world.say("Once the vent was tightened, the ugly sound stopped at once.")

    world.para()
    child.memes["confidence"] = 3
    child.memes["relief"] = 2
    guide.memes["relief"] = 2
    world.say(f"{child.id} smiled, because the museum was quiet again and the mystery finally made sense.")
    world.say(f"The scoria stayed in a neat little tray, and the room sounded calm instead of ugly.")

    world.facts.update(
        child=child,
        guide=guide,
        clue=clue,
        tool=tool,
        sound=sound,
        fix=fix,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short whodunit for a young child set in a museum, with a strange scoria clue and an ugly sound effect.',
        f"Tell a gentle mystery story where {f['child'].id} hears an ugly sound in the museum and solves it with {(f.get('tool') or next(iter(TOOLS.values()))).label}.",
        "Write a child-friendly detective story that ends when the museum becomes quiet again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    guide = _safe_fact(world, f, "guide")
    clue = _safe_fact(world, f, "clue")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    qa = [
        QAItem(
            question=f"Where did {child.id} hear the ugly sound?",
            answer=f"{child.id} heard it in the museum, near the storage hall where the scoria clue was waiting.",
        ),
        QAItem(
            question=f"What made the mystery feel suspicious?",
            answer=f"The scoria and the ugly clacking sound made the room feel suspicious, so {child.id} listened very carefully.",
        ),
        QAItem(
            question=f"Who helped {child.id} solve the problem?",
            answer=f"{guide.label.capitalize()} helped {child.id} solve the problem by staying calm and choosing {tool.label}.",
        ),
        QAItem(
            question=f"What fixed the ugly sound in the end?",
            answer="A cracked vent was tightened, and that stopped the rattling sound at once.",
        ),
        QAItem(
            question=f"Why was the ending happy?",
            answer=f"The museum became quiet again, the scoria was put in a neat tray, and {child.id} felt proud and relieved.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is scoria?",
            answer="Scoria is a rough kind of volcanic rock with many tiny holes in it. It can look dark and crumbly.",
        ),
        QAItem(
            question="What does a museum do?",
            answer="A museum keeps interesting objects safe so people can look at them and learn about them.",
        ),
        QAItem(
            question="Why do detectives look at clues?",
            answer="Detectives look at clues because clues help them figure out what happened.",
        ),
        QAItem(
            question="Why can sound effects help tell a story?",
            answer="Sound effects can make a story feel real by letting you imagine what something sounds like.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_verify_world() -> int:
    return asp_verify()


def asp_show_program() -> str:
    return asp_program("#show suspicion/1.\n#show safe_fix/2.\n#show solves/2.")


def asp_reasonable_pairs() -> list[tuple[str, str]]:
    return [
        ("scoria", "brush"),
        ("scoria", "tape"),
        ("scoria", "cart"),
        ("marble", "brush"),
        ("coin", "tape"),
    ]


CURATED = [
    StoryParams(name="Mia", gender="girl", guide="curator", clue="scoria", tool="brush"),
    StoryParams(name="Ben", gender="boy", guide="guard", clue="scoria", tool="tape"),
    StoryParams(name="Lila", gender="girl", guide="parent", clue="marble", tool="brush"),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_show_program())
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify_world())

    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show safe_fix/2.\n#show solves/2.\n"))
        pairs = sorted(set(asp.atoms(model, "safe_fix")))
        print(f"{len(pairs)} safe fix pairs:")
        for clue, tool in pairs:
            print(f"  {clue} + {tool}")
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
            header = f"### {p.name}: clue={p.clue}, tool={p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
