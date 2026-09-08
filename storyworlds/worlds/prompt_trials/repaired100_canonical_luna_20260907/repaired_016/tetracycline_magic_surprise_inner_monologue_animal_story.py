#!/usr/bin/env python3
"""
A small animal story world about a fox, a mysterious medicine, and a surprising
lesson: magic can help a little, but careful care helps much more.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
STORYWORLDS_ROOT = next(parent for parent in HERE.parents if (parent / "results.py").is_file())
sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Animal:
    id: str
    name: str
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    fox_name: str
    owl_name: str
    rabbit_name: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.animals: dict[str, Animal] = {}
        self.place = Place("the moonlit meadow")
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.dialogue_turns: list[tuple[str, str]] = []

    def add(self, animal: Animal) -> Animal:
        self.animals[animal.id] = animal
        return animal

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Adventure:
    setting: str
    illness: str
    clue: str
    magic: str
    surprise: str
    care: str
    ending: str
    lesson: str


ADVENTURES = [
    Adventure(
        setting="a silver creek under an old willow",
        illness="a sore paw that made every step painful",
        clue="three tiny drops of blood on a smooth stone",
        magic="whispered a moon-spell that made the paw glow blue",
        surprise="the glow showed a thorn hidden deep between two pads",
        care="washed the paw, removed the thorn, and gave the measured tetracycline prescribed by the forest healer",
        ending="the fox left small paw prints beside the creek, each one shining briefly in the moonlight",
        lesson="magic may reveal a problem, but gentle care must solve it",
    ),
    Adventure(
        setting="a warm burrow beneath the hazel hill",
        illness="a cough that rattled whenever the rabbit hopped",
        clue="a little feather caught in the rabbit's whiskers",
        magic="sang a bright spell that made the burrow walls sparkle",
        surprise="the sparkles shook loose a nest of dusty seeds above the sleeping room",
        care="moved the rabbit into clean air and followed the healer's instructions for tetracycline",
        ending="the rabbit breathed easily while golden dust danced far away from the burrow",
        lesson="a surprising clue can point toward the safest kind of help",
    ),
    Adventure(
        setting="the blackberry path beside the pine trees",
        illness="a swollen ear that made the badger tilt her head",
        clue="the badger kept scratching beside one crooked berry branch",
        magic="called a tiny rainbow from a drop of dew",
        surprise="the rainbow revealed a burr wrapped around the ear's fur",
        care="loosened the burr, cleaned the skin, and brought the correct tetracycline dose from the healer",
        ending="the badger heard the evening crickets and smiled at their bright chorus",
        lesson="looking closely is better than guessing quickly",
    ),
    Adventure(
        setting="a nest tucked inside the clock tower",
        illness="a young pigeon with a hot, tired wing",
        clue="one feather was bent around a red thread",
        magic="lifted the feather with a soft golden breeze",
        surprise="the thread had come from a festival kite stuck on the roof",
        care="freed the wing, cooled it with clean water, and used tetracycline only as the animal doctor directed",
        ending="the pigeon tested one wing, then glided over the clock face at sunset",
        lesson="kindness needs both wonder and wise instructions",
    ),
    Adventure(
        setting="a pumpkin patch beside the village fence",
        illness="a hedgehog with a tender nose and no appetite",
        clue="a shiny crumb was stuck under a curled leaf",
        magic="made the crumb sing a tiny silver note",
        surprise="it was a sharp piece of metal from a broken lantern",
        care="let the healer remove it, cleaned the small wound, and gave the prescribed tetracycline",
        ending="the hedgehog nibbled a soft apple slice beneath a lantern that no longer had sharp edges",
        lesson="a small hidden danger deserves serious attention",
    ),
]

OPENINGS = [
    "Night settled softly over the woodland.",
    "The animals were preparing for the first stars.",
    "A cool breeze moved through the grass.",
    "The forest was quiet except for one worried sound.",
    "Moonlight spilled across the sleeping paths.",
]

DIALOGUES = [
    (
        "Please stop and let me look at you.",
        "I am frightened, but I will tell you what I feel.",
        "Then we will follow the clue before we choose a cure.",
    ),
    (
        "Your face says something is wrong.",
        "My body feels strange, and I do not know why.",
        "We can be brave without pretending to know everything.",
    ),
    (
        "Do not chase the sparkle yet. Tell me where it hurts.",
        "It hurts here, near the place I keep scratching.",
        "Good. Your words are part of our map.",
    ),
    (
        "I hear your cough. May I help?",
        "Yes, but please move slowly.",
        "Slow steps can find what fast steps miss.",
    ),
]


ASP_RULES = r"""
#show danger/1.
#show clue/1.
#show remedy/1.
danger(illness) :- sick(illness).
clue(found) :- danger(illness), evidence(found).
remedy(tetracycline) :- veterinarian(healer), medicine(tetracycline), prescribed(tetracycline).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("sick", "illness"),
            asp.fact("evidence", "found"),
            asp.fact("veterinarian", "healer"),
            asp.fact("medicine", "tetracycline"),
            asp.fact("prescribed", "tetracycline"),
        ]
    )


def asp_program(show: str = "#show danger/1.\n#show clue/1.\n#show remedy/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


FOX_NAMES = ["Luna", "Ember", "Clover", "Pip", "Fern"]
OWL_NAMES = ["Sage", "Mira", "Orin", "Nora", "Juniper"]
RABBIT_NAMES = ["Bramble", "Daisy", "Moss", "Willow", "Pepper"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animal story world with magic and careful medicine.")
    parser.add_argument("--fox-name", choices=FOX_NAMES)
    parser.add_argument("--owl-name", choices=OWL_NAMES)
    parser.add_argument("--rabbit-name", choices=RABBIT_NAMES)
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
    fox = args.fox_name or rng.choice(FOX_NAMES)
    owl = args.owl_name or rng.choice(OWL_NAMES)
    rabbit = args.rabbit_name or rng.choice(RABBIT_NAMES)
    if len({fox, owl, rabbit}) < 3:
        raise StoryError("animal names must be distinct")
    return StoryParams(fox_name=fox, owl_name=owl, rabbit_name=rabbit)


def _setup_world(params: StoryParams) -> World:
    world = World()
    fox = world.add(Animal("fox", params.fox_name, "fox", "helper"))
    owl = world.add(Animal("owl", params.owl_name, "owl", "healer"))
    rabbit = world.add(Animal("rabbit", params.rabbit_name, "rabbit", "patient"))
    world.facts.update(fox=fox, owl=owl, rabbit=rabbit)
    return world


def _say(world: World, speaker: Animal, line: str) -> None:
    world.dialogue_turns.append((speaker.name, line))
    world.say(f'{speaker.name} said, "{line}"')


def _inner_monologue(world: World, fox: Animal, thought: str) -> None:
    fox.memes["wonder"] = fox.memes.get("wonder", 0.0) + 1.0
    world.say(f"{fox.name} thought, *{thought}*.")


def _variation_key(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum(ord(c) for c in f"{params.fox_name}:{params.owl_name}:{params.rabbit_name}")


def generate_story(world: World, params: StoryParams) -> None:
    fox: Animal = world.facts["fox"]
    owl: Animal = world.facts["owl"]
    rabbit: Animal = world.facts["rabbit"]

    key = _variation_key(params)
    adventure = ADVENTURES[key % len(ADVENTURES)]
    opening = OPENINGS[(key // len(ADVENTURES)) % len(OPENINGS)]
    dialogue = DIALOGUES[(key // (len(ADVENTURES) * len(OPENINGS))) % len(DIALOGUES)]

    world.facts.update(
        adventure=adventure,
        opening=opening,
        warning=dialogue[0],
        patient_reply=dialogue[1],
        plan_reply=dialogue[2],
        resolved=False,
    )

    world.place.name = adventure.setting
    world.place.meters["moonlight"] = 1.0
    rabbit.meters["health"] = 0.35
    rabbit.memes["fear"] = 0.8

    world.say(opening)
    world.say(
        f"Near {adventure.setting}, {fox.name} found {rabbit.name} sitting still. "
        f"The rabbit had {adventure.illness}."
    )
    _inner_monologue(
        world,
        fox,
        f"I wish I could make the hurt disappear, but first I must learn what is wrong.",
    )

    world.para()
    _say(world, fox, dialogue[0])
    _say(world, rabbit, dialogue[1])
    world.say(f"{fox.name} noticed {adventure.clue}.")
    _say(world, owl, dialogue[2])
    world.say(
        f"{owl.name}, the forest healer, carried a small medicine pouch, but she did not open it yet. "
        "Medicine was never a guess."
    )

    world.para()
    world.say(f"{fox.name} {adventure.magic}.")
    world.say(f"Then came the surprise: {adventure.surprise}.")
    _inner_monologue(
        world,
        fox,
        "The magic did not fix everything. It showed us where to begin.",
    )
    world.say(
        f"The three animals worked carefully. {adventure.care}. "
        f"{owl.name} checked the label and the dose before anyone gave it."
    )
    rabbit.meters["health"] = 1.0
    rabbit.memes["fear"] = 0.1
    rabbit.memes["trust"] = 1.0
    world.facts["medicine_used"] = "tetracycline"
    world.facts["resolved"] = True

    _say(world, rabbit, "I feel safer now, and I know why we waited to use the medicine.")
    _say(world, fox, "The surprise helped us see the truth.")
    world.say(f"{adventure.lesson.capitalize()}.")
    world.say(f"At last, {adventure.ending}.")


def story_qa(world: World) -> list[QAItem]:
    fox: Animal = world.facts["fox"]
    owl: Animal = world.facts["owl"]
    rabbit: Animal = world.facts["rabbit"]
    adventure: Adventure = world.facts["adventure"]
    return [
        QAItem(
            question=f"Who found {rabbit.name}, and what was wrong with the rabbit?",
            answer=f"{fox.name} found {rabbit.name}, who had {adventure.illness}.",
        ),
        QAItem(
            question=f"What clue did {fox.name} notice?",
            answer=f"{fox.name} noticed {adventure.clue}.",
        ),
        QAItem(
            question=f"What surprising thing did the magic reveal?",
            answer=f"The magic revealed that {adventure.surprise}.",
        ),
        QAItem(
            question=f"How did {owl.name} make sure tetracycline was used safely?",
            answer=f"{owl.name} checked the label and the dose and used tetracycline only as the forest healer directed.",
        ),
        QAItem(
            question="What showed that the animal was better at the end?",
            answer=f"{adventure.ending}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tetracycline?",
            answer="Tetracycline is an antibiotic medicine that may be used for some bacterial infections when a qualified animal or human health professional prescribes it.",
        ),
        QAItem(
            question="Why should animals not take medicine as a guess?",
            answer="Animals should receive medicine only with proper guidance because the wrong medicine or dose can be harmful.",
        ),
        QAItem(
            question="What can magic do in this story world?",
            answer="Magic can reveal clues or make hidden details easier to notice, but it does not replace careful observation and skilled care.",
        ),
        QAItem(
            question="Why is listening important when helping a sick animal?",
            answer="Listening helps a helper learn where the animal hurts and choose a safer next step.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    fox: Animal = world.facts["fox"]
    owl: Animal = world.facts["owl"]
    rabbit: Animal = world.facts["rabbit"]
    adventure: Adventure = world.facts["adventure"]
    return [
        f"Write a child-friendly animal story about {fox.name} helping {rabbit.name} with {owl.name}.",
        f"Include magic that reveals this clue: {adventure.clue}, followed by the surprise that {adventure.surprise}.",
        f"Explain why tetracycline must be given according to a healer's instructions, and end with: {adventure.ending}.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for animal in world.animals.values():
        lines.append(
            f"  {animal.id}: name={animal.name} species={animal.species} "
            f"role={animal.role} meters={animal.meters} memes={animal.memes}"
        )
    lines.append(f"  place: {world.place.name} meters={world.place.meters} memes={world.place.memes}")
    lines.append(f"  dialogue turns: {len(world.dialogue_turns)}")
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    generate_story(world, params)
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


CURATED = [
    StoryParams("Luna", "Sage", "Bramble"),
    StoryParams("Ember", "Mira", "Daisy"),
    StoryParams("Clover", "Orin", "Moss"),
    StoryParams("Pip", "Nora", "Willow"),
    StoryParams("Fern", "Juniper", "Pepper"),
]


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    dangers = asp.atoms(model, "danger")
    clues = asp.atoms(model, "clue")
    remedies = asp.atoms(model, "remedy")
    if ("illness",) not in dangers:
        print("MISMATCH: ASP did not detect the illness.")
        return 1
    if ("found",) not in clues:
        print("MISMATCH: ASP did not detect the clue.")
        return 1
    if ("tetracycline",) not in remedies:
        print("MISMATCH: ASP did not approve the prescribed remedy.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if "tetracycline" not in sample.story.lower():
            print("MISMATCH: generated story omitted tetracycline.")
            return 1
        if len(sample.world.dialogue_turns) < 4:
            print("MISMATCH: generated story lacks dialogue.")
            return 1
        if not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve.")
            return 1
    print("OK: ASP/Python parity and generated stories verified.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        try:
            sys.exit(asp_verify())
        except ImportError as exc:
            raise StoryError("ASP verification requires the clingo dependency.") from exc

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("danger:", asp.atoms(model, "danger"))
        print("clue:", asp.atoms(model, "clue"))
        print("remedy:", asp.atoms(model, "remedy"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story not in seen:
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
