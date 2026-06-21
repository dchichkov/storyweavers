#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/prohibit_sauerkraut_flashback_bravery_repetition_ghost_story.py
================================================================================================

A standalone story world for a small ghost-story domain:

- a child is warned not to go where they are prohibited,
- an old sauerkraut jar brings back a flashback,
- repeated spooky signs test bravery,
- the child speaks up anyway, and
- the ending proves what changed in the house.

The world is designed for child-facing prose, with a state-driven middle turn and
a concrete ending image. The story uses physical meters and emotional memes,
and includes a Python reasonableness gate plus an inline ASP twin.

This world intentionally keeps the vocabulary small and the events classical:
an old cellar, a strict rule, a sour smell, a memory, a little courage, and a
ghostly misunderstanding that is resolved by a brave, practical action.
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
BRAVERY_MIN = 2.0
REPETITION_MIN = 2
FLASHBACK_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    dark_place: str
    smell: str
    echo_phrase: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class StoryAction:
    id: str
    name: str
    sound: str
    effect: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class StoryParams:
    setting: str
    child: str
    child_gender: str
    parent: str
    parent_gender: str
    prohibit: str
    sauerkraut: str
    flashback: str
    bravery: str
    repetition: str
    action: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_unease(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["spooky"] < THRESHOLD:
            continue
        sig = ("unease", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in list(world.entities.values()):
            if kid.role == "child":
                kid.memes["fear"] += 1
        out.append("__spooky__")
    return out


def _r_brave(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.entities.values() if e.role == "child"), None)
    if not child or child.memes["fear"] < THRESHOLD or child.memes["bravery"] < BRAVERY_MIN:
        return out
    sig = ("brave", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["bravery"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    out.append("__brave__")
    return out


CAUSAL_RULES = [Rule("unease", _r_unease), Rule("brave", _r_brave)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_reasonable(setting: Setting, sauerkraut: Prop, flashback: Prop, bravery: Prop, repetition: Prop) -> bool:
    return (
        "ghost_story" in setting.tags
        and "sour" in sauerkraut.tags
        and "memory" in flashback.tags
        and "courage" in bravery.tags
        and "echo" in repetition.tags
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for sid, s in SETTINGS.items():
        for sid2 in SAUERKRAUTS:
            for fid in FLASHBACKS:
                for bid in BRAVERIES:
                    for rid in REPETITIONS:
                        if is_reasonable(s, SAUERKRAUTS[sid2], FLASHBACKS[fid], BRAVERIES[bid], REPETITIONS[rid]):
                            combos.append((sid, sid2, fid, bid, rid))
    return combos


def predict_spooky(world: World) -> dict:
    sim = world.copy()
    cellar = sim.get("cellar")
    cellar.meters["spooky"] += 1
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "fear": child.memes["fear"],
        "bravery": child.memes["bravery"],
    }


def open_scene(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"At {setting.place}, {child.id} heard the house make a small creak each time the wind pressed on the boards."
    )
    world.say(
        f'{parent.id} pointed toward {setting.dark_place} and said, "Do not go there."'
    )
    world.say(
        f"The rule was simple: {parent.label_word} would prohibit the cellar door after supper."
    )


def smell_signal(world: World, setting: Setting, sauerkraut: Prop) -> None:
    world.say(
        f"But when the lid came loose, a sour smell floated out of the jar, sharp as {setting.smell} and old cabbage."
    )
    world.say(
        f'{sauerkraut.phrase.capitalize()} sat on the table, and the smell seemed to repeat itself in the hall, again and again.'
    )


def flashback(world: World, child: Entity, flashback_prop: Prop, setting: Setting) -> None:
    child.memes["memory"] += 1
    world.say(
        f"{child.id} had a flashback: last winter, {child.pronoun('possessive')} boots had slipped near the same door, and {child.pronoun()} had heard that same lonely echo."
    )
    world.say(
        f"That memory came back like a lantern in the dark, and {flashback_prop.phrase} made the old night feel close."
    )


def repeat_spook(world: World, setting: Setting, repetition: Prop) -> None:
    world.add(Entity(id="cellar", label=setting.dark_place, meters={"spooky": 1.0}))
    world.say(
        f"{repetition.phrase.capitalize()} made the house feel stranger."
    )
    world.say(
        f"Tap. Tap. Tap. The sound came again from {setting.dark_place}, and again, and again."
    )
    propagate(world, narrate=False)


def brave_choice(world: World, child: Entity, parent: Entity, bravery: Prop) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} swallowed {child.pronoun('possessive')} fear and said, \"I can be brave.\""
    )
    world.say(
        f"{bravery.phrase.capitalize()} did not make {child.id} reckless; it made {child.id} ask for help."
    )


def reveal(world: World, parent: Entity, setting: Setting, sauerkraut: Prop) -> None:
    world.say(
        f'{parent.id} opened {setting.dark_place} and found the reason for the strange smell: a forgotten jar of sauerkraut on a dusty shelf.'
    )
    world.say(
        f"The sour jar had rolled, the cellar had echoed, and the house had been playing its own spooky game."
    )


def calm_end(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    world.say(
        f"{parent.id} laughed softly, and {child.id} laughed too, because the ghost was only a kitchen smell hiding in a dark corner."
    )
    world.say(
        f"After that, the cellar was still old, but it was only a cellar, and {setting.place} felt ordinary again."
    )


def tell(setting: Setting, child_name: str, child_gender: str, parent_name: str, parent_gender: str,
         prohibit: Prop, sauerkraut: Prop, flashback_prop: Prop, bravery: Prop,
         repetition: Prop, action: StoryAction) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    world.add(Entity(id="house", kind="thing", label=setting.place, tags=set(setting.tags)))
    world.add(Entity(id="cellar", kind="thing", label=setting.dark_place))
    world.add(Entity(id="jar", kind="thing", label=sauerkraut.label, tags=set(sauerkraut.tags)))
    world.add(Entity(id="memory", kind="thing", label=flashback_prop.label, tags=set(flashback_prop.tags)))
    world.add(Entity(id="courage", kind="thing", label=bravery.label, tags=set(bravery.tags)))
    world.add(Entity(id="echo", kind="thing", label=repetition.label, tags=set(repetition.tags)))

    open_scene(world, child, parent, setting)
    world.para()
    smell_signal(world, setting, sauerkraut)
    flashback(world, child, flashback_prop, setting)
    repeat_spook(world, setting, repetition)
    world.para()
    brave_choice(world, child, parent, bravery)
    reveal(world, parent, setting, sauerkraut)
    calm_end(world, child, parent, setting)

    world.facts.update(
        child=child,
        parent=parent,
        setting=setting,
        prohibit=prohibit,
        sauerkraut=sauerkraut,
        flashback=flashback_prop,
        bravery=bravery,
        repetition=repetition,
        action=action,
        flashback_count=child.memes["memory"],
        bravery_level=child.memes["bravery"],
        repetition_count=2,
    )
    return world


SETTINGS = {
    "old_house": Setting(
        id="old_house",
        place="the old house at the end of the lane",
        dark_place="the cellar stairs",
        smell="wet leaves",
        echo_phrase="the long echo in the hall",
        tags={"ghost_story", "old_house"},
    ),
    "attic_home": Setting(
        id="attic_home",
        place="Grandma's attic room",
        dark_place="the attic door",
        smell="dust",
        echo_phrase="the little squeak in the beams",
        tags={"ghost_story", "attic"},
    ),
}

PROHIBITS = {
    "cellar": Prop(id="cellar", label="the cellar", phrase="the cellar door", tags={"prohibit", "dark"}),
    "attic": Prop(id="attic", label="the attic", phrase="the attic door", tags={"prohibit", "dark"}),
}

SAUERKRAUTS = {
    "jar": Prop(id="jar", label="sauerkraut", phrase="the sauerkraut jar", tags={"sour", "food"}),
    "bowl": Prop(id="bowl", label="sauerkraut", phrase="the bowl of sauerkraut", tags={"sour", "food"}),
}

FLASHBACKS = {
    "memory": Prop(id="memory", label="flashback", phrase="the flashback memory", tags={"memory", "past"}),
}

BRAVERIES = {
    "courage": Prop(id="courage", label="bravery", phrase="bravery", tags={"courage", "heart"}),
}

REPETITIONS = {
    "echo": Prop(id="echo", label="repetition", phrase="the repetition of the sound", tags={"echo", "repeat"}),
}

ACTIONS = {
    "open": StoryAction(id="open", name="open the door", sound="creak", effect="revealed", tags={"door"}),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Rose", "Maya"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Noah", "Max", "Owen"]


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly ghost story that includes the words "{f["prohibit"].label}" and "{f["sauerkraut"].label}".',
        f"Tell a spooky-but-kind story where {f['child'].id} remembers a flashback, finds bravery, and the repeated noise in the old house turns out to be {f['sauerkraut'].label}.",
        "Write a short ghost story with a dark room, a brave child, and a funny reveal at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    setting = f["setting"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, who is trying to be brave in the old house with {parent.id}. The dark place makes the story feel spooky, but the child keeps going.",
        ),
        QAItem(
            question="Why did the child think the house might be haunted?",
            answer=f"There was a repeated sound and a sour smell near {setting.dark_place}. {child.id} also had a flashback, so the place felt even stranger for a moment.",
        ),
        QAItem(
            question=f"What did {child.id} do when the spooky sound kept repeating?",
            answer=f"{child.id} stayed with {parent.id} and asked what was making the noise. That brave choice helped turn fear into a simple, safe answer.",
        ),
        QAItem(
            question="What was the frightening thing really?",
            answer="It was not a ghost at all. It was a forgotten jar of sauerkraut making the house smell sour and strange.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a memory from earlier comes back into your mind. It can make a story feel like the past has stepped into the present for a moment.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means feeling scared but still doing the careful thing that needs to be done. It does not mean ignoring danger.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means something happens again and again. In a ghost story, repeated sounds can make a room feel extra spooky.",
        ),
        QAItem(
            question="What is sauerkraut?",
            answer="Sauerkraut is cabbage that has been preserved in a sour way. It has a strong smell that can surprise people in a dark house.",
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: prohibition, sauerkraut, flashback, bravery, repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
    ap.add_argument("--prohibit", choices=PROHIBITS)
    ap.add_argument("--sauerkraut", choices=SAUERKRAUTS)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--bravery", choices=BRAVERIES)
    ap.add_argument("--repetition", choices=REPETITIONS)
    ap.add_argument("--action", choices=ACTIONS)
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


def valid_story_choices() -> list[tuple[str, str, str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PROHIBITS:
            for skid in SAUERKRAUTS:
                for fid in FLASHBACKS:
                    for bid in BRAVERIES:
                        for rid in REPETITIONS:
                            combos.append((sid, pid, skid, fid, bid, rid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = {
        "setting": args.setting or rng.choice(list(SETTINGS)),
        "prohibit": args.prohibit or rng.choice(list(PROHIBITS)),
        "sauerkraut": args.sauerkraut or rng.choice(list(SAUERKRAUTS)),
        "flashback": args.flashback or rng.choice(list(FLASHBACKS)),
        "bravery": args.bravery or rng.choice(list(BRAVERIES)),
        "repetition": args.repetition or rng.choice(list(REPETITIONS)),
        "action": args.action or rng.choice(list(ACTIONS)),
    }
    if choices["setting"] not in SETTINGS:
        raise StoryError("Unknown setting.")
    if choices["prohibit"] not in PROHIBITS or choices["sauerkraut"] not in SAUERKRAUTS:
        raise StoryError("Unknown object choice.")
    if choices["flashback"] not in FLASHBACKS or choices["bravery"] not in BRAVERIES or choices["repetition"] not in REPETITIONS:
        raise StoryError("Unknown narrative instrument.")
    if args.child_gender and args.child_gender not in {"girl", "boy"}:
        raise StoryError("Invalid child gender.")
    if args.parent_gender and args.parent_gender not in {"mother", "father"}:
        raise StoryError("Invalid parent gender.")

    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    child = args.child or _pick_name(rng, child_gender)
    parent = args.parent or ("Mum" if parent_gender == "mother" else "Dad")
    return StoryParams(
        setting=choices["setting"],
        child=child,
        child_gender=child_gender,
        parent=parent,
        parent_gender=parent_gender,
        prohibit=choices["prohibit"],
        sauerkraut=choices["sauerkraut"],
        flashback=choices["flashback"],
        bravery=choices["bravery"],
        repetition=choices["repetition"],
        action=choices["action"],
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.sauerkraut not in SAUERKRAUTS:
        raise StoryError("Unknown sauerkraut choice.")
    if params.flashback not in FLASHBACKS or params.bravery not in BRAVERIES or params.repetition not in REPETITIONS:
        raise StoryError("Unknown narrative instrument.")
    if params.action not in ACTIONS:
        raise StoryError("Unknown action.")
    if params.prohibit not in PROHIBITS:
        raise StoryError("Unknown prohibition.")

    world = tell(
        SETTINGS[params.setting],
        child_name=params.child,
        child_gender=params.child_gender,
        parent_name=params.parent,
        parent_gender=params.parent_gender,
        prohibit=PROHIBITS[params.prohibit],
        sauerkraut=SAUERKRAUTS[params.sauerkraut],
        flashback_prop=FLASHBACKS[params.flashback],
        bravery=BRAVERIES[params.bravery],
        repetition=REPETITIONS[params.repetition],
        action=ACTIONS[params.action],
    )
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
    StoryParams(
        setting="old_house",
        child="Mina",
        child_gender="girl",
        parent="Mum",
        parent_gender="mother",
        prohibit="cellar",
        sauerkraut="jar",
        flashback="memory",
        bravery="courage",
        repetition="echo",
        action="open",
    ),
    StoryParams(
        setting="attic_home",
        child="Theo",
        child_gender="boy",
        parent="Dad",
        parent_gender="father",
        prohibit="attic",
        sauerkraut="bowl",
        flashback="memory",
        bravery="courage",
        repetition="echo",
        action="open",
    ),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROHIBITS:
        lines.append(asp.fact("prohibit", pid))
    for sid in SAUERKRAUTS:
        lines.append(asp.fact("sauerkraut", sid))
    for fid in FLASHBACKS:
        lines.append(asp.fact("flashback", fid))
    for bid in BRAVERIES:
        lines.append(asp.fact("bravery", bid))
    for rid in REPETITIONS:
        lines.append(asp.fact("repetition", rid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, K, F, B, R) :- setting(S), sauerkraut(K), flashback(F), bravery(B), repetition(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_story_choices()):
        print("OK: ASP matches Python valid-combos gate.")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid-combos gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:  # pragma: no cover - defensive
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
