#!/usr/bin/env python3
"""
A child-friendly superhero storyworld about bacon, a surprising twist, and reconciliation.
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
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Pip"
    city: str = "Maple City"
    food: str = "bacon"
    arc: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    hero: Entity
    friend: Entity
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HEROES = ["Luna", "Nova", "Sunny", "Comet", "Mira", "Ziggy"]
FRIENDS = ["Pip", "Tess", "Bo", "Nell", "Rafi", "Jun"]
CITIES = ["Maple City", "Brighton Borough", "Rainbow Ridge"]
FOODS = ["bacon"]

ARCS = [
    {
        "problem": "the giant breakfast banner vanished from the town square",
        "risk": "Without it, the hungry neighbors would not know where the community breakfast was happening",
        "temptation": "blame the only person holding a strip of bacon near the empty flagpole",
        "clue": "tiny grease stars led from the flagpole toward the old clock tower",
        "action": "Luna and Pip followed the grease stars instead of shouting accusations",
        "twist": "the banner had been carried away by a gust and wrapped around a clock gear, while the bacon eater was trying to catch it",
        "reconcile": "Luna apologized for suspecting the bacon eater, and everyone worked together to free the banner",
        "lesson": "a hero repairs hurt feelings as carefully as a broken machine",
        "ending": "the banner waved above the breakfast table, and the former suspect served the first plate of bacon",
        "question": "Why did Luna follow the grease stars?",
        "answer": "Luna followed the grease stars because they were a clue showing where the missing breakfast banner had gone.",
    },
    {
        "problem": "a runaway food cart rolled down Hero Hill with the town's bacon stacked inside",
        "risk": "The cart could crash into the parade and spill breakfast across the road",
        "temptation": "remove the cart's bright sign and accuse its owner of causing the trouble",
        "clue": "the cart slowed whenever someone pulled the long blue awning",
        "action": "Luna asked the owner for help and used her cape to guide the awning like a brake",
        "twist": "the owner had not pushed the cart; a loose wheel had been frightened by a loud parade drum",
        "reconcile": "The owner forgave the accusation, and Luna helped repair the wheel before the parade continued",
        "lesson": "asking before judging can turn a quarrel into teamwork",
        "ending": "the cart rested safely at the curb while warm bacon sandwiches fed every drummer",
        "question": "What made the food cart roll away?",
        "answer": "A loose wheel made the food cart roll away when a loud parade drum startled it.",
    },
    {
        "problem": "the mayor's welcome speech was covered by a cloud of smoky bacon-scented bubbles",
        "risk": "Nobody could hear the message welcoming new families to the city",
        "temptation": "remove every bubble at once and scold the young inventor nearby",
        "clue": "the bubbles popped whenever people spoke kindly to one another",
        "action": "Luna invited the inventor to explain the bubble machine and asked the crowd to use gentle voices",
        "twist": "the bubbles were meant to carry cheerful smells, but the machine had been set too high",
        "reconcile": "The inventor admitted the mistake, and Luna helped lower the setting instead of taking away the machine",
        "lesson": "a mistake is easier to fix when people feel safe telling the truth",
        "ending": "the last bubble popped above the mayor's hat, leaving the air sweet and clear",
        "question": "How did Luna help remove the bubbles?",
        "answer": "Luna helped the inventor lower the machine's setting while the crowd spoke kindly.",
    },
    {
        "problem": "a mysterious hero-shaped shadow frightened shoppers beside the bacon shop",
        "risk": "The shoppers were ready to close their stalls and run home",
        "temptation": "remove the shadow with a blast and declare victory",
        "clue": "the shadow copied every move made by a small flashlight",
        "action": "Luna lowered her shield and asked who was behind the light",
        "twist": "the shadow belonged to a shy child practicing superhero poses behind a curtain",
        "reconcile": "Luna told the child she should have asked first, then invited her to join the safety demonstration",
        "lesson": "understanding a fear can be braver than defeating it",
        "ending": "the child stood beside Luna while the bacon shop sign cast two friendly shadows",
        "question": "What made the hero-shaped shadow?",
        "answer": "A shy child made the shadow while practicing superhero poses with a flashlight.",
    },
]

OPENINGS = [
    "Morning sun flashed on the windows of",
    "At first bell, the rooftops of",
    "A warm breeze hurried through",
    "Bright kites bobbed above",
]

DIALOGUE_STARTS = [
    "Pip raised both hands and said",
    "Luna turned to the crowd and asked",
    "The worried neighbor called",
    "Pip whispered, then spoke louder",
]

DIALOGUE_LINES = [
    '"Before we blame anyone, can we follow the clue?"',
    '"If I made a mistake, I want to help fix it."',
    '"A real hero listens before using her strongest power."',
    '"We can remove the trouble without removing a friend."',
]

TWIST_REACTIONS = [
    "Everyone grew quiet as the truth came into view.",
    "Luna lowered her mask and took a careful breath.",
    "Pip blinked, then smiled with relief.",
    "The crowd leaned closer, ready to make things right.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a superhero story about bacon, removal, a twist, and reconciliation."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--city", choices=CITIES)
    parser.add_argument("--food", choices=FOODS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HEROES)
    choices = [name for name in FRIENDS if name != hero]
    friend = args.friend or rng.choice(choices)
    if hero == friend:
        raise StoryError("The superhero and friend must have different names.")
    return StoryParams(
        hero=hero,
        friend=friend,
        city=args.city or rng.choice(CITIES),
        food=args.food or "bacon",
        arc=rng.randrange(len(ARCS)),
    )


def build_world(params: StoryParams) -> World:
    hero = Entity(params.hero, "superhero")
    friend = Entity(params.friend, "friend")
    return World(params=params, hero=hero, friend=friend)


def simulate(world: World) -> None:
    params = world.params
    hero = world.hero
    friend = world.friend
    arc = ARCS[params.arc]
    rng = random.Random(params.seed)

    hero.memes["bravery"] = 1.0
    hero.memes["patience"] = 0.0
    friend.memes["trust"] = 1.0
    world.facts.update(
        {
            "city": params.city,
            "food": params.food,
            "problem": arc["problem"],
            "risk": arc["risk"],
            "clue": arc["clue"],
            "resolved": False,
        }
    )

    opening = rng.choice(OPENINGS)
    world.say(
        f"{opening} {params.city}. {hero.name}, the city's caped superhero, "
        f"was helping {friend.name} prepare a basket of crispy {params.food} "
        f"for the neighborhood breakfast."
    )
    world.say(f"Then {arc['problem']}. {arc['risk']}.")
    world.para()

    world.say(
        f"For one quick moment, {hero.name} wanted to {arc['temptation']}. "
        f"Her gloves glowed with impatient blue light."
    )
    world.say(f"{rng.choice(DIALOGUE_STARTS)} {rng.choice(DIALOGUE_LINES)}")
    world.say(
        f"{hero.name} paused. Instead of rushing, she noticed that {arc['clue']}."
    )
    hero.memes["patience"] = 1.0
    world.facts["clue_seen"] = True

    world.para()
    world.say(f"{arc['action']}.")
    world.say(
        f"{friend.name} asked, \"Should we remove the trouble first, or find out "
        f"who needs our help?\""
    )
    world.say(
        f"{hero.name} answered, \"We can do both, but we must not hurt someone "
        f"with a guess.\""
    )
    world.say(f"Then came the twist: {arc['twist']}. {rng.choice(TWIST_REACTIONS)}")
    world.facts["twist"] = arc["twist"]
    world.facts["resolved"] = True

    world.para()
    world.say(f"{arc['reconcile']}.")
    hero.memes["reconciliation"] = 1.0
    friend.memes["trust"] = 2.0
    world.facts["reconciliation"] = arc["reconcile"]
    world.say(
        f"{hero.name} learned that {arc['lesson']}. "
        f"{arc['ending']}."
    )
    world.facts["ending"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]

    prompts = [
        f"Write a superhero story in {params.city} where {params.hero} helps with bacon.",
        f"Tell a child-friendly story about removing a problem, discovering a twist, and finding reconciliation.",
        f"Create a superhero adventure in which {params.hero} listens before blaming someone.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} face?",
            answer=f"{params.hero} faced a problem when {arc['problem']}.",
        ),
        QAItem(
            question=f"What did {params.hero} first feel tempted to do?",
            answer=f"{params.hero} was tempted to {arc['temptation']}.",
        ),
        QAItem(
            question=f"What clue changed {params.hero}'s plan?",
            answer=f"The clue was that {arc['clue']}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {arc['twist']}.",
        ),
        QAItem(
            question="How did reconciliation happen?",
            answer=f"Reconciliation happened when {arc['reconcile']}.",
        ),
        QAItem(
            question=f"What did {params.hero} learn?",
            answer=f"{params.hero} learned that {arc['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave character who uses special abilities and good choices to help others.",
        ),
        QAItem(
            question="What does remove mean?",
            answer="Remove means to take something away or move it out of the way.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that reveals the situation is different from what characters expected.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the process of repairing hurt feelings and making peace after a disagreement.",
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
    for entity in [world.hero, world.friend]:
        lines.append(
            f"  {entity.name:10} ({entity.kind:9}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
#show has_twist/1.
#show has_reconciliation/1.

valid(story) :- has_twist(story), has_reconciliation(story), includes_bacon(story).
has_twist(story) :- feature(twist).
has_reconciliation(story) :- feature(reconciliation).
includes_bacon(story) :- ingredient(bacon).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("domain", "superhero_story"),
            asp.fact("ingredient", "bacon"),
            asp.fact("action", "remove"),
            asp.fact("feature", "twist"),
            asp.fact("feature", "reconciliation"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    expected = {
        ("story",): "valid",
    }
    valid = asp.atoms(model, "valid")
    if valid != [("story",)]:
        print("MISMATCH: ASP validity failed.")
        return 1
    if asp.atoms(model, "has_twist") != [("story",)]:
        print("MISMATCH: ASP twist feature failed.")
        return 1
    if asp.atoms(model, "has_reconciliation") != [("story",)]:
        print("MISMATCH: ASP reconciliation feature failed.")
        return 1
    if expected:
        for atom in expected:
            if atom not in valid:
                return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.story or "bacon" not in sample.story.lower():
            print("MISMATCH: generated story omitted bacon.")
            return 1
        if "twist" not in sample.story.lower() and "Then came the twist" not in sample.story:
            print("MISMATCH: generated story omitted its twist.")
            return 1
        if "reconcil" not in sample.story.lower() and "forgave" not in sample.story.lower():
            print("MISMATCH: generated story omitted reconciliation.")
            return 1

    print("OK: ASP twin and generated stories are consistent.")
    return 0


CURATED = [
    StoryParams(hero="Luna", friend="Pip", city="Maple City", food="bacon", arc=0, seed=101),
    StoryParams(hero="Nova", friend="Tess", city="Brighton Borough", food="bacon", arc=1, seed=202),
    StoryParams(hero="Mira", friend="Bo", city="Rainbow Ridge", food="bacon", arc=2, seed=303),
]


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
        print(asp_program("#show valid/1.\n#show has_twist/1.\n#show has_reconciliation/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print(asp.atoms(model, "valid"))
        print(asp.atoms(model, "has_twist"))
        print(asp.atoms(model, "has_reconciliation"))
        return

    if args.n < 1:
        raise StoryError("The number of requested stories must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 30, 30):
            attempts += 1
            rng = random.Random(base_seed + index)
            index += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

        if len(samples) < args.n:
            raise StoryError("Could not create enough distinct stories.")

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
