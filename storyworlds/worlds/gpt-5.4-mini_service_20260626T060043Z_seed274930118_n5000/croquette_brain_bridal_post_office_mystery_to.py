#!/usr/bin/env python3
"""
storyworlds/worlds/croquette_brain_bridal_post_office_mystery_to.py
===================================================================

A small fable-style story world: a mystery in a post office.
Seed words: croquette, brain, bridal.
Premise: a kind letter-carrier and a brainy helper solve a gentle puzzle
before a bridal parcel is lost for good.

The story is modeled as a tiny simulation with meters and memes:
- physical meters track crumbs, tidiness, and whether the missing parcel is found
- emotional memes track worry, curiosity, pride, and relief

The mystery is always solvable and always ends with a clear turn:
a clue is noticed, the right suspect is checked, and the lost thing is restored.

Fable note:
- the voice should feel like a small moral tale
- the ending should prove the world changed
- the language stays concrete and child-facing
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("crumbs", "tidy", "found", "stolen"):
            self.meters.setdefault(k, 0.0)
        for k in ("worry", "curiosity", "pride", "relief", "hunger"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Character(Entity):
    kind: str = "character"


@dataclass
class StoryParams:
    detective: str
    helper: str
    culprit: str
    lost_item: str
    seed: Optional[int] = None


@dataclass
class Mystery:
    place: str = "the post office"
    clue_word: str = "croquette"
    brain_word: str = "brain"
    bridal_word: str = "bridal"


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        clone = World(self.params)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


MYSTERY = Mystery()

DETECTIVES = {
    "owl": ("Oona", "owl"),
    "mouse": ("Milo", "mouse"),
    "fox": ("Fern", "fox"),
}
HELPERS = {
    "sparrow": ("Sib", "sparrow"),
    "cat": ("Cleo", "cat"),
    "turtle": ("Tess", "turtle"),
}
CULPRITS = {
    "pigeon": ("Pip", "pigeon"),
    "squirrel": ("Squeak", "squirrel"),
    "badger": ("Bram", "badger"),
}
LOST_ITEMS = {
    "bridal ribbon": ("ribbon", "a bridal ribbon tied with a white bow"),
    "bridal card": ("card", "a bridal card with golden flowers"),
    "parcel seal": ("seal", "a bridal parcel seal stamped with hearts"),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for d in DETECTIVES:
        for h in HELPERS:
            for c in CULPRITS:
                for i in LOST_ITEMS:
                    if c != "badger" or i != "parcel seal":
                        out.append((d, h, c, i))
    return out


ASP_RULES = r"""
detective(D) :- detective(D).
helper(H) :- helper(H).
culprit(C) :- culprit(C).
item(I) :- item(I).

solvable(D,H,C,I) :- detective(D), helper(H), culprit(C), item(I),
                     clue_matches(C,I), not impossible(C,I).

impossible(C,I) :- culprit(C), item(I), C = badger, I != parcel_seal.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for d in DETECTIVES:
        lines.append(asp.fact("detective", d))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for c in CULPRITS:
        lines.append(asp.fact("culprit", c))
    for i in LOST_ITEMS:
        lines.append(asp.fact("item", i.replace(" ", "_")))
    # simple clue relation: each culprit leaves a clue only for their own style
    lines.append(asp.fact("clue_matches", "pigeon", "bridal_ribbon"))
    lines.append(asp.fact("clue_matches", "squirrel", "bridal_card"))
    lines.append(asp.fact("clue_matches", "badger", "parcel_seal"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show solvable/4."))
    return sorted(set(asp.atoms(model, "solvable")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style mystery in a post office.")
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--lost-item", choices=LOST_ITEMS, dest="lost_item")
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
    combos = valid_combos()
    if args.detective:
        combos = [c for c in combos if c[0] == args.detective]
    if args.helper:
        combos = [c for c in combos if c[1] == args.helper]
    if args.culprit:
        combos = [c for c in combos if c[2] == args.culprit]
    if args.lost_item:
        combos = [c for c in combos if c[3] == args.lost_item]
    if not combos:
        raise StoryError("No valid mystery matches the given options.")
    d, h, c, i = rng.choice(sorted(combos))
    return StoryParams(
        detective=d,
        helper=h,
        culprit=c,
        lost_item=i,
    )


def intro_name(key: str, registry: dict[str, tuple[str, str]]) -> str:
    return registry[key][0]


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    detective_name, detective_type = DETECTIVES[params.detective]
    helper_name, helper_type = HELPERS[params.helper]
    culprit_name, culprit_type = CULPRITS[params.culprit]
    lost_label, lost_phrase = LOST_ITEMS[params.lost_item]

    detective = world.add(Character(id=detective_name, type=detective_type, label=detective_name))
    helper = world.add(Character(id=helper_name, type=helper_type, label=helper_name))
    culprit = world.add(Character(id=culprit_name, type=culprit_type, label=culprit_name))
    item = world.add(Entity(id=lost_label, type="parcel", label=lost_label, phrase=lost_phrase))

    # setup
    detective.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    culprit.memes["hunger"] += 1

    world.say(
        f"In the post office, {detective_name} the {detective_type} kept a tidy desk and a steady heart."
    )
    world.say(
        f"Beside {detective_name}, {helper_name} the {helper_type} liked to think hard, like a little {MYSTERY.brain_word} with feathers and whiskers."
    )
    world.say(
        f"That morning, a bridal parcel should have gone out, but {lost_phrase} had vanished."
    )
    world.say(
        f"On the floor lay a single {MYSTERY.clue_word} crumb, warm and neat as if it had just dropped from a snack."
    )

    world.para()

    # tension / clue gathering
    detective.memes["worry"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"{detective_name} worried that the bride would wait too long, so {detective_name} and {helper_name} followed the crumb trail between the mail sacks."
    )
    world.say(
        f"{helper_name} noticed that the crumbs stopped under the bright window, where {culprit_name} the {culprit_type} stood with a guilty-looking beak or paws."
    )

    # clue logic
    if params.culprit == "pigeon":
        clue = "a little flour on the beak"
    elif params.culprit == "squirrel":
        clue = "a torn ribbon stuck to the tail"
    else:
        clue = "a sticky seal in the fur"
    world.say(
        f"{helper_name} thought with care and said, \"The clue is {clue}; it points to {culprit_name}.\""
    )

    # turn / resolution
    culprit.memes["worry"] += 1
    culprit.meters["stolen"] += 1
    culprit.meters["found"] = 1
    item.meters["found"] = 1
    detective.memes["pride"] += 1
    detective.memes["relief"] += 1
    helper.memes["pride"] += 1
    helper.memes["relief"] += 1

    world.para()
    world.say(
        f"{culprit_name} confessed, because a full belly had made {culprit_name} careless and the honest clue had found its way home."
    )
    world.say(
        f"{culprit_name} returned {lost_phrase}, and the bridal parcel was sent on its way at once."
    )
    world.say(
        f"By sunset, the post office was tidy again, and {detective_name} smiled to see that a small brain, a patient friend, and a true clue can mend a big worry."
    )
    world.say(
        "The fable's lesson was simple: when trouble arrives, a calm mind and a kind helper often solve what anger cannot."
    )

    world.facts.update(
        detective=detective,
        helper=helper,
        culprit=culprit,
        item=item,
        detective_key=params.detective,
        helper_key=params.helper,
        culprit_key=params.culprit,
        item_key=params.lost_item,
        solved=True,
        clue=clue,
    )

    prompts = [
        "Write a short fable about a mystery in a post office where a missing bridal parcel is found by following a croquette crumb.",
        f"Tell a gentle story about {detective_name} and {helper_name} using their brains to solve a mystery without being unkind.",
        "Write a child-friendly post office mystery that ends with the lost thing returned and a small moral about patience.",
    ]

    story_qa = [
        QAItem(
            question="Where did the mystery happen?",
            answer="It happened in the post office, among the mail sacks, windows, and tidy desks.",
        ),
        QAItem(
            question="What was missing?",
            answer=f"The missing thing was {lost_phrase}, a bridal parcel that should have gone out with the mail.",
        ),
        QAItem(
            question="Who solved the mystery?",
            answer=f"{detective_name} solved it with help from {helper_name}, who noticed the clue and thought carefully about it.",
        ),
        QAItem(
            question="Why did the culprit give the parcel back?",
            answer="The culprit gave it back because the clue made the truth plain, and the story chose honesty over hiding.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a croquette?",
            answer="A croquette is a small fried food, often round or oval, with a crisp outside and a soft middle.",
        ),
        QAItem(
            question="What does it mean to have a brain?",
            answer="A brain is the part of the body that helps a creature think, remember, and solve problems.",
        ),
        QAItem(
            question="What does bridal mean?",
            answer="Bridal means something belongs to a bride or is made for a wedding.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts.get('solved', False)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("owl", "sparrow", "pigeon", "bridal ribbon"),
    StoryParams("mouse", "cat", "squirrel", "bridal card"),
    StoryParams("fox", "turtle", "badger", "parcel seal"),
]


def show_asp_program() -> str:
    return asp_program("#show solvable/4.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(show_asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show solvable/4."))
        print(sorted(set(asp.atoms(model, "solvable"))))
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
            header = f"### {p.detective} / {p.helper} / {p.culprit} / {p.lost_item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
