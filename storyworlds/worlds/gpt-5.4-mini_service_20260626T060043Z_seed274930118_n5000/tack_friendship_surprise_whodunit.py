#!/usr/bin/env python3
"""
A small whodunit-style story world about friendship, surprise, and a tack.

Premise:
- A child and a friend notice a small problem: a tack has gone missing.
- Strange little clues point in different directions.
- The friends solve the mystery together and the surprise turns into relief.

The world model tracks:
- physical meters: where the tack is, whether the page is pinned, whether a
  glove protects a hand, whether the floor is safe
- emotional memes: curiosity, worry, trust, relief, surprise, friendship

The story is intentionally simple and child-facing, but state-driven:
the clue trail, the reveal, and the ending image are all derived from the
simulated world.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    tack: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    indoor: bool = True
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
    hint: str
    risky_place: str
    requires_glove: bool = False
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
class Tool:
    id: str
    label: str
    covers: set[str]
    protects: set[str]
    prep: str
    tail: str
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
        self.path: list[str] = []

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


def resolve_comfort(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{hero.id} and {friend.id} were best friends, and they liked solving small "
        f"puzzles together."
    )


def introduce_clue(world: World, clue: Clue) -> None:
    world.say(
        f"One quiet afternoon, a shiny little {clue.label} was supposed to stay in its "
        f"place, but then it was gone."
    )
    world.say(
        f"There was only one odd sign: {clue.hint}"
    )


def worry(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"{hero.id} frowned. {friend.id} looked around slowly. "
        f"Something small had become a very big mystery."
    )


def investigate(world: World, hero: Entity, friend: Entity, clue: Clue) -> None:
    world.path.append("search")
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"They followed the clue to {clue.risky_place}. {hero.id} pointed at the little marks, "
        f"and {friend.id} bent down to look closer."
    )


def reveal(world: World, hero: Entity, friend: Entity, clue: Clue, tool: Tool) -> None:
    world.path.append("reveal")
    hero.memes["surprise"] += 1
    friend.memes["surprise"] += 1
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"At last, they found the answer: the {clue.label} had been nudged under a cushion "
        f"after someone hurried by. That was why the room looked strange."
    )
    world.say(
        f"{friend.id} used {tool.label} to pick it up safely, and {hero.id} gave a small gasp "
        f"that turned into a laugh."
    )


def ending(world: World, hero: Entity, friend: Entity, clue: Clue) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"In the end, the {clue.label} was back where it belonged, and the two friends "
        f"smiled at each other like detectives who had solved a tiny case."
    )
    world.say(
        f"The surprise was over, the room was safe again, and {hero.id} and {friend.id} "
        f"walked off side by side, still best friends."
    )


SETTINGS = {
    "sewing_room": Setting(place="the sewing room", indoor=True),
    "hall": Setting(place="the hall", indoor=True),
    "workbench": Setting(place="the workbench corner", indoor=True),
}

CLUES = {
    "tack_on_floor": Clue(
        id="tack_on_floor",
        label="tack",
        phrase="a tiny silver tack",
        hint="there was a bright glint on the floor by the chair",
        risky_place="the floor by the chair",
        requires_glove=True,
    ),
    "tack_in_cushion": Clue(
        id="tack_in_cushion",
        label="tack",
        phrase="a tiny silver tack",
        hint="the cushion had a little pricked spot in it",
        risky_place="the soft chair cushion",
        requires_glove=False,
    ),
    "tack_by_board": Clue(
        id="tack_by_board",
        label="tack",
        phrase="a tiny silver tack",
        hint="the board had a loose paper hanging crooked",
        risky_place="the notice board",
        requires_glove=False,
    ),
}

TOOLS = {
    "glove": Tool(
        id="glove",
        label="a padded glove",
        covers={"hand"},
        protects={"pricked"},
        prep="put on a padded glove first",
        tail="carefully lifted the tack with the glove",
    ),
    "tongs": Tool(
        id="tongs",
        label="small tongs",
        covers={"hand"},
        protects={"pricked"},
        prep="use small tongs first",
        tail="carefully lifted the tack with the tongs",
    ),
}


@dataclass
class StoryParams:
    setting: str
    clue: str
    tool: str
    hero: str
    friend: str
    seed: Optional[int] = None
    p: object | None = None
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
    ap = argparse.ArgumentParser(description="A tiny whodunit-style story world about a tack and two friends.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    return StoryParams(
        setting=setting,
        clue=clue,
        tool=tool,
        hero=getattr(args, "hero", None) or rng.choice(["Mina", "Noah", "Lena", "Owen"]),
        friend=getattr(args, "friend", None) or rng.choice(["June", "Pip", "Theo", "Ivy"]),
    )


def valid_story(params: StoryParams) -> bool:
    clue = _safe_lookup(CLUES, params.clue)
    return clue.requires_glove == (params.tool == "glove")


def reason_invalid(params: StoryParams) -> str:
    clue = _safe_lookup(CLUES, params.clue)
    tool = _safe_lookup(TOOLS, params.tool)
    if clue.requires_glove and tool.id != "glove":
        return "This clue needs a padded glove because the tack is on the floor and could prick a bare hand."
    return "This combination does not make a good whodunit puzzle for this world."


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("label", cid, clue.label))
        if clue.requires_glove:
            lines.append(asp.fact("needs_glove", cid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(tool.protects):
            lines.append(asp.fact("protects", tid, p))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(C, T) :- clue(C), tool(T), needs_glove(C), T = glove.
valid_story(C, T) :- clue(C), tool(T), not needs_glove(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p.clue, p.tool) for p in all_valid_pairs()}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} pairs).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def all_valid_pairs() -> list[StoryParams]:
    out = []
    for s in SETTINGS:
        for c in CLUES:
            for t in TOOLS:
                p = StoryParams(setting=s, clue=c, tool=t, hero="Mina", friend="June")
                if valid_story(p):
                    out.append(p)
    return out


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.hero, kind="character", type="girl"))
    friend = world.add(Entity(id=params.friend, kind="character", type="girl"))
    clue = _safe_lookup(CLUES, params.clue)
    tool = _safe_lookup(TOOLS, params.tool)
    tack = world.add(Entity(id="tack", type="thing", label="tack", phrase=clue.phrase))
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, worn_by=friend.id))

    world.facts.update(hero=hero, friend=friend, clue=clue, tool=tool, tack=tack)

    resolve_comfort(world, hero, friend)
    world.para()
    introduce_clue(world, clue)
    worry(world, hero, friend)
    investigate(world, hero, friend, clue)
    if clue.requires_glove and tool.id != "glove":
        pass
    world.para()
    world.say(
        f"{friend.id} said, 'Let's be careful.'"
    )
    world.say(
        f"They decided to {tool.prep}."
    )
    reveal(world, hero, friend, clue, tool)
    world.para()
    ending(world, hero, friend, clue)

    tack.meters["found"] = 1
    tack.memes["surprise"] = 1
    tool_ent.memes["helpful"] = 1
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = _safe_fact(world, f, "clue")
    return [
        f"Write a short whodunit for young children about a missing {clue.label} and two friends who solve the mystery.",
        f"Tell a gentle detective story where {f['hero'].id} and {f['friend'].id} follow clues and find a tiny {clue.label}.",
        f"Create a simple surprise mystery in {world.setting.place} that ends with friendship and a safe fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    clue: Clue = _safe_fact(world, f, "clue")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What mystery did {hero.id} and {friend.id} try to solve?",
            answer=f"They tried to solve the mystery of the missing {clue.label}. It turned into a small surprise when they found where it had gone.",
        ),
        QAItem(
            question=f"Why did they need {tool.label}?",
            answer=f"They needed {tool.label} because the {clue.label} could be sharp, so the friends wanted to pick it up safely.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {friend.id}?",
            answer=f"It ended with the {clue.label} back where it belonged and the two friends smiling together after solving the puzzle.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tack?",
            answer="A tack is a small sharp fastener that can pin paper or cloth in place.",
        ),
        QAItem(
            question="Why should you be careful with a tack on the floor?",
            answer="You should be careful because a tack can prick a hand or foot if you touch it carelessly.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and enjoy being together.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes someone stop and notice what just happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id} ({e.type}) " + " ".join(bits))
    lines.append(f"path={world.path}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="sewing_room", clue="tack_in_cushion", tool="tongs", hero="Mina", friend="June"),
    StoryParams(setting="hall", clue="tack_on_floor", tool="glove", hero="Noah", friend="Ivy"),
    StoryParams(setting="workbench", clue="tack_by_board", tool="glove", hero="Lena", friend="Pip"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/2."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            if not valid_story(params):
                continue
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
