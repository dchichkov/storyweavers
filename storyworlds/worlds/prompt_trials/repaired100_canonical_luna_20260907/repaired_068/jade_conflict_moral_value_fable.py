#!/usr/bin/env python3
"""
A small fable world about Jade, who learns that honest kindness is worth more
than a glittering prize.
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
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    child: str = "Jade"
    companion: str = "the old tortoise"
    setting: str = "a small village market"
    treasure: str = "a polished jade bead"
    moral_value: str = "honesty"
    seed: Optional[int] = None


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"energy": 1.0, "worry": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"honesty": 0.0, "courage": 0.0, "kindness": 0.0}
    )


@dataclass
class World:
    setting: str
    child: Person
    companion: Person
    treasure: str
    moral_value: str
    conflict: str = ""
    clue: str = ""
    first_choice: str = ""
    better_choice: str = ""
    consequence: str = ""
    ending_image: str = ""
    returned: bool = False
    transformed: bool = False
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


CONFLICTS = [
    {
        "conflict": "Jade found a jade bead beneath a spice seller's table, but two traders both claimed it.",
        "clue": "A tiny thread of red silk clung to the bead, matching the ribbon on a baker's purse.",
        "first_choice": "Jade slipped the bead into a pocket and thought about keeping its cool green shine.",
        "better_choice": "Jade held the bead up and asked both traders to describe where they had lost it.",
        "consequence": "The baker remembered that the bead had fallen from her mother's old necklace, while the spice seller admitted he had only guessed.",
        "lesson": "truth gives every person a fair chance",
        "ending": "The baker tied the jade bead back onto the necklace, and its green gleam rested beside her warm loafs.",
    },
    {
        "conflict": "A proud merchant offered Jade a silver coin for a jade carving that belonged to a quiet potter.",
        "clue": "The carving bore the potter's three little thumbprints beneath its base.",
        "first_choice": "Jade reached for the coin because it was brighter than anything in her pocket.",
        "better_choice": "Jade turned the carving over and showed the merchant the marks that proved its maker.",
        "consequence": "The potter recognized her careful eyes and thanked her for protecting the work he had shaped.",
        "lesson": "a fair heart should not be bought by a bright reward",
        "ending": "The merchant kept his coin, but the potter gave Jade a small clay bird that whistled in the wind.",
    },
    {
        "conflict": "Jade discovered that the village contest had a missing rule, and the easiest path to victory was to stay silent.",
        "clue": "The faded rule was still visible on the back of the wooden sign.",
        "first_choice": "Jade nearly covered the faded words with her hand so the other players would not see them.",
        "better_choice": "Jade called the judge and read the old rule aloud for everyone.",
        "consequence": "The contest was restarted fairly, and a younger player won with a simple but clever answer.",
        "lesson": "fairness matters even when it changes who wins",
        "ending": "Jade walked home without a ribbon, yet the village children followed her with grateful smiles.",
    },
    {
        "conflict": "A hungry fox begged Jade to blame a sleeping crow for a basket of missing berries.",
        "clue": "Purple berry stains marked the fox's own paws.",
        "first_choice": "Jade opened her mouth to repeat the fox's story.",
        "better_choice": "Jade pointed gently to the pawprints and asked the fox to tell the truth.",
        "consequence": "The fox confessed, returned the basket, and received a fair share after helping gather new berries.",
        "lesson": "kindness is strongest when it does not hide the truth",
        "ending": "The fox ate beneath the elder tree while the crow and Jade shared the ripest berries.",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Jade conflict and moral value fable.")
    parser.add_argument("--child")
    parser.add_argument("--companion")
    parser.add_argument("--setting", choices=["a small village market", "a forest clearing"])
    parser.add_argument("--treasure")
    parser.add_argument("--moral-value", dest="moral_value")
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


NAMES = ["Jade", "Lina", "Pip", "Mara", "Nia"]
COMPANIONS = ["the old tortoise", "the patient heron", "the kindly goat"]
MORALS = ["honesty", "fairness", "kindness", "courage"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    moral = args.moral_value or rng.choice(MORALS)
    if moral not in MORALS:
        raise StoryError("Moral value must be honesty, fairness, kindness, or courage.")
    return StoryParams(
        child=args.child or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        setting=args.setting or "a small village market",
        treasure=args.treasure or "a polished jade bead",
        moral_value=moral,
    )


def make_world(params: StoryParams) -> World:
    return World(
        setting=params.setting,
        child=Person(params.child, "child"),
        companion=Person(params.companion, "helper"),
        treasure=params.treasure,
        moral_value=params.moral_value,
    )


def generate_story(world: World, params: StoryParams) -> None:
    index = (params.seed or 0) % len(CONFLICTS)
    case = CONFLICTS[index]
    world.conflict = case["conflict"]
    world.clue = case["clue"]
    world.first_choice = case["first_choice"]
    world.better_choice = case["better_choice"]
    world.consequence = case["consequence"]
    world.ending_image = case["ending"]

    c = world.child.name
    h = world.companion.name

    world.say(f"One bright morning, {c} walked through {world.setting} with {h}.")
    world.say(
        f"Beside a stall, {c} saw {world.treasure}. "
        f"\"What a beautiful thing,\" {c} whispered."
    )
    world.say(f"{h} nodded. \"A beautiful thing still needs an honest owner.\"")
    world.say(world.conflict)
    world.say(world.first_choice)
    world.child.meters["worry"] += 0.2
    world.child.memes["honesty"] += 0.2
    world.say(
        f"Then {c} noticed a small clue: {world.clue} "
        f"\"Let us ask before we decide,\" {h} said."
    )
    world.say(world.better_choice)
    world.say(world.consequence)
    world.returned = True
    world.child.meters["worry"] = 0.0
    world.child.memes["honesty"] += 1.0
    world.child.memes["kindness"] += 0.5
    world.say(
        f"{c} felt no heavier for giving up a tempting prize. "
        f"Instead, {c} learned that {case['lesson']}."
    )
    world.transformed = True
    world.child.memes["courage"] += 0.5
    world.say(world.ending_image)


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            f"Where did {p.child} walk?",
            f"{p.child} walked through {p.setting} with {p.companion}.",
        ),
        QAItem(
            f"What did {p.child} find?",
            f"{p.child} found {p.treasure}.",
        ),
        QAItem(
            "What was the conflict?",
            world.conflict,
        ),
        QAItem(
            f"Why did {p.child} change the first choice?",
            f"{p.child} noticed that {world.clue} The clue showed that asking questions would be fairer than taking the easy path.",
        ),
        QAItem(
            f"What moral value did {p.child} practice?",
            f"{p.child} practiced {p.moral_value} by choosing a fair and truthful response instead of keeping the tempting prize.",
        ),
        QAItem(
            "What happened at the end?",
            world.ending_image,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is jade?",
            "Jade is a hard stone that is often green and can be polished or carved.",
        ),
        QAItem(
            "What does honesty mean?",
            "Honesty means telling the truth and not taking what belongs to someone else.",
        ),
        QAItem(
            "Why is fairness important?",
            "Fairness gives people an equal chance and helps them trust one another.",
        ),
    ]


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        f"Write a fable about {params.child} finding jade and facing a conflict.",
        f"Tell a child-friendly story in {params.setting} about the moral value of {params.moral_value}.",
        f"Show how {params.child} chooses truth over a tempting treasure.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
place(market).
material(jade).
conflict.
moral_value(honesty).
choice(return_treasure).
valid_story :- place(market), material(jade), conflict, moral_value(honesty), choice(return_treasure).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "market"),
            asp.fact("material", "jade"),
            asp.fact("conflict"),
            asp.fact("moral_value", "honesty"),
            asp.fact("choice", "return_treasure"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/0."))
    if any(symbol.name == "valid_story" for symbol in model):
        print("OK: ASP and Python moral-value gate agree.")
        return 0
    print("MISMATCH: ASP gate failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    world.facts["params"] = params
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(params),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        print(asdict(sample.params))
        print(
            {
                "child": sample.world.child.meters | sample.world.child.memes,
                "returned": sample.world.returned,
                "transformed": sample.world.transformed,
                "treasure": sample.world.treasure,
                "moral_value": sample.world.moral_value,
            }
        )
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(seed=0),
    StoryParams(
        child="Lina",
        companion="the patient heron",
        setting="a forest clearing",
        treasure="a polished jade carving",
        moral_value="fairness",
        seed=1,
    ),
    StoryParams(
        child="Pip",
        companion="the kindly goat",
        setting="a small village market",
        treasure="a green jade button",
        moral_value="kindness",
        seed=2,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        print("ASP model:", asp.one_model(asp_program("#show valid_story/0.")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
