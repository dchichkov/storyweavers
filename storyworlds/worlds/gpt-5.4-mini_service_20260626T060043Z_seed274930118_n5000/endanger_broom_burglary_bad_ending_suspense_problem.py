#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/endanger_broom_burglary_bad_ending_suspense_problem.py
================================================================================

A small ghost-story world about a broom, a burglary, and a child trying to solve
a scary problem before night gets too deep.

Premise:
- A child lives in an old house where a broom is important for keeping the
  floor clean and for chasing cobwebs into a pile.
- A burglary threat enters the story as a quiet, shadowy danger.
- The child and a ghostly helper notice clues in the dark.

Tension:
- The broom is endangered because the burglar wants to take useful things.
- The child must use observation, courage, and problem solving to protect the
  house.
- Suspense comes from sounds, missing objects, and uncertain shadows.

Turn:
- The child follows clues, tries to block the burglar, and uses the broom as a
  practical tool rather than a weapon.
- A ghostly hint reveals where the burglar went.

Resolution:
- The ending is a bad ending: the burglar escapes with the broom, leaving the
  house uneasy and the floor still dusty.
- Still, the child learns how to watch for clues and locks the door before the
  night grows worse.

The prose is intentionally authored from world state: meter changes, clue
accumulation, fear, and the failed protection of the broom shape the narration.
"""

from __future__ import annotations

import argparse
import copy
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
    carried_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str = "the old house"
    dark: bool = True


@dataclass
class StoryParams:
    place: str = "house"
    child_name: str = "Maya"
    child_type: str = "girl"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(copy.deepcopy(self.place))
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _entropy(world: World) -> float:
    return sum(e.meters.get("fear", 0.0) + e.meters.get("clue", 0.0) for e in world.entities.values())


def _r_whisper(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    child = world.entities.get("child")
    if not ghost or not child:
        return out
    if child.meters.get("fear", 0.0) < THRESHOLD:
        return out
    sig = ("whisper",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["warning"] = ghost.memes.get("warning", 0.0) + 1
    child.meters["clue"] = child.meters.get("clue", 0.0) + 1
    out.append("A pale whisper slipped through the hall, and the child noticed one more clue.")
    return out


def _r_burgle(world: World) -> list[str]:
    out: list[str] = []
    burglar = world.entities.get("burglar")
    broom = world.entities.get("broom")
    if not burglar or not broom:
        return out
    if burglar.memes.get("resolved", 0.0) >= THRESHOLD:
        return out
    if world.facts.get("door_locked"):
        return out
    if broom.carried_by == burglar.id:
        return out
    sig = ("take_broom",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    broom.carried_by = burglar.id
    broom.hidden = True
    burglar.memes["victory"] = burglar.memes.get("victory", 0.0) + 1
    out.append("In the dark, the burglar snatched the broom and vanished with it.")
    return out


def _r_bad_ending(world: World) -> list[str]:
    if not world.facts.get("door_locked"):
        return []
    if world.facts.get("broom_saved"):
        return []
    sig = ("bad_end",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["bad_ending"] = True
    return ["__bad_ending__"]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_whisper, _r_burgle, _r_bad_ending):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__bad_ending__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    world = World(Place(name="the old house", dark=True))
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the pale ghost"))
    burglar = world.add(Entity(id="burglar", kind="character", type="burglar", label="the burglar"))
    broom = world.add(Entity(id="broom", type="broom", label="broom", phrase="an old wooden broom"))
    child.meters["fear"] = 0.0
    child.meters["clue"] = 0.0
    ghost.meters["fade"] = 0.0
    burglar.meters["sneak"] = 1.0
    broom.meters["clean"] = 1.0
    world.facts["broom_saved"] = False
    return world


def tell(world: World, params: StoryParams) -> World:
    child = world.get("child")
    ghost = world.get("ghost")
    burglar = world.get("burglar")
    broom = world.get("broom")

    world.say(
        f"{child.label} lived in {world.place.name}, where the hallway creaked like a throat in the dark. "
        f"The old broom stood by the door, because it helped keep the floor clear and the cobwebs small."
    )
    world.say(
        f"One night, {child.label} heard a soft bump from the kitchen. "
        f"Then came another sound, as quiet as a shoe on dry wood."
    )
    child.meters["fear"] += 1
    propagate(world)

    world.para()
    world.say(
        f"{child.label} held very still and listened. "
        f"Near the stairs, a pale shape floated once and then again, as if the house itself were trying to whisper."
    )
    ghost.meters["warning"] = ghost.meters.get("warning", 0.0) + 1
    world.say(
        f"{ghost.label} did not speak in a loud voice. Instead, it pointed toward the front hall, where the moonlight showed a dusty trail."
    )
    child.meters["clue"] += 1
    child.meters["fear"] += 1

    world.para()
    world.say(
        f"{child.label} found a small open drawer and a missing hook on the wall. "
        f"That meant someone had already been inside, and the thought made the room feel colder."
    )
    world.say(
        f"{child.label} grabbed the broom to sweep the dusty trail, hoping the marks would lead to the intruder before the intruder found anything else."
    )
    world.facts["tried_problem_solving"] = True
    propagate(world)

    world.para()
    world.say(
        f"The trail led past the sink, around the rug, and to the front door. "
        f"Behind it all, a shadow moved too fast for a child to catch."
    )
    if not world.facts.get("door_locked"):
        world.say(
            f"{child.label} reached for the latch, but the door shivered open at the same moment. "
            f"The burglar slipped through the crack like smoke."
        )
    world.say(
        f"At the last second, the burglar spotted the broom and took it too, as if a clean floor were something worth stealing."
    )
    broom.carried_by = burglar.id
    broom.hidden = True
    child.meters["fear"] += 1
    burglar.meters["sneak"] += 1
    propagate(world)

    world.para()
    world.facts["door_locked"] = True
    world.say(
        f"By the time {child.label} slammed the door shut, the hallway was quiet again. "
        f"The burglar was gone, and the broom was gone with them."
    )
    world.say(
        f"{ghost.label} hovered by the dark window, looking smaller and sadder than before. "
        f"{child.label} locked the latch with shaking hands and stared at the dusty floor that was still waiting to be cleaned."
    )
    world.facts["broom_saved"] = False
    world.facts["bad_ending"] = True
    world.say(
        f"It was a bad ending for the broom and a bad night for {child.label}, but it taught one hard lesson: the house needed a better lock before the next whisper came."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a ghost story for a young child about a broom being endangered during a burglary.",
        "Tell a suspenseful story in an old house where a child uses problem solving to track a burglar, but the ending is a bad one.",
        "Write a short spooky tale with a broom, a ghost, and a thief, ending with a clear image of what changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.get("child")
    ghost = world.get("ghost")
    burglar = world.get("burglar")
    broom = world.get("broom")
    return [
        QAItem(
            question=f"Why did {child.label} feel scared in the old house?",
            answer="The child felt scared because the hallway was dark, there were strange noises, and someone might have been inside the house.",
        ),
        QAItem(
            question="What clue helped the child start solving the problem?",
            answer="A dusty trail and an open drawer helped the child realize that someone had already been in the house.",
        ),
        QAItem(
            question="What did the ghost do in the story?",
            answer="The ghost floated quietly, pointed toward the front hall, and helped the child notice the clues.",
        ),
        QAItem(
            question="What happened to the broom at the end?",
            answer="The burglar took the broom, so the house ended with the broom missing and the floor still dusty.",
        ),
        QAItem(
            question="Was the ending happy or bad?",
            answer="It was a bad ending because the burglar escaped and the broom was not recovered.",
        ),
        QAItem(
            question="What did the child do to try to fix the problem?",
            answer="The child followed the dusty trail, listened carefully, and used the broom to help trace where the intruder had gone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a broom for?",
            answer="A broom is used to sweep dust and dirt into a pile so the floor can be cleaned.",
        ),
        QAItem(
            question="What is a burglary?",
            answer="A burglary is when someone goes into a place without permission to take things that do not belong to them.",
        ),
        QAItem(
            question="Why can old houses feel spooky at night?",
            answer="Old houses can feel spooky at night because they creak, cast shadows, and make little sounds that are easy to imagine as ghosts.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "house":
        raise StoryError("This storyworld only supports the old house setting.")
    if params.child_type not in {"girl", "boy"}:
        raise StoryError("The child must be a boy or girl.")
    if not params.child_name:
        raise StoryError("The child needs a name.")


ASP_RULES = r"""
% A broom is endangered when a burglar is present and the door is not locked.
endangered(broom) :- burglar_present, not door_locked.

% The suspense comes from clues that accumulate after fear rises.
suspense :- fear(child), clue(child).

% Problem solving happens when the child follows a trail or uses the broom.
problem_solving :- followed_trail, used_broom.

% A bad ending occurs when the burglar escapes with the broom.
bad_ending :- endangered(broom), burglar_took(broom).

#show endangered/1.
#show suspense/0.
#show problem_solving/0.
#show bad_ending/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("burglar_present"),
        asp.fact("fear", "child"),
        asp.fact("clue", "child"),
        asp.fact("followed_trail"),
        asp.fact("used_broom"),
        asp.fact("burglar_took", "broom"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {sym.name for sym in model}
    wanted = {"endangered", "suspense", "problem_solving", "bad_ending"}
    if names == wanted:
        print("OK: ASP twin matches the Python world model.")
        return 0
    print("MISMATCH between ASP and Python reasoning:")
    print("  asp:", sorted(names))
    print("  py :", sorted(wanted))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A spooky storyworld about a broom, a burglary, and a bad ending.")
    ap.add_argument("--place", choices=["house"], default="house")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.place != "house":
        raise StoryError("Only the house setting is available.")
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(["Maya", "Noah", "Iris", "Finn", "Ella", "Theo"])
    return StoryParams(place=args.place, child_name=child_name, child_type=child_type)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell(world, params)
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


def asp_show_program() -> str:
    return asp_program()


def asp_story_check() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {sym.name for sym in model}
    return 0 if {"endangered", "suspense", "problem_solving", "bad_ending"} <= names else 1


CURATED = [
    StoryParams(place="house", child_name="Maya", child_type="girl"),
    StoryParams(place="house", child_name="Noah", child_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    elif args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:", " ".join(sorted(f"{sym.name}/{len(sym.arguments)}" for sym in model)))
        return
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
