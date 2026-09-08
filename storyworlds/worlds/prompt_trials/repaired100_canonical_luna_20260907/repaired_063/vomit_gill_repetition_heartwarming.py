#!/usr/bin/env python3
"""
A standalone heartwarming storyworld about a small pond rescue, careful
observation, and the repeated courage of asking for help.

Seed tale:
A child finds a little fish floating near the pond's edge. The fish has vomit
on its gill and cannot breathe well. The child repeats a calm rescue routine:
stop, look, call, and wait. With a pond keeper's help, the fish is moved to
clean water and swims home.
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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the willow pond"


@dataclass
class StoryParams:
    name: str
    helper_name: str
    fish_name: str
    incident_id: int = 0
    opening_mode: int = 0
    repetition_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


SETTING = Setting()

NAMES = ["Luna", "Milo", "Nia", "Theo", "Pia", "Jun", "Asha", "Owen"]
HELPERS = ["Mara", "Sam", "Inez", "Rowan"]
FISH_NAMES = ["Blink", "Bubbles", "Dart", "Sunny", "Pebble"]

OPENINGS = [
    "Early one soft morning",
    "After a warm rain",
    "While the willow leaves whispered",
    "Just before breakfast",
    "On a bright day beside the water",
]

REPETITIONS = [
    "Luna remembered the pond keeper's safety words: stop, look, call, and wait. She said them once, then said them again.",
    "They used the same gentle pattern each time: stop, look, call, and wait. Stop, look, call, and wait.",
    "The words became a little bridge between worry and help: stop, look, call, and wait. Luna repeated the bridge until help arrived.",
    "Luna breathed in and repeated the plan slowly: stop, look, call, and wait. Then she repeated it for the fish.",
]

ENDINGS = [
    "That evening, Luna left a small painted sign by the pond: STOP, LOOK, CALL, WAIT. Beneath it, the water shone with tiny rings.",
    "The next morning, Luna heard a quick splash near the reeds. She smiled, because careful help had given the pond another happy swimmer.",
    "Luna went home with damp shoes and a warm heart. Behind her, the willow pond kept the little fish safe in its quiet green arms.",
    "At sunset, the pond keeper hung a bright blue ribbon on the fence. It fluttered each time the rescued fish made a ripple.",
]

INCIDENTS = [
    {
        "symptom": "a little fish floating sideways near the reeds",
        "vomit": "a small patch of vomit resting against its gill",
        "cause": "A storm had washed spoiled picnic crumbs into the shallow water, and the fish had swallowed something that upset it.",
        "help": "The pond keeper used a clean net and a bowl of fresh pond water to move the fish away from the dirty patch.",
        "result": "In the clean bowl, the fish steadied and opened its gill more easily.",
        "lesson": "Small creatures need careful help, not hurried guesses.",
        "image": "By evening, the fish slipped through clear water and left a bright silver comma behind it.",
    },
    {
        "symptom": "a tiny fish resting beneath a flat leaf",
        "vomit": "a thread of pale vomit caught beside its gill",
        "cause": "A bit of old food had drifted from a feeder and bothered the fish's breathing.",
        "help": "The pond keeper gently cleared the water with a scoop and placed the fish in a clean recovery tub.",
        "result": "The fish began to glide in slow circles while the keeper watched its gill.",
        "lesson": "Watching closely can be a kind form of care.",
        "image": "When the sun came out, the fish made three neat circles beneath the lily pads.",
    },
    {
        "symptom": "a young fish trembling beside the pond steps",
        "vomit": "a little smear of vomit near one gill",
        "cause": "The pond water had become cloudy after a fallen branch stirred the muddy bottom.",
        "help": "The pond keeper guided the fish into a clear holding bowl and asked an adult to remove the branch.",
        "result": "The fish's breathing grew calmer as the water cleared.",
        "lesson": "A calm routine helps people notice what a living creature needs.",
        "image": "The next day, sunlight reached the pond floor, and the fish flashed gold beneath the willow.",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming pond storyworld with repetition and gentle rescue."
    )
    parser.add_argument("--name")
    parser.add_argument("--helper-name")
    parser.add_argument("--fish-name")
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper_name=args.helper_name or rng.choice(HELPERS),
        fish_name=args.fish_name or rng.choice(FISH_NAMES),
        incident_id=rng.randrange(len(INCIDENTS)),
        opening_mode=rng.randrange(len(OPENINGS)),
        repetition_mode=rng.randrange(len(REPETITIONS)),
        ending_mode=rng.randrange(len(ENDINGS)),
    )


def _build_world(params: StoryParams) -> World:
    if not params.name.strip():
        raise StoryError("The child's name cannot be empty.")
    if not params.helper_name.strip():
        raise StoryError("The helper's name cannot be empty.")
    if not params.fish_name.strip():
        raise StoryError("The fish's name cannot be empty.")

    incident = INCIDENTS[params.incident_id % len(INCIDENTS)]
    world = World(SETTING)

    child = world.add(
        Entity(
            id="child",
            kind="character",
            type="child",
            label=params.name,
            meters={"attention": 1.0},
            memes={"care": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type="pond_keeper",
            label=params.helper_name,
            meters={"knowledge": 1.0},
            memes={"calm": 1.0},
        )
    )
    fish = world.add(
        Entity(
            id="fish",
            kind="animal",
            type="fish",
            label=params.fish_name,
            meters={"breathing": 0.2, "safe": 0.0},
            memes={"trust": 0.2},
        )
    )
    water = world.add(
        Entity(
            id="water",
            kind="place",
            type="pond_water",
            label="the pond water",
            meters={"clean": 0.3},
        )
    )
    gill = world.add(
        Entity(
            id="gill",
            kind="body_part",
            type="gill",
            label="the fish's gill",
            meters={"clear": 0.0},
        )
    )

    world.facts.update(
        params=params,
        incident=incident,
        child=child,
        helper=helper,
        fish=fish,
        water=water,
        gill=gill,
        repetitions=0,
        rescue_complete=False,
    )
    return world


def tell(world: World) -> None:
    facts = world.facts
    params: StoryParams = facts["params"]  # type: ignore[assignment]
    incident: dict[str, str] = facts["incident"]  # type: ignore[assignment]
    child: Entity = facts["child"]  # type: ignore[assignment]
    helper: Entity = facts["helper"]  # type: ignore[assignment]
    fish: Entity = facts["fish"]  # type: ignore[assignment]
    gill: Entity = facts["gill"]  # type: ignore[assignment]

    world.say(
        f"{OPENINGS[params.opening_mode % len(OPENINGS)]}, {child.label} walked to "
        f"{world.setting.place} with a small blue cup in her hand."
    )
    world.say(
        f"Near the reeds, she saw {incident['symptom']}. It was {fish.label}, and "
        f"{incident['vomit']} made the little fish breathe in short, tired flickers."
    )

    world.para()
    world.say(
        f"{child.label} wanted to scoop up {fish.label}, but she remembered that a "
        "struggling animal could be hurt by hurried hands."
    )
    world.say(REPETITIONS[params.repetition_mode % len(REPETITIONS)])
    world.say(
        f'"I see a problem with {fish.label}\'s gill," {child.label} called. '
        f'"Can you help us, {helper.label}?"'
    )
    world.say(
        f'"I can help," said {helper.label}. "Tell me exactly what you saw, and keep "
        "your hands still until I bring the clean net."'
    )

    world.para()
    world.say(
        f"{child.label} pointed without touching. She explained that she had seen "
        f"{incident['vomit']} and that {fish.label} was floating sideways."
    )
    world.say(f"{helper.label} nodded. {incident['cause']}")
    world.say(
        f"Together they repeated the safe plan: stop, look, call, and wait. "
        f"Then {helper.label} used the clean net while {child.label} held the bowl steady."
    )
    world.say(incident["help"])

    fish.meters["breathing"] = 0.8
    fish.meters["safe"] = 1.0
    gill.meters["clear"] = 1.0
    fish.memes["trust"] = 1.0
    facts["repetitions"] = 3

    world.para()
    world.say(incident["result"])
    world.say(
        f"{child.label} watched the gill open and close. "
        f'"Is {fish.label} ready to go?" she asked.'
    )
    world.say(
        f'"The water is clear, and the breathing is calm," said {helper.label}. '
        f'"Now we can let {fish.label} choose the way."'
    )
    world.say(
        f"The fish flicked its tail, slipped from the bowl, and swam beneath the willow."
    )
    world.say(incident["lesson"])
    world.say(ENDINGS[params.ending_mode % len(ENDINGS)])
    world.say(incident["image"])

    facts["rescue_complete"] = True


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    incident: dict[str, str] = facts["incident"]  # type: ignore[assignment]
    return [
        "Write a short heartwarming story for a young child about noticing an animal in trouble and asking a trusted helper for safe help.",
        f"Tell a gentle pond story in which {facts['child'].label} sees {facts['fish'].label} with vomit near a gill and repeats a calm rescue routine.",
        f"Write a story with repetition, brief dialogue, careful observation, and an ending image showing that {incident['result'].lower()}",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    incident: dict[str, str] = facts["incident"]  # type: ignore[assignment]
    child: Entity = facts["child"]  # type: ignore[assignment]
    helper: Entity = facts["helper"]  # type: ignore[assignment]
    fish: Entity = facts["fish"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {child.label} notice near the pond?",
            answer=f"{child.label} noticed {incident['symptom']} and {incident['vomit']}.",
        ),
        QAItem(
            question="What repeated safety plan did the child use?",
            answer="The child repeated the plan: stop, look, call, and wait.",
        ),
        QAItem(
            question=f"Why did {child.label} call {helper.label}?",
            answer=f"{child.label} called {helper.label} because {fish.label} was struggling to breathe and needed careful help.",
        ),
        QAItem(
            question="How did the helper move the fish?",
            answer=incident["help"],
        ),
        QAItem(
            question="What showed that the fish was getting better?",
            answer=incident["result"],
        ),
        QAItem(
            question="What happened at the end?",
            answer=incident["image"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gill?",
            answer="A gill is a breathing organ that helps many fish take oxygen from water.",
        ),
        QAItem(
            question="What does vomit mean?",
            answer="Vomit is material that comes back up from a stomach when an animal or person is sick.",
        ),
        QAItem(
            question="Why should someone ask a trusted adult before helping an animal?",
            answer="A trusted adult can choose a safer way to help and can contact the right animal-care person.",
        ),
        QAItem(
            question="Why can repetition be useful?",
            answer="Repetition can help someone remember calm steps when a situation feels confusing or worrying.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id:8} ({entity.type:11}) meters={meters} memes={memes}"
        )
    lines.append(f"  repetitions={world.facts.get('repetitions', 0)}")
    lines.append(f"  rescue_complete={world.facts.get('rescue_complete', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
observed(vomit).
observed(gill).
repetition(stop_look_call_wait).
helper_available.
clean_water.
safe_plan :- repetition(stop_look_call_wait), helper_available.
rescued :- observed(vomit), observed(gill), safe_plan, clean_water.
good_story :- rescued.
#show good_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("observed", "vomit"),
            asp.fact("observed", "gill"),
            asp.fact("repetition", "stop_look_call_wait"),
            asp.fact("helper_available"),
            asp.fact("clean_water"),
        ]
    )


def asp_program(show: str = "#show good_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    good = any(symbol.name == "good_story" for symbol in model)
    if not good:
        print("MISMATCH: ASP twin did not find good_story.")
        return 1

    sample = generate(
        StoryParams(
            name="Luna",
            helper_name="Mara",
            fish_name="Blink",
            incident_id=0,
            opening_mode=0,
            repetition_mode=0,
            ending_mode=0,
            seed=1,
        )
    )
    required = ["vomit", "gill", "stop, look, call, and wait"]
    missing = [word for word in required if word not in sample.story]
    if missing:
        print(f"MISMATCH: generated story is missing {missing}.")
        return 1
    if sample.world is None or not sample.world.facts["rescue_complete"]:
        print("MISMATCH: Python world did not complete the rescue.")
        return 1

    print("OK: ASP and Python agree on the repeated, careful rescue.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    tell(world)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        name="Luna",
        helper_name="Mara",
        fish_name="Blink",
        incident_id=0,
        opening_mode=0,
        repetition_mode=0,
        ending_mode=0,
    ),
    StoryParams(
        name="Milo",
        helper_name="Sam",
        fish_name="Sunny",
        incident_id=1,
        opening_mode=2,
        repetition_mode=1,
        ending_mode=1,
    ),
    StoryParams(
        name="Nia",
        helper_name="Inez",
        fish_name="Pebble",
        incident_id=2,
        opening_mode=1,
        repetition_mode=3,
        ending_mode=2,
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
        print("good_story" if any(symbol.name == "good_story" for symbol in model) else "(none)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} and {sample.params.fish_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
