#!/usr/bin/env python3
"""
A small Adventure storyworld about Nia, Eval, and a pewter bell whose
repeated notes help them find and rescue a lost hiker in the mountains.
"""

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
    kind: str
    type: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scenario:
    key: str
    obstacle: str
    traveler: str
    clue: str
    rescue: str
    outcome: str
    ending_image: str


@dataclass
class StoryParams:
    hero: str
    place: str
    scenario: str
    telling_mode: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)


HEROES = ["Nia", "Mira", "Tavi", "Sol", "Lena", "Ari"]
PLACES = [
    "the Bluecap Mountains",
    "the Whispering Pass",
    "the Cloudberry Ridge",
    "the Pineglass Range",
]
TELLING_MODES = ["arrival", "warning", "dialogue", "promise"]

SCENARIOS = [
    Scenario(
        key="misty_pine",
        obstacle="A bank of fog swallowed the trail, and a child named Rowan called from somewhere below the ridge.",
        traveler="Rowan",
        clue="Rowan's whistle echoed clearly only when Nia stood beside a bent pine",
        rescue="Eval tied their climbing rope around the sturdy pine, and Nia helped Rowan up the broad, safe slope",
        outcome="Rowan reached the trail safely, and the three of them carried the bell onward together",
        ending_image="At the lookout, the pewter bell shone beside three steaming cups as Rowan waved into the clearing sky",
    ),
    Scenario(
        key="broken_step",
        obstacle="A crack split the mountain path, and a child named Kit stood on a ledge on the other side.",
        traveler="Kit",
        clue="Kit's lantern flashed from a safe ledge whenever the bell's note reached the far wall",
        rescue="Eval secured the rope around a stone anchor, and Nia guided Kit across one careful step at a time",
        outcome="Kit crossed safely, and the three of them carried the bell onward together",
        ending_image="At the lookout, Kit hung the lantern beside the pewter bell, and both lights warmed the darkening ridge",
    ),
    Scenario(
        key="snow_drift",
        obstacle="A soft snowdrift covered the trail, and a child named Bo called faintly from behind it.",
        traveler="Bo",
        clue="Bo's answer grew louder whenever Nia rang the bell from the drift's sheltered side",
        rescue="Eval held the rope steady while Nia carefully cleared a small opening and helped Bo climb out",
        outcome="Bo stood safely on the trail, and the three of them carried the bell onward together",
        ending_image="At the lookout, Bo's red mitten dried beside the pewter bell while snowflakes glittered outside",
    ),
]

SCENARIO_BY_KEY = {scenario.key: scenario for scenario in SCENARIOS}


def reasonableness_gate(params: StoryParams) -> None:
    """Reject options that cannot be rendered as a coherent story."""
    if params.hero not in HEROES:
        raise StoryError(f"Unknown hero {params.hero!r}; choose one of: {', '.join(HEROES)}.")
    if params.place not in PLACES:
        raise StoryError(f"Unknown place {params.place!r}; choose one of: {', '.join(PLACES)}.")
    if params.scenario not in SCENARIO_BY_KEY:
        options = ", ".join(SCENARIO_BY_KEY)
        raise StoryError(f"Unknown scenario {params.scenario!r}; choose one of: {options}.")
    if params.telling_mode not in TELLING_MODES:
        raise StoryError(
            f"Unknown telling mode {params.telling_mode!r}; "
            f"choose one of: {', '.join(TELLING_MODES)}."
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Adventure storyworld about a pewter bell, repeated signals, and a kind rescue."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--scenario", choices=list(SCENARIO_BY_KEY))
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
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
    params = StoryParams(
        hero=args.hero or rng.choice(HEROES),
        place=args.place or rng.choice(PLACES),
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
        seed=args.seed,
    )
    reasonableness_gate(params)
    return params


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("domain", "adventure"),
        asp.fact("seed_word", "pewter"),
        asp.fact("seed_word", "eval"),
        asp.fact("feature", "repetition"),
        asp.fact("feature", "kindness"),
        asp.fact("feature", "inner_monologue"),
    ]
    for scenario in SCENARIOS:
        lines.append(asp.fact("scenario", scenario.key))
    return "\n".join(lines)


ASP_RULES = r"""
required(repetition).
required(kindness).
required(inner_monologue).

has_feature(F) :- feature(F).
ready :- domain(adventure), seed_word(pewter), seed_word(eval),
         required(F) : has_feature(F).
valid_scenario(S) :- scenario(S), ready.

#show domain/1.
#show seed_word/1.
#show feature/1.
#show valid_scenario/1.
"""


def asp_program(show: Optional[str] = None) -> str:
    program = f"{asp_facts()}\n{ASP_RULES}"
    if show:
        program += f"\n{show}\n"
    return program


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    features = sorted(asp.atoms(model, "feature"))
    expected_features = [
        ("inner_monologue",),
        ("kindness",),
        ("repetition",),
    ]
    scenarios = sorted(asp.atoms(model, "valid_scenario"))
    expected_scenarios = sorted((key,) for key in SCENARIO_BY_KEY)
    seeds = sorted(asp.atoms(model, "seed_word"))

    if features != expected_features:
        print(f"MISMATCH: ASP features {features!r} != Python features {expected_features!r}")
        return 1
    if scenarios != expected_scenarios:
        print(f"MISMATCH: ASP scenarios {scenarios!r} != Python scenarios {expected_scenarios!r}")
        return 1
    if seeds != [("eval",), ("pewter",)]:
        print(f"MISMATCH: ASP seed words are {seeds!r}")
        return 1

    print("OK: ASP and Python agree on the features, seed words, and valid scenarios.")
    return 0


def _opening(params: StoryParams, rng: random.Random) -> list[str]:
    hero = params.hero
    mode = params.telling_mode
    if mode == "warning":
        return [
            f'"The fog is coming fast," Eval warned as {hero} reached {params.place}.',
            f"They were carrying a small pewter bell to the old lookout before the storm closed the mountain trail.",
        ]
    if mode == "dialogue":
        return [
            f'"Do you think the lookout is far?" {hero} asked. "Far enough for an adventure," Eval replied.',
            f"Together they climbed into {params.place}, carrying a pewter bell for the old lookout.",
        ]
    if mode == "promise":
        return [
            f"{hero} had promised to bring a pewter bell to the old lookout in {params.place}.",
            "Eval, a little trail-making automaton, walked beside them with a coil of climbing rope over one shoulder.",
        ]
    opening = [
        f"{hero} and Eval climbed into {params.place} beneath a wide, bright sky.",
        "Eval was a little trail-making automaton, and together they were carrying a pewter bell to the old lookout.",
    ]
    if rng.random() < 0.5:
        opening[0] = f"With Eval beside them, {hero} started up the mountain trail through {params.place}."
    return opening


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    rng = random.Random(params.seed)
    scenario = SCENARIO_BY_KEY[params.scenario]
    world = World()

    hero = world.add(
        Entity(
            id=params.hero,
            kind="character",
            type="young_adventurer",
            label=params.hero,
            location="mountain trail",
            meters={"courage": 0.65, "attention": 0.55},
            memes={"kindness": 0.45, "resolve": 0.6},
        )
    )
    guide = world.add(
        Entity(
            id="Eval",
            kind="character",
            type="trail_automaton",
            label="little trail-making automaton",
            location="beside the hero",
            meters={"rope_ready": 1.0, "signal_knowledge": 0.75},
            memes={"loyalty": 0.8, "patience": 0.7},
        )
    )
    bell = world.add(
        Entity(
            id="pewter_bell",
            kind="thing",
            type="bell",
            label="small pewter bell",
            location="carried on the trail",
            meters={"sound": 0.7, "safety": 0.8},
            memes={"signal": 0.35},
        )
    )
    traveler = world.add(
        Entity(
            id=scenario.traveler,
            kind="character",
            type="lost_hiker",
            label=f"child named {scenario.traveler}",
            location="off the trail",
            meters={"safety": 0.3, "heard_signal": 0.0},
            memes={"hope": 0.35},
        )
    )
    world.facts.update(
        scenario=scenario.key,
        place=params.place,
        task="carry the pewter bell to the old lookout",
        obstacle=scenario.obstacle,
        clue=scenario.clue,
        helping_method=scenario.rescue,
        repeated_signal_count=3,
        choice="stop to help the lost hiker",
        outcome=scenario.outcome,
        ending_image=scenario.ending_image,
    )

    for sentence in _opening(params, rng):
        world.say(sentence)
    world.say(scenario.obstacle)

    world.para()
    world.say(
        f"The storm clouds hurried over the ridge. {params.hero} looked toward the lookout, "
        f"then heard {scenario.traveler}'s frightened call."
    )
    world.say(
        f'"We could keep going," {params.hero} said. "But {scenario.traveler} needs help first."'
    )
    world.say(
        f'"I know a way to find them," Eval replied. "Listen for an answer, not just the wind."'
    )
    world.say(
        f"{params.hero} thought, “If I hurry on alone, I may deliver the bell, but someone will "
        "be left scared in the storm.” The thought changed their choice: they stopped to help."
    )

    world.para()
    world.say(f"Instead of rushing ahead, they watched and listened. They noticed that {scenario.clue}.")
    world.say(
        f'"Let us send one gentle signal at a time," {params.hero} said. Eval nodded and held the rope ready.'
    )
    world.say(
        f"{params.hero} rang the pewter bell once. They waited. Then came a faint answer."
    )
    world.say("They rang it twice. A clearer answer came back through the mountain air.")
    world.say(
        "On the third ring, they heard exactly where the call was coming from, and Eval pointed out the safe route."
    )

    world.para()
    world.say(f"Eval and {params.hero} worked together: {scenario.rescue}.")
    world.say(f'"I thought nobody would hear me," {scenario.traveler} said. "We heard you," {params.hero} replied.')
    world.say(f"{scenario.outcome}.")
    world.say(
        f"With everyone safe, they reached the lookout before the rain began. "
        f"{scenario.ending_image}."
    )

    hero.location = "old lookout"
    hero.meters["attention"] = 1.0
    hero.memes["kindness"] = 1.0
    guide.location = "old lookout"
    guide.meters["rope_ready"] = 0.25
    traveler.location = "safe at the old lookout"
    traveler.meters["safety"] = 1.0
    traveler.meters["heard_signal"] = 1.0
    traveler.memes["hope"] = 0.9
    bell.location = "hung at the old lookout"
    bell.meters["sound"] = 0.0
    bell.memes["signal"] = 1.0
    world.facts.update(
        rescue_complete=True,
        destination_reached=True,
        kindness_shown=True,
        signal_repetitions=3,
    )

    prompts = [
        f"Write an Adventure about {params.hero} and Eval carrying a pewter bell through {params.place}.",
        f"Include a kind rescue in which three repeated bell rings help find {scenario.traveler}.",
        "Use a brief inner monologue that changes the hero's decision, and finish with a concrete image of what changed.",
    ]
    story_qa = [
        QAItem(
            question="Why did the travelers stop on the trail?",
            answer=(
                f"They heard {scenario.traveler} calling for help after this happened: "
                f"{scenario.obstacle} They chose to help before continuing to the lookout."
            ),
        ),
        QAItem(
            question="What clue helped them find the lost hiker?",
            answer=(
                f"They noticed that {scenario.clue}. They used that clue to listen carefully "
                "for the hiker's answer."
            ),
        ),
        QAItem(
            question="How did the repeated bell rings help?",
            answer=(
                "Nia rang the pewter bell three times, waiting for an answer after each ring. "
                f"The answers helped the travelers find {scenario.traveler} and choose a safe route."
            ),
        ),
        QAItem(
            question="Why did the hero decide to help instead of hurrying on?",
            answer=(
                f"The hero thought that someone would be left scared in the storm if they hurried "
                f"on alone. They stopped, and Eval helped them {scenario.rescue}."
            ),
        ),
        QAItem(
            question="What changed by the end of the adventure?",
            answer=(
                f"{scenario.traveler} was safe, and the group reached the lookout with the pewter "
                f"bell. {scenario.ending_image}."
            ),
        ),
    ]
    world_qa = [
        QAItem(
            question="Why can repeating a signal help during an adventure?",
            answer=(
                "Repeating a clear signal gives someone more than one chance to hear it and answer, "
                "which can help travelers find one another."
            ),
        ),
        QAItem(
            question="What does kindness look like when a traveler is in a hurry?",
            answer=(
                "Kindness can mean pausing to notice someone who needs help and making a safe plan "
                "before continuing."
            ),
        ),
        QAItem(
            question="What is an inner monologue?",
            answer=(
                "An inner monologue is a character's private thought. It can show why the character "
                "changes their mind or chooses what to do."
            ),
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
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
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def verify_generated_stories() -> bool:
    cases = [
        StoryParams("Nia", PLACES[0], "misty_pine", "arrival", 11),
        StoryParams("Mira", PLACES[1], "broken_step", "warning", 22),
        StoryParams("Tavi", PLACES[2], "snow_drift", "dialogue", 33),
    ]
    for params in cases:
        sample = generate(params)
        story = sample.story
        required_text = (
            "pewter bell",
            "Eval",
            "thought,",
            "rang the pewter bell once",
            "They rang it twice",
            "On the third ring",
            "said.",
            "replied.",
        )
        if any(fragment not in story for fragment in required_text):
            print(f"MISMATCH: generated story for {params.scenario!r} is missing a required story element.")
            return False
        if not sample.world or not sample.world.facts.get("rescue_complete"):
            print(f"MISMATCH: generated story for {params.scenario!r} has no completed rescue state.")
            return False
        if sample.world.entities[params.scenario].meters.get("safety") != 1.0:
            print(f"MISMATCH: generated story for {params.scenario!r} has an unsafe ending state.")
            return False
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.n < 1 and not args.all:
        raise StoryError("-n must be at least 1.")
    if args.show_asp:
        print(asp_program("#show valid_scenario/1."))
        return
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        for atom in sorted(str(symbol) for symbol in model):
            print(atom)
        return
    if args.verify:
        if not verify_generated_stories():
            sys.exit(1)
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        curated = [
            StoryParams("Nia", PLACES[0], "misty_pine", "arrival", 101),
            StoryParams("Mira", PLACES[1], "broken_step", "dialogue", 202),
            StoryParams("Tavi", PLACES[2], "snow_drift", "warning", 303),
        ]
        samples = [generate(params) for params in curated]
    else:
        samples = []
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            attempt += 1
            attempt_seed = base_seed + attempt
            params = resolve_params(args, random.Random(attempt_seed))
            params.seed = attempt_seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
        if len(samples) < args.n:
            raise StoryError("Could not generate the requested number of distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} in {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(f"Story error: {exc}", file=sys.stderr)
        sys.exit(2)
