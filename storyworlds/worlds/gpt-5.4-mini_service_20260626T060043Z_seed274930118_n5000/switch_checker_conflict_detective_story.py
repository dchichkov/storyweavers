#!/usr/bin/env python3
"""
storyworlds/worlds/switch_checker_conflict_detective_story.py
=============================================================

A compact detective-style storyworld about a switch, a checker, and a conflict.

Premise:
A careful checker notices that an important switch is in the wrong position.
That causes a small conflict: lights, signs, or sounds stop behaving as they
should, and the detective has to figure out who moved it.

World model:
- Physical meters track the switch position and the state of the place.
- Emotional memes track suspicion, worry, conflict, relief, and pride.
- The story is driven by simulated state, not by a frozen template.

The story is deliberately small and classical:
beginning -> clue -> conflict -> resolution -> closing image.
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
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    dark_when_off: bool = False


@dataclass
class StoryParams:
    place: str
    detector: str
    checker: str
    switch_name: str
    switch_kind: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _label(name: str) -> str:
    return name


def _switch_state(world: World) -> str:
    sw = world.get("switch")
    pos = int(sw.meters.get("position", 0))
    return "on" if pos >= THRESHOLD else "off"


def _room_state(world: World) -> str:
    room = world.get("room")
    return "bright" if room.meters.get("bright", 0) >= THRESHOLD else "dark"


def _apply_switch_state(world: World) -> None:
    sw = world.get("switch")
    room = world.get("room")
    if sw.meters.get("position", 0) >= THRESHOLD:
        room.meters["bright"] = 1
    else:
        room.meters["bright"] = 0


def detect_conflict(world: World) -> None:
    checker = world.get("checker")
    detective = world.get("detective")
    sw = world.get("switch")
    room = world.get("room")
    if sw.meters.get("position", 0) < THRESHOLD and room.meters.get("bright", 0) < THRESHOLD:
        checker.memes["worry"] = 1
        detective.memes["suspicion"] = 1
        detective.memes["conflict"] = 1
        checker.memes["conflict"] = 1
        world.fired.add(("conflict",))
        return


def solve_case(world: World) -> None:
    detective = world.get("detective")
    checker = world.get("checker")
    sw = world.get("switch")
    room = world.get("room")
    detective.memes["conflict"] = 0
    checker.memes["conflict"] = 0
    detective.memes["pride"] = 1
    checker.memes["relief"] = 1
    sw.meters["position"] = 1
    room.meters["bright"] = 1
    world.fired.add(("resolved",))


def tell(world: World, params: StoryParams) -> World:
    detective = world.add(Entity(id="detective", kind="character", type="boy", label=params.detector))
    checker = world.add(Entity(id="checker", kind="character", type="girl", label=params.checker))
    switch = world.add(Entity(id="switch", type="switch", label=params.switch_name, phrase=params.switch_kind))
    room = world.add(Entity(id="room", type="room", label=params.place))

    switch.meters["position"] = 0
    room.meters["bright"] = 0
    detector_name = detective.label
    checker_name = checker.label

    world.say(
        f"{detector_name} was a small detective who loved quiet rooms, sharp clues, and neat answers."
    )
    world.say(
        f"{checker_name} was the checker, the one who watched the details and noticed when something looked wrong."
    )
    world.say(
        f"In the {params.place}, there was a {params.switch_kind} called the {params.switch_name}."
    )

    world.para()
    world.say(
        f"One evening, the {params.place} went dim, and the checker frowned because the {params.switch_name} was off."
    )
    world.say(
        f"The detective leaned close and said the case would not be hard if they followed the clue with care."
    )

    detect_conflict(world)
    if checker.memes.get("conflict", 0) >= THRESHOLD:
        world.say(
            f"The checker felt the conflict right away, because a dark room made the job harder and the clue felt urgent."
        )
    if detective.memes.get("suspicion", 0) >= THRESHOLD:
        world.say(
            f"The detective suspected someone had moved the switch and wanted to know why."
        )

    world.para()
    world.say(
        f"They checked the wall, checked the floor, and checked the switch again. The detective noticed a tiny smudge on the lever."
    )
    world.say(
        f"That was enough to solve the mystery: someone had bumped the switch while hurrying past."
    )

    solve_case(world)
    world.say(
        f"The detective flipped the {params.switch_name} back on, and the {params.place} glowed bright again."
    )
    world.say(
        f"The checker smiled, the conflict faded, and the two of them stood in the warm light with the case solved."
    )

    world.facts.update(
        detective=detective,
        checker=checker,
        switch=switch,
        room=room,
        place=params.place,
        switch_kind=params.switch_kind,
    )
    return world


PLACES = {
    "hall": Setting(place="the hall"),
    "station": Setting(place="the station"),
    "library": Setting(place="the library"),
    "workshop": Setting(place="the workshop"),
}

SWITCH_KINDS = {
    "lamp switch": "lamp switch",
    "signal switch": "signal switch",
    "power switch": "power switch",
    "panel switch": "panel switch",
}

DETECTOR_NAMES = ["Mina", "Iris", "Theo", "Noah", "Lena", "Owen", "Ruby", "Finn"]
CHECKER_NAMES = ["Pip", "June", "Kit", "Tessa", "Milo", "Nora", "Jules", "Ada"]


ASP_RULES = r"""
% A case is in conflict when the switch is off and the room is dark.
conflict(C) :- switch(C), off(C), dark(C).

% The detective can solve the case if the switch is the only reason for darkness.
solved(C) :- conflict(C), switch(C), checked(C), turned_on(C).

#show conflict/1.
#show solved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid in SWITCH_KINDS:
        lines.append(asp.fact("switch", sid))
        lines.append(asp.fact("checked", sid))
        lines.append(asp.fact("turned_on", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld about a switch, a checker, and a conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--switch-kind", choices=SWITCH_KINDS)
    ap.add_argument("--detector")
    ap.add_argument("--checker")
    ap.add_argument("--switch-name")
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
    switch_kind = args.switch_kind or rng.choice(list(SWITCH_KINDS))
    detector = args.detector or rng.choice(DETECTOR_NAMES)
    checker = args.checker or rng.choice(CHECKER_NAMES)
    switch_name = args.switch_name or rng.choice(["main switch", "big switch", "brass switch", "wall switch"])
    return StoryParams(
        place=place,
        detector=detector,
        checker=checker,
        switch_name=switch_name,
        switch_kind=switch_kind,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child that includes the words "switch" and "checker".',
        f"Tell a gentle mystery where {f['checker'].label} notices the {f['switch'].label} is wrong and {f['detective'].label} helps solve the conflict.",
        f"Write a simple detective tale set in {f['place']} where a switch changes the room from dark to bright.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.facts["detective"]
    c = world.facts["checker"]
    sw = world.facts["switch"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Who noticed the problem with the switch in {place}?",
            answer=f"The checker, {c.label}, noticed that the {sw.label} was off and the room was dark.",
        ),
        QAItem(
            question=f"What kind of story is this?",
            answer=f"It is a detective story about {d.label} and {c.label} solving a small conflict.",
        ),
        QAItem(
            question=f"What changed after the detective solved the case?",
            answer=f"The {sw.label} was flipped on, so {place} became bright again.",
        ),
        QAItem(
            question=f"Why was there conflict in the story?",
            answer=f"There was conflict because the {sw.label} was off and the dark room made the checker worry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a switch do?",
            answer="A switch can turn something on or off, like a light or a machine.",
        ),
        QAItem(
            question="What does a checker do?",
            answer="A checker looks carefully for details and notices when something is not right.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and solves mysteries.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
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


def valid_combos() -> list[tuple[str, str]]:
    return sorted((place, sw) for place in PLACES for sw in SWITCH_KINDS)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show switch/1.\n#show place/1.\n"))
    return sorted(set(asp.atoms(model, "switch"))), sorted(set(asp.atoms(model, "place")))


def asp_verify() -> int:
    import asp
    # Basic parity check: the ASP facts and Python registry should name the same sets.
    py_places = set(PLACES)
    py_switches = set(SWITCH_KINDS)
    model = asp.one_model(asp_program("#show place/1.\n#show switch/1.\n"))
    asp_places = {a[0] for a in asp.atoms(model, "place")}
    asp_switches = {a[0] for a in asp.atoms(model, "switch")}
    ok = py_places == asp_places and py_switches == asp_switches
    if ok:
        print(f"OK: ASP/Python registry parity ({len(py_places)} places, {len(py_switches)} switches).")
        return 0
    print("MISMATCH:")
    print(" places only in python:", sorted(py_places - asp_places))
    print(" places only in asp:", sorted(asp_places - py_places))
    print(" switches only in python:", sorted(py_switches - asp_switches))
    print(" switches only in asp:", sorted(asp_switches - py_switches))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show switch/1.\n#show place/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show switch/1.\n#show place/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="hall", detector="Mina", checker="Pip", switch_name="main switch", switch_kind="lamp switch"),
            StoryParams(place="station", detector="Theo", checker="June", switch_name="signal switch", switch_kind="signal switch"),
            StoryParams(place="library", detector="Lena", checker="Ada", switch_name="wall switch", switch_kind="power switch"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
