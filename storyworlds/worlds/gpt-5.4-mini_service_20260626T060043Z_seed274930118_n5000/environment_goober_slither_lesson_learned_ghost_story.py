#!/usr/bin/env python3
"""
storyworlds/worlds/environment_goober_slither_lesson_learned_ghost_story.py
===========================================================================

A small spooky storyworld: a child in a haunted environment meets a goober that
likes to slither, mistakes fear for danger, and learns a lesson in the end.

The premise is intentionally close to a ghost-story shape:
- a dim environment
- an odd goober appearing by a soft slither
- a frightened first reaction
- a careful turn toward kindness
- a lesson learned that changes the ending image

The world is state-driven: light, fear, trust, and movement all matter.
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

    child: object | None = None
    ghost: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    mood: str
    can_echo: bool = False
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
class Creature:
    id: str
    label: str
    phrase: str
    slither: str
    lesson: str
    friendly: bool
    tiny: bool = True
    kind: str = "character"
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
class StoryParams:
    place: str
    creature: str
    name: str
    gender: str
    parent: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "attic": Setting(place="the attic", mood="dusty and dim", can_echo=True),
    "hallway": Setting(place="the hallway", mood="quiet and narrow", can_echo=True),
    "garden": Setting(place="the moonlit garden", mood="still and silver", can_echo=False),
    "cellar": Setting(place="the cellar", mood="cool and shadowy", can_echo=True),
}

CREATURES = {
    "goober": Creature(
        id="goober",
        label="goober",
        phrase="a little goober with a round wobble and a shy blink",
        slither="slither softly",
        lesson="not every strange thing is a scary thing",
        friendly=True,
    ),
    "ghost": Creature(
        id="ghost",
        label="ghost",
        phrase="a pale ghost with a loose, whispery drift",
        slither="drift like a ribbon",
        lesson="kindness can calm a frightened room",
        friendly=True,
    ),
    "slitherer": Creature(
        id="slitherer",
        label="slitherer",
        phrase="a long slitherer that gleamed like wet moonlight",
        slither="slither under the door",
        lesson="slow steps can be safe steps",
        friendly=True,
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Tess", "Nora", "Eden"]
BOY_NAMES = ["Finn", "Owen", "Theo", "Milo", "Eli", "Hugo"]
PARENTS = ["mother", "father"]
TRAITS = ["brave", "curious", "gentle", "shy", "careful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story world with an environment, a goober, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, creature) for place in SETTINGS for creature in CREATURES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "creature", None) is None:
        pass
    if getattr(args, "creature", None) and getattr(args, "place", None) is None:
        pass
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "creature", None):
        combos = [c for c in combos if c[1] == getattr(args, "creature", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, creature = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    return StoryParams(place=place, creature=creature, name=name, gender=gender, parent=parent)


def _sentence_end(text: str) -> str:
    return text if text.endswith((".", "!", "?")) else text + "."


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    creature = _safe_lookup(CREATURES, params.creature)
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    ghost = world.add(Entity(
        id=creature.id,
        kind="character",
        type="thing",
        label=creature.label,
        phrase=creature.phrase,
    ))

    child.meters["light"] = 1.0
    child.memes["curiosity"] = 1.0
    child.memes["fear"] = 0.0
    child.memes["lesson"] = 0.0
    ghost.meters["drift"] = 1.0
    ghost.memes["loneliness"] = 1.0
    ghost.memes["fear"] = 0.0

    world.say(
        f"{child.id} lived near {setting.place} in an environment that felt {setting.mood}."
    )
    world.say(
        f"One night, when the air was quiet and the floorboards held their breath, "
        f"{child.id} saw {creature.phrase} near the dark window."
    )
    world.say(
        f"It did not stomp or shout. It began to {creature.slither} across the floor, "
        f"and that made the room feel even stranger."
    )

    child.memes["fear"] += 1.0
    if setting.can_echo:
        child.meters["sound"] = 1.0
        world.say(
            f"{child.id} gasped, and the little sound echoed in {setting.place}, making the shadows seem taller."
        )
    else:
        world.say(
            f"{child.id} gasped, but the moonlit garden only answered with a soft rustle in the leaves."
        )

    world.para()
    world.say(
        f"{params.parent.capitalize()} came close and held up a hand. "
        f"\"Look carefully,\" {parent.pronoun('subject')} said, \"sometimes a strange shape is only a lonely one.\""
    )
    child.memes["fear"] += 0.5
    child.memes["curiosity"] += 0.5
    ghost.memes["loneliness"] += 0.5

    world.say(
        f"{child.id} watched again and noticed that {creature.label} was not hiding claws or teeth. "
        f"It only had a damp patch on its side, as if it had been caught in the cold."
    )
    child.meters["care"] = 1.0
    ghost.memes["trust"] += 1.0
    child.memes["fear"] = max(0.0, child.memes["fear"] - 0.5)

    world.para()
    world.say(
        f"{child.id} took a small lantern from the shelf and set it on the floor. "
        f"The warm light made the {creature.label}'s wobble look round and almost funny."
    )
    world.say(
        f"Then {child.id} said, \"You can stay here for a moment. You do not have to be scary.\""
    )
    child.memes["lesson"] += 1.0
    ghost.memes["joy"] = 1.0

    if creature.friendly:
        world.say(
            f"The {creature.label} gave a tiny, grateful blink and {creature.slither} more gently, "
            f"as if it had been waiting for someone to speak kindly."
        )
    else:
        world.say(
            f"The {creature.label} paused, and the room grew very still, as though it was waiting to learn what to do next."
        )

    world.para()
    world.say(
        f"In the end, {child.id} was not chasing a monster at all. {child.id} was keeping company with "
        f"{creature.phrase}, and the fear in the room had a place to go."
    )
    world.say(
        f"{child.id} learned a lesson: in a quiet environment, a careful look and a kind word can turn a ghost story into a good night."
    )

    world.facts = {
        "child": child,
        "parent": parent,
        "creature": ghost,
        "creature_cfg": creature,
        "setting": setting,
        "lesson": "learned",
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    creature = _safe_fact(world, f, "creature_cfg")
    setting = _safe_fact(world, f, "setting")
    return [
        f'Write a short ghost story for a young child about {child.id} in {setting.place}, with a {creature.label} that likes to slither.',
        f"Tell a spooky but gentle story where {child.id} thinks the environment is scary, then learns that the {creature.label} needs kindness.",
        f'Write a simple story with the words "environment", "goober", and "slither", ending with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    creature = _safe_fact(world, f, "creature_cfg")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Where did {child.id} see the {creature.label}?",
            answer=f"{child.id} saw the {creature.label} in {setting.place}, where the environment felt {setting.mood}.",
        ),
        QAItem(
            question=f"Why did {child.id} feel scared at first?",
            answer=f"{child.id} felt scared because the {creature.label} was strange, quiet, and began to {creature.slither}.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer=f"{child.id} learned that {creature.lesson}.",
        ),
        QAItem(
            question=f"What did {params_name(world)} do to help the room feel safer?",
            answer=f"{params_name(world)} set down a little lantern and spoke kindly, which helped turn fear into trust.",
        ),
    ]


def params_name(world: World) -> str:
    return world.facts["child"].id


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an environment?",
            answer="An environment is the place and conditions around something, like a room, a garden, or the air in a story.",
        ),
        QAItem(
            question="What does it mean to slither?",
            answer="To slither means to move smoothly along a surface, like something sliding or wriggling close to the ground.",
        ),
        QAItem(
            question="What is a goober?",
            answer="A goober is a silly, cute little creature or person, often used for something odd but harmless.",
        ),
        QAItem(
            question="Why can a lantern help in a spooky story?",
            answer="A lantern gives warm light, and light can make scary shadows smaller and easier to understand.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="attic", creature="goober", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="hallway", creature="ghost", name="Finn", gender="boy", parent="father"),
    StoryParams(place="garden", creature="slitherer", name="Ivy", gender="girl", parent="mother"),
]


ASP_RULES = r"""
% A story is valid when it has a place and a creature choice.
valid(Place, Creature) :- place(Place), creature(Creature).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CREATURES:
        lines.append(asp.fact("creature", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible place/creature combos:\n")
        for place, creature in combos:
            print(f"  {place:10} {creature}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
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
            header = f"### {p.name}: {p.creature} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
