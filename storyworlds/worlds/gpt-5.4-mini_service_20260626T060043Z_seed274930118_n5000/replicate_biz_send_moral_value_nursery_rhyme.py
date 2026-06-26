#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/replicate_biz_send_moral_value_nursery_rhyme.py
=============================================================================================================

A tiny storyworld in a nursery-rhyme voice.

Seed tale:
---
A little child helps at a small biz by sending little parcels. The child wants
to keep the shiny sticker sheet and send the parcel too, but the grown-up says
that sharing and keeping a promise matter more than the sticker sheet. The child
chooses the honest, helpful way, and the biz sends the parcel on time.

World idea:
- A child at a tiny family biz
- A parcel or token that can be kept or sent
- A moral value that matters in the choice: sharing, honesty, or helping
- A short turn from temptation to kind resolution
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
# Core world data
# ---------------------------------------------------------------------------

MORAL_VALUES = {"sharing", "honesty", "helpfulness"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    bearer: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Biz:
    name: str
    place: str
    small: bool = True
    sends: set[str] = field(default_factory=set)


@dataclass
class Parcel:
    label: str
    phrase: str
    size: str
    sendable: bool = True
    moral_value: str = "sharing"


@dataclass
class StoryParams:
    place: str
    parcel: str
    moral_value: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    biz: Biz
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

    def copy(self) -> "World":
        import copy as _copy
        return World(
            biz=_copy.deepcopy(self.biz),
            entities=_copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=_copy.deepcopy(self.facts),
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

BIZES = {
    "bakery": Biz(name="the bakery", place="the bakery", sends={"parcel", "bun"}),
    "postshop": Biz(name="the post shop", place="the post shop", sends={"parcel", "letter"}),
    "flowerstall": Biz(name="the flower stall", place="the flower stall", sends={"parcel", "flowers"}),
}

PARCELS = {
    "parcel": Parcel(
        label="parcel",
        phrase="a little parcel with a bright string",
        size="small",
        sendable=True,
        moral_value="helpfulness",
    ),
    "giftbox": Parcel(
        label="gift box",
        phrase="a little gift box with a red bow",
        size="small",
        sendable=True,
        moral_value="sharing",
    ),
    "letter": Parcel(
        label="letter",
        phrase="a neat little letter in an envelope",
        size="small",
        sendable=True,
        moral_value="honesty",
    ),
}

GENDERS = {"girl", "boy"}
GIRL_NAMES = ["Mia", "Lily", "Nina", "Ruby", "Tess", "Maya"]
BOY_NAMES = ["Ben", "Toby", "Finn", "Leo", "Noah", "Max"]
HELPERS = ["mother", "father"]

# A child-friendly moral cue, with a little rhyme flavor.
MORAL_LINES = {
    "sharing": "Share what you can, and your heart feels light.",
    "honesty": "Tell the true thing, and your day stays bright.",
    "helpfulness": "Help with your hands, and the work goes right.",
}

ASP_RULES = r"""
valid(Place, Parcel, Moral) :- biz(Place), parcel(Parcel), moral(Moral),
                               sends(Place, Parcel), matches(Parcel, Moral).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, biz in BIZES.items():
        lines.append(asp.fact("biz", key))
        lines.append(asp.fact("place_name", key, biz.place))
        for item in sorted(biz.sends):
            lines.append(asp.fact("sends", key, item))
    for key, p in PARCELS.items():
        lines.append(asp.fact("parcel", key))
        lines.append(asp.fact("size", key, p.size))
        lines.append(asp.fact("matches", key, p.moral_value))
    for moral in sorted(MORAL_VALUES):
        lines.append(asp.fact("moral", moral))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, biz in BIZES.items():
        for parcel, p in PARCELS.items():
            if parcel in biz.sends:
                combos.append((place, parcel, p.moral_value))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny nursery-rhyme storyworld about a child, a biz, and a moral choice."
    )
    ap.add_argument("--place", choices=BIZES)
    ap.add_argument("--parcel", choices=PARCELS)
    ap.add_argument("--moral-value", choices=sorted(MORAL_VALUES))
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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


def explain_rejection(place: str, parcel: str, moral_value: str) -> str:
    return (
        f"(No story: {BIZES[place].place} does not send {parcel} for the moral value "
        f"{moral_value!r} in this tiny rhyme-world.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place and args.parcel and args.moral_value:
        if (args.place, args.parcel, PARCELS[args.parcel].moral_value) not in combos:
            raise StoryError(explain_rejection(args.place, args.parcel, args.moral_value))

    candidates = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.parcel is None or c[1] == args.parcel)
        and (args.moral_value is None or c[2] == args.moral_value)
    ]
    if not candidates:
        raise StoryError("(No valid combination matches the given options.)")

    place, parcel, moral = rng.choice(sorted(candidates))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(
        place=place,
        parcel=parcel,
        moral_value=moral,
        name=name,
        gender=gender,
        helper=helper,
    )


def _setup_world(params: StoryParams) -> World:
    biz = BIZES[params.place]
    world = World(biz=biz)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    parcel = PARCELS[params.parcel]
    thing = world.add(Entity(
        id="parcel",
        kind="thing",
        type=parcel.label,
        label=parcel.label,
        phrase=parcel.phrase,
        owner=child.id,
        bearer=child.id,
        location=biz.place,
    ))
    world.facts.update(
        child=child,
        helper=helper,
        parcel_entity=thing,
        parcel_cfg=parcel,
        moral_value=params.moral_value,
        params=params,
    )
    return world


def _opening(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    parcel: Entity = f["parcel_entity"]
    moral_value: str = f["moral_value"]
    world.say(f"{child.id} was a little {child.type} who came to {world.biz.place}.")
    world.say(
        f"There, {child.pronoun('subject')} saw {parcel.phrase}, and the day felt as light as song."
    )
    world.say(
        f"{child.id} loved the {moral_value} way of work, and the tiny biz hummed along."
    )


def _turn(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    parcel: Entity = f["parcel_entity"]
    moral_value: str = f["moral_value"]

    world.para()
    world.say(
        f"But {child.id} reached for the parcel and paused, for a shiny sticker sheet sat near."
    )
    if moral_value == "sharing":
        world.say(
            f'{child.id} said, "I want to keep the stickers, and send the parcel too!"'
        )
        helper.memes["concern"] = helper.memes.get("concern", 0.0) + 1
        world.say(
            f"{helper.pronoun('possessive').capitalize()} helper shook {helper.pronoun('possessive')} head gently."
        )
        world.say(' "A kept sticker is small, but a shared hand is kind," {0} said.'.format(helper.id))
    elif moral_value == "honesty":
        world.say(
            f'{child.id} whispered, "I nearly mixed up the label. I should tell the true thing."'
        )
        helper.memes["concern"] = helper.memes.get("concern", 0.0) + 1
        world.say(
            f"{helper.id} nodded and said, \"Truth is a bright little bell; it rings the right way home.\""
        )
    else:
        world.say(
            f'{child.id} wanted to play first and send later, though the biz had promised the parcel at noon.'
        )
        helper.memes["concern"] = helper.memes.get("concern", 0.0) + 1
        world.say(
            f"{helper.id} reminded {child.id} that a helping hand should not delay a waiting friend."
        )
    parcel.memes["at_risk"] = 1.0


def _resolution(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    parcel: Entity = f["parcel_entity"]
    moral_value: str = f["moral_value"]

    world.para()
    world.say(
        f"Then {child.id} breathed in, did the kind thing, and chose the careful way."
    )
    if moral_value == "sharing":
        world.say(f"{child.id} shared the sticker sheet with {helper.id}, and sent the parcel at once.")
        world.say(f"The little biz rang a bell: ding-dong, ding-dong, the parcel sailed on.")
    elif moral_value == "honesty":
        world.say(f"{child.id} told the true label, and {helper.id} fixed it in a blink.")
        world.say(f"The parcel went clean and neat, like a moonbeam on a string.")
    else:
        world.say(f"{child.id} helped stack the parcels, then sent the waiting one with care.")
        world.say(f"The little biz smiled wide, for the promise was kept right there.")
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1
    parcel.meters["sent"] = 1.0
    world.say(f"{child.id} felt warm and proud, and {world.biz.place} was bright again.")
    world.say(MORAL_LINES[moral_value])


def tell_story(params: StoryParams) -> World:
    world = _setup_world(params)
    _opening(world)
    _turn(world)
    _resolution(world)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    parcel: Entity = f["parcel_entity"]
    moral_value: str = f["moral_value"]
    params: StoryParams = f["params"]

    return [
        QAItem(
            question=f"Who is the story about at {world.biz.place}?",
            answer=f"The story is about {child.id}, a little {child.type} who visits {world.biz.place}.",
        ),
        QAItem(
            question=f"What did {child.id} want to do with the {parcel.label}?",
            answer=f"{child.id} wanted to send the {parcel.label} and keep the day kind and careful.",
        ),
        QAItem(
            question=f"Why did the helper speak up about the choice?",
            answer=(
                f"The helper spoke up because the story's moral value was {moral_value}, "
                f"and the right way mattered more than keeping the shiny thing."
            ),
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=(
                f"{child.id} chose the kind, careful way, sent the {parcel.label}, "
                f"and felt proud at {world.biz.place}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    moral_value = world.facts["moral_value"]
    return [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else use or have a little of what you have, so both people feel cared for.",
        ),
        QAItem(
            question="What is honesty?",
            answer="Honesty means telling the true thing and not pretending something else is real.",
        ),
        QAItem(
            question="What is helpfulness?",
            answer="Helpfulness means doing a useful thing for someone else, like carrying, fixing, or sending something on time.",
        ),
        QAItem(
            question="What kind of feeling does a kind choice give?",
            answer="A kind choice often gives a warm, glad feeling, because it helps someone and keeps the peace.",
        ),
    ] + [
        QAItem(
            question=f"Which moral value did this story use?",
            answer=f"This story used {moral_value}.",
        )
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    parcel: Entity = f["parcel_entity"]
    moral_value: str = f["moral_value"]
    return [
        f'Write a nursery-rhyme style story about {child.id}, a tiny biz, and a parcel that should be sent.',
        f'Write a gentle story that includes the word "replicate" and the moral value "{moral_value}".',
        f'Write a child-friendly rhyme where a helper and a child at the biz choose the kind way to send {parcel.label}.',
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


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
    StoryParams(place="bakery", parcel="parcel", moral_value="helpfulness", name="Mia", gender="girl", helper="mother"),
    StoryParams(place="postshop", parcel="letter", moral_value="honesty", name="Leo", gender="boy", helper="father"),
    StoryParams(place="flowerstall", parcel="giftbox", moral_value="sharing", name="Ruby", gender="girl", helper="mother"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible stories:\n")
        for place, parcel, moral in triples:
            print(f"  {place:12} {parcel:10} {moral}")
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
            header = f"### {p.name}: {p.parcel} at {p.place} ({p.moral_value})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
