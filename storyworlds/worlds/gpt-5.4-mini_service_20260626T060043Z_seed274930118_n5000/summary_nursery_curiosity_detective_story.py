#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/summary_nursery_curiosity_detective_story.py
===============================================================================================================

A tiny detective story world set in a nursery, where curiosity helps solve a
small mystery. The domain is built around a child detective, a missing nursery
object, clues, and a gentle reveal.

Story seed summary:
- A curious child notices something missing in the nursery.
- They look for clues with a parent or helper.
- Their curiosity leads them to the hidden item.
- The ending proves what changed in the world.

The style stays close to a detective story, but the world remains simple and
child-friendly.
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
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue_ent: object | None = None
    detective: object | None = None
    helper: object | None = None
    missing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman", "sister"}
        masculine = {"boy", "father", "dad", "man", "brother"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
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
class Setting:
    place: str = "the nursery"
    cozy: bool = True
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
class Clue:
    kind: str
    label: str
    place: str
    reveal_word: str
    memos: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    missing_label: str
    missing_phrase: str
    hidden_place: str
    clue_kind: str
    solve_action: str
    solve_verb: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

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
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _r_find_hidden(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.hidden and ent.meters.get("found", 0) >= THRESHOLD:
            sig = ("found", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.hidden = False
            out.append(f"The missing {ent.label} was finally found.")
    return out


def _r_clue_to_answer(world: World) -> list[str]:
    out = []
    detective = world.facts.get("detective")
    clue = world.facts.get("clue")
    missing = world.facts.get("missing")
    if not detective or not clue or not missing:
        return out
    if detective.memes.get("curiosity", 0) < THRESHOLD:
        return out
    if clue.meters.get("noticed", 0) < THRESHOLD:
        return out
    sig = ("answer", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    missing.meters["found"] = 1
    out.append("The clue led the detective to the answer.")
    return out


CAUSAL_RULES = [_r_clue_to_answer, _r_find_hidden]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule(world)
            if got:
                changed = True
                out.extend(got)
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    helper_gender: str
    mystery: str
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
    "nursery": Setting(place="the nursery", cozy=True, afford={"look", "search", "peek"}),
    "playroom": Setting(place="the playroom", cozy=True, afford={"look", "search", "peek"}),
}

MYSTERIES = {
    "bear": Mystery(
        id="bear",
        missing_label="bear",
        missing_phrase="the blue teddy bear",
        hidden_place="under the blanket",
        clue_kind="blanket",
        solve_action="lift the blanket",
        solve_verb="lifted",
        tags={"nursery", "soft", "hidden"},
    ),
    "star": Mystery(
        id="star",
        missing_label="star sticker",
        missing_phrase="the shiny star sticker",
        hidden_place="behind the storybook",
        clue_kind="storybook",
        solve_action="move the storybook",
        solve_verb="moved",
        tags={"nursery", "bright", "hidden"},
    ),
    "rattle": Mystery(
        id="rattle",
        missing_label="rattle",
        missing_phrase="the red rattle",
        hidden_place="inside the toy basket",
        clue_kind="basket",
        solve_action="check the toy basket",
        solve_verb="checked",
        tags={"nursery", "noisy", "hidden"},
    ),
}

CLUES = {
    "blanket": Clue(kind="blanket", label="a blanket wrinkle", place="the crib", reveal_word="blanket", memos={"soft"}),
    "storybook": Clue(kind="storybook", label="a page corner sticking out", place="the shelf", reveal_word="storybook", memos={"quiet"}),
    "basket": Clue(kind="basket", label="a little rattle sound", place="the toy basket", reveal_word="basket", memos={"noisy"}),
}

CHILD_NAMES = ["Mia", "Noah", "Lily", "Theo", "Ava", "Finn", "Nora", "Eli"]
HELPER_NAMES = ["Mom", "Dad", "Aunt June", "Mr. Ben"]
TRAITS = ["curious", "careful", "clever", "brave"]


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS["nursery"] if params.mystery in MYSTERIES else SETTINGS["playroom"]
    world = World(setting)

    mystery = _safe_lookup(MYSTERIES, params.mystery)
    clue = _safe_lookup(CLUES, mystery.clue_kind)

    detective = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={"curiosity": 1.0}))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, meters={}, memes={"care": 1.0}))
    missing = world.add(Entity(id=mystery.id, type="toy", label=mystery.missing_label, phrase=mystery.missing_phrase, hidden=True))
    clue_ent = world.add(Entity(id=f"clue_{clue.kind}", type="clue", label=clue.label, phrase=clue.label, hidden=False))

    world.facts.update(
        detective=detective,
        helper=helper,
        missing=missing,
        clue=clue_ent,
        mystery=mystery,
        clue_def=clue,
    )
    return world


def intro(world: World) -> None:
    d = _safe_fact(world, world.facts, "detective")
    m = _safe_fact(world, world.facts, "mystery")
    world.say(
        f"{d.id} was a little detective with a very curious mind, and {d.pronoun('possessive')} eyes "
        f"loved spotting small details in the nursery."
    )
    world.say(
        f"One morning, {d.id} noticed that {m.missing_phrase} was gone."
    )


def suspicion(world: World) -> None:
    d = _safe_fact(world, world.facts, "detective")
    h = _safe_fact(world, world.facts, "helper")
    m = _safe_fact(world, world.facts, "mystery")
    c = _safe_fact(world, world.facts, "clue_def")
    world.para()
    world.say(
        f"{d.id} looked low and high, then found {c.label} near {c.place}."
    )
    world.say(
        f"{d.id} told {h.id}, 'I think the clue points to {m.hidden_place}.'"
    )
    d.memes["curiosity"] += 1
    c_ent = _safe_fact(world, world.facts, "clue")
    c_ent.meters["noticed"] = 1


def solve(world: World) -> None:
    d = _safe_fact(world, world.facts, "detective")
    h = _safe_fact(world, world.facts, "helper")
    m = _safe_fact(world, world.facts, "mystery")
    c = _safe_fact(world, world.facts, "clue_def")
    world.para()
    world.say(
        f"{d.id} {m.solve_verb} {c.solve_action}."
    )
    world.say(
        f"Right there, {d.pronoun('object')} found {m.missing_phrase}."
    )
    propagate(world, narrate=False)
    world.say(
        f"{h.id} smiled, and the nursery felt calm again."
    )
    world.say(
        f"{m.missing_phrase.capitalize()} was back where it belonged, and {d.id}'s curiosity had solved the case."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    suspicion(world)
    solve(world)
    world.facts["solved"] = not world.facts["missing"].hidden
    return world


KNOWLEDGE = {
    "nursery": [
        ("What is a nursery?", "A nursery is a room for little children, with toys, soft things, and places to rest."),
    ],
    "curious": [
        ("What does it mean to be curious?", "Curious means you want to find out more and ask questions about things."),
    ],
    "detective": [
        ("What does a detective do?", "A detective looks for clues and uses careful thinking to solve a mystery."),
    ],
    "clue": [
        ("What is a clue?", "A clue is a small piece of information that can help solve a mystery."),
    ],
    "toy": [
        ("Why do children keep toys in baskets?", "Toys are often kept in baskets so the room stays tidy and the toys are easy to find."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d = _safe_fact(world, f, "detective")
    m = _safe_fact(world, f, "mystery")
    return [
        f'Write a short detective story for a child about a curious detective in a nursery who notices that {m.missing_phrase} is missing.',
        f"Tell a gentle nursery mystery where {d.id} follows a clue and finds {m.missing_phrase}.",
        f'Write a story with the words "summary" and "nursery" where curiosity helps solve a small detective case.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = _safe_fact(world, f, "detective")
    h = _safe_fact(world, f, "helper")
    m = _safe_fact(world, f, "mystery")
    c = _safe_fact(world, f, "clue_def")
    return [
        QAItem(
            question=f"What was missing in the nursery?",
            answer=f"{m.missing_phrase} was missing from the nursery.",
        ),
        QAItem(
            question=f"Who noticed the clue first?",
            answer=f"{d.id} noticed the clue first because {d.pronoun('possessive')} curiosity made {d.pronoun('object')} look carefully.",
        ),
        QAItem(
            question=f"How did {d.id} solve the case?",
            answer=f"{d.id} followed the clue near {c.place}, then {m.solve_action} and found {m.missing_phrase}.",
        ),
        QAItem(
            question=f"What did {h.id} do at the end?",
            answer=f"{h.id} smiled when the missing item was found and the nursery was calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(["nursery", "curious", "detective", "clue", "toy"])
    for tag in ["nursery", "curious", "detective", "clue", "toy"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery detective story world driven by curiosity.")
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--mystery", choices=MYSTERIES)
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
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["girl", "boy"])
    return StoryParams(name=name, gender=gender, helper=helper, helper_gender=helper_gender, mystery=mystery)


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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for m in MYSTERIES:
            combos.append((place, m))
    return combos


ASP_RULES = r"""
valid(Place, M) :- setting(Place), mystery(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(name="Mia", gender="girl", helper="Mom", helper_gender="girl", mystery="bear"),
    StoryParams(name="Theo", gender="boy", helper="Dad", helper_gender="boy", mystery="star"),
    StoryParams(name="Nora", gender="girl", helper="Aunt June", helper_gender="girl", mystery="rattle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for p, m in asp_valid_combos():
            print(p, m)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
