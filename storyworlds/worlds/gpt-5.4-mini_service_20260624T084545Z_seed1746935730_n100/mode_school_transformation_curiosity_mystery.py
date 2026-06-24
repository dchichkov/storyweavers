#!/usr/bin/env python3
"""
storyworlds/worlds/mode_school_transformation_curiosity_mystery.py
==================================================================

A small school storyworld about curiosity, a mystery clue, and a gentle
transformation.

Core premise:
- A curious child at school notices a strange "mode" on an object.
- The child wants to investigate, but the teacher worries that the mystery
  object might be broken or lost.
- The child follows clues through the school and discovers that the object
  changes safely into a better form.
- The ending proves the change with a concrete new image.

This world keeps the prose close to mystery: clues, noticing, careful looking,
and a reveal. The transformation is physical and state-driven, not just a
word swap.
"""

from __future__ import annotations

import argparse
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
    plural: bool = False
    modes: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    item: object | None = None
    teacher: object | None = None
    def __post_init__(self) -> None:
        for key in ("curiosity", "worry", "relief", "joy", "confusion", "attention", "transformed"):
            self.memes.setdefault(key, 0.0)
        for key in ("bright", "plain", "moved", "hidden"):
            self.meters.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "student", "child"}
        male = {"boy"}
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
    place: str = "the school"
    rooms: list[str] = field(default_factory=lambda: ["the classroom", "the hallway", "the library"])
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
class MysteryItem:
    id: str
    label: str
    phrase: str
    start_state: str
    end_state: str
    clue: str
    reveal: str
    mode: str
    room: str
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
class StoryParams:
    place: str
    item: str
    name: str
    gender: str
    role: str
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
        self.trace: list[str] = []

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "school": Setting(place="the school", rooms=["the classroom", "the hallway", "the library"]),
}

ITEMS = {
    "chalkbox": MysteryItem(
        id="chalkbox",
        label="chalk box",
        phrase="a plain chalk box with a tiny dial",
        start_state="plain",
        end_state="bright",
        clue="a streak of colored dust on the lid",
        reveal="the lid opened and the chalks changed into bright rainbow pieces",
        mode="color mode",
        room="the classroom",
        tags={"chalk", "mode", "color", "mystery"},
    ),
    "map": MysteryItem(
        id="map",
        label="map board",
        phrase="a folded map board with a hidden flap",
        start_state="hidden",
        end_state="open",
        clue="a corner of paper sticking out near the library shelf",
        reveal="the flap lifted and the map showed a secret path through the school",
        mode="find mode",
        room="the library",
        tags={"map", "mode", "hidden", "mystery"},
    ),
    "robot": MysteryItem(
        id="robot",
        label="class robot",
        phrase="a small class robot with a sticker that said mode",
        start_state="quiet",
        end_state="helpful",
        clue="its wheels had dust from the hallway",
        reveal="the robot woke up in helper mode and rolled out with a tray of crayons",
        mode="helper mode",
        room="the hallway",
        tags={"robot", "mode", "help", "mystery"},
    ),
    "lantern": MysteryItem(
        id="lantern",
        label="paper lantern",
        phrase="a paper lantern with a little switch",
        start_state="dim",
        end_state="glowing",
        clue="a warm glow showed under the art-room door",
        reveal="the lantern lit up and turned into a glowing star for story time",
        mode="glow mode",
        room="the classroom",
        tags={"light", "mode", "glow", "mystery"},
    ),
}

NAMES = {
    "girl": ["Mia", "Nora", "Lily", "Zoe", "Ava", "Ivy"],
    "boy": ["Leo", "Finn", "Noah", "Max", "Ben", "Eli"],
}
ROLES = ["student", "pupil", "kid"]


ASP_RULES = r"""
% An item is mysterious when a curious child notices a clue in the right room.
mysterious(I) :- item(I), clue(I,_), room(I,R), in_room(C,R), curious(C).

% A valid story needs a real room path and a transformation from start to end.
transforms(I) :- item(I), start(I,S), end(I,E), S != E.

valid_story(P, I, G) :- place(P), item(I), gender(G), school(P), transforms(I), mysterious(I).
"""


@dataclass
class State:
    child: Entity
    teacher: Entity
    item: Entity
    current_room: str
    clue_seen: bool = False
    transformed: bool = False
    resolved: bool = False
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


def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a {child.type} at {world.setting.place} who noticed small details."
    )


def establish_item(world: World, item: Entity) -> None:
    world.say(
        f"In the {world.facts['item_room']}, there was {item.phrase}."
    )
    world.say(
        f"It looked ordinary at first, but one little word on it said mode."
    )


def curiosity(world: World, child: Entity, item: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} leaned closer, because {child.pronoun('subject')} wanted to know why {item.label} felt strange."
    )


def clue(world: World, child: Entity, item: Entity) -> None:
    child.meters["attention"] += 1
    world.say(
        f"Then {child.id} noticed {world.facts['clue']}. That was the first clue."
    )


def teacher_warning(world: World, teacher: Entity, child: Entity, item: Entity) -> None:
    teacher.memes["worry"] += 1
    world.say(
        f"{teacher.id} said, \"Be careful. We do not want to lose {item.label} before we understand it.\""
    )


def move_to_room(world: World, child: Entity, room: str) -> None:
    child.meters["moved"] += 1
    world.say(f"{child.id} followed the clue to {room}.")


def reveal(world: World, child: Entity, item: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    item.meters["bright"] += 1
    item.meters["hidden"] = 0.0
    world.say(
        f"At last, {world.facts['reveal']}. {child.id} smiled, because the mystery now made sense."
    )


def end_image(world: World, child: Entity, item: Entity) -> None:
    world.say(
        f"By the end, {child.id} was looking at {item.phrase} in its new {world.facts['end_state']} mode, and the school felt cheerful and calm."
    )


def tell(setting: Setting, item_cfg: MysteryItem, name: str, gender: str, role: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=role))
    teacher = world.add(Entity(id="Teacher", kind="character", type="adult", label="the teacher"))
    item = world.add(Entity(id=item_cfg.id, type="thing", label=item_cfg.label, phrase=item_cfg.phrase, owner=child.id))

    world.facts.update(
        item_room=item_cfg.room,
        clue=item_cfg.clue,
        reveal=item_cfg.reveal,
        end_state=item_cfg.end_state,
        mode=item_cfg.mode,
        gender=gender,
        name=name,
        role=role,
        item=item_cfg,
    )

    introduce(world, child)
    world.para()
    establish_item(world, item)
    curiosity(world, child, item)
    teacher_warning(world, teacher, child, item)
    world.para()
    move_to_room(world, child, item_cfg.room)
    clue(world, child, item)
    world.para()
    reveal(world, child, item)
    end_image(world, child, item)

    child.meters["bright"] += 1
    child.memes["transformed"] += 1
    world.facts["resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for item_id in ITEMS:
            out.append((place, item_id))
    return out


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
        lines.append(asp.fact("school", place))
        for room in _safe_lookup(SETTINGS, place).rooms:
            lines.append(asp.fact("room", room))
            lines.append(asp.fact("in_school", place, room))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("room", item_id, item.room))
        lines.append(asp.fact("start", item_id, item.start_state))
        lines.append(asp.fact("end", item_id, item.end_state))
        lines.append(asp.fact("clue", item_id, item.clue))
        lines.append(asp.fact("mode", item_id, item.mode))
        for tag in sorted(item.tags):
            lines.append(asp.fact("tag", item_id, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((p, i, "girl") for p, i in valid_combos()) | set((p, i, "boy") for p, i in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} story combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="School mystery storyworld with a small transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [(p, i) for p, i in combos if p == getattr(args, "place", None)]
    if getattr(args, "item", None):
        combos = [(p, i) for p, i in combos if i == getattr(args, "item", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, item_id = rng.choice(combos)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    role = getattr(args, "role", None) or rng.choice(ROLES)
    return StoryParams(place=place, item=item_id, name=name, gender=gender, role=role)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item"]
    return [
        f'Write a short mystery story for a child at {f["item_room"]} about "{item.mode}" and a careful clue.',
        f"Tell a gentle school story where {f['name']} follows a clue, asks questions, and discovers how {item.label} changes.",
        f"Write a mystery about a curious {f['role']} at {world.setting.place} that ends with {item.phrase} in a new mode.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    item = f["item"]
    return [
        QAItem(
            question=f"What did {f['name']} want to know about the {item.label}?",
            answer=f"{f['name']} wanted to know why the {item.label} had a strange mode and seemed different from an ordinary school object.",
        ),
        QAItem(
            question=f"What clue helped {f['name']} solve the mystery?",
            answer=f"The clue was {f['clue']}. It showed that the {item.label} had been changed on purpose, not lost.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"{f['reveal']}. That is how the mystery ended with a safe transformation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you do not understand right away, so you look for clues to figure it out.",
        ),
        QAItem(
            question="What does curious mean?",
            answer="Curious means wanting to know more and asking questions to learn something new.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ITEMS, params.item), params.name, params.gender, params.role)
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
    StoryParams(place="school", item="chalkbox", name="Mia", gender="girl", role="student"),
    StoryParams(place="school", item="robot", name="Leo", gender="boy", role="pupil"),
    StoryParams(place="school", item="map", name="Nora", gender="girl", role="kid"),
    StoryParams(place="school", item="lantern", name="Finn", gender="boy", role="student"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for p, i, g in combos:
            print(f"  {p:8} {i:10} {g}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
