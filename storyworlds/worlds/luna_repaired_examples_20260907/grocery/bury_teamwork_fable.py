#!/usr/bin/env python3
"""
A small fable storyworld about two young gardeners who bury a treasure seed
together and learn that teamwork makes hidden good things grow.
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
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
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


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
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
    child_a: str
    child_b: str
    helper: str
    weather: str
    seed_kind: str
    disagreement: str
    ending: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Weather:
    name: str
    sign: str
    danger: str
    gift: str


@dataclass(frozen=True)
class SeedKind:
    name: str
    appearance: str
    promise: str
    result: str


@dataclass(frozen=True)
class Disagreement:
    temptation: str
    mistake: str
    repair: str
    lesson: str


@dataclass(frozen=True)
class Ending:
    image: str
    final_line: str


WEATHER = {
    "morning_rain": Weather(
        "a soft morning rain",
        "Clouds gathered over the garden",
        "the fresh hole could fill with water before the seed was covered",
        "the rain would settle the soil around the buried seed",
    ),
    "hot_sun": Weather(
        "a bright, hot sun",
        "The sun climbed high and made the garden shimmer",
        "the loose earth could dry into a hard crust before the seed was tucked in",
        "the warm light would help the first green shoot find its way upward",
    ),
    "wind": Weather(
        "a brisk spring wind",
        "The wind skipped through the bean poles",
        "the light seed might blow away if they worked carelessly",
        "the wind would carry pollen to the flowers once their teamwork made them bloom",
    ),
    "evening_cool": Weather(
        "a cool evening",
        "The shadows stretched across the garden",
        "there was little daylight left for a second try",
        "the quiet night would give the buried seed a peaceful beginning",
    ),
}

SEEDS = {
    "sunflower": SeedKind(
        "a sunflower seed",
        "small, striped, and bright as a tiny moon",
        "a tall golden flower that could feed the bees",
        "one tall sunflower opened above the fence, and bees hummed around its golden face",
    ),
    "pumpkin": SeedKind(
        "a pumpkin seed",
        "flat, pale, and smooth as a little boat",
        "a broad vine with a pumpkin large enough to share",
        "a round pumpkin grew beneath the leaves, big enough for the whole village to admire",
    ),
    "bean": SeedKind(
        "a bean seed",
        "small, cream-colored, and marked with a brown smile",
        "a climbing vine that could make a leafy shelter",
        "green bean vines climbed the trellis and made a cool shelter for tired sparrows",
    ),
    "apple": SeedKind(
        "an apple pip",
        "dark, shiny, and no bigger than a crumb",
        "a patient tree whose fruit could be shared for many years",
        "a young apple tree lifted its first leaves toward the sky",
    ),
}

DISAGREEMENTS = {
    "same_spot": Disagreement(
        "choose the planting spot alone",
        "Each friend dug in a different place, and the garden became a patchwork of shallow holes",
        "look at the sun, test the soil together, and choose one good place",
        "A shared plan is stronger than two separate starts.",
    ),
    "fastest": Disagreement(
        "be the one who buried the seed fastest",
        "They tugged at the same spade until the neat hole became wide and crooked",
        "take turns loosening, holding, and covering the earth",
        "Work is not a race when the treasure belongs to everyone.",
    ),
    "best_tool": Disagreement(
        "claim the strongest garden tool",
        "They both pulled the long-handled spade, and the seed rolled toward a row of stones",
        "choose the right tool for each part and pass it carefully",
        "Good teamwork gives every tool and every helper a useful place.",
    ),
    "secret": Disagreement(
        "hide the seed so the other friend could not take credit",
        "One friend closed a fist around it, and the other stopped trusting the plan",
        "place the seed in an open palm and name the work each friend would do",
        "Trust lets a small gift become a shared hope.",
    ),
    "blame": Disagreement(
        "blame the other friend when the first hole failed",
        "Their sharp words made both of them put down their tools",
        "speak about the problem instead of blaming a person",
        "Kind words can reopen a path that anger has closed.",
    ),
}

ENDINGS = {
    "harvest": Ending(
        "When the season changed, the friends carried the first harvest to the village table",
        "The smallest seed had become a feast because no one had tried to grow it alone.",
    ),
    "bees": Ending(
        "By summer, bees danced over the flowers while the two friends watered them side by side",
        "The garden taught every visitor that shared care makes a bright home.",
    ),
    "shade": Ending(
        "At noon, the new leaves cast a cool patch where the friends could rest together",
        "They smiled beneath the shade and remembered how carefully their teamwork had begun.",
    ),
    "rainbow": Ending(
        "After a spring shower, a rainbow shone above the garden and the new plant glistened below it",
        "The friends knew that patience and teamwork had hidden a little wonder in the soil.",
    ),
    "birds": Ending(
        "Birds soon visited the garden, finding both food and a safe place to sing",
        "The friends had buried one seed, but their teamwork had planted welcome for many.",
    ),
}

NAMES = ["Mara", "Tavi", "Nia", "Oren", "Lumi", "Pip", "Sela", "Bram"]
HELPERS = ["the old gardener", "their kind aunt", "the patient groundskeeper"]
WEATHER_KEYS = tuple(WEATHER)
SEED_KEYS = tuple(SEEDS)
DISAGREEMENT_KEYS = tuple(DISAGREEMENTS)
ENDING_KEYS = tuple(ENDINGS)


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        ("garden", "teamwork", "bury"),
    ]


def explain_rejection() -> str:
    return "This fable only supports burying a seed in a garden through teamwork."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A teamwork fable about burying a seed.")
    parser.add_argument("--place", choices=["garden"])
    parser.add_argument("--activity", choices=["teamwork"])
    parser.add_argument("--prize", choices=["bury"])
    parser.add_argument("--child-a")
    parser.add_argument("--child-b")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--weather", choices=WEATHER_KEYS)
    parser.add_argument("--seed-kind", choices=SEED_KEYS)
    parser.add_argument("--disagreement", choices=DISAGREEMENT_KEYS)
    parser.add_argument("--ending", choices=ENDING_KEYS)
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
    requested = [args.place, args.activity, args.prize]
    if any(requested) and requested != [None, None, None]:
        if any(value not in (None, expected) for value, expected in zip(requested, ["garden", "teamwork", "bury"])):
            raise StoryError(explain_rejection())

    child_a = args.child_a or rng.choice(NAMES)
    child_b = args.child_b or rng.choice([name for name in NAMES if name != child_a])
    if child_a == child_b:
        raise StoryError("The two gardeners need different names.")

    return StoryParams(
        child_a=child_a,
        child_b=child_b,
        helper=args.helper or rng.choice(HELPERS),
        weather=args.weather or rng.choice(WEATHER_KEYS),
        seed_kind=args.seed_kind or rng.choice(SEED_KEYS),
        disagreement=args.disagreement or rng.choice(DISAGREEMENT_KEYS),
        ending=args.ending or rng.choice(ENDING_KEYS),
    )


def tell(params: StoryParams) -> World:
    weather = WEATHER[params.weather]
    seed_kind = SEEDS[params.seed_kind]
    disagreement = DISAGREEMENTS[params.disagreement]
    ending = ENDINGS[params.ending]

    world = World()
    first = world.add(Entity(params.child_a, "character", "child", params.child_a, "garden"))
    second = world.add(Entity(params.child_b, "character", "child", params.child_b, "garden"))
    helper = world.add(Entity("helper", "character", "helper", params.helper, "garden"))
    seed = world.add(Entity("seed", "object", "seed", seed_kind.name, "palm"))
    soil = world.add(Entity("soil", "place", "earth", "the garden soil", "garden"))

    world.facts.update(
        first=first,
        second=second,
        helper=helper,
        seed=seed,
        soil=soil,
        weather=weather,
        seed_kind=seed_kind,
        disagreement=disagreement,
        ending=ending,
        teamwork=False,
        buried=False,
    )

    first.memes["hope"] = 1
    second.memes["hope"] = 1

    openings = [
        f"Once, in a little garden behind the village, {first.id} and {second.id} found {seed_kind.name}.",
        f"At the edge of the village garden, {first.id} and {second.id} discovered {seed_kind.name} beneath a fallen leaf.",
        f"{first.id} and {second.id} loved the garden, but on that day they had never buried a seed together.",
        f"The garden keeper gave {first.id} and {second.id} {seed_kind.name} and asked them to make a careful beginning.",
    ]
    world.say(random.Random(params.seed).choice(openings) if params.seed is not None else openings[0])
    world.say(f"It was {weather.name}, and {weather.sign.lower()}.")
    world.say(f"The little seed looked {seed_kind.appearance}.")
    world.say(f"{params.helper.capitalize()} told them that it promised {seed_kind.promise}.")

    world.para()
    world.say(f"At first, the friends disagreed about how to bury it. One wanted to {disagreement.temptation}.")
    world.say(f"{disagreement.mistake}.")
    first.memes["frustration"] = 1
    second.memes["frustration"] = 1
    world.say(f"{params.helper.capitalize()} watched quietly while {weather.danger}.")

    world.para()
    world.say(f"Then {first.id} noticed that the seed was safe only if both friends stopped pulling in different directions.")
    world.say(f"{second.id} opened a hand and said, \"Let us make one plan together.\"")
    world.say(f"They decided to {disagreement.repair}.")
    world.say(f"{first.id} loosened the earth while {second.id} held the seed safely above the hole.")
    world.say(f"Then they changed places: {second.id} lowered the seed, and {first.id} covered it with soft soil.")
    world.say(f"{params.helper.capitalize()} showed them how to press the earth gently, so the seed could breathe and {weather.gift}.")
    first.memes["frustration"] = 0
    second.memes["frustration"] = 0
    first.memes["trust"] = 1
    second.memes["trust"] = 1
    world.facts["teamwork"] = True
    world.facts["buried"] = True
    world.fired.add("teamwork")
    world.say(f"When the seed was buried, neither friend claimed the work. They smiled because the careful beginning belonged to both of them.")

    world.para()
    world.say(f"Days passed. The friends watered the place together and took turns pulling weeds.")
    world.say(f"At last, {seed_kind.result}.")
    world.say(f"They remembered the lesson: {disagreement.lesson}")
    world.say(f"{ending.image}.")
    world.say(ending.final_line)
    return world


def generation_prompts(world: World) -> list[str]:
    first = world.facts["first"]
    second = world.facts["second"]
    seed_kind = world.facts["seed_kind"]
    return [
        f"Write a fable about {first.id} and {second.id} using teamwork to bury {seed_kind.name}.",
        "Show how a disagreement changes when the characters share the work.",
        "End with a concrete garden image proving that their teamwork mattered.",
    ]


def story_qa(world: World) -> list[QAItem]:
    first = world.facts["first"]
    second = world.facts["second"]
    helper = world.facts["helper"]
    weather = world.facts["weather"]
    seed_kind = world.facts["seed_kind"]
    disagreement = world.facts["disagreement"]
    return [
        QAItem(
            question=f"What did {first.id} and {second.id} find in the garden?",
            answer=f"They found {seed_kind.name}, which promised {seed_kind.promise}.",
        ),
        QAItem(
            question="Why could the friends not work separately?",
            answer=f"They could not work separately because {disagreement.mistake.lower()}. They needed one careful plan before they could bury the seed safely.",
        ),
        QAItem(
            question="How did the friends use teamwork?",
            answer=f"{first.id} loosened the earth while {second.id} held the seed, and then they changed places so {second.id} could lower it while {first.id} covered it. {helper.label.capitalize()} helped them press the soil gently.",
        ),
        QAItem(
            question="What changed after the seed was buried?",
            answer=f"The friends began watering and weeding together, and {seed_kind.result}. Their shared work showed that {disagreement.lesson.lower()}",
        ),
        QAItem(
            question="What was special about the weather?",
            answer=f"It was {weather.name}. The friends had to work carefully because {weather.danger.lower()}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why do people bury seeds?",
            answer="People bury seeds in soil so the seeds can stay protected while their roots and shoots begin to grow.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people share a plan, divide the work, and help one another reach a goal.",
        ),
        QAItem(
            question="Why should a seed be covered gently?",
            answer="A seed should be covered gently so it stays in place and has room to receive air and water.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        details = [f"location={entity.location}"]
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:8} ({entity.type:8}) " + " ".join(details))
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(f"  buried: {world.facts.get('buried')}")
    lines.append(f"  teamwork: {world.facts.get('teamwork')}")
    return "\n".join(lines)


ASP_RULES = r"""
place(garden).
feature(teamwork).
action(bury).
valid(garden,teamwork,bury).

safe_burial :- valid(garden,teamwork,bury).
shared_growth :- safe_burial.
#show valid/3.
#show safe_burial/0.
#show shared_growth/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "garden"),
            asp.fact("feature", "teamwork"),
            asp.fact("action", "bury"),
        ]
    )


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected != actual:
        print("MISMATCH between Python and ASP valid combinations.")
        print("Only in Python:", sorted(expected - actual))
        print("Only in ASP:", sorted(actual - expected))
        return 1

    sample = generate(
        StoryParams(
            child_a="Mara",
            child_b="Tavi",
            helper="the old gardener",
            weather="morning_rain",
            seed_kind="sunflower",
            disagreement="same_spot",
            ending="bees",
        )
    )
    if "teamwork" not in sample.story.lower() or "buried" not in sample.story.lower():
        print("Generated story failed the teamwork/bury exercise.")
        return 1
    if not sample.world.facts["teamwork"] or not sample.world.facts["buried"]:
        print("Generated world failed its state checks.")
        return 1

    print("OK: ASP/Python parity and generated-story checks passed.")
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


def show_qa_item(item: QAItem) -> str:
    return f"Q: {item.question}\nA: {item.answer}"


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
        print()
        print(dump_trace(sample.world))
    if qa:
        for index, prompt in enumerate(sample.prompts, 1):
            print()
            print(f"[Prompt {index}] {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print()
            print(show_qa_item(item))


CURATED = [
    StoryParams(
        child_a="Mara",
        child_b="Tavi",
        helper="the old gardener",
        weather="morning_rain",
        seed_kind="sunflower",
        disagreement="same_spot",
        ending="bees",
    ),
    StoryParams(
        child_a="Nia",
        child_b="Oren",
        helper="the patient groundskeeper",
        weather="wind",
        seed_kind="bean",
        disagreement="best_tool",
        ending="shade",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3.\n#show safe_burial/0.\n#show shared_growth/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            current_seed = base_seed + attempt
            attempt += 1
            try:
                params = resolve_params(args, random.Random(current_seed))
            except StoryError as error:
                print(error)
                return
            params.seed = current_seed
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
