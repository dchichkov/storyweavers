#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about toe-pl-dim, where kind dialogue
helps a little character repair a wobbly plan.
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    helper: str
    object_name: str
    place: str
    rhyme: str = "couplets"
    kindness: str = "gentle_words"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    key: str
    title: str
    problem: str
    cause: str
    repair: str
    image: str


NAMES = ["Luna", "Milo", "Pip", "Nell", "Toby", "Wren"]
HELPERS = ["Mara", "Ollie", "Tess", "Jun"]
OBJECTS = ["a blue button", "a moon-white bead", "a red ribbon", "a tiny bell"]
PLACES = ["the nursery window", "the patchwork rug", "the little garden gate", "the toy shelf"]
RHYMES = ["couplets", "refrain", "lullaby"]
KINDNESSES = ["gentle_words", "patient_listening", "shared_try"]
TRIALS = [
    Trial(
        "button",
        "the button boat",
        "the button boat bumped a block and tipped its paper sail into the dust",
        "the sail's thread had loosened while the boat was being pushed too fast",
        "tie the thread twice and push the boat slowly around the block",
        "the blue button sailed in a saucer of moonlight",
    ),
    Trial(
        "bead",
        "the bead parade",
        "the moon-white bead rolled away before it could join the nursery parade",
        "a loose spoon had made a sloping path across the table",
        "block the slope with a cloth and roll the bead back beside its friends",
        "the bead shone like a little moon among the toy stars",
    ),
    Trial(
        "ribbon",
        "the ribbon kite",
        "the red ribbon kite drooped and kissed the floor instead of dancing high",
        "one paper loop had folded flat beneath the string",
        "open the loop gently and hold the string where the window breeze could find it",
        "the ribbon fluttered pink and bright above the sleepy toys",
    ),
    Trial(
        "bell",
        "the tiny bell march",
        "the tiny bell gave a dull plunk when the marching toys expected a ding",
        "a soft wool thread had slipped inside the bell's little clapper",
        "lift the thread out with care and test the bell beside a cushion",
        "one clear ding twinkled over the quiet nursery",
    ),
]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def find_trial(key: str) -> Trial:
    for trial in TRIALS:
        if trial.key == key:
            return trial
    raise StoryError(f"Unknown toe-pl-dim trial: {key}")


def complete_params(params: StoryParams) -> None:
    if params.name not in NAMES:
        raise StoryError(f"Name must be one of {', '.join(NAMES)}.")
    if params.helper not in HELPERS:
        raise StoryError(f"Helper must be one of {', '.join(HELPERS)}.")
    if params.object_name not in OBJECTS:
        raise StoryError(f"Object must be one of {', '.join(OBJECTS)}.")
    if params.place not in PLACES:
        raise StoryError(f"Place must be one of {', '.join(PLACES)}.")
    if params.rhyme not in RHYMES:
        raise StoryError(f"Rhyme must be one of {', '.join(RHYMES)}.")
    if params.kindness not in KINDNESSES:
        raise StoryError(f"Kindness path must be one of {', '.join(KINDNESSES)}.")


def choose_trial(params: StoryParams) -> Trial:
    seed = params.seed if params.seed is not None else 0
    return TRIALS[random.Random(seed + 71).randrange(len(TRIALS))]


def build_world(params: StoryParams) -> World:
    complete_params(params)
    trial = choose_trial(params)
    world = World()
    child = Entity(
        "child",
        "character",
        params.name,
        "child",
        meters={"worry": 0.0, "confidence": 0.0, "joy": 0.0},
        memes={"kindness": 0.0, "hope": 0.0},
    )
    helper = Entity(
        "helper",
        "character",
        params.helper,
        "friend",
        meters={"patience": 2.0},
        memes={"care": 2.0},
    )
    prop = Entity(
        "prop",
        "object",
        params.object_name,
        meters={"stability": 1.0},
        memes={"play": 1.0},
    )
    world.add(child)
    world.add(helper)
    world.add(prop)
    world.facts.update(params=params, trial=trial, child=child, helper=helper, prop=prop)
    return world


def rhyme_line(params: StoryParams, first: str, second: str) -> str:
    if params.rhyme == "couplets":
        return f"{first} {second}"
    if params.rhyme == "refrain":
        return f"{first} And toe-pl-dim, toe-pl-dim, try once more with care; {second}"
    return f"{first} Soft as a lullaby, {second}"


def begin(world: World) -> None:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    trial: Trial = world.facts["trial"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    world.say(
        f"In {params.place}, {child.label} prepared {trial.title} with "
        f"{params.object_name} beneath the sleepy moon."
    )
    world.say(
        rhyme_line(
            params,
            f"Toe-pl-dim, toe-pl-dim, tap went the toe;",
            f"{child.label} made a small plan and began it just so.",
        )
    )


def trouble(world: World) -> None:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    trial: Trial = world.facts["trial"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    child.meters["worry"] += 2
    child.memes["hope"] -= 1
    world.say(trial.problem.capitalize() + ".")
    world.say(f"{trial.cause.capitalize()}.")
    world.say(
        f'"Oh dear," said {child.label}. "My {trial.title} is all mixed up. '
        f'What shall I do?"'
    )


def kind_dialogue(world: World) -> None:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    kindness = params.kindness
    helper.meters["patience"] += 1
    helper.memes["care"] += 1
    child.memes["kindness"] += 1
    if kindness == "gentle_words":
        line = (
            f'"No blame, {child.label}," said {helper.label}. '
            f'"Let us use gentle words and look at one small thing."'
        )
    elif kindness == "patient_listening":
        line = (
            f'"Tell me what you noticed," said {helper.label}. '
            f'"I will listen before we choose a fix."'
        )
    else:
        line = (
            f'"You need not mend it alone," said {helper.label}. '
            f'"You try one part, and I will share the next."'
        )
    world.say(line)
    world.say(
        f'"Then I can try again," said {child.label}. '
        f'"Thank you for helping me think."'
    )


def repair(world: World) -> None:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    trial: Trial = world.facts["trial"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    prop: Entity = world.facts["prop"]  # type: ignore[assignment]
    child.meters["worry"] -= 2
    child.meters["confidence"] += 2
    child.memes["hope"] += 2
    prop.meters["stability"] += 2
    world.say(f"Together, they saw the true trouble: {trial.cause}.")
    world.say(f"{child.label} followed the kind plan to {trial.repair}.")
    world.say(
        rhyme_line(
            params,
            "Toe-pl-dim, toe-pl-dim, steady and bright;",
            "a little kind helping can set things right.",
        )
    )


def finish(world: World) -> None:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    trial: Trial = world.facts["trial"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    child.meters["joy"] += 2
    world.say(f"At last, {trial.image}.")
    world.say(
        f'"We did it kindly," said {child.label}. '
        f'"Yes," said {helper.label}, "and kind words helped us notice what to do."'
    )
    world.say(
        rhyme_line(
            params,
            f"Toe-pl-dim, toe-pl-dim, the nursery grew still;",
            f"with kindness in words, there is courage and skill.",
        )
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    begin(world)
    trouble(world)
    world.para()
    kind_dialogue(world)
    repair(world)
    world.para()
    finish(world)
    return world


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    trial: Trial = world.facts["trial"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was {child.label} trying to do in the toe-pl-dim nursery rhyme?",
            answer=f"{child.label} was trying {trial.title} with {params.object_name} in {params.place}."
        ),
        QAItem(
            question=f"What went wrong for {child.label}?",
            answer=f"{trial.problem.capitalize()}. The cause was that {trial.cause}."
        ),
        QAItem(
            question=f"What did {helper.label} say or do to show kindness?",
            answer=f"{helper.label} used a kind dialogue response and helped {child.label} examine one small part of the problem without blame."
        ),
        QAItem(
            question="How was the problem repaired?",
            answer=f"{child.label} and the helper followed a calm plan: {trial.repair}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is the spoken conversation characters have with one another."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means treating someone with care, patience, and helpful words or actions."
        ),
        QAItem(
            question="Why is it useful to find the true cause of a problem?",
            answer="Finding the true cause helps people choose a repair that fits instead of guessing."
        ),
        QAItem(
            question="What is a nursery rhyme?",
            answer="A nursery rhyme is a short, playful poem or song with a simple rhythm and memorable words."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    trial: Trial = world.facts["trial"]  # type: ignore[assignment]
    return [
        f"Write a Nursery Rhyme story using the seed words toe-pl-dim, with Dialogue and Kindness.",
        f"Tell a child-friendly story about {params.name} repairing {trial.title} in {params.place}.",
        "Include a brief back-and-forth exchange where kind words change what a character does.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(out)


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("seed", "toe_pl_dim"),
            asp.fact("feature", "dialogue"),
            asp.fact("feature", "kindness"),
            asp.fact("style", "nursery_rhyme"),
            asp.fact("requires", "repair"),
            asp.fact("requires", "spoken_exchange"),
        ]
    )


ASP_RULES = r"""
valid_world :-
    seed(toe_pl_dim),
    feature(dialogue),
    feature(kindness),
    style(nursery_rhyme),
    requires(repair),
    requires(spoken_exchange).

#show valid_world/0.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    ok = bool(asp.atoms(model, "valid_world"))
    if not ok:
        print("MISMATCH: ASP gate failed.")
        return 1
    for seed in range(3):
        params = StoryParams(
            name="Luna",
            helper="Mara",
            object_name="a blue button",
            place="the nursery window",
            seed=seed,
        )
        sample = generate(params)
        if "toe-pl-dim" not in sample.story or "said" not in sample.story:
            print("MISMATCH: generated story lacks required narrative features.")
            return 1
    print("OK: ASP and Python gates agree; generated stories passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="The toe-pl-dim kindness nursery-rhyme world.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--rhyme", choices=RHYMES)
    parser.add_argument("--kindness", choices=KINDNESSES)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        object_name=args.object_name or rng.choice(OBJECTS),
        place=args.place or rng.choice(PLACES),
        rhyme=args.rhyme or rng.choice(RHYMES),
        kindness=args.kindness or rng.choice(KINDNESSES),
        seed=args.seed,
    )


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
        print("--- trace ---")
        for entity in sample.world.entities.values():
            meters = {key: value for key, value in entity.meters.items() if value}
            memes = {key: value for key, value in entity.memes.items() if value}
            print(f"{entity.label}: meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Mara", "a blue button", "the nursery window", seed=11),
    StoryParams("Milo", "Ollie", "a tiny bell", "the patchwork rug", seed=22),
    StoryParams("Nell", "Tess", "a red ribbon", "the toy shelf", seed=33),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        print(asp.atoms(model, "valid_world"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for offset in range(max(1, args.n)):
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
    main()
