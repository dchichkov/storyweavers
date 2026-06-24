#!/usr/bin/env python3
"""
A tiny story world for a Pirate Tale about transformation.

Seed tale sketch:
---
A small pirate crew was sailing with a shiny treasure map. On the deck was a little parrot named Mhiabbi. The parrot wanted to help find the treasure, but a stormy magic bottle changed Mhiabbi into different forms at the wrong moments. The crew had to learn that the right shape mattered for the right task. In the end, Mhiabbi changed into the needed helper at just the right time, and the crew found the treasure together.

This world models one strong premise:
- a pirate crew needs a helper for a task
- a transformation causes trouble or solves it
- the ending shows what form Mhiabbi became and why that mattered
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
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
    meters: dict[str, float] = None
    memes: dict[str, float] = None

    def __post_init__(self):
        if self.meters is None:
            self.meters = {}
        if self.memes is None:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Transformation:
    id: str
    from_form: str
    to_form: str
    trigger: str
    help_task: str
    reason: str
    effect: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    crew_name: str = "Captain Reed"
    helper_name: str = "Mhiabbi"
    starting_form: str = "small parrot"
    ending_form: str = "strong parrot"
    transformation: str = "storm-glow"


@dataclass
class World:
    entities: dict[str, Entity]
    paragraphs: list[list[str]]
    facts: dict

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


TRANSFORMATIONS = {
    "storm-glow": Transformation(
        id="storm-glow",
        from_form="small parrot",
        to_form="bright lantern-parrot",
        trigger="the sea wind touched the magic bottle",
        help_task="light the dark cave",
        reason="the cave was too dark for the crew to see the treasure path",
        effect="its glow helped the crew see the stones",
    ),
    "rope-feet": Transformation(
        id="rope-feet",
        from_form="small parrot",
        to_form="quick rope-footed parrot",
        trigger="the captain shook the charm pouch",
        help_task="pull a loose rope",
        reason="the ship needed one more helper to tie the sail fast",
        effect="its quick feet kept the sail from tearing",
    ),
    "shell-armor": Transformation(
        id="shell-armor",
        from_form="small parrot",
        to_form="shell-armored parrot",
        trigger="the moon flashed on the bottle",
        help_task="block the spray",
        reason="the deck was slippery and the map would have blown away",
        effect="its hard shell kept the map dry",
    ),
}

SETTING = {
    "sea": "the open sea",
    "ship": "the little ship",
    "cave": "a dark sea cave",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate Tale story world with transformation.")
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
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
    trans = args.transformation or rng.choice(list(TRANSFORMATIONS))
    return StoryParams(
        seed=args.seed,
        transformation=trans,
    )


def _reasonableness_check(params: StoryParams) -> None:
    if params.transformation not in TRANSFORMATIONS:
        raise StoryError("Unknown transformation choice.")
    t = TRANSFORMATIONS[params.transformation]
    if "parrot" not in t.from_form:
        raise StoryError("This tale only works when Mhiabbi begins as a parrot.")
    if t.from_form == t.to_form:
        raise StoryError("The transformation must actually change the form.")


ASP_RULES = r"""
form(mhiabbi, small_parrot).
transformation(storm_glow).
transformation(rope_feet).
transformation(shell_armor).

changes(storm_glow, small_parrot, bright_lantern_parrot).
changes(rope_feet, small_parrot, quick_rope_footed_parrot).
changes(shell_armor, small_parrot, shell_armored_parrot).

valid(T) :- transformation(T), changes(T, small_parrot, _).
#show valid/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("form", "mhiabbi", "small_parrot")]
    for tid in TRANSFORMATIONS:
        t = TRANSFORMATIONS[tid]
        lines.append(asp.fact("transformation", tid))
        lines.append(asp.fact("changes", tid, t.from_form.replace(" ", "_"), t.to_form.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/1."))
    got = sorted(set(asp.atoms(model, "valid")))
    want = [(tid,) for tid in sorted(TRANSFORMATIONS)]
    if got == want:
        print(f"OK: clingo gate matches transformations ({len(got)}).")
        return 0
    print("MISMATCH between clingo and python.")
    print("clingo:", got)
    print("python:", want)
    return 1


def generate(params: StoryParams) -> StorySample:
    _reasonableness_check(params)
    t = TRANSFORMATIONS[params.transformation]

    captain = Entity(id=params.crew_name, kind="character", type="captain", label=params.crew_name)
    helper = Entity(id="mhiabbi", kind="character", type="parrot", label="Mhiabbi")
    treasure = Entity(id="treasure", kind="thing", type="treasure", label="treasure map", phrase="a curled treasure map")
    world = World(entities={"captain": captain, "mhiabbi": helper, "treasure": treasure}, paragraphs=[[]], facts={})

    world.say(f"Captain Reed sailed across {SETTING['sea']} with a curled treasure map and a tiny friend named Mhiabbi.")
    world.say(f"Mhiabbi was a {t.from_form}, and the crew loved how bright-eyed and curious {helper.pronoun()} was.")
    world.para()
    world.say(f"One night, the crew reached {SETTING['cave']}, where the path was dark and the rocks looked sharp.")
    world.say(f"The captain frowned, because {t.reason}. Mhiabbi wanted to help, but being a {t.from_form} was not enough.")
    world.para()
    world.say(f"Then {t.trigger}, and the magic bottle began to shine.")
    helper.type = t.to_form
    helper.memes["pride"] = 1.0
    helper.meters["shaped"] = 1.0
    world.say(f"Mhiabbi changed into a {t.to_form}, just in time to {t.help_task}.")
    world.say(f"{t.effect.capitalize()}, and the crew laughed as they followed the map deeper inside.")
    world.para()
    world.say(f"At last, the treasure chest was found, and Mhiabbi changed the whole voyage from tricky to triumphant.")

    world.facts.update(
        captain=captain,
        helper=helper,
        treasure=treasure,
        transformation=t,
        resolved=True,
    )

    prompts = [
        f"Write a short pirate story where Mhiabbi changes form to help the crew.",
        f"Tell a gentle tale about a captain, a treasure cave, and a transformation called {t.id}.",
        f"Write a child-friendly pirate story that ends with Mhiabbi becoming {t.to_form}.",
    ]
    story_qa = [
        QAItem(
            question="Who was Mhiabbi traveling with?",
            answer="Mhiabbi was traveling with Captain Reed and the pirate crew.",
        ),
        QAItem(
            question=f"What form did Mhiabbi start in before the transformation?",
            answer=f"Mhiabbi started as a {t.from_form}.",
        ),
        QAItem(
            question=f"What did Mhiabbi become after the magic moment?",
            answer=f"Mhiabbi became a {t.to_form}.",
        ),
        QAItem(
            question=f"Why did the crew need the transformation?",
            answer=f"The crew needed it because {t.reason}.",
        ),
        QAItem(
            question=f"How did the new form help the pirates?",
            answer=f"It helped because {t.effect}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a pirate crew?",
            answer="A pirate crew is a group of sailors who travel together on a ship and help each other with the work.",
        ),
        QAItem(
            question="What is a treasure map?",
            answer="A treasure map is a picture or drawing that shows where someone hopes to find treasure.",
        ),
        QAItem(
            question="Why can a dark cave be scary?",
            answer="A dark cave can be scary because it is hard to see what is ahead, so people may need a light or a helper.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for eid, ent in world.entities.items():
        lines.append(f"{eid}: type={ent.type} meters={ent.meters} memes={ent.memes}")
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


CURATED = [StoryParams(transformation=k) for k in TRANSFORMATIONS]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
