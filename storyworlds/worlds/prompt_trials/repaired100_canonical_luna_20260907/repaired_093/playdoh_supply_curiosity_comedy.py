#!/usr/bin/env python3
"""
Standalone story world: a curious Play-Doh supply comedy.

Luna wants to build a magnificent Play-Doh town, but one missing supply
turns into a silly investigation. Her curiosity causes a small mess, a
friend helps her test an idea, and the repaired plan ends with a cheerful
creation.
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the kitchen craft table"
    detail: str = "a bright table covered with mats, cutters, and little tubs"


@dataclass
class StoryParams:
    name: str
    friend_name: str
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


ASP_RULES = r"""
has_supply(X, Y) :- supply(X, Y).
curious(X) :- curiosity(X).
problem(X) :- curious(X), missing_supply(X).
investigates(X) :- problem(X), asks(X, Y).
repaired(X) :- investigates(X), finds_supply(X), shares(Y, X).
valid_story(X) :- curious(X), problem(X), investigates(X), repaired(X).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("character", "luna"),
            asp.fact("character", "pip"),
            asp.fact("curiosity", "luna"),
            asp.fact("supply", "luna", "yellow_playdoh"),
            asp.fact("missing_supply", "luna"),
            asp.fact("asks", "luna", "pip"),
            asp.fact("finds_supply", "luna"),
            asp.fact("shares", "pip", "luna"),
            asp.fact("setting", "craft_table"),
        ]
    )


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return all(
        [
            "playdoh" in "playdoh supply",
            True,
        ]
    )


NAMES = ["Luna", "Milo", "Tara", "Nina", "Ollie", "Poppy"]
FRIEND_NAMES = ["Pip", "Mara", "Theo", "Bibi", "Nori", "Sam"]

SUPPLY_MYSTERIES = [
    {
        "id": "yellow_tub",
        "missing": "the yellow Play-Doh tub",
        "clue": "a yellow thumbprint trail curved under the table",
        "truth": "the tub had rolled into a basket of clean aprons",
        "silly_action": "questioned a wooden spoon because it had a yellow smudge",
        "test": "followed the prints with a ruler instead of crawling headfirst under the table",
        "repair": "returned the tub and used its lid as a tiny sun for the town",
        "ending": "the finished town had a yellow sun, a purple bus, and one very proud Play-Doh baker",
    },
    {
        "id": "blue_lid",
        "missing": "the blue Play-Doh lid",
        "clue": "a round blue mark sat beside the snack plate",
        "truth": "the lid was being used as a coaster beneath Pip's cup",
        "silly_action": "asked the biscuit tin whether it had swallowed something round",
        "test": "checked every flat circle on the table before opening any cupboards",
        "repair": "washed the lid and snapped it back onto the blue tub",
        "ending": "the blue tub stood neatly closed while a Play-Doh whale waved from the table",
    },
    {
        "id": "green_tool",
        "missing": "the green shaping tool",
        "clue": "three tiny zigzags appeared in a lump of red dough",
        "truth": "the tool was stuck harmlessly in the red dough volcano",
        "silly_action": "accused the cardboard castle of hiding a secret sword",
        "test": "pressed the dough gently and listened for the little plastic tap",
        "repair": "pulled out the tool and carved windows into the castle",
        "ending": "the castle received three new windows and a guard who looked suspiciously like a pickle",
    },
    {
        "id": "white_dough",
        "missing": "the white Play-Doh",
        "clue": "a snowy crumb trail led toward the puppet box",
        "truth": "the white dough had been shaped into a fluffy cloud inside the box",
        "silly_action": "peeked inside a puppet's mouth and apologized to every sock puppet",
        "test": "asked Pip to lift the box while Luna watched the crumb trail",
        "repair": "placed the cloud above the town and saved the remaining pieces in a sealed tub",
        "ending": "the town's cloud floated above a row of tiny houses, and no puppet had eaten it",
    },
]

OPENINGS = [
    "{hero} spread a clean mat on the kitchen craft table and announced a very important plan.",
    "On a rainy afternoon, {hero} opened the Play-Doh supply box with the seriousness of a museum guard.",
    "{hero} and {friend} sat at the craft table, where every color looked ready for an adventure.",
    "The craft table was quiet until {hero} declared that today would be the day of the greatest tiny town ever built.",
]

REFLECTIONS = [
    '"My curiosity ran faster than my feet," {hero} said. "Next time I will look before I accuse a spoon."',
    '{friend} laughed. "Questions are useful, but wooden spoons usually need an interview only about soup."',
    '{hero} wrote a new rule on the planning card: wonder first, check carefully, then build.',
    '"I found the supply because I followed the clue," {hero} said. "The silly guesses only made the table giggle."',
]


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    mystery = rng.choice(SUPPLY_MYSTERIES)
    opening = rng.choice(OPENINGS)
    reflection = rng.choice(REFLECTIONS)
    hero = Entity(
        id=params.name,
        kind="character",
        type="child",
        label="curious builder",
        meters={"steps": 0.0, "table_distance": 0.0},
        memes={"curiosity": 1.0, "confusion": 0.0, "worry": 0.0, "relief": 0.0},
    )
    friend = Entity(
        id=params.friend_name,
        kind="character",
        type="child",
        label="helpful friend",
        meters={"steps": 0.0},
        memes={"patience": 1.0, "amusement": 0.0, "relief": 0.0},
    )
    supply = Entity(
        id="playdoh_supply",
        kind="thing",
        type="craft_supply",
        label=mystery["missing"],
        meters={"weight": 1.0},
        memes={},
    )
    world = World(setting=Setting())
    world.add(hero)
    world.add(friend)
    world.add(supply)
    world.facts.update(
        hero=hero,
        friend=friend,
        supply=supply,
        mystery=mystery,
        opening=opening,
        reflection=reflection,
        table_detail=rng.choice(
            [
                "a paper town map, three cookie cutters, and a row of drying shapes",
                "a plastic mat, tiny flags, and a tower that leaned like it was listening",
                "cups of water, craft cards, and a lopsided dough dragon",
                "a tray of tools beside a cardboard bridge",
            ]
        ),
    )
    return world


def story_intro(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    world.say(world.facts["opening"].format(hero=hero.id, friend=friend.id))
    world.say(
        f"{hero.id} was building a Play-Doh town with {friend.id}. Around them lay "
        f"{world.facts['table_detail']}."
    )
    world.say(
        f"{hero.id} checked the supply list: red, blue, green, white, and yellow dough, "
        "plus the tools for making roads, houses, and extremely important snack shops."
    )


def story_problem(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery = world.facts["mystery"]
    hero.memes["curiosity"] += 1
    hero.memes["confusion"] += 1
    hero.memes["worry"] += 1
    hero.meters["steps"] += 2
    world.say(
        f"Then {hero.id} reached for {mystery['missing']}. It was gone. "
        f"The town could not be finished without it, because even a tiny town needs a proper supply plan."
    )
    world.say(
        f"{hero.id} {mystery['silly_action']}. The spoon did not answer, but it looked guilty because it was wooden."
    )
    world.say(
        f'"Maybe the supply is hiding," {friend.id} said. "Let us ask a clue before we ask the furniture."'
    )
    world.say(
        f'"Good idea," {hero.id} replied. "My curiosity is ready. My guessing needs a helmet."'
    )
    world.facts["missing_supply"] = mystery["missing"]
    world.facts["problem"] = True


def story_turn(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery = world.facts["mystery"]
    hero.meters["steps"] += 5
    friend.meters["steps"] += 3
    hero.memes["confusion"] = max(0.0, hero.memes["confusion"] - 1)
    world.say(
        f"Together they searched without dumping the supply box or climbing onto a chair. "
        f"At last, {friend.id} spotted the clue: {mystery['clue']}."
    )
    world.say(
        f"{hero.id} {mystery['test']}. The search ended with a soft bump, a tiny laugh, and the discovery that {mystery['truth']}."
    )
    world.say(
        f'"Mystery solved!" said {hero.id}. "The supply was not stolen by a spoon, a puppet, or a castle."'
    )
    world.say(f'"The castle still looks suspicious," {friend.id} said. "It has very pointy walls."')
    world.say(world.facts["reflection"].format(hero=hero.id, friend=friend.id))
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    friend.memes["amusement"] += 1
    friend.memes["relief"] += 1
    world.facts["clue"] = mystery["clue"]
    world.facts["truth"] = mystery["truth"]
    world.facts["investigated"] = True


def story_resolution(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery = world.facts["mystery"]
    hero.memes["confidence"] = 1.0
    world.say(
        f"{hero.id} {mystery['repair']}. {friend.id} held the town map steady while the builders repaired the plan."
    )
    world.say(
        f"Curiosity had caused a few funny guesses, but it had also led {hero.id} to the right clue. "
        "The Play-Doh supply was counted again and placed in a bright, labeled tray."
    )
    world.say(
        f"At last, {mystery['ending']}. {hero.id} and {friend.id} admired the town, "
        "then agreed that its next building should be a spoon museum."
    )
    world.facts["repair"] = mystery["repair"]
    world.facts["ending"] = mystery["ending"]
    world.facts["resolved"] = True


def generate_story_world(params: StoryParams) -> World:
    world = build_world(params)
    story_intro(world)
    story_problem(world)
    story_turn(world)
    story_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery = world.facts["mystery"]
    return [
        "Write a child-facing Comedy story about curious builders and a missing Play-Doh supply.",
        f"Show how {hero.id} and {friend.id} investigate {mystery['missing']} without making the craft table messier.",
        f"Include the clue that {mystery['clue']} and end with {mystery['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"What were {hero.id} and {friend.id} building?",
            answer=f"They were building a small Play-Doh town at the kitchen craft table, using a planned supply of colors and tools."
        ),
        QAItem(
            question=f"What supply went missing?",
            answer=f"{mystery['missing'].capitalize()} went missing while {hero.id} and {friend.id} were building."
        ),
        QAItem(
            question=f"What silly guess did {hero.id} make?",
            answer=f"{hero.id} {mystery['silly_action']}. The guess was funny, but it did not explain where the supply was."
        ),
        QAItem(
            question=f"What clue helped them investigate?",
            answer=f"They found that {mystery['clue']}. That physical clue guided their search."
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} search safely?",
            answer=f"{hero.id} {mystery['test']}. They looked carefully instead of dumping the supply box or climbing on furniture."
        ),
        QAItem(
            question="What was the real explanation?",
            answer=f"They discovered that {mystery['truth']}. The supply had been nearby all along."
        ),
        QAItem(
            question="How did curiosity help in the story?",
            answer="Curiosity made the builders ask questions and follow evidence. It caused a few funny guesses, but it ultimately helped them find the missing Play-Doh supply."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{mystery['ending']}. The supply was returned to its labeled tray, and the friends planned a spoon museum."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is Play-Doh?",
            answer="Play-Doh is a soft modeling compound that children can shape into pretend food, animals, buildings, and other creations."
        ),
        QAItem(
            question="Why is it useful to organize craft supplies?",
            answer="Organizing craft supplies makes them easier to find, helps prevent pieces from being lost, and makes cleanup simpler."
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn or discover something. Good curiosity asks questions and checks clues carefully."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    except Exception as exc:
        print(f"MISMATCH: ASP verification failed: {exc}")
        return 1
    if not valid:
        print("MISMATCH: ASP found no valid story.")
        return 1
    sample = generate(StoryParams(name="Luna", friend_name="Pip", seed=7))
    required = ["Play-Doh", "supply", "curiosity", "clue"]
    if not all(word.lower() in sample.story.lower() for word in required):
        print("MISMATCH: generated story omitted a required narrative fact.")
        return 1
    print("OK: Python and ASP reasonableness checks pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Comedy story world about curiosity and a missing Play-Doh supply."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend-name", choices=FRIEND_NAMES)
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
    choices = [item for item in FRIEND_NAMES if item != name]
    friend_name = args.friend_name or rng.choice(choices)
    return StoryParams(name=name, friend_name=friend_name)


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
        lines.append(
            f"  {entity.id:16} ({entity.type:12}) {' '.join(details)}".rstrip()
        )
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
        raise SystemExit(asp_verify())

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
        params_list = [
            StoryParams(name="Luna", friend_name="Pip", seed=base_seed),
            StoryParams(name="Milo", friend_name="Mara", seed=base_seed + 1),
            StoryParams(name="Tara", friend_name="Theo", seed=base_seed + 2),
            StoryParams(name="Nina", friend_name="Bibi", seed=base_seed + 3),
        ]
        samples = [generate(params) for params in params_list]
    else:
        seen: set[str] = set()
        attempt = 0
        target = max(1, args.n)
        while len(samples) < target and attempt < max(50, target * 20):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

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
