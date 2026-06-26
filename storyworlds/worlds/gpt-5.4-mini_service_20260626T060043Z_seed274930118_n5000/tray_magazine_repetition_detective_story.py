#!/usr/bin/env python3
"""
A small storyworld about a careful detective, a tray, a magazine, and a clue
that keeps showing up in the same place.

Premise:
- A child detective notices that a magazine is always left on a tray.
- Repetition matters: the same clue appears again and again, which helps the
  detective figure out who keeps borrowing the tray.

The world is intentionally tiny: one place, one object pair, one repeating habit,
one gentle reveal.
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

SETTING_NAME = "the reading nook"
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    touched: bool = False
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        if self.kind == "character":
            return "she" if self.id in {"Mina"} else "he"
        return "it"

    def possessive(self) -> str:
        if self.kind == "character":
            return "her" if self.id in {"Mina"} else "his"
        return "its"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
    seed: Optional[int] = None
    name: str = "Mina"
    partner: str = "Milo"
    detective_item: str = "tray"
    clue_item: str = "magazine"


NAMES = ["Mina", "Ruby", "Nina", "Theo", "Milo", "Iris"]
PARTNERS = ["Milo", "June", "Owen", "Tara", "Eli", "Nora"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny detective storyworld about repetition, a tray, and a magazine."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--partner", choices=PARTNERS)
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
    name = args.name or rng.choice(NAMES)
    partner = args.partner or rng.choice([p for p in PARTNERS if p != name] or PARTNERS)
    return StoryParams(seed=args.seed, name=name, partner=partner)


def _repeat_clue(world: World, detective: Entity, tray: Entity, magazine: Entity) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0.0) + 1
    tray.meters["present"] = tray.meters.get("present", 0.0) + 1
    magazine.meters["present"] = magazine.meters.get("present", 0.0) + 1

    if ("repeat", 1) not in world.fired:
        world.fired.add(("repeat", 1))
        detective.memes["certainty"] = detective.memes.get("certainty", 0.0) + 1
        tray.touched = True
        magazine.hidden = True
        world.say(
            f"{detective.id} noticed the same tray in the reading nook again, "
            f"and the same magazine on it again."
        )
    if ("repeat", 2) not in world.fired:
        world.fired.add(("repeat", 2))
        detective.memes["pattern"] = detective.memes.get("pattern", 0.0) + 1
        world.say(
            f"Then the detective saw the same little bend in the magazine page again, "
            f"which meant this was not an accident."
        )


def _solve_case(world: World, detective: Entity, partner: Entity, tray: Entity, magazine: Entity) -> None:
    if ("solve", 1) in world.fired:
        return
    world.fired.add(("solve", 1))
    magazine.hidden = False
    magazine.found = True
    detective.meters["insight"] = detective.meters.get("insight", 0.0) + 1
    partner.memes["surprise"] = partner.memes.get("surprise", 0.0) + 1
    world.say(
        f"{detective.id} looked under the tray and found why the clue kept repeating: "
        f"{partner.id} kept using {tray.possessive()} flat top to hold the magazine while reading."
    )
    world.say(
        f"{partner.id} smiled and said {tray.possessive().capitalize()} spot was the easiest place to remember it, "
        f"so the mystery was really a habit, not a thief."
    )
    world.say(
        f"After that, the magazine went back to the shelf, and the tray stayed empty and tidy."
    )


def tell(params: StoryParams) -> World:
    world = World()
    detective = world.add(Entity(id=params.name, kind="character", label="the detective"))
    partner = world.add(Entity(id=params.partner, kind="character", label="the helper"))
    tray = world.add(Entity(id="tray", kind="thing", label="tray", phrase="a small wooden tray"))
    magazine = world.add(Entity(id="magazine", kind="thing", label="magazine", phrase="a glossy magazine"))

    world.say(
        f"{detective.id} was a little detective who loved looking for patterns in quiet places."
    )
    world.say(
        f"In {SETTING_NAME}, {detective.id} kept seeing {tray.phrase} and {magazine.phrase} together."
    )

    world.para()
    _repeat_clue(world, detective, tray, magazine)
    world.say(
        f"{detective.id} thought the repetition meant something important, because clues that repeat "
        f"usually want to be noticed."
    )
    world.para()
    _solve_case(world, detective, partner, tray, magazine)

    world.facts.update(
        detective=detective,
        partner=partner,
        tray=tray,
        magazine=magazine,
        repeated=True,
        solved=True,
    )
    return world


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("thing", "tray"),
            asp.fact("thing", "magazine"),
            asp.fact("can_repeat", "tray"),
            asp.fact("can_repeat", "magazine"),
            asp.fact("supports", "tray", "magazine"),
            asp.fact("detective_theme", "pattern"),
        ]
    )


ASP_RULES = r"""
repeat_clue(X) :- can_repeat(X).
mystery(X,Y) :- repeat_clue(X), supports(X,Y).
solved :- mystery(tray, magazine).
#show solved/0.
#show mystery/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name or not params.partner:
        raise StoryError("A detective story needs both a detective and a helper.")
    if params.name == params.partner:
        raise StoryError("The detective and the helper must be different people.")


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(params)
    story = world.render()
    prompts = [
        f"Write a short detective story for a child about a tray and a magazine that keep showing up together.",
        f"Tell a gentle mystery where {params.name} notices repetition and solves it with {params.partner}.",
        f"Write a simple story in which the repeated clue is a magazine on a tray.",
    ]
    story_qa = [
        QAItem(
            question="What kept showing up again and again in the reading nook?",
            answer="The tray and the magazine kept showing up together, and that repetition was the clue.",
        ),
        QAItem(
            question=f"Why did {params.name} think the clue mattered?",
            answer="Because the same tray and magazine appeared more than once, and repeated clues usually point to a pattern.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer="The detective looked under the tray and learned the magazine was not lost; it was just being left there as a habit.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a tray used for?",
            answer="A tray is a flat object used to carry or hold things together.",
        ),
        QAItem(
            question="What is a magazine?",
            answer="A magazine is a thin book of pictures and articles to read.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means something happens or appears again and again.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.touched:
            bits.append("touched=True")
        if e.hidden:
            bits.append("hidden=True")
        if e.found:
            bits.append("found=True")
        lines.append(f"  {e.id:9} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    try:
        from storyworlds import asp  # type: ignore
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show solved/0. #show mystery/2."))
    atoms = set((sym.name, tuple(arg.name if arg.type != 1 else arg.string for arg in sym.arguments)) for sym in model)
    expected = {("solved", ()), ("mystery", ("tray", "magazine"))}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH: ASP model did not match expectation.")
    print(atoms)
    return 1


CURATED = [
    StoryParams(name="Mina", partner="Milo", seed=1),
    StoryParams(name="Theo", partner="Nora", seed=2),
    StoryParams(name="Ruby", partner="Eli", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show solved/0. #show mystery/2."))
        return
    if args.asp:
        print(asp_program("#show solved/0. #show mystery/2."))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < max(args.n, 1) and i < max(50, args.n * 20):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
