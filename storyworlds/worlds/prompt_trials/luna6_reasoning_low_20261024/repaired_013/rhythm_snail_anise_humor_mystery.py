#!/usr/bin/env python3
"""
A small comic mystery in which a snail's steady rhythm and a pinch of anise
help friends discover who has been moving the moonlit garden's little bell.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_HERE = os.path.abspath(__file__)
for _parent in (_HERE, *[os.path.join(os.path.dirname(_HERE), *([]))]):
    pass
_ROOT = os.path.dirname(_HERE)
while True:
    if os.path.isfile(os.path.join(_ROOT, "storyworlds", "results.py")):
        sys.path.insert(0, os.path.join(_ROOT, "storyworlds"))
        break
    _next = os.path.dirname(_ROOT)
    if _next == _ROOT:
        break
    _ROOT = _next
if "storyworlds" not in sys.modules:
    _candidate = os.path.join(os.path.dirname(_HERE), "storyworlds")
    if os.path.isfile(os.path.join(_candidate, "results.py")):
        sys.path.insert(0, _candidate)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the moonlit garden"
    hero: str = "Luna"
    friend: str = "Pip"
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
    "the moonlit garden": {"mood": "silver and hushed", "clue": "a damp, glittering trail"},
    "the sleepy greenhouse": {"mood": "warm and foggy", "clue": "a wiggly line in the potting dust"},
    "the clockwork orchard": {"mood": "tick-tocking and leafy", "clue": "a trail of tiny leaf-shaped dents"},
}

HUMOR_BEATS = [
    "A sleepy moth landed on Pip's nose and mistook it for a very small hill.",
    "A beetle wearing a cherry stem as a hat marched past as if it were the chief inspector.",
    "Pip sneezed at a puff of pollen, and the echo made a nearby pumpkin say, \"Pardon me!\"",
    "A tiny frog tried to hide behind a mushroom, though its two large eyes remained in plain view.",
]

MYSTERIES = [
    {
        "title": "The Case of the Vanishing Bell",
        "problem": "The garden bell had vanished from its little blue post, though no one had heard it ring.",
        "clue": "The snail noticed that the damp trail curved toward the rosemary bed, then doubled back.",
        "suspect": "a careful hedgehog named Bramble",
        "truth": "Bramble had tucked the bell beneath a leaf so its ringing would not wake a nest of baby birds.",
        "solution": "Luna asked Bramble about the trail instead of accusing him, and Pip tapped a gentle rhythm on the post.",
        "result": "Bramble came out, explained the nest, and helped them hang the bell where it could be muffled at night.",
        "ending": "the bell hung under a soft leaf while three baby birds slept through the evening breeze",
        "answer_problem": "The garden bell was missing from its post, and nobody knew where it had gone.",
        "answer_clue": "The snail followed a damp trail that curved toward the rosemary bed and then doubled back.",
        "answer_turn": "Luna asked a question rather than accusing Bramble, and Pip used a gentle rhythm to call him out.",
        "answer_result": "Bramble explained that he had hidden the bell to protect the baby birds, and everyone found a quieter place for it.",
    },
    {
        "title": "The Mystery of the Anise Crumbs",
        "problem": "A jar of anise seeds had tipped over, but the sweet-smelling crumbs disappeared before breakfast.",
        "clue": "The snail followed the scent and found a neat crumb trail leading beneath a large watering can.",
        "suspect": "a shy mouse named Tumble",
        "truth": "Tumble had carried the seeds away to share with a sick friend who could not leave its nest.",
        "solution": "Pip hummed the snail's slow rhythm, and Luna sprinkled a little anise near the watering can.",
        "result": "Tumble stepped out, admitted what happened, and invited them to bring the rest of the seeds to the nest.",
        "ending": "a tiny bowl of anise sat beside the nest, and the empty jar held one bright daisy",
        "answer_problem": "The anise seeds had spilled from their jar and vanished before breakfast.",
        "answer_clue": "A sweet scent and a trail of crumbs led the snail beneath the watering can.",
        "answer_turn": "The friends used a familiar rhythm and a little anise scent to invite Tumble out instead of startling him.",
        "answer_result": "Tumble had taken the seeds to help a sick friend, and the group shared the rest with the nest.",
    },
    {
        "title": "The Three-Tap Riddle",
        "problem": "Someone tapped three times on the greenhouse glass each night, but the garden keeper found no visitor.",
        "clue": "The snail matched the taps to its own steady pace and traced them to a loose vine against the pane.",
        "suspect": "a young robin named Rilla",
        "truth": "Rilla had been tapping the glass with her beak to ask for help reaching a fallen ribbon.",
        "solution": "Luna tapped the rhythm back, while Pip held out a pinch of anise to draw the robin near.",
        "result": "Rilla answered with a chirp, and the friends lifted the ribbon from the thorny path together.",
        "ending": "the ribbon rested safely on the robin's nest, and three gentle taps became their hello",
        "answer_problem": "Three mysterious taps sounded on the greenhouse glass each night.",
        "answer_clue": "The snail recognized the taps' steady rhythm and found a loose vine touching the glass.",
        "answer_turn": "Luna tapped back and Pip offered anise, turning the strange signal into a friendly invitation.",
        "answer_result": "Rilla had been asking for help with a fallen ribbon, and the friends lifted it from the thorny path.",
    },
    {
        "title": "The Case of the Crooked Seed Row",
        "problem": "A perfectly straight row of moonflower seeds had become a wobbly zigzag overnight.",
        "clue": "The snail found tiny round marks between the seeds and a faint dusting of anise on a stepping stone.",
        "suspect": "a bumblebee named Bop",
        "truth": "Bop had nudged the seed markers while practicing a dance to the garden's evening rhythm.",
        "solution": "Pip asked Bop to show the dance, and Luna listened for the beat before resetting the markers.",
        "result": "The friends planted the seeds along Bop's cheerful zigzag, leaving room for every sprout.",
        "ending": "a crooked row of seedlings made a green dance line beneath the moon",
        "answer_problem": "The straight moonflower seed row had become a zigzag.",
        "answer_clue": "The snail found round marks and a trace of anise on a nearby stepping stone.",
        "answer_turn": "Pip invited Bop to show the dance, and Luna listened to its rhythm instead of blaming the bee.",
        "answer_result": "Bop had moved the markers while dancing, so the friends made the zigzag into a roomy planting row.",
    },
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.hero, params.friend))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _valid_params(params: StoryParams) -> None:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting {params.setting!r}; choose one of the registered gardens.")
    if not params.hero.strip() or not params.friend.strip():
        raise StoryError("The detective and their friend must both have names.")
    if params.hero.strip().casefold() == params.friend.strip().casefold():
        raise StoryError("The detective and friend must be different characters.")


def generate(params: StoryParams) -> StorySample:
    _valid_params(params)
    seed = _stable_seed(params)
    rng = random.Random(seed)
    mystery = MYSTERIES[seed % len(MYSTERIES)]
    humor = HUMOR_BEATS[(seed // len(MYSTERIES)) % len(HUMOR_BEATS)]
    setting_info = SETTING_REGISTRY[params.setting]
    snail_name = "the garden snail"
    world = World(setting=params.setting)
    hero = world.add(Entity(params.hero, "detective", memes={"curiosity": 0.7, "kindness": 0.7}))
    friend = world.add(Entity(params.friend, "friend", memes={"humor": 0.8, "patience": 0.6}))
    snail = world.add(Entity(snail_name, "snail", meters={"pace": 0.15, "trail_length": 0.0}, memes={"observation": 0.9}))
    world.add(Entity("anise seeds", "spice", meters={"scent": 0.8, "amount": 1.0}))
    world.add(Entity("the garden bell", "clue", meters={"located": 0.0}, memes={"mystery": 0.8}))
    world.facts.update(
        mystery=mystery,
        humor=humor,
        clue=setting_info["clue"],
        suspect=mystery["suspect"],
        truth=mystery["truth"],
        solved=True,
        rhythm_used=True,
        anise_used=True,
        seed=seed,
    )
    snail.meters["trail_length"] = 1.0
    world.entities["the garden bell"].meters["located"] = 1.0

    opening = (
        f"At dusk, {params.hero} and {params.friend} arrived at {params.setting}, "
        f"where the air was {setting_info['mood']}."
    )
    story = "\n\n".join(
        [
            f"{opening} They had come to investigate \"{mystery['title']}\" because {mystery['problem'][0].lower() + mystery['problem'][1:]}",
            f"\"What can a snail tell us?\" {params.friend} whispered. \"More than a hurried person,\" said {params.hero}. "
            f"The snail began its slow search, following {setting_info['clue']} until it found that {mystery['clue'][0].lower() + mystery['clue'][1:]}",
            humor,
            f"Nearby waited {mystery['suspect']}. \"Did you see what happened?\" asked {params.hero}. "
            f"\"I might have,\" the suspect replied, \"but I was afraid you would laugh.\" "
            f"{params.friend} smiled. \"We only laugh with you, not at you.\"",
            f"Then {params.friend} tapped the snail's patient rhythm while {params.hero} set down a pinch of anise. "
            f"{mystery['solution']} The familiar beat made the quiet garden feel safe enough for the truth.",
            f"{mystery['truth']} {mystery['result']}",
            f"By moonrise, {mystery['ending']}. The friends left the garden smiling, with the snail's shining trail leading them home.",
        ]
    )
    prompts = [
        f"Write a child-friendly mystery about {params.hero}, {params.friend}, and a snail in {params.setting}.",
        "Use a steady rhythm and anise as clues, with gentle humor and a kind solution.",
        "Make the characters talk, discover the truth, and end with a concrete image of what changed.",
    ]
    story_qa = [
        QAItem(question=f"What was the mystery in \"{mystery['title']}\"?", answer=mystery["answer_problem"]),
        QAItem(question="What clue helped the friends investigate?", answer=mystery["answer_clue"]),
        QAItem(question="How did humor and rhythm help the investigation?", answer=f"The joke made the search feel friendly, and the friends used a gentle rhythm to invite the shy suspect to speak. {mystery['answer_turn']}"),
        QAItem(question="What was really happening, and how was it resolved?", answer=f"{mystery['truth']} {mystery['answer_result']}"),
        QAItem(question="What image ends the story?", answer=f"The story ends with {mystery['ending']}."),
    ]
    world_qa = [
        QAItem(question="What is a snail?", answer="A snail is a small animal with a soft body and, often, a shell; it moves by gliding on a muscular foot."),
        QAItem(question="What is anise?", answer="Anise is an aromatic plant whose seeds have a sweet, licorice-like scent and flavor."),
        QAItem(question="What is rhythm?", answer="Rhythm is a pattern of sounds or movements that repeats in a regular or recognizable way."),
        QAItem(question="How can humor help friends?", answer="Gentle humor can help people feel relaxed and welcome, especially when they are nervous."),
        QAItem(question="What does a detective do?", answer="A detective looks carefully for clues and asks questions to understand what happened."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


ASP_RULES = r"""
setting(moonlit_garden).
setting(sleepy_greenhouse).
setting(clockwork_orchard).
feature(humor).
feature(rhythm).
feature(snail).
feature(anise).
reasonable(S) :- setting(S), feature(humor), feature(rhythm), feature(snail), feature(anise).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTING_REGISTRY:
        key = setting.removeprefix("the ").replace(" ", "_")
        lines.append(asp.fact("setting", key))
    for feature in ("humor", "rhythm", "snail", "anise"):
        lines.append(asp.fact("feature", feature))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _python_valid() -> set[tuple]:
    return {(setting.removeprefix("the ").replace(" ", "_"),) for setting in SETTING_REGISTRY}


def _asp_valid() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/1."))
    return set(asp.atoms(model, "reasonable"))


def asp_verify() -> int:
    try:
        python = _python_valid()
        clingo = _asp_valid()
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if python != clingo:
        print("MISMATCH between Python and ASP reasonableness gates.")
        print("python only:", sorted(python - clingo))
        print("ASP only:", sorted(clingo - python))
        return 1
    for index in range(len(MYSTERIES) * len(HUMOR_BEATS)):
        sample = generate(StoryParams(seed=index))
        if not sample.story.strip() or len(sample.story_qa) < 3:
            print(f"Generated-story check failed at seed {index}.")
            return 1
        if not all(word in sample.story.lower() for word in ("snail", "anise", "rhythm")):
            print(f"Story content check failed at seed {index}.")
            return 1
    print(f"OK: ASP matches Python ({len(python)} settings); generated stories passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a humorous snail-and-anise garden mystery.")
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
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
    hero = args.hero or rng.choice(["Luna", "Milo", "Nell", "Ari"])
    friend = args.friend or rng.choice(["Pip", "Tess", "Bo", "Mira"])
    params = StoryParams(
        setting=args.setting or rng.choice(list(SETTING_REGISTRY)),
        hero=hero,
        friend=friend,
        seed=args.seed,
    )
    _valid_params(params)
    return params


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(f"{entity.name}: kind={entity.kind}, meters={dict(entity.meters)}, memes={dict(entity.memes)}")
        print(f"facts: {sample.world.facts}")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1 and not args.all:
        raise SystemExit("-n must be at least 1.")
    if args.show_asp:
        print(asp_program("#show reasonable/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            for setting in sorted(_asp_valid()):
                print(setting[0])
        except Exception as exc:
            raise SystemExit(f"Could not run ASP: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for index, setting in enumerate(SETTING_REGISTRY):
            samples.append(generate(StoryParams(setting=setting, seed=base_seed + index)))
    else:
        for index in range(args.n):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return
    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
