#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pus_ticklish_claim_misunderstanding_twist_reconciliation_nursery.py
======================================================================================

A small nursery-rhyme story world about a child, a tiny sore, a ticklish surprise,
and a misunderstanding that turns into a gentle reconciliation.

Seed tale imagined from the prompt:
- A child notices a sore with a little pus and worries about it.
- Another child misunderstands the worry and makes a claim about what happened.
- A ticklish wash, a small twist, and a careful look reveal the real problem.
- The family reconciles with a bandage, a kind word, and a bedtime rhyme.

The world keeps one little medical-accident domain with a child-facing tone.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
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
    body_part: str = ""
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool
    light: str


@dataclass
class Issue:
    id: str
    cause: str
    visible: str
    remedy: str
    seed_word: str = ""


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    issue: str
    fix: str
    name: str
    sibling_name: str
    gender: str
    seed: Optional[int] = None


SETTINGS = {
    "nursery": Setting(place="the nursery", indoors=True, light="soft"),
    "kitchen": Setting(place="the kitchen", indoors=True, light="warm"),
    "garden": Setting(place="the garden", indoors=False, light="bright"),
}

ISSUES = {
    "scratch": Issue(
        id="scratch",
        cause="a thorn",
        visible="a tiny scratch with a dot of pus",
        remedy="wash it and keep it clean",
        seed_word="pus",
    ),
    "splinter": Issue(
        id="splinter",
        cause="a little splinter",
        visible="a sore finger that looked ticklish",
        remedy="pull out the splinter and bandage it",
        seed_word="ticklish",
    ),
}

FIXES = {
    "water": Fix(
        id="water",
        label="warm water",
        phrase="a small bowl of warm water",
        prep="bring a bowl of warm water",
        tail="brought the warm water and a soft cloth",
        helps={"scratch", "splinter"},
    ),
    "bandage": Fix(
        id="bandage",
        label="a bandage",
        phrase="a clean little bandage",
        prep="find a clean little bandage",
        tail="found the bandage and smiled",
        helps={"scratch", "splinter"},
    ),
    "tweezers": Fix(
        id="tweezers",
        label="tweezers",
        phrase="tiny tweezers",
        prep="fetch tiny tweezers",
        tail="fetched the tweezers and pinched the splinter",
        helps={"splinter"},
    ),
}

NAMES = ["Mina", "Pip", "Toby", "Luna", "Nell", "Benny"]
SIBLINGS = ["Mia", "Sam", "Kit", "Bea", "Nico", "Dot"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for issue_id, issue in ISSUES.items():
            for fix_id, fix in FIXES.items():
                if issue_id in fix.helps:
                    combos.append((place, issue_id, fix_id))
    return combos


def _is_reasonable(issue: Issue, fix: Fix) -> bool:
    return issue.id in fix.helps


def _do_issue(world: World, child: Entity, issue: Issue) -> None:
    child.meters["hurt"] = child.meters.get("hurt", 0.0) + 1
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    if issue.id == "scratch":
        child.meters["pus"] = child.meters.get("pus", 0.0) + 1
    if issue.id == "splinter":
        child.memes["ticklish"] = child.memes.get("ticklish", 0.0) + 1


def _look(world: World, child: Entity, sibling: Entity, issue: Issue) -> None:
    world.say(
        f"In {world.setting.place}, little {child.id} found {issue.visible} on {child.pronoun('possessive')} finger."
    )
    world.say(
        f"{child.id} said, \"Oh dear, that looks like {issue.seed_word}.\" "
        f"{sibling.id} tilted {sibling.pronoun('possessive')} head and made a claim of {sibling.pronoun('possessive')} own."
    )


def _misunderstanding(world: World, child: Entity, sibling: Entity, issue: Issue) -> None:
    child.memes["misunderstanding"] = child.memes.get("misunderstanding", 0.0) + 1
    sibling.memes["claim"] = sibling.memes.get("claim", 0.0) + 1
    world.say(
        f"\"I claim it is only a wee old bee-sting,\" said {sibling.id}, "
        f"but {child.id} frowned, for the dot looked more like {issue.seed_word}."
    )


def _twist(world: World, child: Entity, sibling: Entity, issue: Issue) -> None:
    if issue.id == "scratch":
        world.say(
            f"Then came the twist in the nursery rhyme: the dot was not a monster at all, "
            f"but a tiny thorn's tiny tease."
        )
    else:
        world.say(
            f"Then came the twist in the nursery rhyme: the sore was ticklish because a little splinter still slept inside."
        )


def _fix(world: World, child: Entity, sibling: Entity, fix: Fix, issue: Issue) -> None:
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    child.memes["fear"] = 0.0
    world.say(
        f"{sibling.id} {fix.tail}, and {child.id} let the hurt be seen."
    )
    if fix.id == "tweezers":
        world.say(
            f"After a careful tug, the splinter popped out, and the ticklish ache grew small."
        )
    else:
        world.say(
            f"The warm water washed the spot clean, and the little pus was gone."
        )
    world.say(
        f"{sibling.id} laid on {fix.label}, and {child.id} smiled because the sore could rest."
    )
    world.say(
        f"So the two made up at once, and the nursery grew quiet again."
    )


def tell(setting: Setting, issue: Issue, fix: Fix, name: str, sibling_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="boy" if name in {"Pip", "Toby", "Benny"} else "girl"))
    sibling = world.add(Entity(id=sibling_name, kind="character", type="boy" if sibling_name in {"Sam", "Nico"} else "girl"))
    world.say(
        f"Once in {setting.place}, there lived a small child named {child.id}, and {sibling.id} too."
    )
    world.say(
        f"{child.id} was quick to laugh, and the whole room felt bright and light."
    )
    world.para()
    _do_issue(world, child, issue)
    _look(world, child, sibling, issue)
    _misunderstanding(world, child, sibling, issue)
    world.para()
    _twist(world, child, sibling, issue)
    _fix(world, child, sibling, fix, issue)
    world.facts.update(child=child, sibling=sibling, issue=issue, fix=fix, setting=setting)
    return world


KNOWLEDGE = {
    "pus": [
        (
            "What is pus?",
            "Pus is a thick yellow or white fluid that can show up in a sore when the body is fighting a tiny infection."
        ),
    ],
    "ticklish": [
        (
            "What does ticklish mean?",
            "Ticklish means something makes you want to laugh or wiggle when it is touched."
        ),
    ],
    "claim": [
        (
            "What does it mean to claim something?",
            "To claim something means to say it belongs to you, or to make a strong statement about it."
        ),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme story about {f["child"].id}, a small sore, and the word "{f["issue"].seed_word}".',
        f"Tell a gentle story where {f['child'].id} and {f['sibling'].id} have a misunderstanding, then a twist, then a reconciliation.",
        f'Write a child-friendly rhyme that includes the words "pus", "ticklish", and "claim".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, sibling, issue, fix = f["child"], f["sibling"], f["issue"], f["fix"]
    qa = [
        QAItem(
            question=f"What did {child.id} find in {world.setting.place}?",
            answer=f"{child.id} found {issue.visible}. It looked small, but it made {child.id} worry."
        ),
        QAItem(
            question=f"Why did {sibling.id} make a claim about the sore?",
            answer=f"{sibling.id} misunderstood the little sore and made a claim that it was only something minor, but {child.id} could see it needed care."
        ),
        QAItem(
            question=f"What fixed the problem in the end?",
            answer=f"{fix.label} helped. The spot was cleaned or eased, and the two children made up."
        ),
    ]
    if issue.id == "scratch":
        qa.append(QAItem(
            question=f"What happened to the pus?",
            answer="The warm water washed the tiny dot clean, and the pus was gone."
        ))
    else:
        qa.append(QAItem(
            question=f"Why was the sore ticklish?",
            answer="It was ticklish because a tiny splinter was still inside, so touching it made the finger feel funny."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ("pus", "ticklish", "claim"):
        for q, a in KNOWLEDGE[tag]:
            out.append(QAItem(question=q, answer=a))
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
issue_valid(I, F) :- issue(I), fix(F), helps(F, I).
story_valid(P, I, F) :- setting(P), issue(I), fix(F), issue_valid(I, F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for i in ISSUES:
        lines.append(asp.fact("issue", i))
    for f in FIXES.values():
        lines.append(asp.fact("fix", f.id))
        for i in sorted(f.helps):
            lines.append(asp.fact("helps", f.id, i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_valid/3."))
    return sorted(set(asp.atoms(model, "story_valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if py == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - clingo_set))
    print("  only in clingo:", sorted(clingo_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: pus, ticklish, claim, misunderstanding, twist, reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--issue", choices=ISSUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--sibling-name", choices=SIBLINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.issue and args.fix:
        issue = ISSUES[args.issue]
        fix = FIXES[args.fix]
        if not _is_reasonable(issue, fix):
            raise StoryError(f"(No story: {fix.label} cannot help with {issue.id}.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.issue is None or c[1] == args.issue)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, issue_id, fix_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    sibling = args.sibling_name or rng.choice(SIBLINGS)
    gender = args.gender or ("boy" if name in {"Pip", "Toby", "Benny"} else "girl")
    return StoryParams(place=place, issue=issue_id, fix=fix_id, name=name, sibling_name=sibling, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ISSUES[params.issue], FIXES[params.fix], params.name, params.sibling_name)
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
    StoryParams(place="nursery", issue="scratch", fix="water", name="Mina", sibling_name="Pip", gender="girl"),
    StoryParams(place="kitchen", issue="splinter", fix="tweezers", name="Toby", sibling_name="Mia", gender="boy"),
    StoryParams(place="garden", issue="scratch", fix="bandage", name="Luna", sibling_name="Sam", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_valid/3."))
        print(f"{len(set(asp.atoms(model, 'story_valid')))} compatible combos")
        for row in sorted(set(asp.atoms(model, "story_valid"))):
            print(row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
