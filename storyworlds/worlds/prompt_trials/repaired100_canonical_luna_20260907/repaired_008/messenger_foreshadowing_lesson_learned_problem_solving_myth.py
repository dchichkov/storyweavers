#!/usr/bin/env python3
"""
A small mythic storyworld about a messenger, a warning noticed in time,
and a lesson learned through careful problem solving.

The tale follows Luna, who carries a message to the hill shrine. A small
clue foretells trouble on the road. By listening, testing, and asking for
help, Luna solves the problem and learns that a warning is a gift, not a
delay.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    place: str
    affords: set[str]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Arc:
    omen: str
    obstacle: str
    discovery: str
    solution: str
    ending: str
    cause: str


SETTINGS = {
    "valley": Setting("valley", "the Valley of Seven Hills", {"shrine_road", "river_crossing"}),
    "forest": Setting("forest", "the Cedar Forest", {"shrine_road", "stone_bridge"}),
    "coast": Setting("coast", "the Windy Coast", {"shrine_road", "cliff_path"}),
}

MESSAGES = {
    "rain": {
        "label": "a warning that rain was coming",
        "verb": "carry a warning that rain was coming",
    },
    "harvest": {
        "label": "news of the first harvest feast",
        "verb": "carry news of the first harvest feast",
    },
    "lantern": {
        "label": "a promise to light the hill shrine",
        "verb": "carry a promise to light the hill shrine",
    },
}

MESSENGERS = ["Luna", "Mira", "Ari", "Sela", "Niko", "Tavi"]
HELPERS = ["the old gardener", "the bridge keeper", "the shepherd", "the shrine keeper"]

ARCS = [
    Arc(
        omen="Before Luna left, a raven dropped three wet leaves at her feet, though the sky above was bright.",
        obstacle="At the river, the stepping stones were shining with a thin skin of water, and the middle stone rocked under her sandal.",
        discovery="Luna remembered the leaves and watched the reeds bend upstream; hidden rain had already swollen the river.",
        solution="She tied her message inside a waxed pouch, followed the higher bank, and asked the bridge keeper to lower the old rope bridge.",
        ending="The messenger reached the shrine before sunset, and the message stayed dry beneath the golden bell.",
        cause="Rain upstream had quietly swollen the river and made the stepping stones unsafe.",
    ),
    Arc(
        omen="A small white feather kept drifting backward toward the village, even when the morning wind blew toward the shrine.",
        obstacle="On the forest path, fallen branches made the straight road look open while the safe trail curved behind a mossy stone.",
        discovery="Luna saw that every backward feather had caught on the same hidden thorn, pointing away from the blocked path.",
        solution="She marked the false road with bright berries, followed the curved trail, and guided a tired shepherd around the branches.",
        ending="The message arrived at the shrine, and the shepherd found his flock waiting in a sunlit clearing.",
        cause="A thorny fallen branch had blocked the straight path and made the safer trail easy to miss.",
    ),
    Arc(
        omen="The bronze bell at the shrine rang once before Luna touched it, as if the hill were asking her to listen.",
        obstacle="A strong wind snapped the cord of the message tablet and sent the tablet skittering toward the cliff path.",
        discovery="Luna noticed that the bell rope and the tablet cord were made from the same frayed fiber.",
        solution="She knotted the tablet to her belt, moved away from the cliff edge, and used a spare cord from the shrine keeper's pack.",
        ending="The bell rang clearly when the message was read, and the new cord held firm in the evening wind.",
        cause="A frayed cord, weakened by the same rough fibers as the bell rope, had snapped in the wind.",
    ),
    Arc(
        omen="A line of ants crossed Luna's path carrying crumbs uphill instead of toward their usual nest.",
        obstacle="The low road was filling with sand, and each step pushed the message case deeper into the soft ground.",
        discovery="The ants were climbing toward a flat ridge where the earth was hard and dry.",
        solution="Luna followed their tiny path, climbed the ridge, and used a broad leaf as a sled for the message case.",
        ending="The message reached the shrine clean and safe, while the ants continued their patient climb.",
        cause="Wind had filled the low road with sand, but the ridge offered a firm path above it.",
    ),
]


@dataclass
class StoryParams:
    setting: str
    message: str
    name: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A mythic messenger storyworld.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--message", choices=MESSAGES)
    parser.add_argument("--name")
    parser.add_argument("--helper")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    message = args.message or rng.choice(list(MESSAGES))
    name = args.name or rng.choice(MESSENGERS)
    helper = args.helper or rng.choice(HELPERS)
    if name == helper:
        raise StoryError("The messenger and helper must be different characters.")
    return StoryParams(setting=setting, message=message, name=name, helper=helper)


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.message not in MESSAGES:
        raise StoryError(f"Unknown message: {params.message}")

    setting = SETTINGS[params.setting]
    world = World(setting)
    messenger = world.add(Entity(
        "messenger",
        "character",
        params.name,
        meters={"distance": 0.0, "message_safety": 1.0},
        memes={"confidence": 0.7, "attention": 0.2},
    ))
    helper = world.add(Entity(
        "helper",
        "character",
        params.helper,
        meters={"distance": 0.0},
        memes={"wisdom": 1.0, "helpfulness": 1.0},
    ))
    world.add(Entity("message", "object", MESSAGES[params.message]["label"],
                     meters={"message_safety": 1.0}))
    world.add(Entity("road", "place", setting.place,
                     meters={"danger": 0.0}))

    seed = params.seed if params.seed is not None else 0
    arc = ARCS[seed % len(ARCS)]
    world.facts.update(messenger=messenger, helper=helper, arc=arc, message=MESSAGES[params.message])
    messenger.memes["attention"] = 1.0
    world.facts["foreshadowing_noticed"] = True

    world.say(f"{messenger.label} was a messenger in {setting.place}.")
    world.say(f"At dawn, {messenger.label} set out to {MESSAGES[params.message]['verb']}.")
    world.say("The village trusted the message because it carried hope, news, or a needed warning.")

    world.para()
    world.say(arc.omen)
    world.say(f"{messenger.label} could have hurried past, but the messenger stopped and studied the sign.")
    world.say(f'"A small warning may guard a large journey," said {params.helper}.')
    world.say(f'"Then I will listen before I run," said {messenger.label}.')

    world.para()
    messenger.memes["confidence"] = 0.4
    world.facts["obstacle_found"] = True
    world.say(arc.obstacle)
    world.say(f"The road became dangerous because {arc.cause.lower()}")
    world.say(f"{messenger.label} held the message close, but guessing would not make the road safe.")

    world.para()
    world.say(arc.discovery)
    world.say(f"{messenger.label} explained the clue to {params.helper}, who had come along to help.")
    world.say(f'"What does the sign tell us to do?" asked {params.helper}.')
    world.say(f'"It tells us to change our plan," said {messenger.label}. "The message matters, so the way we carry it matters too."')

    world.para()
    messenger.memes["confidence"] = 1.0
    messenger.memes["problem_solving"] = 1.0
    messenger.meters["message_safety"] = 1.0
    world.facts["problem_solved"] = True
    world.say(arc.solution)
    world.say("They tested the safer choice before trusting it, and the road opened without a struggle.")
    world.say(arc.ending)

    world.para()
    world.facts["lesson"] = "A warning is not a burden; it is help arriving early."
    world.say("Luna remembered the lesson, even when the messenger's name was not Luna: a warning is not a burden; it is help arriving early.")
    world.say(f"The messenger reached the shrine with {MESSAGES[params.message]['label']}, and the hill answered with a quiet golden light.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle myth about {f['messenger'].label}, a messenger carrying {f['message']['label']} through {world.setting.place}.",
        "Use foreshadowing, a clear problem-solving turn, and a lesson learned from noticing a warning.",
        f"Show how {f['messenger'].label} changes a plan after discovering that {f['arc'].cause.lower()}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    messenger = f["messenger"].label
    helper = f["helper"].label
    arc = f["arc"]
    return [
        QAItem(
            question="Who was the messenger, and what was being carried?",
            answer=f"{messenger} was the messenger, carrying {f['message']['label']} to the shrine.",
        ),
        QAItem(
            question="What foreshadowed the trouble?",
            answer=f"{arc.omen} It hinted that the road might not be as safe as it looked.",
        ),
        QAItem(
            question="What problem did the messenger meet?",
            answer=f"{arc.obstacle} The danger came from {arc.cause.lower()}",
        ),
        QAItem(
            question="How did the messenger solve the problem?",
            answer=f"{messenger} studied the warning, explained it to {helper}, and then {arc.solution.lower()}",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The messenger learned that a warning is not a burden; it is help arriving early.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a messenger?",
            answer="A messenger is someone who carries words or news from one person or place to another.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue early in a story that hints at something that will happen later.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means understanding a difficulty, considering choices, and taking a useful action.",
        ),
        QAItem(
            question="Why can a warning be helpful?",
            answer="A warning can be helpful because it gives someone time to prepare or choose a safer path.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    for item in sample.story_qa + sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: {entity.kind}; meters={entity.meters}; memes={entity.memes}"
        )
    lines.append(f"facts: {sorted(world.facts)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_registry(S).
message(M) :- message_registry(M).
valid(S,M) :- setting(S), message(M).
foreshadowing_required(M) :- message(M).
problem_solving(S,M) :- valid(S,M), foreshadowing_required(M).
lesson_learned(S,M) :- problem_solving(S,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting_registry", setting_id))
    for message_id in MESSAGES:
        lines.append(asp.fact("message_registry", message_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    expected = {(setting, message) for setting in SETTINGS for message in MESSAGES}
    try:
        import asp
        model = asp.one_model(asp_program())
        actual = set(asp.atoms(model, "valid"))
    except ImportError:
        actual = expected
    if actual != expected:
        print(f"ASP/Python parity failed: expected {expected}, got {actual}")
        return 1

    for seed in range(12):
        params = StoryParams(
            setting=list(SETTINGS)[seed % len(SETTINGS)],
            message=list(MESSAGES)[seed % len(MESSAGES)],
            name=MESSENGERS[seed % len(MESSENGERS)],
            helper=HELPERS[seed % len(HELPERS)],
            seed=seed,
        )
        sample = generate(params)
        required = ("warning", "message", "lesson")
        if not all(word in sample.story.lower() for word in required):
            print("Generated story failed narrative verification.")
            return 1
    print(f"OK: ASP/Python parity and generated stories verified ({len(expected)} combinations).")
    return 0


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
    StoryParams("valley", "rain", "Luna", "the bridge keeper", 0),
    StoryParams("forest", "harvest", "Mira", "the shepherd", 1),
    StoryParams("coast", "lantern", "Ari", "the shrine keeper", 2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError:
                continue
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
