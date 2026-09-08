#!/usr/bin/env python3
"""
A tiny comedy world about a bouncy game, a mixed-up rhyme, and kindness.
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
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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
    hero: str
    friend: str
    mood: str
    seed: Optional[int] = None


HEROES = ["Luna", "Milo", "Pip", "Nora", "Tess"]
FRIENDS = ["the duck", "the goat", "the mole", "the otter", "the fox"]
MOODS = ["cheerful", "curious", "patient", "silly"]
PLACES = [
    "the sunny playground",
    "the village gym",
    "the park beside the bakery",
    "the little school yard",
]
RHYME_PAIRS = [
    ("pong", "gong"),
    ("pong", "song"),
    ("pong", "long"),
    ("pong", "wrong"),
]
MISUNDERSTANDINGS = [
    "the word 'pong' meant they should bang the table like a gong",
    "the phrase 'ping-pong' meant they should ping the ball before every bounce",
    "the rhyme made everyone think the ball had learned to sing",
    "the word 'long' made the goat search for the longest paddle in town",
]
CLUES = [
    "the tiny ball bouncing twice before it crossed the net",
    "the soft tap of the paddle and the ball's bright plop",
    "the chalk line beneath the net",
    "the scoreboard showing one neat point at a time",
]
MORALS = [
    "Kindness can untangle a funny misunderstanding without making anyone feel small.",
    "A good joke is best when everybody gets to laugh, including the person who made the mistake.",
    "Listening kindly helps friends turn a mixed-up word into a shared game.",
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, "pong", "kindness") for place in PLACES]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A comic pong story about rhyme, misunderstanding, and kindness."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--mood", choices=MOODS)
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
        hero=args.hero or rng.choice(HEROES),
        friend=args.friend or rng.choice(FRIENDS),
        mood=args.mood or rng.choice(MOODS),
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        'Write a funny child-friendly story containing the word "pong".',
        f"Tell a comedy about {hero.label} and {friend.label} solving a pong misunderstanding.",
        "Write a gentle tale with a rhyme, a silly mistake, and kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "Who played pong?",
            f"{f['hero'].label} and {f['friend'].label} played pong together.",
        ),
        QAItem(
            "What did the rhyme make the friends misunderstand?",
            f"They misunderstood the rhyme as meaning {f['misunderstanding']}.",
        ),
        QAItem(
            "How did the problem get fixed?",
            f"{f['hero'].label} kindly explained that pong meant bouncing the ball over the net, and then they practiced together.",
        ),
        QAItem(
            "What happened at the end?",
            f"They shared a cheerful pong game, and {f['friend'].label} made the winning bounce.",
        ),
        QAItem("What lesson did they learn?", f["moral"]),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is pong?",
            "Pong is a game in which players hit a ball back and forth over a net or across a table.",
        ),
        QAItem(
            "What is a rhyme?",
            "A rhyme is a word or line that sounds like another word or line, often at the end.",
        ),
        QAItem(
            "What is a misunderstanding?",
            "A misunderstanding happens when someone receives a message but thinks it means something else.",
        ),
        QAItem(
            "What is kindness?",
            "Kindness means treating others gently and helping them feel safe and welcome.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: meters={dict(entity.meters)} memes={dict(entity.memes)}"
        )
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    if params.hero == params.friend:
        raise StoryError("The hero and friend must be different characters.")
    if params.hero not in HEROES:
        raise StoryError(f"Unknown hero: {params.hero}")
    if params.friend not in FRIENDS:
        raise StoryError(f"Unknown friend: {params.friend}")
    if params.mood not in MOODS:
        raise StoryError(f"Unknown mood: {params.mood}")

    stable_seed = params.seed
    if stable_seed is None:
        stable_seed = sum(
            (index + 1) * ord(char)
            for index, char in enumerate(
                f"{params.hero}:{params.friend}:{params.mood}"
            )
        )
    rng = random.Random(stable_seed)

    world = World(place=rng.choice(PLACES))
    hero = world.add(Entity(params.hero.lower(), "child", params.hero))
    friend = world.add(Entity("friend", "animal", params.friend))
    ball = world.add(Entity("ball", "toy", "the little pong ball"))
    paddle = world.add(Entity("paddle", "toy", "a bright red paddle"))

    pair = rng.choice(RHYME_PAIRS)
    misunderstanding = rng.choice(MISUNDERSTANDINGS)
    clue = rng.choice(CLUES)
    moral = rng.choice(MORALS)

    world.facts.update(
        hero=hero,
        friend=friend,
        ball=ball,
        paddle=paddle,
        rhyme=pair,
        misunderstanding=misunderstanding,
        clue=clue,
        moral=moral,
    )

    hero.memes["excitement"] = 1
    friend.memes["confidence"] = 1
    world.say(
        f"On a {params.mood} morning at {world.place}, {hero.label} brought "
        f"{friend.label} to play pong."
    )
    world.say(
        f"They had one little ball, two paddles, and a rhyme: "
        f'"Pong, {pair[1]}, bounce along!"'
    )
    world.say(f"{friend.label.capitalize()} clapped and said, \"I know what that means!\"")
    world.say(
        f"But {friend.label} had misunderstood the rhyme. {misunderstanding.capitalize()}."
    )
    world.para()

    friend.meters["confusion"] = 1
    hero.memes["surprise"] = 1
    world.say(
        f"When {hero.label} asked for a gentle serve, {friend.label} lifted the paddle "
        f"like a drumstick and made a grand, wobbly pose."
    )
    world.say(
        f"{hero.label} giggled, but then noticed {friend.label}'s ears droop."
    )
    world.say(
        f"\"I am sorry,\" said {hero.label}. \"I laughed at the mix-up, not at you. "
        f"Let me show you pong.\""
    )
    world.say(
        f"\"Will you show me slowly?\" asked {friend.label}. "
        f"\"Slowly and kindly,\" said {hero.label}."
    )
    world.para()

    hero.memes["kindness"] = 1
    friend.memes["kindness"] = 1
    friend.meters["confusion"] = 0
    world.fired.add("kindness_explains_pong")
    world.say(
        f"{hero.label} tapped the ball once. It bounced over the net with a tiny "
        f"pong and landed near {friend.label}'s paws."
    )
    world.say(
        f"The sound matched the rhyme, but the game was clearer: hit, bounce, return."
    )
    world.say(
        f"{friend.label} watched {clue}, took a careful swing, and sent the ball back."
    )
    world.say(
        f"\"Pong!\" cried {friend.label}. \"Now I understand. It is a bounce, not a gong!\""
    )
    world.para()

    hero.memes["joy"] = 1
    friend.memes["joy"] = 1
    friend.meters["successful_bounces"] = 3
    world.fired.add("shared_game")
    world.say(
        f"They played three happy rallies. On the last one, {friend.label} made "
        f"the winning bounce, and the ball landed in the chalk circle."
    )
    world.say(
        f"{hero.label} bowed while {friend.label} bowed too, so deeply that both "
        f"nearly toppled into the paddle basket."
    )
    world.say(f"They laughed together. {moral}")
    return world


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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    import asp

    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    lines.append(asp.fact("word", "pong"))
    lines.append(asp.fact("feature", "rhyme"))
    lines.append(asp.fact("feature", "misunderstanding"))
    lines.append(asp.fact("feature", "kindness"))
    lines.append(asp.fact("game", "pong"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P) :- place(P), game(pong), feature(rhyme),
                  feature(misunderstanding), feature(kindness).
"""


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(place,) for place in PLACES}
    actual = set(asp_valid_places())
    if actual != expected:
        print("MISMATCH between ASP and Python gates.")
        print("Only in ASP:", sorted(actual - expected))
        print("Only in Python:", sorted(expected - actual))
        return 1
    for params in (
        StoryParams("Luna", "the duck", "cheerful", 1),
        StoryParams("Milo", "the goat", "patient", 2),
        StoryParams("Pip", "the otter", "silly", 3),
    ):
        sample = generate(params)
        if "pong" not in sample.story.lower():
            print("Generated story omitted pong.")
            return 1
        if len(sample.story_qa) < 4:
            print("Generated story lacks story questions.")
            return 1
    print(f"OK: ASP gate matches Python gate ({len(actual)} places); stories exercised.")
    return 0


CURATED = [
    StoryParams("Luna", "the duck", "cheerful"),
    StoryParams("Milo", "the goat", "patient"),
    StoryParams("Pip", "the otter", "silly"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2))
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
