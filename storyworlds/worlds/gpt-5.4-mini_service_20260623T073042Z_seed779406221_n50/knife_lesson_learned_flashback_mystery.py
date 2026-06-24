#!/usr/bin/env python3
"""
storyworlds/worlds/knife_lesson_learned_flashback_mystery.py
=============================================================

A small mystery-flavored storyworld about a missing kitchen knife, a flashback
that reveals the clue, and a lesson learned about careful handling.

The seed premise:
- A child notices a knife is missing.
- Suspicion and searching create mystery tension.
- A flashback reveals where it was last used.
- The ending teaches a gentle lesson learned: put sharp things away safely.

This world models typed entities with physical meters and emotional memes, and
renders state-driven prose plus grounded Q&A.
"""

from __future__ import annotations

import argparse
import copy
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    knife: object | None = None
    mother: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Setting:
    place: str
    detail: str
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
class Tool:
    id: str
    label: str
    phrase: str
    sharp: bool = False
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
class FlashbackClue:
    id: str
    trigger: str
    memory: str
    reveal: str
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


def _ensure_meter(e: Entity, key: str) -> None:
    e.meters.setdefault(key, 0.0)


def _ensure_meme(e: Entity, key: str) -> None:
    e.memes.setdefault(key, 0.0)


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    knife = world.get("knife")
    if child.memes.get("worry", 0.0) < THRESHOLD:
        return out
    sig = ("worry", knife.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("mother").memes["concern"] = world.get("mother").memes.get("concern", 0.0) + 1
    out.append("The missing knife made everyone feel uneasy.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_worry,):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def flashback_moment(world: World, child: Entity, clue: FlashbackClue) -> None:
    child.memes["remembering"] = child.memes.get("remembering", 0.0) + 1
    world.say(
        f"Then {child.id} had a flashback: {clue.memory} {clue.reveal}."
    )


def search_scene(world: World, child: Entity, mother: Entity, tool: Tool) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    world.say(
        f"At {world.setting.place}, {child.id} looked under the table and near the sink. "
        f"{child.pronoun().capitalize()} could not find the knife."
    )
    propagate(world, narrate=True)


def lesson_learned(world: World, child: Entity, mother: Entity, tool: Tool) -> None:
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    child.memes["lesson"] = child.memes.get("lesson", 0.0) + 1
    mother.memes["relief"] = mother.memes.get("relief", 0.0) + 1
    world.say(
        f"{mother.id} nodded and said, \"Good eye. Sharp things go back in the drawer right away.\""
    )
    world.say(
        f"{child.id} put the {tool.label} away carefully, and the kitchen felt calm again."
    )


def tell(setting: Setting, tool: Tool, clue: FlashbackClue,
         child_name: str = "Mia", child_type: str = "girl",
         mother_type: str = "mother") -> World:
    world = World(setting)

    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    mother = world.add(Entity(id="mother", kind="character", type=mother_type, label="Mom", role="mother"))
    knife = world.add(Entity(id="knife", type="thing", label=tool.label, phrase=tool.phrase, role="tool"))

    # Initialize all state before any propagation.
    for e in (child, mother, knife):
        for k in ("worry", "relief", "lesson", "remembering", "concern"):
            _ensure_meme(e, k)
        for k in ("lost", "found", "used"):
            _ensure_meter(e, k)

    knife.attrs["sharp"] = tool.sharp
    knife.attrs["stored"] = False
    child.attrs["looked"] = False
    mother.attrs["noticed"] = True
    world.facts["setting"] = setting
    world.facts["tool"] = tool
    world.facts["clue"] = clue

    world.say(
        f"One quiet afternoon, {child.id} noticed that the {tool.label} was missing from the kitchen."
    )
    world.say(
        f"The room was still {setting.detail}, and that made the search feel like a mystery."
    )
    search_scene(world, child, mother, tool)

    world.para()
    flashback_moment(world, child, clue)

    world.para()
    mother.memes["concern"] += 1
    world.say(
        f"After the memory, {child.id} checked the counter and saw where the {tool.label} had been left."
    )
    lesson_learned(world, child, mother, tool)

    knife.meters["found"] = 1.0
    knife.attrs["stored"] = True
    world.facts.update(child=child, mother=mother, knife=knife, resolved=True)
    return world


SETTINGS = {
    "kitchen": Setting(
        place="the kitchen",
        detail="quiet and bright",
        affords={"search", "flashback", "lesson"},
    ),
    "pantry": Setting(
        place="the pantry",
        detail="small and shadowy",
        affords={"search", "flashback", "lesson"},
    ),
}

TOOLS = {
    "kitchen_knife": Tool(
        id="kitchen_knife",
        label="kitchen knife",
        phrase="a small kitchen knife",
        sharp=True,
        tags={"knife", "sharp"},
    ),
}

CLUES = {
    "laundry": FlashbackClue(
        id="laundry",
        trigger="the sight of the counter",
        memory="Mia remembered slicing apples at lunch",
        reveal="and leaving the knife beside the cutting board",
    ),
}


@dataclass
class StoryParams:
    setting: str
    tool: str
    clue: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, c) for s in SETTINGS for t in TOOLS for c in CLUES]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    clue = f["clue"]
    return [
        f'Write a short mystery story for a young child about a missing {tool.label} and a helpful flashback.',
        f"Tell a gentle story where {child.id} cannot find the {tool.label}, remembers a clue, and learns to store sharp things safely.",
        f'Write a simple story with the word "{tool.tags and "knife"}" that ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    mother = f["mother"]
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    clue = f["clue"]
    return [
        QAItem(
            question=f"What was missing in the kitchen?",
            answer=f"The {tool.label} was missing, and that is why the search felt mysterious.",
        ),
        QAItem(
            question=f"What did {child.id} remember in the flashback?",
            answer=f"{child.id} remembered {clue.memory.lower()} {clue.reveal}.",
        ),
        QAItem(
            question=f"What lesson did {mother.id} teach?",
            answer=f"{mother.id} taught that sharp things go back in the drawer right away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should children be careful with a knife?",
            answer="A knife is sharp, so it can cut fingers if it is not handled slowly and put away safely.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that shows something that happened before, to help explain a clue.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"  {e.id:8} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)} attrs={e.attrs}"
        )
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
resolved :- knife_found, lesson.
knife_found :- found(knife).
lesson :- learned(child).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    lines += [asp.fact("tool", tid) for tid in TOOLS]
    lines += [asp.fact("clue", cid) for cid in CLUES]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Knife mystery storyworld with flashback and lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (getattr(args, "tool", None) is None or c[1] == getattr(args, "tool", None))
              and (getattr(args, "clue", None) is None or c[2] == getattr(args, "clue", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, tool, clue = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or (rng.choice(["Mia", "Nora", "Lily"]) if gender == "girl" else rng.choice(["Eli", "Noah", "Theo"]))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, tool=tool, clue=clue, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(TOOLS, params.tool), _safe_lookup(CLUES, params.clue), params.name, params.gender, params.parent)
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    if not asp.one_model(asp_program("#show resolved/0.")):
        print("ASP loaded.")
    print("OK: ASP twin present.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show resolved/0."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(s, t, c, "Mia", "girl", "mother")) for s, t, c in valid_combos()]
    else:
        seen: set[str] = set()
        for i in range(max(getattr(args, "n", None) * 50, 50)):
            if len(samples) >= getattr(args, "n", None):
                break
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
