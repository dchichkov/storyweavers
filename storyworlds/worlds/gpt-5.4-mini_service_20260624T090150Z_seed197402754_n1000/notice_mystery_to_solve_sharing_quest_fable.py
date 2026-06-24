#!/usr/bin/env python3
"""
Standalone Storyworld: Notice, Mystery to Solve, Sharing, Quest, Fable

A small classical simulation about a careful animal who notices a mystery,
follows a quest, and learns that sharing helps solve it.

This world is intentionally compact:
- one setting
- one mystery item
- one seeker
- one sharer/helper
- one final resolution that changes the world state

The story is driven by meters and memes so prose reflects state changes rather
than a frozen template.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    name: str = ""
    label: str = ""
    owner: Optional[str] = None
    carrier: Optional[str] = None
    plural: bool = False
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hare", "rabbit", "fox", "wolf", "squirrel", "mouse"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def subj(self) -> str:
        return self.pronoun("subject")

    def obj(self) -> str:
        return self.pronoun("object")

    def pos(self) -> str:
        return self.pronoun("possessive")


@dataclass
class Setting:
    place: str
    light: str
    features: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    object_name: str
    clue_name: str
    hidden_by: str
    solved_by_sharing: bool = True
    prompt_word: str = "notice"


@dataclass
class Quest:
    id: str
    verb: str
    trail: str
    risk: str
    reward: str
    requires: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the bright meadow", light="sunny", features={"flowers", "paths", "brook"}),
    "woods": Setting(place="the quiet woods", light="dappled", features={"trees", "moss", "stream"}),
    "hill": Setting(place="the windy hill", light="golden", features={"grass", "stones", "birdsong"}),
}

MYSTERIES = {
    "lost_seed": Mystery(
        id="lost_seed",
        object_name="golden seed",
        clue_name="sunny shell",
        hidden_by="a burrow",
        prompt_word="notice",
    ),
    "missing_bell": Mystery(
        id="missing_bell",
        object_name="small silver bell",
        clue_name="bright ribbon",
        hidden_by="the roots",
        prompt_word="notice",
    ),
    "vanished_map": Mystery(
        id="vanished_map",
        object_name="folded map",
        clue_name="ink mark",
        hidden_by="a hollow log",
        prompt_word="notice",
    ),
}

QUESTS = {
    "follow_trail": Quest(
        id="follow_trail",
        verb="follow the trail",
        trail="tiny prints",
        risk="getting lost",
        reward="the hidden thing",
        requires={"sharing"},
    ),
    "climb_rock": Quest(
        id="climb_rock",
        verb="climb the old rock",
        trail="scratches in the moss",
        risk="a wobbly step",
        reward="a wider view",
        requires={"sharing"},
    ),
    "cross_brook": Quest(
        id="cross_brook",
        verb="cross the brook",
        trail="stones by the water",
        risk="wet paws",
        reward="the far bank",
        requires={"sharing"},
    ),
}

NAMES = ["Milo", "Pip", "Nia", "Luna", "Taro", "Bram", "Suki", "Tessa"]
KINDS = ["squirrel", "hare", "mouse", "fox"]
TRAITS = ["careful", "curious", "kind", "brave", "patient", "gentle"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is solvable when the seeker notices a clue and shares it.
solvable(M) :- mystery(M), clue(C), notice(M, C), sharing(M).

% A quest is reasonable only if sharing is part of the plan.
reasonable(Q) :- quest(Q), requires(Q, sharing).

valid_story(S, M, Q) :- setting(S), mystery(M), quest(Q), solvable(M), reasonable(Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", m.clue_name))
        lines.append(asp.fact("notice", mid, m.clue_name))
        lines.append(asp.fact("sharing", mid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for req in sorted(q.requires):
            lines.append(asp.fact("requires", qid, req))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    quest: str
    seeker_name: str
    seeker_kind: str
    helper_name: str
    helper_kind: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            for qid in QUESTS:
                combos.append((sid, mid, qid))
    return combos


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def _do_notice(world: World, seeker: Entity, mystery: Mystery) -> None:
    seeker.memes["attention"] = seeker.memes.get("attention", 0) + 1
    world.say(
        f"One morning, {seeker.name} was walking through {world.setting.place} when "
        f"{seeker.subj()} noticed something odd."
    )
    world.say(
        f"Near {mystery.hidden_by}, there was {mystery.clue_name}, and it did not belong there."
    )


def _ask_help(world: World, seeker: Entity, helper: Entity, mystery: Mystery) -> None:
    seeker.memes["worry"] = seeker.memes.get("worry", 0) + 1
    helper.memes["sharing"] = helper.memes.get("sharing", 0) + 1
    world.say(
        f"{seeker.name} stopped and looked at {helper.name}. "
        f'"I think a mystery is hiding nearby," {seeker.subj()} said. '
        f'"Will you share the search with me?"'
    )
    world.say(
        f"{helper.name} nodded at once, because {helper.subj()} liked to share crumbs, clues, and time."
    )


def _quest_turn(world: World, seeker: Entity, helper: Entity, quest: Quest, mystery: Mystery) -> None:
    seeker.memes["hope"] = seeker.memes.get("hope", 0) + 1
    helper.memes["help"] = helper.memes.get("help", 0) + 1
    world.say(
        f"Together they set out on a small quest: to {quest.verb} and find what was missing."
    )
    world.say(
        f"They chose the safer way, so they would not trip on {quest.trail} or rush into {quest.risk}."
    )
    world.say(
        f"As they went, {helper.name} shared a simple idea: follow the clue, then look where {mystery.object_name} might be hidden."
    )


def _solve(world: World, seeker: Entity, helper: Entity, mystery: Mystery) -> None:
    seeker.meters["mystery_solved"] = seeker.meters.get("mystery_solved", 0) + 1
    helper.meters["shared"] = helper.meters.get("shared", 0) + 1
    world.say(
        f"At last they found the place where the clue pointed. Under the soft cover, there was the {mystery.object_name}."
    )
    world.say(
        f"{helper.name} shared the discovery with a grin, and {seeker.name} shared the joy right back."
    )
    world.say(
        f"Their careful sharing had solved the mystery, and the little quest ended in a happy way."
    )


def tell(setting: Setting, mystery: Mystery, quest: Quest,
         seeker_name: str, seeker_kind: str, helper_name: str, helper_kind: str,
         trait: str) -> World:
    world = World(setting)

    seeker = world.add(Entity(
        id="seeker",
        kind="character",
        type=seeker_kind,
        name=seeker_name,
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_kind,
        name=helper_name,
    ))
    hidden = world.add(Entity(
        id="hidden_item",
        kind="thing",
        type="thing",
        name=mystery.object_name,
        label=mystery.object_name,
    ))

    world.facts.update(
        seeker=seeker,
        helper=helper,
        hidden=hidden,
        mystery=mystery,
        quest=quest,
        setting=setting,
    )

    world.say(
        f"{seeker.name} was a {trait} {seeker.type} who loved to notice small things."
    )
    world.say(
        f"{helper.name} was a {helper_kind} who liked to share, because sharing made the day feel warmer."
    )
    world.say(
        f"People in {setting.place} said that a good eye and a kind friend could solve many troubles."
    )

    world.para()
    _do_notice(world, seeker, mystery)
    _ask_help(world, seeker, helper, mystery)

    world.para()
    _quest_turn(world, seeker, helper, quest, mystery)
    _solve(world, seeker, helper, mystery)

    world.facts["solved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s = f["seeker"]
    m = f["mystery"]
    q = f["quest"]
    return [
        f"Write a gentle fable about {s.name}, who uses {m.prompt_word} to solve a mystery and share the answer.",
        f"Tell a child-friendly story in which a {s.type} named {s.name} and a friend go on a quest to {q.verb}.",
        f"Write a short fable where noticing a clue leads to sharing and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    s: Entity = f["seeker"]  # type: ignore[assignment]
    h: Entity = f["helper"]  # type: ignore[assignment]
    m: Mystery = f["mystery"]  # type: ignore[assignment]
    q: Quest = f["quest"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who noticed the mystery first in {world.setting.place}?",
            answer=f"{s.name} noticed it first. {s.subj().capitalize()} saw the clue near {m.hidden_by}.",
        ),
        QAItem(
            question=f"What did {s.name} ask {h.name} to do?",
            answer=f"{s.name} asked {h.name} to share the search and help solve the mystery together.",
        ),
        QAItem(
            question=f"What quest did they go on?",
            answer=f"They went on a quest to {q.verb}, and they chose the careful way so they would stay safe.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"It was solved by noticing {m.clue_name}, sharing the clue, and then finding the {m.object_name} where it had been hidden.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else use, know, or enjoy something with you.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you do not understand right away, so you have to look for clues.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or journey to find something or reach a goal.",
        ),
        QAItem(
            question="Why is noticing useful?",
            answer="Noticing is useful because careful eyes can spot clues that others might miss.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} name={e.name!r} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like storyworld about noticing a mystery and sharing a quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--helper-kind", choices=KINDS)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    choices = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.quest is None or c[2] == args.quest)
    ]
    if not choices:
        raise StoryError("No valid combination matches the given options.")
    setting, mystery, quest = rng.choice(sorted(choices))
    seeker_kind = args.kind or rng.choice(KINDS)
    helper_kind = args.helper_kind or rng.choice([k for k in KINDS if k != seeker_kind])
    seeker_name = args.name or rng.choice(NAMES)
    helper_name = args.helper or rng.choice([n for n in NAMES if n != seeker_name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        quest=quest,
        seeker_name=seeker_name,
        seeker_kind=seeker_kind,
        helper_name=helper_name,
        helper_kind=helper_kind,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        QUESTS[params.quest],
        params.seeker_name,
        params.seeker_kind,
        params.helper_name,
        params.helper_kind,
        params.trait,
    )
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
    StoryParams("meadow", "lost_seed", "follow_trail", "Milo", "squirrel", "Tessa", "mouse", "curious"),
    StoryParams("woods", "missing_bell", "cross_brook", "Pip", "hare", "Suki", "fox", "careful"),
    StoryParams("hill", "vanished_map", "climb_rock", "Nia", "mouse", "Bram", "squirrel", "kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.seeker_name}: {p.mystery} in {p.setting} (quest: {p.quest})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
