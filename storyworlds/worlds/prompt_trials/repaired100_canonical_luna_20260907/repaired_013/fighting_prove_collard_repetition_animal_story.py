#!/usr/bin/env python3
"""
A child-facing animal story world about fighting, proving courage, and collard
leaves, where repetition turns a quarrel into cooperation.
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
    setting: str = "the leafy garden"
    hero: str = "Pip"
    friend: str = "Moss"
    challenger: str = "Brindle"
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
    "the leafy garden": {
        "mood": "bright and busy",
        "features": {"repetition", "collard", "animal"},
    },
    "the creekside patch": {
        "mood": "cool and green",
        "features": {"repetition", "collard", "animal"},
    },
    "the red barn yard": {
        "mood": "warm and dusty",
        "features": {"repetition", "collard", "animal"},
    },
}


@dataclass(frozen=True)
class Arc:
    title: str
    premise: str
    problem: str
    choice: str
    action: str
    result: str
    ending: str
    problem_answer: str
    choice_answer: str
    result_answer: str


ARCS = [
    Arc(
        title="The Collard Leaf Challenge",
        premise="Every animal in the garden knew that the largest collard leaf belonged to whoever could prove the strongest.",
        problem="Brindle the badger thumped his paws and challenged Pip to a fight beside the vegetable bed.",
        choice="Pip wanted to fight back, but Moss whispered, \"Being brave does not mean hurting someone. Ask what the garden needs.\"",
        action="Pip repeated the garden keeper's old call, \"Step, listen, share,\" and invited Brindle to pull weeds instead of pushing paws.",
        result="They worked side by side until the tangled vines loosened and the biggest collard leaf stood free.",
        ending="Pip, Moss, and Brindle shared the crisp leaf beneath the dancing bean vines",
        problem_answer="Brindle challenged Pip to a fight to decide who deserved the biggest collard leaf.",
        choice_answer="Pip chose not to fight and listened to Moss's advice to discover what the garden needed.",
        result_answer="Repeating the garden call helped the animals cooperate, clear the vines, and share the large collard leaf.",
        ),
    Arc(
        title="The Repeated Pawprint",
        premise="A row of muddy pawprints crossed the collard patch each morning, and the animals argued about who had made them.",
        problem="Brindle blamed Pip, Pip blamed Brindle, and soon both animals were ready to fight beside the seedlings.",
        choice="Moss said, \"Say it again: first we look, then we learn.\" Pip repeated the words, and Brindle slowly lowered his paw.",
        action="The three animals followed the prints again and again until the trail led to a loose gate swinging in the wind.",
        result="They fixed the gate and proved that no animal had been stealing the collards.",
        ending="the repaired gate clicked softly while three muddy noses shared one leaf",
        problem_answer="The animals nearly fought because they blamed one another for muddy prints in the collard patch.",
        choice_answer="Moss taught them to repeat a calm rule: look first and learn before fighting.",
        result_answer="Following the prints revealed a loose gate, so the animals repaired it and cleared each other's names.",
        ),
    Arc(
        title="The Strongest Bite",
        premise="A plump collard leaf hung from a high stem, and Brindle announced that only a fighter could reach it.",
        problem="He pushed Pip toward the stem, saying, \"Prove you are strong!\" Pip's feathers trembled.",
        choice="Pip answered, \"I can prove I am kind and clever.\" Moss repeated, \"Kind and clever,\" until Brindle stopped growling.",
        action="Pip held the stem low while Moss tugged a vine and Brindle used his broad back as a step.",
        result="The leaf came down without a single blow, and the animals saw that each kind of strength mattered.",
        ending="the collard leaf became three neat green ribbons on a flat stone",
        problem_answer="Brindle demanded that Pip fight to prove strength before taking the high collard leaf.",
        choice_answer="Pip chose to prove kindness and cleverness instead of accepting Brindle's fight.",
        result_answer="The animals combined their different strengths and reached the leaf without hurting one another.",
        ),
    Arc(
        title="The Echo by the Water Trough",
        premise="Near the water trough, animals repeated every angry word until the whole yard sounded like a quarrel.",
        problem="Brindle heard one sharp bark, repeated it, and mistook the echo for a new attack from Pip.",
        choice="Moss called, \"Pause, breathe, ask.\" Pip repeated it once, then Brindle repeated it too.",
        action="Each animal took one step back, named the collard leaf he wanted, and listened while the others spoke.",
        result="Their repeated calm words became a turn-taking game, and the fight melted into a fair plan.",
        ending="the trough reflected three peaceful faces beside a basket of collard leaves",
        problem_answer="An echo made Brindle think Pip was attacking, causing an angry quarrel near the trough.",
        choice_answer="The animals repeated a calm instruction to pause, breathe, and ask instead of fighting.",
        result_answer="Taking turns and listening helped them make a fair plan for sharing the collard leaves.",
        ),
    ],
]


OPENINGS = [
    "In {setting}, Pip the rabbit and Moss the mouse met beside a basket of fresh collard leaves.",
    "One bright morning in {setting}, the animals gathered where the collards grew tall.",
    "At the edge of {setting}, Pip carried a collard leaf while Moss watched the busy garden path.",
    "The animals of {setting} had one rule: no one was to fight over food.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.hero, params.friend, params.challenger))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def _story_lines(world: World) -> list[str]:
    facts = world.facts
    arc: Arc = facts["arc"]
    opening = _fill(OPENINGS[facts["opening_variant"]], facts)
    premise = _fill(arc.premise, facts)
    problem = _fill(arc.problem, facts)
    choice = _fill(arc.choice, facts)
    action = _fill(arc.action, facts)
    result = _fill(arc.result, facts)
    ending = _fill(arc.ending, facts)
    hero = facts["hero"]
    friend = facts["friend"]
    challenger = facts["challenger"]

    structures = [
        [
            opening,
            f"{premise} {problem}",
            f"\"Why should we fight?\" asked {hero}. {choice}",
            action,
            f"{result} {challenger} blinked and said, \"That proves teamwork is strong.\"",
            f"At sunset, {ending}.",
        ],
        [
            opening,
            f"{problem} \"I will prove myself!\" cried {challenger}.",
            f"{friend} shook his head. \"Repeat after me: kind words first.\" {choice}",
            f"Together they tried a better way. {action}",
            result,
            f"After that, {ending}. The garden stayed peaceful.",
        ],
        [
            f"The animals still tell the story of {arc.title}. {opening}",
            premise,
            f"Then the trouble began: {problem}",
            f"\"Listen once more,\" said {friend}. {choice}",
            action,
            f"The plan worked because no one had to be hurt. {result}",
            f"The proof was easy to see: {ending}.",
        ],
        [
            opening,
            f"{_cap(problem)} The collard leaves shook whenever the animals stomped.",
            f"\"We can repeat a better choice,\" said {hero}. {choice}",
            action,
            f"{result} Even {challenger} smiled.",
            f"That evening, {ending}, and the animals remembered that courage can be gentle.",
        ],
    ]
    return structures[facts["structure_variant"]]


ASP_RULES = r"""
setting(leafy_garden).
setting(creekside_patch).
setting(red_barn_yard).
feature(repetition).
feature(collard).
feature(animal).
can_tell_story(S) :- setting(S), feature(repetition), feature(collard), feature(animal).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTING_REGISTRY:
        key = setting.replace("the ", "").replace(" ", "_")
        lines.append(asp.fact("setting", key))
    for feature in ("repetition", "collard", "animal"):
        lines.append(asp.fact("feature", feature))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="An animal story about fighting, proving, collards, and repetition.")
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--challenger")
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Pip", "Clover", "Nell", "Bram"])
    friend = args.friend or rng.choice(["Moss", "Tilly", "Fern", "Wren"])
    challenger = args.challenger or rng.choice(["Brindle", "Rook", "Dapple", "Gorse"])
    if len({hero, friend, challenger}) < 3:
        raise StoryError("The hero, friend, and challenger must be different animals.")
    return StoryParams(setting=setting, hero=hero, friend=friend, challenger=challenger)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting}")
    if len({params.hero, params.friend, params.challenger}) < 3:
        raise StoryError("The hero, friend, and challenger must be different animals.")

    seed = _stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    world = World(setting=params.setting)

    hero = world.add(Entity(params.hero, "animal", meters={"energy": 1.0}, memes={"courage": 0.7}))
    friend = world.add(Entity(params.friend, "animal", meters={"energy": 0.8}, memes={"wisdom": 0.9}))
    challenger = world.add(Entity(params.challenger, "animal", meters={"energy": 1.0}, memes={"anger": 0.7}))
    world.add(Entity("the collard leaves", "food", meters={"freshness": 1.0}, memes={"sharing": 0.8}))
    world.add(Entity("the garden path", "place", meters={"safety": 0.8}, memes={"belonging": 0.7}))

    facts = {
        "hero": hero.name,
        "friend": friend.name,
        "challenger": challenger.name,
        "setting": params.setting,
        "arc": arc,
        "opening_variant": (seed // len(ARCS)) % len(OPENINGS),
        "structure_variant": (seed // (len(ARCS) * len(OPENINGS))) % 4,
    }
    world.facts.update(facts)
    story = "\n\n".join(_story_lines(world))

    prompts = [
        f"Write an animal story about {params.hero}, {params.friend}, and {params.challenger} in {params.setting}.",
        "Include a fight that is solved without hurting anyone.",
        "Use repetition and a collard leaf to show how an animal proves courage.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did the animals face in \"{arc.title}\"?",
            answer=arc.problem_answer,
        ),
        QAItem(
            question="How did the animals choose a better path than fighting?",
            answer=arc.choice_answer,
        ),
        QAItem(
            question="What did their repeated words or actions help them do?",
            answer=arc.result_answer,
        ),
        QAItem(
            question=f"How does \"{arc.title}\" end?",
            answer=f"It ends with {arc.ending.format(hero=params.hero, friend=params.friend, challenger=params.challenger, setting=params.setting)}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does it mean to prove something?",
            answer="To prove something means to show that it is true through words, choices, or actions.",
        ),
        QAItem(
            question="Why can fighting be dangerous?",
            answer="Fighting can hurt bodies and feelings, so peaceful choices are safer when they are possible.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means saying or doing something again, often to help remember it or make it clear.",
        ),
        QAItem(
            question="What are collard leaves?",
            answer="Collard leaves are large green leaves that people and some animals can eat.",
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


def _valid_python() -> list[str]:
    return sorted(setting.replace("the ", "").replace(" ", "_") for setting in SETTING_REGISTRY)


def _asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_tell_story/1."))
    return sorted(set(asp.atoms(model, "can_tell_story")))


def asp_verify() -> int:
    py = {(setting,) for setting in _valid_python()}
    clingo = set(_asp_valid())
    if py == clingo:
        print(f"OK: clingo gate matches python ({len(py)} settings).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - clingo))
    print("clingo only:", sorted(clingo - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_tell_story/1."))
        return
    if args.verify:
        status = asp_verify()
        if status:
            sys.exit(status)
        for seed in range(3):
            params = StoryParams(seed=seed)
            sample = generate(params)
            if not sample.story or "{" in sample.story or "}" in sample.story:
                raise StoryError("Generated story failed its prose check.")
        print("OK: generated stories pass prose checks.")
        return
    if args.asp:
        for item in _asp_valid():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTING_REGISTRY:
            samples.append(
                generate(
                    StoryParams(
                        setting=setting,
                        hero="Pip",
                        friend="Moss",
                        challenger="Brindle",
                        seed=base_seed,
                    )
                )
            )
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            seed = base_seed + index
            index += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
