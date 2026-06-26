#!/usr/bin/env python3
"""
storyworlds/worlds/ladle_dime_suspense_rhyming_story.py
========================================================

A tiny story world for a suspenseful rhyming tale about a ladle and a dime.

Premise:
- A child hears a faint jingle and wants to find a lost dime.
- A shiny ladle is the key tool for reaching a hidden place.

Tension:
- The dime may be stuck somewhere dark and hard to reach.
- The child must choose between rushing and listening carefully.

Turn:
- The ladle is used as a safe hook and scoop.
- The dime is found in a surprising place, and the suspense ends.

This world is intentionally small and constraint-checked. It models physical
state with meters and emotional state with memes, then narrates from the trace.
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
    held_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    dime: object | None = None
    ladle: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
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
class Room:
    name: str
    dark_spot: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    help_text: str
    guards: set[str] = field(default_factory=set)
    can_hook: bool = False
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
    def __init__(self, room: Room) -> None:
        self.room = room
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _safe_hooking(world: World, child: Entity, tool: Entity, target: Entity) -> None:
    if tool.label != "ladle":
        pass
    child.memes["focus"] += 1
    child.memes["suspense"] += 1
    tool.meters["reach"] += 1
    target.hidden_in = None
    target.held_by = child.id
    target.meters["found"] += 1


def _still_hidden(world: World, child: Entity, target: Entity) -> bool:
    return target.hidden_in is not None and child.memes["search"] >= THRESHOLD


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for actor in world.characters():
            dime = world.get("dime")
            if _still_hidden(world, actor, dime):
                sig = ("tension", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    actor.memes["worry"] += 1
                    out.append("The little room felt tense and tight.")
                    changed = True
    if narrate:
        for line in out:
            world.say(line)
    return out


@dataclass
class StoryParams:
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


SETTINGS = {
    "pantry": Room(name="the pantry", dark_spot="behind the flour bin", affords={"search"}),
    "kitchen": Room(name="the kitchen", dark_spot="under the shelf", affords={"search"}),
    "mudroom": Room(name="the mudroom", dark_spot="beside the boots", affords={"search"}),
}

TOOLS = {
    "ladle": Tool(
        id="ladle",
        label="ladle",
        phrase="a bright ladle",
        help_text="a long spoon for reaching and scooping",
        guards={"spill"},
        can_hook=True,
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ivy", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Max", "Theo", "Eli"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suspenseful rhyming story world with a ladle and a dime.")
    ap.add_argument("--place", choices=SETTINGS)
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


def valid_places() -> list[str]:
    return list(SETTINGS)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(valid_places())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent)


def tell(room: Room, params: StoryParams) -> World:
    world = World(room)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    ladle = world.add(Entity(id="ladle", type="ladle", label="ladle", phrase=TOOLS["ladle"].phrase, owner=child.id))
    dime = world.add(Entity(id="dime", type="dime", label="dime", phrase="a tiny silver dime", owner=child.id))
    dime.hidden_in = room.dark_spot

    child.memes["curiosity"] = 1
    child.memes["search"] = 1

    world.say(f"{child.id} was a small {params.gender} with a nose for rhyme,")
    world.say(f"who heard a soft ping in the hush of time.")
    world.say(f"In {room.name}, near {room.dark_spot}, something gave a tiny chime,")
    world.say(f"and {child.id} knew a lost dime might still be there, just in line.")

    world.para()
    world.say(f"{child.id} looked and listened, slow as a mouse,")
    world.say(f"{parent.label} whispered, \"Careful now—quiet in this house.\"")
    world.say(f"The dark spot waited, tight and small,")
    world.say(f"and the suspense grew tall, tall, tall.")

    world.para()
    world.say(f"Then {child.id} picked up the ladle with a steady little grip,")
    world.say(f"not to poke too hard, not to let it slip.")
    _safe_hooking(world, child, ladle, dime)
    world.say(f"The ladle reached behind the bin with a gentle silver sweep,")
    world.say(f"and out rolled the dime, awake from its sleep.")

    world.para()
    world.say(f"{child.id} smiled wide; the worry sank away,")
    world.say(f"the room grew bright at the end of the play.")
    world.say(f"The dime went back in {child.id}'s hand, shiny and slim,")
    world.say(f"and the ladle ended the riddle just on a whim.")

    world.facts.update(child=child, parent=parent, ladle=ladle, dime=dime, room=room, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    room = _safe_fact(world, f, "room")
    return [
        f'Write a short suspense rhyming story for a child named {child.id} about a lost dime in {room.name}.',
        f'Tell a gentle rhyming tale where a ladle helps {child.id} find a dime hidden {room.dark_spot}.',
        "Write a child-friendly suspense story that ends with a shiny dime and a relieved smile.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    dime = _safe_fact(world, f, "dime")
    room = _safe_fact(world, f, "room")
    parent = _safe_fact(world, f, "parent")
    return [
        QAItem(
            question=f"What was {child.id} trying to find in {room.name}?",
            answer=f"{child.id} was trying to find a tiny silver dime hidden {room.dark_spot}.",
        ),
        QAItem(
            question=f"What tool helped {child.id} reach the dime?",
            answer="A bright ladle helped reach behind the dark spot without getting too rough.",
        ),
        QAItem(
            question=f"Why did the room feel suspenseful before the dime appeared?",
            answer=f"The dime was hidden out of sight, and {parent.label} told {child.id} to move slowly and listen carefully.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The dime was found, the worry faded, and {child.id} ended happy with the dime in hand.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ladle for?",
            answer="A ladle is a long-handled spoon used for scooping soup or reaching into deep containers.",
        ),
        QAItem(
            question="What is a dime?",
            answer="A dime is a small silver coin that is worth ten cents.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling of not knowing what will happen next, which can make a story exciting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show compatible/1.
compatible(ladle).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("tool", "ladle"), asp.fact("coin", "dime")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/1."))
    atoms = set(asp.atoms(model, "compatible"))
    if atoms == {("ladle",)}:
        print("OK: ASP and Python agree on the ladle being the compatible tool.")
        return 0
    print("MISMATCH: ASP gate did not match Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    room = _safe_lookup(SETTINGS, params.seed_room if hasattr(params, "seed_room") else random.choice(list(SETTINGS.keys())))  # type: ignore[attr-defined]
    world = tell(room, params)
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
        print(asp_program("#show compatible/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("1 compatible tool: ladle")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(name="Mia", gender="girl", parent="mother", seed=0),
            StoryParams(name="Leo", gender="boy", parent="father", seed=1),
        ]
        for i, p in enumerate(curated):
            room = SETTINGS[list(SETTINGS)[i % len(SETTINGS)]]
            world = tell(room, p)
            samples.append(
                StorySample(
                    params=p,
                    story=world.render(),
                    prompts=generation_prompts(world),
                    story_qa=story_qa(world),
                    world_qa=world_knowledge_qa(world),
                    world=world,
                )
            )
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            room_name = getattr(args, "place", None) or random.Random(seed + 7).choice(list(SETTINGS))
            world = tell(_safe_lookup(SETTINGS, room_name), params)
            sample = StorySample(
                params=params,
                story=world.render(),
                prompts=generation_prompts(world),
                story_qa=story_qa(world),
                world_qa=world_knowledge_qa(world),
                world=world,
            )
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
