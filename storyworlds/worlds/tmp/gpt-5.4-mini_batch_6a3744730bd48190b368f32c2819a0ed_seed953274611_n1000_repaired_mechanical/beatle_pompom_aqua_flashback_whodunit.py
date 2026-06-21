#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/beatle_pompom_aqua_flashback_whodunit.py
=========================================================================

A standalone storyworld for a small whodunit with a flashback:
a child notices three odd clues -- a beatle, a pompom, and aqua paint --
and, by remembering an earlier scene, solves the mystery and restores what
was missing.

The world is designed to be:
- small and deterministic given a seed,
- state-driven, with physical meters and emotional memes,
- child-facing and concrete,
- compatible with the shared Storyweavers result API,
- and paired with a tiny ASP twin for parity checks.

This world's core premise:
A costume box goes missing at playtime. The children first chase the wrong
suspect, then a flashback reveals who borrowed the box and why. The final
story ends with the box returned and a neat little clue image proving the
answer.

Seed words: beatle, pompom, aqua
Style: whodunit
Feature: flashback
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
        return self.label or self.id
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
    dark: bool = False
    indoors: bool = True
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
class Clue:
    id: str
    word: str
    label: str
    kind: str
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
class Suspect:
    id: str
    label: str
    age: int
    type: str
    motive: str
    honest: bool
    clue: str
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


@dataclass
class StoryParams:
    place: str = "green_room"
    clue1: str = "beatle"
    clue2: str = "pompom"
    clue3: str = "aqua"
    suspect: str = "nora"
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


PLACES = {
    "green_room": Place(id="green_room", label="the green room", dark=False, indoors=True, tags={"room"}),
    "library_corner": Place(id="library_corner", label="the library corner", dark=True, indoors=True, tags={"room", "dark"}),
    "back_stage": Place(id="back_stage", label="behind the stage curtain", dark=True, indoors=True, tags={"room", "dark"}),
}

CLUES = {
    "beatle": Clue(id="beatle", word="beatle", label="beatle-shaped pin", kind="pin", tags={"beatle", "small"}),
    "pompom": Clue(id="pompom", word="pompom", label="a fluffy pompom", kind="fiber", tags={"pompom", "soft"}),
    "aqua": Clue(id="aqua", word="aqua", label="aqua paint", kind="paint", tags={"aqua", "wet"}),
}

SUSPECTS = {
    "nora": Suspect(id="Nora", label="Nora", age=7, type="girl", motive="to decorate a costume", honest=True, clue="pompom", tags={"helper"}),
    "milo": Suspect(id="Milo", label="Milo", age=8, type="boy", motive="to borrow the art box for a project", honest=True, clue="aqua", tags={"helper"}),
    "ivy": Suspect(id="Ivy", label="Ivy", age=6, type="girl", motive="to hide a surprise until showtime", honest=True, clue="beatle", tags={"helper"}),
}

GIRL_NAMES = ["Nora", "Ivy", "Mia", "Ava", "Luna", "Zoe"]
BOY_NAMES = ["Milo", "Theo", "Eli", "Noah", "Finn", "Ben"]


def hazard(place: Place) -> bool:
    return place.dark


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, place in PLACES.items():
        for sid, suspect in SUSPECTS.items():
            if hazard(place) and suspect.honest:
                out.append((pid, sid))
    return out


def _r_mystery(world: World) -> list[str]:
    out = []
    room = world.get("room")
    if room.meters["mystery"] >= THRESHOLD and ("mystery",) not in world.fired:
        world.fired.add(("mystery",))
        for e in list(world.entities.values()):
            e.memes["curious"] += 1
        out.append("__mystery__")
    return out


def _r_flashback(world: World) -> list[str]:
    out = []
    if world.get("narrator").memes["remember"] >= THRESHOLD and ("flashback",) not in world.fired:
        world.fired.add(("flashback",))
        world.get("narrator").memes["certainty"] += 1
        out.append("__flashback__")
    return out


CAUSAL_RULES = [Rule("mystery", _r_mystery), Rule("flashback", _r_flashback)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def predict_truth(world: World, suspect: Suspect, clue: Clue) -> bool:
    sim = world.copy()
    sim.get("narrator").memes["remember"] += 1
    sim.get("room").meters["mystery"] += 1
    return clue.id == suspect.clue


def intro(world: World, narrator: Entity, place: Place, clue1: Clue, clue2: Clue, clue3: Clue) -> None:
    narrator.memes["interest"] += 1
    world.say(
        f"It was a quiet afternoon in {place.label}, and {narrator.id} noticed three odd things: "
        f"{clue1.word}, {clue2.word}, and {clue3.word}."
    )
    world.say(
        f"That was enough to make {narrator.id} feel like a detective."
    )


def find_missing(world: World, narrator: Entity, box: Entity, place: Place) -> None:
    box.meters["missing"] += 1
    world.get("room").meters["mystery"] += 1
    world.say(
        f"Then the costume box was gone from its shelf, and the whole room felt even stranger."
    )
    if place.dark:
        world.say(
            f"The dark corner behind the curtains looked suspicious, as if it were hiding a secret."
        )


def accuse_wrong(world: World, narrator: Entity, suspect: Suspect) -> None:
    narrator.memes["doubt"] += 1
    world.say(
        f'{narrator.id} looked at {suspect.label} and whispered, "Maybe {suspect.label} took it."'
    )


def flashback(world: World, narrator: Entity, suspect: Suspect, clue: Clue) -> None:
    narrator.memes["remember"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {narrator.id} remembered something from earlier: {suspect.label} had been carrying {clue.label}."
    )
    world.say(
        f"In that memory, {suspect.label} was trying to make the costume sparkle, not steal it."
    )


def solve(world: World, narrator: Entity, suspect: Suspect, box: Entity, place: Place) -> None:
    narrator.memes["certainty"] += 1
    box.meters["found"] += 1
    world.get("room").meters["mystery"] = 0
    world.say(
        f'{narrator.id} hurried back to the hiding place and found the box where {suspect.label} had tucked it safely.'
    )
    world.say(
        f"{suspect.label} had borrowed it to help with a surprise, and the clues all made sense at last."
    )


def ending(world: World, narrator: Entity, box: Entity, clue1: Clue, clue2: Clue, clue3: Clue) -> None:
    narrator.memes["pride"] += 1
    world.say(
        f"By the end, the costume box was back on the shelf, and {clue1.word}, {clue2.word}, and {clue3.word} felt like a proper case file."
    )
    world.say(
        f"{narrator.id} smiled, knowing that a good detective listens, remembers, and checks the facts before pointing a finger."
    )


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    clue1 = CLUES[params.clue1]
    clue2 = CLUES[params.clue2]
    clue3 = CLUES[params.clue3]
    suspect = SUSPECTS[params.suspect]

    narrator = world.add(Entity(id="Pip", kind="character", type="girl", label="Pip"))
    helper = world.add(Entity(id=suspect.label, kind="character", type=suspect.type, label=suspect.label))
    room = world.add(Entity(id="room", type="room", label=place.label))
    box = world.add(Entity(id="box", type="thing", label="the costume box"))
    world.add(Entity(id="narrator", kind="character", type="girl", label="Pip"))

    intro(world, narrator, place, clue1, clue2, clue3)
    world.para()
    find_missing(world, narrator, box, place)
    accuse_wrong(world, narrator, suspect)
    world.para()
    flashback(world, narrator, suspect, clue2 if clue2.id == suspect.clue else clue3)
    solve(world, narrator, suspect, box, place)
    world.para()
    ending(world, narrator, box, clue1, clue2, clue3)

    world.facts.update(
        narrator=narrator,
        helper=helper,
        suspect=suspect,
        place=place,
        clue1=clue1,
        clue2=clue2,
        clue3=clue3,
        box=box,
        outcome="solved",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit for a child that includes the words "{f["clue1"].word}", "{f["clue2"].word}", and "{f["clue3"].word}".',
        f"Tell a flashback mystery where Pip thinks {f['suspect'].label} caused the trouble, then remembers an earlier clue and solves it kindly.",
        "Write a short detective story for a young child where the final answer comes from remembering what happened before.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    suspect = f["suspect"]
    return [
        ("Who is the story about?",
         "It is about Pip, who tries to solve a small mystery and find the missing costume box."),
        ("What was missing?",
         "The costume box was missing from its shelf, which made the room feel like a mystery."),
        ("Why did Pip think at first that " + suspect.label + " might be involved?",
         f"Pip saw {suspect.label} near the clues and guessed wrongly for a moment. But that was only a first guess, not the answer."),
        ("What happened in the flashback?",
         f"Pip remembered seeing {suspect.label} with {world.facts['clue2'].label if world.facts['clue2'].id == suspect.clue else world.facts['clue3'].label}. That memory showed the missing box had been borrowed for a surprise, not stolen."),
        ("How did the mystery end?",
         "Pip found the box, the clues made sense, and everyone could smile because the facts matched the memory."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a detective?",
         "A detective is someone who looks carefully at clues and tries to figure out what really happened."),
        ("What is a flashback?",
         "A flashback is a memory scene that takes the story back to something that happened earlier."),
        ("Why do clues matter in a mystery?",
         "Clues matter because they help the detective check guesses and find the true answer."),
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
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


def explain_rejection(place: Place, suspect: Suspect) -> str:
    if not hazard(place):
        return f"(No story: {place.label} is not a good whodunit setting because it is not mysterious enough.)"
    return "(No story: this combination does not support the mystery premise.)"


def valid_story_combos() -> list[tuple[str, str]]:
    return valid_combos()


def outcome_of(params: StoryParams) -> str:
    return "solved"


ASP_RULES = r"""
mystery(P) :- place(P), dark(P).
interesting(S) :- suspect(S), honest(S).
valid(P, S) :- mystery(P), interesting(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.dark:
            lines.append(asp.fact("dark", pid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        if s.honest:
            lines.append(asp.fact("honest", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_story_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, clue1=None, clue2=None, clue3=None, suspect=None), random.Random(1)))
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    if rc == 0:
        print("OK: ASP parity and smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue1", choices=CLUES)
    ap.add_argument("--clue2", choices=CLUES)
    ap.add_argument("--clue3", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
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
    place = args.place or rng.choice(list(PLACES))
    if not hazard(PLACES[place]):
        raise StoryError(explain_rejection(PLACES[place], SUSPECTS[args.suspect] if args.suspect else next(iter(SUSPECTS.values()))))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    return StoryParams(
        place=place,
        clue1=args.clue1 or "beatle",
        clue2=args.clue2 or "pompom",
        clue3=args.clue3 or "aqua",
        suspect=suspect,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.clue1 not in CLUES or params.clue2 not in CLUES or params.clue3 not in CLUES:
        raise StoryError("Unknown clue.")
    if params.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    world = tell(params)
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


CURATED = [
    StoryParams(place="library_corner", clue1="beatle", clue2="pompom", clue3="aqua", suspect="nora", seed=1),
    StoryParams(place="back_stage", clue1="beatle", clue2="aqua", clue3="pompom", suspect="milo", seed=2),
    StoryParams(place="library_corner", clue1="pompom", clue2="beatle", clue3="aqua", suspect="ivy", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, s in asp_valid_combos():
            print(p, s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
