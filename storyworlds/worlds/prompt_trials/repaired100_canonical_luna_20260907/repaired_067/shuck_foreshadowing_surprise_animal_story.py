#!/usr/bin/env python3
"""
A small animal story world about Shuck, a careful duckling, with foreshadowing
and a gentle surprise.

Seed premise:
- Shuck notices small signs before a surprise arrives.
- An animal friend wants to hurry toward a bright pond.
- Careful sharing and a helpful choice turn the surprise into a safe delight.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
foreshadowed(X) :- animal(X), notices_clue(X).
surprise_scene(P) :- pond(P), hidden_friend(P).
careful_choice(X) :- animal(X), follows_clue(X), helps_friend(X).
safe_story(X) :- foreshadowed(X), surprise_scene(pond), careful_choice(X).
"""

ANIMAL_NAMES = ["Shuck", "Milo", "Pip", "Clover", "Nell", "Bram"]
FRIEND_NAMES = ["Wren", "Tumble", "Moss", "Puddle", "Fern", "Biscuit"]
PLACES = ["the reed pond", "the berry meadow", "the old willow", "the clover bank"]
TREATS = ["a yellow apple", "three round berries", "a warm oat cake", "a shiny acorn"]
SOUNDS = ["tap-tap", "rustle-rustle", "plop", "hush"]


@dataclass(frozen=True)
class Incident:
    title: str
    premise: str
    early_clue: str
    mistaken_guess: str
    danger: str
    brave_plan: str
    surprise: str
    result: str
    sharing: str
    joke: str
    ending: str


INCIDENTS = [
    Incident(
        title="the silver ripples",
        premise="Shuck and Wren carried a basket toward the reed pond on a bright morning.",
        early_clue="three little ripples moved against the breeze near the lily pads",
        mistaken_guess="a shiny stone was hiding under the water",
        danger="the deepest mud waited just beyond the dry grass",
        brave_plan="stop at the bank, call softly, and use a long reed to test the ground",
        surprise="a family of tiny frogs popped up wearing petals like hats",
        result="the frogs hopped safely onto the warm stones",
        sharing="set the basket between the animals and offered each friend one berry",
        joke="the frog hats were much too fancy for an ordinary pond",
        ending="At sunset, the petal-hatted frogs blinked beside the quiet water while Shuck's basket stood empty.",
    ),
    Incident(
        title="the whispering leaves",
        premise="Shuck followed Clover beneath the old willow to gather fallen apples.",
        early_clue="the willow leaves whispered even though the branches were still",
        mistaken_guess="the tree was telling a secret about hidden fruit",
        danger="a loose branch hung above the path",
        brave_plan="move everyone away, point out the swinging twig, and ask the wind to settle",
        surprise="a nest of sleepy field mice tumbled gently from a safe fork onto a bed of leaves",
        result="the mice found a dry hollow while the animals passed beneath the cleared branch",
        sharing="placed the apples in a common pile and left the softest one near the mouse hollow",
        joke="the willow had been practicing mouse-sized applause",
        ending="The empty branch waved over a neat apple circle and a warm, safe mouse hollow.",
    ),
    Incident(
        title="the blue feather",
        premise="Shuck and Tumble crossed the clover bank when a blue feather spun beside them.",
        early_clue="the feather always turned back toward a patch of tall grass",
        mistaken_guess="a bird had dropped a decoration for a picnic",
        danger="the tall grass hid a narrow ditch filled with rainwater",
        brave_plan="follow the feather from the side, warn Tumble, and circle around the ditch",
        surprise="a young kingfisher rose from the grass with the missing feather in its beak",
        result="the bird reached its nest without anyone stepping into the ditch",
        sharing="returned the feather and divided the oat cake under the open sky",
        joke="the kingfisher had brought its own napkin and still looked untidy",
        ending="The blue feather rested in the nest while crumbs dotted the safe path home.",
    ),
    Incident(
        title="the bobbing basket",
        premise="Shuck saw a little basket bobbing near the edge of the berry meadow.",
        early_clue="the basket moved in a pattern that matched a quiet squeak",
        mistaken_guess="the meadow breeze was playing with an empty basket",
        danger="the basket was drifting toward a thorny bramble patch",
        brave_plan="ask Wren to fetch a branch and pull the basket from the dry side",
        surprise="a sleepy hedgehog curled inside, holding one stolen berry",
        result="the hedgehog rolled away from the thorns and woke beneath a fern",
        sharing="washed the berries and saved the ripest one for the hedgehog",
        joke="the hedgehog had packed a picnic but forgotten the picnic blanket",
        ending="A single berry gleamed beside the fern as the basket rested safely on the grass.",
    ),
    Incident(
        title="the moonlit plop",
        premise="Shuck and Fern watched the pond after the first evening star appeared.",
        early_clue="a soft plop came twice from the dark water, then stopped",
        mistaken_guess="a pebble had fallen from the willow",
        danger="Fern wanted to lean far over the slippery bank",
        brave_plan="hold Fern's wing, stay on the flat stones, and shine a firefly jar from a distance",
        surprise="a lost duckling paddled out from behind the reeds",
        result="the duckling followed the firefly glow back to its waiting family",
        sharing="passed the oat cake around and left crumbs on the shore for the duckling's family",
        joke="the duckling had made a grand entrance without learning its lines",
        ending="Fireflies floated above the reunited family while the pond settled into silver rings.",
    ),
]


@dataclass
class Animal:
    id: str
    species: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    name: str
    friend: str
    place: str
    treat: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    hero: Animal
    friend: Animal
    treat: str
    incident: Incident
    route: int = 0
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


OPENINGS = [
    "The morning began with {title}.",
    "At {place}, Shuck noticed something before anyone else did: {title}.",
    "The animals had planned a simple walk, but {title} changed the day.",
    "A tiny clue waited beside {title}.",
    "Shuck expected berries, not {title}.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animal story world with foreshadowing and a gentle surprise."
    )
    parser.add_argument("--name", choices=ANIMAL_NAMES)
    parser.add_argument("--friend", choices=FRIEND_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--treat", choices=TREATS)
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
        name=args.name or rng.choice(ANIMAL_NAMES),
        friend=args.friend or rng.choice(FRIEND_NAMES),
        place=args.place or rng.choice(PLACES),
        treat=args.treat or rng.choice(TREATS),
    )


def make_world(params: StoryParams) -> World:
    if params.name == params.friend:
        raise StoryError("The hero and friend must have different names.")
    if params.name != "Shuck":
        hero_name = params.name
    else:
        hero_name = "Shuck"
    hero = Animal(
        id=hero_name,
        species="duckling",
        meters={"caution": 1.0, "kindness": 0.8},
        memes={"wonder": 0.7, "trust": 0.6},
    )
    friend = Animal(
        id=params.friend,
        species="small animal",
        meters={"curiosity": 0.9, "patience": 0.4},
        memes={"friendship": 0.8},
    )
    key = params.seed
    if key is None:
        key = sum(ord(char) for char in "|".join(
            [params.name, params.friend, params.place, params.treat]
        ))
    incident = INCIDENTS[key % len(INCIDENTS)]
    return World(
        setting=Setting(place=params.place),
        hero=hero,
        friend=friend,
        treat=params.treat,
        incident=incident,
        route=(key // len(INCIDENTS)) % len(OPENINGS),
    )


def tell(world: World) -> None:
    incident = world.incident
    hero = world.hero
    friend = world.friend
    opening = OPENINGS[world.route].format(
        title=incident.title,
        place=world.setting.place,
    )
    world.say(f"{opening} {incident.premise}")
    world.say(
        f"Before they reached the bright part of {world.setting.place}, "
        f"Shuck saw that {incident.early_clue}. "
        "The small sign made Shuck slow down."
    )
    world.para()
    world.say(
        f'"Maybe {incident.mistaken_guess}," said {friend.id}. '
        f'"Let us look first," said {hero.id}. '
        f'"The clue may be telling us something important."'
    )
    world.say(
        f"Shuck noticed that {incident.danger}. "
        f"Instead of rushing, Shuck decided to {incident.brave_plan}."
    )
    world.para()
    world.say(
        f"That careful choice brought a surprise: {incident.surprise}. "
        f"{incident.result}."
    )
    world.say(
        f"Then the friends {incident.sharing}. "
        f"The {world.treat} became a treat for everyone, not a prize for the fastest animal."
    )
    world.para()
    world.say(
        f'"{incident.joke.capitalize()}," said {friend.id}. '
        f"Shuck laughed, and the surprise felt warm instead of frightening."
    )
    world.say(
        f"By listening to the early clue, Shuck had helped a friend and made room "
        f"for an unexpected kindness. {incident.ending}"
    )
    world.facts.update(
        hero=hero,
        friend=friend,
        setting=world.setting,
        incident=incident,
        clue=incident.early_clue,
        danger=incident.danger,
        plan=incident.brave_plan,
        surprise=incident.surprise,
        result=incident.result,
        ending=incident.ending,
    )


def generation_prompts(world: World) -> list[str]:
    incident = world.incident
    return [
        f"Write an animal story about Shuck at {world.setting.place}. "
        f"Use the foreshadowing clue that {incident.early_clue}, then reveal "
        f"the surprise that {incident.surprise}.",
        f"Tell a child-friendly story in which Shuck and {world.friend.id} "
        f"avoid {incident.danger} by following an early clue.",
        f"Write a gentle animal tale with dialogue, a careful choice, "
        f"fair sharing of {world.treat}, and an ending that shows {incident.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    incident = world.incident
    return [
        QAItem(
            question="What early clue did Shuck notice?",
            answer=(
                f"Shuck noticed that {incident.early_clue}. "
                "That small sign made Shuck pause instead of rushing."
            ),
        ),
        QAItem(
            question=f"What danger did Shuck help {world.friend.id} avoid?",
            answer=(
                f"Shuck helped avoid {incident.danger}. "
                f"Shuck did this by deciding to {incident.brave_plan}."
            ),
        ),
        QAItem(
            question="What was the surprise?",
            answer=(
                f"The surprise was that {incident.surprise}. "
                f"It was safe because {incident.result}."
            ),
        ),
        QAItem(
            question="How did Shuck and the friend respond to the surprise?",
            answer=(
                f"They stayed calm, helped the animal or animals involved, and then "
                f"{incident.sharing}. Their careful response turned surprise into kindness."
            ),
        ),
        QAItem(
            question="How did the dialogue change what happened?",
            answer=(
                f"{world.friend.id} suggested {incident.mistaken_guess}, but Shuck "
                "asked everyone to look first. That exchange led them to follow the "
                "clue and choose a safer plan."
            ),
        ),
        QAItem(
            question="What proves the story ended well?",
            answer=(
                f"The ending image is this: {incident.ending} "
                "It shows that the danger was over and the animals were safe."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer=(
                "Foreshadowing is an early clue that hints something important may "
                "happen later. In this story, Shuck notices a small sign before the surprise."
            ),
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer=(
                "A surprise is an unexpected event or discovery. A good story prepares "
                "readers with clues while still making the reveal feel special."
            ),
        ),
        QAItem(
            question="Why should an animal stop and inspect a warning sign?",
            answer=(
                "Stopping helps the animal understand the situation, avoid danger, "
                "and choose a helpful action instead of making a rushed guess."
            ),
        ),
    ]


def dump_trace(world: World) -> str:
    incident = world.incident
    return "\n".join(
        [
            "--- world model state ---",
            (
                f"hero={world.hero.id} species={world.hero.species} "
                f"meters={world.hero.meters} memes={world.hero.memes}"
            ),
            (
                f"friend={world.friend.id} species={world.friend.species} "
                f"meters={world.friend.meters} memes={world.friend.memes}"
            ),
            f"place={world.setting.place}",
            f"treat={world.treat}",
            f"incident={incident.title}",
            f"foreshadowing={incident.early_clue}",
            f"danger={incident.danger}",
            f"surprise={incident.surprise}",
            f"result={incident.result}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    from storyworlds import asp

    return "\n".join(
        [
            asp.fact("animal", "shuck"),
            asp.fact("animal", "friend"),
            asp.fact("notices_clue", "shuck"),
            asp.fact("follows_clue", "shuck"),
            asp.fact("helps_friend", "shuck"),
            asp.fact("pond", "pond"),
            asp.fact("hidden_friend", "pond"),
        ]
    )


def asp_program(show: str = "#show safe_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    from storyworlds import asp

    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "safe_story"))
    expected = {("shuck",)}
    if actual != expected:
        print(f"MISMATCH: ASP safe_story={actual!r}, expected={expected!r}")
        return 1
    sample = generate(
        StoryParams(
            name="Shuck",
            friend="Wren",
            place="the reed pond",
            treat="a yellow apple",
            seed=0,
        )
    )
    if "Shuck" not in sample.story or not sample.story.endswith("."):
        print("MISMATCH: generated story validation failed")
        return 1
    if not any("surprise" in prompt.lower() for prompt in sample.prompts):
        print("MISMATCH: prompt validation failed")
        return 1
    print("OK: ASP parity and story generation verified.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated() -> list[StoryParams]:
    return [
        StoryParams(
            name="Shuck",
            friend="Wren",
            place="the reed pond",
            treat="a yellow apple",
            seed=0,
        ),
        StoryParams(
            name="Shuck",
            friend="Clover",
            place="the old willow",
            treat="three round berries",
            seed=1,
        ),
        StoryParams(
            name="Shuck",
            friend="Tumble",
            place="the clover bank",
            treat="a warm oat cake",
            seed=2,
        ),
        StoryParams(
            name="Shuck",
            friend="Fern",
            place="the berry meadow",
            treat="a shiny acorn",
            seed=3,
        ),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        from storyworlds import asp

        model = asp.one_model(
            asp_program(
                "#show foreshadowed/1.\n"
                "#show surprise_scene/1.\n"
                "#show careful_choice/1.\n"
                "#show safe_story/1."
            )
        )
        print("\n".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in curated()]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        for index in range(args.n):
            local_seed = base_seed + index
            params = resolve_params(args, random.Random(local_seed))
            params.seed = local_seed
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
