#!/usr/bin/env python3
"""
storyworlds/worlds/tad_friendship_heartwarming.py
=================================================

A small heartwarming storyworld about a tadpole named Tad, a friendship worry,
and a gentle turn toward helping.

The seed idea:
- Tad wants to do something kind for a friend.
- A small obstacle makes Tad feel uncertain.
- A friend responds warmly, and the two share a peaceful ending.

This script keeps the domain compact and constraint-checked:
- physical state: distance, items, weather, water/depth
- emotional state: worry, joy, gratitude, friendship
- story generation is driven by simulated world state
- invalid explicit requests raise StoryError

The world is intentionally simple and child-facing, with a heartwarming tone.
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
    plural: bool = False
    owner: Optional[str] = None
    near: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"tad", "fish", "frog"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    depth: str
    cozy: bool = False
    sights: tuple[str, ...] = ()


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    hazard: str
    help_kind: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    type: str
    fragile: bool = False
    fits: set[str] = field(default_factory=set)


@dataclass
class FriendAid:
    id: str
    label: str
    action: str
    promise: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


@dataclass
class StoryParams:
    place: str
    task: str
    gift: str
    name: str
    friend_name: str
    seed: Optional[int] = None


PLACES = {
    "pond": Place("pond", "the pond", depth="shallow", cozy=True, sights=("lilypads", "reeds", "tiny ripples")),
    "stream": Place("stream", "the stream", depth="shallow", cozy=False, sights=("smooth stones", "sparkles", "little waves")),
    "garden": Place("garden", "the garden pool", depth="shallow", cozy=True, sights=("flowers", "dew", "soft leaves")),
}

TASKS = {
    "bring_lily": Task(
        id="bring_lily",
        verb="bring a lily",
        gerund="bringing a lily",
        risk="the lily could wilt",
        hazard="it might get bent in the water",
        help_kind="care",
        keyword="lily",
        tags={"flower", "gentle"},
    ),
    "share_pebbles": Task(
        id="share_pebbles",
        verb="share pebbles",
        gerund="sharing pebbles",
        risk="a pebble could slip away",
        hazard="it might splash into the mud",
        help_kind="friendship",
        keyword="pebbles",
        tags={"stones", "share"},
    ),
    "return_shell": Task(
        id="return_shell",
        verb="return a shell",
        gerund="returning a shell",
        risk="the shell could crack",
        hazard="it might bump against a stone",
        help_kind="care",
        keyword="shell",
        tags={"shell", "kind"},
    ),
}

GIFTS = {
    "flower": Gift("flower", "a little flower", "a little flower with a soft stem", "flower", fragile=True, fits={"bring_lily"}),
    "pebbles": Gift("pebbles", "smooth pebbles", "a handful of smooth pebbles", "pebbles", fragile=False, fits={"share_pebbles"}),
    "shell": Gift("shell", "a shiny shell", "a shiny shell with a pale swirl", "shell", fragile=True, fits={"return_shell"}),
}

AIDS = {
    "listen": FriendAid("listen", "listening carefully", "listen close and smile", "would help because Tad would feel understood", helps={"bring_lily", "return_shell"}),
    "carry": FriendAid("carry", "carrying the gift in a leaf", "carry it on a leaf", "would help because the water would be gentler that way", helps={"bring_lily", "return_shell"}),
    "share": FriendAid("share", "sharing pebbles together", "gather pebbles side by side", "would help because doing it together would be more fun", helps={"share_pebbles"}),
}

NAMES = ["Tad", "Milo", "Pip", "Nori", "Ollie"]
FRIEND_NAMES = ["Mina", "Luna", "Bea", "Finn", "Pia"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for task_id, task in TASKS.items():
            for gift_id, gift in GIFTS.items():
                if task_id in gift.fits:
                    combos.append((place, task_id, gift_id))
    return combos


def explain_rejection(task: Task, gift: Gift) -> str:
    return (
        f"(No story: {gift.label} does not match {task.gerund}. "
        f"The gentle fix must actually fit the task, so this request is rejected.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about Tad and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    if args.task and args.gift:
        if args.task not in GIFTS[args.gift].fits:
            raise StoryError(explain_rejection(TASKS[args.task], GIFTS[args.gift]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.gift is None or c[2] == args.gift)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, gift = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != name])
    return StoryParams(place=place, task=task, gift=gift, name=name, friend_name=friend_name)


def _setup(world: World, tad: Entity, friend: Entity, task: Task, gift: Gift) -> None:
    world.say(
        f"Tad lived near {world.place.label}, where the water was calm and the little "
        f"world felt safe."
    )
    world.say(
        f"He liked {task.gerund} for {friend.label}, because {friend.label} always "
        f"smiled when Tad tried to help."
    )
    world.say(f"That morning Tad found {gift.phrase} and wanted to make the day bright.")


def _tension(world: World, tad: Entity, friend: Entity, task: Task, gift: Gift) -> None:
    tad.memes["worry"] = 1.0
    tad.memes["hope"] = 1.0
    world.para()
    world.say(
        f"Tad paddled toward {friend.label}, but he paused when he remembered "
        f"that {task.risk}."
    )
    world.say(
        f"{task.hazard.capitalize()}, and Tad did not want {gift.label} to get hurt."
    )
    world.say(
        f"He looked down, and his little fins grew still."
    )


def _friend_response(world: World, tad: Entity, friend: Entity, task: Task, aid: FriendAid) -> None:
    world.say(
        f"Then {friend.label} noticed and swam closer with a warm smile."
    )
    world.say(
        f'"Let me {aid.action}," {friend.label} said. "{aid.promise}."'
    )
    tad.memes["worry"] = 0.0
    tad.memes["joy"] = 1.0
    tad.memes["friendship"] = 1.0
    friend.memes["joy"] = 1.0
    friend.memes["friendship"] = 1.0


def _resolution(world: World, tad: Entity, friend: Entity, task: Task, gift: Gift, aid: FriendAid) -> None:
    world.para()
    world.say(
        f"Tad nodded, and the two of them {aid.action}."
    )
    world.say(
        f"With the kind help, Tad finished {task.gerund}, and {gift.label} stayed safe."
    )
    world.say(
        f"At the end, Tad and {friend.label} floated side by side, happy to share the quiet water."
    )


def tell(place: Place, task: Task, gift: Gift, name: str, friend_name: str) -> World:
    world = World(place)
    tad = world.add(Entity(id=name, kind="character", type="tad", label=name))
    friend = world.add(Entity(id=friend_name, kind="character", type="fish", label=friend_name))

    _setup(world, tad, friend, task, gift)
    _tension(world, tad, friend, task, gift)
    aid = next(a for a in AIDS.values() if task.id in a.helps)
    _friend_response(world, tad, friend, task, aid)
    _resolution(world, tad, friend, task, gift, aid)

    world.facts.update(tad=tad, friend=friend, task=task, gift=gift, aid=aid, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child about {f["tad"].label} and friendship.',
        f"Tell a gentle story where {f['tad'].label} wants to {f['task'].verb} for {f['friend'].label} but worries, then gets help.",
        f"Write a simple story with the word '{f['task'].keyword}' that ends with two friends feeling warm and safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    tad, friend, task, gift = f["tad"], f["friend"], f["task"], f["gift"]
    return [
        QAItem(
            question=f"Who is the story mostly about?",
            answer=f"The story is mostly about {tad.label}, a little tadpole who wants to be kind to {friend.label}.",
        ),
        QAItem(
            question=f"What did Tad want to do for {friend.label}?",
            answer=f"Tad wanted to {task.verb} for {friend.label}.",
        ),
        QAItem(
            question=f"Why did Tad pause before helping?",
            answer=f"Tad paused because he worried that {task.risk}. He did not want {gift.label} to get hurt.",
        ),
        QAItem(
            question=f"How did the problem get better?",
            answer=f"{friend.label} smiled, offered help, and the two friends did it together. That made Tad feel safe again.",
        ),
        QAItem(
            question=f"What was the ending like?",
            answer=f"At the end, Tad and {friend.label} floated side by side, and {gift.label} stayed safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tadpole?",
            answer="A tadpole is a young frog. It usually has a tail and lives in water.",
        ),
        QAItem(
            question="What does a friend do when someone is worried?",
            answer="A good friend can listen, help, and make the other person feel less alone.",
        ),
        QAItem(
            question="Why is gentle help important?",
            answer="Gentle help matters because kind actions can keep something safe and make a hard moment easier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="pond", task="bring_lily", gift="flower", name="Tad", friend_name="Mina"),
    StoryParams(place="stream", task="share_pebbles", gift="pebbles", name="Tad", friend_name="Finn"),
    StoryParams(place="garden", task="return_shell", gift="shell", name="Tad", friend_name="Bea"),
]


ASP_RULES = r"""
task_fits(Task, Gift) :- fits(Gift, Task).
valid(Place, Task, Gift) :- place(Place), task(Task), gift(Gift), task_fits(Task, Gift).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for g in sorted([gid for gid, gift in GIFTS.items() if tid in gift.fits]):
            lines.append(asp.fact("fits", g, tid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TASKS[params.task], GIFTS[params.gift], params.name, params.friend_name)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
