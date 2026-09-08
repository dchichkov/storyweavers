#!/usr/bin/env python3
"""
A small standalone superhero storyworld about a grizzly-sized trouble, a
careful search, an inner promise, and a happy ending.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"heroine", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"hero", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    city: str
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
    hero: str
    partner: str
    city: str
    quest: Optional[str] = None
    telling_mode: Optional[str] = None
    seed: Optional[int] = None


@dataclass(frozen=True)
class Quest:
    key: str
    threat: str
    rushed: str
    consequence: str
    clue: str
    careful: str
    reveal: str
    repair: str
    victory: str
    lesson: str
    ending: str


HEROES = ["Luna", "Vera", "Maya", "Nia", "Zara", "Ruby"]
PARTNERS = ["Pip", "Theo", "Milo", "Juno", "Kai", "Bo"]
CITIES = [
    "Brightbell City",
    "Moonbeam City",
    "Sunrise Harbor",
    "Starbridge Town",
]
TELLING_MODES = ["alarm", "patrol", "dialogue", "mystery", "promise", "countdown"]

QUESTS = [
    Quest(
        "museum",
        "a grizzly shadow-beast had covered the city museum in sticky night fog",
        "tried to terminate the fog with a thunder beam",
        "the fog split into smaller clouds and hid the museum's children inside",
        "the clouds curled away from warm singing but gathered around angry noises",
        "used a quiet sun-glove to scour the roof for a safe path while humming softly",
        "the grizzly shadow was a lonely guardian whose fog protected a nest of tiny glow-moths",
        "shared the hero's warm cape and made a bright shelter where the glow-moths could rest",
        "the guardian lifted the fog, and the children walked safely home beneath a clear moon",
        "a frightening problem may need kindness before strength",
        "The grizzly guardian waved as glow-moths sparkled around the museum clock.",
    ),
    Quest(
        "bridge",
        "a grizzly-sized robot had jammed the rainbow bridge with fallen star-metal",
        "pulled the biggest piece free without checking the bridge controls",
        "the bridge began to tilt while the evening buses waited on both sides",
        "small blue lights blinked in a pattern beneath the largest piece",
        "scoured the bridge rails with a moon compass and followed the blinking pattern",
        "the robot was not attacking; it was holding a broken support together",
        "helped the robot place the star-metal back as a strong new brace",
        "the bridge straightened and carried every bus safely across",
        "careful questions can reveal a helper hidden inside a hazard",
        "Rainbow lights shone over the repaired bridge while the robot beeped a proud hello.",
    ),
    Quest(
        "park",
        "a grizzly roar from the city park made every friendly animal flee",
        "raced in and tried to terminate the roar with a power whistle",
        "the whistle startled the animals farther into the dark trees",
        "the roar paused whenever someone called the missing bear's name",
        "scoured the trails with a listening badge instead of blowing the whistle",
        "the grizzly was trapped under a fallen parade float and roaring for help",
        "lifted the float with the partner and freed the frightened bear",
        "the bear followed a ranger home while the animals returned to the park",
        "listening is part of being brave",
        "At sunrise, the grateful bear left paw prints beside the hero's shining badge.",
    ),
    Quest(
        "powerhouse",
        "a grizzly storm of sparks rolled through the old power house",
        "sent a super-speed pulse to terminate every loose spark at once",
        "the pulse knocked out the hospital lights across the river",
        "the sparks were moving in the same rhythm as a tiny emergency beacon",
        "scoured the dark control room and traced the rhythm to a trapped repair drone",
        "the storm was the drone's broken battery trying to call for help",
        "shielded the drone and guided its charge into the safe backup circuit",
        "the hospital lights returned, and the drone repaired the city's power grid",
        "the right rescue protects the small signal as well as the big city",
        "Windows glowed all along the river as the little drone circled Luna like a star.",
    ),
    Quest(
        "library",
        "a grizzly book-beast had made the city library's story pages whirl through the streets",
        "used a giant fan to terminate the flying pages",
        "the pages scattered into puddles and lost their order",
        "the book-beast grew calm whenever someone read a story aloud",
        "scoured the library steps for the missing first page while the partner read",
        "the book-beast was a magical reader who had lost the beginning of its favorite tale",
        "found the first page and read it together with the lonely creature",
        "the pages returned to their books, and the library opened for a night of stories",
        "sharing understanding can settle a storm",
        "Warm lamplight filled the library while the book-beast turned pages for every child.",
    ),
]

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero Story inner-monologue quest world.")
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--city", choices=CITIES)
    parser.add_argument("--quest", choices=[q.key for q in QUESTS])
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HEROES)
    partner = args.partner or rng.choice([name for name in PARTNERS if name != hero])
    return StoryParams(
        hero=hero,
        partner=partner,
        city=args.city or rng.choice(CITIES),
        quest=args.quest or rng.choice(QUESTS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("genre", "superhero_story"),
            asp.fact("feature", "inner_monologue"),
            asp.fact("feature", "quest"),
            asp.fact("feature", "happy_ending"),
            asp.fact("seed_word", "terminate"),
            asp.fact("seed_word", "grizzly"),
            asp.fact("seed_word", "scour"),
            asp.fact("virtue", "careful_courage"),
        ]
    )


ASP_RULES = r"""
required_feature(inner_monologue).
required_feature(quest).
required_feature(happy_ending).
present(X) :- feature(X).
present(X) :- seed_word(X).
valid :- present(inner_monologue), present(quest), present(happy_ending),
         present(terminate), present(grizzly), present(scour).
#show required_feature/1.
#show valid/0.
"""


def asp_program(show: str = "#show valid/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = asp.atoms(model, "valid")
    features = sorted(asp.atoms(model, "required_feature"))
    if valid and features == [("happy_ending",), ("inner_monologue",), ("quest",)]:
        print("OK: ASP and Python story features agree.")
        return 0
    print("MISMATCH: ASP validation failed.")
    return 1


def opening(params: StoryParams, quest: Quest) -> list[str]:
    hero = params.hero
    partner = params.partner
    if params.telling_mode == "alarm":
        return [
            f'"Hero Luna, the city alarm is ringing!" {partner} cried.',
            f"{hero} flew over {params.city}. Below, {quest.threat}.",
        ]
    if params.telling_mode == "dialogue":
        return [
            f'"Do we have a quest tonight?" {partner} asked. "Every night," {hero} replied.',
            f"They had barely reached {params.city} when {quest.threat}.",
        ]
    if params.telling_mode == "mystery":
        return [
            f"A deep sound rolled through {params.city}, though the sky was clear.",
            f"{hero} and {partner} followed it and discovered that {quest.threat}.",
        ]
    if params.telling_mode == "promise":
        return [
            f"{hero} had promised to protect {params.city}, and {partner} flew beside her.",
            f"That promise mattered when {quest.threat}.",
        ]
    if params.telling_mode == "countdown":
        return [
            f"The city clock counted down as {hero} and {partner} raced above {params.city}.",
            f"Before it reached zero, they learned that {quest.threat}.",
        ]
    return [
        f"Night settled over {params.city} as {hero} and {partner} began their patrol.",
        f"Their quiet patrol became a quest when {quest.threat}.",
    ]


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.partner:
        raise StoryError("The hero and partner must have different names.")
    quest = next((q for q in QUESTS if q.key == params.quest), None)
    if quest is None:
        raise StoryError(f"Unknown quest: {params.quest}")

    world = World(params.city)
    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type="heroine",
        label="hero",
        phrase=params.hero,
        location="sky",
        meters={"courage": 0.7, "speed": 0.9},
        memes={"responsibility": 0.8, "doubt": 0.3},
        traits=["brave", "thoughtful"],
    ))
    partner = world.add(Entity(
        id=params.partner,
        kind="character",
        type="partner",
        label="partner",
        phrase=params.partner,
        location="sky",
        meters={"alertness": 0.8},
        memes={"trust": 0.7},
        traits=["observant", "kind"],
    ))
    threat = world.add(Entity(
        id="grizzly_problem",
        kind="thing",
        type="threat",
        label="grizzly problem",
        phrase="the grizzly problem",
        location=params.city,
        meters={"danger": 0.9, "confusion": 0.8},
        memes={"loneliness": 0.6},
        traits=["large", "misunderstood"],
    ))
    world.facts.update(
        quest=quest.key,
        threat=quest.threat,
        rushed_action=quest.rushed,
        consequence=quest.consequence,
        clue=quest.clue,
        reveal=quest.reveal,
        repair=quest.repair,
        victory=quest.victory,
        lesson=quest.lesson,
    )

    for sentence in opening(params, quest):
        world.say(sentence)
    world.say(f'"We must terminate this danger now!" {params.hero} said.')
    world.say(f"{params.hero} launched toward it and {quest.rushed}.")
    world.say(f"Instead, {quest.consequence}.")

    world.para()
    world.say(
        f"Inside her helmet, {params.hero} thought, "
        f'"A real hero does not only hit hard. I need to understand what is happening."'
    )
    world.say(f'"Wait," {params.partner} called. "Listen before you act again."')
    world.say(f'"You are right," {params.hero} answered. "We will scour the scene together."')
    world.say(f"They noticed that {quest.clue}.")
    world.say(f"Then {params.hero} {quest.careful}.")
    world.say(f"The search revealed the truth: {quest.reveal}.")

    world.para()
    world.say(
        f"{params.hero} lowered her hands and said, "
        f'"We came to help. Tell us what you need."'
    )
    world.say(f"{params.partner} replied, '"We can repair this together."')
    world.say(f"With care, they {quest.repair}.")
    world.say(f"At last, {quest.victory}.")

    world.para()
    world.say(f"{params.hero} felt her worry become steady courage. She knew that {quest.lesson}.")
    world.say(f"The quest ended with a happy ending: {quest.ending}")

    threat.location = "safe"
    threat.meters["danger"] = 0.0
    threat.meters["confusion"] = 0.0
    threat.memes["loneliness"] = 0.0
    hero.memes["doubt"] = 0.0
    hero.memes["understanding"] = 1.0
    partner.memes["trust"] = 1.0
    world.facts["ending"] = "happy"
    world.facts["quest_resolved"] = True

    prompts = [
        f"Write a Superhero Story about {params.hero} completing a quest in {params.city}.",
        f"Include a grizzly problem, an inner monologue, and the need to scour the scene before trying to terminate the danger.",
        f"End with a happy ending that shows how {quest.lesson}.",
    ]
    story_qa = [
        QAItem(
            question=f"What danger did {params.hero} find in {params.city}?",
            answer=f"{params.hero} found that {quest.threat}.",
        ),
        QAItem(
            question="Why did the first plan fail?",
            answer=f"The first plan failed because {params.hero} {quest.rushed}, and {quest.consequence}.",
        ),
        QAItem(
            question="What did the hero think before changing plans?",
            answer="The hero thought that a real hero must understand a problem instead of only using force.",
        ),
        QAItem(
            question="What clue solved the mystery?",
            answer=f"They noticed that {quest.clue}, which helped them learn that {quest.reveal}.",
        ),
        QAItem(
            question="How did the quest end?",
            answer=f"They {quest.repair}, so {quest.victory} The story ended happily because everyone was safer and understood.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thought written in the story so readers can understand a choice.",
        ),
        QAItem(
            question="What makes a quest?",
            answer="A quest is a difficult journey or task with a goal, obstacles, discoveries, and a result.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending shows that the main problem has been solved and important characters are safe, helped, or reconciled.",
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
            pieces = [f"location={entity.location}"]
            if entity.meters:
                pieces.append(f"meters={entity.meters}")
            if entity.memes:
                pieces.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.type} " + " ".join(pieces))
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        import asp
        print(json.dumps([str(atom) for atom in asp.one_model(asp_program())], indent=2))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Pip", "Brightbell City", "museum", "alarm", 101),
            StoryParams("Vera", "Theo", "Moonbeam City", "bridge", "dialogue", 202),
            StoryParams("Maya", "Juno", "Sunrise Harbor", "park", "mystery", 303),
            StoryParams("Nia", "Kai", "Starbridge Town", "library", "promise", 404),
        ]
        samples = [generate(item) for item in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        target = max(1, args.n)
        while len(samples) < target:
            attempt += 1
            seed = base_seed + attempt
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
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
        if args.all:
            header = f"### {sample.params.hero}'s quest in {sample.params.city}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
