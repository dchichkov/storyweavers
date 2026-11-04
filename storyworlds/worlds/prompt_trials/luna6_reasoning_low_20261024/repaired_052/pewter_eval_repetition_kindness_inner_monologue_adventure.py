#!/usr/bin/env python3
"""A small Adventure storyworld about a pewter compass, repeated clues, and kindness."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


@dataclass
class StoryParams:
    adventurer: str
    companion: str
    place: str
    scenario: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    obstacle: str
    clue: str
    danger: str
    kind_action: str
    solution: str
    ending: str


ADVENTURERS = ["Mara", "Tavi", "Nell", "Rafi", "Jo"]
COMPANIONS = ["Pip", "Bea", "Lio", "Kit", "Sol"]
PLACES = [
    "the Fernhill pass",
    "the windy pebble ridge",
    "the old pine trail",
    "the blue creek valley",
]
SCENARIOS = [
    Scenario(
        "fallen_bridge",
        "a narrow footbridge had slipped sideways over the creek",
        "the pewter compass needle trembled twice, paused, then trembled twice again",
        "the rushing water below hid the stepping stones",
        "held Pip's pack while Pip climbed onto a dry rock to look",
        "they followed the repeated compass tremble to a line of broad stones and crossed one at a time",
        "their muddy boots rested beside the compass, while the creek shone safely below",
    ),
    Scenario(
        "lost_goat",
        "a small white goat was stranded on a ledge above the trail",
        "the compass gave two soft taps whenever the goat bleated twice",
        "loose gravel slid from the ledge with each frightened step",
        "offered the goat a handful of clover and waited without rushing it",
        "they used the compass taps to find a gentle path around the ledge, then guided the goat down",
        "the goat nibbled clover beside their packs as the trail opened toward home",
    ),
    Scenario(
        "blocked_spring",
        "a tumble of branches had covered the spring that fed the trail's water trough",
        "three drops still fell in the same slow rhythm beneath the branches",
        "the thirsty trail animals had begun gathering in the hot afternoon",
        "asked the others to bring cups of water while she cleared only the light branches",
        "they followed the steady drip to the spring's opening and moved the branches together",
        "clear water rippled into the trough as the animals drank in the shade",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Adventure storyworld about a pewter compass and kind choices."
    )
    parser.add_argument("--adventurer", choices=ADVENTURERS)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--scenario", choices=[s.key for s in SCENARIOS])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    adventurer = args.adventurer or rng.choice(ADVENTURERS)
    eligible = [name for name in COMPANIONS if name != adventurer]
    companion = args.companion or rng.choice(eligible)
    if companion == adventurer:
        raise StoryError("The adventurer and companion must be different people.")
    return StoryParams(
        adventurer=adventurer,
        companion=companion,
        place=args.place or rng.choice(PLACES),
        scenario=args.scenario or rng.choice(SCENARIOS).key,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.adventurer not in ADVENTURERS:
        raise StoryError(f"Unknown adventurer: {params.adventurer!r}.")
    if params.companion not in COMPANIONS:
        raise StoryError(f"Unknown companion: {params.companion!r}.")
    if params.adventurer == params.companion:
        raise StoryError("The adventurer and companion must be different people.")
    if params.place not in PLACES:
        raise StoryError(f"Unknown trail setting: {params.place!r}.")
    if params.scenario not in {scenario.key for scenario in SCENARIOS}:
        raise StoryError(f"Unknown adventure scenario: {params.scenario!r}.")


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("domain", "adventure"),
        asp.fact("seed_word", "pewter"),
        asp.fact("seed_word", "eval"),
        asp.fact("feature", "repetition"),
        asp.fact("feature", "kindness"),
        asp.fact("feature", "inner_monologue"),
        *(asp.fact("scenario", scenario.key) for scenario in SCENARIOS),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
required(repetition).
required(kindness).
required(inner_monologue).
feature_ok(F) :- required(F), feature(F).
ready :- scenario(S), scenario_known(S), feature_ok(repetition),
         feature_ok(kindness), feature_ok(inner_monologue).
scenario_known(S) :- scenario(S).
#show feature_ok/1.
#show ready/0.
"""


def asp_program(show: str = "#show feature_ok/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    rng = random.Random(params.seed)
    scenario = next(item for item in SCENARIOS if item.key == params.scenario)
    world = World()
    adventurer = world.add(
        Entity(
            params.adventurer,
            "adventurer",
            params.adventurer,
            params.place,
            meters={"care": 0.3, "confidence": 0.5},
            memes={"curiosity": 0.8},
        )
    )
    companion = world.add(
        Entity(
            params.companion,
            "companion",
            params.companion,
            params.place,
            meters={"trust": 0.5},
            memes={"kindness": 0.6},
        )
    )
    compass = world.add(
        Entity(
            "compass",
            "tool",
            "small pewter compass",
            "in " + params.adventurer + "'s hand",
            meters={"needle_steadiness": 0.2},
            memes={"mystery": 0.8},
        )
    )

    story_parts = [
        f"{params.adventurer} and {params.companion} followed the trail through {params.place}.",
        f"In {params.adventurer}'s hand, a small pewter compass gave a faint, repeated tremble.",
        f"Then they found {scenario.obstacle}.",
        f'"Should we hurry past it?" {params.companion} asked. "No," {params.adventurer} replied. "Let us watch and listen first."',
        f"{params.adventurer} thought, The compass is telling us something, but I need to notice the pattern.",
        f"They waited quietly. Soon they saw that {scenario.clue}.",
        f'"I am a little scared," {params.companion} said. "{params.adventurer}, could you stay close?"',
        f'"Of course," said {params.adventurer}. {scenario.kind_action}.",
        f"That small kindness gave them time to think. The compass needle steadied, and they learned how to face the trouble: {scenario.solution}.",
        f"Together they finished the crossing safely.",
        f"As they continued, {scenario.ending}.",
    ]
    story = " ".join(story_parts)

    adventurer.meters.update(care=1.0, confidence=0.9)
    companion.meters["trust"] = 1.0
    companion.memes["feeling_safe"] = 1.0
    compass.meters["needle_steadiness"] = 1.0
    compass.memes["understood"] = 1.0
    compass.location = "safely tucked in " + params.adventurer + "'s pack"
    world.facts.update(
        scenario=scenario.key,
        obstacle=scenario.obstacle,
        clue=scenario.clue,
        solution=scenario.solution,
        kindness=scenario.kind_action,
        resolution="safe crossing",
        repeated_signal=True,
        inner_monologue=True,
    )

    prompts = [
        f"Write an Adventure about {params.adventurer} and {params.companion} in {params.place}.",
        "Include a pewter compass, a repeated clue, a kind choice, and an inner thought.",
        f"Let the friends solve this problem together: {scenario.obstacle}.",
    ]
    story_qa = [
        QAItem(
            question="What trouble did the friends find?",
            answer=f"They found that {scenario.obstacle}. It made the trail difficult to travel.",
        ),
        QAItem(
            question="What repeated clue helped them?",
            answer=f"They noticed that {scenario.clue}. Waiting and watching helped them understand the compass.",
        ),
        QAItem(
            question=f"How did {params.adventurer} show kindness?",
            answer=f"{params.adventurer} stayed close and {scenario.kind_action}. That gave the friends time to solve the problem together.",
        ),
        QAItem(
            question="How did the friends solve the trouble?",
            answer=f"They worked together: {scenario.solution}. They were able to continue safely afterward.",
        ),
        QAItem(
            question="What was the pewter compass for?",
            answer="The pewter compass gave the friends a repeated signal that helped them notice a safe way forward.",
        ),
    ]
    world_qa = [
        QAItem(
            question="Why can repetition help an adventurer?",
            answer="A repeated sound or movement can reveal a pattern, especially when an adventurer pauses to observe it.",
        ),
        QAItem(
            question="What does kindness do for companions?",
            answer="Kindness can help companions feel safe enough to share what they know and work together.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thought, which can help readers understand what the character is considering.",
        ),
    ]
    world.facts["eval_note"] = "The repeated clue was evaluated by careful observation."
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            print(
                f"  {entity.id}: {entity.type} location={entity.location} "
                f"meters={entity.meters} memes={entity.memes}"
            )
        print(f"  facts={sample.world.facts}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    expected = [("inner_monologue",), ("kindness",), ("repetition",)]
    actual = sorted(set(asp.atoms(model, "feature_ok")))
    if actual != expected or not asp.atoms(model, "ready"):
        print("MISMATCH: the ASP model does not include every required story feature.")
        print(actual)
        return 1
    print("OK: ASP features match the Python storyworld gate.")
    return 0


def verify() -> int:
    try:
        reasonableness_gate(
            StoryParams("Mara", "Pip", PLACES[0], SCENARIOS[0].key)
        )
        for scenario in SCENARIOS:
            sample = generate(StoryParams("Mara", "Pip", PLACES[0], scenario.key, 17))
            if not all(word in sample.story for word in ("pewter", "thought", "said")):
                raise AssertionError(f"Required narrative elements missing for {scenario.key}.")
            if len(sample.story_qa) < 3 or sample.world is None:
                raise AssertionError("Generated sample is missing story-grounded results.")
        try:
            reasonableness_gate(StoryParams("Mara", "Mara", PLACES[0], SCENARIOS[0].key))
        except StoryError:
            pass
        else:
            raise AssertionError("The reasonableness gate accepted duplicate characters.")
    except (AssertionError, StoryError) as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1
    print("OK: Python gate and generated stories passed.")
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1 and not args.all and not args.verify and not args.show_asp:
        raise SystemExit("-n must be at least 1.")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        import asp

        print("\n".join(str(atom) for atom in asp.one_model(asp_program())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Mara", "Pip", PLACES[0], scenario.key, base_seed + i)
            for i, scenario in enumerate(SCENARIOS)
        ]
    else:
        params_list = []
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            params_list.append(params)

    samples = [generate(params) for params in params_list]
    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    for index, sample in enumerate(samples):
        if args.all or len(samples) > 1:
            params = sample.params
            emit(
                sample,
                trace=args.trace,
                qa=args.qa,
                header=f"### {params.adventurer} and {params.companion} — {params.scenario}",
            )
        else:
            emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
