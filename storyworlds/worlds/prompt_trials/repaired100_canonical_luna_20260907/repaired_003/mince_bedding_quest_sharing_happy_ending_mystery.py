#!/usr/bin/env python3
"""
A small mystery storyworld about mince, bedding, a helpful quest, and sharing.
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
class StoryParams:
    setting: str
    seed: Optional[int] = None
    child_name: str = "Luna"
    helper_name: str = "Nana"
    mince_kind: str = "vegetable mince"
    bedding_kind: str = "blue bedding"
    quest_word: str = "quest"
    sharing_word: str = "sharing"
    ending_word: str = "happy ending"
    style: str = "mystery"


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def inc_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def inc_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    setting: str
    child: Entity
    helper: Entity
    mince: Entity
    bedding: Entity
    clue: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in [self.child, self.helper, self.mince, self.bedding, self.clue]:
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            lines.append(f"  {entity.id:12} ({entity.kind:9}) {' '.join(bits)}")
        lines.append(f"  setting: {self.setting}")
        return "\n".join(lines)


SETTINGS = {
    "cottage": "the cottage kitchen",
    "flat": "the little flat",
    "farmhouse": "the farmhouse",
    "lighthouse": "the lighthouse room",
}

NAMES = ["Luna", "Milo", "Nia", "Theo", "Asha", "Pip"]
HELPERS = ["Nana", "Grandpa", "Auntie", "Uncle"]
MINCE = ["vegetable mince", "lentil mince", "savory mince"]
BEDDING = ["blue bedding", "starry bedding", "striped bedding"]

MYSTERIES = {
    "cottage": [
        (
            "A small trail of flour crossed the floor and vanished beneath the table.",
            "followed the flour trail with a wooden spoon",
            "The missing bedding was tucked under the table, where a sleepy kitten had made a nest.",
            "lifted the bedding gently and carried it to the warm basket",
        ),
        (
            "Three round crumbs sat beside the pantry door, as if someone had left a secret message.",
            "counted the crumbs and checked the pantry",
            "The bedding was behind a flour sack, moved there when the pantry door had swung open.",
            "brushed off the bedding and folded it neatly",
        ),
    ],
    "flat": [
        (
            "A soft blue thread curled from the sofa to the quiet hallway.",
            "followed the blue thread past the sofa",
            "A breeze from the open window had pulled the bedding toward the hall.",
            "closed the window and folded the bedding together",
        ),
        (
            "A cupboard door stood open, although everyone remembered closing it.",
            "peered into the cupboard with a little torch",
            "The bedding had slipped from its shelf when the cupboard was bumped.",
            "returned the bedding to its safe shelf",
        ),
    ],
    "farmhouse": [
        (
            "Tiny muddy dots led from the back step toward the laundry room.",
            "tracked the dots while keeping the mince bowl steady",
            "A duckling had tugged the bedding toward a sunny corner.",
            "moved the bedding away from the muddy prints",
        ),
        (
            "A square shadow showed beneath a pile of clean towels.",
            "lifted the top towel and looked underneath",
            "The bedding was hiding under the towels after a gust rattled the laundry door.",
            "shook out the bedding and set it in the clean basket",
        ),
    ],
    "lighthouse": [
        (
            "A pale thread glimmered in the beam of the turning lamp.",
            "followed the thread around the round room",
            "The bedding had caught on a chair and trailed toward the lamp.",
            "freed the bedding and moved the chair from the walkway",
        ),
        (
            "A gentle thump came from the cupboard whenever the tower light passed.",
            "waited for the light and opened the cupboard carefully",
            "The bedding had fallen against a tin box, making the soft thump.",
            "folded the bedding beside the tin box",
        ),
    ],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle mystery quest about mince, bedding, and sharing."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--mince", choices=MINCE)
    parser.add_argument("--bedding", choices=BEDDING)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Choose a setting such as the cottage, flat, farmhouse, or lighthouse.")
    if params.child_name not in NAMES:
        raise StoryError("The child name must come from the storyworld name list.")
    if params.helper_name not in HELPERS:
        raise StoryError("The helper name must come from the storyworld helper list.")
    if params.mince_kind not in MINCE:
        raise StoryError("The meal must use one of the available kinds of mince.")
    if params.bedding_kind not in BEDDING:
        raise StoryError("The bedding must come from the available bedding list.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        seed=args.seed,
        child_name=args.name or rng.choice(NAMES),
        helper_name=args.helper or rng.choice(HELPERS),
        mince_kind=args.mince or rng.choice(MINCE),
        bedding_kind=args.bedding or rng.choice(BEDDING),
    )
    _validate_params(params)
    return params


def make_world(params: StoryParams) -> World:
    return World(
        setting=SETTINGS[params.setting],
        child=Entity(params.child_name, "character", params.child_name, "child"),
        helper=Entity(params.helper_name, "character", params.helper_name, "helper"),
        mince=Entity("mince", "food", params.mince_kind, "shared meal"),
        bedding=Entity("bedding", "thing", params.bedding_kind, "sleeping cover"),
        clue=Entity("clue", "thing", "mysterious trail", "evidence"),
    )


def _build_story(world: World, params: StoryParams) -> None:
    rng = random.Random((params.seed or 0) + 18341)
    child = world.child
    helper = world.helper
    mince = world.mince
    bedding = world.bedding
    clue = world.clue
    opening, action, reveal, cleanup = rng.choice(MYSTERIES[params.setting])

    child.memes["curiosity"] = 1.0
    child.memes["kindness"] = 0.0
    child.meters["quest_steps"] = 0.0
    helper.memes["care"] = 1.0
    mince.meters["portions"] = 4.0
    bedding.meters["warmth"] = 1.0
    clue.meters["hidden"] = 1.0

    world.say(
        f"At supper time in {world.setting}, {child.label} helped {helper.label} stir a pot of "
        f"{mince.label}. The kitchen smelled warm, but one piece of {bedding.label} had vanished."
    )
    world.say(opening)
    world.say(
        f'"We can solve this mystery together," said {helper.label}. '
        f'"Will you join the quest?" '
        f'"Yes," said {child.label}. "And when we find it, we can share supper with everyone."'
    )

    world.para()
    world.say(
        f"{child.label} began the quest. {child.label} {action}, watching every corner and listening "
        f"for a clue. The strange trail was not frightening; it was a path waiting to be understood."
    )
    child.inc_meter("quest_steps", 1.0)
    clue.meters["hidden"] = 0.0
    clue.meters["followed"] = 1.0
    world.say(
        f"{helper.label} carried the pot safely while {child.label} looked. Their careful teamwork "
        f"kept the hot {mince.label} away from the edge of the table."
    )
    child.inc_meme("kindness", 1.0)

    world.para()
    world.say(reveal)
    bedding.meters["found"] = 1.0
    bedding.meters["warmth"] = 2.0
    world.say(
        f'"There you are!" cried {child.label}. "{bedding.label} was not lost forever. '
        f'It only needed someone to notice where it had gone."'
    )
    world.say(
        f"{helper.label} smiled. Together they {cleanup}. The mystery had a small answer, "
        f"but the answer made the whole room feel lighter."
    )

    world.para()
    mince.meters["portions"] = 0.0
    mince.memes["shared"] = 1.0
    child.inc_meme("joy", 1.0)
    world.say(
        f"Then {child.label} and {helper.label} set out bowls of {mince.label}. "
        f"They practiced sharing by giving everyone a fair portion, including the tired kitten nearby."
    )
    world.say(
        f"When the {bedding.label} was placed in its proper spot, the room looked ready for rest. "
        f"{child.label} had finished a quest, solved a mystery, and discovered that sharing made "
        f"the best {params.ending_word}."
    )
    world.say(
        f"At bedtime, the folded {bedding.label} rested in a sunny chair while happy voices rose "
        f"from the table. The mystery was solved, the meal was shared, and everyone smiled."
    )

    world.facts.update(
        opening=opening,
        action=action,
        reveal=reveal,
        cleanup=cleanup,
        quest_complete=True,
        shared=True,
        happy_ending=True,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a gentle mystery quest in {world.setting} involving {world.mince.label} and missing {world.bedding.label}.",
        f"Tell a child-friendly story where {world.child.label} follows a clue, solves a mystery, and shares {world.mince.label}.",
        "Write a happy ending showing that teamwork and sharing changed the outcome.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"What was {world.child.label}'s quest?",
            answer=f"{world.child.label}'s quest was to follow the clues and find the missing {world.bedding.label}.",
        ),
        QAItem(
            question="What solved the mystery?",
            answer=f"The mystery was solved when the trail led to the {world.bedding.label}, which had been moved by an ordinary breeze, animal, or household accident.",
        ),
        QAItem(
            question=f"How did {world.helper.label} help?",
            answer=f"{world.helper.label} stayed close, carried the hot {world.mince.label} safely, and worked together with {world.child.label}.",
        ),
        QAItem(
            question="How did the story end happily?",
            answer=f"Everyone shared the {world.mince.label}, the {world.bedding.label} was put back, and the friends felt happy because their teamwork had solved the mystery.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mince?",
            answer="Mince is food made from ingredients chopped or ground into very small pieces.",
        ),
        QAItem(
            question="Why is bedding useful?",
            answer="Bedding keeps a sleeping place comfortable, clean, and warm.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving other people a fair chance to enjoy or use something.",
        ),
        QAItem(
            question="Why are clues helpful in a mystery?",
            answer="Clues provide small pieces of information that help people discover what happened.",
        ),
    ]


ASP_RULES = r"""
found_bedding(B) :- bedding(B), followed_clue.
quest_complete :- found_bedding(B), sharing_done.
happy_ending :- quest_complete, sharing_done.
sharing_done :- meal(M), shared(M).
reasonable_story :- mince(M), bedding(B), meal(M), found_bedding(B), happy_ending.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for item in MINCE:
        safe = item.replace(" ", "_")
        lines.append(asp.fact("mince", safe))
        lines.append(asp.fact("meal", safe))
    for item in BEDDING:
        safe = item.replace(" ", "_")
        lines.append(asp.fact("bedding", safe))
    lines.append(asp.fact("followed_clue"))
    for item in MINCE:
        lines.append(asp.fact("shared", item.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str = "#show reasonable_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _python_reasonable(params: StoryParams) -> bool:
    return (
        params.setting in SETTINGS
        and params.mince_kind in MINCE
        and params.bedding_kind in BEDDING
        and params.quest_word == "quest"
        and params.sharing_word == "sharing"
        and params.ending_word == "happy ending"
        and params.style == "mystery"
    )


def asp_verify() -> int:
    params = StoryParams(setting="cottage")
    if not _python_reasonable(params):
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    try:
        import storyworlds.asp as asp

        models = asp.solve(asp_program(), models=1)
        if not models:
            print("MISMATCH: ASP produced no reasonable story.")
            return 1
    except ImportError:
        print("OK: Python reasonableness gate passed; clingo is unavailable.")
        return 0
    sample = generate(params)
    if not sample.story or not sample.story_qa:
        print("MISMATCH: generated story verification failed.")
        return 1
    print("OK: Python and ASP story gates agree; generated story exercised.")
    return 0


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = make_world(params)
    _build_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print("\n== Generation prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(setting="cottage", child_name="Luna", helper_name="Nana", mince_kind="vegetable mince", bedding_kind="blue bedding"),
    StoryParams(setting="flat", child_name="Milo", helper_name="Auntie", mince_kind="lentil mince", bedding_kind="starry bedding"),
    StoryParams(setting="farmhouse", child_name="Nia", helper_name="Grandpa", mince_kind="savory mince", bedding_kind="striped bedding"),
    StoryParams(setting="lighthouse", child_name="Theo", helper_name="Uncle", mince_kind="vegetable mince", bedding_kind="starry bedding"),
]


def build_all_samples() -> list[StorySample]:
    return [generate(params) for params in CURATED]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp

            models = asp.solve(asp_program(), models=1)
            print("ASP model:")
            for model in models:
                print(" ".join(str(atom) for atom in model))
        except ImportError:
            print("ASP mode requires the optional clingo package.")
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = build_all_samples()
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
