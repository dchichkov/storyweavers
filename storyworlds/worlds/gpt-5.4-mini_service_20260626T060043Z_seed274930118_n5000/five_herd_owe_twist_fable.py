#!/usr/bin/env python3
"""
storyworlds/worlds/five_herd_owe_twist_fable.py
================================================

A small storyworld for a fable-style tale about five herd animals who owe a debt,
meet a twist, and end by paying it in a kinder way.

Premise seed:
- five herd animals
- they owe something
- a Twist changes the plan
- the style should feel like a fable

The world is deliberately tiny and constraint-driven:
- one small cast
- one debt
- one planned route
- one twist
- one moral ending image
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"goat", "sheep", "lamb", "cow", "horse"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: str


@dataclass
class Debt:
    thing: str
    amount: int
    due_to: str
    reason: str


@dataclass
class Twist:
    id: str
    label: str
    reveal: str
    helps: bool
    moral: str


@dataclass
class StoryParams:
    place: str
    herd_kind: str
    debt_kind: str
    twist: str
    name: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", afford="gather"),
    "barnyard": Setting(place="the barnyard", afford="gather"),
    "hill": Setting(place="the hill", afford="gather"),
}

HERDS = {
    "goats": "goats",
    "sheep": "sheep",
    "calves": "calves",
}

DEBTS = {
    "grain": Debt(thing="a sack of grain", amount=5, due_to="the miller", reason="they had borrowed it for supper"),
    "apples": Debt(thing="a basket of apples", amount=5, due_to="the gardener", reason="they had borrowed it for a feast"),
    "hay": Debt(thing="a bundle of hay", amount=5, due_to="the farmer", reason="they had borrowed it for their stall"),
}

TWISTS = {
    "rain": Twist(
        id="rain",
        label="a sudden rain",
        reveal="dark clouds rolled in and washed the path into little shining streams",
        helps=True,
        moral="A surprise can become a helper when friends stay calm.",
    ),
    "lostlamb": Twist(
        id="lostlamb",
        label="a lost lamb",
        reveal="a small lost lamb wandered out from the reeds and bleated softly",
        helps=True,
        moral="Kindness can turn a hard errand into a good deed.",
    ),
    "brokencart": Twist(
        id="brokencart",
        label="a broken cart",
        reveal="the cart wheel snapped with a loud crack, and the load tipped sideways",
        helps=False,
        moral="When a plan breaks, the steady ones make a new plan together.",
    ),
}

NAMES = ["Pip", "Milo", "Tess", "Nina", "Bram", "Luna", "Roo", "Mara"]
HELPERS = ["the fox", "the hedgehog", "the crane", "the old donkey"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def herd_word(herd_kind: str) -> str:
    return HERDS[herd_kind]


def introduce(world: World, herd_kind: str, name: str, helper: str) -> None:
    world.say(
        f"In {world.setting.place}, there lived a little herd of five {herd_word(herd_kind)} "
        f"led by {name}, who was the most careful of them all."
    )
    world.say(
        f"{name} listened when others rushed, and the herd trusted {helper} to know the old paths."
    )


def debt_tale(world: World, debt: Debt) -> None:
    world.say(
        f"One morning, the five friends remembered that they still owed {debt.due_to} {debt.thing} "
        f"because {debt.reason}."
    )
    world.say(
        f"Their little bell felt heavy, for a fable teaches that a promise left unpaid can make a peaceful day feel lopsided."
    )


def set_out(world: World, debt: Debt) -> None:
    world.say(
        f"So the herd set out across {world.setting.place}, carrying {debt.amount} smooth bundles to pay what they owed."
    )


def foretell_twist(world: World, twist: Twist) -> None:
    world.say(
        f"But before they reached the end of the path, {twist.reveal}."
    )


def react_to_twist(world: World, herd_kind: str, helper: str, twist: Twist, debt: Debt) -> None:
    if twist.id == "rain":
        world.say(
            f"The five {herd_word(herd_kind)} huddled under a thorn bush while {helper} showed them a dry bend in the road."
        )
        world.say(
            f"By waiting instead of hurrying, they kept the {debt.thing} dry and safe."
        )
    elif twist.id == "lostlamb":
        world.say(
            f"The herd stopped at once, because they knew a crying young one needed help before any errand could matter more."
        )
        world.say(
            f"They guided the lost lamb home first, and the thankful parent offered to carry half the load."
        )
    else:
        world.say(
            f"The herd looked at the broken cart, then at one another, and agreed that a broken wheel should not break their promise."
        )
        world.say(
            f"They tied the bundles in smaller packs and took turns carrying them, one careful step at a time."
        )


def repay(world: World, debt: Debt, twist: Twist) -> None:
    if twist.helps:
        world.say(
            f"When the path was safe again, the five friends reached {debt.due_to} and paid every bundle they owed."
        )
    else:
        world.say(
            f"At last, after the new plan, they reached {debt.due_to} and paid every bundle they owed."
        )


def ending(world: World, herd_kind: str, name: str, debt: Debt, twist: Twist) -> None:
    if twist.id == "lostlamb":
        world.say(
            f"{name} smiled, for the herd had gone out to repay a debt and come back having done a kinder thing too."
        )
    elif twist.id == "rain":
        world.say(
            f"The five {herd_word(herd_kind)} came home neat and proud, and not one bundle had been ruined by the storm."
        )
    else:
        world.say(
            f"The five {herd_word(herd_kind)} came home tired but honest, and their new smaller packs proved that teamwork can mend a broken day."
        )


def tell_story(world: World, params: StoryParams) -> World:
    debt = DEBTS[params.debt_kind]
    twist = TWISTS[params.twist]

    world.facts.update(
        place=params.place,
        herd_kind=params.herd_kind,
        debt_kind=params.debt_kind,
        twist=params.twist,
        name=params.name,
        helper=params.helper,
        debt=debt,
        twist_obj=twist,
    )

    introduce(world, params.herd_kind, params.name, params.helper)
    debt_tale(world, debt)
    world.para()
    set_out(world, debt)
    foretell_twist(world, twist)
    react_to_twist(world, params.herd_kind, params.helper, twist, debt)
    world.para()
    repay(world, debt, twist)
    ending(world, params.herd_kind, params.name, debt, twist)
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, herd_kind: str, debt_kind: str, twist: str) -> bool:
    return place in SETTINGS and herd_kind in HERDS and debt_kind in DEBTS and twist in TWISTS


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for herd_kind in HERDS:
            for debt_kind in DEBTS:
                for twist in TWISTS:
                    combos.append((place, herd_kind, debt_kind, twist))
    return combos


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(meadow). place(barnyard). place(hill).
herd(goats). herd(sheep). herd(calves).
debt(grain). debt(apples). debt(hay).
twist(rain). twist(lostlamb). twist(brokencart).

valid(P,H,D,T) :- place(P), herd(H), debt(D), twist(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for h in HERDS:
        lines.append(asp.fact("herd", h))
    for d in DEBTS:
        lines.append(asp.fact("debt", d))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
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


# ---------------------------------------------------------------------------
# Generation / QA
# ---------------------------------------------------------------------------
@dataclass
class StoryState:
    herd: Entity
    helper: Entity
    debt: Debt
    twist: Twist
    place: str


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fable about five {f['herd_kind']} who owe {f['debt'].thing} and meet {f['twist_obj'].label}.",
        f"Tell a short moral story where {f['name']} leads a herd across {f['place']} to repay a debt.",
        f"Write a child-friendly fable with a twist, a promise, and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    debt: Debt = f["debt"]
    twist: Twist = f["twist_obj"]
    return [
        QAItem(
            question=f"How many animals were in the herd?",
            answer="There were five animals in the herd.",
        ),
        QAItem(
            question=f"What did the herd owe {debt.due_to}?",
            answer=f"They owed {debt.due_to} {debt.thing}.",
        ),
        QAItem(
            question=f"What twist changed their plan on the road?",
            answer=f"The twist was {twist.label}. {twist.reveal.capitalize()}.",
        ),
        QAItem(
            question=f"How did the herd respond when the twist happened?",
            answer=(
                "They stayed together, chose a careful plan, and kept going until the debt was paid."
            ),
        ),
        QAItem(
            question=f"What lesson did the story end with?",
            answer=twist.moral,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a herd?",
            answer="A herd is a group of animals that live or move together.",
        ),
        QAItem(
            question="What does it mean to owe something?",
            answer="To owe something means you promised to give it back or pay it later.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise turn that changes what the characters expected.",
        ),
        QAItem(
            question="Why do fables often use animals?",
            answer="Fables use animals to tell simple lessons in a way children can imagine easily.",
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
        lines.append(f"  {e.id:10} ({e.type:8}) kind={e.kind}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def explain_rejection(place: str, herd_kind: str, debt_kind: str, twist: str) -> str:
    return (
        f"(No story: the requested combination is not valid. "
        f"Got place={place!r}, herd={herd_kind!r}, debt={debt_kind!r}, twist={twist!r}.)"
    )


# ---------------------------------------------------------------------------
# CLI contract
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about five, a herd, and what they owe.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--herd-kind", choices=HERDS)
    ap.add_argument("--debt-kind", choices=DEBTS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(SETTINGS))
    herd_kind = args.herd_kind or rng.choice(list(HERDS))
    debt_kind = args.debt_kind or rng.choice(list(DEBTS))
    twist = args.twist or rng.choice(list(TWISTS))
    if not valid_combo(place, herd_kind, debt_kind, twist):
        raise StoryError(explain_rejection(place, herd_kind, debt_kind, twist))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(
        place=place,
        herd_kind=herd_kind,
        debt_kind=debt_kind,
        twist=twist,
        name=name,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    herd = world.add(Entity(id="herd", kind="character", type=params.herd_kind, label="the herd"))
    helper = world.add(Entity(id="helper", kind="character", type="helper", label=params.helper))
    world.facts.update(herd=herd, helper_entity=helper)
    tell_story(world, params)
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


CURATED = [
    StoryParams(place="meadow", herd_kind="goats", debt_kind="grain", twist="rain", name="Pip", helper="the fox"),
    StoryParams(place="barnyard", herd_kind="sheep", debt_kind="apples", twist="lostlamb", name="Tess", helper="the hedgehog"),
    StoryParams(place="hill", herd_kind="calves", debt_kind="hay", twist="brokencart", name="Milo", helper="the old donkey"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:\n")
        for p, h, d, t in combos:
            print(f"  {p:9} {h:7} {d:7} {t}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.herd_kind} at {p.place} (debt: {p.debt_kind}, twist: {p.twist})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
