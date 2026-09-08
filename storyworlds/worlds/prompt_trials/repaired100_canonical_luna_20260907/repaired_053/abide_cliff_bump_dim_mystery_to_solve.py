#!/usr/bin/env python3
"""
A gentle fable about a cliffside mystery, a puzzling bump-dim rhyme, and friendship.

Seed words: abide, cliff, bump-dim
Features: Mystery to Solve, Friendship, Rhyme
Style: Fable
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


ANIMALS = ["fox", "badger", "hare", "wren", "otter", "goat", "mouse", "tortoise"]
NAMES = ["Luna", "Pip", "Mara", "Bram", "Tess", "Oren", "Nell", "Cato"]
PLACES = [
    "the blue cliff",
    "the whispering cliff",
    "the mossy cliff",
    "the sunset cliff",
]
OBJECTS = [
    "a silver bell",
    "a red ribbon",
    "a little acorn cup",
    "a moon-white pebble",
]
RHYME_ENDINGS = [
    "Bump-dim, bump-dim, follow the sound; a patient friend can turn you around.",
    "Bump-dim, bump-dim, beneath the stone; no one should search for a clue alone.",
    "Bump-dim, bump-dim, soft in the night; friendship can make a hidden thing bright.",
    "Bump-dim, bump-dim, over and under; careful ears can solve the wonder.",
]
OPENINGS = [
    "At dawn, Luna reached the cliff while the sea below shone like a blue button.",
    "The cliff was quiet that morning, except for gulls and one curious little thump.",
    "In a valley beside the cliff, two friends prepared for the day with bright eyes and warm hearts.",
    "The sun climbed over the cliff, and a strange sound rolled through the grass.",
]
LESSONS = [
    "The friends learned that a mystery grows smaller when patient friends share their clues.",
    "They discovered that trust is stronger than a quick guess, especially beside a dangerous cliff.",
    "From that day on, they remembered that friendship means listening before leaping.",
    "The fable taught them that a careful question may open a door that force cannot move.",
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    species: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    danger: str = "a steep drop"


@dataclass
class Mood:
    mystery: bool = True
    friendship: bool = True
    rhyme: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_species: str
    friend_name: str
    friend_species: str
    object_label: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mood: Mood) -> None:
        self.setting = setting
        self.mood = mood
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


def tell(params: StoryParams) -> World:
    world = World(Setting(params.place), Mood())
    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            species=params.hero_species,
            memes={"curiosity": 1.0, "courage": 0.7, "worry": 0.4},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend_name,
            kind="character",
            species=params.friend_species,
            memes={"loyalty": 1.0, "patience": 1.0},
        )
    )
    object_ent = world.add(
        Entity(
            id="mystery-object",
            kind="thing",
            label=params.object_label,
            owner=params.hero_name,
            meters={"visible": 0.0, "safe": 0.0},
        )
    )

    seed_value: object = params.seed
    if seed_value is None:
        seed_value = "|".join(
            [
                params.place,
                params.hero_name,
                params.hero_species,
                params.friend_name,
                params.friend_species,
                params.object_label,
            ]
        )
    rng = random.Random(seed_value)

    opening = rng.choice(OPENINGS)
    rhyme = rng.choice(RHYME_ENDINGS)
    lesson = rng.choice(LESSONS)
    clue = rng.choice(
        [
            "three small dents in the dust led away from the edge",
            "a thread of red moss was caught on a low thorn",
            "the sound returned whenever the sea wind shook a hollow branch",
            "tiny round tracks circled the same flat stone",
        ]
    )
    false_guess = rng.choice(
        [
            "a pebble had fallen over the edge",
            "a crow had carried the missing object away",
            "the cliff itself was groaning",
            "someone had hidden it to play a trick",
        ]
    )
    cause = rng.choice(
        [
            "a young mountain goat had nudged the object into a narrow crack while seeking salt",
            "the wind had rolled the object beneath a stone shelf, where it tapped a hollow root",
            "a small marmot had dragged the object into a safe nook beside its den",
            "the object had slipped through a curtain of grass and landed in a shallow ledge",
        ]
    )
    method = rng.choice(
        [
            "a long willow twig",
            "a loop of soft vine",
            "a flat branch and a woven grass cord",
            "two steady sticks tied together",
        ]
    )

    hero.meters["distance_from_cliff_edge"] = 3.0
    friend.meters["distance_from_cliff_edge"] = 3.0
    object_ent.meters["visible"] = 0.0
    object_ent.memes["mystery"] = 1.0

    world.say(opening)
    world.say(
        f"{hero.id}, a thoughtful young {hero.species}, had come to {world.setting.place} to find {params.object_label}."
    )
    world.say(
        f"{friend.id}, a kind {friend.species}, came too, because wise friends do not let one another search near {world.setting.danger} alone."
    )
    world.para()
    world.say(
        f"Then a soft voice seemed to rise from the stones: “{rhyme}”"
    )
    world.say(
        f"{hero.id} spotted a dim mark near the grass and wondered whether {false_guess}."
    )
    world.say(
        f'"Do not step closer yet," said {friend.id}. "A cliff rewards careful ears, not hurried feet."'
    )
    world.say(
        f'"You are right," replied {hero.id}. "We will abide by the safe path and solve the mystery together."'
    )
    world.para()
    world.say(
        f"They listened, looked, and compared their clues. Soon they found that {clue}."
    )
    world.say(
        f"The clue changed their minds: the bump-dim sound was not a warning from the cliff. It came from a hidden place below the safe path."
    )
    world.say(f"{hero.id} held the grass aside while {friend.id} pointed with a paw.")
    world.say(f"There, at last, they understood the truth: {cause}.")
    world.say(
        f'"I know what to do," said {friend.id}. "We can use {method}, but only while both of us stay well back."'
    )
    world.say(
        f'"And I will follow your directions," said {hero.id}. "Friends should make one another safer."'
    )
    world.para()
    world.say(
        f"Together they placed the {method} along the safe ground. {friend.id} held the cord while {hero.id} gently guided it toward the hidden object."
    )
    world.say(
        f"The object slid free without a single dangerous step. The bump-dim sound stopped, and the mystery became a happy answer."
    )
    world.say(
        f"{hero.id} thanked {friend.id}, and {friend.id} smiled. They carried {params.object_label} away from the cliff and returned it to its proper place."
    )
    world.say(lesson)
    world.say(
        f"Before they left, the two friends repeated the rhyme together: “{rhyme}”"
    )
    world.say(
        f"Below them, the sea kept its rhythm, while the safe path beside {world.setting.place} held two sets of cheerful footprints."
    )

    hero.meters["distance_from_cliff_edge"] = 5.0
    friend.meters["distance_from_cliff_edge"] = 5.0
    hero.memes.update(calm=1.0, trust=1.0)
    friend.memes.update(calm=1.0, trust=1.0)
    object_ent.meters.update(visible=1.0, safe=1.0)
    object_ent.memes.update(mystery=0.0, belonging=1.0)

    world.facts.update(
        hero=hero,
        friend=friend,
        object=object_ent,
        clue=clue,
        false_guess=false_guess,
        cause=cause,
        method=method,
        rhyme=rhyme,
        lesson=lesson,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    obj = world.facts["object"]
    return [
        f"Write a child-friendly fable about a mystery near a cliff involving {obj.label}.",
        "Include the words abide and bump-dim, and make friendship solve the problem safely.",
        "Use a short rhyme as a clue, then show how careful listening changes the characters' decision.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    obj = world.facts["object"]
    return [
        QAItem(
            question=f"What mystery did {hero.id} and {friend.id} need to solve?",
            answer=f"They needed to discover where {obj.label} had gone and what was making the bump-dim sound near the cliff.",
        ),
        QAItem(
            question="Why did the friends stay on the safe path?",
            answer=f"They stayed back because the cliff had a steep drop. {friend.id} reminded {hero.id} that careful friends should not take a dangerous step just to reach a clue.",
        ),
        QAItem(
            question="Which clue helped them understand the sound?",
            answer=f"They noticed that {world.facts['clue']}. This showed that the sound came from a hidden place near the safe path rather than from the cliff itself.",
        ),
        QAItem(
            question="How did friendship help solve the mystery?",
            answer=f"{hero.id} and {friend.id} shared observations, listened to each other, and used {world.facts['method']} together. Their teamwork brought the object out without anyone going near the edge.",
        ),
        QAItem(
            question="What lesson did the fable teach?",
            answer=world.facts["lesson"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cliff?",
            answer="A cliff is a steep wall of earth or rock with a drop below it, so people and animals should keep a safe distance from its edge.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, listening to them, and helping them through a difficult moment.",
        ),
        QAItem(
            question="Why can a rhyme help solve a mystery?",
            answer="A rhyme is easy to remember, so its repeated sounds or words can point careful listeners toward an important clue.",
        ),
        QAItem(
            question="What does abide mean in this story?",
            answer="Here, abide means to follow or keep a rule. The friends abided by the safe-path rule near the cliff.",
        ),
    ]


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        label = f", {ent.label}" if ent.label else ""
        out.append(f"  {ent.id} ({ent.species}{label}) {' '.join(bits)}")
    return "\n".join(out)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fable world about a cliff mystery, bump-dim rhyme, and friendship."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero-name")
    parser.add_argument("--friend-name")
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
    place = args.place or rng.choice(PLACES)
    hero_species = rng.choice(ANIMALS)
    friend_species = rng.choice([animal for animal in ANIMALS if animal != hero_species])
    hero_name = args.hero_name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice(
        [name for name in NAMES if name != hero_name]
    )
    object_label = rng.choice(OBJECTS)
    if hero_name == friend_name:
        raise StoryError("hero and friend must have different names")
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_species=hero_species,
        friend_name=friend_name,
        friend_species=friend_species,
        object_label=object_label,
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


def asp_facts() -> str:
    return "\n".join(
        [
            "setting(cliff).",
            "feature(mystery_to_solve).",
            "feature(friendship).",
            "feature(rhyme).",
            "word(abide).",
            "word(bump_dim).",
            "rule(safe_path).",
        ]
    )


ASP_RULES = r"""
valid_story :-
    setting(cliff),
    feature(mystery_to_solve),
    feature(friendship),
    feature(rhyme),
    word(abide),
    word(bump_dim),
    rule(safe_path).
#show valid_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/0."))
    values = set(asp.atoms(model, "valid_story"))
    expected = {()}
    if values != expected:
        print("MISMATCH:", values, expected)
        return 1

    seed = 777
    params = resolve_params(argparse.Namespace(
        place=None,
        hero_name=None,
        friend_name=None,
    ), random.Random(seed))
    params.seed = seed
    sample = generate(params)
    required = ["abide", "cliff", "bump-dim", "friendship", "mystery"]
    lowered = sample.story.lower()
    missing = [word for word in required if word not in lowered]
    if missing:
        print("MISMATCH: generated story missing", missing)
        return 1
    if not sample.story_qa or not sample.world_qa:
        print("MISMATCH: generated story lacks QA")
        return 1
    print("OK: ASP facts and Python world agree; generated story passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed))
        params.seed = base_seed
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and attempt < limit:
            params = resolve_params(args, random.Random(base_seed + attempt))
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

    if len(samples) < args.n:
        raise StoryError("could not produce the requested number of distinct stories")

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/0."))
        if not asp.atoms(model, "valid_story"):
            raise StoryError("ASP reasonableness check rejected this world")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### story {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
