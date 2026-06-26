#!/usr/bin/env python3
"""
storyworlds/worlds/doohicky_binkie_bad_ending_curiosity_whodunit.py
====================================================================

A small whodunit-style story world about a curious child, a missing binkie,
and a doohicky that does not survive the investigation.

Premise:
- A child notices their binkie is missing.
- A strange little doohicky in the room seems to matter.
- Curiosity pushes the child to investigate clues and suspects.
- The answer is found, but the ending is bad: the doohicky is broken or lost,
  and the child learns that poking at everything can make trouble.

The story is intentionally constrained and state-driven:
- characters have emotional memes and physical meters
- clues are generated from a simulated mystery
- the ending depends on the world state, not on a frozen template
- explicit invalid choices raise StoryError

This script supports the standard storyworld interface plus ASP parity checks.
"""

from __future__ import annotations

import argparse
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    broken: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Room:
    id: str
    label: str
    clue_style: str
    exits: list[str] = field(default_factory=list)


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    alibi: str
    hiding_place: str
    can_break: bool = False


@dataclass
class Setting:
    place: str = "the bedroom"
    mood: str = "quiet"
    rooms: dict[str, Room] = field(default_factory=dict)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.rooms_seen: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.rooms_seen = set(self.rooms_seen)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    room: str
    suspect: str
    seed: Optional[int] = None


ROOMS = {
    "bedroom": Room("bedroom", "the bedroom", "soft"),
    "hall": Room("hall", "the hallway", "echoing"),
    "kitchen": Room("kitchen", "the kitchen", "crumbly"),
    "laundry": Room("laundry", "the laundry room", "humming"),
}

SUSPECTS = {
    "cat": Suspect("cat", "the cat", "animal", "I was only napping", "under the chair"),
    "dog": Suspect("dog", "the dog", "animal", "I only sniffed the socks", "behind the basket"),
    "parent": Suspect("parent", "the parent", "person", "I was folding towels", "near the sink"),
}

NAMES = ["Milo", "Nora", "Lena", "Ari", "June", "Theo", "Mina", "Pip"]
GENDERS = {"girl", "boy"}
TRAITS = ["curious", "quiet", "careful", "brave", "determined"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A curious whodunit with a bad ending.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--room", choices=ROOMS)
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
    room = args.room or rng.choice(list(ROOMS))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent, room=room, suspect=suspect)


def valid_combos() -> list[tuple[str, str]]:
    return [(r, s) for r in ROOMS for s in SUSPECTS]


def explain_rejection(_: str, __: str) -> str:
    return "(No story: this whodunit needs a room and a suspect.)"


def _intro(world: World, child: Entity, parent: Entity, suspect: Suspect, doohicky: Entity, binkie: Entity) -> None:
    world.say(
        f"{child.id} was a {child.memes['trait_word']} little {child.type} who loved asking questions."
    )
    world.say(
        f"One quiet day in {world.setting.place}, {child.id} noticed {child.pronoun('possessive')} "
        f"{binkie.label} was missing, and a small {doohicky.label} sat nearby like it knew something."
    )
    world.say(
        f"{parent.label} said, \"Let's look carefully,\" but {child.id}'s curiosity sparkled brighter than the lamp."
    )
    world.facts["suspect_hint"] = suspect.label
    world.facts["room_label"] = world.setting.place


def _search_room(world: World, child: Entity, room: Room, suspect: Suspect, binkie: Entity) -> None:
    child.memes["curiosity"] += 1
    world.rooms_seen.add(room.id)
    if room.id == suspect.hiding_place:
        world.say(
            f"In {room.label}, {child.id} found a clue: a tiny mark near {suspect.label}'s hiding place, "
            f"and {suspect.label} looked a little too still."
        )
    else:
        world.say(
            f"{child.id} searched {room.label}, listening to the {room.clue_style} hush, but found only a bent spoon and dust."
        )
    if room.id == "kitchen":
        binkie.found = True
        binkie.carried_by = child.id
        world.say(f"Behind a basket in {room.label}, {child.id} finally spotted {binkie.label} and held {binkie.label} tight.")


def _question_suspect(world: World, child: Entity, suspect: Suspect) -> None:
    child.memes["suspicion"] += 1
    world.say(f"{child.id} looked at {suspect.label} and asked, \"Were you the one who moved it?\"")
    world.say(f"{suspect.label} answered, \"{suspect.alibi}.\"")
    world.facts["asked"] = suspect.id


def _doohicky_breaks(world: World, child: Entity, doohicky: Entity, suspect: Suspect) -> None:
    # The bad ending: curiosity causes the child to poke at the doohicky too hard.
    if child.memes["curiosity"] >= THRESHOLD:
        doohicky.broken = True
        doohicky.meters["damage"] = 1.0
        world.say(
            f"Curious as ever, {child.id} turned the little {doohicky.label} over and pressed the shiny tab."
        )
        world.say(
            f"It clicked once, then snapped. The {doohicky.label} cracked in two pieces on the floor."
        )
        if suspect.can_break:
            world.say(
                f"The noise startled {suspect.label}, but by then the real answer was already plain: "
                f"{suspect.label} had only hidden the {binkie_name(world)}, not broken the {doohicky.label}."
            )


def binkie_name(world: World) -> str:
    return world.facts["binkie"].label


def _ending(world: World, child: Entity, parent: Entity, binkie: Entity, doohicky: Entity, suspect: Suspect) -> None:
    if binkie.found and doohicky.broken:
        world.say(
            f"{parent.label} picked up the binkie and set the broken {doohicky.label} aside."
        )
        world.say(
            f"{child.id} got {binkie.label} back, but the clever little {doohicky.label} stayed broken, and the room felt much less magical."
        )
        world.say(
            f"That night {child.id} hugged the binkie and promised to ask first next time, while the cracked {doohicky.label} stayed on the shelf."
        )
    elif binkie.found:
        world.say(f"{child.id} found {binkie.label}, but the mystery still felt thorny and unfinished.")
    else:
        world.say(f"The room stayed quiet, and {child.id} never found {binkie.label}.")


def tell(params: StoryParams) -> World:
    setting = Setting(place=ROOMS[params.room].label, rooms=ROOMS)
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender, memes={"curiosity": 0.0, "suspicion": 0.0}))
    child.memes["trait_word"] = 0.0
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))

    suspect = SUSPECTS[params.suspect]
    doohicky = world.add(Entity(id="doohicky", label="doohicky", phrase="a shiny little doohicky"))
    binkie = world.add(Entity(id="binkie", label="binkie", phrase="a soft binkie", owner=child.id))
    world.facts["binkie"] = binkie

    child.memes["trait_word"] = 1.0
    _intro(world, child, parent, suspect, doohicky, binkie)

    world.para()
    order = [params.room] + [r for r in ROOMS if r != params.room]
    for rid in order:
        _search_room(world, child, ROOMS[rid], suspect, binkie)
        if binkie.found:
            break

    world.para()
    _question_suspect(world, child, suspect)
    _doohicky_breaks(world, child, doohicky, suspect)

    world.para()
    _ending(world, child, parent, binkie, doohicky, suspect)

    world.facts.update(child=child, parent=parent, suspect=suspect, doohicky=doohicky, room=params.room)
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    suspect = world.facts["suspect"]
    return [
        f"Write a short whodunit for a child named {child.id} who is curious about a missing binkie and a small doohicky.",
        f"Tell a gentle mystery where {child.id} asks if {suspect.label} moved the binkie, but the ending goes wrong.",
        f"Write a simple detective story that ends with a broken doohicky and a child promising to be less nosy next time.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    suspect = world.facts["suspect"]
    doohicky = world.facts["doohicky"]
    binkie = world.facts["binkie"]
    room = world.facts["room"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child.id}, a curious little {child.type}, and {parent.label} helps look for the missing {binkie.label}."
        ),
        QAItem(
            question=f"What did {child.id} search for in {room}?",
            answer=f"{child.id} searched for {binkie.label}, because it had gone missing in {world.setting.place}."
        ),
        QAItem(
            question=f"What happened to the {doohicky.label}?",
            answer=f"The {doohicky.label} broke when {child.id} pressed it too hard while being curious."
        ),
        QAItem(
            question=f"Who did {child.id} question as a possible culprit?",
            answer=f"{child.id} asked {suspect.label} whether it had moved the missing {binkie.label}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more, so a curious child keeps looking, asking, and exploring."
        ),
        QAItem(
            question="What is a binkie?",
            answer="A binkie is a small soothing toy, often soft, that a child may hold or suck when they want comfort."
        ),
        QAItem(
            question="What does a whodunit story do?",
            answer="A whodunit story gives clues and suspects so the reader can guess who did the important thing."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.broken:
            bits.append("broken=True")
        if e.found:
            bits.append("found=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  rooms_seen={sorted(world.rooms_seen)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Milo", gender="boy", parent="mother", room="bedroom", suspect="cat"),
    StoryParams(name="Nora", gender="girl", parent="father", room="hall", suspect="dog"),
    StoryParams(name="Lena", gender="girl", parent="mother", room="kitchen", suspect="parent"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        lines.append(asp.fact("room_label", rid, room.label))
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("hiding_place", sid, suspect.hiding_place))
    lines.append(asp.fact("object", "binkie"))
    lines.append(asp.fact("object", "doohicky"))
    lines.append(asp.fact("feature", "curiosity"))
    lines.append(asp.fact("feature", "bad_ending"))
    return "\n".join(lines)


ASP_RULES = r"""
room_and_suspect_ok(R,S) :- room(R), suspect(S).
has_mystery(R,S) :- room_and_suspect_ok(R,S).
bad_ending(R,S) :- has_mystery(R,S).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show room_and_suspect_ok/2."))
    return sorted(set(asp.atoms(model, "room_and_suspect_ok")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_combo_filter(args: argparse.Namespace, combo: tuple[str, str]) -> bool:
    room, suspect = combo
    return (args.room is None or args.room == room) and (args.suspect is None or args.suspect == suspect)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos() if valid_combo_filter(args, c)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, suspect = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent, room=room, suspect=suspect)


def valid_combos() -> list[tuple[str, str]]:
    return [(r, s) for r in ROOMS for s in SUSPECTS]


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        return [generate(p) for p in CURATED]
    samples: list[StorySample] = []
    seen: set[str] = set()
    for i in range(max(args.n * 50, 50)):
        if len(samples) >= args.n:
            break
        seed = base_seed + i
        try:
            params = resolve_params(args, random.Random(seed))
        except StoryError as err:
            print(err)
            return []
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show room_and_suspect_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show room_and_suspect_ok/2."))
        combos = sorted(set(asp.atoms(model, "room_and_suspect_ok")))
        print(f"{len(combos)} room/suspect combos:")
        for room, suspect in combos:
            print(f"  {room:10} {suspect}")
        return

    samples = build_samples(args)
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
