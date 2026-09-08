#!/usr/bin/env python3
"""
A small storyworld about a rehearsal, a curious question, and teamwork.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Luna"
    friend_name: str = "Milo"
    mentor_name: str = "Nia"
    show_name: str = "the Lantern Friends"


NAMES = ["Luna", "Milo", "Nia", "Zuri", "Theo", "Ivy", "Sam", "Pip"]
SHOW_NAMES = ["the Lantern Friends", "the Little Acorns", "the Moonbeam Team", "the Rainbow Garden"]

SCENES = [
    {
        "place": "a warm library room",
        "prop": "a cardboard moon",
        "problem": "the moon kept tilting whenever the actors lifted it",
        "clue": "a loose wooden dowel hidden inside the moon",
        "fix": "they added a second handle and practiced lifting together",
        "ending": "the cardboard moon rose straight above the smiling audience",
        "lesson": "Questions can uncover the small change that helps everyone",
    },
    {
        "place": "a sunny community hall",
        "prop": "a row of paper stars",
        "problem": "the stars tangled when the curtain opened",
        "clue": "their strings were tied to one crowded hook",
        "fix": "they spread the strings across three hooks and tested the curtain slowly",
        "ending": "the stars swept across the stage like a bright little sky",
        "lesson": "A curious look can turn a tangle into a team plan",
    },
    {
        "place": "a green school courtyard",
        "prop": "a painted cardboard boat",
        "problem": "the boat wobbled during the rehearsal",
        "clue": "one wheel was smaller than the others",
        "fix": "they measured the wheels, made a matching one, and pushed the boat side by side",
        "ending": "the boat glided across the pretend sea while everyone cheered",
        "lesson": "Careful noticing and shared work make brave performances safer",
    },
    {
        "place": "a little theater beside the park",
        "prop": "a red fox tail",
        "problem": "the tail slipped off during every dance",
        "clue": "its ribbon was smooth instead of knotted",
        "fix": "they sewed a soft loop and asked the dancer to test each step",
        "ending": "the fox twirled, and the tail stayed in place for the final bow",
        "lesson": "Teamwork grows when people test a solution together",
    },
    {
        "place": "a bright art-room stage",
        "prop": "a cardboard castle door",
        "problem": "the door would not open on the important line",
        "clue": "a paintbrush had dried beside its hinge",
        "fix": "they cleaned the hinge and gave one actor the job of opening it gently",
        "ending": "the castle door swung wide just as the heroes arrived",
        "lesson": "Curiosity helps a team find what is really blocking the way",
    },
]


def _setup(world: World, params: StoryParams) -> None:
    child = world.add(Entity(params.child_name, "character", "child", params.child_name))
    friend = world.add(Entity(params.friend_name, "character", "child", params.friend_name))
    mentor = world.add(Entity(params.mentor_name, "character", "mentor", params.mentor_name))
    stage = world.add(Entity("stage", "place", "stage", "practice stage"))
    child.meters["curiosity"] = 1.0
    child.memes["confidence"] = 0.4
    friend.meters["teamwork"] = 1.0
    friend.memes["patience"] = 0.8
    mentor.meters["guidance"] = 1.0
    stage.meters["readiness"] = 0.3
    world.facts.update(child=child, friend=friend, mentor=mentor, stage=stage)


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        f"{params.child_name}|{params.friend_name}|{params.mentor_name}|{params.show_name}"
    ))


def tell_story(params: StoryParams) -> World:
    if params.child_name == params.friend_name:
        raise StoryError("The curious child and teammate must have different names.")
    if params.show_name not in SHOW_NAMES:
        raise StoryError(f"Unknown show name: {params.show_name}")
    world = World()
    _setup(world, params)
    child = world.facts["child"]
    friend = world.facts["friend"]
    mentor = world.facts["mentor"]
    stage = world.facts["stage"]
    scene = SCENES[_token(params) % len(SCENES)]

    world.say(
        f"In {scene['place']}, {child.label}, {friend.label}, and {mentor.label} held a rehearsal "
        f"for {params.show_name}."
    )
    world.say(
        f"The children were excited to use {scene['prop']}, but during the first run-through "
        f"{scene['problem']}."
    )
    world.say(
        f'"Why does it happen only when we reach this part?" {child.label} asked. '
        f'"Let us look closely instead of guessing," {friend.label} replied.'
    )
    world.para()
    world.say(
        f"{child.label} followed the prop with curious eyes while {friend.label} held the scene still. "
        f"{mentor.label} invited them to check every piece gently."
    )
    world.say(f"They discovered {scene['clue']}.")
    world.say(
        f'"I noticed it because I wondered what changed," {child.label} said. '
        f'"And we can fix it together," {friend.label} answered.'
    )
    world.para()
    world.say(f"The team {scene['fix']}.")
    world.say(
        f"They rehearsed the tricky moment three times, listening to one another and changing the plan "
        f"whenever someone had a useful idea."
    )
    world.say(
        f"At last, the rehearsal felt ready. {stage.label.capitalize()} readiness rose from a shaky start "
        f"to a calm, shared confidence."
    )
    world.para()
    world.say(
        f"That evening, {scene['ending']}. {child.label} looked at {friend.label} and smiled."
    )
    world.say(
        f'"I am glad I asked why," {child.label} said. '
        f'"I am glad we answered as a team," {friend.label} replied.'
    )
    world.say(f"{scene['lesson']}.")
    world.say(
        f"After the final bow, {mentor.label} hugged them both, and their warm laughter filled the room."
    )

    child.memes["confidence"] = 1.0
    stage.meters["readiness"] = 1.0
    world.facts.update(scene=scene, params=params, scene_index=_token(params) % len(SCENES))
    world.fired.update({("noticed_problem",), ("asked_question",), ("worked_together",), ("successful_rehearsal",)})
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    scene = world.facts["scene"]
    return [
        f"Write a heartwarming rehearsal story about {p.child_name}, {p.friend_name}, and {p.mentor_name}.",
        f"Show how curiosity reveals {scene['clue']} and teamwork leads to {scene['fix']}.",
        f"End with a warm performance image proving that the rehearsal succeeded.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    scene = world.facts["scene"]
    return [
        QAItem(
            f"Where did {p.child_name}, {p.friend_name}, and {p.mentor_name} hold their rehearsal?",
            f"They held their rehearsal in {scene['place']} for {p.show_name}.",
        ),
        QAItem(
            "What went wrong during the first run-through?",
            f"{scene['problem'].capitalize()}.",
        ),
        QAItem(
            f"How did {p.child_name}'s curiosity help?",
            f"{p.child_name} asked why the problem happened and helped discover {scene['clue']}.",
        ),
        QAItem(
            f"How did the children use teamwork?",
            f"They {scene['fix']}, then rehearsed the tricky moment while listening to one another.",
        ),
        QAItem(
            "What showed that the rehearsal became successful?",
            f"{scene['ending'].capitalize()}",
        ),
        QAItem(
            "What did the children learn?",
            f"They learned that {scene['lesson'].lower()}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a rehearsal?", "A rehearsal is a practice session before a performance."),
        QAItem("What does curiosity mean?", "Curiosity means wanting to learn why something happens or how it works."),
        QAItem("What is teamwork?", "Teamwork means people cooperate, share ideas, and help one another reach a goal."),
    ]


ASP_RULES = r"""
noticed_problem(S) :- rehearsal(S), problem(S).
asked_question(S) :- noticed_problem(S), curiosity(S).
worked_together(S) :- asked_question(S), teamwork(S).
successful_rehearsal(S) :- worked_together(S), repaired(S).
valid_story(S) :- rehearsal(S), successful_rehearsal(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("rehearsal", "story1"),
        asp.fact("problem", "story1"),
        asp.fact("curiosity", "story1"),
        asp.fact("teamwork", "story1"),
        asp.fact("repaired", "story1"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    actual = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if actual == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(actual))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming rehearsal storyworld about curiosity and teamwork.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend-name", choices=NAMES)
    parser.add_argument("--mentor-name", choices=NAMES)
    parser.add_argument("--show-name", choices=SHOW_NAMES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.name or rng.choice(NAMES)
    choices = [n for n in NAMES if n != child]
    friend = args.friend_name or rng.choice(choices)
    mentor_choices = [n for n in NAMES if n not in {child, friend}]
    mentor = args.mentor_name or rng.choice(mentor_choices)
    return StoryParams(
        seed=None,
        child_name=child,
        friend_name=friend,
        mentor_name=mentor,
        show_name=args.show_name or rng.choice(SHOW_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
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


CURATED = [
    StoryParams(child_name="Luna", friend_name="Milo", mentor_name="Nia", show_name="the Lantern Friends"),
    StoryParams(child_name="Zuri", friend_name="Theo", mentor_name="Ivy", show_name="the Moonbeam Team"),
    StoryParams(child_name="Sam", friend_name="Pip", mentor_name="Luna", show_name="the Little Acorns"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
