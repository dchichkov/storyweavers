#!/usr/bin/env python3
"""
A small standalone story world about a sailor and infantry friends whose parade
takes an unexpected turn and becomes a heartwarming welcome.
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
    kind: str
    type: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"sailor", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"infantry", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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


@dataclass
class StoryParams:
    sailor: str
    infantry_friend: str
    town: str
    parade_name: str
    seed: Optional[int] = None
    scenario: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    duty: str
    obstacle: str
    first_plan: str
    consequence: str
    clue: str
    twist: str
    kind_action: str
    ending: str
    lesson: str


SAILOR_NAMES = ["Mara", "Nell", "June", "Rina", "Tess", "Lila"]
INFANTRY_NAMES = ["Ben", "Owen", "Cal", "Milo", "Sam", "Theo"]
TOWNS = [
    "Harbor Bell",
    "Maple Quay",
    "Sunrise Point",
    "Willow Harbor",
]
PARADES = [
    "the Lantern Parade",
    "the Spring Homecoming Parade",
    "the Harbor Day Parade",
    "the Little Flags Parade",
]
TELLING_MODES = ["arrival", "question", "memory", "announcement", "quiet", "dialogue"]

SCENARIOS = [
    Scenario(
        key="missing_drum",
        duty="lead the town parade home after a long voyage",
        obstacle="the parade drum disappeared just before the first march",
        first_plan="searched the bandstand alone while the parade waited",
        consequence="the children stopped waving because the quiet street felt like a canceled celebration",
        clue="small floury footprints ran from the bakery to the pier",
        twist="the baker's little daughter had borrowed the drum to keep time for her nervous father, who was marching for the first time",
        kind_action="invited both of them to walk at the front and let the girl play the opening beat",
        ending="the drum boomed, the baker smiled, and every child found a way to march beside them",
        lesson="a missing piece may be waiting for someone who needs courage",
    ),
    Scenario(
        key="backward_banner",
        duty="carry the town banner at the head of the parade",
        obstacle="a sudden breeze turned the banner backward so its bright welcome could not be read",
        first_plan="pulled hard on the banner rope to force it straight",
        consequence="the pole leaned toward a row of flower pots and the crowd began to duck",
        clue="the cloth always turned toward one quiet balcony",
        twist="an elderly neighbor on that balcony had sewn the banner and was trying to show that one corner needed mending",
        kind_action="stopped the parade, climbed carefully to the balcony, and asked the neighbor to lead the repair",
        ending="the mended banner opened over the street, carrying a welcome stitched by many hands",
        lesson="slowing down can help us notice the person behind a problem",
    ),
    Scenario(
        key="empty_chair",
        duty="honor the people who had helped the harbor during the year",
        obstacle="one chair in the reviewing stand stood empty",
        first_plan="planned to begin the salute without mentioning it",
        consequence="the sailor felt the celebration grow cold even though the flags were bright",
        clue="a folded blue scarf rested on the empty seat",
        twist="the chair belonged to the old ferry keeper, who had stayed below the hill because he thought nobody remembered him",
        kind_action="asked the infantry friend to carry the chair down the hill and brought the whole parade to the ferry house",
        ending="the old keeper watched the salute from his doorway, with the blue scarf around his shoulders",
        lesson="a celebration is warmer when it makes room for the quiet helper",
    ),
    Scenario(
        key="runaway_ribbons",
        duty="guide the smallest marchers through the town square",
        obstacle="a basket of parade ribbons spilled and blew across the road",
        first_plan="chased the ribbons while telling the children to wait",
        consequence="the children scattered after the colors and nearly missed the parade turn",
        clue="each ribbon caught on a different child's sleeve",
        twist="the ribbons had become a trail made by the children for a homebound neighbor to see from her window",
        kind_action="let the children gather the ribbons and turn the march into a bright path beneath the neighbor's window",
        ending="the neighbor waved from her chair, and the children marched slowly enough for her to see every color",
        lesson="a delay can become a gift when we understand where it is leading",
    ),
    Scenario(
        key="silent_whistle",
        duty="start the parade with the harbor whistle",
        obstacle="the sailor's whistle made no sound at the starting line",
        first_plan="blew harder and harder while the crowd waited",
        consequence="her cheeks hurt and the first row began to whisper that the parade was over",
        clue="a little boy in the crowd was holding a matching whistle made from reed",
        twist="the boy had carved it for his mother, who was returning with the sailor, but he was too shy to play it",
        kind_action="asked him to give the starting call beside her and promised to follow his rhythm",
        ending="two whistles sang together, and the boy's mother came running into his arms",
        lesson="sharing the first note can make room for someone else's brave voice",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming parade storyworld with a sailor, infantry friend, and twist."
    )
    parser.add_argument("--sailor", choices=SAILOR_NAMES)
    parser.add_argument("--infantry", dest="infantry_friend", choices=INFANTRY_NAMES)
    parser.add_argument("--town", choices=TOWNS)
    parser.add_argument("--parade-name", choices=PARADES)
    parser.add_argument("--scenario", choices=[s.key for s in SCENARIOS])
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
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
    sailor = args.sailor or rng.choice(SAILOR_NAMES)
    infantry = args.infantry_friend or rng.choice(
        [name for name in INFANTRY_NAMES if name != sailor]
    )
    return StoryParams(
        sailor=sailor,
        infantry_friend=infantry,
        town=args.town or rng.choice(TOWNS),
        parade_name=args.parade_name or rng.choice(PARADES),
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("domain", "parade"),
            asp.fact("role", "sailor"),
            asp.fact("role", "infantry"),
            asp.fact("feature", "twist"),
            asp.fact("style", "heartwarming"),
            asp.fact("value", "kindness"),
        ]
    )


ASP_RULES = r"""
required(domain,parade) :- domain(parade).
required(role,sailor) :- role(sailor).
required(role,infantry) :- role(infantry).
required(feature,twist) :- feature(twist).
required(style,heartwarming) :- style(heartwarming).
required(value,kindness) :- value(kindness).
#show required/2.
"""


def asp_program(show: str = "#show required/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = sorted(asp.atoms(model, "required"))
    wanted = [
        ("domain", "parade"),
        ("feature", "twist"),
        ("role", "infantry"),
        ("role", "sailor"),
        ("style", "heartwarming"),
        ("value", "kindness"),
    ]
    if found == wanted:
        print("OK: ASP and Python story requirements agree.")
        return 0
    print("MISMATCH: ASP requirements are incomplete.")
    print(found)
    return 1


def _opening(params: StoryParams, scenario: Scenario) -> list[str]:
    mode = params.telling_mode or "arrival"
    sailor = params.sailor
    infantry = params.infantry_friend
    parade = params.parade_name
    town = params.town

    if mode == "question":
        return [
            f'"Is the parade ready?" {infantry} asked as {sailor} reached {town}.',
            f'"Ready enough to begin," {sailor} replied. "But we still need to {scenario.duty}."',
        ]
    if mode == "memory":
        return [
            f"{sailor} would remember the day {parade} began in {town}.",
            f"She and {infantry} had come to {scenario.duty}.",
        ]
    if mode == "announcement":
        return [
            f"The mayor called, \"Let {parade} begin!\"",
            f"{sailor} and {infantry} stood ready in {town}, hoping to {scenario.duty}.",
        ]
    if mode == "quiet":
        return [
            f"The flags were bright, but the first street of {parade} was strangely quiet.",
            f"{sailor} and {infantry} had arrived in {town} to {scenario.duty}.",
        ]
    if mode == "dialogue":
        return [
            f'"Keep close," {sailor} told {infantry}. "Today is for everyone."',
            f"They stepped into {town} to {scenario.duty}.',
        ]
    return [
        f"{parade} filled {town} with flags, bells, and happy faces.",
        f"{sailor}, a sailor home from the sea, stood beside {infantry} as they prepared to {scenario.duty}.",
    ]


def generate(params: StoryParams) -> StorySample:
    if not params.sailor or not params.infantry_friend:
        raise StoryError("A parade needs both a sailor and an infantry friend.")
    if params.sailor == params.infantry_friend:
        raise StoryError("The sailor and infantry friend must have different names.")

    scenario = next(
        (item for item in SCENARIOS if item.key == params.scenario),
        None,
    )
    if scenario is None:
        raise StoryError(f"Unknown parade scenario: {params.scenario}")

    rng = random.Random(params.seed)
    world = World()

    sailor = world.add(
        Entity(
            id=params.sailor,
            kind="character",
            type="sailor",
            label="sailor",
            location="parade square",
            meters={"energy": 0.8, "distance_from_home": 0.0},
            memes={"hope": 0.8, "belonging": 0.6},
        )
    )
    infantry = world.add(
        Entity(
            id=params.infantry_friend,
            kind="character",
            type="infantry",
            label="infantry friend",
            location="parade square",
            meters={"energy": 0.9, "readiness": 0.9},
            memes={"loyalty": 0.9, "kindness": 0.7},
        )
    )
    parade = world.add(
        Entity(
            id="parade",
            kind="event",
            type="parade",
            label=params.parade_name,
            location=params.town,
            meters={"joy": 0.7, "order": 0.8},
            memes={"welcome": 0.8},
        )
    )

    world.facts.update(
        town=params.town,
        parade=params.parade_name,
        sailor=sailor,
        infantry=infantry,
        scenario=scenario.key,
        obstacle=scenario.obstacle,
        twist=scenario.twist,
        lesson=scenario.lesson,
    )

    for sentence in _opening(params, scenario):
        world.say(sentence)

    world.say(
        rng.choice(
            [
                f"Then they discovered that {scenario.obstacle}.",
                f"Just before the first step, the trouble came: {scenario.obstacle}.",
                f"The bright morning changed when {scenario.obstacle}.",
            ]
        )
    )

    world.para()
    world.say(
        rng.choice(
            [
                f"{sailor} {scenario.first_plan}.",
                f'"I will fix it quickly," {sailor} said, and {sailor} {scenario.first_plan}.',
                f"{infantry} tried to help, but {sailor} {scenario.first_plan}.",
            ]
        )
    )
    world.say(f"Instead, {scenario.consequence}.")
    world.say(
        f'"Wait," {infantry} said. "The parade can pause, but we should find out who needs us."'
    )

    world.para()
    world.say(f"They looked more carefully and noticed that {scenario.clue}.")
    world.say(
        f"{sailor} and {infantry} followed the clue instead of forcing their first plan."
    )
    world.say(
        rng.choice(
            [
                f"Then came the twist: {scenario.twist}.",
                f"The answer was a surprise, but a gentle one: {scenario.twist}.",
                f"What looked like a parade problem hid a tender truth: {scenario.twist}.",
            ]
        )
    )

    world.para()
    world.say(f'"Then let us help," {sailor} said.')
    world.say(f"{infantry} nodded. Together they {scenario.kind_action}.")
    world.say(
        f"The crowd did not complain about the delay. People smiled, made room, and joined the welcome."
    )
    world.say(f"At last, {scenario.ending}.")

    world.para()
    world.say(f"That day, the parade taught them that {scenario.lesson}.")
    world.say(
        f"When the flags moved again through {params.town}, even the quietest faces looked bright."
    )

    sailor.meters["energy"] = 0.6
    sailor.memes["belonging"] = 1.0
    infantry.memes["kindness"] = 1.0
    parade.meters["joy"] = 1.0
    parade.meters["order"] = 1.0
    parade.memes["welcome"] = 1.0
    world.facts.update(
        resolved=True,
        twist_revealed=True,
        welcome_shared=True,
        ending="heartwarming",
    )

    prompts = [
        f"Write a heartwarming parade story about sailor {params.sailor} and infantry friend {params.infantry_friend}.",
        f"Tell a child-friendly story in {params.town} where a parade problem has a kind twist: {scenario.twist}.",
        f"Write a story showing that {scenario.lesson}",
    ]
    story_qa = [
        QAItem(
            question="What problem interrupted the parade?",
            answer=f"The parade was interrupted because {scenario.obstacle}. The sailor and infantry friend had to pause the celebration and investigate.",
        ),
        QAItem(
            question="What clue helped them understand the problem?",
            answer=f"They noticed that {scenario.clue}. Following that clue showed them that the trouble had a human reason.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {scenario.twist}. The unexpected truth changed the characters from fixing a problem to helping someone.",
        ),
        QAItem(
            question=f"How did {params.sailor} and {params.infantry_friend} respond?",
            answer=f"They responded kindly. Together they {scenario.kind_action}, so the parade became a shared welcome.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended when {scenario.ending}. The parade became heartwarming because everyone made room for another person.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is a public celebration in which people walk, ride, play music, or carry colorful signs together.",
        ),
        QAItem(
            question="What is a sailor?",
            answer="A sailor is a person who works or travels on the sea or another large body of water.",
        ),
        QAItem(
            question="What does infantry mean?",
            answer="Infantry are soldiers who serve as people traveling and working on foot.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is an unexpected change or discovery that makes earlier events mean something new.",
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
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            print(
                f"  {entity.id}: {entity.type} "
                f"location={entity.location} "
                f"meters={entity.meters} memes={entity.memes}"
            )

    if qa:
        print()
        print("== prompts ==")
        for number, prompt in enumerate(sample.prompts, 1):
            print(f"{number}. {prompt}")

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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("\n".join(str(atom) for atom in model))
        return

    if args.verify:
        result = asp_verify()
        if result:
            sys.exit(result)

        check = StoryParams(
            sailor="Mara",
            infantry_friend="Ben",
            town="Harbor Bell",
            parade_name="the Lantern Parade",
            seed=17,
            scenario="missing_drum",
            telling_mode="dialogue",
        )
        sample = generate(check)
        required_phrases = ["parade", "sailor", "infantry", "twist", "Together"]
        if not all(phrase.lower() in sample.story.lower() for phrase in required_phrases):
            print("MISMATCH: generated prose is missing a required story element.")
            sys.exit(1)
        print("OK: generated story exercises the parade, sailor, infantry, and twist.")
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                sailor="Mara",
                infantry_friend="Ben",
                town="Harbor Bell",
                parade_name="the Lantern Parade",
                seed=101,
                scenario="missing_drum",
                telling_mode="arrival",
            ),
            StoryParams(
                sailor="Nell",
                infantry_friend="Owen",
                town="Maple Quay",
                parade_name="the Spring Homecoming Parade",
                seed=202,
                scenario="empty_chair",
                telling_mode="question",
            ),
            StoryParams(
                sailor="June",
                infantry_friend="Cal",
                town="Sunrise Point",
                parade_name="the Little Flags Parade",
                seed=303,
                scenario="silent_whistle",
                telling_mode="dialogue",
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            attempt += 1
            attempt_seed = base_seed + attempt
            params = resolve_params(args, random.Random(attempt_seed))
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
        if args.all:
            params = sample.params
            header = f"### {params.sailor} and {params.infantry_friend} in {params.town}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""

        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
