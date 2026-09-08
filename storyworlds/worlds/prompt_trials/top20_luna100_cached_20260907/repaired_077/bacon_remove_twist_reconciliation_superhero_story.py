#!/usr/bin/env python3
"""
A small superhero story world about bacon, a careful removal, a twist,
and reconciliation.
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
    hero_name: str
    friend_name: str
    place: str
    power: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Character
    friend: Character
    place: str
    power: str
    bacon_state: str = "stuck"
    trust_state: str = "strained"
    twist_revealed: bool = False
    reconciled: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Luna", "Mira", "Nova", "Pip", "Tess", "Rafi", "Sol", "Juno"]
PLACES = [
    "the moonlit city square",
    "the rooftop garden",
    "the bright rescue station",
    "the school playground",
    "the quiet corner of Star Street",
]
POWERS = [
    "glowing moonlight",
    "a silver shield",
    "super hearing",
    "a wind-whirling cape",
    "the power to make tiny stars sparkle",
]

SCENES = [
    {
        "title": "the breakfast beacon",
        "setup": "a strip of bacon slipped from a picnic plate and caught on the bell rope of the rescue station",
        "problem": "the rope could not ring, so everyone thought the hero had hidden the emergency bell",
        "risk": "pulling hard could tear the rope and leave the station unable to signal for help",
        "clue": "a tiny grease mark led from the picnic plate to the knot above the bell",
        "first_action": "accused the hero of hiding the bell and reached for the rope",
        "twist": "the bacon had not been placed there by the hero at all; a gust had carried it up while the hero was rescuing a lost kitten",
        "remove": "asked the crowd to step back, used a clean cloth and the silver shield to loosen the bacon, and carried it to a covered bin",
        "ending": "the bell rang clearly while the covered bin kept the bacon far from the rope",
    },
    {
        "title": "the cape-clasp mix-up",
        "setup": "a piece of bacon clung to the clasp of the hero's red cape after a community breakfast",
        "problem": "the friend believed the hero had used the cape to steal food from the celebration",
        "risk": "yanking at the clasp could tear the cape or make the hero stumble from the rooftop steps",
        "clue": "the bacon matched the shape of the plate that had tipped beside the stairs",
        "first_action": "shouted that the hero should remove the cape at once",
        "twist": "the bacon was stuck to the clasp by warm butter, and the hero had been carrying the cape while helping clean tables",
        "remove": "calmly removed the bacon with a napkin, checked the clasp, and returned the cape to its hook",
        "ending": "the clean cape fluttered from the hook as the breakfast tables stood ready for everyone",
    },
    {
        "title": "the villain-looking lunchbox",
        "setup": "a bacon-shaped sticker covered the lock on a lunchbox beside the playground gate",
        "problem": "the friend thought the hero had sealed the gate to keep everyone out",
        "risk": "forcing the lock could break the lunchbox and scatter food near the busy path",
        "clue": "the sticker peeled away to reveal the real combination written beneath it",
        "first_action": "blamed the hero and tried to pry the lock open",
        "twist": "the sticker had been placed by a younger child who wanted the lunchbox to look like a superhero gadget",
        "remove": "stopped the prying, removed the sticker gently, and asked the child who had decorated the box",
        "ending": "the lunchbox opened safely, and the gate remained clear for every player",
    },
    {
        "title": "the smoky signal",
        "setup": "a strip of bacon warmed on a camp stove and made a smoky curl near the hero's signal mirror",
        "problem": "the friend thought the hero had started a fire without telling anyone",
        "risk": "smoke near the dry tents could frighten campers and hide a real warning",
        "clue": "the stove was still warm, while the signal mirror was clean and cold",
        "first_action": "told everyone to run from the hero's camp",
        "twist": "the smoke came from the breakfast stove, not from the hero's signal mirror",
        "remove": "turned off the stove with an adult, removed the bacon to a safe plate, and opened the clear air flap",
        "ending": "the smoke faded, and the mirror flashed a bright, honest signal across the field",
    },
    {
        "title": "the robot dog rescue",
        "setup": "a bacon wrapper wound around the wheel of a little robot dog used in a rescue drill",
        "problem": "the friend believed the hero had broken the robot during a race",
        "risk": "pulling the wrapper while the wheel was turning could damage the robot or pinch a finger",
        "clue": "the wrapper's printed corner matched the snack table beside the track",
        "first_action": "accused the hero and reached toward the moving wheel",
        "twist": "the wrapper had blown onto the track after the robot passed the snack table",
        "remove": "switched off the robot, removed the wrapper with a tool, and placed it in the recycling bin",
        "ending": "the robot dog rolled again, carrying a tiny flag that read HELPERS WORK TOGETHER",
    },
]

OPENINGS = [
    "At sunrise, the city expected a quiet day, but",
    "When the first star faded above the rooftops,",
    "During the neighborhood's cheerful breakfast,",
    "Just as the hero finished a morning rescue,",
    "The day began with bright capes and warm plates until",
]

DIALOGUE = [
    "\"You did this!\" said {friend}. \"Wait,\" said {hero}. \"Let's find out before we blame anyone.\"",
    "\"Remove it now!\" cried {friend}. \"I will,\" said {hero}, \"but safely, and with you watching.\"",
    "\"I thought you caused the trouble,\" said {friend}. \"I understand,\" replied {hero}. \"Let the clue speak first.\"",
    "\"Can you forgive my quick guess?\" asked {friend}. \"Yes,\" said {hero}. \"You helped me make the safe choice.\"",
]

LESSONS = [
    "A real superhero does not rush to blame; a real superhero protects people while checking the facts.",
    "The strongest power that day was not a cape or a shield, but the courage to listen and repair trust.",
    "Removing a problem safely mattered, but reconciling afterward made the team strong again.",
    "A twist can change a story, and an honest apology can change what happens next.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bacon removal superhero story world.")
    parser.add_argument("--hero-name", choices=NAMES)
    parser.add_argument("--friend-name", choices=NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--power", choices=POWERS)
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
    hero = args.hero_name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([name for name in NAMES if name != hero])
    return StoryParams(
        hero_name=hero,
        friend_name=friend,
        place=args.place or rng.choice(PLACES),
        power=args.power or rng.choice(POWERS),
    )


def _reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name == params.friend_name:
        raise StoryError("The superhero and friend need different names.")
    if params.place not in PLACES:
        raise StoryError("That place is not part of this superhero world.")
    if params.power not in POWERS:
        raise StoryError("That power is not available in this story world.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    scene = rng.choice(SCENES)
    opening = rng.choice(OPENINGS)
    exchange = rng.choice(DIALOGUE).format(hero=params.hero_name, friend=params.friend_name)
    lesson = rng.choice(LESSONS)

    hero = Character(
        name=params.hero_name,
        kind="superhero",
        meters={"courage": 1.0, "care": 1.0},
        memes={"protector": 1.0, "listener": 1.0},
    )
    friend = Character(
        name=params.friend_name,
        kind="helper",
        meters={"trust": 0.8, "worry": 0.4},
        memes={"honest": 1.0},
    )
    world = World(hero=hero, friend=friend, place=params.place, power=params.power)

    lines = [
        f"{opening} {scene['setup']}.",
        f"{params.hero_name}, known for {params.power}, was nearby when {scene['problem']}.",
        f"The danger was clear: {scene['risk']}.",
        exchange,
        f"Before anyone could make the trouble worse, {params.hero_name} paused and said, \"We can remove the problem without hurting anyone.\"",
        f"Together they looked closely. {scene['clue']}.",
        f"Then came the twist: {scene['twist']}.",
        f"{params.friend_name} lowered their voice. \"I was wrong to blame you,\" they said.",
        f"{params.hero_name} smiled. \"Thank you for telling me. We still have a job to do.\"",
        f"Carefully, {scene['remove']}.",
        f"The bacon was no longer in the dangerous place, and the signal, path, or machine was safe again.",
        f"{lesson}",
        f"By the end, {scene['ending']}.",
    ]

    world.bacon_state = "removed and safely contained"
    world.trust_state = "restored"
    world.twist_revealed = True
    world.reconciled = True
    world.facts.update(
        incident=scene["title"],
        risk=scene["risk"],
        clue=scene["clue"],
        twist=scene["twist"],
        removal=scene["remove"],
        ending=scene["ending"],
        story=" ".join(lines),
    )

    prompts = [
        f"Write a superhero story about {params.hero_name} removing bacon from danger.",
        f"Show a twist in which {scene['problem']}.",
        f"End with reconciliation between {params.hero_name} and {params.friend_name}.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem did the bacon cause in {scene['title']}?",
            answer=f"The bacon caused trouble because {scene['problem']}.",
        ),
        QAItem(
            question="What danger did the heroes avoid?",
            answer=f"They avoided the danger that {scene['risk']}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {scene['twist']}.",
        ),
        QAItem(
            question="How was the bacon removed safely?",
            answer=f"The bacon was removed when {scene['remove']}.",
        ),
        QAItem(
            question=f"How did {params.hero_name} and {params.friend_name} reconcile?",
            answer=f"{params.friend_name} admitted the quick blame was wrong, and {params.hero_name} accepted the apology while they worked together safely.",
        ),
    ]

    world_qa = [
        QAItem(
            question="Why should bacon be removed from machinery or safety equipment?",
            answer="Bacon and its wrapper can block moving parts, make surfaces slippery, attract animals, or create smoke, so it should be removed safely.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that reveals the situation is different from what a character first believed.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means repairing a relationship after a disagreement through honesty, listening, apology, and changed actions.",
        ),
        QAItem(
            question="What should someone do before removing an object from a machine?",
            answer="They should stop or switch off the machine, keep hands away from moving parts, and ask a responsible adult or trained helper when needed.",
        ),
        QAItem(
            question="What makes someone a superhero in this story world?",
            answer="A superhero protects others, checks facts before blaming, solves problems carefully, and makes peace after mistakes.",
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
    if trace and sample.world:
        world = sample.world
        print("\n--- trace ---")
        print(f"hero={world.hero.name}, kind={world.hero.kind}, meters={world.hero.meters}, memes={world.hero.memes}")
        print(f"friend={world.friend.name}, kind={world.friend.kind}, meters={world.friend.meters}, memes={world.friend.memes}")
        print(
            f"place={world.place}, power={world.power}, bacon_state={world.bacon_state}, "
            f"trust_state={world.trust_state}, twist_revealed={world.twist_revealed}, reconciled={world.reconciled}"
        )
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
valid_power(P) :- power(P).
safe_removal :- bacon_present, removable.
twist :- bacon_present, wind_caused.
reconciled :- twist, apology, safe_removal.

#show valid_place/1.
#show valid_power/1.
#show safe_removal/0.
#show twist/0.
#show reconciled/0.
"""


def asp_facts() -> str:
    import asp
    facts = [asp.fact("place", place) for place in PLACES]
    facts += [asp.fact("power", power) for power in POWERS]
    facts += [
        asp.fact("bacon_present"),
        asp.fact("removable"),
        asp.fact("wind_caused"),
        asp.fact("apology"),
    ]
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_place/1.\n#show valid_power/1."))
    places = set(asp.atoms(model, "valid_place"))
    powers = set(asp.atoms(model, "valid_power"))
    expected_places = {(place,) for place in PLACES}
    expected_powers = {(power,) for power in POWERS}
    if places != expected_places or powers != expected_powers:
        print("MISMATCH between clingo registries and Python registries.")
        return 1
    for seed in range(8):
        params = StoryParams(
            hero_name=NAMES[seed % len(NAMES)],
            friend_name=NAMES[(seed + 1) % len(NAMES)],
            place=PLACES[seed % len(PLACES)],
            power=POWERS[seed % len(POWERS)],
            seed=seed,
        )
        sample = generate(params)
        if not sample.story or "bacon" not in sample.story.lower():
            print("Generated-story verification failed.")
            return 1
    print("OK: ASP registries and generated stories passed verification.")
    return 0


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(
                hero_name=NAMES[index % len(NAMES)],
                friend_name=NAMES[(index + 1) % len(NAMES)],
                place=PLACES[index % len(PLACES)],
                power=POWERS[index % len(POWERS)],
            )
            for index in range(len(SCENES))
        ]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + index)) for index in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_place/1.\n#show valid_power/1.\n#show safe_removal/0.\n#show twist/0.\n#show reconciled/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_place/1.\n#show valid_power/1.\n#show safe_removal/0.\n#show twist/0.\n#show reconciled/0."))
        for name in ("valid_place", "valid_power", "safe_removal", "twist", "reconciled"):
            for atom in asp.atoms(model, name):
                print(name if not atom else f"{name}{atom}")
        return

    samples = []
    for index, params in enumerate(generation_params(args)):
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
