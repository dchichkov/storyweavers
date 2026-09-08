#!/usr/bin/env python3
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
    meters: dict[str, float] = field(default_factory=lambda: {
        "distance": 0.0,
        "height": 0.0,
        "weight": 0.0,
        "clarity": 0.0,
    })
    memes: dict[str, float] = field(default_factory=lambda: {
        "worry": 0.0,
        "courage": 0.0,
        "trust": 0.0,
        "wonder": 0.0,
        "relief": 0.0,
    })


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    mystery: str
    object_name: str
    place: str
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
        "mystery": "why the town bell rang five times before sunrise",
        "object": "the fifth bell rope",
        "clue": "five round hoofprints circled the bell tower, but only four pointed toward the door",
        "false_lead": "A loud windmill had pushed the bell by mistake, everyone guessed.",
        "method": "Luna stretched a ladder made from three fence rails while Pip listened from the roof.",
        "truth": "A plump cloud-goat had caught the rope on its horn while nibbling the tower ivy.",
        "resolution": "They freed the rope, and the bell gave one gentle ring to welcome the morning.",
        "image": "the bell shone above the village with a fifth golden stripe of sunlight",
        "lesson": "a mystery grows smaller when you count every clue",
    },
    {
        "mystery": "where the mayor's enormous blue hat vanished during the parade",
        "object": "the fifth hat feather",
        "clue": "four blue feathers lay in the square, while a fifth was stuck high in a pear tree",
        "false_lead": "The parade elephant must have worn the hat as a bowl, people declared.",
        "method": "Luna climbed the pear tree and Pip followed a trail of blue dust beneath the branches.",
        "truth": "A friendly breeze had carried the hat into the tree, where a nest of sparrows used it as a roof.",
        "resolution": "The sparrows kept a soft corner of the hat, and the mayor wore the rest with pride.",
        "image": "the mayor marched beneath a blue hat that bobbed like a tiny sky",
        "lesson": "the smallest missing piece can point to the largest answer",
    },
    {
        "mystery": "why five enormous pancakes appeared on the school roof",
        "object": "the fifth pancake",
        "clue": "four pancakes smelled of cinnamon, but the fifth smelled like the baker's lemon soap",
        "false_lead": "The moon had baked breakfast and tossed it down, the children said.",
        "method": "Luna lowered a soup-pot basket from the clock tower while Moss measured the sticky trail.",
        "truth": "The baker's runaway pancake flipper had launched the stack through an open attic window.",
        "resolution": "The fifth pancake returned to the bakery, and the others became a roof-top picnic.",
        "image": "the school roof held a breakfast table wide enough for every child",
        "lesson": "a careful comparison can beat a wonderfully wild guess",
    },
    {
        "mystery": "who painted a silver mustache on the statue of the town founder",
        "object": "the fifth paintbrush",
        "clue": "four brushes were dry, but the fifth still glittered beside a trail of moon-colored pawprints",
        "false_lead": "The statue must have painted itself after hearing a funny joke.",
        "method": "Luna followed the pawprints under the bridge while Pip carried a lantern as tall as a tree.",
        "truth": "A shy raccoon had painted the mustache to make the lonely statue smile.",
        "resolution": "The town kept the mustache and added a small painted smile.",
        "image": "the founder's statue winked in the moonlight with its splendid silver mustache",
        "lesson": "understanding a strange act can reveal a kind reason",
    },
    {
        "mystery": "why the river carried five teacups toward the mountain",
        "object": "the fifth teacup",
        "clue": "four cups floated upright, but the fifth sailed against the current",
        "false_lead": "The river was practicing backward swimming for a giant race.",
        "method": "Luna built a bridge of picnic boards while Pip watched the cup's reflection.",
        "truth": "The fifth cup held a tiny whirlpool made by a pebble lodged beneath its handle.",
        "resolution": "They removed the pebble, and all five cups drifted safely to the tea picnic.",
        "image": "five teacups rested on a blanket while the river sparkled beside them",
        "lesson": "looking underneath can explain what seems to move the wrong way",
    },
]


OPENINGS = [
    "In the tallest town for miles around",
    "One morning beneath a sky so wide it needed two horizons",
    "At the foot of a mountain that wore a snow hat",
    "When the village rooster crowed loud enough to wake the clouds",
    "On a day when the shadows stretched farther than the road",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Tall Tale mystery about fifth clues and a very large answer."
    )
    parser.add_argument("--name")
    parser.add_argument("--type")
    parser.add_argument("--helper")
    parser.add_argument("--helper-type")
    parser.add_argument("--mystery")
    parser.add_argument("--object")
    parser.add_argument("--place")
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
    scenario = SCENARIOS[rng.randrange(len(SCENARIOS))]
    return StoryParams(
        hero_name=args.name or rng.choice(["Luna", "Mabel", "Juniper", "Toby", "Nell"]),
        hero_type=args.type or rng.choice(["girl", "boy", "rabbit", "fox", "bear"]),
        helper_name=args.helper or rng.choice(["Pip", "Moss", "Ada", "Bo", "Clover"]),
        helper_type=args.helper_type or rng.choice(["mouse", "goat", "crow", "dog", "squirrel"]),
        mystery=args.mystery or scenario["mystery"],
        object_name=args.object or scenario["object"],
        place=args.place or rng.choice([
            "the bell tower square",
            "the crooked parade road",
            "the school roof",
            "the founder's hill",
            "the mountain tea meadow",
        ]),
        scenario_index=SCENARIOS.index(scenario),
        detail_variant=rng.randrange(10000),
    )


def tell(params: StoryParams) -> World:
    scenario = SCENARIOS[params.scenario_index % len(SCENARIOS)]
    w = World(Setting(params.place))
    hero = w.add(Entity("hero", "person", params.hero_type, params.hero_name))
    helper = w.add(Entity("helper", "person", params.helper_type, params.helper_name))
    object_entity = w.add(Entity("fifth_object", "thing", "mystery_object", params.object_name))
    w.facts.update(hero=hero, helper=helper, object=object_entity, scenario=scenario)

    hero.memes["wonder"] = 1.0
    helper.memes["trust"] = 1.0
    hero.meters["height"] = 2.0
    helper.meters["height"] = 1.0
    object_entity.meters["clarity"] = 0.2

    opening = OPENINGS[params.detail_variant % len(OPENINGS)]
    w.say(
        f"{opening}, {hero.label} the {hero.type} lived in a place where ordinary things grew unusually large."
    )
    w.say(
        f"That morning, {hero.label} discovered a mystery: {params.mystery}. "
        f"It involved {params.object_name}, the fifth piece everyone had forgotten to count."
    )
    w.para()

    hero.memes["worry"] += 1.0
    w.say(
        f"{hero.label} hurried to {params.place}, where {scenario['false_lead']} "
        f"The guess was enormous, but it did not explain the fifth clue."
    )
    w.say(
        f'"We need a better answer than the biggest guess," {hero.label} said. '
        f'"Then we should follow the clue that does not fit," {helper.label} replied.'
    )
    w.para()

    helper.meters["distance"] = 3.0
    object_entity.meters["distance"] = 5.0
    hero.memes["courage"] += 1.0
    w.say(
        f"They counted four ordinary signs and found one extra trail. {scenario['clue']} "
        f"The fifth clue pointed away from the crowd and toward a hidden place."
    )
    w.say(f"{scenario['method']} The strange trail became clearer with every careful step.")
    w.para()

    object_entity.meters["clarity"] = 1.0
    object_entity.meters["weight"] = 5.0
    hero.memes["wonder"] += 1.0
    helper.memes["trust"] += 1.0
    w.say(f"At last, {scenario['truth']}")
    w.say(
        f'"Mystery solved!" {helper.label} cried. "{scenario["lesson"].capitalize()}." '
        f'{hero.label} nodded, because the fifth clue had changed what they believed.'
    )
    w.para()

    object_entity.memes["relief"] = 1.0
    hero.memes["relief"] = 1.0
    w.say(scenario["resolution"])
    w.say(
        f"The villagers cheered, not because the answer was the biggest, but because it was true. "
        f"{scenario['image']}."
    )
    w.log(f"mystery={params.mystery}")
    w.log("counted_four_then_followed_fifth=True")
    w.log("mystery_solved=True")
    return w


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        f"Write a Tall Tale about {hero.label} solving the mystery of {scenario['mystery']}.",
        f"Include {helper.label}, a fifth clue, a false giant guess, and a funny but sensible answer.",
        f"Tell a child-facing mystery story where counting to five changes what {hero.label} decides to do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What mystery did {hero.label} try to solve?",
            answer=f"{hero.label} tried to solve why {scenario['mystery']}. The mystery centered on the fifth clue and the missing explanation.",
        ),
        QAItem(
            question="Why was the first explanation not enough?",
            answer=f"The first explanation was not enough because {scenario['false_lead'].rstrip('.')} It did not account for the extra fifth clue.",
        ),
        QAItem(
            question=f"How did {hero.label} and {helper.label} find the answer?",
            answer=f"They counted the ordinary signs, followed the clue that did not fit, and used careful observation instead of trusting the biggest guess. {scenario['method']}",
        ),
        QAItem(
            question="What was the true answer to the mystery?",
            answer=f"The true answer was that {scenario['truth'].rstrip('.').lower()}.",
        ),
        QAItem(
            question="What lesson did the fifth clue teach?",
            answer=f"It taught them that {scenario['lesson']}. The fifth clue changed their decision because it gave them evidence instead of a wild guess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a puzzling question that can be answered by noticing clues, testing ideas, and checking what is true.",
        ),
        QAItem(
            question="Why can counting clues help?",
            answer="Counting clues helps because an extra detail may show that a simple explanation is incomplete or wrong.",
        ),
        QAItem(
            question="What makes a Tall Tale different from an ordinary story?",
            answer="A Tall Tale uses playful exaggeration, enormous events, and surprising images while still giving the characters a clear problem and a satisfying answer.",
        ),
        QAItem(
            question="What does fifth mean?",
            answer="Fifth means coming after fourth in a counted order. In this story, the fifth clue is important because it does not match the first guess.",
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
        parts = [f"type={entity.type}"]
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + ", ".join(parts))
    lines.extend(world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
entity(hero).
entity(helper).
entity(fifth_object).

counted_four :- clue_count(4).
followed_fifth :- extra_clue(fifth_object).
mystery_solved :- counted_four, followed_fifth, truth_found.
happy_end :- mystery_solved, safe_resolution.

#show counted_four/0.
#show followed_fifth/0.
#show mystery_solved/0.
#show happy_end/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("clue_count", 4),
        asp.fact("extra_clue", "fifth_object"),
        asp.fact("truth_found"),
        asp.fact("safe_resolution"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    expected = {
        "counted_four/0",
        "followed_fifth/0",
        "mystery_solved/0",
        "happy_end/0",
    }
    if found == expected:
        for scenario_index in range(len(SCENARIOS)):
            params = StoryParams(
                hero_name="Luna",
                hero_type="girl",
                helper_name="Pip",
                helper_type="mouse",
                mystery=SCENARIOS[scenario_index]["mystery"],
                object_name=SCENARIOS[scenario_index]["object"],
                place="the tall square",
                scenario_index=scenario_index,
            )
            sample = generate(params)
            if "fifth" not in sample.story.lower() or "mystery" not in sample.story.lower():
                print("MISMATCH: generated story lost required narrative elements")
                return 1
        print("OK: ASP parity and generated-story checks passed.")
        return 0
    print(f"MISMATCH: {sorted(found)} != {sorted(expected)}")
    return 1


def generate(params: StoryParams) -> StorySample:
    if not params.hero_name.strip():
        raise StoryError("hero name must not be empty")
    if not params.helper_name.strip():
        raise StoryError("helper name must not be empty")
    if not params.mystery.strip():
        raise StoryError("mystery must not be empty")
    if "fifth" not in params.object_name.lower() and params.object_name not in {
        scenario["object"] for scenario in SCENARIOS
    }:
        raise StoryError("the mystery object must connect to the fifth clue")
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        hero_name="Luna",
        hero_type="girl",
        helper_name="Pip",
        helper_type="mouse",
        mystery=SCENARIOS[0]["mystery"],
        object_name=SCENARIOS[0]["object"],
        place="the bell tower square",
        scenario_index=0,
    ),
    StoryParams(
        hero_name="Mabel",
        hero_type="bear",
        helper_name="Clover",
        helper_type="squirrel",
        mystery=SCENARIOS[1]["mystery"],
        object_name=SCENARIOS[1]["object"],
        place="the crooked parade road",
        scenario_index=1,
    ),
    StoryParams(
        hero_name="Juniper",
        hero_type="rabbit",
        helper_name="Moss",
        helper_type="goat",
        mystery=SCENARIOS[2]["mystery"],
        object_name=SCENARIOS[2]["object"],
        place="the school roof",
        scenario_index=2,
    ),
]


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
