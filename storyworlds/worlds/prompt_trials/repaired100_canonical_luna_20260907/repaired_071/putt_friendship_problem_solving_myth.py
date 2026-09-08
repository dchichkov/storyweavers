#!/usr/bin/env python3
"""
Standalone storyworld: a gentle myth about a putt, friendship, and solving a
small problem together.

A young player must guide a putt across a moonlit meadow to awaken a sleeping
star. The first shot fails, but careful observation and a friend's idea turn
the problem into a shared victory.
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
class StoryParams:
    meadow: str
    hero: str
    friend: str
    ball: str
    seed: Optional[int] = None


MEADOWS = {
    "moon meadow": {"slope": 0.0, "dew": 0.4, "magic": "silver"},
    "whispering green": {"slope": 0.2, "dew": 0.2, "magic": "blue"},
    "sunset hollow": {"slope": -0.1, "dew": 0.3, "magic": "golden"},
    "star garden": {"slope": 0.1, "dew": 0.1, "magic": "violet"},
}
HEROES = ["Luna", "Mira", "Tavi", "Niko", "Suri"]
FRIENDS = ["Pip", "Orin", "Kato", "Bela", "Rin"]
BALLS = ["pearl ball", "acorn ball", "moon ball", "glowing ball"]

MYTHS = [
    {
        "name": "the sleeping star",
        "problem": "the little star at the end of the path would not wake",
        "obstacle": "a ring of soft moss bent the path away from the star",
        "first": "Luna gave the ball a brave putt, but it rolled wide and stopped beside a fern",
        "clue": "Pip noticed that the dew made one side of the grass shine more brightly",
        "method": "aimed a little left, where the bright dew showed the smoothest ground",
        "cause": "the moss was acting like a tiny wall and turning every straight shot aside",
        "repair": "pressed a safe lane through the moss with a fallen twig",
        "lesson": "A problem becomes smaller when friends study it together",
        "ending": "the star blinked awake and painted a silver road across the meadow",
    },
    {
        "name": "the moon gate",
        "problem": "the old moon gate would open only when a ball reached its round stone",
        "obstacle": "three pebbles hid in the grass like sleeping beetles",
        "first": "the first putt struck a pebble and hopped into a patch of clover",
        "clue": "Orin saw that each pebble made a dark spot beneath the low moon",
        "method": "rolled the ball between the dark spots instead of aiming straight at the gate",
        "cause": "the hidden pebbles were nudging the ball away from its goal",
        "repair": "moved the loose pebbles to the edge of the path",
        "lesson": "Good solving means noticing what the first try teaches",
        "ending": "the moon gate opened, and moths flew through it like tiny lanterns",
    },
    {
        "name": "the river of light",
        "problem": "a ribbon of light had gone quiet beside the village hill",
        "obstacle": "a shallow groove made the ball lose its speed before it reached the light",
        "first": "the ball began well, then slowed and rested just short of the shining ribbon",
        "clue": "Bela found a trail of dry leaves that marked firmer ground",
        "method": "sent the putt along the leaf trail with a gentle, steady stroke",
        "cause": "the groove was stealing the ball's speed, while the leaf trail crossed smooth earth",
        "repair": "lined the trail with small white stones so others could see it",
        "lesson": "A friend's different view can reveal the road you missed",
        "ending": "the river of light sang again and reflected every smiling face",
    },
]


@dataclass
class World:
    params: StoryParams
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


OPENINGS = [
    "Long ago, when stars still listened to children, a small putting green appeared in a quiet meadow.",
    "In the first age of moonlight, every hill kept a secret game for a brave child and a loyal friend.",
    "The old people said that the meadow's stones remembered every kind deed, especially one made with a putt.",
    "One evening, the sky lost a little light, and two friends followed the dim glow into the grass.",
]

MID_LINES = [
    "They did not quarrel for long, because a problem was easier to face when both pairs of eyes were looking.",
    "The failed shot became a teacher instead of a defeat.",
    "The meadow waited quietly, as if the ancient earth wished to hear their plan.",
    "Together they treated the mistake like a riddle with an answer hidden inside it.",
]

ENDING_LINES = [
    "From that day onward, the children called the place the Green of Two Minds.",
    "The old stones remembered their friendship longer than they remembered the shot.",
    "Whenever someone faced a difficult path, the meadow whispered their lesson through the grass.",
]


def stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.meadow, params.hero, params.friend, params.ball))
    return sum((i + 1) * ord(c) for i, c in enumerate(text))


def build_world(params: StoryParams) -> World:
    rng = random.Random(stable_seed(params) ^ 0x71A17)
    myth = rng.choice(MYTHS)
    meadow_data = MEADOWS[params.meadow]
    world = World(params)
    hero = world.add(Entity("hero", "character", params.hero))
    friend = world.add(Entity("friend", "character", params.friend))
    ball = world.add(Entity("ball", "object", params.ball))
    goal = world.add(Entity("goal", "object", myth["name"]))
    ground = world.add(Entity("ground", "place", params.meadow))

    hero.memes.update({"hope": 1.0, "patience": 0.0, "friendship": 0.0})
    friend.memes.update({"care": 1.0, "friendship": 0.0})
    ball.meters.update({"distance": 1.0, "speed": 1.0, "accuracy": 0.5})
    ground.meters.update({"slope": meadow_data["slope"], "dew": meadow_data["dew"]})

    world.facts.update(
        hero=hero,
        friend=friend,
        ball=ball,
        goal=goal,
        ground=ground,
        myth=myth,
        meadow=params.meadow,
        obstacle=myth["obstacle"],
        cause=myth["cause"],
        method=myth["method"],
        lesson=myth["lesson"],
    )

    world.say(rng.choice(OPENINGS))
    world.say(
        f"{hero.label} carried the {ball.label} into the {params.meadow}, while "
        f"{friend.label} walked beside {hero.label} with a small wooden club."
    )
    world.say(
        f"At the far end of the grass, {myth['problem']}. The elders had promised "
        f"that a careful putt could bring the lost wonder back."
    )

    world.para()
    world.say(
        f"Before the moon reached its highest place, {myth['obstacle']}."
    )
    world.say(
        f'"I will try the first shot," said {hero.label}. "If I miss, we will learn why."'
    )
    world.say(
        f'"And if you miss, I will look from another side," {friend.label} promised.'
    )
    world.say(myth["first"])
    ball.meters["accuracy"] = 0.2
    hero.memes["hope"] -= 0.2
    world.say(rng.choice(MID_LINES))

    world.para()
    world.say(f"{friend.label} knelt without touching the goal. {myth['clue']}.")
    world.say(
        f'"The ground is giving us a hint," {friend.label} said. '
        f'"Let us change the path, not blame the ball."'
    )
    world.say(
        f'{hero.label} smiled. "Then we can solve this together."'
    )
    world.say(f"They studied the meadow and {myth['method']}.")
    hero.memes["patience"] += 1.0
    friend.memes["friendship"] += 1.0
    ball.meters["accuracy"] = 1.0
    world.facts["clue_found"] = True

    world.para()
    world.say(f"The second stroke was soft and true. {myth['cause'].capitalize()}.")
    world.say(f"Together, the friends {myth['repair']}.")
    world.facts["resolved"] = True
    hero.memes["friendship"] += 1.0
    hero.memes["hope"] += 1.0
    friend.memes["friendship"] += 1.0
    world.say(
        f"The {ball.label} reached the ancient place, and {myth['ending']}."
    )
    world.say(
        f'{hero.label} thanked {friend.label}. "Your eyes found the answer my first shot missed."'
    )
    world.say(
        f'{friend.label} replied, "Your courage made the first try. Our friendship made the next one wiser."'
    )
    world.say(f'They carried the club home, remembering: "{myth["lesson"]}."')
    world.say(rng.choice(ENDING_LINES))
    return world


def generation_prompts(world: World) -> list[str]:
    myth = world.facts["myth"]
    return [
        f"Write a child-friendly myth about {world.facts['hero'].label} making a putt in the {world.params.meadow}.",
        f"Tell a friendship story where {world.facts['hero'].label} and {world.facts['friend'].label} solve this problem: {myth['problem']}.",
        f"Write a myth in which a failed putt reveals that {myth['obstacle']}, and the friends succeed by working together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    myth = world.facts["myth"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        QAItem(
            question=f"Who made the putt in the {world.params.meadow}?",
            answer=f"{hero.label} made the putt while {friend.label} helped observe the ground and plan a better path.",
        ),
        QAItem(
            question=f"What problem did {hero.label} and {friend.label} need to solve?",
            answer=f"They needed to solve the problem that {myth['problem']}. The first putt failed because {myth['cause']}.",
        ),
        QAItem(
            question=f"What clue helped the friends improve their putt?",
            answer=f"{friend.label} noticed that {myth['clue']}. That observation showed them how to change the ball's path.",
        ),
        QAItem(
            question="How did friendship help solve the problem?",
            answer=f"{hero.label} made the brave first attempt, while {friend.label} offered a different view. Together they {myth['method']}.",
        ),
        QAItem(
            question="What lesson did the myth teach?",
            answer=f"The myth taught that {myth['lesson']}. The friends succeeded because they listened, tested an idea, and tried again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a putt?",
            answer="A putt is a gentle stroke that rolls a ball toward a nearby target.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond in which people help, listen to, and encourage one another.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means studying a difficulty, thinking of possible answers, testing one, and learning from the result.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old-style story that may use wonders or magical events to share a meaningful lesson.",
        ),
    ]


def validate_params(params: StoryParams) -> None:
    if params.meadow not in MEADOWS:
        raise StoryError(f"Unknown meadow: {params.meadow}")
    if params.hero not in HEROES:
        raise StoryError(f"Unknown hero: {params.hero}")
    if params.friend not in FRIENDS:
        raise StoryError(f"Unknown friend: {params.friend}")
    if params.hero == params.friend:
        raise StoryError("The hero and friend must have different names.")
    if params.ball not in BALLS:
        raise StoryError(f"Unknown ball: {params.ball}")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    meadow = args.meadow or rng.choice(list(MEADOWS))
    hero = args.hero or rng.choice(HEROES)
    friend = args.friend or rng.choice([name for name in FRIENDS if name != hero])
    ball = args.ball or rng.choice(BALLS)
    params = StoryParams(meadow=meadow, hero=hero, friend=friend, ball=ball, seed=args.seed)
    validate_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    lines.append(f"  resolved={world.facts.get('resolved', False)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
valid_meadow(M) :- meadow(M).
valid_story(M) :- valid_meadow(M).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("meadow", meadow) for meadow in MEADOWS)


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> set[tuple[str]]:
    return {(meadow,) for meadow in MEADOWS}


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "valid_story"))
    expected = valid_combos()
    if actual != expected:
        print("MISMATCH between ASP and Python gates")
        print("only in ASP:", sorted(actual - expected))
        print("only in Python:", sorted(expected - actual))
        return 1
    for index, meadow in enumerate(MEADOWS):
        params = StoryParams(meadow, HEROES[index % len(HEROES)], FRIENDS[index % len(FRIENDS)], BALLS[index % len(BALLS)], index)
        sample = generate(params)
        if not sample.story or "putt" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP/Python parity and {len(MEADOWS)} generated stories verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A mythic putt storyworld about friendship and problem solving.")
    parser.add_argument("--meadow", choices=list(MEADOWS))
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--ball", choices=BALLS)
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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("Compatible meadows:")
        for meadow in MEADOWS:
            print(f"  {meadow}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, meadow in enumerate(MEADOWS):
            hero = HEROES[index % len(HEROES)]
            friend = FRIENDS[index % len(FRIENDS)]
            if friend == hero:
                friend = FRIENDS[(index + 1) % len(FRIENDS)]
            params = StoryParams(
                meadow=meadow,
                hero=hero,
                friend=friend,
                ball=BALLS[index % len(BALLS)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(max(1, args.n)):
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = base_seed + index
            samples.append(generate(resolve_params(local_args, random.Random(base_seed + index))))

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
