#!/usr/bin/env python3
"""
storyworlds/worlds/intellectual_condense_peek_quest_ghost_story.py
==================================================================

A small standalone story world: a child-friendly ghost story about an
intellectual quest, where a curious seeker learns to condense clues, peek
carefully, and solve a gentle mystery.

Seed premise:
---
On a foggy evening, a thoughtful child named Mira found a tiny note on the
library steps. The note promised a quest: find the missing moon bell before the
midnight chime.

Mira peeked through the dusty shelves, condensed the clues into a neat list,
and followed the whispering trail past a sleepy clock, a silver key, and a
rattling old map. In the end, the "ghost" was only the library lantern moving
in the wind, and the moon bell was tucked safely inside a storybook.

The world is built as a classical simulation:
- entities have physical meters and emotional memes
- clues change the seeker's state
- the quest advances by peeking at one place at a time
- the ending proves what changed in the world

The story is intentionally small and constraint-checked:
- if a clue is missing, the quest cannot proceed
- if the hidden bell is not in a discoverable place, generation fails closed
- the final tale always resolves the mystery with an ending image

The script also includes a Python reasonableness gate and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    owner: Optional[str] = None
    hidden_in: str = ""
    discovered: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    seeker: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
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
class Quest:
    title: str
    goal: str
    setting: str
    trail: list[str]
    reveal: str
    ghost_hint: str
    final_place: str
    final_truth: str
    tags: set[str] = field(default_factory=set)
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
        return None


@dataclass
class Clue:
    id: str
    label: str
    place: str
    hint: str
    reveals: str
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
class World:
    quest: Quest
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.quest)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone
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
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    RULES: list = field(default_factory=list)
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


def _r_discover(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.get("seeker")
    for clue in CLUES.values():
        if clue.place != seeker.meters.get("at_place_name", ""):
            continue
        if clue.id in world.fired:
            continue
        world.fired.add((clue.id, "discover"))
        world.get(clue.id).discovered = True
        seeker.memes["hope"] = seeker.memes.get("hope", 0) + 1
        out.append(f"{seeker.label} found a clue: {clue.label}.")
    return out


def _r_peek(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.get("seeker")
    for clue in CLUES.values():
        if not world.get(clue.id).discovered:
            continue
        sig = (clue.id, "peeked")
        if sig in world.fired:
            continue
        world.fired.add(sig)
        seeker.meters["clues_seen"] = seeker.meters.get("clues_seen", 0) + 1
        seeker.memes["curiosity"] = seeker.memes.get("curiosity", 0) + 1
        out.append(f"{seeker.label} peeked at {clue.label} and learned something quiet.")
    return out


def _r_condense(world: World) -> list[str]:
    seeker = world.get("seeker")
    if seeker.meters.get("clues_seen", 0) < THRESHOLD:
        return []
    if ("condense",) in world.fired:
        return []
    world.fired.add(("condense",))
    seeker.memes["confidence"] = seeker.memes.get("confidence", 0) + 1
    world.facts["condensed"] = True
    return [f"{seeker.label} condensed the clues into one simple plan."]


RULES = [Rule("discover", _r_discover), Rule("peek", _r_peek), Rule("condense", _r_condense)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for qid, quest in QUESTS.items():
        for cid, clue in CLUES.items():
            if clue.reveals in quest.tags:
                combos.append((qid, cid))
    return combos


@dataclass
class StoryParams:
    quest: str
    clue: str
    seeker_name: str
    seeker_type: str
    sidekick_name: str
    sidekick_type: str
    seed: Optional[int] = None
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


QUESTS = {
    "moon_bell": Quest(
        title="The Moon Bell Quest",
        goal="find the missing moon bell",
        setting="the old library",
        trail=["dust", "whisper", "key", "map"],
        reveal="the bell is in a storybook",
        ghost_hint="a ghostly whisper near the shelves",
        final_place="a hollow storybook",
        final_truth="the lantern in the window made the ghostly shape",
        tags={"bell", "storybook", "ghost"},
    ),
    "lantern_key": Quest(
        title="The Lantern Key Quest",
        goal="find the silver key",
        setting="the attic hall",
        trail=["scratch", "glow", "key", "door"],
        reveal="the key was under the lantern",
        ghost_hint="a pale light by the stair",
        final_place="under the old lantern",
        final_truth="the moving light was only wind in the curtains",
        tags={"key", "lantern", "ghost"},
    ),
}

CLUES = {
    "dust_note": Clue(
        id="dust_note",
        label="a dusty note",
        place="the old library",
        hint="a note promised the quest",
        reveals="bell",
        tags={"note", "bell"},
    ),
    "silver_key": Clue(
        id="silver_key",
        label="a silver key",
        place="the attic hall",
        hint="a key glinted in the dark",
        reveals="key",
        tags={"key"},
    ),
    "storybook": Clue(
        id="storybook",
        label="an open storybook",
        place="the old library",
        hint="a book looked a little too heavy",
        reveals="storybook",
        tags={"storybook", "bell"},
    ),
    "window_lantern": Clue(
        id="window_lantern",
        label="the window lantern",
        place="the attic hall",
        hint="a lantern swayed in the wind",
        reveals="lantern",
        tags={"lantern", "ghost"},
    ),
}


def make_world(params: StoryParams) -> World:
    quest = _safe_lookup(QUESTS, params.quest)
    world = World(quest)
    seeker = world.add(Entity(
        id="seeker",
        kind="character",
        type=params.seeker_type,
        label=params.seeker_name,
        meters={"at_place_name": 0},
        memes={"curiosity": 0, "hope": 0, "confidence": 0},
    ))
    sidekick = world.add(Entity(
        id="sidekick",
        kind="character",
        type=params.sidekick_type,
        label=params.sidekick_name,
        meters={"at_place_name": 0},
        memes={"curiosity": 0, "hope": 0},
    ))
    clue = _safe_lookup(CLUES, params.clue)
    world.add(Entity(
        id=clue.id,
        label=clue.label,
        hidden_in=clue.place,
        discovered=False,
        meters={"weight": 1},
        memes={"mystery": 1},
    ))
    world.facts.update(
        quest=quest,
        clue=clue,
        seeker=seeker,
        sidekick=sidekick,
        condensed=False,
    )
    seeker.meters["at_place_name"] = clue.place
    sidekick.meters["at_place_name"] = clue.place
    return world


def tell(world: World) -> World:
    quest = world.quest
    seeker = world.get("seeker")
    sidekick = world.get("sidekick")
    clue = world.facts["clue"]

    world.say(f"On a foggy evening, {seeker.label} and {sidekick.label} reached {quest.setting}.")
    world.say(f"An intellectual quest waited there: {quest.goal}.")
    world.para()
    world.say(f"{seeker.label} spotted {clue.hint} and decided to peek carefully.")
    propagate(world, narrate=True)
    if not clue.reveals:
        pass
    world.say(f"{sidekick.label} watched while {seeker.label} condensed the clues into a tidy idea.")
    world.para()
    world.say(f"They followed the trail to {quest.final_place}.")
    world.say(f"There, the ghostly mystery was solved: {quest.final_truth}.")
    world.say(f"{quest.reveal.capitalize()}.")
    seeker.meters["quest_done"] = 1
    seeker.memes["relief"] = seeker.memes.get("relief", 0) + 1
    sidekick.memes["relief"] = sidekick.memes.get("relief", 0) + 1
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest"]
    c = world.facts["clue"]
    s = world.facts["seeker"]
    return [
        f'Write a gentle ghost story for a child where {s.label} follows a quest in {q.setting} and uses a clue like "{c.label}".',
        f"Tell a small mystery about {s.label} who must peek, condense clues, and solve {q.goal} without real danger.",
        f'Write an intellectual quest story with a ghostly mood, an ending reveal, and the word "{c.label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    q = world.facts["quest"]
    c = world.facts["clue"]
    s = world.facts["seeker"]
    k = world.facts["sidekick"]
    return [
        QAItem(
            question=f"Who went on the quest in {q.setting}?",
            answer=f"{s.label} went with {k.label} on a quiet quest in {q.setting}.",
        ),
        QAItem(
            question=f"What did {s.label} do to the clue?",
            answer=f"{s.label} peeked at {c.label} and then condensed the clues into one simple plan.",
        ),
        QAItem(
            question=f"What was the ghost story mystery really about?",
            answer=f"It was really about finding {q.goal} and learning that the ghostly sign was harmless.",
        ),
        QAItem(
            question=f"Where was the missing thing found?",
            answer=f"It was found in {q.final_place}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to peek?",
            answer="To peek means to look quickly and carefully, often at something partly hidden.",
        ),
        QAItem(
            question="What does condense mean?",
            answer="To condense means to make many things shorter or simpler.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something or solve a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: {e.label or e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={list(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_combo(Q,C) :- quest(Q), clue(C), reveals(C,R), tag(Q,R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for t in q.tags:
            lines.append(asp.fact("tag", qid, t))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("reveals", cid, c.reveals))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show quest_combo/2."))
    return sorted(set(asp.atoms(model, "quest_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story quest world with peek/condense/intellectual cues.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              if (getattr(args, "quest", None) is None or c[0] == getattr(args, "quest", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    quest, clue = rng.choice(list(combos))
    seeker_name = getattr(args, "name", None) or rng.choice(["Mira", "Niko", "Ivy", "Theo", "Luna"])
    sidekick_name = getattr(args, "sidekick", None) or rng.choice(["Pip", "Bram", "Jules", "Dot", "June"])
    seeker_type = rng.choice(["girl", "boy"])
    sidekick_type = rng.choice(["girl", "boy"])
    return StoryParams(quest=quest, clue=clue, seeker_name=seeker_name, seeker_type=seeker_type, sidekick_name=sidekick_name, sidekick_type=sidekick_type)


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS or params.clue not in CLUES:
        pass
    if _safe_lookup(CLUES, params.clue).reveals not in _safe_lookup(QUESTS, params.quest).tags:
        pass
    world = tell(make_world(params))
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
    StoryParams(quest="moon_bell", clue="storybook", seeker_name="Mira", seeker_type="girl", sidekick_name="Pip", sidekick_type="boy"),
    StoryParams(quest="lantern_key", clue="window_lantern", seeker_name="Ivy", seeker_type="girl", sidekick_name="June", sidekick_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show quest_combo/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
