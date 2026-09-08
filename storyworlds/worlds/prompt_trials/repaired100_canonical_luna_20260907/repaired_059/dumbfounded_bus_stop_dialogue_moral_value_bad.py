#!/usr/bin/env python3
"""
A small mystery storyworld at a bus stop. A dumbfounded child follows a
misleading clue, has a brief dialogue with a helpful stranger, and learns that
a moral value matters even when a bad ending seems possible.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    companion: str
    object_name: str
    setting: str = "bus stop"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


NAMES = ["Luna", "Milo", "Pia", "Nora", "Theo", "Ivy", "Sam", "June"]
COMPANIONS = ["small dog", "grandmother", "friend", "pigeon", "little brother"]
OBJECTS = ["red umbrella", "blue backpack", "silver key", "paper parcel", "yellow scarf"]

SCENARIOS = [
    {
        "key": "backward_arrow",
        "premise": "a paper arrow on the pavement pointed away from the bus stop",
        "problem": "the arrow looked like a secret clue, but following it would lead Luna toward a busy crossing",
        "clue": "the paper was damp on one side, showing that wind had turned it around",
        "dialogue": "'A clue should not make us ignore the street,' the driver said. 'What else do you notice?' Luna answered, 'The wind, and the real sign above us.'",
        "action": "Luna stayed beside the shelter, checked the printed route sign, and asked the driver before moving",
        "result": "the bus arrived at the correct stop, while a worker safely collected the loose paper",
        "ending": "the false arrow curled into a wet leaf beside the curb",
        "lesson": "careful truth-seeking is better than exciting guessing",
    },
    {
        "key": "vanishing_ticket",
        "premise": "a bus ticket rested beneath the bench with a strange dark mark on it",
        "problem": "Luna thought the mark was a warning and nearly accused the tired passenger who had dropped it",
        "clue": "the mark matched the rubber edge of the bench, not a person's handwriting",
        "dialogue": "'Before we blame someone, may we look closer?' Luna asked. 'That is a fair question,' the passenger said.",
        "action": "Luna showed the ticket to the station attendant and waited while the owner was found",
        "result": "the ticket returned to its owner, and the passenger thanked Luna for not spreading a frightening story",
        "ending": "the bus doors folded shut with a soft sigh as the ticket holder waved",
        "lesson": "honesty includes checking facts before judging people",
    },
    {
        "key": "empty_bench",
        "premise": "a scarf lay on an empty bench although the bus stop was almost deserted",
        "problem": "Luna guessed that someone had left in a hurry and wanted to chase the next bus to find them",
        "clue": "a tiny library card was tucked into the scarf's fringe",
        "dialogue": "'The owner may be looking for it,' Luna said. 'Then let us leave a clear message,' her companion replied.",
        "action": "Luna gave the scarf to the attendant and wrote no invented details on the lost-and-found form",
        "result": "the owner returned before sunset and received the scarf without anyone being misled",
        "ending": "the scarf's yellow fringe danced safely inside the owner's coat",
        "lesson": "responsibility means helping without adding guesses",
    },
    {
        "key": "shadow_signal",
        "premise": "a bus shelter shadow made a hand-shaped signal across the timetable",
        "problem": "Luna was dumbfounded and thought the shadow warned that the next bus was dangerous",
        "clue": "the hand moved only when a tree branch moved in the wind",
        "dialogue": "'The shadow is copying the branch,' Luna said. 'Good mysteries change when we test them,' her companion replied.",
        "action": "Luna stepped back from the road, compared the shadow with the branch, and read the official timetable",
        "result": "the bus came normally, and the frightening signal vanished when the wind became still",
        "ending": "the quiet timetable stood plain beneath the unmoving branch",
        "lesson": "curiosity should be guided by evidence, not fear",
    },
    {
        "key": "wrong_bag",
        "premise": "two nearly identical bags sat beneath the bus-stop sign",
        "problem": "Luna picked up the wrong one because its zipper had a bright red thread",
        "clue": "a name tag inside belonged to someone else",
        "dialogue": "'This bag is not ours,' Luna said quickly. 'Then honesty can put it back,' the stranger answered.",
        "action": "Luna placed the bag exactly where she found it and told the attendant what had happened",
        "result": "the owner collected it, and Luna found her own object under the bench",
        "ending": "the red thread flashed once as the correct bag rolled home",
        "lesson": "returning what is not yours protects trust",
    },
    {
        "key": "late_notice",
        "premise": "a handwritten notice covered the official bus schedule",
        "problem": "the note claimed that every bus was canceled, making Luna feel dumbfounded and ready to give up",
        "clue": "the official time and route number still showed through the paper's torn corner",
        "dialogue": "'Which notice should we trust?' Luna asked. 'The one maintained by the transit workers,' said the driver.",
        "action": "Luna asked the attendant to remove the unofficial note and waited by the marked stop",
        "result": "the scheduled bus arrived, while the false notice was placed in the recycling bin",
        "ending": "the clean schedule shone under the shelter light",
        "lesson": "moral courage means correcting a lie without making a bigger one",
    },
]

ASP_RULES = r"""
#show valid/1.
#show story_ok/1.

valid(P) :- params(P), setting(P,bus_stop), dialogue(P), moral_value(P).
story_ok(P) :- valid(P), bad_ending(P), resolved(P).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mystery storyworld at a bus stop.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        object_name=args.object_name or rng.choice(OBJECTS),
        seed=args.seed,
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("params", "p1"),
            asp.fact("setting", "p1", "bus_stop"),
            asp.fact("dialogue", "p1"),
            asp.fact("moral_value", "p1"),
            asp.fact("bad_ending", "p1"),
            asp.fact("resolved", "p1"),
        ]
    )


def aspire() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp

    model = asp.one_model(aspire())
    valid = set(asp.atoms(model, "valid"))
    good = set(asp.atoms(model, "story_ok"))
    if ("p1",) in valid and ("p1",) in good:
        print("OK: ASP and Python story constraints agree.")
        return 0
    print("Mismatch: ASP did not validate the bus-stop mystery.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting != "bus stop":
        raise StoryError("This mystery world is set only at a bus stop.")
    if not params.name or not params.companion or not params.object_name:
        raise StoryError("A name, companion, and object are required.")

    world = World(params)
    child = world.add(Entity(params.name, "character", params.name))
    companion = world.add(Entity("companion", "companion", f"the {params.companion}"))
    object_entity = world.add(Entity("story_object", "object", params.object_name))

    seed = params.seed
    if seed is None:
        seed = sum(ord(c) for c in "|".join((params.name, params.companion, params.object_name)))
    scenario = SCENARIOS[seed % len(SCENARIOS)]

    child.memes.update({"curiosity": 1.0, "honesty": 1.0, "caution": 1.0})
    companion.memes["trust"] = 1.0
    object_entity.meters["safe"] = 1.0

    world.facts.update(
        setting="bus stop",
        mystery=scenario["key"],
        clue=scenario["clue"],
        moral_value=scenario["lesson"],
        dialogue=True,
        bad_ending=True,
        resolved=True,
        safe_distance=True,
        object=params.object_name,
    )

    world.say(
        f"At the {params.setting}, {params.name} waited with {params.companion}. "
        f"A strange sight appeared: {scenario['premise']}. "
        f"The mystery made {params.name} feel completely dumbfounded."
    )
    world.say(
        f"The first guess seemed exciting, but it carried a danger: {scenario['problem']}. "
        f"{params.name} held the {params.object_name} close and stayed behind the shelter line."
    )
    world.say(
        f"Then {params.name} noticed the important clue: {scenario['clue']}. "
        f"{scenario['dialogue']}"
    )
    world.say(
        f"That conversation changed the plan. {scenario['action']}. "
        f"Nobody crossed the road, grabbed a stranger's things, or treated a guess as proof."
    )
    world.say(
        f"For a moment, the mystery seemed ready for a bad ending, but the honest choice mattered. "
        f"{scenario['result']}. {params.name} learned that {scenario['lesson']}."
    )
    world.say(
        f"When the bus stop grew quiet again, {scenario['ending']}. "
        f"The mystery was solved not by a dramatic chase, but by noticing carefully and speaking truthfully."
    )

    story_qa = [
        QAItem(
            f"Why was {params.name} dumbfounded?",
            f"{params.name} was dumbfounded because {scenario['premise']}. The unusual sight made the bus-stop mystery hard to understand at first.",
        ),
        QAItem(
            "What clue helped solve the mystery?",
            f"The useful clue was that {scenario['clue']}. It gave the characters evidence instead of a guess.",
        ),
        QAItem(
            "What did the dialogue change?",
            f"The dialogue helped the characters slow down and choose a safer, more honest action: {scenario['action']}.",
        ),
        QAItem(
            "What was the moral value?",
            f"The moral value was that {scenario['lesson']}. The characters showed it by checking facts and treating others fairly.",
        ),
        QAItem(
            "What would have caused a bad ending?",
            f"A bad ending could have followed if {params.name} had acted on the first guess and ignored the evidence. Instead, the careful plan led to this result: {scenario['result']}.",
        ),
    ]
    world_qa = [
        QAItem(
            "Why should people wait behind a bus-stop safety line?",
            "They should wait behind it so buses and traffic have room and people do not step into danger.",
        ),
        QAItem(
            "What is a mystery clue?",
            "A mystery clue is an observation or fact that helps explain what happened.",
        ),
        QAItem(
            "Why is honesty important?",
            "Honesty is important because truthful words help people make fair decisions and trust one another.",
        ),
        QAItem(
            "What makes a story ending bad?",
            "A bad ending is one in which careless choices cause avoidable harm, loss, or unfairness.",
        ),
    ]
    prompts = [
        f"Write a mystery about {params.name} at a bus stop who becomes dumbfounded by a strange clue.",
        "Include a brief dialogue that changes the hero's decision.",
        "Show a possible bad ending, then let a moral value guide a safer resolution.",
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world:
        print("\n--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={entity.meters}, memes={entity.memes}"
            )
        print(f"facts={sample.world.facts}")
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

    if args.show_asp:
        print(aspire())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(aspire())
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Luna", "small dog", "red umbrella", seed=base_seed),
            StoryParams("Milo", "friend", "blue backpack", seed=base_seed + 1),
            StoryParams("Pia", "grandmother", "yellow scarf", seed=base_seed + 2),
        ]
    else:
        params_list = []
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
