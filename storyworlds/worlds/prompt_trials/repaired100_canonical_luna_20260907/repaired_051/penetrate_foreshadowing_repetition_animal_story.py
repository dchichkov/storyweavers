#!/usr/bin/env python3
"""
A small Animal Story storyworld about a careful animal team learning how to
penetrate a hidden garden wall. Foreshadowing and repetition carry clues from
the beginning to the final safe opening.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "distance": 0.0,
            "strength": 0.0,
            "opening": 0.0,
            "safety": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "courage": 0.0,
            "trust": 0.0,
            "joy": 0.0,
            "relief": 0.0,
        }
    )

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "mouse", "squirrel", "hen", "otter"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"fox", "badger", "bear", "beaver", "hedgehog"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the mossy hill garden"


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    keeper_name: str
    scenario_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace_log: list[str] = field(default_factory=list)

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

    def log(self, text: str) -> None:
        self.trace_log.append(text)


SCENARIOS = [
    {
        "object": "a basket of moon pears",
        "obstacle": "A thick stone wall sealed the garden, and only a tiny gap showed beneath its oldest brick.",
        "foreshadow": "Three pale feathers rested beside the wall, pointing toward the low place.",
        "mistake": "The friends pushed a broad branch at the wall, but it struck the stone and rolled away.",
        "clue": "The same three pale feathers trembled whenever the breeze passed through the hidden gap.",
        "method": "They used a smooth reed to penetrate the loose earth below the brick, widening the little passage without cracking the wall.",
        "result": "The passage opened just wide enough for the basket to slide through.",
        "lesson": "small clues can reveal a safer way through a big problem",
        "image": "moon pears shone in a basket on the far side of the wall",
        "repeat": "Look low, listen twice, and move gently",
    },
    {
        "object": "the gardener's blue ribbon",
        "obstacle": "A thorny hedge surrounded the garden gate, while a narrow dark tunnel disappeared beneath the roots.",
        "foreshadow": "A blue thread clung to a nearby blackberry stem and pointed toward the tunnel.",
        "mistake": "The friends tried to pull the hedge apart, and the thorns caught the helper's scarf.",
        "clue": "The blue thread fluttered three times whenever the tunnel breathed cool air.",
        "method": "They wrapped the scarf safely away, then used a willow spoon to penetrate the soft soil and clear the tunnel.",
        "result": "The ribbon slipped through the tunnel and returned to the gardener without a single torn edge.",
        "lesson": "a careful path is better than forcing a stubborn barrier",
        "image": "the blue ribbon waved from the garden post like a tiny flag",
        "repeat": "Notice the thread, mind the thorns, and try the quiet way",
    },
    {
        "object": "a jar of golden seed",
        "obstacle": "The old greenhouse door was stuck, but warm light leaked through a pinhole near the ground.",
        "foreshadow": "A sunflower petal lay beside that pinhole, bright as a little arrow.",
        "mistake": "The friends leaned against the whole door, making the glass panes rattle.",
        "clue": "The sunflower petal lifted each time air slipped through the pinhole.",
        "method": "They used a narrow twig to penetrate the soft clay around the lower latch, then lifted it with a loop of vine.",
        "result": "The door opened quietly, and the seed jar stayed safe in the helper's paws.",
        "lesson": "a small opening can show where a large problem will yield",
        "image": "golden seeds filled the greenhouse trays beneath a roof of clear light",
        "repeat": "Follow the light, touch the latch, and keep the glass still",
    },
    {
        "object": "a lost copper bell",
        "obstacle": "A fallen log blocked the forest path, though a dark hollow ran through its center.",
        "foreshadow": "A copper-colored leaf lay at the hollow's mouth.",
        "mistake": "The friends pushed the log from the side, but it only sank deeper into the mud.",
        "clue": "The leaf spun whenever a faint bell note traveled through the hollow.",
        "method": "They let the smallest mouse penetrate the hollow with a ribbon, then drew the bell toward the opening.",
        "result": "The bell came free without rolling into the stream.",
        "lesson": "the smallest helper may fit the most important place",
        "image": "the copper bell rang from a pine branch above the cleared path",
        "repeat": "Hear the note, trust the hollow, and pull slowly",
    },
]


OPENINGS = [
    "At sunrise",
    "Before the first birds finished singing",
    "On a cool morning",
    "When the hill was still silver with dew",
    "Just after the garden keeper rang the breakfast bell",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animal Story: a careful team learns to penetrate a hidden barrier."
    )
    parser.add_argument("--name")
    parser.add_argument("--type")
    parser.add_argument("--helper")
    parser.add_argument("--helper-type")
    parser.add_argument("--keeper")
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
        hero_name=args.name or rng.choice(["Luna", "Pip", "Nell", "Tavi", "Mira"]),
        hero_type=args.type or rng.choice(["rabbit", "fox", "squirrel", "otter", "badger"]),
        helper_name=args.helper or rng.choice(["Pogo", "Bramble", "Niko", "Fenn", "Clover"]),
        helper_type=args.helper_type or rng.choice(["mouse", "beaver", "hedgehog", "duck", "bear"]),
        keeper_name=args.keeper or rng.choice(["Aunt Fern", "Old Rowan", "Keeper Moss"]),
        scenario_index=rng.randrange(len(SCENARIOS)),
        detail_variant=rng.randrange(10000),
    )


def tell(params: StoryParams) -> World:
    scenario = SCENARIOS[params.scenario_index % len(SCENARIOS)]
    world = World(Setting())

    hero = world.add(Entity("hero", "animal", params.hero_type, params.hero_name))
    helper = world.add(Entity("helper", "animal", params.helper_type, params.helper_name))
    keeper = world.add(Entity("keeper", "animal", "turtle", params.keeper_name))
    barrier = world.add(Entity("barrier", "thing", "barrier", "the barrier"))
    prize = world.add(Entity("prize", "thing", "object", scenario["object"]))

    world.facts.update(
        hero=hero,
        helper=helper,
        keeper=keeper,
        barrier=barrier,
        prize=prize,
        scenario=scenario,
    )

    hero.memes["trust"] += 1
    helper.memes["courage"] += 1

    opening = OPENINGS[params.detail_variant % len(OPENINGS)]
    world.say(
        f"{opening}, {hero.label} the {hero.type} and {helper.label} the {helper.type} hurried to {world.setting.place}."
    )
    world.say(
        f'{keeper.label} called, "Please bring me {scenario["object"]}; the garden needs it before noon."'
    )
    world.say(
        f"To reach it, the friends had to penetrate the barrier around the garden, but the way in was hidden."
    )
    world.para()

    hero.memes["worry"] += 1
    barrier.meters["strength"] = 1.0
    world.say(scenario["obstacle"])
    world.say(
        f"Near the barrier, {scenario['foreshadow']} {hero.label} remembered it because the same little sign appeared twice."
    )
    world.say(
        f'"Look low," {hero.label} said. "{scenario["repeat"]}."'
    )
    world.para()

    world.say(scenario["mistake"])
    helper.memes["worry"] += 1
    world.say(
        f'"That was too rough," {helper.label} said. "The wall did not move, and the garden should not be hurt."'
    )
    world.say(scenario["clue"])
    world.say(
        f'"The first sign warned us," {hero.label} replied. "{scenario["clue"]}"'
    )
    world.para()

    hero.memes["courage"] += 1
    helper.memes["trust"] += 1
    barrier.meters["opening"] = 1.0
    barrier.meters["safety"] = 1.0
    world.say(scenario["method"])
    world.say(
        f"{helper.label} held the light while {hero.label} worked slowly. They repeated, "
        f'"{scenario["repeat"]}."'
    )
    world.para()

    prize.meters["distance"] = 1.0
    prize.meters["safety"] = 1.0
    keeper.memes["relief"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(scenario["result"])
    world.say(
        f'{keeper.label} smiled. "You found the safe way through," the keeper said. "Now the garden can have what it needs."'
    )
    world.say(scenario["image"] + ".")
    world.say(
        f"{hero.label} understood that {scenario['lesson']}. The repeated clues had prepared them to choose patience instead of force."
    )
    world.log(f"scenario={params.scenario_index % len(SCENARIOS)}")
    world.log("barrier_penetrated=True")
    world.log("foreshadowing_repeated=True")
    world.log("safe_resolution=True")
    return world


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        f"Write an Animal Story about {hero.label} and {helper.label} trying to penetrate a barrier safely.",
        f"Include foreshadowing clues that repeat before {scenario['object']} is recovered.",
        f"Show the animals learning that {scenario['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario = world.facts["scenario"]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    keeper: Entity = world.facts["keeper"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What did {keeper.label} ask {hero.label} and {helper.label} to bring?",
            f"{keeper.label} asked them to bring {scenario['object']} to the garden before noon.",
        ),
        QAItem(
            "What barrier blocked the animals?",
            f"{scenario['obstacle']} They needed to find a safe way through it.",
        ),
        QAItem(
            "What clue was foreshadowed and repeated?",
            f"{scenario['foreshadow']} Later, {scenario['clue']}",
        ),
        QAItem(
            "How did the animals penetrate the barrier?",
            f"{scenario['method']} Their careful method opened a safe passage.",
        ),
        QAItem(
            "What did the animals learn?",
            f"They learned that {scenario['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does penetrate mean?",
            "To penetrate means to pass into or through something, often by using a small opening or careful force.",
        ),
        QAItem(
            "What is foreshadowing?",
            "Foreshadowing is an early hint that prepares us for something important that happens later.",
        ),
        QAItem(
            "What is repetition?",
            "Repetition means using a word, action, or image again so an idea becomes easier to notice and remember.",
        ),
        QAItem(
            "Why should animals use a safe method near a garden?",
            "A safe method protects the plants, the animals, and the useful object they are trying to carry.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        details = [f"type={entity.type}"]
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + ", ".join(details))
    lines.extend(world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
entity(hero).
entity(helper).
entity(barrier).
entity(prize).
hint_repeated.
careful_method.
penetrated(barrier) :- hint_repeated, careful_method.
delivered(prize) :- penetrated(barrier).
happy_end :- delivered(prize).
#show penetrated/1.
#show delivered/1.
#show happy_end/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hint_repeated"),
            asp.fact("careful_method"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show penetrated/1. #show delivered/1. #show happy_end/0."
        )
    )
    atoms = {str(symbol) for symbol in model}
    expected = {"penetrated(barrier)", "delivered(prize)", "happy_end"}
    if expected.issubset(atoms):
        print("OK: ASP parity check passed.")
        return 0
    print(f"MISMATCH: expected {sorted(expected)}, got {sorted(atoms)}")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    if "penetrate" not in sample.story.lower():
        raise StoryError("Generated story must include the word penetrate.")
    if len(sample.story_qa) < 3:
        raise StoryError("Generated story must include grounded questions and answers.")
    return sample


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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        hero_name="Luna",
        hero_type="rabbit",
        helper_name="Pogo",
        helper_type="mouse",
        keeper_name="Aunt Fern",
        scenario_index=0,
    ),
    StoryParams(
        hero_name="Mira",
        hero_type="otter",
        helper_name="Bramble",
        helper_type="beaver",
        keeper_name="Old Rowan",
        scenario_index=1,
    ),
    StoryParams(
        hero_name="Pip",
        hero_type="fox",
        helper_name="Clover",
        helper_type="hedgehog",
        keeper_name="Keeper Moss",
        scenario_index=2,
    ),
    StoryParams(
        hero_name="Nell",
        hero_type="squirrel",
        helper_name="Fenn",
        helper_type="duck",
        keeper_name="Aunt Fern",
        scenario_index=3,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show penetrated/1. #show delivered/1. #show happy_end/0."))
        return

    if args.verify:
        status = asp_verify()
        if status:
            sys.exit(status)
        for params in CURATED:
            generate(params)
        print("OK: generated story checks passed.")
        return

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show penetrated/1. #show delivered/1. #show happy_end/0."
            )
        )
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(20, args.n * 20):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            attempt += 1
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
