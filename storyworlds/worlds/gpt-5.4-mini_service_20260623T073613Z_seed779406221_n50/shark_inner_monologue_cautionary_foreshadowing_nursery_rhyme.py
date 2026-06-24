#!/usr/bin/env python3
"""
storyworlds/worlds/shark_inner_monologue_cautionary_foreshadowing_nursery_rhyme.py
===================================================================================

A small standalone storyworld for a nursery-rhyme-style tale about a shark,
with inner monologue, cautionary beats, and foreshadowing.

Premise:
- A curious little shark wants to chase a shining shell in the cove.
- A careful friend notices the tide and warns that the shell is a trap.
- The shark thinks hard, changes course, and ends by choosing a safer game.

The simulated world keeps:
- physical meters: distance, tide, splash, tiredness
- emotional memes: curiosity, worry, courage, relief, pride

The prose is state-driven rather than a fixed paragraph with swapped nouns.
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"shark"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"fish"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    waters: str
    current: str
    depth: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    shimmer: str
    risky: bool = True


@dataclass
class Friend:
    id: str
    label: str
    type: str
    monologue: str
    warning: str
    safe_game: str


class World:
    def __init__(self, place: Place) -> None:
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

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _r_worry(world: World) -> list[str]:
    out = []
    shark = world.get("shark")
    if shark.meters["distance"] >= THRESHOLD and shark.memes["curiosity"] >= THRESHOLD:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            shark.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    shark = world.get("shark")
    if shark.memes["worry"] >= THRESHOLD and shark.meters["distance"] <= 0:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            shark.memes["relief"] += 1
            out.append("__relief__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_worry, _r_relief):
            got = rule(world)
            if got:
                changed = True
                produced.extend(g for g in got if not g.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def foreshadow(world: World, shark: Entity, prize: Prize) -> None:
    world.say(
        f"The moon on the water wore a silver ring, and {prize.label} kept on "
        f"gleaming where the tide could tug it."
    )
    world.say(
        f"{shark.id} swam near and thought, 'That shiny {prize.label} looks sweet,' "
        f"but the current hummed like a warning song."
    )
    shark.memes["curiosity"] += 1
    shark.meters["distance"] += 1


def inner_monologue(world: World, shark: Entity, prize: Prize) -> None:
    world.say(
        f"'{prize.label} for me?' wondered {shark.id} in his little head. "
        f"'No, wait now, the tide might steal it away.'"
    )
    shark.memes["caution"] += 1


def cautionary_friend(world: World, shark: Entity, friend: Friend, prize: Prize) -> None:
    world.say(
        f"{friend.label} flicked a fin and said, '{friend.warning}'"
    )
    world.say(
        f"'Let's not dash for the {prize.label}; the deep water can turn quick and keen.'"
    )
    shark.memes["fear"] += 1
    shark.memes["worry"] += 1


def choose_safer_game(world: World, shark: Entity, friend: Friend) -> None:
    shark.memes["courage"] += 1
    shark.memes["relief"] += 1
    shark.meters["distance"] = 0
    world.say(
        f"{shark.id} slowed his swim and answered, 'I will not chase the shiny thing. "
        f"I'll play {friend.safe_game} instead.'"
    )
    world.say(
        f"So the two little swimmers twirled in the cove, making moonlit loops and "
        f"laughing where the water was calm."
    )


def tell(place: Place, prize: Prize, friend: Friend) -> World:
    world = World(place)
    shark = world.add(Entity(id="shark", kind="character", type="shark", label="shark"))
    pal = world.add(Entity(id="friend", kind="character", type="fish", label=friend.label))
    world.facts.update(place=place, prize=prize, friend=friend, shark=shark, pal=pal)

    world.say(
        f"By the blue, blue cove, a little shark named shark swam under the soft white foam."
    )
    world.say(f"The sea was {place.waters}, the current was {place.current}, and the deep was {place.depth}.")
    world.say(f"He loved the shine of {prize.phrase}, because {prize.shimmer}.")

    world.para()
    foreshadow(world, shark, prize)
    inner_monologue(world, shark, prize)
    cautionary_friend(world, shark, friend, prize)
    propagate(world, narrate=True)

    world.para()
    choose_safer_game(world, shark, friend)

    world.say(
        f"In the end, the shiny shell stayed where it was, and shark stayed safe, "
        f"smiling in the silver moon-water."
    )
    return world


PLACES = {
    "cove": Place(
        id="cove",
        label="the moonlit cove",
        waters="soft and clear",
        current="a sly little tug",
        depth="shallow near the stones",
        tags={"water", "cove", "tide"},
    ),
    "reef": Place(
        id="reef",
        label="the coral reef",
        waters="bright and warm",
        current="a twisty ribbon",
        depth="full of hidden nooks",
        tags={"water", "reef"},
    ),
}

PRIZES = {
    "shell": Prize(
        id="shell",
        label="shell",
        phrase="a shining shell",
        shimmer="it flashed like a tiny moon",
    ),
    "pearl": Prize(
        id="pearl",
        label="pearl",
        phrase="a pearly bead",
        shimmer="it twinkled like a star drop",
    ),
}

FRIENDS = {
    "minnow": Friend(
        id="minnow",
        label="a little minnow",
        type="fish",
        monologue="I think that shiny thing is trouble.",
        warning="Caution, caution, little shark!",
        safe_game="ring-chasing",
    ),
    "seahorse": Friend(
        id="seahorse",
        label="a gentle seahorse",
        type="fish",
        monologue="The tide can tug hard near shiny things.",
        warning="Slow fins, slow fins!",
        safe_game="bubble-dancing",
    ),
}


@dataclass
class StoryParams:
    place: str
    prize: str
    friend: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, r, f) for p in PLACES for r in PRIZES for f in FRIENDS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme shark storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--friend", choices=FRIENDS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.prize is None or c[1] == args.prize)
              and (args.friend is None or c[2] == args.friend)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prize, friend = rng.choice(sorted(combos))
    return StoryParams(place=place, prize=prize, friend=friend)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    shark = f["shark"]
    prize = f["prize"]
    friend = f["friend"]
    place = f["place"]
    return [
        QAItem(
            question="What did the shark want at first?",
            answer=f"He wanted to chase the {prize.label} because it shone so bright in {place.label}.",
        ),
        QAItem(
            question="What did the friend warn about?",
            answer=f"{friend.warning} The friend was warning that the tide and current could make the shiny prize a bad choice.",
        ),
        QAItem(
            question="How did the shark end the story?",
            answer=f"He chose {friend.safe_game} instead, and the ending was calm and safe in the {place.label}.",
        ),
        QAItem(
            question="What was the shark thinking inside his head?",
            answer="He was thinking that the shiny thing looked nice, but the warning feeling in the water mattered more.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can the tide matter near the shore?",
            answer="The tide moves water in and out, so it can pull small things around and change where they sit.",
        ),
        QAItem(
            question="Why should a little fish listen to a warning?",
            answer="A warning helps someone notice danger before it becomes a bigger problem, which keeps the swim safe.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style story about a shark in {f["place"].label} who wants {f["prize"].phrase} but listens to a warning.',
        f"Tell a gentle cautionary story where a shark has an inner monologue about a shiny {f['prize'].label} and chooses a safer game instead.",
        f"Write a short rhyming story with foreshadowing in the sea and a calm ending where the shark stays safe.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out += [f"{i+1}. {p}" for i, p in enumerate(sample.prompts)]
    out += ["", "== story qa =="]
    for item in sample.story_qa:
        out += [f"Q: {item.question}", f"A: {item.answer}"]
    out += ["", "== world qa =="]
    for item in sample.world_qa:
        out += [f"Q: {item.question}", f"A: {item.answer}"]
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PRIZES[params.prize], FRIENDS[params.friend])
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
place(cove).
place(reef).
prize(shell).
prize(pearl).
friend(minnow).
friend(seahorse).
valid(P, R, F) :- place(P), prize(R), friend(F).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    for f in FRIENDS:
        lines.append(asp.fact("friend", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH")
    print("only in asp:", sorted(asp_set - py_set))
    print("only in py:", sorted(py_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(p, r, f)) for p, r, f in valid_combos()]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
