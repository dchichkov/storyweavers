#!/usr/bin/env python3
"""
A small folk-tale story world about a peg, kindness, and helping others.

The seed premise:
- A little peg lives in a cottage by the hearth.
- It wants to be useful, not merely sit in the basket.
- A gust, a task, or a missing helper creates trouble.
- Kindness turns the trouble into a small, happy change.

The simulation tracks:
- physical meters: stiffness, wear, hold, shine, damage, usefulness
- emotional memes: kindness, pride, worry, gratitude, belonging

The world is intentionally tiny and child-facing, but still state-driven:
what the peg does changes the world, and the ending proves it.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carries: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    detail: str
    weather: str = ""
    affords: set[str] = field(default_factory=set)


@dataclass
class PegKind:
    id: str
    label: str
    phrase: str
    strength: float
    can_hold: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    peg_kind: str
    trouble: str
    name: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


RULES: list = []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class Rule:
    name: str
    apply: callable


def _r_wear(world: World) -> list[str]:
    out: list[str] = []
    peg = world.entities.get("peg")
    if not peg:
        return out
    if peg.meters.get("wear", 0.0) >= THRESHOLD and ("wear",) not in world.fired:
        world.fired.add(("wear",))
        peg.meters["shine"] = max(0.0, peg.meters.get("shine", 0.0) - 0.5)
        out.append("The little peg grew worn from holding on so long.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    peg = world.entities.get("peg")
    helper = world.entities.get("helper")
    if not peg or not helper:
        return out
    if helper.memes.get("kindness", 0.0) >= THRESHOLD and peg.memes.get("worry", 0.0) >= THRESHOLD:
        sig = ("kindness",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        peg.memes["worry"] = 0.0
        peg.memes["gratitude"] = peg.memes.get("gratitude", 0.0) + 1.0
        helper.memes["bond"] = helper.memes.get("bond", 0.0) + 1.0
        out.append("Kind words made the worry soften like snow in the sun.")
    return out


RULES = [
    Rule("wear", _r_wear),
    Rule("kindness", _r_kindness),
]


def places() -> dict[str, Place]:
    return {
        "cottage": Place(
            name="the cottage",
            detail="a small cottage with a warm hearth and a basket by the wall",
            weather="windy",
            affords={"clothesline", "basket", "repair"},
        ),
        "yard": Place(
            name="the yard",
            detail="a little yard with a line between two posts",
            weather="breezy",
            affords={"clothesline", "repair"},
        ),
        "kitchen": Place(
            name="the kitchen",
            detail="a snug kitchen where bread cooled on the sill",
            weather="quiet",
            affords={"basket", "repair"},
        ),
    }


PEGS: dict[str, PegKind] = {
    "plain": PegKind(
        id="plain",
        label="wooden peg",
        phrase="a plain wooden peg",
        strength=1.0,
        can_hold={"cloth", "scarf"},
    ),
    "carved": PegKind(
        id="carved",
        label="carved peg",
        phrase="a carved peg with a little flower on its side",
        strength=1.2,
        can_hold={"cloth", "scarf", "shawl"},
    ),
    "stout": PegKind(
        id="stout",
        label="stout peg",
        phrase="a stout peg made for hard winds",
        strength=1.5,
        can_hold={"cloth", "shawl", "blanket"},
    ),
}

TROUBLES = {
    "wind": {
        "event": "a gust tugging at the washing",
        "risk": "the cloth might slip from the line",
        "mess": "scattered",
        "fix": "a kinder peg taking the load with help",
    },
    "snag": {
        "event": "a shawl snagging on a rough nail",
        "risk": "the cloth might tear",
        "mess": "scraped",
        "fix": "careful hands and a gentler peg",
    },
    "drop": {
        "event": "a bundle sliding from the basket",
        "risk": "the towels might fall into the dust",
        "mess": "dusty",
        "fix": "a peg used as a little latch",
    },
}

NAMES = ["Mara", "Nell", "Owen", "Pip", "Hugo", "Lina", "Tess", "Milo"]
PARENTS = ["mother", "father", "aunt", "uncle", "grandmother", "grandfather"]
TRAITS = ["small", "cheerful", "steady", "gentle", "brave"]


def reasonableness_gate(place: str, peg_kind: str, trouble: str) -> None:
    if place not in places():
        raise StoryError(f"Unknown place: {place}")
    if peg_kind not in PEGS:
        raise StoryError(f"Unknown peg kind: {peg_kind}")
    if trouble not in TROUBLES:
        raise StoryError(f"Unknown trouble: {trouble}")
    if trouble == "wind" and peg_kind == "plain" and place == "kitchen":
        raise StoryError("(No story: a plain peg in the kitchen has no real wind trouble to solve.)")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about a peg and kindness.")
    ap.add_argument("--place", choices=sorted(places()))
    ap.add_argument("--peg-kind", choices=sorted(PEGS))
    ap.add_argument("--trouble", choices=sorted(TROUBLES))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=PARENTS)
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
    place = args.place or rng.choice(sorted(places()))
    peg_kind = args.peg_kind or rng.choice(sorted(PEGS))
    trouble = args.trouble or rng.choice(sorted(TROUBLES))
    reasonableness_gate(place, peg_kind, trouble)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, peg_kind=peg_kind, trouble=trouble, name=name, parent=parent)


def tell(params: StoryParams) -> World:
    place = places()[params.place]
    peg_kind = PEGS[params.peg_kind]
    trouble = TROUBLES[params.trouble]
    world = World(place)
    world.facts.update(params=params, peg_kind=peg_kind, trouble=trouble)

    child = world.add(Entity(id="child", kind="character", type="child", label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    peg = world.add(Entity(id="peg", type=peg_kind.label, label=peg_kind.label, phrase=peg_kind.phrase))
    helper = world.add(Entity(id="helper", kind="character", type="neighbor", label="the kind neighbor"))

    # Opening
    world.say(f"Once in {place.name}, there lived a little peg named {params.name}.")
    world.say(f"It was {trouble['event']}, and the peg wanted to be useful instead of resting in the basket.")
    peg.memes["hope"] = 1.0
    peg.meters["stiffness"] = peg_kind.strength

    world.para()
    world.say(f"{place.detail.capitalize()}.")
    world.say(f"Each morning, the peg held up cloth on the line and felt proud when the wind could not budge it.")

    # Trouble
    world.para()
    world.say(f"But one day, {trouble['event']} made everyone look up at once.")
    peg.meters["wear"] = peg.meters.get("wear", 0.0) + 1.0
    peg.memes["worry"] = 1.0
    child.memes["concern"] = 1.0
    parent.memes["concern"] = 1.0
    propagate(world, narrate=True)

    # Kindness turn
    world.para()
    helper.memes["kindness"] = 1.0
    world.say(f"The kind neighbor saw the little peg and said, \"You have done enough already.\"")
    world.say(f"Then {params.parent} brought a softer cloth and a steadier hook, and the helper worked gently.")
    peg.meters["hold"] = peg.meters.get("hold", 0.0) + 1.0
    peg.memes["belonging"] = 1.0
    propagate(world, narrate=True)

    # Ending
    world.para()
    world.say(f"In the end, the peg stayed in its place, useful and loved, while the washing hung safe again.")
    world.say(f"The little peg shone a little dimmer than before, but its heart felt brighter for the kindness around it.")

    world.facts.update(
        child=child,
        parent=parent,
        peg=peg,
        helper=helper,
        ended_with_kindness=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    t = world.facts["trouble"]
    return [
        f"Write a short folk tale about a peg named {p.name} that learns kindness while facing {t['event']}.",
        f"Tell a gentle story in a cottage where a {p.peg_kind} peg helps with {t['event']} and ends in a kind way.",
        f"Write a simple story for a child about {p.name} the peg, a family, and a helpful act of kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    peg: Entity = world.facts["peg"]
    parent: Entity = world.facts["parent"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    trouble = world.facts["trouble"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about a little peg named {p.name} in {world.place.name}.",
        ),
        QAItem(
            question=f"What trouble happened to the peg?",
            answer=f"{trouble['event'].capitalize()} happened, and it made the peg worry about whether it could still help.",
        ),
        QAItem(
            question=f"Who showed kindness?",
            answer=f"The kind neighbor showed kindness, and {parent.label} helped too, so the peg did not have to carry the whole load alone.",
        ),
        QAItem(
            question=f"How did the peg feel at the end?",
            answer=f"It felt grateful and like it belonged, because its kindness was returned with gentle help.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The peg was still useful, but it was no longer worried. It stayed in place and the washing was safe again.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "peg": [
        QAItem(
            question="What is a peg used for?",
            answer="A peg is a small tool that holds cloth, paper, or other things in place so they do not slip away.",
        )
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        )
    ],
    "wind": [
        QAItem(
            question="What can wind do to things on a line?",
            answer="Wind can tug, flap, and sometimes pull light things loose if they are not held well.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [q for key in ("peg", "kindness", "wind") for q in WORLD_KNOWLEDGE[key]]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
peg(P) :- peg_kind(P).
kindness_event(E) :- trouble(E).
needs_help(P) :- peg(P), kindness_event(_).
resolved(P) :- needs_help(P), helper(h).
#show valid_story/4.
valid_story(Place, PegKind, Trouble, Kindness) :- place(Place), peg_kind(PegKind), trouble(Trouble), kindness(Kindness).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in places().values():
        lines.append(asp.fact("place", place.name.replace("the ", "").replace(" ", "_")))
    for pid in PEGS:
        lines.append(asp.fact("peg_kind", pid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    lines.append(asp.fact("kindness", "yes"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    stories = asp_valid_stories()
    py = [(p, k, t, "yes") for p in sorted(places()) for k in sorted(PEGS) for t in sorted(TROUBLES)]
    if set(stories) == set(py):
        print(f"OK: clingo gate matches Python registry ({len(stories)} combos).")
        return 0
    print("MISMATCH between clingo and Python registries.")
    print("only in clingo:", sorted(set(stories) - set(py)))
    print("only in python:", sorted(set(py) - set(stories)))
    return 1


CURATED = [
    StoryParams(place="cottage", peg_kind="plain", trouble="wind", name="Mara", parent="mother"),
    StoryParams(place="yard", peg_kind="carved", trouble="snag", name="Nell", parent="father"),
    StoryParams(place="kitchen", peg_kind="stout", trouble="drop", name="Owen", parent="grandmother"),
]


def build_sample(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story patterns:\n")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [build_sample(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            sample = build_sample(params)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.peg_kind} peg at {p.place} (trouble: {p.trouble})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
