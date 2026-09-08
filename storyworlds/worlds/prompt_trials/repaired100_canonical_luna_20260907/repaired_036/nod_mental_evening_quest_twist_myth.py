#!/usr/bin/env python3
"""
A standalone mythic story world about Luna's evening quest.

Luna must carry a moon-seed through the forest, but the true obstacle is
mental: she must stop fearing every shadow and learn to listen for the quiet
truth beneath them. A nod from an old owl opens the quest's twist.
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


HERO_NAMES = ["Luna", "Mira", "Sela", "Nia", "Orin"]
GUIDES = ["the old owl", "the silver fox", "the hill keeper", "the river spirit"]
PLACES = ["the whispering wood", "the blue hill", "the sleeping valley", "the moonlit marsh"]
MOON_OBJECTS = ["a moon-seed", "a fallen star", "a pearl of dawn", "a silver acorn"]
FEARS = ["a huge shadow", "a whisper behind the trees", "a face in the mist", "a growl beneath the stones"]
TRAITS = ["curious", "brave", "patient", "kind", "thoughtful"]

QUESTS = {
    "a moon-seed": {
        "mission": "carry the moon-seed to the dark hill before midnight",
        "gift": "a silver flower would bloom beneath the moon",
        "ending": "the hill opened a small silver flower to the stars",
    },
    "a fallen star": {
        "mission": "return the fallen star to the highest stone before midnight",
        "gift": "the valley would remember how to shine",
        "ending": "the star rose from the stone and lit every sleeping path",
    },
    "a pearl of dawn": {
        "mission": "place the pearl of dawn inside the empty well before midnight",
        "gift": "morning would find the valley warm and clear",
        "ending": "the well filled with gentle gold before the sun appeared",
    },
    "a silver acorn": {
        "mission": "plant the silver acorn beside the oldest tree before midnight",
        "gift": "a tree of moonlight would guard the forest",
        "ending": "a young tree lifted silver leaves toward the night",
    },
}

TWISTS = [
    {
        "shadow": "The shadow stretched across the path like a giant with reaching arms.",
        "truth": "the giant shadow belonged to a bent tree, and its reaching arms were only branches",
        "choice": "she touched the tree's rough bark instead of fleeing",
    },
    {
        "shadow": "A voice whispered her name from the mist.",
        "truth": "the voice was the river repeating her name between smooth stones",
        "choice": "she followed the water's steady rhythm instead of the frightening echo",
    },
    {
        "shadow": "Two bright eyes glowed beneath the stones.",
        "truth": "the eyes belonged to a tiny fox pup sheltering beside a lantern beetle",
        "choice": "she knelt and offered the pup a calm greeting",
    },
    {
        "shadow": "A dark face appeared in the silver fog.",
        "truth": "the face was Luna's own reflection in a quiet pool",
        "choice": "she smiled at the reflection and looked beyond it",
    },
]

EVENING_OPENINGS = [
    "At evening, when the first star trembled above the hills,",
    "As evening folded its violet cloak over the valley,",
    "One quiet evening, while the sun sank like a red ember,",
    "When evening bells sounded far beyond the forest,",
]

LESSONS = [
    "A fearful thought can be loud without being true.",
    "The mind can paint a monster where the world holds only a branch.",
    "Courage is not having no fear; it is asking fear a careful question.",
    "A quiet mind can hear what a frightened mind misses.",
]

@dataclass
class Person:
    name: str
    trait: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

@dataclass
class Guide:
    name: str
    wisdom: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

@dataclass
class QuestState:
    object_name: str
    place: str
    fear: str
    mission: str
    twist: dict
    stage: str = "beginning"
    nod_received: bool = False
    fear_understood: bool = False
    completed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

@dataclass
class World:
    hero: Person
    guide: Guide
    quest: QuestState
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

@dataclass
class StoryParams:
    hero: str
    guide: str
    place: str
    object_name: str
    fear: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A mythic evening quest about Luna, a nod, and a mental twist.")
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--guide", choices=GUIDES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object-name", dest="object_name", choices=MOON_OBJECTS)
    parser.add_argument("--fear", choices=FEARS)
    parser.add_argument("--trait", choices=TRAITS)
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


def valid_combo(params: StoryParams) -> bool:
    return (
        params.hero in HERO_NAMES
        and params.guide in GUIDES
        and params.place in PLACES
        and params.object_name in MOON_OBJECTS
        and params.fear in FEARS
        and params.trait in TRAITS
    )


def asp_facts() -> str:
    import asp
    lines = []
    for value in HERO_NAMES:
        lines.append(asp.fact("hero", value))
    for value in GUIDES:
        lines.append(asp.fact("guide", value))
    for value in PLACES:
        lines.append(asp.fact("place", value))
    for value in MOON_OBJECTS:
        lines.append(asp.fact("moon_object", value))
    for value in FEARS:
        lines.append(asp.fact("fear", value))
    for value in TRAITS:
        lines.append(asp.fact("trait", value))
    return "\n".join(lines)


ASP_RULES = r"""
quest(H,G,P,O,F,T) :- hero(H), guide(G), place(P), moon_object(O), fear(F), trait(T).
night_ready(H,G,P,O,F,T) :- quest(H,G,P,O,F,T), O != "a fallen star".
valid(H,G,P,O,F,T) :- night_ready(H,G,P,O,F,T).
#show valid/6.
"""


def asp_program(show: str = "#show valid/6.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid"))


def asp_verify() -> int:
    python_values = {
        (hero, guide, place, obj, fear, trait)
        for hero in HERO_NAMES
        for guide in GUIDES
        for place in PLACES
        for obj in MOON_OBJECTS
        for fear in FEARS
        for trait in TRAITS
        if obj != "a fallen star"
    }
    clingo_values = asp_valid()
    if python_values == clingo_values:
        print(f"OK: clingo gate matches Python ({len(clingo_values)} combinations).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(clingo_values - python_values))
    print("only in python:", sorted(python_values - clingo_values))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        hero=args.hero or rng.choice(HERO_NAMES),
        guide=args.guide or rng.choice(GUIDES),
        place=args.place or rng.choice(PLACES),
        object_name=args.object_name or rng.choice(MOON_OBJECTS),
        fear=args.fear or rng.choice(FEARS),
        trait=args.trait or rng.choice(TRAITS),
        seed=args.seed,
    )
    if not valid_combo(params):
        raise StoryError("The requested quest contains an invalid moon object, fear, or character choice.")
    return params


def make_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    twist = rng.choice(TWISTS)
    data = QUESTS[params.object_name]
    hero = Person(
        params.hero,
        params.trait,
        meters={"steps": 0.0, "distance": 0.0},
        memes={"courage": 1.0, "worry": 1.0, "clarity": 0.0},
    )
    guide = Guide(
        params.guide,
        "Look twice. The mind is a storyteller, but not every story it tells is true.",
        meters={"watchfulness": 1.0},
        memes={"wisdom": 1.0},
    )
    quest = QuestState(
        object_name=params.object_name,
        place=params.place,
        fear=params.fear,
        mission=data["mission"],
        twist=twist,
        meters={"route": 0.0, "goal": 1.0},
        memes={"mystery": 1.0},
    )
    return World(hero, guide, quest, {"opening": rng.choice(EVENING_OPENINGS), "lesson": rng.choice(LESSONS)})


def generate_story(world: World) -> None:
    hero = world.hero
    guide = world.guide
    quest = world.quest
    twist = quest.twist
    reward = QUESTS[quest.object_name]

    world.say(
        f"{world.facts['opening']} {hero.name}, a {hero.trait} child, found {quest.object_name} "
        f"glimmering beside the path."
    )
    world.say(
        f"The old tale said that {hero.name} must {quest.mission}. If the quest succeeded, "
        f"{reward['gift']}."
    )
    world.say(
        f"{guide.name} waited beneath a bent moon-tree. The guide gave one slow nod and said, "
        f'"Carry the light, but question the darkness."'
    )
    quest.nod_received = True
    quest.stage = "departure"
    hero.memes["worry"] += 0.5

    world.say(
        f"{hero.name} stepped into {quest.place}. Soon {quest.fear} appeared, and the path seemed "
        f"to twist beneath her feet."
    )
    world.say(
        f'"Turn back," whispered the frightened part of {hero.name}\'s mind. '
        f'"What if the darkness is truly dangerous?"'
    )
    world.say(
        f'"Ask one more question," called {guide.name}. "What do you know, and what are you only imagining?"'
    )
    hero.memes["clarity"] += 1.0
    quest.memes["mystery"] += 1.0
    quest.stage = "questioning"

    world.say(
        f"{twist['shadow']} {hero.name} held the {quest.object_name} close and waited instead of running."
    )
    world.say(
        f"Then came the twist: {twist['truth']}. {hero.name} {twist['choice']}."
    )
    quest.fear_understood = True
    quest.stage = "turn"
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    hero.memes["courage"] += 1.0
    hero.meters["steps"] += 1.0

    world.say(
        f"The fear had been real inside {hero.name}'s mental world, but it had not been the truth "
        f"of the forest. With the guide's nod remembered, {hero.name} followed the true path."
    )
    world.say(
        f"At the last hill, {hero.name} completed the quest and placed the {quest.object_name} where it belonged. "
        f"{reward['ending']}."
    )
    quest.completed = True
    quest.stage = "resolution"
    hero.meters["distance"] += 1.0
    hero.memes["clarity"] += 1.0

    world.say(
        f"{guide.name} smiled. " + f'"You did not defeat your mind, {hero.name}. You taught it to listen." '
        f"{world.facts['lesson']}"
    )
    world.say(
        f"By midnight, {quest.place} was quiet again, but one small light remained on the path "
        f"for the next traveler."
    )


def story_qa(world: World) -> list[QAItem]:
    hero = world.hero
    quest = world.quest
    twist = quest.twist
    return [
        QAItem(
            question="Who began the evening quest?",
            answer=f"{hero.name} began the quest as a {hero.trait} child carrying {quest.object_name}.",
        ),
        QAItem(
            question="What did the guide's nod mean?",
            answer=f"The nod encouraged {hero.name} to begin carefully and remember the guide's advice to question the darkness.",
        ),
        QAItem(
            question=f"What frightened {hero.name}?",
            answer=f"{hero.name} was frightened when {quest.fear} appeared on the path.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The frightening sight was actually {twist['truth']}.",
        ),
        QAItem(
            question="How did the mental challenge change?",
            answer=f"{hero.name} stopped running from the first thought and asked what was known and what was only imagined.",
        ),
        QAItem(
            question="How did the quest end?",
            answer=f"{hero.name} completed the quest by placing {quest.object_name} where it belonged, and {QUESTS[quest.object_name]['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey in which someone faces challenges to complete an important mission.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a surprising change that reveals the situation is different from what it first seemed.",
        ),
        QAItem(
            question="What does a nod often communicate?",
            answer="A nod can communicate agreement, encouragement, or understanding without using words.",
        ),
        QAItem(
            question="What does mental mean in this story?",
            answer="Mental describes what happens in the mind, such as thoughts, worries, questions, and understanding.",
        ),
        QAItem(
            question="Why can pausing help with fear?",
            answer="Pausing gives a person time to compare a frightening thought with clues from the real world.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly myth about an evening quest whose twist changes what the hero believes.",
        f"Tell how {world.hero.name} carries {world.quest.object_name} through {world.quest.place} after receiving a nod from {world.guide.name}.",
        f"Write a myth in which {world.quest.fear} becomes a mental test, and careful questioning reveals the truth.",
    ]


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"hero={world.hero.name} trait={world.hero.trait}",
            f"hero_meters={world.hero.meters} hero_memes={world.hero.memes}",
            f"guide={world.guide.name} nod_received={world.quest.nod_received}",
            f"quest_object={world.quest.object_name} place={world.quest.place} stage={world.quest.stage}",
            f"fear={world.quest.fear} fear_understood={world.quest.fear_understood}",
            f"completed={world.quest.completed}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


CURATED = [
    StoryParams("Luna", "the old owl", "the whispering wood", "a moon-seed", "a huge shadow", "curious", 1),
    StoryParams("Mira", "the silver fox", "the blue hill", "a fallen star", "a whisper behind the trees", "brave", 2),
    StoryParams("Sela", "the river spirit", "the sleeping valley", "a pearl of dawn", "a face in the mist", "patient", 3),
]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(item) for item in CURATED]
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
