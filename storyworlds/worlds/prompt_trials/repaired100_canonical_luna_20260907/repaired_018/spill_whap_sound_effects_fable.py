#!/usr/bin/env python3
"""
A small fable storyworld about a spill, a comic whap, and the lesson that
careful listening can turn a mishap into a useful invention.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "results.py").is_file()
)
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


ANIMALS = ["fox", "rabbit", "badger", "squirrel", "hedgehog", "mouse"]
HERO_NAMES = ["Luna", "Milo", "Tess", "Pip", "Nell", "Otis"]
HELPER_NAMES = ["Old Oak", "Mara", "Bramble", "Aunt Fern", "Wren"]
PLACES = ["the berry path", "the little meadow", "the acorn bridge", "the moonlit grove"]

SOUND_EFFECTS = ["whap", "plop", "drip-drop", "tap-tap", "swish", "thump"]
MORALS = [
    "A loud mistake may be a quiet clue.",
    "The ear that listens well can mend what the hand has spilled.",
    "A careful pause can turn a blunder into a blessing.",
    "One small sound may tell a large truth.",
]


@dataclass
class StoryParams:
    animal: str
    hero: str
    helper: str
    place: str
    sound: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass(frozen=True)
class Arc:
    treasure: str
    spill: str
    mistaken_belief: str
    whap_cause: str
    clue: str
    test: str
    repair: str
    result: str
    ending: str
    lesson_line: str


ARCS = [
    Arc(
        treasure="a jar of golden honey",
        spill="the jar tipped, and honey made a shining spill across the berry path",
        mistaken_belief="a greedy crow had knocked the jar down",
        whap_cause="the jar had bumped a low branch when the basket swung",
        clue="a sticky leaf trembled above the spill",
        test="lifted the basket slowly and heard the branch brush its rim",
        repair="made a leaf-lined channel that guided the honey into a clean bowl",
        result="the bees could gather the sweet drops without crawling through the mud",
        ending="the honey bowl glowed beneath the branch, while the cleaned path smelled like summer",
        lesson_line="The whap told us where the careless swing had touched the tree.",
    ),
    Arc(
        treasure="a cup of blue paint",
        spill="the cup fell, and a blue spill ran toward the meadow stones",
        mistaken_belief="the wind had blown the paint away",
        whap_cause="the cup struck a hidden root beneath the grass",
        clue="one round root wore a fresh blue mark",
        test="rolled a pebble beside the root and heard the same hollow knock",
        repair="set the paint on a flat stone and marked the root with bright ribbons",
        result="the next blue path stayed neat and easy to follow",
        ending="a blue trail curled around the root like a river that had learned good manners",
        lesson_line="A whap can point to a hidden bump, if we listen before we blame the wind.",
    ),
    Arc(
        treasure="a bowl of warm porridge",
        spill="the bowl slipped, and porridge spread in a soft yellow spill",
        mistaken_belief="the hungry badger had tugged the tablecloth",
        whap_cause="a short table leg had tapped a stone underneath",
        clue="the table wobbled whenever its corner touched the ground",
        test="pressed each leg gently and heard one small whap from the stony corner",
        repair="placed a flat bark chip beneath the short leg",
        result="the table stood firm enough for every hungry neighbor",
        ending="steam rose from a fresh bowl, and nobody had to chase breakfast downhill",
        lesson_line="A little whap under a table may be asking for a little support.",
    ),
    Arc(
        treasure="a pouch of moon seeds",
        spill="the pouch opened, and silver seeds spilled through the grass",
        mistaken_belief="the night breeze had stolen the seeds",
        whap_cause="the pouch clasp had struck the hollow seed basket",
        clue="the basket rang whenever the pouch swung near it",
        test="swung the empty pouch once and heard the bright whap again",
        repair="tied the pouch to a soft cloth loop away from the basket",
        result="the moon seeds stayed together for planting",
        ending="tiny silver sprouts later shone beside the path like stars underfoot",
        lesson_line="When a sound repeats, it may be showing us the path to the cause.",
    ),
    Arc(
        treasure="a basket of ripe apples",
        spill="one apple rolled free, then another, and the basket made a red spill",
        mistaken_belief="the apples had escaped because they were restless",
        whap_cause="a loose basket slat struck the cart wheel",
        clue="the slat clicked each time the cart turned",
        test="stopped the cart and tapped the slat with one finger",
        repair="wove a strip of willow around the loose slat",
        result="the apples stayed snug in their basket",
        ending="the cart rolled home with a red hill of apples and a quiet wheel",
        lesson_line="Even a proud basket needs a kind repair when it begins to whap.",
    ),
    Arc(
        treasure="a bottle of rainwater",
        spill="the bottle tipped, and a clear spill glittered beside the acorn bridge",
        mistaken_belief="the bridge itself had begun to leak",
        whap_cause="the bottle bumped the bridge rail",
        clue="the rail bore a round wet mark beside a small dent",
        test="held the bottle still and tapped the rail to hear the same sound",
        repair="wrapped the bottle in moss and carried it away from the rail",
        result="the bridge remained dry and the water reached the thirsty seedlings",
        ending="green shoots lifted their heads beside the bridge as the last drops sank into the soil",
        lesson_line="A wet mark and a whap together can tell a truer tale than a hurried guess.",
    ),
]


OPENINGS = [
    "{hero} the {animal} lived near {place}, where every creature knew that small things could make large trouble.",
    "Beside {place}, {hero} the {animal} carried important treasures with a brave heart and very careful paws.",
    "One bright morning at {place}, {hero} the {animal} set out to help the woodland neighbors.",
    "The creatures of {place} trusted {hero} the {animal}, though they knew {hero} sometimes hurried faster than wisdom.",
]

HUMOR = [
    "The frog declared that the honey had chosen a very sticky road.",
    "A beetle saluted the blue mark and called it the smallest pond in the forest.",
    "The rabbit said the table had given breakfast a surprising bounce.",
    "The owl blinked at the moon seeds and asked whether they had learned to fly.",
    "The smallest apple rolled in a circle, as if practicing for a parade.",
    "A pair of ants inspected the wet rail and announced that it was not a bridge puddle at all.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fable about a spill and a useful whap.")
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--sound", choices=SOUND_EFFECTS)
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
    animal = args.animal or rng.choice(ANIMALS)
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    place = args.place or rng.choice(PLACES)
    sound = args.sound or "whap"
    if sound not in SOUND_EFFECTS:
        raise StoryError(f"Unknown sound effect: {sound}")
    return StoryParams(animal=animal, hero=hero, helper=helper, place=place, sound=sound)


def build_world(params: StoryParams) -> World:
    world = World(params)
    world.add(
        Entity(
            id="hero",
            kind="character",
            label=params.hero,
            type=params.animal,
            memes={"curiosity": 1.0, "confidence": 0.7},
        )
    )
    world.add(
        Entity(
            id="helper",
            kind="character",
            label=params.helper,
            type="helper",
            memes={"patience": 1.0},
        )
    )
    world.add(
        Entity(
            id="basket",
            kind="thing",
            label="treasure basket",
            type="container",
            meters={"stability": 0.8},
        )
    )
    world.add(
        Entity(
            id="spill",
            kind="thing",
            label="spill",
            type="liquid_or_scattered_treasure",
            meters={"size": 0.0},
        )
    )
    return world


def story_variation(params: StoryParams) -> int:
    text = "|".join((params.animal, params.hero, params.helper, params.place, params.sound))
    seed = params.seed if params.seed is not None else sum((i + 1) * ord(c) for i, c in enumerate(text))
    return (seed * 97 + 31) % (len(ARCS) * len(OPENINGS) * len(HUMOR))


def generate_story(world: World) -> None:
    p = world.params
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    basket = world.entities["basket"]
    spill = world.entities["spill"]
    choice = story_variation(p)
    arc = ARCS[choice % len(ARCS)]
    choice //= len(ARCS)
    opening = OPENINGS[choice % len(OPENINGS)].format(
        hero=p.hero, animal=p.animal, place=p.place
    )
    choice //= len(OPENINGS)
    humor = HUMOR[choice % len(HUMOR)]
    sound = p.sound

    if sound != "whap":
        sound_line = f"The first sound was a {sound}, but soon the branch answered with a clear whap."
    else:
        sound_line = "Then the branch answered with a clear whap."

    world.say(opening)
    world.say(
        f"{p.hero} carried {arc.treasure} in the basket while {p.helper} watched the path. "
        f"'Slow paws make safe journeys,' said {p.helper}. "
        f"'And quick paws finish before lunch,' replied {p.hero}."
    )

    world.para()
    world.say(f"At the bend, {arc.spill}.")
    spill.meters["size"] = 1.0
    basket.meters["stability"] = 0.1
    hero.memes["surprise"] = 1.0
    world.facts["spill"] = arc.spill
    world.facts["mistaken_belief"] = arc.mistaken_belief
    world.say(
        f"{p.helper} gasped, 'Oh dear! {arc.mistaken_belief.capitalize()}!' "
        f"{p.hero} answered, 'I did not mean to make such a mess.'"
    )
    world.say(f"{p.hero} and {p.helper} first believed that {arc.mistaken_belief}.")

    world.para()
    world.say(f"Then the basket swung. {sound_line}")
    world.say(f"{p.helper} asked, 'Did you hear that whap?'")
    world.say(f"'I heard it,' said {p.hero}. 'Let us find where it came from.'")
    world.say(f"The clue was that {arc.clue}.")
    world.say(f"Together they {arc.test}.")
    world.say(f"Now the truth was plain: {arc.whap_cause}.")
    world.say(humor)
    helper.memes["patience"] = 2.0
    hero.memes["curiosity"] = 2.0
    world.facts.update(
        {
            "sound_effect": sound,
            "whap_cause": arc.whap_cause,
            "clue": arc.clue,
            "test": arc.test,
            "humor": humor,
        }
    )

    world.para()
    world.say(f"{p.hero} and {p.helper} worked together and {arc.repair}.")
    world.say(f"The spill was gathered safely, and {arc.result}.")
    world.say(f"{p.helper} smiled. '{arc.lesson_line}'")
    world.say(f"{p.hero} nodded. 'Next time, I will listen before I hurry.'")
    world.say(f"By sunset, {arc.ending}.")
    world.say(f"And the woodland learned: {MORALS[story_variation(p) % len(MORALS)]}")
    spill.meters["size"] = 0.0
    basket.meters["stability"] = 1.0
    hero.memes["pride"] = 1.0
    hero.memes["carefulness"] = 1.0
    world.facts.update(
        {
            "repair": arc.repair,
            "result": arc.result,
            "ending": arc.ending,
            "moral": MORALS[story_variation(p) % len(MORALS)],
            "settled": True,
        }
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a child-friendly fable about {p.hero} the {p.animal}, a spill at {p.place}, and a helpful whap.",
        f"Tell a fable with sound effects, including the word {p.sound} and the word whap, where careful listening solves a problem.",
        f"Create a short fable in which {p.hero} learns what caused a spill and ends with a clear moral.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What spilled during {p.hero}'s journey?",
            answer=f"{p.hero} was carrying a treasure, and {f['spill']}. The spill caused the woodland creatures to stop and investigate.",
        ),
        QAItem(
            question=f"What did {p.hero} and {p.helper} first believe caused the spill?",
            answer=f"They first believed that {f['mistaken_belief']}. They changed their minds after listening carefully to the whap.",
        ),
        QAItem(
            question="What caused the whap?",
            answer=f"The whap came from {f['whap_cause']}. The clue was that {f['clue']}, and the pair tested the idea by {f['test']}.",
        ),
        QAItem(
            question=f"How did {p.hero} and {p.helper} fix the trouble?",
            answer=f"They worked together and {f['repair']}. Then {f['result']}.",
        ),
        QAItem(
            question="What lesson did the fable teach?",
            answer=f"The fable taught that {f['moral'].lower()} Listening to a small sound helped the characters find a practical solution.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spill?",
            answer="A spill is liquid or loose material that accidentally spreads out of its container.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a written or performed sound that helps people imagine an action, such as whap, plop, or swish.",
        ),
        QAItem(
            question="Why is listening useful when something goes wrong?",
            answer="Listening can reveal where a sound came from and provide a clue about what happened.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with talking animals, that teaches a lesson or moral.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        bits = []
        if entity.meters:
            bits.append(f"meters={entity.meters}")
        if entity.memes:
            bits.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:8} ({entity.kind:10}) {entity.label} {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"P{index}: {prompt}")
        print()
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def generate(params: StoryParams) -> StorySample:
    if params.sound not in SOUND_EFFECTS:
        raise StoryError(f"Invalid sound effect {params.sound!r}. Choose a registered effect.")
    world = build_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def asp_facts() -> str:
    import asp

    lines = []
    for animal in ANIMALS:
        lines.append(asp.fact("animal", animal))
    for place in PLACES:
        lines.append(asp.fact("place", place.replace("the ", "").replace(" ", "_")))
    for sound in SOUND_EFFECTS:
        lines.append(asp.fact("sound_effect", sound.replace("-", "_")))
    lines.extend(
        [
            asp.fact("feature", "spill"),
            asp.fact("feature", "whap"),
            asp.fact("feature", "sound_effects"),
            asp.fact("feature", "fable"),
            asp.fact("feature", "repair"),
        ]
    )
    return "\n".join(lines)


ASP_RULES = r"""
story_domain(spill, whap, fable).
has_sound_effects :- sound_effect(_).
has_spill :- feature(spill).
has_whap :- feature(whap).
has_fable_style :- feature(fable).
reasonable :- has_sound_effects, has_spill, has_whap, has_fable_style.
#show reasonable/0.
#show story_domain/3.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    reasonable = set(asp.atoms(model, "reasonable"))
    domain = set(asp.atoms(model, "story_domain"))
    expected_domain = {("spill", "whap", "fable")}
    if reasonable == {()} and domain == expected_domain:
        for params in [
            StoryParams("fox", "Luna", "Old Oak", "the berry path", "whap", 1),
            StoryParams("rabbit", "Milo", "Wren", "the little meadow", "plop", 2),
        ]:
            sample = generate(params)
            if not sample.story or "whap" not in sample.story or "spill" not in sample.story:
                print("Generated story failed required feature check.")
                return 1
        print("OK: ASP parity and generated-story checks pass.")
        return 0
    print("Mismatch between ASP and Python story-domain facts.")
    return 1


CURATED = [
    StoryParams("fox", "Luna", "Old Oak", "the berry path", "whap"),
    StoryParams("rabbit", "Milo", "Wren", "the little meadow", "plop"),
    StoryParams("badger", "Tess", "Aunt Fern", "the acorn bridge", "thump"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/0.\n#show story_domain/3."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            sys.exit(1)
        model = asp.one_model(asp_program("#show reasonable/0.\n#show story_domain/3."))
        print(f"reasonable={len(asp.atoms(model, 'reasonable'))}")
        print(f"story_domain={len(asp.atoms(model, 'story_domain'))}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            seed = base_seed + index
            index += 1
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} the {p.animal} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
