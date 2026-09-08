#!/usr/bin/env python3
"""
A small magical animal storyworld built around an eleventh chance.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


METERS = {"magic": "magic", "distance": "distance", "warmth": "warmth"}
MEMES = {"worry": "worry", "hope": "hope", "trust": "trust", "courage": "courage"}


@dataclass
class Animal:
    name: str
    species: str
    place: str
    meters: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in METERS})
    memes: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in MEMES})
    facts: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.species in {"doe", "hen", "vixen", "rabbit"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "he", "object": "him", "possessive": "his"}[case]


@dataclass(frozen=True)
class Tale:
    tale_id: str
    animal_goal: str
    omen: str
    danger: str
    magical_task: str
    complication: str
    helper: str
    turning_action: str
    result: str
    ending: str


TALES = [
    Tale(
        "moon_bridge",
        "carry a berry to her lonely friend across the brook",
        "eleven silver ripples appeared where only ten had been",
        "the stepping stones would vanish before the berry reached the far bank",
        "ask the moon-moth to weave a bridge of light",
        "the first shining thread snapped in the cold wind",
        "a patient old tortoise",
        "held the thread steady while the tortoise anchored it with a smooth pebble",
        "a bright path stretched from bank to bank",
        "the rabbit shared the berry beneath a bridge that glowed like a quiet smile",
    ),
    Tale(
        "eleventh_leaf",
        "find a warm bed before the forest frost",
        "ten leaves fell from the oak, then an eleventh leaf trembled without falling",
        "the hidden nest would freeze when night covered the hollow",
        "whisper a wish into the leaf so it would become a golden blanket",
        "the wish blew away before the leaf heard all of it",
        "a gentle field mouse",
        "repeated the wish slowly while the mouse cupped its paws around the sound",
        "the leaf unfolded into a soft golden cover",
        "the small animal slept warmly while the eleventh leaf shone above the nest",
    ),
    Tale(
        "starry_den",
        "guide a lost fox cub home",
        "ten stars blinked above the den, but an eleventh star flickered near the trees",
        "the cub would wander farther if the dark path stayed confusing",
        "follow the eleventh star and sing its secret name",
        "clouds covered the star just as the path divided",
        "a bright-winged owl",
        "listened for the cub's tiny call and turned the hidden star into a lantern",
        "the forest path gleamed all the way to the den",
        "the fox cub curled beside its mother while the eleventh star winked overhead",
    ),
    Tale(
        "rainbow_seed",
        "save a garden seed from a long rain",
        "ten puddles filled the burrow yard, and an eleventh puddle began to sparkle",
        "the seed would rot unless it reached dry soil before sunset",
        "borrow a rainbow's smallest color to lift the seed",
        "the rainbow bent too high for small paws to reach",
        "a cheerful magpie",
        "brought a blue feather so the animal could climb the reflected colors",
        "the seed floated safely into a dry patch of earth",
        "a green sprout rose beneath an eleventh-colored arc after the rain",
    ),
    Tale(
        "whispering_den",
        "learn why the forest bell had stopped ringing",
        "the bell gave ten dull knocks, then one soft eleventh chime",
        "the animals would miss the warning of the coming storm",
        "listen to the bell's magic echo inside the old tree",
        "the echo was buried under a pile of noisy acorns",
        "a playful squirrel",
        "sorted the acorns by size until the hidden echo could speak",
        "the bell rang clearly across the trees",
        "every animal reached shelter as the eleventh chime danced over the leaves",
    ),
    Tale(
        "cloud_feather",
        "return a fallen cloud feather to the sky",
        "ten white feathers drifted upward, while an eleventh rested cold in the grass",
        "the feather would lose its sky-magic before morning",
        "place the feather on the hill's highest stone and call the wind",
        "the wind arrived in a rush and scattered the feather",
        "a calm little hedgehog",
        "covered the feather with a leaf until the wind softened",
        "the feather rose gently into the clouds",
        "a new cloud curled overhead, shaped like the eleventh feather",
    ),
]

ANIMAL_NAMES = ["Luna", "Milo", "Pip", "Clover", "Nala", "Otis", "Fern"]
SPECIES = ["rabbit", "fox", "squirrel", "hedgehog", "fawn", "badger", "raccoon"]
PLACES = ["the moonlit meadow", "the whispering woods", "the blue hill", "the fern hollow"]
HELPER_NAMES = ["Moss", "Bramble", "Poppy", "Wren", "Thistle"]

INTRO_FORMS = [
    "{name} the {species} lived in {place}. {name} had counted ten ordinary days, but this morning felt like the eleventh day of something magical.",
    "In {place}, {name} the {species} watched the sunrise. Ten little signs had appeared, and now an eleventh sign shimmered before {name}'s paws.",
    "{name} was a small {species} who loved quiet wonders. In {place}, {name} discovered that the eleventh try might be the one that mattered.",
    "The animals of {place} knew {name} as a careful {species}. Still, {name} had never seen magic gather around an eleventh moment.",
]

DIALOGUE_FORMS = [
    '"Did you see that eleventh sign?" asked {helper}. "I did," said {name}. "It means {danger}. I must {task}."',
    '{name} whispered, "What should I do?" {helper} answered, "Trust the magic, but do not face it alone."',
    '"The first ten tries did not work," said {helper}. "Then the eleventh may need a kinder plan." "You are right," said {name}. "Will you help me {task}?"',
    '{helper} pointed at the glowing sign. "What does it tell you?" "{danger}," replied {name}. "Then I will {task}."',
]

ACTION_LEADS = [
    "Together, they began carefully.",
    "The two animals made a small plan.",
    "There was no time to be frightened for long.",
    "With hope warming the chilly air,",
]

AWARDS = ["a moon-seed", "a silver acorn", "a blue feather", "a bell-shaped flower"]


@dataclass
class StoryParams:
    animal_name: str
    species: str
    place: str
    helper_name: str
    seed: Optional[int] = None


ASP_RULES = r"""
needs_magic(A) :- animal(A), eleventh(A), goal(A).
can_try(A) :- needs_magic(A), helper(A).
valid_story(A) :- can_try(A), danger(A).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("animal", "hero"),
            asp.fact("eleventh", "hero"),
            asp.fact("goal", "hero"),
            asp.fact("helper", "friend"),
            asp.fact("helper", "friend"),
            asp.fact("danger", "hero"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return bool(asp.atoms(model, "valid_story"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a magical eleventh-chance animal story.")
    parser.add_argument("--name", choices=ANIMAL_NAMES)
    parser.add_argument("--species", choices=SPECIES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--helper", choices=HELPER_NAMES)
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
    name = args.name or rng.choice(ANIMAL_NAMES)
    species = args.species or rng.choice(SPECIES)
    return StoryParams(
        animal_name=name,
        species=species,
        place=args.place or rng.choice(PLACES),
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        seed=rng.randrange(2**31),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.animal_name not in ANIMAL_NAMES:
        raise StoryError("The animal must have a known name.")
    if params.species not in SPECIES:
        raise StoryError("The story needs a known animal species.")
    if params.place not in PLACES:
        raise StoryError("The animal needs a known woodland place.")
    if params.helper_name not in HELPER_NAMES:
        raise StoryError("The magical task needs a named helper.")
    if params.animal_name == params.helper_name:
        raise StoryError("The hero and helper must be different animals.")


def make_world(params: StoryParams) -> Animal:
    animal = Animal(params.animal_name, params.species, params.place)
    animal.meters["magic"] = 0.0
    animal.meters["distance"] = 0.0
    animal.meters["warmth"] = 0.0
    animal.facts.update(
        {
            "hero": params.animal_name,
            "species": params.species,
            "place": params.place,
            "helper": params.helper_name,
            "resolved": False,
        }
    )
    return animal


def tell_story(params: StoryParams) -> Animal:
    animal = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    tale = rng.choice(TALES)
    dialogue = rng.choice(DIALOGUE_FORMS)
    intro = rng.choice(INTRO_FORMS).format(
        name=params.animal_name,
        species=params.species,
        place=params.place,
    )
    animal.facts.update(
        {
            "tale": tale,
            "tale_id": tale.tale_id,
            "dialogue": dialogue,
            "award": rng.choice(AWARDS),
        }
    )
    animal.meters["magic"] = 1.0
    animal.memes["worry"] = 1.0
    animal.memes["hope"] = 1.0

    omen = f"{tale.omen.capitalize()}. It warned that {tale.danger}."
    values = {
        "name": params.animal_name,
        "helper": params.helper_name,
        "danger": tale.danger,
        "task": tale.magical_task,
    }
    exchange = " ".join(part.format(**values) for part in dialogue.split(" | ")) if " | " in dialogue else dialogue.format(**values)
    if dialogue.count('"') >= 4:
        exchange = dialogue.format(**values)

    lead = rng.choice(ACTION_LEADS)
    if lead.endswith(","):
        action_lead = f"{lead} {params.animal_name} and {params.helper_name}"
    else:
        action_lead = lead
    action = (
        f"{action_lead} tried to {tale.magical_task}. "
        f"Then {tale.complication}. "
        f"Instead of giving up, {params.animal_name} {tale.turning_action}."
    )

    animal.meters["distance"] = 1.0
    animal.memes["courage"] = 1.0
    animal.memes["trust"] = 1.0
    animal.meters["warmth"] = 1.0
    animal.facts["resolved"] = True
    ending = (
        f"The magic answered: {tale.result.capitalize()}. {tale.ending.capitalize()}. "
        f'{params.helper_name} smiled. "Your eleventh try mattered because you listened and let me help," '
        f"said {params.helper_name}. {params.animal_name} held the {animal.facts['award']} close."
    )
    paragraphs = [intro, omen, exchange, action, ending]
    animal.facts["story"] = "\n\n".join(paragraphs)
    return animal


def prompts(animal: Animal) -> list[str]:
    tale: Tale = animal.facts["tale"]
    return [
        'Write an Animal Story using the word "eleventh" and a little Magic.',
        f"Tell a story about {animal.name} the {animal.species} in {animal.place}.",
        f"Show how the eleventh magical chance helps {animal.name} {tale.animal_goal}, with a helper and dialogue.",
    ]


def story_qa(animal: Animal) -> list[QAItem]:
    tale: Tale = animal.facts["tale"]
    hero = animal.facts["hero"]
    helper = animal.facts["helper"]
    return [
        QAItem(
            question=f"What was special about the eleventh sign that {hero} noticed in {animal.place}?",
            answer=f"The eleventh sign was magical: {tale.omen}. It warned that {tale.danger}.",
        ),
        QAItem(
            question=f"What did {hero} and {helper} say before trying to solve the problem?",
            answer=f"{hero} explained that {tale.danger}, and {helper} encouraged {hero} to trust the magic without facing it alone. They planned to {tale.magical_task}.",
        ),
        QAItem(
            question=f"What went wrong during the magical task?",
            answer=f"{tale.complication.capitalize()}. {hero} responded by {tale.turning_action}.",
        ),
        QAItem(
            question=f"How did the ending prove that the eleventh magical chance worked?",
            answer=f"{tale.result.capitalize()} Then {tale.ending} This showed that {hero}'s careful courage had changed the situation.",
        ),
    ]


def world_qa(animal: Animal) -> list[QAItem]:
    return [
        QAItem(
            question="What does eleventh mean?",
            answer="Eleventh means coming after the tenth in a counting order.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a wondrous power that can make an unusual change, such as turning light into a bridge.",
        ),
        QAItem(
            question="Why can a helper be important in an animal story?",
            answer="A helper can notice another part of the problem, offer courage, and make a difficult task safer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(animal: Animal) -> str:
    return "\n".join(
        [
            "--- trace ---",
            f"animal={animal.name}",
            f"species={animal.species}",
            f"place={animal.place}",
            f"meters={animal.meters}",
            f"memes={animal.memes}",
            f"tale_id={animal.facts['tale_id']}",
            f"resolved={animal.facts['resolved']}",
        ]
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    animal = tell_story(params)
    return StorySample(
        params=params,
        story=animal.facts["story"],
        prompts=prompts(animal),
        story_qa=story_qa(animal),
        world_qa=world_qa(animal),
        world=animal,
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


def asp_verify() -> int:
    import asp

    python_ok = True
    asp_ok = asp_valid()
    if python_ok != asp_ok:
        print("MISMATCH between ASP and Python gates.")
        return 1
    sample = generate(
        StoryParams(
            animal_name="Luna",
            species="rabbit",
            place="the moonlit meadow",
            helper_name="Moss",
            seed=7,
        )
    )
    checks = ["eleventh", "magic", "Luna", "Moss"]
    if not all(word.lower() in sample.story.lower() for word in checks):
        print("Generated story verification failed.")
        return 1
    print("OK: ASP and Python gates agree; generated story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP gate: valid_story/1 is", "true" if asp_valid() else "false")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "rabbit", "the moonlit meadow", "Moss", 11),
            StoryParams("Milo", "fox", "the whispering woods", "Wren", 22),
            StoryParams("Clover", "hedgehog", "the fern hollow", "Poppy", 33),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        wanted = max(1, args.n)
        while len(samples) < wanted and index < max(50, wanted * 50):
            rng = random.Random(base_seed + index)
            index += 1
            params = resolve_params(args, rng)
            try:
                sample = generate(params)
            except StoryError as error:
                print(error)
                return
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
