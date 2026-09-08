#!/usr/bin/env python3
"""
Standalone storyworld: a child-friendly music-room mystery about inspection,
transformation, and sharing.

A careful inspection of a strange panty-shaped mark on a music stand leads
friends from suspicion to a harmless transformation and a shared song.
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
    place: str = "music room"
    hero: str = "Luna"
    friend: str = "Milo"
    object_name: str = "panty"
    seed: Optional[int] = None


PLACES = {"music room": {"instruments": True, "window": True}}
HEROES = ["Luna", "Mia", "Nora", "Tariq", "June"]
FRIENDS = ["Milo", "Ari", "Pip", "Sana", "Theo"]
OBJECTS = ["panty"]


@dataclass(frozen=True)
class Case:
    title: str
    mystery: str
    first_guess: str
    clue: str
    inspection: str
    cause: str
    transformation: str
    sharing: str
    lesson: str
    ending: str


CASES = [
    Case(
        "the silver panty shadow",
        "a silver panty-shaped shadow appeared on the music stand",
        "thought someone had left a strange costume piece there",
        "the shadow moved when the afternoon sun moved",
        "used a flashlight, a ruler, and a mirror while staying beside the floor line",
        "a folded pair of practice pants on a chair blocked the sunlight and made the shape",
        "turning the chair changed the shadow into a bright bow",
        "shared the flashlight and took turns playing the melody",
        "A careful inspection can turn an odd sight into a kind explanation",
        "the old stand held a golden bow of light while their song filled the room",
    ),
    Case(
        "the whispering panty mark",
        "a pale panty-shaped mark seemed to whisper whenever the piano lid opened",
        "believed a friend had hidden a silly prop inside the piano",
        "the sound stopped when the lid was opened slowly",
        "listened from three marked spots while the music teacher checked the piano safely",
        "a loose strip of felt fluttered against the lid and changed its shape",
        "folding the felt into a soft music note stopped the whisper",
        "shared the piano bench and let each child choose one note",
        "A strange sound deserves a fair test before a person gets blamed",
        "the piano grew quiet, then answered their shared song with warm, clear notes",
    ),
    Case(
        "the transformed panty picture",
        "a drawing that looked like a panty appeared on the rehearsal chart",
        "suspected that a friend had scribbled over the song",
        "the shape became a treble clef when the chart was turned sideways",
        "inspected the paper from both sides and compared it with the teacher's stencil",
        "a water mark had spread through the paper and changed the picture",
        "turning the chart transformed the puzzling mark into a useful music symbol",
        "shared the corrected chart so every player could follow the tune",
        "Changing your viewpoint can transform a confusing clue",
        "the transformed treble clef guided every instrument into the same bright ending",
    ),
]


class World:
    def __init__(self, place: str):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join(
        [params.place, params.hero, params.friend, params.object_name]
    )
    return sum((i + 1) * ord(c) for i, c in enumerate(text))


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.object_name not in OBJECTS:
        raise StoryError(f"Unsupported object: {params.object_name}")
    if params.hero == params.friend:
        raise StoryError("The hero and friend must have different names.")

    rng = random.Random(_stable_seed(params) ^ 0x51A7)
    case = rng.choice(CASES)
    world = World(params.place)

    hero = world.add(
        Entity(
            "hero",
            "character",
            params.hero,
            meters={"distance_from_clue": 2.0},
            memes={"curiosity": 1.0, "trust": 0.0},
        )
    )
    friend = world.add(
        Entity(
            "friend",
            "character",
            params.friend,
            meters={"distance_from_clue": 2.0},
            memes={"hurt": 0.0, "trust": 0.0},
        )
    )
    stand = world.add(
        Entity(
            "stand",
            "instrument stand",
            "music stand",
            meters={"height": 1.2, "brightness": 0.6},
            memes={},
        )
    )
    clue = world.add(
        Entity(
            "clue",
            "object",
            params.object_name,
            meters={"oddness": 1.0, "inspected": 0.0},
            memes={},
        )
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        stand=stand,
        clue=clue,
        case=case,
        resolved=False,
        shared=False,
        transformed=False,
    )

    openings = [
        f"The music room was quiet except for one humming string.",
        f"Rain tapped the windows of the music room as {hero.label} opened a mystery notebook.",
        f"Before rehearsal began, {hero.label} noticed something unusual in the music room.",
    ]
    introductions = [
        f"{hero.label} loved mysteries, but believed every clue deserved a careful inspection.",
        f"{hero.label} carried a pencil, a tuning fork, and a promise not to blame anyone too quickly.",
        f"{hero.label} invited {friend.label} to investigate with open eyes and patient ears.",
    ]
    world.say(rng.choice(openings))
    world.say(rng.choice(introductions))
    world.say(
        f"{friend.label} was setting music on the stand when the strange case called for both friends."
    )
    world.say(
        f'The object at the center of the mystery was a little shape that looked like a {params.object_name}.'
    )

    world.para()
    world.say(f"Their inspection began when {case.mystery}.")
    world.say(
        f'{friend.label} frowned. "Maybe someone {case.first_guess}."'
    )
    world.say(
        f'{hero.label} answered, "That is only a guess. Let us inspect the clue before we decide."'
    )
    world.say(
        f'{friend.label} took a breath. "All right. I want the truth, and I want us to be fair."'
    )
    friend.memes["hurt"] += 1.0
    world.say(
        "For a moment, the music room felt less friendly than it had before."
    )

    world.para()
    world.say(
        f"They wrote down what they could see, hear, and measure. {case.clue.capitalize()}."
    )
    world.say(f"Without touching anything fragile, they {case.inspection}.")
    clue.meters["inspected"] = 1.0
    hero.memes["curiosity"] += 1.0
    world.say(
        f"The inspection changed the mystery because {case.cause}."
    )
    world.say(
        f'"Look!" said {friend.label}. "The clue changes when we change what is around it."'
    )
    world.say(
        f'"Then the room is telling us something," {hero.label} replied. "Let us test that idea."'
    )

    world.para()
    world.say(
        f"The fair test showed that {case.cause}."
    )
    world.say(
        f"With the teacher's permission, the friends tried a gentle transformation: {case.transformation}."
    )
    world.facts["transformed"] = True
    stand.meters["brightness"] += 0.4
    world.say(
        f"The strange mark no longer seemed like a secret. {case.sharing.capitalize()}."
    )
    world.facts["shared"] = True
    hero.memes["trust"] += 1.0
    friend.memes["trust"] += 1.0
    friend.memes["hurt"] = 0.0
    world.facts["resolved"] = True

    world.say(
        f'{friend.label} smiled. "I am sorry I made a fast guess."'
    )
    world.say(
        f'{hero.label} smiled back. "I am glad we shared the inspection instead of sharing blame."'
    )
    world.say(
        f"Together they wrote the lesson in the casebook: {case.lesson}."
    )
    world.say(
        f"When rehearsal began, {case.ending.capitalize()}."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    return [
        'Write a child-friendly Mystery in a music room using the words "inspection" and "panty".',
        f"Tell how {hero.label} and {friend.label} investigate {case.title} without blaming one another.",
        f"Include a transformation and a moment of sharing that resolve this mystery: {case.mystery}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    return [
        QAItem(
            question=f"What did {hero.label} and {friend.label} inspect in the music room?",
            answer=f"They inspected a strange shape that looked like a panty on the music stand. They recorded what changed before deciding what caused it.",
        ),
        QAItem(
            question=f"What did the inspection reveal?",
            answer=f"The inspection revealed that {case.cause}. The clue changed because something around it changed.",
        ),
        QAItem(
            question="How did transformation help solve the mystery?",
            answer=f"The friends used a gentle transformation: {case.transformation}. This made the odd clue easier to understand.",
        ),
        QAItem(
            question=f"How did {hero.label} and {friend.label} show sharing?",
            answer=f"They shared the inspection, their observations, and the music-making. They also shared the equipment and let each child take a turn.",
        ),
        QAItem(
            question="What lesson did the friends learn?",
            answer=f"They learned that {case.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inspection?",
            answer="An inspection is a careful look or check used to learn what something is like or what happened.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a change from one form, appearance, or condition into another.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving others a fair chance to use, enjoy, or know about something with you.",
        ),
        QAItem(
            question="What is a music room?",
            answer="A music room is a place where people keep instruments, practice songs, and make music together.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Music-room mystery about inspection, transformation, and sharing."
    )
    parser.add_argument("--place", choices=list(PLACES), default=None)
    parser.add_argument("--hero", choices=HEROES, default=None)
    parser.add_argument("--friend", choices=FRIENDS, default=None)
    parser.add_argument("--object-name", dest="object_name", choices=OBJECTS, default="panty")
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(HEROES)
    available = [name for name in FRIENDS if name != hero]
    if not available:
        raise StoryError("No different friend name is available.")
    friend = args.friend or rng.choice(available)
    if friend == hero:
        raise StoryError("The hero and friend must have different names.")
    return StoryParams(
        place=place,
        hero=hero,
        friend=friend,
        object_name=args.object_name,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
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
        lines.append(
            f"  {entity.id}: kind={entity.kind} meters={meters} memes={memes}"
        )
    lines.append(
        f"  resolved={world.facts.get('resolved')} "
        f"transformed={world.facts.get('transformed')} "
        f"shared={world.facts.get('shared')}"
    )
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_object(O) :- object(O).
valid_story(P,O) :- valid_place(P), valid_object(O).
"""


def asp_facts() -> str:
    import asp

    facts = [asp.fact("place", place) for place in PLACES]
    facts.extend(asp.fact("object", item) for item in OBJECTS)
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(place, item) for place in PLACES for item in OBJECTS]


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH between ASP and Python validity gates.")
        print("Only in ASP:", sorted(clingo_set - python_set))
        print("Only in Python:", sorted(python_set - clingo_set))
        return 1

    for seed in range(5):
        params = StoryParams(seed=seed)
        sample = generate(params)
        if not sample.story or "inspection" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print("Generated QA verification failed.")
            return 1

    print(f"OK: ASP matches Python ({len(python_set)} combinations); stories verified.")
    return 0


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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("Compatible music-room story combinations:")
        for place, item in valid_combos():
            print(f"  {place} / {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, hero in enumerate(HEROES):
            friend = FRIENDS[index % len(FRIENDS)]
            if friend == hero:
                friend = FRIENDS[(index + 1) % len(FRIENDS)]
            params = StoryParams(
                place="music room",
                hero=hero,
                friend=friend,
                object_name="panty",
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(max(1, args.n)):
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
