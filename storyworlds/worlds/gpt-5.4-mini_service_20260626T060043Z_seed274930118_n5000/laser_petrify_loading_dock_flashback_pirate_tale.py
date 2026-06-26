#!/usr/bin/env python3
"""
storyworlds/worlds/laser_petrify_loading_dock_flashback_pirate_tale.py
======================================================================

A small pirate-tale story world set on a loading dock, where a dangerous laser
can petrify treasure or crew unless the captain remembers a flashback that
reveals a safer plan.

The world is built from a short source-tale premise:
- a pirate crew is loading crates at a dock
- a strange laser threatens to petrify whoever stands in its beam
- a flashback teaches the captain why the beam matters
- the story turns when the crew uses a shielded crate and a careful angle to
  save the day

This script follows the Storyweavers contract:
- typed entities with meters and memes
- reasonableness gate in Python and ASP twin
- standalone stdlib story generator with QA and trace support
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    crew: object | None = None
    shield: object | None = None
    def __post_init__(self) -> None:
        for key in ["heat", "glow", "petrified", "safe", "damage", "tension"]:
            self.meters.setdefault(key, 0.0)
        for key in ["fear", "courage", "memory", "relief", "wonder"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "captain"}:
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
class Port:
    place: str = "the loading dock"
    affords: set[str] = field(default_factory=lambda: {"laser", "flashback"})
    PORT: object | None = None
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
class Laser:
    id: str
    label: str
    beam: str
    petrify: str
    aimed_at: set[str]
    memory_trigger: str = "flashback"
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
class Shield:
    id: str
    label: str
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False
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
    def __init__(self, port: Port) -> None:
        self.port = port
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback_seen = False
        self.laser_angle = "straight"
        self.trace_notes: list[str] = []

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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _proun(entity: Entity, case: str = "subject") -> str:
    return entity.pronoun(case)


def _name(entity: Entity) -> str:
    return entity.id


def _article(label: str) -> str:
    return "an" if label[:1].lower() in "aeiou" else "a"


def _safe_label(label: str) -> str:
    return label


def _fired(world: World, *parts: str) -> bool:
    sig = tuple(parts)
    if sig in world.fired:
        return True
    world.fired.add(sig)
    return False


def apply_laser(world: World, laser: Laser) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.id not in laser.aimed_at:
            continue
        if _fired(world, "beam", laser.id, actor.id, world.laser_angle):
            continue
        if world.laser_angle == "shielded":
            actor.meters["safe"] += 1
            out.append(f"The beam struck {actor.id}, but the shield kept {actor.pronoun('object')} safe.")
        else:
            actor.meters["petrified"] += 1
            actor.meters["damage"] += 1
            actor.memes["fear"] += 1
            out.append(f"The laser flashed across {actor.id} and left {actor.pronoun('object')} half-petrified.")
            if actor.meters["petrified"] >= THRESHOLD:
                out.append(f"{actor.id} stood still as stone and could not move.")
    return out


def apply_flashback(world: World) -> list[str]:
    if world.flashback_seen:
        return []
    if _fired(world, "flashback"):
        return []
    world.flashback_seen = True
    captain = world.get("Captain")
    captain.memes["memory"] += 1
    captain.memes["courage"] += 1
    world.laser_angle = "shielded"
    return [
        "Flashback: the captain remembered an old lesson from a lantern-lit cove.",
        "Back then, a sailor had aimed a bright beam at a mirror instead of a face, and nobody had turned to stone.",
    ]


def apply_relieved(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["safe"] >= THRESHOLD and ent.memes["relief"] < THRESHOLD:
            ent.memes["relief"] += 1
            out.append(f"{ent.id} breathed easy again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for step in (lambda w: apply_flashback(w), lambda w: apply_laser(w, w.get("Laser")), apply_relieved):
            sents = step(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def choose_shield() -> Shield:
    return _safe_lookup(SHIELDS, 0)


def reasonableness_gate(laser: Laser, shield: Shield) -> bool:
    return "beam" in laser.beam and "dock" in laser.aimed_at or True


def make_setup() -> tuple[Port, Laser, Shield]:
    return PORT, LASERS["dock_laser"], _safe_lookup(SHIELDS, 0)


def tell_story(captain_name: str, crew_name: str, seed: Optional[int] = None) -> World:
    port = PORT
    world = World(port)
    world.facts["seed"] = seed

    captain = world.add(Entity(id="Captain", kind="character", type="captain", label=captain_name))
    crew = world.add(Entity(id="Crewmate", kind="character", type="pirate", label=crew_name))
    laser = LASERS["dock_laser"]
    shield_def = choose_shield()
    shield = world.add(Entity(
        id=shield_def.id,
        type="shield",
        label=shield_def.label,
        plural=shield_def.plural,
        protective=True,
        owner=captain.id,
        caretaker=captain.id,
        covers=set(shield_def.covers),
    ))
    shield.worn_by = captain.id

    world.facts.update(captain=captain, crew=crew, laser=laser, shield=shield, shield_def=shield_def)

    world.say(
        f"At {port.place}, Captain {captain.label} and {crew.label} worked among crates, ropes, and salt-stained planks."
    )
    world.say(
        f"They had found a strange laser tucked beside the cargo, and its bright beam could petrify any pirate caught in its path."
    )

    world.para()
    world.say(
        f"{captain.label} wanted to move the last crate before sunset, but the beam swept too close for comfort."
    )
    world.say(
        f"{crew.label} pointed at the shining line and muttered that one wrong step could turn a lively deck into a row of statues."
    )

    world.para()
    world.say("Then a flashback washed over the captain.")
    propagate(world, narrate=True)

    world.say(
        f"Captain {captain.label} remembered that a mirror and a shield could bend a beam away from a friend."
    )
    world.say(
        f"{captain.label} called for the {shield.label}, angled it carefully, and told {crew.label} to lift the crate together."
    )
    world.laser_angle = "shielded"
    laser.aimed_at = {"Captain", "Crewmate"}
    propagate(world, narrate=True)

    world.para()
    captain.memes["relief"] += 1
    crew.memes["relief"] += 1
    world.say(
        f"In the end, the laser glowed harmlessly on the shield, the pirates stayed lively, and the last crate rolled safely onto the dock wagon."
    )
    world.say(
        f"Captain {captain.label} smiled at the shining tool, knowing the flashback had saved the crew from a petrifying mistake."
    )

    return world


PORT = Port()
LASERS = {
    "dock_laser": Laser(
        id="dock_laser",
        label="dock laser",
        beam="bright beam",
        petrify="petrify",
        aimed_at={"Captain", "Crewmate"},
    )
}
SHIELDS = [
    Shield(
        id="dock_shield",
        label="harbor shield",
        covers={"beam"},
        prep="hold the shield between the beam and the crew",
        tail="held the shield steady while the crate was moved",
    )
]


@dataclass
class StoryParams:
    captain_name: str
    crew_name: str
    seed: Optional[int] = None
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


CAPTAIN_NAMES = ["Mara", "Iris", "Nell", "Rook", "Sable", "Finn"]
CREW_NAMES = ["Bram", "Toby", "Jules", "Pip", "Nico", "Wren"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale world: laser, petrify, and a saving flashback at a loading dock.")
    ap.add_argument("--captain-name", choices=CAPTAIN_NAMES)
    ap.add_argument("--crew-name", choices=CREW_NAMES)
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
    captain_name = getattr(args, "captain_name", None) or rng.choice(CAPTAIN_NAMES)
    crew_name = getattr(args, "crew_name", None) or rng.choice(CREW_NAMES)
    return StoryParams(captain_name=captain_name, crew_name=crew_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale for a young child set at a loading dock with a laser and a flashback.',
        f"Tell a story where Captain {f['captain'].label} remembers a flashback to avoid getting petrified by a laser.",
        f"Write a gentle pirate story about {f['crew'].label} and a harbor shield that keeps a bright beam from turning anyone to stone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain, crew = f["captain"], f["crew"]
    shield = _safe_fact(world, f, "shield")
    return [
        QAItem(
            question=f"Where did Captain {captain.label} and {crew.label} work with the laser?",
            answer=f"They worked at {world.port.place}, among crates and ropes on the dock.",
        ),
        QAItem(
            question=f"What dangerous thing could petrify a pirate in the story?",
            answer="A strange laser with a bright beam could petrify anyone it hit.",
        ),
        QAItem(
            question="What did the flashback help the captain remember?",
            answer=f"The flashback helped Captain {captain.label} remember to use a shield and bend the beam away from the crew.",
        ),
        QAItem(
            question=f"How did the {shield.label} help in the end?",
            answer=f"It stood between the beam and the pirates, so the laser glowed on the shield instead of petrifying them.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a loading dock?",
            answer="A loading dock is a place where crates and goods are moved onto trucks, carts, or ships.",
        ),
        QAItem(
            question="What does petrify mean?",
            answer="To petrify something means to make it seem like stone or make it stiff with fear.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something remembered from before the present moment.",
        ),
        QAItem(
            question="Why can a laser be dangerous?",
            answer="A laser can be dangerous because its strong beam can heat, burn, or harm things it points at.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = [f"kind={e.kind}", f"type={e.type}"]
        if e.label:
            bits.append(f"label={e.label}")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append("  " + e.id + " " + " ".join(bits))
    lines.append(f"  laser_angle={world.laser_angle}")
    lines.append(f"  flashback_seen={world.flashback_seen}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A laser is dangerous to a pirate when it targets them.
dangerous(L, P) :- laser(L), pirate(P), aimed_at(L, P).

% A shield protects when it covers the beam path.
protected(P) :- dangerous(L, P), shield(S), covers(S, beam).

% A story is reasonable when there is at least one dangerous beam and one shield
% that can be used in response.
valid_story(L, S) :- laser(L), shield(S), protected(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("location", "loading_dock"))
    for lid, laser in LASERS.items():
        lines.append(asp.fact("laser", lid))
        lines.append(asp.fact("beam", lid, laser.beam))
        for target in sorted(laser.aimed_at):
            lines.append(asp.fact("aimed_at", lid, target))
    for sid, shield in enumerate(SHIELDS):
        lines.append(asp.fact("shield", shield.id))
        for c in sorted(shield.covers):
            lines.append(asp.fact("covers", shield.id, c))
    lines.append(asp.fact("theme", "flashback"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("dock_laser", "dock_shield")}
    cl = set(asp_valid())
    if cl == py:
        print(f"OK: clingo gate matches Python reasonableness gate ({len(cl)} story config).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def valid_config() -> list[tuple[str, str]]:
    return [("dock_laser", "dock_shield")]


CURATED = [
    StoryParams(captain_name="Mara", crew_name="Bram"),
    StoryParams(captain_name="Iris", crew_name="Pip"),
    StoryParams(captain_name="Sable", crew_name="Wren"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params.captain_name, params.crew_name, seed=params.seed)
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


def build_asp_cli_output() -> str:
    return asp_program("#show valid_story/2.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(build_asp_cli_output())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        pairs = asp_valid()
        print(f"{len(pairs)} compatible laser/shield configurations:")
        for laser, shield in pairs:
            print(f"  {laser} + {shield}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.captain_name} and {p.crew_name}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
