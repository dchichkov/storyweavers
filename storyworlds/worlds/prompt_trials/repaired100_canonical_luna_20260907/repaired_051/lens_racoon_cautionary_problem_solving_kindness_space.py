#!/usr/bin/env python3
"""
A small Space Adventure storyworld about Lens, a racoon, and careful kindness.

Lens and the racoon travel through a little star station, where a bright signal
must be repaired before a drifting supply pod misses its safe path. The story
turns on a cautionary choice: rushing toward a shiny answer can make danger
worse, while patient problem solving and kindness reveal the right way home.
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
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "distance": 0.0,
            "battery": 0.0,
            "signal": 0.0,
            "safety": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "courage": 0.0,
            "trust": 0.0,
            "kindness": 0.0,
            "relief": 0.0,
        }
    )


@dataclass
class Setting:
    place: str = "the Starling Space Station"
    orbit: str = "above the blue moon"


@dataclass
class StoryParams:
    lens: str
    racoon: str
    pilot: str
    beacon: str
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
        if text:
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
        "problem": "a meteor pebble had cracked the beacon's blue signal lens",
        "risk": "If the wrong beam flashed, the supply pod would follow it toward a field of spinning rocks.",
        "clue": "tiny silver scratches pointed away from the bright control button",
        "method": "They dimmed the beacon, compared the scratches with the pod's map, and turned the lens one careful notch at a time.",
        "kindness": "The racoon shared the last warm snack with a tired moon-moth mechanic who held the map steady.",
        "result": "The repaired lens sent a calm blue path across space, and the supply pod glided safely to the station.",
        "lesson": "a bright answer is not always a safe answer; careful checking protects everyone",
        "image": "the blue beacon shone softly while the moon below looked like a round sleeping lantern",
        "question": "Why was it dangerous to press the bright control button?",
    },
    {
        "problem": "a loose cable had made the station's welcome lights blink in a confusing pattern",
        "risk": "A visiting shuttle could mistake the blinking lights for an emergency landing signal.",
        "clue": "Lens noticed that the blink always paused when the racoon's tail brushed a silver handrail",
        "method": "They switched off one circuit at a time, labeled each cable, and fastened the loose wire with a soft clamp.",
        "kindness": "The racoon waited while a small robot gathered its scattered tools instead of kicking them aside.",
        "result": "The welcome lights formed one clear row, and the shuttle found the gentle landing lane.",
        "lesson": "solving a problem slowly can leave room to care for helpers",
        "image": "the station windows twinkled in a friendly row as the shuttle doors opened",
        "question": "How did Lens discover which cable was loose?",
    },
    {
        "problem": "the navigation screen had fogged after a cup of comet tea tipped beside it",
        "risk": "Without the screen, the crew might fly into a dark gravity pocket.",
        "clue": "The racoon saw one clear crescent where warm air escaped from a tiny vent",
        "method": "They moved the cup away, opened the vent cover, and used a dry cloth instead of scraping the delicate screen.",
        "kindness": "Lens thanked the nervous tea seller and helped clean the spilled tea from the floor.",
        "result": "The map returned with the safe route glowing green around the gravity pocket.",
        "lesson": "a gentle repair can solve trouble without blaming the one who made a mistake",
        "image": "green stars curved across the screen like a quiet river through the dark",
        "question": "Why did the friends use a dry cloth instead of scraping the screen?",
    },
    {
        "problem": "a tiny garden satellite had drifted loose from its gentle orbit",
        "risk": "Its seed pods could tumble into space before the station gardeners found them.",
        "clue": "Lens saw that its shadow moved in a repeating triangle",
        "method": "They measured the three movements, matched them to the station clock, and sent a small tug only at the quietest point.",
        "kindness": "The racoon held the seed-pod basket close so no frightened sprout would float away.",
        "result": "The garden satellite returned to orbit, and its first yellow flower opened beside the airlock.",
        "lesson": "good problem solving listens to patterns and protects small lives",
        "image": "a yellow flower floated in its glass pod beneath a sky full of stars",
        "question": "What pattern helped the friends guide the garden satellite?",
    },
]


OPENINGS = [
    "Before the first sunbeam reached the station windows",
    "While the Starling Space Station sailed above the blue moon",
    "At the quietest hour of the night watch",
    "As stars sprinkled silver across the station dome",
    "When the little station bell chimed for morning",
]


def _choose(options: list[str], variant: int, offset: int) -> str:
    return options[(variant + offset) % len(options)]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Space Adventure: Lens and a racoon solve a dangerous station problem with kindness."
    )
    parser.add_argument("--lens")
    parser.add_argument("--racoon")
    parser.add_argument("--pilot")
    parser.add_argument("--beacon")
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
    lens = args.lens or rng.choice(["Lens", "Lena Lens", "Little Lens"])
    racoon = args.racoon or rng.choice(["the racoon", "Rollo the racoon", "Clover the racoon"])
    pilot = args.pilot or rng.choice(["Captain Mira", "Pilot Sol", "Commander Nia"])
    beacon = args.beacon or rng.choice(["the blue beacon", "the home beacon", "the star beacon"])
    return StoryParams(
        lens=lens,
        racoon=racoon,
        pilot=pilot,
        beacon=beacon,
        scenario_index=rng.randrange(len(SCENARIOS)),
        detail_variant=rng.randrange(10000),
    )


def tell(params: StoryParams) -> World:
    scenario = SCENARIOS[params.scenario_index % len(SCENARIOS)]
    world = World(Setting())

    lens = world.add(Entity("lens", "object", "lens", params.lens))
    racoon = world.add(Entity("racoon", "animal", "racoon", params.racoon))
    pilot = world.add(Entity("pilot", "person", "pilot", params.pilot))
    beacon = world.add(Entity("beacon", "object", "beacon", params.beacon))

    world.facts.update(
        lens=lens,
        racoon=racoon,
        pilot=pilot,
        beacon=beacon,
        scenario=scenario,
    )

    pilot.memes["trust"] = 1.0
    lens.memes["worry"] = 1.0
    racoon.memes["kindness"] = 1.0

    opening = _choose(OPENINGS, params.detail_variant, 0)
    world.say(
        f"{opening}, {params.lens} checked the star maps inside {world.setting.place}, "
        f"where the station sailed {world.setting.orbit}."
    )
    world.say(
        f"Beside {params.lens} padded {params.racoon}, a clever racoon who could fit "
        f"between the humming pipes."
    )
    world.say(
        f'{params.pilot} hurried in. "{params.beacon.capitalize()} needs help before '
        f'the next shuttle arrives," the pilot said.'
    )
    world.say(f"The trouble was clear: {scenario['problem'].capitalize()}.")
    world.para()

    lens.meters["distance"] = 1.0
    beacon.meters["signal"] = 0.25
    lens.memes["worry"] = 2.0
    world.say(scenario["risk"])
    world.say(
        f'"I can rush to the controls!" said {params.racoon}. '
        f'"Please wait," replied {params.lens}. "First we need to know what is wrong."'
    )
    world.say(
        f"{params.lens} remembered that a shiny button could be tempting but unsafe. "
        f"{params.racoon} listened, even though the racoon's paws were already on the rail."
    )
    world.para()

    world.say(
        f"Together they searched. {params.lens.capitalize()} found that {scenario['clue']}."
    )
    world.say(
        f'"Then we can test one small change at a time," said {params.lens}. '
        f'"And we can help anyone nearby," added {params.racoon}.'
    )
    world.say(scenario["kindness"])
    world.say(scenario["method"])
    lens.meters["signal"] = 1.0
    lens.meters["safety"] = 1.0
    beacon.meters["signal"] = 1.0
    racoon.memes["courage"] = 1.0
    racoon.memes["kindness"] = 2.0
    lens.memes["trust"] = 2.0
    world.para()

    world.say(scenario["result"])
    world.say(
        f'"You solved the problem without making a risky guess," said {params.pilot}. '
        f'"And you made room to be kind," the pilot added.'
    )
    world.say(
        f"{params.lens} smiled at {params.racoon}. They had learned that {scenario['lesson']}."
    )
    lens.memes["relief"] = 1.0
    racoon.memes["relief"] = 1.0
    pilot.memes["relief"] = 1.0
    world.say(f"At last, {scenario['image']}.")
    world.log(f"scenario={params.scenario_index % len(SCENARIOS)}")
    world.log("checked_before_action=True")
    world.log("kindness_used=True")
    world.log("safe_resolution=True")
    return world


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    lens: Entity = world.facts["lens"]  # type: ignore[assignment]
    racoon: Entity = world.facts["racoon"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly Space Adventure about {lens.label} and {racoon.label}.",
        f"Tell a cautionary problem-solving story in which {lens.label} helps repair a station problem without rushing.",
        f"Include kindness, a clear danger, spoken dialogue, a useful clue, and a safe ending involving {scenario['problem']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario = world.facts["scenario"]
    lens: Entity = world.facts["lens"]  # type: ignore[assignment]
    racoon: Entity = world.facts["racoon"]  # type: ignore[assignment]
    pilot: Entity = world.facts["pilot"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What problem did {pilot.label} bring to {lens.label} and {racoon.label}?",
            answer=f"{pilot.label} explained that {scenario['problem']}. The problem mattered because it could affect a safe journey through space.",
        ),
        QAItem(
            question=scenario["question"],
            answer=f"It was dangerous because {scenario['risk'][0].lower() + scenario['risk'][1:]} The friends checked the evidence before touching the controls.",
        ),
        QAItem(
            question=f"What clue helped {lens.label} and {racoon.label}?",
            answer=f"They noticed that {scenario['clue']}. This clue showed them where to look and how to make a safer repair.",
        ),
        QAItem(
            question=f"How did {lens.label} and {racoon.label} solve the problem?",
            answer=f"They {scenario['method'][0].lower() + scenario['method'][1:]} Their careful method restored a safe path.",
        ),
        QAItem(
            question=f"How did kindness help during the adventure?",
            answer=f"{scenario['kindness']} Helping others kept the repair calm and made the solution safer for everyone.",
        ),
        QAItem(
            question=f"What did {lens.label} learn?",
            answer=f"{lens.label} learned that {scenario['lesson']}. The safe ending proved that patience and kindness can guide good choices.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a lens do?",
            answer="A lens bends or focuses light so that an image or beam can be seen or aimed more clearly.",
        ),
        QAItem(
            question="What is a racoon?",
            answer="A racoon is a small mammal with a masked face, nimble paws, and a ringed tail.",
        ),
        QAItem(
            question="Why is checking important before solving a problem?",
            answer="Checking is important because it can reveal the real cause and prevent a rushed choice from creating more danger.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means noticing another person's needs and choosing to help with care and respect.",
        ),
        QAItem(
            question="What is a beacon?",
            answer="A beacon is a light or signal that helps guide people, vehicles, or spacecraft toward a place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== world qa =="])
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
entity(lens).
entity(racoon).
entity(pilot).
entity(beacon).

checked_before_action.
kindness_used.
safe_resolution.

solved :- checked_before_action, kindness_used, safe_resolution.
happy_end :- solved.

#show solved/0.
#show happy_end/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("checked_before_action"),
            asp.fact("kindness_used"),
            asp.fact("safe_resolution"),
        ]
    )


def asp_program(show: str = "#show solved/0. #show happy_end/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    names = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"solved/0", "happy_end/0"}
    if names == expected:
        print("OK: ASP parity check passed.")
        return 0
    print(f"MISMATCH: {sorted(names)} != {sorted(expected)}")
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
        lens="Lens",
        racoon="Rollo the racoon",
        pilot="Captain Mira",
        beacon="the blue beacon",
        scenario_index=0,
        detail_variant=1,
    ),
    StoryParams(
        lens="Lena Lens",
        racoon="Clover the racoon",
        pilot="Pilot Sol",
        beacon="the home beacon",
        scenario_index=1,
        detail_variant=4,
    ),
    StoryParams(
        lens="Little Lens",
        racoon="the racoon",
        pilot="Commander Nia",
        beacon="the star beacon",
        scenario_index=2,
        detail_variant=7,
    ),
    StoryParams(
        lens="Lens",
        racoon="Clover the racoon",
        pilot="Captain Mira",
        beacon="the garden beacon",
        scenario_index=3,
        detail_variant=9,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        code = asp_verify()
        if code:
            sys.exit(code)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or "Lens" not in sample.story:
                print("MISMATCH: generated story check failed")
                sys.exit(1)
            if not sample.story_qa or not sample.world_qa:
                print("MISMATCH: generated QA check failed")
                sys.exit(1)
        print("OK: generated story checks passed.")
        return

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
        while len(samples) < args.n and attempt < max(args.n * 20, 20):
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
