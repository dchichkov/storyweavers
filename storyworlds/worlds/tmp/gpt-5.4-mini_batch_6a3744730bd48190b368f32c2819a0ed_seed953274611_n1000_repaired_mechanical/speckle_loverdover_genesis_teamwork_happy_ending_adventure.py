#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/speckle_loverdover_genesis_teamwork_happy_ending_adventure.py
=============================================================================================

A tiny adventure storyworld about two friends, a bright map-mark called
speckle, a friendly place called Loverdover, and the beginning of a quest at
Genesis Hill. The world is built around teamwork and a happy ending: the
characters get stuck, help each other, and finish with a concrete change in the
world state.

The story is intentionally small and classical:
- premise: two children begin an adventure and notice a clue
- tension: one route is blocked by a natural obstacle
- turn: they work together and use a tool / helper / location clue
- resolution: they reach the treasure and end happier and safer than before

This file is standalone and stdlib-only, except for the shared Storyweavers
result containers and the lazy clingo helper used only for ASP modes.
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
BRAVE_INIT = 5.0


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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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


@dataclass
class Place:
    id: str
    label: str
    path: str
    bright_spot: str
    blocked_by: str
    adventure_word: str
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
    label: str
    phrase: str
    reveals: str
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
class HelperTool:
    id: str
    label: str
    phrase: str
    use_line: str
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
class Obstacle:
    id: str
    label: str
    phrase: str
    severity: int
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["stuck"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in (world.entities.get("hero1"), world.entities.get("hero2")):
            if kid:
                kid.memes["worry"] += 1
        out.append("__spoil__")
    return out


RULES = [Rule("spill", _r_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(place: Place, obstacle: Obstacle, helper: HelperTool) -> bool:
    return obstacle.label in place.blocked_by and helper.id in HELPER_BY_OBSTACLE[obstacle.id]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for oid, obs in OBSTACLES.items():
            for hid, helper in HELPERS.items():
                if valid_combo(place, obs, helper):
                    combos.append((pid, oid, hid))
    return combos


@dataclass
class StoryParams:
    place: str = ""
    obstacle: str = ""
    helper: str = ""
    clue: str = ""
    name1: str = ""
    gender1: str = "girl"
    name2: str = ""
    gender2: str = "boy"
    parent: str = "father"
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
    "genesis": Place(
        id="genesis",
        label="Genesis Hill",
        path="the path up Genesis Hill",
        bright_spot="a sparkling sign",
        blocked_by="a fallen log",
        adventure_word="adventure",
        tags={"genesis", "adventure"},
    ),
    "loverdover": Place(
        id="loverdover",
        label="Loverdover Cove",
        path="the sandy trail to Loverdover Cove",
        bright_spot="a bright shell",
        blocked_by="a puddle",
        adventure_word="adventure",
        tags={"loverdover", "adventure"},
    ),
    "speckle": Place(
        id="speckle",
        label="Speckle Grove",
        path="the mossy trail through Speckle Grove",
        bright_spot="a tiny speckle on a stone",
        blocked_by="a tangled vine",
        adventure_word="adventure",
        tags={"speckle", "adventure"},
    ),
}

OBSTACLES = {
    "log": Obstacle("log", "log", "a fallen log", 2, tags={"log"}),
    "puddle": Obstacle("puddle", "puddle", "a wide puddle", 1, tags={"puddle"}),
    "vine": Obstacle("vine", "vine", "a tangled vine", 2, tags={"vine"}),
}

HELPERS = {
    "rope": HelperTool("rope", "rope", "a short rope", "tied the rope around the log and pulled together", tags={"rope", "teamwork"}),
    "bridge_planks": HelperTool("bridge_planks", "planks", "two flat planks", "set the planks down and crossed carefully together", tags={"planks", "teamwork"}),
    "sticks": HelperTool("sticks", "sticks", "a bundle of strong sticks", "made a little bridge and stepped across together", tags={"sticks", "teamwork"}),
}

HELPER_BY_OBSTACLE = {
    "log": {"rope"},
    "puddle": {"bridge_planks", "sticks"},
    "vine": {"sticks"},
}

NAMES_GIRL = ["Lina", "Mira", "Zoe", "Ava", "Nia"]
NAMES_BOY = ["Milo", "Ben", "Theo", "Kai", "Noah"]


def reasonableness_gate(place: Place, obstacle: Obstacle, helper: HelperTool) -> None:
    if not valid_combo(place, obstacle, helper):
        raise StoryError(
            f"(No story: {helper.label} does not honestly solve {obstacle.label} at {place.label}.)"
        )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny adventure storyworld with teamwork and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--clue", choices=["speckle", "loverdover", "genesis"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--gender2", choices=["girl", "boy"])
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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
    combos = valid_combos()
    if args.place or args.obstacle or args.helper:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.obstacle is None or c[1] == args.obstacle)
            and (args.helper is None or c[2] == args.helper)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obstacle, helper = rng.choice(sorted(combos))
    clue = args.clue or rng.choice(["speckle", "loverdover", "genesis"])
    gender1 = args.gender1 or "girl"
    gender2 = args.gender2 or "boy"
    name1 = args.name1 or rng.choice(NAMES_GIRL if gender1 == "girl" else NAMES_BOY)
    name2 = args.name2 or rng.choice([n for n in (NAMES_GIRL if gender2 == "girl" else NAMES_BOY) if n != name1])
    return StoryParams(
        place=place, obstacle=obstacle, helper=helper, clue=clue,
        name1=name1, gender1=gender1, name2=name2, gender2=gender2,
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES or params.obstacle not in OBSTACLES or params.helper not in HELPERS:
        raise StoryError("(Invalid params: unknown place, obstacle, or helper.)")
    place, obstacle, helper = PLACES[params.place], OBSTACLES[params.obstacle], HELPERS[params.helper]
    reasonableness_gate(place, obstacle, helper)

    world = World()
    a = world.add(Entity(id="hero1", kind="character", type=params.gender1, label=params.name1, role="leader"))
    b = world.add(Entity(id="hero2", kind="character", type=params.gender2, label=params.name2, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    speck = world.add(Entity(id="speckle", type="clue", label="speckle"))
    lover = world.add(Entity(id="loverdover", type="clue", label="loverdover"))
    genesis = world.add(Entity(id="genesis", type="place", label="genesis"))

    a.memes["bravery"] = BRAVE_INIT
    b.memes["trust"] = 4.0

    world.say(
        f"At {place.label}, {a.label} and {b.label} began an adventure. "
        f"{place.path} glittered under the morning light, and a {params.clue} clue waited ahead."
    )
    world.say(
        f'"{place.bright_spot}!" {a.label} said. "If we follow the clue, maybe we will find the genesis of the trail."'
    )

    world.para()
    world.say(
        f"But the way ahead stopped at {obstacle.phrase}. {b.label} reached for {a.label}\'s hand. '
        f'We should work together," {b.label} said.'
    )
    a.memes["desire"] += 1
    b.memes["care"] += 1

    world.para()
    world.say(
        f"{a.label} nodded, and {b.label} helped with {helper.phrase}. "
        f"{helper.use_line.capitalize()}."
    )
    world.get("hero1").meters["helped"] += 1
    world.get("hero2").meters["helped"] += 1
    obstacle_ent = world.add(Entity(id="obstacle", type="thing", label=obstacle.label))
    obstacle_ent.meters["stuck"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"Together they crossed the hard spot and kept going to {place.label}. "
        f"There they found a happy surprise: a small chest with a ribbon tied tight."
    )
    world.say(
        f"{parent.label_word.capitalize()} laughed when they returned, proud that the two friends had solved it side by side."
    )
    world.say(
        f"At the end, the {params.clue} clue had led them all the way to {place.label}, "
        f"and the adventure shone like a bright new beginning."
    )

    world.facts.update(
        place=place, obstacle=obstacle, helper=helper, clue=params.clue,
        hero1=a, hero2=b, parent=parent, world_items={"speckle": speck, "loverdover": lover, "genesis": genesis},
        outcome="happy",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly adventure story that includes the words "{f["clue"]}", "loverdover", and "genesis".',
        f"Tell a teamwork adventure where {f['hero1'].label} and {f['hero2'].label} get past an obstacle together and end happily.",
        f'Write a short happy-ending adventure set at {f["place"].label} with a clue that leads to a shared success.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("Who is the story about?",
         f"It is about {f['hero1'].label} and {f['hero2'].label}, who go on an adventure together."),
        ("What problem did they face?",
         f"They found {f['obstacle'].phrase} blocking the way, so they had to solve it as a team."),
        ("How did they solve it?",
         f"They used {f['helper'].phrase} and worked together. That teamwork let them cross safely and keep going."),
        ("How did the story end?",
         f"It ended happily. They reached {f['place'].label} together, and the adventure became a proud, bright memory."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does teamwork mean?",
         "Teamwork means people help each other to do something together. It can make a hard job easier and safer."),
        ("What is a clue?",
         "A clue is a small hint that helps you figure out where to go or what to do next."),
        ("What is a happy ending?",
         "A happy ending is when the problem gets solved and the characters finish safe, proud, or joyful."),
        ("What is an adventure?",
         "An adventure is an exciting trip or story where characters discover new places and solve problems."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if e.memes:
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.label:
            bits.append(f"label={e.label!r}")
        out.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
valid(P,O,H) :- place(P), obstacle(O), helper(H), solves(H,O), fits(P,O).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid, obs in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("solves", "rope", oid)) if oid == "log" else None
        if oid == "puddle":
            lines.append(asp.fact("solves", "bridge_planks", oid))
            lines.append(asp.fact("solves", "sticks", oid))
        if oid == "vine":
            lines.append(asp.fact("solves", "sticks", oid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for pid, place in PLACES.items():
        for oid, obs in OBSTACLES.items():
            if obs.label in place.blocked_by:
                lines.append(asp.fact("fits", pid, oid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, obstacle=None, helper=None, clue=None, parent=None, gender1=None, gender2=None, name1=None, name2=None), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_sample(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
    StoryParams(place="genesis", obstacle="log", helper="rope", clue="speckle", name1="Lina", gender1="girl", name2="Milo", gender2="boy", parent="father"),
    StoryParams(place="loverdover", obstacle="puddle", helper="bridge_planks", clue="loverdover", name1="Mira", gender1="girl", name2="Theo", gender2="boy", parent="mother"),
    StoryParams(place="speckle", obstacle="vine", helper="sticks", clue="genesis", name1="Ava", gender1="girl", name2="Ben", gender2="boy", parent="father"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place or args.obstacle or args.helper:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.obstacle is None or c[1] == args.obstacle)
            and (args.helper is None or c[2] == args.helper)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obstacle, helper = rng.choice(sorted(combos))
    gender1 = args.gender1 or rng.choice(["girl", "boy"])
    gender2 = args.gender2 or ("boy" if gender1 == "girl" else "girl")
    name1 = args.name1 or rng.choice(NAMES_GIRL if gender1 == "girl" else NAMES_BOY)
    name2 = args.name2 or rng.choice(NAMES_BOY if gender2 == "boy" else NAMES_GIRL)
    if name2 == name1:
        name2 = (NAMES_BOY if gender2 == "boy" else NAMES_GIRL)[0]
    return StoryParams(
        place=place, obstacle=obstacle, helper=helper,
        clue=args.clue or rng.choice(["speckle", "loverdover", "genesis"]),
        name1=name1, gender1=gender1, name2=name2, gender2=gender2,
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [build_sample(p) for p in CURATED]
    else:
        seen = set()
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
            sample = build_sample(params)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
