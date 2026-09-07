#!/usr/bin/env python3
"""
A small heartwarming dining-room quest about deciding kindly.

The story follows a child who must decide what to do with a darling place card
before a family meal begins. Suspense grows as the guests arrive, while an
inner monologue helps the hero notice that a thoughtful choice can welcome
everyone.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    @property
    def phrase(self) -> str:
        return self.label or self.id.replace("_", " ")


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple[str, str]] = field(default_factory=set)
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
        return "\n\n".join(" ".join(group) for group in self.paragraphs if group)


@dataclass(frozen=True)
class QuestChoice:
    key: str
    place: str
    object_name: str
    guest: str
    opening: tuple[str, str]
    suspense: tuple[str, str]
    monologue: tuple[str, str]
    action: tuple[str, str]
    ending: tuple[str, str]


QUESTS = (
    QuestChoice(
        key="blue_chair",
        place="dining_room",
        object_name="blue chair",
        guest="Grandma June",
        opening=(
            "In the dining room, Clara polished the blue chair beside the table.",
            "It was her darling spot, close to the window where evening light came in.",
        ),
        suspense=(
            "Then Grandma June arrived with a careful little suitcase, and every other chair was already taken.",
            "Clara's hand rested on the blue chair. The soup was warm, the door was open, and the moment was waiting.",
        ),
        monologue=(
            "“I want my favorite place,” Clara thought. “But I want Grandma to feel at home, too.”",
            "She took one quiet breath. “I can decide with love, darling chair,” she whispered.",
        ),
        action=(
            "Clara carried the blue chair to Grandma June and placed it where the window light shone brightest.",
            "Then she brought a small cushion from the hall and made herself a new seat beside Grandma.",
        ),
        ending=(
            "Grandma's smile warmed the whole table, and Clara discovered that a shared favorite place could become even dearer.",
            "After dinner, Grandma squeezed Clara's hand. The blue chair held them both in its story.",
        ),
    ),
    QuestChoice(
        key="star_napkin",
        place="dining_room",
        object_name="star napkin",
        guest="Ben",
        opening=(
            "In the dining room, Milo folded a darling napkin shaped like a bright star.",
            "He had saved the gold napkin for his own place at the family table.",
        ),
        suspense=(
            "Just before supper, Ben came in with paint on his sleeve and nowhere clean to sit.",
            "The plates waited. The candles flickered. Milo looked from the star napkin to Ben's worried face.",
        ),
        monologue=(
            "“I worked hard on this,” Milo thought. “Still, a napkin is only cloth, and a welcome can last all evening.”",
            "He felt a tiny tug inside. “I must decide,” he told himself. “Kindness can be my brightest star.”",
        ),
        action=(
            "Milo placed the star napkin at Ben's setting and found a fresh cloth for himself.",
            "He showed Ben how to fold the new napkin into a little boat.",
        ),
        ending=(
            "Ben sat taller, and the two napkins sailed side by side while the family passed the bread.",
            "Milo's gift did not disappear; it became part of the warmest supper he could remember.",
        ),
    ),
    QuestChoice(
        key="window_place",
        place="dining_room",
        object_name="window place",
        guest="Aunt Rosa",
        opening=(
            "At the dining-room table, Priya set a darling place beside the window.",
            "She loved watching the first stars appear while everyone ate.",
        ),
        suspense=(
            "Aunt Rosa arrived carrying a small baby, and the dark corner near the window felt too cold.",
            "The chairs scraped softly. Everyone waited while Priya noticed the empty warm place.",
        ),
        monologue=(
            "“I planned this seat all day,” Priya thought. “But Aunt Rosa needs the light, and the baby needs warmth.”",
            "Her heart fluttered with suspense, yet her answer grew clear: “I can decide to make room.”",
        ),
        action=(
            "Priya moved her place setting to the middle and guided Aunt Rosa to the window.",
            "She tucked a folded blanket around the baby and kept a clear place for the serving bowl.",
        ),
        ending=(
            "The baby slept beneath the soft window glow, while Priya watched stars from a seat that felt just right.",
            "When dessert came, Aunt Rosa called Priya her darling helper, and the room seemed to shine.",
        ),
    ),
)


PLACES = {
    "dining_room": Place(
        id="dining_room",
        label="the dining room",
        tags={"home", "warm", "family"},
    )
}

NAMES = {
    "girl": ["Clara", "Milo", "Priya", "Nora", "Lena"],
    "boy": ["Milo", "Sam", "Theo", "Ben", "Eli"],
}


@dataclass
class StoryParams:
    hero_name: str
    hero_gender: str = "girl"
    quest: Optional[str] = None
    place: str = "dining_room"
    seed: Optional[int] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


def valid_combos() -> list[tuple[str, str]]:
    return [(place, quest.key) for place in PLACES for quest in QUESTS]


CURATED = [
    StoryParams(hero_name="Clara", hero_gender="girl", quest="blue_chair", seed=11),
    StoryParams(hero_name="Milo", hero_gender="boy", quest="star_napkin", seed=22),
    StoryParams(hero_name="Priya", hero_gender="girl", quest="window_place", seed=33),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming dining-room quest about deciding kindly."
    )
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=["boy", "girl"])
    parser.add_argument("--quest", choices=[quest.key for quest in QUESTS])
    parser.add_argument("--place", choices=list(PLACES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["boy", "girl"])
    names = NAMES[gender]
    hero = args.hero or rng.choice(names)
    quest = args.quest or rng.choice([item.key for item in QUESTS])
    place = args.place or "dining_room"
    return StoryParams(
        hero_name=hero,
        hero_gender=gender,
        quest=quest,
        place=place,
    )


def choose_quest(params: StoryParams, rng: random.Random) -> QuestChoice:
    if params.quest:
        for quest in QUESTS:
            if quest.key == params.quest:
                return quest
        raise StoryError(f"Unknown quest: {params.quest}")
    return rng.choice(QUESTS)


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("The story must take place in the dining room.")
    if params.hero_gender not in NAMES:
        raise StoryError("The hero must have a supported gender choice.")
    if not params.hero_name.strip():
        raise StoryError("The hero needs a name.")
    if params.hero_name.strip().lower() in {"darling", "decide"}:
        raise StoryError("The hero's name cannot be one of the seed words.")

    rng = random.Random(
        params.seed
        if params.seed is not None
        else sum((index + 1) * ord(char) for index, char in enumerate(params.hero_name))
    )
    quest = choose_quest(params, rng)
    place = PLACES[params.place]
    world = World(place=place)

    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type=params.hero_gender,
            role="hero",
        )
    )
    guest = world.add(
        Entity(
            id="guest",
            kind="character",
            type="visitor",
            role="guest",
            label=quest.guest,
        )
    )
    special = world.add(
        Entity(
            id="special_place",
            kind="object",
            type="table_setting",
            role="choice",
            label=quest.object_name,
        )
    )

    values = {"hero": hero.phrase, "guest": guest.phrase}

    hero.memes["pride"] = 1.0
    hero.memes["uncertainty"] = 1.0
    special.meters["claimed"] = 1.0
    special.meters["available"] = 0.0

    for line in quest.opening:
        world.say(line.replace("Clara", values["hero"]).replace("Milo", values["hero"]).replace("Priya", values["hero"]))
    world.para()

    guest.meters["arrived"] = 1.0
    hero.memes["suspense"] = 1.0
    for line in quest.suspense:
        world.say(line.replace("Clara", values["hero"]).replace("Milo", values["hero"]).replace("Priya", values["hero"]))
    world.para()

    hero.memes["reflection"] = 1.0
    for line in quest.monologue:
        world.say(line.replace("Clara", values["hero"]).replace("Milo", values["hero"]).replace("Priya", values["hero"]))
    world.para()

    hero.meters["decided"] = THRESHOLD
    hero.memes["kindness"] = THRESHOLD
    special.meters["claimed"] = 0.0
    special.meters["shared"] = THRESHOLD
    for line in quest.action:
        world.say(line.replace("Clara", values["hero"]).replace("Milo", values["hero"]).replace("Priya", values["hero"]))
    world.para()

    hero.memes["joy"] = THRESHOLD
    guest.memes["welcomed"] = THRESHOLD
    for line in quest.ending:
        world.say(line.replace("Clara", values["hero"]).replace("Milo", values["hero"]).replace("Priya", values["hero"]))

    world.facts.update(
        hero=hero,
        guest=guest,
        special=special,
        place=place,
        quest=quest,
        decision="The hero shared a beloved dining-room place instead of keeping it only for themself.",
        action="The hero moved the special place or object so the arriving guest could feel welcome.",
        result="The guest felt included, and the hero discovered that kindness made the favorite thing more meaningful.",
        ending=quest.ending[-1].replace("Clara", values["hero"]).replace("Milo", values["hero"]).replace("Priya", values["hero"]),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        'Write a heartwarming dining-room story using the words "decide" and "darling".',
        f"Tell a suspenseful quest in which {facts['hero'].phrase} must decide what to do with {facts['special'].phrase}.",
        "Include an inner monologue that shows why sharing a favorite place can make a family meal warmer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    return [
        QAItem(
            question="What decision did the hero need to make?",
            answer=f"{facts['hero'].phrase} needed to decide whether to keep {facts['special'].phrase} for themself or share it so the arriving guest could feel welcome."
        ),
        QAItem(
            question="What did the hero do?",
            answer=f"{facts['hero'].phrase} chose kindness and {facts['action'].lower()}"
        ),
        QAItem(
            question="How did the ending prove that the decision mattered?",
            answer=f"The ending showed the change clearly: {facts['ending']}"
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to decide?",
            answer="To decide means to think about choices and then choose what to do."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private stream of thoughts a character has inside their mind."
        ),
        QAItem(
            question="Why can sharing make a meal feel special?",
            answer="Sharing can help people feel welcomed and cared for, so an ordinary meal becomes a warm memory."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        state = []
        if meters:
            state.append(f"meters={meters}")
        if memes:
            state.append(f"memes={memes}")
        lines.append(f"  {entity.id:14} ({entity.type:12}) {' '.join(state)}")
    return "\n".join(lines)


ASP_RULES = r"""
arrived(guest) :- arrival_meter(guest, 1).
ready_to_decide(H) :- hero(H), arrived(guest), suspense(H).
kind_decision(H) :- ready_to_decide(H), reflection(H), kindness(H).
welcomed(guest) :- kind_decision(H).
shared_place(choice) :- kind_decision(H).
outcome(warm_meal) :- welcomed(guest), shared_place(choice).
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero", "hero"),
            asp.fact("arrival_meter", "guest", 1),
            asp.fact("suspense", "hero"),
            asp.fact("reflection", "hero"),
            asp.fact("kindness", "hero"),
        ]
    )


def asp_program(show: str = "#show outcome/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show outcome/1."))
    return sorted(set(asp.atoms(model, "outcome")))


def asp_verify() -> int:
    try:
        import asp

        model = asp.one_model(asp_program("#show outcome/1."))
        if ("warm_meal",) not in asp.atoms(model, "outcome"):
            print("ASP parity failed: warm_meal was not derived.")
            return 1
    except Exception as exc:
        print(f"ASP smoke test failed: {exc}")
        return 1

    try:
        for params in CURATED:
            sample = generate(params)
            if not sample.story.strip():
                print("Generation produced empty story text.")
                return 1
            if "decide" not in sample.story.lower() and "decided" not in sample.story.lower():
                print("Story is missing the decision instrument.")
                return 1
            if "darling" not in sample.story.lower():
                print("Story is missing the darling seed word.")
                return 1
            if sample.world is None or sample.world.entities["guest"].memes["welcomed"] < THRESHOLD:
                print("Python world did not reach the welcoming outcome.")
                return 1
    except Exception as exc:
        print(f"Generation smoke test failed: {exc}")
        return 1

    print("OK: smoke tests passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
