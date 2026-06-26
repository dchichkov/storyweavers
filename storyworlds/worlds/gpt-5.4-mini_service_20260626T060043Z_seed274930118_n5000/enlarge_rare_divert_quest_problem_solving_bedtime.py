#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/enlarge_rare_divert_quest_problem_solving_bedtime.py
=============================================================================================================================

A small bedtime-story world about a child on a quiet quest, a rare little
problem, and a gentle diversion that helps solve it.

Premise:
- At bedtime, a child notices a rare tiny thing needs to be enlarged in order
  to help with a small quest.
- The child cannot simply force the answer; they must think, ask, and try a
  safer diversion first.
- The story ends when the child solves the problem and everything settles for
  sleep.

Seed words:
- enlarge
- rare
- divert

Narrative instruments:
- Quest
- Problem Solving

Style:
- Bedtime Story
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wearable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    quiet: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    goal: str
    needs_enlarge: bool
    rare_tag: str
    prompts: list[str] = field(default_factory=list)


@dataclass
class Problem:
    id: str
    label: str
    cause: str
    risk: str
    noise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Diversion:
    id: str
    label: str
    verb: str
    method: str
    effect: str
    helps_tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "nursery": Place("the nursery", quiet=True, affords={"dream_map", "stargaze", "shelter"}),
    "bedroom": Place("the bedroom", quiet=True, affords={"dream_map", "stargaze", "shelter", "music_box"}),
    "hallway": Place("the hallway", quiet=False, affords={"lantern", "stargaze"}),
}

QUESTS = {
    "find_lullaby_star": Quest(
        id="find_lullaby_star",
        verb="find the lullaby star",
        gerund="finding the lullaby star",
        goal="help the room feel sleepy and safe",
        needs_enlarge=True,
        rare_tag="rare_star",
        prompts=[
            "A child wants to find a tiny star for bedtime.",
            "A rare little light needs to be enlarged so it can be seen.",
        ],
    ),
    "match_dream_key": Quest(
        id="match_dream_key",
        verb="match the dream key to the soft lock",
        gerund="matching the dream key to the soft lock",
        goal="open the toy chest before sleep",
        needs_enlarge=False,
        rare_tag="rare_key",
        prompts=[
            "A bedtime quest needs careful thinking, not rushing.",
            "A rare key must be used in a gentle, smart way.",
        ],
    ),
    "lift_raincloud_picture": Quest(
        id="lift_raincloud_picture",
        verb="lift the raincloud picture into the lamp glow",
        gerund="lifting the raincloud picture into the lamp glow",
        goal="show the picture clearly without tearing it",
        needs_enlarge=True,
        rare_tag="rare_picture",
        prompts=[
            "A rare picture needs help to be seen at bedtime.",
            "The child must enlarge the view with a clever idea.",
        ],
    ),
}

PROBLEMS = {
    "too_tiny": Problem(
        id="too_tiny",
        label="too tiny to see",
        cause="the clue was small and dim",
        risk="the child might miss the answer",
        noise="a fussy sigh",
        tags={"rare", "small"},
    ),
    "too_high": Problem(
        id="too_high",
        label="too high to reach",
        cause="the clue sat on a shelf",
        risk="the child might wobble and spill things",
        noise="a worried whisper",
        tags={"reach"},
    ),
    "too_loud": Problem(
        id="too_loud",
        label="too loud for bedtime",
        cause="the first idea made a noisy clatter",
        risk="the room would wake up instead of settling down",
        noise="a sharp clink",
        tags={"noise"},
    ),
}

DIVERTS = {
    "magnifier_pillow": Diversion(
        id="magnifier_pillow",
        label="a pillow magnifier",
        verb="use",
        method="held a rounded glass over the clue while resting it on a soft pillow",
        effect="made the tiny thing look larger without any roughness",
        helps_tags={"rare", "small"},
    ),
    "shadow_lamp": Diversion(
        id="shadow_lamp",
        label="a lamp-shadow trick",
        verb="try",
        method="placed the object near the lamp so its shape could be seen on the wall",
        effect="showed the clue clearly in a sleepy, gentle way",
        helps_tags={"small", "reach"},
    ),
    "quiet_song": Diversion(
        id="quiet_song",
        label="a quiet song",
        verb="sing",
        method="hummed softly and slowed the breathing in the room",
        effect="turned the noise into a hush",
        helps_tags={"noise"},
    ),
}

NAMES = ["Mia", "Noah", "Lina", "Theo", "Ivy", "Sam", "Nora", "Eli"]
PARENTS = ["mother", "father"]
TRAITS = ["sleepy", "curious", "gentle", "careful", "brave"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    problem: str
    diversion: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Logic
# ---------------------------------------------------------------------------
def quest_requires_enlarge(quest: Quest, problem: Problem) -> bool:
    return quest.needs_enlarge and "small" in problem.tags or "rare" in problem.tags


def diversion_works(quest: Quest, problem: Problem, diversion: Diversion) -> bool:
    return bool(problem.tags & diversion.helps_tags) and (not quest.needs_enlarge or diversion.id != "quiet_song")


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, p in PLACES.items():
        for qid, q in QUESTS.items():
            for pid, pr in PROBLEMS.items():
                for did, d in DIVERTS.items():
                    if quest_requires_enlarge(q, pr) and diversion_works(q, pr, d) and qid != "match_dream_key":
                        if did != "quiet_song" or "noise" in pr.tags:
                            if p.quiet or did != "quiet_song":
                                out.append((place, qid, pid, did))
    return out


def explain_rejection(quest: Quest, problem: Problem, diversion: Diversion) -> str:
    return (
        f"(No story: {quest.gerund} does not fit the problem '{problem.label}' with "
        f"the diversion '{diversion.label}'. The bedtime fix must genuinely help "
        f"and stay gentle.)"
    )


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def setup_world(world: World, hero: Entity, parent: Entity, quest: Quest, problem: Problem) -> None:
    world.say(f"{hero.id} was a {hero.meters.get('age_word', 'little')} child who loved quiet bedtime quests.")
    world.say(f"{hero.pronoun().capitalize()} wanted to {quest.verb}, because it would {quest.goal}.")
    world.say(f"But the clue was {problem.label}, and that made the first idea feel hard.")


def introduce_rare_object(world: World, quest: Quest) -> Entity:
    rare = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label="rare clue",
        phrase=f"a rare clue for {quest.id}",
        meters={"size": 1.0},
        memes={"wonder": 1.0},
    ))
    world.say(f"In {world.place.name}, a rare little clue waited near the bed lamp.")
    return rare


def predict_outcome(world: World, quest: Quest, problem: Problem, diversion: Diversion) -> dict:
    sim = world.copy()
    if diversion_works(quest, problem, diversion):
        return {"works": True, "noise": False}
    return {"works": False, "noise": "noise" in problem.tags}


def divert(world: World, hero: Entity, diversion: Diversion, problem: Problem) -> None:
    if diversion.id == "quiet_song":
        hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
        world.say(f"{hero.id} decided to {diversion.verb} {diversion.label} first, so the room could slow down.")
    else:
        world.say(f"{hero.id} decided to {diversion.verb} {diversion.label} first.")
    world.say(f"{diversion.method.capitalize()} {diversion.effect}.")


def enlarge(world: World, clue: Entity, hero: Entity, quest: Quest, diversion: Diversion) -> None:
    clue.meters["size"] = clue.meters.get("size", 1.0) * 2.0
    clue.memes["seen"] = clue.memes.get("seen", 0.0) + 1
    world.say(f"That helped {hero.id} enlarge the clue just enough to see its tiny shape.")
    world.say(f"The little shape became clear, and the bedtime quest suddenly made sense.")


def solve(world: World, hero: Entity, parent: Entity, quest: Quest, problem: Problem) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"{hero.id} smiled and showed {hero.pronoun('possessive')} {parent.label} the answer. "
        f"{parent.id if False else 'The parent'} nodded, proud of the careful thinking."
    )
    world.say(
        f"At the end, the rare clue was safe, the problem was solved, and {hero.id} felt "
        f"sleepy enough to tuck back under the blanket."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
quest_needs_enlarge(Q) :- needs_enlarge(Q).
problem_tag(P, T) :- tag(P, T).
diversion_help(D, T) :- helps(D, T).

compatible(Place, Q, P, D) :- place(Place), quest(Q), problem(P), diversion(D),
    quiet(Place), needs_enlarge(Q), problem_tag(P, T), diversion_help(D, T),
    not bad_pair(Q, P, D).

bad_pair("match_dream_key", _, _) :- true.
bad_pair(Q, P, "quiet_song") :- quest_needs_enlarge(Q), not problem_tag(P, "noise").
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.quiet:
            lines.append(asp.fact("quiet", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        if q.needs_enlarge:
            lines.append(asp.fact("needs_enlarge", qid))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(pr.tags):
            lines.append(asp.fact("tag", pid, t))
    for did, d in DIVERTS.items():
        lines.append(asp.fact("diversion", did))
        for t in sorted(d.helps_tags):
            lines.append(asp.fact("helps", did, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - ac:
        print("  only in python:", sorted(py - ac))
    if ac - py:
        print("  only in clingo:", sorted(ac - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_story(world: World, params: StoryParams) -> StorySample:
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"age_word": 1.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    quest = QUESTS[params.quest]
    problem = PROBLEMS[params.problem]
    diversion = DIVERTS[params.diversion]

    clue = introduce_rare_object(world, quest)
    world.para()
    setup_world(world, hero, parent, quest, problem)
    world.para()

    world.say(f"{hero.id} did not want to wake anybody, so {hero.pronoun()} looked for a softer way.")
    world.say(f"{hero.id} remembered a small problem can sometimes be solved by a gentle diversion.")
    world.say(f"{hero.id} chose to {diversion.verb} {diversion.label}.")

    predict = predict_outcome(world, quest, problem, diversion)
    if not predict["works"]:
        raise StoryError(explain_rejection(quest, problem, diversion))

    divert(world, hero, diversion, problem)
    enlarge(world, clue, hero, quest, diversion)

    world.para()
    solve(world, hero, parent, quest, problem)

    world.facts.update(
        hero=hero,
        parent=parent,
        quest=quest,
        problem=problem,
        diversion=diversion,
        clue=clue,
        resolved=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q = f["quest"]
    p = f["problem"]
    d = f["diversion"]
    return [
        f'Write a bedtime story about a child who must enlarge a rare clue to solve a quest.',
        f"Tell a gentle story where a little hero faces something {p.label} and tries {d.label}.",
        f'Write a soft bedtime tale that includes the words "enlarge", "rare", and "divert".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    quest = f["quest"]
    problem = f["problem"]
    diversion = f["diversion"]
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to do at bedtime?",
            answer=f"{hero.id} was trying to {quest.verb} so the room could feel calm and ready for sleep.",
        ),
        QAItem(
            question=f"Why was the quest hard at first?",
            answer=f"It was hard because the clue was {problem.label}, so {hero.id} needed a careful idea instead of a noisy one.",
        ),
        QAItem(
            question=f"What gentle thing did {hero.id} do instead of rushing?",
            answer=f"{hero.id} chose to {diversion.verb} {diversion.label}, which helped make the clue easier to use.",
        ),
        QAItem(
            question=f"How did the child solve the problem?",
            answer=f"{hero.id} used the diversion to enlarge the rare clue, and then the answer became clear.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does enlarge mean?",
            answer="To enlarge something means to make it bigger or easier to notice.",
        ),
        QAItem(
            question="What does rare mean?",
            answer="Rare means not common, so you do not see it very often.",
        ),
        QAItem(
            question="What does divert mean?",
            answer="To divert means to turn attention or effort toward a different path for a little while.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully about a trouble and trying a good way to fix it.",
        ),
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="bedroom", quest="find_lullaby_star", problem="too_tiny", diversion="magnifier_pillow",
                name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="nursery", quest="lift_raincloud_picture", problem="too_tiny", diversion="magnifier_pillow",
                name="Noah", gender="boy", parent="father", trait="careful"),
    StoryParams(place="bedroom", quest="match_dream_key", problem="too_high", diversion="shadow_lamp",
                name="Lina", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="hallway", quest="find_lullaby_star", problem="too_loud", diversion="quiet_song",
                name="Theo", gender="boy", parent="father", trait="sleepy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: quest, problem solving, and gentle diversion.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--diversion", choices=DIVERTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.quest and args.problem and args.diversion:
        q, p, d = QUESTS[args.quest], PROBLEMS[args.problem], DIVERTS[args.diversion]
        if not (quest_requires_enlarge(q, p) and diversion_works(q, p, d)):
            raise StoryError(explain_rejection(q, p, d))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.quest is None or c[1] == args.quest)
        and (args.problem is None or c[2] == args.problem)
        and (args.diversion is None or c[3] == args.diversion)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, problem, diversion = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, quest, problem, diversion, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    sample = build_story(world, params)
    return sample


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
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/4."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
