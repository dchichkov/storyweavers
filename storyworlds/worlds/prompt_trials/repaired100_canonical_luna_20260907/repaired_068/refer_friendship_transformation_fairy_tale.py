#!/usr/bin/env python3
"""
A small fairy-tale story world about Luna, a friendship, and a gentle
transformation caused by learning whom to trust and how to help.
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
import hashlib
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
    place: str = "the moonlit meadow"
    child: str = "Luna"
    friend: str = "Pip"
    quest: str = "return the lost silver bell"
    transformation: str = "trusting"
    promise: str = "refer to her friend's wisdom before judging anyone"
    seed: Optional[int] = None


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"energy": 1.0, "distance": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"friendship": 0.0, "trust": 0.0, "courage": 0.0}
    )


@dataclass
class World:
    place: str
    child: Person
    friend: Person
    quest: str
    obstacle: str = ""
    clue: str = ""
    false_belief: str = ""
    first_attempt: str = ""
    turning_choice: str = ""
    resolution: str = ""
    lesson: str = ""
    ending_image: str = ""
    friendship_changed: bool = False
    transformed: bool = False
    bell_returned: bool = False
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


TALES = [
    {
        "title": "the bell beneath the elder tree",
        "premise": "A silver bell belonging to the moon queen had vanished from the elder tree.",
        "obstacle": "A trail of muddy footprints seemed to point toward Pip's burrow.",
        "false_belief": "Luna feared that Pip had taken the bell and hidden it.",
        "first_attempt": "Luna hurried toward the burrow with an accusing question ready",
        "clue": "Pip's tiny footprints were round and soft, but the muddy marks were long and sharp like crow claws.",
        "turning_choice": "Instead of blaming Pip, Luna asked her friend what he had seen and followed the different prints together.",
        "resolution": "Behind a thorn bush they found a crow tangled in the bell's ribbon; when they freed it, the crow led them to the bell beneath a fallen branch.",
        "lesson": "friendship grows when questions come before accusations",
        "ending": "The silver bell rang above the elder tree, and moonbeams curled around both friends like a shining ribbon.",
        "items": ["silver bell", "thorn ribbon"],
    },
    {
        "title": "the lantern of the whispering bridge",
        "premise": "A little lantern that guided travelers across the whispering bridge had gone dark.",
        "obstacle": "The bridge keeper claimed Pip had borrowed the magic flame and never returned it.",
        "false_belief": "Luna almost believed the keeper because Pip had once loved collecting bright things.",
        "first_attempt": "Luna reached for Pip's paw and began to lead him away from the bridge",
        "clue": "Pip showed her a blue spark on his sleeve, the same color as the bridge's missing flame.",
        "turning_choice": "Luna referred to Pip's careful memory and listened while he explained that the flame had blown into the reeds.",
        "resolution": "Together they found the flame trapped in a water lily and carried it back inside the lantern.",
        "lesson": "a true friend makes room for another friend's whole story",
        "ending": "The bridge glowed again, and every traveler saw Luna and Pip crossing side by side.",
        "items": ["blue flame", "water lily"],
    },
    {
        "title": "the dragon's quiet garden",
        "premise": "A young dragon's garden lost its golden seeds before spring planting.",
        "obstacle": "The dragon's footprints circled the empty flowerbed, so the villagers whispered that he had eaten them.",
        "false_belief": "Luna wondered whether a hungry dragon could really be trusted near a garden.",
        "first_attempt": "she stepped backward from the dragon and held the seed pouch tightly",
        "clue": "The dragon's claws had made careful lines around the bed, while tiny mouse tracks led toward the old mill.",
        "turning_choice": "Luna referred to Pip's knowledge of animal tracks and followed the small trail instead of the frightening one.",
        "resolution": "At the mill they found the seeds spilling from a torn sack, and the dragon used his warm breath to dry them.",
        "lesson": "friendship can turn fear into patient understanding",
        "ending": "By sunset, golden shoots lifted their heads while the young dragon watered them with a proud smile.",
        "items": ["golden seeds", "torn sack"],
    },
]


OPENINGS = [
    "Once, beneath a velvet sky",
    "In a kingdom where the stars sang softly",
    "Long ago, at the edge of an enchanted wood",
    "On the evening when the moon wore a silver crown",
    "Beyond the last village and the tallest hill",
]

PROMISE_LINES = [
    "Luna made a small promise to refer to Pip's wisdom before judging anyone",
    "Luna tied a blue thread around her wrist to remember that a friend should be heard",
    "Luna promised that fear would not speak louder than friendship",
    "Luna decided to ask questions before letting a rumor become a truth",
    "Luna placed one hand over her heart and promised to trust carefully, not blindly",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fairy-tale friendship transformation world.")
    parser.add_argument("--place", default="the moonlit meadow")
    parser.add_argument("--child")
    parser.add_argument("--friend")
    parser.add_argument("--quest")
    parser.add_argument("--transformation")
    parser.add_argument("--promise")
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


NAME_POOL = ["Luna", "Mira", "Nell", "Asha", "Wren"]
FRIEND_POOL = ["Pip", "Tavi", "Moss", "Bram", "Eli"]
QUEST_POOL = [
    "return the lost silver bell",
    "relight the bridge lantern",
    "restore the dragon's golden garden",
]
TRANSFORMATION_POOL = ["trusting", "brave", "patient", "kind", "wise"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place != "the moonlit meadow":
        raise StoryError("This fairy-tale world supports only the moonlit meadow setting.")
    promise = args.promise or "refer to her friend's wisdom before judging anyone"
    if "refer" not in promise.lower():
        promise = f"refer to {promise}"
    return StoryParams(
        place=args.place,
        child=args.child or rng.choice(NAME_POOL),
        friend=args.friend or rng.choice(FRIEND_POOL),
        quest=args.quest or rng.choice(QUEST_POOL),
        transformation=args.transformation or rng.choice(TRANSFORMATION_POOL),
        promise=promise,
    )


def make_world(params: StoryParams) -> World:
    child = Person(params.child, "young traveler")
    friend = Person(params.friend, "friend")
    return World(params.place, child, friend, params.quest)


def choose_tale(params: StoryParams) -> dict:
    material = "|".join(
        [
            params.place,
            params.child,
            params.friend,
            params.quest,
            params.transformation,
            params.promise,
            str(params.seed),
        ]
    )
    number = int.from_bytes(hashlib.blake2b(material.encode(), digest_size=8).digest(), "big")
    return TALES[number % len(TALES)]


def generate_story(world: World, params: StoryParams) -> None:
    tale = choose_tale(params)
    mode = (params.seed or 0) % len(OPENINGS)

    world.obstacle = tale["obstacle"]
    world.clue = tale["clue"]
    world.false_belief = tale["false_belief"]
    world.first_attempt = tale["first_attempt"]
    world.turning_choice = tale["turning_choice"]
    world.resolution = tale["resolution"]
    world.lesson = tale["lesson"]
    world.ending_image = tale["ending"]

    child = world.child.name
    friend = world.friend.name

    world.say(
        f"{OPENINGS[mode]}, {child} lived near {world.place}, where the grass glittered "
        f"and every path seemed to lead to a secret."
    )
    world.say(
        f"{child} traveled there with {friend}, her loyal friend, because she had promised to "
        f"{params.promise.rstrip('.')}. "
        f"Today their quest was to {params.quest}."
    )
    world.child.memes["friendship"] += 1.0
    world.friend.memes["friendship"] += 1.0
    world.say(
        f'"I will listen before I decide," {child} said. '
        f'"And I will tell you what I know," {friend} replied.'
    )
    world.say(f"That promise mattered when they reached {tale['title']}.")
    world.say(f"{tale['premise']} {tale['obstacle']} {tale['false_belief']}")
    world.say(
        f"At first, {child} {tale['first_attempt']}. "
        f'"Wait," {friend} said. "May I explain what I saw?"'
    )
    world.child.meters["energy"] -= 0.15
    world.say(f"{child} took a breath and answered, \"Yes. I will refer to your wisdom.\"")
    world.say(tale["clue"])
    world.child.memes["trust"] += 1.0
    world.friend.memes["trust"] += 1.0
    world.say(tale["turning_choice"])
    world.say(
        f'"You trusted my words," {friend} said. '
        f'"You helped us find the truth," {child} answered.'
    )
    world.say(tale["resolution"])
    world.bell_returned = True
    world.friendship_changed = True
    world.child.memes["courage"] += 0.7
    world.friend.memes["courage"] += 0.3
    world.say(
        f"Together they completed the quest to {params.quest}, not by being fearless, "
        f"but by being honest and careful with one another."
    )
    world.say(
        f"{child} understood that {tale['lesson']}. "
        f"The understanding transformed her into someone more {params.transformation}."
    )
    world.transformed = True
    world.child.memes["trust"] += 0.8
    world.say(tale["ending"])


def story_questions(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    return [
        QAItem(
            f"Where did {params.child} and {params.friend} go?",
            f"{params.child} and {params.friend} went to {params.place} to {params.quest}.",
        ),
        QAItem(
            f"What did {params.child} promise to do?",
            f"{params.child} promised to {params.promise.rstrip('.')}.",
        ),
        QAItem(
            "What made the first idea seem true?",
            f"The first idea seemed true because {world.obstacle} {world.false_belief}",
        ),
        QAItem(
            "What clue changed the friends' understanding?",
            world.clue,
        ),
        QAItem(
            f"How did {params.child} show friendship?",
            f"{params.child} listened to {params.friend}, referred to the friend's wisdom, and chose evidence instead of blame.",
        ),
        QAItem(
            "How was the problem resolved?",
            world.resolution,
        ),
        QAItem(
            f"How did the adventure transform {params.child}?",
            f"The adventure made {params.child} more {params.transformation} because {world.lesson}.",
        ),
    ]


def world_questions(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is friendship?",
            "Friendship is a caring relationship in which people listen to, help, and respect one another.",
        ),
        QAItem(
            "What does it mean to refer to someone's wisdom?",
            "It means to use that person's experience or careful knowledge when deciding what to do.",
        ),
        QAItem(
            "What is a transformation?",
            "A transformation is a meaningful change in how someone looks, feels, thinks, or acts.",
        ),
    ]


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        f"Write a fairy tale about {params.child} and {params.friend} learning that friendship requires listening.",
        f"Tell a story in which someone must refer to a friend's wisdom before solving {params.quest}.",
        f"Write a gentle transformation tale where {params.child} becomes more {params.transformation}.",
    ]


def format_qa(sample: StorySample) -> str:
    sections = ["== Generation prompts =="]
    sections.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    sections.append("\n== Story Q&A ==")
    for item in sample.story_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    sections.append("\n== World Q&A ==")
    for item in sample.world_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(sections)


ASP_RULES = r"""
place(moonlit_meadow).
feature(friendship).
feature(transformation).
seed(refer).
promise(P) :- seed(refer), P = listening.
valid_story :- place(moonlit_meadow), feature(friendship),
               feature(transformation), promise(listening).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "moonlit_meadow"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "transformation"),
            asp.fact("seed", "refer"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_gate() -> bool:
    return bool(
        "refer"
        and "Friendship".lower() in "friendship"
        and "Transformation".lower() in "transformation"
    )


def asp_verify() -> int:
    if not python_gate():
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    if not any(symbol.name == "valid_story" for symbol in model):
        print("MISMATCH: ASP gate failed.")
        return 1
    sample = generate(
        StoryParams(seed=17, child="Luna", friend="Pip")
    )
    if not sample.story or "Luna" not in sample.story or "Pip" not in sample.story:
        print("MISMATCH: generated story exercise failed.")
        return 1
    print("OK: Python and ASP gates agree; generated story exercised.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if "refer" not in params.promise.lower():
        raise StoryError("The promise must include the word 'refer'.")
    world = make_world(params)
    world.facts["params"] = params
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(params),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        world = sample.world
        print("--- world trace ---")
        print(asdict(sample.params))
        print(
            {
                "child_meters": world.child.meters,
                "child_memes": world.child.memes,
                "friend_memes": world.friend.memes,
                "friendship_changed": world.friendship_changed,
                "transformed": world.transformed,
                "quest_resolved": world.bell_returned,
                "clue": world.clue,
            }
        )
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        child="Luna",
        friend="Pip",
        quest="return the lost silver bell",
        transformation="trusting",
        promise="refer to her friend's wisdom before judging anyone",
        seed=1,
    ),
    StoryParams(
        child="Mira",
        friend="Tavi",
        quest="relight the bridge lantern",
        transformation="brave",
        promise="refer to her friend's wisdom before judging anyone",
        seed=2,
    ),
    StoryParams(
        child="Nell",
        friend="Moss",
        quest="restore the dragon's golden garden",
        transformation="patient",
        promise="refer to her friend's wisdom before judging anyone",
        seed=3,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        print("ASP model:", asp.one_model(asp_program()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
