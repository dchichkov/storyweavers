#!/usr/bin/env python3
"""
storyworlds/worlds/ambush_prison_reggae_attic_ladder_reconciliation_fable.py
=============================================================================

A tiny fable-world about an ambush in an attic ladder, a mistaken little prison,
and a reggae beat that helps two quarrelsome friends reconcile.

Seed tale:
---
At the top of an attic ladder, a mouse and a rat quarreled over a drum.
The rat hid the drum in a little prison cage and thought that would settle it.
Then a cat slipped in for an ambush from the rafters, and both friends had to
run. In the end, the rat opened the cage, the mouse forgave the trick, and the
two tapped a reggae rhythm together until the fear faded.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    locked: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"rat", "boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Params and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str = "attic_ladder"
    conflict: str = "ambush"
    prize: str = "drum"
    hero: str = "Mina"
    rival: str = "Rufus"
    seed: Optional[int] = None


SETTING_LABELS = {
    "attic_ladder": "the attic ladder",
}

PRIZES = {
    "drum": {
        "label": "drum",
        "phrase": "a little wooden drum",
    }
}

# One domain, one small set of plausible tale shapes.
VALID_COMBOS = [("attic_ladder", "ambush", "drum")]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(attic_ladder).
conflict(ambush).
prize(drum).

valid(S,C,P) :- setting(S), conflict(C), prize(P), S = attic_ladder, C = ambush, P = drum.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "attic_ladder"),
            asp.fact("conflict", "ambush"),
            asp.fact("prize", "drum"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(VALID_COMBOS)
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches VALID_COMBOS() ({len(py)} combo).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if (params.setting, params.conflict, params.prize) not in VALID_COMBOS:
        raise StoryError("This little fable only has one honest path: ambush, prison, and reggae in the attic ladder.")
    w = World()
    hero = w.add(Entity(id=params.hero, kind="character", type="mouse", label=params.hero))
    rival = w.add(Entity(id=params.rival, kind="character", type="rat", label=params.rival))
    drum = w.add(Entity(id="drum", type="drum", label="drum", phrase=PRIZES["drum"]["phrase"], owner=hero.id))
    prison = w.add(Entity(id="prison", type="cage", label="prison cage", phrase="a tiny prison cage", locked=True, owner=rival.id))
    cat = w.add(Entity(id="cat", kind="character", type="cat", label="the cat"))
    w.facts.update(hero=hero, rival=rival, drum=drum, prison=prison, cat=cat, setting=params.setting)
    return w


def tell_story(w: World) -> None:
    hero: Entity = w.facts["hero"]
    rival: Entity = w.facts["rival"]
    drum: Entity = w.facts["drum"]
    prison: Entity = w.facts["prison"]
    cat: Entity = w.facts["cat"]

    hero.memes["hope"] = 1
    rival.memes["pride"] = 1
    drum.meters["safe"] = 1

    w.say(
        f"At the top of {SETTING_LABELS['attic_ladder']}, {hero.id} and {rival.id} found "
        f"{drum.phrase}, and both wanted to be the first to play it."
    )
    w.say(
        f"{rival.id} grew proud and shut {drum.pronoun('object')} inside {prison.phrase}, saying it would keep the tune from slipping away."
    )

    w.para()
    hero.memes["hurt"] = 1
    rival.memes["guilt"] = 1
    w.say(
        f"Then a shadow moved over {SETTING_LABELS['attic_ladder']}; {cat.label} made an ambush from the rafters, and the ladder felt suddenly narrow."
    )
    w.say(
        f"{hero.id} trembled, because the little prison had not made anyone kinder, only more afraid."
    )

    w.para()
    hero.memes["fear"] = 1
    rival.memes["regret"] = 1
    prison.locked = False
    drum.owner = hero.id
    hero.memes["forgiveness"] = 1
    rival.memes["reconciliation"] = 1
    hero.memes["reconciliation"] = 1
    hero.memes["joy"] = 1
    rival.memes["joy"] = 1
    w.say(
        f"{rival.id} saw the fear in {hero.id}'s face and opened the prison cage at once. "
        f'"I was wrong," {rival.id} said. "A prison cannot mend a broken feeling."'
    )
    w.say(
        f"To make peace, {hero.id} tapped a soft reggae rhythm on the rung, and {rival.id} answered on the drum. "
        f"The cat lost interest, the ambush passed, and the two friends climbed down together, lighter than before."
    )

    w.facts["resolved"] = True
    w.facts["ending_image"] = "the two friends climbing down the attic ladder together while the reggae beat echoed softly"


def generation_prompts() -> list[str]:
    return [
        'Write a short fable for a young child that includes an ambush, a prison, and reggae in an attic ladder.',
        'Tell a gentle story where a mouse and a rat argue over a drum, then find reconciliation after a scare from above.',
        'Write a simple moral tale about a mistake, a shared rhythm, and two friends making peace on an attic ladder.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    rival: Entity = world.facts["rival"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little mouse, and {rival.id}, a rat, who met on the attic ladder.",
        ),
        QAItem(
            question="What did the rat put the drum in?",
            answer="The rat put the drum in a little prison cage, which was a bad way to solve the argument.",
        ),
        QAItem(
            question="What happened when the cat made an ambush?",
            answer="The surprise made both friends scared, and it showed them they needed to stop fighting and work together.",
        ),
        QAItem(
            question="How did they make peace at the end?",
            answer="They reconciled by opening the prison cage and playing a reggae rhythm together on the drum.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ambush?",
            answer="An ambush is a surprise attack or surprise scare that happens when someone is not expecting it.",
        ),
        QAItem(
            question="What is a prison?",
            answer="A prison is a place where someone is kept locked up and cannot leave freely.",
        ),
        QAItem(
            question="What is reggae?",
            answer="Reggae is a style of music with a steady rhythm that can sound warm and bouncy.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable about ambush, prison, reggae, and reconciliation in an attic ladder.")
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
    return StoryParams(seed=args.seed if args.seed is not None else None)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.locked:
            bits.append("locked=True")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible combo:\n  attic_ladder  ambush   drum")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams())]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

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
