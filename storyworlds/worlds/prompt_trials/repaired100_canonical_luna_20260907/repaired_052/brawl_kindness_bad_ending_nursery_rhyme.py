#!/usr/bin/env python3
"""
A tiny Nursery Rhyme storyworld about a brawl that goes badly when kindness
is forgotten.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


@dataclass
class Yard:
    name: str = "the crooked nursery yard"
    bell: str = "the little brass bell"
    prize: str = "the moon-bright ribbon"
    floor: str = "a muddy puddle"


@dataclass
class World:
    yard: Yard
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


@dataclass
class StoryParams:
    child: str
    rival: str
    animal: str
    setting: str
    seed: Optional[int] = None
    verse_mode: Optional[str] = None


@dataclass(frozen=True)
class Trial:
    key: str
    object_name: str
    first_claim: str
    brawl_action: str
    bad_result: str
    kindness_chance: str
    ignored_kindness: str
    ending: str
    lesson: str


CHILDREN = ["Luna", "Pip", "Mabel", "Toby", "Nell", "Bram"]
RIVALS = ["Bess", "Rory", "Kit", "Daisy", "Finn", "Milo"]
ANIMALS = ["a duck", "a small goat", "a sleepy dog", "a red hen", "a woolly lamb"]
SETTINGS = [
    "the crooked nursery yard",
    "the riddle-tree green",
    "the puddled village lane",
    "the windy schoolyard",
]
VERSE_MODES = ["bell", "riddle", "counting", "lullaby", "warning", "echo"]

TRIALS = [
    Trial(
        "ribbon",
        "the moon-bright ribbon",
        "claimed the ribbon belonged to whoever reached it first",
        "grabbed and tugged until both children tumbled",
        "the ribbon tore, and the silver prize fell into the mud",
        "offering one hand and suggesting they share the prize",
        "laughed, pulled harder, and made the quarrel worse",
        "The ribbon lay in two muddy strips while the proud children went home alone.",
        "A prize is poor comfort when kindness is left behind.",
    ),
    Trial(
        "apple",
        "the red orchard apple",
        "said the biggest bite should go to the loudest child",
        "shoved close and wrestled beside the apple cart",
        "the cart rolled away, and the apple splashed into a ditch",
        "cutting the apple into fair little pieces",
        "snatched the knife away and started the brawl again",
        "The apple bobbed out of reach, and every hungry tummy grumbled.",
        "Sharing a small sweetness is better than losing it all.",
    ),
    Trial(
        "drum",
        "the golden village drum",
        "insisted only one child could beat its cheerful skin",
        "banged elbows and feet around the drum",
        "the drum split with a sad pop and lost its song",
        "taking turns with a gentle tap",
        "answered the gentle tap with a hard thump",
        "The drum gave one crooked boom, then kept silent through the dance.",
        "A song cannot grow where roughness drowns out care.",
    ),
    Trial(
        "crown",
        "the paper daisy crown",
        "declared that the tallest head must wear the crown",
        "clawed and bumped among the daisies",
        "the crown crumpled beneath a muddy shoe",
        "folding a second crown from the waiting flowers",
        "snapped the flowers and said there was only one winner",
        "The crown became a wet paper ring, and no head wore it.",
        "Kind hands can make plenty, but proud hands can spoil enough.",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery Rhyme storyworld about a brawl and a bad ending."
    )
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--rival", choices=RIVALS)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--trial", choices=[t.key for t in TRIALS])
    parser.add_argument("--verse-mode", choices=VERSE_MODES)
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
    child = args.child or rng.choice(CHILDREN)
    rival_choices = [name for name in RIVALS if name != child]
    rival = args.rival or rng.choice(rival_choices)
    return StoryParams(
        child=child,
        rival=rival,
        animal=args.animal or rng.choice(ANIMALS),
        setting=args.setting or rng.choice(SETTINGS),
        seed=args.seed,
        verse_mode=args.verse_mode or rng.choice(VERSE_MODES),
    )


def _opening(params: StoryParams, trial: Trial) -> list[str]:
    if params.verse_mode == "bell":
        return [
            f"Ring-a-ding, ring-a-ding, in {params.setting} bright,",
            f"{params.child} and {params.rival} met at morning light.",
        ]
    if params.verse_mode == "riddle":
        return [
            f"What is round, what is bright, and invites a fight?",
            f"It waited in {params.setting} while {params.child} and {params.rival} came into sight.",
        ]
    if params.verse_mode == "counting":
        return [
            f"One little step, two little feet, three little birds in a row,",
            f"{params.child} and {params.rival} found {trial.object_name} where the soft winds blow.",
        ]
    if params.verse_mode == "lullaby":
        return [
            f"Sleepy bells hummed low and sweet across {params.setting}.",
            f"But {params.child} and {params.rival} woke to find {trial.object_name}.",
        ]
    if params.verse_mode == "warning":
        return [
            f"Mind the puddle, mind the stone, mind the prize that shines alone.",
            f"In {params.setting}, {params.child} and {params.rival} saw {trial.object_name}.",
        ]
    return [
        f"Who said it first? The hedges heard, and the old gate echoed too.",
        f"{params.child} and {params.rival} stood in {params.setting} near {trial.object_name}.",
    ]


def generate(params: StoryParams) -> StorySample:
    if params.child == params.rival:
        raise StoryError("child and rival must have different names")
    if params.setting not in SETTINGS:
        raise StoryError(f"unknown setting: {params.setting}")
    if params.verse_mode not in VERSE_MODES:
        raise StoryError(f"unknown verse mode: {params.verse_mode}")

    rng = random.Random(params.seed)
    trial = next((item for item in TRIALS if item.key == params.trial), TRIALS[0])
    yard = Yard(name=params.setting, prize=trial.object_name)
    world = World(yard)

    child = world.add(Entity(
        id=params.child,
        type="child",
        label=params.child,
        location="yard edge",
        meters={"balance": 1.0, "distance_to_prize": 1.0},
        memes={"pride": 0.4, "kindness": 0.5},
        traits=["quick", "eager"],
    ))
    rival = world.add(Entity(
        id=params.rival,
        type="child",
        label=params.rival,
        location="yard edge",
        meters={"balance": 1.0, "distance_to_prize": 1.0},
        memes={"pride": 0.5, "kindness": 0.5},
        traits=["bright", "stubborn"],
    ))
    animal = world.add(Entity(
        id="watching_animal",
        type="animal",
        label=params.animal,
        location="hedge",
        meters={"distance_to_brawl": 1.0},
        memes={"worry": 0.2},
        traits=["watchful"],
    ))
    prize = world.add(Entity(
        id="prize",
        type="object",
        label=trial.object_name,
        location="center of yard",
        meters={"whole": 1.0, "mud": 0.0},
        memes={"temptation": 1.0},
        traits=["bright"],
    ))

    world.facts.update(
        trial=trial.key,
        prize=trial.object_name,
        kindness_chance=trial.kindness_chance,
        ignored_kindness=trial.ignored_kindness,
        bad_ending=trial.ending,
        lesson=trial.lesson,
    )

    for line in _opening(params, trial):
        world.say(line)
    world.say(f"{params.animal.capitalize()} watched from the hedge as {trial.first_claim}.")
    world.say(f'"It is mine!" cried {params.child}. "No, mine!" cried {params.rival}.')

    world.para()
    world.say(f"Then came the brawl: {params.child} {trial.brawl_action}.")
    world.say(f"The yard shook, the gate clanged, and {params.animal} hid its head.")
    world.say(f"{trial.bad_result}")
    world.say(
        f'"Stop, please," whispered {params.animal}. "Try kindness, and there may be enough for both."'
    )
    world.say(
        f"{params.child} heard the gentle idea, but {params.rival} {trial.ignored_kindness}."
    )

    world.para()
    world.say(f"The brawl rolled on beneath the bell, and the chance for kindness slipped away.")
    world.say(f"At last, {trial.ending}")
    world.say(f"{params.child} looked at {params.rival}, and neither child knew what to say.")
    world.say(f"The watching animal sighed, "{trial.lesson}".")

    world.para()
    world.say(
        rng.choice([
            "So ends the rhyme with a clatter and a frown.",
            "No cheerful crown came floating down that day.",
            "The nursery song grew quiet before its final tune.",
        ])
    )
    world.say(f"{trial.ending} {trial.lesson}")

    prize.location = "muddy and ruined"
    prize.meters["whole"] = 0.0
    prize.meters["mud"] = 1.0
    child.memes["kindness"] = 0.2
    rival.memes["kindness"] = 0.2
    child.memes["regret"] = 0.8
    rival.memes["regret"] = 0.8
    animal.memes["worry"] = 1.0
    world.facts.update(kindness_offered=True, kindness_accepted=False, ending="bad")

    prompts = [
        f"Write a Nursery Rhyme about {params.child} and {params.rival} having a brawl over {trial.object_name}.",
        f"Tell a child-friendly story where kindness is offered but ignored, causing a bad ending in {params.setting}.",
        f"Make a rhyming tale with {params.animal}, a quarrel, and the lesson: {trial.lesson}",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.child} and {params.rival} begin the brawl?",
            answer=f"They began the brawl because {trial.first_claim}. They both wanted {trial.object_name} instead of deciding kindly.",
        ),
        QAItem(
            question="What kindness was offered?",
            answer=f"{params.animal.capitalize()} suggested {trial.kindness_chance}.",
        ),
        QAItem(
            question="Why did the story have a bad ending?",
            answer=f"The kindness was ignored: {trial.ignored_kindness}. The brawl caused this result: {trial.bad_result}",
        ),
        QAItem(
            question="What happened to the prize?",
            answer=f"{trial.ending} The prize ended muddy and ruined in the yard.",
        ),
        QAItem(
            question="What lesson does the rhyme teach?",
            answer=f"It teaches that {trial.lesson}",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a brawl?",
            answer="A brawl is a rough, noisy fight in which people stop treating one another gently.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means noticing another person's needs and choosing a caring action.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is a consequence that leaves the characters or their goal worse than before.",
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
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            print(
                f"  {entity.id}: {entity.type} location={entity.location} "
                f"meters={entity.meters} memes={entity.memes}"
            )
        print(f"  facts={sample.world.facts}")
    if qa:
        print()
        print("== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("domain", "nursery_rhyme"),
        asp.fact("seed_word", "brawl"),
        asp.fact("feature", "kindness"),
        asp.fact("feature", "bad_ending"),
        asp.fact("outcome", "ruined_prize"),
        asp.fact("lesson", "kindness_ignored"),
    ])


ASP_RULES = r"""
kindness_offered :- feature(kindness).
bad_ending :- feature(bad_ending), outcome(ruined_prize).
story_valid :- domain(nursery_rhyme), seed_word(brawl),
               kindness_offered, bad_ending.
#show kindness_offered/0.
#show bad_ending/0.
#show story_valid/0.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    shown = {str(symbol) for symbol in model}
    expected = {"kindness_offered", "bad_ending", "story_valid"}
    if expected.issubset(shown):
        print("OK: ASP twin confirms the brawl, kindness, and bad ending.")
        return 0
    print("MISMATCH: ASP twin did not confirm the required story features.")
    print(sorted(shown))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show domain/1.\n#show feature/1.\n#show outcome/1."))
        return

    if args.verify:
        result = asp_verify()
        if result:
            sys.exit(result)
        sample = generate(StoryParams(
            child="Luna",
            rival="Bess",
            animal="a red hen",
            setting="the crooked nursery yard",
            seed=17,
            verse_mode="bell",
            trial="ribbon",
        ))
        if "brawl" not in sample.story.lower() or "kindness" not in sample.story.lower():
            print("MISMATCH: generated story lacks required narrative terms.")
            sys.exit(1)
        print("OK: generated story exercises the world.")
        return

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Bess", "a red hen", SETTINGS[0], 101, "bell"),
            StoryParams("Pip", "Rory", "a sleepy dog", SETTINGS[1], 202, "riddle"),
            StoryParams("Mabel", "Kit", "a small goat", SETTINGS[2], 303, "counting"),
            StoryParams("Toby", "Daisy", "a woolly lamb", SETTINGS[3], 404, "warning"),
        ]
        for index, params in enumerate(curated):
            params.trial = TRIALS[index].key if False else None
            sample_params = StoryParams(
                child=params.child,
                rival=params.rival,
                animal=params.animal,
                setting=params.setting,
                seed=params.seed,
                verse_mode=params.verse_mode,
            )
            sample = generate(sample_params)
            samples.append(sample)
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < max(1, args.n) and attempts < max(50, args.n * 20):
            attempts += 1
            attempt_seed = base_seed + attempts
            rng = random.Random(attempt_seed)
            params = resolve_params(args, rng)
            params.seed = attempt_seed
            sample = generate(params)
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
        header = ""
        if args.all:
            header = f"### {sample.params.child} and {sample.params.rival}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
