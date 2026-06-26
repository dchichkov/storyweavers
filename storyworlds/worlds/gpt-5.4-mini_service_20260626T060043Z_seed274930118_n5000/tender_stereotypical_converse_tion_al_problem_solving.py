#!/usr/bin/env python3
"""
A small bedtime storyworld about a tender, conversational, stereotypical little
problem that gets solved gently.

The seed tale idea:
- It is bedtime.
- A child feels worried because a favorite item is missing or a routine is off.
- A parent or caregiver speaks tenderly, asks questions, and helps solve the
  problem by searching, rearranging, or making a tiny practical fix.
- The ending shows the child calm in bed, with the problem solved.

This world keeps the story grounded in state:
- entities have meters (physical state) and memes (feelings / social state)
- the plot turns on a solvable bedtime problem
- the narration is authored and child-facing, not a frozen template swap
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


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
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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


@dataclass
class Room:
    name: str
    quiet: bool = True
    dark: bool = False
    cozy: bool = True
    affordances: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    verb: str
    reason: str
    fix_verb: str
    fix_label: str
    help_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    tender_words: list[str] = field(default_factory=list)
    can_fix: set[str] = field(default_factory=set)
    gives: str = ""


@dataclass
class World:
    room: Room
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.room)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


ROOMS = {
    "bedroom": Room(name="the bedroom", quiet=True, dark=True, cozy=True, affordances={"search", "talk", "sleep"}),
    "nursery": Room(name="the nursery", quiet=True, dark=True, cozy=True, affordances={"search", "talk", "sleep"}),
    "cabin": Room(name="the little cabin room", quiet=True, dark=True, cozy=True, affordances={"search", "talk", "sleep"}),
}

PROBLEMS = {
    "stuffie": Problem(
        id="stuffie",
        label="stuffed bunny",
        verb="find the stuffed bunny",
        reason="it was missing from the pillow",
        fix_verb="look under the bed",
        fix_label="look under the bed",
        help_word="search",
        tags={"toy", "bedtime"},
    ),
    "blanket": Problem(
        id="blanket",
        label="blanket",
        verb="find the blanket",
        reason="it had slipped to the floor",
        fix_verb="pick up the blanket",
        fix_label="pick up the blanket",
        help_word="lift",
        tags={"blanket", "bedtime"},
    ),
    "nightlight": Problem(
        id="nightlight",
        label="nightlight",
        verb="turn the nightlight back on",
        reason="the room felt too shadowy",
        fix_verb="press the switch",
        fix_label="press the switch",
        help_word="switch",
        tags={"light", "bedtime"},
    ),
    "cup": Problem(
        id="cup",
        label="water cup",
        verb="reach the water cup",
        reason="it was too far from the bed",
        fix_verb="move the cup closer",
        fix_label="move the cup closer",
        help_word="move",
        tags={"water", "bedtime"},
    ),
}

HELPERS = [
    Helper(
        id="mother",
        label="mother",
        tender_words=["honey", "sweetheart", "little one"],
        can_fix={"stuffie", "blanket", "nightlight", "cup"},
        gives="a soft smile and a calm hand",
    ),
    Helper(
        id="father",
        label="father",
        tender_words=["buddy", "dear one", "little one"],
        can_fix={"stuffie", "blanket", "nightlight", "cup"},
        gives="a steady voice and a warm hug",
    ),
]

NAMES = ["Mia", "Leo", "Nora", "Eli", "Luna", "Finn", "Ivy", "Ben"]
TRAITS = ["sleepy", "curious", "gentle", "small", "brave", "quiet"]


@dataclass
class StoryParams:
    room: str
    problem: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
room(Room) :- room_name(Room).
problem(Prob) :- problem_name(Prob).
helper(Help) :- helper_name(Help).

solvable(Room, Prob, Help) :- afford(Room, search), room(Room), problem(Prob), helper(Help), can_fix(Help, Prob).
valid_story(Room, Prob, Help, Gender) :- solvable(Room, Prob, Help), fits_gender(Prob, Gender).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room_name", rid))
        if room.quiet:
            lines.append(asp.fact("quiet", rid))
        if room.dark:
            lines.append(asp.fact("dark", rid))
        if room.cozy:
            lines.append(asp.fact("cozy", rid))
        for a in sorted(room.affordances):
            lines.append(asp.fact("afford", rid, a))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem_name", pid))
        lines.append(asp.fact("problem_label", pid, prob.label))
        lines.append(asp.fact("fits_gender", pid, "girl"))
        lines.append(asp.fact("fits_gender", pid, "boy"))
    for h in HELPERS:
        lines.append(asp.fact("helper_name", h.id))
        for p in sorted(h.can_fix):
            lines.append(asp.fact("can_fix", h.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/3."))
    return sorted(set(asp.atoms(model, "solvable")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for r in ROOMS:
        for p in PROBLEMS:
            for h in HELPERS:
                if p in next(x for x in HELPERS if x.id == h).can_fix:
                    out.append((r, p, h))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: tender problem solving.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=[h.id for h in HELPERS])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.problem and args.helper:
        helper = next(h for h in HELPERS if h.id == args.helper)
        if args.problem not in helper.can_fix:
            raise StoryError("That helper cannot solve that bedtime problem.")
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.problem is None or c[1] == args.problem)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid bedtime story matches those choices.)")
    room, problem, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(room=room, problem=problem, name=name, gender=gender, helper=helper, trait=trait)


def _pronoun(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def _narrate(world: World, params: StoryParams) -> None:
    child = world.get("child")
    helper = world.get("helper")
    item = world.get("problem")
    room = world.room
    prob = world.facts["problem_obj"]

    world.say(f"{child.id} was a {params.trait} little {params.gender} in {room.name}, where the air was soft and still.")
    world.say(f"{_pronoun(params.gender).capitalize()} had a tender bedtime feeling and liked when the room was quiet.")
    world.say(f"Tonight, though, something felt a little off: {prob.label} was missing, and bedtime did not feel ready.")

    world.para()
    world.say(f"{child.id} looked at the pillow and then at {helper.label}.")
    world.say(f"{helper.label.capitalize()} spoke in a calm, conversational way and asked, \"Where did you last see it, sweetheart?\"")
    child.memes["worry"] += 1
    child.memes["hope"] += 1
    world.say(f"{child.id} thought for a moment and pointed toward the bed.")

    if prob.id == "stuffie":
        child.meters["search"] += 1
        world.say(f"They knelt down together and gently looked under the bed.")
        item.meters["hidden"] = 0
        item.meters["found"] = 1
        world.say(f"There was the stuffed bunny, tucked beside a sleepy sock, as if it had been taking a tiny nap too.")
    elif prob.id == "blanket":
        child.meters["search"] += 1
        world.say(f"{helper.label.capitalize()} lifted the blanket with one soft hand.")
        item.hidden_in = None
        world.say(f"The blanket had slid to the floor, all bundled up like a cloud.")
    elif prob.id == "nightlight":
        child.meters["search"] += 1
        world.say(f"{helper.label.capitalize()} followed the little trail of shadow and pressed the switch.")
        item.meters["lit"] = 1
        world.say(f"The nightlight glowed again, and the room looked friendly instead of fussy.")
    elif prob.id == "cup":
        child.meters["search"] += 1
        world.say(f"{helper.label.capitalize()} reached quietly and moved the water cup closer to the pillow.")
        item.meters["near"] = 1
        world.say(f"Now the cup sat right where sleepy hands could find it.")

    world.para()
    world.say(f"{helper.label.capitalize()} smiled and said, \"That was a good problem to solve together.\"")
    child.memes["calm"] += 1
    child.memes["joy"] += 1
    world.say(f"{child.id} snuggled down, and the room felt cozy again.")
    world.say(f"At last, bedtime was tender and easy, and {child.id} could close {_pronoun(params.gender, 'possessive')} eyes without a worry.")

    world.facts.update(child=child, helper=helper, problem_obj=item, params=params)


def generate(params: StoryParams) -> StorySample:
    room = ROOMS[params.room]
    world = World(room)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    prob = PROBLEMS[params.problem]
    item = world.add(Entity(id="problem", type=prob.id, label=prob.label, phrase=prob.label))
    item.meters["hidden"] = 1
    item.hidden_in = "under the bed" if prob.id == "stuffie" else None

    world.facts["problem_obj"] = item
    _narrate(world, params)

    prompts = [
        f"Write a gentle bedtime story about {params.name} and a small problem that gets solved with calm conversation.",
        f"Tell a child-facing story where a {params.trait} {params.gender} named {params.name} and a {params.helper} work together at bedtime.",
        f"Write a tender, stereotypical bedtime story with a simple problem-solving turn in the bedroom.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem did {params.name} have at bedtime?",
            answer=f"{params.name} had a little bedtime problem: the {prob.label} was missing or not ready, so bedtime felt unsettled.",
        ),
        QAItem(
            question=f"How did the {params.helper} help {params.name}?",
            answer=f"The {params.helper} helped by speaking calmly, asking a gentle question, and solving the problem together with {params.name}.",
        ),
        QAItem(
            question=f"How did {params.name} feel after the problem was solved?",
            answer=f"{params.name} felt calm, happy, and ready for sleep once the problem was fixed.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a tender way to help someone who feels worried?",
            answer="A tender way is to speak softly, listen carefully, and help with a small problem instead of rushing or scolding.",
        ),
        QAItem(
            question="Why do bedtime rooms often feel cozy?",
            answer="Bedtime rooms often feel cozy because they are quiet, warm, and made for rest.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a change or action that makes the trouble stop.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(room="bedroom", problem="stuffie", name="Mia", gender="girl", helper="mother", trait="sleepy"),
    StoryParams(room="nursery", problem="blanket", name="Leo", gender="boy", helper="father", trait="gentle"),
    StoryParams(room="cabin", problem="nightlight", name="Nora", gender="girl", helper="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} solvable combinations ({len(stories)} gendered stories):\n")
        for room, prob, helper in triples:
            genders = sorted({g for (r, p, h, g) in stories if (r, p, h) == (room, prob, helper)})
            print(f"  {room:9} {prob:10} {helper:8} [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
