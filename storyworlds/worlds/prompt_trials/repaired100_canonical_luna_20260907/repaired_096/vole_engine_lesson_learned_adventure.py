#!/usr/bin/env python3
"""
A child-facing adventure about a vole, a stubborn engine, and a lesson learned.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Engine:
    id: str
    name: str
    fuel: str
    problem: str
    repair: str
    safe_test: str
    result: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    name: str
    feature: str
    danger: str
    landmark: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    hero: Entity
    engine: Engine
    helper: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "misty_ravine": Setting(
        id="misty_ravine",
        name="the Misty Ravine",
        feature="a rope bridge over a silver stream",
        danger="the bridge will soon be hidden by rising fog",
        landmark="an old red signal post",
        meters={"length": 42.0, "visibility": 0.7},
        memes={"wonder": 0.8, "urgency": 0.6},
    )
}

ENGINES = {
    "lantern_engine": Engine(
        id="lantern_engine",
        name="the lantern engine",
        fuel="a small jar of sunflower oil",
        problem="its cooling belt has slipped beneath a loose brass panel",
        repair="tighten the belt and clear the panel before starting it",
        safe_test="turn the wheel by hand twice, then start it on the lowest setting",
        result="the engine hummed steadily and lit the signal lantern",
        meters={"weight": 8.0, "power": 4.0},
        memes={"stubbornness": 0.7, "reliability": 0.5},
    ),
    "water_engine": Engine(
        id="water_engine",
        name="the water engine",
        fuel="a pocket of clean stream water",
        problem="a twig is wedged in its small intake",
        repair="lift the cover and remove the twig without forcing the piston",
        safe_test="rinse the intake, move the piston gently, and listen for a clear click",
        result="the engine pumped a bright ribbon of water into the travel tank",
        meters={"weight": 10.0, "power": 5.0},
        memes={"stubbornness": 0.6, "reliability": 0.6},
    ),
}

NAMES = ["Nell", "Pip", "Mara", "Tavi"]
TRAITS = ["curious", "brave", "patient", "quick-footed", "careful"]
LESSONS = [
    "A brave adventurer does not rush past a warning; careful steps can carry everyone farther.",
    "When a machine resists, listening first is wiser than pushing harder.",
    "Asking for help is part of courage, especially when a small mistake could grow large.",
    "A lesson learned becomes useful when it changes the next choice.",
]

SCENES = [
    {
        "opening": "At dawn, a pale trail curled through the grass toward the Misty Ravine.",
        "quest": "the far side of the ravine held the medicine basket needed by the village gardener",
        "clue": "a line of oily paw marks ended beside the engine's brass panel",
        "turn": "the vole noticed that the panel was warm while the belt beneath it was still",
        "choice": "Nell stopped before pulling the starter cord",
        "ending": "the red signal lantern blinked across the fog, showing the safe path home",
    },
    {
        "opening": "The hills were quiet except for one lonely click beneath the morning wind.",
        "quest": "the explorers needed to cross the ravine before the bridge ropes became slick with mist",
        "clue": "a tiny twig trembled inside the engine's intake",
        "turn": "the vole heard the piston knock whenever the engine tried to drink water",
        "choice": "Nell set down the fuel cup and examined the intake",
        "ending": "a silver stream filled the travel tank, and the bridge appeared through the thinning fog",
    },
    {
        "opening": "Beyond the last row of berry bushes, the adventure began with a broken hum.",
        "quest": "the old engine had to power a signal before the evening hikers lost the trail",
        "clue": "a loose screw glittered in the mud near the wheel",
        "turn": "the vole realized that the wheel was wobbling because the screw belonged to its axle",
        "choice": "Nell held the wheel still instead of giving it more power",
        "ending": "the signal shone above the ravine while the returning hikers cheered below",
    },
]

@dataclass
class StoryParams:
    setting: str
    engine: str
    hero_name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(setting, engine) for setting in SETTINGS for engine in ENGINES]


def explain_rejection() -> str:
    return "The chosen setting and engine are not part of this small adventure world."


def build_world(params: StoryParams) -> World:
    if (params.setting, params.engine) not in valid_combos():
        raise StoryError(explain_rejection())
    setting = SETTINGS[params.setting]
    engine = ENGINES[params.engine]
    hero = Entity(
        id="hero",
        kind="vole",
        label=params.hero_name,
        location=setting.name,
        meters={"height": 0.12, "distance": 0.0},
        memes={"curiosity": 0.9, "courage": 0.5},
    )
    helper = Entity(
        id="badger",
        kind="helper",
        label="a patient badger",
        location=setting.name,
        meters={"height": 0.45},
        memes={"patience": 0.9, "trust": 0.7},
    )
    world = World(setting=setting, hero=hero, engine=engine, helper=helper)
    rng = random.Random(params.seed)
    scene = SCENES[rng.randrange(len(SCENES))]
    lesson = LESSONS[rng.randrange(len(LESSONS))]
    object_name = rng.choice(["a red scarf", "a smooth pebble", "a brass button"])

    world.facts.update(
        scene=scene,
        lesson=lesson,
        object_name=object_name,
        checked=False,
        repaired=False,
        crossed=False,
    )

    world.say(scene["opening"])
    world.say(
        f"{params.hero_name} the {params.trait} vole carried {object_name} toward {setting.name}. "
        f"Beside the {setting.feature} waited {engine.name}, a little machine with a bright copper handle."
    )
    world.say(
        f"{scene['quest'].capitalize()}. But {setting.danger}, and the engine would not help."
    )

    world.para()
    world.say(
        f"{params.hero_name} poured out {engine.fuel}, then heard a rough scrape. "
        f"The engine's problem was clear: {engine.problem}."
    )
    world.say(f'"I can make it go if I pull harder," said {params.hero_name}.')
    world.say(f'"You might make the trouble worse," said {helper.label}. "What does the machine tell us?"')
    world.say(f'"It tells me to look before I leap," said the vole.')
    world.say(f"Then {scene['choice']}. The useful clue was {scene['clue']}.")

    world.para()
    world.say(
        f"{scene['turn'].capitalize()}. The badger held a lantern while the vole made a careful plan."
    )
    world.say(
        f"Together they worked to {engine.repair}. They used a light touch, because the engine's power could hurt a paw."
    )
    world.facts["checked"] = True
    world.facts["repaired"] = True
    world.say(
        f"Next they followed the safe test: {engine.safe_test}. "
        f"The test succeeded, and {engine.result}."
    )

    world.para()
    world.say(
        f"The new light showed {setting.landmark}. The vole, the badger, and the engine crossed the adventure's "
        f"hardest stretch together. {scene['ending']}."
    )
    world.facts["crossed"] = True
    world.say(f"The lesson learned was simple: {lesson}")
    world.say(
        f"{params.hero_name} tucked {object_name} safely away and smiled. The next time an engine went quiet, "
        "the vole would listen before rushing ahead."
    )
    return world


KNOWLEDGE = [
    QAItem(
        question="What is a vole?",
        answer="A vole is a small animal that looks a little like a round-eared mouse and often lives among grass and roots.",
    ),
    QAItem(
        question="What is an engine?",
        answer="An engine is a machine that changes fuel or another source of energy into motion or useful work.",
    ),
    QAItem(
        question="What does it mean to learn a lesson?",
        answer="Learning a lesson means understanding something from an experience and using that understanding in a later choice.",
    ),
    QAItem(
        question="Why can an adventure be exciting?",
        answer="An adventure can be exciting because someone faces an unfamiliar place or problem and must make thoughtful choices.",
    ),
]


def generation_prompts(world: World) -> list[str]:
    scene = world.facts["scene"]
    return [
        f"Write an adventurous child-facing story about a vole whose engine stops while {scene['quest']}.",
        "Tell a gentle adventure in which a vole repairs an engine by listening before acting.",
        "Write a story with a clear lesson learned after a small animal solves a dangerous machine problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scene = world.facts["scene"]
    return [
        QAItem(
            question="Why did the vole need the engine?",
            answer=f"The vole needed the engine because {scene['quest']}. The rising fog made the journey urgent.",
        ),
        QAItem(
            question="What was wrong with the engine?",
            answer=f"The engine had trouble because {world.engine.problem}.",
        ),
        QAItem(
            question="What did the badger tell the vole?",
            answer="The badger told the vole not to pull harder and to listen to what the machine was showing them.",
        ),
        QAItem(
            question="How did the vole and badger fix the engine?",
            answer=f"They worked together to {world.engine.repair}. Then they followed a safe test: {world.engine.safe_test}.",
        ),
        QAItem(
            question="What lesson did the vole learn?",
            answer=f"The vole learned that {world.facts['lesson'].lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/2.
valid(S, E) :- setting(S), engine(E), supports(S, E).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for eid in ENGINES:
            lines.append(asp.fact("supports", sid, eid))
    for eid in ENGINES:
        lines.append(asp.fact("engine", eid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("ASP/Python mismatch.")
        print("Only Python:", sorted(py - cl))
        print("Only ASP:", sorted(cl - py))
        return 1
    for seed in range(3):
        params = StoryParams("misty_ravine", "lantern_engine", "Nell", "curious", seed)
        sample = generate(params)
        if "vole" not in sample.story or "engine" not in sample.story:
            print("Generated story exercise failed.")
            return 1
    print(f"OK: ASP/Python parity and generated-story checks passed ({len(py)} combos).")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    for entity in [world.hero, world.helper, world.engine, world.setting]:
        lines.append(
            f"{entity.id}: {entity.label if hasattr(entity, 'label') else entity.name}; "
            f"meters={entity.meters}; memes={entity.memes}"
        )
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adventure storyworld about a vole and an engine.")
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--engine", choices=sorted(ENGINES))
    parser.add_argument("--name")
    parser.add_argument("--trait", choices=TRAITS)
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    engine = args.engine or rng.choice(sorted(ENGINES))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, engine=engine, hero_name=name, trait=trait)


CURATED = [
    StoryParams("misty_ravine", "lantern_engine", "Nell", "curious", 9601),
    StoryParams("misty_ravine", "water_engine", "Pip", "brave", 9602),
    StoryParams("misty_ravine", "lantern_engine", "Mara", "patient", 9603),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible stories:")
        for setting, engine in asp_valid_combos():
            print(f"  {setting} / {engine}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(max(0, args.n)):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
