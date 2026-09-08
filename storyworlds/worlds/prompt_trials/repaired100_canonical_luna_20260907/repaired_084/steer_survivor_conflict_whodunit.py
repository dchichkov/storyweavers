#!/usr/bin/env python3
"""
A small child-facing whodunit about a missing steering wheel, a survivor,
and a conflict repaired through careful listening.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    detective_name: str
    survivor_name: str
    keeper_name: str
    case_id: int = 0
    clue_id: int = 0
    dialogue_id: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


NAMES = ["Luna", "Milo", "Nia", "Tess", "Owen", "Zara"]
SURVIVORS = ["Ari", "Bea", "Kai", "Mina", "Pip", "Sol"]
KEEPERS = ["Ms. Rowan", "Mr. Ellis", "Aunt June", "Coach Remy"]

CASES = [
    {
        "place": "the little harbor museum",
        "object": "a brass steer wheel",
        "problem": "the brass steer wheel vanished from the model boat",
        "conflict": "the other children blamed the survivor before asking what had happened",
        "hurt": "stood beside the boat with their hands tucked tightly behind their back",
        "false_clue": "A muddy footprint pointed toward the storage door, so everyone rushed to a quick answer.",
        "clue": "a clean half-moon mark on the deck showed that the wheel had been lifted, not broken away",
        "turn": "noticed a matching half-moon of dust on the display cloth beneath the repair table",
        "repair": "stopped the blaming and invited the survivor to tell the whole account",
        "truth": "the survivor had moved the wheel to the repair table after noticing its loose peg, then became frightened when the alarm bell rang",
        "ending": "The wheel was safely fitted back onto the boat with a new wooden peg.",
        "image": "The restored boat pointed toward the painted sea, its brass wheel bright beneath the museum lamp.",
    },
    {
        "place": "the old lighthouse classroom",
        "object": "a wooden steer handle",
        "problem": "the wooden steer handle disappeared during a storm-safety game",
        "conflict": "two teammates argued that the survivor had hidden it to win",
        "hurt": "sat near the window while the argument grew louder",
        "false_clue": "A strip of blue ribbon was found near the map chest, and the children treated it like proof.",
        "clue": "the ribbon was tied to a loose drawer that had rolled shut during the pretend storm",
        "turn": "heard a faint wooden tap whenever the drawer was pulled",
        "repair": "apologized for deciding the case before hearing the survivor",
        "truth": "the handle had rolled into the drawer when the survivor moved the map chest away from a dripping window",
        "ending": "They dried the maps and placed the handle back on the practice boat.",
        "image": "The handle rested on the map table while every child checked the storm plan together.",
    },
    {
        "place": "the railway story room",
        "object": "a silver steer badge",
        "problem": "the silver steer badge went missing from the survivor's jacket",
        "conflict": "a friend accused the survivor of losing it and then pretending it had been stolen",
        "hurt": "looked down as if even the truth might make the quarrel worse",
        "false_clue": "A shiny scratch led beneath the reading bench, where everyone searched first.",
        "clue": "the scratch curved upward, matching the edge of the costume trunk",
        "turn": "found a loose thread caught on the trunk latch",
        "repair": "asked questions in order and let the survivor correct the mistaken story",
        "truth": "the badge had snagged on the trunk when the survivor stored a costume, and it had slipped inside",
        "ending": "They found the badge under a folded red scarf and mended its pin.",
        "image": "The silver badge shone on the jacket while the story train rolled past a paper mountain.",
    },
]

DIALOGUES = [
    (
        '"Wait. A clue is not the same as proof,"',
        '"I moved it to keep it safe. I was scared to speak after everyone pointed at me."',
    ),
    (
        '"Let us listen before we decide who is responsible,"',
        '"I remember where I put it, but I need you to hear the whole reason."',
    ),
    (
        '"A fair detective checks the story as well as the footprints,"',
        '"I did touch it, but I did not take it away. I was trying to help."',
    ),
]

OPENINGS = [
    "The mystery began on a quiet afternoon when the museum clock gave one soft chime.",
    "Rain tapped the windows as the children gathered for a make-believe case.",
    "The room was ready for a game of clues, but the first clue was a real surprise.",
]

CLUE_LABELS = [
    "the dust mark",
    "the loose thread",
    "the quiet tap",
    "the curved scratch",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle steer-and-survivor whodunit.")
    parser.add_argument("--detective", choices=NAMES)
    parser.add_argument("--survivor", choices=SURVIVORS)
    parser.add_argument("--keeper", choices=KEEPERS)
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
    detective = args.detective or rng.choice(NAMES)
    survivor = args.survivor or rng.choice([x for x in SURVIVORS if x != detective])
    keeper = args.keeper or rng.choice(KEEPERS)
    return StoryParams(
        detective_name=detective,
        survivor_name=survivor,
        keeper_name=keeper,
        case_id=rng.randrange(len(CASES)),
        clue_id=rng.randrange(len(CLUE_LABELS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
    )


def validate_params(params: StoryParams) -> None:
    if not params.detective_name or not params.survivor_name or not params.keeper_name:
        raise StoryError("Every case needs a detective, a survivor, and a keeper.")
    if params.detective_name == params.survivor_name:
        raise StoryError("The detective and survivor must have different names.")
    if not 0 <= params.case_id < len(CASES):
        raise StoryError("The case number is outside the available mystery cases.")
    if not 0 <= params.dialogue_id < len(DIALOGUES):
        raise StoryError("The dialogue choice is outside the available clues.")


def tell(params: StoryParams) -> World:
    validate_params(params)
    case = CASES[params.case_id]
    dialogue = DIALOGUES[params.dialogue_id]

    world = World()
    detective = world.add(Entity("detective", "character", "detective", params.detective_name))
    survivor = world.add(Entity("survivor", "character", "survivor", params.survivor_name))
    keeper = world.add(Entity("keeper", "character", "keeper", params.keeper_name))
    steer = world.add(Entity("steer", "object", "steer", case["object"]))
    world.facts.update(
        case=case,
        detective=detective,
        survivor=survivor,
        keeper=keeper,
        steer=steer,
        clue_label=CLUE_LABELS[params.clue_id % len(CLUE_LABELS)],
        resolved=False,
    )

    detective.meters["careful_search"] = 1.0
    survivor.memes["trust"] = 1.0

    world.say(OPENINGS[params.case_id % len(OPENINGS)])
    world.say(
        f"{detective.label} was helping {keeper.label} run a small whodunit at {case['place']}. "
        f"The case began when {case['problem']}."
    )
    world.say(f"The missing object was {case['object']}, a real part of the room's model boat.")

    world.para()
    world.say(f"A conflict grew quickly: {case['conflict']}.")
    survivor.memes["hurt"] = 1.0
    survivor.memes["trust"] = 0.0
    world.say(f"{survivor.label} {case['hurt']}.")
    world.say(case["false_clue"])
    detective.meters["hasty_guess"] = 1.0
    world.say(f"{detective.label} almost accepted the guess, but noticed {case['clue']}.")

    world.para()
    keeper.memes["fairness"] = 1.0
    world.say(f"{keeper.label} raised a hand and said, {dialogue[0]} Then {keeper.label} asked everyone to pause.")
    world.say(f"{survivor.label} answered, {dialogue[1]}")
    world.say(f"{detective.label} followed {case['turn']}.")
    detective.meters["evidence_checked"] = 1.0
    survivor.memes["trust"] = 1.0
    world.say(f"The truth was simple: {case['truth']}.")
    world.say(f"{detective.label} apologized for the quick accusation, and the group {case['repair']}.")
    world.say(case["ending"])
    steer.meters["returned"] = 1.0
    world.facts["resolved"] = True

    world.para()
    detective.memes["wisdom"] = 1.0
    survivor.memes["relief"] = 1.0
    world.say(
        f"The case taught {detective.label} that a careful detective checks evidence without turning a person into a suspect."
    )
    world.say(case["image"])
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    case = world.facts["case"]
    survivor = world.facts["survivor"]
    detective = world.facts["detective"]
    story = world.render()
    prompts = [
        f"Write a gentle whodunit at {case['place']} involving {case['object']}.",
        f"Show how {survivor.label} survives the conflict of being blamed and is finally heard.",
        f"Let {detective.label} solve the mystery by checking evidence and repairing the accusation.",
    ]
    story_qa = [
        QAItem(
            "What object went missing?",
            f"The missing object was {case['object']}, which belonged to the model boat.",
        ),
        QAItem(
            f"Why did {survivor.label} feel hurt?",
            f"{survivor.label} felt hurt because the others blamed the survivor before listening to the full story.",
        ),
        QAItem(
            "What clue changed the investigation?",
            f"The important clue was that {case['clue']}.",
        ),
        QAItem(
            "What was the truth about the missing object?",
            f"{case['truth']}.",
        ),
        QAItem(
            "How was the conflict repaired?",
            f"The detective apologized for the quick accusation, listened to the survivor, and helped the group {case['repair']}.",
        ),
    ]
    world_qa = [
        QAItem("What is a steer?", "To steer means to guide the direction of something, such as a boat, bike, or vehicle."),
        QAItem("What is a survivor?", "A survivor is someone who remains safe or keeps going after a difficult event."),
        QAItem("What is a clue?", "A clue is a detail that helps someone discover an answer."),
        QAItem("What is evidence?", "Evidence is information or an object that helps show what really happened."),
        QAItem("What is conflict?", "Conflict is a problem or disagreement between people that needs care to resolve."),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: {entity.label} meters={meters} memes={memes}")
    lines.append(f"resolved: {world.facts.get('resolved')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
case_setting(museum).
case_feature(conflict).
seed_word(steer).
seed_word(survivor).
valid_case :-
    case_setting(museum),
    case_feature(conflict),
    seed_word(steer),
    seed_word(survivor).
#show valid_case/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "museum"),
            asp.fact("feature", "conflict"),
            asp.fact("seed_word", "steer"),
            asp.fact("seed_word", "survivor"),
        ]
    )


def asp_program(show: str = "#show valid_case/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid_case"))
    expected = {()}
    if found != expected:
        print("MISMATCH")
        print("ASP:", sorted(found))
        print("PY :", sorted(expected))
        return 1
    for params in [
        StoryParams("Luna", "Ari", "Ms. Rowan"),
        StoryParams("Milo", "Bea", "Mr. Ellis", case_id=1),
        StoryParams("Tess", "Kai", "Aunt June", case_id=2),
    ]:
        sample = generate(params)
        if not sample.story or not sample.world.facts["resolved"]:
            print("MISMATCH: generated story did not resolve.")
            return 1
    print("OK: ASP parity matches Python gate and generated stories resolve.")
    return 0


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
    StoryParams("Luna", "Ari", "Ms. Rowan", case_id=0),
    StoryParams("Milo", "Bea", "Mr. Ellis", case_id=1),
    StoryParams("Tess", "Kai", "Aunt June", case_id=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program())
        print(asp.one_model(asp_program()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
