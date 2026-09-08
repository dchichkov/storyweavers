#!/usr/bin/env python3
"""
A small mystery storyworld about a hidden mechanism, friendship, and a careful
choice that reveals a surprising twist.
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
    friend: str = "Mira"
    place: str = "the old clock tower"
    object_name: str = "the brass puzzle box"
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
    object_entity: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HERO_NAMES = ["Luna", "Theo", "Nell", "Ivo", "Ada", "Pip"]
FRIEND_NAMES = ["Mira", "Jonah", "Bea", "Sol", "Tess", "Oren"]
PLACES = [
    "the old clock tower",
    "the little museum",
    "the moonlit library",
    "the village greenhouse",
]
OBJECTS = [
    "the brass puzzle box",
    "the silver music case",
    "the wooden map cabinet",
    "the locked lantern",
]

ARCS = [
    {
        "premise": "A soft click came from a dusty cabinet just after sunset",
        "problem": "the cabinet's hidden mechanism seemed ready to spring shut",
        "risk": "A hurried pull could snap its tiny gears and lose whatever was inside",
        "temptation": "force the bright handle before anyone else could solve the mystery",
        "clue": "three scratches beside the lock matched the rhythm of the tower bell",
        "action": "They counted the bellbeats, turned the wheels slowly, and marked each safe notch with chalk",
        "twist": "the cabinet did not hold treasure; it held a bundle of letters from children who had once explored the tower",
        "sharing": "They read the letters together and placed them in a new memory book for visitors",
        "lesson": "careful friendship can protect a secret long enough for its true meaning to appear",
        "ending": "the cabinet's little gears ticked peacefully while the new memory book rested beneath the moon",
        "question": "Why did Luna and Mira avoid forcing the cabinet open?",
        "answer": "They avoided forcing it because the hidden mechanism might break and destroy what was inside.",
    },
    {
        "premise": "A lantern blinked inside the locked music case",
        "problem": "the case had begun rolling toward the museum's steep display ramp",
        "risk": "If it fell, its delicate mechanism could scatter across the floor",
        "temptation": "race after it alone and claim to be the first detective",
        "clue": "the lantern blinked whenever two nearby magnets pointed north",
        "action": "They placed the magnets on opposite sides and guided the case between them",
        "twist": "the blinking was not a warning from a ghost; it was a tiny signal made by a lost firefly",
        "sharing": "They opened a safe window and let the firefly join the garden outside",
        "lesson": "a mystery becomes kinder when friends investigate before they imagine danger",
        "ending": "the empty case gleamed beside the open window as the firefly blinked over the garden",
        "question": "What caused the music case to blink?",
        "answer": "A lost firefly inside the case caused the small light to blink.",
    },
    {
        "premise": "A folded map appeared beneath a loose floorboard",
        "problem": "its ink pointed toward a mechanism hidden under the greenhouse fountain",
        "risk": "Turning the wrong stone could send water across the seed trays",
        "temptation": "twist the largest stone quickly and search for a secret prize",
        "clue": "the map showed leaves beside the stones, not arrows",
        "action": "They matched each leaf shape to a stone and turned only the gentle, green-marked pieces",
        "twist": "the mechanism opened a rain channel designed by the gardener to water every plant at once",
        "sharing": "They cleared the channel and shared the ripe strawberries with the gardener",
        "lesson": "a cautionary clue is a gift when friends take time to understand it",
        "ending": "water whispered through every bed while strawberry leaves shone like tiny flags",
        "question": "How did the friends know which stones to turn?",
        "answer": "They matched the leaf shapes on the map to the green-marked stones.",
    },
    {
        "premise": "The silver music case hummed whenever Luna and her friend whispered nearby",
        "problem": "a spring inside it was tightening with every sound",
        "risk": "Too much noise could make the mechanism burst open",
        "temptation": "shout a command and see what the mysterious case would do",
        "clue": "the humming softened whenever both friends held their breath",
        "action": "They moved slowly, covered the case with a wool scarf, and used hand signals",
        "twist": "the spring was tuning a little music strip for the museum's night concert",
        "sharing": "They invited the whole village to listen when the tune finally played",
        "lesson": "quiet attention can solve what loud excitement only tangles",
        "ending": "the finished melody floated through the hall, and every listener heard a different happy part",
        "question": "Why did Luna and her friend use hand signals?",
        "answer": "They used hand signals because noise made the spring tighten and could damage the mechanism.",
    },
    {
        "premise": "A mysterious key was found beneath the library's oldest rug",
        "problem": "it fit the puzzle box, but the box had a warning etched around its lock",
        "risk": "An impatient turn could release a puff of dusty powder",
        "temptation": "turn the key at once before the librarian returned",
        "clue": "the warning showed a star, a leaf, and a cup in that order",
        "action": "They searched the room for those three pictures and arranged them beside the box",
        "twist": "the powder was only cinnamon, placed there by a baker who had hidden a recipe",
        "sharing": "They copied the recipe and baked the first batch for the whole reading club",
        "lesson": "friends who heed a warning can discover a surprise without making a mess",
        "ending": "cinnamon warmed the library air while the old box stood open and harmless",
        "question": "What was hidden inside the puzzle box?",
        "answer": "A baker's recipe, protected by a harmless puff of cinnamon, was hidden inside it.",
    },
]


OPENINGS = [
    "Rain tapped the windows like tiny detective fingers",
    "The evening fog curled around the steps",
    "A pale moon shone through the dusty glass",
    "The hallway lamps flickered as the doors clicked shut",
    "Wind brushed the roof while the building settled",
    "The last visitors had gone, leaving only soft footsteps",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a child-friendly mystery about a mechanism and friendship."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--friend", choices=FRIEND_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
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
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([name for name in FRIEND_NAMES if name != hero])
    place = args.place or rng.choice(PLACES)
    object_name = args.object_name or rng.choice(OBJECTS)
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(
        hero=hero,
        friend=friend,
        place=place,
        object_name=object_name,
        arc=rng.randrange(len(ARCS)),
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "hero"),
        friend=Entity(params.friend, "friend"),
        object_entity=Entity(params.object_name, "mysterious object"),
    )


def simulate(world: World) -> None:
    params = world.params
    arc = ARCS[params.arc]
    rng = random.Random(params.seed)
    hero = world.hero
    friend = world.friend

    hero.memes["curiosity"] = 1.0
    hero.memes["impatience"] = 1.0
    friend.memes["caution"] = 1.0
    world.facts.update(
        {
            "place": params.place,
            "object": params.object_name,
            "problem": arc["problem"],
            "risk": arc["risk"],
            "clue": arc["clue"],
            "resolved": False,
        }
    )

    opening = rng.choice(OPENINGS)
    world.say(
        f"{opening}. In {params.place}, {hero.name} and {friend.name} were the last "
        f"children to leave when they heard a strange sound near {params.object_name}."
    )
    world.say(f"{arc['premise']}. The sound seemed to come from a small mechanism inside it.")
    world.para()

    world.say(f"Then {arc['problem']}. {arc['risk']}.")
    world.say(
        f"{hero.name} reached toward it, but {friend.name} gently caught their sleeve."
    )
    world.say(
        f'"Wait," said {friend.name}. "A mystery is not worth solving if we break the thing hiding it."'
    )
    world.say(
        f'"You are right," said {hero.name}. "Let us look for a clue before we touch the mechanism."'
    )
    world.say(f"For a moment, {hero.name} wanted to {arc['temptation']}.")
    hero.memes["impatience"] = 0.0
    hero.memes["trust"] = 1.0
    world.facts["choice"] = "pause and investigate with a friend"
    world.para()

    world.say(f"They searched together. Soon they noticed that {arc['clue']}.")
    world.say(
        f'"The clue is telling us how to be careful," said {friend.name}. '
        f'"Then we should follow it exactly," said {hero.name}.'
    )
    world.say(f"{arc['action']}.")
    world.say(f"At last, the mechanism clicked open. Here was the twist: {arc['twist']}.")
    world.facts["solution"] = arc["action"]
    world.facts["twist"] = arc["twist"]
    world.facts["resolved"] = True
    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    world.para()

    world.say(f"{arc['sharing']}.")
    world.say(
        f"{hero.name} smiled. " 
        f'"The mystery was not asking us to be brave by rushing," they said. '
        f'"It was asking us to be wise together."'
    )
    world.say(f"{arc['lesson'].capitalize()}.")
    world.say(f"{arc['ending']}.")
    world.facts["ending_image"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]
    prompts = [
        f"Write a child-friendly mystery about {params.hero} and {params.friend} investigating a hidden mechanism.",
        f"Tell a cautionary friendship story set in {params.place}, with a surprising twist.",
        f"Make the clue matter when {params.hero} and {params.friend} examine {params.object_name}.",
    ]
    story_qa = [
        QAItem(
            question=f"What dangerous shortcut did {params.hero} consider?",
            answer=f"{params.hero} considered trying to {arc['temptation']}.",
        ),
        QAItem(
            question=f"What clue did {params.hero} and {params.friend} discover?",
            answer=f"They discovered that {arc['clue']}.",
        ),
        QAItem(
            question="Why did the friends move carefully?",
            answer=f"They moved carefully because {arc['risk']}.",
        ),
        QAItem(
            question="What was the twist in the mystery?",
            answer=f"The twist was that {arc['twist']}.",
        ),
        QAItem(
            question=f"What did {params.hero} learn from {params.friend}?",
            answer=f"{params.hero} learned that {arc['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, open, close, or happen.",
        ),
        QAItem(
            question="Why should someone heed a cautionary clue?",
            answer="A cautionary clue can warn someone about danger and help them act safely.",
        ),
        QAItem(
            question="What is a twist in a mystery?",
            answer="A twist is a surprising discovery that changes what the characters thought was happening.",
        ),
        QAItem(
            question="How can friendship help solve a mystery?",
            answer="Friendship helps because trusted companions can share observations, slow down risky choices, and think together.",
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
    for entity in [world.hero, world.friend, world.object_entity]:
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.name:24} ({entity.kind:16}) meters={meters} memes={memes}"
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
#show friendship/1.
#show cautionary/1.
#show twist/1.
valid(story) :- mechanism(story), friendship(story), cautionary(story), twist(story).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("domain", "mystery"),
            asp.fact("mechanism", "story"),
            asp.fact("friendship", "story"),
            asp.fact("cautionary", "story"),
            asp.fact("twist", "story"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    expected = {
        ("story",),
    }
    actual = set(asp.atoms(model, "valid"))
    if actual != expected:
        print(f"MISMATCH: expected valid atoms {sorted(expected)}, got {sorted(actual)}.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated story was incomplete.")
            return 1
        if "mechanism" not in sample.story:
            print("MISMATCH: generated story omitted the mechanism.")
            return 1
    print("OK: ASP twin and generated stories are consistent.")
    return 0


CURATED = [
    StoryParams(
        hero="Luna",
        friend="Mira",
        place="the old clock tower",
        object_name="the brass puzzle box",
        arc=0,
        seed=101,
    ),
    StoryParams(
        hero="Theo",
        friend="Bea",
        place="the little museum",
        object_name="the silver music case",
        arc=1,
        seed=202,
    ),
    StoryParams(
        hero="Ada",
        friend="Sol",
        place="the village greenhouse",
        object_name="the wooden map cabinet",
        arc=2,
        seed=303,
    ),
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
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 30, 30):
            rng = random.Random(base_seed + attempt)
            attempt += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
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
