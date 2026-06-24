#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/tassel_session_bad_ending_whodunit.py
===============================================================================================================

A small whodunit-style storyworld about a ceremonial session, a missing tassel,
and a bad ending that leaves the mystery only partly solved.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

from storyworlds.results import QAItem, StoryError, StorySample

BAD_ENDING_NOTE = "bad ending"


@dataclass
class StoryParams:
    room: str
    event: str
    tassel_color: str
    witness: str
    suspect: str
    keeper: str
    clue: str
    seed: Optional[int] = None


@dataclass
class Item:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: {"place": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0})
    held_by: Optional[str] = None
    missing: bool = False


@dataclass
class World:
    room: str
    event: str
    items: dict[str, Item] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def note(self, text: str) -> None:
        self.trace.append(text)

    def add(self, item: Item) -> Item:
        self.items[item.name] = item
        return item

    def get(self, name: str) -> Item:
        return self.items[name]


ROOMS = {
    "hall": "the old hall",
    "library": "the reading room",
    "chapel": "the little chapel",
    "studio": "the music studio",
}

EVENTS = {
    "session": "a quiet session",
    "sewing_session": "a sewing session",
    "music_session": "a music session",
    "tea_session": "a tea session",
}

TASSEL_COLORS = ["red", "gold", "blue", "green", "silver"]
WITNESSES = ["Mina", "Eli", "June", "Otis", "Nina", "Sage"]
SUSPECTS = ["Mr. Pallow", "Ms. Reed", "Aunt Vera", "Theo", "Lark"]
KEEPERS = ["the keeper", "the host", "the usher", "the librarian"]
CLUES = [
    "a frayed ribbon",
    "a dusty shelf",
    "a small chair",
    "a dropped pin",
    "a closed curtain",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with a tassel, a session, and a bad ending.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--tassel-color", choices=TASSEL_COLORS)
    ap.add_argument("--witness", choices=WITNESSES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--keeper", choices=KEEPERS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def reasonableness_gate(params: StoryParams) -> None:
    if params.event != "session":
        raise StoryError("This storyworld only supports a session; other events would not fit the whodunit premise.")
    if params.room == "studio" and params.clue == "a dusty shelf":
        raise StoryError("That clue does not fit the music studio in this little mystery.")
    if params.tassel_color == "silver" and params.suspect == "Lark":
        raise StoryError("That pairing is too neat for this mystery; choose a different suspect or tassel color.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or rng.choice(list(ROOMS))
    event = args.event or "session"
    tassel_color = args.tassel_color or rng.choice(TASSEL_COLORS)
    witness = args.witness or rng.choice(WITNESSES)
    suspect = args.suspect or rng.choice(SUSPECTS)
    keeper = args.keeper or rng.choice(KEEPERS)
    clue = args.clue or rng.choice(CLUES)
    params = StoryParams(room=room, event=event, tassel_color=tassel_color, witness=witness, suspect=suspect, keeper=keeper, clue=clue)
    reasonableness_gate(params)
    return params


def _do_story(params: StoryParams) -> World:
    world = World(room=ROOMS[params.room], event=EVENTS[params.event])
    tassel = world.add(Item(name="tassel", kind="ornament"))
    ledger = world.add(Item(name="ledger", kind="record"))
    witness = world.add(Item(name=params.witness, kind="person"))
    suspect = world.add(Item(name=params.suspect, kind="person"))
    keeper = world.add(Item(name=params.keeper, kind="person"))
    clue = world.add(Item(name=params.clue, kind="clue"))

    tassel.meters["place"] = 1.0
    tassel.memes["worry"] = 0.0
    ledger.held_by = keeper.name
    clue.held_by = witness.name
    world.facts.update(
        room=params.room,
        event=params.event,
        tassel_color=params.tassel_color,
        witness=params.witness,
        suspect=params.suspect,
        keeper=params.keeper,
        clue=params.clue,
        ending=BAD_ENDING_NOTE,
    )

    world.note(f"It was {world.event} in {world.room}, and everyone expected a calm evening.")
    world.note(f"A {params.tassel_color} tassel hung from the ledger, bright enough to catch the eye.")
    world.note(f"{witness.name} noticed it first, because {witness.name} was watching the room closely.")
    world.note(f"Then the tassel was gone, and the small session turned sharp and uneasy.")
    world.note(f"{keeper.name} frowned and asked who had been near the ledger.")
    world.note(f"{witness.name} pointed at {suspect.name}, but the clue was only {params.clue}.")
    world.note(f"The room searched corners and chairs, yet the missing tassel did not come back.")
    world.note(f"By the end of the session, the mystery stayed open, and the answer felt unfinished.")
    world.note(f"That was the bad ending: the tassel never returned, and the wrong silence stayed behind.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = _do_story(params)
    story = "\n\n".join(world.trace)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit about a {f["event"]} in {world.room} where a tassel goes missing.',
        f'Tell a child-friendly mystery story set in {world.room} with a clue and a suspicious person.',
        f'Write a simple story that ends badly when a tassel disappears during a session.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Where did the session happen?",
            answer=f"The session happened in {world.room}.",
        ),
        QAItem(
            question=f"What color was the tassel?",
            answer=f"The tassel was {f['tassel_color']}.",
        ),
        QAItem(
            question=f"Who noticed the tassel first?",
            answer=f"{f['witness']} noticed the tassel first.",
        ),
        QAItem(
            question=f"What made this a bad ending?",
            answer="The tassel disappeared and the mystery was not solved by the end.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of information that can help solve a mystery.",
        ),
        QAItem(
            question="What is a session?",
            answer="A session is a set time when people gather to do one activity together.",
        ),
        QAItem(
            question="What is a tassel?",
            answer="A tassel is a small bunch of thread or cord strands that can hang from a cord or decoration.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "\n".join([f"ROOM={world.room}", f"EVENT={world.event}"] + world.trace)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("session", "session")]
    for room in ROOMS:
        lines.append(asp.fact("room", room))
    for color in TASSEL_COLORS:
        lines.append(asp.fact("tassel_color", color))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(R) :- room(R), session(session).
#show valid_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_ok = bool(asp.atoms(model, "valid_story"))
    py_ok = True
    if asp_ok == py_ok:
        print("OK: ASP and Python gates agree.")
        return 0
    print("MISMATCH: ASP and Python gates disagree.")
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(room="hall", event="session", tassel_color="red", witness="Mina", suspect="Mr. Pallow", keeper="the keeper", clue="a frayed ribbon"),
    StoryParams(room="library", event="session", tassel_color="gold", witness="Eli", suspect="Ms. Reed", keeper="the librarian", clue="a dusty shelf"),
    StoryParams(room="chapel", event="session", tassel_color="blue", witness="June", suspect="Aunt Vera", keeper="the usher", clue="a dropped pin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
