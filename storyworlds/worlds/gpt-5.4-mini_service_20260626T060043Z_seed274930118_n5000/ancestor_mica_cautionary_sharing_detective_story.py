#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ancestor_mica_cautionary_sharing_detective_story.py
=============================================================================================================================

A tiny detective-style storyworld about an ancestor, a piece of mica, cautious
sharing, and a small mystery that gets solved by paying attention to evidence.

Premise:
- A child has a special mica token from an ancestor.
- Someone wants to share it, but the ancestor warns that mica can chip, scratch,
  or vanish if it is handled carelessly.
- A gentle detective turn follows: signs are checked, the truth is inferred,
  and the group chooses a safer way to share.

The world is small on purpose:
- one heirloom object
- one or two places to search
- a single cautionary mistake or near-mistake
- a clear resolution that preserves the mica

The prose should read like a child-friendly detective story, with clues, caution,
sharing, and a satisfying final image proving what changed.
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

TITLE_WORDS = ("ancestor", "mica")


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    handled_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    detail: str
    kind: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    name: str
    gender: str
    ancestor: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "study": Setting(place="the dusty study", affordances={"search", "share"}),
    "attic": Setting(place="the old attic", affordances={"search", "share"}),
    "porch": Setting(place="the porch", affordances={"search", "share"}),
}

CLUES = {
    "mica": Clue(
        id="mica",
        label="mica",
        detail="a thin, shiny flake of mica",
        kind="stone",
    ),
    "mica_note": Clue(
        id="mica_note",
        label="mica note",
        detail="a little note tucked under the mica",
        kind="paper",
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "June", "Lina", "Ada"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Max"]
TRAITS = ["curious", "careful", "brave", "quiet", "sharp-eyed"]


def valid_combos() -> list[tuple[str, str]]:
    return [("study", "mica"), ("attic", "mica"), ("porch", "mica_note")]


def select_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def select_clue(clue_id: str) -> Clue:
    if clue_id not in CLUES:
        raise StoryError(f"Unknown clue: {clue_id}")
    return CLUES[clue_id]


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={},
        memes={"curiosity": 0.0, "worry": 0.0, "relief": 0.0},
    ))
    anc = world.add(Entity(
        id="Ancestor",
        kind="character",
        type=params.ancestor,
        label=f"the {params.ancestor}",
        memes={"care": 1.0, "caution": 1.0},
    ))
    clue = world.add(Entity(
        id="Mica",
        type=select_clue(params.clue).kind,
        label=select_clue(params.clue).label,
        phrase=select_clue(params.clue).detail,
        owner=anc.id,
        caretaker=child.id,
        meters={"safe": 1.0},
        handled_by=child.id,
    ))
    world.facts.update(child=child, ancestor=anc, clue=clue, params=params)
    return world


def _search_for_clue(world: World) -> None:
    child = world.get(world.facts["child"].id)
    clue = world.get("Mica")
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} looked around {world.setting.place} like a little detective, "
        f"trying to find the shiny mica again."
    )
    if clue.meters.get("safe", 0.0) >= 1.0:
        world.say(
            f"Behind a small book and a folded cloth, {child.id} spotted {clue.phrase}."
        )


def _caution(world: World) -> None:
    child = world.get(world.facts["child"].id)
    anc = world.get(world.facts["ancestor"].id)
    clue = world.get("Mica")
    world.say(
        f'"Be gentle," {anc.label} said. "Mica can chip if we rush it, and I want '
        f'{clue.it()} to stay whole."'
    )
    child.memes["worry"] += 1


def _sharing_turn(world: World) -> None:
    child = world.get(world.facts["child"].id)
    anc = world.get(world.facts["ancestor"].id)
    clue = world.get("Mica")
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} wanted to share the mica with everyone, but first {child.pronoun()} "
        f"held {clue.it()} flat on the table."
    )
    world.say(
        f"{anc.label} nodded. " f"That was the safe way to share it."
    )


def _detective_turn(world: World) -> None:
    child = world.get(world.facts["child"].id)
    clue = world.get("Mica")
    world.say(
        f"{child.id} checked the edges like a real detective and noticed that the "
        f"mica was still smooth and bright."
    )
    world.say(
        f"The clue had not broken at all, so the mystery was really about how to "
        f"share it without hurting it."
    )
    clue.meters["safe"] = 1.0
    child.memes["relief"] += 1


def _resolution(world: World) -> None:
    child = world.get(world.facts["child"].id)
    anc = world.get(world.facts["ancestor"].id)
    clue = world.get("Mica")
    world.say(
        f"Together they showed the mica to everyone one at a time, and the shiny piece "
        f"kept its sparkle."
    )
    world.say(
        f"{child.id} smiled, because the answer was simple: careful hands, patient eyes, "
        f"and a shared story from the {anc.type}."
    )
    world.say(
        f"At the end, the mica rested safely in {anc.pronoun('possessive')} open palm, "
        f"and {child.id} felt proud to have solved the little case."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    _search_for_clue(world)
    world.para()
    _caution(world)
    _sharing_turn(world)
    world.para()
    _detective_turn(world)
    _resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    anc = f["ancestor"]
    clue = f["clue"]
    return [
        f'Write a short detective story for a young child about {child.id}, '
        f'{anc.label}, and a piece of {clue.label}.',
        f"Tell a cautionary story where {child.id} learns how to share "
        f"{clue.phrase} safely.",
        f"Write a simple mystery with clues, careful hands, and a happy ending "
        f"in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    anc = f["ancestor"]
    clue = f["clue"]
    params = f["params"]
    return [
        QAItem(
            question=f"Who is the detective in this story?",
            answer=f"The detective is {child.id}, who looks for the mica like a careful little sleuth.",
        ),
        QAItem(
            question=f"What shiny thing was being shared?",
            answer=f"They were sharing {clue.phrase}, a small piece of mica from {anc.label}.",
        ),
        QAItem(
            question=f"Why did {anc.label} warn everyone to be gentle?",
            answer="Because mica is thin and can chip if it is handled too quickly or roughly.",
        ),
        QAItem(
            question=f"How did {child.id} share the mica safely?",
            answer=(
                f"{child.id} held it flat and showed it to everyone one at a time, "
                f"so the mica stayed smooth and bright."
            ),
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened in {SETTINGS[params.setting].place}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mica?",
            answer="Mica is a shiny mineral that can split into thin flakes.",
        ),
        QAItem(
            question="Why should people handle fragile things carefully?",
            answer="Fragile things can break, chip, or bend if they are handled roughly.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and thinks carefully to solve a mystery.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, see, or enjoy something too.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} label={e.label} "
            f"meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
% A clue is fragile if it is mica.
fragile(mica) :- clue(mica).

% Sharing is cautious only if the mica is held flat and shown one at a time.
cautious_share(mica) :- held_flat(mica), one_at_a_time(mica).

% A story is valid when the setting can support searching and sharing the clue.
valid_story(S, C) :- setting(S), clue(C), can_search(S), can_share(S), fragile(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact(f"can_{a}", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.label == "mica":
            lines.append(asp.fact("held_flat", cid))
            lines.append(asp.fact("one_at_a_time", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(s, c) for s, c in valid_combos()}
    model = asp.one_model(asp_program("#show valid_story/2."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid stories).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def explain_rejection(setting: str, clue: str) -> str:
    if (setting, clue) not in valid_combos():
        return (
            f"(No story: the combination of {setting} and {clue} does not give a "
            f"clean detective problem with a cautious sharing turn.)"
        )
    return "(No story: unsupported request.)"


def valid_combos() -> list[tuple[str, str]]:
    return [("study", "mica"), ("attic", "mica"), ("porch", "mica_note")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny cautionary sharing detective storyworld.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--ancestor", choices=["grandmother", "grandfather"])
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
    if args.setting and args.clue and (args.setting, args.clue) not in valid_combos():
        raise StoryError(explain_rejection(args.setting, args.clue))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    clue = args.clue or rng.choice(["mica"])
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or select_name(gender, rng)
    ancestor = args.ancestor or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, clue=clue, name=name, gender=gender, ancestor=ancestor, trait=trait)


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
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        items = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(items)} valid stories:")
        for item in items:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="study", clue="mica", name="Mina", gender="girl", ancestor="grandmother", trait="careful"),
            StoryParams(setting="attic", clue="mica", name="Noah", gender="boy", ancestor="grandfather", trait="curious"),
            StoryParams(setting="porch", clue="mica_note", name="Ivy", gender="girl", ancestor="grandmother", trait="sharp-eyed"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < max(1, args.n) and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.setting}, {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
