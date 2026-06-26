#!/usr/bin/env python3
"""
storyworlds/worlds/bacon_weep_inner_monologue_detective_story.py
===============================================================

A small detective-story world about missing bacon, a worried sleuth, and an
inner monologue that tracks the clues all the way to the answer.

The seed words are baked into the premise:
- bacon
- weep

The world is intentionally tiny: one detective, one setting, one missing snack,
and a short chain of clues that can lead to a satisfying reveal.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "detective_girl"}
        male = {"boy", "man", "father", "detective_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    scent: str
    affordance: str


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    alibi: str
    clue: str
    motive: str
    can_take_bacon: bool = True


@dataclass
class StoryParams:
    setting: str
    culprit: str
    detective_name: str
    detective_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        clone = World(self.setting)
        import copy as _copy

        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "diner": Setting(place="the little diner", scent="warm grease", affordance="breakfast"),
    "kitchen": Setting(place="the kitchen", scent="toasty bread", affordance="breakfast"),
    "camp": Setting(place="the camp cabin", scent="smoke and coffee", affordance="breakfast"),
}

SUSPECTS = {
    "dog": Suspect(
        id="dog",
        label="the hungry dog",
        type="dog",
        alibi="There were bacon crumbs on the floor near the water bowl.",
        clue="The wet nose print under the table matched the dog.",
        motive="The dog loved the smell of bacon.",
    ),
    "cat": Suspect(
        id="cat",
        label="the sly cat",
        type="cat",
        alibi="The cat was sitting on the windowsill and blinking slowly.",
        clue="A tiny paw print was on the chair, but the bacon was too high for the cat.",
        motive="The cat wanted a snack, but not this one.",
    ),
    "mouse": Suspect(
        id="mouse",
        label="the mouse",
        type="mouse",
        alibi="A mouse could slip around quietly in the walls.",
        clue="The crumbs made a little trail toward the wall crack.",
        motive="The mouse wanted a crumb, not the whole slice.",
    ),
}

DETECTIVE_TYPES = ["girl", "boy"]
DETECTIVE_NAMES = {
    "girl": ["Mina", "Nora", "Ivy", "Tess"],
    "boy": ["Owen", "Leo", "Finn", "Max"],
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting in SETTINGS:
        for culprit, suspect in SUSPECTS.items():
            if suspect.can_take_bacon:
                combos.append((setting, culprit))
    return combos


def explain_rejection(culprit: str) -> str:
    return f"(No story: {culprit} is not a plausible bacon thief in this tiny mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny detective story world about bacon, a clue trail, and an inner monologue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--culprit", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--detective-type", choices=DETECTIVE_TYPES)
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
    if args.culprit and args.culprit not in SUSPECTS:
        raise StoryError(explain_rejection(args.culprit))
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.culprit is None or c[1] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid mystery matches the given options.)")
    setting, culprit = rng.choice(sorted(combos))
    d_type = args.detective_type or rng.choice(DETECTIVE_TYPES)
    name = args.name or rng.choice(DETECTIVE_NAMES[d_type])
    return StoryParams(setting=setting, culprit=culprit, detective_name=name, detective_type=d_type)


def _do_search(world: World, detective: Entity, suspect: Suspect) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    world.say(
        f"{detective.id} stepped into {world.setting.place}, where the air smelled like {world.setting.scent}."
    )
    world.say(
        f"The bacon was gone, and {detective.pronoun('subject')} felt a tiny pinch in the chest, almost like {detective.pronoun('subject')} might weep."
    )
    world.say(
        f"In {detective.pronoun('possessive')} inner monologue, {detective.id} said, "
        f'"A good detective does not guess. A good detective looks."'
    )
    world.say(
        f"{detective.pronoun('subject').capitalize()} noticed {suspect.clue}"
    )
    detective.meters["clues"] = detective.meters.get("clues", 0) + 1


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label="detective",
    ))
    suspect = SUSPECTS[params.culprit]
    culprit = world.add(Entity(
        id=suspect.id,
        kind="character",
        type=suspect.type,
        label=suspect.label,
    ))
    bacon = world.add(Entity(
        id="bacon",
        kind="thing",
        type="food",
        label="bacon",
        phrase="a plate of bacon",
        owner=detective.id,
    ))
    world.facts.update(detective=detective, suspect=suspect, culprit=culprit, bacon=bacon)

    world.say(f"{detective.id} was a little detective who loved quiet clues and big answers.")
    world.say(
        f"One morning, {detective.id} found {bacon.label} missing from the plate."
    )
    world.say(
        f"{detective.id} looked around and thought, 'Someone here knows what happened to the bacon.'"
    )

    world.para()
    _do_search(world, detective, suspect)
    world.say(suspect.alibi)
    world.say(f"In {detective.pronoun('possessive')} head, the case began to narrow.")

    world.para()
    world.say(
        f"{detective.id} followed the crumbs, the nose print, and the smell of bacon."
    )
    if params.culprit == "dog":
        world.say(
            f"The trail led under the table, where the hungry dog was licking its lips."
        )
        world.say(
            f"{detective.id} thought, 'So that's it. The bacon wasn't stolen for trouble. It was taken for hunger.'"
        )
        world.say(
            f"{detective.id} offered the dog a small shared bite and smiled at the honest answer."
        )
    elif params.culprit == "cat":
        world.say(
            f"The trail ended on the chair, where the sly cat was pretending not to care."
        )
        world.say(
            f"{detective.id} thought, 'A neat trick, but the bacon is too high for those paws.'"
        )
        world.say(
            f"Then {detective.id} found the bacon on the counter, where the cat had only watched it move."
        )
    else:
        world.say(
            f"The trail led to the wall crack, where the mouse had carried off only crumbs."
        )
        world.say(
            f"{detective.id} thought, 'A tiny thief, but not a bacon thief after all.'"
        )
        world.say(
            f"The bacon was tucked safely in the oven, and the mouse had simply followed the smell."
        )

    world.say(
        f"In the end, {detective.id} had the answer, and the bacon was back where it belonged."
    )
    world.say(
        f"{detective.id} felt the worry leave like rain after a storm, and the mystery was solved."
    )

    world.facts["resolved"] = True
    world.facts["setting"] = params.setting
    world.facts["culprit_id"] = params.culprit
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
    detective: Entity = f["detective"]
    suspect: Suspect = f["suspect"]
    return [
        'Write a short detective story for a young child that includes the words "bacon" and "weep".',
        f"Tell a cozy mystery where {detective.id} follows clues to find the missing bacon.",
        f"Write a story with an inner monologue where {suspect.label} is part of the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    suspect: Suspect = f["suspect"]
    answers = [
        QAItem(
            question="Who was the story about?",
            answer=f"The story was about {detective.id}, a little detective who wanted to find the missing bacon.",
        ),
        QAItem(
            question="What was missing?",
            answer="The bacon was missing from the plate, so the detective started looking for clues.",
        ),
        QAItem(
            question="What did the detective think to do first?",
            answer="The detective thought to look carefully instead of guessing, because clues matter in a mystery.",
        ),
        QAItem(
            question="What clue helped solve the case?",
            answer=suspect.clue,
        ),
        QAItem(
            question="How did the detective feel near the start?",
            answer=f"{detective.id} felt worried and almost like {detective.pronoun('subject')} might weep, but kept going.",
        ),
        QAItem(
            question="How did the mystery end?",
            answer="The detective found the answer, and the bacon ended up back where it belonged.",
        ),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bacon?",
            answer="Bacon is a salty food made from pork that is often cooked until it is crisp.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking inside a character's head.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(diner).
setting(kitchen).
setting(camp).

suspect(dog).
suspect(cat).
suspect(mouse).

can_take_bacon(S) :- suspect(S).

valid(Setting, Suspect) :- setting(Setting), can_take_bacon(Suspect).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for cid in SUSPECTS:
        lines.append(asp.fact("suspect", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
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


CURATED = [
    StoryParams(setting="diner", culprit="dog", detective_name="Mina", detective_type="girl"),
    StoryParams(setting="kitchen", culprit="cat", detective_name="Owen", detective_type="boy"),
    StoryParams(setting="camp", culprit="mouse", detective_name="Ivy", detective_type="girl"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.culprit is None or c[1] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, culprit = rng.choice(sorted(combos))
    d_type = args.detective_type or rng.choice(DETECTIVE_TYPES)
    name = args.name or rng.choice(DETECTIVE_NAMES[d_type])
    return StoryParams(setting=setting, culprit=culprit, detective_name=name, detective_type=d_type)


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.detective_name}: {p.setting} / {p.culprit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
