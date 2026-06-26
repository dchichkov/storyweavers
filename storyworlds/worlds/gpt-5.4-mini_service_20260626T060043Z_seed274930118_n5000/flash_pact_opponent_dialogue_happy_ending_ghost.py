#!/usr/bin/env python3
"""
storyworlds/worlds/flash_pact_opponent_dialogue_happy_ending_ghost.py
======================================================================

A small story world about a ghost, a flash of light, a pact, and an opponent.

Seed tale:
---
A child finds a quiet old house where a shy ghost lives in the attic. Each night,
a loud rival ghost bangs on the walls and frightens the little ghost away from
its favorite window. One evening, the child flashes a lantern, speaks kindly to
both ghosts, and helps them make a pact: the attic window will belong to the shy
ghost at dusk, and the rival ghost will have the moonlit hall after that. The
ghosts stop arguing, and the house becomes peaceful and warm.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Place:
    label: str
    mood: str
    echoes: bool = False


@dataclass
class Item:
    id: str
    label: str
    phrase: str


@dataclass
class Flash:
    id: str
    label: str
    verb: str
    glow: str
    reveals: str


@dataclass
class Pact:
    id: str
    label: str
    promise: str
    truce_line: str
    settles: str


@dataclass
class Opponent:
    id: str
    label: str
    type: str
    grievance: str
    noise: str
    retreat: str


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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    ghost = world.entities.get("ghost")
    rival = world.entities.get("opponent")
    if not child or not ghost or not rival:
        return out
    if child.memes.get("startle", 0) < THRESHOLD:
        return out
    if rival.memes.get("grudge", 0) < THRESHOLD:
        return out
    sig = ("fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["worry"] = ghost.memes.get("worry", 0) + 1
    out.append("The little ghost trembled at the noise.")
    return out


def _r_pact(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    ghost = world.entities.get("ghost")
    rival = world.entities.get("opponent")
    if not child or not ghost or not rival:
        return out
    if child.memes.get("kindness", 0) < THRESHOLD:
        return out
    if ghost.memes.get("worry", 0) < THRESHOLD:
        return out
    if rival.memes.get("grudge", 0) < THRESHOLD:
        return out
    sig = ("pact",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    ghost.memes["peace"] = ghost.memes.get("peace", 0) + 1
    rival.memes["peace"] = rival.memes.get("peace", 0) + 1
    out.append("__PACT__")
    return out


def _r_happy(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    rival = world.entities.get("opponent")
    if not ghost or not rival:
        return out
    if ghost.memes.get("peace", 0) < THRESHOLD or rival.memes.get("peace", 0) < THRESHOLD:
        return out
    sig = ("happy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The house grew warm and quiet.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_fear, _r_pact, _r_happy):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__PACT__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup_world() -> World:
    world = World(PLACE)
    child = world.add(Entity(id="child", kind="character", type="girl", traits=["small", "brave"]))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the shy ghost", traits=["shy", "gentle"]))
    rival = world.add(Entity(id="opponent", kind="character", type="ghost", label="the rival ghost", traits=["loud", "stubborn"]))
    lantern = world.add(Entity(id="lantern", type="lantern", label="a little lantern", phrase="a little lantern"))
    window = world.add(Entity(id="window", type="window", label="the attic window", phrase="the attic window"))

    world.facts["child"] = child
    world.facts["ghost"] = ghost
    world.facts["rival"] = rival
    world.facts["lantern"] = lantern
    world.facts["window"] = window

    world.say("The old house was quiet, and the attic held one small, lonely ghost.")
    world.say("A rival ghost rattled the walls each night, and the little ghost hid from the noise.")
    world.say("A child came with a lantern and noticed the trembling in the dark.")
    return world


def narrate_flash(world: World) -> None:
    child = world.get("child")
    ghost = world.get("ghost")
    rival = world.get("opponent")
    lantern = world.get("lantern")
    child.memes["kindness"] = child.memes.get("kindness", 0) + 1
    child.memes["startle"] = child.memes.get("startle", 0) + 1
    world.say(
        f'The child lifted {lantern.label} and made a quick flash of light across the attic.'
    )
    world.say(
        f'"Please stop scaring each other," {child.pronoun()} said. '
        f'"There is room for both of you if you make a pact."'
    )
    ghost.memes["worry"] = ghost.memes.get("worry", 0) + 1
    rival.memes["grudge"] = rival.memes.get("grudge", 0) + 1
    world.say(
        f'"I only wanted the window," the shy ghost whispered.'
    )
    world.say(
        f'"And I wanted the hall," the rival ghost grumbled.'
    )
    propagate(world, narrate=True)


def narrate_pact(world: World) -> None:
    child = world.get("child")
    ghost = world.get("ghost")
    rival = world.get("opponent")
    window = world.get("window")
    world.say(
        f'The child pointed to {window.label} and said, "At dusk, {ghost.label} can have the window, '
        f'and later {rival.label} can have the moonlit hall."'
    )
    world.say(
        f'"That feels fair," {ghost.pronoun()} said softly.'
    )
    world.say(
        f'"A fair pact is better than a loud fight," {rival.pronoun()} muttered, though the noise was already fading.'
    )
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    ghost.memes["peace"] = ghost.memes.get("peace", 0) + 1
    rival.memes["peace"] = rival.memes.get("peace", 0) + 1
    propagate(world, narrate=True)


def narrate_ending(world: World) -> None:
    ghost = world.get("ghost")
    rival = world.get("opponent")
    world.para()
    world.say(
        "Soon the attic was peaceful. The shy ghost floated by the window without fear, "
        "and the rival ghost rested in the hall without banging the walls."
    )
    world.say(
        "The child smiled at the quiet house, and the lantern glowed like a tiny moon."
    )
    world.say(
        f"By the end, {ghost.label} and the rival ghost kept their pact, and the old house felt happy at last."
    )
    ghost.memes["joy"] = ghost.memes.get("joy", 0) + 1
    world.get("opponent").memes["joy"] = world.get("opponent").memes.get("joy", 0) + 1


def tell() -> World:
    world = setup_world()
    world.para()
    narrate_flash(world)
    world.para()
    narrate_pact(world)
    narrate_ending(world)
    world.facts["place"] = world.place
    return world


PLACE = Place(label="the old house", mood="quiet", echoes=True)


@dataclass
class StoryParams:
    place: str = "old house"
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a gentle ghost story for a young child that includes a flash of light, a pact, and an opponent.',
        'Tell a dialogue-heavy story about a shy ghost and a rival ghost making peace in an old house.',
        'Write a short happy-ending ghost story where a child helps two ghosts stop arguing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    ghost = world.get("ghost")
    rival = world.get("opponent")
    child = world.get("child")
    return [
        QAItem(
            question="Who helped the ghosts make peace?",
            answer="A child with a lantern helped them by speaking kindly and offering a fair pact.",
        ),
        QAItem(
            question="What was the opponent like?",
            answer=f"The opponent was a loud rival ghost who grumbled about wanting the moonlit hall.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with the shy ghost and the rival ghost keeping their pact and the house becoming peaceful.",
        ),
        QAItem(
            question=f"What did {child.id} do first in the attic?",
            answer="The child flashed a little lantern and asked the ghosts to stop scaring each other.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pact?",
            answer="A pact is a promise that two or more sides agree to keep, often to stop a fight or share something fairly.",
        ),
        QAItem(
            question="What does a flash of light do?",
            answer="A flash of light appears quickly and brightly, so it can help someone notice what is hidden in the dark.",
        ),
        QAItem(
            question="What is an opponent?",
            answer="An opponent is someone who is on the other side of a struggle, game, or argument.",
        ),
        QAItem(
            question="Can ghost stories have happy endings?",
            answer="Yes. A ghost story can end happily if the scary problem gets solved and everyone becomes safe or peaceful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
character(child). character(ghost). character(opponent).

light_flash(child) :- kindness(child).
kindness(child) :- child_kind.

worry(ghost) :- light_flash(child), fear(opponent).
grudge(opponent) :- loud(opponent).

pact_made :- kindness(child), worry(ghost), grudge(opponent).
happy_ending :- pact_made.

#show pact_made/0.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("child_kind"),
            asp.fact("fear", "opponent"),
            asp.fact("loud", "opponent"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show pact_made/0.\n#show happy_ending/0."))
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    ok = {"pact_made/0", "happy_ending/0"} <= atoms
    if ok:
        print("OK: ASP twin produces pact_made and happy_ending.")
        sample = generate(StoryParams())
        if "pact" not in sample.story.lower() or "happy" not in sample.story.lower():
            print("Verification failed: generated story does not reflect the domain.")
            return 1
        print("OK: generated story exercises the domain.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected atoms.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world: flash, pact, opponent, and a happy ending.")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell()
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
        print(asp_program("#show pact_made/0.\n#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode available; this world is deterministic and centered on a pact and happy ending.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(seed=base_seed)
        samples = [generate(params)]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
