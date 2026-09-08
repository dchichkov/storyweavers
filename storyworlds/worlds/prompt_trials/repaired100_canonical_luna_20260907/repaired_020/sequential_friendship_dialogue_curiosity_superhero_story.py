#!/usr/bin/env python3
"""
A tiny superhero storyworld about Luna, a curious friend, and a sequence of
small brave choices.
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
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Milo"
    companion: str = "Pip"
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs.append(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


SEQUENCES = [
    {
        "setting": "the rooftop garden above Brightside City",
        "mystery": "three silver lights blinking in a careful row",
        "clue": "a tiny paper star caught on the water tower",
        "danger": "the city beacon had lost its guiding signal",
        "answer": "a frightened rescue drone was trying to call home",
        "step_one": "followed the blinking lights without touching the loose wires",
        "step_two": "asked the drone what it needed and listened to its soft beeps",
        "step_three": "held up a mirror so the beacon could guide the drone toward its charging nest",
        "ending": "the beacon shone in a clear blue line while the little drone rested beside the rooftop tomatoes",
    },
    {
        "setting": "the old train station beneath a violet evening sky",
        "mystery": "a red umbrella rolling uphill against the wind",
        "clue": "a warm pawprint on the station map",
        "danger": "a lost service robot was wandering toward the closed tunnel",
        "answer": "a small robot had mistaken the umbrella's handle for its owner's hand",
        "step_one": "blocked the tunnel with a bright ribbon",
        "step_two": "spoke gently until the robot stopped and showed its memory card",
        "step_three": "used the station bell to call the waiting caretaker",
        "ending": "the robot rode safely home while the red umbrella stood like a cheerful flag",
    },
    {
        "setting": "the moonlit library tower",
        "mystery": "a comic book fluttering from shelf to shelf",
        "clue": "a trail of glowing dust beside the window latch",
        "danger": "the library's story-lantern was about to fall into the street",
        "answer": "a curious cloud sprite had opened the latch while chasing a bright bookmark",
        "step_one": "closed the lower windows and cleared the reading steps",
        "step_two": "asked the sprite to point toward the bookmark",
        "step_three": "returned the bookmark and tied the lantern with a silver cord",
        "ending": "the story-lantern glowed above the tower, and the cloud sprite curled up in its warm light",
    },
    {
        "setting": "the riverside market after a sudden rain",
        "mystery": "a yellow cape floating beneath the bridge",
        "clue": "a row of bubbles traveling upstream",
        "danger": "someone might be trapped behind the floodgate",
        "answer": "a young inventor's wind-up raft had pulled the cape along the current",
        "step_one": "checked the bridge supports before stepping near the water",
        "step_two": "called out and waited for an answer",
        "step_three": "used a rescue rope to pull the raft into the shallow reeds",
        "ending": "the inventor hugged the rescued cape while the river carried the rain away",
    },
]

HEROES = ["Luna", "Nova", "Ari", "Sol"]
FRIENDS = ["Milo", "Jade", "Theo", "Nia"]
COMPANIONS = ["Pip", "Bram", "Zee", "Kiko"]


def tell_story(params: StoryParams) -> World:
    if params.hero == params.friend:
        raise StoryError("The hero and friend must have different names.")
    if params.hero == params.companion or params.friend == params.companion:
        raise StoryError("The three story companions must have different names.")

    seed = params.seed or 0
    arc = SEQUENCES[seed % len(SEQUENCES)]
    world = World()

    hero = world.add(Entity(params.hero, "hero", params.hero))
    friend = world.add(Entity(params.friend, "friend", params.friend))
    companion = world.add(Entity(params.companion, "companion", params.companion))

    hero.meters.update(courage=1.0, attention=0.0)
    friend.meters.update(courage=0.8, attention=0.0)
    companion.meters.update(speed=0.5)
    hero.memes["friendship"] = 1.0
    friend.memes["curiosity"] = 1.0
    companion.memes["trust"] = 0.3

    world.facts.update(
        setting=arc["setting"],
        mystery=arc["mystery"],
        clue=arc["clue"],
        danger=arc["danger"],
        answer=arc["answer"],
        step_one=arc["step_one"],
        step_two=arc["step_two"],
        step_three=arc["step_three"],
        ending=arc["ending"],
        resolved=False,
        sequence=seed % len(SEQUENCES),
    )

    world.say(
        f"In {arc['setting']}, {hero.label} wore a bright red cape and practiced small acts of courage. "
        f"{friend.label} and {companion.label} were her trusted friends, and together they watched over the neighborhood."
    )
    world.say(
        f"One evening, they noticed {arc['mystery']}. Nobody knew whether it was a warning, a secret message, "
        f"or a new problem waiting to grow."
    )
    world.say(
        f'"We should not rush," said {friend.label}. "Curiosity can help us, but only if we ask careful questions." '
        f'{hero.label} nodded. "Then we will solve it sequentially, one safe step at a time."'
    )

    world.facts["clue_found"] = True
    hero.meters["attention"] = 1.0
    friend.meters["attention"] = 1.0
    world.say(
        f"First, they examined {arc['clue']}. The clue showed that {arc['danger']} might be nearby, "
        f"so {hero.label} {arc['step_one']}."
    )

    world.facts["question_asked"] = True
    friend.memes["curiosity"] = 2.0
    world.say(
        f"Next, {friend.label} stepped beside her. 'Can you tell us what happened?' {friend.label} asked. "
        f"The hidden helper answered with a quiet signal: {arc['answer']}."
    )

    world.facts["plan_known"] = True
    companion.memes["trust"] = 1.0
    world.say(
        f"Finally, the friends made a plan. {hero.label} {arc['step_two']}, and then {hero.label} "
        f"{arc['step_three']}. Their friendship made the frightening mystery feel possible to solve."
    )

    world.facts["resolved"] = True
    hero.meters["courage"] = 2.0
    friend.meters["courage"] = 1.5
    world.say(
        f"The danger passed without anyone being hurt. {hero.label} lowered her cape and smiled at {friend.label}. "
        f'"You asked the question that unlocked the answer," she said. "And you stayed with me," replied {friend.label}.'
    )
    world.say(
        f"By moonrise, {arc['ending']}. The friends did not feel like heroes because they were fearless. "
        "They felt like heroes because they listened, trusted one another, and took the next right step."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly superhero story about friendship, dialogue, and curiosity.",
        f"Tell a sequential adventure in {f['setting']} involving {f['mystery']}.",
        f"Write a superhero rescue where the friends discover that {f['answer']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.entities["hero"].label
    friend = world.entities["friend"].label
    return [
        QAItem(
            question=f"Where were {hero} and {friend} keeping watch?",
            answer=f"{hero} and {friend} were keeping watch in {f['setting']}.",
        ),
        QAItem(
            question="What mystery did the friends notice?",
            answer=f"They noticed {f['mystery']}.",
        ),
        QAItem(
            question="What clue did they examine first?",
            answer=f"They first examined {f['clue']}.",
        ),
        QAItem(
            question="What did the friends learn by asking a question?",
            answer=f"They learned that {f['answer']}.",
        ),
        QAItem(
            question="How did the friends solve the problem sequentially?",
            answer=f"First, they {f['step_one']}. Next, they {f['step_two']}. Finally, they {f['step_three']}.",
        ),
        QAItem(
            question="What showed that the friends had changed by the end?",
            answer=f"At the end, {f['ending']}. Their courage came from listening, trusting one another, and acting together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring connection in which people support, trust, and help one another.",
        ),
        QAItem(
            question="Why is dialogue useful during a mystery?",
            answer="Dialogue lets people share observations, ask questions, and make better choices together.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the wish to learn more by noticing things and asking thoughtful questions.",
        ),
        QAItem(
            question="What does sequential mean?",
            answer="Sequential means happening in an ordered series, with one step following another.",
        ),
        QAItem(
            question="What makes someone a superhero in this storyworld?",
            answer="A superhero is someone who uses courage, care, curiosity, and teamwork to help others safely.",
        ),
    ]


ASP_RULES = r"""
clue_found.
question_asked :- clue_found.
plan_known :- question_asked.
resolved :- plan_known.
friendship_supports :- resolved.
heroic_choice :- resolved, friendship_supports.
#show resolved/0.
#show heroic_choice/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("clue_found"),
            asp.fact("question_asked"),
            asp.fact("plan_known"),
        ]
    )


def asp_program(show: str = "#show resolved/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcome() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    return [str(atom) for atom in model if atom.name == "resolved"]


def asp_verify() -> int:
    expected = ["resolved"]
    actual = asp_outcome()
    if actual == expected:
        print("OK: ASP and Python agree that the sequential rescue resolves.")
        return 0
    print(f"MISMATCH: python={expected} asp={actual}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero storyworld about sequential friendship and curiosity."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HEROES)
    friend_choices = [name for name in FRIENDS if name != hero]
    friend = args.friend or rng.choice(friend_choices)
    companion_choices = [name for name in COMPANIONS if name not in {hero, friend}]
    companion = args.companion or rng.choice(companion_choices)
    return StoryParams(hero=hero, friend=friend, companion=companion, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0.\n#show heroic_choice/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_outcome())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(SEQUENCES)):
            params = StoryParams(
                hero="Luna",
                friend="Milo",
                companion="Pip",
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
