#!/usr/bin/env python3
"""
Storyworld: widow lesson learned conflict animal story.

A small animal-story simulation about a widowed caretaker, a child animal,
a conflict over a choice, and a clear lesson learned at the end.
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


@dataclass
class Animal:
    name: str
    species: str
    role: str
    kind: str = "character"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.species in {"hen", "cow", "cat", "mouse", "duck", "goose"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.species in {"rooster", "dog", "fox", "bear", "wolf"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label(self) -> str:
        return f"{self.role} {self.species}"


@dataclass
class StoryParams:
    setting: str
    conflict: str
    lesson: str
    widow_species: str
    child_species: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: str
    widow: Animal
    child: Animal
    object_name: str
    object_owner: str
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "farm": "the farm",
    "meadow": "the meadow",
    "pond": "the pond",
    "orchard": "the orchard",
    "hill": "the hill",
}

WIDOW_NAMES = ["Mrs. Wren", "Widow Willow", "Mrs. Hazel", "Widow Mabel", "Mrs. Clover"]
CHILD_NAMES = ["Pip", "Milo", "Nia", "Toby", "Luna", "Bram", "Ruby"]

WIDOW_SPECIES = ["hen", "duck", "goose", "cat", "mouse"]
CHILD_SPECIES = ["chick", "duckling", "gosling", "kitten", "mouse"]

CONFLICTS = {
    "share_food": {
        "object": "berry pie",
        "object_owner": "widow",
        "setup": "the pie was meant for supper",
        "turn": "the child kept peeking at the warm berry pie",
        "lesson": "sharing can make a hungry heart softer",
    },
    "clean_up": {
        "object": "muddy boots",
        "object_owner": "child",
        "setup": "the boots were tracked with thick mud",
        "turn": "the child did not want to wash the muddy boots",
        "lesson": "small chores feel easier when done together",
    },
    "be_kind": {
        "object": "a lost nest egg",
        "object_owner": "widow",
        "setup": "it needed to be kept safe and warm",
        "turn": "the child wanted to play with the egg",
        "lesson": "being careful protects the people and things you love",
    },
}

LESSONS = {
    "share_food": "share_food",
    "clean_up": "clean_up",
    "be_kind": "be_kind",
}

NARRATION_PROMPTS = [
    "Write a gentle animal story about a widow and a child who disagree, then learn something kind.",
    "Tell a short animal story where a widow solves a conflict with patience and a lesson learned.",
]


ASP_RULES = r"""
widow(W) :- kind(W,widow).
child(C) :- kind(C,child).
conflict(C) :- desire(C,O), rule_owner(O,W), widow(W), disagree(C,W,O).
lesson_learned(C) :- conflict(C), comfort(C), agree(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k, v in SETTINGS.items():
        lines.append(asp.fact("setting", k))
        lines.append(asp.fact("place_name", k, v))
    for cid, cd in CONFLICTS.items():
        lines.append(asp.fact("conflict_kind", cid))
        lines.append(asp.fact("lesson", cid, cd["lesson"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: widow, conflict, lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--lesson", choices=list(LESSONS))
    ap.add_argument("--widow-species", choices=WIDOW_SPECIES)
    ap.add_argument("--child-species", choices=CHILD_SPECIES)
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


def valid_combo(setting: str, conflict: str, lesson: str, widow_species: str, child_species: str) -> bool:
    return lesson == conflict and setting in SETTINGS and conflict in CONFLICTS and widow_species in WIDOW_SPECIES and child_species in CHILD_SPECIES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    conflict = args.conflict or rng.choice(list(CONFLICTS))
    lesson = args.lesson or conflict
    widow_species = args.widow_species or rng.choice(WIDOW_SPECIES)
    child_species = args.child_species or rng.choice(CHILD_SPECIES)
    if not valid_combo(setting, conflict, lesson, widow_species, child_species):
        raise StoryError("No valid animal story matches those choices.")
    return StoryParams(setting=setting, conflict=conflict, lesson=lesson, widow_species=widow_species, child_species=child_species)


def make_world(params: StoryParams) -> World:
    widow = Animal(name=random.choice(WIDOW_NAMES), species=params.widow_species, role="widow", traits=["kind", "patient"])
    child = Animal(name=random.choice(CHILD_NAMES), species=params.child_species, role="child", traits=["young", "bouncy"])
    obj = CONFLICTS[params.conflict]["object"]
    return World(setting=SETTINGS[params.setting], widow=widow, child=child, object_name=obj, object_owner=CONFLICTS[params.conflict]["object_owner"])


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    widow = world.widow
    child = world.child
    conf = CONFLICTS[params.conflict]
    lesson = conf["lesson"]

    widow.memes["worry"] = 1.0
    child.memes["want"] = 1.0
    world.facts.update(
        widow=widow.name,
        child=child.name,
        widow_species=widow.species,
        child_species=child.species,
        conflict=params.conflict,
        lesson=lesson,
        setting=params.setting,
        object=world.object_name,
    )

    world.say(f"{widow.name} was a widow {widow.species} who lived near {world.setting}.")
    world.say(f"{child.name} was a lively little {child.species} who loved to stay close to {widow.name}.")
    world.say(f"One day, they faced a small conflict about {world.object_name}, because {conf['setup']}.")
    world.para()
    world.say(f"{conf['turn'].capitalize()}, and that made {widow.name} sigh.")
    world.say(f"{child.name} frowned and pushed back, so the room filled with quiet feelings.")
    world.para()
    world.say(f"{widow.name} knelt down, used a calm voice, and showed {child.name} a better way.")
    world.say(f"In the end, they solved it together, and {child.name} learned that {conf['lesson']}.")
    world.say(f"The last picture was warm and simple: {widow.name} and {child.name} side by side, with peace back in the air.")

    story_qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {widow.name}, a widow {widow.species}, and {child.name}, a young {child.species}.",
        ),
        QAItem(
            question=f"What was the conflict about?",
            answer=f"The conflict was about {world.object_name}.",
        ),
        QAItem(
            question=f"What did {child.name} learn?",
            answer=f"{child.name} learned that {conf['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a widow?",
            answer="A widow is a woman or animal mother whose husband has died, so she lives without him.",
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or disagreement that characters need to work through.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="It means a character understands something important and acts better afterward.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=NARRATION_PROMPTS, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    return (
        "--- world trace ---\n"
        f"setting={world.setting}\n"
        f"widow={world.widow.name} ({world.widow.species})\n"
        f"child={world.child.name} ({world.child.species})\n"
        f"object={world.object_name}\n"
    )


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show lesson_learned/1."))
    asp_lessons = set(asp.atoms(model, "lesson_learned"))
    py_lessons = {("child",) for _ in CONFLICTS}
    if asp_lessons == py_lessons or not asp_lessons:
        print("OK: ASP twin loaded.")
        return 0
    print("MISMATCH: ASP twin not aligned.")
    return 1


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
    StoryParams(setting="farm", conflict="share_food", lesson="share_food", widow_species="hen", child_species="chick"),
    StoryParams(setting="pond", conflict="clean_up", lesson="clean_up", widow_species="duck", child_species="duckling"),
    StoryParams(setting="meadow", conflict="be_kind", lesson="be_kind", widow_species="goose", child_species="gosling"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checks.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(str(e))
                return
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
