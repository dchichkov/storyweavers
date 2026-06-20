#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/flamingo_elementary_humor_whodunit.py
======================================================================

A standalone story world for a tiny, humorous elementary-school whodunit.

Premise:
- At an elementary school, something pink and silly goes missing or gets moved.
- A child detective follows clue-driven, stateful evidence.
- The "mystery" resolves with an ordinary, funny explanation that fits the clues.
- The ending image proves what changed: the class knows the truth, the item is
  back where it belongs, and the joke has turned into a harmless laugh.

This world keeps the style close to a whodunit while staying child-facing and
lighthearted. It uses typed entities with physical meters and emotional memes,
a small forward-chaining rule engine, a Python reasonableness gate, and an
inline ASP twin for parity checks.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/flamingo_elementary_humor_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/flamingo_elementary_humor_whodunit.py --all
    python storyworlds/worlds/gpt-5.4-mini/flamingo_elementary_humor_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/flamingo_elementary_humor_whodunit.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4-mini/flamingo_elementary_humor_whodunit.py --json
    python storyworlds/worlds/gpt-5.4-mini/flamingo_elementary_humor_whodunit.py --verify
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

# The whodunit is grounded in a tiny elementary school world. The "humor" comes
# from absurd but harmless clues, not from cruelty or punishment.
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    movable: bool = False
    pink: bool = False
    noisy: bool = False
    sticky: bool = False
    muddy: bool = False
    feathered: bool = False
    edible: bool = False
    clue: bool = False

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    friendly: bool = True
    school: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Mystery:
    id: str
    question: str
    object_label: str
    object_phrase: str
    object_kind: str
    reveal_phrase: str
    ending_image: str
    clue_word: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Suspect:
    id: str
    label: str
    role: str
    kind_of_joke: str
    alibi: str
    hidden: str
    can_move: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Clue:
    id: str
    label: str
    phrase: str
    points_to: str
    certainty: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Resolution:
    id: str
    label: str
    text: str
    effect: str
    humor_line: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.trace_notes = list(self.trace_notes)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_clue_heat(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["found"] < THRESHOLD:
            continue
        sig = ("clue_heat", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        detective = world.facts.get("detective")
        if detective is not None:
            detective.memes["focus"] += 1
        out.append(f"__trace__")
    return out


def _r_jiggle(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["moved"] < THRESHOLD:
            continue
        sig = ("jiggle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in world.characters():
            ch.memes["curiosity"] += 1
        out.append(f"__trace__")
    return out


def _r_soft_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("humor_burst") and "class" in world.entities:
        sig = ("soft_laugh",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("class").meters["cheer"] += 1
            out.append("__trace__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("clue_heat", "social", _r_clue_heat),
    Rule("jiggle", "physical", _r_jiggle),
    Rule("soft_laugh", "social", _r_soft_laugh),
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


def is_reasonable(setting: Setting, mystery: Mystery, suspect: Suspect, clue: Clue, resolution: Resolution) -> bool:
    if not setting.school:
        return False
    if mystery.object_kind == "flamingo" and not mystery.object_phrase:
        return False
    if clue.points_to != suspect.id:
        return False
    if resolution.effect not in {"return", "reveal", "laugh"}:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            for sus in SUSPECTS:
                for cid in CLUES:
                    if CLUES[cid].points_to != sus:
                        continue
                    for rid in RESOLUTIONS:
                        if is_reasonable(SETTINGS[sid], MYSTERIES[mid], SUSPECTS[sus], CLUES[cid], RESOLUTIONS[rid]):
                            combos.append((sid, mid, sus, cid))
    return combos


def explain_rejection(setting: Setting, mystery: Mystery, suspect: Optional[Suspect] = None, clue: Optional[Clue] = None) -> str:
    if not setting.school:
        return f"(No story: this world needs an elementary school setting.)"
    if mystery.object_kind == "flamingo" and mystery.object_phrase:
        return ""
    return "(No story: the mystery setup is too thin to make a real whodunit.)"


def predict_reveal(world: World, mystery_id: str, suspect_id: str, clue_id: str) -> dict:
    sim = world.copy()
    _do_search(sim, sim.get("detective"), MYSTERIES[mystery_id], SUSPECTS[suspect_id], CLUES[clue_id], narrate=False)
    return {
        "found": sim.get("object").meters["found"] >= THRESHOLD,
        "laugh": sim.get("class").meters["cheer"] >= THRESHOLD,
    }


def _move_object(world: World, obj: Entity, destination: Entity) -> None:
    obj.meters["moved"] += 1
    obj.attrs["where"] = destination.id


def _add_clue(world: World, clue: Clue) -> Entity:
    ent = world.add(Entity(id=clue.id, kind="thing", type="clue", label=clue.label, clue=True, movable=True))
    ent.meters["found"] += 1
    return ent


def _do_search(world: World, detective: Entity, mystery: Mystery, suspect: Suspect, clue: Clue, narrate: bool = True) -> None:
    object_ent = world.get("object")
    if clue.id == "feather":
        object_ent.meters["found"] += 1
    else:
        object_ent.meters["found"] += 1
    propagate(world, narrate=narrate)


def open_scene(world: World, detective: Entity, friend: Entity, mystery: Mystery, setting: Setting) -> None:
    detective.memes["interest"] += 1
    friend.memes["interest"] += 1
    world.say(
        f"At {setting.place}, {detective.id} and {friend.id} found a mystery waiting right in the middle of the room. "
        f"The missing thing was {mystery.object_phrase}."
    )
    world.say(
        f'"We need to solve it," said {detective.id}. "This is an elementary case."'
    )


def introduce_suspects(world: World, mystery: Mystery, suspects: list[Suspect]) -> None:
    world.say(
        f"They looked at the clues like tiny detectives. One clue was {mystery.clue_word}, and that made everybody smile a little."
    )
    if suspects:
        names = ", ".join(s.label for s in suspects[:-1])
        if len(suspects) > 1:
            names = f"{names}, and {suspects[-1].label}"
        else:
            names = suspects[0].label
        world.say(f"The suspects were {names}.")


def examine_clue(world: World, detective: Entity, clue: Clue, suspect: Suspect) -> None:
    detective.memes["focus"] += 1
    world.say(
        f'{detective.id} found {clue.phrase}. It pointed toward {suspect.label}, which seemed suspicious and a little funny.'
    )


def joke_mislead(world: World, suspect: Suspect, mystery: Mystery) -> None:
    suspect_mood = world.get(suspect.id)
    suspect_mood.memes["nervous"] += 1
    world.say(
        f"{suspect.label} looked guilty for exactly one second, because {suspect.kind_of_joke} sounded like the sort of thing a silly person would do."
    )


def reveal(world: World, detective: Entity, suspect: Suspect, resolution: Resolution, mystery: Mystery) -> None:
    detective.memes["certainty"] += 1
    world.say(
        f"Then {detective.id} put the clues together. {resolution.text}. "
        f"The answer was not a big bad trick at all, just {suspect.hidden}."
    )
    world.say(resolution.humor_line)


def ending(world: World, mystery: Mystery, resolution: Resolution) -> None:
    if mystery.id == "lion":
        ending_image = "the pink flamingo stood on the teacher's desk again, looking as proud as a parade hat"
    else:
        ending_image = mystery.ending_image
    world.say(
        f"In the end, {mystery.object_phrase} was back where it belonged, and the whole class could laugh at the silly mix-up."
    )
    world.say(ending_image)


def build_story(world: World, params: "StoryParams") -> None:
    detective = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender, role="detective"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="helper"))
    teacher = world.add(Entity(id="Teacher", kind="character", type=params.teacher_gender, role="adult", label="the teacher"))
    class_ent = world.add(Entity(id="class", kind="place", type="classroom", label="the class"))
    obj = world.add(Entity(id="object", kind="thing", type=params.mystery, label=params.object_label, movable=True, pink=True))
    obj.attrs["where"] = "unknown"
    mystery = MYSTERIES[params.mystery]
    suspect = SUSPECTS[params.suspect]
    clue = CLUES[params.clue]
    resolution = RESOLUTIONS[params.resolution]

    world.facts.update(
        detective=detective,
        friend=friend,
        teacher=teacher,
        class_ent=class_ent,
        object=obj,
        mystery=mystery,
        suspect=suspect,
        clue=clue,
        resolution=resolution,
    )

    open_scene(world, detective, friend, mystery, SETTINGS[params.setting])
    world.para()
    introduce_suspects(world, mystery, [suspect])
    joke_mislead(world, suspect, mystery)
    examine_clue(world, detective, clue, suspect)
    reveal(world, detective, suspect, resolution, mystery)
    world.para()
    ending(world, mystery, resolution)

    obj.meters["found"] += 1
    class_ent.meters["cheer"] += 1
    world.facts["humor_burst"] = True


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    suspect: str
    clue: str
    resolution: str
    detective: str
    detective_gender: str
    friend: str
    friend_gender: str
    teacher_gender: str
    object_label: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


SETTINGS = {
    "hall": Setting("hall", "the elementary school hall", school=True, tags={"school", "hall"}),
    "art": Setting("art", "the elementary school art room", school=True, tags={"school", "art"}),
    "cafeteria": Setting("cafeteria", "the elementary school cafeteria", school=True, tags={"school", "cafeteria"}),
}

MYSTERIES = {
    "flamingo": Mystery(
        "flamingo",
        "Who moved the pink flamingo?",
        "pink flamingo",
        "a pink flamingo",
        "flamingo",
        "moved the flamingo to a sunny spot near the window",
        "the pink flamingo was back on its stand, looking as tall as a pencil with feathers",
        "pink",
        tags={"flamingo", "pink", "school"},
    ),
    "marker": Mystery(
        "marker",
        "Who borrowed the giant marker?",
        "giant marker",
        "a giant marker",
        "marker",
        "used the marker to make a giant smiley face",
        "the giant marker was back in the caddy, pretending nothing had happened",
        "marker",
        tags={"marker", "school"},
    ),
}

SUSPECTS = {
    "custodian": Suspect(
        "custodian",
        "Mr. Mop",
        "custodian",
        "moved things to clean the floor",
        "he was drying the floor",
        "he had found the flamingo under a chair and set it by the window",
        tags={"adult", "school"},
    ),
    "artist": Suspect(
        "artist",
        "Ms. Paint",
        "art teacher",
        "makes everything look like a poster",
        "she was planning a class display",
        "she had borrowed the flamingo for a silly art corner",
        tags={"adult", "art"},
    ),
    "duck": Suspect(
        "duck",
        "Coach Duck",
        "liked dramatic entrances",
        "he was practicing a noisy march",
        "he had nothing to do with it except walking too loudly",
        tags={"coach", "joke"},
    ),
}

CLUES = {
    "feather": Clue(
        "feather",
        "one pink feather",
        "one pink feather stuck to the chalk tray",
        "flamingo",
        3,
        tags={"flamingo", "pink"},
    ),
    "footprint": Clue(
        "footprint",
        "tiny wet footprints",
        "tiny wet footprints that led toward the window",
        "custodian",
        2,
        tags={"water", "school"},
    ),
    "paint": Clue(
        "paint",
        "a smear of blue paint",
        "a smear of blue paint on the stand",
        "artist",
        2,
        tags={"paint", "art"},
    ),
}

RESOLUTIONS = {
    "return": Resolution(
        "return",
        "Return it kindly",
        "the flamingo had only been moved, not stolen",
        "return",
        "Everybody laughed because the big mystery was just a small move with a silly pose.",
        tags={"return", "humor"},
    ),
    "reveal": Resolution(
        "reveal",
        "Reveal the joke",
        "the truth was hidden in the most ordinary place",
        "reveal",
        "The joke was that the flamingo had been standing by the window the whole time, as if it were watching for popcorn.",
        tags={"reveal", "humor"},
    ),
}

DETECTIVE_NAMES = ["Mina", "Noah", "Lia", "Owen", "Ivy", "Eli", "Ruby", "Theo"]
FRIEND_NAMES = ["Sam", "June", "Pip", "Ben", "Wren", "Maya", "Ari", "Zoe"]


def aspirational_validity() -> list[tuple[str, str, str, str]]:
    return valid_combos()


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.school:
            lines.append(asp.fact("school", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if "flamingo" in m.tags:
            lines.append(asp.fact("flamingo_mystery", mid))
        if "pink" in m.tags:
            lines.append(asp.fact("pink", mid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("points_to", cid, c.points_to))
        lines.append(asp.fact("certainty", cid, c.certainty))
    for rid, r in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, Su, C) :- school(S), mystery(M), suspect(Su), clue(C), points_to(C, Su).
reasonable(S, M, Su, C) :- valid(S, M, Su, C), school(S).
"""


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combo gate:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny humorous elementary-school whodunit with a pink flamingo."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--detective")
    ap.add_argument("--friend")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("(Unknown setting.)")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("(Unknown mystery.)")
    if args.suspect and args.suspect not in SUSPECTS:
        raise StoryError("(Unknown suspect.)")
    if args.clue and args.clue not in CLUES:
        raise StoryError("(Unknown clue.)")
    if args.resolution and args.resolution not in RESOLUTIONS:
        raise StoryError("(Unknown resolution.)")

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.suspect is None or c[2] == args.suspect)
        and (args.clue is None or c[3] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, mystery, suspect, clue = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice(sorted(RESOLUTIONS))
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != detective])
    parent = args.parent or rng.choice(["mother", "father"])
    detective_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if detective_gender == "girl" and rng.random() < 0.5 else "girl"
    object_label = MYSTERIES[mystery].object_phrase
    if mystery == "flamingo":
        object_label = "a pink flamingo"
    return StoryParams(
        setting=setting,
        mystery=mystery,
        suspect=suspect,
        clue=clue,
        resolution=resolution,
        detective=detective,
        detective_gender=detective_gender,
        friend=friend,
        friend_gender=friend_gender,
        teacher_gender=parent,
        object_label=object_label,
    )


def introduce(world: World, detective: Entity, friend: Entity, mystery: Mystery, setting: Setting) -> None:
    detective.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"At {setting.place}, {detective.id} noticed that the class's {mystery.object_phrase} had disappeared."
    )
    world.say(
        f"{friend.id} gasped, because this was not just any missing thing -- it was an elementary mystery, and it looked pink enough to blush."
    )


def clue_scene(world: World, clue: Clue, suspect: Suspect) -> None:
    world.say(
        f"{clue.phrase} was found near the stand, and it pointed toward {suspect.label}."
    )
    world.say(
        f"That looked suspicious, but also a little funny, because {suspect.kind_of_joke} sounded like the kind of story a kid might tell with a grin."
    )


def question(world: World, detective: Entity, suspect: Suspect, mystery: Mystery) -> None:
    detective.memes["focus"] += 1
    world.say(
        f'{detective.id} squinted at the clues. "Who would move a flamingo in an elementary school?" {detective.pronoun()} wondered.'
    )
    world.say(
        f"Only someone who knew the room well would choose such a spot, and that narrowed the case to {suspect.label}."
    )


def reveal_world(world: World, suspect: Suspect, clue: Clue, mystery: Mystery, resolution: Resolution) -> None:
    world.say(
        f"Then the clue turned the whole case around. {resolution.text}, which matched {clue.label} and made the answer plain."
    )
    world.say(
        f"{suspect.label} admitted it with a sheepish smile: {suspect.hidden}. {resolution.humor_line}"
    )


def ending(world: World, mystery: Mystery) -> None:
    world.say(
        f"In the end, the {mystery.object_label} was back on its stand, and the class could stop hunting for a thief and start laughing at the very small drama."
    )
    world.say(mystery.ending_image)


def tell(setting: Setting, mystery: Mystery, suspect: Suspect, clue: Clue, resolution: Resolution,
         detective_name: str = "Mina", detective_gender: str = "girl",
         friend_name: str = "Sam", friend_gender: str = "boy",
         teacher_type: str = "mother") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="helper"))
    teacher = world.add(Entity(id="Teacher", kind="character", type=teacher_type, role="adult", label="the teacher"))
    class_ent = world.add(Entity(id="class", kind="place", type="classroom", label="the class"))
    object_ent = world.add(Entity(
        id="object",
        kind="thing",
        type=mystery.object_kind,
        label=mystery.object_label,
        movable=True,
        pink=("pink" in mystery.tags),
        feathered=("flamingo" in mystery.tags),
    ))
    object_ent.attrs["where"] = "missing"
    clue_ent = world.add(Entity(id="clue", kind="thing", type="clue", label=clue.label, clue=True))

    world.facts.update(
        detective=detective,
        friend=friend,
        teacher=teacher,
        class_ent=class_ent,
        object=object_ent,
        mystery=mystery,
        suspect=suspect,
        clue=clue,
        resolution=resolution,
    )

    introduce(world, detective, friend, mystery, setting)
    world.para()
    clue_scene(world, clue, suspect)
    question(world, detective, suspect, mystery)
    reveal_world(world, suspect, clue, mystery, resolution)
    world.para()
    ending(world, mystery)

    object_ent.meters["found"] += 1
    class_ent.meters["cheer"] += 1
    world.facts["humor_burst"] = True
    world.facts["resolved"] = True
    world.facts["object_where"] = "stand"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery = f["mystery"]
    suspect = f["suspect"]
    clue = f["clue"]
    if mystery.id == "flamingo":
        return [
            'Write a funny whodunit for a young child set at an elementary school, about a missing pink flamingo and a clue that points to the culprit.',
            f"Tell a playful mystery story where {f['detective'].id} follows {clue.label} and finds out who moved the flamingo at elementary school.",
            f'Write a whodunit with humor in which the word "flamingo" appears and the answer is a harmless school mix-up.',
        ]
    return [
        'Write a funny elementary-school mystery with a clue, a suspect, and a silly reveal.',
        f"Tell a child-friendly whodunit where {f['detective'].id} solves who borrowed the marker using {clue.label}.",
        'Write a brief, humorous detective story that ends with the missing item being found.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    teacher = f["teacher"]
    mystery = f["mystery"]
    suspect = f["suspect"]
    clue = f["clue"]
    resolution = f["resolution"]
    qa: list[tuple[str, str]] = [
        (f"What was the mystery in the story?",
         f"The mystery was {mystery.question.lower()} The class wanted to know where the pink flamingo had gone."),
        (f"Who helped solve the mystery?",
         f"{detective.id} solved it with help from {friend.id}, and the teacher stayed nearby to keep things calm."),
        (f"What clue mattered most?",
         f"{clue.phrase} mattered most because it pointed to {suspect.label}. That clue helped {detective.id} stop guessing and start solving."),
    ]
    qa.append((
        f"Why did {suspect.label} look suspicious?",
        f"{suspect.label} looked suspicious because {suspect.kind_of_joke} sounded like a sneaky joke. But the clues showed it was just a harmless school mix-up."
    ))
    qa.append((
        f"How did the story end?",
        f"It ended with the mystery solved and the flamingo back in place. {resolution.humor_line}"
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mystery = f["mystery"]
    tags = set(mystery.tags) | set(f["clue"].tags) | set(f["resolution"].tags)
    out: list[tuple[str, str]] = []
    if "flamingo" in tags:
        out.extend([
            ("What is a flamingo?",
             "A flamingo is a tall pink bird with long legs and a curved neck. People sometimes use flamingo shapes as decorations too."),
        ])
    if "school" in tags:
        out.extend([
            ("What is an elementary school?",
             "An elementary school is a school for young children. It is a place for learning, playing, and small mysteries like a missing class mascot."),
        ])
    if "pink" in tags:
        out.extend([
            ("What does pink look like?",
             "Pink is a soft, bright color that can look cheerful, silly, or sweet. A pink flamingo stands out right away."),
        ])
    if "humor" in tags:
        out.extend([
            ("What makes a story funny?",
             "A funny story uses silly surprises, playful details, or a harmless mix-up. The humor should make people smile, not feel hurt."),
        ])
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
        flags = [n for n, on in (
            ("pink", e.pink),
            ("feathered", e.feathered),
            ("clue", e.clue),
            ("movable", e.movable),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hall", "flamingo", "custodian", "footprint", "return", "Mina", "girl", "Sam", "boy", "mother"),
    StoryParams("art", "flamingo", "artist", "paint", "reveal", "Owen", "boy", "June", "girl", "father"),
    StoryParams("cafeteria", "marker", "duck", "footprint", "return", "Ivy", "girl", "Pip", "boy", "mother"),
]


def outcome_of(params: StoryParams) -> str:
    return "solved"


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_outcomes() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    return ["return", "reveal"]


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_outcomes())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        SUSPECTS[params.suspect],
        CLUES[params.clue],
        RESOLUTIONS[params.resolution],
        params.detective,
        params.detective_gender,
        params.friend,
        params.friend_gender,
        params.teacher_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            for sus in SUSPECTS:
                for cid in CLUES:
                    if CLUES[cid].points_to != sus:
                        continue
                    for rid in RESOLUTIONS:
                        if is_reasonable(SETTINGS[sid], MYSTERIES[mid], SUSPECTS[sus], CLUES[cid], RESOLUTIONS[rid]):
                            combos.append((sid, mid, sus, cid))
    return combos


def explain_response(rid: str) -> str:
    return "(No story: this world only tells reasonable, harmless reveal stories.)"


def build_story_params(rng: random.Random, args: argparse.Namespace) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.suspect is None or c[2] == args.suspect)
        and (args.clue is None or c[3] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, suspect, clue = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice(sorted(RESOLUTIONS))
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != detective])
    parent = args.parent or rng.choice(["mother", "father"])
    detective_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if detective_gender == "girl" else "girl"
    return StoryParams(setting, mystery, suspect, clue, resolution, detective, detective_gender, friend, friend_gender, parent)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return build_story_params(rng, args)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A humorous elementary-school whodunit about a flamingo."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--detective")
    ap.add_argument("--friend")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_outcomes()
        print(f"{len(combos)} compatible (setting, mystery, suspect, clue) combos:\n")
        for setting, mystery, suspect, clue in combos:
            print(f"  {setting:10} {mystery:10} {suspect:10} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective} and {p.friend}: the {p.mystery} mystery ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
