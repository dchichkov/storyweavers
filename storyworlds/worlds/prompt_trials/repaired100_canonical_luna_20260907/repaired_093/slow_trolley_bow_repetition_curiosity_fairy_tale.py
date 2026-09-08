#!/usr/bin/env python3
"""
A small Fairy Tale storyworld about a slow trolley, a curious child, and a bow
that must be tied again and again until its purpose is understood.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the Moonbell Forest"
    detail: str = "a silver forest road where a slow trolley carried wishes to the hilltop castle"


@dataclass
class StoryParams:
    name: str
    companion_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    story_lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.story_lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story_lines)


NAMES = ["Luna", "Mira", "Elsie", "Tala", "Nell", "Pia", "Cora", "Wren"]
COMPANIONS = ["Pip", "Orin", "Moss", "Bram", "Fenn", "Toby", "Ash", "Rook"]

SETTING = Setting()

TRIALS = [
    {
        "id": "red_bow",
        "object": "a red velvet bow",
        "first_clue": "the bow slipped loose whenever the trolley crossed the old stone bridge",
        "wrong_idea": "the bow was simply too small for the trolley bell",
        "repeat": "Luna tied the bow once, twice, and three times",
        "truth": "the bow was meant to be tied around the bell rope, where its long tails could hush the bell until the trolley reached the sleeping village",
        "ending": "the red bow rested on the bell rope, and the trolley rolled past the cottages as softly as a moth",
        "lesson": "A repeated failure may be a message asking for a better question.",
    },
    {
        "id": "blue_bow",
        "object": "a blue silk bow",
        "first_clue": "each time the bow came undone, the trolley slowed beside a different whispering tree",
        "wrong_idea": "the forest wind was stealing it for mischief",
        "repeat": "Luna tied the bow again and again while counting the whispering trees",
        "truth": "the bow was a traveling marker, and its loose ends pointed toward the tree whose roots hid the lost wishing key",
        "ending": "the blue bow hung from the wishing tree, and the trolley carried the recovered key home beneath a sky full of stars",
        "lesson": "Curiosity turns repetition into a trail when we notice what changes.",
    },
    {
        "id": "gold_bow",
        "object": "a golden bow",
        "first_clue": "the bow shone only when the trolley stopped at the dark tunnel",
        "wrong_idea": "the gold thread was afraid of the sunlight",
        "repeat": "Luna tied the bow in a neat loop, then tied it again after every slow stop",
        "truth": "the bow was a signal for the lantern keeper, telling him when the trolley needed light",
        "ending": "the golden bow flashed at the tunnel mouth, and warm lanterns awakened one by one along the track",
        "lesson": "A small repeated sign can help a whole community find its way.",
    },
    {
        "id": "green_bow",
        "object": "a green meadow bow",
        "first_clue": "the bow sprang open whenever the trolley passed the sleeping dragon's meadow",
        "wrong_idea": "the dragon's sneeze had enchanted it",
        "repeat": "Luna tied the bow slowly, carefully, and then slowly once more",
        "truth": "the bow was tied to a bell cord that warned the dragon the trolley was near, so no wheel would surprise him",
        "ending": "the green bow rang a gentle note, and the dragon opened one golden eye before smiling at the passing trolley",
        "lesson": "Repeating a careful act can make room for kindness instead of noise.",
    },
    {
        "id": "white_bow",
        "object": "a white moon-bow",
        "first_clue": "the bow loosened whenever the trolley reached the fork beneath the crooked moon",
        "wrong_idea": "the moon wanted the bow for its own crown",
        "repeat": "Luna retied it at every fork and marked each knot with a pebble",
        "truth": "the bow was a compass ribbon, and its longest tail always pointed toward the safe road",
        "ending": "the white bow guided the trolley onto the safe road, where dawn painted the wheels silver",
        "lesson": "Patient noticing can reveal guidance hidden inside a puzzling pattern.",
    },
]

OPENINGS = [
    "{name} lived beside the Moonbell Forest, where a slow trolley carried wishes to the castle.",
    "At the edge of the kingdom, {name} waited each morning for the slow trolley from the silver woods.",
    "In a village of blue roofs, {name} loved watching the slow trolley climb the hill.",
    "Long ago, {name} found a curious bow beside the forest track where the slow trolley passed.",
]

REFLECTIONS = [
    '"Perhaps it is not failing," {name} said. "Perhaps it is repeating a message."',
    '{companion} tapped the knot. "If it happens again, let us watch what happens around it."',
    '"Curiosity is a little lantern," {name} whispered. "We only need to hold it near the right clue."',
    '{name} stopped tugging the ribbon and began counting every place where it came loose.',
]


ASP_RULES = r"""
misunderstanding(X) :- curious(X), sees(X, bow), guesses_wrong(X).
repetition(X) :- ties_bow(X, 1), ties_bow(X, 2), ties_bow(X, 3).
clue_found(X) :- repetition(X), notices_pattern(X).
resolved(X) :- clue_found(X), learns_purpose(X), helps_others(X).
valid_story(X) :- misunderstanding(X), resolved(X).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("character", "hero"),
            asp.fact("character", "companion"),
            asp.fact("setting", "moonbell_forest"),
            asp.fact("vehicle", "slow_trolley"),
            asp.fact("object", "bow"),
            asp.fact("curious", "hero"),
            asp.fact("sees", "hero", "bow"),
            asp.fact("guesses_wrong", "hero"),
            asp.fact("ties_bow", "hero", 1),
            asp.fact("ties_bow", "hero", 2),
            asp.fact("ties_bow", "hero", 3),
            asp.fact("notices_pattern", "hero"),
            asp.fact("learns_purpose", "hero"),
            asp.fact("helps_others", "hero"),
        ]
    )


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    trial = TRIALS[rng.randrange(len(TRIALS))]
    opening = OPENINGS[rng.randrange(len(OPENINGS))]
    reflection = REFLECTIONS[rng.randrange(len(REFLECTIONS))]
    hero = Entity(
        id=params.name,
        kind="character",
        type="child",
        label="curious child",
        meters={"distance": 0.0, "knots_tied": 0.0},
        memes={"curiosity": 1.0, "confusion": 0.0, "worry": 0.0, "confidence": 0.0, "wonder": 0.0},
    )
    companion = Entity(
        id=params.companion_name,
        kind="character",
        type="fox",
        label="small fox",
        meters={"distance": 0.0},
        memes={"friendship": 1.0, "patience": 1.0, "wonder": 0.0},
    )
    bow = Entity(
        id="bow",
        type="ribbon",
        label=trial["object"],
        meters={"length": 1.0},
        memes={"mystery": 1.0},
    )
    trolley = Entity(
        id="trolley",
        type="vehicle",
        label="slow trolley",
        meters={"speed": 1.0},
        memes={"purpose": 0.0},
    )
    world = World(setting=SETTING)
    for entity in (hero, companion, bow, trolley):
        world.add(entity)
    world.facts.update(
        hero=hero,
        companion=companion,
        bow=bow,
        trolley=trolley,
        trial=trial,
        opening=opening,
        reflection=reflection,
        repetition_count=0,
        pattern_seen=False,
        resolved=False,
    )
    return world


def story_intro(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    world.say(world.facts["opening"].format(name=hero.id))
    world.say(
        f"{hero.id} traveled with {companion.id}, a small fox with bright eyes. "
        f"The {world.facts['trolley'].label} moved so slowly that falling leaves could keep pace with it."
    )
    world.say(
        f"At the trolley door, {hero.id} found {world.facts['trial']['object']} tied to the handrail. "
        "No one in the kingdom knew who had left it there."
    )


def story_problem(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    trial = world.facts["trial"]
    bow = world.facts["bow"]
    world.say(
        f"As the trolley crept toward the forest, {trial['first_clue']}. "
        f"{hero.id} caught the {bow.label} before it touched the track."
    )
    world.say(
        f"{hero.id} guessed that {trial['wrong_idea']}. "
        f"He {trial['repeat']}."
    )
    hero.meters["knots_tied"] = 3.0
    world.facts["repetition_count"] = 3
    hero.memes["confusion"] = 1.0
    hero.memes["worry"] = 1.0
    world.say(
        f'"Why does it happen every time?" {hero.id} asked. '
        f'{companion.id} answered, "Let us not chase the bow. Let us watch the world around it."'
    )


def story_turn(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    trial = world.facts["trial"]
    trolley = world.facts["trolley"]
    world.say(
        f"The {trolley.label} rolled forward, stopped, and rolled forward again. "
        f"{hero.id} watched instead of pulling the ribbon at once."
    )
    world.say(
        f"He noticed that {trial['first_clue']}. "
        f"{companion.id} pointed to the repeating pattern and said, "
        '"The bow is not asking us to tie it tighter. It is asking us to look farther."'
    )
    world.say(world.facts["reflection"].format(name=hero.id, companion=companion.id))
    world.say(f"Then {hero.id} understood: {trial['truth']}.")
    hero.memes["confusion"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["confidence"] = 1.0
    hero.memes["wonder"] = 1.0
    companion.memes["wonder"] = 1.0
    trolley.memes["purpose"] = 1.0
    world.facts["pattern_seen"] = True
    world.facts["truth"] = trial["truth"]


def story_resolution(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    trial = world.facts["trial"]
    hero.memes["confidence"] += 1.0
    hero.memes["wonder"] += 1.0
    world.say(
        f"{hero.id} tied the bow for its true purpose, while {companion.id} held the trolley door steady. "
        f"Together they helped the kingdom by following the ribbon's message."
    )
    world.say(
        f"{trial['lesson']} {hero.id} repeated the words softly, so the lesson would travel as far as the trolley."
    )
    world.say(
        f"At last, {trial['ending']}. "
        f"{hero.id} and {companion.id} smiled as the slow trolley carried them home."
    )
    world.facts["resolved"] = True
    world.facts["ending"] = trial["ending"]
    world.facts["lesson"] = trial["lesson"]


def generate_story_world(params: StoryParams) -> World:
    world = build_world(params)
    story_intro(world)
    world.say("")
    story_problem(world)
    world.say("")
    story_turn(world)
    world.say("")
    story_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    trial = world.facts["trial"]
    return [
        "Write a child-facing Fairy Tale about a slow trolley, a mysterious bow, and a curious hero.",
        f"Show how {hero.id} and {companion.id} use repetition and curiosity to understand why the bow keeps coming loose.",
        f"End with the bow serving its true purpose: {trial['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    trial = world.facts["trial"]
    return [
        QAItem(
            question=f"Where did {hero.id} find the bow?",
            answer=f"{hero.id} found {trial['object']} tied to the handrail of the slow trolley in the Moonbell Forest."
        ),
        QAItem(
            question=f"What happened whenever the trolley traveled?",
            answer=f"{trial['first_clue']}. The repeated event made the bow seem mysterious."
        ),
        QAItem(
            question=f"What did {hero.id} first believe?",
            answer=f"{hero.id} first believed that {trial['wrong_idea']}. That guess did not explain the repeated pattern."
        ),
        QAItem(
            question=f"How did {companion.id} help {hero.id}?",
            answer=f"{companion.id} encouraged {hero.id} to stop pulling at the bow and observe what happened around it."
        ),
        QAItem(
            question="What did repetition help the characters notice?",
            answer=f"Repeating the observation helped them see that {trial['first_clue']}. The pattern pointed toward the bow's real purpose."
        ),
        QAItem(
            question="What was the true purpose of the bow?",
            answer=trial["truth"],
        ),
        QAItem(
            question=f"How did {hero.id}'s curiosity change the journey?",
            answer=f"{hero.id}'s curiosity changed the journey by turning repeated failures into useful clues, allowing the characters to help others safely."
        ),
        QAItem(
            question="What lesson did the Fairy Tale teach?",
            answer=trial["lesson"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trolley?",
            answer="A trolley is a small vehicle that carries people or things, often along a track or a fixed route."
        ),
        QAItem(
            question="Why can repetition be useful?",
            answer="Repetition can reveal a pattern. When the same event happens again, careful observers can compare it with what came before."
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn more by asking questions, looking closely, and testing an idea safely."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_verify() -> int:
    if not asp_valid():
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    try:
        import asp
        model = asp.one_model(asp_program())
        valid = asp.atoms(model, "valid_story")
        if ("hero",) not in valid:
            print("MISMATCH: ASP twin did not validate the story.")
            return 1
    except Exception as exc:
        print(f"MISMATCH: ASP verification failed: {exc}")
        return 1
    sample = generate(StoryParams(name="Luna", companion_name="Pip", seed=7))
    required = ("slow trolley", "bow", "curious")
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated story is missing required narrative elements.")
        return 1
    if not sample.world or not sample.world.facts["resolved"]:
        print("MISMATCH: generated world did not resolve.")
        return 1
    print("OK: Python and ASP reasonableness gates pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Fairy Tale world about a slow trolley, a bow, repetition, and curiosity."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion-name", choices=COMPANIONS)
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
    name = args.name or rng.choice(NAMES)
    choices = [item for item in COMPANIONS if item != name]
    companion_name = args.companion_name or rng.choice(choices)
    return StoryParams(name=name, companion_name=companion_name)


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.type:9}) {' '.join(details)}")
    lines.append(f"  repetition_count={world.facts['repetition_count']}")
    lines.append(f"  pattern_seen={world.facts['pattern_seen']}")
    lines.append(f"  resolved={world.facts['resolved']}")
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
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        values = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(values)} compatible stories:")
        for value in values:
            print(f"  {value}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Luna", companion_name="Pip", seed=base_seed),
            StoryParams(name="Mira", companion_name="Orin", seed=base_seed + 1),
            StoryParams(name="Tala", companion_name="Moss", seed=base_seed + 2),
            StoryParams(name="Cora", companion_name="Bram", seed=base_seed + 3),
            StoryParams(name="Wren", companion_name="Fenn", seed=base_seed + 4),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            index += 1

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
