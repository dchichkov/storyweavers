#!/usr/bin/env python3
"""A child-facing pirate tale about a raccoon, a beehive, and a magical text."""

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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    setting: str = "the Moonlit Cove"
    captain_name: str = "Luna"
    raccoon_name: str = "Patch"
    beehive: str = "the golden beehive"
    text: str = "the glowing text"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    opening: str
    danger: str
    failed: str
    clue: str
    spell: str
    jobs: tuple[str, str]
    transformation: str
    result: str
    lesson: str
    ending: str


SETTINGS = {
    "the Moonlit Cove": True,
    "the Whispering Island": True,
    "the Honey Harbor": True,
    "the Starboard Marsh": True,
}
NAMES = ["Luna", "Mara", "Pip", "Toby", "Nell", "Jasper", "Cora", "Finn"]
RACCOONS = ["Patch", "Bandit", "Pebble", "Stripe", "Clover"]
HIVES = [
    "the golden beehive",
    "the blue-roofed beehive",
    "the little honey hive",
    "the beehive under the palm",
]
TEXTS = [
    "the glowing text",
    "the silver text",
    "the tiny text on the map",
    "the honey-colored text",
]

SCENARIOS = [
    Scenario(
        "honey-lantern",
        "Captain Luna sailed toward a beehive that shone like a lantern",
        "a dark fog covered the safe path, and the raccoon could not see the hive",
        "rowing in circles made the fog curl thicker around the boat",
        "one line of text glimmered whenever the raccoon held it near a honeycomb",
        "By honey and moon, show the way; turn fear to light before the day!",
        ("held the text above the bow", "sniffed out the hive's warmest honeycomb"),
        "the text turned into a bright compass made of beeswax",
        "the compass led them safely through the fog without disturbing the bees",
        "magic is strongest when it helps friends care for a living home",
        "the beehive glowed like a small sun while the raccoon curled beside the new beeswax compass",
    ),
    Scenario(
        "stormy-hive",
        "a pirate storm tossed rain against a beehive lashed to the deck",
        "a loose rope dragged the hive toward the dark sea",
        "pulling harder only made the rope knot itself tighter",
        "the text showed a picture of two paws turning the knot backward",
        "Round the knot and make it light; change this trouble into flight!",
        ("steadied the hive with a folded sail", "followed the text and loosened the rope"),
        "the tight rope transformed into a soft golden ribbon",
        "the ribbon held the beehive safely while the storm sailed away",
        "a careful plan can transform a frightening tangle",
        "the beehive rested on the deck, wrapped in a golden ribbon beneath a clear sky",
    ),
    Scenario(
        "missing-honey",
        "the crew found an empty honey jar beside the beehive",
        "the raccoon worried that hungry bees would have no sweetness for winter",
        "searching alone made the crew miss the tiny trail behind a barrel",
        "the text formed an arrow pointing toward wildflowers beyond the cove",
        "Flower and bee, wake sweetness bright; grow a feast in golden light!",
        ("followed the arrow along the shore", "carried water to the thirsty flowers"),
        "the sandy shore transformed into a small garden of bright flowers",
        "the bees found nectar, and the hive hummed happily again",
        "helping a home grow is better than simply taking its treasure",
        "flowers ringed the beehive, and the raccoon shared one careful spoonful of honey",
    ),
    Scenario(
        "moon-map",
        "Captain Luna discovered a text-map tucked beneath a beehive",
        "the map's letters jumped about whenever the raccoon tried to read them",
        "chasing the letters sent the crew toward a reef",
        "the letters settled when everyone spoke in a calm whisper",
        "Quiet words and moonlit ink, change these letters as we think!",
        ("held the map flat beside the hive", "read each line slowly and listened for the hum"),
        "the scattered letters transformed into a map of safe stars",
        "the star-map guided the ship past the reef to a sheltered beach",
        "patience can turn confusion into a path",
        "the beehive hummed under the stars while the finished map shone on the captain's lap",
    ),
    Scenario(
        "golden-gate",
        "a beehive stood before a gate made of old pirate coins",
        "the gate would not open, and the raccoon was trapped on the wrong side",
        "pushing the coins made them clatter farther out of reach",
        "the text said the gate opened only when a helper was thanked",
        "Thank the bees and speak their name; turn this locked gate into a game!",
        ("offered the bees fresh flowers", "read a thankful message from the text"),
        "the coin gate transformed into a low wooden bridge",
        "the raccoon crossed safely and returned the flowers to the hive",
        "gratitude can open a way that force cannot",
        "the wooden bridge curved over the stream, with a thank-you flag beside the beehive",
    ),
    Scenario(
        "sleeping-swarm",
        "the crew guarded a beehive while its bees slept beneath the moon",
        "a noisy treasure chest began to bang beside the hive",
        "dragging the chest made its rusty lid bang even louder",
        "the text showed a soft feather placed under each hinge",
        "Quiet as foam, gentle and slow; make this noisy chest hush and glow!",
        ("cushioned the chest with a sailcloth", "slid feathers beneath the hinges"),
        "the chest transformed into a silent wooden flower box",
        "the sleeping bees rested peacefully until morning",
        "protecting peaceful neighbors is a treasure worth more than gold",
        "a flower box bloomed beside the quiet beehive as the raccoon stood watch",
    ),
    Scenario(
        "rainbow-honey",
        "a rainbow arched over the beehive after a long voyage",
        "the hive's honey had turned gray and dull",
        "stirring it quickly mixed the colors into a cloudy swirl",
        "the text named three flowers that grew where the rainbow touched land",
        "Red, blue, and yellow glow; change this honey, let colors flow!",
        ("gathered petals without harming their stems", "held the text beneath the rainbow"),
        "the gray honey transformed into jars of rainbow gold",
        "the bees danced, and the crew shared the bright honey at supper",
        "a gentle transformation can restore joy to a tired home",
        "rainbow jars sparkled beside the beehive while every sailor smiled",
    ),
    Scenario(
        "raccoon-captain",
        "the raccoon found a tiny captain's hat beside the beehive",
        "the hat was too small, and the raccoon felt left out of the voyage",
        "stretching the hat tore its silver feather",
        "the text promised that a true captain wears a kind heart first",
        "Kind heart, brave paws, shine like new; change this little hat for you!",
        ("mended the feather with a thread of sail", "read the text aloud to the crew"),
        "the hat transformed into a warm, perfectly fitting captain's cap",
        "the raccoon guided everyone home through the moonlit water",
        "leadership grows from kindness, not from wearing the biggest hat",
        "the new cap rested on the raccoon's head as the beehive waved its bees goodbye",
    ),
    Scenario(
        "island-message",
        "a bottle washed ashore with text about a beehive in trouble",
        "the message was too faint for anyone to read",
        "scrubbing the paper made more letters disappear",
        "a drop of honey revealed hidden words without tearing the page",
        "Honey drop and friendly light; make lost words return tonight!",
        ("held the paper above a lantern", "placed one careful drop of honey on the faded line"),
        "the faint text transformed into a clear rescue message",
        "the crew found the hive and carried it to a sunny garden",
        "gentle care can reveal what hurried hands would destroy",
        "the rescued beehive hummed in its garden while the clear message dried nearby",
    ),
    Scenario(
        "three-bell-bees",
        "three bees rang tiny bells around a beehive",
        "their bells sounded different signals, and the crew did not know which way to sail",
        "following every bell at once sent the ship toward a sandbar",
        "the text matched one bell to the safe channel",
        "Bell and bee, ring clear and true; change our course to what is good for you!",
        ("marked the safe channel with a blue flag", "listened for the bell named in the text"),
        "the three bells transformed into one clear harbor chime",
        "the ship reached calm water, and the bees returned to their hive",
        "listening carefully can turn many warnings into one wise choice",
        "one clear chime floated over the calm harbor as the beehive gleamed",
    ),
    Scenario(
        "honeybridge",
        "the crew needed to cross a stream beside the beehive",
        "the old bridge broke, leaving the raccoon on the far bank",
        "jumping from stone to stone sent the raccoon into the cold water",
        "the text described strong reeds growing near the hive",
        "Reed and root, twist and bind; make a bridge for every kind!",
        ("gathered reeds with permission from the bees", "tied them across the stream with soft vine"),
        "the reeds transformed into a sturdy honey-colored bridge",
        "the raccoon crossed dry and brought the hive a fresh flower",
        "a bridge matters most when it helps everyone cross",
        "the new bridge shone beside the beehive, and dry paws tapped across it",
    ),
    Scenario(
        "happy-harbor",
        "the crew promised to return a beehive to its sunny harbor",
        "the harbor gate was shut before they arrived",
        "calling louder woke the gulls but did not open the gate",
        "the text revealed a small bell hidden under the dock",
        "Ring the bell and share the cheer; turn this harbor bright and clear!",
        ("carried the beehive away from the noisy gulls", "rang the hidden bell once and waited"),
        "the harbor gate transformed into a welcoming flower arch",
        "the hive returned home, and every bee circled the arch in greeting",
        "a happy ending grows when everyone reaches a safe home",
        "the beehive hummed beneath the flower arch while the raccoon waved from the returning ship",
    ),
]


def generate_world(p: StoryParams) -> World:
    if p.captain_name == p.raccoon_name:
        raise StoryError("The captain and raccoon must have different names.")
    if p.setting not in SETTINGS:
        raise StoryError("The setting must be one of the registered pirate locations.")
    world = World(p.setting)
    captain = world.add(Entity("captain", "character", p.captain_name))
    raccoon = world.add(Entity("raccoon", "animal", p.raccoon_name))
    hive = world.add(Entity("hive", "living_home", p.beehive))
    message = world.add(Entity("text", "magic_text", p.text))
    index = abs(p.seed or 0) % len(SCENARIOS)
    scenario = SCENARIOS[index]

    world.say(
        f"In {p.setting}, {captain.label} sailed with {raccoon.label} and a precious "
        f"cargo: {hive.label}."
    )
    world.say(f"At dawn, {scenario.opening}. The only clue was {message.label}.")
    world.say(f"Then {scenario.danger}.")
    world.para()
    world.say(f"{captain.label} called, \"{scenario.spell}\"")
    world.say(f"{raccoon.label} answered, \"I will help, Captain. Let us read the text together.\"")
    world.say(f"At first, {scenario.failed}.")
    world.say(f"Then {raccoon.label} noticed that {scenario.clue}.")
    world.para()
    world.say(
        f"\"The words have changed our plan,\" said {captain.label}. "
        f"\"We need two careful jobs.\""
    )
    world.say(f"{captain.label} {scenario.jobs[0]}, while {raccoon.label} {scenario.jobs[1]}.")
    world.say(f"The magic began: {scenario.transformation}.")
    world.say(f"{raccoon.label} cried, \"It worked!\" {scenario.result.capitalize()}.")
    world.para()
    world.say(
        f"The voyage ended happily because {scenario.lesson}. "
        f"{captain.label} thanked {raccoon.label}, and the bees buzzed a tiny sea shanty."
    )
    world.say(f"In the final picture, {scenario.ending}.")

    captain.memes.update(bravery=1.0, kindness=1.0, leadership=1.0)
    raccoon.memes.update(bravery=1.0, helpfulness=1.0, belonging=1.0)
    hive.meters.update(safe=1.0, home=1.0)
    message.meters.update(readable=1.0, magical=1.0, transformed=1.0)
    world.facts.update(
        captain=captain.label,
        raccoon=raccoon.label,
        hive=hive.label,
        text=message.label,
        scenario=scenario.key,
        danger=scenario.danger,
        failed=scenario.failed,
        clue=scenario.clue,
        spell=scenario.spell,
        first_job=scenario.jobs[0],
        second_job=scenario.jobs[1],
        transformation=scenario.transformation,
        result=scenario.result,
        lesson=scenario.lesson,
        ending=scenario.ending,
        happy=True,
        magical=True,
        transformed=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What danger threatened {f['hive']}?",
            answer=f"The danger was that {f['danger']}. This put the beehive and its bees at risk.",
        ),
        QAItem(
            question=f"What did {f['raccoon']} discover about {f['text']}?",
            answer=f"{f['raccoon']} discovered that {f['clue']}. The clue showed the friends how to use the magic safely.",
        ),
        QAItem(
            question="How did the captain and raccoon divide the work?",
            answer=f"{f['captain']} {f['first_job']}, while {f['raccoon']} {f['second_job']}. Their two jobs made the rescue possible.",
        ),
        QAItem(
            question="What magical transformation solved the problem?",
            answer=f"{f['transformation']}. After the transformation, {f['result']}.",
        ),
        QAItem(
            question="Why did the story have a happy ending?",
            answer=f"The ending was happy because {f['lesson']}. In the final scene, {f['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beehive?",
            answer="A beehive is a home where bees live together, raise young bees, and store honey.",
        ),
        QAItem(
            question="What is a raccoon?",
            answer="A raccoon is a clever mammal with a ringed tail and nimble paws.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is an imagined power that can make unusual changes, such as turning one helpful object into another.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a change from one form or condition into another.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending resolves the danger and shows the characters safe, wiser, or caring for one another.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a pirate tale about {f['captain']} and {f['raccoon']} protecting {f['hive']}.",
        f"Tell a magical transformation story in which {f['text']} reveals a way to save the beehive.",
        "Create a child-friendly happy ending where teamwork brings a magical rescue.",
    ]


ASP_RULES = r"""
safe_hive(H) :- hive(H), protected(H), home(H).
magic_change(T) :- text(T), magical(T), transformed(T).
happy_ending(H,T) :- safe_hive(H), magic_change(T), shared_work.
#show safe_hive/1.
#show magic_change/1.
#show happy_ending/2.
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("hive", "golden_hive"),
        asp.fact("protected", "golden_hive"),
        asp.fact("home", "golden_hive"),
        asp.fact("text", "glowing_text"),
        asp.fact("magical", "glowing_text"),
        asp.fact("transformed", "glowing_text"),
        asp.fact("shared_work"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program("#show happy_ending/2."))
    found = asp.atoms(symbols, "happy_ending")
    if found:
        print("OK: ASP found a safe magical happy ending.")
        return 0
    print("MISMATCH: ASP found no happy ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--captain-name")
    parser.add_argument("--raccoon-name")
    parser.add_argument("--beehive", choices=HIVES)
    parser.add_argument("--text", choices=TEXTS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain = args.captain_name or rng.choice(NAMES)
    raccoon = args.raccoon_name or rng.choice([name for name in RACCOONS if name != captain])
    if captain == raccoon:
        raise StoryError("The captain and raccoon must have different names.")
    return StoryParams(
        setting=args.setting or rng.choice(sorted(SETTINGS)),
        captain_name=captain,
        raccoon_name=raccoon,
        beehive=args.beehive or rng.choice(HIVES),
        text=args.text or rng.choice(TEXTS),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("the Moonlit Cove", "Luna", "Patch", "the golden beehive", "the glowing text", 0),
    StoryParams("the Whispering Island", "Mara", "Bandit", "the blue-roofed beehive", "the silver text", 3),
    StoryParams("the Honey Harbor", "Pip", "Pebble", "the little honey hive", "the tiny text on the map", 7),
]


def emit(sample: StorySample, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        facts = sample.world.facts
        print(
            "\n--- world model state ---\n"
            f"scenario={facts['scenario']} happy={facts['happy']} "
            f"magical={facts['magical']} transformed={facts['transformed']}"
        )
    if qa:
        for index, item in enumerate(sample.story_qa, 1):
            print(f"Q{index}: {item.question}\nA{index}: {item.answer}")
        for index, item in enumerate(sample.world_qa, 1):
            print(f"W{index}: {item.question}\nA{index}: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_hive/1. #show magic_change/1. #show happy_ending/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        print(asp_program("#show safe_hive/1. #show magic_change/1. #show happy_ending/2."))
        for symbol in asp.one_model(asp_program("#show safe_hive/1. #show magic_change/1. #show happy_ending/2.")):
            print(symbol)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("The number of stories must be at least one.")
        for index in range(args.n):
            params = resolve_params(args, random.Random(base + index))
            params.seed = base + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], ensure_ascii=False, indent=2))
        return

    for index, sample in enumerate(samples):
        emit(sample, args.trace, args.qa, f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
