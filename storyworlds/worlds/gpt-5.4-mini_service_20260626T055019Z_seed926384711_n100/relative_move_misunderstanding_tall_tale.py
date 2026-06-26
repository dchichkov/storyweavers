#!/usr/bin/env python3
"""
A tall-tale story world about a relative, a move, and a misunderstanding.

This script models a tiny family scene where a child asks a relative to move
something, the relative takes the request too literally or too grandly, and the
mix-up gets sorted out with a laugh and a careful fix.

The world is intentionally small:
- one child
- one relative
- one object to move
- one requested destination
- one misunderstanding that turns into a friendly resolution
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
# World data
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle", "grandpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False


@dataclass
class MoveTarget:
    label: str
    phrase: str
    weight: str
    size: str
    can_roll: bool
    can_lift: bool
    can_slide: bool


@dataclass
class MoveRequest:
    verb: str
    wording: str
    destination: str
    misunderstand: str
    tall_tale_twist: str
    result_image: str


@dataclass
class StoryParams:
    setting: str
    target: str
    request: str
    relative: str
    relative_type: str
    child_name: str
    child_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "yard": Setting(place="the yard", indoors=False),
    "barn": Setting(place="the barn", indoors=True),
    "kitchen": Setting(place="the kitchen", indoors=True),
    "porch": Setting(place="the porch", indoors=False),
}

TARGETS = {
    "chair": MoveTarget(
        label="chair",
        phrase="the little blue chair",
        weight="light",
        size="small",
        can_roll=False,
        can_lift=True,
        can_slide=True,
    ),
    "bench": MoveTarget(
        label="bench",
        phrase="the long wooden bench",
        weight="heavy",
        size="big",
        can_roll=False,
        can_lift=False,
        can_slide=True,
    ),
    "cart": MoveTarget(
        label="cart",
        phrase="the squeaky red cart",
        weight="heavy",
        size="big",
        can_roll=True,
        can_lift=False,
        can_slide=True,
    ),
    "haybale": MoveTarget(
        label="hay bale",
        phrase="the round hay bale",
        weight="very heavy",
        size="huge",
        can_roll=True,
        can_lift=False,
        can_slide=False,
    ),
    "stool": MoveTarget(
        label="stool",
        phrase="the tiny stool",
        weight="light",
        size="tiny",
        can_roll=False,
        can_lift=True,
        can_slide=True,
    ),
}

REQUESTS = {
    "closer": MoveRequest(
        verb="move",
        wording="move it closer",
        destination="near the door",
        misunderstand="the relative thought 'move' meant a grand parade across the whole place",
        tall_tale_twist="so {relative} heaved it in one shining swoop",
        result_image="the object ended up right where the child could reach it",
    ),
    "aside": MoveRequest(
        verb="move",
        wording="move it aside",
        destination="out of the way",
        misunderstand="the relative thought 'aside' meant 'a little to the left, then a little more, then a lot more'",
        tall_tale_twist="so {relative} scooted it with one mighty nudge",
        result_image="the path opened up like a smiling road",
    ),
    "away": MoveRequest(
        verb="move",
        wording="move it away",
        destination="far enough to make space",
        misunderstand="the relative thought 'away' meant 'all the way to the far fence'",
        tall_tale_twist="so {relative} marched it across the yard as if it were a toy block",
        result_image="the space cleared and the room felt as wide as a storybook field",
    ),
}

RELATIVES = {
    "aunt": ("aunt", "Aunt"),
    "uncle": ("uncle", "Uncle"),
    "grandma": ("grandma", "Grandma"),
    "grandpa": ("grandpa", "Grandpa"),
}

GIRL_NAMES = ["Mia", "Ruby", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Max", "Ben", "Theo", "Sam"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class World:
    setting: Setting
    child: Entity
    relative: Entity
    target: Entity
    request: MoveRequest
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    state: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(yard; barn; kitchen; porch).
relative(aunt; uncle; grandma; grandpa).
target(chair; bench; cart; haybale; stool).
request(closer; aside; away).

valid(S, T, R) :- setting(S), target(T), request(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TARGETS:
        lines.append(asp.fact("target", t))
    for r in REQUESTS:
        lines.append(asp.fact("request", r))
    for rel in RELATIVES:
        lines.append(asp.fact("relative", rel))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, r) for s in SETTINGS for t in TARGETS for r in REQUESTS]


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
# Story logic
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about a relative and a misunderstood move.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--request", choices=REQUESTS)
    ap.add_argument("--relative", choices=RELATIVES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    target = args.target or rng.choice(list(TARGETS))
    request = args.request or rng.choice(list(REQUESTS))
    relative = args.relative or rng.choice(list(RELATIVES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        setting=setting,
        target=target,
        request=request,
        relative=relative,
        relative_type=RELATIVES[relative][0],
        child_name=name,
        child_type=gender,
    )


def validate(params: StoryParams) -> None:
    if params.target == "haybale" and params.request == "closer" and params.setting == "kitchen":
        raise StoryError("A hay bale in a kitchen is too strange for this little tall-tale.")
    if params.target == "cart" and params.request == "away" and params.setting == "porch":
        raise StoryError("That cart would be too big a fuss for a porch-only story.")
    # Keep the domain flexible but sane.


def generate(params: StoryParams) -> StorySample:
    validate(params)
    setting = SETTINGS[params.setting]
    target_cfg = TARGETS[params.target]
    request = REQUESTS[params.request]

    child = Entity(id=params.child_name, kind="character", type=params.child_type)
    rel_word, rel_title = RELATIVES[params.relative]
    relative = Entity(id=rel_title, kind="character", type=rel_word)

    target = Entity(id=params.target, kind="thing", type=params.target, label=target_cfg.label, phrase=target_cfg.phrase)
    world = World(setting=setting, child=child, relative=relative, target=target, request=request)

    # Act 1
    world.say(f"{child.id} was in {setting.place}, where even the dust seemed to stand up straight and listen.")
    world.say(f"Nearby sat {target.phrase}, waiting like a sleepy turtle on a warm stone.")
    world.say(
        f"{child.id} asked {relative.pronoun('object')} {request.wording}, "
        f"because the way was just a little too crowded."
    )

    # Act 2: misunderstanding and tall-tale escalation
    world.para()
    world.say(
        f"But {relative.id} had the kind of ears that caught the wrong pebble on the road and called it a mountain."
    )
    world.say(
        f"{request.misunderstand.capitalize()}."
    )
    world.say(
        f"{request.tall_tale_twist.format(relative=relative.id)}; "
        f"{relative.id} moved with such bravado that the hens blinked twice."
    )
    world.state["misunderstanding"] = True
    world.state["move_done"] = True
    world.state["result"] = request.result_image

    # Act 3: correction and resolution
    world.para()
    world.say(
        f"{child.id} laughed and waved both hands. 'Not that far!' {child.id} said. "
        f"'I only meant {request.wording}, {request.destination}.'"
    )
    world.say(
        f"{relative.id} scratched {relative.pronoun('possessive')} head, grinned, and nudged the {target.label} back into place."
    )
    world.say(
        f"In the end, {request.result_image}, and the whole place felt as neat as a button on Sunday."
    )

    world.facts.update(
        setting=params.setting,
        target=params.target,
        request=params.request,
        relative=params.relative,
        child=params.child_name,
        child_type=params.child_type,
        misunderstanding=True,
        moved=True,
    )

    story = world.render()
    prompts = [
        f"Write a short tall-tale story for a child named {child.id} about a relative who misunderstands a move request.",
        f"Tell a gentle exaggerated story where {relative.id} turns a simple moving job into a grand stunt.",
        f"Write a child-friendly story about {child.id}, {relative.id}, and {target.phrase} in {setting.place}.",
    ]

    story_qa = [
        QAItem(
            question=f"Who asked for help moving the {target.label}?",
            answer=f"{child.id} asked {relative.id} for help.",
        ),
        QAItem(
            question=f"What did {relative.id} misunderstand about the request?",
            answer=f"{relative.id} misunderstood the word 'move' and thought it meant something much bigger than {request.wording}.",
        ),
        QAItem(
            question=f"What fixed the misunderstanding?",
            answer=f"{child.id} explained that {request.wording} only meant {request.destination}, and {relative.id} moved the {target.label} back the right way.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone hears or thinks the wrong meaning, even though no one meant any harm.",
        ),
        QAItem(
            question="What does it mean to move something?",
            answer="To move something means to change where it is, like sliding, carrying, or nudging it to a new place.",
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a story told in a very exaggerated way, where ordinary things sound enormous and funny.",
        ),
    ]

    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


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
    lines.append(f"setting: {world.setting.place}")
    lines.append(f"child: {world.child.id} ({world.child.type})")
    lines.append(f"relative: {world.relative.id} ({world.relative.type})")
    lines.append(f"target: {world.target.phrase}")
    lines.append(f"misunderstanding: {world.state.get('misunderstanding')}")
    lines.append(f"moved: {world.state.get('move_done')}")
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, t, r in combos[:50]:
            print(f"  {s:8} {t:8} {r:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("yard", "chair", "closer", "aunt", "aunt", "Mia", "girl"),
            StoryParams("porch", "cart", "aside", "uncle", "uncle", "Leo", "boy"),
            StoryParams("barn", "haybale", "away", "grandpa", "grandpa", "Nora", "girl"),
            StoryParams("kitchen", "stool", "aside", "grandma", "grandma", "Finn", "boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.child_name}: {p.relative} / {p.target} / {p.request}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
