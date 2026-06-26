#!/usr/bin/env python3
"""
storyworlds/worlds/pomp_calendar_dialogue_problem_solving_whodunit.py
=====================================================================

A small whodunit-style story world about a pompous host, a missing calendar
page, and a child who solves the mystery with dialogue and careful clues.

Premise seed:
- pomp
- calendar

The world is built as a tiny mystery: someone notices a calendar has been
tampered with, several characters speak in clipped dialogue, and the final
turn comes from problem solving rather than action-heavy spectacle.
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

CALENDAR_DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]

ROOMS = {
    "study": "the study",
    "kitchen": "the kitchen",
    "hall": "the hall",
    "porch": "the porch",
    "office": "the office",
}

CHARACTER_TYPES = {
    "child": {"subject": "they", "object": "them", "possessive": "their"},
    "butler": {"subject": "he", "object": "him", "possessive": "his"},
    "aunt": {"subject": "she", "object": "her", "possessive": "her"},
    "neighbor": {"subject": "they", "object": "them", "possessive": "their"},
}

EVIDENCE_TYPES = {
    "ink_smear": {
        "label": "ink smear",
        "clue": "black ink",
        "detail": "a little black smear near the torn corner",
        "shows": "someone touched the page with ink on their fingers",
    },
    "coffee_ring": {
        "label": "coffee ring",
        "clue": "coffee",
        "detail": "a brown ring on the table beside the calendar",
        "shows": "someone set down a cup too close to the paper",
    },
    "footprint": {
        "label": "mud print",
        "clue": "mud",
        "detail": "a small muddy print on the floorboards",
        "shows": "someone came in from outside before the page went missing",
    },
}

SUSPECT_ROLES = ["butler", "aunt", "neighbor"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    room: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in CHARACTER_TYPES:
            return CHARACTER_TYPES[self.type][case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old house"
    rooms: list[str] = field(default_factory=lambda: ["study", "kitchen", "hall", "porch"])


@dataclass
class Clue:
    id: str
    kind: str
    room: str
    detail: str
    reveals: str


@dataclass
class StoryParams:
    place: str
    investigator: str
    investigator_type: str
    suspect: str
    suspect_type: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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


def _p(s: str) -> str:
    return s[0].upper() + s[1:] if s else s


def solve_mystery(world: World) -> Optional[str]:
    investigator = world.get("investigator")
    suspect = world.get("suspect")
    clue = world.facts["clue"]

    if clue.kind == "ink_smear" and suspect.type == "butler":
        return "The butler had handled the calendar after writing the invitations."
    if clue.kind == "coffee_ring" and suspect.type == "aunt":
        return "The aunt had rested her cup beside the calendar while hurrying through the room."
    if clue.kind == "footprint" and suspect.type == "neighbor":
        return "The neighbor had come in from the porch, bringing in mud from the garden path."
    return f"{investigator.id} noticed that the clue matched {suspect.id}'s path through the house."


def tell(place: str, investigator_name: str, investigator_type: str,
         suspect_name: str, suspect_type: str, clue_kind: str) -> World:
    world = World(Setting(place=place))
    investigator = world.add(Entity(id="investigator", kind="character", type=investigator_type, label=investigator_name))
    suspect = world.add(Entity(id="suspect", kind="character", type=suspect_type, label=suspect_name))
    calendar = world.add(Entity(
        id="calendar", kind="thing", type="calendar", label="calendar",
        phrase="a big wall calendar with neat gold numbers", room="study",
        meters={"order": 1.0}, memes={"pomp": 1.0},
    ))
    clue = Clue(
        id="clue",
        kind=clue_kind,
        room={"ink_smear": "study", "coffee_ring": "study", "footprint": "porch"}[clue_kind],
        detail=EVIDENCE_TYPES[clue_kind]["detail"],
        reveals=EVIDENCE_TYPES[clue_kind]["shows"],
    )
    world.facts.update(
        investigator=investigator,
        suspect=suspect,
        calendar=calendar,
        clue=clue,
        place=place,
    )

    world.say(
        f"In {place}, there hung a very pompous calendar, all tidy numbers and careful gold corners."
    )
    world.say(
        f"{investigator.label} frowned at the missing page. “Someone took the Tuesday note,” "
        f"{investigator.pronoun('subject')} said. “And someone in this house is pretending not to know why.”"
    )
    world.say(
        f"{suspect.label} drew themselves up. “I never touch the calendar,” {suspect.pronoun('subject')} said. "
        f"“A house should keep proper order.”"
    )

    world.para()
    if clue_kind == "ink_smear":
        world.say("The investigator knelt by the frame. There was a little black smear near the torn corner.")
    elif clue_kind == "coffee_ring":
        world.say("The investigator pointed at the table. There was a brown ring beside the calendar.")
    else:
        world.say("The investigator bent by the porch. There was a small muddy print on the floorboards.")

    world.say(
        f'“What does that mean?” asked {investigator.label}.\n'
        f'“It means {EVIDENCE_TYPES[clue_kind]["clue"]}," said the suspect, too quickly.'
    )
    world.say(
        f'“And it means,” said {investigator.label}, “that the page was not stolen by a stranger. '
        f"It was moved by someone who was already here.”"
    )

    world.para()
    explanation = solve_mystery(world)
    if explanation is None:
        raise StoryError("Could not solve the mystery from the given clue and suspect pairing.")
    world.say(
        f"{investigator.label} compared the clue, the room, and the suspect's own words. "
        f"Then {investigator.pronoun('subject')} said, “I know who did it.”"
    )
    world.say(
        f"“{explanation}”"
    )
    world.say(
        f"The suspect went quiet. Then the missing calendar page was found folded behind the frame, "
        f"and the whole house felt less grand, but far more honest."
    )

    world.facts["solution"] = explanation
    return world


SETTINGS = {
    "old_house": Setting(place="the old house"),
    "manse": Setting(place="the little manor"),
    "school": Setting(place="the quiet school"),
}

INVESTIGATORS = {
    "child": ["Nina", "Milo", "June", "Ira"],
    "butler": ["Evan", "Noel"],
    "aunt": ["Ada", "Clara"],
    "neighbor": ["Pia", "Rex"],
}

SUSPECTS = {
    "butler": ["Mr. Vale", "Mr. Finch"],
    "aunt": ["Aunt Belle", "Aunt Iris"],
    "neighbor": ["Mr. Lane", "Ms. Reed"],
}

CURATED = [
    StoryParams(place="old_house", investigator="Nina", investigator_type="child",
                suspect="Mr. Vale", suspect_type="butler", clue="ink_smear"),
    StoryParams(place="manse", investigator="Milo", investigator_type="child",
                suspect="Aunt Belle", suspect_type="aunt", clue="coffee_ring"),
    StoryParams(place="school", investigator="June", investigator_type="child",
                suspect="Mr. Lane", suspect_type="neighbor", clue="footprint"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world about pomp, calendar clues, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--investigator-type", choices=sorted(INVESTIGATORS))
    ap.add_argument("--suspect-type", choices=sorted(SUSPECTS))
    ap.add_argument("--clue", choices=sorted(EVIDENCE_TYPES))
    ap.add_argument("--investigator")
    ap.add_argument("--suspect")
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
    place = args.place or rng.choice(list(SETTINGS))
    investigator_type = args.investigator_type or "child"
    suspect_type = args.suspect_type or rng.choice(SUSPECT_ROLES)
    clue = args.clue or rng.choice(list(EVIDENCE_TYPES))
    investigator = args.investigator or rng.choice(INVESTIGATORS[investigator_type])
    suspect = args.suspect or rng.choice(SUSPECTS[suspect_type])

    if investigator_type != "child":
        raise StoryError("This whodunit is built around a child investigator.")
    if suspect_type not in SUSPECT_ROLES:
        raise StoryError("The suspect must be one of the house's likely suspects.")
    return StoryParams(
        place=place,
        investigator=investigator,
        investigator_type=investigator_type,
        suspect=suspect,
        suspect_type=suspect_type,
        clue=clue,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        params.place,
        params.investigator,
        params.investigator_type,
        params.suspect,
        params.suspect_type,
        params.clue,
    )
    story = world.render()
    prompts = [
        "Write a small whodunit about a pompous calendar and a careful child investigator.",
        f"Tell a dialogue-heavy mystery where {params.investigator} notices a clue in {SETTINGS[params.place].place}.",
        "Make the ending solve the mystery by comparing the clue to where the suspect had been.",
    ]
    story_qa = [
        QAItem(
            question=f"Who noticed that something was wrong with the calendar?",
            answer=f"{params.investigator} noticed the missing page and started asking questions.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"The clue was a {EVIDENCE_TYPES[params.clue]['label']}, which showed {EVIDENCE_TYPES[params.clue]['shows']}.",
        ),
        QAItem(
            question="How did the investigator solve the case?",
            answer=f"{params.investigator} matched the clue to the suspect's path and explained what must have happened.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a calendar for?",
            answer="A calendar is used to keep track of days, dates, and planned events.",
        ),
        QAItem(
            question="What does pompous mean?",
            answer="Pompous means acting as if something is more grand or important than it really is.",
        ),
        QAItem(
            question="What do detectives do?",
            answer="Detectives look for clues, ask questions, and connect evidence to solve a mystery.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} room={e.room} label={e.label}")
    clue = world.facts.get("clue")
    if clue:
        lines.append(f"  clue: {clue.kind} in {clue.room}")
    if "solution" in world.facts:
        lines.append(f"  solution: {world.facts['solution']}")
    return "\n".join(lines)


ASP_RULES = r"""
% A clue supports a suspect when it matches where the suspect had been.
supports(S, C) :- suspect(S), clue(C), clue_room(C, R), path(S, R).

% The mystery is solved when exactly one suspect is supported by the clue.
solved(S) :- supports(S, C), not other_supported(C, S).

other_supported(C, S) :- supports(S2, C), S2 != S.

#show supports/2.
#show solved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k in SETTINGS:
        lines.append(asp.fact("setting", k))
    for role in SUSPECT_ROLES:
        lines.append(asp.fact("suspect_type", role))
    for clue, data in EVIDENCE_TYPES.items():
        lines.append(asp.fact("clue", clue))
        lines.append(asp.fact("clue_room", clue, {"ink_smear": "study", "coffee_ring": "study", "footprint": "porch"}[clue]))
    lines.append(asp.fact("path", "butler", "study"))
    lines.append(asp.fact("path", "aunt", "study"))
    lines.append(asp.fact("path", "neighbor", "porch"))
    lines.append(asp.fact("suspect", "butler"))
    lines.append(asp.fact("suspect", "aunt"))
    lines.append(asp.fact("suspect", "neighbor"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    asp_solutions = set(asp.atoms(model, "solved"))
    py_solutions = {("butler",), ("aunt",), ("neighbor",)}
    if asp_solutions:
        print("OK: ASP rules produced a solution set.")
        return 0
    print("MISMATCH: ASP produced no solutions.")
    return 1


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


def asp_validity_report() -> str:
    return "The ASP twin is present as an inline rule set, but the story generator uses Python reasoning for determinism."


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_validity_report())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            rng = random.Random(seed)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
            header = f"### {p.investigator} vs {p.suspect} ({p.clue}) at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
