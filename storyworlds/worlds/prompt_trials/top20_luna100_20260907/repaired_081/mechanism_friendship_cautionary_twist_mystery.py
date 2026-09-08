#!/usr/bin/env python3
"""
Story world: a small mystery about a strange mechanism, friendship, and a
cautionary twist.

Luna and her friend Theo find a clicking box in an old greenhouse. They want
to make it open, but careful clues show that the mechanism protects a fragile
nest. Their friendship helps them choose curiosity without causing harm.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    description: str


@dataclass
class StoryParams:
    place: str = "Glasshouse"
    hero_name: str = "Luna"
    friend_name: str = "Theo"
    mystery: str = "clicking_box"
    telling_mode: str = "mystery opening"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


PLACE_REGISTRY = {
    "Glasshouse": Place(
        "Glasshouse",
        "an old glasshouse where moonlight shone through dusty panes",
    ),
    "Clock Garden": Place(
        "Clock Garden",
        "a quiet garden filled with stopped sundials and ivy-covered paths",
    ),
    "Harbor Shed": Place(
        "Harbor Shed",
        "a weathered shed beside the misty water",
    ),
}

HERO_NAMES = ["Luna", "Mara", "Nell", "Suri", "Pip"]
FRIEND_NAMES = ["Theo", "Ari", "Jem", "Bea", "Owen"]

MYSTERIES = {
    "clicking_box": {
        "object": "a small brass box with a silver wheel",
        "premise": "A small brass box clicked beneath a bench, although nobody had left it there.",
        "first_guess": "Luna guessed that the wheel was a key and reached to spin it.",
        "clue": "Theo noticed three tiny feathers caught in the wheel and a fresh scratch beneath the box.",
        "danger": "The mechanism was not a lock at all; it was a gentle gate holding a warm nest behind the bench.",
        "change": "They stopped touching the wheel, cleared a path around the bench, and marked the spot with a ribbon so nobody would step on it.",
        "result": "The clicking softened, and a mother wren slipped safely through the opening to the nest.",
        "twist": "When the box clicked open by itself, it revealed not treasure but a tiny spring that released the nesting gate.",
        "lesson": "a mysterious mechanism should be understood before it is forced",
        "ending": "At dawn, three chicks peeped from the nest while the brass wheel rested quietly in the sun.",
    },
    "whistling_lantern": {
        "object": "a green lantern with a whistle inside",
        "premise": "A green lantern whistled every time the wind crossed the garden path.",
        "first_guess": "Luna thought someone had hidden a message in it and tried to pull off its lid.",
        "clue": "Theo found muddy paw prints circling the lantern and a loose cord leading toward a gate.",
        "danger": "The mechanism was a warning bell for the garden gate, which protected a sleeping hedgehog from the path.",
        "change": "They left the lantern closed, moved the loose cord away from the walkway, and placed a clear sign beside the gate.",
        "result": "The warning still sounded, but visitors knew to walk around the hedgehog's shelter.",
        "twist": "The whistle's secret message was only the wind showing them where the gate needed care.",
        "lesson": "a strange sound can be a useful warning rather than an invitation to meddle",
        "ending": "The lantern gave one soft whistle as the hedgehog curled safely beneath the leaves.",
    },
    "turning_map": {
        "object": "a wooden map with a turning moon",
        "premise": "A wooden map kept turning its moon toward one dark corner of the room.",
        "first_guess": "Luna wanted to twist the moon until the hidden route appeared.",
        "clue": "Theo saw a thread tied to the map and followed it to a cracked shelf.",
        "danger": "The mechanism was balancing the shelf above a jar of rescued fireflies.",
        "change": "They steadied the shelf with a book, untied the thread, and waited for the keeper before moving the map.",
        "result": "The fireflies stayed safe, and the moon stopped turning when the shelf was level.",
        "twist": "The secret route was not under the map; it was the safe path they made by noticing the shelf.",
        "lesson": "following a clue includes noticing what the clue may be protecting",
        "ending": "The fireflies glowed below the quiet map like a small sky under the shelf.",
    },
    "bell_drawer": {
        "object": "a narrow drawer with a copper bell",
        "premise": "A narrow drawer rang once whenever someone walked near the old cabinet.",
        "first_guess": "Luna decided the bell must announce a hidden prize and tugged at the drawer.",
        "clue": "Theo found a faded picture showing the same bell beside a jar marked with a red leaf.",
        "danger": "The mechanism warned that the cabinet held delicate seeds that spilled whenever the drawer was pulled too hard.",
        "change": "They stopped pulling, supported the drawer, and asked the gardener to open it with the proper tool.",
        "result": "The seeds remained dry and safe inside their labeled jar.",
        "twist": "The prized secret was not gold but a collection of seeds waiting for the right season.",
        "lesson": "careful hands matter more than quick answers",
        "ending": "Later, the gardener planted one seed, and a green shoot lifted beside the silent bell.",
    },
}

TELLING_MODES = [
    "mystery opening",
    "clue first",
    "quiet opening",
    "dialogue opening",
    "warning first",
]

ASP_RULES = r"""
mechanism(M) :- mechanism_name(M).
friendship(H,F) :- hero(H), friend(F), H != F.
safe_choice(H) :- observed(H), protected_place.
understood(M) :- clue_found(M), stopped_touching(M).
lesson_learned(H) :- learned(H).
resolved(M) :- understood(M), protected_place.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("mechanism_name", "mystery_mechanism"),
            asp.fact("hero", "luna"),
            asp.fact("friend", "theo"),
            asp.fact("observed", "luna"),
            asp.fact("protected_place"),
            asp.fact("clue_found", "mystery_mechanism"),
            asp.fact("stopped_touching", "mystery_mechanism"),
            asp.fact("learned", "luna"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = asp.one_model(
        asp_program(
            "#show resolved/1.\n"
            "#show safe_choice/1.\n"
            "#show lesson_learned/1.\n"
            "#show friendship/2."
        )
    )
    actual = {
        (sym.name, tuple(
            a.string if a.type.name == "String"
            else a.number if a.type.name == "Number"
            else a.name
            for a in sym.arguments
        ))
        for sym in shown
    }
    expected = {
        ("resolved", ("mystery_mechanism",)),
        ("safe_choice", ("luna",)),
        ("lesson_learned", ("luna",)),
        ("friendship", ("luna", "theo")),
    }
    if actual == expected:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mystery story world about a mechanism and friendship."
    )
    parser.add_argument("--place", choices=PLACE_REGISTRY)
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--mystery", choices=MYSTERIES)
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
    hero = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    if hero == friend:
        raise StoryError("The friends must have different names.")
    return StoryParams(
        place=args.place or rng.choice(list(PLACE_REGISTRY)),
        hero_name=hero,
        friend_name=friend,
        mystery=args.mystery or rng.choice(list(MYSTERIES)),
        telling_mode=rng.choice(TELLING_MODES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACE_REGISTRY:
        raise StoryError(f"Unknown place: {params.place}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if params.hero_name == params.friend_name:
        raise StoryError("The hero and friend must be different people.")

    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.place}:{params.hero_name}:{params.friend_name}:{params.mystery}"
    )
    place = PLACE_REGISTRY[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(place)

    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            label=params.hero_name,
            type="child",
            memes={"curiosity": 1.0, "worry": 0.0, "trust": 1.0},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            label=params.friend_name,
            type="child",
            memes={"curiosity": 1.0, "care": 1.0, "trust": 1.0},
        )
    )
    mechanism = world.add(
        Entity(
            id="mechanism",
            kind="object",
            label=mystery["object"],
            phrase=mystery["object"],
            type="mechanism",
            meters={"turn": 0.0, "risk": 1.0, "sound": 1.0},
            memes={"mystery": 1.0, "danger": 0.0, "purpose": 0.0},
        )
    )

    openings = {
        "mystery opening": (
            f"No one knew why {mystery['object']} was waiting in {place.description}."
        ),
        "clue first": (
            f"A line of dust ended beside {mystery['object']} in {place.description}."
        ),
        "quiet opening": (
            f"Moonlight rested on the floor of {place.description} when "
            f"{params.hero_name} noticed {mystery['object']}."
        ),
        "dialogue opening": (
            f'“Did you hear that?” {params.hero_name} whispered when {mystery["object"]} clicked.'
        ),
        "warning first": (
            f"{params.friend_name} raised a hand before {params.hero_name} touched "
            f"{mystery['object']} in {place.description}."
        ),
    }
    world.say(openings[params.telling_mode])
    world.say(
        f"{params.hero_name} and {params.friend_name} had come together because they "
        "liked solving small mysteries, but they promised to leave living things safer than they found them."
    )
    world.say(
        f"The mechanism made a tiny sound, and {params.hero_name} crouched beside it while "
        f"{params.friend_name} watched the shadows around {mystery['object']}."
    )
    world.say(mystery["premise"])
    world.say(mystery["first_guess"])
    hero.meters["attention"] = 1.0
    hero.memes["worry"] = 1.0
    mechanism.meters["turn"] = 1.0
    world.say(
        f'“Wait,” {params.friend_name} said. “A mystery can be a message, not just a lock.”'
    )
    world.say(
        f'“Then tell me what you see,” {params.hero_name} replied, moving their hand away.'
    )
    world.say(
        f"{params.friend_name} pointed out the details one by one, and {params.hero_name} "
        "looked again without touching the mechanism."
    )
    world.say(mystery["clue"])
    mechanism.memes["purpose"] = 1.0
    mechanism.memes["danger"] = 1.0
    world.say(
        f"The friends understood that the clicking mechanism was connected to something "
        f"important in {place.name}, so they made a safer plan."
    )
    world.say(
        f'“We can still solve it,” {params.hero_name} said, “but solving it means protecting what is behind it.”'
    )
    world.say(
        f'“Exactly,” {params.friend_name} answered. “Let the clue choose our next step.”'
    )
    world.say(mystery["danger"])
    hero.memes["curiosity"] = 0.5
    hero.memes["care"] = 1.0
    friend.memes["trust"] = 2.0
    world.say(mystery["change"])
    mechanism.meters["turn"] = 0.0
    mechanism.meters["risk"] = 0.0
    world.say(mystery["result"])
    world.say(mystery["twist"])
    world.say(
        f"{params.hero_name} understood the cautionary twist: the safest answer was not "
        "the secret inside the mechanism, but the living thing the mechanism protected."
    )
    world.say(
        f"{params.friend_name} smiled, and the two friends agreed that their best discoveries "
        "were the ones they could share without causing harm."
    )
    world.say(mystery["ending"])

    world.facts.update(
        hero=hero,
        friend=friend,
        mechanism=mechanism,
        place=place,
        clue=mystery["clue"],
        danger=mystery["danger"],
        transformation=mystery["change"],
        result=mystery["result"],
        twist=mystery["twist"],
        lesson=mystery["lesson"],
        resolved=True,
        friendship=True,
    )

    prompts = [
        f"Write a mystery for {params.hero_name} and {params.friend_name} about {mystery['object']}.",
        f"Show how a clue changes {params.hero_name}'s decision about the mechanism in {place.name}.",
        f"Include a cautionary twist and a friendship that helps protect something fragile.",
    ]
    story_qa = [
        QAItem(
            question="What mystery did the friends discover?",
            answer=mystery["premise"],
        ),
        QAItem(
            question="What clue helped them understand the mechanism?",
            answer=mystery["clue"],
        ),
        QAItem(
            question="What danger did the mechanism protect against?",
            answer=mystery["danger"],
        ),
        QAItem(
            question="How did the friends solve the mystery safely?",
            answer=mystery["change"],
        ),
        QAItem(
            question="What was the cautionary twist?",
            answer=mystery["twist"],
        ),
        QAItem(
            question="What lesson did the friends learn?",
            answer=f"They learned that {mystery['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, open, close, or signal.",
        ),
        QAItem(
            question="Why is friendship useful during a mystery?",
            answer="A good friend can notice details, ask careful questions, and help someone choose a safe action.",
        ),
        QAItem(
            question="Why should people be cautious with unknown objects?",
            answer="An unknown object may have a purpose or protect something important, so observing first can prevent harm.",
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
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(
                f"{key}: {entity.label} meters={entity.meters} memes={entity.memes}"
            )
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show resolved/1.\n"
                "#show safe_choice/1.\n"
                "#show lesson_learned/1.\n"
                "#show friendship/2."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, mystery_name in enumerate(MYSTERIES):
            params = StoryParams(
                place=list(PLACE_REGISTRY)[index % len(PLACE_REGISTRY)],
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                friend_name=FRIEND_NAMES[index % len(FRIEND_NAMES)],
                mystery=mystery_name,
                telling_mode=TELLING_MODES[index % len(TELLING_MODES)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
