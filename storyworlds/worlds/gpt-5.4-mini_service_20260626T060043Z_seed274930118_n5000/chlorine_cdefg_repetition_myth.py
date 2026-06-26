#!/usr/bin/env python3
"""
Standalone storyworld: a small mythic tale of repetition, chlorine, and cdefg.

A child-facing world about a river-temple, a keeper, a chorus, and a repeated
ritual that must be tuned until the water is safe and the myth can close cleanly.
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


def _round1(x: float) -> float:
    return round(x, 1)


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"keeper", "king", "priest", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"queen", "girl", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Chamber:
    name: str = "the river-temple"
    affords: set[str] = field(default_factory=lambda: {"chant", "ritual"})


@dataclass
class Rite:
    id: str
    name: str
    refrain: str
    line: str
    turns: int
    chlorine: float
    shadow_gain: float
    calm_gain: float
    keyword: str = "chlorine"
    chorus: str = "cdefg"


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    shields: set[str]


@dataclass
class StoryParams:
    rite: str
    name: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, chamber: Chamber) -> None:
        self.chamber = chamber
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def can_reach_clarity(world: World, keeper: Entity) -> bool:
    return keeper.meters.get("shadow", 0.0) < 1.0


def _apply_repetition(world: World, keeper: Entity, rite: Rite) -> list[str]:
    out: list[str] = []
    for turn in range(1, rite.turns + 1):
        sig = ("turn", rite.id, turn)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        keeper.meters["chlorine"] = _round1(keeper.meters.get("chlorine", 0.0) + rite.chlorine)
        keeper.meters["shadow"] = _round1(keeper.meters.get("shadow", 0.0) + rite.shadow_gain)
        keeper.meters["calm"] = _round1(keeper.meters.get("calm", 0.0) + rite.calm_gain)
        out.append(f"The chorus said {rite.refrain}.")
        out.append(f"The line returned: {rite.line}.")
        if keeper.meters["chlorine"] >= 3.0:
            out.append("The water shone too sharp, and the keeper frowned.")
            break
    return out


def _apply_charm(world: World, keeper: Entity, charm: Charm) -> list[str]:
    out: list[str] = []
    if keeper.meters.get("chlorine", 0.0) < 2.0:
        return out
    if ("charm", charm.id) in world.fired:
        return out
    world.fired.add(("charm", charm.id))
    keeper.meters["chlorine"] = _round1(max(0.0, keeper.meters.get("chlorine", 0.0) - 1.2))
    keeper.meters["shadow"] = _round1(max(0.0, keeper.meters.get("shadow", 0.0) - 0.8))
    out.append(f"Then {keeper.id} lifted {charm.phrase}, and the bright bite softened.")
    return out


def propagate(world: World, keeper: Entity, rite: Rite, charm: Charm) -> list[str]:
    out = _apply_repetition(world, keeper, rite)
    out.extend(_apply_charm(world, keeper, charm))
    return out


def tell(rite: Rite, name: str, role: str) -> World:
    world = World(Chamber())
    keeper = world.add(Entity(id=name, kind="character", type=role, label=name))
    charm = world.add(Entity(id="Charm", kind="thing", type="charm", label="charm", phrase="the river charm"))
    world.facts["keeper"] = keeper
    world.facts["charm"] = charm
    world.facts["rite"] = rite

    world.say(f"{keeper.id} was a small {keeper.type} in the river-temple, where old songs never ended.")
    world.say(f"Each dawn, {keeper.id} guarded the pool and sang the rite of {rite.chorus}.")
    world.say(f"The rite was meant to clear the water, but it also left a sharp chlorine taste.")
    world.para()
    world.say(f"One day, the chorus began again: {rite.refrain}.")
    world.say(f"Again the line came back: {rite.line}.")
    for s in propagate(world, keeper, rite, charm):
        world.say(s)
    world.para()
    if can_reach_clarity(world, keeper):
        world.say(
            f"At last the keeper breathed easy. The pool was calm, the chlorine was low, "
            f"and the same song sounded gentle instead of fierce."
        )
    else:
        world.say(
            f"But the water still bit with chlorine, so the keeper set the charm beside the pool "
            f"and waited for a wiser rhythm."
        )

    world.facts["resolved"] = can_reach_clarity(world, keeper)
    return world


RITES = {
    "cdefg": Rite(
        id="cdefg",
        name="the five-note rite",
        refrain="c, d, e, f, g",
        line="cdefg, cdefg, let the river hear",
        turns=4,
        chlorine=0.8,
        shadow_gain=0.5,
        calm_gain=0.7,
        keyword="chlorine",
        chorus="cdefg",
    ),
    "chorus": Rite(
        id="chorus",
        name="the long chorus",
        refrain="again and again",
        line="again and again, until the foam grows thin",
        turns=5,
        chlorine=0.7,
        shadow_gain=0.4,
        calm_gain=0.8,
        keyword="chlorine",
        chorus="cdefg",
    ),
}

CHAMBER = Chamber()

CURATED = [
    StoryParams(rite="cdefg", name="Ira", role="keeper"),
    StoryParams(rite="chorus", name="Nia", role="priestess"),
]

ASP_RULES = r"""
% A rite is repetitive when it has several turns.
repetitive(R) :- rite(R), turns(R,T), T >= 3.

% Chlorine is dangerous when repetition rises too high.
too_much_chlorine(K) :- keeper(K), chlorine(K,C), C >= 3.

% The charm can soften chlorine only after chlorine has built up.
can_soften(K) :- keeper(K), chlorine(K,C), C >= 2.

resolved_story(R) :- repetitive(R), rite(R), has_charm, not too_much_chlorine_after_charm.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("chamber", "river_temple"))
    for rid, rite in RITES.items():
        lines.append(asp.fact("rite", rid))
        lines.append(asp.fact("refrain", rid, rite.refrain))
        lines.append(asp.fact("line", rid, rite.line))
        lines.append(asp.fact("turns", rid, rite.turns))
    lines.append(asp.fact("charm", "river_charm"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic repetition world with chlorine and cdefg.")
    ap.add_argument("--rite", choices=sorted(RITES))
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["keeper", "priestess", "priest", "queen", "king"])
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
    rite = args.rite or rng.choice(list(RITES))
    name = args.name or rng.choice(["Ira", "Nia", "Sera", "Toma", "Mira", "Ari"])
    role = args.role or rng.choice(["keeper", "priestess", "priest"])
    return StoryParams(rite=rite, name=name, role=role, seed=None)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    rite = f["rite"]
    keeper = f["keeper"]
    return [
        f'Write a short myth for children about "chlorine" and the repeated song "{rite.chorus}".',
        f"Tell a gentle legend where {keeper.id} must repeat {rite.refrain} until the water grows calm.",
        f"Write a small mythic story that includes the strange word cdefg and ends with a safer rhythm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    keeper = world.facts["keeper"]
    rite = world.facts["rite"]
    chlorine = keeper.meters.get("chlorine", 0.0)
    resolved = world.facts.get("resolved", False)
    qa = [
        QAItem(
            question=f"Who guarded the river-temple in this story?",
            answer=f"{keeper.id} did. {keeper.id} was the keeper who watched the pool and sang the old rite.",
        ),
        QAItem(
            question=f"What repeated chant mattered most in the myth?",
            answer=f"The chant was {rite.refrain}, and the line returned as {rite.line}.",
        ),
        QAItem(
            question=f"Why did the keeper worry about the water?",
            answer=f"The repeated rite raised chlorine in the pool, and too much chlorine made the water feel sharp.",
        ),
    ]
    if resolved:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=(
                    f"The keeper used the river charm after the repeated song had built up the chlorine. "
                    f"That softened the bite, and the pool became calm again."
                ),
            )
        )
    else:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=(
                    f"The keeper had to pause, because the chlorine was still high and the story needed a gentler rhythm."
                ),
            )
        )
    qa.append(
        QAItem(
            question="How strong was the chlorine near the end?",
            answer=f"It reached about {chlorine:.1f}, enough to make the keeper careful.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chlorine?",
            answer=(
                "Chlorine is a chemical that can help clean water, but too much of it can smell sharp "
                "and feel harsh."
            ),
        ),
        QAItem(
            question="What does repetition mean?",
            answer=(
                "Repetition means doing or saying the same thing again and again."
            ),
        ),
        QAItem(
            question="What is a chorus in a song?",
            answer=(
                "A chorus is the part of a song that comes back more than once, so people can remember it."
            ),
        ),
        QAItem(
            question="What kind of thing is cdefg?",
            answer=(
                "cdefg looks like a simple run of music notes, the kind that can sound like a little repeated spell."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        if meters:
            lines.append(f"{e.id}: {meters}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(RITES[params.rite], params.name, params.role)
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


def asp_verify() -> int:
    import asp
    prog = asp_program("#show repetitive/1.")
    model = asp.one_model(prog)
    reps = sorted(set(asp.atoms(model, "repetitive")))
    py = [(rid,) for rid, rite in RITES.items() if rite.turns >= 3]
    if set(reps) == set(py):
        print(f"OK: ASP and Python agree on repetition ({len(py)} rites).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP:", reps)
    print("  PY :", py)
    return 1


def asp_available() -> list[tuple[str]]:
    import asp
    model = asp.one_model(asp_program("#show repetitive/1."))
    return sorted(set(asp.atoms(model, "repetitive")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show repetitive/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            reps = asp_available()
        except Exception as exc:
            raise SystemExit(str(exc))
        print(f"{len(reps)} repetitive rites:")
        for (rid,) in reps:
            print(f"  {rid}")
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: rite={p.rite}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
