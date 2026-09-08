#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "community garden": {
        "setting": "the community garden",
        "soil": "rich",
        "water": "rain barrels",
        "landmark": "the old fig tree",
    },
    "roof garden": {
        "setting": "the rooftop community garden",
        "soil": "deep planters",
        "water": "a modern drip system",
        "landmark": "the bright greenhouse",
    },
    "river garden": {
        "setting": "the community garden beside the river",
        "soil": "dark and damp",
        "water": "a solar pump",
        "landmark": "the willow arch",
    },
}

CHARACTERS = ("Luna", "Milo", "Nia", "Tariq", "Sora", "Pip", "Ivy", "Jules")
MOODS = ("curious", "patient", "brave", "careful", "hopeful")
CROPS = ("beans", "tomatoes", "pumpkins", "lettuces", "sunflowers")
TOOLS = ("a hand trowel", "a blue watering can", "a garden cart", "a coil of hose")
MYTHIC_NAMES = (
    "the Silver River Beneath",
    "the Hidden Green Thread",
    "the Moonlit Garden River",
    "the Root-Water Path",
)

TALES = (
    {
        "title": "The Thirsty Patch",
        "opening": "On the hottest morning of summer, one bed of seedlings began to wilt even though the garden's water barrels were full.",
        "sign": "pale leaves curled in a winding line from the bean bed toward the compost corner",
        "wrong": "thought a tiny underground river spirit had stolen the water",
        "turn": "the winding line followed a clogged root-and-soil channel rather than a magical thief",
        "action": "worked in pairs to loosen the soil, clear the blocked channel, and guide water gently toward the roots",
        "result": "the seedlings lifted their leaves before sunset",
        "lesson": "a hidden system can serve a whole community, and teamwork can help it flow again",
        "ending": "That evening, the bean leaves shone like little green hands raised together to the sky.",
    },
    {
        "title": "The Lantern Under the Soil",
        "opening": "Every night, a small garden lamp blinked beneath the old fig tree, although no wire ran there.",
        "sign": "the blinking followed the pulse of water moving from one planting bed to another",
        "wrong": "believed a buried moon-lantern was calling roots to a secret feast",
        "turn": "the light came from a modern moisture sensor reading the living network below the soil",
        "action": "shared observations, checked the sensor map, and repaired its loose solar connection",
        "result": "the lamp began showing which beds needed water instead of blinking at random",
        "lesson": "modern tools can reveal old natural patterns when people use them together",
        "ending": "Under the fig tree, the little lamp glowed steadily, as if the garden had found its heartbeat.",
    },
    {
        "title": "The Garden That Shared",
        "opening": "A storm washed one corner of the garden bare while the far beds stayed green.",
        "sign": "fine roots and pale threads crossed the soil between the surviving plants",
        "wrong": "thought the strongest plants had hidden the rain from their smaller neighbors",
        "turn": "the threads were part of a living lymphatic-like network that helped move fluid and support healing soil",
        "action": "rebuilt the washed bed, spread compost, and planted a shared border of clover and herbs",
        "result": "the garden recovered together instead of leaving one corner behind",
        "lesson": "strength becomes more useful when it is shared",
        "ending": "By the next moon, the bare corner wore a green necklace of clover around every new sprout.",
    },
    {
        "title": "The Quiet Swelling",
        "opening": "A pumpkin vine swelled strangely near the path, and the gardeners worried that something harmful was trapped inside it.",
        "sign": "the swelling softened after water drained through a line of tiny channels",
        "wrong": "imagined a sleeping stone giant beneath the vine",
        "turn": "the channels acted like a simple garden lesson about the lymphatic system, carrying extra fluid away",
        "action": "marked the area, improved drainage, and asked the garden mentor to inspect the vine",
        "result": "the vine returned to a healthy shape and continued climbing its trellis",
        "lesson": "careful observation and shared help can turn a frightening mystery into useful knowledge",
        "ending": "The pumpkin vine curled upward, holding one golden fruit like a lantern above the path.",
    },
)

DIALOGUES = (
    ("The garden is trying to tell us something", "Then let us listen together before we guess"),
    ("I think a hidden spirit did this", "Maybe, but our clues should tell us what kind of spirit it is"),
    ("Can teamwork really change what is under the soil", "We can change what reaches it, and we can learn how it works"),
    ("The old story says roots drink alone", "Our garden keeps showing us that living things are connected"),
    ("Should we fix the bed first or study it first", "We can study safely while we help the plants"),
)

OPENINGS = (
    "Long ago, people said every garden had a secret river beneath it.",
    "In the newest garden in town, an ancient-looking mystery appeared.",
    "At sunrise, the community garden seemed to breathe beneath its beds.",
    "The gardeners had modern tools, but the soil still kept old secrets.",
)

ASP_RULES = r"""
kind(lymphatic).
kind(modern).
kind(teamwork).
kind(myth).
kind(community_garden).

feature(lymphatic) :- kind(lymphatic).
feature(modern) :- kind(modern).
feature(teamwork) :- kind(teamwork).
feature(myth) :- kind(myth).
feature(community_garden) :- kind(community_garden).

compatible_story(P) :-
    place(P),
    supports_lymphatic(P),
    has_modern_tool(P),
    teamwork_required(P),
    mythic(P).

place("community_garden").
place("roof_garden").
place("river_garden").

supports_lymphatic("community_garden").
supports_lymphatic("roof_garden").
supports_lymphatic("river_garden").

has_modern_tool("community_garden").
has_modern_tool("roof_garden").
has_modern_tool("river_garden").

teamwork_required("community_garden").
teamwork_required("roof_garden").
teamwork_required("river_garden").

mythic("community_garden").
mythic("roof_garden").
mythic("river_garden").

#show compatible_story/1.
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    partner: str
    crop: str
    tool: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mythic modern storyworld about the lymphatic garden and teamwork."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero")
    parser.add_argument("--partner")
    parser.add_argument("--crop", choices=CROPS)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("--mood", choices=MOODS)
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


def asp_facts() -> str:
    import asp

    return "\n".join(
        asp.fact("place", place.replace(" ", "_"))
        for place in PLACES
    ) + "\n" + "\n".join(
        asp.fact(predicate, place.replace(" ", "_"))
        for predicate in ("supports_lymphatic", "has_modern_tool", "teamwork_required", "mythic")
        for place in PLACES
    )


def asp_program(show: str = "#show compatible_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatibilities() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "compatible_story"))


def asp_verify() -> int:
    expected = {(place.replace(" ", "_"),) for place in PLACES}
    actual = asp_compatibilities()
    if expected != actual:
        print("MISMATCH:")
        print("only in clingo:", sorted(actual - expected))
        print("only in python:", sorted(expected - actual))
        return 1
    print(f"OK: clingo gate matches Python reasoning ({len(actual)} places).")
    for params in curated_params():
        sample = generate(params)
        if not sample.story or "teamwork" not in sample.story.lower():
            print("MISMATCH: generated story failed its teamwork check.")
            return 1
    print("OK: generated stories passed.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(CHARACTERS)
    partner = args.partner or rng.choice([name for name in CHARACTERS if name != hero])
    crop = args.crop or rng.choice(CROPS)
    tool = args.tool or rng.choice(TOOLS)
    mood = args.mood or rng.choice(MOODS)

    if place not in PLACES:
        raise StoryError(f"Unknown garden place: {place}.")
    if hero == partner:
        raise StoryError("The hero and partner must be different characters.")
    return StoryParams(place, hero, partner, crop, tool, mood, args.seed)


def story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join(
        (params.place, params.hero, params.partner, params.crop, params.tool, params.mood)
    )
    return int.from_bytes(hashlib.blake2b(text.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("A story must take place in a registered community garden.")
    if params.hero == params.partner:
        raise StoryError("Teamwork requires two different characters.")

    seed = story_seed(params)
    rng = random.Random(seed)
    place = PLACES[params.place]
    tale = TALES[seed % len(TALES)]
    opening = OPENINGS[(seed // len(TALES)) % len(OPENINGS)]
    dialogue = DIALOGUES[(seed // (len(TALES) * len(OPENINGS))) % len(DIALOGUES)]
    myth_name = MYTHIC_NAMES[(seed // 17) % len(MYTHIC_NAMES)]
    extra = rng.choice(
        (
            "They carried a notebook, a trowel, and respect for every living thing in the soil.",
            "Their garden rule was simple: no one solved a mystery by working alone.",
            "They had learned that even a modern garden could hold an ancient-looking wonder.",
        )
    )

    world = World(place=place["setting"])
    hero = Entity(
        id=params.hero,
        kind="character",
        label="young gardener",
        type="human",
        meters={"energy": 1.0, "distance_to_bed": 2.0},
        memes={"curiosity": 1.0, "trust": 0.8},
        location=params.place,
    )
    partner = Entity(
        id=params.partner,
        kind="character",
        label="garden partner",
        type="human",
        meters={"energy": 1.0, "distance_to_bed": 2.0},
        memes={"curiosity": 0.8, "trust": 0.9},
        location=params.place,
    )
    crop = Entity(
        id="crop",
        kind="plant",
        label=f"{params.crop} bed",
        type="crop",
        meters={"water_flow": 0.25, "health": 0.45},
        memes={"shared_care": 0.2},
        location=params.place,
    )
    sensor = Entity(
        id="sensor",
        kind="tool",
        label="modern moisture sensor",
        type="sensor",
        meters={"battery": 0.9},
        memes={"reveals_hidden_flow": 1.0},
        location=params.place,
    )
    world.entities = {entity.id: entity for entity in (hero, partner, crop, sensor)}

    world.say(opening)
    world.say(
        f"{params.hero}, a {params.mood} gardener, entered {world.place} with {params.partner} to tend the {params.crop} bed."
    )
    world.say(extra)
    world.say(
        f"The garden had {place['soil']} soil, {place['water']}, and {place['landmark']} watching over the paths."
    )

    world.para()
    world.say(tale["opening"])
    world.say(
        f"Near the plants, they noticed that {tale['sign']}. "
        f"The modern sensor blinked beside {params.tool}."
    )
    world.say(
        f"{params.partner} {tale['wrong']}, while {params.hero} wondered whether the old tale of {myth_name} might be true."
    )
    world.say(f"'{dialogue[0]},' said {params.hero}. '{dialogue[1]},' answered {params.partner}.")
    world.say(
        f"They did not rush. Together they checked the soil, the water, and the leaves while keeping the plants safe."
    )

    world.para()
    world.say(
        f"Then the sensor showed that {tale['turn']}. "
        "In a living garden, the lymphatic system is a useful comparison: it moves extra fluid and helps protect the body, while plants and soil have their own ways of moving water."
    )
    world.say(
        f"{params.hero} held the sensor steady, and {params.partner} used {params.tool}. "
        f"By sharing every small task, they {tale['action']}."
    )
    world.say(
        f"The hidden flow changed, and {tale['result']}. "
        "The gardeners understood that the mystery was not solved by one clever person, but by careful teamwork."
    )

    world.para()
    world.say(
        f"From that day on, they called the garden's unseen network {myth_name}. "
        f"They remembered that the real magic was {tale['lesson']}."
    )
    world.say(tale["ending"])

    hero.meters["energy"] = 0.65
    partner.meters["energy"] = 0.65
    crop.meters["water_flow"] = 0.9
    crop.meters["health"] = 0.95
    hero.memes["teamwork"] = 1.0
    partner.memes["teamwork"] = 1.0
    crop.memes["shared_care"] = 1.0
    sensor.memes["useful_reading"] = 1.0

    world.trace = [
        f"noticed:{tale['sign']}",
        f"questioned:{tale['wrong']}",
        f"measured:{tale['turn']}",
        f"cooperated:{tale['action']}",
        f"resolved:{tale['result']}",
    ]
    world.facts = {
        "setting": place["setting"],
        "hero": params.hero,
        "partner": params.partner,
        "crop": params.crop,
        "tool": params.tool,
        "tale": tale["title"],
        "myth_name": myth_name,
        "lymphatic_connection": "The lymphatic system moves extra fluid and supports protection in the body.",
        "turn": tale["turn"],
        "resolution": tale["result"],
        "lesson": tale["lesson"],
    }

    prompts = [
        f"Tell a myth-like modern story about lymphatic flow and teamwork in {place['setting']}.",
        f"Write how {params.hero} and {params.partner} use a modern garden tool to understand the {params.crop} bed.",
        f"Create a gentle garden myth named {myth_name} that ends with shared care.",
    ]
    story_qa = [
        QAItem(
            question=f"Where did {params.hero} and {params.partner} find the mystery?",
            answer=f"They found it in {place['setting']}, near the {params.crop} bed and {place['landmark']}."
        ),
        QAItem(
            question="What did the modern sensor help the gardeners discover?",
            answer=f"It helped them discover that {tale['turn'].capitalize()}."
        ),
        QAItem(
            question="How did teamwork change the outcome?",
            answer=f"They divided the work and {tale['action']}. As a result, {tale['result']}."
        ),
        QAItem(
            question="Why was the lymphatic idea useful in the story?",
            answer="It gave the gardeners a way to think about hidden channels that move extra fluid and help protect living systems."
        ),
        QAItem(
            question="What lesson did the garden teach?",
            answer=f"The garden taught that {tale['lesson']}."
        ),
    ]
    world_qa = [
        QAItem(
            question="What is the lymphatic system?",
            answer="The lymphatic system is a body-wide network of vessels, tissues, and organs that helps move extra fluid and supports the immune system."
        ),
        QAItem(
            question="Why can modern tools help gardeners?",
            answer="Modern tools such as moisture sensors can reveal conditions under the soil, helping gardeners make careful decisions."
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people share tasks, listen to one another, and combine their efforts to reach a goal."
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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"  {entity.id}: {entity.kind}; location={entity.location}; "
                f"meters={entity.meters}; memes={entity.memes}"
            )
        for item in sample.world.trace:
            print(f"  event: {item}")
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


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("community garden", "Luna", "Milo", "beans", "a hand trowel", "curious"),
        StoryParams("roof garden", "Nia", "Tariq", "tomatoes", "a garden cart", "patient"),
        StoryParams("river garden", "Sora", "Ivy", "pumpkins", "a coil of hose", "brave"),
    ]


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
        print(asp.atoms(model, "compatible_story"))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in curated_params()]
    else:
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            local = argparse.Namespace(
                place=args.place,
                hero=args.hero,
                partner=args.partner,
                crop=args.crop,
                tool=args.tool,
                mood=args.mood,
                seed=(args.seed + index if args.seed is not None else rng.randrange(2**31)),
            )
            params = resolve_params(local, random.Random(local.seed))
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
