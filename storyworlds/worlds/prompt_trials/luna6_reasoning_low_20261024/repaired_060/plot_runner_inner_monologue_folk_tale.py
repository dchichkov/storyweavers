#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
% A runner can save a garden plot when a warning is carried and neighbors act.
has_runner :- role(runner).
has_plot :- place(garden_plot).
warning_ready :- clue(water_marks).
neighbors_help :- feature(kindness).
safe_ending :- has_runner, has_plot, warning_ready, neighbors_help.
#show safe_ending/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Lina"
    village: str = "Willowmere"
    crop: str = "turnips"
    companion: str = "a red-feathered hen"


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def entity(self, name: str, kind: str) -> Entity:
        item = Entity(name=name, kind=kind)
        self.entities[name] = item
        return item

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


TALES = [
    {
        "title": "The Runner and the Thirsty Plot",
        "trouble": "the village brook had slipped from its usual channel, and the garden plot was drying",
        "clue": "a row of damp stones showed where the water had turned beneath the old footbridge",
        "thought": "If I run without looking, I may carry the wrong news",
        "plan": "Lina followed the damp stones to the miller’s gate and asked the neighbors to bring spades",
        "fix": "the neighbors opened a shallow side channel and guided the brook back toward the garden",
        "image": "silver water curled around the turnips, and every leaf lifted its green face",
    },
    {
        "title": "The Runner and the Midnight Rain",
        "trouble": "a heavy rain cloud was rolling toward the low garden plot while its seed rows lay uncovered",
        "clue": "little streams already crossed the hill path and flowed toward the village beds",
        "thought": "A warning is worth more when I know where the water will go",
        "plan": "Lina ran first to the shepherd on the hill, then together they called the villagers to raise a low earth bank",
        "fix": "the neighbors shaped a gentle bank that turned the runoff into an empty stone basin",
        "image": "rain tapped the basin while the seed rows rested beneath their straw blankets",
    },
    {
        "title": "The Runner and the Missing Beans",
        "trouble": "the bean vines in the village plot had begun to droop, though the sky stayed bright",
        "clue": "a tiny line of wet pawprints led from the water jar to a cracked wooden trough",
        "thought": "Perhaps the trouble is not in the sky; perhaps it is beside the path",
        "plan": "Lina showed the trough to the village carpenter and asked the children to carry water in small cups",
        "fix": "the carpenter mended the split, and the children watered the thirsty beans together",
        "image": "purple blossoms nodded above the repaired trough as a bee hummed past",
    },
    {
        "title": "The Runner and the Wind-Torn Plot",
        "trouble": "a gust had knocked the garden’s reed fence across the young cabbage rows",
        "clue": "one fence reed was caught in a low branch, showing which way the wind had blown",
        "thought": "I cannot mend a fence by myself, but I can find the hands that can",
        "plan": "Lina carried the loose reed to the weaver and invited the nearby farmers to help lift the fence",
        "fix": "the weaver tied the reeds with strong willow cord, and the farmers set the fence upright",
        "image": "the cabbage leaves stood safe inside their neat fence while a kite danced over the roofs",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A folk-tale world of a quick-footed runner and a village garden plot."
    )
    parser.add_argument("--name")
    parser.add_argument("--village")
    parser.add_argument("--crop")
    parser.add_argument("--companion")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(["Lina", "Tomas", "Nuri", "Mara", "Pavel"])
    village = args.village or rng.choice(["Willowmere", "Pebbleford", "Cloverbank"])
    crop = args.crop or rng.choice(["turnips", "beans", "cabbages", "peas"])
    companion = args.companion or rng.choice(
        ["a red-feathered hen", "a patient old dog", "a small gray donkey"]
    )
    if not name.strip():
        raise StoryError("The runner needs a name.")
    if village not in {"Willowmere", "Pebbleford", "Cloverbank"}:
        raise StoryError("Choose a village from Willowmere, Pebbleford, or Cloverbank.")
    if crop not in {"turnips", "beans", "cabbages", "peas"}:
        raise StoryError("The garden plot can grow turnips, beans, cabbages, or peas.")
    if not companion.strip():
        raise StoryError("The runner's companion must have a name.")
    return StoryParams(name=name, village=village, crop=crop, companion=companion)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("role", "runner"),
            asp.fact("place", "garden_plot"),
            asp.fact("clue", "water_marks"),
            asp.fact("feature", "kindness"),
        ]
    )


def asp_program(show: str = "#show safe_ending/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return bool(TALES) and all(
        tale.get("trouble") and tale.get("clue") and tale.get("fix") and tale.get("image")
        for tale in TALES
    )


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    asp_ok = bool(asp.atoms(model, "safe_ending"))
    py_ok = python_reasonable_story()
    if asp_ok != py_ok:
        print(f"MISMATCH: asp={asp_ok} python={py_ok}")
        return 1
    for seed in range(len(TALES) * 2):
        sample = generate(StoryParams(seed=seed))
        if not sample.story or not sample.story_qa or "“" not in sample.story:
            print(f"FAILED: generated story check for seed {seed}")
            return 1
    print("OK: ASP and Python agree; generated stories pass the story checks.")
    return 0


def generate(params: StoryParams) -> StorySample:
    seed = params.seed if params.seed is not None else 0
    tale = TALES[seed % len(TALES)]
    world = World(params=params)
    runner = world.entity(params.name, "runner")
    plot = world.entity(f"{params.village} garden plot", "garden_plot")
    companion = world.entity(params.companion, "companion")

    runner.add_meter("distance_run", 3)
    runner.add_meme("care", 1)
    runner.add_meme("doubt", 0.5)
    plot.add_meter("needs_help", 1)
    companion.add_meme("loyalty", 1)

    world.say(
        f"In the old days, in {params.village}, {params.name} was the swiftest runner "
        f"between the cottages and the garden plot. {params.companion} trotted at "
        f"{params.name}'s heels whenever the village bell rang."
    )
    world.say(
        f"One morning, trouble came to the plot where the villagers grew {params.crop}: "
        f"{tale['trouble']}. {params.name} saw {tale['clue']}."
    )
    world.say(
        f"At the path’s fork, {params.name} paused. *{tale['thought']}*, "
        f"{params.name} thought, and looked once more at the clue."
    )
    world.say(
        f"“What have you found?” called {params.companion}. "
        f"“A sign that can guide us,” said {params.name}. "
        f"“Then I’ll help you tell the neighbors,” the companion replied."
    )
    world.say(
        f"That was the turning of the tale: speed alone could not save the plot, "
        f"but careful eyes could bring many helping hands. {tale['plan']}."
    )
    world.say(
        f"By sunset, {tale['fix']}. The villagers thanked the runner, "
        f"and {params.companion} received the first crisp {params.crop} leaf."
    )
    world.say(
        f"From that day on, the garden flourished, for the villagers remembered "
        f"to listen to a runner who carried both a message and a thoughtful heart. "
        f"At dusk, {tale['image']}."
    )

    world.facts = {
        "title": tale["title"],
        "trouble": tale["trouble"],
        "clue": tale["clue"],
        "thought": tale["thought"],
        "plan": tale["plan"],
        "fix": tale["fix"],
        "image": tale["image"],
    }
    prompts = [
        f"Tell a folk tale about {params.name}, a runner in {params.village}.",
        f"Show how the clue, {tale['clue']}, changes the runner's choice.",
        f"End with the garden plot safe and this image: {tale['image']}.",
    ]
    story_qa = [
        QAItem(
            question="What trouble threatened the garden plot?",
            answer=f"{tale['trouble']}. It mattered because the villagers depended on the plot for their {params.crop}.",
        ),
        QAItem(
            question="Which clue helped the runner choose what to do?",
            answer=f"{tale['clue']}. The runner studied that sign before carrying a message to the neighbors.",
        ),
        QAItem(
            question="How did the runner's inner thought change the plan?",
            answer=f"The runner thought, “{tale['thought']}.” That pause turned a hasty run into a careful plan to gather help.",
        ),
        QAItem(
            question="How was the trouble resolved?",
            answer=f"{tale['fix']}. The neighbors followed the runner's message and worked together to protect the plot.",
        ),
        QAItem(
            question="What picture closes the tale?",
            answer=f"The final picture is this: {tale['image']}. It shows the garden after the neighbors have helped.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does a runner do in a village?",
            answer="A runner carries messages from one place to another, especially when people need news quickly.",
        ),
        QAItem(
            question="Why can a garden plot matter to a village?",
            answer="A garden plot gives neighbors a place to grow food and care for the plants together.",
        ),
        QAItem(
            question="What is an inner thought?",
            answer="An inner thought is something a character thinks privately; it can help the character pause, learn, or choose what to do.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.name} ({entity.kind}) meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== (3) World knowledge =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(
    sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise StoryError("-n must be at least 1.")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("safe_ending" if asp.atoms(model, "safe_ending") else "(no safe ending)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Lina",
            village=args.village or "Willowmere",
            crop=args.crop or "turnips",
            companion=args.companion or "a red-feathered hen",
        )
        samples = [generate(params)]
    else:
        samples = []
        for offset in range(args.n):
            rng = random.Random(base_seed + offset)
            params = resolve_params(args, rng)
            params.seed = base_seed + offset
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
    try:
        main()
    except StoryError as error:
        print(error, file=sys.stderr)
        sys.exit(2)
