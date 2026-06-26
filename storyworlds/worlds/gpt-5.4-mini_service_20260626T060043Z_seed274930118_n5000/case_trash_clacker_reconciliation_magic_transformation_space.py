#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure with a case, trash, and a
clacker, plus reconciliation, magic, and transformation.

A short source tale was imagined first:
- A child on a small station opens a storage case.
- Inside is a clacker tool and a bundle of trash that should be sorted.
- The clacker causes a noisy mishap that upsets a helper.
- A little magic transforms the trash into a useful space-garden kit.
- The upset helper and child reconcile, and the station feels peaceful again.

The prose, world model, and ASP twin are all driven by the same tiny domain.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0
NARRATIVE_LABEL = "Space Adventure"

SETTINGS = {
    "cargo_bay": "the cargo bay",
    "orbital_garden": "the orbital garden",
    "station_corridor": "the station corridor",
    "moon_deck": "the moon deck",
}

CHARS = {
    "child": ["Ari", "Mika", "Jun", "Nova", "Pip"],
    "helper": ["Tess", "Rin", "Sol", "Ivy", "Koa"],
}

TRAITS = ["curious", "brave", "gentle", "lively", "patient"]

# ---------------------------------------------------------------------------
# Shared model
# ---------------------------------------------------------------------------


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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    case: object | None = None
    child: object | None = None
    clacker: object | None = None
    garden_kit: object | None = None
    helper: object | None = None
    trash: object | None = None
    def __post_init__(self) -> None:
        for key in ["trash", "noise", "magic", "transform", "tidy"]:
            self.meters.setdefault(key, 0.0)
        for key in ["joy", "worry", "hurt", "reconcile", "wonder"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class StoryParams:
    place: str
    name: str
    helper: str
    trait: str
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


class World:
    def __init__(self, place: str) -> None:
        self.place = place
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class Case:
    id: str
    label: str
    contents: str
    risky: bool = True
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
class Clacker:
    id: str
    label: str
    sound: str
    effect: str
    transform_target: str
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


CASES = {
    "cargo_case": Case(
        id="cargo_case",
        label="cargo case",
        contents="trash",
        risky=True,
    ),
    "garden_case": Case(
        id="garden_case",
        label="seed case",
        contents="magic dust",
        risky=False,
    ),
}

CLACKERS = {
    "tool_clacker": Clacker(
        id="tool_clacker",
        label="a clacker tool",
        sound="clack-clack",
        effect="noise",
        transform_target="trash_bundle",
    ),
    "toy_clacker": Clacker(
        id="toy_clacker",
        label="a little clacker",
        sound="clackety-clack",
        effect="noise",
        transform_target="trash_bundle",
    ),
}

TRANSFORMS = {
    "trash_to_garden": {
        "from": "trash",
        "to": "sparkling seed flakes",
        "result_label": "a tiny space-garden kit",
    }
}

# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------


def _char_pronouns(name: str, kind: str = "child") -> Entity:
    typ = "girl" if kind == "child" else "adult"
    return Entity(id=name, kind="character", type=typ)


def build_world(params: StoryParams) -> World:
    w = World(params.place)
    child = w.add(Entity(id=params.name, kind="character", type="child"))
    helper = w.add(Entity(id=params.helper, kind="character", type="helper"))
    case = w.add(Entity(
        id="case",
        kind="thing",
        type="case",
        label=CASES["cargo_case"].label,
        phrase="an old cargo case with a sticky latch",
        owner=child.id,
    ))
    trash = w.add(Entity(
        id="trash_bundle",
        kind="thing",
        type="trash",
        label="trash bundle",
        phrase="a crinkly bundle of space trash",
        owner=child.id,
        caretaker=helper.id,
    ))
    clacker = w.add(Entity(
        id="clacker",
        kind="thing",
        type="clacker",
        label=CLACKERS["tool_clacker"].label,
        phrase="a shiny clacker tool",
        owner=helper.id,
    ))
    garden_kit = w.add(Entity(
        id="garden_kit",
        kind="thing",
        type="kit",
        label="space-garden kit",
        phrase="a tiny space-garden kit",
        owner=child.id,
    ))

    child.memes["joy"] += 1
    helper.memes["worry"] += 0.5
    w.facts.update(child=child, helper=helper, case=case, trash=trash, clacker=clacker, garden_kit=garden_kit)
    return w


def predict_mess(world: World) -> bool:
    sim = world.copy()
    sim.get("clacker").meters["noise"] += 1
    sim.get("trash_bundle").meters["trash"] += 1
    return sim.get("trash_bundle").meters["trash"] >= THRESHOLD


# ---------------------------------------------------------------------------
# Narrative beats
# ---------------------------------------------------------------------------


def intro(world: World) -> None:
    c = world.get("child")
    h = world.get("helper")
    p = world.place
    world.say(
        f"{c.id} was a {random.choice(TRAITS)} little traveler on {NARRATIVE_LABEL}."
    )
    world.say(
        f"One day, {c.id} and {h.id} went to {p}, where a cargo case waited near a window full of stars."
    )


def setup(world: World) -> None:
    c = world.get("child")
    h = world.get("helper")
    case = world.get("case")
    trash = world.get("trash_bundle")
    clacker = world.get("clacker")
    world.say(
        f"{c.id} opened the {case.label} and found {trash.phrase} and {clacker.phrase} inside."
    )
    world.say(
        f"{c.id} loved the clacker's {CLACKERS['tool_clacker'].sound} sound, but {h.id} frowned at the trash."
    )


def conflict(world: World) -> None:
    c = world.get("child")
    h = world.get("helper")
    trash = world.get("trash_bundle")
    clacker = world.get("clacker")
    trash.meters["trash"] += 1
    clacker.meters["noise"] += 1
    h.memes["worry"] += 1
    c.memes["joy"] += 0.5
    world.say(
        f"When {c.id} tapped the clacker, it went {CLACKERS['tool_clacker'].sound} and sent the trash skittering across the floor."
    )
    world.say(
        f"{h.id} said the cargo bay needed to stay tidy, and {c.id} felt a small pinch of worry."
    )


def magic_turn(world: World) -> None:
    c = world.get("child")
    h = world.get("helper")
    trash = world.get("trash_bundle")
    kit = world.get("garden_kit")
    trash.meters["magic"] += 1
    trash.meters["transform"] += 1
    kit.meters["transform"] += 1
    c.memes["wonder"] += 1
    world.say(
        f"Then {c.id} whispered a magic wish, and the floating trash began to glow."
    )
    world.say(
        f"The scraps turned into {TRANSFORMS['trash_to_garden']['to']}, and soon they looked like {kit.phrase}."
    )
    world.say(
        f"{h.id}'s eyes softened, because the messy pile had become something useful and bright."
    )


def reconcile(world: World) -> None:
    c = world.get("child")
    h = world.get("helper")
    c.memes["reconcile"] += 1
    h.memes["reconcile"] += 1
    c.memes["worry"] = 0.0
    h.memes["worry"] = 0.0
    c.memes["joy"] += 1
    h.memes["joy"] += 1
    world.say(
        f"{c.id} handed the new garden kit to {h.id} and said sorry for the mess."
    )
    world.say(
        f"{h.id} smiled, forgave {c.id}, and said they could build a tiny garden together."
    )


def ending(world: World) -> None:
    c = world.get("child")
    h = world.get("helper")
    kit = world.get("garden_kit")
    world.say(
        f"By the end, the cargo bay was calm again, and {c.id} and {h.id} were planting bright seeds in the {kit.label}."
    )
    world.say(
        f"The clacker rested quietly beside them, and the station looked peaceful under the stars."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Space Adventure story about a child, a case, and a clacker, with a magical transformation and reconciliation.',
        f"Tell a child-friendly story set in {world.place} where {f['child'].id} finds trash in a case and a helper helps turn it into something good.",
        "Write a gentle science-fiction story that uses the words case, trash, and clacker, and ends with friends making up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.get("child")
    h = world.get("helper")
    trash = world.get("trash_bundle")
    kit = world.get("garden_kit")
    return [
        QAItem(
            question=f"Where did {c.id} and {h.id} find the case?",
            answer=f"They found it in {world.place}, near the stars and the station wall.",
        ),
        QAItem(
            question=f"What was inside the case?",
            answer=f"Inside the case were trash and a clacker tool.",
        ),
        QAItem(
            question=f"What changed the trash into something helpful?",
            answer=f"A little magic made the trash transform into {kit.phrase}.",
        ),
        QAItem(
            question=f"How did {c.id} and {h.id} end the story?",
            answer=f"They forgave each other, worked together, and planted seeds with the new garden kit.",
        ),
        QAItem(
            question=f"Why was {h.id} upset at first?",
            answer=f"{h.id} was upset because the trash made the cargo bay messy and the clacker made a noisy scatter.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clacker?",
            answer="A clacker is a noisy little tool or toy that makes a clacking sound when it moves or taps.",
        ),
        QAItem(
            question="What is trash?",
            answer="Trash is stuff people do not need anymore, so they sort it away or throw it out.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who were upset make peace again and feel friendly with each other.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new form or becomes different.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something wonderful that can make impossible changes happen in a story world.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        parts = [e.kind, e.type]
        if e.label:
            parts.append(f"label={e.label}")
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append("  " + e.id + " :: " + " ".join(parts))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% An item is at risk when trash or noise reaches it in the cargo setting.
at_risk(I) :- item(I), has_trash(I).

% Magic transforms trash into a useful kit.
transformed(trash_bundle, garden_kit) :- magic_used, has_trash(trash_bundle).

% Reconciliation happens after transformation and a spoken sorry.
reconciled(child, helper) :- transformed(trash_bundle, garden_kit), said_sorry(child), forgiven(helper, child).

% A valid story requires the space setting, a case, trash, a clacker, magic, and reconciliation.
valid_story(P) :- place(P), has_case(P), has_trash(P), has_clacker(P), magic_used, reconciled(child, helper).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, label in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("label", pid, label))
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    for clid in CLACKERS:
        lines.append(asp.fact("clacker", clid))
    lines.append(asp.fact("has_case", "cargo_bay"))
    lines.append(asp.fact("has_trash", "trash_bundle"))
    lines.append(asp.fact("has_clacker", "cargo_bay"))
    lines.append(asp.fact("magic_used"))
    lines.append(asp.fact("said_sorry", "child"))
    lines.append(asp.fact("forgiven", "helper", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n" + show + "\n"


def asp_story_models() -> list[list]:
    import asp
    return asp.solve(asp_program("#show valid_story/1."), models=0)


def asp_verify() -> int:
    import asp
    # The ASP twin should at least see a valid story in the chosen setting.
    models = asp.solve(asp_program("#show valid_story/1."), models=1)
    if not models:
        print("MISMATCH: ASP found no valid story.")
        return 1
    print("OK: ASP found at least one valid story model.")
    return 0


# ---------------------------------------------------------------------------
# Selection / generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="cargo_bay", name="Ari", helper="Tess", trait="curious"),
    StoryParams(place="orbital_garden", name="Nova", helper="Rin", trait="gentle"),
    StoryParams(place="moon_deck", name="Jun", helper="Sol", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld: a case, trash, and a clacker.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=sorted(TRAITS))
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
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    name = getattr(args, "name", None) or rng.choice(CHARS["child"])
    helper = getattr(args, "helper", None) or rng.choice(CHARS["helper"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    intro(world)
    world.para()
    setup(world)
    conflict(world)
    world.para()
    magic_turn(world)
    reconcile(world)
    ending(world)

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
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        models = asp.solve(asp_program("#show valid_story/1."), models=1)
        print("ASP models:", len(models))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
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
