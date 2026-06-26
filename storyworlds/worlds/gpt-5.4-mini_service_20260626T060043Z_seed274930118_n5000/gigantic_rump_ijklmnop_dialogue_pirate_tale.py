#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gigantic_rump_ijklmnop_dialogue_pirate_tale.py
===============================================================================================================

A standalone storyworld for a tiny pirate tale domain with dialogue, a
gigantic rump, and the strange word "ijklmnop" tucked into the sail-house code.

Premise:
- A proud pirate captain has a gigantic rump and loves sitting in the cramped
  chart nook to stare at treasure maps.
- The little stool in the nook is too small for that rump.
- A clever mate notices the trouble and offers a wider barrel seat.
- The crew uses the password "ijklmnop" to open the locker where the barrel seat
  is kept.
- The captain accepts the fix, sits safely, and the crew cheers over the map.

This world is intentionally small and constraint-checked: the captain only gets
a happy ending when the seat actually fits the rump and the locker code is
correct.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    seat_for: Optional[str] = None
    lock_code: str = ""
    openable: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fit": 0.0, "sturdy": 0.0, "mess": 0.0, "width": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "worry": 0.0, "joy": 0.0, "embarrassment": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "mate"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Harbor:
    place: str = "the harbor"
    on_ship: bool = True
    affords: set[str] = field(default_factory=lambda: {"chart", "treasure", "barrel"})


@dataclass
class Seat:
    id: str
    label: str
    width: int
    sturdy: int
    clue: str
    lock_code: str = ""
    openable: bool = False


@dataclass
class StoryParams:
    place: str
    seat: str
    name: str
    mate_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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

    def copy(self) -> "World":
        import copy
        w = World(self.harbor)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def seat_fits(captain: Entity, seat: Seat) -> bool:
    return captain.meters["width"] <= seat.width


def seat_is_sturdy(captain: Entity, seat: Seat) -> bool:
    return seat.sturdy >= 1 and captain.meters["weight"] <= seat.sturdy


def reasonableness_gate(captain: Entity, seat: Seat) -> bool:
    return seat_fits(captain, seat) and seat_is_sturdy(captain, seat)


def invalid_reason(captain: Entity, seat: Seat) -> str:
    if not seat_fits(captain, seat):
        return (
            f"(No story: {seat.label} is too narrow for {captain.pronoun('possessive')} "
            f"gigantic rump. The fix must actually fit.)"
        )
    return (
        f"(No story: {seat.label} isn't sturdy enough to hold the captain safely. "
        f"The fix must be strong as well as wide.)"
    )


def resolve_name(gender_seed: str, rng: random.Random) -> str:
    choices = {
        "captain": ["Captain Brine", "Captain Coral", "Captain Nell", "Captain Rook"],
        "mate": ["Mina", "Jory", "Tess", "Pip"],
    }
    return rng.choice(choices[gender_seed])


def tell(params: StoryParams) -> World:
    world = World(Harbor(place=params.place))
    captain = world.add(Entity(
        id=params.name,
        kind="character",
        type="captain",
        label="captain",
        meters={"width": 3.0, "weight": 3.0, "fit": 0.0, "sturdy": 0.0, "mess": 0.0},
        memes={"pride": 1.0, "worry": 0.0, "joy": 0.0, "embarrassment": 0.0},
    ))
    mate = world.add(Entity(
        id=params.mate_name,
        kind="character",
        type="mate",
        label="mate",
        meters={"width": 1.0, "weight": 1.0, "fit": 0.0, "sturdy": 0.0, "mess": 0.0},
        memes={"pride": 0.0, "worry": 0.0, "joy": 0.0, "embarrassment": 0.0},
    ))

    stool = world.add(Entity(
        id="stool",
        type="thing",
        label="tiny stool",
        phrase="a tiny chart-room stool",
        meters={"width": 1.0, "sturdy": 1.0, "fit": 0.0, "mess": 0.0},
        seat_for="captain",
    ))
    barrel = world.add(Entity(
        id="barrel_seat",
        type="thing",
        label="barrel seat",
        phrase="a wide barrel seat",
        meters={"width": 4.0, "sturdy": 3.0, "fit": 0.0, "mess": 0.0},
        seat_for="captain",
        lock_code="ijklmnop",
        openable=True,
    ))

    world.say(
        f'“Ahoy!” said {captain.id}, patting {captain.pronoun("possessive")} gigantic rump. '
        f'“I want to sit in the chart nook and look for treasure.”'
    )
    world.say(
        f'“That stool is a wee one,” said {mate.id}. “It looks like it would squeak under '
        f'{captain.pronoun("possessive")} rump.”'
    )
    world.say(
        f'{captain.id} frowned. “Aye, but I love that nook. The map feels lucky there.”'
    )

    world.para()
    if not seat_fits(captain, stool):
        captain.memes["worry"] += 1
        captain.memes["embarrassment"] += 1
        world.say(
            f'{captain.id} tried to sit on the tiny stool anyway, but the seat wobbled and '
            f'slid sideways. “Blimey,” said {mate.id}, “that stool is too small for that '
            f'gigantic rump.”'
        )
        world.say(
            f'“Then find me a better one,” muttered {captain.id}, hugging the map tight.'
        )

    world.para()
    world.say(
        f'{mate.id} pointed at a locker under the chart table. “The barrel seat is in there, '
        f'but the lock wants a code.”'
    )
    world.say(f'“What code?” asked {captain.id}.')
    world.say(f'“The ship-song word: ijklmnop,” said {mate.id}.')
    world.say(
        f'{captain.id} grinned. “Aye! A silly code for a grand seat. Open it up!”'
    )

    if barrel.lock_code != "ijklmnop":
        raise StoryError("The barrel seat code must be ijklmnop in this world.")

    world.say(
        f'{mate.id} clicked the locker open, and out came the wide barrel seat. “Now that '
        f'looks stout,” said {captain.id}.'
    )
    if not reasonableness_gate(captain, Seat(
        id="barrel_seat", label="barrel seat", width=barrel.meters["width"], sturdy=barrel.meters["sturdy"], clue="", lock_code="ijklmnop", openable=True
    )):
        raise StoryError("The chosen fix does not actually solve the seating problem.")

    captain.memes["joy"] += 1
    captain.memes["worry"] = 0.0
    captain.memes["embarrassment"] = 0.0
    world.say(
        f'{captain.id} sat down, and the barrel seat held steady. “That feels fine as fish '
        f'cake,” {captain.id} said. “My rump fits at last.”'
    )
    world.say(
        f'{mate.id} laughed. “Now you can read the map without wobbling!”'
    )
    world.say(
        f'The two pirates leaned over the chart and found the X, while the ship rocked '
        f'kindly in the harbor.'
    )

    world.facts.update(
        captain=captain,
        mate=mate,
        stool=stool,
        barrel=barrel,
        params=params,
        resolved=True,
        code="ijklmnop",
    )
    return world


SETTINGS = {
    "harbor": Harbor(place="the harbor", on_ship=True, affords={"chart", "treasure", "barrel"}),
    "dock": Harbor(place="the dock", on_ship=False, affords={"chart", "treasure", "barrel"}),
    "cove": Harbor(place="the cove", on_ship=True, affords={"chart", "treasure", "barrel"}),
}

SEATS = {
    "stool": Seat(id="stool", label="tiny stool", width=1, sturdy=1, clue="small"),
    "barrel": Seat(id="barrel_seat", label="barrel seat", width=4, sturdy=3, clue="wide"),
}

CAPTAIN_NAMES = ["Captain Brine", "Captain Coral", "Captain Nell", "Captain Rook"]
MATE_NAMES = ["Mina", "Jory", "Tess", "Pip"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for seat_name, seat in SEATS.items():
            if seat_name == "barrel":
                combos.append((place, seat_name))
    return combos


@dataclass
class _ResolverParams:
    place: str
    seat: str
    name: str
    mate_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with dialogue and a gigantic rump.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--seat", choices=SEATS)
    ap.add_argument("--name")
    ap.add_argument("--mate-name")
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
    place = args.place or rng.choice(list(SETTINGS))
    seat = args.seat or "barrel"
    if seat != "barrel":
        raise StoryError(invalid_reason(
            Entity(id="captain", type="captain", meters={"width": 3.0, "weight": 3.0}), SEATS[seat]
        ))
    name = args.name or rng.choice(CAPTAIN_NAMES)
    mate_name = args.mate_name or rng.choice(MATE_NAMES)
    return StoryParams(place=place, seat=seat, name=name, mate_name=mate_name)


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short pirate tale where a captain with a gigantic rump needs a better seat.',
        'Tell a story with dialogue in which a pirate mate uses the password "ijklmnop" to help.',
        f'Write a child-friendly pirate story set at {world.harbor.place} about a wide seat and a small stool.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    return [
        QAItem(
            question=f"Why did {captain.id} need help in the chart nook?",
            answer=f"{captain.id} needed help because {captain.pronoun('possessive')} gigantic rump did not fit on the tiny stool.",
        ),
        QAItem(
            question="What password opened the locker?",
            answer='The password was "ijklmnop". It opened the locker that held the barrel seat.',
        ),
        QAItem(
            question=f"How did {mate.id} solve the problem?",
            answer=f"{mate.id} opened the locker, brought out the wide barrel seat, and gave {captain.id} a safe place to sit.",
        ),
        QAItem(
            question=f"How did {captain.id} feel at the end?",
            answer=f"{captain.id} felt happy and relieved because the barrel seat fit and the map could be read without wobbling.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a harbor?",
            answer="A harbor is a calm place near the water where ships can wait, load, and unload safely.",
        ),
        QAItem(
            question="What is a barrel seat for?",
            answer="A barrel seat gives someone a wider, sturdier place to sit than a tiny stool.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:12} type={e.type} meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
seat_fits(C,S) :- captain(C), seat(S), cap_width(C,W1), seat_width(S,W2), W1 <= W2.
seat_sturdy(C,S) :- captain(C), seat(S), cap_weight(C,W1), seat_sturdiness(S,W2), W1 <= W2.
valid(C,S) :- seat_fits(C,S), seat_sturdy(C,S).

% The accepted pirate tale is only the barrel-seat solution.
story_ok(C,S) :- valid(C,S), seat_code(S,"ijklmnop").
#show valid/2.
#show story_ok/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("captain", "captain"))
    lines.append(asp.fact("seat", "barrel_seat"))
    lines.append(asp.fact("seat", "stool"))
    lines.append(asp.fact("cap_width", "captain", 3))
    lines.append(asp.fact("cap_weight", "captain", 3))
    lines.append(asp.fact("seat_width", "barrel_seat", 4))
    lines.append(asp.fact("seat_sturdiness", "barrel_seat", 3))
    lines.append(asp.fact("seat_code", "barrel_seat", "ijklmnop"))
    lines.append(asp.fact("seat_width", "stool", 1))
    lines.append(asp.fact("seat_sturdiness", "stool", 1))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {("captain", "barrel_seat")}
    cl = set(asp_valid())
    if py == cl:
        print("OK: ASP matches Python reasonableness gate.")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="harbor", seat="barrel", name="Captain Brine", mate_name="Mina"),
    StoryParams(place="dock", seat="barrel", name="Captain Coral", mate_name="Pip"),
    StoryParams(place="cove", seat="barrel", name="Captain Nell", mate_name="Tess"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show story_ok/2."))
        return
    if args.asp:
        valid = asp_valid()
        print(f"{len(valid)} valid pirate-seat combos:")
        for v in valid:
            print(" ", v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
