#!/usr/bin/env python3
"""
A small animal storyworld about a multitude of forest creatures, a suspenseful
storm, and the courage to help one another.
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


@dataclass
class Animal:
    name: str
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "bravery": 0.0,
            "worry": 0.0,
            "trust": 0.0,
            "belonging": 0.0,
        }
    )


@dataclass
class World:
    setting: str
    animals: dict[str, Animal] = field(default_factory=dict)
    objects: dict[str, dict[str, object]] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add_animal(self, animal: Animal) -> Animal:
        self.animals[animal.name] = animal
        return animal

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    helper_name: str = "Moss"
    setting: str = "moonlit meadow"


@dataclass(frozen=True)
class SuspenseArc:
    key: str
    opening_sign: str
    danger: str
    false_move: str
    consequence: str
    clue: str
    brave_move: str
    cause: str
    rescue: str
    ending: str
    lesson: str


SETTINGS = {
    "moonlit meadow": {
        "place": "the moonlit meadow",
        "features": "silver grass, a shallow brook, and a circle of old stones",
    },
    "pine hollow": {
        "place": "the pine hollow",
        "features": "dark pine trunks, soft needles, and a narrow animal path",
    },
    "reed marsh": {
        "place": "the reed marsh",
        "features": "tall reeds, floating leaves, and a little wooden footbridge",
    },
}

HEROES = [
    ("Luna", "fox"),
    ("Pip", "rabbit"),
    ("Neri", "otter"),
    ("Mallow", "hedgehog"),
    ("Kito", "squirrel"),
]

HELPERS = [
    ("Moss", "badger"),
    ("Fern", "deer"),
    ("Bramble", "beaver"),
    ("Wren", "owl"),
    ("Clover", "mouse"),
]

ARCS = [
    SuspenseArc(
        key="fallen-bridge",
        opening_sign="the brook made a strange, hollow knocking sound",
        danger="the old branch bridge was bending above the rushing water",
        false_move="rushed onto the bridge to search for the missing fawn",
        consequence="a branch cracked, and the whole multitude of animals froze at the bank",
        clue="small wet hoofprints ended beneath a broad fern on the safe side of the brook",
        brave_move="asked the multitude to form a quiet line and checked the ferns from the ground",
        cause="the fawn had never crossed the brook; it had slipped into a ferny hollow while following a firefly",
        rescue="lowered a vine loop while the beaver braced the bank and the deer pulled gently",
        ending="the repaired bridge stood empty while the rescued fawn drank beside its mother",
        lesson="courage works best when it listens to evidence and includes others",
    ),
    SuspenseArc(
        key="storm-cave",
        opening_sign="a cold wind slipped through the grass although the sky was clear",
        danger="a sudden storm was racing toward the open meadow",
        false_move="called for every animal to scatter into the darkest hiding places",
        consequence="the multitude became separated, and frightened cries rose from every direction",
        clue="moss arrows on the stones pointed toward a wide cave behind the hill",
        brave_move="called the animals together and counted them while following the moss arrows",
        cause="the old cave had a dry chamber large enough for every animal to shelter safely",
        rescue="guided the smallest animals first, then waited at the entrance for the stragglers",
        ending="rain drummed outside while the multitude shared warm berries in the dry chamber",
        lesson="in danger, a calm plan can bring many different friends to safety",
    ),
    SuspenseArc(
        key="glowing-water",
        opening_sign="the pond began to glow beneath the reeds",
        danger="the glow hid a deep hole where the youngest animals liked to play",
        false_move="splashed straight toward the shining water",
        consequence="the mud swallowed one paw, and the nearby animals cried out in alarm",
        clue="a line of unbroken lily pads showed the firm path around the hole",
        brave_move="tested the bank with a long reed and marked the safe lily-pad route",
        cause="moonlight was shining through clear pond flowers, making the dangerous hollow look inviting",
        rescue="pulled the stuck paw free with a woven grass rope",
        ending="the pond still glowed, but a ring of stones warned everyone away from the hollow",
        lesson="a beautiful sight should still be examined carefully before it is trusted",
    ),
    SuspenseArc(
        key="silent-nest",
        opening_sign="the treetops suddenly became quiet",
        danger="a nest full of hatchlings had fallen near a sleeping fox den",
        false_move="shouted loudly to wake the whole forest",
        consequence="the sleeping fox stirred, and the hatchlings huddled beneath the leaves",
        clue="one pale feather pointed from the nest toward a low branch",
        brave_move="whispered instructions and used a fallen log as a quiet step",
        cause="the nest had been caught by a gust and carried safely beside the den",
        rescue="returned the nest to the low branch while the owl watched for danger",
        ending="the treetops filled with tiny chirps again above the peaceful den",
        lesson="gentle teamwork can solve a frightening problem without making it worse",
    ),
    SuspenseArc(
        key="bell-in-the-reeds",
        opening_sign="a tiny bell rang somewhere inside the reeds",
        danger="the sound came from a young lamb trapped on a sinking patch of marsh",
        false_move="charged through the reeds toward the ringing",
        consequence="the mud pulled both feet down, and the bell went silent",
        clue="ripples moved in a straight line toward the wooden footbridge",
        brave_move="passed long sticks from paw to paw and made a path without stepping into the mud",
        cause="the lamb had fallen beside a hidden reed island and was ringing a collar for help",
        rescue="slid a flat board across the mud and pulled the lamb onto firm ground",
        ending="the little bell rang brightly as the lamb walked across the safe bridge",
        lesson="careful cooperation is stronger than a hurried dash",
    ),
]


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(
            f"Unknown setting {params.setting!r}; choose one of: {', '.join(SETTINGS)}."
        )
    if not params.hero_name.strip() or not params.helper_name.strip():
        raise StoryError("Hero and helper names must not be empty.")
    world = World(setting=params.setting)
    hero_species = next((s for n, s in HEROES if n == params.hero_name), "fox")
    helper_species = next((s for n, s in HELPERS if n == params.helper_name), "badger")
    hero = world.add_animal(
        Animal(params.hero_name, hero_species, "young leader", {"x": 0.0, "y": 0.0})
    )
    helper = world.add_animal(
        Animal(params.helper_name, helper_species, "steady helper", {"x": 1.0, "y": 0.0})
    )
    world.facts.update(hero=hero, helper=helper)
    world.objects.update(
        missing_fawn={"kind": "animal", "safe": False},
        warning_bell={"kind": "signal", "safe": True},
        shelter={"kind": "shelter", "safe": True},
    )
    return world


def narrate(world: World, seed: int) -> None:
    rng = random.Random(seed ^ 0x9E3779B9)
    hero: Animal = world.facts["hero"]
    helper: Animal = world.facts["helper"]
    arc = rng.choice(ARCS)
    setting = SETTINGS[world.setting]
    multitude_size = rng.choice([17, 23, 31,  forty := 40])
    if multitude_size == 40:
        multitude_word = "forty"
    else:
        multitude_word = str(multitude_size)

    methods = [
        "counted the animals in pairs",
        "placed smooth pebbles beside each safe place",
        "asked the birds to watch from above while the ground animals checked below",
        "made a quiet chain from the meadow to the danger",
        "shared the clue aloud so no animal had to guess alone",
    ]
    method = rng.choice(methods)
    weather = rng.choice(
        [
            "The moon was a thin silver boat",
            "Clouds crowded together like woolly sheep",
            "The last gold of sunset rested on the grass",
            "Stars blinked between the branches",
        ]
    )
    dialogue = rng.choice(
        [
            (
                f'"Wait," said {hero.name}. "The sound tells us where to look, but not how to hurry."',
                f'"Then we will listen and move together," replied {helper.name}.',
            ),
            (
                f'{hero.name} whispered, "I am scared, but I can still ask for help."',
                f'"That is a brave beginning," said {helper.name}. "Tell everyone what you noticed."',
            ),
            (
                f'"Should we all rush in?" asked {hero.name}.',
                f'"No," said {helper.name}. "A multitude is safest when every small step has a plan."',
            ),
        ]
    )

    world.facts.update(
        arc=arc,
        multitude_size=multitude_size,
        method=method,
        danger=arc.danger,
        cause=arc.cause,
        resolution=arc.rescue,
    )

    world.say(
        f"{weather} over {setting['place']}, where {setting['features']} waited under the night."
    )
    world.say(
        f"{hero.name} the {hero.species} lived there with a multitude of forest animals—"
        f"{multitude_word} creatures who shared the paths, puddles, and quiet places."
    )
    world.say(
        f"One evening, the multitude gathered for supper when {arc.opening_sign}. "
        f"Then {arc.danger}."
    )
    hero.memes["worry"] += 1.0
    world.say(
        f"The danger was hard to see, which made every rustle sound bigger than a tree."
    )

    world.para()
    world.say(dialogue[0])
    world.say(dialogue[1])
    world.say(f"But before the plan was ready, {hero.name} {arc.false_move}.")
    hero.memes["worry"] += 1.0
    world.say(f"{arc.consequence}. For one long moment, the multitude could hear only its own frightened breathing.")
    world.say(f"Then {hero.name} noticed that {arc.clue}.")
    world.say(f"{hero.name} called, 'Everyone, stay close! We have a clue, not a reason to panic.'")

    world.para()
    hero.memes["bravery"] += 1.0
    helper.memes["trust"] += 1.0
    world.say(
        f"With {helper.name} beside {hero.name}, the animals {method}. "
        f"They moved slowly enough for the smallest mouse to keep up."
    )
    world.say(f"At the dangerous place, {hero.name} {arc.brave_move}.")
    world.say(f"The hidden truth became clear: {arc.cause}.")
    world.say(
        f"Together, the animals {arc.rescue}. No single creature could have managed it alone."
    )

    world.para()
    world.objects["missing_fawn"]["safe"] = True
    hero.memes["belonging"] += 1.0
    helper.memes["belonging"] += 1.0
    world.say(f"The multitude grew quiet again, but this time the quiet felt safe.")
    world.say(f"{hero.name} learned that {arc.lesson}.")
    world.say(f"By dawn, {arc.ending}.")
    world.say(
        f"{hero.name} and {helper.name} shared the first berries, and every animal had a place beside them."
    )


def generation_prompts(world: World) -> list[str]:
    hero: Animal = world.facts["hero"]
    return [
        f"Write a suspenseful animal story about {hero.name} the {hero.species} helping a multitude of creatures.",
        "Make the danger frightening but suitable for children, and let a clue change the animals' plan.",
        "End with a concrete image showing that teamwork made the animals safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Animal = world.facts["hero"]
    helper: Animal = world.facts["helper"]
    arc: SuspenseArc = world.facts["arc"]
    count = world.facts["multitude_size"]
    return [
        QAItem(
            question=f"Who led the animals when the danger appeared?",
            answer=f"{hero.name} the {hero.species} noticed the danger and helped the multitude make a safer plan.",
        ),
        QAItem(
            question="What made the middle of the story suspenseful?",
            answer=f"The animals faced this danger: {arc.danger}. It was hard to see clearly, so every sound made them wonder what might happen.",
        ),
        QAItem(
            question="What clue changed the animals' plan?",
            answer=f"They noticed that {arc.clue}. That evidence showed them where to move carefully instead of rushing.",
        ),
        QAItem(
            question=f"How did {hero.name} and {helper.name} solve the problem?",
            answer=f"They worked with the multitude: {arc.rescue}. Their shared plan succeeded because no animal had to act alone.",
        ),
        QAItem(
            question="What lesson did the animals learn?",
            answer=f"They learned that {arc.lesson}. The safe ending proved that lesson through their teamwork.",
        ),
        QAItem(
            question="How many animals were in the multitude?",
            answer=f"The story describes a multitude of {count} forest animals.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does multitude mean?",
            answer="A multitude means a very large number or a great many of something.",
        ),
        QAItem(
            question="Why can a multitude of animals help one another?",
            answer="Many animals can share different jobs, such as watching, carrying, guiding, and comforting smaller animals.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the excited or worried feeling people have while they wait to discover what will happen next.",
        ),
        QAItem(
            question="Why is listening useful during danger?",
            answer="Listening can reveal clues and help everyone choose a safe action instead of rushing into a worse problem.",
        ),
    ]


ASP_RULES = r"""
setting(meadow).
animal_multitude.
danger_present.
clue_found.
calm_plan.
rescued.
lesson(teamwork).

safe_outcome :- danger_present, clue_found, calm_plan, rescued.
suspenseful :- danger_present, not rescued.
#show safe_outcome/0.
#show suspenseful/0.
#show lesson/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "meadow"),
            asp.fact("animal_multitude"),
            asp.fact("danger_present"),
            asp.fact("clue_found"),
            asp.fact("calm_plan"),
            asp.fact("rescued"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program("#show safe_outcome/0.\n#show suspenseful/0.\n#show lesson/1.")
    )
    names = {(sym.name, tuple(str(a) for a in sym.arguments)) for sym in model}
    expected = {
        ("safe_outcome", ()),
        ("lesson", ("teamwork",)),
    }
    if names == expected:
        print("OK: ASP and Python agree that the multitude reaches safety through teamwork.")
        return 0
    print("MISMATCH between ASP and Python parity gate.")
    print("ASP atoms:", sorted(names))
    print("Expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a suspenseful animal story about a multitude."
    )
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--hero", dest="hero_name", choices=[n for n, _ in HEROES])
    parser.add_argument("--helper", dest="helper_name", choices=[n for n, _ in HELPERS])
    parser.add_argument("--setting", choices=list(SETTINGS))
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero_name=args.hero_name or rng.choice(HEROES)[0],
        helper_name=args.helper_name or rng.choice(HELPERS)[0],
        setting=args.setting or rng.choice(list(SETTINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world, params.seed if params.seed is not None else 0)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting={world.setting}")
    lines.append(f"multitude_size={world.facts.get('multitude_size')}")
    lines.append(f"danger={world.facts.get('danger')}")
    lines.append(f"cause={world.facts.get('cause')}")
    for animal in world.animals.values():
        lines.append(
            f"{animal.name}: species={animal.species} "
            f"meters={animal.meters} memes={animal.memes}"
        )
    for name, obj in world.objects.items():
        lines.append(f"{name}: {obj}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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
        print(asp_program("#show safe_outcome/0.\n#show suspenseful/0.\n#show lesson/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program("#show safe_outcome/0.\n#show suspenseful/0.\n#show lesson/1.")
        )
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                seed=base_seed,
                hero_name="Luna",
                helper_name="Moss",
                setting="moonlit meadow",
            ),
            StoryParams(
                seed=base_seed + 1,
                hero_name="Pip",
                helper_name="Fern",
                setting="pine hollow",
            ),
            StoryParams(
                seed=base_seed + 2,
                hero_name="Neri",
                helper_name="Bramble",
                setting="reed marsh",
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
