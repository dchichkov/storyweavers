#!/usr/bin/env python3
"""
A gentle detective story about a favorite sound effect, kindness, and a laugh.
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
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = (
    "the little library beside the park",
    "the old clock tower on Maple Street",
    "the cheerful museum of tiny inventions",
    "the community hall under the striped awning",
)

SOUND_EFFECTS = (
    "a bright rubber-duck squeak",
    "a tiny trumpet toot",
    "a cheerful springy boing",
    "a soft popcorn pop",
    "a silly kazoo wah-wah",
)

PLACES = (
    "behind the puppet theater",
    "inside the lost-and-found cupboard",
    "beneath the reading-room bench",
    "beside the coat rack",
)

CLUES = (
    "a yellow feather",
    "three shiny buttons",
    "a trail of paper stars",
    "a red wool thread",
)

HELPERS = (
    ("Aunt Jo", "had tucked it somewhere safe while sweeping"),
    ("Mr. Bell", "had moved it away from a dripping umbrella"),
    ("Nia", "had carried it gently from the crowded stage"),
    ("Leo", "had hidden it from a curious puppy"),
)

JOKES = (
    "The detective notebook called the clue a very suspicious feather duster.",
    "The clue was so tiny that even the magnifying glass needed a magnifying glass.",
    "The buttons formed a trail that looked more like a parade than a crime scene.",
    "The paper stars seemed to whisper, 'Look down, detective!'",
)

ENDINGS = (
    "Then the favorite sound effect played once more, and everyone laughed kindly together.",
    "The room filled with the sound effect, warm laughter, and the happy click of a solved case.",
    "After that, the sound became a signal for helping hands and bright smiles.",
)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    detective_name: str = "Luna"
    friend_name: str = "Milo"
    setting: str = SETTINGS[0]
    sound_effect: str = SOUND_EFFECTS[0]
    hiding_place: str = PLACES[0]
    clue: str = CLUES[0]
    helper_name: str = HELPERS[0][0]
    helper_reason: str = HELPERS[0][1]
    joke: str = JOKES[0]
    ending: str = ENDINGS[0]


def tell(params: StoryParams) -> World:
    if not params.sound_effect.strip():
        raise StoryError("The favorite sound effect cannot be empty.")
    if not params.detective_name.strip() or not params.friend_name.strip():
        raise StoryError("The detective and friend need names.")

    world = World()
    detective = world.add(Entity(
        "detective", "character", params.detective_name,
        meters={"curiosity": 1.0, "kindness": 0.5},
        memes={"confidence": 0.5},
    ))
    friend = world.add(Entity(
        "friend", "character", params.friend_name,
        meters={"worry": 1.0},
        memes={"hope": 0.2},
    ))
    sound = world.add(Entity(
        "sound_effect", "object", params.sound_effect,
        meters={"volume": 0.0},
        memes={"favorite": 1.0},
    ))
    helper = world.add(Entity(
        "helper", "character", params.helper_name,
        meters={"care": 1.0},
        memes={"kindness": 1.0},
    ))
    world.facts.update(
        detective=detective,
        friend=friend,
        sound=sound,
        helper=helper,
        clue=params.clue,
        setting=params.setting,
        hiding_place=params.hiding_place,
        joke=params.joke,
        helper_reason=params.helper_reason,
    )

    world.say(
        f"Luna was the best little detective in {params.setting}, especially when a mystery made someone feel worried."
    )
    world.say(
        f"Her friend {params.friend_name} had lost their favorite sound effect: {params.sound_effect}."
    )
    world.para()
    world.say(
        f'"I heard it near the stage, and then it vanished," {params.friend_name} said.'
    )
    world.say(
        f'"Do not worry," Luna replied. "We will follow the clues, and we will be gentle with everyone we meet."'
    )
    detective.memes["confidence"] += 0.5
    friend.meters["worry"] -= 0.2

    world.say(
        f"Near the stage, Luna found {params.clue} pointing toward {params.hiding_place}."
    )
    world.say(params.joke)
    detective.memes["humor"] = 1.0
    world.para()

    world.say(
        f'"Tap, tap. Is anyone there?" Luna called. A small voice answered, "Please do not be cross."'
    )
    world.say(
        f"It was {params.helper_name}, who had found the sound effect and {params.helper_reason}."
    )
    world.say(
        f'"Thank you for protecting it," Luna said. "Would you help us return it?"'
    )
    world.say(
        f'"Of course," said {params.helper_name}. "Kind detectives make room for helpers."'
    )
    helper.memes["kindness"] += 1.0
    detective.meters["kindness"] += 0.5
    world.fired.add("kindness_turn")

    world.say(
        f"{params.helper_name} handed over the favorite sound effect. {params.friend_name} pressed it carefully."
    )
    world.say(
        f"{params.sound_effect.capitalize()}! The sound bounced off the walls, and Luna's joke made everybody laugh."
    )
    sound.meters["volume"] = 1.0
    friend.meters["worry"] = 0.0
    friend.memes["relief"] = 1.0
    world.fired.add("case_solved")
    world.para()
    world.say(params.ending)
    return world


ASP_RULES = r"""
missing(sound_effect).
has_clue(clue).
has_helper(helper).
helper_kind(helper).
favorite(sound_effect).
case_solved(sound_effect) :-
    missing(sound_effect),
    has_clue(clue),
    has_helper(helper),
    helper_kind(helper),
    favorite(sound_effect).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("missing", "sound_effect"),
        asp.fact("has_clue", "clue"),
        asp.fact("has_helper", "helper"),
        asp.fact("helper_kind", "helper"),
        asp.fact("favorite", "sound_effect"),
    ])


def asp_program(show: str = "#show case_solved/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    solved = set(asp.atoms(model, "case_solved"))
    if solved == {("sound_effect",)}:
        print("OK: ASP and Python agree that kindness solves the sound-effect case.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP case_solved:", sorted(solved))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    seed = int(args.seed if args.seed is not None else 0)
    detective_names = ("Luna", "Mara", "Tess", "Pip", "Nora")
    friend_names = ("Milo", "Ari", "Bee", "Jun", "Sol")
    helper_name, helper_reason = rng.choice(HELPERS)
    return StoryParams(
        seed=seed,
        detective_name=rng.choice(detective_names),
        friend_name=rng.choice(friend_names),
        setting=rng.choice(SETTINGS),
        sound_effect=rng.choice(SOUND_EFFECTS),
        hiding_place=rng.choice(PLACES),
        clue=rng.choice(CLUES),
        helper_name=helper_name,
        helper_reason=helper_reason,
        joke=rng.choice(JOKES),
        ending=rng.choice(ENDINGS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle detective story about a missing favorite sound effect.",
        f"Include kindness and humor as {f['detective'].label} follows {f['clue']}.",
        f"Resolve the mystery when {f['helper'].label} explains why the sound effect was moved to {f['hiding_place']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What did {friend.label} lose?",
            answer=f"{friend.label} lost their favorite sound effect, {f['sound'].label}.",
        ),
        QAItem(
            question=f"Which clue did {detective.label} follow?",
            answer=f"{detective.label} followed {f['clue']}, which pointed toward {f['hiding_place']}.",
        ),
        QAItem(
            question=f"Who had moved the sound effect, and why?",
            answer=f"{helper.label} had moved it because {f['helper_reason']}.",
        ),
        QAItem(
            question=f"How did kindness help solve the case?",
            answer=f"{detective.label} listened without blaming anyone, thanked {helper.label}, and invited the helper to return the sound effect.",
        ),
        QAItem(
            question="What happened when the sound effect was played?",
            answer=f"{f['sound'].label.capitalize()} It bounced around the room, and everyone laughed together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a sound made or played to help a story, game, or performance feel lively and clear.",
        ),
        QAItem(
            question="Why is kindness useful during a mystery?",
            answer="Kindness helps people feel safe enough to share what they know, so a problem can be solved without blame.",
        ),
        QAItem(
            question="Why can humor help friends?",
            answer="A gentle joke can ease worry and give people a shared moment of happiness.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A kindness-and-humor detective story about a favorite sound effect."
    )
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
        print(sorted(set(asp.atoms(model, "case_solved"))))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 1 if args.all else args.n
    samples: list[StorySample] = []

    for offset in range(count):
        sample_seed = base_seed + offset
        local_args = argparse.Namespace(**vars(args))
        local_args.seed = sample_seed
        params = resolve_params(local_args, random.Random(sample_seed))
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
