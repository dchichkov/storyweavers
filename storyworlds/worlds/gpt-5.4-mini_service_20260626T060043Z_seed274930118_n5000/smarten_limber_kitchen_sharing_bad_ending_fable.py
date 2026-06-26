#!/usr/bin/env python3
"""
storyworlds/worlds/smarten_limber_kitchen_sharing_bad_ending_fable.py
======================================================================

A small fable-like story world set in a kitchen, built from the seed words
"smarten" and "limber", with sharing as the central action and a bad ending
that still feels complete and causal.

Premise:
- Two small kitchen creatures want the same snack.
- One is limber enough to reach the high shelf.
- One tries to smarten the plan into a fair share.

Turn:
- The pair attempt to share a treat in the kitchen.
- Greed, haste, or poor judgment can spoil the sharing.

Ending:
- The bad ending must be earned by world state, not by a frozen moral.
- The final image should show what was lost and what changed.

The story style is fable-like: simple, concrete, and lightly moralizing.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "squirrel", "bird", "fox", "rabbit"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Kitchen:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=lambda: {"share", "reach", "snack"})


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    size: str
    shareable: bool = True
    high_shelf: bool = False


@dataclass
class Helper:
    id: str
    label: str
    covers: set[str] = field(default_factory=set)
    boosts: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""
    plural: bool = False


class World:
    def __init__(self, kitchen: Kitchen) -> None:
        self.kitchen = kitchen
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.kitchen)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_hunger(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.memes.get("hunger", 0.0) >= THRESHOLD and ("hunger", e.id) not in world.fired:
            world.fired.add(("hunger", e.id))
            out.append(f"{e.id} felt hungry enough to notice every crumb.")
    return out


def _r_spill(world: World) -> list[str]:
    out = []
    snack = world.entities.get("snack")
    if not snack:
        return out
    if snack.meters.get("spilled", 0.0) < THRESHOLD:
        return out
    if ("spill", snack.id) in world.fired:
        return out
    world.fired.add(("spill", snack.id))
    out.append(f"The snack was spilled across the kitchen floor.")
    return out


CAUSAL_RULES = [
    _r_hunger,
    _r_spill,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    name_a: str
    type_a: str
    name_b: str
    type_b: str
    snack: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Kitchen(),
}

SNACKS = {
    "berry_tart": Snack(
        id="berry_tart",
        label="berry tart",
        phrase="a sweet berry tart",
        size="small",
        shareable=True,
        high_shelf=True,
    ),
    "honey_bun": Snack(
        id="honey_bun",
        label="honey bun",
        phrase="a sticky honey bun",
        size="small",
        shareable=True,
        high_shelf=False,
    ),
    "apple_pie": Snack(
        id="apple_pie",
        label="apple pie",
        phrase="a round apple pie",
        size="medium",
        shareable=True,
        high_shelf=True,
    ),
}

HELPERS = {
    "stool": Helper(
        id="stool",
        label="a little stool",
        covers={"reach"},
        boosts={"reach"},
        prep="push the little stool under the shelf",
        tail="used the stool to reach the bowl",
    ),
    "ladder": Helper(
        id="ladder",
        label="a narrow ladder",
        covers={"reach"},
        boosts={"reach"},
        prep="set up the narrow ladder",
        tail="climbed carefully and reached the bowl",
    ),
}

A_TYPES = ["mouse", "squirrel", "bird"]
B_TYPES = ["mouse", "squirrel", "bird"]
NAMES = ["Smarten", "Limber", "Pip", "Moss", "Nettle", "Wren"]
CURATED = [
    StoryParams("Smarten", "mouse", "Limber", "squirrel", "berry_tart", "stool"),
    StoryParams("Smarten", "bird", "Limber", "mouse", "apple_pie", "ladder"),
]


ASP_RULES = r"""
shareable(S) :- snack(S).
at_risk(S) :- snack(S), high_shelf(S).
can_reach(H) :- helper(H), boosts(H, reach).
valid_story(S, H) :- shareable(S), can_reach(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if snack.shareable:
            lines.append(asp.fact("shareable", sid))
        if snack.high_shelf:
            lines.append(asp.fact("high_shelf", sid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for b in sorted(helper.boosts):
            lines.append(asp.fact("boosts", hid, b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, snack in SNACKS.items():
        for hid in HELPERS:
            if snack.shareable and snack.high_shelf:
                combos.append((sid, hid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like kitchen story world about sharing and a bad ending.")
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name-a")
    ap.add_argument("--type-a", choices=A_TYPES)
    ap.add_argument("--name-b")
    ap.add_argument("--type-b", choices=B_TYPES)
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
    combos = valid_combos()
    if args.snack and args.helper:
        if (args.snack, args.helper) not in combos:
            raise StoryError("That snack and helper do not make a plausible kitchen story here.")
    if not combos:
        raise StoryError("No valid story combinations exist.")
    snack, helper = rng.choice(combos)
    sa = args.name_a or rng.choice(NAMES)
    sb = args.name_b or rng.choice([n for n in NAMES if n != sa])
    ta = args.type_a or rng.choice(A_TYPES)
    tb = args.type_b or rng.choice(B_TYPES)
    return StoryParams(sa, ta, sb, tb, snack, helper)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS["kitchen"])
    snack = world.add(Entity(id="snack", type="snack", label=SNACKS[params.snack].label, phrase=SNACKS[params.snack].phrase))
    helper = HELPERS[params.helper]
    a = world.add(Entity(id=params.name_a, kind="character", type=params.type_a))
    b = world.add(Entity(id=params.name_b, kind="character", type=params.type_b))

    a.memes["hunger"] = 1.0
    b.memes["hunger"] = 1.0
    a.memes["desire"] = 1.0
    b.memes["desire"] = 1.0

    world.say(f"In the kitchen, {a.id} and {b.id} both wanted {snack.phrase}.")
    world.say(f"{a.id} tried to smarten the plan and asked for a fair share, while {b.id} stayed limber and ready to help.")

    world.para()
    world.say(f"{b.id} could {helper.prep} and {helper.tail}.")
    world.say(f"They agreed to share the snack, but each wanted the bigger half.")

    # conflict escalates
    a.memes["greed"] = 1.0
    b.memes["greed"] = 1.0
    world.para()
    world.say(f"{a.id} reached first, then {b.id} snatched at the plate.")
    snack.meters["spilled"] = 1.0
    propagate(world, narrate=True)

    # bad ending
    world.para()
    world.say(f"The tart slid off the edge and broke on the floor.")
    world.say(f"At last, {a.id} and {b.id} had to sit with empty paws and a mess to clean.")
    world.say("The kitchen learned a small fable: a shared treat is sweetest when both sides are kind.")
    world.facts.update(a=a, b=b, snack=snack, helper=helper, params=params)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a short fable set in a kitchen about {p.name_a} and {p.name_b} sharing a {p.snack}.',
        f"Tell a child-friendly story where {p.name_b} is limber enough to help, but the snack still ends badly.",
        f'Write a simple moral tale using the words "smarten" and "limber" in a kitchen scene about sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    snack: Entity = f["snack"]
    a: Entity = f["a"]
    b: Entity = f["b"]
    helper: Helper = f["helper"]
    return [
        QAItem(
            question=f"Who wanted to share the {snack.label} in the kitchen?",
            answer=f"{a.id} and {b.id} both wanted to share the {snack.label} in the kitchen.",
        ),
        QAItem(
            question=f"Why was {b.id} useful in the story?",
            answer=f"{b.id} was limber, so {b.id} could help reach and handle the snack with the {helper.label}.",
        ),
        QAItem(
            question=f"What went wrong with the sharing?",
            answer=f"They both wanted the bigger half, so the snack spilled and the sharing ended badly.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{a.id} and {b.id} ended up with an empty kitchen treat and a mess to clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people or creatures use or enjoy something with you.",
        ),
        QAItem(
            question="What does limber mean?",
            answer="Limber means flexible and quick to move, like a body that can bend and reach easily.",
        ),
        QAItem(
            question="What does smarten up mean?",
            answer="To smarten up means to start thinking more carefully and make a wiser choice.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals, that teaches a lesson.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible snack/helper combos:\n")
        for snack, helper in combos:
            print(f"  {snack:12} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name_a} and {p.name_b}: {p.snack} in the kitchen"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
