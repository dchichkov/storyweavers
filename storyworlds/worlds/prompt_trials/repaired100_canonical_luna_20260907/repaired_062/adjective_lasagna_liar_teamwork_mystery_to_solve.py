#!/usr/bin/env python3
"""
A nursery-rhyme storyworld about an adjective, a lasagna, a liar, teamwork,
and a small mystery to solve.
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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: {"clue_care": 0.0, "trust": 0.5})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "courage": 0.0, "honesty": 0.0})
    inventory: list[str] = field(default_factory=list)


@dataclass
class Lasagna:
    adjective: str
    layers: int = 3
    missing_corner: bool = True
    owner: str = "the village table"
    meters: dict[str, float] = field(default_factory=lambda: {"warmth": 1.0, "fullness": 1.0})
    memes: dict[str, float] = field(default_factory=lambda: {"welcome": 1.0})


@dataclass
class Setting:
    place: str = "the moonlit kitchen"
    description: str = "a little kitchen with a round table, a blue oven, and a window full of stars"


@dataclass
class StoryParams:
    place: str = "the moonlit kitchen"
    hero_name: str = "Luna"
    hero_kind: str = "girl"
    friend_name: str = "Pip"
    friend_kind: str = "mouse"
    suspect_name: str = "Bram"
    suspect_kind: str = "crow"
    adjective: str = "golden"
    scenario_id: int = 0
    rhyme_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Mystery:
    opening: str
    problem: str
    false_claim: str
    clue: str
    teamwork: str
    discovery: str
    resolution: str
    lesson: str
    ending_image: str


MYSTERIES = (
    Mystery(
        opening="A {adjective} lasagna cooled on a platter while the village supper bell rang ding-ding.",
        problem="One corner was gone, though no fork, crumb, or plate had moved from the table.",
        false_claim="'I saw Pip take it,' said {suspect}, with a flap and a frown.",
        clue="Luna found a red cheese dab on the windowsill and three tiny floury footprints beneath it.",
        teamwork="{hero} counted the footprints while {friend} followed the cheese marks toward the pantry.",
        discovery="the trail ended beside a loose cat door, where a hungry kitten had curled up with the missing corner",
        resolution="They invited the kitten to the table, then cut the remaining layers into fair, warm squares.",
        lesson="a quick accusation is not a careful answer",
        ending_image="four bowls shone beneath the moon, and the kitten purred beside the empty platter",
    ),
    Mystery(
        opening="A {adjective} lasagna sat in the kitchen, and its bubbling top went pop-pop-pop.",
        problem="The supper card said eight portions, but the platter held only seven neat squares.",
        false_claim="'The baker forgot one,' cried {suspect}, though the baker had counted twice.",
        clue="Pip noticed a buttery thumbprint on the cupboard handle and a noodle folded like a tiny flag.",
        teamwork="{hero} checked the recipe card while {friend} searched the cupboards without touching the food.",
        discovery="the extra square had been placed on the high shelf for the shy night gardener",
        resolution="They carried the saved square outside and learned that it had been promised, not stolen.",
        lesson="a hidden promise can look like a mystery until kind questions uncover it",
        ending_image="the gardener bowed beneath the stars while seven friends shared the rest",
    ),
    Mystery(
        opening="By the little oven lay a {adjective} lasagna, warm as a rhyme and wide as a drum.",
        problem="A spoonful of sauce had vanished, and a red trail led away from the dish.",
        false_claim="'The liar is Pip,' announced {suspect}; 'that mouse always loves a taste.'",
        clue="Luna heard a soft cough behind the flour sack and saw sauce on a silver bell.",
        teamwork="{hero} lifted the sack carefully while {friend} rang the bell to call the cook.",
        discovery="the old bell-ringer had tasted the sauce only to check whether it needed salt",
        resolution="The cook thanked the checker, added a pinch of herbs, and served everyone a proper helping.",
        lesson="truth grows clearer when friends inspect clues together",
        ending_image="the bell chimed bright as the lasagna passed from hand to hand",
    ),
    Mystery(
        opening="Three layers of {adjective} lasagna waited beneath a cloth, humming yum-yum-yum.",
        problem="The serving spoon was missing, and someone claimed it had never been on the table.",
        false_claim="'No spoon was here,' said {suspect}, hiding a shiny handle behind one wing.",
        clue="A crescent of sauce shone on the floor beside the broom closet.",
        teamwork="{hero} swept gently toward the closet while {friend} peeped behind the flour bin.",
        discovery="the spoon had slid away when a wagging puppy bumped the table, and {suspect} had hidden it in embarrassment",
        resolution="The crow admitted the lie, returned the spoon, and helped serve every guest.",
        lesson="telling the truth repairs a friendship faster than hiding a mistake",
        ending_image="the spoon made a merry circle, and nobody ate alone",
    ),
)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, eid: str, entity: object) -> object:
        self.entities[eid] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _fill(text: str, params: StoryParams) -> str:
    return text.format(
        hero=params.hero_name,
        friend=params.friend_name,
        suspect=params.suspect_name,
        adjective=params.adjective,
    )


def _rhyme(mode: int, hero: Character, friend: Character) -> str:
    lines = (
        f"{hero.name} said, 'A clue, a clue!' and {friend.name} said, 'Me too!'",
        f"'Look low, look high,' said {hero.name}; {friend.name} answered, 'We shall try!'",
        f"{hero.name} tapped twice, and {friend.name} tapped thrice; teamwork made the search precise.",
        f"'Not blame but care,' said {hero.name}; 'Not guess but share,' replied {friend.name}.",
        f"{hero.name} sang, 'We seek the truth!' {friend.name} danced, 'With eyes and proof!'",
    )
    return lines[mode % len(lines)]


def tell(params: StoryParams) -> World:
    if params.hero_name == params.friend_name:
        raise StoryError("hero_name and friend_name must be different")
    if params.hero_name == params.suspect_name or params.friend_name == params.suspect_name:
        raise StoryError("all character names must be different")
    if not params.adjective.strip():
        raise StoryError("adjective must not be empty")

    setting = Setting(place=params.place)
    world = World(setting)
    hero = world.add("hero", Character(params.hero_name, params.hero_kind))
    friend = world.add("friend", Character(params.friend_name, params.friend_kind))
    suspect = world.add("suspect", Character(params.suspect_name, params.suspect_kind))
    dish = world.add("lasagna", Lasagna(params.adjective))
    mystery = MYSTERIES[params.scenario_id % len(MYSTERIES)]

    hero.memes["curiosity"] = 1.0
    friend.memes["courage"] = 1.0
    suspect.memes["trust"] = 0.2 if "trust" in suspect.memes else 0.0

    world.say(
        f"In {setting.place}, {params.hero_name} and {params.friend_name} heard the supper bell ring. "
        f"{setting.description.capitalize()} waited quietly around them."
    )
    world.say(_fill(mystery.opening, params))
    world.say(
        f"The word '{params.adjective}' is an adjective: it describes the lasagna. "
        f"It told everyone what sort of lasagna waited on the platter."
    )

    world.para()
    world.say(_fill(mystery.problem, params))
    world.say(_fill(mystery.false_claim, params))
    world.say(
        f"{params.hero_name} frowned. '{params.suspect_name}, are you sure?' "
        f"asked {params.friend_name}. '{params.hero_name}, I am sure,' replied {params.suspect_name}, "
        "though one wing trembled."
    )
    world.say(_rhyme(params.rhyme_mode, hero, friend))

    world.para()
    world.say(_fill(mystery.clue, params))
    world.say(
        f"{params.hero_name} said, '{params.friend_name}, let us follow facts, not guesses.' "
        f"{params.friend_name} nodded. 'Together, we can solve this.'"
    )
    world.say(_fill(mystery.teamwork, params))
    world.say(_fill(mystery.discovery, params))

    hero.meters["clue_care"] = 1.0
    friend.meters["clue_care"] = 1.0
    hero.memes["honesty"] = 1.0
    friend.memes["honesty"] = 1.0
    suspect.memes["honesty"] = 1.0
    suspect.meters["trust"] = 1.0
    dish.missing_corner = False
    world.events.extend(["mystery_noticed", "false_claim_heard", "clue_found", "teamwork_used", "truth_revealed"])

    world.say(_fill(mystery.resolution, params))
    world.say(
        f"'{params.suspect_name}, thank you for telling the truth,' said {params.hero_name}. "
        f"'And thank you for helping,' said {params.friend_name}. The liar became a helper."
    )

    world.para()
    endings = (
        f"They remembered that {mystery.lesson}.",
        f"The rhyme settled softly: {mystery.lesson}.",
        f"From that day on, they knew that {mystery.lesson}.",
        f"{params.suspect_name} learned beside them that {mystery.lesson}.",
    )
    world.say(endings[params.ending_mode % len(endings)])
    world.say(_fill(mystery.ending_image, params))

    world.facts.update(
        hero=hero,
        friend=friend,
        suspect=suspect,
        lasagna=dish,
        mystery=mystery,
        problem=_fill(mystery.problem, params),
        false_claim=_fill(mystery.false_claim, params),
        clue=_fill(mystery.clue, params),
        teamwork=_fill(mystery.teamwork, params),
        discovery=_fill(mystery.discovery, params),
        resolution=_fill(mystery.resolution, params),
        lesson=mystery.lesson,
        ending=_fill(mystery.ending_image, params),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Character = f["hero"]
    friend: Character = f["friend"]
    return [
        f"Write a nursery-rhyme mystery about {hero.name} and {friend.name} solving this problem: {f['problem']}",
        f"Show how teamwork uncovers this clue: {f['clue']}",
        f"Describe the {f['lasagna'].adjective} lasagna and explain why accusing a liar requires careful evidence.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Character = f["hero"]
    friend: Character = f["friend"]
    suspect: Character = f["suspect"]
    return [
        QAItem(
            question=f"What mystery did {hero.name} and {friend.name} solve?",
            answer=f"They solved this mystery: {f['problem']}"
        ),
        QAItem(
            question=f"What clue helped {hero.name} and {friend.name}?",
            answer=f"They found this clue: {f['clue']}. It led them to discover that {f['discovery']}."
        ),
        QAItem(
            question="How did teamwork help?",
            answer=f"{hero.name} and {friend.name} worked together because {f['teamwork']}. Their shared search revealed the truth."
        ),
        QAItem(
            question=f"What happened to {suspect.name}'s false claim?",
            answer=f"{suspect.name}'s claim was tested against the clues. The friends learned that {f['discovery']}."
        ),
        QAItem(
            question="What lesson did the characters learn?",
            answer=f"They learned that {f['lesson']}. The lasagna was then shared fairly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an adjective?",
            answer="An adjective is a word that describes a person, place, animal, or thing, such as the word 'golden' in 'golden lasagna.'"
        ),
        QAItem(
            question="What is lasagna?",
            answer="Lasagna is a baked dish made with layers of pasta, sauce, and often cheese or vegetables."
        ),
        QAItem(
            question="Why should a mystery be solved with clues?",
            answer="Clues give people evidence, so they can learn what happened instead of blaming someone from a guess."
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people helping one another and combining their skills to reach a shared goal."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
hero(luna).
friend(pip).
suspect(bram).
dish(lasagna).
mystery_found :- clue_found, teamwork_used.
truth_revealed :- mystery_found, honest_answer.
shared_meal :- truth_revealed, dish(lasagna).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("clue_found"),
            asp.fact("teamwork_used"),
            asp.fact("honest_answer"),
        ]
    )


def asp_program(show: str = "#show mystery_found/0. #show truth_revealed/0. #show shared_meal/0.") -> str:
    return f"{ASP_RULES}\n{asp_facts()}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nursery-rhyme lasagna mystery storyworld.")
    parser.add_argument("--place", default=None)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(["the moonlit kitchen", "the village hall", "the yellow pantry"]),
        hero_name=rng.choice(["Luna", "Nell", "Mara", "Tess"]),
        hero_kind="girl",
        friend_name=rng.choice(["Pip", "Moss", "Dot", "Bibi"]),
        friend_kind=rng.choice(["mouse", "rabbit", "sparrow", "hedgehog"]),
        suspect_name=rng.choice(["Bram", "Cobb", "Rook", "Tumble"]),
        suspect_kind=rng.choice(["crow", "fox", "goat", "magpie"]),
        adjective=rng.choice(["golden", "cheesy", "jolly", "warm"]),
        scenario_id=rng.randrange(len(MYSTERIES)),
        rhyme_mode=rng.randrange(5),
        ending_mode=rng.randrange(4),
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


def dump_trace(world: World) -> str:
    hero: Character = world.entities["hero"]
    friend: Character = world.entities["friend"]
    suspect: Character = world.entities["suspect"]
    dish: Lasagna = world.entities["lasagna"]
    return "\n".join(
        [
            "--- world trace ---",
            f"place: {world.setting.place}",
            f"hero: {hero.name} kind={hero.kind} meters={hero.meters} memes={hero.memes}",
            f"friend: {friend.name} kind={friend.kind} meters={friend.meters} memes={friend.memes}",
            f"suspect: {suspect.name} kind={suspect.kind} meters={suspect.meters} memes={suspect.memes}",
            f"lasagna: adjective={dish.adjective} missing_corner={dish.missing_corner} layers={dish.layers}",
            f"events: {world.events}",
        ]
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    expected = {"mystery_found", "truth_revealed", "shared_meal"}
    actual = {str(atom) for atom in model}
    if not all(name in actual for name in expected):
        print("MISMATCH: ASP twin did not derive the complete resolution.")
        return 1
    sample = generate(StoryParams())
    if "teamwork" not in sample.story.lower() or "lasagna" not in sample.story.lower():
        print("MISMATCH: generated story lacks required world evidence.")
        return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program())
            print("mystery_found:", asp.atoms(model, "mystery_found"))
            print("truth_revealed:", asp.atoms(model, "truth_revealed"))
            print("shared_meal:", asp.atoms(model, "shared_meal"))
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            raise SystemExit(1)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(place="the moonlit kitchen", hero_name="Luna", friend_name="Pip", suspect_name="Bram", adjective="golden", scenario_id=i)
            for i in range(len(MYSTERIES))
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples = [
            generate(resolve_params(args, random.Random(base_seed + i)))
            for i in range(max(0, args.n))
        ]

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
