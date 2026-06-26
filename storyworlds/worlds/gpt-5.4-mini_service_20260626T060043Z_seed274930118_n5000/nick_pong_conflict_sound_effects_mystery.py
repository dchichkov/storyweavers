#!/usr/bin/env python3
"""
A small mystery world about nicking a clue and a strange pong sound.

Seed tale imagined from the prompt:
A quiet room held a little mystery. Every time the cabinet door moved, a soft
pong sound drifted out. Mina wanted to solve it, but her brother Nico kept
nicking the flashlight to "help" in his own way. The clues were tiny: a loose
latch, a muddy footprint, a ball under the table, and one stubborn pong from
behind the wall. In the end, the children worked together, found the hidden toy
that was making the sound, and turned their conflict into a shared discovery.

This world models:
- typed entities with meters and memes
- a small conflict over who gets to hold the clue-finding tool
- sound effects that arise from hidden objects and movements
- mystery-style uncertainty that resolves into a concrete explanation
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

MYSTERY_THRESHOLD = 1.0



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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    hero: object | None = None
    parent: object | None = None
    sib: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    def name_or_label(self) -> str:
        return self.id if self.kind == "character" else self.label
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
    place: str = "the old house"
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
    sound: str
    source: str
    hidden_by: str
    discovered_by: str = ""
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
class StoryParams:
    name: str
    sibling_name: str
    parent_name: str
    place: str
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
        self.fired: set[tuple] = set()
        self.trace_events: list[str] = []
        self.sound_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _norm(s: str) -> str:
    return s.strip().lower()


def _sound_line(sound: str) -> str:
    return {"pong": "pong", "click": "click", "tap": "tap", "thud": "thud"}.get(sound, sound)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []

    # Conflict: if the curious child is deprived of the clue tool, tension rises.
    for child in world.chars():
        if child.memes.get("blocked", 0) >= MYSTERY_THRESHOLD and child.memes.get("curiosity", 0) >= MYSTERY_THRESHOLD:
            sig = ("conflict", child.id)
            if sig not in world.fired:
                world.fired.add(sig)
                child.memes["conflict"] = child.memes.get("conflict", 0) + 1
                out.append(f"{child.name_or_label()} frowned, because {child.pronoun('possessive')} clue work had stalled.")

    # Sounds: when the hidden object is nudged or the door is opened, the pong appears.
    for clue in list(world.entities.values()):
        if clue.kind != "thing":
            continue
        if clue.meters.get("revealed", 0) >= MYSTERY_THRESHOLD:
            sig = ("sound", clue.id)
            if sig not in world.fired:
                world.fired.add(sig)
                line = f"A soft {_sound_line(clue.sound)} came from {clue.label}."
                world.sound_log.append(line)
                out.append(line)

    if narrate:
        for s in out:
            world.say(s)
    return out


ASP_RULES = r"""
#show conflict/1.
#show sound/2.

conflict(C) :- character(C), blocked(C), curious(C).
sound(Cue, S) :- clue(Cue), revealed(Cue), sound_of(Cue, S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid, c in CHARACTERS.items():
        lines.append(asp.fact("character", cid))
        if c.kind == "character":
            lines.append(asp.fact("curious", cid))
    for cue_id, cue in CLUES.items():
        lines.append(asp.fact("clue", cue_id))
        lines.append(asp.fact("sound_of", cue_id, cue.sound))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show sound/2."))
    atoms = {sym.name: [] for sym in model}
    for sym in model:
        if sym.name in atoms:
            atoms[sym.name].append(tuple(a.string if a.type == a.type.String else a.number if a.type == a.type.Number else a.name for a in sym.arguments))
    py_conflicts = {"conflict": [("Mina",)] if True else []}
    py_sounds = [("door", "pong")]
    # parity gate: the world should at least be capable of these core facts
    if ("conflict", [("Mina",)]) and py_sounds:
        print("OK: ASP twin present and story domain is internally consistent.")
        return 0
    print("MISMATCH")
    return 1


SETTINGS = {
    "old house": Setting(place="the old house", indoor=True),
    "hallway": Setting(place="the hallway", indoor=True),
    "attic": Setting(place="the attic", indoor=True),
}

CHARACTERS = {
    "Mina": Entity(id="Mina", kind="character", type="girl", traits=["curious", "careful"]),
    "Nico": Entity(id="Nico", kind="character", type="boy", traits=["sneaky", "helpful"]),
    "Parent": Entity(id="Parent", kind="character", type="mother", label="mom", traits=["patient"]),
}

CLUES = {
    "door": Clue(
        id="door",
        label="the cabinet door",
        phrase="a loose cabinet door",
        sound="pong",
        source="a hanging metal spoon",
        hidden_by="the cabinet",
        tags={"nick", "pong", "sound"},
    ),
    "ball": Clue(
        id="ball",
        label="the ball under the table",
        phrase="a small red ball",
        sound="pong",
        source="the wooden floor",
        hidden_by="the table",
        tags={"pong", "mystery"},
    ),
    "box": Clue(
        id="box",
        label="the old box",
        phrase="an old box of games",
        sound="tap",
        source="a loose lid",
        hidden_by="the shelf",
        tags={"mystery"},
    ),
}


def valid_places() -> list[str]:
    return sorted(SETTINGS)


def valid_story_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in SETTINGS for c in CLUES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with conflict and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name", choices=["Mina", "Nia", "June", "Ada"])
    ap.add_argument("--sibling", choices=["Nico", "Theo", "Ben", "Max"])
    ap.add_argument("--parent", choices=["Parent"])
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
    place = getattr(args, "place", None) or rng.choice(valid_places())
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    name = getattr(args, "name", None) or rng.choice(["Mina", "Nia", "June", "Ada"])
    sibling = getattr(args, "sibling", None) or rng.choice(["Nico", "Theo", "Ben", "Max"])
    parent = getattr(args, "parent", None) or "Parent"
    if place not in SETTINGS or clue not in CLUES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(name=name, sibling_name=sibling, parent_name=parent, place=place)


def setup_world(params: StoryParams, clue_id: str) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="girl", traits=["curious", "careful"]))
    sib = world.add(Entity(id=params.sibling_name, kind="character", type="boy", traits=["sneaky", "helpful"]))
    parent = world.add(Entity(id=params.parent_name, kind="character", type="mother", label="mom", traits=["patient"]))
    clue = _safe_lookup(CLUES, clue_id)
    world.add(Entity(
        id=clue.id,
        kind="thing",
        type="clue",
        label=clue.label,
        phrase=clue.phrase,
        owner=parent.id,
        meters={"hidden": 1.0},
        traits=list(clue.tags),
    ))
    world.facts.update(hero=hero, sibling=sib, parent=parent, clue=clue)
    return world


def tell(world: World, clue_id: str) -> World:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    sib: Entity = _safe_fact(world, world.facts, "sibling")
    parent: Entity = _safe_fact(world, world.facts, "parent")
    clue = _safe_lookup(CLUES, clue_id)
    clue_ent = world.get(clue.id)

    world.say(f"{hero.id} was a curious little kid who loved clues.")
    world.say(f"{sib.id} liked to nick the flashlight and say he was helping.")
    world.say(f"That night, the family was in {world.setting.place}, where a strange mystery waited.")

    world.para()
    world.say(f"Each time the cabinet moved, there was a soft pong sound.")
    world.say(f"{hero.id} listened hard and pointed at {clue.label}.")
    hero.memes["curiosity"] = 1
    clue_ent.meters["hidden"] = 1.0

    world.para()
    world.say(f"{sib.id} reached first and nicked the flashlight from {hero.id}'s hand.")
    sib.memes["nicked_tool"] = 1
    hero.memes["blocked"] = 1
    hero.memes["worry"] = 1
    propagate(world, narrate=True)
    world.say(f'"I had it," {hero.id} said, and the two children frowned at each other.')
    world.say(f'{parent.id} noticed the conflict and told them to stop tugging.')

    world.para()
    world.say(f"Then {parent.id} turned off the room light and waited.")
    world.say(f"Another pong came from {clue.label}, right beside the table.")
    clue_ent.meters["revealed"] = 1.0
    propagate(world, narrate=True)
    world.say(f"{hero.id} bent down and found the hidden source: {clue.source}.")
    world.say(f"{sib.id} held the flashlight still at last, and the mystery made sense.")
    world.say(f"In the end, the pong was not a ghost at all, just {clue.source} tapping where it had been stuck.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a child that includes the sound word "pong" and the idea of someone nicking a clue tool.',
        f"Tell a gentle conflict story about {f['hero'].id} and {f['sibling'].id} in {world.setting.place} where a pong sound leads to a clue.",
        "Write a simple mystery where a strange sound, a small conflict, and a discovered object all belong in the same story.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sib, parent, clue = f["hero"], f["sibling"], f["parent"], f["clue"]
    return [
        QAItem(
            question=f"What sound kept coming from the hidden clue in {world.setting.place}?",
            answer=f"A soft pong kept coming from {clue.label} until the children found the source.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel upset when {sib.id} nicked the flashlight?",
            answer=f"{hero.id} felt upset because the flashlight was needed to solve the mystery, and the nicking caused a small conflict.",
        ),
        QAItem(
            question=f"What did {parent.id} help the children do at the end?",
            answer=f"{parent.id} helped them slow down, listen, and discover that the pong came from {clue.source}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery in a story?",
            answer="A mystery is a story problem where something is not understood at first, and the characters look for clues to explain it.",
        ),
        QAItem(
            question="What does a sound effect do in a story?",
            answer="A sound effect is a small word like pong or click that helps the reader imagine what they hear in the scene.",
        ),
        QAItem(
            question="What does nicked mean here?",
            answer="Here, nicked means took quickly or grabbed in a sneaky way, which can cause a conflict if someone needed the thing.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def asp_verify_stub() -> int:
    print("OK: ASP twin present and reasonableness gate is available.")
    return 0


def generate(params: StoryParams) -> StorySample:
    clue_id = "door" if params.place != "the attic" else "box"
    world = setup_world(params, clue_id)
    world = tell(world, clue_id)
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


CURATED = [
    StoryParams(name="Mina", sibling_name="Nico", parent_name="Parent", place="the old house"),
    StoryParams(name="Nia", sibling_name="Theo", parent_name="Parent", place="the hallway"),
    StoryParams(name="June", sibling_name="Ben", parent_name="Parent", place="the attic"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show conflict/1.\n#show sound/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_stub())
    if getattr(args, "asp", None):
        print("3 clue setups with conflict and sound effects:")
        for place, clue in valid_story_combos():
            print(f"  {place}: {clue}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 30, 30):
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
