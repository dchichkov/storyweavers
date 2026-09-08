#!/usr/bin/env python3
"""
A small folk-tale storyworld about a vestibule, a mistaken message, and a
rhyme that helps a child and a porter put a funny mix-up right.
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

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, REPO_ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass(frozen=True)
class Case:
    case_id: str
    setup: str
    message: str
    misunderstanding: str
    funny_sight: str
    test: str
    truth: str
    repair: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    case_id: str = "blue_bell"
    telling_mode: str = "rhyme_first"
    detail_id: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()


VESTIBULES = {
    "oak": "the old oak vestibule",
    "river": "the river-stone vestibule",
    "hill": "the windy hill vestibule",
    "market": "the cheerful market vestibule",
}

CASES = {
    "blue_bell": Case(
        case_id="blue_bell",
        setup="A blue bell hung beside the door",
        message="A card said, 'Ring for the king'",
        misunderstanding="Luna thought the bell was meant for a royal visitor",
        funny_sight="she bowed to every traveler while wearing one muddy boot and one red slipper",
        test="ask the porter which bell belonged to which visitor",
        truth="the card meant the village baker, whose nickname was King Crust",
        repair="replace the card with a picture of a crown on a loaf of bread",
        ending="the baker rang once, and Luna greeted him with a floury handshake instead of a grand royal bow",
        lesson="a message should be checked before a person builds a whole guess around it",
    ),
    "goat_guest": Case(
        case_id="goat_guest",
        setup="A chalk mark shaped like two horns appeared on the guest board",
        message="The porter called, 'Make room for the horned guest'",
        misunderstanding="Luna expected a proud duke in a shiny helmet",
        funny_sight="she practiced a noble greeting while a small goat chewed the welcome mat",
        test="follow the hoofprints and ask who had sent the message",
        truth="the horned guest was the farmer's goat, invited to the spring fair",
        repair="move the mat, give the goat a basket of hay, and write 'goat guest' plainly",
        ending="the goat nibbled beside the door while Luna bowed only once, very carefully",
        lesson="clear words save people from preparing the wrong welcome",
    ),
    "moon_cloak": Case(
        case_id="moon_cloak",
        setup="A silver cloak lay on the vestibule bench",
        message="A note read, 'The moon is coming through'",
        misunderstanding="Luna thought a moon-princess would enter wearing the cloak",
        funny_sight="she held a cucumber like a royal scepter and announced the doorway to the sky",
        test="ask the night watchman why the cloak had been left there",
        truth="the note meant moonlight was coming through the cracked roof",
        repair="hang the cloak on its peg and cover the crack with a wooden tile",
        ending="moonlight shone through the repaired roof, and the cloak waited neatly for its sleepy owner",
        lesson="poetic words can be playful, but practical clues still need checking",
    ),
    "three_knocks": Case(
        case_id="three_knocks",
        setup="Three tiny knocks sounded behind the coat rack",
        message="A whisper said, 'The third caller is the one to trust'",
        misunderstanding="Luna decided that the third person through the door must be a secret hero",
        funny_sight="she hid behind an umbrella and tried to look mysterious while her nose stuck out",
        test="count the knocks, open the cupboard safely, and ask the callers what they heard",
        truth="a loose broom handle tapped the rack three times whenever the wind blew",
        repair="tie the broom securely and tell the callers what made the sound",
        ending="the vestibule grew quiet, except for Luna's giggle when the broom stood straight",
        lesson="a strange sound deserves a calm test before a grand story",
    ),
    "golden_hat": Case(
        case_id="golden_hat",
        setup="A golden hat sat on the welcome hook",
        message="The sign said, 'The sun's hat belongs above'",
        misunderstanding="Luna tried to hang the hat above the doorway for the morning sun",
        funny_sight="she climbed a stool with a feather duster and told the sunrise to mind its manners",
        test="compare the hat with the porter’s lost-and-found list",
        truth="the hat belonged to the mayor's child, whose name was Sunny",
        repair="place the hat in the lost-and-found basket and add the child's name",
        ending="Sunny claimed the hat and laughed when Luna asked whether the sun had missed it",
        lesson="a name can sound like a thing, so listening carefully matters",
    ),
}

TELLING_MODES = ("rhyme_first", "dialogue_first", "clue_first", "quiet_first")
OPENINGS = {
    "rhyme_first": "At the vestibule gate, where travelers came and went, Luna sang, 'A clue can bend, but truth is meant!'",
    "dialogue_first": "'Mind the doorway,' said the porter, as Luna swept the vestibule.",
    "clue_first": "Before breakfast, Luna noticed something peculiar in the vestibule.",
    "quiet_first": "The vestibule was quiet except for the tick of a wooden clock.",
}
BRIDGES = (
    "Luna tucked the odd detail behind her ear, where she kept important thoughts.",
    "The porter raised one eyebrow, but Luna raised both.",
    "They wrote the clue on a slate so a guess would not wander away with it.",
    "A sparrow outside chirped as if it, too, wanted to know the answer.",
)


def story_reasonable(place: str) -> bool:
    return place in VESTIBULES


def explain_rejection(place: str) -> str:
    return f"The place '{place}' is not one of the story's vestibules."


def build_world(params: StoryParams) -> World:
    if not story_reasonable(params.place):
        raise StoryError(explain_rejection(params.place))
    if params.case_id not in CASES:
        raise StoryError(f"Unknown vestibule case '{params.case_id}'.")
    if params.telling_mode not in TELLING_MODES:
        raise StoryError(f"Unknown telling mode '{params.telling_mode}'.")

    case = CASES[params.case_id]
    world = World(VESTIBULES[params.place])
    hero = world.add(Entity(params.hero_name, "character", params.hero_name))
    helper = world.add(Entity(params.helper_name, "character", params.helper_name))
    door = world.add(Entity("vestibule_door", "place", "the vestibule door"))
    clue = world.add(Entity("odd_clue", "clue", case.message))

    hero.add_meter("curiosity", 2)
    hero.add_meme("confidence", 1)
    helper.add_meter("patience", 2)
    helper.add_meme("kindness", 1)
    door.add_meter("threshold", 1)
    clue.add_meme("ambiguity", 2)

    world.facts.update(
        hero=hero,
        helper=helper,
        case=case,
        clue=clue,
        misunderstanding=True,
        tested=False,
        repaired=False,
    )

    world.say(OPENINGS[params.telling_mode])
    world.say(
        f"In {world.place}, {params.hero_name} helped {params.helper_name} welcome "
        "neighbors, merchants, and wandering hens."
    )
    world.say(f"{case.setup}. {case.message}.")
    world.say(BRIDGES[params.detail_id % len(BRIDGES)])
    world.say(f"The words caused a misunderstanding: {case.misunderstanding}.")
    world.say(f"Soon, {case.funny_sight}.")
    world.say(f"'Is this the proper welcome?' Luna asked. '{params.helper_name}, what do you think?'")
    world.say(
        f"'{params.hero_name}, a message is not a map,' said {params.helper_name}. "
        "'Let us ask, look, and listen before we leap.'"
    )
    world.say(f"Together they decided to {case.test}.")
    world.facts["tested"] = True
    world.say(f"Then the truth came tumbling out: {case.truth}.")
    world.say(f"'Aha!' said Luna. 'My guess wore a very silly hat.'")
    world.say(f"They chose to {case.repair}.")
    world.facts["repaired"] = True
    hero.add_meme("understanding", 2)
    helper.add_meme("trust", 1)
    world.say(f"They remembered that {case.lesson}.")
    world.say(
        f"By sunset, {case.ending}. Luna swept the vestibule, and the doorway felt "
        "ready for the next true story."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    return [
        f"Write a folk tale set in {world.place} about Luna misunderstanding this message: {case.message}.",
        f"Include humor, a spoken exchange, a test of the clue, and a rhyme-like lesson about {case.lesson}.",
        f"End with a concrete image showing how the vestibule changed after learning that {case.truth}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    return [
        QAItem(
            "Where did Luna help the porter?",
            f"Luna helped the porter in {world.place}, where travelers entered through the vestibule.",
        ),
        QAItem(
            "What misunderstanding did Luna have?",
            f"She misunderstood the message and believed that {case.misunderstanding.lower()}.",
        ),
        QAItem(
            "What funny thing happened?",
            f"The humor came when {case.funny_sight}.",
        ),
        QAItem(
            "How did Luna and the porter discover the truth?",
            f"They discovered it when they chose to {case.test}; then they learned that {case.truth}.",
        ),
        QAItem(
            "How did they repair the problem?",
            f"They repaired it by choosing to {case.repair}.",
        ),
        QAItem(
            "What lesson did Luna learn?",
            f"She learned that {case.lesson}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a vestibule?",
            "A vestibule is a small entrance space between an outside door and the rooms inside.",
        ),
        QAItem(
            "Why can a misunderstanding happen?",
            "A misunderstanding can happen when words are unclear or someone guesses without checking what they mean.",
        ),
        QAItem(
            "What is a folk tale?",
            "A folk tale is a traditional-style story often told with memorable characters, humor, and a simple lesson.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_place/1.
#show valid_story/1.
valid_place(P) :- vestibule(P).
valid_story(P) :- valid_place(P), has_clue(P), has_helper(P), has_repair(P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [asp.fact("vestibule", key) for key in VESTIBULES]
    for key in VESTIBULES:
        lines.extend(
            [
                asp.fact("has_clue", key),
                asp.fact("has_helper", key),
                asp.fact("has_repair", key),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(asp.atoms(model, "valid_place"))


def asp_verify() -> int:
    asp_places = {item[0] for item in asp_valid_places()}
    py_places = set(VESTIBULES)
    if asp_places != py_places:
        print("MISMATCH between ASP and Python registries.")
        print("ASP only:", sorted(asp_places - py_places))
        print("Python only:", sorted(py_places - asp_places))
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 3:
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP gate matches Python registry ({len(py_places)} vestibules).")
    print(f"OK: generated {len(CURATED)} complete stories.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A humorous rhyming folk tale about a vestibule misunderstanding."
    )
    parser.add_argument("--place", choices=sorted(VESTIBULES))
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--case-id", choices=sorted(CASES))
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: Optional[int] = None,
) -> StoryParams:
    place = args.place or rng.choice(list(VESTIBULES))
    hero_name = args.hero_name or rng.choice(["Luna", "Mira", "Tavi", "Nell"])
    helper_name = args.helper_name or rng.choice(["Perrin", "Aunt Bria", "Old Tom", "Mara"])
    index = sample_seed if sample_seed is not None else rng.randrange(2**31)
    case_id = args.case_id or list(CASES)[index % len(CASES)]
    mode = args.telling_mode or TELLING_MODES[(index // len(CASES)) % len(TELLING_MODES)]
    return StoryParams(
        place=place,
        hero_name=hero_name,
        helper_name=helper_name,
        case_id=case_id,
        telling_mode=mode,
        detail_id=(index // 7) % len(BRIDGES),
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---", f"place: {world.place}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"facts: tested={world.facts['tested']} repaired={world.facts['repaired']}")
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


CURATED = [
    StoryParams("oak", "Luna", "Perrin", "blue_bell", "rhyme_first", 0),
    StoryParams("river", "Mira", "Aunt Bria", "goat_guest", "dialogue_first", 1),
    StoryParams("hill", "Tavi", "Old Tom", "moon_cloak", "clue_first", 2),
    StoryParams("market", "Nell", "Mara", "three_knocks", "quiet_first", 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("\n".join(place[0] for place in asp_valid_places()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            sample_seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(sample_seed), sample_seed)
            sample = generate(params)
            if sample.story not in seen:
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
