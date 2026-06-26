#!/usr/bin/env python3
"""
storyworlds/worlds/toad_mask_alien_transformation_bad_ending_bedtime.py
======================================================================

A tiny bedtime storyworld about a child, a strange mask, and a troubling
transformation. The premise is simple: at bedtime, a child finds a toad-like
alien mask and wants to wear it just a little longer. The tension comes from
sleepiness, the mask's clingy fit, and a parent who can see that bedtime is not
the time for pretend. The turn is that the mask is not merely a costume; it
changes what the child feels like. The ending is intentionally bad: the child
does not get to switch back before sleep, and the final image leaves the
transformation unresolved.

This world is child-facing, concrete, and state-driven. It uses physical meters
and emotional memes to decide what happens, rather than swapping nouns inside a
fixed paragraph.
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

BEDTIME_THRESHOLD = 1.0
TRANSFORM_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the bedroom"
    bedtime: bool = True
    quiet: bool = True


@dataclass
class Mask:
    id: str
    label: str
    phrase: str
    effect: str
    risk: str
    type: str = "mask"


@dataclass
class StoryParams:
    setting: str
    mask: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()


def plural_or_name(name: str, suffix: str = "'s") -> str:
    return f"{name}{suffix}"


SETTINGS = {
    "bedroom": Setting(place="the bedroom", bedtime=True, quiet=True),
}

MASKS = {
    "toad_mask": Mask(
        id="toad_mask",
        label="toad mask",
        phrase="a green toad mask with round eyes",
        effect="croaky and bouncy",
        risk="stuck and strange",
    ),
    "alien_mask": Mask(
        id="alien_mask",
        label="alien mask",
        phrase="a shiny alien mask with a tiny silver chin",
        effect="floaty and buzzy",
        risk="too bright for sleep",
    ),
    "toad_alien_mask": Mask(
        id="toad_alien_mask",
        label="toad alien mask",
        phrase="a toad alien mask with green spots and silver ridges",
        effect="croaky and floaty",
        risk="hard to take off",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Ava", "Zoe"]
BOY_NAMES = ["Finn", "Theo", "Max", "Noah", "Eli", "Ben"]
TRAITS = ["curious", "gentle", "sleepy", "brave", "playful", "quiet"]


def valid_masks() -> list[str]:
    return ["toad_mask", "alien_mask", "toad_alien_mask"]


def explain_rejection(mask_id: str) -> str:
    return f"(No story: {mask_id} is not a supported bedtime mask in this world.)"


ASP_RULES = r"""
valid_mask(toad_mask).
valid_mask(alien_mask).
valid_mask(toad_alien_mask).

bedtime_story(S) :- setting(S), bedtime(S).
mask_story(M) :- valid_mask(M).

valid_story(S, M) :- bedtime_story(S), mask_story(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.bedtime:
            lines.append(asp.fact("bedtime", sid))
        if s.quiet:
            lines.append(asp.fact("quiet", sid))
    for mid in MASKS:
        lines.append(asp.fact("mask", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_masks() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p["setting"], p["mask"]) for p in [{"setting": "bedroom", "mask": m} for m in valid_masks()]}
    clingo_set = set(asp_valid_masks())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: a child, a mask, and a bad transformation ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mask", choices=MASKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = args.setting or "bedroom"
    mask = args.mask or rng.choice(valid_masks())
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    if mask not in MASKS:
        raise StoryError(explain_rejection(mask))
    return StoryParams(setting=setting, mask=mask, name=name, gender=gender, parent=parent, trait=trait)


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
    ))
    mask = world.add(Entity(
        id=params.mask,
        type="mask",
        label=MASKS[params.mask].label,
        phrase=MASKS[params.mask].phrase,
        owner=child.id,
        worn_by=child.id,
    ))
    bed = world.add(Entity(id="bed", type="bed", label="the bed"))
    world.facts.update(child=child, parent=parent, mask=mask, bed=bed, params=params)
    return world


def tell(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    mask: Entity = f["mask"]
    params: StoryParams = f["params"]
    m = MASKS[params.mask]

    child.memes["curiosity"] = 1
    child.memes["delight"] = 1
    child.meters["sleepiness"] = 0.6

    world.say(
        f"{child.id} was a little {params.trait} {params.gender} who loved bedtime stories and quiet corners."
    )
    world.say(
        f"One night, {child.id} found {m.phrase} by the pillow and grinned at {child.pronoun('object')} in the dim light."
    )

    world.say(
        f"{child.id} wanted to wear the {m.label} for just one more story, even though the room was already getting sleepy."
    )
    child.memes["wanting"] = 1.0
    child.meters["mask_pressure"] = 0.5
    child.meters["play"] = 1.0

    world.say(
        f"{parent.pronoun().capitalize()} noticed that {m.label} was not a sleep-friendly toy."
    )
    world.say(
        f'"Time for bed," {parent.id} said softly. "That mask looks {m.risk}."'
    )
    child.memes["resistance"] = 1.0

    world.say(
        f"{child.id} shook {child.pronoun('possessive')} head, and the {m.label} stayed on."
    )
    child.meters["mask_pressure"] += 0.7
    child.meters["sleepiness"] += 0.7
    child.meters["transformation"] = 1.0
    child.memes["unease"] = 1.0

    world.say(
        f"The mask felt {m.effect}, and {child.id}'s hands began to look small and greenish in the lamp glow."
    )
    world.say(
        f"Before anyone could fix it, {child.id} gave a tiny croak and turned into a toad-like little alien."
    )
    child.type = "toad"
    child.label = "toad child"
    child.meters["transformed"] = 1.0
    child.meters["croak"] = 1.0
    child.memes["fear"] = 1.0
    child.memes["sadness"] = 1.0

    world.say(
        f"The {m.label} was still there, but now it sat over a round, quiet toad face with bright alien eyes."
    )
    world.say(
        f"{parent.id} lifted a blanket, but the change would not come undone before sleep."
    )
    world.say(
        f"So the bedtime story ended with {child.id} tucked under the covers, a toad alien in a too-tight mask, blinking at the dark."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c: Entity = f["child"]
    m: Entity = f["mask"]
    return [
        f'Write a short bedtime story for a child named {c.id} who finds {m.phrase}.',
        f"Tell a gentle but spooky bedtime story about a {c.type} who puts on a {m.label} and changes.",
        f'Write a child-facing story that includes a toad, a mask, an alien, and a bad ending at bedtime.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c: Entity = f["child"]
    p: Entity = f["parent"]
    m: Entity = f["mask"]
    params: StoryParams = f["params"]
    qa = [
        QAItem(
            question=f"What did {c.id} find by the pillow?",
            answer=f"{c.id} found {m.phrase} by the pillow at bedtime.",
        ),
        QAItem(
            question=f"Why did {p.label} worry about the {m.label}?",
            answer=f"{p.label.capitalize()} worried because the {m.label} was not a sleep-friendly toy and it looked {MASKS[params.mask].risk}.",
        ),
        QAItem(
            question=f"What happened after {c.id} kept the mask on?",
            answer=f"{c.id} transformed into a toad-like little alien and the change did not get fixed before sleep.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bedtime?",
            answer="Bedtime is the time when children get ready for sleep, with quiet voices, blankets, and stories.",
        ),
        QAItem(
            question="What is a mask?",
            answer="A mask is something you wear on your face to pretend, hide, or look like someone or something else.",
        ),
        QAItem(
            question="What is an alien?",
            answer="An alien is a made-up visitor from somewhere far away in space.",
        ),
        QAItem(
            question="What is a toad?",
            answer="A toad is a small hopping animal with a bumpy body and a croaky voice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


CURATED = [
    StoryParams(setting="bedroom", mask="toad_mask", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="bedroom", mask="alien_mask", name="Finn", gender="boy", parent="father", trait="sleepy"),
    StoryParams(setting="bedroom", mask="toad_alien_mask", name="Luna", gender="girl", parent="mother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_masks()
        print(f"{len(combos)} compatible bedtime mask combos:\n")
        for setting, mask in combos:
            print(f"  {setting:8} {mask}")
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
            header = f"### {p.name}: {p.mask} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
