#!/usr/bin/env python3
"""
A small mystery quest about linden leaves, a strange piece of slag, and a
missing beard-shaped key.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

try:
    from storyworlds.results import QAItem, StoryError, StorySample
except ModuleNotFoundError:
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, _root)
    from results import QAItem, StoryError, StorySample  # type: ignore


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    helper_name: str = "Milo"
    keeper_name: str = "Aunt Sella"
    place: str = "the old linden mill"
    clue_style: str = "ash"


HERO_NAMES = ["Luna", "Nora", "Pip", "Tavi", "Mira", "Rowan"]
HELPER_NAMES = ["Milo", "Wren", "Ivo", "Bram", "Tansy"]
KEEPER_NAMES = ["Aunt Sella", "Master Orin", "Old Nessa", "Keeper Vale"]
PLACES = ["the old linden mill", "the hilltop forge", "the village archive"]
CLUE_STYLES = ["ash", "rain", "bell", "moss"]

CASES = [
    {
        "title": "The Sooty Footprint",
        "opening": "A thin trail of gray dust crossed the floor beside the linden press.",
        "secret": "a loose floorboard beneath the press",
        "answer": "the missing beard-shaped key had been hidden under the loose board",
        "turn": "Luna noticed that the slag dust stopped exactly at one floorboard",
        "ending": "the key returned to the archive chest, while fresh linden leaves dried in a bright green ring",
    },
    {
        "title": "The Cold Ember",
        "opening": "A cold black fleck of slag rested inside a basket of linden leaves.",
        "secret": "the hollow behind the old chimney",
        "answer": "the missing beard-shaped key had been tucked behind the chimney",
        "turn": "Milo found a matching scrape on the chimney stone",
        "ending": "the key hung beside the ledger, and the chimney held only clean winter light",
    },
    {
        "title": "The Bent Leaf Mark",
        "opening": "One linden leaf lay folded into the shape of a tiny beard.",
        "secret": "a narrow drawer in the map table",
        "answer": "the missing beard-shaped key had been placed in the map drawer",
        "turn": "Luna matched the folded leaf to a notch on the drawer's brass handle",
        "ending": "the drawer closed around its maps, and the key shone under the keeper's lamp",
    },
    {
        "title": "The Ashen Bell",
        "opening": "The warning bell gave one dull ring, although nobody had touched its rope.",
        "secret": "the bell's wooden mounting box",
        "answer": "the missing beard-shaped key had slipped into the bell box",
        "turn": "a grain of slag fell when Luna gently lifted the bell rope",
        "ending": "the bell rang clearly again, with the key safe in the keeper's pocket",
    },
]

ASP_RULES = r"""
% A quest is solvable when the clue points to the hidden key.
quest_active :- quest.
clue_supports_key :- slag_clue, linden_clue, beard_clue.
solved :- quest_active, clue_supports_key, key_found.
safe_return :- solved, key_returned.
#show quest_active/0.
#show clue_supports_key/0.
#show solved/0.
#show safe_return/0.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A mystery quest about linden, slag, and a beard-shaped key.")
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--keeper-name")
    parser.add_argument("--place")
    parser.add_argument("--clue-style", choices=CLUE_STYLES)
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
    hero = args.hero_name or rng.choice(HERO_NAMES)
    helper = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero])
    keeper = args.keeper_name or rng.choice(KEEPER_NAMES)
    place = args.place or rng.choice(PLACES)
    clue_style = args.clue_style or rng.choice(CLUE_STYLES)
    if hero == helper:
        raise StoryError("The hero and helper must have different names.")
    return StoryParams(
        seed=args.seed,
        hero_name=hero,
        helper_name=helper,
        keeper_name=keeper,
        place=place,
        clue_style=clue_style,
    )


def make_world(params: StoryParams) -> World:
    world = World()
    world.add(Entity(
        "hero", "character", params.hero_name,
        meters={"care": 0.8, "distance": 0.0},
        memes={"curiosity": 0.9, "courage": 0.7, "trust": 0.3},
    ))
    world.add(Entity(
        "helper", "character", params.helper_name,
        meters={"care": 0.6, "distance": 0.0},
        memes={"curiosity": 0.8, "doubt": 0.4},
    ))
    world.add(Entity(
        "keeper", "character", params.keeper_name,
        meters={"distance": 1.0},
        memes={"worry": 0.8, "trust": 0.4},
    ))
    world.add(Entity(
        "linden", "plant", "the linden tree",
        meters={"leaf_scent": 1.0, "shade": 0.9},
        memes={"calm": 0.7},
    ))
    world.add(Entity(
        "slag", "clue", "the black slag",
        meters={"weight": 0.4, "roughness": 0.9},
        memes={"mystery": 0.8},
    ))
    world.add(Entity(
        "beard", "object", "the beard-shaped key",
        meters={"weight": 0.3, "safety": 0.2},
        memes={"importance": 1.0},
        owner="keeper",
    ))
    world.facts.update(
        place=params.place,
        hero=params.hero_name,
        helper=params.helper_name,
        keeper=params.keeper_name,
        linden="linden",
        slag="slag",
        beard="beard",
        key_found=False,
        key_returned=False,
    )
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    seed = params.seed
    if seed is None:
        seed = sum(ord(c) for c in params.hero_name + params.place + params.clue_style)
    rng = random.Random(seed ^ 0xB34D)
    case = rng.choice(CASES)
    hero = params.hero_name
    helper = params.helper_name
    keeper = params.keeper_name

    world.facts.update(
        case_title=case["title"],
        opening=case["opening"],
        hiding_place=case["secret"],
        answer=case["answer"],
        turn=case["turn"],
        ending=case["ending"],
        clue_style=params.clue_style,
        clue_method=f"a {params.clue_style}-colored mark beside the slag",
    )

    hero_entity = world.entities["hero"]
    helper_entity = world.entities["helper"]
    slag = world.entities["slag"]
    beard = world.entities["beard"]

    world.say(f"At {params.place}, {hero} guarded the old archive while the linden tree whispered over the roof.")
    world.say(f"{case['opening']} The keeper, {keeper}, had discovered that the beard-shaped key was missing.")
    world.para()
    world.say(f"{keeper} held up an empty hook. \"Without that key, the archive chest must stay closed,\" {keeper} said.")
    world.say(f"{helper} pointed at the black slag. \"Should we move everything until we find it?\"")
    world.say(f"\"No,\" {hero} replied. \"A quest needs clues, not a storm of guesses.\"")
    world.say(f"Near the linden leaves, they found {case['clue_method']}.")
    world.say(f"The slag carried a faint scratch shaped like a beard. It was too small to be an accident.")
    world.para()
    world.say(f"{case['turn']}.")
    world.say(f"{helper} whispered, \"Do you think the mark is telling us where to look?\"")
    world.say(f"\"It is telling us to look carefully,\" {hero} answered. \"Follow the trail, and touch nothing that could hide the truth.\"")
    world.say(f"The linden scent led them toward {case['secret']}. Beneath the dust, the beard-shaped key waited.")
    world.say(f"{hero} lifted it with a linden leaf instead of bare fingers. The rough slag mark matched the key's darkened edge.")
    world.para()
    world.say(f"{case['answer'].capitalize()}.")
    world.say(f"{keeper} hurried over. \"You solved the mystery,\" {keeper} said.")
    world.say(f"{hero} handed over the key. \"The clues solved it. We only listened.\"")
    world.say(f"{helper} smiled. \"And we did not wreck the room looking for a shortcut.\"")
    world.say(f"{keeper} locked the key away and recorded the slag mark beside the linden clue.")
    world.say(f"At sunset, {case['ending']}.")

    hero_entity.memes["trust"] += 0.6
    hero_entity.memes["courage"] += 0.2
    helper_entity.memes["doubt"] = 0.0
    helper_entity.memes["trust"] += 0.4
    slag.meters["mystery"] = 0.0
    beard.meters["safety"] = 1.0
    world.facts["key_found"] = True
    world.facts["key_returned"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly Mystery Quest about {f['hero']} following linden, slag, and beard-shaped key clues at {f['place']}.",
        f"Tell a mystery in which {f['hero']} and {f['helper']} solve the disappearance of a beard-shaped key without damaging the archive.",
        f"Write a short Quest mystery using linden leaves, black slag, careful dialogue, and a satisfying recovered object.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What was missing at {f['place']}?",
            answer=f"The keeper's beard-shaped key was missing, so the archive chest could not be opened.",
        ),
        QAItem(
            question="What clues helped solve the mystery?",
            answer=f"The investigators followed the linden scent, examined the black slag, and used {f['clue_method']} to locate the key.",
        ),
        QAItem(
            question=f"What did {f['hero']} decide when {f['helper']} suggested searching carelessly?",
            answer=f"{f['hero']} decided that the quest needed clues rather than guesses and chose to follow the evidence carefully.",
        ),
        QAItem(
            question="Where was the key found?",
            answer=f"The beard-shaped key was found at {f['hiding_place']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The key was returned safely, its clue was recorded, and {f['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is linden?",
            answer="Linden is a tree with heart-shaped leaves and fragrant flowers.",
        ),
        QAItem(
            question="What is slag?",
            answer="Slag is a rough material left behind when metal is melted or separated from rock.",
        ),
        QAItem(
            question="What is a beard?",
            answer="A beard is hair that grows on a person's chin and cheeks.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey or challenge undertaken to find, solve, or achieve something.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 3) for k, v in entity.meters.items()}
        memes = {k: round(v, 3) for k, v in entity.memes.items()}
        lines.append(
            f"  {entity.id}: {entity.label}; meters={meters}; memes={memes}; owner={entity.owner}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("quest"),
        asp.fact("slag_clue"),
        asp.fact("linden_clue"),
        asp.fact("beard_clue"),
        asp.fact("key_found"),
        asp.fact("key_returned"),
    ])


def asp_program(show: str = "#show solved/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    symbols = asp.one_model(asp_program())
    names = {symbol.name for symbol in symbols}
    expected = {"solved"}
    if expected.issubset(names):
        print("OK: ASP quest gate matches the Python resolution.")
        return 0
    print("MISMATCH: ASP quest gate did not find solved.")
    print("  got:", sorted(names))
    return 1


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(hero_name="Luna", helper_name="Milo", keeper_name="Aunt Sella", place="the old linden mill", clue_style="ash"),
    StoryParams(hero_name="Nora", helper_name="Wren", keeper_name="Master Orin", place="the hilltop forge", clue_style="rain"),
    StoryParams(hero_name="Pip", helper_name="Ivo", keeper_name="Old Nessa", place="the village archive", clue_style="bell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_active/0. #show clue_supports_key/0. #show solved/0. #show safe_return/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        for symbol in asp.one_model(asp_program("#show quest_active/0. #show clue_supports_key/0. #show solved/0. #show safe_return/0.")):
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, params in enumerate(CURATED):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for index in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + index
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
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
