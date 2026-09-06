#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bead_sound_effects_cautionary_repetition_animal_story.py
========================================================================================

A small animal-story world: a curious young animal finds a shiny bead, plays with
it, gets warned about a risky place, and learns to choose a safer way. The story
uses sound effects, cautionary beats, and repetition while keeping the prose
child-facing and state-driven.

The domain is intentionally tiny:
- one bead
- one risky place where the bead can be lost or swallowed
- one helper who warns
- one safe ending image that proves what changed
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "fox":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "rabbit":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    animal: str
    helper: str
    bead: str
    risky_place: str
    safe_place: str
    sound1: str
    sound2: str
    caution_level: int = 1
    seed: Optional[int] = None
    premise: str = "pattern_game"
    mishap: str = "eager_tap"
    recovery: str = "leaf_gate"
    practice: str = "stop_look_ask"
    ending: str = "lidded_box"
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


@dataclass
class Beast:
    id: str
    type: str
    label: str
    sound: str
    cautious_words: str
    nibble_risk: bool = False
    drop_risk: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return Entity(id=self.id, type=self.type, label=self.label).pronoun(case)
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    risky: bool = False
    safe: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    bead = world.entities.get("bead")
    if bead and bead.meters["near_risk"] >= THRESHOLD:
        if "place" in world.entities:
            world.get("place").meters["danger"] += 1
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["worry"] += 1
        sig = ("risk",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__danger__")
    return out


CAUSAL_RULES = [Rule("risk", _r_risk)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


ANIMALS = {
    "rabbit": Beast("rabbit", "rabbit", "rabbit", "bop-bop", "Don't put tiny things in your mouth.", nibble_risk=True),
    "fox": Beast("fox", "fox", "fox", "tip-tip", "Be careful near the edge.", drop_risk=True),
    "turtle": Beast("turtle", "turtle", "turtle", "clink-clink", "Slow down and look first.", nibble_risk=True),
}

PLACES = {
    "grass": Place("grass", "a wide craft tray on the soft grass", safe=True),
    "pond": Place("pond", "the pond edge", risky=True),
    "nest": Place("nest", "the nest bowl", risky=True),
}

BEADS = {
    "red": {"label": "a red bead", "phrase": "a little red bead", "sound": "plink"},
    "blue": {"label": "a blue bead", "phrase": "a bright blue bead", "sound": "ting"},
    "gold": {"label": "a gold bead", "phrase": "a shiny gold bead", "sound": "clink"},
}

SOUNDS = ["plink-plink", "ting-ting", "clink-clink", "click-click"]

PREMISES = [
    "bracelet_board",
    "counting_game",
    "gift_string",
    "pattern_game",
    "sound_parade",
    "treasure_find",
]
MISHAPS = [
    "breeze",
    "eager_tap",
    "loose_thread",
    "sneeze",
    "surprise_hop",
    "wobbly_board",
]
MISHAPS_BY_PREMISE = {
    "bracelet_board": ["loose_thread", "sneeze", "surprise_hop", "wobbly_board"],
    "counting_game": ["breeze", "eager_tap", "sneeze", "surprise_hop"],
    "gift_string": ["breeze", "loose_thread", "sneeze", "surprise_hop"],
    "pattern_game": ["breeze", "eager_tap", "sneeze", "wobbly_board"],
    "sound_parade": ["eager_tap", "sneeze", "surprise_hop", "wobbly_board"],
    "treasure_find": ["breeze", "eager_tap", "sneeze", "surprise_hop"],
}
RECOVERIES = [
    "cloth_catch",
    "cup_cover",
    "leaf_gate",
    "spoon_stop",
    "team_pause",
    "tray_tilt",
]
PRACTICES = [
    "container_rule",
    "count_and_check",
    "mat_rule",
    "slow_hands",
    "stop_look_ask",
]
ENDINGS = [
    "craft_tray",
    "high_shelf",
    "lidded_box",
    "tied_pouch",
    "threaded_garland",
    "window_pattern",
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for animal in ANIMALS:
        for bead in BEADS:
            for place in PLACES:
                if PLACES[place].risky:
                    combos.append((animal, bead, place))
    return combos


def explain_rejection(animal: str, bead: str, place: str) -> str:
    if not PLACES[place].risky:
        return f"(No story: {bead} in {PLACES[place].label} is not risky enough for a cautionary animal story.)"
    return "(No story: this combination does not create a clear cautionary turn.)"


def _names(animal: Entity, helper: Entity) -> tuple[str, str]:
    return animal.id.capitalize(), helper.id.capitalize()


def begin(world: World, animal: Entity, helper: Entity, bead: Entity, params: StoryParams) -> None:
    animal_name, helper_name = _names(animal, helper)
    openings = {
        "bracelet_board": (
            f"On a bright afternoon, {animal_name}, a young {animal.type}, joined the grown-up helper {helper_name} at a low craft board. "
            f"They planned to thread {bead.label} onto a bracelet for the forest fair."
        ),
        "counting_game": (
            f"After breakfast, {animal_name}, a young {animal.type}, spread a cloth beside the grown-up helper {helper_name}. "
            f"They placed {bead.label} on it for a careful counting game."
        ),
        "gift_string": (
            f"{animal_name}, a young {animal.type}, wanted to make a tiny beaded gift for a friend. "
            f"The grown-up helper {helper_name} brought a tray, some thick string, and {bead.label}."
        ),
        "pattern_game": (
            f"One sunny morning, {animal_name}, a young {animal.type}, sat with the grown-up helper {helper_name} on the grass. "
            f"They were arranging {bead.label} in a bright pattern on a wide tray."
        ),
        "sound_parade": (
            f"At music time, {animal_name}, a young {animal.type}, and the grown-up helper {helper_name} made a quiet rhythm tray. "
            f"Inside it, {bead.label} could rattle without rolling away."
        ),
        "treasure_find": (
            f"While tidying the garden path, {animal_name}, a young {animal.type}, spotted {bead.label}. "
            f"Instead of picking it up alone, {animal_name} called the grown-up helper {helper_name}, who moved it onto a cloth-lined tray."
        ),
    }
    world.say(openings[params.premise])
    world.say(
        f'"{params.sound1}!" went the bead. "{params.sound1}, {params.sound1}," '
        f'{animal_name} echoed, and {helper_name} answered, "{params.sound2}!"'
    )


def warn(world: World, helper: Entity, animal: Entity, bead: Entity, place: Entity) -> None:
    helper.memes["care"] += 1
    animal_name, helper_name = _names(animal, helper)
    world.say(
        f'{helper_name} pointed toward {place.label}. "{animal_name}, pause and keep the bead on the tray," '
        f'{helper_name} said. "A bead is tiny, so we keep it away from mouths and risky places."'
    )


def almost_drop(world: World, animal: Entity, bead: Entity, place: Entity, params: StoryParams) -> str:
    animal_name = animal.id.capitalize()
    mishaps = {
        "breeze": (
            f"A breeze lifted one corner of the cloth. Flip-flap! The bead began rolling toward {place.label}.",
            "a breeze lifted the cloth",
        ),
        "eager_tap": (
            f"{animal_name} tapped the tray a little too eagerly. Tap, tap, TAP! The bead hopped over the rim and rolled toward {place.label}.",
            f"{animal_name} tapped the tray too eagerly",
        ),
        "loose_thread": (
            f"The thick string caught on a twig and pulled free. Zip, plip! The bead slid off its end toward {place.label}.",
            "the string caught on a twig and pulled free",
        ),
        "sneeze": (
            f'A puff of pollen made {animal_name} sneeze. "Ah-choo!" The cloth jumped, and the bead spun toward {place.label}.',
            f"a sneeze jolted the cloth",
        ),
        "surprise_hop": (
            f"A grasshopper sprang past with a boing. {animal_name} gave a surprised hop, bumped the board, and sent the bead toward {place.label}.",
            f"a grasshopper startled {animal_name} into bumping the board",
        ),
        "wobbly_board": (
            f"One acorn under the board made it wobble. Tip-tip, tilt! The bead curved toward {place.label}.",
            "an acorn made the board wobble",
        ),
    }
    text, cause = mishaps[params.mishap]
    bead.meters["near_risk"] += 1
    world.say(text)
    propagate(world, narrate=False)
    return cause


def recover(
    world: World,
    helper: Entity,
    animal: Entity,
    bead: Entity,
    safe: Entity,
    params: StoryParams,
) -> str:
    animal_name, helper_name = _names(animal, helper)
    recoveries = {
        "cloth_catch": (
            f'{animal_name} called, "Bead rolling!" {helper_name} spread the cloth in its path. Fuff! The cloth caught it well before the edge.',
            f"{animal_name} called out and {helper_name} caught it with the cloth",
        ),
        "cup_cover": (
            f'{helper_name} said, "Hands still." {animal_name} froze while {helper_name} placed a clear cup over the bead. Clink! Together they slid cup and bead back to the tray.',
            f"they paused, covered it with a clear cup, and slid it back",
        ),
        "leaf_gate": (
            f"{helper_name} laid a broad leaf across the bead's path. Swish, stop! {animal_name} fetched the tray while {helper_name} guarded the little leaf gate.",
            f"{helper_name} blocked it with a broad leaf while {animal_name} fetched the tray",
        ),
        "spoon_stop": (
            f"A wooden spoon lay beside the craft things. {animal_name} held still while {helper_name} set the spoon across the path. Tok! The bead stopped against it.",
            f"{helper_name} safely stopped it with a wooden spoon",
        ),
        "team_pause": (
            f'{animal_name} remembered the warning and called, "Stop, look, ask!" Both animals stayed back. {helper_name} brought the tray close, then gently swept the bead into it.',
            f"they stayed back, brought the tray close, and swept the bead into it",
        ),
        "tray_tilt": (
            f"{helper_name} set the wide tray downhill from the bead. {animal_name} pointed but did not grab. Rrrroll, plink! The bead rolled safely into the tray.",
            f"they placed the tray in its path and let it roll safely inside",
        ),
    }
    text, action = recoveries[params.recovery]
    world.say(text)
    bead.meters["near_risk"] = 0
    bead.meters["contained"] += 1
    safe.meters["holding_bead"] += 1
    return action


def lesson(world: World, animal: Entity, helper: Entity, bead: Entity, safe: Entity, params: StoryParams) -> None:
    animal_name, helper_name = _names(animal, helper)
    animal.memes["lesson"] += 1
    animal.memes["relief"] += 1
    helper.memes["relief"] += 1
    practices = {
        "container_rule": f'They practiced the rule together: "Out for crafts, in the box; out for crafts, in the box." Then {animal_name} put the bead away before leaving.',
        "count_and_check": f'{animal_name} counted slowly, "One bead out, one bead back." {helper_name} checked the empty cloth, and they counted once more.',
        "mat_rule": f'They moved every craft piece to the middle of the mat. "Middle of the mat, safe where we sat," they repeated while they tidied.',
        "slow_hands": f'{animal_name} tried again with slow paws over the tray. "Slow hands, safe bead. Slow hands, safe bead," {animal_name} repeated.',
        "stop_look_ask": f'{animal_name} practiced the three-part warning: "Stop, look, ask. Stop, look, ask." {helper_name} smiled when {animal_name} asked before touching the bead again.',
    }
    world.say(practices[params.practice])
    endings = {
        "craft_tray": f"At sunset, the little bead rested in the tray's covered center cup while {helper_name} carried it to the high craft cupboard.",
        "high_shelf": f"When craft time ended, {helper_name} closed a small container and placed it on a high shelf. Below it, {animal_name}'s paws were empty and safe.",
        "lidded_box": f"Click went the lid of the craft box. Through its clear top, {animal_name} could see the bead resting safely inside.",
        "tied_pouch": f"{helper_name} tied the bead inside a little craft pouch. It gave one soft clink, then hung safely beyond the animals' reach.",
        "threaded_garland": f"With {helper_name} holding both ends, they threaded the bead onto a finished garland and tied two strong knots. It gleamed safely above their picnic table.",
        "window_pattern": f"They sealed the bead in a clear pattern jar with the other craft pieces. Evening light shone through the colors while the closed jar stood safely on the shelf.",
    }
    world.say(endings[params.ending])


def tell(params: StoryParams) -> World:
    world = World()
    animal = world.add(Entity(id=params.animal, kind="character", type=params.animal, role="young"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper, role="grown-up helper"))
    bead = world.add(Entity(id="bead", kind="thing", type="bead", label=params.bead))
    risky = world.add(Entity(id="place", kind="thing", type="place", label=PLACES[params.risky_place].label))
    safe = world.add(Entity(id="basket", kind="thing", type="basket", label=PLACES[params.safe_place].label))
    animal.attrs["sound"] = params.sound1
    animal.attrs["repeat"] = f"{params.sound1}! {params.sound1}!"
    helper.attrs["caution"] = "Small beads stay on a tray or inside a closed container."
    begin(world, animal, helper, bead, params)
    world.para()
    warn(world, helper, animal, bead, risky)
    cause = almost_drop(world, animal, bead, risky, params)
    recovery = recover(world, helper, animal, bead, safe, params)
    world.para()
    lesson(world, animal, helper, bead, safe, params)
    world.facts.update(
        animal=animal,
        helper=helper,
        bead=bead,
        place=risky,
        safe=safe,
        cause=cause,
        recovery=recovery,
        premise=params.premise,
        practice=params.practice,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal = f["animal"].id
    return [
        "Write an animal story for a young child that includes a bead, sound effects, repetition, and a clear safety warning.",
        f"Tell a cautionary animal story where {animal} uses a bead during a supervised activity, notices a mishap, and helps keep it safe.",
        "Write a complete story in which a tiny craft object nearly reaches a risky place, the characters respond calmly, and the final image proves it is contained.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    animal = f["animal"].id
    helper = f["helper"].id
    return [
        ("What caused the bead to move toward the risky place?", f"The bead moved because {f['cause']}. That turned their careful activity into a problem they had to solve."),
        ("How did the animals make the bead safe again?", f"{animal.capitalize()} and {helper.capitalize()} made it safe when {f['recovery']}. They did not use their mouths or rush after the tiny bead."),
        ("What safety lesson did the young animal practice?", f"{animal.capitalize()} practiced keeping small beads on a tray or in a closed container and asking for help. The repeated words made the rule easier to remember."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a bead?", "A bead is a small object with a hole for thread or cord. Young children should use beads only with a grown-up and keep them away from mouths."),
        ("Why should little animals be careful with tiny objects?", "Tiny objects can be swallowed or lost easily. That is why grown-ups warn children to keep them in a safe place."),
        ("What do sound effects do in a story?", "Sound effects make the action feel lively and fun. They help the reader hear the moment in their head."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(animal="rabbit", helper="fox", bead="a red bead", risky_place="pond", safe_place="grass", sound1="plink", sound2="ting", caution_level=1),
    StoryParams(animal="turtle", helper="rabbit", bead="a gold bead", risky_place="nest", safe_place="grass", sound1="clink", sound2="click", caution_level=1),
]


def explain_response(params: StoryParams) -> str:
    return "(Refusing: unsupported story parameters.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for b in BEADS:
        lines.append(asp.fact("bead", b))
    for p, pl in PLACES.items():
        lines.append(asp.fact("place", p))
        if pl.risky:
            lines.append(asp.fact("risky", p))
    return "\n".join(lines)


ASP_RULES = r"""
valid(A,B,P) :- animal(A), bead(B), place(P), risky(P).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH:")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
    try:
        s = generate(CURATED[0])
        assert s.story
        print("OK: smoke test generate() produced a story.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with bead, sound effects, caution, and repetition.")
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--helper", choices=sorted(ANIMALS))
    ap.add_argument("--bead", choices=sorted(BEADS))
    ap.add_argument("--risky-place", dest="risky_place", choices=sorted(k for k, v in PLACES.items() if v.risky))
    ap.add_argument("--safe-place", dest="safe_place", choices=sorted(k for k, v in PLACES.items() if v.safe))
    ap.add_argument("--sound1")
    ap.add_argument("--sound2")
    ap.add_argument("--caution-level", type=int, default=None)
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
    animal = args.animal or rng.choice(sorted(ANIMALS))
    helper = args.helper or rng.choice([a for a in sorted(ANIMALS) if a != animal])
    bead = args.bead or rng.choice(sorted(BEADS))
    risky = args.risky_place or rng.choice([k for k, v in PLACES.items() if v.risky])
    safe = args.safe_place or "grass"
    s1 = args.sound1 or rng.choice(SOUNDS)
    s2 = args.sound2 or rng.choice([s for s in SOUNDS if s != s1])
    premise = rng.choice(PREMISES)
    if not PLACES[risky].risky:
        raise StoryError(explain_rejection(animal, bead, risky))
    return StoryParams(
        animal=animal,
        helper=helper,
        bead=BEADS[bead]["phrase"],
        risky_place=risky,
        safe_place=safe,
        sound1=s1,
        sound2=s2,
        caution_level=args.caution_level if args.caution_level is not None else 1,
        premise=premise,
        mishap=rng.choice(MISHAPS_BY_PREMISE[premise]),
        recovery=rng.choice(RECOVERIES),
        practice=rng.choice(PRACTICES),
        ending=rng.choice(ENDINGS),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        world = tell(params)
    except KeyError as e:
        raise StoryError(f"Invalid parameter: {e}") from e
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(" ", t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
