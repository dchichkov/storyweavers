#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about naked bravery and friendship.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


@dataclass
class StoryParams:
    child: str
    friend: str
    helper: str
    problem: str
    bravery: str
    ending: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Problem:
    sign: str
    danger: str
    response: str
    result: str


@dataclass(frozen=True)
class Bravery:
    fear: str
    choice: str
    lesson: str


@dataclass(frozen=True)
class Ending:
    image: str
    line: str


NAMES = ["Nell", "Pip", "Mia", "Tom", "Kit", "Lulu", "Ben", "Tess"]
HELPERS = ["the moon", "the old bell", "a kind robin"]

PROBLEMS = {
    "lost_lamb": Problem(
        "A little lamb bleated beyond the hedge",
        "it had wandered into a dark, muddy ditch",
        "followed the lamb's soft calls and lowered a long scarf into the ditch",
        "the lamb climbed up and skipped safely home",
    ),
    "fallen_star": Problem(
        "A small star tumbled from the sky",
        "it lay cold and dim beneath the garden gate",
        "crossed the dewy grass and carried the star to the highest hill",
        "the star shone again and climbed back into the sky",
    ),
    "broken_bridge": Problem(
        "The brook sang louder than before",
        "the little bridge had lost one of its boards",
        "held hands and placed flat stones across the shallow water",
        "their friends crossed the brook without a single splash",
    ),
    "sleepy_dragon": Problem(
        "A tiny dragon sneezed beside the village lane",
        "smoke curled around its nose and frightened everyone away",
        "walked close enough to offer a cool cloth and a friendly song",
        "the dragon stopped sneezing and puffed only silver bubbles",
    ),
    "flooded_nest": Problem(
        "Rain drummed hard on the willow tree",
        "a bird's nest was slipping toward the rushing stream",
        "carried twigs one by one and built a dry nest under the eaves",
        "the birds settled safely while the rain tapped on",
    ),
}

BRAVERIES = {
    "speak_up": Bravery(
        "a tremble in the knees",
        "spoke clearly even though the dark made the voice quiver",
        "bravery can begin with one honest voice",
    ),
    "step_forward": Bravery(
        "a wish to hide behind the others",
        "stepped forward first and invited the friend to come along",
        "courage grows when friends make room for one another",
    ),
    "ask_help": Bravery(
        "not knowing the right way alone",
        "asked for help instead of pretending to know everything",
        "a brave question can open a safe path",
    ),
    "keep_going": Bravery(
        "cold feet and a long road",
        "kept going slowly, with a friend beside the frightened heart",
        "bravery is not the absence of fear but a steady step through it",
    ),
}

ENDINGS = {
    "dawn": Ending(
        "At dawn, two bright footprints crossed the silver meadow",
        "Naked of pride, but clothed in courage, the friends danced home",
    ),
    "lantern": Ending(
        "That night, a warm lantern glowed beside the garden gate",
        "Friendship made the little light seem wide as day",
    ),
    "rhyme": Ending(
        "The moon sang softly, and the brook chimed along",
        "Brave hearts beat together in a bright little song",
    ),
    "feast": Ending(
        "The neighbors set out berries, buns, and a blue bowl of milk",
        "The friends shared every bite, for friendship makes a feast",
    ),
}

REFLECTIONS = {
    "moon": "The moon watched quietly, then painted a silver path for their feet",
    "robin": "The robin chirped three notes, as if praising their careful teamwork",
    "bell": "The old bell rang once, not for alarm, but for joy",
    "rain": "The last raindrop glittered like a tiny medal on the grass",
}


def valid_combos() -> list[tuple[str, str]]:
    return [("nursery", "friendship")]


def explain_rejection() -> str:
    return "This storyworld only supports a nursery-rhyme tale about friendship and bravery."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Naked bravery nursery-rhyme storyworld.")
    parser.add_argument("--child")
    parser.add_argument("--friend")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--bravery", choices=BRAVERIES)
    parser.add_argument("--ending", choices=ENDINGS)
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
    child = args.child or rng.choice(NAMES)
    friend = args.friend or rng.choice([name for name in NAMES if name != child])
    if child == friend:
        raise StoryError("The two friends need different names.")
    return StoryParams(
        child=child,
        friend=friend,
        helper=args.helper or rng.choice(HELPERS),
        problem=args.problem or rng.choice(tuple(PROBLEMS)),
        bravery=args.bravery or rng.choice(tuple(BRAVERIES)),
        ending=args.ending or rng.choice(tuple(ENDINGS)),
    )


def tell(params: StoryParams) -> World:
    problem = PROBLEMS[params.problem]
    bravery = BRAVERIES[params.bravery]
    ending = ENDINGS[params.ending]

    world = World()
    child = world.add(Entity(params.child, "child", params.child, "meadow"))
    friend = world.add(Entity(params.friend, "friend", params.friend, "meadow"))
    helper = world.add(Entity("helper", "helper", params.helper, "nearby"))

    child.meters["courage"] = 0.4
    friend.meters["courage"] = 0.5
    child.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    world.facts.update(child=child, friend=friend, helper=helper, problem=problem, bravery=bravery)

    world.say(f"One bright day, {child.label} and {friend.label} played where the green grasses sway.")
    world.say(f"They wore no proud armor, no crown, and no shield; they stood naked of pretense in the wide-open field.")
    world.say(f"{problem.sign}; {problem.danger}.")
    world.para()

    world.say(f"{child.label} felt {bravery.fear}, while {friend.label} held close.")
    world.say(f"But {child.label} {bravery.choice}.")
    child.meters["courage"] = 1.0
    friend.meters["courage"] = 0.9
    world.fired.add("bravery_awakened")

    world.say(f"{friend.label} joined in, for a friend will not flee.")
    world.say(f"Together they {problem.response}.")
    world.facts["resolved"] = True
    world.facts["changed"] = problem.result
    world.para()

    world.say(f"Then {problem.result}.")
    world.say(f"{REFLECTIONS[params.helper.split()[-1]] if params.helper.split()[-1] in REFLECTIONS else 'The quiet world smiled around them'}.")
    world.say(f"They learned that {bravery.lesson}.")
    world.say(f"{ending.image}.")
    world.say(ending.line)
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    problem = world.facts["problem"]
    return [
        f"Write a nursery rhyme about {child.label} and {friend.label}, whose friendship faces this danger: {problem.danger}.",
        f"Show how naked bravery helps {child.label} and {friend.label} solve the problem together.",
        "End with a warm image proving that friendship has changed the day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    problem = world.facts["problem"]
    bravery = world.facts["bravery"]
    return [
        QAItem(
            question=f"Who were the two friends in the rhyme?",
            answer=f"The two friends were {child.label} and {friend.label}. They stayed together when the trouble began.",
        ),
        QAItem(
            question=f"What danger did {child.label} notice?",
            answer=f"{child.label} noticed that {problem.danger}. The danger made the quiet day suddenly unsafe.",
        ),
        QAItem(
            question=f"How did the friends show bravery?",
            answer=f"{child.label} {bravery.choice}, and {friend.label} joined in instead of running away.",
        ),
        QAItem(
            question="What did the friends learn?",
            answer=f"They learned that {bravery.lesson}. Their friendship helped them finish the careful rescue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is choosing a helpful or safe action even when something feels frightening.",
        ),
        QAItem(
            question="Why is friendship useful during a difficult task?",
            answer="Friendship gives people encouragement and lets them share work so a difficult task can be handled more safely.",
        ),
        QAItem(
            question="Does being brave mean never feeling afraid?",
            answer="No. A brave person may feel afraid but still take a careful, kind step forward.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind} location={entity.location} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(nursery).
feature(bravery).
feature(friendship).
valid(nursery,bravery,friendship).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "nursery"),
            asp.fact("feature", "bravery"),
            asp.fact("feature", "friendship"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if python_combos != asp_combos:
        print("MISMATCH between Python and ASP combinations.")
        print("Python only:", sorted(python_combos - asp_combos))
        print("ASP only:", sorted(asp_combos - python_combos))
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("Generated story verification failed.")
            return 1
    print("OK: ASP/Python parity and generated stories verified.")
    return 0


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


def show_qa_item(item: QAItem) -> str:
    return f"Q: {item.question}\nA: {item.answer}"


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"[Prompt {index}] {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print()
            print(show_qa_item(item))


CURATED = [
    StoryParams(
        child="Nell",
        friend="Pip",
        helper="the moon",
        problem="lost_lamb",
        bravery="step_forward",
        ending="dawn",
    ),
    StoryParams(
        child="Mia",
        friend="Tom",
        helper="the old bell",
        problem="broken_bridge",
        bravery="keep_going",
        ending="rhyme",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n) and attempt < max(50, args.n * 20):
            current_seed = base_seed + attempt
            attempt += 1
            try:
                params = resolve_params(args, random.Random(current_seed))
            except StoryError as error:
                print(error)
                return
            params.seed = current_seed
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
