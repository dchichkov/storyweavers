#!/usr/bin/env python3
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
        if self.type in {"girl", "she", "queen", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "he", "king", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    friend: str
    helper: str
    seed: Optional[int] = None


@dataclass
class Setting:
    name: str = "the isle"
    description: str = "a small isle with a bright path, a sandy cove, and a leaning palm"


@dataclass
class Problem:
    id: str
    risk: str
    verb: str
    action: str
    resolve: str
    mess_key: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


PROBLEMS = {
    "net": Problem(
        id="net",
        risk="the fisher's net had tangled knots",
        verb="help untangle the net",
        action="lift and loosen the loops",
        resolve="together",
        mess_key="tangle",
    ),
    "basket": Problem(
        id="basket",
        risk="the berry basket had a cracked handle",
        verb="help mend the basket",
        action="hold, weave, and tie",
        resolve="together",
        mess_key="crack",
    ),
    "lantern": Problem(
        id="lantern",
        risk="the lantern had gone dim",
        verb="help brighten the lantern",
        action="shelter, polish, and share light",
        resolve="together",
        mess_key="dim",
    ),
}

HELPERS = {
    "shell": "a patient sea turtle",
    "bird": "a clever little gull",
    "goat": "a gentle island goat",
}

FRIEND_NAMES = ["Pip", "Miri", "Tavi", "Luma", "Nilo", "Sera", "Joss", "Kiki"]
HELPER_NAMES = ["Shell", "Gull", "Goat"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about teamwork, kindness, and friendship on an isle.")
    ap.add_argument("--name", choices=FRIEND_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    name = args.name or rng.choice(FRIEND_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != name])
    helper = args.helper or rng.choice(list(HELPERS))
    if name == friend:
        raise StoryError("The friend must be a different child so the friendship can grow.")
    return StoryParams(name=name, friend=friend, helper=helper)


def story_problem() -> Problem:
    return PROBLEMS["net"]


def valid_combo(params: StoryParams) -> bool:
    return params.name != params.friend and params.helper in HELPERS


ASP_RULES = r"""
child(X) :- name(X).
helper(H) :- helper_kind(H).
different(X,Y) :- X != Y.
valid_story(N,F,H) :- child(N), child(F), helper(H), different(N,F).
#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for n in FRIEND_NAMES:
        lines.append(asp.fact("name", n))
    for h in HELPERS:
        lines.append(asp.fact("helper_kind", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(n, f, h) for n in FRIEND_NAMES for f in FRIEND_NAMES if n != f for h in HELPERS}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def choose_problem(rng: random.Random) -> Problem:
    return PROBLEMS[rng.choice(list(PROBLEMS))]


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params):
        raise StoryError("That story setup is not reasonable.")
    rng = random.Random(params.seed)
    world = World(setting=Setting())
    problem = choose_problem(rng)
    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    friend = world.add(Entity(id=params.friend, kind="character", type="child", label=params.friend))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper, label=HELPERS[params.helper]))

    hero.memes["care"] = 1
    friend.memes["care"] = 1
    helper.memes["care"] = 1

    world.say(
        f"On a small isle, {hero.id} and {friend.id} walked where the sea breeze sang."
    )
    world.say(
        f"They met {helper.label}, and the three of them listened to the isle's quiet needs."
    )

    world.para()
    world.say(
        f"Near the cove, they found {problem.risk}; {hero.id} frowned, and {friend.id} said the two of them should help."
    )
    hero.memes["worry"] = 1
    friend.memes["kindness"] = 1
    helper.memes["kindness"] = 1
    world.facts["problem"] = problem.id

    if problem.id == "net":
        hero.meters["lift"] = 1
        friend.meters["pull"] = 1
        helper.meters["hold"] = 1
        world.say(
            f"{hero.id} held one side, {friend.id} held the other, and {helper.label} lifted the middle."
        )
        world.say(
            f"With teamwork, they {problem.action}, and the fisher could smile again."
        )
    elif problem.id == "basket":
        hero.meters["hold"] = 1
        friend.meters["weave"] = 1
        helper.meters["tie"] = 1
        world.say(
            f"{hero.id} held the basket steady while {friend.id} wove a strong strip and {helper.label} tied it tight."
        )
        world.say(
            f"Kindness made the basket whole, and the berries stayed safe for supper."
        )
    else:
        hero.meters["shield"] = 1
        friend.meters["polish"] = 1
        helper.meters["share"] = 1
        world.say(
            f"{hero.id} sheltered the lantern from the wind while {friend.id} polished the glass and {helper.label} shared a bright spark."
        )
        world.say(
            f"Friendship brought back the light, and the path on the isle shone gold."
        )

    hero.memes["joy"] = 2
    friend.memes["joy"] = 2
    helper.memes["joy"] = 2
    world.facts.update(hero=hero, friend=friend, helper=helper, problem=problem)

    story = world.render()
    prompts = [
        f"Write a fable about two friends on an isle who solve a small problem with teamwork.",
        f"Tell a child-friendly story with kindness and friendship that includes the word \"isle\".",
        f"Write a short fable where {params.name} and {params.friend} help {HELPERS[params.helper].lower()} make things better.",
    ]
    story_qa = [
        QAItem(
            question=f"Who were the friends in the story?",
            answer=f"The friends were {params.name} and {params.friend}. They worked together on the isle.",
        ),
        QAItem(
            question="What did they do to help?",
            answer=f"They used teamwork and kindness to solve the problem by helping {HELPERS[params.helper].lower()} on the isle.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with the problem fixed and the isle feeling peaceful again.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together to do something that is easier or better with help.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward others.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a close, caring bond between friends who help and enjoy one another.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Pip", friend="Miri", helper="shell"),
    StoryParams(name="Tavi", friend="Luma", helper="bird"),
    StoryParams(name="Joss", friend="Kiki", helper="goat"),
]


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for n, f, h in stories:
            print(f"  {n} {f} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            p.seed = base_seed
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.name} with {p.friend} and {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
