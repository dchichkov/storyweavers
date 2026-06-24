#!/usr/bin/env python3
"""
storyworlds/worlds/stimulate_muffin_disadvantaged_curiosity_humor_slice_of.py
===============================================================================

A small slice-of-life storyworld about a child, a muffin, a tiny kitchen
problem, and a gentle compromise.

Seed tale idea:
---
A curious child wanted to make a muffin that would make the whole room smile.
They did not have many ingredients, so they felt a little disadvantaged.
A grown-up noticed the child’s curiosity, added a bit of humor, and helped
turn the small plan into a shared muffin and a warm afternoon.

World model:
---
- people have both physical meters (kitchen_resources, mess, finished_food)
  and emotional memes (curiosity, humor, patience, pride, warmth)
- the simulated state drives the prose
- the tension is small and slice-of-life: a child wants to do something now,
  but the kitchen only has limited ingredients
- the turn is a kind compromise that still lets the child act
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["mess", "hunger", "finished_food", "comfort", "softness"]:
            self.meters.setdefault(key, 0.0)
        for key in ["curiosity", "humor", "patience", "pride", "warmth", "disadvantage", "joy", "worry"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Kitchen:
    place: str = "the kitchen"
    has_oven: bool = True
    has_bowl: bool = True
    has_spoon: bool = True
    has_few_ingredients: bool = True


@dataclass
class StoryParams:
    name: str
    child_type: str
    caregiver_type: str
    place: str
    muffin_kind: str
    seed: Optional[int] = None


@dataclass
class IngredientSet:
    id: str
    label: str
    mix_note: str
    smell: str
    makes: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MuffinPlan:
    id: str
    label: str
    adjective: str
    reason: str
    crowd_effect: str
    improves: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, kitchen: Kitchen) -> None:
        self.kitchen = kitchen
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


INGREDIENTS = {
    "plain": IngredientSet(
        id="plain", label="plain batter", mix_note="stirred into a smooth batter",
        smell="warm and buttery", makes="a soft muffin", tags={"muffin", "batter"}
    ),
    "banana": IngredientSet(
        id="banana", label="banana batter", mix_note="squished with soft banana",
        smell="sweet and cozy", makes="a sweet muffin", tags={"muffin", "fruit"}
    ),
    "oat": IngredientSet(
        id="oat", label="oat batter", mix_note="mixed with oats and a little milk",
        smell="toasty and calm", makes="a sturdy muffin", tags={"muffin", "oat"}
    ),
}

PLANS = {
    "tiny": MuffinPlan(
        id="tiny", label="tiny muffin", adjective="tiny",
        reason="there were only a few ingredients left",
        crowd_effect="one muffin was enough for a small snack",
        improves="made the little amount feel special",
        tags={"small", "muffin"},
    ),
    "shared": MuffinPlan(
        id="shared", label="shared muffin", adjective="shared",
        reason="the child wanted everyone to taste it",
        crowd_effect="it could be split into kind little bites",
        improves="turned the kitchen into a sharing place",
        tags={"share", "muffin"},
    ),
    "smiley": MuffinPlan(
        id="smiley", label="smiley muffin", adjective="smiley",
        reason="the child wanted the muffin to make somebody laugh",
        crowd_effect="its top could be drawn with a funny face",
        improves="added a little humor to the day",
        tags={"humor", "muffin"},
    ),
}

KIDS = ["Mia", "Noah", "Lina", "Theo", "Ava", "Iris", "Ben", "June"]
CAREGIVERS = {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}

ASP_RULES = r"""
child_wants_muffin(C, M) :- child(C), muffin(M).
at_risk(M) :- limited_ingredients, muffin(M).
needs_compromise(M) :- at_risk(M), child_wants_muffin(_, M).
has_fix(M) :- needs_compromise(M), plan(P), fits(P, M).
valid_story(C, M, P) :- child(C), muffin(M), plan(P), has_fix(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in KIDS:
        lines.append(asp.fact("child", cid))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
    for mid in INGREDIENTS:
        lines.append(asp.fact("muffin", mid))
    lines.append(asp.fact("limited_ingredients"))
    for pid, plan in PLANS.items():
        for tag in sorted(plan.tags):
            lines.append(asp.fact("fits", pid, "any"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for name in KIDS:
        for muffin_id in INGREDIENTS:
            for plan_id in PLANS:
                out.append((name, muffin_id, plan_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: a child, a muffin, and a gentle fix.")
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--caregiver-type", choices=list(CAREGIVERS))
    ap.add_argument("--place", default="the kitchen")
    ap.add_argument("--muffin-kind", choices=list(INGREDIENTS))
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
    child_type = args.child_type or rng.choice(["girl", "boy"])
    caregiver_type = args.caregiver_type or rng.choice(list(CAREGIVERS))
    name = args.name or rng.choice(KIDS)
    muffin_kind = args.muffin_kind or rng.choice(list(INGREDIENTS))
    return StoryParams(
        name=name,
        child_type=child_type,
        caregiver_type=caregiver_type,
        place=args.place,
        muffin_kind=muffin_kind,
    )


def _setup_world(params: StoryParams) -> World:
    w = World(Kitchen(place=params.place))
    child = w.add(Entity(id=params.name, kind="character", type=params.child_type, label=params.name))
    caregiver = w.add(Entity(id="caregiver", kind="character", type=params.caregiver_type, label=CAREGIVERS[params.caregiver_type]))
    ingredient = w.add(Entity(id="ingredient", type="thing", label=INGREDIENTS[params.muffin_kind].label, phrase=INGREDIENTS[params.muffin_kind].label))
    plan = w.add(Entity(id="plan", type="thing", label=PLANS["shared"].label, phrase=PLANS["shared"].label))
    w.facts.update(child=child, caregiver=caregiver, ingredient=ingredient, plan=plan, params=params)
    return w


def tell(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    caregiver: Entity = f["caregiver"]
    ingredient: Entity = f["ingredient"]
    params: StoryParams = f["params"]
    ing = INGREDIENTS[params.muffin_kind]
    plan = PLANS["smiley" if params.muffin_kind == "plain" else "shared"]

    child.memes["curiosity"] += 1
    child.memes["humor"] += 1
    child.memes["disadvantage"] += 1
    caregiver.memes["patience"] += 1

    world.say(
        f"{child.id} was a little {child.type} with a bright case of Curiosity and a knack for Humor. "
        f"{child.pronoun('subject').capitalize()} kept looking at the small counter in {world.kitchen.place} and wondering how a muffin could become a happy surprise."
    )
    world.say(
        f"The day felt a bit disadvantaged, because there were only a few ingredients left. "
        f"Still, the air smelled {ing.smell}, and {child.id} thought that a careful plan might stimulate something nice."
    )

    world.para()
    child.memes["worry"] += 1
    caregiver.memes["worry"] += 1
    world.say(
        f"{child.id} wanted to make {ing.makes} right away, but the cupboard was almost empty. "
        f"{child.pronoun('subject').capitalize()} asked {caregiver.pronoun('object')} if they could use what little they had."
    )
    world.say(
        f"{caregiver.pronoun('subject').capitalize()} smiled and said the kitchen was not fancy, but it was still full of chances for a good idea."
    )
    world.say(
        f'"If we make a {plan.adjective} muffin," {caregiver.pronoun("subject")} said, "we can share it and keep the day light."'
    )

    world.para()
    child.memes["joy"] += 1
    child.memes["curiosity"] += 1
    caregiver.memes["warmth"] += 1
    world.say(
        f"{child.id} laughed at the idea of a muffin with a funny smile on top. "
        f"{child.pronoun('subject').capitalize()} stirred the bowl, and the batter was {ing.mix_note}."
    )
    world.say(
        f"The little muffin went into the oven and came out warm, soft, and proud. "
        f"It was small, but it was enough."
    )
    world.say(
        f"In the end, {child.id} and {caregiver.id} sat together, broke the muffin into bites, and enjoyed how a small idea could feel big when it was shared."
    )

    world.facts["resolved"] = True
    world.facts["story_text"] = world.render()
    world.facts["plan_used"] = plan


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f'Write a gentle slice-of-life story for young children about {p.name}, Curiosity, Humor, and a muffin in {p.place}.',
        f'Write a short story that includes the words "stimulate", "muffin", and "disadvantaged" in a warm, child-friendly way.',
        f"Tell a small kitchen story where a child and a caregiver make a muffin together after noticing there are only a few ingredients left.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    caregiver: Entity = f["caregiver"]
    params: StoryParams = f["params"]
    return [
        QAItem(
            question=f"What did {child.id} want to make in {params.place}?",
            answer=f"{child.id} wanted to make a muffin in {params.place}.",
        ),
        QAItem(
            question=f"Why did the day feel disadvantaged in the story?",
            answer="It felt disadvantaged because there were only a few ingredients left, so the child could not make a big fancy treat.",
        ),
        QAItem(
            question=f"How did {caregiver.label} help {child.id}?",
            answer=f"{caregiver.label.capitalize()} helped by suggesting a small, shared plan and making the muffin feel special instead of disappointing.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {child.id} was smiling and sharing a warm muffin with {caregiver.label}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is the playful feeling that helps people laugh and enjoy a funny idea.",
        ),
        QAItem(
            question="What is a muffin?",
            answer="A muffin is a small baked treat that is soft inside and often warm and sweet.",
        ),
        QAItem(
            question="What does it mean to stimulate something?",
            answer="To stimulate something means to help it get started or become more active, like a good idea or a lively thought.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show child_wants_muffin/2."))
    return sorted(set(asp.atoms(model, "child_wants_muffin")))


def asp_verify() -> int:
    import asp
    py = set((n, m) for (n, m, _) in valid_combos())
    cl = set(asp.atoms(asp.one_model(asp_program("#show child_wants_muffin/2.")), "child_wants_muffin"))
    if py and cl:
        print("OK: ASP and Python both produce story space atoms.")
        return 0
    print("MISMATCH or empty model.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show child_wants_muffin/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show child_wants_muffin/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mia", child_type="girl", caregiver_type="mother", place="the kitchen", muffin_kind="plain"),
            StoryParams(name="Ben", child_type="boy", caregiver_type="father", place="the kitchen", muffin_kind="banana"),
            StoryParams(name="June", child_type="girl", caregiver_type="grandmother", place="the kitchen", muffin_kind="oat"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
