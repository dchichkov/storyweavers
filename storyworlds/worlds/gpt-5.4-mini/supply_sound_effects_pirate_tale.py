#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/supply_sound_effects_pirate_tale.py
===================================================================

A standalone story world for a tiny pirate tale about a missing supply, a noisy
search, and a clever fix. The world stays small: one ship, one crew, one needed
supply, a few sound effects, and a final image showing the supply was found and
the voyage could continue.

The story premise is simple:
- pirates need a supply for their trip,
- a first plan goes wrong or turns out risky,
- the crew follows the sounds to solve the problem,
- the ending proves the supply is secured and the ship sails on.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes,
- simulated state drives prose,
- an inline ASP twin and a Python reasonableness gate,
- prompts, story-grounded QA, and world-knowledge QA from world state,
- stdlib-only, self-contained, runnable directly from the repo root.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Supply:
    id: str
    label: str
    phrase: str
    needed_for: str
    location: str
    sound: str
    plural: bool = False
    supply_kind: str = "thing"
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class SoundSource:
    id: str
    label: str
    sound: str
    helps: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    def __init__(self) -> None:
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_unsteady(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["panic"] < THRESHOLD:
            continue
        sig = ("panic", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["jolt"] += 1
        out.append("__sound__")
    return out


def _r_found(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("supply_found"):
        return out
    if world.facts.get("signal_seen") and world.facts.get("crew_together"):
        sig = ("found", world.facts.get("supply_id"))
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.facts["supply_found"] = True
        world.get(world.facts["supply_holder"]).meters["supplied"] += 1
        out.append("__found__")
    return out


CAUSAL_RULES = [
    Rule("unsteady", "social", _r_unsteady),
    Rule("found", "physical", _r_found),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quiet_supply_ok(supply: Supply) -> bool:
    return supply.label in {"rope", "lantern oil", "map", "fresh water", "sail cloth"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene in SCENES:
        for sid, supply in SUPPLIES.items():
            for snd in SOUNDS:
                if supply.needed_for == scene.need and quiet_supply_ok(supply):
                    combos.append((scene.id, sid, snd))
    return combos


def severity_for(scene: "Scene", delay: int) -> int:
    return scene.risk + delay


def is_resolved(choice: "Choice", scene: "Scene", delay: int) -> bool:
    return choice.power >= severity_for(scene, delay)


def python_gate(scene: "Scene", supply: Supply) -> bool:
    return supply.needed_for == scene.need and quiet_supply_ok(supply)


def predict(world: World, supply_id: str) -> dict:
    sim = world.copy()
    _get_lost(sim, narrate=False)
    sim.facts["signal_seen"] = True
    sim.facts["crew_together"] = True
    _r_found(sim)
    return {"found": bool(sim.facts.get("supply_found", False))}


def setup(world: World, cap: Entity, mate: Entity, scene: "Scene", supply: Supply, sound: SoundSource) -> None:
    cap.memes["hope"] += 1
    mate.memes["hope"] += 1
    world.say(
        f"On a bright pirate morning, {cap.id} and {mate.id} were ready to sail. "
        f"They needed {supply.phrase} for {scene.goal}, and the deck was full of busy sea air."
    )
    world.say(
        f"Their little ship had a tiny supply chest, a map by the mast, and a job to do: keep {scene.goal} safe."
    )


def lose_supply(world: World, supply: Supply, holder: Entity) -> None:
    holder.meters["empty"] += 1
    world.facts["supply_holder"] = holder.id
    world.facts["supply_id"] = supply.id
    world.say(
        f"Then came a wild gust -- whirr! -- and the {supply.label} slipped from the chest."
    )
    world.say(f"Plip! Plop! It vanished under the boards before anyone could grab it.")


def search(world: World, cap: Entity, mate: Entity, sound: SoundSource) -> None:
    cap.memes["worry"] += 1
    mate.memes["worry"] += 1
    world.say(
        f'"{sound.sound}" went the boat ropes, and {cap.id} froze. "{sound.helps}," '
        f'{mate.id} said, listening hard.'
    )


def worry(world: World, cap: Entity, mate: Entity, supply: Supply) -> None:
    world.facts["signal_seen"] = True
    cap.memes["panic"] += 1
    mate.memes["panic"] += 1
    world.say(
        f'{cap.id} peeked into the chest and gasped. "Our {supply.label} is gone!"'
    )
    world.say(f'"Oh no," {mate.id} whispered. "We cannot sail without it."')


def signal(world: World, cap: Entity, mate: Entity, sound: SoundSource) -> None:
    world.facts["crew_together"] = True
    world.say(
        f'Then they heard it again: "{sound.sound}!" This time it came from the crow\'s nest.'
    )
    world.say(
        f'"That means {sound.helps.lower()}!" {mate.id} shouted, and both pirates climbed fast -- thump, thump, thump!'
    )


def rescue(world: World, cap: Entity, mate: Entity, supply: Supply) -> None:
    world.get(world.facts["supply_holder"]).meters["supplied"] += 1
    world.facts["supply_found"] = True
    world.say(
        f"At the top, they found the {supply.label} tucked in a safe knot, right where the wind could not take it."
    )
    world.say(
        f'{cap.id} laughed, "{supply.sound}!" and {mate.id} laughed back, because the missing supply was back where it belonged.'
    )


def finish(world: World, cap: Entity, mate: Entity, scene: "Scene", supply: Supply) -> None:
    cap.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"With the {supply.label} secured, the crew tied the chest shut with a sturdy rope and set the sails again."
    )
    world.say(
        f"The ship went on toward {scene.goal}, quick and brave, while the sea made one last happy splash against the hull."
    )


def tell(scene: "Scene", supply: Supply, sound: SoundSource, choice: "Choice", delay: int = 0,
         captain_name: str = "Captain Mina", mate_name: str = "Mate Toby") -> World:
    world = World()
    cap = world.add(Entity(id=captain_name, kind="character", type="captain", role="captain"))
    mate = world.add(Entity(id=mate_name, kind="character", type="pirate", role="mate"))
    world.facts["supply_holder"] = "supplybox"
    world.add(Entity(id="supplybox", type="box", label="supply chest"))

    setup(world, cap, mate, scene, supply, sound)
    world.para()
    lose_supply(world, supply, world.get("supplybox"))
    search(world, cap, mate, sound)
    worry(world, cap, mate, supply)
    signal(world, cap, mate, sound)
    world.para()
    if is_resolved(choice, scene, delay):
        rescue(world, cap, mate, supply)
        finish(world, cap, mate, scene, supply)
    else:
        world.say(
            f"But the stormy chase took too long, and the pirates had to use the spare supply while they kept searching."
        )
        world.say(
            f"At last they still found it, wet but safe, and tied it down for the next stretch of sea."
        )

    world.facts.update(
        scene=scene,
        supply=supply,
        sound=sound,
        choice=choice,
        delay=delay,
        outcome="resolved" if is_resolved(choice, scene, delay) else "delayed",
        supply_found=bool(world.facts.get("supply_found")),
    )
    return world


@dataclass
class Scene:
    id: str
    name: str
    goal: str
    need: str
    risk: int
    detail: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Choice:
    id: str
    label: str
    power: int
    sense: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SCENES = {
    "dock": Scene("dock", "the dock", "the harbor light", "rope", 1, "The pier boards creaked under their boots."),
    "island": Scene("island", "the island shore", "the hidden cove", "fresh water", 2, "The beach sparkled with shells."),
    "reef": Scene("reef", "the reef path", "the map island", "map", 2, "The waves hissed around the rocks."),
}

SUPPLIES = {
    "rope": Supply("rope", "rope", "a coil of rope", "rope", "in the supply chest", "twang", tags={"rope"}),
    "water": Supply("water", "fresh water", "a jug of fresh water", "fresh water", "near the lantern", "glug", tags={"water"}),
    "map": Supply("map", "map", "the sea map", "map", "under a paper sail", "rustle", tags={"map"}),
    "oil": Supply("oil", "lantern oil", "a bottle of lantern oil", "lantern oil", "beside the lamp", "glug", tags={"oil"}),
    "cloth": Supply("cloth", "sail cloth", "a folded sail cloth", "sail cloth", "under the bench", "flap", tags={"cloth"}),
}

SOUNDS = {
    "clank": SoundSource("clank", "clank", "clank, clank", "the chest is loose", tags={"sound"}),
    "thump": SoundSource("thump", "thump", "thump, thump", "someone is climbing", tags={"sound"}),
    "whoosh": SoundSource("whoosh", "whoosh", "whoosh", "the wind is changing", tags={"sound"}),
}

CHOICES = {
    "steady": Choice("steady", "steady hands", 2, 3, "carefully tie the chest shut", "try to tie it too late", {"steady"}),
    "quick": Choice("quick", "quick feet", 1, 2, "run to the mast fast", "run after the gale", {"quick"}),
    "smart": Choice("smart", "a smart search", 3, 3, "look in the crow's nest first", "look in the waves first", {"smart"}),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Zoe", "Ivy"]
BOY_NAMES = ["Toby", "Finn", "Jude", "Arlo", "Pip"]


@dataclass
@dataclass
class StoryParams:
    scene: str
    supply: str
    sound: str
    choice: str
    delay: int = 0
    captain_name: str = "Captain Mina"
    mate_name: str = "Mate Toby"
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene, supply, sound = f["scene"], f["supply"], f["sound"]
    return [
        f'Write a pirate tale for a young child that includes the word "{supply.label}" and the sound "{sound.sound}".',
        f"Tell a short story about pirates on {scene.name} who lose {supply.phrase}, then follow a noisy clue to find it.",
        f"Write a story with sound effects where a pirate crew needs {supply.label} to continue their trip and gets it back safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scene, supply, sound = f["scene"], f["supply"], f["sound"]
    outcome = f["outcome"]
    ans1 = (
        f"It is about {world.get('Captain Mina').id} and {world.get('Mate Toby').id}, two pirates on {scene.name}. "
        f"They were trying to keep their trip going."
    )
    ans2 = (
        f"They needed {supply.phrase} because their voyage depended on it. "
        f"When it went missing, the crew had to search carefully instead of sailing on."
    )
    items = [
        QAItem("Who is the story about?", ans1),
        QAItem(f"Why did the pirates need {supply.label}?", ans2),
        QAItem(f"What did the sound '{sound.sound}' help them notice?", f"It helped them notice that the supply was nearby. The sound became a clue that led the crew to the right place."),
    ]
    if outcome == "resolved":
        items.append(QAItem("How did the story end?", f"The pirates found the {supply.label}, tied it down, and sailed on toward {scene.goal}. The ending shows the missing supply was secured and the ship could continue."))
    else:
        items.append(QAItem("How did the story end?", f"The pirates still found the {supply.label}, but only after a longer search. In the end it was safe again and ready for the next stretch of sea."))
    return items


WORLD_KNOWLEDGE = {
    "rope": [("What is rope for on a ship?", "Rope helps sailors tie things down so wind and waves do not toss them around.")],
    "map": [("What does a map do?", "A map shows where to go and helps people find places they want to reach.")],
    "water": [("Why do sailors keep fresh water?", "Fresh water is important because people need to drink it on a trip.")],
    "oil": [("What is lantern oil used for?", "Lantern oil helps a lamp burn so it can give light in the dark.")],
    "cloth": [("What can sail cloth do?", "Sail cloth catches the wind and helps a ship move.")],
    "sound": [("What are sound effects in a story?", "Sound effects are words like clank or whoosh that help you hear the action in your head.")],
}
WORLD_ORDER = ["rope", "map", "water", "oil", "cloth", "sound"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["supply"].tags) | set(world.facts["sound"].tags)
    out: list[QAItem] = []
    for key in WORLD_ORDER:
        if key in tags and key in WORLD_KNOWLEDGE:
            for q, a in WORLD_KNOWLEDGE[key]:
                out.append(QAItem(q, a))
    return out


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(scene: Scene, supply: Supply) -> str:
    return f"(No story: {supply.label} does not match what {scene.name} needs, so the tale would not have a sensible missing-supply problem.)"


def explain_choice(c: Choice) -> str:
    if c.sense < SENSE_MIN:
        return f"(Refusing choice '{c.id}': it scores too low on common sense.)"
    return "(No story: invalid choice.)"


ASP_RULES = r"""
valid(Scene, Supply, Sound) :- scene(Scene), supply(Supply), sound(Sound), needed(Scene, Need), supply_need(Supply, Need), quiet(Supply).
sensible(C) :- choice(C), sense(C, S), sense_min(M), S >= M.
outcome(resolved) :- chosen_scene(Scene), chosen_supply(Supply), chosen_choice(C), risk(Scene, R), delay(D), power(C, P), P >= R + D.
outcome(delayed) :- chosen_scene(Scene), chosen_supply(Supply), chosen_choice(C), risk(Scene, R), delay(D), power(C, P), P < R + D.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("needed", sid, s.need))
        lines.append(asp.fact("risk", sid, s.risk))
    for sid, sup in SUPPLIES.items():
        lines.append(asp.fact("supply", sid))
        lines.append(asp.fact("supply_need", sid, sup.needed_for))
        if quiet_supply_ok(sup):
            lines.append(asp.fact("quiet", sid))
    for sid in SOUNDS:
        lines.append(asp.fact("sound", sid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, c.sense))
        lines.append(asp.fact("power", cid, c.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_scene", params.scene),
        asp.fact("chosen_supply", params.supply),
        asp.fact("chosen_choice", params.choice),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combos gate.")
    if set(asp_sensible()) == {c.id for c in CHOICES.values() if c.sense >= SENSE_MIN}:
        print("OK: sensible choices match.")
    else:
        rc = 1
        print("MISMATCH in sensible choices.")
    samples = [resolve_params(argparse.Namespace(scene=None, supply=None, sound=None, choice=None, delay=None, n=1, seed=None, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False), random.Random(7))]
    sample = generate(samples[0])
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: empty story.")
    else:
        print("OK: story generation smoke test passed.")
    cases = [CURATED[0], CURATED[-1]]
    if all(asp_outcome(p) == outcome_of(p) for p in cases):
        print("OK: ASP outcome matches Python outcome.")
    else:
        rc = 1
        print("MISMATCH: ASP outcome differs.")
    return rc


def outcome_of(params: StoryParams) -> str:
    scene = SCENES[params.scene]
    choice = CHOICES[params.choice]
    return "resolved" if is_resolved(choice, scene, params.delay) else "delayed"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate supply storyworld with sound effects.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--supply", choices=SUPPLIES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
    ap.add_argument("--captain-name")
    ap.add_argument("--mate-name")
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
    if args.scene and args.supply:
        if not python_gate(SCENES[args.scene], SUPPLIES[args.supply]):
            raise StoryError(explain_rejection(SCENES[args.scene], SUPPLIES[args.supply]))
    if args.choice and CHOICES[args.choice].sense < SENSE_MIN:
        raise StoryError(explain_choice(CHOICES[args.choice]))
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.supply is None or c[1] == args.supply)
              and (args.sound is None or c[2] == args.sound)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, supply, sound = rng.choice(sorted(combos))
    choice = args.choice or rng.choice(sorted(CHOICES))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    captain_name = args.captain_name or rng.choice(GIRL_NAMES)
    mate_name = args.mate_name or rng.choice(BOY_NAMES)
    return StoryParams(scene, supply, sound, choice, delay, captain_name, mate_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], SUPPLIES[params.supply], SOUNDS[params.sound], CHOICES[params.choice], params.delay, params.captain_name, params.mate_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in [(x.question, x.answer) for x in story_qa(world)]],
        world_qa=[QAItem(q, a) for q, a in [(x.question, x.answer) for x in world_knowledge_qa(world)]],
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
    StoryParams("dock", "rope", "clank", "steady", 0, "Captain Mina", "Mate Toby"),
    StoryParams("island", "fresh_water", "whoosh", "smart", 1, "Captain Mina", "Mate Finn"),
]

# fix names/ids to actual keys
CURATED = [
    StoryParams("dock", "rope", "clank", "steady", 0, "Captain Mina", "Mate Toby"),
    StoryParams("island", "water", "whoosh", "smart", 1, "Captain Mina", "Mate Finn"),
    StoryParams("reef", "map", "thump", "quick", 0, "Captain Mina", "Mate Arlo"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for scene, supply, sound in combos:
            print(f"  {scene:8} {supply:12} {sound}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
                p.seed = base_seed + i
            except StoryError as err:
                print(err)
                return
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        header = ""
        if args.all:
            p = s.params
            header = f"### {p.scene}: {p.supply} / {p.sound} / {p.choice}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
