#!/usr/bin/env python3
"""
A small detective storyworld about a crouton quest, friendship, and a repeating clue.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    detective_name: str
    friend_name: str
    caretaker_name: str
    seed: Optional[int] = None
    case_id: int = 0
    opening_id: int = 0
    dialogue_id: int = 0
    ending_id: int = 0


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


DETECTIVE_NAMES = ["Luna", "Milo", "Tess", "Arlo", "Nina", "Jasper"]
FRIEND_NAMES = ["Bea", "Owen", "Sami", "Ivy", "Theo", "Pia"]
CARETAKER_NAMES = ["Ms. Rowan", "Mr. Ellis", "Aunt June", "Coach Mira"]

CASES = [
    {
        "place": "the school kitchen",
        "quest": "find the missing golden crouton before soup time",
        "repeat": "a buttery crumb appeared beside three different cupboard doors",
        "first_guess": "the crumbs were a trail leading toward the pantry",
        "turn": "the same three crumbs appeared again after the doors were closed",
        "clue": "the crumbs were not moving toward a cupboard; they were marking the cupboard with the loose hinge",
        "solution": "they opened the loose-hinged cupboard and found the crouton tucked inside a clean measuring cup",
        "image": "The golden crouton rested in the cup like a tiny sun.",
    },
    {
        "place": "the library reading room",
        "quest": "recover the crouton-shaped prize from the missing-lunch display",
        "repeat": "a small orange mark showed up at the end of every third shelf",
        "first_guess": "the marks pointed toward a hidden book",
        "turn": "the mark repeated even on shelves with no books moved",
        "clue": "each mark lined up with the library cart's squeaky wheel",
        "solution": "they followed the cart to a cushion where the prize had rolled beneath its cover",
        "image": "The prize peeked from beneath the cushion, beside one bright orange library card.",
    },
    {
        "place": "the community garden shed",
        "quest": "find the picnic crouton packed for the friendship club",
        "repeat": "a neat square of dry soil appeared beneath the same window each time",
        "first_guess": "someone had buried the snack in the garden",
        "turn": "the square returned after the soil was smoothed flat",
        "clue": "the repeating square matched the bottom of a seed tray leaning against the shed",
        "solution": "they lifted the tray and discovered the crouton inside a basket behind it",
        "image": "The crouton sat in the basket while garden beans curled toward the light.",
    },
    {
        "place": "the little train station",
        "quest": "locate the crouton badge lost during the friendship club's train ride",
        "repeat": "a blue thread appeared on the same bench after every search",
        "first_guess": "the thread pointed down the platform",
        "turn": "the thread appeared again when nobody had walked that way",
        "clue": "the bench slat was rubbing blue paint from the badge's ribbon",
        "solution": "they lifted the slat and found the badge caught in a narrow crack",
        "image": "The crouton badge shone on the bench while the next train gave one friendly bell.",
    },
    {
        "place": "the rain shelter",
        "quest": "retrieve the crouton token for the day's puzzle game",
        "repeat": "three drops tapped the same tin bucket whenever the wind rose",
        "first_guess": "the tapping was a secret signal from outside",
        "turn": "the three-drop rhythm continued even after the rain stopped",
        "clue": "a loose roof flap was dripping into the bucket in the same three places",
        "solution": "they moved the bucket and found the token behind it, dry beneath the roof beam",
        "image": "The token gleamed beside the bucket as the last raindrop made a soft plink.",
    },
]

OPENINGS = [
    "Luna kept a notebook for small mysteries, and that morning it opened to a fresh page.",
    "The friendship club had barely gathered when a curious case landed on Luna's desk.",
    "A quiet morning became a detective morning when the snack tray arrived one crouton short.",
    "Luna noticed that every good mystery began with someone paying attention.",
]

DIALOGUES = [
    ('"Let us watch what repeats before we decide what it means,"', "Luna told Bea."),
    ('"You saw the pattern first, so your idea belongs in the case,"', "Luna told Bea."),
    ('"A good friend does not grab the answer; a good friend helps another person test it,"', "Luna said."),
    ('"We can disagree about the clue and still solve the mystery together,"', "Luna said."),
]

ENDINGS = [
    "From then on, Luna and Bea called repeated clues their quiet bells.",
    "The two friends added a new rule to their notebook: notice, share, and check again.",
    "Their friendship grew stronger because neither detective needed to solve a case alone.",
    "The next mystery could wait; for now, the friends shared the recovered crouton.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detective storyworld about a crouton quest and friendship.")
    parser.add_argument("--detective", choices=DETECTIVE_NAMES)
    parser.add_argument("--friend", choices=FRIEND_NAMES)
    parser.add_argument("--caretaker", choices=CARETAKER_NAMES)
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
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    friend_choices = [name for name in FRIEND_NAMES if name != detective]
    friend = args.friend or rng.choice(friend_choices)
    if friend == detective:
        raise StoryError("The detective and friend must have different names.")
    return StoryParams(
        detective_name=detective,
        friend_name=friend,
        caretaker_name=args.caretaker or rng.choice(CARETAKER_NAMES),
        case_id=rng.randrange(len(CASES)),
        opening_id=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        ending_id=rng.randrange(len(ENDINGS)),
    )


def validate_params(params: StoryParams) -> None:
    if not params.detective_name or not params.friend_name or not params.caretaker_name:
        raise StoryError("Detective, friend, and caretaker names are required.")
    if params.detective_name == params.friend_name:
        raise StoryError("The detective and friend cannot be the same person.")
    if not 0 <= params.case_id < len(CASES):
        raise StoryError("The case choice is outside the detective registry.")


def tell(params: StoryParams) -> World:
    validate_params(params)
    case = CASES[params.case_id]
    detective = Entity("detective", "character", "child", params.detective_name)
    friend = Entity("friend", "character", "child", params.friend_name)
    caretaker = Entity("caretaker", "character", "adult", params.caretaker_name)
    crouton = Entity("crouton", "food", "crouton", "golden crouton")
    notebook = Entity("notebook", "tool", "notebook", "case notebook")

    world = World()
    for entity in (detective, friend, caretaker, crouton, notebook):
        world.add(entity)

    detective.meters["attention"] = 1.0
    detective.memes["curiosity"] = 1.0
    friend.memes["belonging"] = 1.0
    crouton.meters["safe"] = 1.0

    world.facts.update(
        case=case,
        detective=detective,
        friend=friend,
        caretaker=caretaker,
        crouton=crouton,
        notebook=notebook,
        repeated_clue=case["repeat"],
        resolved=False,
    )

    world.say(OPENINGS[params.opening_id])
    world.say(
        f"{detective.label} and {friend.label} were helping {caretaker.label} at {case['place']} "
        f"when they discovered that the quest was to {case['quest']}."
    )
    world.say(f"The missing snack was a plain, crunchy crouton, safe to handle and meant for the club's soup.")

    world.para()
    world.say(f"{friend.label} spotted the first clue: {case['repeat']}.")
    world.say(f"{detective.label} wrote it in the notebook and guessed that {case['first_guess']}.")
    friend.memes["uncertain"] = 1.0
    world.say(f"{friend.label} was unsure, but {detective.label} made room for the idea instead of brushing it aside.")
    world.say(f"Then the clue repeated: {case['turn']}.")
    detective.meters["observations"] = 2.0
    friend.meters["observations"] = 2.0

    world.para()
    dialogue, speaker = DIALOGUES[params.dialogue_id]
    world.say(f"{speaker} {dialogue}")
    world.say(f"{friend.label} answered, \"Then I think the repeating clue is showing us what stayed still.\"")
    world.say(f"Together, the friends checked the pattern and discovered that {case['clue']}.")
    friend.memes["confidence"] = 1.0
    detective.memes["trust"] = 1.0
    world.say(f"They tested the idea carefully, and {case['solution']}.")
    crouton.meters["found"] = 1.0
    world.facts["resolved"] = True

    world.para()
    world.say(f"{caretaker.label} thanked both young detectives because the solution came from listening and checking, not from guessing loudly.")
    world.say(ENDINGS[params.ending_id])
    world.say(f"{case['image']}")

    return world


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a child-friendly detective story about a quest to {case['quest']}.",
        f"Show how {world.facts['friend'].label} notices that {case['repeat']} and how friendship helps test the clue.",
        "Include a repeating clue, a brief back-and-forth conversation, and an ending image proving the crouton was found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    detective = world.facts["detective"].label
    friend = world.facts["friend"].label
    return [
        QAItem("What was the detectives' quest?", f"{detective} and {friend} had to {case['quest']}."),
        QAItem("What clue kept repeating?", f"The repeating clue was that {case['repeat']}."),
        QAItem("Why was the friendship important?", f"{friend} noticed the pattern, and {detective} listened and tested the idea together with {friend}."),
        QAItem("What did the repeated clue finally reveal?", f"It revealed that {case['clue']}."),
        QAItem("How did the case end?", f"They solved the case when {case['solution']}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a crouton?", "A crouton is a small, crisp piece of toasted bread, often added to soup or salad."),
        QAItem("What does a detective do?", "A detective observes clues, asks questions, and reasons carefully to solve a mystery."),
        QAItem("What is a quest?", "A quest is a purposeful search or mission to find or accomplish something important."),
        QAItem("What does friendship involve?", "Friendship involves caring, listening, sharing, and helping one another."),
        QAItem("Why can repetition help solve a mystery?", "A repeated detail can show a pattern and point toward a cause that a single detail might hide."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: {entity.label} meters={meters} memes={memes}")
    lines.append(f"resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_ok(crouton).
feature_ok(quest).
feature_ok(friendship).
feature_ok(repetition).
detective_story_ok :-
    quest_ok(crouton),
    feature_ok(quest),
    feature_ok(friendship),
    feature_ok(repetition).
#show detective_story_ok/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("seed_word", "crouton"),
            asp.fact("setting", "mystery_place"),
            asp.fact("feature", "quest"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "repetition"),
            asp.fact("style", "detective_story"),
        ]
    )


def asp_program(show: str = "#show detective_story_ok/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "detective_story_ok"))
    expected = {()}
    if found == expected:
        print("OK: ASP parity matches Python gate.")
        for params in CURATED:
            sample = generate(params)
            if "crouton" not in sample.story.lower():
                print("MISMATCH: generated story omitted crouton.")
                return 1
            if len(sample.story_qa) < 3:
                print("MISMATCH: generated story lacked grounded QA.")
                return 1
        return 0
    print("MISMATCH")
    print("ASP:", sorted(found))
    print("PY :", sorted(expected))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams("Luna", "Bea", "Ms. Rowan", case_id=0),
    StoryParams("Milo", "Ivy", "Mr. Ellis", case_id=1),
    StoryParams("Tess", "Owen", "Aunt June", case_id=2),
    StoryParams("Arlo", "Pia", "Coach Mira", case_id=3),
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
        samples = [generate(params) for params in CURATED]
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
