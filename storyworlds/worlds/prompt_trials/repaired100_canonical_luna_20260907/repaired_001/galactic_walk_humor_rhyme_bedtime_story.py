#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a galactic walk, a sleepy moon, and a
rhyming joke that helps a small traveler find the way home.
"""

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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "moon_garden": "the moon garden",
    "comet_lane": "Comet Lane",
    "star_meadow": "the star meadow",
    "quiet_crater": "the quiet crater",
}

PLACE_DETAILS = {
    "moon_garden": (
        "silver flowers opened beneath the stars",
        "a sleepy moon-moth",
        "a round hill made of moon dust",
    ),
    "comet_lane": (
        "little comets zipped past like glowing crumbs",
        "a polite space goose",
        "a warm blue nebula",
    ),
    "star_meadow": (
        "soft stars bobbed above the grass",
        "a yawning owl from Saturn",
        "a ring-shaped pond",
    ),
    "quiet_crater": (
        "the crater walls hummed a very low lullaby",
        "a tiny robot with a blanket",
        "a silver telescope",
    ),
}

NAMES = ["Luna", "Milo", "Pip", "Nell", "Toby", "Zia"]
HELPERS = ["a moon-moth", "a space goose", "a tiny robot", "a sleepy owl"]

WALKS = {
    "moonbeam_walk": {
        "verb": "take a moonbeam walk",
        "trail": "a bright moonbeam",
        "obstacle": "a puddle of floating stardust",
        "destination": "the pillow-shaped hill",
    },
    "comet_walk": {
        "verb": "take a careful walk beside the comets",
        "trail": "a trail of warm comet crumbs",
        "obstacle": "a hiccuping comet",
        "destination": "the quiet cloud at the end of the lane",
    },
    "star_walk": {
        "verb": "walk across the star meadow",
        "trail": "a line of twinkling stars",
        "obstacle": "a star that had forgotten which way was up",
        "destination": "the ring-shaped pond",
    },
}

RHYMES = [
    ("If your feet feel slow and your nose feels cold, follow the glow and be brave and bold.", "glow"),
    ("When the sky looks wide and the path looks new, rhyme with the light and the light finds you.", "light"),
    ("If a comet sneezes and wiggles its tail, giggle, say bless you, and follow the trail.", "trail"),
    ("When sleepy stars begin to yawn, walk by the rhyme till night is gone.", "yawn"),
]

JOKES = [
    "Why did the comet bring a blanket? Because it wanted to make a soft landing.",
    "What do you call a moon that tells jokes? A lunar-tickler.",
    "Why did the star wear a tiny hat? It wanted to look out-standing.",
    "What did the sleepy planet say? I need my space.",
]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    place: str
    name: str
    helper: str
    walk: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a humorous rhyming bedtime story about a galactic walk."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--walk", choices=sorted(WALKS))
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
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        walk=args.walk or rng.choice(list(WALKS)),
    )


def validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown galactic place: {params.place}")
    if params.name not in NAMES:
        raise StoryError(f"Unknown traveler name: {params.name}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    if params.walk not in WALKS:
        raise StoryError(f"Unknown walk: {params.walk}")


def tell(params: StoryParams, rng: random.Random) -> World:
    validate_params(params)
    place = PLACES[params.place]
    setting_detail, local_helper, landmark = PLACE_DETAILS[params.place]
    walk = WALKS[params.walk]
    rhyme, rhyme_word = rng.choice(RHYMES)
    joke = rng.choice(JOKES)

    world = World(place=place)
    traveler = world.add(
        Entity(
            id="traveler",
            kind="character",
            label=params.name,
            meters={"sleepiness": 0.2, "distance": 0.0},
            memes={"curiosity": 1.0, "worry": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            label=params.helper,
            meters={"helpfulness": 1.0},
            memes={"cheer": 0.8},
        )
    )
    path = world.add(
        Entity(
            id="path",
            kind="place",
            label=walk["trail"],
            meters={"brightness": 0.9, "length": 1.0},
            memes={"comfort": 0.7},
        )
    )
    moon = world.add(
        Entity(
            id="moon",
            kind="celestial",
            label="the sleepy moon",
            meters={"height": 1.0},
            memes={"drowsiness": 0.9},
        )
    )

    world.say(
        f"Good night, little universe. In {place}, {params.name} woke for one last "
        f"galactic walk while {setting_detail}."
    )
    world.say(
        f"The plan was to {walk['verb']} along {walk['trail']} until reaching "
        f"{walk['destination']}, where the traveler could tuck the sleepy moon into bed."
    )
    world.say(
        f"{params.helper.capitalize()} offered to help. \"I know a rhyme for every "
        f"wobbly step,\" said {params.helper}."
    )
    world.say(
        f"\"And I know a joke for every sleepy yawn,\" said {params.name}. \"{joke}\""
    )

    world.para()
    world.say(
        f"At first, the path shimmered softly. Then {walk['obstacle']} rolled across "
        f"the way and blocked the safest route."
    )
    traveler.meters["distance"] = 0.5
    traveler.memes["worry"] = 0.6
    world.say(
        f"\"Should we turn back?\" asked {params.name}. \"My slippers are beginning "
        "to feel like two tired pancakes.\""
    )
    world.say(
        f"\"Not yet,\" replied {params.helper}. \"Say the rhyme, and watch for {rhyme_word}.\""
    )
    world.say(f"Together they whispered, \"{rhyme}\"")

    traveler.meters["distance"] = 1.0
    traveler.memes["worry"] = 0.1
    path.meters["brightness"] = 1.0
    world.say(
        f"The rhyme made a shining {rhyme_word} appear beside the path. It curled "
        f"around {walk['obstacle']} and led the walkers safely onward."
    )
    world.say(
        f"{walk['obstacle'].capitalize()} gave a tiny bow. \"Excuse me,\" it said, "
        "and floated aside."
    )
    world.say(
        f"At last, {params.name} reached {walk['destination']} near {landmark}. "
        f"The sleepy moon settled down, and {params.helper} pulled a blanket of starlight "
        "over its round cheeks."
    )

    moon.memes["drowsiness"] = 1.0
    world.para()
    world.say(
        f"Before going home, {params.name} told the joke again, and even the faraway "
        "planets giggled in their sleep."
    )
    world.say(
        f"Then the galactic walk became a quiet walk, the quiet walk became a dream, "
        f"and the dream floated gently home beneath {path.label}."
    )

    world.facts.update(
        traveler=traveler,
        helper=helper,
        path=path,
        moon=moon,
        walk=walk,
        rhyme=rhyme,
        rhyme_word=rhyme_word,
        joke=joke,
        obstacle=walk["obstacle"],
        destination=walk["destination"],
        landmark=landmark,
        local_helper=local_helper,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a humorous bedtime story about a galactic walk to {f['destination']}.",
        f"Tell a rhyming story in which {f['traveler'].label} and {f['helper'].label} solve a path problem.",
        "Write a gentle child-facing bedtime tale with galactic humor, rhyme, and a sleepy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    traveler = f["traveler"].label
    helper = f["helper"].label
    return [
        QAItem(
            question=f"Why did {traveler} go on a galactic walk?",
            answer=(
                f"{traveler} went on a galactic walk to reach {f['destination']} and "
                f"help tuck the sleepy moon into bed."
            ),
        ),
        QAItem(
            question=f"What helped {traveler} and {helper} get past {f['obstacle']}?",
            answer=(
                f"They said the rhyme, and a shining {f['rhyme_word']} appeared beside "
                f"the path. It curled around {f['obstacle']} and showed them a safe way onward."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"The sleepy moon was covered with a blanket of starlight, the planets "
                f"laughed at a joke, and the galactic walk softened into a peaceful dream."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does galactic mean?",
            answer="Galactic means relating to a galaxy, a huge group of stars, gas, and dust in space.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern in which words have matching or similar ending sounds.",
        ),
        QAItem(
            question="What makes a bedtime story gentle?",
            answer="A gentle bedtime story uses comforting events, calm language, and a safe ending that helps the listener relax.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
galactic.
walk.
humor.
rhyme.
bedtime_story.

valid_domain :- galactic, walk, humor, rhyme, bedtime_story.
#show valid_domain/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("galactic"),
            asp.fact("walk"),
            asp.fact("humor"),
            asp.fact("rhyme"),
            asp.fact("bedtime_story"),
        ]
    )


def asp_program(show: str = "#show valid_domain/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    found = bool(asp.atoms(model, "valid_domain"))
    expected = True
    if found == expected:
        print("OK: ASP parity matches Python.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = tell(params, rng)
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
        print("\n-- trace --")
        for entity in sample.world.entities.values():
            print(
                f"{entity.id}: kind={entity.kind} label={entity.label} "
                f"meters={entity.meters} memes={entity.memes}"
            )
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp or args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combinations = [
            StoryParams(place=place, name=name, helper=helper, walk=walk)
            for place in PLACES
            for name in NAMES[:2]
            for helper in HELPERS[:2]
            for walk in WALKS
        ]
        for index, params in enumerate(combinations):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
