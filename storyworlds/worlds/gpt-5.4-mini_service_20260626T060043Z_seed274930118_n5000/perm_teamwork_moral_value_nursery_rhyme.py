#!/usr/bin/env python3
"""
A small standalone storyworld: a nursery-rhyme style tale about a child who
wants a perm, learns patience, and succeeds through teamwork.

The world model tracks a few physical meters and emotional memes:
- hair meters: curl, neat, wet
- meme meters: want, worry, teamwork, pride, calm
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Salon:
    place: str = "the sunny salon"
    shimmer: str = "soft"
    helper_name: str = "Nina"
    helper_type: str = "stylist"


@dataclass
class ChildPlan:
    wanted_style: str = "a perm"
    turn_phrase: str = "take turns and help"
    moral: str = "teamwork makes the little job feel light"


class World:
    def __init__(self, salon: Salon) -> None:
        self.salon = salon
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
        clone = World(self.salon)
        clone.entities = {k: Entity(**{
            **vars(v),
            "meters": dict(v.meters),
            "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Parameters / content registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    place: str = "salon"
    seed: Optional[int] = None


NAMES = {
    "girl": ["Lily", "Mia", "Nora", "Ruby", "Zoe", "Ivy"],
    "boy": ["Theo", "Milo", "Finn", "Owen", "Eli", "Noah"],
}
HELPERS = [
    ("Nina", "stylist"),
    ("Mara", "stylist"),
    ("Bess", "helper"),
]
SALONS = {
    "salon": Salon(place="the sunny salon", shimmer="soft", helper_name="Nina", helper_type="stylist"),
}


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def introduce(world: World, child: Entity, helper: Entity, plan: ChildPlan) -> None:
    world.say(
        f"Little {child.id} trotted in with a bright old grin, "
        f"for {child.pronoun('subject')} wanted {plan.wanted_style} within."
    )
    world.say(
        f"{helper.id} was there with comb and spray, "
        f"ready to help in a careful way."
    )


def setup_world(params: StoryParams) -> World:
    salon = SALONS["salon"]
    world = World(salon)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"curl": 0.0, "wet": 0.0, "neat": 1.0},
        memes={"want": 1.0, "worry": 0.0, "teamwork": 0.0, "pride": 0.0, "calm": 0.0},
    ))
    helper = world.add(Entity(
        id=salon.helper_name,
        kind="character",
        type="woman" if params.gender == "girl" else "woman",
        label=salon.helper_name,
        meters={"skill": 1.0},
        memes={"teamwork": 1.0, "calm": 1.0},
    ))
    brush = world.add(Entity(
        id="brush",
        type="tool",
        label="brush",
        phrase="a shiny brush",
        owner=helper.id,
    ))
    spray = world.add(Entity(
        id="spray",
        type="tool",
        label="spray bottle",
        phrase="a misty spray bottle",
        owner=helper.id,
    ))
    plan = ChildPlan()
    world.facts.update(child=child, helper=helper, brush=brush, spray=spray, plan=plan)
    return world


def predict_perm(world: World, child: Entity) -> dict[str, bool]:
    sim = world.copy()
    do_perm(sim, sim.get(child.id), narrate=False)
    c = sim.get(child.id)
    return {"curly": c.meters.get("curl", 0.0) >= 1.0, "neat": c.meters.get("neat", 0.0) >= 1.0}


def do_perm(world: World, child: Entity, narrate: bool = True) -> None:
    if "perm_done" in world.fired:
        return
    world.fired.add("perm_done")
    child.meters["wet"] = child.meters.get("wet", 0.0) + 1.0
    child.meters["curl"] = child.meters.get("curl", 0.0) + 1.0
    child.meters["neat"] = child.meters.get("neat", 0.0) + 1.0
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1.0
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1.0
    if narrate:
        world.say(f"The curls came in tiny rings, and {child.id} held still as a stone.")


def teamwork_turn(world: World, child: Entity, helper: Entity, plan: ChildPlan) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    world.say(
        f"At first {child.id} squirmed and sighed, "
        f"for waiting did not feel so spry."
    )
    world.say(
        f"Then {helper.id} said, 'We can {plan.turn_phrase}, "
        f"one hand for me and one for thee.'"
    )
    child.memes["teamwork"] = child.memes.get("teamwork", 0.0) + 1.0
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0.0) + 1.0


def resolve(world: World, child: Entity, helper: Entity, plan: ChildPlan) -> None:
    do_perm(world, child)
    world.say(
        f"{helper.id} and {child.id} worked in tune; "
        f"the brush went dance, the spray went swoon."
    )
    world.say(
        f"By and by the mirror showed {child.id} beaming bright, "
        f"with shiny little curls all neat and light."
    )
    world.say(
        f"And so the child learned, in a happy glow: "
        f"{plan.moral}."
    )


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    child = world.get(params.name)
    helper = world.get(world.salon.helper_name)
    plan = world.facts["plan"]

    introduce(world, child, helper, plan)
    world.para()
    world.say("The salon was soft, and the days were sweet, with mirrors tall and a tiny seat.")
    world.say("The child wanted a perm, all curl and charm, but first came patience, gentle and warm.")
    teamwork_turn(world, child, helper, plan)
    world.para()
    resolve(world, child, helper, plan)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    return [
        f"Write a short nursery-rhyme story about {child.id} wanting a perm and learning teamwork.",
        f"Tell a gentle story where {helper.id} helps {child.id} stay calm while getting a perm.",
        f"Write a rhyme about a child, a salon, and the moral that teamwork makes things easier.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    plan: ChildPlan = world.facts["plan"]
    return [
        QAItem(
            question=f"What did {child.id} want at the salon?",
            answer=f"{child.id} wanted {plan.wanted_style}, with bouncy little curls.",
        ),
        QAItem(
            question=f"Who helped {child.id} in the story?",
            answer=f"{helper.id} helped {child.id}, and they worked together kindly.",
        ),
        QAItem(
            question="What did the child learn by the end?",
            answer=f"The child learned that {plan.moral}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} smiling in the mirror, happy with neat curls and a calm heart.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a perm?",
            answer="A perm is a hair treatment that makes hair curl into ringlets or waves.",
        ),
        QAItem(
            question="Why do people work together in a salon?",
            answer="People work together so one person can hold, brush, spray, and care for the hair safely and neatly.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help one another and share the job so it goes better.",
        ),
        QAItem(
            question="Why is patience a good moral?",
            answer="Patience is a good moral because waiting calmly can help people do careful work without making mistakes.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"{e.id} ({e.type}): " + ", ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts provide: child/1, helper/1, and plan/1-like predicates.

needs_perm(C) :- child(C).
teamwork_story(C,H) :- child(C), helper(H).
good_end(C) :- needs_perm(C), teamwork_story(C,H).

#show needs_perm/1.
#show teamwork_story/2.
#show good_end/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("child", "child"),
        asp.fact("helper", "helper"),
        asp.fact("perm", "perm"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_model_atoms() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show needs_perm/1.\n#show teamwork_story/2.\n#show good_end/1."))
    return [(s.name, tuple(a.name if a.type != a.type.Number else a.number for a in s.arguments)) for s in model]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show needs_perm/1.\n#show teamwork_story/2.\n#show good_end/1."))
    atoms = {(sym.name, tuple(arg.name if arg.type != arg.type.Number else arg.number for arg in sym.arguments)) for sym in model}
    want = {("needs_perm", ("child",)), ("teamwork_story", ("child", "helper")), ("good_end", ("child",))}
    if atoms == want:
        print("OK: ASP twin matches the Python story shape.")
        return 0
    print("MISMATCH between ASP and Python story shape.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(want))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: a child, a perm, teamwork, and a moral.")
    ap.add_argument("--name", choices=sum(NAMES.values(), []))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=[h for h, _ in HELPERS])
    ap.add_argument("--place", choices=SALONS.keys(), default="salon")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES[gender])
    helper = args.helper or rng.choice([h for h, _ in HELPERS])
    return StoryParams(name=name, gender=gender, helper=helper, place=args.place)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(name="Lily", gender="girl", helper="Nina", place="salon"),
    StoryParams(name="Theo", gender="boy", helper="Mara", place="salon"),
    StoryParams(name="Mia", gender="girl", helper="Bess", place="salon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show needs_perm/1.\n#show teamwork_story/2.\n#show good_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show needs_perm/1.\n#show teamwork_story/2.\n#show good_end/1."))
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
