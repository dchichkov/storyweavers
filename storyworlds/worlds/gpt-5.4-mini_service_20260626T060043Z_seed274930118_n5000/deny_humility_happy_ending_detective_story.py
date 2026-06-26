#!/usr/bin/env python3
"""
storyworlds/worlds/deny_humility_happy_ending_detective_story.py
===============================================================

A small detective-story world with a child-friendly mystery, a denial beat,
a humility beat, and a happy ending.

Premise:
- Something goes wrong in a cozy place.
- The detective follows concrete clues.
- One suspect denies it at first.
- Humility turns the story toward the truth.
- The ending is warm and fixed.

This world is designed to stay close to a classic detective story shape while
remaining simple enough for TinyStories-style generation.
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
# Core domain
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "lady"}
        male = {"boy", "father", "man", "gentleman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    light: str
    location_tag: str


@dataclass
class Clue:
    label: str
    visible: str
    points_to: str


@dataclass
class Suspect:
    id: str
    type: str
    label: str
    honesty: str
    humility: str
    likely_reason: str


@dataclass
class Case:
    id: str
    title: str
    missing_item: str
    missing_phrase: str
    mess: str
    cleanup: str
    clue: Clue
    culprit: str
    suspects: list[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    case: str
    detective: str
    detective_type: str
    suspect: str
    seed: Optional[int] = None


SETTINGS = {
    "library": Setting(
        place="the old library",
        detail="Tall shelves made narrow lanes between the books.",
        light="soft lamp light",
        location_tag="library",
    ),
    "kitchen": Setting(
        place="the little kitchen",
        detail="A warm table sat near the window.",
        light="bright morning light",
        location_tag="kitchen",
    ),
    "garden_room": Setting(
        place="the garden room",
        detail="Potted plants made the room smell green and fresh.",
        light="golden afternoon light",
        location_tag="garden",
    ),
}

CASES = {
    "missing_cookie": Case(
        id="missing_cookie",
        title="The Missing Cookie",
        missing_item="cookie",
        missing_phrase="a plate of warm cookies",
        mess="crumbs",
        cleanup="swept the crumbs into a neat pile",
        clue=Clue(
            label="crumb trail",
            visible="tiny crumbs leading under the table",
            points_to="who had reached the plate first",
        ),
        culprit="mouse",
        suspects=["mouse", "cat", "child"],
    ),
    "spilled_ink": Case(
        id="spilled_ink",
        title="The Spilled Ink",
        missing_item="ink bottle",
        missing_phrase="a small ink bottle",
        mess="ink",
        cleanup="wiped the blue spill with a soft cloth",
        clue=Clue(
            label="blue pawprint",
            visible="a blue pawprint on the paper",
            points_to="who bumped the desk",
        ),
        culprit="cat",
        suspects=["cat", "dog", "bird"],
    ),
    "lost_key": Case(
        id="lost_key",
        title="The Lost Key",
        missing_item="key",
        missing_phrase="a brass key",
        mess="dust",
        cleanup="picked up the dust with a tiny brush",
        clue=Clue(
            label="shiny scratch",
            visible="a shiny scratch near the rug",
            points_to="who had dragged something heavy",
        ),
        culprit="child",
        suspects=["child", "dog", "mouse"],
    ),
}

SUSPECTS = {
    "mouse": Suspect(
        id="mouse",
        type="mouse",
        label="a small mouse",
        honesty="skittish",
        humility="quiet",
        likely_reason="wanted a crumb",
    ),
    "cat": Suspect(
        id="cat",
        type="cat",
        label="a sleepy cat",
        honesty="proud",
        humility="soft-hearted",
        likely_reason="was chasing something shiny",
    ),
    "dog": Suspect(
        id="dog",
        type="dog",
        label="a bouncy dog",
        honesty="eager",
        humility="gentle",
        likely_reason="was wagging too hard",
    ),
    "bird": Suspect(
        id="bird",
        type="bird",
        label="a small bird",
        honesty="quick",
        humility="careful",
        likely_reason="was looking for a crumb of bread",
    ),
    "child": Suspect(
        id="child",
        type="boy",
        label="a little boy",
        honesty="shy",
        humility="brave",
        likely_reason="had tried to help and made a mistake",
    ),
}


GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Theo", "Max", "Ben"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A case is valid if the detective and culprit are both in the suspect list.
valid_story(Case, Detective, Culprit) :- case(Case), suspect(Detective), suspect(Culprit),
                                         available(Case, Detective), culprit_of(Case, Culprit).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("culprit_of", cid, case.culprit))
        for s in case.suspects:
            lines.append(asp.fact("available", cid, s))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_story_configs())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} configs).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_story_configs() -> list[tuple[str, str, str]]:
    out = []
    for case_id, case in CASES.items():
        for suspect_id in case.suspects:
            out.append((case_id, suspect_id, case.culprit))
    return out


def explain_invalid(case: Case, suspect: Suspect) -> str:
    return (
        f"(No story: {suspect.label} does not fit this case well enough. "
        f"The mystery needs a suspect in the room with a believable mistake, "
        f"and the happy ending depends on a real clue, a denial, and a humble fix.)"
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world with denial, humility, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--case", choices=CASES.keys())
    ap.add_argument("--detective")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--suspect", choices=SUSPECTS.keys())
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
    case_id = args.case or rng.choice(list(CASES.keys()))
    case = CASES[case_id]
    suspect_id = args.suspect or rng.choice(case.suspects)
    if suspect_id not in case.suspects:
        raise StoryError(explain_invalid(case, SUSPECTS[suspect_id]))
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    detective = args.detective or rng.choice(GIRL_NAMES if detective_type == "girl" else BOY_NAMES)
    place = args.place or rng.choice(list(SETTINGS.keys()))
    return StoryParams(place=place, case=case_id, detective=detective, detective_type=detective_type, suspect=suspect_id)


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    case = CASES[params.case]
    suspect_cfg = SUSPECTS[params.suspect]
    world = World(setting)

    detective = world.add(Entity(id=params.detective, kind="character", type=params.detective_type, label=params.detective))
    suspect = world.add(Entity(id=suspect_cfg.id, kind="character", type=suspect_cfg.type, label=suspect_cfg.label))
    helper = world.add(Entity(id="helper", kind="character", type="woman", label="the kind librarian"))
    item = world.add(Entity(id=case.missing_item, kind="thing", type=case.missing_item, label=case.missing_item, plural=False))

    detective.memes["curiosity"] = 1
    suspect.memes["nervousness"] = 1
    helper.memes["calm"] = 1
    item.meters["missing"] = 1

    # Act 1
    world.say(f"In {setting.place}, {setting.light} rested over the room.")
    world.say(f"{params.detective} was a little detective who noticed everything.")
    world.say(f"That day, {case.missing_phrase} was gone.")
    world.say(f"{setting.detail} The detective looked at the empty spot and began to search.")

    world.para()
    # Act 2
    world.say(f"The first clue was {case.clue.visible}.")
    world.say(f"It pointed to {case.clue.points_to}.")
    world.say(f"{params.detective} asked {suspect_cfg.label} what had happened.")
    world.say(f"{suspect_cfg.label.capitalize()} denied it at once: \"No, not me.\"")
    world.say(f"But the clue was still there, and the story needed a true answer.")
    world.say(f"Then the kind librarian spoke softly and asked for humility instead of pride.")

    world.para()
    # Act 3
    world.say(f"{suspect_cfg.label.capitalize()} took a slow breath.")
    world.say(f"With humility, {suspect_cfg.label} admitted the truth: {suspect_cfg.likely_reason}.")
    world.say(f"{params.detective} helped put everything right.")
    world.say(f"They found the missing {case.missing_item}, and {case.cleanup}.")
    world.say(f"At the end, the room felt calm again, and everyone could smile.")

    world.facts.update(
        detective=detective,
        suspect=suspect,
        helper=helper,
        item=item,
        case=case,
        setting=setting,
        suspect_cfg=suspect_cfg,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child that includes the words "deny" and "humility".',
        f"Tell a gentle mystery set in {f['setting'].place} where {f['suspect'].label} first denies what happened, then shows humility and helps fix it.",
        f"Write a happy-ending detective story about a missing {f['case'].missing_item} and a clue that leads to the truth.",
    ]


def generate_story_text(world: World) -> str:
    return world.render()


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    suspect: Suspect = f["suspect_cfg"]
    detective = f["detective"].label
    place = f["setting"].place
    return [
        QAItem(
            question=f"Where did the mystery happen?",
            answer=f"The mystery happened in {place}.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{case.missing_phrase} was missing.",
        ),
        QAItem(
            question=f"What did {suspect.label} do at first?",
            answer=f"{suspect.label.capitalize()} denied it at first.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: the truth came out, the missing {case.missing_item} was found, and the room was fixed up.",
        ),
        QAItem(
            question=f"What did {detective} do?",
            answer=f"{detective} followed the clue, asked questions, and helped solve the mystery.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "denial": [
        (
            "What does it mean to deny something?",
            "To deny something means to say it is not true or to say you did not do it.",
        )
    ],
    "humility": [
        (
            "What is humility?",
            "Humility means being willing to admit a mistake, listen carefully, and not act proud.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues, asks questions, and tries to find out what really happened.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small piece of information that helps solve a mystery.",
        )
    ],
    "happy": [
        (
            "What is a happy ending?",
            "A happy ending is when the problem gets fixed and the story ends in a good way.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for items in WORLD_KNOWLEDGE.values() for q, a in items]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=generate_story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_verify_print() -> None:
    print(asp_program("#show valid_story/3."))


def asp_facts_only() -> str:
    return asp_facts()


def asp_valid_configs() -> list[tuple]:
    return asp_valid_stories()


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_story_configs_py() -> list[tuple]:
    return valid_story_configs()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible (case, detective, culprit) stories:\n")
        for case_id, detective, culprit in triples:
            print(f"  {case_id:14} {detective:10} {culprit:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = valid_story_configs()
        for i, (case_id, detective, culprit) in enumerate(combos):
            case = CASES[case_id]
            params = StoryParams(
                place=next(iter(SETTINGS.keys())),
                case=case_id,
                detective=detective if detective in GIRL_NAMES + BOY_NAMES else ("Mia" if detective == "girl" else "Leo"),
                detective_type="girl" if detective in GIRL_NAMES else "boy",
                suspect=culprit,
                seed=base_seed + i,
            )
            samples.append(generate(params))
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
        if len(samples) > 1:
            p = sample.params
            header = f"### variant {i + 1}: {p.case}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
