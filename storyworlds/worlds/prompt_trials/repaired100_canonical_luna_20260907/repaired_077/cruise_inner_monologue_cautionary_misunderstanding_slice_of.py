#!/usr/bin/env python3
"""
A small slice-of-life cruise story about an inner worry, a cautionary clue,
and a misunderstanding repaired with calm questions.
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


@dataclass
class Character:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    child_name: str
    companion_name: str
    deck: str
    weather: str
    seed: Optional[int] = None


@dataclass
class World:
    child: Character
    companion: Character
    deck: str
    weather: str
    cruise: str = "steady"
    misunderstanding: bool = False
    caution_heard: bool = False
    repaired: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Luna", "Milo", "Nori", "Tavi", "Suri", "Pip", "Mina", "Ollie"]
DECKS = ["the quiet observation deck", "the family deck", "the covered promenade", "the little aft deck"]
WEATHER = ["bright wind", "soft rain", "a hazy afternoon", "clear evening air"]

SCENES = [
    {
        "title": "the wet deck sign",
        "setup": "a yellow caution sign stood beside a damp patch near the rail",
        "mistake": "the sign looked to the child like a marker for the best place to watch the waves",
        "risk": "the wet deck could make someone slip, especially when the ship moved",
        "first_try": "started toward the bright sign",
        "clue": "the sign showed a person slipping and the words WAIT UNTIL DRY",
        "helper_action": "pointed to the painted footprints that led around the damp boards",
        "fix": "stopped, told a crew member, and took the dry path around the patch",
        "ending": "the caution sign remained beside the drying boards while the cruise carried everyone toward a silver horizon",
    },
    {
        "title": "the closed stairway",
        "setup": "a rope blocked one stairway while a small caution card hung from the rail",
        "mistake": "the child thought the rope marked a secret shortcut to the lower deck",
        "risk": "the stairs were being cleaned, and stepping through could cause a fall or interrupt the crew",
        "first_try": "reached for the rope",
        "clue": "the card showed a mop and said USE THE OTHER STAIRS",
        "helper_action": "noticed a crew member carrying a bucket below the landing",
        "fix": "asked the crew member, followed the open route, and left the rope in place",
        "ending": "the rope stayed closed as the proper stairs brought them safely beside the warm dining room",
    },
    {
        "title": "the lifebuoy misunderstanding",
        "setup": "a bright orange lifebuoy rested in its holder beside the rail",
        "mistake": "the child believed it was a giant ring meant for a cruise game",
        "risk": "safety equipment must remain ready for an emergency and should never be used as a toy",
        "first_try": "began lifting the lifebuoy from its holder",
        "clue": "a label said FOR EMERGENCY USE and an arrow pointed toward the water",
        "helper_action": "explained that the ring could help a person in the sea",
        "fix": "returned the lifebuoy, apologized, and chose a soft deck game away from the safety station",
        "ending": "the orange ring stayed ready by the rail while a paper ship sailed across their game mat",
    },
    {
        "title": "the windy hat",
        "setup": "a loose sun hat skittered across the deck near a notice about strong wind",
        "mistake": "the child thought the hat belonged to a playful passenger hiding behind the chairs",
        "risk": "chasing loose objects near the rail could make someone stumble or lean somewhere unsafe",
        "first_try": "hurried after the hat",
        "clue": "the notice said HOLD LOOSE ITEMS and the hat had a name tag inside",
        "helper_action": "caught the hat with a towel far from the rail",
        "fix": "walked instead of running, gave the hat to the crew, and held their own cap securely",
        "ending": "the wind tugged at the flags while every hat on the deck stayed safely on a head or in a bag",
    },
    {
        "title": "the quiet-door question",
        "setup": "a plain door beside the promenade had a sign asking passengers to keep it closed",
        "mistake": "the child guessed that the door led to a secret room where the cruise musicians practiced",
        "risk": "opening an unmarked service door could let someone enter a busy work area",
        "first_try": "put a hand on the handle",
        "clue": "the sign showed a service cart and said CREW AREA",
        "helper_action": "heard dishes clinking on the other side",
        "fix": "let go of the handle, asked a crew member about the music, and listened from the public lounge",
        "ending": "the service door stayed shut while a real song floated from the open lounge nearby",
    },
]

OPENINGS = [
    "The cruise had been ordinary until",
    "During a quiet hour of the cruise,",
    "After breakfast on the ship,",
    "As the cruise moved through calm water,",
    "Near the middle of the afternoon cruise,",
]

THOUGHTS = [
    "Inside, {child} thought, 'If I hurry, I can fix this before anyone notices.'",
    "A worried thought tapped at {child}'s mind: 'Maybe I should not ask and look silly.'",
    "{child} wondered, 'What if the sign means something completely different?'",
    "For one small moment, {child} thought, 'The exciting explanation must be the true one.'",
    "{child}'s inner voice whispered, 'Stop first. Look again.'",
]

RESPONSES = [
    "\"I thought it meant something else,\" {child} admitted. \"Can we check before I move?\"",
    "\"I made a guess,\" {child} said. \"What does the sign really tell us?\"",
    "\"Thank you for stopping me,\" {child} replied. \"I want to choose the safe path.\"",
    "\"I was curious,\" {child} explained. \"I did not mean to make the deck unsafe.\"",
]

LESSONS = [
    "The cruise taught {child} that a caution sign was a helpful message, not a mystery to ignore.",
    "{child} learned that an exciting guess should wait until the plain facts have been checked.",
    "The small misunderstanding became useful: stopping to ask can protect people and equipment.",
    "Being cautious did not spoil the cruise; it made room for a calmer adventure.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life cautionary cruise story world.")
    ap.add_argument("--child-name", choices=NAMES)
    ap.add_argument("--companion-name", choices=NAMES)
    ap.add_argument("--deck", choices=DECKS)
    ap.add_argument("--weather", choices=WEATHER)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child_name or rng.choice(NAMES)
    companion = args.companion_name or rng.choice([n for n in NAMES if n != child])
    return StoryParams(
        child_name=child,
        companion_name=companion,
        deck=args.deck or rng.choice(DECKS),
        weather=args.weather or rng.choice(WEATHER),
    )


def _reasonableness_gate(params: StoryParams) -> None:
    if params.child_name == params.companion_name:
        raise StoryError("The child and companion need different names.")
    if params.deck not in DECKS:
        raise StoryError("That deck is not part of this cruise.")
    if params.weather not in WEATHER:
        raise StoryError("That weather does not belong in this small cruise story.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    scene = rng.choice(SCENES)
    opening = rng.choice(OPENINGS)
    thought = rng.choice(THOUGHTS).format(child=params.child_name)
    response = rng.choice(RESPONSES).format(child=params.child_name)
    lesson = rng.choice(LESSONS).format(child=params.child_name)
    coda = rng.choice([
        "Then they watched the wake curl behind the ship.",
        "After that, even the ordinary doors and rails seemed worth noticing.",
        "Their next walk was slower, but it was still full of interesting things to see.",
        "The companion smiled, and the two of them returned to the view.",
    ])

    child = Character(
        name=params.child_name,
        kind="child",
        meters={"distance_from_risk": 0.4, "calm": 0.5},
        memes={"curious": 1.0, "careful": 0.4},
    )
    companion = Character(
        name=params.companion_name,
        kind="companion",
        meters={"distance_from_risk": 1.0, "calm": 0.8},
        memes={"helpful": 1.0, "patient": 1.0},
    )
    world = World(
        child=child,
        companion=companion,
        deck=params.deck,
        weather=params.weather,
        misunderstanding=True,
        facts={
            "scene": scene["title"],
            "risk": scene["risk"],
            "clue": scene["clue"],
            "repair": scene["fix"],
        },
    )

    lines = [
        f"{params.child_name} was on a cruise with {params.companion_name}, enjoying {params.weather} from {params.deck}.",
        f"{opening} {scene['setup']}.",
        f"{params.child_name} misunderstood it: {scene['mistake']}.",
        thought,
        f"Without checking, {params.child_name} {scene['first_try']}.",
        f"{params.companion_name} gently said, \"Let's pause and read it together.\"",
        f"{params.child_name} answered, {response}",
        f"Then {params.companion_name} {scene['helper_action']}.",
        f"The important clue was simple: {scene['clue']}.",
        f"That caution mattered because {scene['risk']}.",
        f"{params.child_name} took a breath and {scene['fix']}.",
        lesson,
        coda,
        f"By sunset, {scene['ending']}",
    ]

    child.meters["distance_from_risk"] = 1.0
    child.meters["calm"] = 1.0
    child.memes["careful"] = 1.0
    world.caution_heard = True
    world.repaired = True
    world.cruise = "steady and safe"
    world.facts["ending"] = scene["ending"]
    world.facts["lesson"] = lesson
    world.facts["story"] = " ".join(lines)

    prompts = [
        f"Write a slice-of-life cruise story called {scene['title']} about a small misunderstanding.",
        f"Tell a cautionary story set on {params.deck} where a clue changes {params.child_name}'s decision.",
        f"Include an inner monologue, a brief dialogue, and a safe repair during a cruise.",
    ]

    story_qa = [
        QAItem(
            question=f"What did {params.child_name} misunderstand in the story?",
            answer=f"{params.child_name} misunderstood the scene because {scene['mistake']}.",
        ),
        QAItem(
            question="What cautionary clue changed the first guess?",
            answer=f"The clue was that {scene['clue']}.",
        ),
        QAItem(
            question=f"How did {params.companion_name} help?",
            answer=f"{params.companion_name} {scene['helper_action']} and encouraged {params.child_name} to check the sign.",
        ),
        QAItem(
            question=f"How did {params.child_name} repair the problem?",
            answer=f"{params.child_name} {scene['fix']}.",
        ),
        QAItem(
            question="What did the inner monologue reveal?",
            answer="It revealed that the child felt worried and curious, but could choose to pause and check before acting.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a cruise?",
            answer="A cruise is a journey on a ship, often with passengers visiting places or enjoying time on the water.",
        ),
        QAItem(
            question="Why should people obey caution signs on a ship?",
            answer="Caution signs point out risks such as wet floors, closed routes, strong wind, or work areas, so following them helps prevent injuries.",
        ),
        QAItem(
            question="What should someone do when a sign is confusing?",
            answer="They should stop, read it carefully, and ask a responsible adult or crew member before moving or entering anything.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gives the wrong meaning to what they see or hear.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private stream of thoughts a character has inside their mind.",
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
        w = sample.world
        print("\n--- trace ---")
        print(f"child={w.child.name}, kind={w.child.kind}, meters={w.child.meters}, memes={w.child.memes}")
        print(f"companion={w.companion.name}, kind={w.companion.kind}, meters={w.companion.meters}, memes={w.companion.memes}")
        print(f"deck={w.deck}, weather={w.weather}, cruise={w.cruise}")
        print(f"misunderstanding={w.misunderstanding}, caution_heard={w.caution_heard}, repaired={w.repaired}")
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


ASP_RULES = r"""
valid_deck(D) :- deck(D).
valid_weather(W) :- weather(W).
safe_cruise :- valid_deck(D), valid_weather(W).
cautionary_scene :- safe_cruise.
repaired_misunderstanding :- cautionary_scene.
#show valid_deck/1.
#show valid_weather/1.
#show safe_cruise/0.
#show cautionary_scene/0.
#show repaired_misunderstanding/0.
"""


def asp_facts() -> str:
    import asp
    facts = [asp.fact("deck", deck) for deck in DECKS]
    facts += [asp.fact("weather", weather) for weather in WEATHER]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    expected_decks = {("valid_deck", deck) for deck in DECKS}
    expected_weather = {("valid_weather", weather) for weather in WEATHER}
    model = asp.one_model(asp_program())
    actual_decks = {("valid_deck", row[0]) for row in asp.atoms(model, "valid_deck")}
    actual_weather = {("valid_weather", row[0]) for row in asp.atoms(model, "valid_weather")}
    if actual_decks != expected_decks or actual_weather != expected_weather:
        print("MISMATCH between ASP and Python registries.")
        return 1
    for seed in range(5):
        params = StoryParams(
            child_name=NAMES[seed],
            companion_name=NAMES[(seed + 1) % len(NAMES)],
            deck=DECKS[seed % len(DECKS)],
            weather=WEATHER[seed % len(WEATHER)],
            seed=seed,
        )
        sample = generate(params)
        if not sample.story or not sample.story.endswith("."):
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP/Python parity holds for {len(DECKS)} decks and {len(WEATHER)} weather choices.")
    return 0


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(
                child_name=NAMES[i % len(NAMES)],
                companion_name=NAMES[(i + 1) % len(NAMES)],
                deck=DECKS[i % len(DECKS)],
                weather=WEATHER[i % len(WEATHER)],
            )
            for i in range(len(SCENES))
        ]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        for atom in model:
            print(atom)
        return

    samples = []
    base = args.seed if args.seed is not None else 0
    for i, params in enumerate(generation_params(args)):
        params.seed = base + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
