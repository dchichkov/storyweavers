#!/usr/bin/env python3
"""
A gentle nursery-rhyme story world about a repeated tour, numerous helpers,
and a danger of drowning that is solved by careful teamwork.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the winding riverside"
    hero: str = "Luna"
    friend: str = "Pip"
    guide: str = "the bright boatman"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "the winding riverside": {"tags": {"river", "bridge", "repetition"}, "mood": "bright and rippling"},
    "the moonlit marsh": {"tags": {"water", "lantern", "repetition"}, "mood": "silver and quiet"},
    "the singing canal": {"tags": {"canal", "boats", "repetition"}, "mood": "busy and musical"},
}


@dataclass(frozen=True)
class RHYME:
    title: str
    premise: str
    trouble: str
    dialogue: str
    action: str
    result: str
    ending: str
    trouble_answer: str
    action_answer: str
    result_answer: str


RHYMES = [
    RHYME(
        "The Round-and-Round Boat",
        "Luna and Pip began a little tour, rowing past the reeds and counting every door.",
        "A sudden swirl spun their boat around, and water climbed while no safe shore was found.",
        "\"Row once, row twice,\" cried Pip. \"Do not drown!\" Luna answered, \"We will turn the boat around.\"",
        "They followed the repeated rhyme of three taps on the oar and steered toward a red-roofed ferry.",
        "The ferry folk pulled them in, and the boat stopped spinning in the friendly current.",
        "Round went the moon, round went the boat, and safe on the bank their bright lanterns glowed.",
        "A strong swirl spun the tour boat in circles while water rose around Luna and Pip.",
        "They used three repeated oar taps as a rhythm and steered toward the red-roofed ferry.",
        "The ferry folk rescued them and brought the spinning boat into calm water.",
    ),
    RHYME(
        "The Numerous Ducks",
        "Luna led a tour beside the pond, where numerous yellow ducks marched along.",
        "A duckling slipped from the path and began to drown beneath the lily leaves.",
        "\"Quack, quack, come back!\" called Pip. Luna said, \"Hold the reed, and make a rescue track.\"",
        "The numerous ducks repeated the call, lining up from the bank to the duckling while Luna reached with a long reed.",
        "The duckling caught the reed, and every duck waddled home in a cheerful row.",
        "Quack went the flock, quack went the rain, and the little duck danced safely down the lane.",
        "A duckling fell into deep pond water and began to drown under the lily leaves.",
        "The ducks repeated a call and formed a living line while Luna used a long reed to reach the duckling.",
        "The duckling was pulled to safety and returned home with the flock.",
    ),
    RHYME(
        "The Bridge Bell",
        "On a sunny tour, Luna and Pip crossed a bridge where a tiny bell rang ding, ding, ding.",
        "A loose plank dropped away, and Pip slipped toward the river below.",
        "\"Ding once, ding twice,\" called Luna. Pip cried, \"I hear you! Pull me toward the light!\"",
        "Luna repeated the bell rhythm until numerous walkers stopped, joined hands, and hauled Pip back.",
        "The bridge keeper replaced the plank, and everyone crossed in a careful line.",
        "Ding went the bell, step went the feet, and dry little shoes made a dancing beat.",
        "A loose bridge plank made Pip slip toward the river and risk drowning.",
        "Luna rang the bell rhythm repeatedly so numerous walkers would stop and join hands.",
        "The walkers pulled Pip away from the river, and the bridge keeper repaired the plank.",
    ),
    RHYME(
        "The Lantern Tour",
        "Luna took a twilight tour through the marsh with Pip and one small lantern.",
        "Mist hid the path, and their boat drifted toward a deep pool where both might drown.",
        "\"Glow, glow, show the way,\" said Pip. Luna replied, \"We will repeat the light until dawn's first ray.\"",
        "They blinked the lantern twice, waited, and blinked twice again; numerous fireflies copied the pattern.",
        "The fireflies formed a shining trail that guided the boat back to the shallow landing.",
        "Blink went the light, blink went the flies, and home rose warm beneath the skies.",
        "Mist pushed their boat toward a deep pool and hid the safe path back.",
        "They repeated a two-blink lantern pattern, and numerous fireflies copied it.",
        "The fireflies made a glowing trail that led the boat safely to shallow water.",
    ),
    RHYME(
        "The Helpful Herons",
        "Luna and Pip toured the quiet shore while numerous herons stood on one leg by the stream.",
        "A heavy basket tipped into the current, and Pip leaned too far while trying to catch it.",
        "\"One leg, two legs, stand still,\" said Luna. Pip answered, \"A steady friend is stronger than a thrill.\"",
        "The herons repeated their slow wingbeat, and Luna copied it to keep balance while Pip used a branch to pull the basket close.",
        "The basket floated back, and Pip stepped away from the current before anyone could drown.",
        "Wing went the herons, wing went the breeze, and the basket came home through the trees.",
        "Pip leaned over a fast stream to catch a drifting basket and nearly fell in.",
        "The herons' repeated slow wingbeat helped Luna keep balance while Pip used a branch.",
        "They recovered the basket, and Pip moved safely away from the current.",
    ),
    RHYME(
        "The Three Little Ferries",
        "Luna's tour passed three ferries, each painted blue and each singing the same small tune.",
        "The last ferry lost its oar, and numerous passengers feared the river would carry them away.",
        "\"Pull, pull, pass the tune,\" sang Pip. Luna called, \"Together, we will reach the moon!\"",
        "The passengers repeated the tune while passing baskets, ropes, and spare poles from ferry to ferry.",
        "The ferries formed a safe chain, and the stranded passengers reached the dock without a single splash.",
        "Pull went the rope, pass went the pole, and every brave traveler reached the goal.",
        "The last ferry lost its oar, leaving numerous passengers drifting on the river.",
        "Passengers repeated the ferry tune while sharing ropes, baskets, and spare poles.",
        "The three ferries formed a chain and brought everyone safely to the dock.",
    ),
    RHYME(
        "The Pebble Path",
        "Luna and Pip took a tour where pebbles made a pattern: red, blue, red, blue.",
        "Rain covered the stepping stones, and Pip could not see where the deep water began.",
        "\"Red, blue, red,\" said Luna. Pip replied, \"Repeat the path, and keep your toes dry!\"",
        "They repeated the pebble pattern, placing bright leaves beside each safe stone while numerous frogs watched.",
        "The marked path led them across, and the frogs hopped after them to the dry bank.",
        "Red went the pebble, blue went the rain, and dry feet danced down the lane.",
        "Rain hid the stepping stones and made deep water hard to see.",
        "They repeated the red-and-blue pattern and marked each safe stone with a leaf.",
        "The marked path guided Luna, Pip, and the frogs safely to the bank.",
    ),
    RHYME(
        "The River of Echoes",
        "During a riverside tour, Luna heard the water answer every word with a soft echo.",
        "Pip called too close to the bank, slipped on wet moss, and began to slide toward the river.",
        "\"Stop, stop, stay near!\" called Luna. Pip answered, \"Your repeated voice is clear!\"",
        "Luna called the same words again and again while numerous campers formed a rope line behind her.",
        "The rope reached Pip before he touched the water, and the campers pulled him onto the grass.",
        "Stop went the echo, pull went the line, and safe on the grass the two friends would shine.",
        "Pip slipped on wet moss and slid toward the river during the tour.",
        "Luna repeated a clear warning while numerous campers formed a rope line.",
        "The rope reached Pip in time and pulled him safely onto the grass.",
    ),
]


OPENINGS = [
    "Luna and Pip went out on a tour, through {setting}, bright from shore to shore.",
    "Sing a small rhyme, gentle and true: Luna and Pip had a tour to do.",
    "By {setting}, where the waters gleam, Luna carried a lantern and Pip carried a dream.",
    "One, two, three, the day began; Luna and Pip set off with a careful plan.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(ch) for i, ch in enumerate("|".join(
        (params.setting, params.hero, params.friend, params.guide)
    )))


def _fill(text: str, values: dict[str, object]) -> str:
    return text.format(**values)


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def _story_lines(world: World) -> list[str]:
    f = world.facts
    rhyme: RHYME = f["rhyme"]
    values = f
    opening = _fill(OPENINGS[f["opening_variant"]], values)
    premise = _fill(rhyme.premise, values)
    trouble = _fill(rhyme.trouble, values)
    dialogue = _fill(rhyme.dialogue, values)
    action = _fill(rhyme.action, values)
    result = _fill(rhyme.result, values)
    ending = _fill(rhyme.ending, values)
    guide = f["guide"]

    structures = [
        [
            f"{opening} This is the rhyme called \"{rhyme.title}.\"",
            f"{premise} {trouble}",
            f"{_cap(guide)} watched from the bank. {dialogue}",
            action,
            f"{result} \"Repeat the good plan,\" said {guide}, \"and help will come.\"",
            f"{ending} So the tour ended safely, with no one left to drown.",
        ],
        [
            opening,
            f"\"What shall we do?\" asked {f['friend']}. {premise}",
            _cap(trouble),
            dialogue,
            f"Then came the turn: {action}",
            f"{result} {ending}",
        ],
        [
            f"Whenever children sing \"{rhyme.title},\" they begin with this line: {opening}",
            premise,
            f"But trouble came along the way. {trouble}",
            dialogue,
            f"Again and again they worked together. {action}",
            f"{result} From then on, every tour began with a careful look at the water.",
            ending,
        ],
        [
            f"The last verse shows {ending}.",
            f"Before that verse, {f['hero']} and {f['friend']} began their tour. {premise}",
            trouble,
            f"\"Listen to me,\" said {f['hero']}. {dialogue}",
            action,
            f"{result} The rhyme teaches that repeating a safe plan can make numerous helpers brave.",
        ],
        [
            f"One step, two steps, three steps—{opening[0].lower() + opening[1:]}",
            f"{trouble} Nobody hurried, because water can be playful and dangerous.",
            f"{f['friend']} asked, \"Will our plan work?\" {f['hero']} answered, \"We will repeat it together.\"",
            action,
            result,
            f"{ending} And that was the safest ending for their tour.",
        ],
    ]
    return structures[f["structure_variant"]]


ASP_RULES = r"""
setting(winding_riverside).
setting(moonlit_marsh).
setting(singing_canal).

feature(repetition).
danger(drown).
activity(tour).
quantity(numerous).

safe_story(S) :- setting(S), feature(repetition), danger(drown), activity(tour).
safe_story(S) :- setting(S), feature(repetition), quantity(numerous), activity(tour).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for setting in SETTING_REGISTRY:
        key = setting.replace("the ", "").replace(" ", "_")
        lines.append(asp.fact("setting", key))
    lines.extend(
        [
            asp.fact("feature", "repetition"),
            asp.fact("danger", "drown"),
            asp.fact("activity", "tour"),
            asp.fact("quantity", "numerous"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A nursery-rhyme story world about a careful tour by the water."
    )
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--guide")
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Luna", "Milo", "Nell", "Rory", "Tess"])
    friend = args.friend or rng.choice(["Pip", "Bram", "Faye", "Ollie", "Rue"])
    guide = args.guide or rng.choice(
        ["the bright boatman", "the patient ferrymaster", "the red-hatted guide"]
    )
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    if not hero.strip() or not friend.strip() or not guide.strip():
        raise StoryError("Hero, friend, and guide names must not be empty.")
    return StoryParams(setting=setting, hero=hero, friend=friend, guide=guide)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero == params.friend:
        raise StoryError("The hero and friend must be different characters.")

    seed = _stable_seed(params)
    rhyme = RHYMES[seed % len(RHYMES)]
    world = World(setting=params.setting)

    hero = world.add(
        Entity(
            name=params.hero,
            kind="child",
            meters={"balance": 0.7, "distance_from_water": 1.0},
            memes={"care": 1.0, "courage": 0.8},
        )
    )
    friend = world.add(
        Entity(
            name=params.friend,
            kind="child",
            meters={"balance": 0.6, "distance_from_water": 1.0},
            memes={"trust": 1.0, "attention": 0.9},
        )
    )
    guide = world.add(
        Entity(
            name=params.guide,
            kind="helper",
            meters={"reach": 1.0, "boat_skill": 1.0},
            memes={"patience": 1.0, "helpfulness": 1.0},
        )
    )
    world.add(
        Entity(
            name="the river",
            kind="water",
            meters={"depth": 0.9, "current": 0.7},
            memes={"danger": 0.8, "movement": 1.0},
        )
    )
    world.add(
        Entity(
            name="the repeated rhyme",
            kind="pattern",
            meters={"rhythm": 1.0, "clarity": 1.0},
            memes={"coordination": 1.0, "memory": 1.0},
        )
    )
    world.add(
        Entity(
            name="numerous helpers",
            kind="group",
            meters={"number": 1.0, "reach": 0.9},
            memes={"cooperation": 1.0},
        )
    )

    values = {
        "hero": params.hero,
        "friend": params.friend,
        "guide": params.guide,
        "setting": params.setting,
    }
    world.facts.update(
        values,
        rhyme=rhyme,
        opening_variant=(seed // len(RHYMES)) % len(OPENINGS),
        structure_variant=(seed // (len(RHYMES) * len(OPENINGS))) % 5,
        danger="drowning",
        method="repetition",
        helpers="numerous helpers",
        theme="a careful tour by the water",
        problem=_fill(rhyme.trouble, values),
        causal_action=_fill(rhyme.action, values),
        resolution=_fill(rhyme.result, values),
        ending_image=_fill(rhyme.ending, values),
    )

    hero.memes["courage"] = 1.0
    friend.memes["trust"] = 1.0
    world.facts["safe_turn"] = True

    story = "\n\n".join(_story_lines(world))

    prompts = [
        f"Write a nursery rhyme about {params.hero} and {params.friend} taking a careful tour near {params.setting}.",
        "Use repetition, numerous helpers, and a gentle danger involving water.",
        "Write a child-facing rhyme in which repeating a safe plan prevents someone from drowning.",
    ]

    story_qa = [
        QAItem(
            question=f"What danger did {params.hero} and {params.friend} face during their tour?",
            answer=rhyme.trouble_answer,
        ),
        QAItem(
            question="How did repetition help the characters?",
            answer=rhyme.action_answer,
        ),
        QAItem(
            question="What changed by the end of the rhyme?",
            answer=rhyme.result_answer,
        ),
        QAItem(
            question=f"What final image closes \"{rhyme.title}\"?",
            answer=f"The rhyme closes with {world.facts['ending_image']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="Why can water be dangerous?",
            answer="Deep or moving water can pull people away from safety, so children should stay with trusted helpers."
        ),
        QAItem(
            question="How can repetition help in an emergency?",
            answer="Repeating a clear word, signal, or safe step helps many people understand what to do together."
        ),
        QAItem(
            question="What does numerous mean?",
            answer="Numerous means many or a large number of something."
        ),
        QAItem(
            question="What is a tour?",
            answer="A tour is a trip around a place to see and learn about it."
        ),
        QAItem(
            question="What does drown mean?",
            answer="To drown means to be unable to breathe because of being under water; people should seek help immediately around dangerous water."
        ),
    ]

    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={dict(entity.meters)}, memes={dict(entity.memes)}"
            )

    if qa:
        print()
        print("== prompts ==")
        for prompt in sample.prompts:
            print(prompt)

        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")

        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _valid_python() -> list[str]:
    return sorted(
        setting.replace("the ", "").replace(" ", "_")
        for setting in SETTING_REGISTRY
    )


def _asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show safe_story/1."))
    return sorted(set(asp.atoms(model, "safe_story")))


def asp_verify() -> int:
    expected = {(setting,) for setting in _valid_python()}
    actual = set(_asp_valid())

    if expected != actual:
        print("MISMATCH between clingo and python:")
        print("python only:", sorted(expected - actual))
        print("clingo only:", sorted(actual - expected))
        return 1

    rng = random.Random(20260907)
    for _ in range(5):
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated sample was incomplete")
            return 1

    print(f"OK: clingo gate matches python ({len(expected)} settings); generation passed.")
    return 0


def generation_prompts(sample: StorySample) -> list[str]:
    return sample.prompts


def build_story_params(
    args: argparse.Namespace, rng: random.Random
) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        for item in _asp_valid():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTING_REGISTRY:
            params = StoryParams(
                setting=setting,
                hero="Luna",
                friend="Pip",
                guide="the bright boatman",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            try:
                params = build_story_params(args, rng)
            except StoryError as error:
                print(error)
                return
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
