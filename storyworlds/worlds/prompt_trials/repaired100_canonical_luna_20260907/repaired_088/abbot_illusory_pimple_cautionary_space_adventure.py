#!/usr/bin/env python3
"""
A cautionary space adventure about an abbot, an illusory pimple, and a lesson
about checking strange signals before touching them.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
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
    abbot_name: str
    pilot_name: str
    moon_name: str
    seed: Optional[int] = None
    hazard_id: Optional[str] = None
    mode: Optional[str] = None


@dataclass(frozen=True)
class Hazard:
    id: str
    signal: str
    false_clue: str
    test: str
    danger: str
    repair: str
    ending: str


ABBOT_NAMES = ["Abbot Sol", "Abbot Mira", "Abbot Taro", "Abbot Nemi"]
PILOT_NAMES = ["Luna", "Pip", "Rae", "Orin"]
MOON_NAMES = ["Vela", "Orra", "Nix", "Cinder"]
MODES = ["quiet_launch", "signal_first", "question_open", "warning_open"]

HAZARDS = [
    Hazard(
        "mirror_bloom",
        "a bright purple pimple appeared on the moon's dark side",
        "It looked like a tiny mountain pushing through the moon's skin",
        "The crew viewed it through two different filters and saw that its glow stayed fixed to the ship's window",
        "It was an illusory reflection from a cracked navigation lens, not a mountain",
        "They covered the lens, recalibrated the scanner, and turned away from the false landing signal",
        "The moon looked smooth again, while the repaired lens showed honest stars instead of a tempting purple bump",
    ),
    Hazard(
        "plasma_pimple",
        "a red pimple blinked on the hull beside the engine",
        "The blinking mark seemed to be a warning from a tiny space creature",
        "They compared the mark with the hull camera and found it moved exactly with a loose plasma spark",
        "Touching it could have burned a glove and damaged the engine panel",
        "They shut down the small circuit and called the ship's repair drone",
        "The red mark vanished, and the engine hummed safely beneath a clean silver hull",
    ),
    Hazard(
        "hollow_crater",
        "an illusory pimple floated above a silent crater",
        "The bump seemed to promise a hidden tunnel under the crater",
        "A beam from the rover passed through the bump without casting a shadow",
        "Landing on the false bump would have sent the rover toward a deep dust trench",
        "They marked the crater as unsafe and followed the real ridge shown by the radar",
        "The rover crossed firm ground, leaving two careful tracks beneath a sky full of stars",
    ),
    Hazard(
        "green_beacon",
        "a green pimple glowed on an asteroid's spinning face",
        "The crew thought it was a friendly beacon asking for help",
        "The abbot waited through one full turn and saw the glow repeat with the asteroid's reflection",
        "Following it would have pulled the ship into a field of fast rocks",
        "They ignored the illusory beacon and used the steady navigation star instead",
        "The ship slipped past the rocks, and the false green light faded behind them",
    ),
]

HAZARD_BY_ID = {h.id: h for h in HAZARDS}


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xAB807)
    text = "|".join([params.abbot_name, params.pilot_name, params.moon_name, params.hazard_id or ""])
    return random.Random(sum((i + 1) * ord(c) for i, c in enumerate(text)))


def build_world(params: StoryParams) -> World:
    rng = _rng(params)
    hazard = HAZARD_BY_ID.get(params.hazard_id or "")
    if hazard is None:
        hazard = rng.choice(HAZARDS)
    mode = params.mode if params.mode in MODES else rng.choice(MODES)

    world = World()
    abbot = world.add(Entity("abbot", "character", params.abbot_name))
    pilot = world.add(Entity("pilot", "character", params.pilot_name))
    moon = world.add(Entity("moon", "place", f"moon {params.moon_name}"))
    scanner = world.add(Entity("scanner", "tool", "double-filter scanner"))
    pimple = world.add(Entity("pimple", "phenomenon", "illusory pimple"))

    abbot.memes.update(caution=1.0, curiosity=1.0)
    pilot.memes.update(caution=1.0, trust=1.0)
    scanner.meters.update(clarity=0.0, power=1.0)
    pimple.meters.update(glow=1.0, danger=1.0)
    world.facts.update(hazard=hazard, mode=mode, solved=False, place=moon.label)

    openings = {
        "quiet_launch": f"The little ship drifted quietly past {moon.label} until {hazard.signal}.",
        "signal_first": f"A strange signal flashed beside {moon.label}: {hazard.signal}.",
        "question_open": f"What was the glowing bump near {moon.label}? It was {hazard.signal}.",
        "warning_open": f"Abbot {params.abbot_name.removeprefix('Abbot ')} raised a warning when {hazard.signal}.",
    }
    world.say(openings[mode])
    world.say(f"The crew called it a pimple because it looked like a small raised spot on a much larger world.")
    world.para()

    world.say(
        f'"Do not touch it yet," {abbot.label} said. "A bright thing can be a trick."'
    )
    world.say(
        f'"Then I will check it from the safe side," {pilot.label} replied, turning the ship away from the glow.'
    )
    world.say(f"Their brief exchange changed the plan: curiosity would guide them, but caution would choose their path.")
    world.say(f"At first, {hazard.false_clue}.")
    world.para()

    abbot.memes["caution"] += 1.0
    pilot.memes["trust"] += 1.0
    scanner.meters["clarity"] = 1.0
    world.say(f"{hazard.test}.")
    world.say(
        f"The test showed that the pimple was illusory. It was not a safe doorway or a friendly message; {hazard.danger.lower()}."
    )
    world.say(
        f'"Good checking keeps explorers alive," said {abbot.label}. "Now we know what not to follow."'
    )
    world.para()

    pimple.meters["danger"] = 0.0
    scanner.meters["clarity"] = 2.0
    abbot.memes["relief"] = 1.0
    pilot.memes["relief"] = 1.0
    hazard_repair = hazard.repair
    world.say(f"{hazard_repair}.")
    world.say(
        f"They recorded the lesson in the ship's log: never land on a strange pimple or chase a beautiful signal before testing what it is."
    )
    world.say(f"{hazard.ending}.")
    world.facts["solved"] = True
    world.facts["hazard"] = hazard
    world.facts["abbot"] = abbot
    world.facts["pilot"] = pilot
    world.facts["moon"] = moon
    world.facts["scanner"] = scanner
    world.facts["pimple"] = pimple
    return world


def generation_prompts(world: World) -> list[str]:
    h = world.facts["hazard"]
    a = world.facts["abbot"]
    p = world.facts["pilot"]
    return [
        f"Write a child-friendly cautionary space adventure about {a.label}, {p.label}, and {h.signal}.",
        f"Show how the crew discovers that the pimple is illusory by using a safe test instead of touching it.",
        "Include a brief back-and-forth conversation and end with a concrete image proving the ship and crew are safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hazard"]
    a = world.facts["abbot"]
    p = world.facts["pilot"]
    return [
        QAItem(
            f"What strange thing did {a.label} and {p.label} see?",
            f"They saw {h.signal}. It looked like a small pimple on or near the space world.",
        ),
        QAItem(
            "Why did the crew avoid touching the pimple?",
            f"They avoided touching it because {h.danger.lower()} The abbot wanted to test the strange sight safely first.",
        ),
        QAItem(
            "How did the crew learn that the pimple was illusory?",
            f"They learned it was illusory when {h.test.lower()} This evidence showed that the glow was a trick rather than a safe object.",
        ),
        QAItem(
            "What did the crew do after discovering the danger?",
            f"They repaired or avoided the source of the false signal: {h.repair}. This kept their ship on a safe course.",
        ),
        QAItem(
            "What lesson did the space adventure teach?",
            "It taught that explorers should check unusual sights carefully before touching them or following them.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an abbot?", "An abbot is a leader of a community of monks."),
        QAItem("What does illusory mean?", "Illusory means seeming real but actually being a trick or an appearance."),
        QAItem("What is a pimple?", "A pimple is a small raised spot on skin or on a surface that looks like skin."),
        QAItem("Why are caution and testing useful in space?", "Space can contain hidden dangers, so careful testing helps explorers make safe choices."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.kind} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  solved: {world.facts.get('solved')}")
    lines.append(f"  hazard: {world.facts['hazard'].id}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("setting", "space"),
            asp.fact("role", "abbot"),
            asp.fact("phenomenon", "illusory_pimple"),
            asp.fact("action", "observe"),
            asp.fact("action", "test"),
            asp.fact("action", "avoid"),
            asp.fact("value", "caution"),
        ]
    )


ASP_RULES = r"""
safe_observation :- setting(space), role(abbot), action(observe).
tested_signal :- safe_observation, action(test).
cautionary_choice :- tested_signal, action(avoid), value(caution).
valid_story :- cautionary_choice, phenomenon(illusory_pimple).
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    ok = any(symbol.name == "valid_story" for symbol in model)
    if not ok:
        print("MISMATCH: ASP twin did not confirm the cautionary space adventure.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("solved"):
            print("MISMATCH: generated story did not resolve its danger.")
            return 1
        if "illusory" not in sample.story.lower() or "pimple" not in sample.story.lower():
            print("MISMATCH: generated story lost required narrative words.")
            return 1
    print("OK: ASP twin and generated stories agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cautionary space adventure storyworld.")
    parser.add_argument("--abbot")
    parser.add_argument("--pilot")
    parser.add_argument("--moon")
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
        abbot_name=args.abbot or rng.choice(ABBOT_NAMES),
        pilot_name=args.pilot or rng.choice(PILOT_NAMES),
        moon_name=args.moon or rng.choice(MOON_NAMES),
        hazard_id=rng.choice(HAZARDS).id,
        mode=rng.choice(MODES),
    )


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
    StoryParams("Abbot Sol", "Luna", "Vela", hazard_id="mirror_bloom", mode="signal_first"),
    StoryParams("Abbot Mira", "Pip", "Nix", hazard_id="plasma_pimple", mode="warning_open"),
    StoryParams("Abbot Taro", "Rae", "Cinder", hazard_id="hollow_crater", mode="quiet_launch"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
