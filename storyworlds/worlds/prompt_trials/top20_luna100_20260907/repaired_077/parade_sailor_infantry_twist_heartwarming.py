#!/usr/bin/env python3
"""
A heartwarming little story world about a parade, a sailor, and an infantry
drummer whose quiet twist helps everyone march together.
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

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAMES = ["Luna", "Mara", "Pip", "Niko", "Tess", "Owen", "Suri", "Bea"]
SAILOR_NAMES = ["Ari", "Jo", "Mina", "Theo", "Rae", "Sol"]
PLACES = [
    "the town square",
    "the harbor road",
    "the school field",
    "the riverside park",
    "the old train station",
]
WEATHER = ["a bright morning", "a breezy morning", "a cool golden morning", "a warm cloudy morning"]


@dataclass
class Character:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    sailor_name: str
    place: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Character
    sailor: Character
    infantry: Character
    place: str
    parade_ready: bool = False
    problem: str = ""
    twist: str = ""
    heart_changed: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


TWISTS = [
    {
        "problem": "a small wheel on the sailor's bright signal cart came loose",
        "risk": "the cart could roll into the marching children if nobody stopped it",
        "clue": "the cart's flag leaned toward the curb while its wheel made a soft click",
        "first_action": "tried to hide the broken wheel beneath a folded banner",
        "twist": "the sailor had been carrying the cart for the parade captain, but the captain's own little brother had made the loose pin while decorating it",
        "fix": "asked the infantry drummer to guard the crossing, then helped the sailor secure the wheel with a spare leather strap",
        "ending": "the cart rolled safely at the back of the parade, its flag waving beside the sailor's grateful smile",
        "lesson": "A parade becomes stronger when people tell the truth about a small problem before it grows.",
    },
    {
        "problem": "the sailor's song sheet blew beneath the boots of the waiting infantry",
        "risk": "the march could begin with the wrong tune and leave the youngest walkers confused",
        "clue": "one corner of the sheet was caught on a red parade ribbon",
        "first_action": "guessed that the sailor had forgotten the music",
        "twist": "the sailor had not lost the song at all; they had been teaching the melody to a shy child who could not yet read",
        "fix": "knelt beside the child, found the sheet, and invited the child to hum the opening while the infantry kept a gentle beat",
        "ending": "the whole parade entered the square behind a child's brave humming",
        "lesson": "Sometimes the quietest helper is already holding the first note of a beautiful surprise.",
    },
    {
        "problem": "a little flag from the infantry line disappeared before the parade began",
        "risk": "the missing flag could make one marcher feel forgotten and break the careful line",
        "clue": "blue thread led from the empty flagpole to a bench near the sailor's sea chest",
        "first_action": "blamed the wind and began searching the wrong side of the street",
        "twist": "the sailor had found the flag first and tucked it away because its torn edge reminded them of a friend who had once marched with it",
        "fix": "listened to the sailor's memory, stitched the flag with bright thread, and returned it to the infantry marcher",
        "ending": "the repaired flag rose higher than the others, carrying both an old memory and a new beginning",
        "lesson": "A tender memory need not stop a celebration; it can help people carry one another forward.",
    },
    {
        "problem": "the youngest infantry marcher froze when the drums sounded too loudly",
        "risk": "the child might run into the street or feel too frightened to join the parade",
        "clue": "the child's hand reached toward the sailor's quiet brass whistle instead of the booming drums",
        "first_action": "suggested leaving the child behind the parade tent",
        "twist": "the sailor had brought the whistle for exactly this moment because they too had once been afraid of their first marching day",
        "fix": "let the child walk beside the sailor while the infantry drummer changed to a soft heartbeat rhythm",
        "ending": "the child took three brave steps, then marched proudly beside the sailor under the fluttering flags",
        "lesson": "Courage can begin with one gentle sound and a person who remembers being afraid.",
    },
    {
        "problem": "the parade route's welcome sign had fallen face-down in a puddle",
        "risk": "visitors might miss the turn and the town's careful celebration could seem empty",
        "clue": "the sailor's polished bootprints ended beside the fallen sign",
        "first_action": "thought the sailor had knocked it down while carrying a heavy rope",
        "twist": "the sailor had lowered the sign on purpose to shelter a tiny bird from the rain",
        "fix": "moved the sign to a dry post, placed a small box beneath the bench for the bird, and asked the infantry to guide guests",
        "ending": "the sign pointed the way as the parade passed, while the rescued bird chirped from its dry little box",
        "lesson": "Making room for a small life can make a whole celebration feel kinder.",
    },
]

OPENINGS = [
    "On the morning of the town parade,",
    "When the first flags lifted over the street,",
    "Just before the band gathered in the square,",
    "As sunlight touched the harbor bells,",
    "On a morning made for marching,",
]

CLOSINGS = [
    "After the last flag passed, everyone stayed to share warm rolls and stories.",
    "The parade ended, but the new friendship kept pace all the way home.",
    "Even the tired drums seemed to smile as the square filled with grateful voices.",
    "That evening, the repaired things shone more brightly than anything brand new.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming parade, sailor, and infantry story world.")
    parser.add_argument("--hero-name", choices=NAMES)
    parser.add_argument("--sailor-name", choices=SAILOR_NAMES)
    parser.add_argument("--place", choices=PLACES)
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
    hero_name = args.hero_name or rng.choice(NAMES)
    sailor_name = args.sailor_name or rng.choice([name for name in SAILOR_NAMES if name != hero_name])
    place = args.place or rng.choice(PLACES)
    return StoryParams(hero_name=hero_name, sailor_name=sailor_name, place=place)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name == params.sailor_name:
        raise StoryError("The storyteller and sailor need different names.")
    if params.place not in PLACES:
        raise StoryError("That place is not one of the parade's possible routes.")
    if not params.hero_name or not params.sailor_name:
        raise StoryError("Both the storyteller and sailor need names.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    event = rng.choice(TWISTS)
    opening = rng.choice(OPENINGS)
    weather = rng.choice(WEATHER)
    closing = rng.choice(CLOSINGS)

    hero = Character(
        name=params.hero_name,
        kind="young parade helper",
        meters={"energy": 0.7, "distance_to_sailor": 3.0},
        memes={"curiosity": 0.9, "kindness": 0.8},
    )
    sailor = Character(
        name=params.sailor_name,
        kind="sailor",
        meters={"energy": 0.6, "distance_to_route": 1.0},
        memes={"steadiness": 0.9, "tenderness": 0.8},
    )
    infantry = Character(
        name="the infantry drummer",
        kind="infantry",
        meters={"marching_distance": 0.0},
        memes={"discipline": 0.9, "patience": 0.8},
    )
    world = World(hero=hero, sailor=sailor, infantry=infantry, place=params.place)
    world.problem = event["problem"]
    world.twist = event["twist"]

    story_lines = [
        f"{opening} {weather} rested over {params.place}, where {params.hero_name} watched a sailor named {params.sailor_name} prepare the flags.",
        f"The infantry waited nearby, polished and patient, while the parade crowd gathered along the route.",
        f"Then {event['problem']}.",
        f"{params.hero_name} saw the danger: {event['risk']}.",
        f"At first, {params.hero_name} {event['first_action']}.",
        f'"Wait," said {params.sailor_name}. "Before we blame anyone, let us look closely."',
        f'"The clue is here," {params.hero_name} replied, pointing out that {event["clue"]}.',
        f"The clue revealed a surprising twist: {event['twist']}.",
        f'"I did not know that," said {params.hero_name}. "What can I do?"',
        f'"Stay with me," said {params.sailor_name}. "We can mend this together."',
        f"With the infantry drummer keeping watch, {params.hero_name} {event['fix']}.",
        f"The parade captain thanked them, and the sailor's shoulders relaxed.",
        event["lesson"],
        closing,
        f"By the time the parade moved through {params.place}, {event['ending']}.",
    ]

    world.parade_ready = True
    world.heart_changed = True
    world.facts.update(
        {
            "problem": event["problem"],
            "risk": event["risk"],
            "clue": event["clue"],
            "twist": event["twist"],
            "repair": event["fix"],
            "lesson": event["lesson"],
            "ending": event["ending"],
        }
    )
    world.facts["story"] = " ".join(story_lines)

    prompts = [
        f"Write a heartwarming parade story about {params.hero_name}, a sailor named {params.sailor_name}, and infantry helpers.",
        f"Include a gentle twist in which the first assumption about {event['problem']} changes after a clue is noticed.",
        f"End with a concrete image showing how the parade and the characters have changed.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem happened before the parade in {params.place}?",
            answer=f"Before the parade, {event['problem']}.",
        ),
        QAItem(
            question=f"What clue helped {params.hero_name} understand the problem?",
            answer=f"The clue was that {event['clue']}.",
        ),
        QAItem(
            question="What was the story's twist?",
            answer=f"The twist was that {event['twist']}.",
        ),
        QAItem(
            question=f"How did {params.hero_name} and the sailor repair the situation?",
            answer=f"They repaired it when {params.hero_name} {event['fix']}.",
        ),
        QAItem(
            question="What showed that the parade ended safely?",
            answer=f"It ended safely because {event['ending']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people walk, perform, or display flags and other decorations for an audience.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works or travels on the water and learns to handle boats, ropes, weather, and life with a crew.",
        ),
        QAItem(
            question="What does infantry mean?",
            answer="Infantry are soldiers who serve as ground troops and move on foot, often working together in an organized group.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in understanding that reveals an important fact and changes what the characters decide to do.",
        ),
        QAItem(
            question="How can kindness help during a difficult moment?",
            answer="Kindness can make people feel safe enough to tell the truth, ask for help, and work together on a careful solution.",
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        world = sample.world
        print("\n--- trace ---")
        print(f"hero={world.hero.name}, kind={world.hero.kind}, meters={world.hero.meters}, memes={world.hero.memes}")
        print(f"sailor={world.sailor.name}, kind={world.sailor.kind}, meters={world.sailor.meters}, memes={world.sailor.memes}")
        print(f"infantry={world.infantry.kind}, meters={world.infantry.meters}, memes={world.infantry.memes}")
        print(f"place={world.place}, parade_ready={world.parade_ready}, heart_changed={world.heart_changed}")
        print(f"problem={world.problem}")
        print(f"twist={world.twist}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_role(sailor).
valid_role(infantry).
valid_role(parade_helper).
parade_can_start :- valid_place(P), valid_role(sailor), valid_role(infantry), valid_role(parade_helper).
#show valid_place/1.
#show valid_role/1.
#show parade_can_start/0.
"""


def asp_facts() -> str:
    import asp
    facts = [asp.fact("place", place) for place in PLACES]
    facts.extend(asp.fact("role", role) for role in ("sailor", "infantry", "parade_helper"))
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_place/1.\n#show valid_role/1.\n#show parade_can_start/0."))
    places = set(asp.atoms(model, "valid_place"))
    roles = set(asp.atoms(model, "valid_role"))
    starts = set(asp.atoms(model, "parade_can_start"))
    expected_places = {(place,) for place in PLACES}
    expected_roles = {("sailor",), ("infantry",), ("parade_helper",)}
    if places != expected_places or roles != expected_roles or starts != {()}:
        print("MISMATCH between ASP and Python registries.")
        return 1
    for seed in range(8):
        params = StoryParams(
            hero_name=NAMES[seed % len(NAMES)],
            sailor_name=SAILOR_NAMES[seed % len(SAILOR_NAMES)],
            place=PLACES[seed % len(PLACES)],
            seed=seed,
        )
        sample = generate(params)
        if not sample.story or "parade" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP parity and generated stories verified ({len(PLACES)} places, 3 roles).")
    return 0


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(
                hero_name=NAMES[index % len(NAMES)],
                sailor_name=SAILOR_NAMES[index % len(SAILOR_NAMES)],
                place=place,
                seed=index,
            )
            for index, place in enumerate(PLACES)
        ]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + index)) for index in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_place/1.\n#show valid_role/1.\n#show parade_can_start/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_place/1.\n#show valid_role/1.\n#show parade_can_start/0."))
        for predicate in ("valid_place", "valid_role", "parade_can_start"):
            for atom in asp.atoms(model, predicate):
                print(f"{predicate}{atom}")
        return

    samples: list[StorySample] = []
    for index, params in enumerate(generation_params(args)):
        if params.seed is None:
            params.seed = (args.seed if args.seed is not None else 0) + index
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
