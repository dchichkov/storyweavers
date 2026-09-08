#!/usr/bin/env python3
"""A nursery-rhyme StoryWorld about a lyricist, clear sight, and a false clue."""

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

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
sys.path.insert(0, str(STORYWORLDS_DIR.parent))

from results import QAItem, StoryError, StorySample  # noqa: E402


TITLE = "The Lyricist and the False Star"


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class StoryParams:
    lyricist: str = "Lila"
    place: str = "the moonlit meadow"
    song: str = "a bright little marching song"
    ending: str = "happy"
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


PLACES = [
    "the moonlit meadow",
    "the sleepy village green",
    "the bluebell hill",
]
LYRICISTS = ["Lila", "Nell", "Pip"]
SONGS = [
    "a bright little marching song",
    "a tum-ti-tum song for the moon",
    "a gentle tune for sleepy bees",
]
ENDINGS = ["happy", "bad"]

TRIALS = [
    {
        "false": "a painted star on a crooked sign",
        "clue": "the painted star had no dew on its paper points",
        "true": "a silver bell hanging from an old pear tree",
        "song_line": "Bell in the tree, ring bright for me!",
        "happy": "the true bell rang, and every lost lamb came trotting home",
        "bad": "the false star led the lambs toward a thorny ditch before the dark",
    },
    {
        "false": "a yellow lantern painted on a barn door",
        "clue": "the painted lantern gave no light and cast no glow",
        "true": "a real lantern swinging beside the baker's gate",
        "song_line": "Glow by the gate, do not be late!",
        "happy": "the real lantern shone, and the little mice found their warm burrow",
        "bad": "the false lantern sent the mice scratching at a cold wall all night",
    },
    {
        "false": "a chalk moon on a garden fence",
        "clue": "the chalk moon stayed still while the real moon sailed above it",
        "true": "a round pond reflecting the moon",
        "song_line": "Moon in the pond, guide us beyond!",
        "happy": "the pond reflected the moon, and the ducklings paddled safely home",
        "bad": "the chalk moon fooled the ducklings, who wandered into the brambles",
    },
]


def choose_trial(params: StoryParams) -> dict[str, str]:
    index = (params.seed or 0) % len(TRIALS)
    return TRIALS[index]


def setup_world(params: StoryParams, trial: dict[str, str]) -> World:
    if params.ending not in ENDINGS:
        raise StoryError(f"ending must be one of {ENDINGS}, not {params.ending!r}")
    if params.place not in PLACES:
        raise StoryError(f"place must be one of {PLACES}, not {params.place!r}")
    if params.lyricist not in LYRICISTS:
        raise StoryError(f"lyricist must be one of {LYRICISTS}, not {params.lyricist!r}")
    if params.song not in SONGS:
        raise StoryError(f"song must be one of {SONGS}, not {params.song!r}")

    world = World(params.place)
    lyricist = world.add(Entity(
        id="lyricist",
        kind="character",
        label=params.lyricist,
        memes={"acuity": 0.0, "confidence": 0.0},
    ))
    world.add(Entity(
        id="false_sign",
        kind="object",
        label=trial["false"],
        meters={"truth": 0.0, "visibility": 1.0},
    ))
    world.add(Entity(
        id="true_clue",
        kind="object",
        label=trial["true"],
        meters={"truth": 1.0, "visibility": 0.7},
    ))
    world.facts.update(
        lyricist=lyricist,
        trial=trial,
        song=params.song,
        ending=params.ending,
        place=params.place,
    )
    return world


def tell(params: StoryParams) -> World:
    trial = choose_trial(params)
    world = setup_world(params, trial)
    lyricist = world.entities["lyricist"]
    outcome = params.ending

    world.say(
        f"In {world.place} lived {params.lyricist}, a lyricist who spun little verses "
        f"for {params.song}."
    )
    world.say(
        f"One dusky day, the lambs lost their way. A false sign appeared first: "
        f"{trial['false']}. It seemed to point toward home."
    )
    world.say(
        f'"Follow the star!" cried a lamb. "{params.lyricist}, is that the path?" '
        f'"It may be," said the lyricist, "but let us look closely before we sing."'
    )
    world.para()

    world.say(f"{params.lyricist} used acuity, the sharp power of careful seeing.")
    world.say(
        f"The lyricist noticed that {trial['clue']}. "
        "A false thing may look bright, but true clues leave signs in the world."
    )
    lyricist.memes["acuity"] = 1.0
    lyricist.memes["confidence"] = 1.0
    world.fired.add("false_clue_tested")
    world.say(
        f'"A painted promise is not a road," said {params.lyricist}. '
        f'"Listen, little friends. What else can we notice?"'
    )
    world.say(
        f'"I hear a faint ring!" cried the lamb. '
        f'"Then follow the sound," said the lyricist, '
        f'"and let the next verse match what is real."'
    )
    world.para()

    if outcome == "happy":
        world.fired.add("true_clue_followed")
        world.entities["true_clue"].meters["found"] = 1.0
        world.say(
            f"{params.lyricist} found {trial['true']} and sang, "
            f'"{trial["song_line"]}"'
        )
        world.say(f"{trial['happy'].capitalize()}.")
        world.say(
            "The lambs skipped in a ring, and the lyricist wrote a final couplet: "
            '"Look, listen, test, then cheer; true paths bring the loved ones near."'
        )
        world.fired.add("happy_ending")
    else:
        world.fired.add("false_clue_followed")
        world.entities["false_sign"].meters["followed"] = 1.0
        world.say(
            f"{params.lyricist} trusted the false sign too soon and sang, "
            f'"Star on the board, lead us abroad!"'
        )
        world.say(f"{trial['bad'].capitalize()}.")
        world.say(
            "At last the village bell called the lambs back, but the song ended sadly. "
            "The lyricist learned that a catchy rhyme cannot make a false clue true."
        )
        world.fired.add("bad_ending")

    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a nursery-rhyme story about the lyricist {facts['lyricist'].label} in {facts['place']}.",
        "Include acuity, a false clue, a brief back-and-forth dialogue, and a consequence.",
        f"Give the story a {facts['ending']} ending in which careful observation changes what the characters do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    trial = facts["trial"]
    if facts["ending"] == "happy":
        ending_answer = f"{trial['happy'].capitalize()}. The lyricist used acuity and followed the real clue."
    else:
        ending_answer = f"{trial['bad'].capitalize()}. The lyricist learned too late that the first sign was false."
    return [
        QAItem(
            question=f"What did {facts['lyricist'].label} do for work?",
            answer=f"{facts['lyricist'].label} was a lyricist who wrote little songs and verses.",
        ),
        QAItem(
            question="What false clue appeared?",
            answer=f"The false clue was {trial['false']}. It looked useful, but it was not a real guide.",
        ),
        QAItem(
            question="How did acuity help?",
            answer=f"Acuity helped the lyricist notice that {trial['clue']}.",
        ),
        QAItem(
            question="What did the lambs say during the dialogue?",
            answer=f"A lamb asked whether the sign showed the path, and the lyricist answered that they should look closely before singing.",
        ),
        QAItem(
            question="How did the story end?",
            answer=ending_answer,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lyricist?",
            answer="A lyricist is someone who writes the words of songs.",
        ),
        QAItem(
            question="What is acuity?",
            answer="Acuity is sharpness of thought or observation, especially the ability to notice small details.",
        ),
        QAItem(
            question="Why should a clue be tested?",
            answer="A clue should be tested because something that looks convincing may be false.",
        ),
        QAItem(
            question="What makes a nursery rhyme?",
            answer="A nursery rhyme often uses a simple rhythm, repeated sounds, and a memorable little verse.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {entity.id:11} ({entity.kind:9}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for ending in ENDINGS:
        lines.append(asp.fact("ending", ending))
    for place in PLACES:
        lines.append(asp.fact("place", place))
    lines.extend([
        "lyricist.",
        "acuity.",
        "false_clue.",
        "true_clue.",
        "dialogue.",
    ])
    return "\n".join(lines)


ASP_RULES = r"""
observes_truth :- lyricist, acuity, true_clue.
tests_false :- lyricist, acuity, false_clue.
ready_for_happy :- observes_truth, tests_false, dialogue.
happy_story :- ready_for_happy, ending(happy).
bad_story :- false_clue, ending(bad), not observes_truth.
#show observes_truth/0.
#show tests_false/0.
#show ready_for_happy/0.
#show happy_story/0.
#show bad_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program(
        "#show observes_truth/0. #show tests_false/0. "
        "#show ready_for_happy/0. #show happy_story/0. #show bad_story/0."
    ))
    if not model:
        print("ASP verification failed: no model.")
        return 1
    required = ("observes_truth", "tests_false", "ready_for_happy")
    if not all(asp.atoms(model, name) for name in required):
        print("ASP verification failed: missing acuity pathway.")
        return 1
    for ending in ENDINGS:
        sample = generate(StoryParams(
            lyricist="Lila",
            place=PLACES[0],
            song=SONGS[0],
            ending=ending,
            seed=0,
        ))
        if not sample.story or "lyricist" not in sample.story:
            print("ASP verification failed: generated story was incomplete.")
            return 1
    print("OK: ASP twin grounded, acuity pathway found, and generated stories passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery-rhyme story world about a lyricist, acuity, and a false clue."
    )
    parser.add_argument("--lyricist", choices=LYRICISTS, default=None)
    parser.add_argument("--place", choices=PLACES, default=None)
    parser.add_argument("--song", choices=SONGS, default=None)
    parser.add_argument("--ending", choices=ENDINGS, default=None)
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
    return StoryParams(
        lyricist=args.lyricist or rng.choice(LYRICISTS),
        place=args.place or rng.choice(PLACES),
        song=args.song or rng.choice(SONGS),
        ending=args.ending or rng.choice(ENDINGS),
        seed=args.seed,
    )


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


CURATED = [
    StoryParams(lyricist="Lila", place="the moonlit meadow", song=SONGS[0], ending="happy", seed=0),
    StoryParams(lyricist="Nell", place="the sleepy village green", song=SONGS[1], ending="bad", seed=1),
    StoryParams(lyricist="Pip", place="the bluebell hill", song=SONGS[2], ending="happy", seed=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(
            "#show observes_truth/0. #show tests_false/0. "
            "#show ready_for_happy/0. #show happy_story/0. #show bad_story/0."
        ))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program(
            "#show observes_truth/0. #show tests_false/0. "
            "#show ready_for_happy/0. #show happy_story/0. #show bad_story/0."
        ))
        for predicate in (
            "observes_truth",
            "tests_false",
            "ready_for_happy",
            "happy_story",
            "bad_story",
        ):
            print(asp.atoms(model, predicate))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
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
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = (
                f"### {sample.params.lyricist} / "
                f"{sample.params.ending} ending / {sample.params.place}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
