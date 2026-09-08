#!/usr/bin/env python3
"""
A gentle ghost story about a pantry, a fourth bell, and teamwork.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the old village house"
    hero: str = "Luna"
    helper: str = "Pip"
    ghost: str = "the pantry ghost"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "the old village house": {"mood": "creaky and moonlit", "pantry": "a narrow pantry under the stairs"},
    "the seaside cottage": {"mood": "salt-damp and quiet", "pantry": "a little pantry beside the kitchen"},
    "the hilltop inn": {"mood": "windy and warm", "pantry": "a crowded pantry behind the dining room"},
}

STORY_ARCS = [
    {
        "title": "The Fourth Candle",
        "problem": "On the fourth night, a blue pantry flame would not go out, and its cold light frightened everyone away from the food shelves.",
        "choice": "{hero} wanted to hide under the table, but {helper} whispered, \"We can face it together.\"",
        "action": "They carried a bowl of salt, a wool blanket, and a small bell into the pantry.",
        "turn": "The ghost appeared beside the flour jars and said, \"I am not trying to scare you. I cannot find the fourth candle that keeps my old promise.\"",
        "resolution": "The children searched as a team, lifting boxes and sharing the light until they found the candle beneath a basket of apples.",
        "ending": "When they extinguished the blue flame, the ghost smiled, and the pantry filled with the warm smell of cinnamon bread.",
        "problem_answer": "A blue flame burned in the pantry on the fourth night, frightening people away from the shelves.",
        "choice_answer": "Luna and Pip chose to enter the pantry together instead of hiding.",
        "resolution_answer": "They worked together to find the lost fourth candle beneath an apple basket.",
    },
    {
        "title": "The Ghost in the Flour",
        "problem": "A white handprint appeared in the pantry flour every evening, followed by a lonely knocking from behind the shelves.",
        "choice": "\"We should ask what the ghost needs,\" said {hero}. \"And we should bring a lantern,\" answered {helper}.",
        "action": "The friends entered shoulder to shoulder and placed the lantern between them.",
        "turn": "The ghost rose from the flour and explained, \"My supper bell has rung three times, but nobody hears the fourth ring.\"",
        "resolution": "Together they cleared a fallen jar, found the tiny bell, and tied it to the pantry door.",
        "ending": "The fourth ring sounded sweetly, and the ghost faded after thanking them with a bright little bow.",
        "problem_answer": "Ghostly handprints and knocking showed that someone was trapped or lonely behind the pantry shelves.",
        "choice_answer": "Luna and Pip decided to listen to the ghost and enter the pantry together.",
        "resolution_answer": "They found and hung the missing supper bell so the ghost could hear its fourth ring.",
    },
    {
        "title": "The Pantry Door at Midnight",
        "problem": "At midnight the pantry door opened by itself, and a chilly ghost wind began to extinguish every lamp in the house.",
        "choice": "{helper} grabbed a broom, while {hero} took the last lantern. \"Not to chase the ghost,\" said {hero}, \"but to show it the way.\"",
        "action": "They followed the wind in careful steps, replacing each darkened lamp as they went.",
        "turn": "At the pantry's back wall, the ghost confessed, \"I have been lost since the fourth bell, and darkness follows me.\"",
        "resolution": "The friends made a bright trail with four lamps and invited the ghost to follow it outside.",
        "ending": "The wind stopped, the lamps glowed, and the ghost became a friendly silver shape by the garden gate.",
        "problem_answer": "A ghostly wind opened the pantry and extinguished the lamps throughout the house.",
        "choice_answer": "Luna and Pip used light to help the ghost rather than trying to chase it away.",
        "resolution_answer": "They made a trail of four lamps that led the lost ghost safely outside.",
    },
    {
        "title": "The Fourth Jar",
        "problem": "Three pantry jars rattled at sunset, but the fourth jar stayed silent and cold beneath a dusty cloth.",
        "choice": "\"Let us lift it together,\" said {hero}. \"Then we will know its story,\" said {helper}.",
        "action": "They held the jar between them and carried it to the window.",
        "turn": "A tiny ghost rose from the jar and said, \"I was waiting for someone kind enough to share the last moon-sugar.\"",
        "resolution": "The children divided the sugar into two spoons and offered the rest to the ghost.",
        "ending": "The fourth jar chimed, the ghost laughed, and every pantry shelf shone like a row of stars.",
        "problem_answer": "A silent fourth jar hid beneath a cloth while the other pantry jars rattled mysteriously.",
        "choice_answer": "Luna and Pip lifted the jar together so they could discover its story.",
        "resolution_answer": "They shared the moon-sugar with the ghost, which made the fourth jar ring happily.",
    },
]


OPENINGS = [
    "On a quiet evening in {setting}, {hero} heard a soft tapping from the pantry.",
    "The moon was high above {setting} when {hero} noticed that the pantry door stood open.",
    "Everyone in {setting} knew not to visit the pantry after dark, but {hero} and {helper} heard a tiny fourth bell.",
    "In the oldest room of {setting}, shadows gathered around the pantry shelves.",
]


def stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.hero, params.helper, params.ghost))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def fill(text: str, values: dict[str, object]) -> str:
    return text.format(**values)


def sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:]


def build_world(params: StoryParams) -> World:
    seed = stable_seed(params)
    arc = STORY_ARCS[seed % len(STORY_ARCS)]
    world = World(params.setting)
    world.add(Entity(params.hero, "child", meters={"courage": 0.5}, memes={"teamwork": 0.8}))
    world.add(Entity(params.helper, "child", meters={"courage": 0.6}, memes={"teamwork": 0.9}))
    world.add(Entity(params.ghost, "ghost", meters={"spookiness": 0.7}, memes={"loneliness": 1.0}))
    world.add(Entity("the pantry", "place", meters={"shelves": 1.0, "lamps": 4.0}))
    world.add(Entity("the fourth candle", "object", meters={"flame": 1.0}))
    world.facts.update(
        hero=params.hero,
        helper=params.helper,
        ghost=params.ghost,
        setting=params.setting,
        arc=arc,
        opening_variant=(seed // len(STORY_ARCS)) % len(OPENINGS),
        structure_variant=(seed // (len(STORY_ARCS) * len(OPENINGS))) % 4,
        theme="teamwork and a happy ending",
    )
    return world


def story_lines(world: World) -> list[str]:
    f = world.facts
    arc = f["arc"]
    values = {k: f[k] for k in ("hero", "helper", "ghost", "setting")}
    opening = fill(OPENINGS[f["opening_variant"]], values)
    problem = fill(arc["problem"], values)
    choice = fill(arc["choice"], values)
    action = fill(arc["action"], values)
    turn = fill(arc["turn"], values)
    resolution = fill(arc["resolution"], values)
    ending = fill(arc["ending"], values)

    structures = [
        [
            f"{opening} This became known as \"{arc['title']}\".",
            problem,
            choice,
            action,
            turn,
            resolution,
            ending,
        ],
        [
            opening,
            f"\"Did you hear that?\" asked {f['helper']}. {problem}",
            f"{f['hero']} took a slow breath. {choice}",
            action,
            turn,
            resolution,
            ending,
        ],
        [
            f"The story of \"{arc['title']}\" begins with {opening[0].lower() + opening[1:]}",
            sentence_start(problem),
            f"\"We do not have to be brave alone,\" said {f['hero']}. {choice}",
            action,
            turn,
            resolution,
            f"After that, {ending[0].lower() + ending[1:]} Everyone in the house remembered that teamwork can turn a ghost story into a happy ending.",
        ],
        [
            f"Before the pantry became peaceful, {opening[0].lower() + opening[1:]}",
            f"First came the trouble: {problem[0].lower() + problem[1:]}",
            f"{f['helper']} asked, \"What should we do?\" {f['hero']} answered, \"We will find out together.\" {choice}",
            action,
            turn,
            resolution,
            f"At last, {ending[0].lower() + ending[1:]} The old house felt safe and cheerful again.",
        ],
    ]
    return structures[f["structure_variant"]]


ASP_RULES = r"""
place(pantry).
signal(fourth).
feature(teamwork).
ending(happy).

story_ok :- place(pantry), signal(fourth), feature(teamwork), ending(happy).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "pantry"),
            asp.fact("signal", "fourth"),
            asp.fact("feature", "teamwork"),
            asp.fact("ending", "happy"),
        ]
    )


def asp_program(show: str = "#show story_ok/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle pantry ghost story about teamwork.")
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--ghost")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Luna", "Milo", "Nora", "Ivy"])
    helper = args.helper or rng.choice(["Pip", "Tess", "Ollie", "Bea"])
    ghost = args.ghost or rng.choice(["the pantry ghost", "the silver ghost", "the gentle ghost"])
    if hero == helper:
        raise StoryError("The hero and helper must be different characters.")
    if not hero.strip() or not helper.strip():
        raise StoryError("Character names cannot be empty.")
    return StoryParams(setting=setting, hero=hero, helper=helper, ghost=ghost)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    f = world.facts
    arc = f["arc"]
    story = "\n\n".join(story_lines(world))
    prompts = [
        f"Write a gentle ghost story about {params.hero} and {params.helper} helping a ghost in a pantry.",
        "Tell a child-facing story involving a fourth bell, teamwork, and a happy ending.",
        f"Write a spooky but kind tale set in {params.setting}.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.helper} find in the pantry?",
            answer=arc["problem_answer"],
        ),
        QAItem(
            question="How did the children use teamwork?",
            answer=arc["choice_answer"],
        ),
        QAItem(
            question="How was the ghost's problem resolved?",
            answer=arc["resolution_answer"],
        ),
        QAItem(
            question=f"What kind of ending did \"{arc['title']}\" have?",
            answer="It ended happily: the ghost was helped, the pantry became peaceful, and the children were safe.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a pantry?",
            answer="A pantry is a room or cupboard where food and kitchen supplies are stored.",
        ),
        QAItem(
            question="What does extinguish mean?",
            answer="To extinguish something means to put out a flame or light.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people cooperate and share their efforts to solve a problem.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spirit character that is often said to remain after a person has died.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending shows that the danger or problem has been safely resolved.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(f"{entity.name}: kind={entity.kind}, meters={dict(entity.meters)}, memes={dict(entity.memes)}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if asp.atoms(model, "story_ok") == [()]:
        print("OK: ASP gate confirms pantry, fourth, extinguish, teamwork, and happy ending.")
        return 0
    print("ASP gate failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/0."))
        for atom in asp.atoms(model, "story_ok"):
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTING_REGISTRY:
            samples.append(
                generate(
                    StoryParams(
                        setting=setting,
                        hero="Luna",
                        helper="Pip",
                        ghost="the pantry ghost",
                        seed=base_seed,
                    )
                )
            )
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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
